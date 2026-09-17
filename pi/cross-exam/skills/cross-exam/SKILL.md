---
name: cross-exam
description: >
  Evidence-backed completion audit of a delivery, including rule consistency and user-declared journeys;
  records, never fixes. User-invoked only via /skill:cross-exam; never invoke it
  yourself. Requires independent fresh-context subagents; refuse rather than self-audit.
---

# cross-exam — Pi Adapter

用户显式调用 `/skill:cross-exam [target]` 才运行。空参数进入定靶。模型不得自行启动。
这是完成度盘问，不是 keep-code-simple，也不是 product-review。不要读或执行 `product-review.md`。

**只记账不修。只在有人在场时运行。无人值守或被自治流程调用时直接拒绝。**

## 0. 能力前置门（先于一切，硬拒绝）

cross-exam 的诚实性建立在「每问一个 fresh-context 实测官独立取证」上。
Pi 能发现 skill **不等于**有子代理。只使用当前已加载的能力，**不自动安装扩展**，不启动另一 harness。

1. 没有 `subagent` 工具 → 当场停。
2. 有则先 `subagent({action:"list", capabilities:true})`。只认 executable、非 disabled 的**原生 Pi** 代理，
   且它必须能跑本次取证（读项目、写证据目录、按需起服务/用浏览器），能按看图预算取副本（跑 `view_copy.py`、
   用 Pillow 取样），并支持 `context:"fresh"` 或等价的不继承盘问官对话。
   **不要用外部 CLI runner**（`codex-exec`、`claude-code`、`cursor-agent`）：它们启动另一个 harness 和另一套模型，
   不是本次会话模型，也不归本宿主管理。`runner.available === true` 只说明命令在 PATH 上，不构成使用理由，
   也不是已登录或可启动的证明；外部 CLI 一律不算前置门通过。
3. 派不出独立 fresh-context 子代理 → 告诉用户：
   「这里跑不了 cross-exam：它必须靠独立实测官取证，本环境没有可用子代理；请安装并加载 pi-subagents 或换环境。我不会降级成自审，也不会自动装扩展。」
   然后结束。不要定靶、不要摆面、不要用主会话冒充实测官。

结构化提问有没有选择器**不是**前置门。缺了就用纯文本问。

## Canonical Source

包根目录是本文件上两级（含 `package.json` 的 `pi/cross-exam/`）。按顺序解析 `$ROOT`：

1. `<package-root>/../../codex/cross-exam-skill/`（myskills 源码布局）
2. `<package-root>/canonical/`（可选独立快照）

两者都不存在则停止，说明需要从 myskills 源码安装或放入 `canonical/`。不要猜路径。

`$ROOT` 是协议资源根，不是被测项目 cwd。镜头、prompt、schema、脚本、visual、engine 都从 `$ROOT` 读：

- `$ROOT/lenses.md`
- `$ROOT/prompts/{prober,census,sites,sweep}.md`
- `$ROOT/schemas.md`
- `$ROOT/rule-consistency.md`、`$ROOT/prompts/rules.md`（定靶后、基线冻结前必读）
- `$ROOT/scripts/ledger_store.py`（有则用来加锁写 ledger）
- `$ROOT/scripts/render_report.py`
- `$ROOT/visual/visual-acceptance.md`（用户选了视觉 facet 之后；「看图预算」一节）
- `$ROOT/visual/view_copy.py`（`MAX_EDGE` / `MAX_BYTES`，取 `view/` 副本）
- `$ROOT/visual/validation.py`（`MAX_BATCH_IMAGES`）

读完 `$ROOT/SKILL.md` 从 `# cross-exam — 实证完成度盘问` 起的全文（跳过文件开头的 package router），执行该协议，并只应用下列 Pi 替换。不要继续 router 里的 product-review / keep-code-simple 分支。

## Required Pi Substitutions

### 1. 派发

主会话是盘问官：出牌、对话、解读证据、裁决、写 ledger、跑 `render_report.py`。
实测官 / 普查官 / 规则审查官 / 枚举官 / 扫全实测官 / 视觉 reviewer / 复核官都是 **fresh-context 子代理**。
期望隔离：派发输入只含协议规定的 prompt 全文 + 输入 JSON；**不夹带怀疑、预期答案、oracle、waypoints**。

每当 canonical 写 `spawn_agent` / `wait_agent` / `Agent(...)` / `fork_turns:"none"`：

- 用 **一个顶层** `subagent` 调用，`workflowScript`、`async:true`、明确 `cwd`（被测项目）、`context:"fresh"`。
- 普查官、规则审查官、复核官、视觉 reviewer：一次一个 `runs.run`。
- 规则审查官专用 `prompts/rules.md`，可读全部规则快照（对账例外），但不接收预期冲突；这些材料不传给运行实测官。
- 互不依赖的实测官（扫全扇出、并行旅程）用同一工作流里的 `runs.all`。`runs.all` 返回有序数组。
- **不要用 git worktree 隔离实测官。** 他们必须打同一棵被测树、同一本地/开发实例。隔离的是对话上下文，不是工作区。同一模拟器/设备一次只由一个实测官操作。
- 子代理只许写派发给它的 `evidence_dir`（及该问约定的截图/视觉批次目录）。禁止改产品源码，禁止写 `ledger.json` 或 `completion-report.md`。
- **模型只用当前会话模型。** 缺省不传 `model`，子代理继承会话模型；不传其他 provider 或模型家族的字面量，
  不启动外部 CLI 来换模型。要控制成本与能力只调**思考等级**：省略时继承 agent 默认档位，需要显式分档时
  只传会话模型自己的 `provider/id:<level>` 后缀（`off/minimal/low/medium/high/xhigh/max`），等级不超宿主与用户配置的上限。
  派发时读 ledger `model_policy` 的档位，不读记忆。思考等级同样是证据属性：降档只发生 0b 允许的角色上，且落在 ledger 里。
- 异步运行已有原生完成通知：继续独立的盘问官工作或归还控制，通知到达再合并。不轮询、不 sleep、不仅为了等待调用 `bg_wait`。
- 派发开始后的基础设施失败：停止该路径，记录精确错误和 run/cwd/ref/工作区状态。只能按协议重派一次实测官。不切到 CLI、`pi -ne`、前台自审或其他执行模式。
- `agent_task` 记 Pi 子代理的 run/child id（或宿主给出的 session/output 引用），不是 `spawn_agent` id。

### 2. 模型：继承会话模型，只调思考等级

canonical《模型：默认全部继承会话模型》在 Pi 下**加强**为：模型不换，只用思考等级分档。
跨平台双审的外部 reviewer 在 Pi 不适用——不启动另一个 harness；第二审用原生 Pi 子代理在会话模型下的独立 fresh 上下文。

- 定靶 0b 不问“用哪个模型”，改问“取证用哪个思考档”：先读当前会话模型与可用的思考等级
  （`subagent` 的 `action:"models"` / 当前会话配置），找出会话当前档位的下一级。选项仍写具体字面量：
  - A「证据优先」：全部继承会话模型与默认档位；`model_policy.observation` 记 `"session"`。
  - B「成本优先」：取证类角色（实测官、枚举官、扫全实测官）用同一会话模型的低一档思考，例如
    `session:<level>`；普查官、规则审查官、视觉 reviewer、复核官仍用会话模型与默认/高档，从不降。
- 推荐规则与 canonical 相同（用户提过成本、或走扫全模式→推荐 B；旅程要过弹窗/多标签/OAuth 这类难走界面→推荐 A，
  并说明降档实测官更容易残缺重派）。只推荐“会话当前档位的下一级”，不推荐最低档，也不推荐另一个模型。
- `model_policy` 照 canonical 写：`judgment` 固定 `"session"`；`observation` 填上面选的档位；
  `confirmed_by_user` / `confirmed_at` / `recommended` / `history[]` 不变。
- **每次派发落盘实际档位**：`entries[].agent_model`、`census_model`、`patterns[].enumerator_model` 写
  会话模型字面量加 `(session, thinking=<level>)`；拿不到宿主 metadata/receipt 就写未知，不能自报当已确认。
- 残缺重派回到会话默认档位：首派降过档时，重派不传后缀；同一问两次派发档位不同照样落盘（`agent_model` 记重派那次，
  首派降过档时再写 `first_agent_model`）。
- 视觉与截图外发边界里的“第二平台 reviewer”在 Pi 一律读作：同一会话模型的原生 fresh-context reviewer；
  不新增外部 receive 方，不把截图发给另一个 harness。

### 3. 提问

Pi 没有 `AskUserQuestion`。牌、定面勾选、旅程确认、扫全模板过目、安全确认一律纯文本。
一次问一件阻塞的事。不要发明答案。

### 4. 台账与报告

新 run 写 `ledger_version: 3` 并初始化 `rule_consistency`；执行 canonical §0c 规则对比，候选只交用户澄清，不改产品或扩大范围。有 `ledger_store.py` 就用它加锁写；没有则直接写 `docs/cross-exam/<日期>-<目标slug>/ledger.json`，仍须每问立刻落盘。
报告只由 `python3 $ROOT/scripts/render_report.py docs/cross-exam/<run>/` 渲染。禁止口述生成完成度报告。

### 5. 看图预算与外发边界

canonical 的「看图预算」在 Pi 上是硬约束，不是建议：Pi 把图片作为附件直接内联进工具结果，一张超预算的
截图会让整轮调用作废、token 照扣。盘问官、实测官、视觉 reviewer 一视同仁。

- **开图前先看尺寸**（`ls -l` 或 Pillow size）。超过 `$ROOT/visual/view_copy.py` 的 `MAX_EDGE` / `MAX_BYTES`
  就跑它取副本到原图旁的 `view/`，先开 overview、要读局部再开切片，够用就停。原图不动；`view/` 副本不算证据，
  不进 manifest `images`、不进 `evidence_files`、不列进 `inspected_images`。
- **不要用 `read` 直接开超预算原图或整页图**（Pi 的 `read` 会把它作为附件内联进上下文）。截图工具有 `filename`
  选项就先落盘，再按预算开副本。一张图报 payload 类错误不重试同一张——尺寸决定的，第二次结果一样。
- **经副本看的原图照列 `inspected_images`**，另记 `viewed_via: {原图: [副本相对路径…]}`（相对 run/evidence，
  与 `images` 键同一坐标系）。「看过」口径：`read` 作为图像打开 / 截图工具内联返回 / 外部 CLI 附图调用算；
  `ls`、算摘要、Pillow 读尺寸不算。色值 / 字号 / 间距这类精确数值用 Pillow 从**原图**取样（坐标加取到的值写进
  observation），副本上的颜色不作数。
- **一批也有上限**：一次 reviewer 派发（一个原生 Pi 子代理）打开的原图加基线参考图不超过 `MAX_BATCH_IMAGES`
  （`$ROOT/visual/validation.py`），超限 entry 拒渲。一组自己就超上限的，回矩阵拆 state 或抽象，不拆组也不硬派。
- **截图外发边界**：只进会话模型和定靶时冻结的第二平台 reviewer；不经任何第三方网关（`ask_model` 一类）或
  未冻结模型外发。Pi 没有外部平台，也没冻结第二端时就只进会话模型（§2：第二平台 reviewer 一律读作同一会话模型的原生
  fresh-context reviewer）。第二端失败走 `degradation_ref`，不找替身。用户要对本 run 放开，先在定靶安全确认里问清，
  写 ledger 顶层 `image_export: {targets, confirmed_by_user 原话, confirmed_at}` 再发；含真实数据的图外发不在选项里。
- **采集侧从源头省**：所有截图设备像素比设 1（高分屏视口图也是），缺省拍视口，只在状态要求整页时拍 `full_page`；
  设不了像素比就滚一屏拍一张（文件名带段号）。细节以 `$ROOT/visual/visual-acceptance.md` 为准。

### 6. 后续用户步骤

报告呈完后可以提：产品层面用 Claude/Codex 的 `/product-review`（Pi 尚未移植）。不要在本技能里启动它。
keep-code-simple 是本包另一个入口，与完成度盘问分开调用。
