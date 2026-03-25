---
name: ui-design
description: >
  Use when the user wants to "generate UI design", "create UI spec", "design screens",
  "what should the UI look like", "UI style guide", "UI from product map",
  "design system recommendation", "UI 设计", "界面设计", "生成UI", "UI 规格",
  "从产品地图生成UI", "设计风格", "UI 预览", "界面风格",
  or wants to turn product map and screen map into visual design specifications.
  Requires product-map to have been run first. Optionally uses experience-map and product-concept.
version: "1.1.0"
---

# UI Design — UI 设计规格生成

> 产品地图说应该有什么，设计应该长什么样？

## 目标

以 `product-map`（以及可选的 `experience-map`、`product-concept`）为输入，结合用户选定的 UI 风格和实时检索的设计原则，输出两类产物：

1. **`ui-design-spec.md`** — 高层 UI 设计规格：每个界面的布局模式、配色语义、组件建议、交互状态
2. **按角色拆分的 HTML 预览** — 每个角色一个 HTML 文件，展示该角色可见的所有界面卡片；`index.html` 做总导航

当上游判定为 `consumer` 或 `mixed` 时，UI 设计的目标不是把页面“画出来”，而是把用户端做出成熟产品感。

---

## 定位

```
product-concept → product-map → experience-map → ui-design
（方向）          （任务）       （界面结构）  （视觉规格 + 预览）
```

**前提**：必须先运行 `product-map`。`experience-map` 不存在时自动运行生成体验地图。

**下游消费边界**（dev-forge 如何消费 ui-design 产出）：

| 产物 | 消费方式 | 说明 |
|------|---------|------|
| `tokens.json` | 直接用 | 确定性设计变量（颜色、间距、字号），scaffold 阶段生成 CSS 变量 |
| `component-spec.json` | 直接用 | 确定性组件结构（名称、变体、a11y），task-execute 阶段实现组件 |
| `ui-design-spec.json` | 直接用 | 确定性屏幕规格（布局、数据绑定、交互模式） |
| `screenshots/` | 视觉约束 | 视觉风格参考，dev-forge 生成后可 Playwright 截图对比验证还原度 |
| Stitch HTML / hifi-preview HTML | 不传递 | 视觉稿的使命在截图后结束，代码不进入开发阶段 |

### 新增输入通道（来自 experience-map）

| 输入 | 来源 | 用途 |
|------|------|------|
| `emotion_state` + `intensity` | experience-map 每个 node | 决定视觉层级、色彩情绪、动效强度 |
| `ux_intent` | experience-map 每个 node | 指导组件选择和布局策略 |
| `non_negotiable` | experience-map 每个 screen | 作为设计约束写入 spec |
| `continuity` | experience-map 每条 line | 指导转场动效和导航模式 |
| `quality_gate.issues` | interaction-gate.json | 标记需要特别处理的交互问题 |
| `experience_priority` | product-map.json | 判断是否需要按用户端产品化标准生成 UI 规格 |

---

## 快速开始

```
/ui-design            # 完整流程（风格选择 → 检索 → 生成规格 → 生成 HTML）
/ui-design refresh    # 清除决策缓存，重新选风格 + 完整重跑
/ui-design --variants 3    # 生成 3 套视觉风格方案，对比后选择
```

**参数**：
- `--variants N`：生成 N 套不同的视觉风格方案（默认 1，最大 5）。N ≥ 2 时进入 variants 模式。

## 增强协议（WebSearch + 4D+6V + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：`"design system" + 行业词 + "case study" + 2025`、`"WCAG 2.2" + 组件类型 + "accessibility"`、`"dashboard UI" + "information density" + "best practices"`

**4D+6V 重点**：
- 读取 `task-inventory.json` 中的 `innovation_tasks` 字段，对 `innovation_task=true` 的界面标注 `innovation_ui: true`
- `source_refs` 指向 `adversarial-concepts.json` 的对应概念 ID（如 `IC001`）
- 规格附带设计决策理由；对高风险交互（删除、提交、权限）明确记录可访问性与失败反馈依据
- 创新概念 UI 规格必须体现跨领域参考（如"抖音无限滚动"、"游戏赛季制"）

**XV 交叉验证**（Step 4 生成设计规格后）：

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| 设计审查 | `design_review`→gpt | 设计规格摘要：配色系统 + 排版规范 + 关键界面布局 + 受众类型 | cross_model_review.design_issues |
| 视觉一致性 | `visual_consistency`→gemini | 设计规格摘要：各界面配色/圆角/间距参数 + 组件风格 + 状态设计 | cross_model_review.consistency_gaps |

自动写入：视觉层级问题（主操作不够突出、信息密度与受众不匹配、色彩语义冲突）、一致性缺陷（跨界面组件风格不统一、状态反馈模式不一致、间距/圆角参数偏差）。

**上游基线验收**（Step 4.7）：LLM 加载 experience-map.json 作为基线，逐界面验证设计意图还原度。详见 Step 4.7。

## 尾段理论支持（可选增强）

为让 UI 产出从"风格偏好"升级为"可评审、可审计的设计决策"，可在现有流程叠加：

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|----------|----------|
| Design System / Design Tokens | Step 3/4 | 将配色、字号、间距、圆角参数化，保证多角色预览与后续实现一致 |
| Atomic Design | Step 4/5 | 将规格按原子-分子-组织拆分，避免界面规格仅停留在页面描述 |
| WCAG 可访问性（2.1/2.2） | Step 3/4 | 在颜色、排版、状态反馈中加入对比度与可达性约束 |
| Gestalt / 视觉层级原则 | Step 4 | 约束信息分组与主次层级，降低认知负荷，提升可扫读性 |

> 说明：此增强不替代用户风格选择；风格仍由 Step 2 明确决策。

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 1 画像确认** | 向用户确认 | 自动确认，记入 `pipeline-decisions.json`（`decision: "auto_confirmed"`） |
| **Step 2 风格选择** | 向用户提问 8 选 1 | 读 `pipeline_preferences.ui_styles[当前端类型]`：非 `"undecided"` → 直接使用预设风格，跳过 向用户提问；`"undecided"` → **回退交互模式**（展示 8 种风格，用户选择）。兼容旧版 `ui_style`（字符串） |
| **Step 3 设计原则确认** | 向用户确认 | 自动确认（WebSearch 照常执行，搜索结果自动采纳） |
| **Step 4 规格确认** | 向用户确认 | 自动确认 |
| **Step 5 预览确认** | 向用户确认 | 自动确认 |
| **Step 5.5 Stitch 不可用** | 向用户询问 | 自动降级到 Step 5.6（LLM 高保真预览） |
| **--variants 模式** | 生成 N 套风格方案 → 视觉对比 → 用户选择 | 自动选择与 `pipeline_preferences.ui_styles[当前端类型]` 最匹配的方案，记入 decisions.json |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（无法推导任何界面、product-map 损坏）
- 当前端类型的 `ui_styles` 值为 `"undecided"` 时 Step 2 回退交互模式

**基础设施偏好消费**：

读取 `pipeline_preferences.infrastructure` 数组，在 token 体系和组件规格中体现对应需求（如暗色模式需双色系 token、i18n 需文案 key 化、a11y 需对比度和 ARIA 规范等）。具体实现方式由 LLM 根据所选 UI 风格和技术栈判定。

---

## 步骤详情加载

本技能的详细步骤定义拆分为两个文件，按认知阶段分组。执行时加载对应文件：

### 设计步骤（生成阶段）

**加载**：`Read ./docs/ui-design/design-steps.md`

包含：Step 1（产品画像推导）、Step 2（风格选择 + Variants 模式）、Step 3（检索设计原则）、Step 4（生成设计规格）、Step 5（HTML 线框预览）、Step 5.3（组件规格）、Step 5.5（Stitch 视觉生成）、Step 5.6（LLM 高保真预览）、生成方式说明。

### 验证步骤（审计阶段）

**加载**：`Read ./docs/ui-design/validation-steps.md`

包含：Step 4.5（Pattern Consistency Check）、Step 4.7（LLM 自审验证 Loop）、闭环审计、防御性规范（加载校验、零结果处理、规模自适应、WebSearch 故障、上游过期检测、执行失败保护）。

---

## 工作流

```
前置检查：
  concept-baseline.json 自动加载（推拉协议 §三.A）→ 不存在则 WARNING，不阻塞
  product-map.json 必须存在（否则终止）
  experience-map.json 必须（不存在则自动运行 experience-map 生成）
  product-concept.json 可选（跨级拉取源：定位/价值主张用于配色基调）
  ui-design-decisions.json 存在则加载历史决策

  跨级原始数据拉取（按需，推拉协议 §三.B）：
    role-value-map.json:
      - roles[].operation_profile.density  → 决定缓存策略和预加载行为
    product-concept.json:
      - value_propositions                 → 配色基调和品牌感知

  Pattern & Behavioral 数据（从 experience-map.json 读取）：
    experience-map.json 的 screen 节点已包含 _pattern*、_behavioral* 字段（由 experience-map Step 3.6 写入）：
    - screen._pattern_group 相同的界面 → 必须使用相同的组件布局模板
    - screen._pattern_template 字段 → 作为界面设计的首选方案参考
    - screen._behavioral_standards → 强制使用对应的标准方案
    - 例：BC-LOADING 标准为 skeleton → 所有界面的 loading 状态均使用骨架屏
    - 例：BC-DELETE-CONFIRM 标准为 modal_confirm → 所有 crud=D 操作使用模态弹窗确认

  视图模式数据（从 experience-map.json 读取）：
    screen.view_modes 字段（由 experience-map Step 2 填充）：
    - 后台屏幕（merchant/admin）的 view_modes 描述屏幕内的视图模式流转
    - UI 设计时，每个 view_mode 需要独立的布局规格（组件可见性、区域占比、交互状态）
    - 例：工单列表有 3 种 view_mode（全量列表 → 筛选列表 → 详情面板），UI 规格需为每种模式描述布局变化
    - 无 view_modes 的屏幕（移动端单任务）按单一视图模式处理

  Phase 2.8 — 加载创新概念清单（新增）：
    检查 .allforai/product-concept/adversarial-concepts.json：
      存在 → 加载 `concepts[]` 数组，标记 innovation_mode = "active"
      不存在 → innovation_mode = "none"
    检查 task-inventory.json 的 `innovation_tasks` 字段：
      存在 → 告知用户：「创新感知：active — 检测到 X 个创新任务」
      不存在 → innovation_mode = "none"
  ↓
Step 1: 产品画像推导                          ← design-steps.md
  读取 task-inventory + role-profiles + experience-map + innovation_tasks + experience_priority
  推导：B端/C端、角色列表、各角色高频任务、界面总数
  向用户展示，确认
  ↓
Step 2: 风格选择（向用户提问（单选））      ← design-steps.md
  展示 8 种主流风格
  用户选定后，记录到 ui-design-decisions.json
  ↓
Step 3: 检索设计原则（WebSearch）             ← design-steps.md
  根据所选风格搜索官方设计系统文档和核心原则文章
  提取：配色逻辑、排版规范、组件偏好、交互原则
  摘要展示，用户确认后才应用
  ↓
Step 4: 生成设计规格（ui-design-spec.md）     ← design-steps.md
  逐界面/推导界面输出高层规格
  ↓
Step 4.5: Pattern Consistency Check           ← validation-steps.md
  ↓
Step 4.7: LLM 自审验证（Loop）               ← validation-steps.md
  对照 experience-map 验证设计意图还原度
  不通过 → 修正 → 重审（最多 2 轮）
  ↓
Step 5: 生成多角色 HTML 线框预览              ← design-steps.md
  index.html + 每角色一个 ui-role-{角色名}.html
  ↓
Step 5.6: LLM 高保真 HTML 预览               ← design-steps.md
  tokens.json → CSS 变量 → Tailwind + 真实内容 → 高保真页面

## 用户端产品化设计原则（新增）

当 `experience_priority.mode = consumer` 或 `mixed` 时，ui-design 必须额外满足：

- 首页不是入口拼盘，而是主线任务与状态总览
- 列表/卡片/详情形成明确层级节奏，而不是同质化页面堆叠
- 主操作、次操作、反馈信息、风险操作有清晰视觉优先级
- 空态/加载态/错误态/成功态有统一设计语言
- 页面要支持回访与持续关系，而不是一次性完成即结束

对用户端移动应用，优先考虑：

- 首屏情绪和品牌感
- 单手操作路径
- 低注意力场景下的下一步引导
- 系统反馈的即时性

禁止把用户端 UI 退化成“后台组件换皮”。
```

> **强制规则**：Step 2「风格选择」不可跳过。即使存在历史决策，也必须向用户展示当前风格并请求确认（可沿用历史风格或改选），不得静默默认。

---

## 输出文件结构

```
.allforai/ui-design/
├── ui-design-spec.md               # 高层设计规格（含 micro-interaction 规格表）
├── ui-design-spec.json             # 设计规格（机器可读）
├── ui-design-decisions.json        # 用户决策日志
├── tokens.json                     # 设计令牌单一来源（配色、间距、圆角、排版）
├── micro-interactions.json         # 微交互规格（按屏幕，含情绪对齐）
├── preview/                        # 线框预览（Step 5，始终生成）
│   ├── index.html
│   ├── ui-role-{角色1}.html
│   └── ...
├── hifi-preview/                   # 高保真预览（Step 5.6，Stitch 不可用时自动生成）
│   ├── _tokens.css                 # tokens.json → CSS 变量（所有页面共享）
│   ├── _design-system.html         # 共享组件视觉参考（锚点页面）
│   ├── {screen-id}.html            # 每屏一个高保真 HTML 页面
│   └── index.html                  # 导航页
├── screenshots/                    # 关键界面视觉截图（供 dev-forge 作为视觉约束消费）
│   └── {screen-id}.png             # Stitch 或 hifi-preview 的屏幕截图
└── variants/                       # --variants 模式
    ├── variant-1/                  # 风格方案 A
    │   ├── tokens.json
    │   └── hifi-preview/           # 2-3 个代表性界面
    ├── variant-2/                  # 风格方案 B
    │   ├── tokens.json
    │   └── hifi-preview/
    └── comparison.html             # 对比导航页
```

### tokens.json (Design Token Single Source)

从所选风格自动导出的设计令牌，供 dev-forge project-scaffold 消费：

- `color` — 配色系统（primary, secondary, surface, error 等）
- `spacing` — 间距系统（4px 基准 + 标度）
- `radius` — 圆角（sm/md/lg）
- `typography` — 排版（display/headline/title/body/label）
- `font`, `shadow`, `style_name`

下游 scaffold 读取 tokens.json 自动生成框架配置（Tailwind theme / CSS variables / Flutter theme），避免手动复制导致的令牌漂移。

### micro-interactions.json

基于 emotion_intensity 自动推导的微交互规格：

| 情绪强度 | 层级 | 动画 | 时长 | 触觉反馈 |
|---------|------|------|------|---------|
| 1-3 | calm | fade | 200ms | none |
| 4-6 | moderate | slide-fade | 250ms | light |
| 7-10 | intense | scale-bounce | 300ms | impact-medium |

特殊覆盖：CRUD "C" 成功 → scale-bounce + impact-medium；CRUD "D" 错误 → shake + notification-error；CUD 异步操作 → pulse loading 反馈。

### JSON 对应件

同步生成 `ui-design-spec.json`，供下游技能（design-audit、design-to-spec、product-verify）直接解析：

```json
{
  "generated_at": "ISO8601",
  "style": "Flat / Minimal",
  "style_source": "URL",
  "design_tokens": {
    "colors": { "primary": "#111827", "background": "#FFFFFF", "success": "...", "warning": "...", "error": "..." },
    "typography": { "h1": "28px/700", "h2": "22px/600", "body": "14px/400", "caption": "12px/400" },
    "spacing": "8px grid",
    "border_radius": "4px"
  },
  "screens": [
    {
      "id": "S-05",
      "name": "工单管理",
      "role": "管理员",
      "audience_type": "professional",
      "interaction_type": "MG3",
      "layout": "侧边导航+内容区",
      "sections": ["顶部操作栏", "数据表格", "分页器"],
      "states": { "empty": "引导文案", "loading": "骨架屏", "error": "toast 提示" },
      "task_refs": ["T-12", "T-13"],
      "innovation_ui": false,
      "_pattern": ["PT-CRUD"]
    }
  ],
  "pattern_alignment": []
}
```

---

## 4 条铁律

1. **只出规格不出生产代码** — 输出是设计语言描述（布局/配色/组件建议），不生成任何 React、Vue 生产组件代码；Step 5 线框预览是静态骨架展示，Step 5.6 高保真预览是 Tailwind + CSS 变量驱动的视觉参考页面（供设计评审和开发参考，不是可部署的功能实现）

2. **experience-map 优先，缺席则推导** — 有 experience-map 按界面生成规格（每个 experience-map 界面对应一节规格）；没有 experience-map 则从 task-inventory 中的高频任务自动推导主要界面结构（每个高/中频任务 → 一个推导界面）。界面规格标注其关联任务的 `category`（core/basic）+ `innovation_ui`（true/false），便于团队区分核心功能界面、基础设施界面和创新概念界面

3. **WebSearch 摘要展示，用户确认后才应用** — 检索到的设计原则必须以摘要形式展示给用户并等待确认，不自动静默应用；用户有权跳过检索（输入「跳过」）并手动指定设计参数

4. **风格选择不可省略** — 设计风格属于用户偏好决策，必须在 Step 2 由用户明确选择或确认沿用历史风格；未确认风格前不得生成规格和预览

---

## 下一步

ui-design 完成后，运行 `/review` 启动统一审核站点（http://localhost:18900/），在 UI tab 中浏览所有界面预览、标注 pin 评论。提交反馈后运行 `/review process ui` 局部迭代修改的界面，循环直到全部通过。

在 `/product-design full` 流程中，UI 审核作为 Phase 8 自动串入（Phase 5-7 并行完成后、Phase 9 终审前）。
