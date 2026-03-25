#!/usr/bin/env python3
"""Merge screen fragment files into an experience-map stub.

CLI: python3 cr_merge_screens.py <base_path> <fragments_dir>

For frontend/fullstack modes only.  Loads all <fragments_dir>/screens/*.json,
merges, groups into a 3-layer hierarchy (operation_lines > nodes > screens),
assigns OL/N/S IDs, and writes a stub experience-map to
<base_path>/.allforai/experience-map/experience-map.json.

Design-side fields (emotion_design, ux_intent, non_negotiable, continuity)
are intentionally omitted — this is a code-reverse-engineered stub.
"""

import os
import re
import sys
from collections import OrderedDict

# Allow importing _common from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import (
    load_fragments,
    ensure_list,
    now_iso,
    write_json,
)


RENDER_AS_KEYWORDS = {
    "table": "data_table", "list": "data_table", "grid": "data_table",
    "form": "input_form", "edit": "input_form", "create": "input_form",
    "detail": "key_value", "info": "key_value", "profile": "key_value",
    "chart": "bar_chart", "graph": "bar_chart", "stats": "bar_chart", "dashboard": "bar_chart",
    "search": "search_filter", "filter": "search_filter",
    "action": "action_bar", "toolbar": "action_bar", "button": "action_bar",
    "tab": "tab_nav", "nav": "tab_nav", "menu": "tab_nav",
    "image": "media_grid", "photo": "media_grid", "gallery": "media_grid", "video": "media_grid",
    "card": "card_grid",
    "tree": "tree_view", "hierarchy": "tree_view",
    "timeline": "timeline", "history": "timeline", "log": "timeline",
    "text": "text_block", "content": "text_block", "article": "text_block",
}


def _infer_render_as(component):
    """Fallback: infer render_as when LLM fragment did not provide it.

    This is a best-effort heuristic. LLM fragments SHOULD include render_as
    directly (set via prompt in Phase 3.1.5). This function is only called when
    the fragment omits the field.
    """
    combined = (str(component.get("type", "")) + " " + str(component.get("purpose", ""))).lower()
    # Use word-boundary-aware matching to reduce false positives
    for keyword, render_as in RENDER_AS_KEYWORDS.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', combined):
            return render_as
    print(f"WARN: render_as for component '{component.get('type', '?')}' defaulted to 'text_block' by fallback — "
          "LLM fragment should include render_as directly", file=sys.stderr)
    return "text_block"


def merge_screens(base_path, fragments_dir):
    """Merge screen fragments into experience-map.json stub."""
    screens_dir = os.path.join(fragments_dir, "screens")
    fragments = load_fragments(screens_dir)

    # Collect all screens from all fragments
    all_screens = []
    for _module_id, data in fragments:
        screens = ensure_list(data, "screens")
        all_screens.extend(screens)

    # Group into 3-layer hierarchy: route_group -> page -> screen data
    group_map = OrderedDict()  # route_group -> OrderedDict(page -> [screen_data])

    for scr in all_screens:
        route_group = scr.get("route_group", "General")
        page = scr.get("page", "Unknown Page")

        if route_group not in group_map:
            group_map[route_group] = OrderedDict()
        if page not in group_map[route_group]:
            group_map[route_group][page] = {
                "route": scr.get("route", ""),
                "screens": [],
            }

        # Build components from actions (upgrade to structured format)
        raw_actions = scr.get("actions", [])
        components = scr.get("components", [])
        if not components and raw_actions:
            # Migrate legacy actions to components structure
            for act in raw_actions:
                comp = act if isinstance(act, dict) else {"type": str(act), "purpose": "", "behavior": ""}
                if "render_as" not in comp:
                    comp["render_as"] = _infer_render_as(comp)
                components.append(comp)

        # Build structured data_fields
        raw_fields = scr.get("data_fields", [])
        data_fields = []
        for f in raw_fields:
            if isinstance(f, dict):
                data_fields.append(f)
            else:
                data_fields.append({
                    "name": str(f),
                    "label": str(f),
                    "type": "string",
                    "input_widget": "text_input",
                    "required": False,
                })

        # Build states as structured dict
        raw_states = scr.get("states", [])
        if isinstance(raw_states, list):
            states = {
                "empty": "",
                "loading": "",
                "error": "",
                "success": "",
            }
            for s in raw_states:
                if isinstance(s, dict):
                    states.update(s)
                elif isinstance(s, str):
                    states[s] = s
        elif isinstance(raw_states, dict):
            states = raw_states
        else:
            states = {"empty": "", "loading": "", "error": "", "success": ""}

        screen_entry = {
            "name": scr.get("name", page),
            "description": scr.get("description", ""),
            "layout_type": scr.get("layout_type", ""),
            "layout_description": scr.get("layout_description", ""),
            "tasks": scr.get("tasks", []),
            "actions": raw_actions,
            "components": components,
            "interaction_pattern": scr.get("interaction_pattern", ""),
            "emotion_design": scr.get("emotion_design"),
            "states": states,
            "data_fields": data_fields,
            "view_modes": scr.get("view_modes"),
            "flow_context": scr.get("flow_context", {"prev": None, "next": None}),
        }
        group_map[route_group][page]["screens"].append(screen_entry)

    # Build output structure with IDs
    operation_lines = []
    ol_counter = 0
    s_counter = 0

    for group_name, pages in group_map.items():
        ol_counter += 1
        nodes = []
        n_counter = 0

        for page_name, page_data in pages.items():
            n_counter += 1
            # Assign screen IDs
            for scr in page_data["screens"]:
                s_counter += 1
                scr["id"] = f"S{s_counter:03d}"

            nodes.append({
                "id": f"N{n_counter:03d}",
                "name": page_name,
                "route": page_data["route"],
                "screens": page_data["screens"],
            })

        operation_lines.append({
            "id": f"OL{ol_counter:03d}",
            "name": group_name,
            "nodes": nodes,
        })

    # Build screen_index for fast downstream lookup
    screen_index = {}
    for ol in operation_lines:
        for node in ol.get("nodes", []):
            for scr in node.get("screens", []):
                screen_index[scr["id"]] = {
                    "name": scr.get("name", ""),
                    "operation_line": ol["id"],
                    "node": node["id"],
                }

    # Write output
    output_path = os.path.join(base_path, ".allforai", "experience-map", "experience-map.json")
    output = {
        "generated_at": now_iso(),
        "source": "code-replicate",
        "fidelity": "stub",
        "operation_lines": operation_lines,
        "screen_index": screen_index,
    }
    write_json(output_path, output)

    total_screens = s_counter
    print(f"Merged {total_screens} screens → {output_path}", file=sys.stderr)
    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: cr_merge_screens.py <base_path> <fragments_dir>", file=sys.stderr)
        sys.exit(1)
    base_path = sys.argv[1]
    fragments_dir = sys.argv[2]
    merge_screens(base_path, fragments_dir)


if __name__ == "__main__":
    main()
