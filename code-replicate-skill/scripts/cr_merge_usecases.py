#!/usr/bin/env python3
"""Merge use-case fragment files into a single use-case-tree.json.

CLI: python3 cr_merge_usecases.py <base_path> <fragments_dir>

Loads all <fragments_dir>/usecases/*.json, merges, assigns UC001..UC999 IDs,
builds a 4-layer tree (role > feature_area > task > use_case), validates
required fields, and writes to <base_path>/.allforai/use-case/use-case-tree.json.
"""

import os
import sys

# Allow importing _common from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import (
    load_fragments,
    ensure_list,
    assign_ids,
    now_iso,
    write_json,
)

VALID_TYPES = {"happy_path", "exception", "boundary", "validation"}
REQUIRED_FIELDS = ("title", "type", "given", "when", "then")


def merge_usecases(base_path, fragments_dir):
    """Merge use-case fragments into use-case-tree.json."""
    uc_dir = os.path.join(fragments_dir, "usecases")
    fragments = load_fragments(uc_dir)

    # Collect all use cases from all fragments
    all_ucs = []
    for _module_id, data in fragments:
        ucs = ensure_list(data, "use_cases")
        all_ucs.extend(ucs)

    # Validate required fields and type enum
    valid_ucs = []
    for uc in all_ucs:
        missing = [f for f in REQUIRED_FIELDS if not uc.get(f)]
        if missing:
            print(f"WARN: skipping use case missing {missing}: {uc.get('title', '???')}", file=sys.stderr)
            continue
        if uc["type"] not in VALID_TYPES:
            print(f"WARN: skipping use case with invalid type '{uc['type']}': {uc.get('title', '???')}", file=sys.stderr)
            continue
        valid_ucs.append(uc)

    # Assign sequential IDs
    assign_ids(valid_ucs, prefix="UC", start=1)

    # Build 4-layer tree: role > feature_area > task > use_case
    tree = _build_tree(valid_ucs)

    # Write output
    output_path = os.path.join(base_path, ".allforai", "use-case", "use-case-tree.json")
    output = {
        "generated_at": now_iso(),
        "source": "code-replicate",
        "tree": tree,
    }
    write_json(output_path, output)

    print(f"Merged {len(valid_ucs)} use cases → {output_path}", file=sys.stderr)
    return output_path


def _build_tree(use_cases):
    """Build 4-layer tree: role > feature_area > task > use_case."""
    # Intermediate grouping: (role, feature_area, task_ref) -> [use_cases]
    from collections import OrderedDict

    role_map = OrderedDict()  # role -> OrderedDict(feature_area -> OrderedDict(task_ref -> [ucs]))

    for uc in use_cases:
        role = uc.get("role", "UNKNOWN")
        fa = uc.get("feature_area", "General")
        task = uc.get("task_ref", "NONE")

        if role not in role_map:
            role_map[role] = OrderedDict()
        if fa not in role_map[role]:
            role_map[role][fa] = OrderedDict()
        if task not in role_map[role][fa]:
            role_map[role][fa][task] = []

        # Build the use-case entry (exclude grouping fields)
        uc_entry = {
            "id": uc["id"],
            "title": uc["title"],
            "type": uc["type"],
            "given": uc["given"],
            "when": uc["when"],
            "then": uc["then"],
            "priority": uc.get("priority", "medium"),
        }
        role_map[role][fa][task].append(uc_entry)

    # Convert to list structure
    tree = []
    for role, fa_map in role_map.items():
        feature_areas = []
        for fa_name, task_map in fa_map.items():
            tasks = []
            for task_ref, ucs in task_map.items():
                tasks.append({"task_ref": task_ref, "use_cases": ucs})
            feature_areas.append({"name": fa_name, "tasks": tasks})
        tree.append({"role": role, "feature_areas": feature_areas})

    return tree


def main():
    if len(sys.argv) < 3:
        print("Usage: cr_merge_usecases.py <base_path> <fragments_dir>", file=sys.stderr)
        sys.exit(1)
    base_path = sys.argv[1]
    fragments_dir = sys.argv[2]
    merge_usecases(base_path, fragments_dir)


if __name__ == "__main__":
    main()
