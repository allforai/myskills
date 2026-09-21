"""The approval server answers only the dashboard it serves."""
import http.client
import http.server
import importlib.util
import json
from pathlib import Path
import threading

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/orchestrator/serve_approval.py"
SPEC = importlib.util.spec_from_file_location("tested_serve_approval", SCRIPT)
serve_approval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(serve_approval)


@pytest.fixture
def server(tmp_path):
    records = tmp_path / "game-design/approval-records.json"
    records.parent.mkdir()
    records.write_text(json.dumps({"records": [{"node_id": "n1", "gate_status": "in-review"}]}))

    class Handler(serve_approval.ApprovalHandler):
        approval_paths = [records]

    httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd.server_address[1], records
    httpd.shutdown()
    httpd.server_close()


def post(port, action, **headers):
    conn = http.client.HTTPConnection("127.0.0.1", port)
    conn.request("POST", "/api/action", json.dumps(action),
                 {"Content-Type": "application/json", **headers})
    response = conn.getresponse()
    return response.status, json.loads(response.read())


def status(records):
    return json.loads(records.read_text())["records"][0]["gate_status"]


def test_dashboard_origin_may_approve(server):
    port, records = server
    code, _ = post(port, {"action": "approve", "node_id": "n1",
                          "approval_record_path": "game-design/approval-records.json"},
                   Origin=f"http://127.0.0.1:{port}")
    assert code == 200 and status(records) == "approved"


@pytest.mark.parametrize("headers", [
    {"Origin": "https://evil.example"},
    {"Host": "evil.example"},
    {"Content-Type": "text/plain"},
])
def test_foreign_requests_cannot_approve(server, headers):
    port, records = server
    code, body = post(port, {"action": "approve", "node_id": "n1"}, **headers)
    assert code == 403 and body["ok"] is False
    assert status(records) == "in-review"


def test_unserved_record_path_is_refused_not_widened(server):
    port, records = server
    code, _ = post(port, {"action": "approve", "node_id": "n1",
                          "approval_record_path": "app-design/approval-records.json"})
    assert code == 400 and status(records) == "in-review"


def test_binds_loopback_only():
    source = SCRIPT.read_text()
    assert 'HTTPServer(("127.0.0.1"' in source and "Access-Control-Allow-Origin" not in source
