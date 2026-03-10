# Skeleton generator — LLM enrichment required after running
#!/usr/bin/env python3
"""Generate UI design spec skeleton with raw screen data.

Skeleton for Phase 7 (ui-design). For each screen, outputs basic UI spec
using existing data (interaction_type, data_fields, actions, emotion context).
No keyword-based screen type classification or layout inference.
LLM enrichment is required for screen type, layout, and wireframe generation.

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
tasks = {t["id"]: C._normalize_task(t) for t in inv["tasks"]}
roles = C.load_role_profiles_full(BASE)
role_map = {r["id"]: r["name"] for r in roles}
role_audience = {r["id"]: r.get("audience_type", "default") for r in roles}

op_lines, screen_index, em_loaded = C.load_experience_map(BASE)
if not em_loaded:
    print("ERROR: experience-map.json is required for ui-design", file=sys.stderr)
    sys.exit(1)

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
fctx = C.load_full_context(BASE)

# ── Style configuration ──────────────────────────────────────────────────────
_UI_STYLE_ALIASES = {
    "apple-hig": "ios-human-interface",
    "apple": "ios-human-interface",
    "ios": "ios-human-interface",
    "hig": "ios-human-interface",
    "material": "material-design-3",
    "material-3": "material-design-3",
    "md3": "material-design-3",
}


def _resolve_style(args, concept):
    explicit = args.get("style", "")
    if explicit:
        return _UI_STYLE_ALIASES.get(explicit, explicit)
    if concept:
        prefs = concept.get("pipeline_preferences", {})
        pref_style = prefs.get("ui_style", "")
        if pref_style and pref_style != "undecided":
            return _UI_STYLE_ALIASES.get(pref_style, pref_style)
    return "material-design-3"


style_name = _resolve_style(args, concept)

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
            raw_role = task.get("owner_role") or task.get("role_id", "")
            for r in raw_role.split(","):
                r = r.strip()
                if r:
                    screen_roles.add(r)
    for rid in screen_roles:
        role_screens.setdefault(rid, []).append(s)

# ── Generate design spec (markdown) ──────────────────────────────────────────
mission = concept.get("mission", "") if concept else ""

spec_lines = []
spec_lines.append("# UI 设计规格（骨架）\n")
spec_lines.append("> LLM enrichment required: screen types and layouts pending\n")
spec_lines.append(f"> 风格: {STYLE}")
spec_lines.append(f"> 生成时间: {NOW}")
spec_lines.append(f"> 产品: {mission}\n")

spec_lines.append("## 设计语言基础\n")
spec_lines.append("### 配色系统\n")
spec_lines.append(f"- 主色 (Primary): {S['primary']}")
spec_lines.append(f"- 次色 (Secondary): {S['secondary']}")
spec_lines.append(f"- 强调色 (Tertiary): {S['tertiary']}")
spec_lines.append(f"- 背景: {S['bg']}")
spec_lines.append(f"- 表面 (Surface): {S['surface']}")
spec_lines.append(f"- 功能色: 成功 {S['success']} · 警告 {S['warning']} · 错误 {S['error']}\n")

spec_lines.append("### 排版\n")
spec_lines.append(f"- 字体推荐: {S['font']}")
spec_lines.append(f"- 圆角: {S['radius']}\n")

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
        actions = s.get("actions", [])
        primary_actions = [a["label"] for a in actions if a.get("frequency") == "高"]
        secondary_actions = [a["label"] for a in actions if a.get("frequency") != "高"]

        # Emotion context
        ctx = screen_context.get(sid, {})

        spec_lines.append(f"#### {s['name']}（{sid}）\n")
        if ctx:
            spec_lines.append(f"**Emotion Context**: {ctx['emotion_state']} ({ctx['emotion_intensity']}/10)")
            if ctx['ux_intent']:
                spec_lines.append(f"**Interaction Intent**: {ctx['ux_intent']}")
            if ctx['non_negotiable']:
                spec_lines.append(f"**Non-negotiable**: {', '.join(ctx['non_negotiable'])}")
            if ctx['gate_issues']:
                issues_str = "; ".join(i.get('detail', '') for i in ctx['gate_issues'])
                spec_lines.append(f"**Quality Gate Issues**: {issues_str}")
            spec_lines.append("")

        spec_lines.append(f"**界面目的**: {s.get('notes', '支撑关联任务')}")
        spec_lines.append(f"**Interaction Type**: {s.get('interaction_type', 'pending')}")
        spec_lines.append("**主要操作**:")
        for a in primary_actions[:3]:
            spec_lines.append(f"  - {a} (primary)")
        for a in secondary_actions[:3]:
            spec_lines.append(f"  - {a} (secondary)")
        spec_lines.append("")

with open(os.path.join(OUT, "ui-design-spec.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(spec_lines) + "\n")

# ── Generate ui-design-spec.json ──────────────────────────────────────────────
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
            raw_role = task.get("owner_role") or task.get("role_id", "")
            if not screen_role:
                first_r = raw_role.split(",")[0].strip()
                screen_role = role_map.get(first_r, "")
            for _r in raw_role.split(","):
                _r = _r.strip()
                if _r and role_audience.get(_r, "default") == "professional":
                    audience = "professional"

    actions = s.get("actions", [])
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
    task_priority = "core" if "core" in task_cats else ("basic" if "basic" in task_cats else "auxiliary")

    # Use real states from experience-map when available, else generic
    em_states = s.get("states", {})
    if not em_states or not isinstance(em_states, dict):
        em_states = {
            "empty": "pending_design",
            "loading": "pending_design",
            "error": "pending_design",
        }

    # Emotion context
    ctx = screen_context.get(sid, {})

    screen_entry = {
        "id": sid,
        "name": s.get("name", ""),
        "role": screen_role,
        "module": s.get("module", "其他"),
        "audience_type": audience,
        "task_priority": task_priority,
        "interaction_type": s.get("interaction_type", ""),
        "screen_type": "pending_llm_classification",
        "layout": "pending_llm_classification",
        "sections": sections,
        "states": em_states,
        "actions": [{"label": a.get("label", ""), "crud": a.get("crud", "R"),
                      "frequency": a.get("frequency", "")} for a in actions],
        "data_fields": s.get("data_fields", []),
        "non_negotiable": s.get("non_negotiable", []),
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

    # ── FullContext enrichment ────────────────────────────────────────────
    # (a) VO-based field enrichment
    vos = fctx.vo_for_screen(sid)
    if vos and not screen_entry.get("data_fields"):
        vo_fields = []
        for vo in vos:
            for f in vo.get("fields", []):
                vo_fields.append({
                    "name": f.get("name", ""),
                    "type": f.get("type", "string"),
                    "input_widget": f.get("input_widget", "text"),
                    "required": f.get("required", False),
                    "label": f.get("label", f.get("name", "")),
                })
        if vo_fields:
            screen_entry["data_fields"] = vo_fields
            screen_entry["data_fields_source"] = "view-objects"

    # (b) API binding enrichment
    apis = fctx.api_for_screen(sid)
    if apis:
        screen_entry["api_bindings"] = [
            {"endpoint": ep.get("path", ""), "method": ep.get("method", ""), "api_id": ep.get("id", "")}
            for ep in apis
        ]

    # (c) Behavioral standards injection
    if fctx.behavioral_standards:
        standards = fctx.behavioral_standards.get("standards", fctx.behavioral_standards.get("behaviors", []))
        if isinstance(standards, list):
            existing_states = screen_entry.get("states", {})
            if isinstance(existing_states, dict):
                for std in standards:
                    state_key = std.get("state", "")
                    if state_key and state_key not in existing_states:
                        existing_states[state_key] = std.get("behavior", std.get("description", ""))
                screen_entry["states"] = existing_states

    # (d) Pattern catalog reference
    if fctx.pattern_catalog:
        itype = screen_entry.get("interaction_type", "")
        patterns = fctx.pattern_catalog.get("patterns", [])
        matched = [p for p in patterns if itype in p.get("interaction_types", [])]
        if matched:
            screen_entry["pattern_refs"] = [p.get("pattern_id", p.get("id", "")) for p in matched[:3]]

    # (e) Constraint overrides
    screen_constraints = [c for c in fctx.get_constraints("ui-design")
                          if c.get("screen_id") == sid or not c.get("screen_id")]
    if screen_constraints:
        screen_entry["review_constraints"] = [
            {"constraint": c.get("comment") or c.get("constraint", ""), "severity": c.get("severity", "must")}
            for c in screen_constraints
        ]

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
    "llm_enrichment_required": True,
}
C.write_json(os.path.join(OUT, "ui-design-spec.json"), spec_json)

# ── Generate tokens.json ──────────────────────────────────────────────────────
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

# ── Decisions ─────────────────────────────────────────────────────────────────
decisions = [
    {"step": "Step 1", "item_id": "profile", "decision": "auto_confirmed",
     "value": f"{len(roles)} roles, {len(screens)} screens", "decided_at": NOW},
    {"step": "Step 2", "item_id": "style", "decision": "auto_confirmed",
     "value": STYLE, "reason": f"style={style_name}", "decided_at": NOW},
    {"step": "Step 3", "item_id": "spec", "decision": "auto_confirmed",
     "value": "ui-design-spec.md + ui-design-spec.json generated (skeleton)", "decided_at": NOW},
]
C.write_json(os.path.join(OUT, "ui-design-decisions.json"), decisions)

# ── Pipeline decisions ────────────────────────────────────────────────────────
C.append_pipeline_decision(
    BASE,
    "Phase 7 — ui-design",
    f"style={STYLE}, roles={len(roles)}, screens={len(screens)}, "
    f"skeleton generated (LLM enrichment required for screen types, layouts, wireframes)",
    shard=args.get("shard")
)

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"Style: {STYLE}")
print(f"Roles: {len(roles)}")
print(f"Screens: {len(screens)}")
print(f"Status: skeleton generated, LLM enrichment required")
print(f"  - Screen type classification: pending")
print(f"  - Layout inference: pending")
print(f"  - Wireframe generation: pending")
print(f"  - HTML previews: pending (requires screen types)")
print(f"\nAll files written to {OUT}/")
