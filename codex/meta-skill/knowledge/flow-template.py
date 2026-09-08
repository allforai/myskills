#!/usr/bin/env python3
"""Non-stop Codex workflow driver template.

Bootstrap should materialize this file into `.allforai/codex/flow.py` inside the
target project. Shared workflow contracts remain under `.allforai/bootstrap/`,
while Codex-only runtime helpers live under `.allforai/codex/`.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MAX_ITERATIONS = 200
MAX_CONSECUTIVE_FAILURES_PER_NODE = 3
MAX_STAGNANT_ITERATIONS = 5
DEFAULT_GOAL = "Complete the entire generated workflow end-to-end. Do not stop to ask what to do next. Keep executing nodes until the workflow is done, then stop for unified acceptance."

BLOCKING_STATUS_VALUES = {
    "accepted_with_gaps",
    "accepted_with_warnings",
    "blocked",
    "conditional_pass",
    "degraded",
    "failed",
    "failed_validation",
    "failed_env",
    "incomplete",
    "needs_revision",
    "not_generated",
    "not_ready",
    "partial",
    "partial_pass",
    "placeholder",
    "passed_with_warnings",
    "revision-requested",
    "spec_only",
    "spec_ready",
}

STATUS_FIELDS = (
    "status",
    "qa_status",
    "overall_status",
    "repair_status",
    "revalidation_status",
    "overall_launch_status",
    "validation_status",
    "acceptance_state",
)

PRODUCTION_GAP_FIELDS = (
    "asset_gaps",
    "audio_gaps",
    "code_gaps",
    "contract_gaps",
    "gaps",
    "warnings",
    "non_blocking_warnings",
    "known_gaps",
    "remaining_gaps",
    "test_gaps",
    "unresolved_findings",
    "degraded_contracts",
    "blockers",
    "major_findings",
)

FORBIDDEN_PRODUCTION_GAP_TERMS = (
    "absent",
    "borrowed",
    "conditional pass",
    "debug scene",
    "degraded",
    "fallback",
    "generic",
    "graphics",
    "missing",
    "not delivered",
    "not_generated",
    "placeholder",
    "prototype",
    "prototypeboard",
    "pure-color",
    "sample scene",
    "silent",
    "spec_ready",
    "stub",
    "tween fallback",
    "缺失",
    "未完成",
    "未生成",
    "未修复",
    "未处理",
    "待处理",
    "剩余",
    "降级",
    "占位",
    "警告",
)

STALE_SENSITIVE_ARTIFACT_MARKERS = (
    ".allforai/game-2d/assembly/",
    ".allforai/game-2d/qa/",
    ".allforai/game-2d/repair/",
    ".allforai/game-frontend/assembly/",
    ".allforai/game-frontend/qa/",
    ".allforai/visual-qa/",
)

STALE_SOURCE_DIRS = (
    "game-client/assets/scripts",
    "game-client/assets/scenes",
    "game-client/assets/resources",
    "assets/scripts",
    "assets/scenes",
    "assets/resources",
    "src",
)


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


def artifact_path(item) -> str:
    if isinstance(item, dict):
        return str(item.get("path", ""))
    return str(item)


def artifact_status_error(path: Path, project_root: Path | None = None) -> str | None:
    if path.suffix != ".json" or not path.exists():
        return None
    stale_error = stale_runtime_artifact_error(path, project_root)
    if stale_error:
        return stale_error
    try:
        data = load_json(path)
    except Exception:
        return "invalid or unreadable JSON artifact"
    if not isinstance(data, dict):
        return None
    if not data:
        return "empty JSON artifact is not a valid completion report or contract"

    for field in STATUS_FIELDS:
        value = data.get(field)
        if isinstance(value, str) and (
            value.lower() in BLOCKING_STATUS_VALUES or value.lower().startswith("blocked_by_")
        ):
            return f"{field}={value}"

    for field in PRODUCTION_GAP_FIELDS:
        value = data.get(field)
        if value in (None, [], {}):
            continue
        if field in {
            "asset_gaps",
            "audio_gaps",
            "blockers",
            "code_gaps",
            "contract_gaps",
            "gaps",
            "major_findings",
            "remaining_gaps",
            "test_gaps",
            "unresolved_findings",
        }:
            return f"{field} contains unresolved gaps/findings"
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, dict) and (
                item.get("allowed_by_production_policy") is True
                or item.get("explicitly_approved_for_launch") is True
            ):
                continue
            text = json.dumps(item, ensure_ascii=False).lower()
            for term in FORBIDDEN_PRODUCTION_GAP_TERMS:
                if term in text:
                    return f"{field} contains forbidden production gap term: {term}"
    return None


def stale_runtime_artifact_error(path: Path, project_root: Path | None) -> str | None:
    if project_root is None:
        return None
    try:
        rel_path = str(path.resolve().relative_to(project_root.resolve()))
    except Exception:
        return None
    if not any(marker in rel_path for marker in STALE_SENSITIVE_ARTIFACT_MARKERS):
        return None
    artifact_mtime = path.stat().st_mtime
    newest_source: tuple[str, float] | None = None
    for rel_dir in STALE_SOURCE_DIRS:
        source_dir = project_root / rel_dir
        if not source_dir.exists():
            continue
        for source in source_dir.rglob("*"):
            if not source.is_file() or source.suffix.lower() not in {
                ".ts", ".js", ".json", ".scene", ".prefab", ".png", ".jpg", ".jpeg", ".webp", ".mp3", ".wav", ".ogg"
            }:
                continue
            mtime = source.stat().st_mtime
            if mtime > artifact_mtime and (newest_source is None or mtime > newest_source[1]):
                newest_source = (str(source.relative_to(project_root)), mtime)
    if newest_source is None:
        return None
    return f"stale runtime/visual artifact; newer source exists: {newest_source[0]}"


def artifact_ready(project_root: Path, rel_path: str) -> bool:
    path = project_root / rel_path
    return path.exists() and artifact_status_error(path, project_root) is None


def diagnosis_protocol_path(project_root: Path) -> Path:
    return project_root / ".allforai/bootstrap/protocols/diagnosis.md"


def first_pending_node(project_root: Path, workflow: dict) -> dict | None:
    for node in workflow.get("nodes", []):
        if not independent_artifact_gate(project_root, str(node.get("node_id") or node.get("id") or "")):
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
    # The supervisor owns the verdict; a worker's self-reported completion cannot
    # conceal a failed gate or prevent the consecutive-failure stop condition.
    for entry in transition_log[before_count:]:
        if entry.get("node") == node_id:
            entry.update(status=status, completed_at=now_iso(), artifacts_created=artifacts_created)
            if error:
                entry["error"] = error
            else:
                entry.pop("error", None)
            save_json(workflow_path, workflow)
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


def script_path(project_root: Path, name: str) -> Path:
    return project_root / ".allforai/bootstrap/scripts" / name


def execution_policy(project_root: Path) -> dict:
    path = project_root / ".allforai/codex/execution-policy.json"
    policy = {"sandbox": "workspace-write", "node_timeout_seconds": 1800, "helper_timeout_seconds": 300}
    if path.exists():
        supplied = load_json(path)
        if not isinstance(supplied, dict) or set(supplied) - set(policy):
            raise ValueError("invalid execution-policy.json")
        policy.update(supplied)
    if policy["sandbox"] not in {"read-only", "workspace-write"}:
        raise ValueError("unsupported sandbox: permission escalation must not be automatic")
    for key in ("node_timeout_seconds", "helper_timeout_seconds"):
        if type(policy[key]) is not int or not 1 <= policy[key] <= 86400:
            raise ValueError(f"{key} must be an integer between 1 and 86400")
    return policy


def run_bounded(command: list[str], project_root: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    """Bound the whole subprocess group, including children of CLI/helper processes."""
    try:
        proc = subprocess.Popen(command, cwd=project_root, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=(os.name == "posix"))
    except OSError as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc))
    def stop():
        if os.name == "posix":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            proc.kill()
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        stop()
        out, err = proc.communicate()
        return subprocess.CompletedProcess(command, 124, out, err + f"\nTimed out after {timeout}s")
    except KeyboardInterrupt:
        stop()
        out, err = proc.communicate()
        return subprocess.CompletedProcess(command, 130, out, err + "\nInterrupted by user")
    return subprocess.CompletedProcess(command, proc.returncode, out, err)


def run_script(project_root: Path, name: str, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    path = script_path(project_root, name)
    if not path.exists():
        return None
    return run_bounded([sys.executable, str(path), *args], project_root,
                       execution_policy(project_root)["helper_timeout_seconds"])


def run_preflight(project_root: Path) -> int:
    run_script(project_root, "record_run_event.py", [".", "--event", "run_started", "--status", "started", "--message", "codex flow.py invoked"])
    readiness = run_script(project_root, "validate_unattended_readiness.py", [".", "--write-report"])
    report = project_root / ".allforai/bootstrap/unattended-run-readiness.json"
    status = ""
    if report.exists():
        try:
            status = str(load_json(report).get("status") or "")
        except Exception:
            status = ""
    if readiness is None or readiness.returncode != 0:
        run_script(project_root, "record_run_event.py", [".", "--event", "preflight_blocked", "--status", "blocked", "--message", "unattended readiness failed"])
        run_script(project_root, "summarize_run_log.py", [".", "--write-report"])
        return 6
    if status != "ready":
        run_script(project_root, "record_run_event.py", [".", "--event", "preflight_blocked", "--status", "blocked", "--message", f"unattended readiness status={status}" ])
        run_script(project_root, "summarize_run_log.py", [".", "--write-report"])
        return 6
    return 0


def run_expanders(project_root: Path, workflow: dict) -> bool:
    expanders = workflow.get("expanders", ["expand_game_2d_production.py"])
    for expander in expanders:
        name = Path(str(expander)).name
        if not name.endswith(".py"):
            return False
        result = run_script(project_root, name, ["."])
        if result is None or result.returncode != 0:
            return False
    return True


def independent_artifact_gate(project_root: Path, node_id: str) -> bool:
    result = run_script(
        project_root,
        "check_artifacts.py",
        [str(project_root / ".allforai/bootstrap/workflow.json"), "--node", node_id, "--json"],
    )
    if result is None or result.returncode != 0 or not result.stdout.strip():
        return False
    try:
        payload = json.loads(result.stdout)
    except Exception:
        return False
    return (isinstance(payload, dict) and payload.get("node_id") == node_id
            and payload.get("all_exist") is True
            and isinstance(payload.get("artifacts"), list) and bool(payload["artifacts"]))


def run_post_checks(project_root: Path) -> bool:
    bootstrap_dir = project_root / ".allforai/bootstrap"
    result = run_script(project_root, "validate_bootstrap.py", [str(bootstrap_dir)])
    if result is None or result.returncode != 0:
        return False
    product_summary = bootstrap_dir / "product-summary.json"
    if product_summary.exists():
        result = run_script(project_root, "check_product_summary.py", [str(product_summary)])
        if result is None or result.returncode != 0:
            return False
    run_script(project_root, "summarize_run_log.py", [".", "--write-report"])
    return True


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
    report = project_root / ".allforai/concept-acceptance/acceptance-report.json"
    if report.exists():
        try:
            data = load_json(report)
            if data.get("verdict", data.get("status")) == "needs_iteration":
                return True
        except (ValueError, OSError, AttributeError):
            return True
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
6. Do not write `completed` when any exit artifact says `conditional_pass`, `partial`, `accepted_with_gaps`, `accepted_with_warnings`, `passed_with_warnings`, `blocked_by_*`, or contains unresolved `gaps`, `code_gaps`, `asset_gaps`, `audio_gaps`, `remaining_gaps`, `blockers`, `major_findings`, or `unresolved_findings`. Continue repairing and rerunning validation inside this node when it owns the fix; otherwise write `failed` with the exact blocker and repair owner.
7. If the node fails, write a one-line `error` field explaining the blocker.
8. Stop only after this node is truly completed or a failed transition has been written.
9. Record non-blocking safety warnings as a warnings array of strings in `.allforai/bootstrap/run-warnings.json`; the supervisor applies the recorded Run Policy. Hard safety or unresolved product requirements remain failures, never warnings.
10. Follow `.allforai/bootstrap/protocols/input-freshness.md`: after implementation settles, observe current inputs, register additional reads, refresh required documents, and publish the evidence observation with the actual acceptance command. Reobserve and reverify stale input; contract-only publication cannot prove completion. The independent artifact gate consumes this freshness state.

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
    policy = execution_policy(project_root)
    command = [
        "codex",
        "exec",
        "--sandbox", policy["sandbox"],
        "-c", 'approval_policy="never"',
        "-C",
        str(project_root),
        "--skip-git-repo-check",
        prompt,
    ]
    return run_bounded(command, project_root, policy["node_timeout_seconds"])


def run_diagnosis(project_root: Path, node_id: str, attempt_count: int) -> subprocess.CompletedProcess[str]:
    return run_codex(project_root, build_diagnosis_prompt(node_id, attempt_count))


def policy_action(project_root: Path, event: str | None = None) -> str:
    args = [".", "--policy-event", event] if event else [".", "--run-policy"]
    result = run_script(project_root, "product_intent.py", args)
    if result is None or result.returncode:
        return "blocked"
    try:
        data = json.loads(result.stdout)
        return data["action"] if event else ("ready" if data["status"] == "run_policy_ready" else "blocked")
    except (ValueError, KeyError, TypeError):
        return "blocked"


def handle_iteration(project_root: Path) -> int:
    action = policy_action(project_root, "on_needs_iteration")
    report = project_root / ".allforai/concept-acceptance/acceptance-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    if action == "accept":
        path = project_root / ".allforai/bootstrap/assumed-decisions.json"
        data = load_json(path) if path.exists() else {"decisions": []}
        entry = {"status": "accepted_with_gaps", "source": ".allforai/bootstrap/run-policy.json",
                 "scope": "run outcome only; no product requirement is approved"}
        if entry not in data.setdefault("decisions", []):
            data["decisions"].append(entry)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        # A qualified acceptance does not pass the artifact gate or complete a
        # node. Recheck product prerequisites; leave failing exit artifacts intact.
        return 0 if run_preflight(project_root) == 0 else 6
    report.write_text("Acceptance needs iteration. Review acceptance-report.json for the gaps.\n"
                      "At the next interactive entry choose fix, re-bootstrap, or accept; execution asks no new questions.\n")
    if action == "auto_fix_once":
        state_path = project_root / ".allforai/bootstrap/run-policy-state.json"
        state = load_json(state_path) if state_path.exists() else {}
        if not state.get("iteration_repair_started"):
            state["iteration_repair_started"] = True
            state_path.write_text(json.dumps(state) + "\n")
            repaired = run_codex(project_root, "Apply the recorded auto_fix_once Run Policy: read the current concept-acceptance report, "
                "repair only its named gaps authorized by existing decision_inputs, rerun concept-acceptance and its independent "
                "verification, then stop. Do not ask questions or change product requirements; unresolved product choices block repair.")
            if repaired.returncode == 0 and not acceptance_requires_iteration(project_root) and run_post_checks(project_root):
                return 0
    return 5


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
    preflight = run_preflight(project_root)
    if preflight != 0:
        print(
            json.dumps(
                {
                    "passed": False,
                    "done": False,
                    "error": "unattended readiness preflight blocked execution",
                },
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return preflight

    if max_iterations > 0 and policy_action(project_root) != "ready":
        print(json.dumps({"passed": False, "done": False,
                          "error": "Run Policy missing or invalid; return to interactive run entry before the first node"}), file=sys.stderr)
        return 6

    for iteration in range(1, max_iterations + 1):
        warning_path = project_root / ".allforai/bootstrap/run-warnings.json"
        if warning_path.exists():
            try:
                warnings = load_json(warning_path)["warnings"]
                if not isinstance(warnings, list) or not all(isinstance(w, str) and w.strip() for w in warnings):
                    raise ValueError("warnings must be an array of non-empty strings")
            except (OSError, ValueError, KeyError, TypeError):
                print(json.dumps({"passed": False, "done": False, "error": "invalid safety warning report"}), file=sys.stderr)
                return 6
            if warnings:
                run_script(project_root, "record_run_event.py", [".", "--event", "safety_warning", "--status", "warning", "--message", "; ".join(warnings)])
                if policy_action(project_root, "on_safety_warning") != "continue":
                    print(json.dumps({"passed": False, "done": False, "error": "recorded Run Policy halted on safety warning", "warnings": warnings}), file=sys.stderr)
                    return 4
        workflow = load_json(workflow_path)
        if not run_expanders(project_root, workflow):
            print(json.dumps({"passed": False, "done": False, "error": "workflow expander failed"}), file=sys.stderr)
            return 6
        workflow = load_json(workflow_path)
        node = first_pending_node(project_root, workflow)
        acceptance_node = node is None or any(artifact_path(a) == ".allforai/concept-acceptance/acceptance-report.json"
                                               for a in node.get("exit_artifacts", []))
        if acceptance_node and acceptance_requires_iteration(project_root):
            outcome = handle_iteration(project_root)
            accepted = outcome == 0 and load_json(project_root / ".allforai/bootstrap/run-policy.json")["on_needs_iteration"] == "accept"
            print(
                json.dumps(
                    {
                        "passed": outcome == 0 and not accepted,
                        "done": outcome == 0 and not accepted,
                        "run_policy_outcome": "accepted_with_gaps" if accepted else "repair verified" if outcome == 0 else "iteration halted with report",
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return outcome
        if node is None:
            if not workflow.get("nodes") or not run_post_checks(project_root):
                print(json.dumps({"passed": False, "done": False, "error": "final validation failed"}), file=sys.stderr)
                return 6
            print(json.dumps({"passed": True, "done": True, "iterations": iteration - 1}, indent=2, ensure_ascii=False))
            return 0

        node_id = str(node.get("node_id") or node.get("id"))
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
            history = load_json(workflow_path).get("diagnosis_history", [])
            related = [d for d in history if d.get("node_id", d.get("node")) == node_id]
            causes = [d.get("root_cause", {}).get("node") for d in related]
            capped = any(d.get("out_of_scope") is True for d in related) or any(
                cause and causes.count(cause) >= 2 for cause in causes)
            if not capped and policy_action(project_root, "on_repeated_failure") == "continue":
                pass
            else:
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
            artifact_path(path)
            for path in node.get("exit_artifacts", [])
            if artifact_ready(project_root, artifact_path(path))
        ]
        gate_node_id = str(node.get("node_id") or node_id)
        all_ready = result.returncode == 0 and independent_artifact_gate(
            project_root, gate_node_id
        )

        if all_ready:
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
            readiness_errors = []
            for item in node.get("exit_artifacts", []):
                rel_path = artifact_path(item)
                path = project_root / rel_path
                if not path.exists():
                    readiness_errors.append(f"missing {rel_path}")
                    continue
                status_error = artifact_status_error(path, project_root)
                if status_error:
                    readiness_errors.append(f"{rel_path}: {status_error}")
            error_line = "; ".join(readiness_errors)[:300] if readiness_errors else (
                lines[-1][:300] if lines else "Codex stopped before satisfying ready exit artifacts."
            )
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
            "all_exit_artifacts_ready": all_ready,
        }, ensure_ascii=False))
        if result.returncode in {124, 130}:
            print(json.dumps({"passed": False, "done": False, "node": node_id,
                              "error": "execution timed out or was interrupted; revalidate on resume"}), file=sys.stderr)
            return result.returncode

    print(json.dumps({
        "passed": False,
        "done": False,
        "error": f"max iterations reached: {max_iterations}",
    }, indent=2, ensure_ascii=False), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
