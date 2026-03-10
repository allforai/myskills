#!/usr/bin/env python3
"""Generate component-spec.json from experience-map analysis.

Universal component analysis: shared components, interaction primitives,
variants, and a11y specs. Does NOT depend on Stitch or any external service.

Usage:
    python3 gen_ui_components.py <BASE_PATH> [--mode auto]
"""
import os, sys, json
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from _common import (
    parse_args, load_experience_map, build_screen_by_id_from_lines,
    load_product_concept,
    write_json, ensure_dir, append_pipeline_decision, now_iso,
)

# ── Component inference — REMOVED in v5.0 ─────────────────────────────────────
# Previously: PRIMITIVE_MAP (37 entries), A11Y_RULES (10 entries), keyword matching.
# Now: Claude Code assigns primitives and a11y specs during LLM enrichment.

def get_primitives(interaction_type):
    """Deprecated: returns empty list. LLM enrichment assigns primitives directly."""
    return []

def infer_a11y(component_name, has_actions=False):
    """Deprecated: returns minimal a11y stub. LLM enrichment assigns full a11y specs."""
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
            "screens": [s["id"] for s in screens],
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

        if itype.startswith("MG1") or itype == "MG2-L" or itype.startswith("CT"):
            # List-type screens → shared list + card components
            list_name = _infer_component_name(ss, "List")
            card_name = _infer_component_name(ss, "Card")

            shared[list_name] = {
                "screens": [s["id"] for s in ss],
                "inferred_from": f"同一 interaction_type:{itype} 列表容器",
                "props": ["items", "onLoadMore", "onRefresh"],
                "primitives": get_primitives(itype),
                "variants": infer_variants(ss, list_name),
                "a11y": infer_a11y(list_name),
            }
            shared[card_name] = {
                "screens": [s["id"] for s in ss],
                "inferred_from": f"同一 interaction_type:{itype} 列表项",
                "props": _infer_card_props(ss),
                "primitives": [],
                "variants": infer_variants(ss, card_name),
                "a11y": infer_a11y(card_name, has_actions=True),
            }

        if itype in ("MG2-C", "MG2-E", "MG8", "SY2", "SB1"):
            form_name = _infer_component_name(ss, "Form")
            shared[form_name] = {
                "screens": [s["id"] for s in ss],
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
            "screens": [s["id"] for s in search_screens],
            "inferred_from": "多个屏幕包含搜索操作",
            "props": ["placeholder", "onSearch", "onClear"],
            "primitives": [],
            "variants": {"state": ["default", "focused", "disabled"]},
            "a11y": infer_a11y("SearchBar"),
        }

    return shared


def _infer_component_name(screens, suffix):
    """Infer component name from screen names."""
    names = [s.get("screen_name", "") for s in screens]
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


def build_screen_components(screens, shared_components):
    """Build per-screen component usage map."""
    mapping = {}
    for s in screens:
        sid = s["id"]
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
    """Build reverse mapping: primitive → components that use it.

    Previously used PRIMITIVE_MAP; now derived from shared_components at runtime.
    LLM enrichment will populate primitives on each component.
    """
    reverse = defaultdict(set)
    for name, comp in shared_components.items():
        for p in comp.get("primitives", []):
            reverse[p].add(name)
    return {k: ", ".join(sorted(v)) for k, v in reverse.items() if v}


def main():
    base, args = parse_args()
    op_lines, screen_index, em_loaded = load_experience_map(base)
    if not em_loaded or not op_lines:
        print("ERROR: experience-map.json not found or empty", file=sys.stderr)
        sys.exit(1)

    screens = list(build_screen_by_id_from_lines(op_lines).values())

    # Build screen context for ux_intent reference
    screen_context = {}
    for ol in op_lines:
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                screen_context[s["id"]] = {
                    "ux_intent": node.get("ux_intent", ""),
                }

    shared = identify_shared_components(screens)
    screen_comps = build_screen_components(screens, shared)
    prim_map = build_primitive_mapping(shared)

    spec = {
        "generated_at": now_iso(),
        "source": "experience-map",
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
