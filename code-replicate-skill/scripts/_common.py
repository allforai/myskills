#!/usr/bin/env python3
"""Shared utilities for code-replicate pre-built scripts.

Replicates essential functions from product-design's _common.py.
Plugins are independently installable and cannot import each other.
"""

import json
import os
import datetime
import sys

# ── Field Constants ───────────────────────────────────────────────────────────

# business-flows.json uses "nodes" (NOT "steps")
FLOW_NODES_FIELD = "nodes"


def get_flow_nodes(flow):
    """Get node list from a flow object, using the canonical 'nodes' field."""
    return flow.get(FLOW_NODES_FIELD, [])


def ensure_list(data, *keys):
    """Extract a list from data that may be a list or a dict wrapping one.

    If data is already a list, return it directly.
    If data is a dict, try each key in order, returning the first list found.
    Otherwise return [].
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in keys:
            v = data.get(k)
            if isinstance(v, list):
                return v
        # If dict has no matching key, try common wrapper patterns
        for k in ("items", "data", "results", "tasks", "gaps", "decisions"):
            v = data.get(k)
            if isinstance(v, list):
                return v
    return []


# ── Timestamp ─────────────────────────────────────────────────────────────────

def now_iso():
    """Return current UTC time in ISO 8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── File Utilities ────────────────────────────────────────────────────────────

def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def write_json(path, data):
    """Write data as formatted JSON with UTF-8 encoding."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_json(path):
    """Load JSON from path, return None if file not found or invalid."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def require_json(path, label="file"):
    """Load JSON from path, exit with error if not found."""
    data = load_json(path)
    if data is None:
        print(f"ERROR: {label} not found or invalid: {path}", file=sys.stderr)
        sys.exit(1)
    return data


def write_markdown(path, content):
    """Write markdown content to path with UTF-8 encoding."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ── Fragment Loader ───────────────────────────────────────────────────────────

def load_fragments(fragments_dir, prefix=""):
    """Load all .json files from dir, return sorted list of (module_id, data) tuples.

    Args:
        fragments_dir: Directory containing JSON fragment files.
        prefix: Optional prefix filter for filenames.

    Returns:
        Sorted list of (module_id, data) tuples where module_id is the
        filename stem (without .json extension).
    """
    results = []
    if not os.path.isdir(fragments_dir):
        return results
    for fname in os.listdir(fragments_dir):
        if not fname.endswith(".json"):
            continue
        if prefix and not fname.startswith(prefix):
            continue
        module_id = fname[:-5]  # strip .json
        data = load_json(os.path.join(fragments_dir, fname))
        if data is not None:
            results.append((module_id, data))
    results.sort(key=lambda x: x[0])
    return results


# ── ID Assignment ─────────────────────────────────────────────────────────────

def assign_ids(items, prefix="T", start=1):
    """Assign sequential IDs like T001, T002 to items.

    Modifies items in-place and returns them.
    """
    for i, item in enumerate(items, start=start):
        item["id"] = f"{prefix}{i:03d}"
    return items


# ── Deduplication ─────────────────────────────────────────────────────────────

def dedup_by(items, *keys):
    """Remove duplicates based on key combination.

    Args:
        items: List of dicts.
        *keys: Field names to use as composite dedup key.

    Returns:
        New list with duplicates removed (first occurrence kept).
    """
    seen = set()
    result = []
    for item in items:
        key = tuple(item.get(k, "") for k in keys)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("_common.py loaded successfully")
    print(f"  FLOW_NODES_FIELD = {FLOW_NODES_FIELD!r}")
    print(f"  now_iso() = {now_iso()}")
    print("All imports OK")
