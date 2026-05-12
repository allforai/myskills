#!/usr/bin/env python3
"""HTTP server for the review dashboard with approval action API.

Serves static files from the review dashboard directory AND handles
POST /api/action requests to write approval actions directly to
approval-records.json — no Playwright required.

Usage:
    python3 serve_approval.py \\
        --approval .allforai/game-design/approval-records.json \\
        --approval .allforai/app-design/approval-records.json \\
        --directory .allforai \\
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
    approval_paths: list[Path]

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
        node_id = action.get("node_id")
        if not node_id:
            raise ValueError("missing node_id")

        requested_path = action.get("approval_record_path")
        candidates = self.approval_paths
        if requested_path:
            requested = Path(requested_path)
            candidates = [
                path
                for path in self.approval_paths
                if path == requested.resolve() or path.as_posix().endswith(requested.as_posix())
            ] or self.approval_paths

        matched_path = None
        data = None
        record = None
        for path in candidates:
            if not path.exists():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            records = payload.get("records", [])
            found = next(
                (r for r in records if r.get("node_id") == node_id),
                None,
            )
            if found is not None:
                matched_path = path
                data = payload
                record = found
                break

        if matched_path is None or data is None or record is None:
            raise ValueError(f"record not found: {node_id}")

        records = data.get("records", [])

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

        matched_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def log_message(self, format: str, *args: object) -> None:
        pass  # quiet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--approval",
        action="append",
        required=True,
        help="Path to approval-records.json. May be passed more than once.",
    )
    parser.add_argument("--directory", required=True, help="Static files directory to serve")
    parser.add_argument("--port", type=int, default=43871)
    args = parser.parse_args()

    approval_paths = [Path(path).resolve() for path in args.approval]
    directory = Path(args.directory).resolve()

    existing_approvals = [path for path in approval_paths if path.exists()]
    if not existing_approvals:
        print(
            "ERROR: no approval files found: "
            + ", ".join(path.as_posix() for path in approval_paths),
            file=sys.stderr,
        )
        return 1

    class Handler(ApprovalHandler):
        pass

    Handler.approval_paths = existing_approvals

    os.chdir(directory)

    if (directory / "game-design/review-dashboard.html").exists():
        dashboard_path = "/game-design/review-dashboard.html"
    else:
        dashboard_path = "/review-dashboard.html"

    with http.server.HTTPServer(("", args.port), Handler) as httpd:
        url = f"http://127.0.0.1:{args.port}{dashboard_path}"
        print(f"审批看板: {url}", flush=True)
        print("请在 Chrome 中打开进行审批。按 Ctrl-C 停止。", flush=True)
        httpd.serve_forever()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
