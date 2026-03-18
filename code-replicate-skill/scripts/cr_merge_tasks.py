#!/usr/bin/env python3
"""Merge task fragment files into a single task-inventory.json.

CLI: python3 cr_merge_tasks.py <base_path> <fragments_dir>

Loads all <fragments_dir>/tasks/*.json, merges, dedups by
(name, owner_role), assigns T001..T999 IDs, fills missing recommended
fields, and writes to <base_path>/.allforai/product-map/task-inventory.json.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import (
    load_fragments,
    ensure_list,
    assign_ids,
    now_iso,
    write_json,
)

# Required fields every task must have (id is assigned by us)
REQUIRED_FIELDS = ("name", "owner_role", "frequency", "risk_level", "main_flow", "status", "category")

# Recommended fields — filled with defaults if missing
RECOMMENDED_STRING_FIELDS = ("exceptions", "rules", "sla")
RECOMMENDED_ARRAY_FIELDS = ("acceptance_criteria", "inputs", "outputs", "prerequisites", "cross_dept")


def merge_tasks(base_path, fragments_dir):
    """Merge task fragments into task-inventory.json."""
    tasks_dir = os.path.join(fragments_dir, "tasks")
    fragments = load_fragments(tasks_dir)

    # Collect all tasks
    all_tasks = []
    for _module_id, data in fragments:
        tasks = ensure_list(data, "tasks")
        all_tasks.extend(tasks)

    # Dedup by (name, owner_role) — case-insensitive on name
    seen = set()
    deduped = []
    for task in all_tasks:
        key = (task.get("name", "").strip().lower(), task.get("owner_role", "").strip())
        if not key[0]:
            continue
        if key not in seen:
            seen.add(key)
            deduped.append(task)

    # Assign sequential IDs
    assign_ids(deduped, prefix="T", start=1)

    # Validate required fields and fill recommended fields
    for task in deduped:
        # Fill missing required fields with placeholder
        for field in REQUIRED_FIELDS:
            if field not in task or not task[field]:
                task[field] = "[INFERRED]"
        # Fill missing recommended string fields
        for field in RECOMMENDED_STRING_FIELDS:
            if field not in task:
                task[field] = "[INFERRED]"
        # Fill missing recommended array fields
        for field in RECOMMENDED_ARRAY_FIELDS:
            if field not in task:
                task[field] = []

    # Hard constraint: tasks MUST be an array
    assert isinstance(deduped, list), "tasks must be an array"

    # Write output
    output_path = os.path.join(base_path, ".allforai", "product-map", "task-inventory.json")
    output = {
        "generated_at": now_iso(),
        "source": "code-replicate",
        "tasks": deduped,
    }
    write_json(output_path, output)

    print(f"Merged {len(deduped)} tasks → {output_path}", file=sys.stderr)
    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: cr_merge_tasks.py <base_path> <fragments_dir>", file=sys.stderr)
        sys.exit(1)
    base_path = sys.argv[1]
    fragments_dir = sys.argv[2]
    merge_tasks(base_path, fragments_dir)


if __name__ == "__main__":
    main()
