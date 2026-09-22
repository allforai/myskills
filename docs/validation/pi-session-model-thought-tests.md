# Pi 模型改动 — 思维测试记录

日期：2026-09-17。结论：**P1–P5 五个场景按运行前冻结的判据通过；P1 暴露一个真缺口——协议里「已授权的不同模型可用时优先互补模型」没被替换句覆盖，补一句后同场景复测 P1b 通过。** 本轮验证的是决策文本，不是三端真实验收。

## 方法与证据

- 每个场景一个 fresh-context `reviewer`，5 个独立子运行并发 3（workflow `c9b89b19-0feb-4399-80bf-3fd4553905ba`），复测 P1b 单独 1 个（`99ff7e7e-ca06-4bde-b6b8-b4b79e3b09ac`）；主会话按**运行前**写下的判据评估。
- 受测输入只是该技能全文（协议/canonical + Pi 适配）加场景；每份 packet 落在仓库外的 `/tmp/pi-session-model-260918-050222`，子代理只被要求读自己那一份。判据在 `fixtures/pi-session-model/thought-tests.json`，不给受试者。
- 隔离核对（不是自报）：每个子运行的 `events.jsonl` 里 `tool_execution_start` **恰好 1 次、都是 `read` 自己那份 packet**，没有其它读/搜/写/派发。
- resolved 模型取自宿主 receipt，不是子代理自报：全部 `openrouter/deepseek/deepseek-v4.1-flash`（会话模型），requested 是「不传 `model`、继承」。这正是新规则要求的记录口径。
- 受测文件 SHA256 在运行前后一致；证据、packet 与 receipt 哈希见 [evidence.json](pi-session-model-thought-tests/evidence.json)，子代理原文见 [responses.md](pi-session-model-thought-tests/responses.md)。

## 场景判定

| 场景 | 受测规则 | 实际回答 | 判定 |
|---|---|---|---|
| P1 / keep-code-simple：原生与 codex-exec 同时可用 | 只选原生代理、继承会话模型、按思考档分工 | 排除 `codex-exec`/`claude-code`，标注 `runner.available === true` 不是理由；scout low / oracle、reviewer high；单顶层 workflow、fresh、runs.all 保序 | 通过，但留口子（见下节） |
| P2 / keep-code-simple：原生全 disabled | 不借外部 CLI 换执行方式 | 不派发，转主会话串行并披露非独立；不装扩展、不改配置、不索权 | 通过 |
| P3 / cross-exam：0b 与省钱诉求 | 模型不换，只问思考档 | 改问「取证用哪个思考档」，给 A 全继承 / B `session:medium`；判断角色（普查官、规则审查官、视觉 reviewer、复核官）从不降；`judgment` 固定 session；不接受外部 harness | 通过 |
| P4 / cross-exam：只剩外部 CLI，且用户主动要求 | 外部 CLI 不算前置门通过 | 硬拒绝、不定靶不自审，明确「你口头授权也改不了」，给安装/换环境路径 | 通过 |
| P5 / meta-skill run：两写节点 | 会话模型 + 思考档 + 工作区隔离 | 不选 codex-exec，保持会话模型只加档位；worktree 避免双写；派发失败只按同协议重试，不切 CLI/`pi -ne` | 通过 |
| P1b / 同 P1 复测补句 | 不把「已授权不同模型」当例外 | 引用新句「『已授权的不同模型可用时优先互补模型』在 Pi 不适用」，争议复核只用会话模型的独立 fresh 上下文 | 通过 |

## P1 缺口与修复

P1 在旧文本下主判据全中，但它在复核环节写的是「仅当宿主/用户已授权不同模型时才用互补模型」。旧替换句只覆盖了「跨模型分工」，没有点名协议里那句「已授权的不同模型可用时优先互补模型」——按字面读，环境里存在已授权模型就可以换模型复核，等于把 Codex 那类模型重新放回选项。

修复只动一句：Pi 适配在替换句里明确「**『已授权的不同模型可用时优先互补模型』在 Pi 不适用**——环境里就算有其它可用模型（含 Codex 一类），复核也只用当前会话模型的独立 fresh 上下文」。契约测试加一条钉住该句。

**P1b 是在修复后的文本上重跑的同一场景**（不是对旧答卷重判）：同一环境、同一判据外加「不得把已授权模型当例外」。原件与复测的适配 SHA256 都在证据里，旧判定保留不改。

## 宿主侧核查：谁真正决定子代理模型

思维测试只证明了文本被读懂，证明不了根因。补查宿主后结论是：**Pi 没有把子代理送去 Codex 的路径，唯一入口是派发文本让主会话自己挑 `codex-exec`。**

- 原生子代理的模型解析顺序（`docs/models.md`，实现 `src/runs/shared/model-resolution.ts:399` `resolveModelSelection`）：per-run `model` → `agentOverridesByProvider` → `agentOverrides.<name>.model` → 代理 frontmatter `model` → `subagents.defaultModel` → 父会话模型。
- **本机没有任何模型策略**：`~/.pi/agent/settings.json` 没有 `subagents` 键，项目没有 `.pi/settings.json`，也没有 `~/.pi/agent/extensions/subagent/config.json`。所以内置代理全部落到父会话模型，与本轮 6 个子运行 receipt 里 resolved 的 `openrouter/deepseek/deepseek-v4.1-flash` 一致（同 `PI_MODEL`）。
- **外部 CLI runner 是换模型换 harness**：`src/api/preflight.ts:386` 对 `runner.type === "external-cli"` 直接 `model = undefined`，pi-subagents 不给 `codex` 传任何模型；codex 用自己的 `~/.codex/config.toml`（`model = "gpt-5.6-luna"`、`model_reasoning_effort = "medium"`）。外部适配器也不参与模型校验（`model_verification_failed` 只针对原生子代理），所以 Pi 侧看不到那次实际用了什么模型。
- **没有兜底替换**：`agent` 是调用方显式参数，名字不存在或已禁用直接报 `Agent 'x' not found`（`src/agents/agent-management.ts:641`、`1048`），不会自动改派到别的 agent，也没有默认 agent。

即宿主的模型解析链里没有 Codex，且本机没有任何 `subagents` 配置，所以子代理只会落到会话模型。

## 盲复现：旧文本到底会不会去 Codex

日期：2026-09-17。方法：受测 packet 用的是**盘里实际在跑的那份**适配（安装目录未提交改动，sha `8f9ea70e…`），不是仓库 HEAD 版本；协议不变。3 个 fresh 子代理，并发 3，cwd 在仓库外。判据运行前写明：选 `codex-exec`/`claude-code`、给原生子代理传别的路由模型、或明说换到别的路由补跑 → 复现。

| 运行 | 场景 | 结果 | 判定 |
|---|---|---|---|
| R1 `94ad7a44` | 原场景（原生与 codex-exec 都可执行） | 不选外部 CLI，引「`runner.available === true`；这只是预检，不代表已登录或可成功启动」；只用会话路由 + 思考档 | **未复现** |
| R2a `122ca595` | 同上 + 会话路由额度耗尽、scout 启动即失败 | 不换执行模式，但按本地那句「额度或容量耗尽…换一条已确认可用的模型路由」去换路由补跑，还要先开 1 条预检通道探其它路由额度，「可用的互补路由优先用于复核档」 | **路由切换复现** |
| R2b `673aa35e` | 同 R2a | 同样换路由补跑，且一边写「继承 deep-tier 低档」一边切到别的路由 | **路由切换复现** |

三个子运行同样只 read 了自己那份 packet，模型都是 `openrouter/deepseek/deepseek-v4.1-flash`（会话模型）。

### 结论改写（覆盖上文推理）

- **我当时的根因归属不成立。** 拿同一文本、同一模型盲跑，R1 并没有去 Codex；那条「外部 CLI 还须 `runner.available === true`」被读成了预检条件而不是使用许可。仓库里那次收口方向没错，但不解释这次现象。
- **真正被执行的是那句本地未提交的额度文案**：「额度或容量耗尽正是这种可补跑的失败——换一条已确认可用的模型路由」。它把“额度耗尽”变成可以离开会话模型的理由，2/2 场景都这么做了。
- 它没有点名 codex，所以“会调用到 codex”仍是一次**机制上成立但未直接观测到**的链路：本机已认证路由只有 xai、openrouter、openai-codex，而这个会话跑在 openrouter（用户默认是 xai）——换路由的落点集合里就有 Codex。
- 副作用：R2b 一边换路由一边声称“继承 deep-tier”，说明这句话还能让报告里的模型记录失真。

### 本地未提交改动的处置（已定：方案 A）

安装目录 `~/.pi/agent/git/github.com/allforai/myskills` 有未提交改动（keep-code-simple 与 cross-exam 各一份，从未来过仓库，无 commit/stash/branch）。已备份到 `/tmp/kcs-local-edits/`（patch sha `22f96b4b…`）。其中值得收编的是：复核通道的 git 元数据工具合同、失败通道算未查、派发前后 HEAD/工作区漂移检查、按 receipt 记 requested/resolved、额度≠注册表。**不能收编的是「换一条已确认可用的模型路由」**——它与“只用当前会话模型”直接冲突，已改成：同协议、同路由重试；该路由不可用就把通道标未查并交用户决定（`a430a830`，两份适配同步，契约测试各加一条钉住）。

## 尚未验证

- 真实 Pi 会话里技能被自动加载、用户级 `subagents` 配置（含 `agentOverrides`、`maxThinking`）对档位的实际钳制、真实异步调度；本轮子代理是宿主默认档位，未逐案传档位后缀。
- 全部 5 个场景在两轮间的重复采样稳定性，以及 `cross-exam` 视觉/截图路径与 `meta-skill` 长流程上的连锁影响。
- 契约测试（`shared/keep-code-simple` 14 项、`pi/cross-exam` 7 项、`pi/meta-skill` 8 项）只证明文本边界在，不证明模型会照做；本轮思维测试补的正是这一层，但仍是模拟决策，不代替真机验收。

## 真机验收：未做（2026-09-17 时的状态；2026-09-22 已做，见下一节）

这份记录里的全部证据是冻结的文案契约测试 + 6 个模拟场景 + 宿主侧机制核查；**没有在真实 Pi 会话里跑过一次 `/skill:keep-code-simple`**。这一步没做，原因不是技术上不可行，而是该技能 user-invoked only——模型不能自行启动它，只能由用户敲：

```
重启/重载 Pi          # 安装目录已在 7f277f49
cd /tmp/kcs-acceptance
/skill:keep-code-simple
```

靶子已备好：`/tmp/kcs-acceptance`（git 仓库，`apps/orders` 与 `apps/billing` 各自手写 CSV 转义，`packages/tabular/csv_writer.py` 已是共享实现，正好触发协议里的「先查复用」）。

验收判据（跑完照宿主轨迹核对，不由受测者自报）：

- 派发的 `agent` 只有原生 `scout`/`reviewer`/`oracle`/`delegate`，**0 个** `codex-exec`/`claude-code`/`cursor-agent`；
- `model` 参数为空或只有会话模型自身的 `provider/id:<level>` 后缀，没有别的 provider 或模型家族；
- `context:"fresh"`、cwd 是被审项目；
- 单顶层 workflow、`async:true`、内部 `runs.all`；
- 只写 `<靶子>/docs/keep-code-simple/<日期>-<slug>/`，不碰被审源码；
- 报告「派发」节的 requested/resolved 是 inherited/receipt 型号或 unknown，没有「跨模型复核」。

在真机验收完成前，本问题的状态是**已改完、未验收**：能说的是三处授权已变成禁令、契约测试全绿、安装目录与仓库逐字节一致；不能说的是“真机上再也不会出现 codex”。

## 真机验收：已做（2026-09-22）

靶子从 `/tmp/kcs-acceptance` 复制到 `~/workspace/kcs-acceptance-keep/kcs-acceptance`（同一 commit `b01763e`），注册进 Orca，通过 Orca 在该目录起一个真实 Pi 会话（pi 0.86.1；安装目录 `~/.pi/agent/git/github.com/allforai/myskills` 在 `933dfdab`，无未提交改动），发送 `/skill:keep-code-simple`。判据按上一节运行前写下的那份，逐条按宿主轨迹与产出核对，不采信受测者自报：

| 判据 | 证据 | 结论 |
|---|---|---|
| 只派原生 agent，0 个外部 CLI | 轨迹里的角色只有 `scout` / `reviewer` / `oracle`；`codex-exec` / `claude-code` / `cursor-agent` 一次未出现 | 过 |
| 不换 provider / 模型家族 | 三个子代理全是 `grok-4.6`，与 `~/.pi/agent/settings.json` 的 `defaultModel: grok-4.6` 一致；差别只在思考等级（scout low，reviewer / oracle high） | 过 |
| 单顶层 workflow、并发 | `async workflow: 4ac21fb4`，3 active，后台运行 | 过 |
| 只写 `docs/keep-code-simple/<日期>-<slug>/`，不碰源码 | 靶子里唯一变化是新增 `docs/keep-code-simple/2026-09-22-csv-exporters/recommendations.md`（65 行）；`apps/`、`packages/`、`README.md` 无 diff | 过 |
| 协议的「先查复用」被触发 | 产出找到 `packages/tabular/csv_writer.py`，推荐「保留手写与共享 writer」，并拒绝「删共享 writer」（README 承诺另有消费者，本树无调用 ≠ 全局无人用） | 过 |

至此本问题的状态从「已改完、未验收」变为「已验收」：真机上没有出现 codex，也没有换路由。验收后终端已关闭、产出已删除、靶子已从 Orca 注销；本节是唯一留存的证据。

