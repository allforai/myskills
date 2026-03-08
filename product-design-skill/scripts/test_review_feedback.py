#!/usr/bin/env python3
"""Automated tests for all 4 review server feedback submission flows.

Tests:
  1. Concept review (mindmap_review_server.py --source concept, port 18900)
  2. Product-map review (mindmap_review_server.py --source product-map, port 18901)
  3. Wireframe review (wireframe_review_server.py, port 18902)
  4. UI review (ui_review_server.py, port 18903)

Each test:
  - Creates temp .allforai dir with minimal test data
  - Starts server in a subprocess with --no-open true
  - POSTs feedback via API, then POSTs /api/submit
  - Reads review-feedback.json and verifies structure
  - Captures stdout to verify feedback summary output
  - Cleans up temp dir

Usage:
    cd product-design-skill/scripts && python3 test_review_feedback.py
"""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.request
import urllib.error

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PASS = 0
FAIL = 0
ERRORS = []


def log(msg):
    print(f"  {msg}")


def wait_for_port(port, timeout=10):
    """Wait until a port is accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(0.5)
            result = sock.connect_ex(("localhost", port))
            if result == 0:
                return True
        except Exception:
            pass
        finally:
            sock.close()
        time.sleep(0.2)
    return False


def http_post(port, path, data=None):
    """POST JSON to localhost:port/path, return (status, response_body)."""
    url = f"http://localhost:{port}{path}"
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"}
        )
    else:
        req = urllib.request.Request(url, data=b"", method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def http_get(port, path):
    """GET from localhost:port/path, return (status, response_body)."""
    url = f"http://localhost:{port}{path}"
    try:
        resp = urllib.request.urlopen(url, timeout=5)
        return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def assert_true(condition, msg):
    global PASS, FAIL
    if condition:
        PASS += 1
        log(f"  PASS: {msg}")
    else:
        FAIL += 1
        ERRORS.append(msg)
        log(f"  FAIL: {msg}")


def kill_proc(proc):
    """Kill subprocess and wait."""
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=2)
        except Exception:
            pass


# ── Test data factories ──────────────────────────────────────────────────────

def create_concept_data(base):
    """Create minimal product-concept.json."""
    d = os.path.join(base, "product-concept")
    os.makedirs(d, exist_ok=True)
    data = {
        "mission": "Test Product",
        "problem_domain": "Testing review servers",
        "roles": [
            {"id": "R001", "name": "Tester", "description": "A test role",
             "role_type": "consumer", "impl_group": "end-user"}
        ],
        "business_model": {
            "revenue_model": "subscription",
            "key_metrics": ["DAU", "retention"]
        },
        "mechanisms": [
            {"id": "mec-1", "name": "Auth", "description": "Authentication mechanism"}
        ]
    }
    with open(os.path.join(d, "product-concept.json"), "w") as f:
        json.dump(data, f)


def create_product_map_data(base):
    """Create minimal product-map data files."""
    d = os.path.join(base, "product-map")
    os.makedirs(d, exist_ok=True)

    roles = {
        "roles": [
            {"id": "R001", "name": "Tester", "description": "Test role",
             "audience_type": "consumer"}
        ]
    }
    with open(os.path.join(d, "role-profiles.json"), "w") as f:
        json.dump(roles, f)

    inv = {
        "tasks": [
            {"id": "T001", "name": "Login", "owner_role": "R001",
             "category": "core", "frequency": "daily", "risk_level": "low",
             "value": "User authentication"},
            {"id": "T002", "name": "View Dashboard", "owner_role": "R001",
             "category": "core", "frequency": "daily", "risk_level": "low",
             "value": "Main overview"}
        ]
    }
    with open(os.path.join(d, "task-inventory.json"), "w") as f:
        json.dump(inv, f)

    flows = {
        "flows": [
            {"id": "F001", "name": "Login Flow", "description": "Basic login",
             "nodes": [
                 {"seq": 1, "task_ref": "T001", "role": "R001"},
                 {"seq": 2, "task_ref": "T002", "role": "R001"}
             ]}
        ]
    }
    with open(os.path.join(d, "business-flows.json"), "w") as f:
        json.dump(flows, f)


def create_wireframe_data(base):
    """Create minimal experience-map + product-map data for wireframe server."""
    # Wireframe server also needs product-map data (task-inventory, role-profiles)
    create_product_map_data(base)

    d = os.path.join(base, "experience-map")
    os.makedirs(d, exist_ok=True)

    em = {
        "operation_lines": [
            {
                "id": "OL001",
                "name": "Main Journey",
                "nodes": [
                    {
                        "id": "N001",
                        "emotion_state": "curious",
                        "emotion_intensity": 6,
                        "ux_intent": "Guide user to login",
                        "screens": [
                            {
                                "id": "S001",
                                "name": "Login Screen",
                                "module": "auth",
                                "notes": "Standard login form",
                                "tasks": ["T001"],
                                "actions": [
                                    {"label": "Submit Login", "crud": "C", "frequency": "高"}
                                ],
                                "non_negotiable": ["password masking"]
                            }
                        ]
                    },
                    {
                        "id": "N002",
                        "emotion_state": "satisfied",
                        "emotion_intensity": 8,
                        "ux_intent": "Show overview",
                        "screens": [
                            {
                                "id": "S002",
                                "name": "Dashboard",
                                "module": "main",
                                "notes": "Main dashboard view",
                                "tasks": ["T002"],
                                "actions": [
                                    {"label": "View Stats", "crud": "R", "frequency": "高"},
                                    {"label": "Export", "crud": "R", "frequency": "低"}
                                ],
                                "non_negotiable": []
                            }
                        ]
                    }
                ]
            }
        ]
    }
    with open(os.path.join(d, "experience-map.json"), "w") as f:
        json.dump(em, f)


def create_ui_data(base):
    """Create minimal ui-design data for UI review server."""
    # UI server also loads experience-map
    create_wireframe_data(base)

    d = os.path.join(base, "ui-design")
    os.makedirs(d, exist_ok=True)

    spec = {
        "product": "Test App",
        "design_style": "Modern Minimal",
        "design_tokens": {
            "colors": {"primary": "#3b82f6", "background": "#ffffff"},
            "border_radius": "8px"
        },
        "screens": [
            {
                "id": "S001",
                "name": "Login Screen",
                "role": "R001",
                "interaction_type": "form",
                "audience_type": "consumer",
                "layout": "centered-card",
                "sections": ["Header", "Login Form", "Footer"],
                "states": {"empty": "No input", "loading": "Submitting"},
                "emotion_context": {"state": "curious", "operation_line": "OL001"}
            },
            {
                "id": "S002",
                "name": "Dashboard",
                "role": "R001",
                "interaction_type": "dashboard",
                "audience_type": "consumer",
                "layout": "sidebar-content",
                "sections": ["Nav", "Stats Cards", "Chart"],
                "states": {"empty": "No data", "loading": "Fetching"},
                "emotion_context": {"state": "satisfied", "operation_line": "OL001"}
            }
        ]
    }
    with open(os.path.join(d, "ui-design-spec.json"), "w") as f:
        json.dump(spec, f)

    # Create preview dir with minimal HTML
    preview_dir = os.path.join(d, "preview")
    os.makedirs(preview_dir, exist_ok=True)
    for sid in ("S001", "S002"):
        with open(os.path.join(preview_dir, f"{sid}.html"), "w") as f:
            f.write(f"<html><body><h1>{sid} Preview</h1></body></html>")


# ── Test runners ─────────────────────────────────────────────────────────────

def run_server_test(name, port, server_script, server_args, create_data_fn,
                    feedback_key, feedback_data, feedback_subdir,
                    expected_structure_key):
    """Generic test runner for a review server.

    Args:
        name: test name for display
        port: port number
        server_script: e.g. "mindmap_review_server.py"
        server_args: list of extra args after base_path
        create_data_fn: function(base) to create test data
        feedback_key: "nodes" or "screens" — top-level key in feedback POST body
        feedback_data: the data to POST to /api/feedback
        feedback_subdir: subdirectory under base where review-feedback.json is written
        expected_structure_key: "nodes" or "screens" — expected key in saved feedback
    """
    global PASS, FAIL

    print(f"\n{'─'*60}")
    print(f"TEST: {name} (port {port})")
    print(f"{'─'*60}")

    tmpdir = tempfile.mkdtemp(prefix="review_test_")
    base = os.path.join(tmpdir, ".allforai")
    os.makedirs(base)
    proc = None

    try:
        # 1. Create test data
        create_data_fn(base)
        log("Test data created")

        # 2. Start server
        cmd = [
            sys.executable, os.path.join(SCRIPTS_DIR, server_script),
            base
        ] + server_args + ["--no-open", "true"]

        env = os.environ.copy()
        env["PYTHONPATH"] = SCRIPTS_DIR + os.pathsep + env.get("PYTHONPATH", "")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=SCRIPTS_DIR
        )

        # Wait for server to start
        if not wait_for_port(port, timeout=10):
            stderr_out = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
            log(f"Server failed to start on port {port}")
            if stderr_out:
                log(f"STDERR: {stderr_out[:500]}")
            assert_true(False, f"{name}: server started on port {port}")
            return
        assert_true(True, f"{name}: server started on port {port}")

        # 3. Verify GET / returns 200
        status, _ = http_get(port, "/")
        assert_true(status == 200, f"{name}: GET / returns 200 (got {status})")

        # 4. POST feedback data
        status, resp = http_post(port, "/api/feedback", feedback_data)
        assert_true(status == 200 and resp.get("ok") is True,
                    f"{name}: POST /api/feedback returns ok (status={status})")

        # 5. Verify feedback was saved (GET /api/feedback)
        status, body = http_get(port, "/api/feedback")
        if status == 200:
            fb = json.loads(body)
            has_key = expected_structure_key in fb
            assert_true(has_key,
                        f"{name}: GET /api/feedback has '{expected_structure_key}' key")
            if has_key:
                entries = fb[expected_structure_key]
                assert_true(len(entries) > 0,
                            f"{name}: feedback has {len(entries)} entries (expected > 0)")
        else:
            assert_true(False, f"{name}: GET /api/feedback returns 200 (got {status})")

        # 6. POST /api/submit — server will auto-exit after 1s
        status, resp = http_post(port, "/api/submit")
        assert_true(status == 200 and resp.get("ok") is True,
                    f"{name}: POST /api/submit returns ok (status={status})")

        # 7. Wait for server to auto-exit
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            log("Server did not auto-exit, killing...")
            kill_proc(proc)

        # 8. Read stdout and check for feedback summary
        stdout_out = proc.stdout.read().decode("utf-8", errors="replace") if proc.stdout else ""
        assert_true("Feedback submitted" in stdout_out or "feedback submitted" in stdout_out,
                    f"{name}: stdout contains 'Feedback submitted'")
        assert_true("Approved:" in stdout_out,
                    f"{name}: stdout contains 'Approved:' count")
        assert_true("FEEDBACK_JSON_PATH=" in stdout_out,
                    f"{name}: stdout contains FEEDBACK_JSON_PATH")

        # 9. Read the persisted review-feedback.json from disk
        fb_path = os.path.join(base, feedback_subdir, "review-feedback.json")
        assert_true(os.path.exists(fb_path),
                    f"{name}: review-feedback.json exists at {feedback_subdir}/")

        if os.path.exists(fb_path):
            with open(fb_path) as f:
                saved = json.load(f)

            assert_true(saved.get("submitted_at") is not None,
                        f"{name}: submitted_at is set (got {saved.get('submitted_at')})")
            assert_true(expected_structure_key in saved,
                        f"{name}: saved file has '{expected_structure_key}' key")
            assert_true("round" in saved,
                        f"{name}: saved file has 'round' key")

            # Verify the actual feedback content was persisted
            saved_entries = saved.get(expected_structure_key, {})
            assert_true(len(saved_entries) > 0,
                        f"{name}: saved feedback has {len(saved_entries)} entries")

        proc = None  # already exited

    except Exception as e:
        FAIL += 1
        ERRORS.append(f"{name}: EXCEPTION: {e}")
        log(f"  EXCEPTION: {e}")
        traceback.print_exc()

    finally:
        if proc is not None:
            kill_proc(proc)
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── Individual test configurations ───────────────────────────────────────────

def test_concept_review():
    """Test mindmap_review_server.py --source concept (port 18900)."""
    feedback_data = {
        "root": {"status": "approved", "comments": []},
        "problem": {"status": "approved", "comments": []},
        "R001": {
            "status": "revision",
            "comments": [
                {"id": 1, "text": "Needs more detail", "category": "concept"}
            ]
        }
    }
    run_server_test(
        name="Concept Review (mindmap)",
        port=18900,
        server_script="mindmap_review_server.py",
        server_args=["--source", "concept", "--port", "18900"],
        create_data_fn=create_concept_data,
        feedback_key="nodes",
        feedback_data=feedback_data,
        feedback_subdir="concept-review",
        expected_structure_key="nodes",
    )


def test_product_map_review():
    """Test mindmap_review_server.py --source product-map (port 18901)."""
    feedback_data = {
        "root": {"status": "approved", "comments": []},
        "R001": {"status": "approved", "comments": []},
        "T001": {
            "status": "revision",
            "comments": [
                {"id": 1, "text": "Login should support SSO", "category": "product-map"}
            ]
        }
    }
    run_server_test(
        name="Product Map Review (mindmap)",
        port=18901,
        server_script="mindmap_review_server.py",
        server_args=["--source", "product-map", "--port", "18901"],
        create_data_fn=lambda base: (create_concept_data(base), create_product_map_data(base)),
        feedback_key="nodes",
        feedback_data=feedback_data,
        feedback_subdir="product-map-review",
        expected_structure_key="nodes",
    )


def test_wireframe_review():
    """Test wireframe_review_server.py (port 18902)."""
    # Wireframe uses per-screen feedback: POST body = {screen_id, status, pins}
    # We need to post for each screen individually
    # But the feedback endpoint takes one screen at a time
    feedback_data = {
        "screen_id": "S001",
        "status": "revision",
        "pins": [
            {"id": 1, "x": 50.0, "y": 30.0, "comment": "Button too small",
             "category": "experience-map"}
        ]
    }
    run_server_test(
        name="Wireframe Review",
        port=18902,
        server_script="wireframe_review_server.py",
        server_args=["--port", "18902"],
        create_data_fn=create_wireframe_data,
        feedback_key="screens",
        feedback_data=feedback_data,
        feedback_subdir="wireframe-review",
        expected_structure_key="screens",
    )


def test_ui_review():
    """Test ui_review_server.py (port 18903)."""
    feedback_data = {
        "screen_id": "S001",
        "status": "approved",
        "pins": []
    }
    run_server_test(
        name="UI Review",
        port=18903,
        server_script="ui_review_server.py",
        server_args=["--port", "18903"],
        create_data_fn=create_ui_data,
        feedback_key="screens",
        feedback_data=feedback_data,
        feedback_subdir="ui-design",
        expected_structure_key="screens",
    )


# ── Multi-feedback test (post multiple items then submit) ────────────────────

def test_wireframe_multi_feedback():
    """Test wireframe server with multiple screen feedbacks before submit."""
    print(f"\n{'─'*60}")
    print(f"TEST: Wireframe Multi-Screen Feedback (port 18902)")
    print(f"{'─'*60}")

    tmpdir = tempfile.mkdtemp(prefix="review_test_")
    base = os.path.join(tmpdir, ".allforai")
    os.makedirs(base)
    proc = None

    try:
        create_wireframe_data(base)
        log("Test data created")

        cmd = [
            sys.executable, os.path.join(SCRIPTS_DIR, "wireframe_review_server.py"),
            base, "--port", "18902", "--no-open", "true"
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = SCRIPTS_DIR + os.pathsep + env.get("PYTHONPATH", "")

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, cwd=SCRIPTS_DIR
        )

        if not wait_for_port(18902, timeout=10):
            assert_true(False, "Multi-feedback: server started")
            return

        # Post feedback for S001 (revision)
        status1, _ = http_post(18902, "/api/feedback", {
            "screen_id": "S001",
            "status": "revision",
            "pins": [{"id": 1, "x": 10, "y": 20, "comment": "Fix alignment", "category": "experience-map"}]
        })
        assert_true(status1 == 200, "Multi-feedback: POST S001 feedback ok")

        # Post feedback for S002 (approved)
        status2, _ = http_post(18902, "/api/feedback", {
            "screen_id": "S002",
            "status": "approved",
            "pins": []
        })
        assert_true(status2 == 200, "Multi-feedback: POST S002 feedback ok")

        # Verify both are persisted
        status3, body = http_get(18902, "/api/feedback")
        if status3 == 200:
            fb = json.loads(body)
            screens = fb.get("screens", {})
            assert_true("S001" in screens and "S002" in screens,
                        f"Multi-feedback: both S001 and S002 in feedback (got keys: {list(screens.keys())})")
            assert_true(screens.get("S001", {}).get("status") == "revision",
                        "Multi-feedback: S001 status is 'revision'")
            assert_true(screens.get("S002", {}).get("status") == "approved",
                        "Multi-feedback: S002 status is 'approved'")

        # Submit
        http_post(18902, "/api/submit")

        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            kill_proc(proc)

        stdout_out = proc.stdout.read().decode("utf-8", errors="replace")
        assert_true("Approved: 1" in stdout_out, "Multi-feedback: stdout shows Approved: 1")
        assert_true("Revision: 1" in stdout_out, "Multi-feedback: stdout shows Revision: 1")

        fb_path = os.path.join(base, "wireframe-review", "review-feedback.json")
        if os.path.exists(fb_path):
            with open(fb_path) as f:
                saved = json.load(f)
            assert_true(saved.get("submitted_at") is not None,
                        "Multi-feedback: submitted_at is set")
            assert_true(len(saved.get("screens", {})) == 2,
                        f"Multi-feedback: 2 screens saved (got {len(saved.get('screens', {}))})")

        proc = None

    except Exception as e:
        FAIL += 1
        ERRORS.append(f"Multi-feedback: EXCEPTION: {e}")
        traceback.print_exc()
    finally:
        if proc is not None:
            kill_proc(proc)
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    global PASS, FAIL

    print("=" * 60)
    print("Review Server Feedback Tests")
    print("=" * 60)

    # Check that no servers are already running on test ports
    for port in (18900, 18901, 18902, 18903):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(0.3)
            if sock.connect_ex(("localhost", port)) == 0:
                print(f"WARNING: Port {port} already in use, test may conflict")
        except Exception:
            pass
        finally:
            sock.close()

    # Run tests sequentially (ports must not conflict)
    test_concept_review()
    test_product_map_review()
    test_wireframe_review()
    test_ui_review()
    test_wireframe_multi_feedback()

    # Summary
    total = PASS + FAIL
    print(f"\n{'='*60}")
    print(f"RESULTS: {PASS}/{total} passed, {FAIL}/{total} failed")
    if ERRORS:
        print(f"\nFailed assertions:")
        for e in ERRORS:
            print(f"  - {e}")
    print(f"{'='*60}")

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
