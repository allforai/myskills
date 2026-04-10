#!/usr/bin/env python3
"""Non-stop Codex workflow driver template.

Bootstrap should materialize this file into `.allforai/codex/flow.py` inside the
target project. Shared workflow contracts remain under `.allforai/bootstrap/`,
while Codex-only runtime helpers live under `.allforai/codex/`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MAX_ITERATIONS = 200
DEFAULT_GOAL = "Complete the entire generated workflow end-to-end. Do not stop to ask what to do next. Keep executing nodes until the workflow is done, then stop for unified acceptance."


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".allforai/bootstrap/workflow.json").exists():
            return candidate
    raise FileNotFoundError("Could not find project root containing .allforai/bootstrap/workflow.json")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def artifact_exists(project_root: Path, rel_path: str) -> bool:
    return (project_root / rel_path).exists()


def first_pending_node(project_root: Path, workflow: dict) -> dict | None:
    for node in workflow.get("nodes", []):
        if not all(artifact_exists(project_root, path) for path in node.get("exit_artifacts", [])):
            return node
    return None


def append_transition_if_missing(
    workflow_path: Path,
    before_count: int,
    node_id: str,
    status: str,
    started_at: str,
    artifacts_created: list[str],
    error: str | None = None,
) -> None:
    workflow = load_json(workflow_path)
    transition_log = workflow.setdefault("transition_log", [])
    if len(transition_log) > before_count:
        return

    entry = {
        "node": node_id,
        "status": status,
        "started_at": started_at,
        "completed_at": now_iso(),
        "artifacts_created": artifacts_created,
    }
    if error:
        entry["error"] = error
    transition_log.append(entry)
    save_json(workflow_path, workflow)


def run_post_checks(project_root: Path) -> None:
    scripts = project_root / ".allforai/bootstrap/scripts"
    bootstrap_dir = project_root / ".allforai/bootstrap"
    subprocess.run([sys.executable, str(scripts / "validate_bootstrap.py"), str(bootstrap_dir)], cwd=project_root, check=False)
    product_summary = bootstrap_dir / "product-summary.json"
    if product_summary.exists():
        subprocess.run([sys.executable, str(scripts / "check_product_summary.py"), str(product_summary)], cwd=project_root, check=False)


def build_prompt(node_id: str, goal: str) -> str:
    return f"""Continue the generated workflow autonomously.

Selected node: {node_id}
User goal: {goal}

Requirements:
1. Read `.allforai/bootstrap/workflow.json`.
2. Read `.allforai/bootstrap/node-specs/{node_id}.md`.
3. Complete exactly this node end-to-end. Do not stop after planning.
4. Create or update any project files required to satisfy the node's exit artifacts.
5. Append a `transition_log` entry to `.allforai/bootstrap/workflow.json` with `completed` or `failed`.
6. If the node fails, write a one-line `error` field explaining the blocker.
7. Stop only after this node is completed or a failed transition has been written.

Do not ask for acceptance. Execute the work directly."""


def run_codex(project_root: Path, prompt: str) -> subprocess.CompletedProcess[str]:
    command = [
        "codex",
        "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        "-C",
        str(project_root),
        "--skip-git-repo-check",
        prompt,
    ]
    return subprocess.run(command, cwd=project_root, text=True, capture_output=True)


def parse_legacy_args(argv: list[str]) -> tuple[str, int]:
    goal = DEFAULT_GOAL
    max_iterations = DEFAULT_MAX_ITERATIONS
    if len(argv) >= 2 and argv[1].strip():
        goal = argv[1].strip()
    if len(argv) >= 3:
        try:
            max_iterations = int(argv[2])
        except ValueError:
            pass
    return goal, max_iterations


def main() -> int:
    goal, max_iterations = parse_legacy_args(sys.argv)
    project_root = find_project_root(Path.cwd())
    workflow_path = project_root / ".allforai/bootstrap/workflow.json"

    for iteration in range(1, max_iterations + 1):
        workflow = load_json(workflow_path)
        node = first_pending_node(project_root, workflow)
        if node is None:
            run_post_checks(project_root)
            print(json.dumps({"passed": True, "done": True, "iterations": iteration - 1}, indent=2, ensure_ascii=False))
            return 0

        node_id = node["id"]
        before_count = len(workflow.get("transition_log", []))
        started_at = now_iso()
        result = run_codex(project_root, build_prompt(node_id, goal))

        artifacts_created = [
            path for path in node.get("exit_artifacts", []) if artifact_exists(project_root, path)
        ]
        all_exist = len(artifacts_created) == len(node.get("exit_artifacts", []))

        if all_exist:
            append_transition_if_missing(
                workflow_path,
                before_count,
                node_id,
                "completed",
                started_at,
                artifacts_created,
            )
        else:
            lines = (result.stderr or result.stdout or "").strip().splitlines()
            error_line = lines[-1][:300] if lines else "Codex stopped before satisfying exit artifacts."
            append_transition_if_missing(
                workflow_path,
                before_count,
                node_id,
                "failed",
                started_at,
                artifacts_created,
                error_line,
            )

        print(json.dumps({
            "iteration": iteration,
            "node": node_id,
            "returncode": result.returncode,
            "all_exit_artifacts_exist": all_exist,
        }, ensure_ascii=False))

    print(json.dumps({
        "passed": False,
        "done": False,
        "error": f"max iterations reached: {max_iterations}",
    }, indent=2, ensure_ascii=False), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
