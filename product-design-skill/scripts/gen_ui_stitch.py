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


def build_prompt(screen, concept, component_spec, device_type, is_anchor):
    """Build a layered Stitch prompt for a screen."""
    sid = screen["id"]
    name = screen.get("name", sid)
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

    anchor_id = selected[0]["id"]
    prompt_entries = []
    for i, s in enumerate(selected):
        prompt = build_prompt(s, concept, comp_spec, device_type, is_anchor=(i == 0))
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
