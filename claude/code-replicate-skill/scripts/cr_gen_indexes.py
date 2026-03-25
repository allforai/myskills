#!/usr/bin/env python3
"""Generate lightweight index files for two-phase loading.

CLI: python3 cr_gen_indexes.py <base_path>

Reads task-inventory.json and business-flows.json, produces:
  - task-index.json  (categories + modules)
  - flow-index.json  (flow summaries)
"""

import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import (
    require_json,
    ensure_list,
    get_flow_nodes,
    now_iso,
    write_json,
)


def generate_indexes(base_path):
    """Generate task-index.json and flow-index.json."""
    pm_dir = os.path.join(base_path, ".allforai", "product-map")

    tasks_data = require_json(os.path.join(pm_dir, "task-inventory.json"), "task-inventory")
    flows_data = require_json(os.path.join(pm_dir, "business-flows.json"), "business-flows")

    tasks = ensure_list(tasks_data, "tasks")
    flows = ensure_list(flows_data, "flows")

    # ── task-index.json ──────────────────────────────────────────────────────
    # Group by category
    cat_map = OrderedDict()
    for t in tasks:
        cat = t.get("category", "")
        if not cat:
            continue
        if cat not in cat_map:
            cat_map[cat] = []
        cat_map[cat].append(t.get("id", ""))

    categories = [
        {"name": name, "task_count": len(ids), "task_ids": ids}
        for name, ids in cat_map.items()
    ]

    # Group by module (only if at least one task has module field)
    mod_map = OrderedDict()
    for t in tasks:
        mod = t.get("module", "")
        if not mod:
            continue
        if mod not in mod_map:
            mod_map[mod] = []
        mod_map[mod].append(t.get("id", ""))

    modules = [
        {"name": name, "task_count": len(ids), "task_ids": ids}
        for name, ids in mod_map.items()
    ]

    task_index = {
        "generated_at": now_iso(),
        "categories": categories,
        "modules": modules,
    }
    ti_path = write_json(os.path.join(pm_dir, "task-index.json"), task_index)

    # ── flow-index.json ──────────────────────────────────────────────────────
    flow_entries = []
    for flow in flows:
        nodes = get_flow_nodes(flow)
        gap_count = sum(1 for n in nodes if n.get("gap"))
        roles = list(OrderedDict.fromkeys(
            n.get("role") for n in nodes if n.get("role")
        ))
        flow_entries.append({
            "id": flow.get("id", ""),
            "name": flow.get("name", ""),
            "node_count": len(nodes),
            "gap_count": gap_count,
            "roles": roles,
        })

    flow_index = {
        "generated_at": now_iso(),
        "flows": flow_entries,
    }
    fi_path = write_json(os.path.join(pm_dir, "flow-index.json"), flow_index)

    print(f"Generated task-index ({len(categories)} cats, {len(modules)} mods) → {ti_path}", file=sys.stderr)
    print(f"Generated flow-index ({len(flow_entries)} flows) → {fi_path}", file=sys.stderr)
    return [ti_path, fi_path]


def main():
    if len(sys.argv) < 2:
        print("Usage: cr_gen_indexes.py <base_path>", file=sys.stderr)
        sys.exit(1)
    generate_indexes(sys.argv[1])


if __name__ == "__main__":
    main()
