#!/usr/bin/env python3
"""Non-stop Codex workflow driver template.

Bootstrap should materialize this file into `.allforai/codex/flow.py` inside the
target project. Shared workflow contracts remain under `.allforai/bootstrap/`,
while Codex-only runtime helpers live under `.allforai/codex/`.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MAX_ITERATIONS = 200
MAX_CONSECUTIVE_FAILURES_PER_NODE = 3
# The documented fallback for a declared repair loop that carries no budget at all.
# A declared budget always wins; an unusable one is never replaced by this.
DEFAULT_REPAIR_ATTEMPTS = 3
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
    "existence_only",
    "not_good_enough",
    "quality_failed",
    "passed_with_warnings",
    "revision-requested",
    "spec_only",
    "spec_ready",
}

# A failed QA node only opens a repair loop when it reached its own verdict. These
# report statuses say it never got that far — environment, authority, or never-ran —
# so there is nothing to repair against. Mirrors engine-core.js NON_QA_FAILURE_TYPES
# so both orchestrators admit the same failures.
NON_QA_REPORT_STATUSES = {
    "blocked",
    "existence_only",
    "failed_env",
    "not_generated",
    "not_ready",
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
    # The concept-acceptance coverage gate: behaviour mappings with no evidence. A
    # non-empty list is that gate's QA verdict, routed like any other (ADR 0008).
    "missing_mappings",
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
            "missing_mappings",
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


SAFETY_QUARANTINE = ".allforai/bootstrap/safety-quarantine.json"
SAFETY_LOCK = ".allforai/bootstrap/safety-quarantine.lock"
SAFETY_WARNINGS = ".allforai/bootstrap/run-warnings.json"
SAFETY_HALT_REASON = "Recorded Run Policy requires a run-wide safety halt"


def safety_halted(project_root: Path) -> bool:
    """A run-wide halt is already recorded, so nothing further may be dispatched.

    The lock counts as well as the marker: `run_safety.py` leaves it behind when a
    quarantine could not be published, and the absence of the marker is then not proof
    that no halt was required. `validate_unattended_readiness.py` refuses the same two
    paths, so the halt survives a restart instead of living only in this process.
    """
    return (project_root / SAFETY_QUARANTINE).exists() or (project_root / SAFETY_LOCK).exists()


def read_safety_warnings(project_root: Path):
    """The warnings the executor recorded, or None when the report cannot be trusted.

    An unreadable or wrong-shaped report is not an empty one. Reading it as "no warnings"
    would let a malformed safety report authorize the very completion the report exists
    to stop.
    """
    path = project_root / SAFETY_WARNINGS
    if not path.exists():
        return []
    try:
        warnings = load_json(path)["warnings"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not isinstance(warnings, list) or not all(isinstance(w, str) and w.strip() for w in warnings):
        return None
    return warnings


def safety_halt_required(project_root: Path, warnings: list[str]) -> bool:
    """Record the warnings and ask the recorded Run Policy whether the run may continue."""
    if not warnings:
        return False
    run_script(project_root, "record_run_event.py",
               [".", "--event", "safety_warning", "--status", "warning",
                "--message", "; ".join(warnings)])
    return policy_action(project_root, "on_safety_warning") != "continue"


def fence_safety_halt(project_root: Path) -> bool:
    """Leave the persistent fence a quarantine that could not be published leaves behind.

    `run_safety.py` keeps `safety-quarantine.lock` for exactly this meaning: a quarantine
    was attempted and its marker is not proof of anything. When the helper is missing or
    could not answer at all, the driver still owes the run that fence — otherwise the only
    record of the halt is the worker-written warnings file and a mutable Run Policy, and
    the next start would read the quarantined outputs as a completed node. `safety_halted`
    and `validate_unattended_readiness.py` both already refuse this path.
    """
    lock = project_root / SAFETY_LOCK
    try:
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.mkdir(exist_ok=True)
    except OSError:
        return False
    return True


def quarantine_outputs(project_root: Path, node_ids: list[str], reason: str) -> bool:
    """Fence these nodes' outputs behind the canonical quarantine. Never accepts or deletes.

    Codex cannot cancel an executor that has already finished, so the outputs of the
    attempt that raised the warning exist. They are quarantined rather than completed:
    the run stops, and only independent revalidation may release them (ADR 0006).
    Returns whether the canonical quarantine is durably recorded — an unconfirmed
    persistence is reported, never assumed. Whatever the answer, the run is fenced before
    it is returned: an unpublished quarantine still stops the next start.
    """
    result = run_script(project_root, "run_safety.py",
                        [".", "--nodes-json", json.dumps(node_ids), "--reason", reason])
    verdict = None
    if result is not None and result.returncode == 0:
        try:
            verdict = json.loads(result.stdout)
        except (ValueError, TypeError):
            verdict = None
    recorded = verdict.get("node_ids") if isinstance(verdict, dict) else None
    quarantined = (isinstance(verdict, dict) and verdict.get("status") == "quarantined"
                   and isinstance(recorded, list)
                   and all(node_id in recorded for node_id in node_ids))
    if not quarantined:
        fence_safety_halt(project_root)
    return quarantined


def diagnosis_protocol_path(project_root: Path) -> Path:
    return project_root / ".allforai/bootstrap/protocols/diagnosis.md"


def node_identity(node: dict) -> str:
    return str(node.get("node_id") or node.get("id") or "")


def declared_repair_loops(project_root: Path) -> list[dict]:
    """`required_repair_loops` from the readiness spec; unreadable state declares nothing."""
    path = project_root / ".allforai/bootstrap/unattended-run-readiness-spec.json"
    if not path.exists():
        return []
    try:
        loops = load_json(path).get("required_repair_loops")
    except (OSError, ValueError, AttributeError):
        return []
    if not isinstance(loops, list):
        return []
    return [loop for loop in loops if isinstance(loop, dict) and loop.get("repair_node_id")]


def loop_nodes(loop: dict, *primary_keys: str) -> list[str]:
    for key in primary_keys:
        value = loop.get(key)
        if isinstance(value, list):
            return [str(item) for item in value]
    return []


def repair_budget(loop: dict) -> int | None:
    """Declared attempts for one QA node; None when the loop has no usable bound.

    An explicitly declared budget that is not a positive integer is a planning
    error, not a request for the default: defaulting there would grant attempts
    the plan never authorized, so such a loop routes nothing and its failed QA
    node is blocked rather than re-run — see `unbounded_repair_loops`.
    `validate_unattended_readiness.py` blocks the same shape before the run starts.
    """
    if "max_attempts" not in loop:
        return DEFAULT_REPAIR_ATTEMPTS
    budget = loop.get("max_attempts")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
        return None
    return budget


def unbounded_repair_loops(project_root: Path) -> list[str]:
    """Repair node ids whose declared loop states a `max_attempts` that is not usable.

    Such a loop can never bound anything, so its QA failure has no repair route at all.
    Re-running the QA node would reproduce the same failure with nothing able to fix it
    and hide the planning error behind a busy run, so the failure is fail-closed instead:
    the QA node is blocked and the run reports it, the same terminal answer the Claude
    engine gives. `validate_unattended_readiness.py` and `validate_bootstrap.py` reject
    the shape before the run; this is what happens if one ever gets past them.
    """
    return sorted({str(loop["repair_node_id"]) for loop in declared_repair_loops(project_root)
                   if repair_budget(loop) is None})


def repair_awaiting_finalization(project_root: Path, workflow: dict, repair_node_id: str) -> bool:
    """This repair already delivered and every QA node it answers has since completed.

    Its implementation landed; what it never got to do is publish the evidence the
    freshness gate withheld while the QA node was failing. Re-running the implementation
    now would mutate the very source that QA node has just verified and invalidate it, so
    the dispatch that follows finalizes the delivery instead of repeating it.
    """
    loops = [loop for loop in declared_repair_loops(project_root)
             if str(loop["repair_node_id"]) == repair_node_id]
    if not loops:
        return False
    log = workflow.get("transition_log", [])
    if not any(repair_delivered(entry) for entry in log if entry.get("node") == repair_node_id):
        return False
    qa_nodes = {qa for loop in loops for qa in loop_nodes(loop, "qa_node_ids", "qa_nodes")}
    for qa_node_id in qa_nodes:
        latest = next((entry for entry in reversed(log) if entry.get("node") == qa_node_id), None)
        if latest is None or latest.get("status") != "completed":
            return False
    return True


REPAIR_LEDGER = ".allforai/bootstrap/repair-authorizations.json"
LEDGER_HELPER = "repair_authorization.py"

# Consumption verdicts keyed by the exact ledger bytes they were read from. The helper
# stays the only accounting authority; this only avoids re-asking it the same question
# about a file that has not changed. Any write to the ledger changes the digest and the
# next read goes back to the helper.
_LEDGER_READS: dict[tuple[str, str], dict] = {}


def authorization_request(project_root: Path, request: dict) -> dict | None:
    """One request to the canonical repair-authorization helper, or None when unusable.

    `.allforai/bootstrap/repair-authorizations.json` is the authority on what each QA
    obligation has spent, and this driver never reads or writes it directly: a second
    implementation of the accounting rules is a second set of bugs. A missing helper, a
    crashed one, or output that is not a verdict is not a zero balance — it is unknown,
    and unknown blocks.
    """
    result = run_script(project_root, LEDGER_HELPER, ["."], json.dumps(request))
    if result is None or result.returncode not in (0, 1):
        return None
    try:
        verdict = json.loads(result.stdout)
    except (ValueError, TypeError):
        return None
    return verdict if isinstance(verdict, dict) and isinstance(verdict.get("status"), str) else None


def ledger_consumption(project_root: Path) -> dict | None:
    """Per-obligation spend for this run, read from the canonical ledger.

    Returns None when the accounting cannot be established — a missing helper, an
    unreadable ledger, an existing run whose history is ambiguous. `initialize` is only
    ever reached from a provably new ledger, and nothing here resets one.
    """
    ledger_path = project_root / REPAIR_LEDGER
    key = (str(project_root), file_digest(ledger_path) or "absent")
    cached = _LEDGER_READS.get(key)
    if cached is not None:
        return cached
    verdict = authorization_request(project_root, {"operation": "consumption"})
    if verdict is None:
        return None
    if verdict.get("status") == "ok":
        _LEDGER_READS[key] = verdict
        return verdict
    if verdict.get("untrusted") != "missing_ledger":
        # An unreadable ledger, an ambiguous history, or a foreign run identity. The
        # spent budget is unknown and a guess would hand back attempts already spent.
        return None
    # No ledger at all. Only a run the helper can itself prove untouched may start at
    # zero; a workflow that already shows execution is refused there, and this driver
    # neither overrides that nor invents the history it is missing.
    started = authorization_request(project_root, {"operation": "initialize",
                                                   "run_id": uuid.uuid4().hex})
    if started is None or started.get("status") != "ok":
        return None
    verdict = authorization_request(project_root, {"operation": "consumption"})
    if verdict is None or verdict.get("status") != "ok":
        return None
    _LEDGER_READS[(str(project_root), file_digest(ledger_path) or "absent")] = verdict
    return verdict


def repair_ledger_unreadable(project_root: Path, workflow: dict) -> bool:
    """True when a run with declared repair loops has no trustworthy spend accounting.

    Nothing may then run: dispatching now could re-grant an attempt whose work is already
    in the tree. A run with no declared loop has no budget to lose and is unaffected.
    """
    if not declared_repair_loops(project_root):
        return False
    return ledger_consumption(project_root) is None


def unresolved_authorizations(project_root: Path) -> list[str]:
    """Ids of grants the ledger holds with no recorded outcome.

    Each one is an execution nobody watched end: it may have edited the tree and it may
    never have started. That is not an ordinary QA failure and it is not this driver's to
    guess, so it stops the whole run up front rather than being discovered whenever the
    affected repair node happens to be selected. Reconciling it against attributable
    evidence is a deliberate operation (ADR 0006, ADR 0007).
    """
    consumption = ledger_consumption(project_root)
    if consumption is None:
        return []
    return sorted({str(entry["authorization_id"])
                   for entry in consumption.get("unresolved") or []
                   if isinstance(entry, dict) and entry.get("authorization_id")})


def obligation_record(consumption: dict, repair_node_id: str, qa_node_id: str) -> dict:
    for record in consumption.get("obligations") or []:
        if (isinstance(record, dict) and record.get("repair_node_id") == repair_node_id
                and record.get("qa_node_id") == qa_node_id):
            return record
    return {}


def repair_attempts_spent(project_root: Path, repair_node_id: str, qa_node_id: str) -> int | None:
    """Repair dispatches this QA obligation has been charged for, per the canonical ledger.

    Per (repair node, QA node) because the declared budget is per QA node: one repair node
    may serve several, and attempts spent answering one are never charged to a sibling.
    Charged at the grant, not at the delivery — a budget that only charges for success
    bounds nothing, since a repair that errors or writes nothing would cost nothing and
    could repeat. None means the accounting is unknown, which is not zero.
    """
    consumption = ledger_consumption(project_root)
    if consumption is None:
        return None
    spent = obligation_record(consumption, repair_node_id, qa_node_id).get("spent", 0)
    if isinstance(spent, bool) or not isinstance(spent, int) or spent < 0:
        return None
    return spent


def repair_progress(project_root: Path, workflow: dict, repair_node_id: str,
                    qa_node_id: str) -> tuple[int | None, bool]:
    """(attempts this QA obligation has spent, repair already delivered for its last failure).

    The two answer different questions and come from different records. The spent budget is
    the canonical authorization ledger. `answered` is the loop's sequencing, read from the
    workflow transition log: a repair that already delivered against this QA node's current
    failure is not dispatched again, because the QA rerun, not another repair, is what
    judges it. Both are durable, so a restart resumes the same state instead of starting
    over.
    """
    awaiting_repair = False   # this QA node failed and no repair has answered it yet
    answered = False          # a repair delivered after this QA node's last transition
    for entry in workflow.get("transition_log", []):
        node = entry.get("node")
        status = entry.get("status")
        if node == qa_node_id:
            awaiting_repair = status == "failed"
            answered = False
        elif node == repair_node_id and repair_delivered(entry):
            if awaiting_repair and not answered:
                answered = True
    return repair_attempts_spent(project_root, repair_node_id, qa_node_id), answered


def eligible_obligations(project_root: Path, workflow: dict, repair_node_id: str,
                         qa_node_ids: list[str]) -> dict[str, int]:
    """{QA node id: its declared budget} for the obligations this dispatch may charge.

    A shared repair charges only the obligations that still have budget. An exhausted
    sibling is neither charged again nor discharged by the attempt that answers another
    obligation — it still has to be satisfied (ADR 0005).
    """
    budgets: dict[str, int] = {}
    for loop in declared_repair_loops(project_root):
        if str(loop["repair_node_id"]) != repair_node_id:
            continue
        budget = repair_budget(loop)
        if budget is None:
            continue
        for qa_node_id in loop_nodes(loop, "qa_node_ids", "qa_nodes"):
            if qa_node_id not in qa_node_ids:
                continue
            spent, _ = repair_progress(project_root, workflow, repair_node_id, qa_node_id)
            if spent is None or spent >= budget:
                continue
            budgets[qa_node_id] = budget
    return budgets


def authorize_repair_dispatch(project_root: Path, workflow: dict, repair_node_id: str,
                              qa_node_ids: list[str]) -> dict | None:
    """Charge and then claim the one execution this repair dispatch pays for.

    Two durable steps, in this order, both before the executor. `authorize` records the
    charge — it is never permission to run — and `start` claims the single execution it
    paid for. A process that dies between them leaves an unresolved grant, and the helper
    then refuses a further grant for those obligations rather than replaying uncertain
    work or refunding an attempt that may already have edited the tree (ADR 0006).
    Returns the claim when this dispatch may execute, otherwise None.
    """
    consumption = ledger_consumption(project_root)
    if consumption is None:
        return None
    budgets = eligible_obligations(project_root, workflow, repair_node_id, qa_node_ids)
    if not budgets:
        return None
    authorization_id = uuid.uuid4().hex
    granted = authorization_request(project_root, {
        "operation": "authorize", "run_id": consumption["run_id"],
        "authorization_id": authorization_id, "repair_node_id": repair_node_id,
        "obligations": sorted(budgets), "budgets": budgets,
        "provenance": {"host": "codex", "dispatched_at": now_iso()}})
    if not receipt_for(granted, "authorized", authorization_id,
                       run_id=consumption["run_id"]):
        return None
    claimed = authorization_request(project_root, {
        "operation": "start", "run_id": consumption["run_id"],
        "authorization_id": authorization_id})
    if (not receipt_for(claimed, "started", authorization_id)
            or claimed.get("execution_allowed") is not True):
        # The claim this dispatch would execute under is not the claim it asked for.
        # Nothing runs: the grant may be recorded, so the attempt stays unresolved and
        # the next dispatch for these obligations is refused rather than replayed.
        return None
    return {"authorization_id": authorization_id, "run_id": consumption["run_id"],
            "obligations": sorted(budgets)}


def receipt_for(verdict: dict | None, status: str, authorization_id: str, **fields) -> bool:
    """This verdict answers the request that was actually made, or it is not an answer.

    A verdict is trusted for its accounting, not for its addressing: a receipt naming a
    different authorization or a different run says nothing about this dispatch, and
    reading it as if it did would attribute one attempt's charge, claim or outcome to
    another. The helper echoes what it decided about; this checks it.
    """
    if not isinstance(verdict, dict) or verdict.get("status") != status:
        return False
    if verdict.get("authorization_id") != authorization_id:
        return False
    return all(verdict.get(key) == value for key, value in fields.items())


def settle_repair_dispatch(project_root: Path, grant: dict, outcome: str) -> bool:
    """Record how a claimed attempt ended. It never returns budget and never re-runs it.

    Only called when this driver observed the attempt finish. An interrupted or
    quarantined attempt is deliberately left unresolved: whether its execution occurred
    is then a question for `reconcile` and its evidence, not for the driver to assume.

    Returns whether the ledger confirmed this outcome for this authorization. A refused
    or unanswerable settlement is not a settled attempt, and the caller may not accept
    the work it was reporting on: the record of what the attempt did is the ledger's, and
    an attempt whose outcome never reached it is exactly the unresolved state that stops
    the next dispatch.
    """
    verdict = authorization_request(project_root, {
        "operation": "settle", "authorization_id": grant["authorization_id"],
        "outcome": outcome})
    return receipt_for(verdict, "settled", grant["authorization_id"], outcome=outcome)


def qa_nodes_routed_to(project_root: Path, workflow: dict, repair_node_id: str) -> list[str]:
    """QA node ids whose open failure this repair dispatch is being authorized against."""
    if repair_node_id not in declared_repair_nodes(project_root):
        return []
    complete = {node_identity(n): independent_artifact_gate(project_root, node_identity(n))
                for n in workflow.get("nodes", [])}
    return [qa_node_id
            for qa_node_id, loop in open_repair_loops(project_root, workflow, complete).items()
            if str(loop["repair_node_id"]) == repair_node_id]


def last_failed_transition(workflow: dict, node_id: str) -> dict | None:
    """This node's latest transition, only when that attempt failed.

    A repair answers a failure this run recorded. A node that never ran, or whose
    latest attempt completed, has no failed attempt to repair — whatever a file on
    disk says.
    """
    for entry in reversed(workflow.get("transition_log", [])):
        if entry.get("node") != node_id:
            continue
        return entry if entry.get("status") == "failed" else None
    return None


def last_failed_dispatch(workflow: dict, node_id: str) -> str | None:
    """`started_at` of this node's latest attempt, only when that attempt failed."""
    entry = last_failed_transition(workflow, node_id)
    return entry.get("started_at") if entry else None


def file_digest(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def report_state(project_root: Path, node: dict) -> dict[str, dict]:
    """Content identity and write time of the node's exit artifacts, by project path.

    Both, because either alone misreads an attempt: a node that re-runs and reaches the
    same verdict writes identical bytes, and a leftover that nobody wrote keeps both.
    Only the driver, measuring across the attempt it started, can tell them apart.
    """
    state = {}
    for item in node.get("exit_artifacts", []) or []:
        rel = artifact_path(item)
        path = project_root / rel
        digest = file_digest(path)
        if digest is None:
            continue
        try:
            written = path.stat().st_mtime_ns
        except OSError:
            continue
        state[rel] = {"digest": digest, "written": written}
    return state


def report_digests(project_root: Path, node: dict) -> dict[str, str]:
    """Content identity of the node's exit artifacts, by project path."""
    return {rel: entry["digest"] for rel, entry in report_state(project_root, node).items()}


def binding_identity(project_root: Path, node_id: str) -> str | None:
    """Identity of the input snapshot the node's freshness record was observed against.

    Two independent "inputs are current" answers do not prove the answers describe the
    same inputs: a source can change and be re-observed between them, and both say yes.
    This names the snapshot itself, so dispatch, report and admission can be required to
    refer to one observation. Read-only over the recorded state; the freshness helper
    that writes it is owned elsewhere.
    """
    state_path = project_root / ".allforai/bootstrap/evidence-freshness.json"
    if not state_path.exists():
        return None
    try:
        state = load_json(state_path)
    except (OSError, ValueError):
        return None
    if not isinstance(state, dict):
        return None
    # Contracts first, matching how the freshness helper resolves a node's record: a
    # freshly observed contract is the node's current binding even when older passing
    # evidence is still on file, and a failed QA node can never replace that evidence.
    for bucket in ("contracts", "nodes"):
        record = (state.get(bucket) or {}).get(node_id)
        if isinstance(record, dict) and record.get("inputs") is not None:
            payload = {"bucket": bucket, "kind": record.get("kind"), "inputs": record["inputs"]}
            return hashlib.sha256(
                json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()
    return None


def deliverable_state(project_root: Path, node: dict) -> dict[str, dict]:
    """`report_state` minus artifacts that say the node never reached a verdict.

    A report carrying an environment, authority or never-ran status is not a delivery
    and not a verdict, so writing one is not production: it must not spend a repair
    attempt or release a QA rerun.
    """
    state = {}
    for rel, entry in report_state(project_root, node).items():
        path = project_root / rel
        if path.suffix == ".json":
            try:
                data = load_json(path)
            except (OSError, ValueError):
                continue
            if isinstance(data, dict) and non_qa_report_status(data):
                continue
        state[rel] = entry
    return state


def attempt_evidence(before: dict, after: dict, binding: str | None, ran: bool = True) -> dict:
    """What one attempt of a QA node proved about its own report.

    `produced` is what this attempt wrote a new verdict into: an artifact whose content
    changed while it ran. A write time is not proof of execution — a `touch` inside the
    attempt window moves it without any QA report being generated — so it never admits
    anything on its own.

    That leaves one case the driver genuinely cannot decide from outside: content that
    did not change while something did write the file. A node that re-ran and reached the
    same verdict looks exactly like a file nobody produced. Rather than guess either way,
    the attempt records it as `ambiguous`: the repair route stays shut, and the run
    diagnoses it. A QA node that must be able to repeat a verdict makes its report say
    which attempt produced it — an attempt or run identifier changes the bytes, so the
    same finding twice is still two distinct verdicts.

    `binding` is the input snapshot the node was observed against, recorded only when it
    was the same snapshot at the start and the end of the attempt. A binding published
    afterwards, or a source changed and re-observed mid-attempt, leaves it null and the
    report unusable for automatic repair.

    `ran` is whether the executor completed the attempt at all. An environment failure, a
    timeout, or a worker that never started can still leave files behind; none of that is
    an attempt that produced anything.
    """
    produced = {rel: entry["digest"] for rel, entry in after.items()
                if (before.get(rel) or {}).get("digest") != entry["digest"]}
    ambiguous = sorted(rel for rel, entry in after.items()
                       if rel not in produced
                       and (before.get(rel) or {}).get("written") != entry["written"])
    evidence = {"binding": binding, "ran": bool(ran), "produced": produced}
    if ambiguous:
        evidence["ambiguous"] = ambiguous
    return evidence


def declared_qa_nodes(project_root: Path) -> set[str]:
    """Node ids the readiness spec names as QA sources of a declared repair loop."""
    return {qa for loop in declared_repair_loops(project_root)
            for qa in loop_nodes(loop, "qa_node_ids", "qa_nodes")}


def declared_repair_nodes(project_root: Path) -> set[str]:
    """Node ids the readiness spec names as repair targets of a declared loop."""
    return {str(loop["repair_node_id"]) for loop in declared_repair_loops(project_root)}


def repair_delivered(entry: dict) -> bool:
    """Did this repair transition deliver the work the QA node must now re-verify?

    A completed transition obviously did. So did an attempt that ran, was bound to an
    observed input snapshot, and wrote new content into the repair node's declared exit
    artifacts but could not be recorded completed — and that is not an edge case: a
    declared repair node is `hard_blocked_by` the QA node it repairs, so while that QA
    node is failing its own evidence is stale, and the freshness gate refuses the repair
    node by construction. Waiting for the repair node to complete first would invert the
    loop and hang it.

    Everything else is not a delivery: a pre-existing or merely touched artifact, an
    executor that failed to run, a report saying the node was blocked or hit an
    environment error, and an attempt whose inputs were not bound.

    Nothing is waived by counting this. The transition stays `failed`, the node stays
    incomplete, the attempt still spends a budgeted attempt, and the QA rerun — not
    this record — is what decides whether the repair worked. Once that rerun passes,
    the repair node is dispatched again as an ordinary node, publishes its evidence
    with its upstream now valid, and completes on its own merits.
    """
    if entry.get("status") == "completed":
        return True
    evidence = entry.get("qa_evidence")
    if not isinstance(evidence, dict):
        return False
    # An attempt that did not run, ran against no observed input snapshot, or wrote
    # nothing new delivered nothing — a pre-existing or touched artifact least of all.
    return bool(evidence.get("ran") is True and evidence.get("binding")
                and evidence.get("produced"))


def _epoch(timestamp: str | None) -> float | None:
    if not isinstance(timestamp, str) or not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp).timestamp()
    except ValueError:
        return None


def node_freshness(project_root: Path, node_id: str):
    """The freshness state the independent artifact gate computes for a node.

    Returns the freshness object, None when the project runs no freshness system at
    all, or False when the gate cannot be read — which admits nothing.
    """
    payload = artifact_gate_payload(project_root, node_id)
    if payload is None:
        return False
    return payload.get("freshness")


# Drift a failed QA node cannot avoid: it never publishes its evidence, and its
# outputs are exactly what failed. Every other key names an input that moved after
# the report was observed.
NON_INPUT_DRIFT = {"documents", "evidence", "outputs"}


def qa_inputs_current(freshness) -> bool:
    """True when the QA report is proven bound to the node's current inputs.

    Completion is not what this decides. A legacy node still completes exactly as it
    always did, on the pre-freshness gate. Automatic repair is different in kind: it is
    work this run starts, unattended, on the strength of a report — so the report has to
    carry proof, and absence of proof is not permission to act. A project with no
    freshness state, or a node that claims no provenance, has nothing tying its report to
    any input; it is re-run, and repeated failure is diagnosed under the recorded Run
    Policy, which is the same route any unrepairable QA failure takes. Declaring the
    node's `source_inputs` and observing it once restores the route — see "Recovering a
    legacy node's repair route" in the orchestrator template.

    `status: valid` is the wrong test for a failed QA node — that field tracks published
    evidence, which a failing node has none of, so it would refuse every repair the loop
    exists for. `readiness_status` is the contract-level answer: the node's most recent
    binding still matches its inputs, with no file, requirement, contract, baseline or
    upstream drift and no external change still undecided.

    Touching a report does not create that binding, but neither does the binding alone make
    an old report current: when the inputs never moved, or were observed after the fact,
    this predicate is satisfied and says nothing about which attempt wrote the file. That is
    what the attempt evidence in `qa_report_usable` decides; this decides only whether the
    inputs still stand.
    """
    if not isinstance(freshness, dict):
        return False                      # no freshness state, or an unreadable gate
    if freshness.get("external") in {"conflict", "unverified"}:
        return False
    if freshness.get("admission") != "declared":
        return False                      # legacy, missing or malformed: impact unknown
    # `readiness_status`, not `status`: `status` answers whether the node's *evidence* is
    # current, which a failed QA node can never make true — it has no passing delivery to
    # publish. `readiness_status` answers whether the node's most recent binding, contract
    # preferred, still matches the inputs, which is the question here. A node that once
    # published passing evidence and whose inputs have since moved recovers by observing
    # its contract against the new inputs; the stale evidence must not deny it forever.
    return freshness.get("readiness_status") == "valid"


def qa_verdict(data: dict) -> str | None:
    """The field stating a QA verdict this node actually reached, if any.

    A verdict is a failing outcome the node itself produced, or a non-empty list of
    gaps or findings. An empty document, empty arrays, or a report that states no
    outcome carry nothing for a repair node to act on.
    """
    for field in STATUS_FIELDS:
        value = data.get(field)
        if not isinstance(value, str):
            continue
        lowered = value.lower()
        if (lowered in BLOCKING_STATUS_VALUES and lowered not in NON_QA_REPORT_STATUSES
                and not lowered.startswith("blocked_by_")):
            return f"{field}={value}"
    for field in PRODUCTION_GAP_FIELDS:
        value = data.get(field)
        if isinstance(value, (list, dict)) and value:
            return f"{field} lists unresolved findings"
    return None


def non_qa_report_status(data: dict) -> str | None:
    """The report field that says this failure carries no QA verdict, if any."""
    for field in STATUS_FIELDS:
        value = data.get(field)
        if not isinstance(value, str):
            continue
        lowered = value.lower()
        if lowered in NON_QA_REPORT_STATUSES or lowered.startswith("blocked_by_"):
            return f"{field}={value}"
    return None


def qa_report_usable(project_root: Path, node: dict, workflow: dict) -> bool:
    """A failed QA node routes to repair only on its own current verdict.

    Existence and parseability are not proof of a current report, and neither is a
    recent mtime — `touch` moves that without producing anything. Four things must hold
    together:

    - this run recorded a **failed attempt** of the node, as its latest transition;
    - that attempt **produced** the report: the driver recorded which exit artifacts were
      written while it ran, and those bytes are still what is on disk;
    - the attempt ran against **one identified input snapshot**, unchanged from its start
      to its end, and that is still the snapshot bound now — a binding published
      afterwards, or a source changed and re-observed mid-attempt, cannot launder a
      historical report into a current one — with no drift since;
    - the report **positively states a QA verdict**, rather than an empty document, an
      empty gap list, or an environment, authority or never-ran failure.

    Anything short of all four is re-run or diagnosed, never repaired against a report
    nobody produced this run.
    """
    artifacts = node.get("exit_artifacts") or []
    if not artifacts:
        return False
    node_id = node_identity(node)
    # No failed attempt on record means no verdict this run produced, whatever a
    # leftover file on disk says.
    entry = last_failed_transition(workflow, node_id)
    if entry is None:
        return False
    dispatched_at = _epoch(entry.get("started_at"))
    if dispatched_at is None:
        return False
    evidence = entry.get("qa_evidence")
    if not isinstance(evidence, dict):
        return False
    binding = evidence.get("binding")
    # The attempt must have run against an input snapshot, and admission must be looking
    # at that same snapshot — not merely at another one that also happens to be current.
    if not binding or binding != binding_identity(project_root, node_id):
        return False
    produced = evidence.get("produced")
    if not isinstance(produced, dict) or not produced:
        return False        # the attempt changed nothing: it produced no verdict
    for rel, digest in produced.items():
        if file_digest(project_root / rel) != digest:
            return False    # edited or replaced since the attempt that produced it
    verdict = False
    for item in artifacts:
        rel = artifact_path(item)
        path = project_root / rel
        if not path.exists():
            return False
        # One second of slack: transition timestamps are second-resolution while
        # filesystem mtimes are not.
        if path.stat().st_mtime + 1 < dispatched_at:
            return False
        if path.suffix != ".json":
            continue
        try:
            data = load_json(path)
        except (OSError, ValueError):
            return False
        if not isinstance(data, dict):
            continue
        if non_qa_report_status(data):
            return False
        # The verdict has to come from something this attempt wrote.
        verdict = verdict or (rel in produced and bool(qa_verdict(data)))
    if not verdict:
        return False
    # Last, because it costs a helper process: the recorded evidence says the inputs
    # were bound when the attempt ran; this says they have not moved since.
    return qa_inputs_current(node_freshness(project_root, node_id))


def open_repair_loops(project_root: Path, workflow: dict, complete: dict[str, bool]) -> dict[str, dict]:
    """QA nodes currently routed to their declared repair node, keyed by QA node id."""
    nodes = {node_identity(n): n for n in workflow.get("nodes", [])}
    routed: dict[str, dict] = {}
    if safety_halted(project_root):
        # A safety halt is not an ordinary QA failure and a repair is not its answer.
        # Routing one would dispatch new work over quarantined outputs.
        return routed
    for loop in declared_repair_loops(project_root):
        repair_node_id = str(loop["repair_node_id"])
        if repair_node_id not in nodes:
            continue
        budget = repair_budget(loop)
        if budget is None:
            continue
        for qa_node_id in loop_nodes(loop, "qa_node_ids", "qa_nodes"):
            qa_node = nodes.get(qa_node_id)
            if qa_node is None or complete.get(qa_node_id):
                continue
            spent, answered = repair_progress(project_root, workflow, repair_node_id, qa_node_id)
            # A delivered repair is answered by the QA rerun, never by another repair, and
            # an unknown spend routes nothing rather than guessing an attempt is left.
            if answered or spent is None or spent >= budget:
                continue
            if qa_report_usable(project_root, qa_node, workflow):
                routed[qa_node_id] = loop
    return routed


def exhausted_obligation_pairs(project_root: Path, workflow: dict) -> list[tuple[str, str]]:
    """(repair node, QA node) for every obligation whose declared budget is spent.

    A QA node whose budget is spent has no repair attempt left. Running it again would
    reproduce the same failure with nothing able to fix it, and finishing the run around
    it would accept an obligation that was never satisfied. It is blocked and reported —
    an exhausted obligation is refused, never accepted (ADR 0005).

    What satisfies it is its own QA attempt, and only the attempt this driver recorded
    says whether that happened. A ready exit artifact does not: the exit artifact of a QA
    node is a file, and a node dispatched in some other role can write it. So an
    obligation whose latest recorded attempt failed stays exhausted however ready its
    report now looks. A repair that has already delivered is not exhausted either: its QA
    rerun is what judges that delivery, and the rerun is not another repair attempt.
    """
    pairs: list[tuple[str, str]] = []
    for loop in declared_repair_loops(project_root):
        budget = repair_budget(loop)
        if budget is None:
            continue
        repair_node_id = str(loop["repair_node_id"])
        for qa_node_id in loop_nodes(loop, "qa_node_ids", "qa_nodes"):
            if last_failed_transition(workflow, qa_node_id) is None:
                continue
            spent, answered = repair_progress(project_root, workflow, repair_node_id, qa_node_id)
            if not answered and spent is not None and spent >= budget:
                pairs.append((repair_node_id, qa_node_id))
    return pairs


def exhausted_obligations(project_root: Path, workflow: dict) -> list[str]:
    """QA node ids whose declared repair budget is spent and whose last attempt failed."""
    return sorted({qa_node_id for _, qa_node_id in
                   exhausted_obligation_pairs(project_root, workflow)})


def _pending_state(project_root: Path, workflow: dict) -> tuple[dict | None, list[str]]:
    """(next dispatchable node, ids of pending nodes nothing may dispatch yet)."""
    nodes = workflow.get("nodes", [])
    if safety_halted(project_root):
        # Run-wide, not branch-wide: a recorded halt stops new dispatch for every pending
        # node, including branches that never failed, until the quarantined outputs are
        # independently revalidated.
        return None, [node_identity(n) for n in nodes]
    if repair_ledger_unreadable(project_root, workflow):
        # The spent budget cannot be read, so nothing may run: dispatching now could
        # re-grant an attempt whose work is already in the tree.
        return None, [node_identity(n) for n in nodes]
    if declared_repair_loops(project_root) and unresolved_authorizations(project_root):
        # An authorization with no recorded outcome is uncertain execution, not a QA
        # verdict. Its work may already be in the tree, so no branch may proceed on the
        # assumption that it is not — the refusal is global and it is refused before the
        # first dispatch, not when the affected repair node comes up.
        return None, [node_identity(n) for n in nodes]
    complete = {node_identity(n): independent_artifact_gate(project_root, node_identity(n)) for n in nodes}
    routed = open_repair_loops(project_root, workflow, complete)
    repair_nodes = {str(loop["repair_node_id"]) for loop in routed.values()}
    # Closure waits for its QA node itself, never for the repair alone: only a
    # passing rerun releases it.
    closure_blocked = {
        closure
        for loop in declared_repair_loops(project_root)
        for closure in loop_nodes(loop, "closure_node_ids", "closure_nodes")
        if any(not complete.get(qa) for qa in loop_nodes(loop, "qa_node_ids", "qa_nodes"))
    }
    # A QA node that has already failed under a loop whose declared budget is unusable has
    # no repair route and nothing to gain from running again: it is blocked, and the run
    # reports it rather than looping on a planning error.
    unbounded = {
        qa_node_id
        for loop in declared_repair_loops(project_root)
        if repair_budget(loop) is None
        for qa_node_id in loop_nodes(loop, "qa_node_ids", "qa_nodes")
        if last_failed_transition(workflow, qa_node_id) is not None
    }
    # An obligation whose declared budget is spent is blocked and reported, whatever its
    # report now looks like — see `exhausted_obligation_pairs`.
    spent_out = exhausted_obligation_pairs(project_root, workflow)
    exhausted = {qa_node_id for _, qa_node_id in spent_out}
    dead_loop_repairs = {repair_node_id for repair_node_id, _ in spent_out}
    # A repair node whose only obligations are exhausted has nothing left to be authorized
    # for. Dispatching it as an ordinary pending node would run a repair attempt the
    # budget never paid for, so it is blocked too. One still routed for an obligation that
    # has budget keeps running for that obligation alone (ADR 0005).
    dead_loop_repairs -= repair_nodes
    blocked: list[str] = []
    selected: dict | None = None
    for node in nodes:
        node_id = node_identity(node)
        # A node's blockers hold in every role it plays. Reaching the repair role first
        # would let a dispatch authorized for one loop write this node's own QA verdict
        # and discharge an obligation of another: success in one role never cancels
        # another role's blocker (ADR 0006).
        if node_id in exhausted:
            blocked.append(node_id)
            continue
        if not complete.get(node_id) and (node_id in routed or node_id in closure_blocked
                                          or node_id in unbounded
                                          or node_id in dead_loop_repairs):
            blocked.append(node_id)
            continue
        if node_id in repair_nodes:
            if selected is None:
                selected = node
            continue
        if complete.get(node_id):
            continue
        dependencies = node.get("hard_blocked_by") or []
        dispatchable = all(
            complete.get(dependency)
            or str((routed.get(dependency) or {}).get("repair_node_id") or "") == node_id
            for dependency in dependencies
        )
        if not dispatchable:
            blocked.append(node_id)
            continue
        if selected is None:
            selected = node
    return selected, blocked


def first_pending_node(project_root: Path, workflow: dict) -> dict | None:
    return _pending_state(project_root, workflow)[0]


def blocked_pending_nodes(project_root: Path, workflow: dict) -> list[str]:
    return _pending_state(project_root, workflow)[1]


def _keep_last_transition(transition_log: list, node_id: str, entry: dict) -> None:
    """Make the driver's entry this node's latest transition, dropping any behind it.

    Admission reads the node's latest transition, and only the driver observed the
    attempt that entry describes. A worker that appends its own — a second entry, or one
    carrying `qa_evidence` it invented — must not be able to put it there.
    """
    position = next(index for index, item in enumerate(transition_log) if item is entry)
    transition_log[:] = [
        item for index, item in enumerate(transition_log)
        if item is entry or index < position or item.get("node") != node_id
    ]


def append_transition_if_missing(
    workflow_path: Path,
    before_count: int,
    node_id: str,
    status: str,
    started_at: str,
    artifacts_created: list[str],
    error: str | None = None,
    qa_evidence: dict | None = None,
) -> None:
    workflow = load_json(workflow_path)
    transition_log = workflow.setdefault("transition_log", [])
    # The supervisor owns the verdict; a worker's self-reported completion cannot
    # conceal a failed gate or prevent the consecutive-failure stop condition. It also
    # cannot leave a second entry of its own behind this one, or write its own
    # qa_evidence: admission reads the node's latest transition, and only the driver
    # observed the attempt it describes.
    mine = [entry for entry in transition_log[before_count:] if entry.get("node") == node_id]
    if mine:
        entry = mine[0]
        entry.update(status=status, completed_at=now_iso(), artifacts_created=artifacts_created)
        if error:
            entry["error"] = error
        else:
            entry.pop("error", None)
        if qa_evidence is None:
            entry.pop("qa_evidence", None)
        else:
            entry["qa_evidence"] = qa_evidence
        _keep_last_transition(transition_log, node_id, entry)
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
    if qa_evidence is not None:
        entry["qa_evidence"] = qa_evidence
    transition_log.append(entry)
    _keep_last_transition(transition_log, node_id, entry)
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


def loop_budgets_for(project_root: Path, node_id: str) -> list[int]:
    """Declared per-QA budgets of every loop this node takes part in."""
    budgets = []
    for loop in declared_repair_loops(project_root):
        members = {str(loop["repair_node_id"]), *loop_nodes(loop, "qa_node_ids", "qa_nodes")}
        if node_id not in members:
            continue
        budget = repair_budget(loop)
        if budget is not None:
            budgets.append(budget)
    return budgets


def failure_threshold(project_root: Path, node_id: str) -> int:
    """Consecutive failures this node may record before the supervisor stops the run.

    The generic cap is a backstop for a node nobody planned a bound for. It must never
    be the thing that ends a declared loop: a plan that authorized `max_attempts`
    repairs authorized the failures that go with them, and stopping at the smaller
    generic number would silently curtail an explicit per-QA budget while reporting a
    supervisor threshold instead of an exhausted one. The bound stays finite either
    way — it is the declared budget, plus the failure that opened the loop.
    """
    budgets = loop_budgets_for(project_root, node_id)
    return max([MAX_CONSECUTIVE_FAILURES_PER_NODE] + [budget + 1 for budget in budgets])


def stagnation_limit(project_root: Path) -> int:
    """Transitions without new artifacts allowed before the run is called stagnant.

    A declared loop legitimately produces them: a repair that delivers nothing and the
    QA rerun that judges it both record a transition and neither writes an artifact —
    two per authorized attempt, plus the QA failure that opened the loop. Below that,
    the generic guard would end the loop before its declared budget was spent.
    """
    budgets = [budget for loop in declared_repair_loops(project_root)
               for budget in [repair_budget(loop)] if budget is not None]
    return max([MAX_STAGNANT_ITERATIONS] + [2 * budget + 1 for budget in budgets])


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


def run_bounded(command: list[str], project_root: Path, timeout: int,
                stdin_text: str | None = None) -> subprocess.CompletedProcess[str]:
    """Bound the whole subprocess group, including children of CLI/helper processes."""
    try:
        proc = subprocess.Popen(command, cwd=project_root, text=True,
                                stdin=subprocess.PIPE if stdin_text is not None else None,
                                stdout=subprocess.PIPE,
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
        out, err = proc.communicate(input=stdin_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        stop()
        out, err = proc.communicate()
        return subprocess.CompletedProcess(command, 124, out, err + f"\nTimed out after {timeout}s")
    except KeyboardInterrupt:
        stop()
        out, err = proc.communicate()
        return subprocess.CompletedProcess(command, 130, out, err + "\nInterrupted by user")
    return subprocess.CompletedProcess(command, proc.returncode, out, err)


def run_script(project_root: Path, name: str, args: list[str],
               stdin_text: str | None = None) -> subprocess.CompletedProcess[str] | None:
    path = script_path(project_root, name)
    if not path.exists():
        return None
    return run_bounded([sys.executable, str(path), *args], project_root,
                       execution_policy(project_root)["helper_timeout_seconds"], stdin_text)


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


def artifact_gate_payload(project_root: Path, node_id: str) -> dict | None:
    """The independent artifact gate's JSON for one node; None when it cannot be read.

    One reader for one checker run: the gate takes its verdict from it, repair
    admission takes the freshness state from it.
    """
    result = run_script(
        project_root,
        "check_artifacts.py",
        [str(project_root / ".allforai/bootstrap/workflow.json"), "--node", node_id, "--json"],
    )
    if result is None or result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        payload = json.loads(result.stdout)
    except Exception:
        return None
    if not isinstance(payload, dict) or payload.get("node_id") != node_id:
        return None
    return payload


def independent_artifact_gate(project_root: Path, node_id: str) -> bool:
    payload = artifact_gate_payload(project_root, node_id)
    return bool(payload and payload.get("all_exist") is True
                and isinstance(payload.get("artifacts"), list) and payload["artifacts"])


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


ACCEPTANCE_REPORT = ".allforai/concept-acceptance/acceptance-report.json"
# What a scored acceptance report carried before ADR 0008. The coverage gate renders none
# of them: a report that still does is not this gate's output, whatever list it also holds.
ACCEPTANCE_SCORE_FIELDS = ("verdict", "overall_score", "pass_threshold", "dimensions")


def acceptance_gate(project_root: Path) -> tuple[list, str | None]:
    """(behaviour mappings the coverage gate named as missing, why the report is not the gate's).

    concept-acceptance answers one machine-decidable question: does every behaviour
    mapping in the concept have evidence, or is it named as missing (ADR 0008). Its report
    is read for that list only. No report is a gate that has not run — an empty list and
    no refusal. A report with no readable list, or one that still carries a score,
    threshold or verdict, is refused by name rather than read as either answer.
    """
    report = project_root / ACCEPTANCE_REPORT
    if not report.exists():
        return [], None
    try:
        data = load_json(report)
    except (ValueError, OSError):
        return [], f"{ACCEPTANCE_REPORT} is unreadable"
    if not isinstance(data, dict):
        return [], f"{ACCEPTANCE_REPORT} is not a report document"
    scored = [field for field in ACCEPTANCE_SCORE_FIELDS if field in data]
    if scored:
        return [], (f"{ACCEPTANCE_REPORT} carries {', '.join(scored)}; the coverage gate names "
                    "missing behaviour mappings and renders no score, threshold or verdict")
    missing = data.get("missing_mappings")
    if not isinstance(missing, list):
        return [], (f"{ACCEPTANCE_REPORT} names no missing_mappings list; the gate produced "
                    "no decidable output")
    return missing, None


def acceptance_gate_node(workflow: dict) -> str | None:
    """The node whose exit artifact is the coverage gate's report, when the plan has one."""
    for node in workflow.get("nodes", []):
        if any(artifact_path(a) == ACCEPTANCE_REPORT for a in node.get("exit_artifacts", [])):
            return node_identity(node)
    return None


def acceptance_gate_loop(project_root: Path, gate_node: str | None) -> dict | None:
    """The declared repair loop that names the gate as one of its QA obligations."""
    if not gate_node:
        return None
    return next((loop for loop in declared_repair_loops(project_root)
                 if gate_node in loop_nodes(loop, "qa_node_ids", "qa_nodes")), None)


def acceptance_requires_iteration(project_root: Path) -> bool:
    missing, refused = acceptance_gate(project_root)
    if missing or refused:
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


FINALIZE_EVIDENCE_NOTE = """
FINALIZATION ONLY. This node already delivered its exit artifacts, and the QA node it
repairs has since passed against the current source. Do NOT modify any source file and do
NOT redo the repair: doing so would invalidate the verification that just passed. Observe
and publish this node's evidence for the delivery already on disk, then stop. If that
delivery no longer satisfies the node, write a failed transition naming the blocker rather
than changing sources.
"""


def build_prompt(node_id: str, goal: str, finalize_evidence: bool = False) -> str:
    if finalize_evidence:
        return f"""Continue the generated workflow autonomously.

Selected node: {node_id}
User goal: {goal}
{FINALIZE_EVIDENCE_NOTE}
Do not ask for acceptance. Execute the work directly."""
    return f"""Continue the generated workflow autonomously.

Selected node: {node_id}
User goal: {goal}

Requirements:
1. Read `.allforai/bootstrap/workflow.json`.
2. Read `.allforai/bootstrap/node-specs/{node_id}.md`.
3. Complete exactly this node end-to-end. Do not stop after planning.
4. Create or update any project files required to satisfy the node's exit artifacts.
5. Append a `transition_log` entry to `.allforai/bootstrap/workflow.json` with `completed` or `failed`.
6. Do not write `completed` when any exit artifact says `conditional_pass`, `partial`, `accepted_with_gaps`, `accepted_with_warnings`, `passed_with_warnings`, `blocked_by_*`, or contains unresolved `gaps`, `code_gaps`, `asset_gaps`, `audio_gaps`, `remaining_gaps`, `blockers`, `major_findings`, `unresolved_findings`, or `missing_mappings`. Continue repairing and rerunning validation inside this node when it owns the fix; otherwise write `failed` with the exact blocker and repair owner.
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


def handle_iteration(project_root: Path, workflow: dict) -> int | None:
    """Apply the recorded on_needs_iteration policy to the gate's missing-mapping list.

    Returns the driver's exit code, or None when the gate's declared repair may now be
    dispatched — through the same ledger-authorized route as any other QA finding, never
    around it (ADR 0005, ADR 0006). `auto_fix_once` grants that route once: a gate whose
    obligation the ledger already shows charged halts with its report, and one that no
    loop declares a repair for, or whose budget is spent or unknown, halts as an
    unauthorized repair. Nothing here dispatches an executor of its own.
    """
    missing, refused = acceptance_gate(project_root)
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
    named = "\n".join(f"- {json.dumps(item, ensure_ascii=False)}" for item in missing)
    report.write_text(
        (f"Concept acceptance refused: {refused}\n" if refused
         else f"Behaviour mappings without evidence:\n{named}\n")
        + "At the next interactive entry choose fix, re-bootstrap, or accept; execution asks no new questions.\n")
    if action != "auto_fix_once":
        return 5
    if refused:
        print(json.dumps({"passed": False, "done": False, "error": refused}), file=sys.stderr)
        return 6
    gate_node = acceptance_gate_node(workflow)
    loop = acceptance_gate_loop(project_root, gate_node)
    if loop is None:
        print(json.dumps({
            "passed": False, "done": False,
            "error": "no declared repair loop names the concept-acceptance gate; a missing-mapping "
                     "repair nobody authorized does not run",
            "missing_mappings": missing}), file=sys.stderr)
        return 6
    repair_node_id = str(loop["repair_node_id"])
    budget = repair_budget(loop)
    spent, answered = repair_progress(project_root, workflow, repair_node_id, gate_node)
    if answered:
        return None       # the repair delivered; the gate's rerun is what judges it
    if spent is None or budget is None or spent >= budget:
        print(json.dumps({
            "passed": False, "done": False,
            "error": "the concept-acceptance repair budget is spent or its accounting is unknown; "
                     "nothing further is charged and no unpaid attempt runs",
            "obligation": gate_node, "repair_node_id": repair_node_id,
            "spent": spent, "budget": budget}), file=sys.stderr)
        return 6
    if spent >= 1:
        return 5          # the one recorded repair already ran; the gate still names mappings
    return None


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
        if safety_halted(project_root):
            print(json.dumps({"passed": False, "done": False,
                              "error": "a run-wide safety halt is recorded; no node may be dispatched "
                                       "until the quarantined outputs are independently revalidated",
                              "quarantine": SAFETY_QUARANTINE}), file=sys.stderr)
            return 4
        warnings = read_safety_warnings(project_root)
        if warnings is None:
            print(json.dumps({"passed": False, "done": False, "error": "invalid safety warning report"}), file=sys.stderr)
            return 6
        if safety_halt_required(project_root, warnings):
            print(json.dumps({"passed": False, "done": False, "error": "recorded Run Policy halted on safety warning", "warnings": warnings}), file=sys.stderr)
            return 4
        workflow = load_json(workflow_path)
        if not run_expanders(project_root, workflow):
            print(json.dumps({"passed": False, "done": False, "error": "workflow expander failed"}), file=sys.stderr)
            return 6
        workflow = load_json(workflow_path)
        node = first_pending_node(project_root, workflow)
        if node is None:
            blocked = blocked_pending_nodes(project_root, workflow)
            if blocked:
                payload = {"passed": False, "done": False,
                           "error": "no dispatchable node; pending nodes remain blocked",
                           "blocked_nodes": blocked}
                if repair_ledger_unreadable(project_root, workflow):
                    payload["invalid_repair_attempt_history"] = (
                        f"{REPAIR_LEDGER} is not a trustworthy per-obligation budget ledger; "
                        "recover it with the repair-authorization helper before resuming")
                unbounded = unbounded_repair_loops(project_root)
                if unbounded:
                    # Name the planning error rather than leaving a bare blocked list: a
                    # declared loop with an unusable `max_attempts` is why its failed QA
                    # node has no route.
                    payload["unbounded_repair_loops"] = unbounded
                # Two different stops, never one list. An exhausted obligation is a QA
                # verdict this run recorded and a budget the plan declared: the evidence
                # is complete and the answer is that it was never satisfied. An
                # unresolved authorization is the opposite — an execution nobody watched
                # end, which is recovered by reconciling evidence, not by more QA.
                exhausted = exhausted_obligations(project_root, workflow)
                if exhausted:
                    payload["exhausted_obligations"] = exhausted
                unresolved = unresolved_authorizations(project_root)
                if unresolved:
                    payload["unresolved_repair_authorizations"] = unresolved
                    payload["uncertain_execution"] = (
                        "an authorization has no recorded outcome, so whether its repair "
                        "ran is unknown; the whole run is refused until it is reconciled "
                        "against attributable evidence — this is not a QA failure")
                print(json.dumps(payload), file=sys.stderr)
                return 6
        # The coverage gate's policy is applied whenever the gate, its declared repair node
        # or the run's end comes up: the declared loop would otherwise route the gate's
        # failure past a recorded halt_with_report, and a routed repair must still be the
        # one the policy grants.
        gate_node = acceptance_gate_node(workflow)
        gate_loop = acceptance_gate_loop(project_root, gate_node)
        pending = node_identity(node) if node is not None else None
        acceptance_node = pending is None or pending == gate_node or (
            gate_loop is not None and pending == str(gate_loop["repair_node_id"]))
        if acceptance_node and acceptance_requires_iteration(project_root):
            outcome = handle_iteration(project_root, workflow)
            if outcome is not None:
                accepted = outcome == 0 and load_json(
                    project_root / ".allforai/bootstrap/run-policy.json")["on_needs_iteration"] == "accept"
                print(
                    json.dumps(
                        {
                            "passed": False,
                            "done": False,
                            "run_policy_outcome": "accepted_with_gaps" if accepted else "iteration halted with report",
                        },
                        indent=2,
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
                return outcome
            # The gate's one recorded repair is dispatched below like any other QA finding:
            # the declared repair node runs under a ledger grant, or nothing runs.
        if node is None:
            if not workflow.get("nodes") or not run_post_checks(project_root):
                print(json.dumps({"passed": False, "done": False, "error": "final validation failed"}), file=sys.stderr)
                return 6
            print(json.dumps({"passed": True, "done": True, "iterations": iteration - 1}, indent=2, ensure_ascii=False))
            return 0

        node_id = str(node.get("node_id") or node.get("id"))
        failure_count = count_consecutive_failures(workflow, node_id)
        threshold = failure_threshold(project_root, node_id)
        if failure_count >= threshold:
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
                f"Repeated node failure reached threshold {threshold}.",
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

        stagnation_cap = stagnation_limit(project_root)
        if stagnant_iteration_count(workflow) >= stagnation_cap:
            print(
                json.dumps(
                    {
                        "passed": False,
                        "done": False,
                        "error": f"stagnant workflow: {stagnation_cap} consecutive transitions without new artifacts",
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 4

        before_count = len(workflow.get("transition_log", []))
        started_at = now_iso()
        # A declared QA node's failure may open an automatic repair, so this attempt has
        # to leave proof of what it actually produced and of whether its inputs were
        # bound while it ran. Observed before the node runs; a binding published after
        # the fact proves nothing about what this attempt read.
        is_qa_node = node_id in declared_qa_nodes(project_root)
        # A declared repair node's attempt is recorded the same way: the loop advances on
        # what the attempt produced, and a repair that cannot complete while its QA node
        # is failing still has to be distinguishable from one that ran and wrote nothing.
        is_loop_node = is_qa_node or node_id in declared_repair_nodes(project_root)
        finalize_evidence = (not is_qa_node and is_loop_node
                             and repair_awaiting_finalization(project_root, workflow, node_id))
        reports_before = deliverable_state(project_root, node) if is_loop_node else {}
        binding_before = binding_identity(project_root, node_id) if is_loop_node else None
        if binding_before is not None and not qa_inputs_current(node_freshness(project_root, node_id)):
            binding_before = None      # already drifted before the attempt began
        # Write-ahead repair accounting through the canonical ledger: dispatching a
        # declared repair node charges one of each answered QA obligation's declared
        # attempts and then claims the single execution that charge pays for, both durable
        # before the executor starts. Charging on delivery instead would leave a repair
        # that errors or writes nothing costing nothing, which bounds neither host.
        routed_obligations = qa_nodes_routed_to(project_root, workflow, node_id)
        grant = None
        if routed_obligations:
            grant = authorize_repair_dispatch(project_root, workflow, node_id, routed_obligations)
            if grant is None:
                # No durable grant, so no execution. An exhausted budget, an unresolved
                # earlier grant, or unknown accounting all land here, and each is a stop
                # rather than an unpaid attempt.
                print(json.dumps({
                    "passed": False, "done": False, "node": node_id,
                    "error": "repair dispatch was not authorized; no attempt may run without a "
                             "durable per-obligation grant",
                    "obligations": routed_obligations}), file=sys.stderr)
                return 6
        result = run_codex(project_root, build_prompt(node_id, goal, finalize_evidence))
        # Read before anything this attempt produced can be accepted. Answering a warning
        # on the next iteration would be too late: this node would already be recorded
        # completed and would already have released its successors. Codex cannot cancel an
        # executor that has finished, so its outputs are quarantined rather than accepted,
        # and the halt is run-wide — every branch stops, not only this one.
        post_warnings = read_safety_warnings(project_root)
        if post_warnings is None or safety_halt_required(project_root, post_warnings):
            quarantined = [artifact_path(a) for a in node.get("exit_artifacts", [])
                           if (project_root / artifact_path(a)).exists()]
            persisted = quarantine_outputs(project_root, [node_id], SAFETY_HALT_REASON)
            append_transition_if_missing(
                workflow_path, before_count, node_id, "failed", started_at, quarantined,
                "run-wide safety halt: outputs quarantined pending independent revalidation")
            print(json.dumps({
                "passed": False, "done": False, "node": node_id,
                "error": ("invalid safety warning report" if post_warnings is None
                          else "recorded Run Policy halted on safety warning"),
                "warnings": post_warnings or [],
                "quarantined_outputs": quarantined,
                "quarantine_persisted": persisted,
                # Persistence of the canonical marker is reported, never assumed; the
                # fence is separate and is what stops the next start. Both are stated.
                "halt_fenced": safety_halted(project_root),
                # Left unresolved on purpose: the outputs are quarantined, so whether this
                # attempt delivered anything is not settled by the driver that halted it.
                "unresolved_repair_authorization": grant and grant["authorization_id"],
                "quarantine": SAFETY_QUARANTINE}), file=sys.stderr)
            return 6 if post_warnings is None else 4
        binding_after = binding_identity(project_root, node_id) if is_loop_node else None

        artifacts_created = [
            artifact_path(path)
            for path in node.get("exit_artifacts", [])
            if artifact_ready(project_root, artifact_path(path))
        ]
        gate_node_id = str(node.get("node_id") or node_id)
        all_ready = result.returncode == 0 and independent_artifact_gate(
            project_root, gate_node_id
        )

        # Settled before the attempt may be accepted. This driver watched the attempt
        # finish, so its end is recorded; settling returns no budget, because the attempt
        # was granted and is spent either way. An interrupted or timed-out attempt is
        # deliberately left unresolved — whether its execution occurred is a question for
        # `reconcile` and evidence that can be checked, never an assumption made here.
        # A settlement the ledger did not confirm is the same uncertainty: the node is not
        # completed on it, and the run stops for reconciliation rather than accepting work
        # whose authorization stays open.
        settlement_error = None
        if grant is not None and result.returncode not in {124, 130}:
            if not settle_repair_dispatch(project_root, grant,
                                          "delivered" if all_ready else "failed"):
                settlement_error = (
                    "repair attempt outcome was not recorded in the canonical ledger "
                    f"(authorization {grant['authorization_id']}); the attempt stays "
                    "unresolved and is reconciled against evidence, never assumed")
                all_ready = False

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
            qa_evidence = attempt_evidence(
                reports_before,
                deliverable_state(project_root, node),
                binding_before if binding_before == binding_after else None,
                result.returncode == 0,
            ) if is_loop_node else None
            if settlement_error:
                error_line = (settlement_error + "; " + error_line)[:600]
            if qa_evidence and qa_evidence.get("ambiguous"):
                # Neither a verdict this attempt produced nor a file it left alone.
                # Say so on the record instead of letting it pass or vanish.
                error_line = (error_line + "; unchanged QA report(s) rewritten without a new "
                              f"verdict: {', '.join(qa_evidence['ambiguous'])}; a repeated verdict "
                              "must carry the attempt that produced it")[:600]
            append_transition_if_missing(
                workflow_path,
                before_count,
                node_id,
                "failed",
                started_at,
                artifacts_created,
                error_line,
                qa_evidence,
            )

        if settlement_error:
            print(json.dumps({
                "passed": False, "done": False, "node": node_id,
                "error": settlement_error,
                "unresolved_repair_authorizations": [grant["authorization_id"]],
                "obligations": grant["obligations"]}), file=sys.stderr)
            return 6

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
