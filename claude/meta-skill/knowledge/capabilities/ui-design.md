# UI Design Capability

> Generate UI design specifications from product artifacts.
> Internal execution is LLM-driven — design approach adapts to project type.

## Goal

Transform experience-map + product-map into concrete UI specifications:
design tokens, per-screen layouts, component specs, and optional interactive previews.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `ui-design-spec.md` | Per-screen specification: layout, components, states, interactions. Must contain a `screens[]` inventory with `screen_name` and `role` for each screen, followed by per-screen detail sections. |
| `tokens.json` | Design tokens: color, typography, spacing, component, animation |

### Optional Outputs

| Output | When |
|--------|------|
| `preview/*.html` | Interactive HTML previews (if user wants visual validation) |
| `art-direction.md` | For games or visually-driven products |
| `interaction-spec.md` | For products with significant dynamic interactions (IM, collaborative tools, games). Covers: transition animations, gesture interactions (swipe-to-reply, long-press menus), real-time update patterns (typing indicators, live cursors), micro-interactions (message send animation, pull-to-refresh), loading/skeleton states with timing. |

### Required Quality

- Every screen from experience-map has a specification
- Design tokens are binding — downstream implementation must consume them
- State completeness: every screen shows all state variants
- Consumer maturity: consumer products get production-grade spec, not wireframes
- Prune coverage: every task where `feature-prune decisions[].included = true` must have at least one corresponding screen in the spec. Load `prune-tasks.json` before designing — tasks excluded by prune (`included = false`) must NOT get screens.

## Methodology Guidance (not steps)

- **Design tokens first**: Establish visual language before screen design
- **Per-role previews**: Each role sees different screens — design separately
- **Multi-client roles**: Load `product-concept.json roles[].clients[]`. For `feature_parity: full` → one unified screen set. For `partial` → base screen set plus per-client deviation specs for each `parity_exceptions[]` item. For `independent` → separate screen sets per client. For `explicit` → design only `supported_features[]` per client. Use `client_type` to select component vocabulary (Cupertino for `swiftui-ios`, Material for `kotlin-android`).
- **State completeness**: Every screen includes all state variants in the spec
- **Don't over-specify**: Describe intent and constraints, not pixel coordinates
- **Component reuse**: Identify shared components across screens, define once

## Specialization Guidance

| Project Type | UI Design Differences |
|-------------|----------------------|
| Consumer mobile app | Mobile-first, touch targets, thumb zones, offline states |
| Admin dashboard | Data density, table/form patterns, multi-action pages |
| Casual / narrative game | Art direction replaces UI design; mood board, style guide, character design |
| Multiplayer / action game with HUD | Produce both art direction AND interaction-spec covering HUD components (health/stamina bars, minimap, scoreboard, inventory grid, toast notifications) plus UI screens (lobby, matchmaking, settings) |
| SDK/Library | Documentation design replaces UI design (Diátaxis framework) |
| CLI | No UI design needed — skip entirely |

## Knowledge References

### Phase-Specific:
- experience-map-schema.md: screen definitions and component specs to design from
- consumer-maturity-patterns.md: consumer UX maturity requirements
- product-design-theory.md §Phase-6: Design System, Atomic Design, WCAG, Gestalt

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `ui-design-spec.md` | `screens[]` | product-verify | required | 动态验证按屏幕列表逐一检查 |
| `ui-design-spec.md` | `screens[]`, component specs | ui-forge | required | UI 精修需要原始设计规格作为基线 |
| `ui-design-spec.md` | `screens[]` | visual-verify | required | 截图对比需要设计规格作为参照 |
| `tokens.json` | all tokens | translate (implement nodes) | required | 实现必须消费设计 token（颜色/字体/间距） |

## Composition Hints

### Single Node (default)
Run after experience-map is complete.

### Skip Entirely
For backend-only projects, CLI tools, `embedded-firmware`, `github-action`, or when user explicitly skips.

### Split by Role
For apps with very different role UIs (e.g., consumer app + admin dashboard).

---

## App Design Concept Visualization

> App设计阶段可视化协议。仅当 phase-id = `app-design` 时适用。
> 游戏 UI 通过 game-design 阶段的可视化协议处理，不在此范围内。
> 引用协议：`knowledge/capabilities/concept-visualization.md`（phase-id = `app-design`）

**启动：** App设计阶段开始时（通常在 experience-map 完成后），调用「工具层：启动序列」（phase-id = `app-design`）。

**各子阶段结论确认后** 调用「工具层：结论更新序列」：

| 子阶段内容 | 目标看板列 slug | 线框触发 |
|---|---|---|
| 用户流程定义（JTBD / 体验地图 / 导航路径） | `liucheng` | **低保真**（此列第1张卡片写入时触发，内容：主屏幕骨架线框） |
| 页面结构定义（信息架构 / 导航层级 / 屏幕清单） | `jiegou` | **中保真**（此列第1张卡片写入时触发，内容：核心页面线框集3-5页） |
| 组件规范（Design System 组件定义 / 复用规则） | `zujian` | — |
| 设计 Token（颜色 / 字体 / 间距 / 圆角） | `token` | — |

**结束：** UI设计阶段全部完成后，调用「工具层：结束序列」。
