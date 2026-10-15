# jev 插件 — 把 Jev 的判断能力接进 Claude Code

## 背景

Jev 是 TypeSafe 的 System One 模型：给它一段数据（`state`）和几道带类型的题（`choice` 单选 / `score` 打分 /
`noul` 是否概率），它返回带概率的结构化答案，不生成文字，输入按 token 计费、输出免费。
来源：docs.typesafe.ai、OpenRouter 的 Jev 指南、视频《Jev + Claude，男女搭配，幹活不累》（社区用法汇总，
其中的省钱比例与耗时数字未经核实，不作为本设计的验收依据）。

本插件做三件事：**选模型**（每句 prompt 先由 Jev 判难度，简单题本轮降到便宜模型）、**批量分类与打分**、
**代码扫描**（批量判断的一个特化）。**不做**选 skill：Claude Code 的 skill 名单不能按 prompt 删减，
省不到 token，只剩"挑得更准"，对当前规模收益不足，用户已确认不做。

## 已确认的平台事实（决定了设计形状）

来自 code.claude.com 文档（hooks / skills / sub-agents / model-config / plugins）：

- hook 不能设置主会话模型；插件的 `settings.json` 只认 `agent`、`subagentStatusLine` 两个键。
- skill frontmatter 的 `model` "applies for the rest of the current turn"——这是本轮降档的唯一杠杆。**未实测。**
- `UserPromptSubmit` hook 收到 `prompt`、`session_id`、`transcript_path` 等；可输出 `additionalContext`
  （附在 prompt 旁）与 `systemMessage`；不能改写 prompt；阻塞执行直到返回；超时则其输出被丢弃、prompt 照常进入。
- 该 hook 也会被计划任务、后台子 agent 回报、跨会话消息触发，不只是用户手打的话。
- hook 进程能拿到 `CLAUDE_PLUGIN_DATA`，但 Claude 用 Bash 跑的脚本不保证有；故状态与配置统一放用户配置目录。

调用方式：`POST https://openrouter.ai/api/v1/systemone`，请求体与 TypeSafe 官方 `/v1/systemone` 相同，
`model` 用 `~typesafe/jev-latest`，用 `OPENROUTER_API_KEY` 计费。鉴权头格式文档未写明，按 Bearer 假设，**未实测。**
OpenRouter 上的 `typesafe/jev-router` 是在 OpenRouter 自己的模型池里选模型并生成回答的聊天接口，
不能切换 Claude Code 的模型，本设计不用它。

## 实现前必须先跑通的三个探针

实现计划的第一个任务就是这三个探针，结论写进本文件末尾"探针结论"一节再继续：

- **P1 真实调用**：用用户的 `OPENROUTER_API_KEY` 发一次含 choice / score / noul 三题的请求，记下鉴权头、
  响应信封（`answers`、`usage`、`usage.cost` 是否存在）、实测延迟与单次花费。
- **P2 本轮降档**：装一个 frontmatter `model: haiku` 的 skill，让会话在 Opus/Fable 下调用它，
  从 transcript 中后续 assistant 消息的 `message.model` 确认本轮确实换了模型、下一轮恢复原模型。
  同时记下 transcript 里 Skill 调用（`tool_use` 的 `name` 与 `input` 键）和 skill 正文注入（是否是一条带 `isMeta`
  的 user 消息）的确切形状——R-07 判断"轮"的边界依赖它。
  **P2 不通过时**：R-07 的注入改为"建议"文案（告诉 Claude 本题判为简单、可委派给低档子 agent），
  tier skill 不发布；先告诉用户再改，不默默降级。
- **P3 区分用户手打的 prompt**：在 hook 里落盘几种来源（手打、后台任务通知、子 agent 回报）的原始输入，
  找出能区分它们的字段或文本特征。找不到可靠字段时，规则是：prompt 以 `<` 开头的 XML 风格标签
  （如 `<task-notification>`、`<system-reminder>`）一律视为非手打，跳过。

## 需求

### 插件形状

- **R-01 独立插件。** `claude/jev/`，自带 `.claude-plugin/plugin.json` 与 `marketplace.json`，
  安装为 `jev@jev`。纯 Python 标准库，无第三方依赖、无构建步骤。只做 Claude 平台；Codex / Pi 不在本期。
- **R-02 一个调用模块。** 三个功能都经同一个 `scripts/jev_client.py` 调 Jev：读 `OPENROUTER_API_KEY`，
  `JEV_BASE_URL` 可覆盖地址（测试用），模型 id 默认 `~typesafe/jev-latest`、可由配置覆盖。
  对 429 / 5xx / 网络错误按指数退避重试（上限可配，默认 3 次），4xx 其余错误不重试。
  返回答案、`usage`、模型版本；从不打印或落盘 API key。
- **R-03 配置与状态目录。** 全部放在 `${XDG_CONFIG_HOME:-~/.config}/jev/`：`config.json`（模型 id、阈值、
  花费上限等，缺省全部有默认值，文件可以不存在）、`state.json`（选模型开关，按项目记录，见 R-04）、
  `route-log.jsonl`（每行带项目根目录）、`allow.json`（外发放行清单）、`question-sets/`（存下来的题目）。不写 `CLAUDE_PLUGIN_ROOT`（版本化缓存目录）。

### 功能 1：选模型

- **R-04 开关（按项目，默认关）。** `/jev on`、`/jev off`、`/jev status`（`commands/jev.md`）。
  开关只对当前项目生效：项目 = hook 输入里 `cwd` 所在 git 仓库的根目录，不在 git 仓库里时就是 `cwd` 本身。
  `state.json` 记录已打开的项目根目录；不在记录里的项目一律视为关。没有全局开关。
  打开即视为同意：此后在这个项目里每句手打的 prompt 的原文会发给 Jev。`on` 时把这句话和生效的项目路径
  原样告诉用户一次。`status` 显示：当前项目的开关状态、所有已打开的项目、当前项目最近 7 天判了多少句、
  各档各多少句、失败与超时各多少、平均延迟、累计花费。
- **R-05 发什么。** 只发这一句 prompt 的原文。不发对话历史、文件内容、skill 清单。
  prompt 超过 `route.max_prompt_chars`（默认 8000）不发、不降档——长 prompt 本身就说明任务不轻。
  按 P3 规则判为非手打的不发。
- **R-06 怎么判。** 一道 `choice` 题，三个选项 `light` / `standard` / `heavy`，每个选项写明判定标准
  （light：查找、格式转换、读一个函式签名这类单步、无需设计判断的事；standard：在已知范围内的常规改动与解释；
  heavy：设计、调试未知问题、跨多文件的改动、需要权衡的决定）。题面文本放在 `scripts/route_question.json`，
  不写死在代码里，便于调。
- **R-07 怎么降。** 只往下降，不升档：
  - 选中档的概率 ≥ `route.threshold`（默认 0.8）才动作，否则什么都不做。
  - `light` → 档位模型 `haiku`；`standard` → `sonnet`；`heavy` → 不动作。档位到模型别名的映射在配置里可改。
  - **会话模型不得被降档本身污染。** 从 `transcript_path` 读会话模型时，跳过"已调用 `jev:tier-*` 的那一轮"里
    调用之后的 assistant 消息——否则降过一次档，之后每句都会把会话误认成低档而不再降，或在用户改用 `/model`
    切低后误判成升档。轮的边界是用户真正发出的一条消息（不含 tool_result、不含 Claude Code 注入的元消息；
    skill 正文注入成什么形状由 P2 确认）。用户自己用 `/model` 切换后的回复照常计入。
  - 目标档不低于会话模型、或读不出会话模型时不动作。新会话的第一句之前没有任何回复、读不出会话模型：
    `route.assume_model`（默认不设）设了就按它算，不设则第一句不降，并在文档写明。
  - 动作 = 输出 `additionalContext`：注明来自 Jev、判定档位与概率，要求先调用对应的 tier skill
    （`jev:tier-light` / `jev:tier-standard`，frontmatter `model` 分别为 `haiku` / `sonnet`）再处理请求；
    同时输出 `systemMessage` 一行（如 `Jev → haiku (0.93)`）让用户看见这次降档。
  - tier skill 的描述写明"只在 Jev 路由注记要求时调用"。正文：继续处理用户的原请求；做的过程中发现超出
    低档模型能稳妥处理的范围时，停下并告诉用户这一轮被降了档、建议重发（下一轮自动恢复原模型）——降错的代价
    限定在这一轮，且用户看得见。
- **R-08 绝不挡路。** 开关关闭、没有 key、调用失败、超过 `route.timeout_s`（默认 3 秒）、响应格式不对——
  一律零输出、退出码 0，prompt 照常进入。hooks.json 里该 hook 的 `timeout` 设为 5 秒（大于客户端超时）。
- **R-09 日志。** 每次被触发都追加一行 `route-log.jsonl`：时间、session_id、是否发送及不发送的原因、
  档位、概率、动作、延迟、花费。**不记 prompt 原文**，只记长度。
- **R-09a 建议有没有被照做要可见。** 注入只是建议，Claude 可以不调用 tier skill。一个 `PostToolUse`（matcher
  `Skill`）hook 在 `jev:tier-*` 真被调用时记一行日志；`status` 分开显示"建议降档 N 次 / 照做 M 次"。
- **R-09b 省没省钱要可量。** `status` 从本项目最近 7 天的 transcript（`${CLAUDE_CONFIG_DIR:-~/.claude}/projects/`
  下按项目路径命名的目录）按"降档轮 / 其他轮"× 模型汇总实际 token（输入含缓存、输出分列，按 `message.id` 去重），
  不写死任何价格。这是开关对比的依据。

### 功能 2：批量分类与打分

- **R-10 skill 与触发。** `skills/classify/SKILL.md`，模型可自行调用。触发条件写在 description：
  数据量大（经验线：几十条以上）、每一条问的是同一组问题、答案能事先枚举成选项 / 分档 / 是否。
  条数少、每条问题不同、需要生成文字的，不用它。
- **R-11 脚本接口。** `scripts/jev_batch.py`：
  - 输入：JSONL，每行 `{"id": ..., "state": <字符串或对象>}`；题目文件 `{"questions": {...}, "thresholds": {...}}`，
    `questions` 即 Jev 原生格式，`thresholds` 按题 id 给阈值。
  - 输出：JSONL，每行 `id`、`answers`、`bucket`（`auto` / `review` / `failed`）、`reasons`（进 review 的原因）；
    另写 `<输出>.summary.json`：各桶条数、阈值、题目文件的哈希、模型版本、总 token、总花费、是否经过校准。
  - `export` 子命令把结果转成 CSV。
- **R-12 分桶规则。** 一行所有题都过阈值才进 `auto`；任一题不过进 `review`；重试用尽仍失败进 `failed`。
  choice / score 看 `confidence`；noul 看是否 ≥ 上阈值或 ≤ 下阈值（默认 0.9 / 0.1），落在中间就不过。
  `review` 不得并入 `auto`，脚本不提供这种开关。
- **R-13 先校准再全量，校准要留下审查记录。** 超过 50 行的数据，全量运行要求同一题目哈希下已有
  **经过 `approve` 的** `--sample N`（默认 20）试跑；只跑过样本不算。`approve` 必须给出样本里不同意的条数与要点；
  不同意数大于 0 时必须改题目重新试跑，或带 `--accept-reason "<理由>"` 接受。审查记录（样本数、不同意数、要点、
  接受理由）进 summary 与交付说明——它就是这批结果准确率的粗估。`--skip-calibration "<理由>"` 可越过，理由写进 summary。
- **R-13a 调阈值不重新花钱。** 题目哈希只覆盖题目与模型，不含阈值；`rebucket` 用已有答案按新阈值重新分桶，不发请求。
- **R-14 花费上限。** 全量运行前按字符数估算输入 token 与花费并打印；超过 `batch.cost_cap_usd`（默认 1 美元）
  需要 `--confirm-cost`。
- **R-15 断点续跑与并发。** 输出文件里已有的 id 跳过，不重复调用；并发数可配（默认 8）。
  单行 `state` 超过 32000 字节照跑，但在结果里标 `long_context: true`（Jev 此时走更慢、更不准的长上下文模式）。
- **R-16 外发放行。** `allow.json` 列出允许外发的路径前缀。输入文件不在任何前缀之下时，脚本不发任何请求、
  以退出码 3 结束并说明原因；SKILL.md 规定此时 Claude 去问用户，用户同意后由用户（或经用户同意由 Claude）
  把路径加进 `allow.json` 再跑。SKILL.md 同时规定：不得绕过脚本直接用 curl 等方式把数据发给 Jev。
- **R-17 题目复用。** 校准通过（已 `approve`）的题目用 `save-set` 存到 `question-sets/<名字>.json`，未 approve 的拒存；
  SKILL.md 规定处理同类数据时先查这里。
- **R-17a review 的裁决要落地。** `resolve` 逐条记录 review（或任意）行的最终结论与判定人（`claude` / `user`），
  存在结果文件旁；`export` 的 CSV 带"最终结论"与"判定人"列（auto 行的判定人是 `jev`）；summary 报告仍未裁决的 review 条数。
- **R-18 交付披露。** 交出结果时必须说明：哪些结论来自 Jev、各桶条数、阈值、校准审查记录、`review` 桶最后怎么处理的
  （Claude 判了哪些、交给用户哪些、还剩几条未裁决）、花费。

### 功能 3：代码扫描

- **R-19 skill 与触发。** `skills/code-scan/SKILL.md`，模型可自行调用。用于对大量代码片段问同一组
  "是否"问题：语义 lint（"这行日志是否打印了密钥"）、注释与代码是否不符、改动是否削弱测试等。
  单个文件的审查、需要推理的 bug 定位不用它。
- **R-20 切块。** `scripts/code_chunks.py` 把代码切成 R-11 的输入 JSONL，四种方式：
  `file`（整个文件）、`hunk`（`git diff` 的改动片段，带上下文行）、`grep`（匹配某个模式的行加前后各 N 行）、
  `window`（固定行数滑窗）。只取 `git ls-files` 列出的文件，跳过二进制与超过大小上限的文件。
  每块的 `id` 为 `路径:起始行-结束行`，`state` 开头带文件路径。**不做按函数切分**：跨语言的函数切分不可靠，
  `grep` 与 `window` 已能覆盖目标场景。
- **R-21 规则与结果。** 规则文件是一组 `noul` 题（可附 `criteria`）。跑 `jev_batch.py`（R-12 到 R-16 全部适用，
  外发放行要求代码目录在 `allow.json` 里）。命中上阈值的块列为待查；SKILL.md 规定 Claude 逐条打开源码确认，
  报告里只有确认过的才算问题，Jev 命中但 Claude 否定的单独列为"Jev 误报"并计数。
  确认 / 误报用 `resolve` 按"行 + 规则"记录；summary 按规则给出命中、确认、误报数。某条规则已核实 ≥ 4 次且误报过半时，
  `save-set` 拒存，必须先改这条规则——误报率反馈回规则本身。

## 测试

- `claude/jev/tests/`（pytest），用本地假 Jev 服务（`JEV_BASE_URL` 指过去）覆盖：
  开关开 / 关；在项目 A 打开后项目 B 仍是关、项目子目录里算项目 A；没 key、超时、5xx、坏响应都零输出且退出码 0；降档只往下；长 prompt 与非手打 prompt 不发；
  日志不含 prompt 原文；分桶规则（含 noul 上下阈值）；`review` 不进 `auto`；未校准拒绝全量；花费上限；
  断点续跑不重复请求；不在放行清单里时零请求、退出码 3；四种切块方式的 id 与范围。
- 目录加进 `shared/suites/suites.txt`（`test_suite_coverage.py` 会检查），并加进 `.githooks/pre-commit`
  的快速子集（几秒钟），每次提交自动跑。
- 实测一次（用户的真 key）：P1–P3，外加一个 30 条左右的真实分类样例，结论记进本文件。

## 文档

- 根 `CLAUDE.md` 的安装段加 `claude/jev` → `jev@jev`；"External Service Keys" 表里 OpenRouter 一行的
  "Used By" 加上 jev。
- 版本从 `0.1.0` 起。
- 交付时给出本机安装与改版后更新的确切命令（以 `claude plugin --help` 当时列出的子命令为准），安装由用户确认后执行。

## 不做

- 选 skill。
- Codex / Pi 适配。
- 选模型时升档、按对话历史判档。
- 按函数切分代码。
- 走 TypeSafe 官方地址（只走 OpenRouter；`JEV_BASE_URL` 仅供测试与日后切换）。

## 探针结论

（实现计划第一个任务完成后填写。）
