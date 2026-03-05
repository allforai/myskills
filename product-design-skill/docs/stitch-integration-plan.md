# 计划：Stitch 高质量 UI 嵌入 product-design 工作流

## Context

当前 `ui-design` 阶段（Phase 6）产出仅有文字规格（`ui-design-spec.md`）和基础 HTML 卡片预览，缺乏真实视觉稿。Google Stitch 可从文字描述生成高质量视觉 UI（HTML/CSS + 截图），且已有 MCP Server 接口（`@_davideast/stitch-mcp@0.4.0`）。

目标：
1. 在产品概念阶段让用户选择是否接入 Stitch
2. 独立脚本 `gen_ui_stitch.py` 构建 Stitch-ready prompts
3. `ui-design.md` 技能在 Phase 6 尾部执行 Stitch 调用（MCP 工具）

---

## MCP 验证结果（2026-03-05 实测）

### 工具清单

| 工具 | 类型 | 说明 |
|------|------|------|
| `create_project` | 创建 | 新建 Stitch 项目（设计容器），返回 projectId |
| `generate_screen_from_text` | **生成** | 从文本 prompt 生成新屏幕，支持 deviceType + modelId |
| `generate_variants` | 生成 | 基于已有屏幕生成变体 |
| `edit_screens` | 编辑 | 用文本 prompt 修改已有屏幕 |
| `list_projects` / `get_project` | 读取 | 项目管理 |
| `list_screens` / `get_screen` | 读取 | 屏幕列表/详情 |
| `get_screen_code` | 读取(虚拟) | 获取屏幕 HTML 代码 |
| `get_screen_image` | 读取(虚拟) | 获取屏幕截图（base64） |
| `build_site` | 构建(虚拟) | 屏幕映射为路由，生成 Astro 站点 |

### `generate_screen_from_text` 参数

```
输入：
  - projectId (required): Stitch 项目 ID（由 create_project 返回）
  - prompt (required): 文本描述
  - deviceType (optional): MOBILE | DESKTOP | TABLET | AGNOSTIC
  - modelId (optional): GEMINI_3_PRO | GEMINI_3_FLASH

输出：
  - projectId, sessionId
  - outputComponents[]: 生成结果（可能包含文本、建议、设计）
  - 后续可通过 get_screen_code / get_screen_image 获取 HTML 和截图
```

### 认证方式

**重要**：stitch-mcp 使用 **Google Cloud OAuth**，非 API Key。

```bash
# 初始化认证（一次性）
npx -y @_davideast/stitch-mcp init
# 选择 MCP 客户端（claude-code）→ 自动配置 OAuth

# 验证配置
npx -y @_davideast/stitch-mcp doctor
```

认证凭据存储在 `~/.stitch-mcp/` 目录，通过 gcloud application-default 管理。

---

## 架构说明（两层设计）

```
Phase 6: ui-design
  Step 1-5: 现有流程（spec.md + HTML cards）

  Step 5.3: [NEW] 组件规格生成（始终执行，通用路径）
    └─ Python: gen_ui_components.py → component-spec.json
       ├─ 从 screen-map 识别共享组件
       ├─ interaction_type → primitives 映射
       ├─ 推断组件变体（size/state）
       └─ 标注 a11y 要求

  Step 5.5: [NEW] Stitch 视觉生成（stitch_ui=true 时，增强路径）
    ├─ Python: gen_ui_stitch.py 读取 component-spec.json → stitch-prompts.json
    └─ Claude: 调用 Stitch MCP 工具 → ui-design/stitch/
       1. create_project(title) → projectId
       2. generate_screen_from_text(projectId, prompt, deviceType) × N
       3. get_screen_code(projectId, screenId) → HTML
       4. get_screen_image(projectId, screenId) → 截图 base64
```

**两层架构原则**：
- **Layer 1（通用）**：`gen_ui_components.py` + `component-spec.json` 始终执行，不依赖任何外部服务。
  所有生产级能力（共享组件、交互原语、变体、a11y）在此层完成。
- **Layer 2（增强）**：Stitch 是锦上添花，补充高质量视觉参考 + 精确 DOM 结构。
  无 Stitch 时全流程正常运行，只是少了视觉参考。

**Python 脚本负责**：数据准备、组件分析、prompt 构建、文件输出
**Claude 技能负责**：调用 Stitch MCP 工具（Python 无法直接调用 MCP）

---

## 改动清单

### 1. `docs/schemas/product-concept-schemas.md`
**位置**：`pipeline_preferences` 对象（当前第 52-56 行）
**改动**：新增 `stitch_ui` 字段

```json
"pipeline_preferences": {
  "ui_style": "material-design-3 | ...",
  "competitors": [...],
  "scope_strategy": "aggressive | balanced | conservative | undecided",
  "stitch_ui": true | false   // NEW：是否在 ui-design 阶段调用 Stitch 生成视觉稿
}
```

---

### 2. `skills/product-concept.md`
**位置**：Step 3.5 Pipeline Preferences（Q3 之后，约第 560 行）
**改动**：追加 Q4，写入 `stitch_ui`

```markdown
**Q4（可选）高质量 UI 视觉稿**

检测 Stitch MCP 可用性：
- 检查 MCP 工具 `mcp__plugin_product-design_stitch__create_project` 是否可用
- 可用 → 提示「Stitch 已就绪」，直接询问是否启用
- 不可用 → 提示「需先运行 `npx -y @_davideast/stitch-mcp init` 完成 Google 认证，
  现在跳过，后续可在 ui-design 阶段再启用」

AskUserQuestion:
  question: "是否在 UI 设计阶段使用 Stitch 生成高质量视觉稿？"
  options:
    - label: "是，启用 Stitch（推荐，需 Google 认证）"
      description: "自动为核心界面生成视觉 UI，可获取 HTML 代码和截图"
    - label: "否，使用文字规格"
      description: "生成 ui-design-spec.md + HTML 预览，不调用 Stitch"

写入：pipeline_preferences.stitch_ui = true | false
```

---

### 3. `scripts/gen_ui_components.py`（新建 — 通用，始终执行）
**职责**：从 screen-map 分析共享组件、交互原语、变体、a11y。不依赖 Stitch。

```
输入：
  - .allforai/screen-map/screen-map.json（或 screen-index.json 轻量加载）
  - .allforai/ui-design/ui-design-spec.md（style tokens）
  - .allforai/product-concept/product-concept.json（audience_type + platform_type）

处理流程：

  1. 加载所有屏幕的 interaction_type + actions + states
     索引优化：优先加载 screen-index.json（~3KB），不存在时回退 screen-map.json

  2. 跨屏幕共享组件识别：
     - 扫描所有屏幕，按 interaction_type 分组
     - 同一 interaction_type 出现在 ≥2 个屏幕 → 该类型的 UI 模式是共享组件
     - 相同 actions 模式（如多个屏幕都有 add-to-cart）→ 共享交互组件
     - 所有屏幕都有的结构（导航栏）→ AppShell 组件
     推断命名规则：
       MG1 列表 → {Entity}List
       MG2-C/E 表单 → {Entity}Form
       CT1 卡片 → {Entity}Card / {Entity}FeedItem
       通用导航 → AppShell
       通用搜索 → SearchBar

  3. 交互原语关联（interaction_type → primitives 映射）：
     内置映射表（同前文定义的 20+ 类型映射规则）

  4. 组件变体推断：
     - size：同一组件在不同屏幕的上下文差异（列表项 vs 详情页引用 → compact/default）
     - state：从 actions 的 states 字段 + screen states（empty/loading/error/disabled）
     - 所有交互组件默认有 ["default", "disabled"] 状态
     - 有 loading 相关 state 的组件追加 "loading" 变体
     - 有 selection 相关 action 的组件追加 "selected" 变体

  5. a11y 规格标注：
     按组件语义类型自动注入（内置规则表）：
     | 语义类型 | a11y 要求 |
     |----------|----------|
     | button | role=button, aria-label, focus-visible, min 44×44px |
     | form/input | label 关联, aria-required, aria-invalid, autocomplete |
     | list | role=list + role=listitem, aria-label |
     | image | alt text, decorative → alt="" |
     | navigation | role=navigation, aria-current=page |
     | dialog/modal | role=dialog, aria-modal, focus trap, Escape |
     | card (interactive) | role=article 或 button, tabindex=0 |
     | tab | role=tablist + tab + tabpanel, aria-selected |

  6. 屏幕→组件映射：
     记录每个屏幕使用了哪些共享组件 + 页面特有组件

输出：
  .allforai/ui-design/component-spec.json

运行方式：
  python3 gen_ui_components.py <BASE> [--mode auto]
```

---

### 4. `scripts/gen_ui_stitch.py`（新建 — Stitch 增强，条件执行）
**职责**：读取 component-spec.json，构建 Stitch prompt。不调用 Stitch（Python 无法调 MCP）。

```
输入：
  - .allforai/ui-design/component-spec.json（由 gen_ui_components.py 生成）
  - .allforai/screen-map/screen-map.json
  - .allforai/ui-design/ui-design-spec.md（style tokens）
  - .allforai/product-concept/product-concept.json（mission + 风格 + target_market）

屏幕优先级选择（动态，非硬编码）：
  基于 screen-map 元数据自动选屏，上限 10 个：
  P0（最多 5 个）：
    - 每个角色的入口屏（第一个 MG 类型的屏幕）
    - 核心表单屏（interaction_type 为 CT1/CT2 的屏幕）
  P1（补足至 10 个）：
    - 有 primary_action 的屏幕
    - states 数量 ≥ 3 的高复杂度屏幕
  可通过 --screens S010,S025 显式覆盖

生成策略（基于 component-spec.json，两阶段 prompt 构建）：

  **前置**：读取 component-spec.json 的 shared_components 作为 component_vocabulary。
  组件分析（共享组件、原语、变体、a11y）已由 gen_ui_components.py 完成，
  gen_ui_stitch.py 只负责将其转化为 Stitch prompt。

  **阶段 1：分层 prompt 构建**
  prompt 分为三层，保障跨屏幕一致性：

  Layer 1 — 设计系统指令（所有屏幕共享）：
    - App context（mission, target_market, language）
    - Design tokens（颜色/字体/圆角/间距，从 ui-design-spec.md 提取）
    - Component vocabulary（阶段 1 产出，明确组件命名和结构）
    - 一致性指令："All screens belong to the same app.
      Reuse these exact component patterns across screens:
      [vocabulary]. Same card style, same navigation, same button hierarchy."

  Layer 2 — 屏幕特定内容：
    - Screen purpose + primary action（从 screen-map 提取）
    - Actions（主操作/次操作）
    - States（从 screen-map states 字段提取）
    - 引用 vocabulary 中的组件：
      "This screen uses: AppShell, ProductCard(×N in grid), SearchBar"

  Layer 3 — 锚点屏引用（非首屏时）：
    - 首屏（P0 第一个）作为"锚点屏"独立生成
    - 后续屏幕的 prompt 追加：
      "Maintain visual consistency with the first screen in this project.
      Use the same component styles, spacing, and color application."

每个屏幕的 prompt 附加元数据：
  - deviceType 推断（mobile_app → MOBILE, web_app → DESKTOP, responsive → AGNOSTIC）
  - referenced_components: 该屏幕使用的 vocabulary 组件列表

输出：
  .allforai/ui-design/stitch-prompts.json
  格式：{
    generated_at, product_name, device_type,
    component_vocabulary: { ... },
    anchor_screen_id: "S010",
    screens: [{
      screen_id, screen_name, priority, prompt,
      device_type, model_id,
      referenced_components, generation_order,
      style_hint, source_fields
    }]
  }

运行方式：
  python3 gen_ui_stitch.py <BASE> [--screens S010,S025] [--mode auto] [--limit 10]

检查 pipeline_preferences.stitch_ui：
  false → 仍生成 stitch-prompts.json（供手动使用），不阻塞
  true  → 正常运行，后续 Claude 技能读取并调 Stitch MCP
```

---

### 5. `skills/ui-design.md`
**位置**：Step 5（HTML 预览）之后，design-decisions 记录之前
**改动**：新增 Step 5.3（通用）+ Step 5.5（Stitch 增强）

```markdown
### Step 5.3：组件规格生成（始终执行）

运行组件分析脚本：
```
python3 <SCRIPTS>/gen_ui_components.py <BASE> --mode auto
```

输出：`ui-design/component-spec.json`
- 共享组件识别（跨屏幕复用模式）
- 交互原语关联（interaction_type → primitives）
- 组件变体推断（size/state）
- a11y 规格标注（按组件类型）
- 屏幕→组件映射

**此步骤不依赖任何外部服务，始终执行。**
即使用户不使用 Stitch，component-spec.json 也会被 dev-forge 消费，
用于生成共享组件规格、注入 a11y、关联交互原语实现方案。
```

```markdown
### Step 5.5：Stitch 视觉生成（条件执行）

**跳过条件**：`pipeline_preferences.stitch_ui ≠ true`

**补充入口**：如果 `stitch_ui` 字段不存在（用户单独跑了 /product-concept）
且 Stitch MCP 工具可用 → 主动询问是否启用，写入 pipeline_preferences

**执行流程**：

1. 运行 prompt 构建脚本：
   ```
   python3 <SCRIPTS>/gen_ui_stitch.py <BASE> --mode auto
   ```
   输出：`ui-design/stitch-prompts.json`（最多 10 个屏幕的结构化 prompt）

2. 检测 Stitch MCP 可用性：
   - 检查 MCP 工具 `mcp__plugin_product-design_stitch__create_project` 是否可用
   - 不可用 → 跳转 3b

3a. **可用** → 执行 Stitch 两阶段生成流程：

   **阶段 A：锚点屏生成**
   i.    调用 `create_project(title="产品名-ui-design")` → 获得 projectId
   ii.   从 stitch-prompts.json 取 anchor_screen（P0 第一个，最复杂的屏幕）
   iii.  调用 `generate_screen_from_text(projectId, anchor_prompt, deviceType)`
         - 此屏幕建立整个项目的视觉语言
         - 注意：可能需要几分钟，不要重试
   iv.   获取锚点屏结果：
         - `get_screen_code(projectId, screenId)` → HTML
         - `get_screen_image(projectId, screenId)` → 截图
   v.    写入 `ui-design/stitch/` 并记录 stitch-index.json

   **阶段 B：后续屏幕生成（引用锚点）**
   vi.   对 stitch-prompts.json 中剩余屏幕，按 generation_order 逐个生成：
         - 每个 prompt 已包含 component_vocabulary + 锚点屏引用指令
         - 调用 `generate_screen_from_text(projectId, prompt, deviceType)`
         - 同一 projectId 下生成，Stitch 自动维持项目级一致性
   vii.  逐个获取 HTML + 截图，写入 `ui-design/stitch/`

   **阶段 C：一致性检查与修正**
   viii. 对所有生成的 HTML 做快速一致性检查：
         - 比较各屏幕中 component_vocabulary 引用组件的 CSS 类名/结构
         - 如果发现明显偏差（如 ProductCard 在不同屏幕结构不同）：
           调用 `edit_screens(projectId, screenId, "Make the ProductCard
           component match the style from screen [anchor_screen_name]:
           same border-radius, same shadow, same padding, same image ratio")`
         - 重新获取修正后的 HTML
   ix.   最终更新 `ui-design/stitch-index.json`，增加一致性检查结果：
         `consistency_check: { passed: true/false, corrections: [...] }`

3b. **不可用** → 仅输出 prompts，展示手动使用说明：
   ```
   Stitch MCP 未配置，已生成 stitch-prompts.json。
   手动使用：
   1. 运行 `npx -y @_davideast/stitch-mcp init` 完成 Google 认证
   2. 访问 stitch.withgoogle.com，粘贴各屏幕 prompt 生成视觉稿
   3. 或重新运行 /ui-design 自动调用 Stitch
   ```

**输出文件**：
  - `ui-design/component-spec.json`（Step 5.3 始终生成，通用）
  - `ui-design/stitch-prompts.json`（Step 5.5 始终生成）
  - `ui-design/stitch/`（Stitch MCP 可用时）
  - `ui-design/stitch-index.json`（Stitch MCP 可用时）
```

---

### 5. `.mcp.json`
**位置**：`product-design-skill/.mcp.json`
**改动**：追加 stitch server（使用 proxy 子命令）

```json
{
  "mcpServers": {
    "openrouter": { ... },
    "stitch": {
      "command": "npx",
      "args": ["-y", "@_davideast/stitch-mcp", "proxy"],
      "env": {}
    }
  }
}
```

> 注：stitch-mcp 使用 Google Cloud OAuth（~/.stitch-mcp/ 凭据），不需要环境变量。
> 未认证时 MCP Server 启动会失败并输出认证提示，不影响主流程。
> `proxy` 子命令启动 MCP proxy server，暴露所有上游 Stitch 工具。

---

## 输出 Schema 定义

### `component-spec.json`（通用，始终生成）

```json
{
  "generated_at": "2026-03-05T10:00:00Z",
  "source": "screen-map",
  "shared_components": {
    "AppShell": {
      "screens": ["S010","S020","S030"],
      "inferred_from": "所有屏幕共有的导航结构",
      "structure": "TopBar + Content + BottomNav",
      "props": ["title","showBack","showSearch","activeTab"],
      "primitives": [],
      "variants": {
        "state": ["default","loading"]
      },
      "a11y": {
        "role": "navigation",
        "requirements": ["aria-current=page on active tab", "role=navigation on nav"]
      }
    },
    "ProductCard": {
      "screens": ["S010","S030","S060"],
      "inferred_from": "同一 interaction_type:MG1 + 相同 actions 模式",
      "props": ["image","name","price","rating"],
      "primitives": [],
      "variants": {
        "size": ["compact","default","featured"],
        "state": ["default","selected","disabled","loading"]
      },
      "a11y": {
        "role": "article",
        "requirements": ["alt on image","tabindex=0 if clickable"]
      }
    },
    "ProductList": {
      "screens": ["S030","S060"],
      "inferred_from": "MG1 列表容器",
      "props": ["items","onLoadMore","onRefresh"],
      "primitives": ["VirtualList","InfiniteScroll","PullToRefresh"],
      "variants": {
        "layout": ["list","grid"],
        "state": ["default","empty","loading","error"]
      },
      "a11y": {
        "role": "list",
        "requirements": ["aria-label","role=listitem on children"]
      }
    }
  },
  "screen_components": {
    "S010": {
      "used_shared": ["AppShell","ProductCard","ProductList","SearchBar"],
      "page_specific": ["HeroBanner"],
      "interaction_type": "MG1",
      "primitives": ["VirtualList","PullToRefresh"]
    }
  },
  "primitive_mapping": {
    "VirtualList": "MG1, MG2-L, MG5",
    "InfiniteScroll": "CT1, WK1",
    "FormWithValidation": "MG2-C, MG2-E, MG8, SY2, SB1",
    "DragAndDrop": "WK5, WK7",
    "StateMachine": "MG3, MG2-ST, SB1"
  }
}
```

### `stitch-prompts.json`

```json
{
  "generated_at": "2026-03-05T10:00:00Z",
  "product_name": "产品名",
  "device_type": "MOBILE",
  "total_screens": 10,
  "screens": [
    {
      "screen_id": "S010",
      "screen_name": "买家首页",
      "priority": "P0",
      "selection_reason": "role_entry:R01 + interaction_type:MG1",
      "prompt": "Design a mobile home screen for...",
      "device_type": "MOBILE",
      "model_id": "GEMINI_3_PRO",
      "style_hint": "Material Design 3, primary=#6750A4"
    }
  ]
}
```

### `stitch-index.json`

```json
{
  "generated_at": "2026-03-05T10:30:00Z",
  "stitch_project_id": "4044680601076201931",
  "stitch_project_url": "https://stitch.withgoogle.com/project/...",
  "tool_version": "@_davideast/stitch-mcp@0.4.0",
  "consumer_note": "设计源文件，由 dev-forge 转换为项目技术栈组件。组件规格见 component-spec.json",
  "component_spec_ref": "ui-design/component-spec.json",
  "anchor_screen_id": "S010",
  "consistency_check": {
    "passed": true,
    "corrections": [
      { "screen_id": "S030", "component": "ProductCard", "action": "aligned border-radius to anchor" }
    ]
  },
  "screens": [
    {
      "screen_id": "S010",
      "screen_name": "买家首页",
      "priority": "P0",
      "status": "success",
      "stitch_screen_id": "abc123",
      "local_files": {
        "html": "stitch/S010-买家首页.html",
        "screenshot": "stitch/S010-买家首页.png"
      },
      "route_path": "/home",
      "interaction_type": "MG1",
      "target_component": null,
      "error": null
    }
  ],
  "summary": {
    "total": 10,
    "success": 8,
    "failed": 1,
    "skipped": 1
  }
}
```

---

## 跨插件数据流

### Stitch 产出的消费定位

Stitch 生成的 HTML/CSS 定位为 **设计源文件**（design source of truth），由 dev-forge 转换为项目技术栈的生产组件。

工作流：
```
Stitch HTML/CSS（设计源）
    ↓ dev-forge 读取
转换为项目组件（React/Vue/Svelte 等）
    ↓ 保留视觉还原度
生产代码（集成到项目技术栈）
```

### 下游消费方式

| 消费者 | 读取文件 | 用途 | 必需性 |
|--------|----------|------|--------|
| `dev-forge` | `stitch-index.json` + `stitch/*.html` | **核心输入**：读取 Stitch HTML，转换为项目技术栈组件（React/Vue 等），保留视觉还原度 | stitch_ui=true 时必读 |
| `dev-forge` | `ui-design-spec.md` | 设计 token（颜色/字体/间距），与 Stitch HTML 中的样式对齐 | 始终必读 |
| 人类（PM/设计师） | `stitch/*.png` | 视觉审阅，确认设计方向后再进入开发 | 推荐 |
| `demo-forge` | `stitch-index.json` + `stitch/*.html` | 直接使用 Stitch HTML 作为 demo 页面 | 可选 |
| `design-audit` | `stitch-index.json` | 审计视觉稿覆盖率 | 可选 |

### dev-forge 对接要求

dev-forge 的 `task-execute` 阶段需新增 **Stitch 组件转换** 能力：

1. **检测**：读取 `stitch-index.json`，检查 `status=success` 的屏幕列表
2. **解析**：对每个 Stitch HTML 文件，提取结构（组件树、样式、交互元素）
3. **转换**：根据项目技术栈（`dev-spec` 中定义），将 HTML 结构转换为：
   - 组件文件（如 `HomePage.tsx`）
   - 样式文件（CSS Modules / Tailwind / styled-components，取决于项目配置）
   - 提取 Stitch 内联样式 → 对齐 `ui-design-spec.md` 的 design tokens
4. **映射**：`stitch-index.json` 中的 `screen_id` 与 `screen-map.json` 的路由映射关联

> 注：dev-forge 侧的具体实现属于 dev-forge-skill 的改动范围，
> 本计划只定义 product-design 侧的输出契约。
> dev-forge 需要一个对应的计划文档来详细设计转换逻辑。

---

## 生产级 UI 补强（G1-G10）

Stitch HTML → 生产代码的完整链路需要补强 10 个维度。按职责分层：

### product-design 侧改动（ui-design Step 4 规格补强）

以下规格改动独立于 Stitch，提升 ui-design-spec.md 的完整度。
在 `skills/ui-design.md` Step 4 生成 ui-design-spec.md 时增加以下章节：

**G1. 响应式设计**（新增 `## 响应式策略` 章节）
```markdown
## 响应式策略

断点定义（从 product-concept 推断 platform_type）：
- mobile_app → 不需要断点（原生布局系统）
- web_app / responsive →
  | 断点 | 宽度 | 布局变化 |
  |------|------|----------|
  | sm   | <640px  | 单列，BottomNav，全宽卡片 |
  | md   | 640-1024px | 双列网格，侧边导航可折叠 |
  | lg   | >1024px | 三列网格，固定侧边栏 |

容器策略：max-width: 1280px, 居中
组件适配规则：
- Card grid: 1col(sm) → 2col(md) → 3-4col(lg)
- Navigation: BottomNav(sm) → SideNav(md+)
- Table: 横滚(sm) → 完整显示(md+)
```

**G4. 间距系统**（新增 `## 间距标度` 章节）
```markdown
## 间距标度

基础单位：4px
标度：
| token | 值 | 用途 |
|-------|-----|------|
| --space-1 | 4px | 图标与文字间距 |
| --space-2 | 8px | 组件内边距（紧凑） |
| --space-3 | 12px | 组件内边距（默认） |
| --space-4 | 16px | 卡片内边距、列表项间距 |
| --space-6 | 24px | 区块间距 |
| --space-8 | 32px | 页面区域间距 |
| --space-12 | 48px | 大区块分隔 |
```

**G5. 排版标度**（补强现有 `## 排版` 章节）
```markdown
## 排版标度

| token | 字号 | 行高 | 字重 | 字间距 | 用途 |
|-------|------|------|------|--------|------|
| --text-display | 36px | 1.2 | 700 | -0.5px | 首屏标题 |
| --text-h1 | 28px | 1.3 | 700 | -0.25px | 页面标题 |
| --text-h2 | 22px | 1.35 | 600 | 0 | 区块标题 |
| --text-h3 | 18px | 1.4 | 600 | 0 | 卡片标题 |
| --text-body | 16px | 1.5 | 400 | 0 | 正文 |
| --text-body-sm | 14px | 1.45 | 400 | 0.1px | 辅助文字 |
| --text-caption | 12px | 1.4 | 400 | 0.2px | 标注、时间戳 |
```

**G6. 动效 Token**（新增 `## 动效规范` 章节）
```markdown
## 动效规范

| token | 值 | 用途 |
|-------|-----|------|
| --duration-fast | 150ms | 按钮反馈、开关切换 |
| --duration-normal | 250ms | 页面转场、模态弹出 |
| --duration-slow | 400ms | 复杂动画、展开收起 |
| --easing-standard | cubic-bezier(0.4, 0, 0.2, 1) | 大部分转场 |
| --easing-decelerate | cubic-bezier(0, 0, 0.2, 1) | 进入屏幕 |
| --easing-accelerate | cubic-bezier(0.4, 0, 1, 1) | 离开屏幕 |

原则：
- prefers-reduced-motion 时所有动画降为 0ms
- 交互反馈（按钮、开关）使用 fast
- 布局变化（展开、折叠、页面切换）使用 normal
- 首次加载动画使用 slow
```

**G7. 图标系统**（新增 `## 图标规范` 章节）
```markdown
## 图标规范

图标库选型（根据 ui_style 推断）：
| ui_style | 推荐图标库 | 备选 |
|----------|-----------|------|
| material-design-3 | Material Symbols | Phosphor |
| apple-hig | SF Symbols (iOS) / Lucide (Web) | Heroicons |
| fluent-design | Fluent UI Icons | — |
| ant-design | Ant Design Icons | — |
| shadcn-tailwind | Lucide | Radix Icons |
| 其他 | Lucide（通用性最好） | Phosphor |

尺寸标度：
| 用途 | 尺寸 | 示例 |
|------|------|------|
| 内联（按钮图标） | 16px / 20px | 编辑、删除按钮 |
| 标准（列表、导航） | 24px | 导航栏图标 |
| 特征（空状态、引导） | 48px / 64px | 空列表提示图 |
```

**G2. 深浅主题**（新增 `## 主题变体` 章节）
```markdown
## 主题变体

默认生成 light theme token。dark theme 通过语义映射自动派生：
| 语义 token | light 值 | dark 值（自动派生规则） |
|------------|----------|------------------------|
| --surface | #FFFFFF | #1C1B1F |
| --on-surface | #1C1B1F | #E6E1E5 |
| --surface-container | #F3EDF7 | #2B2930 |
| --primary | 保持不变 | 保持不变 |
| --on-primary | 保持不变 | 保持不变 |
| --elevation-1 | shadow | lighter surface-container |

派生规则：
- 背景色：反转亮度（HSL L 通道取反）
- 前景色：反转亮度
- 品牌色（primary/secondary）：保持不变
- 阴影：dark 模式下用 surface 层级差异替代阴影
```

### product-design 侧改动（Stitch prompt 增强）

**G1-stitch**：`gen_ui_stitch.py` prompt Layer 1 增加响应式提示
```
Layer 1 追加：
"Design for [deviceType] as primary viewport.
 Use flexible layouts (flexbox/grid) that can adapt to different screen sizes.
 Avoid fixed pixel widths on containers — use percentage or max-width."
```

**G9. 组件变体标注**：`component_vocabulary` 新增 `variants` 字段
```json
"ProductCard": {
  "screens": ["S010","S030"],
  "props": ["image","name","price","rating"],
  "primitives": [],
  "variants": {
    "size": ["compact", "default", "featured"],
    "state": ["default", "selected", "disabled", "loading"]
  }
}
```
变体维度从 screen-map 推断：
- 同一组件在不同屏幕出现大小不同 → `size` variants
- 组件关联的 actions 有 disabled/loading 状态 → `state` variants
- 所有交互组件默认有 `["default", "disabled"]` 状态

### dev-forge 侧改动

以下补强写入 `dev-forge-skill/docs/stitch-conversion-plan.md`。

**G3. 无障碍（a11y）**：design-to-spec Step 2.5 新增 a11y 规则注入
```
对每个共享组件，根据组件类型自动注入 a11y 要求：
| 组件类型 | a11y 要求 |
|----------|----------|
| Button | role="button", aria-label, :focus-visible outline, min 44×44px touch target |
| Input/Form | <label> 关联, aria-required, aria-invalid + error message, autocomplete |
| List | role="list" + role="listitem", aria-label for container |
| Image | alt text (从 screen-map 的 screen_name 推断), decorative → alt="" |
| Navigation | role="navigation", aria-current="page" for active |
| Modal/Dialog | role="dialog", aria-modal, focus trap, Escape 关闭 |
| Card (interactive) | role="article" 或 role="button"（可点击时）, tabindex="0" |

写入 design.md 每个组件的 `### 无障碍` 小节。
```

**G2-dev**：task-execute 增加主题支持指令
```
B3 任务上下文追加：
"实现组件时，使用 CSS 变量 / theme token 而非硬编码颜色值。
 参考 ui-design-spec.md 的「主题变体」章节，确保组件支持 light/dark 切换。
 如果项目技术栈有 ThemeProvider（MUI/shadcn/AntD），使用它而非自定义方案。"
```

**G9-dev**：task-execute 增加变体实现指令
```
读取 component_vocabulary 中每个组件的 variants 字段。
B3 共享组件任务需要实现所有标注的变体：
- size variants → 通过 props 控制（className/size prop）
- state variants → 通过 props + CSS 控制（disabled/loading/selected）
每个变体需要在 Storybook / 组件文档中有示例（如果项目使用 Storybook）。
```

**G10. 视觉回归验证**：e2e-verify 新增截图对比
```
当 stitch-index.json 存在时，e2e-verify 增加视觉回归步骤：

1. 读取 stitch/*.png 作为基准截图（baseline）
2. 启动开发服务器，用 Playwright 截取对应路由的实际渲染截图
3. 像素级对比（允许 5% 差异阈值，Stitch 与实际渲染不可能 100% 一致）
4. 输出 visual-regression-report.json：
   { screen_id, baseline_path, actual_path, diff_percentage, passed }
5. 差异 >15% 的标记为 WARNING，>30% 标记为 FAIL
6. 截图对比结果写入 .allforai/product-verify/visual-regression/

阈值说明：
- Stitch 截图是设计参考，不是像素级基准
- 5% 以内：正常的字体渲染/抗锯齿差异
- 5-15%：轻微布局偏差，可接受
- 15-30%：明显偏差，需要人工确认
- >30%：还原度不合格
```

---

## 非阻断原则

| 条件 | 行为 |
|------|------|
| `stitch_ui=false` | 跳过 Step 5.5，正常完成 |
| `stitch_ui` 字段不存在 + MCP 可用 | 主动询问是否启用 |
| `stitch_ui=true` + MCP 不可用 | 输出 stitch-prompts.json，提示认证方式 |
| `stitch_ui=true` + MCP 调用失败 | 记录 warning，跳过失败项，继续 |
| Stitch 生成部分失败 | 成功的写入，失败的跳过，不回滚 |

---

## 动态选屏策略（替代硬编码）

```python
def select_priority_screens(screens, limit=10):
    """基于 screen-map 元数据动态选择优先屏幕"""
    scored = []
    for s in screens:
        score = 0
        it = s.get("interaction_type", "")

        # P0 信号：角色入口屏
        if it.startswith("MG"):
            score += 10  # 管理/导航类屏幕
        # P0 信号：核心表单
        if it in ("CT1", "CT2"):
            score += 8   # 创建/编辑表单

        # P1 信号
        if s.get("primary_action"):
            score += 3
        state_count = len(s.get("states", []))
        if state_count >= 3:
            score += 2
        # 有多个 actions 的屏幕更复杂
        if len(s.get("actions", [])) >= 3:
            score += 1

        scored.append((score, s["screen_id"], s))

    scored.sort(key=lambda x: -x[0])
    selected = scored[:limit]

    # 标记优先级
    result = []
    for i, (score, sid, s) in enumerate(selected):
        priority = "P0" if i < 5 else "P1"
        result.append({**s, "priority": priority, "selection_score": score})
    return result
```

---

## 关键文件路径

| 文件 | 状态 | 说明 |
|------|------|------|
| `skills/product-concept.md` | 修改 | 第 560 行附近加 Q4 |
| `docs/schemas/product-concept-schemas.md` | 修改 | 第 52-56 行加 stitch_ui |
| `scripts/gen_ui_components.py` | **新建** | ~200 行，通用组件分析（共享组件/原语/变体/a11y） |
| `scripts/gen_ui_stitch.py` | **新建** | ~120 行，Stitch prompt 构建（读取 component-spec.json） |
| `skills/ui-design.md` | 修改 | Step 5 后加 Step 5.3（通用）+ Step 5.5（Stitch） |
| `.mcp.json` | 修改 | 追加 stitch proxy server（5行） |

---

## 可复用的现有工具

- `_common.py: xv_available()` — 参考其检测模式（改为检测 MCP 工具可用性）
- `_common.py: parse_args()` — 脚本参数解析（含 --mode auto）
- `_common.py: load_screen_map()` — 读取 screen-map.json
- `_common.py: load_product_concept()` — 读取 product-concept.json
- `_common.py: write_json()` + `ensure_dir()` — 文件输出
- `_common.py: append_pipeline_decision()` — 决策日志
- `xv_prompts.py` — 参考 prompt 构建模式

---

## 修订记录

### v2（2026-03-05）— 基于架构分析 + MCP 实测

| # | 原方案问题 | 修订内容 |
|---|-----------|----------|
| 1 | 硬编码屏幕 ID（S010/S020 等特定产品） | 改为基于 screen-map 元数据动态选屏（interaction_type, primary_action, states） |
| 2 | 输出 schema 缺失（stitch-index.json 无定义） | 新增完整 stitch-prompts.json + stitch-index.json schema |
| 3 | 认证方式错误（写 STITCH_API_KEY 环境变量） | 改为 Google Cloud OAuth，通过 `stitch-mcp init` 认证 |
| 4 | 缺少 create_project 步骤 | 在 Step 5.5 执行流程中加入 create_project → projectId |
| 5 | 跨插件数据流未定义 | 新增「跨插件数据流」节，明确 Stitch 产出为参考视觉稿 |
| 6 | product-concept Q4 仅在 full-pipeline 触发 | 在 ui-design Step 5.5 加补充入口：字段不存在 + MCP 可用时主动询问 |
| 7 | prompt 中硬编码业务知识（IC001、日文市场） | 改为从 product-concept.json 动态提取 mission/target_market/language |
| 8 | `.mcp.json` 写法不对 | 改为 `proxy` 子命令，移除无效的 STITCH_API_KEY env |
| 9 | MCP 输出格式不明（.{ext}） | 明确为 .html（代码）+ .png（截图 base64 解码） |
| 10 | 大型项目索引优化未考虑 | gen_ui_stitch.py 优先加载 screen-index.json（~3KB） |
| 11 | Stitch 产出定位为「参考」 | 改为「设计源文件」，dev-forge 必须消费并转换为项目组件 |
| 12 | stitch-index.json 缺少路由映射 | 新增 route_path/interaction_type/target_component 字段供 dev-forge 使用 |
| 13 | dev-forge 对接未定义 | 新增 dev-forge 组件转换要求（检测→解析→转换→映射四步） |
| 14 | 各屏幕独立生成，组件风格不一致 | 改为两阶段生成：先建组件词汇表 → 锚点屏 → 后续屏引用 → 一致性修正 |
| 15 | prompt 无跨屏幕组件复用指令 | prompt 分三层：设计系统指令 + 屏幕内容 + 锚点屏引用 |
| 16 | stitch-index.json 无组件信息 | 新增 component_vocabulary + consistency_check 字段 |
| 17 | component_vocabulary 只有视觉维度 | 扩展为视觉+交互双维度，每个组件标注关联的 behavioral primitives |
| 18 | interaction_type→primitive 映射未内置 | gen_ui_stitch.py 内置 20+ 类型的原语映射规则 |
| 19 | ui-design-spec.md 无响应式断点 | 新增「响应式策略」章节（G1），根据 platform_type 推断断点 |
| 20 | ui-design-spec.md 无间距系统 | 新增「间距标度」章节（G4），4px 基础单位 |
| 21 | ui-design-spec.md 排版不完整 | 补强排版标度（G5），增加 line-height/letter-spacing/scale |
| 22 | 无动效规范 | 新增「动效规范」章节（G6），定义 duration/easing token |
| 23 | 无图标系统 | 新增「图标规范」章节（G7），根据 ui_style 推荐图标库 |
| 24 | 无深浅主题 | 新增「主题变体」章节（G2），语义 token light/dark 派生规则 |
| 25 | 组件无变体定义 | component_vocabulary 新增 variants 字段（G9） |
| 26 | 无视觉回归验证 | dev-forge e2e-verify 新增截图对比（G10） |
| 27 | 无 a11y 自动注入 | dev-forge design-to-spec 按组件类型注入 a11y 规格（G3） |
| 28 | 生产级能力绑定 Stitch | 拆为两层：gen_ui_components.py（通用）+ gen_ui_stitch.py（增强） |
| 29 | 无 Stitch 时 dev-forge 无组件规格 | 新增 component-spec.json（始终生成），dev-forge Step 2.5 始终触发 |
| 30 | stitch-index.json 重复 vocabulary | 改为 component_spec_ref 引用，不再重复存储 |

---

## 验证方式

1. 运行 `python3 gen_ui_stitch.py <BASE>` → 确认 `stitch-prompts.json` 生成，屏幕按元数据动态选择
2. 运行 `npx -y @_davideast/stitch-mcp doctor` → 确认认证状态
3. 运行 `npx -y @_davideast/stitch-mcp tool` → 确认工具列表包含 `generate_screen_from_text`
4. 运行 full product-concept → 确认 Q4 出现在 Step 3.5 最后
5. 读 `product-concept.json` → 确认 `pipeline_preferences.stitch_ui` 字段写入
6. 跑 full ui-design → 确认 Step 5.5 在 `stitch_ui=true` 时触发，`false` 时跳过
7. 验证 stitch-index.json 符合定义的 schema
