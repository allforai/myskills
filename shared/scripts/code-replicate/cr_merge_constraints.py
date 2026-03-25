#!/usr/bin/env python3
"""Merge constraint fragment files into a single constraints.json.

CLI: python3 cr_merge_constraints.py <base_path> <fragments_dir>

Loads all <fragments_dir>/constraints/*.json, merges, dedups by description
(fuzzy — normalize whitespace + lowercase), assigns C001..C999 IDs, validates
required fields, and writes to <base_path>/.allforai/product-map/constraints.json.
"""

import os
import re
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

VALID_ENFORCEMENT = {"hard", "soft"}
REQUIRED_FIELDS = ("description", "enforcement")


def _normalize_description(desc):
    """Normalize description for fuzzy dedup: lowercase, collapse whitespace."""
    return re.sub(r"\s+", " ", desc.strip().lower())


def merge_constraints(base_path, fragments_dir):
    """Merge constraint fragments into constraints.json."""
    cons_dir = os.path.join(fragments_dir, "constraints")
    fragments = load_fragments(cons_dir)

    # Collect all constraints from all fragments
    all_constraints = []
    for _module_id, data in fragments:
        constraints = ensure_list(data, "constraints")
        all_constraints.extend(constraints)

    # Validate required fields
    valid = []
    for c in all_constraints:
        missing = [f for f in REQUIRED_FIELDS if not c.get(f)]
        if missing:
            print(f"WARN: skipping constraint missing {missing}: {c.get('description', '???')[:50]}", file=sys.stderr)
            continue
        if c["enforcement"] not in VALID_ENFORCEMENT:
            print(f"WARN: skipping constraint with invalid enforcement '{c['enforcement']}'", file=sys.stderr)
            continue
        valid.append(c)

    # Dedup by description (fuzzy)
    seen = set()
    deduped = []
    for c in valid:
        key = _normalize_description(c["description"])
        if key not in seen:
            seen.add(key)
            deduped.append(c)

    # Assign sequential IDs
    assign_ids(deduped, prefix="C", start=1)

    # Write output
    output_path = os.path.join(base_path, ".allforai", "product-map", "constraints.json")
    output = {
        "generated_at": now_iso(),
        "source": "code-replicate",
        "constraints": deduped,
    }
    write_json(output_path, output)

    print(f"Merged {len(deduped)} constraints → {output_path}", file=sys.stderr)
    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: cr_merge_constraints.py <base_path> <fragments_dir>", file=sys.stderr)
        sys.exit(1)
    base_path = sys.argv[1]
    fragments_dir = sys.argv[2]
    merge_constraints(base_path, fragments_dir)


if __name__ == "__main__":
    main()
