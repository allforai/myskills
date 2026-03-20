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

VALID_TYPES = {
    "happy_path", "exception", "boundary", "validation",
    "journey_guidance", "result_visibility", "continuity", "entry_clarity",
    "innovation_mechanism", "innovation_boundary",
    "state_transition", "state_timeout", "state_compensation",
}
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

    # Build flat use_cases array with explicit fields (product-design v2.5.0+ format)
    flat_ucs = _build_flat_list(valid_ucs)

    # Write output
    output_path = os.path.join(base_path, ".allforai", "use-case", "use-case-tree.json")
    output = {
        "generated_at": now_iso(),
        "version": "2.5.0",
        "source": "code-replicate",
        "scope": "full",
        "use_cases": flat_ucs,
    }
    write_json(output_path, output)

    print(f"Merged {len(flat_ucs)} use cases → {output_path}", file=sys.stderr)
    return output_path


def _build_flat_list(use_cases):
    """Build flat use_cases array with explicit role/area/task fields."""
    flat = []
    for uc in use_cases:
        # Ensure then is an array
        then_val = uc.get("then", "")
        if isinstance(then_val, str):
            then_val = [then_val] if then_val else []

        entry = {
            "id": uc["id"],
            "role_id": uc.get("role", "UNKNOWN"),
            "role_name": uc.get("role_name", ""),
            "functional_area_id": uc.get("functional_area_id", ""),
            "functional_area_name": uc.get("feature_area", "General"),
            "task_id": uc.get("task_ref", "NONE"),
            "task_name": uc.get("task_name", ""),
            "type": uc["type"],
            "priority": uc.get("priority", "medium"),
            "given": uc["given"],
            "when": uc["when"],
            "then": then_val,
            "innovation_use_case": uc.get("innovation_use_case", False),
        }
        flat.append(entry)
    return flat


def main():
    if len(sys.argv) < 3:
        print("Usage: cr_merge_usecases.py <base_path> <fragments_dir>", file=sys.stderr)
        sys.exit(1)
    base_path = sys.argv[1]
    fragments_dir = sys.argv[2]
    merge_usecases(base_path, fragments_dir)


if __name__ == "__main__":
    main()
