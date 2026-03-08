# Review Hub Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace 5 standalone review servers with a single unified Review Hub on port 18900, serving 6 tabs (concept/map/data-model/wireframe/ui/spec) with shared navigation, mind map rendering, and feedback APIs.

**Architecture:** One Python HTTP server (`review_hub_server.py`) using `http.server`, routing requests by URL path prefix (`/concept`, `/map`, `/data-model`, `/wireframe`, `/ui`, `/spec`). Each tab reuses extracted rendering logic from the old servers. Shared nav bar shows tab availability via product artifact detection. Feedback storage paths unchanged (backward compatible).

**Tech Stack:** Python 3 stdlib (`http.server`, `json`, `os`), inline HTML/CSS/JS (same pattern as existing servers), SVG mind map rendering, iframe-based preview panels.

---

## Dependencies & Context

- **Design doc:** `docs/plans/2026-03-09-review-hub-design.md`
- **Existing servers to merge:**
  - `product-design-skill/scripts/mindmap_review_server.py` (940 lines) — concept + map tabs
  - `product-design-skill/scripts/wireframe_review_server.py` (1475 lines) — wireframe tab
  - `product-design-skill/scripts/datamodel_review_server.py` (949 lines) — data-model tab
  - `product-design-skill/scripts/ui_review_server.py` (820 lines) — ui tab
- **Common module:** `product-design-skill/scripts/_common.py` (781 lines)
- **Git branch:** `feat/wireframe-quality-upgrade`

## Task Overview

| # | Task | Key Files | Est. |
|---|------|-----------|------|
| 1 | Shared nav bar + tab detection | `review_hub_server.py` (NEW) | 20 min |
| 2 | Concept tab (mind map) | `review_hub_server.py` | 15 min |
| 3 | Map tab (mind map + patterns) | `review_hub_server.py` | 15 min |
| 4 | Data-model tab (mind map) | `review_hub_server.py` | 15 min |
| 5 | Wireframe tab (tree + preview) | `review_hub_server.py` | 30 min |
| 6 | UI tab (tree + preview) | `review_hub_server.py` | 20 min |
| 7 | Spec tab (mind map) | `review_hub_server.py` | 20 min |
| 8 | Feedback APIs (all tabs) | `review_hub_server.py` | 15 min |
| 9 | Home page (tab cards + status) | `review_hub_server.py` | 10 min |
| 10 | `/review` command + skill wiring | `commands/review.md`, `SKILL.md` | 15 min |
| 11 | Delete old commands + servers | 5 commands, 4 scripts | 10 min |
| 12 | Update `product-design.md` orchestrator | `commands/product-design.md` | 15 min |
| 13 | Update `_common.py` | `scripts/_common.py` | 5 min |
| 14 | dev-forge design.json output | `dev-forge-skill/skills/design-to-spec.md` | 20 min |
| 15 | Integration test | Manual test | 15 min |

---

### Task 1: Server Skeleton + Shared Nav Bar + Tab Detection

**Files:**
- Create: `product-design-skill/scripts/review_hub_server.py`

**Step 1: Create server skeleton with tab detection and shared nav**

Create the file with:
- CLI args parsing via `_common.parse_args()` (BASE path, --port 18900, --host, --no-open)
- Tab availability detection: scan `.allforai/` for each tab's data source files
- Shared nav bar HTML generator function `render_nav(active_tab)` returning the top navigation with 6 tab links, availability indicators (● / ○), and current tab highlighting
- `ReviewHubHandler` class extending `http.server.BaseHTTPRequestHandler`
- URL routing: `/` → home, `/concept` → concept tab, `/map` → map tab, etc.
- Server startup with `HTTPServer`

Tab detection logic:

```python
def detect_tabs():
    """Detect which tabs have data available."""
    tabs = {}
    tabs["concept"] = os.path.exists(os.path.join(BASE, "product-concept/product-concept.json"))
    tabs["map"] = os.path.exists(os.path.join(BASE, "product-map/task-inventory.json"))
    tabs["data-model"] = os.path.exists(os.path.join(BASE, "product-map/entity-model.json"))
    tabs["wireframe"] = os.path.exists(os.path.join(BASE, "experience-map/experience-map.json"))
    tabs["ui"] = os.path.exists(os.path.join(BASE, "ui-design/ui-design-spec.json"))
    tabs["spec"] = any(
        os.path.exists(os.path.join(BASE, "project-forge/sub-projects", d, "design.json"))
        for d in (os.listdir(os.path.join(BASE, "project-forge/sub-projects")) if os.path.isdir(os.path.join(BASE, "project-forge/sub-projects")) else [])
    )
    return tabs
```

Nav bar structure (from design doc lines 29-38):
```
┌──────────────────────────────────────────────────────┐
│  Review Hub    [概念] [地图] [数据模型] [线框] [UI] [规格]  │
│                 ●      ●      ●         ●     ○    ○     │
└──────────────────────────────────────────────────────┘
```

Key CSS classes to port from `mindmap_review_server.py:297-312`:
- `.header` — shared header bar
- Tab links with active state highlighting
- Availability dot indicators

**Step 2: Run syntax check**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/review_hub_server.py', doraise=True)"`
Expected: No errors

**Step 3: Commit**

```bash
git add product-design-skill/scripts/review_hub_server.py
git commit -m "feat(review-hub): server skeleton with shared nav bar and tab detection"
```

---

### Task 2: Concept Tab (Mind Map)

**Files:**
- Modify: `product-design-skill/scripts/review_hub_server.py`

**Step 1: Extract and adapt concept mind map rendering**

Port from `mindmap_review_server.py`:
- `_node()` helper (line 44-52) — already generic, reuse as `_node(nid, label, ntype, detail, children, tags)`
- `load_concept_tree()` (line 55) — loads `product-concept/product-concept.json`, builds tree
- `render_page()` (line 282) — the massive HTML/CSS/JS for XMind-style radial mind map

Key adaptations:
1. Replace standalone header with shared nav bar from Task 1
2. Feedback path: `concept-review/review-feedback.json` (unchanged)
3. Comment panel categories: General, Feature, Concept, Flow (from `mindmap_review_server.py`)
4. Submit button POSTs to `/api/concept/feedback`
5. Add `collect_all_node_ids(tree)` helper for progress tracking

The mind map rendering is the largest shared component (~400 lines of HTML/CSS/JS). Extract it as `render_mindmap_page(tree, feedback, title, tab_id, categories)` so concept/map/data-model/spec tabs all reuse it.

**Step 2: Verify concept tab renders**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/review_hub_server.py', doraise=True)"`

**Step 3: Commit**

```bash
git add product-design-skill/scripts/review_hub_server.py
git commit -m "feat(review-hub): concept tab with mind map rendering"
```

---

### Task 3: Map Tab (Mind Map + Shared Patterns)

**Files:**
- Modify: `product-design-skill/scripts/review_hub_server.py`

**Step 1: Port map tree loader with shared patterns branch**

Port from `mindmap_review_server.py`:
- `load_product_map_tree()` (line 160) — loads `role-profiles.json`, `task-inventory.json`, `business-flows.json`
- Tree structure (from design doc lines 89-110):
  ```
  产品地图
  ├── R001 商户 [primary]
  │   ├── 核心任务 / 基本任务
  │   └── ...
  ├── 业务流
  └── 共性模式 (NEW branch from pattern-catalog.json + behavioral-standards.json)
  ```

Add shared patterns branch to the map tree:
- Load `pattern-catalog.json` (optional) → CRUD台, 审批流, etc.
- Load `behavioral-standards.json` (optional) → 删除确认, 空状态, 加载模式, etc.
- Append as children of root node under "共性模式" group

Feedback categories: role, task, flow, pattern (add pattern for shared patterns)
Feedback path: `product-map-review/review-feedback.json` (unchanged)

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/review_hub_server.py', doraise=True)"`

**Step 3: Commit**

```bash
git add product-design-skill/scripts/review_hub_server.py
git commit -m "feat(review-hub): map tab with shared patterns branch"
```

---

### Task 4: Data Model Tab (Mind Map)

**Files:**
- Modify: `product-design-skill/scripts/review_hub_server.py`

**Step 1: Port data model tree loader**

Port from `datamodel_review_server.py`:
- `load_datamodel_tree()` (line 50) — loads `entity-model.json`, `api-contracts.json`, `view-objects.json`
- Tree structure (from design doc lines 115-133):
  ```
  数据模型
  ├── E001 订单
  │   ├── 字段 group (id, status, amount...)
  │   ├── 状态机 group (pending → paid → shipped)
  │   ├── API group (GET /orders, POST /orders...)
  │   └── 视图 group (VO001 订单列表, VO002 订单详情...)
  ├── E002 商品
  └── 关系 (订单 1:N 商品项)
  ```

Custom node type CSS for data-model tab (from `datamodel_review_server.py`):
- entity, field-pk, field-fk, field-required, state-machine, transition, api-group, api, vo-group, vo, vo-field, action, relation-group, relation

Feedback categories: entity, api, vo, action, state-machine, product-map
Feedback path: `data-model-review/review-feedback.json` (unchanged)

Reuse `render_mindmap_page()` with data-model-specific node type CSS injected.

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/review_hub_server.py', doraise=True)"`

**Step 3: Commit**

```bash
git add product-design-skill/scripts/review_hub_server.py
git commit -m "feat(review-hub): data-model tab with entity/API/VO mind map"
```

---

### Task 5: Wireframe Tab (Tree + Preview Panel)

**Files:**
- Modify: `product-design-skill/scripts/review_hub_server.py`

**Step 1: Port wireframe data loading and screen building**

Port from `wireframe_review_server.py`:
- `load_data()` (line 41) — loads experience-map, task-inventory, role-profiles, gate, VOs, APIs
- `build_screens_with_context()` (line 74) — enriches screens with VO data, emotion context

**Step 2: Port wireframe rendering (tree + preview layout)**

Layout (from design doc lines 53-64):
```
┌──────────────────┬──────────────────┐
│  屏幕树（左）     │  预览+评论（右）  │
│  按旅程线分组     │  线框 iframe     │
│                  │  + pin 评论      │
│                  │  + 6V tabs       │
│                  │  + 4D panel      │
└──────────────────┴──────────────────┘
```

Port from `wireframe_review_server.py`:
- Screen tree (left panel): group by operation_line → nodes → screens, show interaction_type badges
- Wireframe generation: `generate_wireframe()` (line 646) with 7 type-specific templates (_wf_readonly_list, _wf_crud_list, _wf_create_form, _wf_edit_form, _wf_detail, _wf_state_machine, _wf_approval, _wf_default)
- 4D panel: `_build_4d_panel()` — Data/Action/State/Flow sections
- 6V tabs: Structure/Behavior/Data/State/Flow/Emotion side panel tabs
- Pin comments: click-to-add pin on wireframe preview
- XV cross-validation results (badge counts on tree items)

This is the largest tab (~800 lines of rendering logic). Key functions to port:
- `WF_CSS` constant (line 159)
- `_wf_*` template functions (lines 160-645)
- `generate_wireframe(screen)` dispatcher (line 646)
- `_build_4d_panel(screen)` (4D panel builder)
- Screen detail page with 6V tabs
- Pin comment overlay with category selection

Feedback path: `wireframe-review/review-feedback.json` (unchanged)
Feedback format: per-screen with `{pins: [{x, y, comment, category}], status}`

**Step 3: Port XV cross-validation (optional)**

Port from `wireframe_review_server.py`:
- `_run_xv_checks()` — runs on startup if OPENROUTER_API_KEY available
- Uses `C.xv_available()` and `C.xv_call()` from `_common.py`
- Results shown as badge counts on screen tree items

**Step 4: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/review_hub_server.py', doraise=True)"`

**Step 5: Commit**

```bash
git add product-design-skill/scripts/review_hub_server.py
git commit -m "feat(review-hub): wireframe tab with tree+preview, 4D/6V/XV"
```

---

### Task 6: UI Tab (Tree + Preview Panel)

**Files:**
- Modify: `product-design-skill/scripts/review_hub_server.py`

**Step 1: Port UI data loading**

Port from `ui_review_server.py`:
- `load_spec()` (line 36) — loads `ui-design/ui-design-spec.json`, normalizes screens
- `load_experience_map()` (line 51) — loads experience-map for design rationale
- `load_stitch_index()` (line 58) — loads Stitch screen mappings
- `get_preview_html()` (line 89) — finds preview HTML from `preview/*.html` or generates skeleton
- `get_stitch_html()` (line 73) — reads Stitch-generated HTML
- `generate_skeleton()` (line 112) — fallback skeleton generator

**Step 2: Port UI rendering (tree + preview layout)**

Layout matches wireframe tab pattern but with different content:
```
┌──────────────────┬──────────────────┐
│  角色→屏幕树（左）│  HTML 预览（右）  │
│  R001 商户       │  ← 点击显示预览   │
│    ├── 订单列表  │  + pin 评论       │
│    └── ...       │                   │
└──────────────────┴──────────────────┘
```

Port from `ui_review_server.py`:
- `_render_card()` (line 145) → adapt to tree item in left panel
- `render_dashboard()` (line 201) → left panel tree
- `render_screen_detail()` (line 390) → right panel preview with pin comments
- Preview iframe: loads HTML from `ui-design/preview/*.html` or `ui-design/stitch/*.html`
- Pin comments: same overlay mechanism as wireframe tab
- Stitch image display when available

Feedback path: `ui-review/review-feedback.json` (unchanged)
Feedback format: per-screen with `{pins: [{x, y, comment}], status}`

**Step 3: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/review_hub_server.py', doraise=True)"`

**Step 4: Commit**

```bash
git add product-design-skill/scripts/review_hub_server.py
git commit -m "feat(review-hub): UI tab with role-screen tree and HTML preview"
```

---

### Task 7: Spec Tab (Mind Map)

**Files:**
- Modify: `product-design-skill/scripts/review_hub_server.py`

**Step 1: Create spec tree loader**

This is a NEW tab (no existing server to port from). Load from `project-forge/sub-projects/*/design.json`.

Tree structure (from design doc lines 176-204):
```
开发规格
├── 后端服务 (backend-api)
│   ├── 数据模型
│   │   ├── orders 表
│   │   │   ├── 字段 + 类型 + 约束 + 索引
│   │   │   └── 状态机
│   │   └── products 表
│   ├── API 接口
│   │   ├── GET /orders → 请求参数 · 响应结构 · 错误码
│   │   └── POST /orders → 请求体 · 响应 · 验证规则
│   ├── 中间件：认证 · 审计
│   └── 任务 (8)
│       ├── B1 初始化 [□]
│       └── B2 数据模型 [□]
├── 前端管理后台 (admin-frontend)
│   ├── 页面路由
│   │   ├── /orders → 组件列表 · 四态 · 交互
│   │   └── /orders/new → 表单字段 · 验证
│   └── 任务 (6)
├── 共享基础
│   ├── 设计 Token
│   ├── 共享类型定义
│   └── 基础中间件
└── 跨项目依赖
    └── 后端 B2 → 前端 B4
```

Implementation:
```python
def load_spec_tree():
    """Transform design.json files into a mind map tree."""
    forge_dir = os.path.join(BASE, "project-forge/sub-projects")
    if not os.path.isdir(forge_dir):
        return _node("root", "No spec data", "error")

    children = []
    for name in sorted(os.listdir(forge_dir)):
        design_path = os.path.join(forge_dir, name, "design.json")
        design = C.load_json(design_path)
        if not design:
            continue
        # Build sub-project tree from design.json structure
        sp_children = []
        # Data models branch
        for dm in design.get("data_models", []):
            # fields, indexes, state_machine
            ...
        # Endpoints branch
        for ep in design.get("endpoints", []):
            ...
        # Tasks branch
        for task in design.get("tasks", []):
            ...
        children.append(_node(f"sp_{name}", name, "group", "", sp_children))

    # Shared section
    # Cross-dependencies section

    return _node("root", "开发规格", "root", "", children)
```

Reuse `render_mindmap_page()` with spec-specific node type CSS.

Feedback categories: data-model, api, task, dependency
Feedback path: `project-forge/spec-review-feedback.json` (NEW)

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/review_hub_server.py', doraise=True)"`

**Step 3: Commit**

```bash
git add product-design-skill/scripts/review_hub_server.py
git commit -m "feat(review-hub): spec tab with dev spec mind map"
```

---

### Task 8: Feedback APIs (All Tabs)

**Files:**
- Modify: `product-design-skill/scripts/review_hub_server.py`

**Step 1: Implement feedback API endpoints**

Each tab needs POST endpoints for saving feedback and a submit endpoint:

```
POST /api/concept/feedback    — save node feedback (status + comments)
POST /api/concept/submit      — submit all feedback, write to disk
POST /api/map/feedback        — same pattern
POST /api/map/submit
POST /api/data-model/feedback
POST /api/data-model/submit
POST /api/wireframe/feedback  — save screen feedback (pins + status)
POST /api/wireframe/submit
POST /api/ui/feedback         — save screen feedback (pins + status)
POST /api/ui/submit
POST /api/spec/feedback
POST /api/spec/submit
```

Mind map tabs (concept, map, data-model, spec) share the same feedback format:
```json
{
  "round": 1,
  "submitted_at": null,
  "nodes": {
    "node_id": {
      "status": "approved|revision",
      "comments": [{"text": "...", "category": "...", "created_at": "..."}]
    }
  }
}
```

Preview tabs (wireframe, ui) use pin-based feedback:
```json
{
  "round": 1,
  "submitted_at": null,
  "screens": {
    "screen_id": {
      "status": "approved|revision",
      "pins": [{"x": 0.5, "y": 0.3, "comment": "...", "category": "..."}]
    }
  }
}
```

Feedback write paths (unchanged from design doc lines 235-242):
| Tab | Path |
|-----|------|
| concept | `concept-review/review-feedback.json` |
| map | `product-map-review/review-feedback.json` |
| data-model | `data-model-review/review-feedback.json` |
| wireframe | `wireframe-review/review-feedback.json` |
| ui | `ui-review/review-feedback.json` |
| spec | `project-forge/spec-review-feedback.json` |

On submit: set `submitted_at` to ISO timestamp, print summary to server stdout.

**Important difference from old servers:** The old servers shut down after submit. The hub stays running — submit just saves feedback and shows a success toast in the browser.

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/review_hub_server.py', doraise=True)"`

**Step 3: Commit**

```bash
git add product-design-skill/scripts/review_hub_server.py
git commit -m "feat(review-hub): feedback APIs for all 6 tabs"
```

---

### Task 9: Home Page (Tab Cards + Status)

**Files:**
- Modify: `product-design-skill/scripts/review_hub_server.py`

**Step 1: Create home page renderer**

The home page (`/`) shows 6 cards, one per tab, with availability status and review progress.

```python
def render_home():
    """Render home page with 6 tab entry cards."""
    tabs_info = detect_tabs()
    # For each available tab, show:
    # - Tab name (Chinese)
    # - Availability indicator
    # - Review progress (X/Y reviewed) if feedback exists
    # - Link to tab page
    # Unavailable tabs show grayed out with "暂无产物" message
```

Card layout: 2×3 grid, each card ~200px wide, showing:
- Icon/emoji for tab type
- Tab name in Chinese
- Status badge (有产物 / 暂无)
- Review progress bar if feedback file exists
- Click → navigate to tab

Use shared nav bar at top (same as all other pages).

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/review_hub_server.py', doraise=True)"`

**Step 3: Commit**

```bash
git add product-design-skill/scripts/review_hub_server.py
git commit -m "feat(review-hub): home page with tab status cards"
```

---

### Task 10: `/review` Command + Skill Wiring

**Files:**
- Create: `product-design-skill/commands/review.md`
- Modify: `product-design-skill/SKILL.md`

**Step 1: Create `/review` command**

```markdown
---
name: review
description: >
  Use when the user says "review", "审核", "review hub", "审核站点".
  Unified review hub — one site, 6 tabs covering concept to dev spec.
arguments:
  - name: mode
    description: "start (launch hub) | process (read feedback) | process <tab> (process specific tab)"
    required: false
    default: "start"
---

# Review Hub — 统一审核站点

## 模式

| 模式 | 触发 | 行为 |
|------|------|------|
| `start` | `/review` 或 `/review start` | 启动审核站点 |
| `process` | `/review process` | 处理所有 tab 的反馈 |
| `process <tab>` | `/review process concept` | 处理指定 tab 的反馈 |

---

## Mode: start

启动统一审核站点，一个端口覆盖 6 个 tab。

\```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_hub_server.py <BASE> --port 18900
\```

- 打印 URL: `http://localhost:18900/`
- **不自动弹浏览器** — 用户自行打开
- 6 个 tab: 概念 / 地图 / 数据模型 / 线框 / UI / 规格
- 没有产物的 tab 灰显不可点击
- 每个 tab 独立保存反馈，提交后站点不关闭

---

## Mode: process

读取所有 tab（或指定 tab）的反馈文件，汇总修改建议。

### 支持的 tab 名

| tab | 反馈文件 |
|-----|---------|
| concept | `.allforai/concept-review/review-feedback.json` |
| map | `.allforai/product-map-review/review-feedback.json` |
| data-model | `.allforai/data-model-review/review-feedback.json` |
| wireframe | `.allforai/wireframe-review/review-feedback.json` |
| ui | `.allforai/ui-review/review-feedback.json` |
| spec | `.allforai/project-forge/spec-review-feedback.json` |

### 流程

1. 读取指定（或全部）反馈文件
2. 统计：N 个节点/界面已审核，M 通过，K 需修改
3. K = 0 → 全部通过
4. K > 0 → 按类别汇总修改建议，输出修复行动清单
5. 更新 round += 1
```

**Step 2: Update SKILL.md**

In `product-design-skill/SKILL.md`:
- Replace sections 1.5 (concept-review), 2.5 (map-review), 2.6 (data-model-review) with single section for `/review`
- Update pipeline description (line 10) to show `/review` instead of individual review commands
- Remove wireframe-review section reference
- Add `/review` command listing

Update pipeline description to:
```
Pipeline: concept → review(概念) → map → review(地图) → experience-map → review(线框+数据模型) →
[use-case ∥ gap ∥ ui-design] → review(UI) → audit.
```

**Step 3: Commit**

```bash
git add product-design-skill/commands/review.md product-design-skill/SKILL.md
git commit -m "feat(review-hub): /review command and SKILL.md update"
```

---

### Task 11: Delete Old Commands + Servers

**Files:**
- Delete: `product-design-skill/commands/concept-review.md`
- Delete: `product-design-skill/commands/map-review.md`
- Delete: `product-design-skill/commands/wireframe-review.md`
- Delete: `product-design-skill/commands/ui-review.md`
- Delete: `product-design-skill/commands/data-model-review.md`
- Delete: `product-design-skill/scripts/mindmap_review_server.py`
- Delete: `product-design-skill/scripts/wireframe_review_server.py`
- Delete: `product-design-skill/scripts/datamodel_review_server.py`
- Delete: `product-design-skill/scripts/ui_review_server.py`

**Step 1: Delete files**

```bash
git rm product-design-skill/commands/concept-review.md
git rm product-design-skill/commands/map-review.md
git rm product-design-skill/commands/wireframe-review.md
git rm product-design-skill/commands/ui-review.md
git rm product-design-skill/commands/data-model-review.md
git rm product-design-skill/scripts/mindmap_review_server.py
git rm product-design-skill/scripts/wireframe_review_server.py
git rm product-design-skill/scripts/datamodel_review_server.py
git rm product-design-skill/scripts/ui_review_server.py
```

**Step 2: Verify no broken references**

Search for references to deleted files in remaining code:
```bash
grep -r "concept-review\|map-review\|wireframe-review\|ui-review\|data-model-review\|mindmap_review_server\|wireframe_review_server\|datamodel_review_server\|ui_review_server" product-design-skill/ --include="*.md" --include="*.py" -l
```

Fix any remaining references to point to `review_hub_server.py` or `/review` command.

**Step 3: Commit**

```bash
git commit -m "refactor(review-hub): delete old review commands and server scripts"
```

---

### Task 12: Update `product-design.md` Orchestrator

**Files:**
- Modify: `product-design-skill/commands/product-design.md`

**Step 1: Replace all review phases to use `/review`**

Changes needed in `product-design.md`:

1. **Phase 1.5** (concept-review, lines 216-244): Replace `mindmap_review_server.py --source concept --port 18900` with `review_hub_server.py <BASE> --port 18900`. After startup, tell user to open `http://localhost:18900/concept`. Server does NOT auto-close after submit.

2. **Phase 2.5** (map-review, lines 280-313): Replace `mindmap_review_server.py --source product-map --port 18901` with telling user to refresh `http://localhost:18900/map` (hub already running from Phase 1.5). If hub not running, start it.

3. **Phase 5** (wireframe-review, lines 419-454): Replace `wireframe_review_server.py <BASE> --port 18902` with telling user to refresh `http://localhost:18900/wireframe`. If hub not running, start it.

4. **Phase 9** (ui-review, lines 651-685): Replace `ui_review_server.py <BASE> --port 18903` with telling user to refresh `http://localhost:18900/ui`. If hub not running, start it.

5. **Phase 4.5** (design-pattern): Change text to indicate auto execution.

6. **Phase 4.6** (behavioral-standards): Change text to indicate auto execution.

Key behavioral change: The hub starts once (Phase 1.5) and stays running. Subsequent review phases just tell the user to navigate to the relevant tab. If the hub process died, restart it.

Hub lifecycle:
```
Phase 1.5: Start hub → user reviews concept tab
Phase 2.5: Hub already running → user navigates to map tab
Phase 5:   Hub already running → user navigates to wireframe tab (+ data-model tab available)
Phase 9:   Hub already running → user navigates to UI tab
```

**Step 2: Update Phase 0 detection**

Update the detection table (lines 87-108) to use unified review paths:
- Remove separate `concept-review`, `map-review`, `wireframe-review` detection
- Add: `review-hub` — check if hub process is running on port 18900

**Step 3: Verify no port conflicts**

Ensure all references to ports 18901-18904 are removed from the orchestrator.

**Step 4: Commit**

```bash
git add product-design-skill/commands/product-design.md
git commit -m "refactor(review-hub): update orchestrator to use unified review hub"
```

---

### Task 13: Update `_common.py`

**Files:**
- Modify: `product-design-skill/scripts/_common.py`

**Step 1: Update REVIEW_PORTS**

Change `REVIEW_PORTS` dict (line 54-60) from:
```python
REVIEW_PORTS = {
    "concept": 18900,
    "product-map": 18901,
    "wireframe": 18902,
    "ui": 18903,
    "data-model": 18904,
}
```

To:
```python
REVIEW_PORTS = {
    "review-hub": 18900,
}
```

**Step 2: Update `kill_other_review_servers()`**

Simplify `kill_other_review_servers()` (line 63) — since there's only one port now, this function can check if port 18900 is in use and kill the existing process before starting a new one.

**Step 3: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('product-design-skill/scripts/_common.py', doraise=True)"`

**Step 4: Commit**

```bash
git add product-design-skill/scripts/_common.py
git commit -m "refactor(review-hub): simplify REVIEW_PORTS to single hub port"
```

---

### Task 14: dev-forge design.json Output

**Files:**
- Modify: `dev-forge-skill/skills/design-to-spec.md`

**Step 1: Add Step 3a — Load product-design data model**

Insert before current Step 3 (line 431) a new Step 3a:

```markdown
Step 3a: 加载产品设计数据模型（可选增强）
  检查 .allforai/product-map/ 下是否存在:
    - entity-model.json → ER 设计起点
    - api-contracts.json → API 设计起点
    - view-objects.json → 前端组件规格起点
  存在 → 作为 design 生成的基础输入:
    - entities 从 entity-model.json 加载（而非从零推导）
    - endpoints 从 api-contracts.json 加载（而非从零推导）
    - 前端 screens 从 view-objects.json 提取字段定义
    - 每个节点保留 source_entity, source_api, source_vo 字段溯源
  不存在 → 回退到当前 Step 3 的从零推导（向后兼容）
```

Rename current Step 3 to Step 3b:

```markdown
Step 3b: 技术丰富（在产品设计基础上补充）
  后端: + 索引策略 + 中间件链 + 错误响应结构 + 分页约束
  前端: + 组件架构 + 状态管理 + 路由守卫
  （当 Step 3a 无数据时，3b = 当前完整 Step 3）
```

**Step 2: Add design.json output alongside design.md**

After Step 3b (current Step 3 end, around line 500), add instruction to generate `design.json`:

```markdown
  → 同时写入 .allforai/project-forge/sub-projects/{name}/design.json
  design.json 结构:
  {
    "sub_project": "{name}",
    "type": "backend|frontend",
    "data_models": [
      {
        "table": "orders",
        "source_entity": "E001",
        "fields": [...],
        "indexes": [...],
        "state_machine": {}
      }
    ],
    "endpoints": [
      {
        "source_api": "API001",
        "method": "GET",
        "path": "/orders",
        "params": [],
        "response": {},
        "errors": []
      }
    ],
    "pages": [...],
    "middleware": [...],
    "tasks": [...]
  }
```

**Step 3: Commit**

```bash
git add dev-forge-skill/skills/design-to-spec.md
git commit -m "feat(dev-forge): Step 3a/3b load product-design data model + design.json output"
```

---

### Task 15: Integration Test

**Files:** None (manual verification)

**Step 1: Verify server starts**

```bash
cd /tmp && mkdir -p test-hub/.allforai/product-concept test-hub/.allforai/product-map test-hub/.allforai/experience-map test-hub/.allforai/product-map-review test-hub/.allforai/concept-review

# Create minimal test data
echo '{"name":"Test","positioning":"test","roles":[]}' > test-hub/.allforai/product-concept/product-concept.json
echo '{"tasks":[{"id":"T001","name":"Test Task","owner_role":"R001","category":"core"}]}' > test-hub/.allforai/product-map/task-inventory.json
echo '{"roles":[{"id":"R001","name":"Merchant"}]}' > test-hub/.allforai/product-map/role-profiles.json

python3 product-design-skill/scripts/review_hub_server.py test-hub/.allforai --port 18900 --no-open true &
sleep 2

# Test endpoints
curl -s http://localhost:18900/ | head -5          # Home page
curl -s http://localhost:18900/concept | head -5    # Concept tab
curl -s http://localhost:18900/map | head -5        # Map tab (should work)
curl -s http://localhost:18900/wireframe | head -5  # Wireframe tab (may show "no data")

kill %1
rm -rf /tmp/test-hub
```

Expected: Server starts, home page shows tab cards, concept/map tabs render mind maps, unavailable tabs show "no data" message.

**Step 2: Verify feedback round-trip**

```bash
# Start server, submit feedback via curl, verify file written
python3 product-design-skill/scripts/review_hub_server.py test-hub/.allforai --port 18900 --no-open true &
sleep 2

curl -X POST http://localhost:18900/api/concept/feedback \
  -H 'Content-Type: application/json' \
  -d '{"node_id":"root","status":"approved","comments":[]}'

curl -X POST http://localhost:18900/api/concept/submit \
  -H 'Content-Type: application/json' \
  -d '{}'

cat test-hub/.allforai/concept-review/review-feedback.json

kill %1
```

Expected: Feedback file written with `submitted_at` timestamp.

**Step 3: Verify old commands/scripts deleted**

```bash
ls product-design-skill/commands/concept-review.md 2>&1    # Should not exist
ls product-design-skill/scripts/mindmap_review_server.py 2>&1  # Should not exist
ls product-design-skill/commands/review.md 2>&1              # Should exist
ls product-design-skill/scripts/review_hub_server.py 2>&1    # Should exist
```

**Step 4: Commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix(review-hub): integration test fixes"
```

---

## Implementation Notes

### Shared Mind Map Renderer

The biggest code reuse opportunity is the mind map rendering. Extract a function:

```python
def render_mindmap_page(tree, feedback, title, tab_id, categories, extra_css="", extra_node_types=""):
    """Render XMind-style mind map page with shared nav bar.

    Args:
        tree: Root node dict with {id, label, type, detail, children, tags}
        feedback: Feedback dict with {round, submitted_at, nodes: {}}
        title: Page title (Chinese)
        tab_id: Active tab ID for nav highlighting
        categories: List of feedback category options
        extra_css: Additional CSS for tab-specific node types
        extra_node_types: Additional node type → color mappings
    """
```

This function should contain:
- Shared nav bar (from Task 1)
- Full mind map CSS (~100 lines, from `mindmap_review_server.py:297-372`)
- Mind map JS (~400 lines: tree layout, SVG curves, zoom/pan, node interaction)
- Comment panel HTML + JS
- Submit button wired to `/api/{tab_id}/submit`

### Shared Preview Panel Renderer

For wireframe and UI tabs, extract:

```python
def render_preview_page(screens, feedback, title, tab_id, render_preview_fn, extra_panels=""):
    """Render tree + preview layout with shared nav bar.

    Args:
        screens: List of screen dicts
        feedback: Feedback dict with {round, submitted_at, screens: {}}
        title: Page title
        tab_id: Active tab ID
        render_preview_fn: Function(screen) → HTML string for the preview iframe
        extra_panels: Additional panel HTML (e.g., 4D panel, 6V tabs)
    """
```

### File Size Estimate

The unified server will be ~2500-3000 lines (vs ~4200 lines total across 4 old servers). Size reduction comes from:
- Shared nav bar: write once, used 7 times
- Shared mind map renderer: write once, used 4 times
- Shared HTTP handler: one class instead of 4
- Shared feedback APIs: one pattern, parameterized by tab

### Migration Safety

1. Feedback file paths are unchanged → existing review data preserved
2. Port 18900 reused → firewall/bookmark compatible for concept-review users
3. Old servers deleted only after new server is verified working (Task 15 before Task 11)

### Reordering Note

Tasks 11 (delete old) should be done AFTER Task 15 (integration test) passes. The plan lists them in logical order, but execution should verify the new server works before deleting the old ones.
