#!/usr/bin/env python3
"""Merge role fragment files into a single role-profiles.json.

CLI: python3 cr_merge_roles.py <base_path> <fragments_dir>

Loads all <fragments_dir>/roles/*.json, merges, dedups by name
(case-insensitive), assigns R001..R999 IDs, and writes to
<base_path>/.allforai/product-map/role-profiles.json.
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


def merge_roles(base_path, fragments_dir):
    """Merge role fragments into role-profiles.json."""
    roles_dir = os.path.join(fragments_dir, "roles")
    fragments = load_fragments(roles_dir)

    # Collect all roles from all fragments
    all_roles = []
    for _module_id, data in fragments:
        roles = ensure_list(data, "roles")
        all_roles.extend(roles)

    # Dedup by name (case-insensitive) — keep first occurrence
    seen = set()
    deduped = []
    for role in all_roles:
        key = role.get("name", "").strip().lower()
        if not key:
            continue
        if key not in seen:
            seen.add(key)
            deduped.append(role)

    # Assign sequential IDs
    assign_ids(deduped, prefix="R", start=1)

    # Ensure minimum required fields: id, name
    for role in deduped:
        if "name" not in role:
            role["name"] = "[UNKNOWN]"

    # Write output
    output_path = os.path.join(base_path, ".allforai", "product-map", "role-profiles.json")
    output = {
        "generated_at": now_iso(),
        "source": "code-replicate",
        "roles": deduped,
    }
    write_json(output_path, output)

    print(f"Merged {len(deduped)} roles → {output_path}", file=sys.stderr)
    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: cr_merge_roles.py <base_path> <fragments_dir>", file=sys.stderr)
        sys.exit(1)
    base_path = sys.argv[1]
    fragments_dir = sys.argv[2]
    merge_roles(base_path, fragments_dir)


if __name__ == "__main__":
    main()
