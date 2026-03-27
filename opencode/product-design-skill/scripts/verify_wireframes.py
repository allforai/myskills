#!/usr/bin/env python3
"""Playwright-driven wireframe verification.

Architecture:
  This script handles the MECHANICAL parts (start hub, collect screen list,
  output report structure). Claude Code handles the INTELLIGENT parts
  (navigate each screen via MCP Playwright, judge correctness via LLM).

Usage:
  # Phase 1: Collect screen metadata + start Review Hub
  python3 verify_wireframes.py <BASE> --prepare

  # Phase 2: After Claude Code verifies via Playwright, feed back results
  python3 verify_wireframes.py <BASE> --report --input verification-input.json

  # One-shot: just output screen list for Claude Code to verify
  python3 verify_wireframes.py <BASE>

Output:
  .allforai/wireframe-verify/screens-to-verify.json  — screen list + metadata
  .allforai/wireframe-verify/verification-report.json — final report (after --report)
"""

import json
import os
import sys
import subprocess
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(__file__))
from _common import (
    resolve_base_path, load_experience_map, build_screen_by_id_from_lines,
    ensure_dir, write_json, now_iso, append_pipeline_decision,
    kill_other_review_servers
)


# ── Interaction Type → Expected Layout Components ─────────────────────────────

# Maps interaction_type prefix to expected structural elements in the wireframe.
# These are the layout slots that Review Hub renders for each type.
EXPECTED_LAYOUT = {
    "CT1": ["filter-bar", "card-grid"],
    "CT2": ["cover-image", "title", "meta", "body-content", "action-bar"],
    "CT3": ["avatar-header", "profile-fields", "action-bar"],
    "CT4": ["progress", "card-main", "action-buttons"],
    "CT5": ["player", "controls", "playlist"],
    "CT6": ["map-container", "markers", "info-panel"],
    "CT7": ["feed-item", "infinite-scroll"],
    "CT8": ["slide-container", "indicators", "nav-arrows"],
    "MG1": ["header", "detail-fields", "action-bar"],
    "MG2-C": ["header", "form-body", "field-group", "action-bar"],
    "MG2-E": ["header", "form-body", "field-group", "action-bar"],
    "MG2-L": ["header", "search-bar", "table", "pagination", "action-bar"],
    "MG3": ["header", "state-tabs", "table", "action-bar"],
    "MG4": ["header", "pending-badge", "approval-cards", "action-bar"],
    "MG5": ["tree-view", "drag-handle", "action-bar"],
    "MG6": ["header", "permission-matrix", "action-bar"],
    "MG7": ["header", "kpi-cards", "charts", "date-filter"],
    "MG8": ["header", "config-sections", "save-bar"],
    "EC1": ["product-image", "title-price", "specs", "features", "action-bar"],
    "EC2": ["item-list", "total", "payment-options", "action-bar"],
    "EC3": ["order-header", "timeline", "status-badge"],
    "WK1": ["toolbar", "canvas", "layer-panel"],
    "WK2": ["header", "kanban-columns", "card"],
    "WK3": ["editor-toolbar", "editor-area", "preview", "status-bar"],
    "WK4": ["calendar-grid", "event-card", "nav-arrows"],
    "WK5": ["file-tree", "breadcrumb", "action-bar"],
    "WK6": ["header", "notification-list", "filter-tabs"],
    "WK7": ["search-bar", "result-list", "filter-sidebar"],
    "RT1": ["message-list", "input-bar", "avatar"],
    "RT2": ["video-grid", "controls", "participant-list"],
    "RT3": ["comment-thread", "input-bar", "sort-toggle"],
    "RT4": ["live-feed", "reaction-bar", "viewer-count"],
    "SB1": ["form-sections", "progress", "submit-bar"],
    "SY1": ["illustration", "step-content", "dots", "action-bar"],
    "SY2": ["progress-steps", "form-body", "action-bar"],
}


def collect_screens(base):
    """Extract all unique screens from experience-map with metadata."""
    lines, index, loaded = load_experience_map(base)
    if not loaded:
        print("ERROR: experience-map.json not found", file=sys.stderr)
        sys.exit(1)

    screens = []
    seen = set()
    for ol in lines:
        for node in ol.get("nodes", []):
            for s in node.get("screens", []):
                sid = s.get("id", "")
                if sid and sid not in seen:
                    seen.add(sid)
                    itype = s.get("interaction_type", "")
                    expected = EXPECTED_LAYOUT.get(itype, [])
                    screens.append({
                        "screen_id": sid,
                        "name": s.get("name", ""),
                        "interaction_type": itype,
                        "platform": s.get("platform", "mobile"),
                        "expected_layout": expected,
                        "has_data_fields": bool(s.get("data_fields")),
                        "has_actions": bool(s.get("actions")),
                        "has_states": bool(s.get("states")),
                        "field_count": len(s.get("data_fields", [])),
                        "action_count": len(s.get("actions", [])),
                        "state_count": len(s.get("states", [])),
                        "flow_prev": s.get("flow_prev", ""),
                        "flow_next": s.get("flow_next", ""),
                    })
    screens.sort(key=lambda x: x["screen_id"])
    return screens


def ensure_hub_running(base, port=18900):
    """Start Review Hub if not already running."""
    try:
        urllib.request.urlopen(f"http://localhost:{port}/", timeout=2)
        return True  # already running
    except (urllib.error.URLError, OSError):
        pass

    # Start hub
    script_dir = os.path.dirname(__file__)
    hub_script = os.path.join(script_dir, "review_hub_server.py")
    if not os.path.exists(hub_script):
        print("ERROR: review_hub_server.py not found", file=sys.stderr)
        return False

    kill_other_review_servers(port)
    subprocess.Popen(
        [sys.executable, hub_script, base, "--port", str(port), "--no-open", "true"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Wait for startup
    for _ in range(10):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"http://localhost:{port}/", timeout=2)
            return True
        except (urllib.error.URLError, OSError):
            continue

    print("ERROR: Review Hub failed to start", file=sys.stderr)
    return False


def generate_report(base, input_file):
    """Read Claude Code's verification results and generate final report."""
    with open(input_file) as f:
        results = json.load(f)

    errors = [r for r in results if r.get("severity") == "ERROR"]
    warnings = [r for r in results if r.get("severity") == "WARNING"]
    passed = [r for r in results if r.get("severity") == "PASS"]

    report = {
        "generated_at": now_iso(),
        "total_screens": len(results),
        "passed": len(passed),
        "warnings": len(warnings),
        "errors": len(errors),
        "overall": "PASS" if not errors else "FAIL",
        "findings": results,
    }

    out_dir = os.path.join(base, "wireframe-verify")
    ensure_dir(out_dir)
    write_json(os.path.join(out_dir, "verification-report.json"), report)

    # Pipeline decision
    append_pipeline_decision(base, {
        "phase": "Phase 4.7 — playwright-verify",
        "decision": "auto_verified" if not errors else "errors_found",
        "detail": f"screens={len(results)}, pass={len(passed)}, warn={len(warnings)}, error={len(errors)}",
    })

    print(f"\nVerification Report: {len(passed)} PASS, {len(warnings)} WARNING, {len(errors)} ERROR")
    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  {e['screen_id']} ({e.get('name','')}): {e.get('issue','')}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  {w['screen_id']} ({w.get('name','')}): {w.get('issue','')}")

    return report


def main():
    base = resolve_base_path()
    args = sys.argv[1:]

    # Remove base from args if present
    remaining = [a for a in args if not os.path.isdir(a)]

    if "--report" in remaining:
        # Phase 2: Generate report from Claude Code's input
        idx = remaining.index("--input") if "--input" in remaining else -1
        if idx >= 0 and idx + 1 < len(remaining):
            input_file = remaining[idx + 1]
        else:
            input_file = os.path.join(base, "wireframe-verify", "verification-input.json")
        report = generate_report(base, input_file)
        sys.exit(0 if report["overall"] == "PASS" else 1)

    # Default / --prepare: Collect screens + ensure hub running
    screens = collect_screens(base)
    if not screens:
        print("ERROR: No screens found in experience-map", file=sys.stderr)
        sys.exit(1)

    # Ensure Review Hub is running
    port = 18900
    hub_ok = ensure_hub_running(base, port)

    out_dir = os.path.join(base, "wireframe-verify")
    ensure_dir(out_dir)

    output = {
        "generated_at": now_iso(),
        "hub_url": f"http://localhost:{port}/wireframe" if hub_ok else None,
        "hub_status": "running" if hub_ok else "failed",
        "screen_count": len(screens),
        "screens": screens,
        "instructions": (
            "For each screen: navigate to hub_url, click screen in sidebar tree, "
            "capture accessibility snapshot. Compare snapshot against expected_layout "
            "and screen metadata. Output verification-input.json with findings."
        ),
    }

    out_file = os.path.join(out_dir, "screens-to-verify.json")
    write_json(out_file, output)

    print(f"Screens to verify: {len(screens)}")
    print(f"Review Hub: {'running at ' + output['hub_url'] if hub_ok else 'FAILED'}")
    print(f"Output: {out_file}")
    print(f"\nClaude Code should now:")
    print(f"  1. Navigate to {output['hub_url']}")
    print(f"  2. Click each screen → snapshot → verify")
    print(f"  3. Write findings to wireframe-verify/verification-input.json")
    print(f"  4. Run: python3 {__file__} {base} --report")


if __name__ == "__main__":
    main()
