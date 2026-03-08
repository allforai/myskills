#!/usr/bin/env python3
"""Generate UI design spec, decisions, and HTML previews.

Pre-built script for Phase 7 (ui-design).
- Reads experience-map (operation_lines with emotion/intent/constraints)
- Loads interaction-gate for quality-gate issues per node
- Generates emotion-aware design spec with context fields
- HTML previews include emotion indicator color bars
- Style parameterized via --style argument
- Pipeline-decisions dedup via _common.append_pipeline_decision()

Usage:
    python3 gen_ui_design.py <BASE_PATH> [--mode auto] [--style material-design-3]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

# ── Setup ─────────────────────────────────────────────────────────────────────
BASE, args = C.parse_args()
OUT = os.path.join(BASE, "ui-design")
PREVIEW = os.path.join(OUT, "preview")
C.ensure_dir(PREVIEW)
NOW = C.now_iso()

# ── Load data ─────────────────────────────────────────────────────────────────
inv = C.require_json(
    os.path.join(BASE, "product-map/task-inventory.json"),
    "task-inventory.json"
)
tasks = {t["id"]: t for t in inv["tasks"]}
roles = C.load_role_profiles_full(BASE)
role_map = {r["id"]: r["name"] for r in roles}
role_audience = {r["id"]: r.get("audience_type", "default") for r in roles}

op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
if not em_loaded:
    print("ERROR: experience-map.json is required for ui-design", file=sys.stderr)
    sys.exit(1)

# Flatten screens from operation lines
screen_by_id = C.build_screen_by_id_from_lines(op_lines)
screens = list(screen_by_id.values())

# Load interaction gate for quality-gate issues
gate = C.load_interaction_gate(BASE)
gate_issues_by_node = {}
if gate:
    for lr in gate.get("lines", []):
        for issue in lr.get("issues", []):
            nid = issue.get("node", "")
            gate_issues_by_node.setdefault(nid, []).append(issue)

# Build screen context mapping (emotion, intent, constraints, continuity, gate issues)
screen_context = {}
for ol in op_lines:
    for node in ol.get("nodes", []):
        nid = node["id"]
        for s in node.get("screens", []):
            sid = s["id"]
            screen_context[sid] = {
                "emotion_state": node.get("emotion_state", "neutral"),
                "emotion_intensity": node.get("emotion_intensity", 5),
                "ux_intent": node.get("ux_intent", ""),
                "non_negotiable": s.get("non_negotiable", []),
                "operation_line": ol["id"],
                "node_id": nid,
                "continuity": ol.get("continuity", {}),
                "gate_issues": gate_issues_by_node.get(nid, []),
            }

concept = C.load_product_concept(BASE)

# ── Style configuration ──────────────────────────────────────────────────────
style_name = args.get("style", "material-design-3")

# Style presets
STYLES = {
    "material-design-3": {
        "name": "Material Design 3",
        "primary": "#6750A4", "on_primary": "#FFFFFF",
        "secondary": "#625B71", "tertiary": "#7D5260",
        "bg": "#FFFBFE", "surface": "#FFFBFE",
        "surface_variant": "#E7E0EC",
        "on_surface": "#1C1B1F", "on_surface_variant": "#49454F",
        "error": "#B3261E", "success": "#2E7D32", "warning": "#ED6C02",
        "radius": "12px",
        "shadow": "0 1px 3px 1px rgba(0,0,0,.15), 0 1px 2px rgba(0,0,0,.3)",
        "font": "'Roboto', 'Noto Sans SC', sans-serif",
        "lib": "Flutter Material 3",
        "lib_alt": "MUI (React)",
    },
    "ios-human-interface": {
        "name": "iOS Human Interface",
        "primary": "#007AFF", "on_primary": "#FFFFFF",
        "secondary": "#5856D6", "tertiary": "#FF9500",
        "bg": "#F2F2F7", "surface": "#FFFFFF",
        "surface_variant": "#E5E5EA",
        "on_surface": "#000000", "on_surface_variant": "#8E8E93",
        "error": "#FF3B30", "success": "#34C759", "warning": "#FF9500",
        "radius": "10px",
        "shadow": "0 1px 4px rgba(0,0,0,.12)",
        "font": "-apple-system, 'SF Pro', 'Noto Sans SC', sans-serif",
        "lib": "SwiftUI / Cupertino (Flutter)",
        "lib_alt": "Ant Design (React)",
    },
}

S = STYLES.get(style_name, STYLES["material-design-3"])
STYLE = S["name"]

# ── Build role -> screens mapping ─────────────────────────────────────────────
role_screens = {}
for s in screens:
    screen_tasks = s.get("tasks", [])
    screen_roles = set()
    for tid in screen_tasks:
        task = tasks.get(tid)
        if task:
            screen_roles.add(task["owner_role"])
    for rid in screen_roles:
        role_screens.setdefault(rid, []).append(s)

# ── Generate design spec ─────────────────────────────────────────────────────
spec_lines = []
spec_lines.append("# UI 设计规格\n")
spec_lines.append(f"> 风格: {STYLE}")
spec_lines.append(f"> 生成时间: {NOW}")
mission = concept.get("mission", "") if concept else ""
spec_lines.append(f"> 产品: {mission}\n")

spec_lines.append("## 设计语言基础\n")
spec_lines.append("### 配色系统\n")
spec_lines.append(f"- 主色 (Primary): {S['primary']}")
spec_lines.append(f"- 次色 (Secondary): {S['secondary']}")
spec_lines.append(f"- 强调色 (Tertiary): {S['tertiary']}")
spec_lines.append(f"- 背景: {S['bg']}")
spec_lines.append(f"- 表面 (Surface): {S['surface']}")
spec_lines.append(f"- 表面变体: {S['surface_variant']}")
spec_lines.append(f"- 功能色: 成功 {S['success']} · 警告 {S['warning']} · 错误 {S['error']}\n")

spec_lines.append("### 排版\n")
spec_lines.append("- Display: 57px / 400")
spec_lines.append("- Headline: 32px / 400")
spec_lines.append("- Title: 22px / 500")
spec_lines.append("- Body: 16px / 400 / 行高 24px")
spec_lines.append("- Label: 14px / 500")
spec_lines.append(f"- 字体推荐: {S['font']}\n")

spec_lines.append("### 组件规范\n")
spec_lines.append(f"- 圆角: {S['radius']}")
spec_lines.append("- 间距系统: 4px 基准 (4/8/12/16/24/32)")
spec_lines.append("- 按钮: Filled (主操作) / Outlined (次要) / Text (辅助)")
spec_lines.append("- 卡片: Elevated (阴影) / Filled (填充) / Outlined (边框)")
spec_lines.append("- 输入框: 默认 outlined，聚焦态主色边框")
spec_lines.append("- 导航: Bottom navigation (C端) / Navigation rail (B端)\n")

spec_lines.append("### 推荐组件库\n")
spec_lines.append(f"- 首选: {S['lib']}")
spec_lines.append(f"- 备选: {S['lib_alt']}\n")

spec_lines.append("---\n")
spec_lines.append("## 界面规格\n")

# Group screens by module
module_screens = {}
for s in screens:
    mod = s.get("module", "其他")
    module_screens.setdefault(mod, []).append(s)

for mod, slist in module_screens.items():
    spec_lines.append(f"### 模块: {mod}\n")
    for s in slist:
        sid = s["id"]
        screen_tasks = s.get("tasks", [])
        audience = "consumer"
        for tid in screen_tasks:
            task = tasks.get(tid)
            if task:
                at = role_audience.get(task["owner_role"], "default")
                if at == "professional":
                    audience = "professional"
                    break

        actions = s.get("actions", [])
        primary_actions = [a["label"] for a in actions if a.get("frequency") == "高"]
        secondary_actions = [a["label"] for a in actions if a.get("frequency") != "高"]

        if audience == "professional":
            layout = "侧边导航 + 内容区（表格/列表导向）"
        elif len(actions) > 5:
            layout = "顶部导航 + 多区域卡片布局"
        else:
            layout = "单列卡片流"

        # Determine if screen serves core or basic tasks
        task_cats = set()
        for tid in screen_tasks:
            t = tasks.get(tid)
            if t:
                task_cats.add(t.get("category", ""))
        cat_label = "core" if "core" in task_cats else ("basic" if "basic" in task_cats else "")

        spec_parts = []
        # Emotion context from experience-map
        ctx = screen_context.get(sid, {})
        if ctx:
            spec_parts.append(f"**Emotion Context**: {ctx['emotion_state']} ({ctx['emotion_intensity']}/10)")
            if ctx['ux_intent']:
                spec_parts.append(f"**Interaction Intent**: {ctx['ux_intent']}")
            if ctx['non_negotiable']:
                spec_parts.append(f"**Non-negotiable**: {', '.join(ctx['non_negotiable'])}")
            if ctx['gate_issues']:
                issues_str = "; ".join(i.get('detail', '') for i in ctx['gate_issues'])
                spec_parts.append(f"**Quality Gate Issues**: {issues_str}")

        spec_lines.append(f"#### {s['name']}（{sid}）[{audience}]{' [core]' if cat_label == 'core' else ''}\n")
        # Prepend emotion context before layout/component content
        for sp in spec_parts:
            spec_lines.append(sp)
        if spec_parts:
            spec_lines.append("")
        spec_lines.append(f"**界面目的**: {s.get('notes', '支撑关联任务')}\n")
        spec_lines.append(f"**功能类别**: {'核心功能' if cat_label == 'core' else '基本功能'}\n")
        spec_lines.append(f"**布局模式**: {layout}\n")
        spec_lines.append("**主要操作**:")
        for a in primary_actions[:3]:
            spec_lines.append(f"  - {a} (Filled Button)")
        for a in secondary_actions[:3]:
            spec_lines.append(f"  - {a} (Outlined Button)")
        spec_lines.append("")
        spec_lines.append("**关键状态设计**:")
        spec_lines.append("  - 空态: 插图 + 引导文案 + CTA 按钮")
        spec_lines.append("  - 加载中: 骨架屏 (shimmer)")
        spec_lines.append("  - 错误: Snackbar (错误色) + 重试按钮")
        spec_lines.append("  - 成功: Snackbar (成功色) / 页面跳转")
        spec_lines.append("")

with open(os.path.join(OUT, "ui-design-spec.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(spec_lines) + "\n")

# ── Generate ui-design-spec.json (for ui_review_server) ─────────────────────
spec_json_screens = []
for s in screens:
    sid = s["id"]
    screen_tasks = s.get("tasks", [])

    # Determine audience type and role
    audience = "consumer"
    screen_role = ""
    for tid in screen_tasks:
        task = tasks.get(tid)
        if task:
            if not screen_role:
                screen_role = role_map.get(task["owner_role"], "")
            at = role_audience.get(task["owner_role"], "default")
            if at == "professional":
                audience = "professional"

    # Determine layout
    actions = s.get("actions", [])
    if audience == "professional":
        layout = "侧边导航 + 内容区（表格/列表导向）"
    elif len(actions) > 5:
        layout = "顶部导航 + 多区域卡片布局"
    else:
        layout = "单列卡片流"

    # Determine sections from actions
    primary_actions = [a["label"] for a in actions if a.get("frequency") == "高"]
    secondary_actions = [a["label"] for a in actions if a.get("frequency") != "高"]
    sections = []
    if primary_actions:
        sections.append("主操作区")
    if secondary_actions:
        sections.append("辅助操作区")
    sections.append("内容区")

    # Task categories
    task_cats = set()
    for tid in screen_tasks:
        t = tasks.get(tid)
        if t:
            task_cats.add(t.get("category", ""))
    interaction_type = "core" if "core" in task_cats else ("basic" if "basic" in task_cats else "auxiliary")

    # Emotion context
    ctx = screen_context.get(sid, {})

    screen_entry = {
        "id": sid,
        "name": s.get("name", ""),
        "role": screen_role,
        "module": s.get("module", "其他"),
        "audience_type": audience,
        "interaction_type": interaction_type,
        "layout": layout,
        "sections": sections,
        "states": {
            "empty": "插图 + 引导文案 + CTA 按钮",
            "loading": "骨架屏 (shimmer)",
            "error": "Snackbar (错误色) + 重试按钮",
        },
        "task_refs": screen_tasks,
        "notes": s.get("notes", ""),
    }
    if ctx:
        screen_entry["emotion_context"] = {
            "state": ctx.get("emotion_state", "neutral"),
            "intensity": ctx.get("emotion_intensity", 5),
            "ux_intent": ctx.get("ux_intent", ""),
            "operation_line": ctx.get("operation_line", ""),
        }

    spec_json_screens.append(screen_entry)

spec_json = {
    "generated_at": NOW,
    "style": STYLE,
    "product": mission,
    "design_tokens": {
        "colors": {
            "primary": S["primary"],
            "secondary": S["secondary"],
            "tertiary": S["tertiary"],
            "background": S["bg"],
            "surface": S["surface"],
            "error": S["error"],
            "success": S["success"],
            "warning": S["warning"],
        },
        "typography": {
            "font": S["font"],
            "display": "57px / 400",
            "headline": "32px / 400",
            "title": "22px / 500",
            "body": "16px / 400 / 行高 24px",
            "label": "14px / 500",
        },
        "spacing": "4px 基准 (4/8/12/16/24/32)",
        "border_radius": S["radius"],
    },
    "screens": spec_json_screens,
}
C.write_json(os.path.join(OUT, "ui-design-spec.json"), spec_json)

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
    "success": {"animation": "scale-bounce", "duration_ms": 300, "easing": "cubic-bezier(0.34, 1.56, 0.64, 1)", "haptic": "impact-medium"},
    "error": {"animation": "shake", "duration_ms": 400, "easing": "ease-out", "haptic": "notification-error"},
    "loading": {"animation": "pulse", "duration_ms": 1000, "easing": "ease-in-out", "haptic": "none"},
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

    # Detect CRUD types present on this screen
    crud_set = {a.get("crud") for a in s.get("actions", [])}
    has_mutating = crud_set & {"C", "U", "D"}

    # Success state override for C-type screens
    if "C" in crud_set:
        ov = MICRO_OVERRIDES["success"]
        screen_micros.append({
            "trigger": "create-success",
            **ov,
            "emotion_alignment": "satisfying confirmation",
        })
        spec_lines.append(
            f"| {s['name']} ({sid}) | create-success | {ov['animation']} "
            f"| {ov['duration_ms']}ms | {ov['easing']} | {ov['haptic']} |"
        )

    # Error state override for any mutating screen (C/U/D)
    if has_mutating:
        ov = MICRO_OVERRIDES["error"]
        screen_micros.append({
            "trigger": "error-feedback",
            **ov,
            "emotion_alignment": "error alert",
        })
        spec_lines.append(
            f"| {s['name']} ({sid}) | error-feedback | {ov['animation']} "
            f"| {ov['duration_ms']}ms | {ov['easing']} | {ov['haptic']} |"
        )

    # Loading state for screens with async operations (C/U/D)
    if has_mutating:
        ov = MICRO_OVERRIDES["loading"]
        screen_micros.append({
            "trigger": "async-loading",
            **ov,
            "emotion_alignment": "processing feedback",
        })
        spec_lines.append(
            f"| {s['name']} ({sid}) | async-loading | {ov['animation']} "
            f"| {ov['duration_ms']}ms | {ov['easing']} | {ov['haptic']} |"
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

# Rewrite spec with micro-interactions appended
with open(os.path.join(OUT, "ui-design-spec.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(spec_lines) + "\n")
spec_text = "\n".join(spec_lines)


# ── XV auto-apply helpers ────────────────────────────────────────────────────

def _apply_design_review_findings(data, spec_lines):
    """Apply design review: append high-severity usability issues as warnings in spec.

    Returns issue_count.
    """
    issues = [i for i in data.get("usability_issues", []) if i.get("severity") == "high"]
    if not issues:
        return 0

    spec_lines.append("\n---\n")
    spec_lines.append("## XV 交叉验证：高严重度可用性问题\n")
    spec_lines.append("| 位置 | 问题 | 建议 |")
    spec_lines.append("|------|------|------|")
    for issue in issues:
        spec_lines.append(
            f"| {issue.get('screen_or_section', '')} "
            f"| {issue.get('issue', '')} "
            f"| {issue.get('suggestion', '')} |"
        )
    return len(issues)


def _apply_visual_consistency_findings(data, spec_lines):
    """Apply visual consistency: append inconsistencies and token gaps to spec.

    Returns finding_count.
    """
    items = data.get("inconsistencies", []) + data.get("token_gaps", [])
    if not items:
        return 0

    spec_lines.append("\n## XV 交叉验证：设计一致性\n")
    inconsistencies = data.get("inconsistencies", [])
    if inconsistencies:
        spec_lines.append("### 不一致问题\n")
        for inc in inconsistencies:
            screens_str = ", ".join(inc.get("screens", []))
            spec_lines.append(f"- **{screens_str}**: {inc.get('issue', '')}")

    token_gaps = data.get("token_gaps", [])
    if token_gaps:
        spec_lines.append("\n### 缺失设计令牌\n")
        for tg in token_gaps:
            spec_lines.append(f"- **{tg.get('token', '')}**: {tg.get('context', '')}")

    return len(items)


# ── XV Cross-model validation ────────────────────────────────────────────────
xv_reviews = []

if C.xv_available():
    from xv_prompts import design_review_prompt, visual_consistency_prompt

    # XV-1: design_review → gemini
    try:
        dr_prompt = design_review_prompt(spec_text, len(screens), len(roles))
        dr_result = C.xv_call("design_review", dr_prompt["user"], dr_prompt["system"])
        print(f"  XV design_review: model={dr_result['model_used']}")
        dr_data = C.xv_parse_json(dr_result["response"])
        issue_count = _apply_design_review_findings(dr_data, spec_lines)
        xv_reviews.append({
            "task_type": "design_review",
            "model_used": dr_result["model_used"],
            "family": dr_result["family"],
            "auto_applied": {"high_severity_issues": issue_count},
            "raw_findings": dr_data,
        })
        print(f"  XV design_review: {issue_count} high-severity issues appended")
    except Exception as e:
        print(f"  XV design_review failed: {e} (continuing without XV)", file=sys.stderr)

    # XV-2: visual_consistency → gpt
    try:
        vc_prompt = visual_consistency_prompt(screens, S)
        vc_result = C.xv_call("visual_consistency", vc_prompt["user"], vc_prompt["system"])
        print(f"  XV visual_consistency: model={vc_result['model_used']}")
        vc_data = C.xv_parse_json(vc_result["response"])
        finding_count = _apply_visual_consistency_findings(vc_data, spec_lines)
        xv_reviews.append({
            "task_type": "visual_consistency",
            "model_used": vc_result["model_used"],
            "family": vc_result["family"],
            "auto_applied": {"consistency_findings": finding_count},
            "raw_findings": vc_data,
        })
        print(f"  XV visual_consistency: {finding_count} findings appended")
    except Exception as e:
        print(f"  XV visual_consistency failed: {e} (continuing without XV)", file=sys.stderr)

    if xv_reviews:
        # Rewrite spec with XV findings appended
        with open(os.path.join(OUT, "ui-design-spec.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(spec_lines) + "\n")
        # Write XV review to separate file
        C.write_json(os.path.join(OUT, "ui-xv-review.json"), C.xv_review(xv_reviews))
        print(f"  XV: ui-design-spec.md rewritten, ui-xv-review.json created")
    else:
        print(f"  XV: all calls failed, primary output unchanged")


# ── Emotion color mapping ────────────────────────────────────────────────────
EMOTION_COLORS = {
    "curious": "#4FC3F7", "anxious": "#FF8A65", "satisfied": "#81C784",
    "frustrated": "#E57373", "neutral": "#B0BEC5", "exploring": "#64B5F6",
    "confident": "#66BB6A", "confused": "#FFB74D",
}

# ── Generate HTML previews ───────────────────────────────────────────────────
CSS = f"""
body {{ font-family: {S['font']}; background: {S['bg']}; color: {S['on_surface']}; margin: 0; padding: 0; }}
.header {{ background: {S['primary']}; color: {S['on_primary']}; padding: 16px 24px; font-size: 22px; font-weight: 500; }}
.header a {{ color: {S['on_primary']}; text-decoration: none; opacity: 0.8; font-size: 14px; }}
.header a:hover {{ opacity: 1; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
.card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
.card {{ background: {S['surface']}; border-radius: {S['radius']}; box-shadow: {S['shadow']}; padding: 20px; transition: box-shadow 0.2s; }}
.card:hover {{ box-shadow: 0 2px 6px 2px rgba(0,0,0,.15), 0 1px 2px rgba(0,0,0,.3); }}
.card h3 {{ margin: 0 0 8px; font-size: 18px; color: {S['on_surface']}; }}
.card .subtitle {{ font-size: 14px; color: {S['on_surface_variant']}; margin-bottom: 12px; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 8px; font-size: 12px; font-weight: 500; }}
.badge-consumer {{ background: #E8DEF8; color: {S['primary']}; }}
.badge-professional {{ background: #D0BCFF; color: #21005D; }}
.actions {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
.btn-filled {{ background: {S['primary']}; color: {S['on_primary']}; border: none; padding: 8px 16px; border-radius: 20px; font-size: 14px; cursor: pointer; }}
.btn-outlined {{ background: transparent; color: {S['primary']}; border: 1px solid {S['primary']}; padding: 8px 16px; border-radius: 20px; font-size: 14px; cursor: pointer; }}
.states {{ margin-top: 12px; font-size: 13px; color: {S['on_surface_variant']}; }}
.states span {{ margin-right: 12px; }}
.module-title {{ font-size: 20px; font-weight: 500; margin: 24px 0 12px; color: {S['primary']}; }}
a.card-link {{ text-decoration: none; color: inherit; }}
.task-count {{ font-size: 13px; color: {S['on_surface_variant']}; margin-top: 8px; }}
"""

def html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# index.html
index_cards = []
for role in roles:
    rid = role["id"]
    rname = role["name"]
    at = role.get("audience_type", "default")
    rscreens = role_screens.get(rid, [])
    screen_count = len(rscreens)
    role_tasks = [t for t in inv["tasks"] if t["owner_role"] == rid and t.get("frequency") == "高"]
    top3 = [t["task_name"] for t in role_tasks[:3]]
    safe_name = rname.replace("/", "-").replace(" ", "-")
    badge_class = "badge-consumer" if at == "consumer" else "badge-professional"
    index_cards.append(f"""
    <a href="ui-role-{html_escape(safe_name)}.html" class="card-link">
      <div class="card">
        <h3>{html_escape(rname)}</h3>
        <span class="badge {badge_class}">{html_escape(at)}</span>
        <div class="subtitle">{screen_count} 个界面</div>
        <div class="states">{'<br>'.join(html_escape(t) for t in top3) if top3 else '无高频任务'}</div>
      </div>
    </a>""")

index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UI 设计预览 — {html_escape(mission[:40])}</title>
<style>{CSS}</style></head>
<body>
<div class="header">{html_escape(mission[:50])} — UI 设计预览
<div style="font-size:14px;opacity:0.8;margin-top:4px">风格: {STYLE} · {len(roles)} 角色 · {len(screens)} 界面</div>
</div>
<div class="container">
<div class="card-grid">
{''.join(index_cards)}
</div>
</div>
</body></html>"""

with open(os.path.join(PREVIEW, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)

# Per-role HTML files
for role in roles:
    rid = role["id"]
    rname = role["name"]
    at = role.get("audience_type", "default")
    safe_name = rname.replace("/", "-").replace(" ", "-")
    rscreens = role_screens.get(rid, [])

    mod_groups = {}
    for s in rscreens:
        mod = s.get("module", "其他")
        mod_groups.setdefault(mod, []).append(s)

    content = ""
    for mod, slist in mod_groups.items():
        content += f'<div class="module-title">{html_escape(mod)}</div>\n<div class="card-grid">\n'
        for s in slist:
            actions = s.get("actions", [])
            high_actions = [a for a in actions if a.get("frequency") == "高"]
            other_actions = [a for a in actions if a.get("frequency") != "高"]

            btns = ""
            for a in high_actions[:3]:
                btns += f'<button class="btn-filled">{html_escape(a["label"])}</button>\n'
            for a in other_actions[:2]:
                btns += f'<button class="btn-outlined">{html_escape(a["label"])}</button>\n'

            task_count = len(s.get("tasks", []))
            # Emotion indicator color
            ctx = screen_context.get(s["id"], {})
            emo_color = EMOTION_COLORS.get(ctx.get("emotion_state", ""), "#B0BEC5")
            emo_label = ctx.get("emotion_state", "neutral") if ctx else "neutral"
            content += f"""
  <div class="card" style="border-top: 4px solid {emo_color};">
    <h3>{html_escape(s['name'])}</h3>
    <span class="badge badge-{'consumer' if at == 'consumer' else 'professional'}">{html_escape(at)}</span>
    <span class="badge" style="background:{emo_color}33;color:{emo_color};margin-left:4px;">{html_escape(emo_label)}</span>
    <div class="subtitle">{html_escape(s.get('notes', ''))}</div>
    <div class="actions">{btns}</div>
    <div class="states">
      <span>正常: 默认视图</span>
      <span>空态: 引导+CTA</span>
      <span>错误: Snackbar</span>
    </div>
    <div class="task-count">{task_count} 个关联任务</div>
  </div>"""
        content += "\n</div>\n"

    role_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html_escape(rname)} — UI 设计预览</title>
<style>{CSS}</style></head>
<body>
<div class="header">
  <a href="index.html">← 返回总览</a> &nbsp;·&nbsp; {html_escape(rname)}
  <div style="font-size:14px;opacity:0.8;margin-top:4px">风格: {STYLE} · {len(rscreens)} 个界面</div>
</div>
<div class="container">
{content}
</div>
</body></html>"""

    with open(os.path.join(PREVIEW, f"ui-role-{safe_name}.html"), "w", encoding="utf-8") as f:
        f.write(role_html)

# ── Decisions ─────────────────────────────────────────────────────────────────
decisions = [
    {"step": "Step 1", "item_id": "profile", "decision": "auto_confirmed",
     "value": f"{len(roles)} roles, {len(screens)} screens", "decided_at": NOW},
    {"step": "Step 2", "item_id": "style", "decision": "auto_confirmed",
     "value": STYLE, "reason": f"style={style_name}", "decided_at": NOW},
    {"step": "Step 3", "item_id": "principles", "decision": "auto_confirmed",
     "value": "CSS variables applied", "decided_at": NOW},
    {"step": "Step 4", "item_id": "spec", "decision": "auto_confirmed",
     "value": "ui-design-spec.md generated", "decided_at": NOW},
    {"step": "Step 5", "item_id": "preview", "decision": "auto_confirmed",
     "value": f"index.html + {len(roles)} role HTML files", "decided_at": NOW},
]
if xv_reviews:
    xv_summary = ", ".join(f"{r['task_type']}({r['model_used']})" for r in xv_reviews)
    decisions.append({
        "step": "XV", "item_id": "cross_model_review", "decision": "auto_confirmed",
        "value": xv_summary, "decided_at": C.now_iso(),
    })
C.write_json(os.path.join(OUT, "ui-design-decisions.json"), decisions)

# ── Pipeline decisions ────────────────────────────────────────────────────────
html_files = [f for f in os.listdir(PREVIEW) if f.endswith(".html")]
C.append_pipeline_decision(
    BASE,
    "Phase 7 — ui-design",
    f"style={STYLE}, roles={len(roles)}, screens={len(screens)}, html_files={len(html_files)}",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Style: {STYLE}")
print(f"Roles: {len(roles)}")
print(f"Screens: {len(screens)}")
print(f"HTML files: {len(html_files)}")
print(f"Spec: ui-design-spec.md")
print(f"\nAll files written to {OUT}/")
