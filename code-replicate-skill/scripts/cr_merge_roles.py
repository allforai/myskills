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

    # Ensure minimum required fields: id, name, audience_type
    for role in deduped:
        if "name" not in role:
            role["name"] = "[UNKNOWN]"
        # audience_type — dev-forge consumer_apps identification depends on this
        if "audience_type" not in role:
            role["audience_type"] = _infer_audience_type(role)

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


def _infer_audience_type(role):
    """Fallback: infer audience_type when LLM fragment did not provide it.

    This is a best-effort heuristic. LLM fragments SHOULD include audience_type
    directly (set via prompt in Phase 3.1). This function is only called when
    the fragment omits the field.
    """
    # If LLM provided permission_boundary or kpi hints, use them
    perms = " ".join(role.get("permission_boundary", [])).lower()
    if any(kw in perms for kw in ("admin", "manage", "system", "moderate", "审核", "管理")):
        return "professional"

    # Last resort: keyword heuristic on name + description
    name = role.get("name", "").lower()
    desc = role.get("description", "").lower()
    combined = name + " " + desc

    professional_signals = ("admin", "manager", "operator", "staff", "merchant",
                            "moderator", "reviewer", "auditor", "管理", "运营", "审核", "客服")
    for kw in professional_signals:
        if kw in combined:
            return "professional"

    print(f"WARN: audience_type for role '{role.get('name')}' inferred as 'consumer' by fallback heuristic — "
          "LLM fragment should include audience_type directly", file=sys.stderr)
    return "consumer"


def main():
    if len(sys.argv) < 3:
        print("Usage: cr_merge_roles.py <base_path> <fragments_dir>", file=sys.stderr)
        sys.exit(1)
    base_path = sys.argv[1]
    fragments_dir = sys.argv[2]
    merge_roles(base_path, fragments_dir)


if __name__ == "__main__":
    main()
