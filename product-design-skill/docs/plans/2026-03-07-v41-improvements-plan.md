# v4.1 Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 5 improvements (#1 Implementation Contract, #3 Micro-interactions, #4 Token Single Source, #5 LLM Cognitive Walkthrough, #6 Stitch Decision Point) across product-design and dev-forge plugins.

**Architecture:** All changes extend existing files. gen_ui_design.py gets tokens.json output + micro-interactions section. gen_experience_map.py gets implementation_contract field on screens. Skill docs updated for downstream consumption. Version bumps to product-design 4.1.0, dev-forge 2.7.0.

**Tech Stack:** Python 3 scripts, Markdown skill files, JSON schemas

---

### Task 1: Add tokens.json output to gen_ui_design.py

**Files:**
- Modify: `product-design-skill/scripts/gen_ui_design.py:242-246` (after spec file write, before XV section)

**Step 1: Add tokens.json generation code**

Insert the following block after line 245 (`spec_text = "\n".join(spec_lines)`) and before line 248 (`# -- XV auto-apply helpers`):

```python
# ── Generate tokens.json (single source of truth) ────────────────────────────
tokens = {
    "color": {
        "primary": S["primary"],
        "on_primary": S["on_primary"],
        "secondary": S["secondary"],
        "tertiary": S["tertiary"],
        "background": S["bg"],
        "surface": S["surface"],
        "surface_variant": S["surface_variant"],
        "on_surface": S["on_surface"],
        "on_surface_variant": S["on_surface_variant"],
        "error": S["error"],
        "success": S["success"],
        "warning": S["warning"],
    },
    "spacing": {
        "unit": 4,
        "scale": [4, 8, 12, 16, 24, 32],
    },
    "radius": {
        "sm": 4,
        "md": int(S["radius"].replace("px", "")),
        "lg": 16,
    },
    "typography": {
        "display": {"size": 57, "weight": 400},
        "headline": {"size": 32, "weight": 400},
        "title": {"size": 22, "weight": 500},
        "body": {"size": 16, "weight": 400, "line_height": 24},
        "label": {"size": 14, "weight": 500},
    },
    "font": S["font"],
    "shadow": S["shadow"],
    "style_name": S["name"],
    "generated_at": NOW,
}
C.write_json(os.path.join(OUT, "tokens.json"), tokens)
```

**Step 2: Run script to verify no syntax errors**

Run: `cd /Users/aa/Documents/myskills && python3 -c "import ast; ast.parse(open('product-design-skill/scripts/gen_ui_design.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add product-design-skill/scripts/gen_ui_design.py
git commit -m "feat(ui-design): generate tokens.json as single source of truth (#4)"
```

---

### Task 2: Add micro-interactions to gen_ui_design.py

**Files:**
- Modify: `product-design-skill/scripts/gen_ui_design.py` (insert after tokens.json block, before XV section)

**Step 1: Add micro-interaction preset constants and generation logic**

Insert after the tokens.json block (from Task 1), before the `# -- XV auto-apply helpers` comment:

```python
# ── Micro-interaction presets ────────────────────────────────────────────────
MICRO_PRESETS = {
    "calm": {
        "animation": "fade",
        "duration_ms": 200,
        "easing": "ease-out",
        "haptic": "none",
    },
    "moderate": {
        "animation": "slide-fade",
        "duration_ms": 250,
        "easing": "ease-in-out",
        "haptic": "light",
    },
    "intense": {
        "animation": "scale-bounce",
        "duration_ms": 300,
        "easing": "cubic-bezier(0.34, 1.56, 0.64, 1)",
        "haptic": "impact-medium",
    },
}

MICRO_OVERRIDES = {
    "success": {"animation": "scale-bounce", "haptic": "impact-medium"},
    "error": {"animation": "shake", "haptic": "notification-error"},
    "loading": {"animation": "pulse", "haptic": "none"},
}


def _intensity_tier(intensity):
    if intensity <= 3:
        return "calm"
    elif intensity <= 6:
        return "moderate"
    return "intense"


# Generate micro-interactions per screen
micro_interactions_data = []
spec_lines.append("\n---\n")
spec_lines.append("## Micro-Interaction Specifications\n")
spec_lines.append("| Screen | Trigger | Animation | Duration | Easing | Haptic |")
spec_lines.append("|--------|---------|-----------|----------|--------|--------|")

for s in screens:
    sid = s["id"]
    ctx = screen_context.get(sid, {})
    intensity = ctx.get("emotion_intensity", 5)
    tier = _intensity_tier(intensity)
    preset = MICRO_PRESETS[tier]

    screen_micros = []

    # Primary action interaction
    primary_micro = {
        "trigger": "primary-action-tap",
        **preset,
        "emotion_alignment": f"{ctx.get('emotion_state', 'neutral')} ({tier})",
    }
    screen_micros.append(primary_micro)
    spec_lines.append(
        f"| {s['name']} ({sid}) | primary-action-tap | {preset['animation']} "
        f"| {preset['duration_ms']}ms | {preset['easing']} | {preset['haptic']} |"
    )

    # Success state override for C-type screens
    has_create = any(a.get("crud") == "C" for a in s.get("actions", []))
    if has_create:
        success_micro = {
            "trigger": "create-success",
            "animation": MICRO_OVERRIDES["success"]["animation"],
            "duration_ms": 300,
            "easing": "cubic-bezier(0.34, 1.56, 0.64, 1)",
            "haptic": MICRO_OVERRIDES["success"]["haptic"],
            "emotion_alignment": "satisfying confirmation",
        }
        screen_micros.append(success_micro)
        spec_lines.append(
            f"| {s['name']} ({sid}) | create-success | scale-bounce "
            f"| 300ms | spring overshoot | impact-medium |"
        )

    micro_interactions_data.append({
        "screen_id": sid,
        "screen_name": s["name"],
        "emotion_tier": tier,
        "micro_interactions": screen_micros,
    })

spec_lines.append("")

# Write micro-interactions.json
C.write_json(os.path.join(OUT, "micro-interactions.json"), {
    "generated_at": NOW,
    "presets": MICRO_PRESETS,
    "overrides": MICRO_OVERRIDES,
    "screens": micro_interactions_data,
})
```

**Step 2: Run syntax check**

Run: `cd /Users/aa/Documents/myskills && python3 -c "import ast; ast.parse(open('product-design-skill/scripts/gen_ui_design.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add product-design-skill/scripts/gen_ui_design.py
git commit -m "feat(ui-design): add micro-interaction specifications from emotion presets (#3)"
```

---

### Task 3: Add implementation_contract to gen_experience_map.py

**Files:**
- Modify: `product-design-skill/scripts/gen_experience_map.py:43-88` (build_screens_for_node function)

**Step 1: Add contract derivation constants and logic**

Insert after the `infer_frequency` function (line 40) and before `build_screens_for_node` (line 43):

```python
# ── Implementation contract presets ──────────────────────────────────────────
CONTRACT_PATTERNS = {
    "bottom-sheet": {
        "forbidden": ["page-route", "full-screen-modal"],
        "required_behaviors": ["swipe-to-dismiss", "backdrop-tap-close"],
    },
    "full-page": {
        "forbidden": ["bottom-sheet", "inline-expand"],
        "required_behaviors": ["back-navigation", "scroll-to-top"],
    },
    "modal-picker": {
        "forbidden": ["page-route", "inline-expand"],
        "required_behaviors": ["backdrop-tap-close", "keyboard-dismiss"],
    },
    "multi-step-form": {
        "forbidden": ["single-submit", "inline-edit"],
        "required_behaviors": ["step-indicator", "back-to-previous-step", "draft-save"],
    },
    "standard-page": {
        "forbidden": [],
        "required_behaviors": ["back-navigation"],
    },
}


def infer_contract(ux_intent, crud_type, emotion_intensity):
    """Infer implementation contract from UX intent, CRUD type, and emotion intensity."""
    intent_lower = (ux_intent or "").lower()

    if any(kw in intent_lower for kw in ["quick", "overlay", "confirm", "dismiss"]):
        pattern = "bottom-sheet"
    elif any(kw in intent_lower for kw in ["detail", "full", "comprehensive"]):
        pattern = "full-page"
    elif any(kw in intent_lower for kw in ["select", "pick", "choose"]):
        pattern = "modal-picker"
    elif crud_type == "C" and emotion_intensity >= 7:
        pattern = "multi-step-form"
    else:
        pattern = "standard-page"

    preset = CONTRACT_PATTERNS[pattern]
    return {
        "pattern": pattern,
        "forbidden": preset["forbidden"],
        "required_behaviors": preset["required_behaviors"],
    }
```

**Step 2: Modify build_screens_for_node to accept and use node context**

Change the function signature and add contract to each screen. Replace lines 43-88 entirely:

```python
def build_screens_for_node(node_tasks, tasks_inv, screen_counter, ux_intent="", emotion_intensity=5):
    """Build screen objects from a list of task IDs. Returns (screens, updated_counter)."""
    if not node_tasks:
        return [], screen_counter

    # Group by module
    module_groups = {}
    for tid in node_tasks:
        task = tasks_inv.get(tid, {})
        module = task.get("module", task.get("owner_role", "unknown"))
        module_groups.setdefault(module, []).append((tid, task))

    screens = []
    for module, task_pairs in module_groups.items():
        screen_counter += 1
        sid = f"S{screen_counter:03d}"

        actions = []
        task_ids = []
        for tid, task in task_pairs:
            tname = task.get("name", tid)
            crud = infer_crud(tname)
            actions.append({
                "label": tname,
                "crud": crud,
                "frequency": infer_frequency(task),
                "task_ref": tid,
            })
            task_ids.append(tid)

        # Determine primary action and dominant CRUD
        primary = actions[0]["label"] if actions else module
        dominant_crud = actions[0]["crud"] if actions else "R"
        screen_name = f"{module}_screen"

        # Derive implementation contract
        contract = infer_contract(ux_intent, dominant_crud, emotion_intensity)

        screens.append({
            "id": sid,
            "name": screen_name,
            "description": f"{module} operations",
            "route_type": "push",
            "tasks": task_ids,
            "actions": actions,
            "primary_action": primary,
            "non_negotiable": [],
            "implementation_contract": contract,
        })

    return screens, screen_counter
```

**Step 3: Update the call site in main() to pass node context**

Replace lines 135-137 (the call to `build_screens_for_node` inside `main()`) with:

```python
            # Build screens for this node
            node_screens, screen_counter = build_screens_for_node(
                node_tasks, tasks_inv, screen_counter,
                ux_intent=en.get("design_hint", ""),
                emotion_intensity=en.get("intensity", 5),
            )
```

**Step 4: Run syntax check**

Run: `cd /Users/aa/Documents/myskills && python3 -c "import ast; ast.parse(open('product-design-skill/scripts/gen_experience_map.py').read()); print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add product-design-skill/scripts/gen_experience_map.py
git commit -m "feat(experience-map): add implementation_contract to screens (#1)"
```

---

### Task 4: Update experience-map schema doc

**Files:**
- Modify: `product-design-skill/docs/schemas/experience-map-schema.md:37-48` (screens[] table)

**Step 1: Add implementation_contract to screens[] table**

After the `non_negotiable` row in the screens[] table, add a new row:

```markdown
| `implementation_contract` | object | `{pattern, forbidden[], required_behaviors[]}` — design intent contract |
```

**Step 2: Add implementation_contract section after screen_index**

Append at the end of the file:

```markdown
## implementation_contract

| Field | Type | Description |
|-------|------|-------------|
| `pattern` | string | UI pattern: `bottom-sheet`, `full-page`, `modal-picker`, `multi-step-form`, `standard-page` |
| `forbidden` | array | Patterns that must NOT be used for this screen |
| `required_behaviors` | array | Behaviors that must be implemented |

### Pattern derivation rules

| Condition | Pattern |
|-----------|---------|
| ux_intent contains "quick"/"overlay"/"confirm" | `bottom-sheet` |
| ux_intent contains "detail"/"full" | `full-page` |
| ux_intent contains "select"/"pick" | `modal-picker` |
| CRUD "C" + emotion_intensity >= 7 | `multi-step-form` |
| default | `standard-page` |
```

**Step 3: Commit**

```bash
git add product-design-skill/docs/schemas/experience-map-schema.md
git commit -m "docs: add implementation_contract to experience-map schema"
```

---

### Task 5: Update experience-map.md skill doc

**Files:**
- Modify: `product-design-skill/skills/experience-map.md:255-265` (output file structure section)

**Step 1: Add implementation_contract mention to output description**

In the output file structure section (around line 255), after the existing description of `experience-map.json`, add a note about the new field:

After line 259 (`├── experience-map.json              # 机器可读：操作线 > 节点 > 屏幕完整结构`), update the comment:

```
├── experience-map.json              # 机器可读：操作线 > 节点 > 屏幕完整结构（含 implementation_contract）
```

**Step 2: Add a note about implementation_contract in the Step 2 section**

After line 134 (end of Step 2 description), add:

```markdown
每个屏幕自动推导 `implementation_contract`（pattern + forbidden + required_behaviors），确保设计意图传递到代码层。
```

**Step 3: Commit**

```bash
git add product-design-skill/skills/experience-map.md
git commit -m "docs: mention implementation_contract in experience-map skill"
```

---

### Task 6: Update ui-design.md skill doc

**Files:**
- Modify: `product-design-skill/skills/ui-design.md:669-681` (output file structure section)

**Step 1: Add tokens.json and micro-interactions.json to output file structure**

In the output file structure section (around line 669), add the new files:

```
.allforai/ui-design/
├── ui-design-spec.md               # 高层设计规格（含 micro-interaction 规格表）
├── ui-design-spec.json             # 设计规格（机器可读）
├── ui-design-decisions.json        # 用户决策日志
├── tokens.json                     # 设计令牌单一来源（配色、间距、圆角、排版）
├── micro-interactions.json         # 微交互规格（按屏幕，含情绪对齐）
└── preview/
    ├── index.html
    ├── ui-role-{角色1}.html
    └── ...
```

**Step 2: Add tokens.json and micro-interactions description**

After the output file structure section, add:

```markdown
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

特殊覆盖：CRUD "C" 成功 → scale-bounce + impact-medium；错误 → shake + notification-error。
```

**Step 3: Commit**

```bash
git add product-design-skill/skills/ui-design.md
git commit -m "docs: add tokens.json and micro-interactions to ui-design skill"
```

---

### Task 7: Add contract verification to product-verify.md

**Files:**
- Modify: `dev-forge-skill/skills/product-verify.md` (after S3 section, before S4)

**Step 1: Add S3.5 Contract Verification section**

After the S3 section (after line 267 `**输出**：写入 \`static-report.json\` 的 \`constraint_coverage\` 字段。`), insert:

```markdown
---

### S3.5：Implementation Contract 验证

**前提**：`.allforai/experience-map/experience-map.json` 中 screens 含 `implementation_contract` 字段。字段不存在 → 跳过 S3.5。

**扫描策略**：
1. 遍历 experience-map 中每个 screen 的 `implementation_contract`
2. 对每个 screen，Grep 前端代码找到对应组件
3. 检查组件是否匹配 `pattern`：
   - `bottom-sheet` → 查找 BottomSheet / Drawer / ActionSheet 组件
   - `modal-picker` → 查找 Modal / Dialog / Picker 组件
   - `multi-step-form` → 查找 Stepper / Steps / multi-step 模式
   - `full-page` → 查找独立页面路由
   - `standard-page` → 不检查（默认模式）
4. 检查 `forbidden` 列表中的模式是否出现
5. 检查 `required_behaviors` 是否有对应实现

**覆盖状态**：
- `compliant` — 组件匹配 pattern，无 forbidden 违规
- `violation` — 使用了 forbidden 模式，或缺少 required_behaviors（→ FIX_CONTRACT 任务）
- `unchecked` — 组件未找到（由 S2 处理）

**输出**：写入 `static-report.json` 的 `contract_compliance` 字段：

```json
{
  "contract_compliance": [
    {
      "screen_id": "S003",
      "screen_name": "退款申请页",
      "contract_pattern": "bottom-sheet",
      "status": "violation",
      "violations": ["uses page-route instead of bottom-sheet"],
      "matched_component": "src/pages/refund/index.tsx"
    }
  ]
}
```

violation 项生成 `FIX_CONTRACT` 类型任务到 `verify-tasks.json`。
```

**Step 2: Commit**

```bash
git add dev-forge-skill/skills/product-verify.md
git commit -m "feat(product-verify): add S3.5 implementation contract verification (#1)"
```

---

### Task 8: Add LLM cognitive walkthrough to product-verify.md

**Files:**
- Modify: `dev-forge-skill/skills/product-verify.md` (after D3 section, before D4)

**Step 1: Add D3.5 LLM Cognitive Walkthrough section**

After the D2/D3 section (after line 393 `- 超时阈值：单步 10 秒，单用例 60 秒（可配置）`), insert:

```markdown
---

### D3.5：LLM Cognitive Walkthrough（可发现性测试）

**前提**：dynamic 或 full 模式 + Playwright 可用 + 应用已可达（D0 通过）。任一不满足 → 跳过。

**目的**：验证用户能否**发现**功能，而非功能是否存在。E2E 测试知道组件 ID 直接点击；认知走查模拟真实用户只看界面内容。

**执行流程**：

```
1. 从 role-profiles.json 提取角色列表
2. 从 experience-map.json 提取每个角色的核心操作线（取 frequency=高 的前 3 条）
3. 对每条操作线构造认知走查任务:
   - persona: "{角色名}，首次使用本系统"
   - goal: 操作线的 name（如 "完成首次下单"）
   - 期望步数: 操作线 continuity.total_steps
   - 禁止提供: 路由名、组件 ID、导航提示
4. 对每个任务:
   a. browser_navigate 到首页
   b. browser_snapshot 获取页面快照
   c. 基于快照内容（纯文本，不看 HTML 结构），决定下一步点击
   d. 记录每次点击的 ref 和原因
   e. 重复 b-d 直到目标完成或达到 max_clicks（期望步数 × 3）
   f. 记录: 完成/放弃、实际点击数、卡住点
5. 输出 cognitive-walkthrough.json
```

**卡住判定**：连续 2 次快照相同（点击无效果）或 3 次回退（找不到入口）。

**输出**：`.allforai/product-verify/cognitive-walkthrough.json`

```json
{
  "generated_at": "ISO8601",
  "walkthroughs": [
    {
      "persona": "R01 买家",
      "goal": "完成首次下单",
      "result": "completed | abandoned",
      "click_count": 7,
      "expected_clicks": 5,
      "stuck_points": [
        {
          "at_step": 3,
          "snapshot_text": "商品详情页",
          "reason": "加入购物车按钮在折叠区域下方",
          "recovery": "滚动后找到"
        }
      ],
      "discoverability_score": 0.71
    }
  ],
  "overall_discoverability": 0.85,
  "recommendations": [
    "S003: 将加入购物车按钮固定在底部"
  ]
}
```

`discoverability_score` = `expected_clicks / actual_clicks`（上限 1.0）。
`overall_discoverability` = 所有走查分数的算术平均。

**D4 汇总集成**：D3.5 结果在 D4 汇总中展示为独立段落，不影响 FIX_FAILING 分类。discoverability_score < 0.5 的走查标记为 WARNING。
```

**Step 2: Commit**

```bash
git add dev-forge-skill/skills/product-verify.md
git commit -m "feat(product-verify): add D3.5 LLM cognitive walkthrough (#5)"
```

---

### Task 9: Add tokens consumption doc to project-scaffold.md

**Files:**
- Modify: `dev-forge-skill/skills/project-scaffold.md` (in Step 2 Monorepo section)

**Step 1: Add tokens.json consumption to Step 2**

After the existing Step 2 description of `tsconfig.base.json` generation (around line 146-151 in the scaffold workflow), add:

```markdown
  Design Tokens 消费（tokens.json 存在时）:
    检查 .allforai/ui-design/tokens.json 是否存在:
      存在 → 从 tokens.json 自动生成框架配置:
        Web (Tailwind): tailwind.config.ts 的 theme.extend（colors/spacing/borderRadius/fontSize）
        Web (CSS): src/styles/tokens.css（CSS 自定义属性 --color-primary 等）
        Flutter: lib/theme/app_theme.dart（ColorScheme + TextTheme）
        React Native: src/theme/tokens.ts（对象常量导出）
      不存在 → 跳过，使用框架默认值（向后兼容）
```

**Step 2: Commit**

```bash
git add dev-forge-skill/skills/project-scaffold.md
git commit -m "docs(project-scaffold): add tokens.json consumption (#4)"
```

---

### Task 10: Add Stitch decision point to SKILL.md and product-design.md

**Files:**
- Modify: `product-design-skill/SKILL.md:333-349` (Phase 5-7 section)
- Modify: `product-design-skill/commands/product-design.md:350-359` (Phase 5-7 section)

**Step 1: Add Stitch check to SKILL.md before Phase 5-7**

In SKILL.md, before the `## Phase 5-8 预置脚本优先（自动模式）` section (line 333), insert:

```markdown
## Phase 4.7：Stitch 可用性决策点

Phase 4.5/4.6 完成后、进入 Phase 5-7 并行执行前，检查 Stitch 可用性：

```
检查 mcp__plugin_product-design_stitch__create_project 是否可用:
  可用 → 继续（Stitch 将在 Phase 7 ui-design 的 Step 5.5 中使用）
  不可用 → AskUserQuestion（3 选 1）:
    A) 上传设计稿 — 用户手动上传 mockup 到 .allforai/ui-design/mockups/
    B) 跳过视觉验收 — 继续，但 forge-report 标注「Visual quality NOT verified」
    C) 配置 Stitch — 中断，运行 /setup 配置后重新执行

    用户选 B:
      记录 pipeline-decisions: { decision: "stitch_skipped", reason: "user acknowledged" }
      design-audit 将标记 stitch_skipped: true
    用户选 C:
      终止当前流程，提示运行 /setup
```

---

```

**Step 2: Add same check to commands/product-design.md**

In commands/product-design.md, before the Phase 5-7 parallel execution section (line 350), insert the same Stitch decision point block (adapted to the command flow format):

```markdown
---

## Phase 4.7：Stitch 可用性决策点

进入并行阶段前，检测 Stitch MCP 可用性。不可用时 AskUserQuestion 三选一（上传设计稿 / 跳过视觉验收 / 配置 Stitch）。选择跳过时记入 pipeline-decisions（`stitch_skipped`），design-audit 标记 `stitch_skipped: true`。

---
```

**Step 3: Commit**

```bash
git add product-design-skill/SKILL.md product-design-skill/commands/product-design.md
git commit -m "feat: add Stitch unavailability decision point before Phase 5-7 (#6)"
```

---

### Task 11: Version bumps

**Files:**
- Modify: `product-design-skill/.claude-plugin/plugin.json` — version `4.0.0` → `4.1.0`
- Modify: `product-design-skill/SKILL.md` — version in frontmatter
- Modify: `dev-forge-skill/.claude-plugin/plugin.json` — version `2.6.0` → `2.7.0`
- Modify: `.claude-plugin/marketplace.json` — sync both versions

**Step 1: Read current version files**

Read all four files to confirm current versions.

**Step 2: Bump product-design to 4.1.0**

In `product-design-skill/.claude-plugin/plugin.json`, change `"version": "4.0.0"` to `"version": "4.1.0"`.

In `product-design-skill/SKILL.md` frontmatter, change `version: "3.7.0"` to `version: "4.1.0"`.

**Step 3: Bump dev-forge to 2.7.0**

In `dev-forge-skill/.claude-plugin/plugin.json`, change `"version": "2.6.0"` to `"version": "2.7.0"`.

**Step 4: Sync marketplace.json**

In `.claude-plugin/marketplace.json`, update:
- product-design version to `4.1.0`
- dev-forge version to `2.7.0`

**Step 5: Commit**

```bash
git add product-design-skill/.claude-plugin/plugin.json product-design-skill/SKILL.md dev-forge-skill/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump product-design to 4.1.0, dev-forge to 2.7.0"
```

---

### Task 12: Integration test

**Files:**
- Use existing mock data from v4.0.0 integration test

**Step 1: Create test directory and mock data**

```bash
mkdir -p /tmp/v41-test/.allforai/product-map
mkdir -p /tmp/v41-test/.allforai/experience-map
```

Write mock `product-map.json`, `task-inventory.json`, `role-profiles.json`, `business-flows.json`, `journey-emotion-map.json` to `/tmp/v41-test/.allforai/` (reuse v4.0.0 integration test data format with `{"roles": [...]}`, `{"tasks": [...]}`, `{"flows": [...]}` wrappers).

**Step 2: Run gen_experience_map.py and verify contract field**

```bash
python3 product-design-skill/scripts/gen_experience_map.py /tmp/v41-test/.allforai
```

Verify: `cat /tmp/v41-test/.allforai/experience-map/experience-map.json | python3 -c "import sys,json; d=json.load(sys.stdin); s=d['operation_lines'][0]['nodes'][0]['screens'][0]; assert 'implementation_contract' in s, 'missing contract'; assert 'pattern' in s['implementation_contract']; print('contract OK:', s['implementation_contract']['pattern'])"`

Expected: `contract OK: standard-page` (or another pattern depending on mock data)

**Step 3: Run gen_ui_design.py and verify tokens + micro-interactions**

```bash
python3 product-design-skill/scripts/gen_ui_design.py /tmp/v41-test/.allforai --mode auto
```

Verify tokens:
```bash
python3 -c "import json; t=json.load(open('/tmp/v41-test/.allforai/ui-design/tokens.json')); assert 'color' in t; assert 'spacing' in t; assert 'typography' in t; print('tokens OK:', t['style_name'])"
```
Expected: `tokens OK: Material Design 3`

Verify micro-interactions:
```bash
python3 -c "import json; m=json.load(open('/tmp/v41-test/.allforai/ui-design/micro-interactions.json')); assert 'screens' in m; assert 'presets' in m; print('micro OK:', len(m['screens']), 'screens')"
```
Expected: `micro OK: N screens` (N > 0)

Verify spec has micro-interaction table:
```bash
grep -c "Micro-Interaction Specifications" /tmp/v41-test/.allforai/ui-design/ui-design-spec.md
```
Expected: `1`

**Step 4: Clean up**

```bash
rm -rf /tmp/v41-test
```

**Step 5: Commit all changes (if any test fixes needed)**

```bash
git add -A
git commit -m "test: v4.1 integration test passes (contract + tokens + micro-interactions)"
```

---

### Task 13: Final push

**Step 1: Review all changes**

```bash
git log --oneline -10
git diff --stat HEAD~8
```

**Step 2: Push**

```bash
git push
```
