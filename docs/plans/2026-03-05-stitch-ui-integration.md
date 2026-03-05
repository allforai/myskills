# Stitch UI Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable production-grade UI generation through a two-layer architecture: universal component analysis (always runs) + optional Stitch visual enhancement.

**Architecture:** Layer 1 (`gen_ui_components.py`) analyzes screen-map to produce `component-spec.json` with shared components, interaction primitives, variants, and a11y specs — independent of any external service. Layer 2 (`gen_ui_stitch.py` + Stitch MCP) optionally generates high-fidelity HTML/CSS visuals using Google Stitch. Both layers feed into dev-forge's design-to-spec for framework component generation.

**Tech Stack:** Python 3.9+ (scripts), Markdown (skills), JSON (data contracts), `@_davideast/stitch-mcp@0.4.0` (MCP server)

**Design Docs:**
- `product-design-skill/docs/stitch-integration-plan.md` (30 revisions, primary reference)
- `dev-forge-skill/docs/stitch-conversion-plan.md` (dev-forge side)

---

## Phase 1: Product-Design Schema & Concept (product-design-skill)

### Task 1: Add `stitch_ui` to pipeline_preferences schema

**Files:**
- Modify: `product-design-skill/docs/schemas/product-concept-schemas.md:52-56`

**Step 1: Add stitch_ui field**

In `product-concept-schemas.md`, find the `pipeline_preferences` object (line 52-56) and add the new field:

```json
"pipeline_preferences": {
  "ui_style": "material-design-3 | apple-hig | fluent-design | flat-minimal | glassmorphism | ant-design | shadcn-tailwind | undecided",
  "competitors": ["竞品A", "竞品B"] | [],
  "scope_strategy": "aggressive | balanced | conservative | undecided",
  "stitch_ui": true | false | "undecided"
}
```

Add documentation note below the schema: `stitch_ui` — 是否在 ui-design 阶段调用 Google Stitch 生成视觉稿。`true` 需要 Google Cloud OAuth 认证（`npx -y @_davideast/stitch-mcp init`）。

**Step 2: Commit**

```bash
git add product-design-skill/docs/schemas/product-concept-schemas.md
git commit -m "feat(product-design): add stitch_ui to pipeline_preferences schema"
```

---

### Task 2: Add Q4 to product-concept Step 3.5

**Files:**
- Modify: `product-design-skill/skills/product-concept.md:550-563`

**Step 1: Add Q4 after Q3**

After line 550 (Q3 options table), before the "**写入 `product-concept.json`**" block, insert:

```markdown
**Q4（可选）— 高质量 UI 视觉稿**

检测 Stitch MCP 可用性：
- 检查 MCP 工具 `mcp__plugin_product-design_stitch__create_project` 是否可用
- 可用 → 提示「Stitch 已就绪（Google 认证有效）」
- 不可用 → 提示「Stitch 未配置。如需启用，运行 `npx -y @_davideast/stitch-mcp init` 完成 Google 认证。现在可跳过，后续在 ui-design 阶段仍可启用。」

AskUserQuestion（单选）：

问题：「是否在 UI 设计阶段使用 Google Stitch 生成高质量视觉稿？」

| 编号 | 选项 | 说明 |
|------|------|------|
| 1 | 是，启用 Stitch（推荐） | 自动为核心界面生成视觉 UI（HTML/CSS + 截图），需 Google 认证 |
| 2 | 否，使用文字规格 | 生成 ui-design-spec.md + HTML 预览 + 组件规格，不调用 Stitch |
| 3 | 暂不确定 | 下游 ui-design 阶段再决定 |
```

**Step 2: Update the "写入 product-concept.json" block to include stitch_ui**

Find the existing write block (around line 552-562) and add `stitch_ui` to the output example:

```json
"pipeline_preferences": {
  "ui_style": "...",
  "competitors": [...],
  "scope_strategy": "...",
  "stitch_ui": true | false | "undecided"
}
```

**Step 3: Commit**

```bash
git add product-design-skill/skills/product-concept.md
git commit -m "feat(product-design): add Stitch Q4 to product-concept Step 3.5"
```

---

## Phase 2: Universal Component Analysis Script (product-design-skill)

### Task 3: Create `gen_ui_components.py`

**Files:**
- Create: `product-design-skill/scripts/gen_ui_components.py`
- Reference: `product-design-skill/scripts/_common.py` (reuse utilities)
- Reference: `product-design-skill/docs/interaction-types.md` (primitive mapping source)

**Step 1: Create the script with imports and primitive mapping table**

```python
#!/usr/bin/env python3
"""Generate component-spec.json from screen-map analysis.

Universal component analysis: shared components, interaction primitives,
variants, and a11y specs. Does NOT depend on Stitch or any external service.

Usage:
    python3 gen_ui_components.py <BASE_PATH> [--mode auto]
"""
import os, sys, json
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from _common import (
    parse_args, load_screen_map, load_product_concept,
    write_json, ensure_dir, append_pipeline_decision, now_iso,
)

# ── interaction_type → behavioral primitives mapping ──
PRIMITIVE_MAP = {
    "MG1":   ["VirtualList", "PullToRefresh", "SwipeAction", "BatchSelection"],
    "MG2-L": ["VirtualList", "BatchSelection"],
    "MG2-C": ["FormWithValidation", "FileUpload"],
    "MG2-E": ["FormWithValidation", "FileUpload"],
    "MG2-D": [],
    "MG2-ST":["StateMachine", "AsyncProcessing"],
    "MG3":   ["StateMachine", "Timeline"],
    "MG4":   ["BatchSelection", "StateMachine"],
    "MG5":   ["VirtualList", "InlineEdit"],
    "MG6":   ["TreeNavigation"],
    "MG7":   [],
    "MG8":   ["FormWithValidation", "InlineEdit"],
    "CT1":   ["InfiniteScroll", "PullToRefresh", "AppendOnlyStream"],
    "CT2":   ["InfiniteScroll"],
    "CT3":   [],
    "CT4":   ["HorizontalSwipe"],
    "CT5":   ["MediaPlayer"],
    "CT6":   ["ImageLightbox", "CanvasDrag"],
    "CT7":   ["VirtualList"],
    "CT8":   ["VerticalSwipe", "MediaPlayer", "AppendOnlyStream"],
    "EC1":   ["ImageLightbox", "CanvasDrag"],
    "EC2":   ["FormWithValidation", "BatchSelection"],
    "EC3":   ["Timeline"],
    "WK1":   ["AppendOnlyStream", "RealtimeSync", "InfiniteScroll"],
    "WK2":   ["AppendOnlyStream", "RealtimeSync"],
    "WK3":   ["RealtimeSync"],
    "WK4":   ["CanvasDrag", "DragAndDrop", "RealtimeSync"],
    "WK5":   ["DragAndDrop", "StateMachine"],
    "WK6":   ["Timeline", "DragAndDrop"],
    "WK7":   ["TreeNavigation", "DragAndDrop", "FileUpload"],
    "RT1":   ["StateMachine"],
    "RT2":   ["AppendOnlyStream", "MediaPlayer"],
    "RT3":   [],
    "RT4":   ["AppendOnlyStream"],
    "SB1":   ["FormWithValidation", "FileUpload", "StateMachine", "AsyncProcessing"],
    "SY1":   ["MultiStepWizard"],
    "SY2":   ["MultiStepWizard", "FormWithValidation"],
}

# ── a11y rules by component semantic type ──
A11Y_RULES = {
    "button":     {"role": "button",     "requirements": ["aria-label", "focus-visible outline", "min 44x44px touch target"]},
    "form":       {"role": "form",       "requirements": ["label association", "aria-required", "aria-invalid + error message", "autocomplete"]},
    "list":       {"role": "list",       "requirements": ["aria-label on container", "role=listitem on children"]},
    "image":      {"role": "img",        "requirements": ["alt text", "decorative images use alt=''"]},
    "navigation": {"role": "navigation", "requirements": ["aria-current=page on active item"]},
    "dialog":     {"role": "dialog",     "requirements": ["aria-modal", "focus trap", "Escape to close", "return focus on close"]},
    "card":       {"role": "article",    "requirements": ["tabindex=0 if clickable", "aria-label"]},
    "tab":        {"role": "tablist",    "requirements": ["role=tab + role=tabpanel", "aria-selected", "arrow key navigation"]},
    "input":      {"role": "textbox",    "requirements": ["label association", "aria-required", "aria-invalid"]},
}
```

**Step 2: Add component inference functions**

```python
def get_primitives(interaction_type):
    """Get primitives for an interaction_type (handles arrays and sub-types)."""
    if isinstance(interaction_type, list):
        result = []
        for it in interaction_type:
            result.extend(PRIMITIVE_MAP.get(it, []))
        return list(dict.fromkeys(result))  # dedup preserving order
    return PRIMITIVE_MAP.get(interaction_type, [])


def infer_a11y(component_name, has_actions=False):
    """Infer a11y requirements from component name heuristics."""
    name_lower = component_name.lower()
    if "form" in name_lower or "input" in name_lower:
        return A11Y_RULES["form"]
    if "list" in name_lower:
        return A11Y_RULES["list"]
    if "nav" in name_lower or "shell" in name_lower or "bar" in name_lower:
        return A11Y_RULES["navigation"]
    if "card" in name_lower or "item" in name_lower:
        r = dict(A11Y_RULES["card"])
        if has_actions:
            r["requirements"] = r["requirements"] + ["role=button if entire card is clickable"]
        return r
    if "dialog" in name_lower or "modal" in name_lower:
        return A11Y_RULES["dialog"]
    if "tab" in name_lower:
        return A11Y_RULES["tab"]
    if "button" in name_lower or "btn" in name_lower:
        return A11Y_RULES["button"]
    if "image" in name_lower or "gallery" in name_lower:
        return A11Y_RULES["image"]
    # Default for interactive components
    if has_actions:
        return A11Y_RULES["card"]
    return {"role": "generic", "requirements": []}


def infer_variants(screens_data, component_name):
    """Infer component variants from screen usage context."""
    variants = {"state": ["default"]}

    has_loading = any(
        "loading" in str(s.get("states", {})).lower()
        for s in screens_data
    )
    has_empty = any(
        "empty" in str(s.get("states", {})).lower()
        for s in screens_data
    )
    has_error = any(
        "error" in str(s.get("states", {})).lower()
        for s in screens_data
    )

    if has_loading:
        variants["state"].append("loading")
    if has_empty:
        variants["state"].append("empty")
    if has_error:
        variants["state"].append("error")

    # All interactive components get disabled
    variants["state"].append("disabled")

    # Size variants if component appears in different contexts
    if len(screens_data) >= 2:
        variants["size"] = ["compact", "default"]

    return variants
```

**Step 3: Add shared component identification logic**

```python
def identify_shared_components(screens):
    """Identify shared UI components across screens."""
    # Group screens by interaction_type
    type_screens = defaultdict(list)
    for s in screens:
        it = s.get("interaction_type", "MG1")
        types = it if isinstance(it, list) else [it]
        for t in types:
            type_screens[t].append(s)

    shared = {}

    # AppShell: if >50% screens share navigation pattern
    if len(screens) >= 2:
        shared["AppShell"] = {
            "screens": [s["screen_id"] for s in screens],
            "inferred_from": "所有屏幕共有的导航结构",
            "structure": "TopBar + Content + BottomNav",
            "props": ["title", "showBack", "showSearch", "activeTab"],
            "primitives": [],
            "variants": {"state": ["default", "loading"]},
            "a11y": infer_a11y("AppShell"),
        }

    # Pattern: same interaction_type appears in >=2 screens → shared component
    for itype, ss in type_screens.items():
        if len(ss) < 2:
            continue

        base_type = itype.split("-")[0]  # MG2-L → MG2

        if itype.startswith("MG1") or itype == "MG2-L" or itype.startswith("CT"):
            # List-type screens → shared list + card components
            list_name = _infer_component_name(ss, "List")
            card_name = _infer_component_name(ss, "Card")

            shared[list_name] = {
                "screens": [s["screen_id"] for s in ss],
                "inferred_from": f"同一 interaction_type:{itype} 列表容器",
                "props": ["items", "onLoadMore", "onRefresh"],
                "primitives": get_primitives(itype),
                "variants": infer_variants(ss, list_name),
                "a11y": infer_a11y(list_name),
            }
            shared[card_name] = {
                "screens": [s["screen_id"] for s in ss],
                "inferred_from": f"同一 interaction_type:{itype} 列表项",
                "props": _infer_card_props(ss),
                "primitives": [],
                "variants": infer_variants(ss, card_name),
                "a11y": infer_a11y(card_name, has_actions=True),
            }

        if itype in ("MG2-C", "MG2-E", "MG8", "SY2", "SB1"):
            form_name = _infer_component_name(ss, "Form")
            shared[form_name] = {
                "screens": [s["screen_id"] for s in ss],
                "inferred_from": f"同一 interaction_type:{itype} 表单",
                "props": ["fields", "onSubmit", "onValidate"],
                "primitives": get_primitives(itype),
                "variants": infer_variants(ss, form_name),
                "a11y": infer_a11y(form_name),
            }

    # Search: if >=2 screens have search-related actions
    search_screens = [
        s for s in screens
        if any("search" in str(a.get("label", "")).lower()
               for a in s.get("actions", []))
    ]
    if len(search_screens) >= 2:
        shared["SearchBar"] = {
            "screens": [s["screen_id"] for s in search_screens],
            "inferred_from": "多个屏幕包含搜索操作",
            "props": ["placeholder", "onSearch", "onClear"],
            "primitives": [],
            "variants": {"state": ["default", "focused", "disabled"]},
            "a11y": infer_a11y("SearchBar"),
        }

    return shared


def _infer_component_name(screens, suffix):
    """Infer component name from screen names."""
    # Find common noun across screen names
    names = [s.get("screen_name", "") for s in screens]
    # Simple heuristic: use most common meaningful word
    return f"Item{suffix}" if suffix == "Card" else f"Item{suffix}"


def _infer_card_props(screens):
    """Infer card props from screen actions."""
    props = ["image", "name"]
    all_actions = []
    for s in screens:
        all_actions.extend(s.get("actions", []))
    action_labels = [a.get("label", "").lower() for a in all_actions]
    if any("price" in l or "金额" in l for l in action_labels):
        props.append("price")
    if any("rating" in l or "评分" in l for l in action_labels):
        props.append("rating")
    return props
```

**Step 4: Add screen-component mapping and main function**

```python
def build_screen_components(screens, shared_components):
    """Build per-screen component usage map."""
    mapping = {}
    for s in screens:
        sid = s["screen_id"]
        it = s.get("interaction_type", "MG1")
        used_shared = [
            name for name, comp in shared_components.items()
            if sid in comp["screens"]
        ]
        mapping[sid] = {
            "used_shared": used_shared,
            "page_specific": [],  # Will be refined by Stitch Layer 2
            "interaction_type": it,
            "primitives": get_primitives(it),
        }
    return mapping


def build_primitive_mapping(shared_components):
    """Build reverse mapping: primitive → interaction_types that use it."""
    reverse = defaultdict(set)
    for itype, prims in PRIMITIVE_MAP.items():
        for p in prims:
            reverse[p].add(itype)
    return {k: ", ".join(sorted(v)) for k, v in reverse.items() if v}


def main():
    base, args = parse_args()
    screens, loaded = load_screen_map(base)
    if not loaded or not screens:
        print("ERROR: screen-map.json not found or empty", file=sys.stderr)
        sys.exit(1)

    shared = identify_shared_components(screens)
    screen_comps = build_screen_components(screens, shared)
    prim_map = build_primitive_mapping(shared)

    spec = {
        "generated_at": now_iso(),
        "source": "screen-map",
        "total_screens": len(screens),
        "shared_components": shared,
        "screen_components": screen_comps,
        "primitive_mapping": prim_map,
    }

    out_dir = os.path.join(base, "ui-design")
    ensure_dir(out_dir)
    out_path = write_json(os.path.join(out_dir, "component-spec.json"), spec)
    print(f"OK  component-spec.json → {len(shared)} shared components, {len(screens)} screens")

    append_pipeline_decision(base, "ui-design/component-spec",
        f"generated {len(shared)} shared components from {len(screens)} screens",
        decision="auto_generated")


if __name__ == "__main__":
    main()
```

**Step 5: Test with a real project**

```bash
# Find a project with .allforai/screen-map/screen-map.json
# Run the script:
cd product-design-skill
python3 scripts/gen_ui_components.py /path/to/project/.allforai --mode auto

# Verify output:
cat /path/to/project/.allforai/ui-design/component-spec.json | python3 -m json.tool | head -50
```

Expected: JSON with `shared_components`, `screen_components`, `primitive_mapping` fields.

**Step 6: Commit**

```bash
git add product-design-skill/scripts/gen_ui_components.py
git commit -m "feat(product-design): add gen_ui_components.py — universal component analysis"
```

---

### Task 4: Create `gen_ui_stitch.py`

**Files:**
- Create: `product-design-skill/scripts/gen_ui_stitch.py`
- Reference: `product-design-skill/scripts/_common.py`
- Reference: `product-design-skill/scripts/gen_ui_components.py` (reads component-spec.json)

**Step 1: Create the Stitch prompt builder script**

```python
#!/usr/bin/env python3
"""Generate stitch-prompts.json from component-spec.json + screen-map.

Reads the universal component-spec.json and builds Stitch-ready prompts
with component vocabulary, consistency directives, and style tokens.

Usage:
    python3 gen_ui_stitch.py <BASE_PATH> [--screens S010,S025] [--mode auto] [--limit 10]
"""
import os, sys, json, re

sys.path.insert(0, os.path.dirname(__file__))
from _common import (
    parse_args, load_screen_map, load_product_concept,
    write_json, ensure_dir, append_pipeline_decision, now_iso,
    load_json,
)


def load_component_spec(base):
    """Load component-spec.json."""
    return load_json(os.path.join(base, "ui-design/component-spec.json"))


def load_ui_design_spec(base):
    """Extract key style tokens from ui-design-spec.md (text parsing)."""
    spec_path = os.path.join(base, "ui-design/ui-design-spec.md")
    if not os.path.exists(spec_path):
        return {}
    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Extract style hints (simplified — Claude will do full parsing in skill)
    tokens = {}
    if "primary" in content.lower():
        tokens["has_color_system"] = True
    if "font" in content.lower() or "字体" in content:
        tokens["has_typography"] = True
    return tokens


def infer_device_type(concept):
    """Infer Stitch deviceType from product concept."""
    if not concept:
        return "MOBILE"
    platform = concept.get("platform_type", "")
    if "mobile" in platform.lower() or "app" in platform.lower():
        return "MOBILE"
    if "desktop" in platform.lower():
        return "DESKTOP"
    if "web" in platform.lower():
        return "DESKTOP"
    return "AGNOSTIC"


def select_priority_screens(screens, limit=10, explicit=None):
    """Dynamically select priority screens based on metadata."""
    if explicit:
        explicit_ids = set(explicit.split(","))
        return [s for s in screens if s["screen_id"] in explicit_ids]

    scored = []
    for s in screens:
        score = 0
        it = s.get("interaction_type", "")
        if isinstance(it, list):
            it = it[0] if it else ""

        if it.startswith("MG"):
            score += 10
        if it in ("CT1", "CT2"):
            score += 8
        if s.get("primary_action"):
            score += 3
        states = s.get("states", {})
        if isinstance(states, dict) and len(states) >= 3:
            score += 2
        if len(s.get("actions", [])) >= 3:
            score += 1

        scored.append((score, s["screen_id"], s))

    scored.sort(key=lambda x: -x[0])
    selected = scored[:limit]

    result = []
    for i, (score, sid, s) in enumerate(selected):
        s_copy = dict(s)
        s_copy["priority"] = "P0" if i < 5 else "P1"
        s_copy["selection_score"] = score
        result.append(s_copy)
    return result


def build_prompt(screen, concept, component_spec, device_type, is_anchor):
    """Build a layered Stitch prompt for a screen."""
    sid = screen["screen_id"]
    name = screen.get("screen_name", sid)
    it = screen.get("interaction_type", "MG1")
    actions = screen.get("actions", [])
    states = screen.get("states", {})

    # Find which shared components this screen uses
    sc = component_spec.get("screen_components", {}).get(sid, {})
    used_shared = sc.get("used_shared", [])

    # Layer 1: Design system directive (shared across all screens)
    mission = concept.get("mission", "") if concept else ""
    target_market = concept.get("target_market", "") if concept else ""
    language = concept.get("language", "") if concept else ""

    layer1 = f"""App: {mission}
Target market: {target_market}. Language: {language}.
All screens belong to the same app and must share a consistent design language.
"""
    if used_shared:
        vocab = component_spec.get("shared_components", {})
        comp_descs = []
        for comp_name in used_shared:
            comp = vocab.get(comp_name, {})
            props = comp.get("props", [])
            comp_descs.append(f"- {comp_name}: props=[{', '.join(props)}]")
        layer1 += "Reuse these component patterns consistently:\n" + "\n".join(comp_descs) + "\n"

    # Layer 2: Screen-specific content
    action_descs = [a.get("label", "") for a in actions[:5]]
    layer2 = f"""Screen: {name}
Purpose: {screen.get('primary_purpose', name)}
Primary action: {screen.get('primary_action', action_descs[0] if action_descs else 'View')}
Actions: {', '.join(action_descs)}
"""
    if isinstance(states, dict):
        state_descs = [f"{k}: {v}" for k, v in states.items()]
        layer2 += f"States to consider: {'; '.join(state_descs)}\n"

    # Layer 3: Anchor reference (non-anchor screens only)
    layer3 = ""
    if not is_anchor:
        layer3 = "Maintain visual consistency with the first screen in this project. Use the same component styles, spacing, and color application.\n"

    # Layout hint
    layout = "Use flexible layouts (flexbox/grid) that can adapt to different screen sizes. Avoid fixed pixel widths on containers."

    return f"{layer1}\n{layer2}\n{layer3}{layout}"


def main():
    base, args = parse_args()
    screens, loaded = load_screen_map(base)
    if not loaded:
        print("ERROR: screen-map.json not found", file=sys.stderr)
        sys.exit(1)

    concept = load_product_concept(base)
    comp_spec = load_component_spec(base)
    if not comp_spec:
        print("WARNING: component-spec.json not found. Run gen_ui_components.py first.", file=sys.stderr)
        comp_spec = {"shared_components": {}, "screen_components": {}}

    limit = int(args.get("limit", "10"))
    explicit_screens = args.get("screens")
    device_type = infer_device_type(concept)

    selected = select_priority_screens(screens, limit=limit, explicit=explicit_screens)
    if not selected:
        print("ERROR: no screens selected", file=sys.stderr)
        sys.exit(1)

    anchor_id = selected[0]["screen_id"]
    prompt_entries = []
    for i, s in enumerate(selected):
        prompt = build_prompt(s, concept, comp_spec, device_type, is_anchor=(i == 0))
        prompt_entries.append({
            "screen_id": s["screen_id"],
            "screen_name": s.get("screen_name", s["screen_id"]),
            "priority": s.get("priority", "P1"),
            "generation_order": i,
            "prompt": prompt,
            "device_type": device_type,
            "model_id": "GEMINI_3_PRO",
            "referenced_components": comp_spec.get("screen_components", {}).get(s["screen_id"], {}).get("used_shared", []),
            "selection_reason": s.get("selection_score", 0),
        })

    output = {
        "generated_at": now_iso(),
        "product_name": concept.get("product_name", "unknown") if concept else "unknown",
        "device_type": device_type,
        "anchor_screen_id": anchor_id,
        "component_spec_ref": "ui-design/component-spec.json",
        "total_screens": len(prompt_entries),
        "screens": prompt_entries,
    }

    out_dir = os.path.join(base, "ui-design")
    ensure_dir(out_dir)
    out_path = write_json(os.path.join(out_dir, "stitch-prompts.json"), output)
    print(f"OK  stitch-prompts.json → {len(prompt_entries)} screens, anchor={anchor_id}")

    append_pipeline_decision(base, "ui-design/stitch-prompts",
        f"generated {len(prompt_entries)} Stitch prompts, device={device_type}",
        decision="auto_generated")


if __name__ == "__main__":
    main()
```

**Step 2: Test**

```bash
cd product-design-skill
python3 scripts/gen_ui_stitch.py /path/to/project/.allforai --mode auto
cat /path/to/project/.allforai/ui-design/stitch-prompts.json | python3 -m json.tool | head -30
```

**Step 3: Commit**

```bash
git add product-design-skill/scripts/gen_ui_stitch.py
git commit -m "feat(product-design): add gen_ui_stitch.py — Stitch prompt builder"
```

---

## Phase 3: UI-Design Skill Updates (product-design-skill)

### Task 5: Add Step 5.3 + Step 5.5 to ui-design.md

**Files:**
- Modify: `product-design-skill/skills/ui-design.md:442` (after Step 5, before "---")

**Step 1: Insert Step 5.3 (universal) after line 442**

After the CSS variables table at end of Step 5, before the `---` separator, insert:

```markdown
---

## Step 5.3：组件规格生成（始终执行）

运行组件分析脚本：
```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_ui_components.py <BASE> --mode auto
```

输出：`ui-design/component-spec.json`
- 共享组件识别（跨屏幕复用模式）
- 交互原语关联（interaction_type → behavioral primitives）
- 组件变体推断（size/state）
- a11y 规格标注（按组件类型自动注入）
- 屏幕→组件映射

**此步骤不依赖任何外部服务，始终执行。**
component-spec.json 是 dev-forge 的核心输入，用于生成共享组件规格、注入 a11y、关联交互原语实现方案。
```

**Step 2: Insert Step 5.5 (Stitch, conditional)**

Immediately after Step 5.3, insert the full Step 5.5 content.

Reference: `product-design-skill/docs/stitch-integration-plan.md` section "5. skills/ui-design.md" — copy the complete Step 5.5 markdown block from the design doc, including:
- Skip condition (`pipeline_preferences.stitch_ui ≠ true`)
- Fallback entry (stitch_ui undefined + MCP available → ask user)
- Three-phase generation flow (A: anchor, B: subsequent, C: consistency check)
- Fallback path (MCP unavailable → output prompts + manual instructions)
- Output files list

**Step 3: Commit**

```bash
git add product-design-skill/skills/ui-design.md
git commit -m "feat(product-design): add Step 5.3 (universal components) + Step 5.5 (Stitch) to ui-design"
```

---

### Task 6: Add G1-G7 spec enhancements to ui-design Step 4

**Files:**
- Modify: `product-design-skill/skills/ui-design.md` (Step 4 output section)

**Step 1: Add spec chapter generation instructions to Step 4**

Find Step 4 in ui-design.md (the section that generates `ui-design-spec.md` content). Add instructions to generate these additional chapters in the spec output:

- `## 响应式策略` (G1) — breakpoint definitions based on platform_type
- `## 间距标度` (G4) — 4px grid spacing scale
- `## 排版标度` (G5) — complete typography scale with line-height/letter-spacing
- `## 动效规范` (G6) — duration/easing tokens + prefers-reduced-motion
- `## 图标规范` (G7) — icon library selection based on ui_style + size scale
- `## 主题变体` (G2) — light/dark semantic token derivation rules

Reference: `product-design-skill/docs/stitch-integration-plan.md` section "生产级 UI 补强（G1-G10）" — use the exact spec content defined there.

**Step 2: Commit**

```bash
git add product-design-skill/skills/ui-design.md
git commit -m "feat(product-design): add G1-G7 production spec chapters to ui-design Step 4"
```

---

### Task 7: Add Stitch MCP server to .mcp.json

**Files:**
- Modify: `product-design-skill/.mcp.json`

**Step 1: Add stitch server entry**

Current content (lines 1-12) has only `openrouter`. Add `stitch` server:

```json
{
  "mcpServers": {
    "openrouter": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp-openrouter/dist/index.js"],
      "env": {
        "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}"
      }
    },
    "stitch": {
      "command": "npx",
      "args": ["-y", "@_davideast/stitch-mcp", "proxy"],
      "env": {}
    }
  }
}
```

**Step 2: Commit**

```bash
git add product-design-skill/.mcp.json
git commit -m "feat(product-design): add Stitch MCP proxy server to .mcp.json"
```

---

## Phase 4: Dev-Forge Skill Updates (dev-forge-skill)

### Task 8: Add Step 2.5 to design-to-spec.md

**Files:**
- Modify: `dev-forge-skill/skills/design-to-spec.md:400` (after Step 2, before Step 3)

**Step 1: Insert Step 2.5 after line 400**

After "（仅前端子项目执行；后端子项目跳过此步直接进入 Step 3）", insert:

```markdown

Step 2.5: 组件规格导入（component-spec.json 存在时执行）
  **触发条件**：`<BASE>/ui-design/component-spec.json` 存在
  **跳过**：文件不存在 → 直接进入 Step 3（向后兼容）

  **Layer 1（通用，始终执行）**：
  1. 读取 `component-spec.json` 的 `shared_components`
  2. 对每个共享组件：
     a. 从 `primitive-impl-map.md` 查找当前技术栈的 primitives 实现
     b. 写入 design.md 的 `## 共享组件` 章节：
        - 组件名、出现屏幕、Props 接口
        - 交互原语 + 技术栈实现方案
        - 变体矩阵（size/state）
        - a11y 要求（role、aria 属性、键盘导航）
  3. 对 `screen_components` 中的每个屏幕：
     将 used_shared + page_specific 写入对应页面规格
  4. 生成键盘导航矩阵写入 design.md

  **Layer 2（Stitch 增强，`stitch-index.json` 存在且有 success 屏幕时）**：
  5. 读取 `stitch-index.json`
  6. 对每个 `status=success` 的屏幕：
     a. 读取 `stitch/*.html`，提取精确 DOM 结构
     b. 提取内联样式 → design token 映射
     c. 补充 design.md 的组件结构（增强 Layer 1 的推断）
  7. 记录 pipeline-decision

  ↓
```

**Step 2: Commit**

```bash
git add dev-forge-skill/skills/design-to-spec.md
git commit -m "feat(dev-forge): add Step 2.5 component spec import to design-to-spec"
```

---

### Task 9: Add Stitch context injection to task-execute.md

**Files:**
- Modify: `dev-forge-skill/skills/task-execute.md:206` (after Step 1 strategy display)

**Step 1: Insert context injection block after line 206**

After "展示: "Round {N}: {任务数} 个任务，策略: {策略}（{reason}）"", insert:

```markdown

Step 1.5: B3 前端 UI 上下文准备（Round 2 的 B3 任务执行前）
  仅在当前 Round 包含 B3（前端 UI）任务时执行：

  1. 读取 `<BASE>/ui-design/component-spec.json`（如存在）
  2. B3 共享组件任务上下文追加：
     - 「使用 CSS 变量 / theme token，不硬编码颜色值。
       参考 ui-design-spec.md 的主题变体章节，确保 light/dark 切换。」
     - 「实现 component-spec.json 中标注的所有 variants（size/state）。」
     - 「注入 a11y 属性：按 component-spec.json 的 a11y.requirements 实现。」
  3. 读取 `<BASE>/ui-design/stitch-index.json`（如存在）
  4. 对关联了 Stitch HTML 的任务，注入：
     - 读取 `stitch/{screen_id}-{name}.html`
     - 「基于 Stitch 视觉稿结构，使用项目组件库和 design token 实现。
       保留布局结构，用框架原生方式重写。
       交互原语按 primitive-impl-map 实现：[primitives 列表]」
  5. 无 component-spec.json 或 stitch-index.json → 跳过，正常执行
  ↓
```

**Step 2: Commit**

```bash
git add dev-forge-skill/skills/task-execute.md
git commit -m "feat(dev-forge): add Stitch/component context injection to task-execute"
```

---

### Task 10: Add visual regression to e2e-verify.md

**Files:**
- Modify: `dev-forge-skill/skills/e2e-verify.md:169` (after Step 1.5)

**Step 1: Insert visual regression step after line 169**

After "OpenRouter 不可用 → 跳过", insert:

```markdown

Step 1.7: 视觉回归基准准备（stitch-index.json 存在时）
  跳过条件：`<BASE>/ui-design/stitch-index.json` 不存在
  1. 读取 stitch-index.json，获取 status=success 的屏幕 + route_path
  2. 将 stitch/*.png 复制到 `.allforai/product-verify/visual-regression/baseline/`
  3. 在 Step 2（Playwright 场景执行）中，对每个有基准的路由：
     a. 导航到 route_path
     b. 截取实际渲染截图 → `visual-regression/actual/`
     c. 像素级对比（pixelmatch，阈值参考）：
        ≤5% → PASS（字体渲染差异）
        5-15% → INFO（轻微偏差）
        15-30% → WARNING（明显偏差）
        >30% → FAIL（还原度不合格）
  4. 输出 `visual-regression/visual-regression-report.json`
  5. 无基准截图 → 跳过，不影响其他 E2E 场景
  ↓
```

**Step 2: Commit**

```bash
git add dev-forge-skill/skills/e2e-verify.md
git commit -m "feat(dev-forge): add visual regression verification to e2e-verify"
```

---

## Phase 5: Design-to-Spec Task Generation Update

### Task 11: Update design-to-spec Step 4 for B3 task ordering

**Files:**
- Modify: `dev-forge-skill/skills/design-to-spec.md` (Step 4 task generation section)

**Step 1: Add B3 task ordering rule**

Find the Step 4 section that generates `tasks.md`. Add this rule for B3 task ordering:

```markdown
当 component-spec.json 存在时，B3 任务分批调整：

**B3 Round 1**（共享组件优先）：
- 实现 component-spec.json 中的 shared_components
- 每个共享组件一个任务，含 variants + a11y 实现
- 任务元数据追加：`component_spec_ref: true`

**B3 Round 2+**（页面组件）：
- 页面级组件引用 Round 1 已实现的共享组件
- 如有 Stitch HTML → 任务追加 `stitch_ref: screen_id` + `stitch_html: 文件路径`
```

**Step 2: Commit**

```bash
git add dev-forge-skill/skills/design-to-spec.md
git commit -m "feat(dev-forge): add B3 shared-component-first ordering to design-to-spec"
```

---

## Verification Checklist

After all tasks complete, verify end-to-end:

1. `python3 product-design-skill/scripts/gen_ui_components.py <BASE> --mode auto` → `component-spec.json` generated
2. `python3 product-design-skill/scripts/gen_ui_stitch.py <BASE> --mode auto` → `stitch-prompts.json` generated
3. `npx -y @_davideast/stitch-mcp tool` → 11 tools listed (MCP server works)
4. Read `product-concept.md` → Q4 present in Step 3.5
5. Read `ui-design.md` → Step 5.3 (universal) + Step 5.5 (Stitch) present
6. Read `design-to-spec.md` → Step 2.5 with Layer 1/Layer 2 present
7. Read `task-execute.md` → Step 1.5 B3 context injection present
8. Read `e2e-verify.md` → Step 1.7 visual regression present
9. Verify non-blocking: remove stitch-index.json → all flows still work
