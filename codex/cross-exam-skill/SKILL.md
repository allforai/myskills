---
name: cross-exam
description: Package with two explicit commands. cross-exam — evidence-backed completion cross-examination, including user-declared journeys walked end-to-end. product-review — product-thinking critique, commercial UI/interaction, and competitor borrow notes, advice only. Neither is automatic. If the user named product-review, read product-review.md and stop; do not run this completion protocol. cross-exam asks "is it really done", product-review asks "is it good for the user"; the usual order is cross-exam first.
---

# Package router

This directory is one Codex install (`cross-exam`) with two protocols.

- User named **product-review** → read `./product-review.md` only. Stop.
- User named **cross-exam** → continue this file.

Do not mix ledgers, verdicts, or loops.

# cross-exam — 实证完成度盘问

`$ROOT` = this skill directory。镜头：`$ROOT/lenses.md`；
实测官 / 普查官 / 枚举官 / 扫全 prompt：`$ROOT/prompts/{prober,census,sites,sweep}.md`；schema：`$ROOT/schemas.md`；
台账原子写入/锁：`$ROOT/scripts/ledger_store.py`；报告：`$ROOT/scripts/render_report.py`。

**不变式：**
- **只记账不修** — 缺口带证据入台账，修复是用户另一个决定；盘问官没有"把问题修掉"的动机。
- **只在有人在场时运行** — 无人值守不盘；被别的流程在自治阶段调用时直接拒绝。
- **结论必须来自独立采集的证据** — 每条裁决链到实测官落盘的证据文件；口头裁决会被渲染器拒收。
- **实测官独立不可降级——缺了就拒跑，绝不自审。** cross-exam 的诚实性完全建立在"每问一个
  fresh-context 实测官独立取证"上。若本 harness 派不出独立子 agent（如 Codex 未开 `multi_agent`，
  或任何无并发子 agent 的环境），**当场停，明说"这里跑不了 cross-exam"，绝不降级成"盘问官自己
  检查自己的交付"**。自审恰恰是 cross-exam 存在要抓的那种假完成——一个没有独立实测官的 cross-exam，
  看起来盘过了、实际什么都没验，是最坏的假成功。**宁可说跑不了，不可假装盘过。**
- **通用** — 零项目痕迹、零技术栈硬编码；流水线台账（如 superstorm registry）只是可选数据源。
- **报告只由 `render_report.py` 渲染** — 禁止口述生成完成度报告。

## 两个角色，硬分离

- **盘问官（你，主会话）**：扫泄漏点、出问题牌、对话、解读证据、下裁决、记台账。
  你持有全部上下文与怀疑。
- **实测官（每问一个 fresh-context 子 agent）**：只拿到 prober.md 的输入合同，
  看不到你的怀疑与对话史。带回原始观察，不下结论。
  **期望隔离是本技能的诚实性根基：绝不在派发输入里夹带你预期的答案。**

## 模型：默认全部继承会话模型

**`spawn_agent` 默认不传 `model`，让子 agent 继承会话模型。** 实测官、普查官、枚举官、视觉 reviewer、复核官都是。
理由：实测官干的是整条链里最难的 agentic 活（起服务、造前置、走陌生界面、识别拦截层、自选旅程路径），
而且它的产出盘问官无法复核，坏了只能裁 unprovable 或误判；普查官漏一面就是永久盲区；复核官是对盘问官
动机的制衡。把最难、最不可逆的活交给比会话弱的模型，省的是钱，赔的是证据。技能不写死任何模型字面量：
写死的那一刻，它就比下一代会话模型弱一档。

**降档只是可选的成本控制，且只许降取证类角色；模型名由用户在定靶时给，落在 ledger 顶层 `model_policy`，
不落在技能里。** 用户明确要省成本时，只有"产出原始观察、盘问官自己会
解读"的角色（实测官、枚举官）可以用定靶时探测到的更便宜模型；产出盘问官无法复核的判断的角色（普查官、
视觉 reviewer）和作者自审时的复核官永远继承会话模型。哪怕降了档，也要遵守：
- **重派回到会话模型。** 残缺重派时若首派用的是降档模型，重派不传 `model`；首派已是会话模型则原样重派。
  同一问两次派发用了不同模型这件事本身要落盘（`agent_model` 记重派那次的）。
- **每次派发都落盘用了什么模型**：`entries[].agent_model`（实测官或视觉 reviewer 的字面量，继承会话时写
  会话模型名加 `(session)`）、顶层 `census_model`、`patterns[].enumerator_model`。事后核对"这条裁决的证据是
  谁取的"要能一眼看到。本版 `spawn_agent` 若不暴露 `model` 参数，一律记会话模型名加 `(session)`。
- **派发时读 `model_policy`，不读记忆里的模型名。** `model_policy.observation` 是字面量就给实测官、枚举官、扫全
  实测官传它；是 `"session"` 或整个键不存在就不传。普查官、视觉 reviewer、复核官从不读这个键。
- 会话模型是什么就用什么裁决，技能不猜用户能拿到哪些模型，也不提醒换模型。
- 跨平台双审的外部 reviewer 用对方平台**当时可用的最强模型**（定靶时用 `--help` / 模型列表探测），
  字面量记进 `agent_model`；不在技能里写死。

## 0. 定靶（intake）

0. **能力前置门（先于一切，硬拒绝）：** 确认本 harness 能派出**独立的 fresh-context 子 agent**
   （Codex: `spawn_agent`/`wait_agent`; both tools must be available）。**派不出 → 当场停，告诉用户"这里跑不了 cross-exam：它必须靠
   独立实测官取证，本环境没有；请开多智能体或换环境，我不会降级成自审"，然后结束。** 不要继续定靶、
   不要摆面、不要用主会话冒充实测官。（结构化提问工具有没有选择器**不是**前置门——那只是
   问法，退成纯文本问答不影响方法；能力门只卡"独立取证"这一件事。）
0b. **模型策略（一问，默认不省）**：把本 harness 能派的模型列表摆给用户（Claude Code：Agent 工具 `model` 的
   枚举；Codex：`codex --help` / 模型列表），问一句"取证类角色（实测官、枚举官）要不要用更便宜的模型"，第一个
   选项是"全部继承会话模型"。用户选了字面量就写 ledger 顶层 `model_policy`（`observation` 字面量、`judgment`
   固定 `"session"`、`confirmed_by_user` 用户原话、`confirmed_at`）；选默认则不写这个键。用户没提省钱你不主动
   劝省，也不替用户选。报告总览会点明本 run 取证用了哪个模型、谁在什么时候确认的；续盘沿用旧 ledger 的策略，
   用户改口时把旧值推进 `model_policy.history[]` 再改键并更新原话与时间——前半段证据是谁取的不能从总览消失。
1. 确认被测对象与访问方式（怎么跑起来：web/cli/api？入口？）。
2. **需求基准探测**（依次）：superstorm overview registry（R-*，在
   `docs/superpowers/specs/*-overview.md` 的 registry 标记内）→ `docs/superpowers/specs/`
   下相关 spec → README → 问用户 → **无基准模式**（需求覆盖/跑偏两镜头关闭，
   报告声明，只开集成缝隙+细节质量+契约 census+旅程）。**找到基准就把需求逐条落进 ledger
   顶层 `requirements[]`**（`id` + 一句原文）：这是需求侧的点名册，渲染器据此出"需求覆盖"专节；
   没有它，一条需求只要没进 facet 表就整条蒸发，连"未盘问声明"都进不去。无基准模式不写。
3. 环境能力探测：能否真跑起来；有无浏览器自动化（截图能力）。缺截图能力时
   UI 类问题只能裁"无法自证"，起手就告诉用户。
4. **安全确认（必须）**：实测会造真实调用（退款、删除这类）。与用户确认靶子是
   本地/开发实例后才放开手；生产系统一律拒绝盘问。**同一次确认里问清开发实例的后端是什么**：真实服务、
   mock（MSW / json-server / miragejs / 显式 stub 开关）还是混合，连同普查官报的 `mock_layers` 写进 ledger 顶层
   `target_backend`。安全规则把探针推向开发环境，而 mock 正好住在那里——请求返回 200 和真的一模一样；
   经 mock 层取到的 runtime 证据最高裁 unprovable，渲染器会拒收这种 done。
5. **run 目录**：`docs/cross-exam/<日期>-<目标slug>/`。检测到未收敛 run
   （`ledger.json` 存在且 `completion-report.md` 不存在）→ 问用户续接还是新开；
   续接时读旧 ledger 的 `open_threads` 作为起手牌候选。
6. 使用 `ledger_store.py` 加锁并初始化/载入 `ledger.json`（schema 见 `$ROOT/schemas.md`），新 run 写 `ledger_version: 2`。

## 1. 定面（facet map）

**UI 目标**：自动列出可选 `visual-acceptance` facet。用户选中后读取
`$ROOT/visual/visual-acceptance.md`，执行实图采集、逐类基线确认、全矩阵和独立视觉评审。
该模式的视觉裁决必须通过 renderer 的视觉证据校验；不能降级为源码通过。
用户未选择则记录未验收。SwiftUI 规则内置，按需读取，无需另装 Skill。

**先独立 census 播种，再由你摆面——别让"你想到要盘什么"成为覆盖上限。** facet 表最危险的
盲区是"你根本没想到要盘的那块"：盘问官持怀疑但也带盲区，只凭 hunch + 读代码摆面，交付里整类
问题会因"没进 facet 表"而永远盘不到（实战教训：一整族假成功操作，只因盘问官碰巧把其中一个做成
了牌才被抓出，那类本身从没有独立 facet）。所以定面分两步：
1. **独立 surface 枚举**：派一个 fresh-context agent（`spawn_agent`，不传 `model`），prompt = `$ROOT/prompts/census.md` 全文 +
   输入 JSON（target / scope）。它用覆盖法（不是 hunch）从代码拓扑穷举交付的操作面——每个用户可触发
   操作 / 每个端点 / 每个 store 方法 / 每个契约（RPC/handler）。它不看你的怀疑，只产出"这交付一共
   有哪些面 + 每个面的入口"，外加零调用点的 `dead_contracts`。死端点/契约 census（见 lenses.md）
   是最省的播种法。不要即兴写普查 prompt：措辞变了，覆盖面就变了。**普查官返回后把 `surfaces`
   原样写进 ledger 顶层 `surfaces[]`**（`dead_contracts` 也各作一行，`entry` 用它的 `defined_at`），
   不改名、不合并、不删：这是操作面的分母，渲染器据此算"操作面 K 个，裁决触及 T 个，未触及逐个
   点名"。分母不入账，覆盖就没有数，只剩盘问官一句"盘过了"。UI 目标的 `locales`、`axis_support`、`translation_keys`、
   `dark_variant_gaps` 同样原样入账（顶层同名键）：`translation_keys.missing` 或 `dark_variant_gaps` 非空时按
   "孤例还是一类"直接建 pattern（hypothesis "某语言翻译回落" / "深色模式资源半做"，sites = 缺失 key / 无深色
   变体的资源），不等哪张牌碰巧撞上；语言、深浅色、字号、方向要不要验收，由用户在视觉验收的 environment 类
   逐轴确认，放弃的值记 `declined` 带原话，报告列"未验收"，不进计数（见 visual-acceptance.md）。
2. **合并 + 摆面**：把 census 面与你自己想到的面合并去重，**标出"census 有、你没想到"的面**（那
   往往正是盲区）。facet 表每面两个槽位必填：`surface_ids`（它包含的 census 面 id）与
   `requirement_refs`（它承接的需求 id）——粒度随你摆，但每个 census 面必须落在至少一个 facet 里，
   报告才能对每个面说"K 个操作面触及了 T 个"；粒度再粗也藏不住没盘过的操作面。
   **再反向对账需求基准**：`requirements[]` 每条至少落一个 facet；census 一个 surface 都对不上（或只
   对上 `dead_contracts`）的需求**单独成面并标"需求有、census 无"**（该需求的类别出现在 census `could_not`
   里时改标"类别未枚举"——"没枚举到"和"枚举了没有"是两种强度），与"census 有、你没想到"并列摆给
   用户——facet 表有两个盲区方向，census 只补代码侧那一个，需求侧这一步没人替你做。
   **横切面**（身份边界、角色权限、离线与重试、并发、数据生命周期，见 lenses.md 横切轴）不住在任何一个
   入口里，census 结构上列不出它；由你从需求与代码观察摆出，`surface_ids` 写它横跨的全部 census 面。然后一次只问用户一个选择，确定盘哪些、先盘哪个。

没选的面在 ledger 里记 `status: "not_examined"`，**并写 `risk`**（`level` high|medium|low +
`why` 一句：需求引用的分量 + 若真坏的破坏面），让人清楚把什么留在了桌上——渲染器按 risk 排序列进
"未盘问声明"，绝不算进完成度。盘问官==交付作者时，ledger 顶层写 `examiner_is_author: true`，
渲染器会在总览点明。**facet 的"盘过"由渲染器按被采信 entry 推导，不看你手写的 `status`**：一问
都没落账的面，写了 examined 也进"未盘问声明"。

## 1b. 旅程采集（定面之后，盘问循环之前）

旅程 = 用户声明的意图基线：`who / circumstance / progress` 三元组（与 product-review 的 job 同格式）
加 oracle。它回答"这份工作在这个交付里走不走得通"，是 product-review "在不在、走不走得完"两问的
独立取证来源。

1. **整理候选**：把 census 的操作面按"入口 → 能推进到的终态"归成候选旅程，加上需求基准里的任务
   （registry、spec、README；`.allforai/product-map/task-inventory.json` 存在也读，它只是可选数据源）。
   每条候选写成三元组草稿。**不另派 agent 读代码，也不凭印象读代码定候选**——census 已经用覆盖法
   列过入口了。census 失败（ledger 顶层 `census: "failed"`）时，候选只来自需求基准与用户补充，
   并在报告里声明旅程候选未经 census 播种。
2. **摆给用户**：一次只问用户一个选择，逐条确认要盘的候选；用户永远可以补自己的旅程。零选择不阻塞：
   ledger 写 `journeys: []`，报告声明"无旅程声明"。
3. **改写读回**：每条选中的旅程改写成三元组加 oracle（`done_looks_like` + `stuck_looks_like`），读
   回用户确认。一轮改写后仍无 `who` 或 `progress` 的不是旅程——说明缺哪部分，用户补一次，仍缺就
   不收。`stuck_looks_like` 空的同样退回补一次："没报错"不是 oracle，要写出卡死长什么样。
4. **落盘**：确认的旅程写入 `journeys[]`，`status: not_examined`，带 `risk`（这份工作的分量 + 若真走
   不通的破坏面）。未选的候选不入台账。`step_budget` 默认 15，按旅程长度调。

## 2. 盘问循环（每轮一个面）

```
扫泄漏点（读 lenses.md，浅而快）→ 出 3 张问题牌 → 用户选一张（或自己出题）
  → 派实测官（fresh context）→ 带回证据 → 你对证据下裁决 → 入台账 → 下一轮
```

**两种模式，按目标选。** 上面的循环是**深挖模式**（Socratic 牌）：逐面出牌、用户选、单实测官
深证——答"这条线成不成立"。当目标是"消灭某一类 / 交付完整性"时，先切**扫全模式（census
sweep）**：并行扇出覆盖式实测官把整个 surface 扫一遍（每个操作/端点逐条查"契约是否兑现"），拿
到全集后再对高风险线回到深挖。**深挖答不了"我们有没有到处都看过"——那是扫全模式的活；只做深挖
等于用 3 张牌去覆盖一整个交付。** 深挖中途抓到"一类的实例"时也会升级——见下面"孤例还是一类"。

**扫全实测官的输入不即兴。** 一面一个 fresh-context 实测官（`model` 按 `model_policy`），prompt = prober.md 全文 +
`$ROOT/prompts/sweep.md` 全文 + 输入 JSON；`question` 与 `states_to_capture` 只许用 sweep.md 的固定
模板填入该面的名字与入口——模板按面的种类分三个变体（界面操作 / 命令与接口 / 后台任务与消费者），
你只做"选哪个变体"这一件事，不润色措辞。扇出前把填好的模板整句用 AskUserQuestion 给用户过目一次——这是扫全模式的
"选牌"——然后原文一字不改落进每条 entry 的 `q`，`surfaces` 写该面 id。理由与普查官相同：深挖里一张
牌措辞差一点只影响一问，扫全把同一句盖 N 个面，模板漏一个观察口，N 个面一起漏，而且没有用户逐张
选牌那道复核。

**旅程轮（用户选中一条旅程时）**：不出三张牌，问题固定是"`<id>` 走得通吗？"。

- **派实测官**：输入 JSON 加 `journey` 块——只含 `goal`（三元组拼成一句话）、`preconditions`、
  `step_budget`；`states_to_capture` 写"起点"、"终态"。**oracle 和 waypoints 都绝不进输入**：
  探针不知道"做成"长什么样，也不知道你点名了哪些必经点，自选路径，到了就到了，到不了就如实记——
  这是旅程版的期望隔离。waypoints 是给你事后对 `steps[]` 查的：探针若被告知必经点就会主动绕过去
  经过它，产品允许跳过该点这件事就永远测不出来。
- **收证据**：把 `steps[]` 和终态截图给用户看。
- **裁决**（对着 `journeys[].oracle`）：
  `done` = `done_looks_like` 全部命中、`stuck_looks_like` 无一命中、每个 waypoint 都在某步
  `observed` 或截图里出现过；
  `gap` = 任一 `stuck_looks_like` 命中，或探针 `could_not` 含 `budget_exhausted`，或任一步 `stuck`；
  必填 `stuck_kind`（no_entry 无入口 / not_found 找不到 / misleading 误导 / no_feedback 无反馈 /
  no_recovery 无恢复路径 / broken 系统报错）与 severity；
  `drift` = 终态满足 `done_looks_like` 但 `steps[]` 从未经过某个 waypoint——产品允许用户跳过你点名
  的必经点（如未经支付确认页就下了单），必填 `missed_waypoints`；
  `unprovable` = 前置条件造不出来，或探针因环境原因 `could_not`（起不来、缺依赖、缺浏览器）。
  预算用尽不是 unprovable：预算内到不了进展是产品的问题。
- **落账**：entry 带 `journey`、`steps`、`terminal_state`；`journeys[].entry_q` 指到该 entry 的 `q`，
  `status` 改 `examined`。
- **扫全模式下**：所有 `not_examined` 旅程并行扇出，一条旅程一个 fresh-context 实测官（同样按 `model_policy`），收齐后逐条裁决。
- **发散与 bias-guard 照旧**：旅程 gap 后下一轮从卡死点纵向出牌进 `open_threads`；多条旅程在同一种
  `stuck_kind` 卡死，走"孤例还是一类"建 pattern；盘问官==交付作者时旅程 gap 从严。

**深挖轮（按面出牌）的通用规则：**

- **问题牌**：遵守 lenses.md 的 4 条硬约束（挂泄漏点、可实测、覆盖不同疑点、
  UI 牌注明状态清单）。牌一次呈现一组，用户永远可以自己出题。
- **派实测官**：`spawn_agent` with `fork_turns:"none"`（`model` 按 `model_policy`，缺省不传）, followed by `wait_agent`，prompt = `$ROOT/prompts/prober.md`
  全文 + 输入 JSON（question / target / states_to_capture / evidence_dir /
  可选 context_paths——只传路径不传你的解读）。**不夹带怀疑。需求基准文件（spec / registry /
  README 的需求段）不进 context_paths：它写着预期答案。** 对账类问题例外，且只传对账所需的那一段。
- **收证据**：把关键观察和截图路径给用户看，再对照需求基准下裁决。实测官返回的 `incidental_observations`
  （取证途中顺带看到、与本问无关的事）不进本问裁决，逐条变成牌候选写进 `open_threads`（q 写成可实测的问题，
  leak_point 写实测官的原话）——强实测官最值钱的产出常常是它没被问到的那一眼，别让它蒸发。
- **裁决四种**：`done` 实证完成 / `gap` 缺口 / `drift` 跑偏 / `unprovable` 无法自证
  （需真设备/人工，如实挂账不猜）。`gap|drift` 定 severity（high|medium|low，
  依据：需求引用的分量 + 实测后果的破坏面）。**问题问的是运行时结果**（服务端收没收到、界面变没变、
  数据落没落）**而证据只有代码摘录时，最高裁 `unprovable`**，不裁 `done`：链路在代码里接好了不等于
  它跑通了。报告把实证完成按介质分列（运行时 / 代码 / 台账），读者要能一眼分辨这两种证据强度。
- **自审 bias-guard（盘问官==交付作者时必开）**：取证独立 ≠ 裁决独立。作者给自己的活定 severity
  有往轻里判的动机。此时 `gap` 默认从严——把 gap 降成 low 或判 done，需要**额外独立证据**（另一
  个 fresh agent 复核——不传 `model`，继承会话模型，制衡者不能比盘问官弱；或明确的"生产不可达"实证），不能只凭盘问官一句"影响不大"。
- **每问立刻落盘 ledger.json**（中断不丢），entry 按 schemas.md。entry 必写 `surfaces[]`（这问的证据
  实际触及了 `surfaces[]` 里的哪些面——渲染器只认登记过的 id，没写的逐条点名）与 `requirement_refs[]`
  （引用了 `requirements[]` 的哪些条）。这两个槽位是覆盖分子；没有它们，分母白记。**v2 每条 entry 另必写**
  `probed_at`、`states_to_capture`（派发时要的状态清单原样）、`agent_task`（Codex 记 `spawn_agent` 返回的 agent id）；
  runtime 介质再写 `served_by`（实测官带回的请求去向与 mock 层）。这些不是文书：渲染器用 transcript 核对证据文件
  是不是实测官写的，用状态数核对有没有少截，用 mock 层拒收假 done。
- **弃牌不蒸发**：每轮发牌后，未被选中的牌**立即**记入 ledger 的 `open_threads`
  （q/facet/leak_point）；某线后来被实测则移入 entries 并从 open_threads 删除。
  报告会把它们渲染成"未拉的线"，续盘从这里接手。**gap 落账后用户随即喊停**：把本该下一轮
  纵向发散的牌（顺这条线追后果）也记入 open_threads，否则续盘时这条线断在缺口处。
- **孤例还是一类（每条 `gap|drift` 落账时必答）**：这个缺口是这一处独有，还是某个结构模式的
  实例（一个契约类缺同一种防护/接线）？判"一类"则**当即两个动作**，不等用户表态：
  ① `ledger.patterns` 建 pattern（`hypothesis` 一句话缺陷模式，schema 见 schemas.md）；
  ② 派**同类位点枚举官**（fresh-context，`model` 按 `model_policy`，只枚举不取证，成本一问一 agent）：prompt =
  `$ROOT/prompts/sites.md` 全文 + 输入 JSON（target / structure / contract），structure 和
  contract 都是中立描述（"接受写请求并持久化的端点" / "重复提交的防护现状"），**绝不夹带首例的
  裁决**（"我们发现 A 坏了，看看别的坏没坏"就是把期望塞给它）——期望隔离在横向扫描时最容易破。
  **"census 已经列过了"不是跳过枚举官的理由**：census 只给位点，枚举官给每个位点的契约现状，两者
  不等价。**用户喊停也先派枚举官再渲染**——它不取证，几秒钟，喊停针对的是实测不是清点。
  枚举回来的位点全部进 pattern 的 `sites`，然后向用户提议：对该类切 mini-census 扫掉，或逐点
  出牌，或先放着。**用户不接也已落账**——渲染器会把未查位点逐个点名，同类嫌疑不许蒸发，也不许
  塞进 open_threads（那是牌的槽位，装不下横跨多面的类假设）。类怀疑的去处只有 patterns。
- **发散（纵横两个方向）**：挖出缺口后，下一轮的牌从缺口**纵向**发散（顺同一条线追后果，
  open_threads 里的旧牌也是候选）；**横向**发散不出牌——走上面"孤例还是一类"的 patterns 路径，
  按名册清点，别靠下一轮碰巧想到。
- **实测官死/超时或返回残缺**：重派一次（基础设施失败不算数）；再失败该问记 `could_not`
  证据（原因文件），裁 `unprovable`，绝不编造。**返回残缺**指旅程 steps 合并了步骤、某步没写 evidence、
  引用的文件不在证据目录、`observed` 写的是结论不是观察——这种返回不落账：你不能替它补文件名、拆步骤、
  改措辞（那是你在替实测官取证），只能按同一输入重派一个 fresh-context 实测官。**重派前先把首派产物整目录挪到
  `evidence/qNN.rejected-1/`**（留痕；不进 ledger，不被任何 entry 引用，渲染器不读它），让 `evidence_dir` 原路径空着
  交给新实测官——残留文件会撞 transcript 核对，也会给第二个实测官示范"不适用"这类写法。最终落账的 entry 写
  `redispatched: 1`（重派次数）；首派用的是降档模型时再写 `first_agent_model`，报告读者一眼看出两次派发换了模型；渲染器不据此改计数。被拒返回里的原始观察
  （如"结算时弹了 OAuth 窗"）可以作为下一轮的牌候选进 `open_threads`，但不作任何裁决依据。**普查官/枚举官无返回**同样重派一次；普查官再失败
  → 只能按自己的面摆表，并在 ledger 顶层记 `census: "failed"`、向用户明说覆盖上限是你的 hunch；
  枚举官再失败 → pattern 写 `enumerated: false`，sites 只留首例，不造哨兵位点。
- **靶子起不来**：本身就是一条集成缝隙 `gap`（"声称可跑，实测失败"，实测官的
  失败输出就是证据），盘问降级为 code/ledger 介质继续。

## 3. 收敛出报告

用户喊停或选中的面盘完 →
`python3 $ROOT/scripts/render_report.py docs/cross-exam/<run>/` →
把 completion-report.md 呈给用户。报告四类裁决计数（普通与旅程分列，实证完成按介质分列）、需求覆盖
（基准 N 条，有裁决 M 条；无裁决的按落在哪个面点名，没落面的单独点名）、逐面"X 问中 Y 问实证通过 ·
操作面 K 个，裁决触及 T 个，未触及逐个点名"、
旅程完成度（每条走通 N 步或卡在第 K 步加卡死类型）、缺口清单（可直接转修复任务）、无法自证清单、未盘问声明、缺陷模式（patterns：每类
"共 N 位点，实证 M，未查 K"，未查位点逐个点名）、未拉的线（open_threads，
续盘接手点）——**没有编造的总百分比**。
