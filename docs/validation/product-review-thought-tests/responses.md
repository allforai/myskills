# P01 / P02 / P03 原始答卷

2026-09-15。受试者收到对应平台的 product-review 协议全文与本场景，不含判据。原文保留，未修稿；`<...>` 占位符按原文。

## P01（claude 适配）

读完协议与场景，以下是本轮的实际行动与答复。

### 实际动作（伪调用）

1. 确认人在会话中（交互式，未被管道调用）→ 继续。
2. 采信既有三元组 JOB1（小店主 / 每月对账 / 上月订单导成可交会计的表）；不自行扩充工作集。
3. `Read docs/cross-exam/2026-09-01-export/completion-report.md` → J1 = done、gap 列表为空；报告日期与代码一致，**不标过期**。
4. 记录 Evidence limits：runs here: no（只读代码）· browser: no · WebSearch: yes。
5. `WebSearch` 一次，只查竞品「如何让同一份进展发生」（对账导出/交付会计），只收 P1/P3 来源；`P4 supports no item on its own`。
6. 只写 `docs/product-review/2026-09-15-export-accounting/recommendations.md`，不动产品源码，不碰 `.allforai/`。

### 报告要点

前提行：JOB1 · 前提 J1 (done)。依据「前提有 `J` 判定覆盖就直接采信，不重走」，我**没有重走导出旅程**，也不写 `missing_job`/`broken_path`（`只用于没有 J 判定覆盖的工作`）。本次只答第 3、4 问。

- **R1 导出 20 秒静默** — kind: `interaction_gap` · recommend: `adopt` · evidence: `code-only`（导出处理器无进度/状态回传，UI 无 pending 态）· tradeoff: 加进度与成功态要改一次导出状态流，但没有它，对账人无法判断是否成功。
- **R2 首屏即 14 项功能菜单、无引导** — kind: `ui_friction` · recommend: `adopt` · evidence: `code-only`（左侧导航 14 项，无首次进入引导）· tradeoff: 给对账场景一个首屏入口会弱化其它功能的平权曝光；这是「功能清单式设计」而非主线。
- **R3 完成后无下一步** — kind: `ui_friction` · recommend: `defer` · evidence: `code-only`（完成分支只触发下载）· tradeoff: 工作本身仍能完成，加提示需先定义「交给会计」的下一步语义。
- **R4 空态与错误态两套样式** — kind: `ui_friction` · recommend: `defer` · evidence: `code-only`（两处样式来源不同）· tradeoff: 统一要动共享组件，收益是让「本月无订单」与「导出失败」可区分；这是四条里最弱的一条。

**被删掉的**：其余 13 个菜单项没有写成 `decoration` —— 只有一份工作在场，工作集不覆盖产品主要用途，且我没查到它们为何存在，按「只有当本次点名的工作集覆盖了产品的主要用途、且已查明它为何存在时才可 `adopt`」，连 `defer` 项都不立。竞品条目只在能映射到 JOB1 时进树，其余入 Out of scope。

### 面向用户的答复

完成度不是本轮产出：那份 cross-exam 报告里 J1 判 done、无 gap，「在不在 / 走不走得完」我直接采信，没有重走，「这里的观察永不覆盖那份报告的判定」。我答的是「该不该有」和「商业级够不够」：导出能跑完，但陌生人会觉得它像后台工具——静默 20 秒、无引导、完成即终止。四条意见全部 `evidence: code-only`（此环境无浏览器；真机看一遍可能升级 R1/R2 的证据等级）。产品若在 2026-09-01 之后动过导出链路，重新判完成度的入口是 `/cross-exam`，不是这里。

报告已写入 `docs/product-review/2026-09-15-export-accounting/recommendations.md`；这份文件是 `$grill-me` 的上游，你可以对它开 grilling。我不会自己开始 grill，也不实现任何一条。

本轮工具调用：1. `Read` — pr-packet-P01.md（成功，唯一一次真实调用；报告中其余动作均为场景内伪调用，未实际执行）

## P02（claude 适配）

### 实际动作（伪调用）

1. 确认人类在场；目标与检视方式已定；两份三元组已回读确认。
2. 先记证据上限 → `Evidence limits: runs here / browser / WebSearch` 三个事实；无浏览器则 JOB1 的摩擦类条目一律 `evidence: code-only`。
3. `Read docs/cross-exam/2026-08-20-*/completion-report.md`（最新一份）→ 取 J1(gap, no_feedback)、无 JOB1 旅程。
4. `Grep 路由表 / 搜 spec、README 中 "invoice|tax id|客户筛选"` → 确认无入口、无路由、无承诺。
5. `git log -- <导出模块>` 只用来记「报告后动过、引用代码已变」，**不重走 JOB2 旅程**。
6. 竞品只查「别人怎么让同一份进展发生」，逐条标 P1–P4 与采纳/否决理由。
7. 写 `docs/product-review/2026-09-15-<slug>/recommendations.md`，然后停。

### JOB1（无 J 覆盖 → 本审查的发现）

- Jobs 行前提：`本次观察（未验收）· 无按客户/税号的入口，代码无相关路由`
- `R1 — 按客户+税号拉发票清单无入口`：`job: JOB1`；`kind: missing_job`；`depends_on:` 空；`recommend: adopt`；`tradeoff:` 要新增筛选维度与税号字段落库，季度审计外的日常使用几乎不触发；`evidence:` 路由表无该路径、spec/README 均未出现该工作（无浏览器时标 `code-only`）。
- 依据：「只有在没有 `J` 覆盖、产品对这份工作连入口或终态都没有时，`missing_job` / `broken_path` 才是本审查的发现——那正是对着基线的完成度审计看不见的情况：产品从没承诺过这份工作。」

### JOB2（被 J1 覆盖 → 留在 Prior evidence，不占 `R` 号）

- `Prior evidence: docs/cross-exam/2026-08-20-.../completion-report.md — J1 (gap, no_feedback) blocks JOB2；报告后导出模块大量提交，所引代码已变，JOB2 前提标记为过期`
- 不写 `R` 条目：既不重判 `missing_job`/`broken_path`，也不拿今天看到的代码翻案；本轮无 JOB2 的第 3/4 问观察，故无条目。将来任何等它的条目在 `depends_on` 写 `J1`。
- 依据：「被覆盖的留在 Prior evidence，不占 `R` 号」；「产品在那份报告之后动过，也不在这里重走旅程补判：记下报告日期与你看到的差异，把该工作的前提标成过期」；「这里的观察永不覆盖那份报告的判定」。

### 面向用户的答复

JOB1 从没被产品承诺过，也没有旅程判过它，所以它是本轮唯一的 `R` 条目（R1，missing_job，adopt）。JOB2 已由 8-20 的完成度报告判为 J1(gap, no_feedback)，我按它采信、不重走；但导出模块在那之后大量改动、报告引用的代码已变，我把 JOB2 的前提标为过期——重新判它的入口是 `/cross-exam`，不是这份审查。报告已写到 `docs/product-review/2026-09-15-<slug>/recommendations.md`。这个文件是 `$grill-me` 的上游，你可以对它开 grilling；我不会自己开始，也不会去改代码。

本轮工具调用：1. `Read` — pr-packet-P02.md — 成功；无其它调用。

## P03（codex 适配）

读完协议与场景，按 product-review 执行。

### 实际动作（伪调用）

1. 确认人在会话中；回读 JOB1 三元组待确认：who 外卖店员 / circumstance 午高峰接单时 / progress 把新订单标记为已出餐。
2. `ls docs/cross-exam/*/completion-report.md` → 无 → `Prior evidence: none`；JOB1 前提无 `J` 覆盖。
3. 记录证据上限：runs here 未确认 · browser 未用 · WebSearch 未用 → UI 类断言一律 `code-only`。
4. 查该页为何存在：`git log --follow`、`git blame`（只到一次 squash 导入）、`grep -ri "数据洞察|insight" spec/ README.md`、查埋点/日志 → 全无出处。
5. 写 `docs/product-review/2026-09-15-takeout-pos/recommendations.md`，然后停。

### 报告要点

- Jobs in scope：JOB1 · 前提「本次观察（未验收）」——本轮没有走接单→已出餐这条路，只说一次：判「在不在／走不走得完」的入口是 cross-exam，不在这里补判。
- Inspection plan：首页入口与「数据洞察」页的调用链、提交历史/spec/埋点三处出处。
- Decision tree，唯一一条：
  - R1 — 首页「数据洞察」页不推进任何点名工作
  - job: JOB1；kind: `decoration`；depends_on: 空
  - recommend: **defer**（不是 adopt/移除）
  - tradeoff: 约 900 行代码的维护面，加上每次进首页都打一次聚合接口，占用的正是午高峰接单那块屏幕的注意力与首屏时间；但它可能在服务本次未点名的其它用途。
  - evidence: 首页路由挂载该页 + 三张图表与聚合接口调用（`code-only`）；提交历史仅见一次 squash 导入，无关联 issue，spec/README 未提，无埋点或日志（自查出处只得到「查不到原因」）。
- Competitors：本轮未对 JOB1 做竞品搜索，空。Out of scope：空。
- 我**没有**顺手开第二条 `ui_friction`/`broken_path`：我没有观察到接单流程被实际拖慢或卡死，凭「应该会变慢」写条目过不了自查。

### 支持判断的原句

- 「只有当本次点名的工作集覆盖了产品的主要用途、且已查明它为何存在时才可 `adopt`，否则 `defer` 并写明它可能服务未点名的工作」——场景明说「产品还有这次没有被点名的其它用途」，第一个条件就不成立。
- 「只查到『找不到原因』就降为 `defer`」——第二个条件也不成立，两条各自独立地把它压到 defer。
- 「装饰永远是**相对本次点名的工作集**而言」。
- 「没有覆盖就按看到的写一行观察并标未验收」。

### 面向用户的答复

JOB1 只有一份，我只写出了一条：首页那个「数据洞察」页相对这份工作是装饰，但我给的是 **defer，不是删**。原因有两条，任一条都够：你这次点名的工作集没有覆盖产品的主要用途，它可能在服务你没点名的那些；而且我查遍提交历史、spec、README、埋点都查不到它为何存在——按协议，查不到原因就只能降为 defer，不能建议移除。想让它变成可执行的移除结论，请补两件事：这页当初是给谁做的（哪次需求/谁要的），以及有没有访问数据。另外，「接单→已出餐」这条路本轮我没走，前提标了未验收——判它完不完整的入口是 `$cross-exam`，我不在这里替它下判。报告已写在 `docs/product-review/2026-09-15-takeout-pos/recommendations.md`，它是 `$grill-me` 的上游；要拷问这条 defer，就对着这个文件开。我不自行 grill，也不动产品代码。

本轮工具调用（如实，仅一次）：1. Read — pr-packet-P03.md（成功）
