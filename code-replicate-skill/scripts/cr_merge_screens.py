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

        screen_entry = {
            "actions": scr.get("actions", []),
            "states": scr.get("states", []),
            "data_fields": scr.get("data_fields", []),
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

    # Write output
    output_path = os.path.join(base_path, ".allforai", "experience-map", "experience-map.json")
    output = {
        "generated_at": now_iso(),
        "source": "code-replicate",
        "fidelity": "stub",
        "operation_lines": operation_lines,
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
