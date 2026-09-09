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
    the plan never authorized, so such a loop routes nothing.
    `validate_unattended_readiness.py` blocks the same shape before the run starts.
    """
    if "max_attempts" not in loop:
        return DEFAULT_REPAIR_ATTEMPTS
    budget = loop.get("max_attempts")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
        return None
    return budget


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


def repair_progress(workflow: dict, repair_node_id: str, qa_node_id: str) -> tuple[int, bool]:
    """(attempts this QA node has spent, repair already delivered for its last failure).

    The declared budget is per QA node — one repair node may serve several — so an
    attempt is counted only for the QA node whose failure it answered. Both values
    come from the durable transition_log, so a restart resumes the same budget
    instead of handing out the spent attempts again.
    """
    delivered = 0
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
                delivered += 1
            answered = True
    return delivered, answered


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
            spent, answered = repair_progress(workflow, repair_node_id, qa_node_id)
            # A delivered repair is answered by the QA rerun, never by another repair.
            if answered or spent >= budget:
                continue
            if qa_report_usable(project_root, qa_node, workflow):
                routed[qa_node_id] = loop
    return routed


def _pending_state(project_root: Path, workflow: dict) -> tuple[dict | None, list[str]]:
    """(next dispatchable node, ids of pending nodes nothing may dispatch yet)."""
    nodes = workflow.get("nodes", [])
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
    blocked: list[str] = []
    selected: dict | None = None
    for node in nodes:
        node_id = node_identity(node)
        if node_id in repair_nodes:
            if selected is None:
                selected = node
            continue
        if complete.get(node_id):
            continue
        if node_id in routed or node_id in closure_blocked:
            blocked.append(node_id)
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
        if node is None:
            blocked = blocked_pending_nodes(project_root, workflow)
            if blocked:
                print(json.dumps({"passed": False, "done": False,
                                  "error": "no dispatchable node; pending nodes remain blocked",
                                  "blocked_nodes": blocked}), file=sys.stderr)
                return 6
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
        result = run_codex(project_root, build_prompt(node_id, goal, finalize_evidence))
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
