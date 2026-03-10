# Product Design 指导思想与经典理论支持

> 本文档用于公开产品设计套件在各阶段的核心设计思想，并明确对应的**经典理论锚点**（如第一性原理、JTBD、Kano 等），帮助用户理解“为什么这样做”。

## 目标

把 `product-design` 全流程（concept → map → screen → use-case → gap → ui-design → audit）的设计理念说清楚：

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
6. **双轨证据机制**：经典理论提供稳定锚点，Web 热门文章/案例提供时效补充。

---

## 动态研究机制（Web 热门文章与趋势补充）

除了经典理论，每个阶段都建议执行一次「动态趋势补充」：

1. **搜索近期内容**：优先近 12–24 个月（必要时回溯经典长文）
2. **筛选来源质量**：优先官方规范、权威研究、头部产品实践
3. **形成采纳决策**：不是“看到了就用”，而是记录“是否采纳 + 为什么”

### 来源优先级（建议）

| 级别 | 来源类型 | 处理方式 |
|------|----------|----------|
| P1 | 官方规范/标准（W3C、ISO、官方 Design System） | 可直接作为强依据 |
| P2 | 权威研究机构/行业报告（NN/g、McKinsey、Gartner 等） | 高可信，建议交叉验证 |
| P3 | 一线产品团队实践文章（Linear/Stripe/Figma/Notion 工程博客） | 可作为实操参考 |
| P4 | 社区文章/社媒帖子 | 仅作灵感，不单独作为决策依据 |

### 建议输出（趋势证据留痕）

- `.allforai/product-design/trend-sources.json`（机器可读）
- `.allforai/product-design/trend-notes.md`（人类可读）

`trend-sources.json` 最小结构建议：

```json
[
  {
    "phase": "ui-design",
    "topic": "dashboard information density",
    "title": "文章标题",
    "url": "https://...",
    "source_level": "P1|P2|P3|P4",
    "published_at": "2025-06-01",
    "adoption": "ADOPT|REJECT|DEFER",
    "reason": "采纳或拒绝理由"
  }
]
```

---

## 经典理论总览（阶段 × 理论锚点）

| 阶段 | 经典理论锚点 | 代表来源（作者/年份） |
|------|--------------|------------------------|
| product-concept | 第一性原理、JTBD、VPC、Lean Canvas、Blue Ocean ERRC、Kano、Mom Test | Christensen et al. (2016); Osterwalder et al. (2014); Osterwalder & Pigneur (2010); Kim & Mauborgne (2005); Kano et al. (1984); Fitzpatrick (2013) |
| product-map | Story Mapping、RACI、风险矩阵、DoR | Patton (2014); PMI (2013, RACI in PM practice) |
| experience-map | Nielsen Heuristics、Service Blueprint、认知负荷理论 | Nielsen (1994); Shostack (1984); Sweller (1988) |
| use-case | INVEST、DoD、风险驱动测试 | Cohn (2004); Schwaber & Sutherland (2020); Bach (1999) |
| feature-gap | INVEST、DoR/DoD、服务蓝图、风险矩阵 | Cohn (2004); Schwaber & Sutherland (2020); Shostack (1984) |
| ui-design | Design System、Atomic Design、WCAG、Gestalt | W3C (2018/2023, WCAG 2.1/2.2); Frost (2016); Wertheimer (1923) |
| design-audit | Nielsen Heuristics、ISO 9241-11、WCAG、一致性原则 | Nielsen (1994); ISO 9241-11 (2018); W3C (2018/2023) |

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

**覆盖阶段**：`product-map`、`experience-map`、`use-case`、`feature-gap`

**核心思想**：把战略意图转成可执行、可验证、可取舍的产品资产。

**经典理论**：
- Story Mapping（功能切片与版本范围）
- RACI（职责边界）
- 风险矩阵（Impact × Probability）
- INVEST（需求可测试性）
- DoR / DoD（准入与完成门禁）
- Service Blueprint（前后台链路）
- Nielsen Heuristics（交互可用性）

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

## 分段趋势搜索建议（关键词模板）

### 前段（战略定义层）

- `"JTBD" + 行业词 + "case study" + 2025`
- `"problem discovery" + 产品类型 + "user research"`
- `"Blue Ocean" + 行业词 + "competitive landscape"`

### 中段（功能与交互建模层）

- `"story mapping" + 产品类型 + "best practices"`
- `"service blueprint" + 行业词 + "journey design"`
- `"RICE prioritization" + "product team" + 2024 OR 2025`

### 尾段（视觉落地与发布审计层）

- `"design system" + 行业词 + "case study" + 2025`
- `"WCAG 2.2" + 组件类型 + "accessibility"`
- `"usability audit" + "Nielsen heuristics" + "real examples"`

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

## Phase 3-4：journey-emotion + experience-map（交互与异常设计）

**核心问题**：任务在界面上如何完成，异常是否可感知、可恢复。

**指导思想 / 框架**：
- Service Blueprint（前台触点/后台支撑链路）
- Nielsen Heuristics（可用性启发式）
- Cognitive Load（认知负荷控制）
- 风险控制矩阵（高风险操作确认策略）

**经典理论定位**：以 Nielsen 启发式和服务蓝图保障“可用 + 可恢复 + 可达”。

**核心产出**：`experience-map.json`、`screen-conflict.json`、`experience-map-report.md`

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

## Phase 6：ui-design（UI 规格与预览）

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

## Phase 7：design-audit（终审）

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

---

## 参考文献（经典来源）

1. Christensen, C. M., Hall, T., Dillon, K., & Duncan, D. S. (2016). *Competing Against Luck*.
2. Osterwalder, A., Pigneur, Y., Bernarda, G., & Smith, A. (2014). *Value Proposition Design*.
3. Osterwalder, A., & Pigneur, Y. (2010). *Business Model Generation*.
4. Kim, W. C., & Mauborgne, R. (2005). *Blue Ocean Strategy*.
5. Kano, N., Seraku, N., Takahashi, F., & Tsuji, S. (1984). Attractive quality and must-be quality.
6. Fitzpatrick, R. (2013). *The Mom Test*.
7. Patton, J. (2014). *User Story Mapping*.
8. Nielsen, J. (1994). 10 Usability Heuristics for User Interface Design.
9. Shostack, G. L. (1984). Designing Services That Deliver.
10. Sweller, J. (1988). Cognitive Load During Problem Solving.
11. Cohn, M. (2004). *User Stories Applied* (INVEST).
12. Schwaber, K., & Sutherland, J. (2020). *The Scrum Guide* (DoD).
13. Bach, J. (1999). Risk-Based Testing.
14. Reinertsen, D. (2009). *The Principles of Product Development Flow* (Cost of Delay).
15. Frost, B. (2016). *Atomic Design*.
16. W3C. (2018/2023). *WCAG 2.1 / 2.2*.
17. ISO. (2018). *ISO 9241-11:2018 Ergonomics of human-system interaction*.
