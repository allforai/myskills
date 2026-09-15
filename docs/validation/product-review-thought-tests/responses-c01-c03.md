# C01 / C02 / C03 原始答卷

2026-09-15，第二轮：受测版本为 `claim` 拆分之后的协议（commit `d1abe3f3`）。受试者收到对应平台协议全文与本场景，不含判据。原文保留，未修稿。

## C01（claude 适配 · 与 P01 同一场景重跑）

### 实际动作（伪调用）

1. 人在场已确认（用户显式 `/product-review`）；JOB1 三元组已回读确认。
2. 读 `docs/cross-exam/2026-09-01-export/completion-report.md`：J1=done、gap 空、日期与代码一致 → **前提采信，不重走导出旅程**。
3. 检查 `docs/product-review/2026-09-15-export/recommendations.md` 是否已存在（不存在则新建 run）。
4. 读代码确认四处观察的出处（导航菜单配置、导出调用链、完成后回调、空态/错误态两处渲染）。
5. `WebSearch`「小店主月度对账导出交付会计」竞品如何制造同一进展 —— 本轮未取得可评级来源，故不写竞品条目，也不以 P4 独撑任何条目。
6. 写报告后停止，不 grill、不改源码。

### 报告要点

**Evidence limits**：runs here: 部分（只读代码）· browser: no · WebSearch: yes · 后果：全部 `ui_friction`/`interaction_gap` 一律 `evidence: code-only`，不声称看过界面截图。
**Prior evidence**：J1 (done) 覆盖 JOB1 的「在不在」「走不走得完」；gap 列表为空。
**Decision tree**（全部 `claim: 不够商业级`，`depends_on:` 空）：

- **R1 首次进入无引导** · `interaction_gap` · `adopt` · evidence: 侧栏 14 项菜单配置 + 无任何 onboarding 代码路径（code-only）· tradeoff: 多一条一次性状态与文案要维护，且会挡熟练店主一屏。
- **R2 导出 20 秒无过程反馈** · `ui_friction` · `adopt` · evidence: 导出调用链无 pending/进度态，文件直接出现（code-only）· tradeoff: 要后端暴露阶段或至少加禁用+等待态，改动触及整条导出链。
- **R3 完成后无下一步** · `interaction_gap` · `adopt` · evidence: 下载回调后无后续提示（code-only）· tradeoff: 下一步可能推错动作，需先确认对账后的真实去处。
- **R4 空态与错误态两套说法** · `ui_friction` · `adopt` · evidence: 两处状态渲染各自一套结构与文案（code-only）· tradeoff: 统一状态组件要改两处调用方，短期只换来可预期性。

**不写的东西**：没有 `missing_job`/`broken_path`（J1 已覆盖前提）；没有 `decoration`——只点名一份工作，菜单里另外 13 项很可能服务未点名的工作，且未查明其存在原因，判装饰不成立。

### 面向用户的答复

导出这份工作「在不在、走不走得完」按 2026-09-01 的完成度报告 J1=done 采信，我没有重走。本轮判的是「该不该有」和「商业级够不够」：该不该有没有问题，导出是这份工作的核心进展；商业级不够，四条都落在「陌生人不敢当正经产品」的具体点上。当前无浏览器，四条证据都是代码级，非界面实证。竞品这一趟没拿到 P1–P3 来源，竞品段为空而非凭印象填。报告在 `docs/product-review/2026-09-15-export/recommendations.md`，它是 `$grill-me` 的上游，你可以对它开 grilling；我不会自己开，也不会去改代码。

本轮工具调用：1. Read — pr-packet-C01.md（成功，唯一一次调用）

## C02（claude 适配 · 四条候选的去留）

### 四条候选的去留

- **(a) 删除，不改写。** 只有「观感不精致、配色老气」，过不了「谁/情景/事/观察」四关，也说不出让陌生人不敢当正经产品的**具体那一点**——「说不出具体是哪一点、只剩『体验不好』就删」。
- **(b) 保留 → R1，`ui_friction`，`claim: 进展受阻`，adopt。** J1 已判 done，所以不能写 `missing_job`/`broken_path`（「只用于没有 `J` 判定覆盖的工作」）。入口存在但每月必做的主线唯一路径埋在第三层，属于进展「变难」。
- **(c) 保留 → R2，`interaction_gap`，`claim: 不够商业级`，adopt。** 具体那一点是「核心动作有没有过程反馈；完成后有没有下一步」都没有；用 Nielsen 的 visibility of system status 命名，只为 grill 时有共同语言。
- **(d) 删除。** 「『这类产品都有 X』是惯例，不是缺口」；attractive 缺失「只在竞品对同一份工作做到时才是 `borrow_*`」，我没核对过，也无人需要它的观察。不进 Out of scope（我并未在别处真看到）。

### 报告要点

- Jobs in scope：JOB1 · 前提 J1 (done)。
- Prior evidence：completion-report — J1 (done) 覆盖 JOB1 前提。
- Inspection plan：无浏览器，只读导出相关代码——菜单/路由声明与导出成功分支，判入口层级与完成反馈。
- **R1 — 导出入口只存在于设置第三层**｜job JOB1｜kind `ui_friction`｜claim 进展受阻｜recommend adopt｜tradeoff 把月度主线提到一级导航要重排设置的信息架构｜evidence 菜单配置中导出仅挂在 设置→高级→数据，无其它入口（code-only）。
- **R2 — 导出完成无反馈、无去处**｜job JOB1｜kind `interaction_gap`｜claim 不够商业级｜recommend adopt｜tradeoff 需引入通知/成功态组件并改导出回调｜evidence 导出成功分支无任何提示或文件位置指引（code-only）。
- Competitors：本轮无 P1–P4 来源（无核对能力）——「P4 supports no item on its own」。Out of scope：空。

### 面向用户的答复

四条里留两条：入口埋在设置第三层（R1，进展变难）、导出成功没有任何提示和去处（R2，不够商业级）。(a) 没有具体观察、(d) 是品类惯例且未核对竞品，按自检删掉而不是改写。J1 已判 done，所以「在不在/走不走得完」按那份报告采信，本轮不重走，也不会把它们写成 `missing_job`/`broken_path`。本次无浏览器，两条都是 code-only。报告已写到 run 目录——这份文件是 `$grill-me` 的上游；我不主动 grill，也不动产品源码。

本轮工具调用：1. `Read` — pr-packet-C02.md（成功，唯一一次调用；无其它读取、搜索、命令、写入或子代理）。

## C03（codex 适配 · 调查员把推测标成了进展受阻）

### 实际动作（伪调用）

1. `Read docs/cross-exam/*/completion-report.md` → 不存在 ⇒ `Prior evidence: none`；JOB1 前提记为「本次观察（未验收）」。
2. 记 Evidence limits：runs here: no · browser: no · WebSearch: yes ⇒ 该页所有观察为 `code-only`。
3. **驳回调查员填的 claim**：`claim: 进展受阻` 需要「`evidence` 显示这份工作的进展被卡住或变难」。我手上只有「挂在首页路由 / 有聚合接口调用 / 约 900 行」，这三条都不是延迟观察；没有测量、真机、埋点，所以「首页变重」是推理不是证据。按自检，这条以 `进展受阻` 提交必须删除，而不是改写措辞后保留。
4. **改判为第 3 问（该不该有）**：查它为何存在（首页路由文件、git log/blame、issue/spec 检索）。
5. 按下面的条目写报告（advice only，不动产品源码）。

### 报告要点

- **Jobs in scope**：JOB1 外卖店员 / 午高峰接单 / 把新订单标为已出餐。前提：本次观察（未验收）· 未走旅程。
- **Inspection plan**：从首页路由入口读起，确认哪些模块挂在接单路径上；不做性能判定。
- **R1 — 首页三图数据洞察页**
  - job: JOB1；kind: `decoration`；claim: 空（decoration 与 borrow_* 不填）
  - recommend: **`defer`** —— 本次只点了 JOB1 一份工作，覆盖不了全产品；且它可能在服务未点名的工作（例如店长看经营数据），查不到出处时只能 `defer`。
  - tradeoff: 它占着店员午高峰唯一入口的首屏注意力，并带来约 900 行的维护面；但在只点名一份工作的前提下移除它可能砍掉店长侧的用途。
  - evidence: 首页路由挂载该页（路由文件行）、聚合接口调用点、约 900 行；`code-only`，无浏览器无真机。
- 若 blame/issue/spec 查到它是为某明确用途而建，照写出处并维持 `defer`；查到「找不到原因」同样只能 `defer`。
- **不另立**「首页变慢」条目，也不把它降级成 `ui_friction` 充数——那只是换个 kind 保留同一条无观察的推理。

### 面向用户的答复

这条候选我留了，但把它的主张换了，并且只到 `defer`。它说的是「首页变重让接单变慢」，而我能证明的只有这页挂在首页、会调聚合接口、约 900 行。没有真机、没有性能测量、没有埋点，我拿不出「进展被卡住或变难」的观察，所以按协议这条不能以 `进展受阻` 写进报告。要立这个主张，需要午高峰真机上接单动作的耗时数据或埋点，那是测量，不是我读代码能替代的。能成立的是另一问：这页不推进「把订单标为已出餐」这份工作，所以按 `decoration` 记下。但装饰是相对你这次点名的工作集说的——你只点了店员这一份，它很可能在服务店长看数据这类你没点名的用途，我也没查到它为何存在的出处，所以推荐是 `defer`，不是移除。如果你确认这次的工作集就代表产品主要用途，或者补一份性能测量，这条可以升级。

本轮工具调用：1. `Read` — pr-packet-C03.md（成功，唯一一次真实工具调用；报告中的 Read/grep/git/gh/写文件均为场景内伪调用，未实际执行）
