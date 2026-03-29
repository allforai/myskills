#!/usr/bin/env python3
"""Mechanical loop detection for the orchestrator.

Tracks iteration history as (node_id, exit_results_hash) entries in a sliding window.
Detects when the same state repeats beyond thresholds.

Usage:
  python loop_detection.py record <history-file> <node-id> <exit-results-json>
  python loop_detection.py check <history-file> <node-id> <exit-results-json>
"""

import hashlib
import json
import os
import sys


DEFAULT_WINDOW_SIZE = 10
DEFAULT_WARN_THRESHOLD = 3
DEFAULT_STOP_THRESHOLD = 5


def _make_hash(node_id: str, exit_results: list) -> str:
    """Deterministic hash of node_id + exit_requires evaluation results."""
    blob = json.dumps({"node": node_id, "results": exit_results}, sort_keys=True)
    return hashlib.md5(blob.encode()).hexdigest()[:12]


def _load_history(path: str) -> list:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_history(path: str, history: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f)


def record_iteration(
    history_path: str,
    node_id: str,
    exit_results: list,
    warn_threshold: int = DEFAULT_WARN_THRESHOLD,
    stop_threshold: int = DEFAULT_STOP_THRESHOLD,
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> dict:
    """Record an iteration and check for loops. Returns { status, hash, count }."""
    history = _load_history(history_path)
    h = _make_hash(node_id, exit_results)
    history.append(h)

    # Sliding window
    if len(history) > window_size:
        history = history[-window_size:]

    _save_history(history_path, history)

    count = history.count(h)
    if count >= stop_threshold:
        status = "stop"
    elif count >= warn_threshold:
        status = "warn"
    else:
        status = "ok"

    return {"status": status, "hash": h, "count": count}


def check_loop(
    history_path: str,
    node_id: str,
    exit_results: list,
    warn_threshold: int = DEFAULT_WARN_THRESHOLD,
    stop_threshold: int = DEFAULT_STOP_THRESHOLD,
) -> str:
    """Check if adding this iteration would trigger a loop, without recording."""
    history = _load_history(history_path)
    h = _make_hash(node_id, exit_results)
    count = history.count(h) + 1  # +1 for the hypothetical addition

    if count >= stop_threshold:
        return "stop"
    elif count >= warn_threshold:
        return "warn"
    return "ok"


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(f"Usage: {sys.argv[0]} record|check <history-file> <node-id> <exit-results-json>", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    history_path = sys.argv[2]
    node_id = sys.argv[3]
    exit_results = json.loads(sys.argv[4])

    if action == "record":
        result = record_iteration(history_path, node_id, exit_results)
        print(json.dumps(result))
        sys.exit(0 if result["status"] != "stop" else 1)
    elif action == "check":
        status = check_loop(history_path, node_id, exit_results)
        print(json.dumps({"status": status}))
        sys.exit(0 if status != "stop" else 1)
    else:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
