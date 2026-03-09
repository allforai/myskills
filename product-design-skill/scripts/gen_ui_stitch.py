#!/usr/bin/env python3
"""Generate stitch-prompts.json from component-spec.json + experience-map.

Reads the universal component-spec.json and builds Stitch-ready prompts
with component vocabulary, consistency directives, and style tokens.

Usage:
    python3 gen_ui_stitch.py <BASE_PATH> [--screens S010,S025] [--mode auto] [--limit 10]
"""
import os, sys, json, re

sys.path.insert(0, os.path.dirname(__file__))
import _common as C
from _common import (
    parse_args, load_experience_map, build_screen_by_id_from_lines,
    load_product_concept,
    write_json, ensure_dir, append_pipeline_decision, now_iso,
    load_json,
)

# ── Interaction type → layout description mapping ────────────────────────────
ITYPE_LAYOUT = {
    "MG1": "Read-only list/grid view. Show data items with search/filter bar at top. Each item is a card or row. Tap opens detail.",
    "MG2-L": "CRUD list with action toolbar. Search bar + '+ New' button at top. Each row has inline edit/delete actions. Bulk selection supported.",
    "MG2-C": "Create form. Input fields stacked vertically with labels. Primary 'Submit/Create' button at bottom. Show validation states on fields.",
    "MG2-E": "Edit form. Pre-filled input fields. 'Save' primary button + 'Cancel' secondary. Show changed field indicators.",
    "MG2-D": "Detail view. Hero section at top with key info. Content sections below. Action buttons (edit/delete) in header or bottom bar.",
    "MG3": "State machine / workflow view. Status tabs or progress indicator at top. List of items filtered by status. Action buttons change item state.",
    "MG4": "Approval workflow. Pending count badge. Each item shows requester, content summary, timestamp. Approve/Reject action buttons per item.",
}


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
        return [s for s in screens if s["id"] in explicit_ids]

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

        scored.append((score, s["id"], s))

    scored.sort(key=lambda x: -x[0])
    selected = scored[:limit]

    result = []
    for i, (score, sid, s) in enumerate(selected):
        s_copy = dict(s)
        s_copy["priority"] = "P0" if i < 5 else "P1"
        s_copy["selection_score"] = score
        result.append(s_copy)
    return result


def build_prompt(screen, concept, component_spec, device_type, is_anchor,
                 screen_context=None, wf_feedback=None, ctx=None):
    """Build a layered Stitch prompt for a screen."""
    sid = screen["id"]
    name = screen.get("name", sid)
    it = screen.get("interaction_type", "")
    if isinstance(it, list):
        it = it[0] if it else ""
    actions = screen.get("actions", [])
    states = screen.get("states", {})
    data_fields = screen.get("data_fields", [])
    non_negotiable = screen.get("non_negotiable", [])

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

    # Layer 2: Screen structure from interaction_type (wireframe → Stitch bridge)
    layout_desc = ITYPE_LAYOUT.get(it, "")
    action_descs = []
    for a in actions[:5]:
        label = a.get("label", "") if isinstance(a, dict) else str(a)
        action_descs.append(label)

    layer2 = f"""Screen: {name}
Purpose: {screen.get('primary_purpose', name)}
Primary action: {screen.get('primary_action', action_descs[0] if action_descs else 'View')}
Actions: {', '.join(action_descs)}
"""
    if it and layout_desc:
        layer2 += f"Screen type ({it}): {layout_desc}\n"

    # Data fields → Stitch knows what real fields to render
    if data_fields:
        field_names = []
        for f in data_fields[:10]:
            if isinstance(f, dict):
                fn = f.get("label", f.get("name", ""))
            else:
                fn = str(f)
            if fn:
                field_names.append(fn)
        if field_names:
            layer2 += f"Data fields to show: {', '.join(field_names)}\n"

    # ── VO-precision data fields ──
    if ctx:
        vos = ctx.vo_for_screen(sid)
        if vos:
            precise_fields = []
            for vo in vos:
                for f in vo.get("fields", []):
                    fname = f.get("label", f.get("name", ""))
                    ftype = f.get("type", "string")
                    freq = "required" if f.get("required") else "optional"
                    precise_fields.append(f"{fname}({ftype}, {freq})")
            if precise_fields:
                layer2 += f"Precise data fields: {', '.join(precise_fields)}\n"

        # API binding context
        apis = ctx.api_for_screen(sid)
        if apis:
            api_descs = [f"{ep.get('method', 'GET')} {ep.get('path', '')}" for ep in apis]
            layer2 += f"API endpoints: {', '.join(api_descs)}\n"

    if isinstance(states, dict) and states:
        state_descs = [f"{k}: {v}" for k, v in states.items()]
        layer2 += f"States: {'; '.join(state_descs)}\n"

    # Non-negotiable constraints
    if non_negotiable:
        layer2 += f"Required: {', '.join(non_negotiable)}\n"

    # Layer 3: Anchor reference (non-anchor screens only)
    layer3 = ""
    if not is_anchor:
        layer3 = "Maintain visual consistency with the first screen in this project. Use the same component styles, spacing, and color application.\n"

    # ── Behavioral standards ──
    bs_hint = ""
    if ctx and ctx.behavioral_standards:
        standards = ctx.behavioral_standards.get("standards", ctx.behavioral_standards.get("behaviors", []))
        if isinstance(standards, list):
            std_descs = []
            for std in standards[:5]:
                state = std.get("state", "")
                behavior = std.get("behavior", std.get("description", ""))
                if state and behavior:
                    std_descs.append(f"{state}: {behavior}")
            if std_descs:
                bs_hint = "Behavioral standards: " + "; ".join(std_descs) + "\n"

    # Layer 4: Emotion / UX intent from experience-map
    prompt_parts = []
    if screen_context:
        sc_ctx = screen_context.get(sid, {})
        if sc_ctx.get("emotion_state"):
            prompt_parts.append(f"Emotion context: {sc_ctx['emotion_state']}")
        if sc_ctx.get("ux_intent"):
            prompt_parts.append(f"UX intent: {sc_ctx['ux_intent']}")

    # Layer 5: Wireframe review feedback (human reviewer constraints)
    if wf_feedback:
        screen_fb = wf_feedback.get("screens", {}).get(sid, {})
        pins = screen_fb.get("pins", [])
        if pins:
            comments = [p.get("comment", "") for p in pins if p.get("comment")]
            if comments:
                prompt_parts.append("Reviewer feedback: " + "; ".join(comments[:5]))

    layer4 = "\n".join(prompt_parts) + "\n" if prompt_parts else ""

    # Layout hint
    layout = "Use flexible layouts (flexbox/grid) that can adapt to different screen sizes. Avoid fixed pixel widths on containers."

    # ── Constraint layer (highest priority) ──
    constraint_hint = ""
    if ctx:
        screen_constraints = [c for c in ctx.get_constraints("ui-design")
                              if c.get("screen_id") == sid or not c.get("screen_id")]
        if screen_constraints:
            lines = []
            for c in screen_constraints:
                prefix = "MUST" if c.get("severity") == "must" else "SHOULD"
                lines.append(f"{prefix}: {c['constraint']}")
            constraint_hint = "\n".join(lines) + "\n"

    return f"{constraint_hint}{layer1}\n{bs_hint}{layer2}\n{layer3}{layer4}{layout}"


def main():
    base, args = parse_args()
    op_lines, screen_index, em_loaded = load_experience_map(base)
    if not em_loaded:
        print("ERROR: experience-map.json not found", file=sys.stderr)
        sys.exit(1)

    screens = list(build_screen_by_id_from_lines(op_lines).values())

    # Build screen context from operation lines
    screen_context = {}
    for ol in op_lines:
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                screen_context[s["id"]] = {
                    "emotion_state": node.get("emotion_state", "neutral"),
                    "ux_intent": node.get("ux_intent", ""),
                }

    concept = load_product_concept(base)
    comp_spec = load_component_spec(base)
    ctx = C.load_full_context(base)
    if not comp_spec:
        print("WARNING: component-spec.json not found. Run gen_ui_components.py first.", file=sys.stderr)
        comp_spec = {"shared_components": {}, "screen_components": {}}

    # Load wireframe review feedback (optional — human reviewer constraints)
    wf_feedback = load_json(os.path.join(base, "wireframe-review/review-feedback.json"))
    if wf_feedback and wf_feedback.get("submitted_at"):
        pin_count = sum(len(sc.get("pins", [])) for sc in wf_feedback.get("screens", {}).values())
        print(f"  WF feedback: {pin_count} pins from wireframe review")
    else:
        wf_feedback = None

    limit = int(args.get("limit", "10"))
    explicit_screens = args.get("screens")
    device_type = infer_device_type(concept)

    selected = select_priority_screens(screens, limit=limit, explicit=explicit_screens)
    if not selected:
        print("ERROR: no screens selected", file=sys.stderr)
        sys.exit(1)

    anchor_id = selected[0]["id"]
    prompt_entries = []
    for i, s in enumerate(selected):
        prompt = build_prompt(s, concept, comp_spec, device_type, is_anchor=(i == 0),
                              screen_context=screen_context, wf_feedback=wf_feedback, ctx=ctx)
        prompt_entries.append({
            "screen_id": s["id"],
            "screen_name": s.get("name", s["id"]),
            "priority": s.get("priority", "P1"),
            "generation_order": i,
            "prompt": prompt,
            "device_type": device_type,
            "model_id": "GEMINI_3_PRO",
            "referenced_components": comp_spec.get("screen_components", {}).get(s["id"], {}).get("used_shared", []),
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
