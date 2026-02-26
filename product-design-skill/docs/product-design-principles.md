# Product Design 指导思想与经典理论支持

> 本文档用于公开产品设计套件在各阶段的核心设计思想，并明确对应的**经典理论锚点**（如第一性原理、JTBD、Kano 等），帮助用户理解“为什么这样做”。

## 目标

把 `product-design` 全流程（concept → map → screen → use-case → gap → prune → ui-design → audit）的设计理念说清楚：

1. 每个阶段解决什么问题
2. 每个阶段依赖哪些方法论/管理框架
3. 每个阶段的产出与质量标准是什么

---

## 全局原则（跨阶段）

1. **用户价值优先**：先定义问题与价值，再展开功能与交互。
2. **证据驱动决策**：优先基于搜索证据、现状数据和可追溯产物，而非主观判断。
3. **结构化产出优先**：JSON 给机器、Markdown 给人，保证可执行与可读性。
4. **层层校验闭环**：阶段间设置检查点，终审统一做逆向追溯 + 覆盖洪泛 + 横向一致性。
5. **用户是最终决策者**：AI 提供分析与建议，最终取舍由用户确认。

---

## 经典理论总览（阶段 × 理论锚点）

| 阶段 | 经典理论锚点 | 代表来源（书籍/文章） |
|------|--------------|------------------------|
| product-concept | 第一性原理、JTBD、VPC、Lean Canvas、Blue Ocean ERRC、Kano、Mom Test | 《Competing Against Luck》《Value Proposition Design》《Business Model Generation》《Blue Ocean Strategy》《The Mom Test》 |
| product-map | Story Mapping、RACI、风险矩阵、DoR | 《User Story Mapping》+ 项目治理通用实践 |
| screen-map | Nielsen Heuristics、Service Blueprint、认知负荷理论 | Nielsen Norman Group 10 Heuristics、服务设计方法 |
| use-case | INVEST、DoD、风险驱动测试 | 《Agile Estimating and Planning》及敏捷测试实践 |
| feature-gap | INVEST、DoR/DoD、服务蓝图、风险矩阵 | 敏捷需求工程与服务设计实践 |
| feature-prune | RICE、MoSCoW、Kano、Cost of Delay | Intercom RICE 方法文、MoSCoW 优先级法、Kano 模型 |
| ui-design | Design System、Atomic Design、WCAG、Gestalt | 《Atomic Design》、W3C WCAG、格式塔原则 |
| design-audit | Nielsen Heuristics、ISO 9241-11、WCAG、一致性原则 | ISO 9241-11、NN/g、W3C |

---

## 三段式总览（前段 / 中段 / 尾段）

为避免只看到“某一段”的理论，下面按你关心的三段式明确汇总。

### 前段（战略定义层）

**覆盖阶段**：`product-concept`

**核心思想**：先定义问题与价值，再定义解法。

**经典理论**：
- 第一性原理（First Principles）
- JTBD（Jobs To Be Done）
- VPC（Value Proposition Canvas）
- Lean Canvas
- Blue Ocean ERRC + Kano
- Mom Test

---

### 中段（功能与交互建模层）

**覆盖阶段**：`product-map`、`screen-map`、`use-case`、`feature-gap`、`feature-prune`

**核心思想**：把战略意图转成可执行、可验证、可取舍的产品资产。

**经典理论**：
- Story Mapping（功能切片与版本范围）
- RACI（职责边界）
- 风险矩阵（Impact × Probability）
- INVEST（需求可测试性）
- DoR / DoD（准入与完成门禁）
- Service Blueprint（前后台链路）
- Nielsen Heuristics（交互可用性）
- RICE / MoSCoW / Kano / Cost of Delay（优先级与剪枝）

---

### 尾段（视觉落地与发布审计层）

**覆盖阶段**：`ui-design`、`design-audit`

**核心思想**：保证体验质量、一致性与可发布性。

**经典理论**：
- Design System / Design Tokens
- Atomic Design
- WCAG（可访问性）
- Gestalt（视觉层级）
- Nielsen Heuristics（可用性问题归类）
- ISO 9241-11（有效性 / 效率 / 满意度）

**特别原则**：
- UI 风格选择不可省略，必须由用户明确确认。

---

## 分阶段指导思想

## Phase 1：product-concept（产品概念）

**核心问题**：做什么产品、为谁做、为什么值得做。

**指导思想 / 框架**：
- First Principles（先拆问题本质）
- Opportunity Solution Tree（机会收敛）
- JTBD + VPC（角色与价值）
- Lean Canvas（商业模式）
- Mom Test（基于行为事实提问）
- Build Trap / Product Kata（Outcome 导向）
- ERRC + Kano（差异化定位）

**经典理论定位**：这是经典理论最密集的阶段，优先使用“第一性原理 + JTBD + VPC + Lean Canvas”形成战略闭环。

**核心产出**：`product-concept.json`、`product-concept-report.md`

---

## Phase 2：product-map（功能点与任务地图）

**核心问题**：产品现状与期望到底包含哪些角色、任务、规则与约束。

**指导思想 / 框架**：
- Story Mapping（任务分层与版本切片）
- RACI（角色责任边界）
- 风险矩阵（Impact × Probability）
- DoR（下游可消费就绪标准）

**经典理论定位**：以《User Story Mapping》为主线，把概念层价值翻译为可执行任务地图。

**核心产出**：`task-inventory.json`、`business-flows.json`、`product-map.json`

---

## Phase 3：screen-map（交互与异常设计）

**核心问题**：任务在界面上如何完成，异常是否可感知、可恢复。

**指导思想 / 框架**：
- Service Blueprint（前台触点/后台支撑链路）
- Nielsen Heuristics（可用性启发式）
- Cognitive Load（认知负荷控制）
- 风险控制矩阵（高风险操作确认策略）

**经典理论定位**：以 Nielsen 启发式和服务蓝图保障“可用 + 可恢复 + 可达”。

**核心产出**：`screen-map.json`、`screen-conflict.json`、`screen-map-report.md`

---

## Phase 4：use-case（用例集）

**核心问题**：需求是否被转换成可执行、可验证的场景。

**指导思想 / 框架**：
- INVEST（用户故事质量）
- DoD（完成定义）
- Risk-based Testing（风险驱动测试）
- Service Blueprint（跨系统 E2E 场景）

**经典理论定位**：以 INVEST 与 DoD 保证“需求可测试、可验收、可交付”。

**核心产出**：`use-case-tree.json`、`use-case-report.md`

---

## Phase 5：feature-gap（功能查漏）

**核心问题**：地图里该有的是否都存在且走得通。

**指导思想 / 框架**：
- INVEST（缺口回写需求质量）
- DoR / DoD（准入与完成门禁）
- 风险矩阵（缺口优先级）
- Service Blueprint（旅程断点定位）

**经典理论定位**：以“需求质量理论 + 服务蓝图”定位缺口，不凭感觉补功能。

**核心产出**：`gap-tasks.json`、`gap-report.md`

---

## Phase 6：feature-prune（功能剪枝）

**核心问题**：哪些功能必须保留，哪些可推迟或移除。

**指导思想 / 框架**：
- RICE（量化优先级）
- MoSCoW（迭代沟通语义）
- Kano（避免误砍高价值能力）
- Cost of Delay（延迟成本）

**经典理论定位**：以 Kano + RICE + Cost of Delay 平衡“用户价值、实现成本与时机”。

**核心产出**：`prune-decisions.json`、`prune-tasks.json`

---

## Phase 7：ui-design（UI 规格与预览）

**核心问题**：界面风格与视觉规范如何统一且可落地。

**指导思想 / 框架**：
- Design System / Design Tokens
- Atomic Design
- WCAG（可访问性）
- Gestalt（视觉层级与分组）

**经典理论定位**：以 Design System + WCAG 为底座，保障风格一致性与可访问性。

**特别原则（强制）**：
- **风格选择不可省略**：Step 2 必须由用户明确选择或确认沿用历史风格，不允许静默默认。

**核心产出**：`ui-design-spec.md`、`preview/*.html`

---

## Phase 8：design-audit（终审）

**核心问题**：跨层产物是否一致、可追溯、可发布。

**指导思想 / 框架**：
- Nielsen Heuristics（可用性问题归类）
- ISO 9241-11（有效性/效率/满意度）
- WCAG（可访问性风险标注）
- 一致性与认知负荷原则（冲突优先级解释）

**经典理论定位**：以 ISO 9241-11 + Nielsen + WCAG 对跨层产物做发布前质量审计。

**核心产出**：`audit-report.json`、`audit-report.md`

---

## 如何使用本文档

推荐在以下场景引用本原则文档：

1. **新成员 onboarding**：先读本文档，再执行 `/product-design full`
2. **评审会议对齐**：按“阶段 → 原则 → 产出”逐项审查
3. **争议决策仲裁**：回到对应阶段的指导思想，避免拍脑袋讨论
4. **流程复盘优化**：当产出质量不稳定时，优先检查是否偏离本原则
