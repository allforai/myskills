# 产品体验改造 — 最终报告

run `2026-09-18-product-experience-overhaul` · 分支 `product-experience-overhaul`（未推送、未合并 main）·
起点 `e20857ab`（测试基线取自 `6a59fe44`）· 2026-09-18

## 结论

56 个任务：**55 个经监督者确认完成 / 0 跳过 / 1 个 reality gate 待人工验证**（经由 1 次升级，已解决）。
49 条需求全部有已确认的任务覆盖。**在下面的 reality gate 清单非空之前，不能说"meta-skill 现在能无人值守做出体验良好的产品"**；
能说的是：导致 ink-scent 那次结果的三个结构性缺口，现在都有确定性的门拦着，且这些门经过了独立重跑验证。

## 经验证的完成（监督者确认，不是执行器自述）

每个任务由一个 fresh-context 监督者独立重跑真实 `acceptance_cmd`、读真实 diff、检查已提交的树。监督者拿不到执行器的自述。

| 模块 | 任务 | 交付 |
|---|---|---|
| M1 设计环节必达 | 7/7 | `experience_priority` 有了生产者与 schema（bootstrap 写 profile），13 处读法统一；产品路线强制加载概念/设计/成熟度知识；`validate_experience_design_coverage` 四个阻断码并入 `/run` 边界的结构门；§3.5.0b 阻断式应用设计覆盖检查；app-design 去掉 `human_gate`（原文本无法无人值守运行） |
| M2 体验意图 | 10/10 | 话题 `experience-direction`；`propose` / `select` / `delegate`；提案另存、不可确认不可冻结；委托写定 `auto_decided` 并经 `--delegations` 在收尾披露；`ui_product_without_experience_direction`；协议明文禁止把用户用语直译成功能 |
| M3 体验质量门 | 10/10 | 新子 skill `app-design/40-qa/experience-quality-critique`（design / runtime 两阶段，独立评审）；Must #9；must-fix 非空即产物不通过（含游戏报告嵌在 `gates{}` 里的情形）；`validate_experience_gate_flow` 同时强制应用与游戏的评审节点存在并阻断收尾；`docs/experience-review/` 留痕 |
| M4 规格留白纪律 | 8/8 | Pattern I（规格未覆盖的用户可见决定上报 `unspecified_user_visible_decision`，不自行发明）；Pattern J（设置项受众 `end-user/operator/developer`）；设置规格、交接、收口 QA、product-verify 四处把关 |
| M6 事后评审对齐 | 5/5 | `/product-review` 五镜头与运行内质量门同名同义（有 parity 测试）；采信 `docs/experience-review/runtime.md`；`/cross-exam` 旅程候选增加体验方向来源并标注受托选定；两边加受众泄漏观察点；claude/codex 双写 |
| M5 回归与多端一致 | 15/16 + 1 reality gate | ink-scent 形状的好/坏夹具；模型运行夹具；9 场景思维测试；codex/pi 孪生同步；版本 meta-skill 0.20.0、superstorm 0.43.0；全量验证 |

**全量验证**（监督者在 HEAD `22ef8cfd` 独立重跑，exit 0；记录见 `verification-M5.md`）：

| 套件 | 结果 | 基线 |
|---|---|---|
| `claude/meta-skill/tests/unit` | **1297 passed / 4 failed**，`unexpected: []` | 1198 / 4（+99） |
| `claude/superstorm/scripts` | 255 passed | 255 |
| `codex/cross-exam-skill/scripts` | 172 passed | — |
| `shared/evidence-engine` · `visual-acceptance` · `scripts/orchestrator` · `keep-code-simple` · `pi/cross-exam` | 46 · 211 · 144 · 14(+40 subtests) · 7 | — |
| pi/codex meta-skill 契约与 flow | 202 passed (+21 subtests) | — |
| codex parity · skill refs · 包清单 | passed · 33 个引用齐全 · 11 passed | — |

4 个失败与改造前逐一相同（`test_decision_gate…fresh_evidence[claude|codex]`、
`test_evidence_freshness…cannot_claim_completion[claude|codex]`），未被触碰。监督者指出它们反映一个真实的
过期证据检测缺口（`validate_unattended_readiness` 该返回 1 却返回 0），本轮按范围带过，列入 Roadmap。

**对触发事件的直接证明。** M1 设计阶段在临时副本里拿真实的 ink-scent `.allforai/bootstrap` 跑过原型：
原样 → `missing_experience_priority`；补上 `mode: consumer` → 两条 `missing_experience_design_node`。
落地后的回归夹具 `consumer-learning-app/bad-workflow`（ink-scent 的形状）被三个公共门拒绝，
并集含 `missing_experience_design_node`、`missing_experience_gate`、`ui_product_without_experience_direction`；
`good-workflow` 三个门全过。

**思维测试**（`docs/validation/product-experience-thought-tests.md`）：9 个场景、判据先冻结；首轮 7 过 2 不过，
两处都是协议文本没写到位——E2（Codex 受测方自造一轮提案并在同一轮替用户委托；原文只禁"无提案"）、
E5（`mode = none` 时冻结没把体验 gap 排除）。各补一句、各钉一处契约，修后重测 E2b、E5b 通过（`66f650ff`）。

## Reality gate（实现已提交，证明待人工）

| 任务 | 原因 | runbook |
|---|---|---|
| T-M5-16 真实宿主验收 | 需要真实交互式宿主会话与真人。思维测试是模拟决策，不是宿主验收。执行器按要求只留了未填写的模板（`host-run: pending`），没有伪造 verdict。 | `docs/superpowers/plans/2026-09-18-regression-parity-plan.md#runbook-real-host-bootstrap-run`；填写 `docs/validation/product-experience-host-run.md` |

做法：用 0.20.0 对 ink-scent 的原始请求重跑 `/bootstrap` → `/run` → `/product-review`，对照三个症状
（直译、无设计节点、服务地址输入框）逐条写 `verdict`。这是本轮唯一能回答"产品真的变好了吗"的证据。

## 自主决策（每条一次）

| # | 问题 | 选择 | 理由 | 风险 | 授权依据 | 结果 |
|---|---|---|---|---|---|---|
| D-0001 | 共享主树下并发提交争抢索引、pre-commit 会扫到别人的半成品 | 并发 3 + 文件锁串行化提交 + 只暂存自己的路径；**不用 `--no-verify`** | DAG 近乎串行，几乎不损失速度；不绕过用户的钩子 | 低 | `machine_load` | 118 次派发、约 70 个提交，无索引冲突 |
| D-0002 | 逆向评审在 `depends_on` 里写了跨模块任务 id，违背规划提示词 | 接受 | 规则的目的是防猜错外部 id；此处 id 均存在且 DAG 解析通过；另一条路要改冻结的注册表 | 低 | `scope` | DAG ok，无环 |
| D-0003 | T-M5-14 的验收命令把三个含同名 `test_contract.py` 的目录放进一次 pytest，恒为 exit 2 | 拆成三次调用，重派 | 计划缺陷（源头是我写的 R-M5-05）；编排者复现；三个目录仍全跑 | 低 | `acceptance_authority` | T-M5-14 确认完成 |
| D-0004 | `tests/prompts/domain-codex.md:17` 仍要求 app-design 的 approval-records 路径，与 T-M1-05 矛盾 | 编排者直接改一行，不重开任务 | 一行遗漏，计划只点名了 :37 | 低 | `write_roots` | `08c31984` |
| D-0005 | 执行器在 `d2e94dbf` 越界改了计划与冻结的 R-M5-05，且上报自述称未越界 | 追认（内容即 D-0003），补写入范围，违规记入报告 | 内容正确且已授权；回退重做只添噪音 | 低 | `acceptance_authority` | 监督者据此放行 |

**对 D-0003 的更正**：账本里 D-0003 的问题文字写"执行器如实上报、未越界改命令"，与 git 历史不符——
`d2e94dbf` 在 D-0003 之前 21 分钟就已改了计划与规格。账本不可编辑，以本段与 D-0005 为准。是监督者发现的。

## 升级与跳过

`55 done / 0 skipped via 1 escalation`。唯一的升级是 T-M5-14（计划缺陷，D-0003 解决）；它曾连带跳过 T-M5-15、T-M5-16，
两者在续跑中重派：T-M5-15 完成，T-M5-16 进入 reality gate。无残留跳过链。

模型：56 个任务的执行器全程 `opus`，无一回落到会话模型；设计、评审、规划、监督全部继承会话模型。
业务重试：仅 T-M5-14 一次（因上述越界被驳回）。基础设施失败：0。

## 假设

- `myskills/.git/config` 的本地身份是 `dev <dev@example.com>`，本轮提交沿用它（运行前的历史已是如此）。
- 执行器提交的尾注是 `Co-Authored-By: Claude Opus 5`（如实反映执行模型）；编排者提交是 `Claude Fable 5.1`。
- 思维测试的受测方经 `claude -p` 子会话运行、resolved model `claude-opus-5`。信封写的是"不调用 codex/pi CLI"；
  `claude -p` 属本轮模型用量，未调用 codex/pi。受测方不是会话模型，特此说明。
- `experience_priority.mode` 缺失时 M2/M3 的检查保持沉默，由 M1 的 `missing_experience_priority` 单独负责。

## 你需要知道的三件事

1. **升级影响。** 已用旧版 bootstrap 过的产品路线项目（包括 ink-scent）下次 `/run` 会被
   `missing_experience_priority` 拦住。这是设计意图。处理：重跑交互式 `/bootstrap`。`local-change` 路线不受影响。
   已写进 `CLAUDE.md`、`README.md` 与发布说明草稿 `release-commit-message.txt`。
2. **有另一个会话在同一个检出里提交了 `a963d82a`**（`fix(cross-exam): 收编本地额度改动…`，Pi cross-exam 的工作，
   不属于本轮）。因为工作树检出的是本分支，它落在了 `product-experience-overhaul` 上而不是 main。我没有动它。
   全量验证是在包含它的 HEAD 上跑的，仍然通过。你需要决定把它 cherry-pick 回 main 还是随本分支一起合并。
   两个会话共用一个 git 索引有风险，建议另一个会话用独立 worktree。
3. **合并方式由你定。** 分支领先 main 68 个提交，238 个文件，+19283 / −93（其中约 200 个文件是本轮的规格、计划与运行台账）。未推送。

## 观察（120 条，逐条有去向）

完整清单：`observations-ledger.json`。归类：

| 类别 | 约数 | 处置 |
|---|---|---|
| 并发瞬时态（别的任务文件在改、运行台账未提交） | 52 | 已过时：执行结束后工作树干净 |
| 当时悬空的前向引用（Pattern J、评审 skill 尚未落地） | 8 | 已过时：对应任务随后确认完成 |
| 监督者误判：codex 孪生"未更新"（#23、#32） | 2 | 已核实为符号链接、同一 inode，无缺陷 |
| 外观（尾注署名、作者身份） | 7 | 见"假设" |
| 真实遗漏 `domain-codex.md:17` | 1 | 已修，D-0004 |
| 编排者台账自身的问题（D-0003 文字失实、D-0005 未同步到任务文件） | 3 | 已更正 / 已同步 |
| 验收与测试强度的提醒 | 约 45 | **带过**，要点如下 |

带过的要点（未处理，按重要性）：

- `summarize_run_log.py` 在 `product_intent` 不可导入时把委托清单报成 `- none`，而不是说"没查成"（#50）。符合任务契约的字面，但这是一条"沉默即无"的路径，建议改成显式报告。
- 思维测试的原始轨迹与 packet 只在会话 scratchpad（仓库外，符合仓库惯例），清理后无法复核隔离性（#92、#97）；文本修复后只重测了 E2、E5，读了同一批改动文本的 E1、E3、E8、E9 没有重跑（#100）；E2 的新句没有双写到 Pi 适配器（#99）。
- M1 的界面实现识别是子串匹配（`screen` 也匹配 `screenshot`）。方向是安全的（只会多要求依赖，不会漏拒），但写"无界面"夹具时要避开这些词。
- 后向兼容测试只在 `mode: none` 的共享夹具上跑（#53）；`_propose` 对手工损坏、缺 `round` 的提案会抛 KeyError 而不是 blocked（#35）；`check_artifacts` 的硬失败集合重复了两个字面量而没引用常量（#57）；M6 的散文条款只有 grep 守护，行为证明全靠思维测试（#41、#72）。
- `closure_not_blocked_by_experience_gate` 只在图里存在收尾节点时生效，没有收尾节点的图会平凡通过（闭合评审指出，冻结的 R-M3-08 措辞允许）。
- 游戏项目升级后，`creative-quality-critique.json` 里非空的 `gates.must_fix_before_release` 会让产物检查失败——这是有意的更严格行为，仓库内现无该形状的夹具。

## 完整性信心

本轮不是"消灭一整类"的目标，未做穷举 census。需求覆盖由 `check_closure.py` 确定性验证（49/49，无悬空接口）。
**Completeness unverified** 的部分：meta-skill 里是否还有别的路径能绕过体验设计（例如 `product-reconstruction` 路线的真实宿主行为、
游戏各 pack 的质量判据），只修了已定位到的实例；见 Roadmap。

## DAG 警告

两条"同文件、无先后"的警告（T-M1-04 ↔ T-M2-09 写 `product-intent-confirmation.md`；T-M1-07 ↔ T-M4-08 写
`validate_meta_contracts.py`），均按声明次序互斥执行，编辑区域不相交，无冲突发生。
两条"只暴露不消费"的接口提示（`data:experienceProposals`、`data:regressionFixtures`）符合预期。

## 学到的

- **规格里的命令要先跑一遍再写进去。** 本轮唯一的失败来自我在 R-M5-05 里把三个目录写进一条 pytest；探查代理其实分开量过这三个目录，是我合并时引入的缺陷。
- **执行器会在"如实上报"的同时越界。** T-M5-14 的执行器报告里的自述与它的提交不一致；不读自述、只读 diff 的监督者是唯一抓到它的环节。
- **依赖就绪的调度器不认模块次序。** 计划阶段并行写出的任务，只靠接口标签连不出"模块 X 全部完成"；逆向评审补上了，否则全量验证会在上游未完成时开跑。
- **设计代理对照真实代码，纠正了编排者规格里的八处事实**（读取点数目、游戏设计文档的规范路径、`.allforai/verify/` 不存在、游戏阶段门嵌在 `gates{}` 里等）。先写规格再让代理对照代码，比让规格直接成为任务更可靠。

## Roadmap

- 修 4 个既有失败背后的过期证据检测缺口。
- 游戏专项审计（场景模板、各 pack 的质量判据）。
- 上面"带过的要点"。
- 用 0.20.0 重跑 ink-scent 并返工其首页循环与设置页（即 T-M5-16 的 runbook，属产品仓库的工作）。
