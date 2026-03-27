#!/usr/bin/env python3
"""Merge flow fragment files into a single business-flows.json.

CLI: python3 cr_merge_flows.py <base_path> <fragments_dir>

Loads all <fragments_dir>/flows/*.json, merges, dedups by flow name,
assigns F001..F999 IDs, validates node structure, cross-references
task-inventory.json, and writes to
<base_path>/.allforai/product-map/business-flows.json.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import (
    FLOW_NODES_FIELD,
    load_fragments,
    load_json,
    ensure_list,
    assign_ids,
    now_iso,
    write_json,
)


def merge_flows(base_path, fragments_dir):
    """Merge flow fragments into business-flows.json."""
    flows_dir = os.path.join(fragments_dir, "flows")
    fragments = load_fragments(flows_dir)

    # Collect all flows
    all_flows = []
    for _module_id, data in fragments:
        flows = ensure_list(data, "flows")
        all_flows.extend(flows)

    # Dedup by flow name (case-insensitive)
    seen = set()
    deduped = []
    for flow in all_flows:
        key = flow.get("name", "").strip().lower()
        if not key:
            continue
        if key not in seen:
            seen.add(key)
            deduped.append(flow)

    # Assign sequential IDs
    assign_ids(deduped, prefix="F", start=1)

    # Validate: every flow has nodes array, each node has task_ref, role, seq
    for flow in deduped:
        if FLOW_NODES_FIELD not in flow or not isinstance(flow[FLOW_NODES_FIELD], list):
            flow[FLOW_NODES_FIELD] = []
            print(f"WARNING: flow '{flow.get('name')}' missing {FLOW_NODES_FIELD}, set to []", file=sys.stderr)
        # Ensure description exists
        if "description" not in flow:
            flow["description"] = ""
        # Ensure confirmed flag
        if "confirmed" not in flow:
            flow["confirmed"] = False
        # Ensure gap_count
        gap_count = 0
        for node in flow[FLOW_NODES_FIELD]:
            for field in ("task_ref", "role", "seq"):
                if field not in node:
                    node[field] = "[INFERRED]"
                    print(f"WARNING: node in flow '{flow.get('name')}' missing '{field}'", file=sys.stderr)
            # Ensure handoff structure for cross-role transitions
            if "handoff" not in node:
                node["handoff"] = None
            # Ensure gap flag
            if "gap" not in node:
                node["gap"] = False
            if node.get("gap"):
                gap_count += 1
        flow["gap_count"] = gap_count

    # Cross-reference with task-inventory.json
    task_inv_path = os.path.join(base_path, ".allforai", "product-map", "task-inventory.json")
    task_data = load_json(task_inv_path)
    task_ids = set()
    if task_data:
        tasks = ensure_list(task_data, "tasks")
        task_ids = {t.get("id") for t in tasks if t.get("id")}

    # Collect all task_refs from flows
    referenced_task_ids = set()
    for flow in deduped:
        for node in flow.get(FLOW_NODES_FIELD, []):
            ref = node.get("task_ref", "")
            if ref and ref != "[INFERRED]":
                referenced_task_ids.add(ref)

    # Warn about missing references (only if we have task inventory)
    if task_ids:
        missing = referenced_task_ids - task_ids
        for ref in sorted(missing):
            print(f"WARNING: task_ref '{ref}' not found in task-inventory.json", file=sys.stderr)

    # Compute orphan tasks
    orphan_tasks = sorted(task_ids - referenced_task_ids) if task_ids else []

    # Write output
    output_path = os.path.join(base_path, ".allforai", "product-map", "business-flows.json")
    output = {
        "generated_at": now_iso(),
        "source": "code-replicate",
        "systems": {"current": "replicated-system", "linked": []},
        "flows": deduped,
        "orphan_tasks": orphan_tasks,
        "summary": {
            "flow_count": len(deduped),
            "flow_gaps": sum(f.get("gap_count", 0) for f in deduped),
            "orphan_tasks": orphan_tasks,
            "independent_operations": [],
            "orphan_count": len(orphan_tasks),
        },
    }
    write_json(output_path, output)

    print(f"Merged {len(deduped)} flows → {output_path}", file=sys.stderr)
    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: cr_merge_flows.py <base_path> <fragments_dir>", file=sys.stderr)
        sys.exit(1)
    base_path = sys.argv[1]
    fragments_dir = sys.argv[2]
    merge_flows(base_path, fragments_dir)


if __name__ == "__main__":
    main()
