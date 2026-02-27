#!/usr/bin/env python3
"""Shared utilities for product-design pre-built scripts.

All Phase 4-8 scripts import this module for:
- Field constants (single source of truth for field names across layers)
- Data loaders (defensive loading with FileNotFoundError handling)
- Pipeline-decisions writer (append with phase-level deduplication)
- Utility functions (timestamps, JSON writing, directory creation)
"""

import json
import os
import datetime
import sys

# ── Field Constants ───────────────────────────────────────────────────────────
# screen-map.json uses "tasks", screen-index.json uses "task_refs"
SCREEN_TASKS_FIELD = "tasks"
SCREEN_INDEX_TASK_REFS_FIELD = "task_refs"

# business-flows.json uses "nodes" (NOT "steps")
FLOW_NODES_FIELD = "nodes"


def get_screen_tasks(screen):
    """Get task ID list from a screen object, supporting both field names."""
    return screen.get(SCREEN_TASKS_FIELD, screen.get(SCREEN_INDEX_TASK_REFS_FIELD, []))


def get_flow_nodes(flow):
    """Get node list from a flow object, using the canonical 'nodes' field."""
    return flow.get(FLOW_NODES_FIELD, [])


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


# ── Data Loaders ──────────────────────────────────────────────────────────────

def load_task_inventory(base, category=None):
    """Load task-inventory.json, return dict keyed by task ID.

    Args:
        base: .allforai base path
        category: None (all), "basic", or "core" — filter by task category
    """
    inv = require_json(
        os.path.join(base, "product-map/task-inventory.json"),
        "task-inventory.json"
    )
    tasks = inv["tasks"]
    if category:
        tasks = [t for t in tasks if t.get("category") == category]
    return {t["id"]: t for t in tasks}


def load_task_index(base):
    """Load task-index.json, return data or None."""
    return load_json(os.path.join(base, "product-map/task-index.json"))


def load_role_profiles(base):
    """Load role-profiles.json, return {role_id: role_name} map."""
    roles = require_json(
        os.path.join(base, "product-map/role-profiles.json"),
        "role-profiles.json"
    )
    return {r["id"]: r["name"] for r in roles["roles"]}


def load_role_profiles_full(base):
    """Load role-profiles.json, return full roles list."""
    roles = require_json(
        os.path.join(base, "product-map/role-profiles.json"),
        "role-profiles.json"
    )
    return roles["roles"]


def load_screen_map(base):
    """Load screen-map.json, return (screens_list, injected_bool)."""
    sm = load_json(os.path.join(base, "screen-map/screen-map.json"))
    if sm is None:
        return [], False
    return sm.get("screens", []), True


def load_business_flows(base):
    """Load business-flows.json, return flows list."""
    fd = load_json(os.path.join(base, "product-map/business-flows.json"))
    if fd is None:
        return []
    return fd.get("flows", [])


def load_flow_index(base):
    """Load flow-index.json, return data or None."""
    return load_json(os.path.join(base, "product-map/flow-index.json"))


def load_product_concept(base):
    """Load product-concept.json, return data or None."""
    return load_json(os.path.join(base, "product-concept/product-concept.json"))


# ── Screen-Task Mapping ──────────────────────────────────────────────────────

def build_task_screen_map(screens):
    """Build {task_id: [screen_objects]} mapping from screen list."""
    result = {}
    for s in screens:
        for tid in get_screen_tasks(s):
            result.setdefault(tid, []).append(s)
    return result


def build_screen_by_id(screens):
    """Build {screen_id: screen_object} mapping."""
    return {s["id"]: s for s in screens}


# ── Flow-Task References ─────────────────────────────────────────────────────

def collect_flow_task_refs(flows):
    """Collect all task IDs referenced by flow nodes."""
    refs = set()
    for flow in flows:
        for node in get_flow_nodes(flow):
            if isinstance(node, str):
                refs.add(node)
            elif isinstance(node, dict):
                refs.add(node.get("task_ref", ""))
    return refs


# ── Pipeline Decisions ────────────────────────────────────────────────────────

def append_pipeline_decision(base, phase, detail, decision="auto_confirmed"):
    """Append a decision to pipeline-decisions.json, dedup by phase name.

    If an entry with the same 'phase' already exists, it is replaced
    (prevents duplicate entries on re-runs).
    """
    pipe_path = os.path.join(base, "pipeline-decisions.json")
    pipe = []
    if os.path.exists(pipe_path):
        try:
            with open(pipe_path) as f:
                pipe = json.load(f)
        except (json.JSONDecodeError, IOError):
            pipe = []

    # Remove existing entry with same phase (dedup)
    pipe = [p for p in pipe if p.get("phase") != phase]

    pipe.append({
        "phase": phase,
        "decision": decision,
        "detail": detail,
        "decided_at": now_iso()
    })

    write_json(pipe_path, pipe)
    return pipe_path


# ── CLI Base Path Resolution ─────────────────────────────────────────────────

def resolve_base_path():
    """Resolve BASE path from CLI argument or default to .allforai/ in cwd."""
    if len(sys.argv) >= 2:
        base = sys.argv[1]
    else:
        base = os.path.join(os.getcwd(), ".allforai")

    if not os.path.isdir(base):
        print(f"ERROR: Base path does not exist: {base}", file=sys.stderr)
        sys.exit(1)

    return base


def parse_args():
    """Parse common CLI arguments: <BASE_PATH> [--mode auto] [--extra value].

    Returns (base_path, args_dict).
    """
    base = resolve_base_path()

    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith("--") and i + 1 < len(sys.argv):
            key = sys.argv[i][2:]
            args[key] = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    return base, args


# ── Split File Writer ─────────────────────────────────────────────────────────

def write_split_files(base, subdir, prefix, split_by, splits, extra_meta=None):
    """Write human-friendly split files using a unified wrapper schema.

    Args:
        base: .allforai base path
        subdir: output subdirectory under base (e.g. "screen-map")
        prefix: filename prefix (e.g. "screen-map" → "screen-map-R001.json")
        split_by: dimension name (e.g. "role", "priority")
        splits: dict {split_value: {"label": str, "description": str, "items": list}}
        extra_meta: optional dict of extra top-level fields to merge into each file
    """
    out_dir = os.path.join(base, subdir)
    ensure_dir(out_dir)
    ts = now_iso()
    written = []
    for split_value, info in splits.items():
        wrapper = {
            "split_by": split_by,
            "split_value": split_value,
            "split_label": info["label"],
            "description": info["description"],
            "generated_at": ts,
            "count": len(info["items"]),
            "items": info["items"],
        }
        if extra_meta:
            wrapper.update(extra_meta)
        fname = f"{prefix}-{split_value}.json"
        path = write_json(os.path.join(out_dir, fname), wrapper)
        written.append(path)
    return written


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("_common.py loaded successfully")
    print(f"  SCREEN_TASKS_FIELD = {SCREEN_TASKS_FIELD!r}")
    print(f"  FLOW_NODES_FIELD = {FLOW_NODES_FIELD!r}")
    print(f"  now_iso() = {now_iso()}")
    print("All imports OK")
