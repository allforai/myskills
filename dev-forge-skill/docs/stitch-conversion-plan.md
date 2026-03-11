# 计划：dev-forge 消费组件规格 + Stitch HTML 生成生产级组件

## Context

product-design 的 ui-design Phase 6 产出两层数据：

- **Layer 1（通用）**：`component-spec.json` — 共享组件、交互原语、变体、a11y 规格。
  由 `gen_ui_components.py` 从 experience-map 分析生成，**始终存在**，不依赖 Stitch。
- **Layer 2（增强）**：`stitch/` 目录 — Stitch 生成的 HTML/CSS + 截图。
  由 Stitch MCP 生成，**条件存在**（用户启用 Stitch 且认证通过时）。

本计划定义 dev-forge 如何消费这两层数据，生成生产级项目组件。

**前置依赖**：`product-design-skill/docs/stitch-integration-plan.md`（定义输出契约）

---

## 数据输入契约

来自 product-design 的输出：

```
.allforai/ui-design/
├── ui-design-spec.md          # 设计 token（颜色/字体/间距/动效/图标/主题）
├── component-spec.json        # [通用] 共享组件/原语/变体/a11y（始终存在）
├── stitch-prompts.json        # [Stitch] prompt 记录
├── stitch-index.json          # [Stitch] 屏幕→文件映射 + 一致性检查
└── stitch/                    # [Stitch] 条件存在
    ├── S010-买家首页.html      # Stitch 生成的 HTML/CSS
    ├── S010-买家首页.png       # 截图
    └── ...
```

### `component-spec.json`（核心输入，始终存在）
- `shared_components` → 共享组件定义（props/primitives/variants/a11y）
- `screen_components` → 每个屏幕使用的组件列表
- `primitive_mapping` → interaction_type → primitives 映射
- dev-forge 通过 `primitive-impl-map.md` 查找技术栈实现

### `stitch-index.json`（增强输入，条件存在）
- `screens[].screen_id` → 关联 `experience-map.json`
- `screens[].local_files.html` → HTML 文件路径
- `screens[].route_path` → 页面路由
- `screens[].status` → success/failed/skipped
- `component_spec_ref` → 指向 component-spec.json

---

## 集成点分析

### 当前 dev-forge 流程（与 Stitch 相关）

```
design-to-spec (Phase B 前端)
  Step 2: 读 experience-map → 生成 page routes + component specs → design.md
  Step 3: 引用 ui-design-spec.md 的 design tokens
  Step 4: 生成 tasks.md（B0-B5 任务分批）
      ↓
task-execute
  B3 Round: 前端 UI 任务（组件实现 + 样式 + 状态管理）
```

### 集成方案

Stitch HTML 转换插入 **两个位置**：

**位置 A — design-to-spec Phase B Step 2.5**（丰富 design.md）

**触发条件**：`component-spec.json` 存在（通用路径，始终触发）

Layer 1（通用，component-spec.json）：
- 读取 shared_components → 生成共享组件规格到 design.md
- 关联 primitives → primitive-impl-map 技术栈实现
- 注入 a11y 要求 + 变体矩阵

Layer 2（增强，stitch-index.json + stitch/*.html，条件执行）：
- 当 `stitch-index.json` 存在且有 success 屏幕时额外执行：
- 读取对应的 Stitch HTML，提取精确组件结构（DOM 树 → 组件层级）
- 补充 design.md 中组件规格的精确 DOM 结构和样式映射
- 这让 tasks.md 的 B3 任务更精确（有具体的组件树 + 视觉参考）

**位置 B — task-execute B3 Round**（组件实现）

Layer 1（通用）：
- 读取 design.md 中的组件规格（来自 component-spec.json）
- 按共享组件优先的顺序实现
- 注入 a11y、主题、变体实现指令

Layer 2（增强，条件执行）：
- 如果任务关联的屏幕有 Stitch HTML → 读取作为视觉参考
- Claude 基于 Stitch HTML 结构 + 项目技术栈 → 更精确的组件实现
- 不是机械翻译 HTML → JSX，而是理解结构后用项目的组件库/设计系统重写

---

## 改动清单

### 1. `skills/design-to-spec.md`
**位置**：Phase B（前端子项目规格生成）
**改动**：在 Step 2（页面路由提取）后新增 Step 2.5

```markdown
### Step 2.5：组件规格导入（始终执行）

**触发条件**：`component-spec.json` 存在（通用路径）

**Layer 1 执行流程**（始终）：

1. 读取 `<BASE>/ui-design/component-spec.json`
2. 对 `shared_components` 中的每个组件：
   a. 读取 props / primitives / variants / a11y
   b. 查 `primitive-impl-map.md` 获取当前技术栈的实现方案
   c. 写入 design.md 的 `## 共享组件` 章节（含 a11y、变体矩阵、原语实现）
3. 对 `screen_components` 中的每个屏幕：
   a. 将 used_shared + page_specific 写入 design.md 对应页面规格
   b. 关联 experience-map 的 screen_id → page route

**Layer 2 执行流程**（条件：`stitch-index.json` 存在且有 success 屏幕）：

4. 读取 `<BASE>/ui-design/stitch-index.json`
5. 对每个 `status=success` 的屏幕：
   a. 读取对应的 `stitch/*.html` 文件
   b. 提取精确组件结构：
      - 顶层布局（header/main/footer/sidebar）
      - 组件层级树（语义化 HTML 标签 → 组件名推断）
      - 关键交互元素（button/input/select/modal）
      - 内联样式 → design token 映射
   c. 补充到 design.md 的对应页面规格中（增强 Layer 1 的推断结果）：

   ```markdown
   ### /home — 首页

   **组件结构**（来源：component-spec.json + stitch/S010-买家首页.html）
   ```
   AppShell
   ├── TopAppBar [title, search_action, notification_action]
   ├── HeroBanner [image, cta_button]  (page_specific)
   ├── CategoryGrid [items: CategoryCard[]]
   │   └── CategoryCard [icon, label, link]
   ├── ProductList [items: ProductCard[], primitives: VirtualList+PullToRefresh]
   │   └── ProductCard [image, name, price, rating, cart_action]
   └── BottomNav [home, category, cart, profile]
   ```

   **样式映射**（Stitch 增强）：
   - `background: #f5f5f5` → `var(--surface-container)`
   - `color: #1c1b1f` → `var(--on-surface)`
   - `border-radius: 12px` → `var(--shape-medium)`
   ```

6. 记录到 pipeline-decision：
   - `component_spec_imported: N shared components`（始终）
   - `stitch_components_enhanced: M screens`（有 Stitch 时）
```

---

### 2. `skills/task-execute.md`
**位置**：任务执行上下文注入部分
**改动**：在 Round 执行前的上下文准备中，新增 Stitch HTML 参考加载

```markdown
### 任务上下文：Stitch 视觉参考（条件加载）

在执行 B3（前端 UI）Round 的任务时：

1. 检查任务关联的屏幕是否有 Stitch HTML：
   - 从 tasks.md 中提取任务对应的 screen_id
   - 查询 stitch-index.json 中该 screen_id 的 status
2. 如果有 `status=success`：
   - 读取 `stitch/{screen_id}-{name}.html`
   - 从 `component_vocabulary` 中找出该屏幕使用的组件及其 `primitives`
   - 将 HTML + primitives 实现方案一起注入任务上下文
   - 指令：「基于以下 Stitch 视觉稿的结构，使用项目的组件库和设计 token 实现。
     保留布局结构，但用框架原生方式重写，不要直接复制 HTML。
     该屏幕使用以下交互原语，请按技术栈实现：[primitives 列表 + impl-map 方案]」
3. 如果没有 → 正常执行，使用 design.md 中的文字规格
```

---

### 3. `skills/design-to-spec.md`（tasks.md 生成调整）
**位置**：Step 4（任务生成）
**改动**：B3 任务增加 Stitch 参考标记

```markdown
当 Stitch 组件结构已提取（Step 2.5 执行过）时，B3 任务增加元数据：

每个前端页面任务追加：
- `stitch_ref`: screen_id（如 "S010"）
- `stitch_html`: 文件路径（如 "stitch/S010-买家首页.html"）
- `component_tree`: Step 2.5 提取的组件层级（简化版）

这让 task-execute 阶段可以精确加载对应的 Stitch HTML。
```

---

## 共享组件识别（跨屏幕去重）

### 上游已提供：component-spec.json

product-design 的 `gen_ui_components.py`（通用脚本，不依赖 Stitch）已完成：
- 跨屏幕共享组件识别
- 交互原语关联
- 变体推断
- a11y 规格标注

结果存储在 `component-spec.json` 中，**始终存在**。

如果用户启用了 Stitch，`stitch-index.json` 的 `component_spec_ref` 指向同一份 component-spec.json，
Stitch HTML 提供额外的精确 DOM 结构和样式映射。

### Step 2.5b 消费 component-spec.json

直接读取上游已识别的结果，不需要重新分析：

```markdown
**Step 2.5b：共享组件规格生成**

1. 读取 `stitch-index.json` 的 `component_vocabulary`
2. 对每个共享组件，结合对应的 Stitch HTML 补充实现细节：
   - 从 anchor_screen 的 HTML 中提取该组件的实际 DOM 结构
   - 推断 Props 接口：对比各屏幕中该组件的使用差异 → 可变属性
   - 提取样式规格：内联样式 → design token 映射
3. **关联交互原语**：读取组件的 `primitives` 字段，
   查 `primitive-impl-map.md` 获取当前技术栈的具体实现：
   - 如 `ProductList.primitives: ["VirtualList", "InfiniteScroll"]`
   - React 项目 → `@tanstack/react-virtual` + `IntersectionObserver`
   - Vue 项目 → `el-table-v2` + 自定义 scroll hook
   - Flutter 项目 → `ListView.builder` (原生虚拟滚动)
4. 输出到 design.md 的 `## 共享组件` 章节：

   ```markdown
   ## 共享组件（来源：Stitch component_vocabulary）

   ### ProductCard
   - 来源：stitch-index.json component_vocabulary
   - 出现屏幕：S010(首页推荐), S030(列表页), S060(收藏页)
   - Props: { image: string, name: string, price: number, rating?: number, badge?: string, onCartAdd: () => void }
   - DOM 结构（来自锚点屏 S010）：
     article.card > img.card-image + div.card-body > (h3 + span.price + div.rating) + button.cart-btn
   - 样式映射：border-radius → var(--shape-medium), box-shadow → var(--elevation-1)
   - 交互原语：无（纯展示组件）
   - Stitch 参考：stitch/S010-买家首页.html

   ### ProductList
   - 来源：stitch-index.json component_vocabulary
   - 出现屏幕：S030(列表页), S060(收藏页)
   - Props: { items: Product[], onLoadMore: () => void, onRefresh: () => void }
   - DOM 结构：div.list-container > ProductCard[] + div.load-more-indicator
   - 交互原语：VirtualList, InfiniteScroll, PullToRefresh
   - 技术栈实现（React）：@tanstack/react-virtual + IntersectionObserver + pull-to-refresh hook
   - Stitch 参考：stitch/S030-商品列表页.html
   ```

5. 与 shared-utilities.md（Phase 5）的关系：
   - Step 2.5b 在 **design 阶段** 从上游 vocabulary 规划共享组件（含交互原语）
   - shared-utilities Phase 5 在 **代码阶段** 验证实际代码的复用一致性
   - 两者互补：前者前置规划，后者后置验证
```

### tasks.md 影响

B3 任务分批需要调整优先级：
- **共享组件优先实现**（B3 Round 1）：先实现 ProductCard/AppShell 等共享组件
- **页面组件后实现**（B3 Round 2+）：页面组件引用已实现的共享组件
- 这避免了「先实现页面→发现重复→再抽取」的返工循环

---

## 生产级补强（G2/G3/G9/G10）

product-design 侧负责规格定义（G1/G4-G7 在 ui-design-spec.md），
dev-forge 侧负责实现层面的补强：

### G3. 无障碍（a11y）注入

**位置**：design-to-spec Step 2.5 共享组件规格生成时，自动附加 a11y 要求

对每个共享组件，根据组件类型注入 a11y 规格到 design.md：

| 组件类型 | a11y 要求 |
|----------|----------|
| Button | `role="button"`, `aria-label`, `:focus-visible` outline, min 44×44px touch target |
| Input/Form | `<label>` 关联, `aria-required`, `aria-invalid` + error message 关联, `autocomplete` |
| List | `role="list"` + `role="listitem"`, `aria-label` for container |
| Image | `alt` text（从 screen_name 推断）, decorative → `alt=""` |
| Navigation | `role="navigation"`, `aria-current="page"` for active item |
| Modal/Dialog | `role="dialog"`, `aria-modal`, focus trap, Escape 关闭, 焦点返回触发元素 |
| Card (interactive) | `role="article"` 或 `role="button"`（可点击时）, `tabindex="0"` |
| Tab | `role="tablist"` + `role="tab"` + `role="tabpanel"`, `aria-selected`, 方向键切换 |

写入 design.md 每个组件的 `### 无障碍` 小节。

键盘导航矩阵也写入 design.md：
```markdown
## 键盘导航

| 区域 | Tab 顺序 | 快捷键 |
|------|----------|--------|
| TopAppBar | 1 | — |
| 主内容区 | 2 | — |
| 侧边栏（如有） | 3 | — |
| BottomNav/Footer | 4 | — |
| Modal 弹出时 | Focus trap | Escape 关闭 |
```

### G2. 主题支持指令

**位置**：task-execute B3 Round 上下文注入

B3 任务上下文追加主题指令：
```
实现组件时：
1. 使用 CSS 变量 / theme token 而非硬编码颜色值
2. 参考 ui-design-spec.md 的「主题变体」章节
3. 确保组件支持 light/dark 切换：
   - 如果项目有 ThemeProvider（MUI/shadcn/AntD）→ 使用它
   - 如果项目用 Tailwind → 使用 dark: 前缀
   - 如果项目用 CSS Modules → 使用 [data-theme="dark"] 选择器
4. Stitch HTML 中的硬编码颜色值必须替换为 token 变量
```

### G9. 组件变体实现

**位置**：task-execute B3 Round + design-to-spec Step 2.5b

Step 2.5b 补充：读取 `component_vocabulary` 中每个组件的 `variants` 字段，
写入 design.md 的组件规格：

```markdown
### ProductCard

**变体矩阵**：
| 维度 | 值 | 视觉差异 |
|------|-----|---------|
| size | compact | 高度 80px，水平布局，无 rating |
| size | default | 高度 200px，垂直布局，完整信息 |
| size | featured | 高度 280px，大图，badge 标签 |
| state | default | 正常显示 |
| state | selected | 边框高亮 + check icon |
| state | disabled | 灰度 + 不可点击 |
| state | loading | 骨架屏占位 |
```

task-execute B3 共享组件任务指令：
```
实现组件时，必须实现 variants 字段中标注的所有变体：
- size variants → 通过 size prop 控制
- state variants → 通过 state/disabled/loading props 控制
- 每个变体需要有对应的 CSS/样式处理
- 如果项目使用 Storybook → 每个变体需要有 story
```

### G10. 视觉回归验证

**位置**：e2e-verify 新增步骤（需要改动 `skills/e2e-verify.md`）

```markdown
### 视觉回归验证（条件执行）

**跳过条件**：stitch-index.json 不存在

**执行流程**：
1. 读取 stitch-index.json，获取 status=success 的屏幕及其 route_path
2. 对每个屏幕：
   a. 读取 stitch/*.png 作为基准截图（baseline）
   b. 用 Playwright 导航到对应 route_path
   c. 截取实际渲染截图
   d. 像素级对比（使用 Playwright 的 toHaveScreenshot 或 pixelmatch）
3. 差异评估阈值：
   | 差异率 | 评级 | 含义 |
   |--------|------|------|
   | ≤5% | PASS | 正常字体渲染/抗锯齿差异 |
   | 5-15% | INFO | 轻微布局偏差，可接受 |
   | 15-30% | WARNING | 明显偏差，需人工确认 |
   | >30% | FAIL | 还原度不合格 |
4. 输出：
   - `.allforai/product-verify/visual-regression/` 目录
   - `visual-regression-report.json`：
     [{ screen_id, baseline, actual, diff_percentage, rating }]
   - diff 图片：高亮差异区域

**注意**：Stitch 截图是设计参考，不是像素级基准。
阈值设置偏宽松，重点是发现「明显走样」而非追求像素完美。
```

---

## 不改动的部分

| 组件 | 是否改动 | 原因 |
|------|----------|------|
| e2e-verify | **改** | G10：新增视觉回归验证（Stitch 截图 vs 实际渲染对比） |
| product-verify | **不改** | 验收标准不变 |
| shared-utilities | **不改** | 共享组件识别已有独立机制 |
| project-setup | **不改** | 子项目拆分与 Stitch 无关 |

---

## 非阻断原则

| 条件 | 行为 |
|------|------|
| `component-spec.json` 存在 | **始终执行** Step 2.5 Layer 1（共享组件/原语/变体/a11y） |
| `component-spec.json` 不存在 | 跳过 Step 2.5，flow 与当前完全一致（向后兼容） |
| `stitch-index.json` 不存在 | Layer 1 正常执行，跳过 Layer 2（无视觉增强） |
| `stitch-index.json` 存在但全部 failed | Layer 1 正常执行，跳过 Layer 2，记录 warning |
| 部分屏幕有 Stitch、部分没有 | 有 Stitch 的用精确 DOM，没有的用 component-spec 推断 |
| Stitch HTML 解析失败 | 跳过该屏幕的 Layer 2，回退到 Layer 1 |
| 项目无前端子项目 | 完全不触发（Phase B 不执行） |

---

## 技术栈转换映射

Stitch HTML 结构 → 框架组件的转换，由 Claude 在 task-execute 阶段完成（非机械翻译）：

| Stitch HTML 元素 | React/Next.js | Vue/Nuxt | Flutter |
|------------------|---------------|----------|---------|
| `<header>` + `<nav>` | `<AppBar>` / `<Navbar>` | `<TheHeader>` | `AppBar` widget |
| `<div class="grid">` | CSS Grid / `<Grid>` 组件 | CSS Grid / `<el-row>` | `GridView` |
| `<button>` | `<Button>` (MUI/shadcn) | `<el-button>` / `<Button>` | `ElevatedButton` |
| `<input>` | `<TextField>` / `<Input>` | `<el-input>` / `<Input>` | `TextField` |
| `<ul><li>` 列表 | `<List>` + `.map()` | `v-for` + `<ListItem>` | `ListView.builder` |
| inline styles | CSS Modules / Tailwind | Scoped CSS / UnoCSS | Theme widget |

> Claude 理解 Stitch HTML 的**语义结构**后，用项目选定的组件库和设计 token 重新实现。
> 不是 HTML→JSX 的字符串替换，而是「看着视觉稿写代码」。

---

## 关键文件路径

| 文件 | 状态 | 说明 |
|------|------|------|
| `skills/design-to-spec.md` | 修改 | Phase B 加 Step 2.5（组件结构提取 + a11y 注入 + 变体矩阵） |
| `skills/task-execute.md` | 修改 | B3 Round 加 Stitch HTML 上下文 + 主题指令 + 变体实现指令 |
| `skills/e2e-verify.md` | 修改 | 新增视觉回归验证步骤（G10） |

---

## 验证方式

1. 准备一个有 `stitch-index.json` + `stitch/*.html` 的测试项目
2. 运行 `/design-to-spec` → 确认 design.md 中包含：
   - Stitch 组件树
   - 每个组件的 a11y 要求（G3）
   - 组件变体矩阵（G9）
   - 交互原语 + 技术栈实现（primitives）
3. 确认 tasks.md B3 任务有 `stitch_ref` 元数据
4. 运行 `/task-execute` B3 Round → 确认：
   - Claude 读取了 Stitch HTML 并生成了框架组件
   - 组件使用 CSS 变量而非硬编码颜色（G2 主题）
   - 组件包含 a11y 属性（G3）
   - 组件实现了所有标注的变体（G9）
5. 运行 e2e-verify → 确认视觉回归报告生成（G10）
6. 对比：有 Stitch vs 无 Stitch 的同一屏幕，视觉还原度差异
7. 确认无 Stitch 时所有流程正常回退（零影响）
