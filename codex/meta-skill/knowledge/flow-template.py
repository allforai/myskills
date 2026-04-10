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
MAX_CONSECUTIVE_FAILURES_PER_NODE = 3
MAX_STAGNANT_ITERATIONS = 5
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


def load_bootstrap_goal(project_root: Path) -> str | None:
    profile_path = project_root / ".allforai/bootstrap/bootstrap-profile.json"
    if not profile_path.exists():
        return None
    try:
        profile = load_json(profile_path)
    except Exception:
        return None

    for key in ("task_goal", "user_goal", "goal"):
        value = profile.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def artifact_exists(project_root: Path, rel_path: str) -> bool:
    return (project_root / rel_path).exists()


def diagnosis_protocol_path(project_root: Path) -> Path:
    return project_root / ".allforai/bootstrap/protocols/diagnosis.md"


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


def append_diagnosis_entry(
    workflow_path: Path,
    node_id: str,
    attempts: int,
    summary: str,
    diagnosis_output: str,
) -> None:
    workflow = load_json(workflow_path)
    diagnosis_history = workflow.setdefault("diagnosis_history", [])
    diagnosis_history.append(
        {
            "node": node_id,
            "attempts": attempts,
            "recorded_at": now_iso(),
            "summary": summary,
            "diagnosis_output": diagnosis_output,
        }
    )
    save_json(workflow_path, workflow)


def count_consecutive_failures(workflow: dict, node_id: str) -> int:
    count = 0
    for entry in reversed(workflow.get("transition_log", [])):
        if entry.get("node") != node_id:
            break
        if entry.get("status") == "failed":
            count += 1
            continue
        break
    return count


def transition_artifacts(entry: dict) -> list[str]:
    artifacts = entry.get("artifacts_created")
    if isinstance(artifacts, list):
        return artifacts

    artifacts = entry.get("artifacts")
    if isinstance(artifacts, list):
        return artifacts

    return []


def stagnant_iteration_count(workflow: dict) -> int:
    count = 0
    for entry in reversed(workflow.get("transition_log", [])):
        if transition_artifacts(entry):
            break
        count += 1
    return count


def run_post_checks(project_root: Path) -> None:
    scripts = project_root / ".allforai/bootstrap/scripts"
    bootstrap_dir = project_root / ".allforai/bootstrap"
    subprocess.run([sys.executable, str(scripts / "validate_bootstrap.py"), str(bootstrap_dir)], cwd=project_root, check=False)
    product_summary = bootstrap_dir / "product-summary.json"
    if product_summary.exists():
        subprocess.run([sys.executable, str(scripts / "check_product_summary.py"), str(product_summary)], cwd=project_root, check=False)


def goal_based_completion_required(project_root: Path) -> bool:
    profile_path = project_root / ".allforai/bootstrap/bootstrap-profile.json"
    if not profile_path.exists():
        return False
    try:
        profile = load_json(profile_path)
    except Exception:
        return False
    return profile.get("completion_mode") == "goal_based"


def acceptance_requires_iteration(project_root: Path) -> bool:
    acceptance_path = project_root / ".allforai/bootstrap/artifacts/parity-acceptance.md"
    if not acceptance_path.exists():
        return False
    try:
        text = acceptance_path.read_text(encoding="utf-8").lower()
    except Exception:
        return False

    markers = [
        "needs_iteration",
        "continue",
        "next repair target",
        "remaining deviations",
        "remaining blockers",
        "goal still open",
    ]
    return any(marker in text for marker in markers)


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


def build_diagnosis_prompt(node_id: str, attempt_count: int) -> str:
    return f"""Diagnose a repeated workflow failure and stop after writing the diagnosis.

Failed node: {node_id}
Consecutive failed attempts: {attempt_count}

Requirements:
1. Read `.allforai/bootstrap/workflow.json`.
2. Read `.allforai/bootstrap/node-specs/{node_id}.md`.
3. Read `.allforai/bootstrap/protocols/diagnosis.md`.
4. Inspect the failed node's missing exit artifacts and the recent `transition_log`.
5. Write a concise diagnosis summary describing:
   - likely root cause
   - whether the missing work is upstream, in-node, or out-of-scope
   - the best next repair step
6. Output plain text only. Do not execute new implementation work in this diagnosis pass.
7. Stop after emitting the diagnosis.
"""


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


def run_diagnosis(project_root: Path, node_id: str, attempt_count: int) -> subprocess.CompletedProcess[str]:
    return run_codex(project_root, build_diagnosis_prompt(node_id, attempt_count))


def parse_legacy_args(argv: list[str], project_root: Path) -> tuple[str, int]:
    goal = load_bootstrap_goal(project_root) or DEFAULT_GOAL
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
    project_root = find_project_root(Path.cwd())
    goal, max_iterations = parse_legacy_args(sys.argv, project_root)
    workflow_path = project_root / ".allforai/bootstrap/workflow.json"

    for iteration in range(1, max_iterations + 1):
        workflow = load_json(workflow_path)
        node = first_pending_node(project_root, workflow)
        if node is None:
            if goal_based_completion_required(project_root) and acceptance_requires_iteration(project_root):
                print(
                    json.dumps(
                        {
                            "passed": False,
                            "done": False,
                            "error": "acceptance indicates the current slice completed but the overall goal remains open",
                        },
                        indent=2,
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
                return 5
            run_post_checks(project_root)
            print(json.dumps({"passed": True, "done": True, "iterations": iteration - 1}, indent=2, ensure_ascii=False))
            return 0

        node_id = node["id"]
        failure_count = count_consecutive_failures(workflow, node_id)
        if failure_count >= MAX_CONSECUTIVE_FAILURES_PER_NODE:
            diagnosis_path = diagnosis_protocol_path(project_root)
            diagnosis = run_diagnosis(project_root, node_id, failure_count)
            diagnosis_text = (diagnosis.stdout or diagnosis.stderr or "").strip()
            if diagnosis_path.exists() and not diagnosis_text:
                diagnosis_text = (
                    "Diagnosis protocol exists but Codex returned no diagnosis output. "
                    f"Read {diagnosis_path} and inspect the latest failed transitions for {node_id}."
                )
            elif not diagnosis_text:
                diagnosis_text = (
                    "Repeated failures exceeded the supervisor threshold and no diagnosis output was returned."
                )
            append_diagnosis_entry(
                workflow_path,
                node_id,
                failure_count,
                f"Repeated node failure reached threshold {MAX_CONSECUTIVE_FAILURES_PER_NODE}.",
                diagnosis_text[:4000],
            )
            print(
                json.dumps(
                    {
                        "passed": False,
                        "done": False,
                        "node": node_id,
                        "error": "failure threshold reached",
                        "consecutive_failures": failure_count,
                        "diagnosis_recorded": True,
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 3

        if stagnant_iteration_count(workflow) >= MAX_STAGNANT_ITERATIONS:
            print(
                json.dumps(
                    {
                        "passed": False,
                        "done": False,
                        "error": f"stagnant workflow: {MAX_STAGNANT_ITERATIONS} consecutive transitions without new artifacts",
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 4

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
