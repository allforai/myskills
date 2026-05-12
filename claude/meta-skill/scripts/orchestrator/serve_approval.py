#!/usr/bin/env python3
"""HTTP server for the review dashboard with approval action API.

Serves static files from the game-design directory AND handles
POST /api/action requests to write approval actions directly to
approval-records.json — no Playwright required.

Usage:
    python3 serve_approval.py \\
        --approval .allforai/game-design/approval-records.json \\
        --directory .allforai/game-design \\
        --port 43871
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


class ApprovalHandler(http.server.SimpleHTTPRequestHandler):
    approval_path: Path

    # ── POST /api/action ────────────────────────────────────────────────────
    def do_POST(self) -> None:
        if self.path == "/api/action":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                action = json.loads(body)
                self._apply_action(action)
                self._json(200, {"ok": True})
            except Exception as exc:
                self._json(400, {"ok": False, "error": str(exc)})
        else:
            self.send_error(404)

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    # ── helpers ─────────────────────────────────────────────────────────────
    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _apply_action(self, action: dict) -> None:
        data = json.loads(self.approval_path.read_text(encoding="utf-8"))
        node_id = action.get("node_id")
        if not node_id:
            raise ValueError("missing node_id")

        records = data.get("records", [])
        record = next(
            (r for r in records if r.get("node_id") == node_id),
            None,
        )
        if record is None:
            raise ValueError(f"record not found: {node_id}")

        now = datetime.now(timezone.utc).isoformat()
        if action.get("reviewer_notes") is not None:
            record["reviewer_notes"] = action["reviewer_notes"]
        if action.get("revision_notes") is not None:
            record["revision_notes"] = action["revision_notes"]

        kind = action.get("action")
        if kind == "approve":
            record["gate_status"] = "approved"
            record["approved_at"] = now
            approved_by = action.get("approved_by") or "discipline_owner"
            existing = record.get("approved_by") or []
            if approved_by not in existing:
                existing.append(approved_by)
            record["approved_by"] = existing
            record["revision_notes"] = ""
        elif kind == "request_revision":
            if not (action.get("revision_notes") or "").strip():
                raise ValueError("request_revision requires revision_notes")
            record["gate_status"] = "revision-requested"
            record["approved_at"] = None
            record["approved_by"] = []
        elif kind == "save_notes":
            pass  # notes already written above
        else:
            raise ValueError(f"unknown action: {kind}")

        self.approval_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def log_message(self, format: str, *args: object) -> None:
        pass  # quiet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approval", required=True, help="Path to approval-records.json")
    parser.add_argument("--directory", required=True, help="Static files directory to serve")
    parser.add_argument("--port", type=int, default=43871)
    args = parser.parse_args()

    approval_path = Path(args.approval).resolve()
    directory = Path(args.directory).resolve()

    if not approval_path.exists():
        print(f"ERROR: approval file not found: {approval_path}", file=sys.stderr)
        return 1

    class Handler(ApprovalHandler):
        pass

    Handler.approval_path = approval_path

    os.chdir(directory)

    with http.server.HTTPServer(("", args.port), Handler) as httpd:
        url = f"http://127.0.0.1:{args.port}/review-dashboard.html"
        print(f"Approval dashboard: {url}", flush=True)
        print("Open in Chrome to review. Press Ctrl-C to stop.", flush=True)
        httpd.serve_forever()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
