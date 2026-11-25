#!/usr/bin/env python3
"""Validate whether a generated workflow is ready for unattended /run."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from product_intent import validate_scope
from validate_bootstrap import (decision_coverage_disclosures, plan_confirmation_blockers,
                               structural_gate_blockers,
                               workflow_shape_blockers)


BLOCKING_STATUS = "not_ready"
READY_STATUS = "ready"

SAFETY_MARKER = "safety-quarantine.json"
SAFETY_LOCK = "safety-quarantine.lock"
LEDGER_LOCK = "repair-authorizations.lock"

# ADR-0008: the entries that judge a delivery from outside it. They follow the pipeline as
# steps the user types, listed in `workflow.json.user_steps`; a node named after one would
# put the author's own run in the examiner's seat.
VERDICT_ENTRIES = ("cross-exam", "product-review")


def _load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: dict) -> None:
    _publish(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _publish(path: Path, text: str) -> None:
    """Replace a published report, or leave nothing behind that could be read as one.

    The report on disk is a verdict about the current graph, and both hosts read it: a
    previous `ready` that survives this run is a stale verdict presented as a current
    one. So the new text replaces the old atomically where it can, falls back to writing
    the file in place when only the file is writable, and, when neither works, removes
    the superseded report rather than leaving it standing. If even that fails the caller
    still refuses the run — a non-zero exit is the guarantee that does not depend on the
    filesystem — but nothing here silently preserves an obsolete verdict.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    try:
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, path)
        return
    except OSError:
        try:
            temp.unlink()
        except OSError:
            pass
    try:
        path.write_text(text, encoding="utf-8")
        return
    except OSError as exc:
        published = exc
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass
    raise published


def _artifact_path(item) -> str:
    if isinstance(item, dict):
        return item.get("path", "")
    return str(item)


def _node_id(node: dict) -> str:
    """The identifier this node is reported under.

    Only a node the graph can address reaches the per-node checks below; the placeholder
    keeps a report readable if one ever arrives by another route, and never becomes a
    real identifier that could match a spec file or a blocker.
    """
    if not isinstance(node, dict):
        return "<missing-node-id>"
    node_id = node.get("node_id")
    return node_id if isinstance(node_id, str) and node_id.strip() else "<missing-node-id>"


# What a person does about each blocker, in one line. The message says what is wrong;
# this says how to clear it. Every code this gate emits has one (tested).
BLOCKER_ACTIONS: dict[str, str] = {
    "closure_not_blocked_by_repair_loop": "Rerun the interactive `/bootstrap`; the closure node must wait for its repair node.",
    "dependency_outside_graph": "At the interactive `/bootstrap`, declare the dependency in hard_blocked_by or remove the stale read from observed-input-dependencies.json.",
    "external_change_repair_pending": "Restore the confirmed behaviour in the named files (or let `/bootstrap` plan the repair), then rerun `/run`.",
    "forbidden_completed_with_limits": "Remove COMPLETED_WITH_LIMITS from the named node-spec, or allow it on that node at the interactive `/bootstrap`.",
    "invalid_repair_attempt_budget": "Set max_repair_attempts in the readiness spec to an integer from 1 to 5, or rerun the interactive `/bootstrap`.",
    "invalid_repair_loop_budget": "Give the repair loop a positive integer max_attempts, or rerun the interactive `/bootstrap`.",
    "invalid_repair_loop_spec": "Make required_repair_loops a list in the readiness spec, or rerun the interactive `/bootstrap`.",
    "invalid_required_capabilities": "Make required_capabilities a list in the readiness spec, or rerun the interactive `/bootstrap`.",
    "invalid_safety_quarantine": "Open the interactive `/bootstrap`; it reconciles the unreadable safety-quarantine record before any node runs.",
    "invalid_unattended_readiness_spec": "Fix the JSON syntax in the readiness spec, or rerun the interactive `/bootstrap` to regenerate it.",
    "invalid_user_steps": "Rerun the interactive `/bootstrap`; it writes user_steps as a list of entry names.",
    "missing_bootstrap_validator": "Rerun the interactive `/bootstrap`; it copies the validator into .allforai/bootstrap/scripts/.",
    "missing_coverage_repair_loop": "Declare a repair loop for the coverage gate at the interactive `/bootstrap`, or change on_needs_iteration in run-policy.json.",
    "missing_google_key": "Set GOOGLE_API_KEY (`/setup` walks you through it), then rerun `/run`.",
    "missing_image_cli": "Install and log in to the Codex CLI (`/setup check` shows the steps), then rerun `/run`.",
    "missing_long_task_recovery": "Rerun the interactive `/bootstrap`; it sets long_task_policy in the readiness spec.",
    "missing_no_fallback_policy": "Rerun the interactive `/bootstrap`; it sets forbid_hidden_fallback_completion in the readiness spec.",
    "missing_node_spec": "Rerun the interactive `/bootstrap`; it writes the missing node-spec.",
    "missing_noninteractive_policy": "Rerun the interactive `/bootstrap`; it sets forbid_mid_run_user_prompts in the readiness spec.",
    "missing_playwright_or_engine_automation": "Install the Playwright MCP or the named engine automation (`/setup check`), then rerun `/run`.",
    "missing_repair_attempt_budget": "Rerun the interactive `/bootstrap`; it sets max_repair_attempts in the readiness spec.",
    "missing_repair_loop_closure": "Rerun the interactive `/bootstrap`; the repair loop names a closure node the workflow does not have.",
    "missing_repair_loop_node": "Rerun the interactive `/bootstrap`; every repair loop needs a repair_node_id.",
    "missing_repair_loop_source": "Rerun the interactive `/bootstrap`; the repair loop names a QA node the workflow does not have.",
    "missing_runtime_command": "Rerun the interactive `/bootstrap`; it records the commands that start the product.",
    "missing_source_inputs": "Rerun the interactive `/bootstrap`; it declares source_inputs for the named node.",
    "missing_unattended_readiness_spec": "Rerun the interactive `/bootstrap`; it writes the unattended-run readiness spec.",
    "missing_video_cli": "Install and log in to the Grok CLI (`/setup check` shows the steps), then rerun `/run`.",
    "missing_workflow": "Run the interactive `/bootstrap` first; it writes workflow.json.",
    "node_spec_allows_user_prompt": "Remove the ask-the-user wording from the named node-spec, or rerun the interactive `/bootstrap`.",
    "pending_human_gate": "Rerun the interactive `/bootstrap`; this legacy approval gate names an approval file that does not exist.",
    "pending_product_decision": "Answer the named product decision at the interactive `/bootstrap` (Phase A).",
    "readiness_gate_error": "Fix the error the message names (usually an unreadable file under .allforai/bootstrap/), then rerun `/run`.",
    "repair_loop_not_blocked_by_qa": "Rerun the interactive `/bootstrap`; the repair node must wait for its QA node.",
    "stale_evidence": "Rerun `/run` if the named repair owner can redo it; otherwise open the interactive `/bootstrap` to reconcile the changed inputs.",
    "undetermined_external_change": "Open the interactive `/bootstrap`; it compares the changed source files and asks about any product conflict.",
    "unexpanded_program_handoff": "Rerun the interactive `/bootstrap`; it adds the runtime gameplay visual QA nodes for the frontend handoff.",
    "unpublished_readiness_report": "Make .allforai/bootstrap/ writable (disk space, permissions), then rerun `/run`.",
    "unreadable_node_spec": "Re-save the named node-spec as UTF-8 text, or rerun the interactive `/bootstrap` to regenerate it.",
    "unreconciled_repair_accounting": "Reconcile the interrupted repair authorization at the interactive `/bootstrap`, then remove the ledger lock; deleting the lock alone resumes nothing.",
    "unreconciled_safety_halt": "Reconcile the interrupted safety halt at the interactive `/bootstrap`, then remove the safety lock; deleting the lock alone resumes nothing.",
    "unresolved_external_change": "Decide the named change at the interactive `/bootstrap`: accept, reject or defer it.",
    "unresolved_safety_quarantine": "Rerun `/run` after the quarantined nodes are revalidated, or reconcile the halt at the interactive `/bootstrap`; never delete the marker by hand.",
    "unverified_external_change": "Open the interactive `/bootstrap` and run its external-changes check for the named files.",
    "verdict_entry_planned_as_node": "Rerun the interactive `/bootstrap`; /cross-exam and /product-review are steps you type after the run, never nodes.",
}


def _add(blockers: list[dict], code: str, message: str, *, node_id: str | None = None) -> None:
    item = {"code": code, "message": message}
    if code in BLOCKER_ACTIONS:
        item["action"] = BLOCKER_ACTIONS[code]
    if node_id:
        item["node_id"] = node_id
    blockers.append(item)


def _read_approval(path: Path, node_id: str) -> dict | None:
    if not path.exists():
        return None
    try:
        data = _load_json(path)
    except Exception:
        return None
    records = data.get("records") if isinstance(data, dict) else data
    if not isinstance(records, list):
        return None
    for record in records:
        if isinstance(record, dict) and record.get("node_id") == node_id:
            return record
    return None


def _as_bool(value) -> bool:
    return value is True or str(value).lower() == "true"


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def _safety_halt_blockers(bootstrap_root: Path, blockers: list[dict]) -> None:
    """A recorded safety halt refuses the whole run until a person reconciles it.

    A safety halt is run-wide, so it is decided before anything about the plan: no graph,
    policy or freshness verdict can qualify it. Two records, both fences:

    `safety-quarantine.json` names outputs that were produced but never revalidated. Its
    mere presence blocks — a marker that cannot be read, or that has been replaced by a
    symlink or a directory, is a stronger reason to stop, not a reason to continue, so the
    content is read only to say what is quarantined and never to decide whether it counts.

    `safety-quarantine.lock` is left behind when a quarantine could not be published, by
    failure or by a crash. The missing marker is then exactly what is untrustworthy: the
    absence of a record is not evidence that nothing had to be recorded.

    Neither is cleared here. Clearing one is a reconciliation decision that requires
    independent revalidation of the quarantined work; this gate only refuses to run.
    """
    marker = bootstrap_root / SAFETY_MARKER
    if os.path.lexists(marker):
        quarantined = None
        try:
            recorded = _load_json(marker)
            if (isinstance(recorded, dict) and recorded.get("schema_version") == 1
                    and recorded.get("status") == "quarantined"
                    and isinstance(recorded.get("node_ids"), list)
                    and isinstance(recorded.get("events"), list)
                    and all(isinstance(node_id, str) for node_id in recorded["node_ids"])
                    and not marker.is_symlink()):
                quarantined = sorted(recorded["node_ids"])
        except (OSError, ValueError):
            quarantined = None
        if quarantined is None:
            _add(blockers, "invalid_safety_quarantine",
                 f"{marker} exists but is not a readable quarantine record, so the work it "
                 f"holds cannot be identified; an unreadable halt is a stronger reason to "
                 f"stop than a legible one. Reconcile it at the interactive entry.")
        _add(blockers, "unresolved_safety_quarantine",
             f"A safety halt is recorded in {marker}"
             + (f" for {', '.join(quarantined)}" if quarantined else "")
             + "; those outputs were produced but never independently revalidated. The run "
               "stays blocked until they are, and this marker is never cleared by a policy "
               "change or by a worker reporting success.")
    if os.path.lexists(bootstrap_root / LEDGER_LOCK):
        # The repair-authorization ledger fences itself the same way, and for the same
        # reason: the lock outlives a writer that died mid-update, so what the ledger says
        # about spent budget may be a read taken across an unfinished write. Refused, never
        # removed — clearing it is a reconciliation decision about a specific interrupted
        # grant, and this gate cannot know which one.
        #
        # Deliberately not paired with a missing-ledger blocker. A run that has not yet
        # recorded its origin has no ledger, and that is the ordinary state of every new
        # run before `initialize` proves zero from the workflow; blocking on it here would
        # refuse every legitimate run at its first readiness check.
        _add(blockers, "unreconciled_repair_accounting",
             f"{bootstrap_root / LEDGER_LOCK} is held, so a repair-authorization write was "
             f"begun and never completed. Whether that attempt was charged, and whether it "
             f"ran, is exactly what is unknown. Reconcile the interrupted authorization and "
             f"remove the fence deliberately; execution does not resume by deleting it.")
    if os.path.lexists(bootstrap_root / SAFETY_LOCK):
        _add(blockers, "unreconciled_safety_halt",
             f"{bootstrap_root / SAFETY_LOCK} is held, so a safety quarantine was begun and "
             f"never durably published. What it would have named is unknown, and an absent "
             f"marker is not evidence that nothing needed quarantining. Reconcile the run "
             f"and remove the fence deliberately; execution does not resume by deleting it.")


PRODUCT_DECISION_GAPS = "product-decision-gaps"


def _product_decision_gap_blockers(bootstrap_root: Path, blockers: list[dict]) -> None:
    """A product decision a node parked waits for the user, not for another run.

    A workflow bootstrapped under ADR-0011 has its node record a user-visible rule nobody
    settled in `product-decision-gaps/<node_id>.json` and fail. The record stays until
    interactive bootstrap asks it, wires the answer into that node's `decision_inputs`
    and removes it, so its presence alone blocks the next unattended run. A record that
    cannot be read is still an unanswered claim, never an absent one. A choice a node took
    on its own recommendation (`run-decisions/`, ADR-0018) is a disclosure, not a blocker,
    and is not read here.
    """
    directory = bootstrap_root / PRODUCT_DECISION_GAPS
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("*.json")):
        try:
            record = _load_json(path)
            decisions = record.get("decisions") if isinstance(record, dict) else None
            questions = [d.get("needed_decision") for d in decisions or [] if isinstance(d, dict)]
        except Exception:
            questions = []
        detail = "; ".join(q for q in questions if isinstance(q, str) and q.strip()) or \
            "the record cannot be read; treat it as unanswered"
        _add(blockers, "pending_product_decision",
             f"{path.relative_to(bootstrap_root.parent.parent)} waits for the user: {detail} — "
             f"answer it at interactive /bootstrap Phase A", node_id=path.stem)


def _load_readiness_spec(path: Path, blockers: list[dict]) -> dict:
    if not path.exists():
        _add(
            blockers,
            "missing_unattended_readiness_spec",
            f"{path} is missing; bootstrap must specialize unattended requirements before /run",
        )
        return {}
    try:
        spec = _load_json(path)
    except Exception as exc:
        _add(blockers, "invalid_unattended_readiness_spec", f"{path} cannot be parsed: {exc}")
        return {}
    if not isinstance(spec, dict):
        _add(blockers, "invalid_unattended_readiness_spec", f"{path} must contain a JSON object")
        return {}
    return spec


def _validate_policy_spec(spec: dict, blockers: list[dict], warnings: list[dict]) -> None:
    if not spec:
        return

    if not _as_bool(spec.get("forbid_mid_run_user_prompts")):
        _add(
            blockers,
            "missing_noninteractive_policy",
            "unattended spec must set forbid_mid_run_user_prompts=true",
        )
    if not _as_bool(spec.get("forbid_hidden_fallback_completion")):
        _add(
            blockers,
            "missing_no_fallback_policy",
            "unattended spec must set forbid_hidden_fallback_completion=true",
        )

    max_repair_attempts = spec.get("max_repair_attempts")
    if max_repair_attempts is None:
        _add(blockers, "missing_repair_attempt_budget", "unattended spec missing max_repair_attempts")
    elif not isinstance(max_repair_attempts, int) or max_repair_attempts < 1 or max_repair_attempts > 5:
        _add(
            blockers,
            "invalid_repair_attempt_budget",
            "unattended spec max_repair_attempts must be an integer from 1 to 5",
        )

    long_task_policy = spec.get("long_task_policy")
    if not isinstance(long_task_policy, dict):
        _add(blockers, "missing_long_task_recovery", "unattended spec missing long_task_policy")
    else:
        for key in ("file_based_handoff", "polling", "timeout", "retry", "resume"):
            if not _as_bool(long_task_policy.get(key)):
                _add(
                    blockers,
                    "missing_long_task_recovery",
                    f"unattended spec long_task_policy.{key} must be true",
                )

    repair_loops = spec.get("required_repair_loops")
    if repair_loops is None:
        warnings.append({
            "code": "missing_required_repair_loops",
            "message": "unattended spec declares no required repair loops; this is valid only for non-QA workflows",
        })
    elif not isinstance(repair_loops, list):
        _add(blockers, "invalid_repair_loop_spec", "required_repair_loops must be a list")


def _validate_required_capabilities(
    project_root: Path,
    spec: dict,
    blockers: list[dict],
    warnings: list[dict],
    external_tool_findings: list[dict],
) -> None:
    capabilities = spec.get("required_capabilities") if isinstance(spec, dict) else None
    if capabilities is None:
        return
    if not isinstance(capabilities, list):
        _add(blockers, "invalid_required_capabilities", "required_capabilities must be a list")
        return

    for item in capabilities:
        if not isinstance(item, dict):
            _add(blockers, "invalid_required_capabilities", "required_capabilities entries must be objects")
            continue
        if item.get("required") is False:
            continue
        capability = item.get("capability")
        if not capability:
            _add(blockers, "invalid_required_capabilities", "required capability missing capability name")
            continue

        if capability == "codex_cli":
            # ADR-0003: the cross-platform CLI is reviewer two's preferred backend, not a
            # requirement. Its absence is recorded and warned; a second fresh-context
            # sub-agent takes reviewer two's seat. Never a blocker.
            codex_path = shutil.which("codex")
            external_tool_findings.append({"capability": "codex_cli", "path": codex_path, "source": "spec",
                                           "reviewer_two_backend": "codex-cli" if codex_path else "session-subagent"})
            if not codex_path:
                warnings.append({"code": "missing_cross_platform_cli",
                                 "message": "Codex CLI not found; reviewer two runs as a second fresh-context sub-agent"})
        elif capability == "image_generation_cli":
            # Generated images come only from Codex; unlike reviewer two there is no fallback.
            codex_path = shutil.which("codex")
            external_tool_findings.append({"capability": "image_generation_cli", "path": codex_path, "source": "spec"})
            if not codex_path:
                _add(blockers, "missing_image_cli", "Codex CLI is required to generate images and was not found")
        elif capability == "video_generation_cli":
            # Generated video comes only from the Grok CLI. Login and plan are checked when it runs.
            grok_path = shutil.which("grok")
            external_tool_findings.append({"capability": "video_generation_cli", "path": grok_path, "source": "spec"})
            if not grok_path:
                _add(blockers, "missing_video_cli", "Grok CLI is required to generate video and was not found")
        elif capability == "google_api_key":
            has_key = bool(os.environ.get(item.get("env") or "GOOGLE_API_KEY"))
            external_tool_findings.append({"capability": "google_api_key", "present": has_key, "source": "spec"})
            if not has_key:
                _add(blockers, "missing_google_key", "Google API key is required by unattended spec")
        elif capability == "runtime_command":
            commands = item.get("commands")
            if not isinstance(commands, list) or not commands:
                _add(blockers, "missing_runtime_command", "runtime_command capability requires commands[]")
                continue
            missing = []
            for command in commands:
                if not isinstance(command, str) or not command.strip():
                    missing.append(command)
                    continue
                binary = command.strip().split()[0]
                if binary.startswith("./"):
                    if not (project_root / binary).exists():
                        missing.append(command)
                elif not shutil.which(binary):
                    missing.append(command)
            external_tool_findings.append({
                "capability": "runtime_command",
                "commands": commands,
                "missing_commands": missing,
                "source": "spec",
            })
            if missing:
                _add(blockers, "missing_runtime_command", f"runtime command binaries/files unavailable: {missing}")
        elif capability in {"playwright", "browser_automation"}:
            has_tool = bool(shutil.which("playwright") or shutil.which("npx"))
            external_tool_findings.append({"capability": capability, "available": has_tool, "source": "spec"})
            if not has_tool:
                _add(
                    blockers,
                    "missing_playwright_or_engine_automation",
                    f"{capability} is required by unattended spec",
                )
        elif capability == "engine_automation":
            commands = item.get("commands")
            if not isinstance(commands, list) or not commands:
                _add(
                    blockers,
                    "missing_playwright_or_engine_automation",
                    "engine_automation capability requires commands[]",
                )
        else:
            external_tool_findings.append({
                "capability": capability,
                "state": "declared_unchecked",
                "source": "spec",
            })


def _planned_verdict_entry(node: dict) -> str | None:
    """The verdict entry a node is named after, or None.

    Matched on the identifier and the capability, case-insensitively and with `_` read as
    `-`: `cross_exam`, `final-product-review` and `capability: "cross-exam"` all plan the
    examiner into the run under another spelling.
    """
    for field in ("node_id", "capability"):
        value = node.get(field)
        if not isinstance(value, str):
            continue
        spelled = value.lower().replace("_", "-")
        for entry in VERDICT_ENTRIES:
            if entry in spelled:
                return entry
    return None


def coverage_gate_nodes(nodes: list[dict]) -> list[str]:
    """Node ids of the concept-acceptance coverage gate (ADR-0008): the gate whose missing-mapping list
    fires on_needs_iteration."""
    return [n["node_id"] for n in nodes
            if isinstance(n, dict) and n.get("capability") == "concept-acceptance" and isinstance(n.get("node_id"), str)]


def _coverage_gate_loop_blockers(project_root: str, nodes: list[dict], spec: dict,
                                 blockers: list[dict]) -> None:
    """auto_fix_once repairs only through a declared loop (ADR-0006). A workflow that carries the coverage
    gate and that policy without a loop naming the gate would halt at run time as an unauthorized
    repair; the plan is the fault, so it is refused here where the user can fix it."""
    policy_path = os.path.join(project_root, ".allforai", "bootstrap", "run-policy.json")
    try:
        with open(policy_path, encoding="utf-8") as fh:
            policy = json.load(fh)
    except (OSError, ValueError):
        return
    if not isinstance(policy, dict) or policy.get("on_needs_iteration") != "auto_fix_once":
        return
    loops = spec.get("required_repair_loops") if isinstance(spec, dict) else None
    declared = set()
    for loop in loops or []:
        if isinstance(loop, dict):
            # qa_node_ids is the gate the loop repairs; closure_node_ids covers the gate's own
            # rerun when the rerun shares the gate's capability (the coverage gate rerun does) —
            # it is already inside the declared loop, not a second gate needing one of its own.
            declared.update(str(q) for q in (loop.get("qa_node_ids") or loop.get("qa_nodes") or []))
            declared.update(str(q) for q in (loop.get("closure_node_ids") or loop.get("closure_nodes") or []))
    for gate in coverage_gate_nodes(nodes):
        if gate not in declared:
            _add(blockers, "missing_coverage_repair_loop",
                 f"run-policy.json on_needs_iteration is auto_fix_once and node {gate} is the "
                 f"concept-acceptance coverage gate, but no unattended-run-readiness-spec.json "
                 f"required_repair_loops entry names it in qa_node_ids. auto_fix_once repairs only "
                 f"through a declared loop (ADR-0006): declare one with a repair node hard_blocked_by "
                 f"{gate} and a rerun of the gate blocked by the repair, or choose halt_with_report.",
                 node_id=gate)


def _dependency_outside_graph_blockers(project_root: Path, by_id: dict, blockers: list[dict]) -> None:
    """A recorded dynamic read of another node's output is an upstream the graph omits.

    Freshness treats the producer of every consumed file as an upstream, so a read
    recorded before a replan — or a read of a node that runs later — makes the consumer
    wait on a node the scheduler never orders before it: the consumer runs, cannot
    publish, and the run stalls mid-wave. The fix is a planning one (drop the stale read,
    or declare the edge), so it is reported here, before anything runs.
    """
    reads_path = Path(project_root) / ".allforai/bootstrap/observed-input-dependencies.json"
    try:
        reads = json.loads(reads_path.read_text(encoding="utf-8")) if reads_path.exists() else {}
    except (OSError, ValueError):
        return  # A malformed register is the freshness gate's own finding.
    if not isinstance(reads, dict):
        return
    producers = {}
    for node_id, node in by_id.items():
        for item in [*(node.get("exit_artifacts") or []), *(node.get("required_documents") or [])]:
            path = item.get("path") if isinstance(item, dict) else item
            if isinstance(path, str):
                producers[path] = node_id

    def ancestors(node_id):
        seen, stack = set(), list(by_id.get(node_id, {}).get("hard_blocked_by") or [])
        while stack:
            current = stack.pop()
            if isinstance(current, str) and current not in seen:
                seen.add(current)
                stack.extend(by_id.get(current, {}).get("hard_blocked_by") or [])
        return seen

    for node_id in sorted(by_id):
        paths = reads.get(node_id)
        if not isinstance(paths, list):
            continue
        upstream = ancestors(node_id)
        for path in sorted({p for p in paths if isinstance(p, str)}):
            producer = producers.get(path)
            if producer and producer != node_id and producer not in upstream:
                _add(blockers, "dependency_outside_graph",
                     f"{node_id} has a recorded read of {path}, which {producer} produces, but "
                     f"{producer} is not upstream of {node_id} in hard_blocked_by; {node_id} would "
                     "wait on a node the scheduler does not order before it. At the interactive "
                     "bootstrap entry, remove the stale read from observed-input-dependencies.json "
                     "or declare the dependency.", node_id=node_id)


def _verdict_entry_blockers(workflow: dict, nodes: list[dict], blockers: list[dict],
                            warnings: list[dict] | None = None) -> None:
    """Neither skill calls the other (ADR-0008); the graph may only list them for the user.

    A node that plans `/cross-exam` or `/product-review` is refused by name: `/run` would
    schedule it as author work, and the examiner's independence is exactly what a node
    cannot supply. `user_steps` is where a generated workflow names them, so it must name
    entries — a value the summary cannot print is not a step the user can take.
    """
    for node in nodes:
        if not isinstance(node, dict):
            continue
        entry = _planned_verdict_entry(node)
        if entry:
            _add(blockers, "verdict_entry_planned_as_node",
                 f"node plans /{entry} as a node; /run never starts it, because a verdict "
                 f"on the delivery is not the author's to give (ADR-0008). It is a user "
                 f"step after the pipeline: remove the node and list it in "
                 f"workflow.json user_steps.", node_id=_node_id(node))
    if not isinstance(workflow, dict):
        return
    # a workflow that plans verification has a delivery to examine afterwards; the steps the
    # user takes then are part of the workflow. No project is exempt from /cross-exam: a CLI or
    # library-sdk drops only /product-review, having no UI to critique (suppress-rules.md).
    plans_verify = any(isinstance(n, dict) and isinstance(n.get("capability"), str)
                       and (n["capability"].endswith("-verify") or n["capability"] == "concept-acceptance")
                       for n in nodes)
    omitted = ("user_steps: [\"/cross-exam\", \"/product-review\"]; a project with no product to "
               "critique (cli, library-sdk) drops only /product-review, user_steps: "
               "[\"/cross-exam\"]. A delivery is always examined, so no list may leave out "
               "/cross-exam.")
    # clause:user-steps-cross-exam-kept@918988ee
    if "user_steps" not in workflow:
        code, message = "missing_user_steps", (
            "workflow.json has no user_steps: the steps the user takes after the run "
            "(/cross-exam, then /product-review) are part of the workflow, and silence is not "
            "an exemption. Write " + omitted)
    else:
        steps = workflow.get("user_steps")
        if (not isinstance(steps, list)
                or not all(isinstance(step, str) and step.strip() for step in steps)):
            _add(blockers, "invalid_user_steps",
                 f"workflow.json user_steps must be a list of entry names such as "
                 f"[\"/cross-exam\", \"/product-review\"], got {steps!r}; a step the user "
                 f"cannot read is not one they can take after the run.")
            return
        if "/cross-exam" in [step.strip() for step in steps]:
            return
        code, message = "missing_cross_exam_step", (
            f"workflow.json user_steps {steps!r} leaves out /cross-exam. Write " + omitted)
    if plans_verify:
        _add(blockers, code, message)
    elif warnings is not None:
        _add(warnings, code, message)


def _validate_repair_loop_spec(spec: dict, nodes: list[dict], blockers: list[dict],
                               warnings: list[dict]) -> None:
    if not spec or not isinstance(spec.get("required_repair_loops"), list):
        return
    # Only addressable nodes reach here (the shape gate defers this check otherwise);
    # rebuilding the map on that rule keeps the assumption local rather than inherited.
    node_by_id = {node["node_id"]: node for node in nodes
                  if isinstance(node, dict) and isinstance(node.get("node_id"), str)
                  and node["node_id"].strip()}
    node_ids = set(node_by_id)

    for index, loop in enumerate(spec.get("required_repair_loops") or []):
        if not isinstance(loop, dict):
            _add(blockers, "invalid_repair_loop_spec", f"required_repair_loops[{index}] must be an object")
            continue
        repair_node_id = loop.get("repair_node_id")
        qa_nodes = loop.get("qa_node_ids") or loop.get("qa_nodes") or []
        closure_nodes = loop.get("closure_node_ids") or loop.get("closure_nodes") or []
        for label, declared in (("qa_node_ids", qa_nodes), ("closure_node_ids", closure_nodes)):
            if not isinstance(declared, list):
                _add(blockers, "invalid_repair_loop_spec",
                     f"required_repair_loops[{index}] {label} must be a list of node ids, "
                     f"got {declared!r}")
        qa_nodes = qa_nodes if isinstance(qa_nodes, list) else []
        closure_nodes = closure_nodes if isinstance(closure_nodes, list) else []
        if not repair_node_id:
            _add(blockers, "missing_repair_loop_node", f"required_repair_loops[{index}] missing repair_node_id")
            continue
        if not isinstance(repair_node_id, str) or repair_node_id not in node_ids:
            _add(blockers, "missing_repair_loop_node", f"repair loop node '{repair_node_id}' missing from workflow")
            continue
        # Both orchestrators refuse to route a loop whose declared budget is unusable, so
        # an unbounded loop is reported here instead of at the first QA failure. An omitted
        # budget is the one legitimate fallback: it takes the documented default of 3.
        if "max_attempts" not in loop:
            warnings.append({
                "code": "repair_loop_budget_defaulted",
                "message": f"repair loop '{repair_node_id}' declares no max_attempts; "
                           "the documented default of 3 attempts per QA node applies",
            })
        else:
            budget = loop.get("max_attempts")
            if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
                _add(
                    blockers,
                    "invalid_repair_loop_budget",
                    f"repair loop '{repair_node_id}' max_attempts must be a positive integer, "
                    f"got {budget!r}; the loop is unbounded and routes nothing",
                )
        repair_edges = node_by_id[repair_node_id].get("hard_blocked_by")
        repair_edges = repair_edges if isinstance(repair_edges, list) else []
        for qa_node_id in qa_nodes:
            if not isinstance(qa_node_id, str) or not qa_node_id.strip():
                _add(blockers, "missing_repair_loop_source",
                     f"repair loop '{repair_node_id}' names QA node {qa_node_id!r}, which "
                     f"identifies no node in the workflow")
            elif qa_node_id not in node_ids:
                _add(blockers, "missing_repair_loop_source", f"QA node '{qa_node_id}' missing from workflow")
            elif qa_node_id not in repair_edges:
                _add(
                    blockers,
                    "repair_loop_not_blocked_by_qa",
                    f"repair loop '{repair_node_id}' must hard_blocked_by QA node '{qa_node_id}'",
                )
        for closure_node_id in closure_nodes:
            if not isinstance(closure_node_id, str) or not closure_node_id.strip():
                _add(blockers, "missing_repair_loop_closure",
                     f"repair loop '{repair_node_id}' names closure node {closure_node_id!r}, "
                     f"which identifies no node in the workflow")
                continue
            if closure_node_id not in node_ids:
                _add(blockers, "missing_repair_loop_closure", f"closure node '{closure_node_id}' missing from workflow")
                continue
            closure_edges = node_by_id[closure_node_id].get("hard_blocked_by")
            closure_edges = closure_edges if isinstance(closure_edges, list) else []
            if repair_node_id not in closure_edges:
                _add(
                    blockers,
                    "closure_not_blocked_by_repair_loop",
                    f"closure node '{closure_node_id}' must hard_blocked_by repair loop '{repair_node_id}'",
                )


def _reset_nodes(workflow: dict) -> set:
    """Nodes a diagnosis reset (`compute_reset_closure.py --apply`) that have not run since."""
    latest: dict = {}
    log = workflow.get("transition_log") if isinstance(workflow, dict) else None
    for entry in log if isinstance(log, list) else []:
        node_id = entry.get("node_id", entry.get("node")) if isinstance(entry, dict) else None
        if isinstance(node_id, str):
            latest[node_id] = entry.get("status")
    return {node_id for node_id, status in latest.items() if status == "superseded"}


def _late_reads(project_root: Path, node: dict) -> set:
    """The node's own reads registered after it published (see evidence_freshness.late_reads)."""
    from evidence_freshness import STATE, late_reads, read_json
    try:
        record = (read_json(project_root, STATE, {}).get("nodes") or {}).get(node.get("node_id"))
        return late_reads(project_root, node, record) if isinstance(record, dict) else set()
    except (OSError, ValueError, TypeError, AttributeError):
        return set()  # unreadable state or register: the stale record blocks, as before


def _stale_evidence_blocks_start(node: dict, freshness: dict, reset: bool = False,
                                 late: set = frozenset()) -> bool:
    """Whether a node's stale record must stop the run before it starts.

    A node that has published nothing has no contract or evidence to invalidate, so it
    stays startable. A node whose *own* declared source inputs moved while it still holds
    only a contract is re-read when it runs and must republish before it can complete, so
    it too stays startable — blocking it is what once left the runner with nothing it
    could run. Two states do block: an input the node merely consumed moved (a wired
    decision file, another node's output — the plan is stale and running this node does
    not repair it), and published evidence exists at all (a completion claim is at risk
    however the input is declared).

    A node a diagnosis reset claims nothing: the run withdrew its completion and will run
    it again, and that rerun is the repair. Its old evidence is what the diagnosis found
    wrong, so it cannot be why the run that would replace it may not start.
    """
    if reset:
        return False
    diff = freshness.get("diff") if isinstance(freshness.get("diff"), dict) else {}
    files = diff.get("files") if isinstance(diff.get("files"), dict) else {}
    # Stale only because the node itself read more after publishing: running it again
    # republishes with those reads, so the run that would do that must be able to start.
    if (late and set(diff) == {"files"} and files
            and all(kind == "added" and path in late for path, kind in files.items())):
        return False
    if diff.get("contract") == "unpublished":
        return False
    if diff.get("evidence") != "unpublished":
        return True
    changed = set(diff.get("files") or {})
    return bool(changed - set(node.get("source_inputs") or []))


def validate_unattended_readiness(project_root: Path) -> dict:
    bootstrap_root = project_root / ".allforai/bootstrap"
    workflow_path = bootstrap_root / "workflow.json"
    node_specs_dir = bootstrap_root / "node-specs"
    spec_path = bootstrap_root / "unattended-run-readiness-spec.json"
    blockers: list[dict] = []
    warnings: list[dict] = []
    approval_gate_findings: list[dict] = []
    non_interactive_findings: list[dict] = []
    external_tool_findings: list[dict] = []
    fallback_findings: list[dict] = []
    long_task_findings: list[dict] = []

    # A safety halt is run-wide and answers to nothing below it, so it is decided first.
    _safety_halt_blockers(bootstrap_root, blockers)
    _product_decision_gap_blockers(bootstrap_root, blockers)
    readiness_spec = _load_readiness_spec(spec_path, blockers)
    _validate_policy_spec(readiness_spec, blockers, warnings)
    # `/run` must not assume bootstrap ran and passed: the plan the user confirmed is
    # re-checked at the run boundary, scoped to the nodes an unconfirmed change affects.
    blockers.extend(plan_confirmation_blockers(project_root))
    # The structural rules the bootstrap gate decides — a declared repair loop that routes
    # nothing, a deferred effect proof with no downstream owner — hold at this boundary too,
    # read from that one implementation. Claude's `/run` reaches them only here.
    #
    # Shape precedes the rules that assume it. A node identifier that is not a non-empty
    # string cannot key a graph, and every check below the load either indexes by
    # identifier or names one in a blocker. The shape verdict is taken first, from the same
    # implementation the bootstrap gate uses, and while it holds the graph-reading checks
    # are deferred rather than answered from the addressable subset of a broken graph.
    shape_blockers = workflow_shape_blockers(project_root)
    blockers.extend(shape_blockers)
    if not shape_blockers:
        blockers.extend(structural_gate_blockers(project_root))
    # A decision-coverage pass that could not run independently is accepted, never passed
    # off as independent: it is carried to the person starting the run (ADR-0011).
    for disclosure in decision_coverage_disclosures(str(bootstrap_root)):
        warnings.append({"code": "decision_coverage_not_independent", "message": disclosure})

    if not workflow_path.exists():
        _add(blockers, "missing_workflow", f"{workflow_path} does not exist")
        nodes: list[dict] = []
        workflow = {}
    else:
        try:
            workflow = _load_json(workflow_path)
            raw_nodes = workflow.get("nodes") if isinstance(workflow, dict) else []
            if isinstance(raw_nodes, list):
                nodes = raw_nodes
            else:
                _add(blockers, "missing_workflow", "workflow.json nodes must be a list")
                nodes = []
        except Exception as exc:
            _add(blockers, "missing_workflow", f"workflow.json cannot be parsed: {exc}")
            workflow = {}
            nodes = []

    # Decided on the graph as written, before shape faults defer the node list: a planned
    # verdict node is a planning fault the user repairs at bootstrap, whatever else holds.
    _verdict_entry_blockers(workflow, nodes, blockers, warnings)
    _coverage_gate_loop_blockers(project_root, nodes, readiness_spec, blockers)
    scope_blockers = validate_scope(project_root, workflow)
    blockers.extend(scope_blockers)
    from check_artifacts import document_verification_errors, freshness_states
    # Freshness needs a well-formed node list; shape rejection above already fails closed.
    # It indexes by node identifier, so an unaddressable one is a shape fault here too.
    well_formed = (not shape_blockers
                   and isinstance(workflow, dict) and isinstance(workflow.get("nodes"), list)
                   and all(isinstance(n, dict) for n in workflow["nodes"]))
    by_id = ({n["node_id"]: n for n in workflow["nodes"] if isinstance(n.get("node_id"), str)}
             if well_formed else {})
    if well_formed:
        _dependency_outside_graph_blockers(project_root, by_id, blockers)
    reset = _reset_nodes(workflow)
    for node_id, freshness in (freshness_states(project_root, workflow) if well_formed else {}).items():
        admission = freshness.get("admission")
        if admission == "invalid":
            code = ("missing_document_verification" if document_verification_errors(by_id.get(node_id, {}))
                    else "invalid_source_inputs")
            _add(blockers, code, freshness["reason"], node_id=node_id)
        elif admission == "missing":
            _add(blockers, "missing_source_inputs", freshness["reason"], node_id=node_id)
        elif admission == "legacy" and freshness.get("readiness_status") == "undeclared":
            _add(warnings, "undeclared_source_inputs", freshness["reason"], node_id=node_id)
        elif (freshness.get("readiness_status") != "valid"
              and _stale_evidence_blocks_start(by_id.get(node_id, {}), freshness, node_id in reset,
                                               _late_reads(project_root, by_id.get(node_id, {})))):
            message = freshness.get("reason") or "Reconcile inputs and reverify affected evidence"
            repair = freshness.get("repair") if isinstance(freshness.get("repair"), dict) else None
            if repair:
                message += (f"; repair owner {repair.get('owner')} "
                            f"({', '.join(repair.get('responsibilities') or [])}); diff {json.dumps(freshness.get('diff', {}), ensure_ascii=False)}")
            _add(blockers, "stale_evidence", message, node_id=node_id)
    if well_formed:
        # A product conflict raised by an external source change is a user decision.
        # Unattended execution reports it and refuses the affected work; it never
        # interviews, and it never reads changed code as an approved requirement.
        from evidence_freshness import rejected_conflicts, routed_external_changes, undecided_conflicts
        try:
            conflicts, unverified = routed_external_changes(project_root)
        except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError, StopIteration) as exc:
            # An undeterminable comparison is not a clear one: unattended execution
            # cannot show that no product conflict is waiting for the user.
            conflicts, unverified = {}, {}
            _add(blockers, "undetermined_external_change",
                 "External source changes cannot be determined, so no delivery can be shown to be free of an "
                 f"unresolved product conflict; resolve it at the interactive bootstrap entry: {exc}")
        for node_id in sorted(unverified):
            for change in unverified[node_id]:
                # The gate observes; it never runs the project's acceptance to find out.
                # Unknown impact is withheld work, not an implementation-only change.
                _add(blockers, "unverified_external_change",
                     f"External source change {change['change_id']} to "
                     f"{', '.join(sorted(change['files']))} has no current verification of its impact; run the "
                     "external-changes verification at the interactive bootstrap entry. Unattended execution "
                     "cannot verify it, and it is not assumed to be implementation-only.",
                     node_id=node_id)
        for node_id in sorted(conflicts):
            for change in undecided_conflicts(conflicts, node_id):
                state = ("deferred" if (change["resolution"] or {}).get("resolution") == "defer"
                         else "reopened, because the requirement its earlier decision was made against was revised"
                         if change.get("superseded_resolutions") else "undecided")
                _add(blockers, "unresolved_external_change",
                     f"External source change {change['change_id']} ({change['classification']}) to "
                     f"{', '.join(sorted(change['files']))} is "
                     f"{state}; resolve it at the interactive bootstrap entry "
                     "(accept, reject or defer). Unattended execution cannot decide it or assume acceptance.",
                     node_id=node_id)
            for change in rejected_conflicts(conflicts, node_id):
                task = (change["resolution"] or {}).get("repair_task", {})
                _add(blockers, "external_change_repair_pending",
                     f"The user rejected external source change {change['change_id']}; restore the confirmed "
                     f"behavior in {', '.join(sorted(change['files']))}, resynchronize the affected documents and "
                     "republish the confirmed acceptance "
                     f"({' '.join(task.get('restore_acceptance') or []) or 'recorded acceptance unavailable'}).",
                     node_id=node_id)
    if scope_blockers or shape_blockers:
        # Defer shape-dependent checks, retaining rejection in the report below.
        nodes = []

    for rel in (
        "scripts/validate_bootstrap.py",
        "scripts/check_artifacts.py",
        "scripts/validate_unattended_readiness.py",
    ):
        path = bootstrap_root / rel
        if not path.exists():
            _add(blockers, "missing_bootstrap_validator", f"{path} is missing")

    all_node_text = []
    for node in nodes:
        nid = _node_id(node)
        spec_path = node_specs_dir / f"{nid}.md"
        if not spec_path.exists():
            _add(blockers, "missing_node_spec", f"{spec_path} is missing", node_id=nid)
            continue
        try:
            text = spec_path.read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            # An unreadable brief is not an absent one and not an accepted one: the
            # non-interactive, fallback and long-task rules below are all decided from
            # this text, so a node whose brief cannot be read has no verdict to give.
            _add(blockers, "unreadable_node_spec",
                 f"{spec_path} cannot be read as UTF-8 text, so its non-interactive, "
                 f"fallback and long-task obligations cannot be checked: {exc}", node_id=nid)
            continue
        all_node_text.append(text)

        if _contains_any(text, ("AskUserQuestion", "request user input", "ask the user", "询问用户")):
            _add(
                blockers,
                "node_spec_allows_user_prompt",
                "node-spec contains interactive user prompt language",
                node_id=nid,
            )
            non_interactive_findings.append({"node_id": nid, "state": "failed"})

        if "COMPLETED_WITH_LIMITS" in text and not node.get("allow_completed_with_limits"):
            _add(
                blockers,
                "forbidden_completed_with_limits",
                "node-spec mentions COMPLETED_WITH_LIMITS without node.allow_completed_with_limits=true",
                node_id=nid,
            )
            fallback_findings.append({"node_id": nid, "state": "failed"})

        if _contains_any(text, ("long-task", "poll", "task_id")):
            has_recovery = _contains_any(text, ("retry", "rerun", "resume", "repair", "timeout", "poll"))
            long_task_findings.append({"node_id": nid, "has_recovery_policy": has_recovery})
            if not has_recovery:
                _add(
                    blockers,
                    "missing_long_task_recovery",
                    "long-task node lacks retry/rerun/resume/poll policy",
                    node_id=nid,
                )

        if node.get("human_gate") is True:
            approval_path = node.get("approval_record_path")
            if approval_path is not None and not isinstance(approval_path, str):
                _add(blockers, "pending_human_gate",
                     f"human_gate node declares approval_record_path {approval_path!r}, which "
                     f"names no file; an approval that cannot be located is not an approval",
                     node_id=nid)
                approval_gate_findings.append({"node_id": nid, "approval_record_path": approval_path,
                                               "gate_status": None})
                continue
            record = _read_approval(project_root / approval_path, nid) if approval_path else None
            gate_status = record.get("gate_status") if record else None
            finding = {"node_id": nid, "approval_record_path": approval_path, "gate_status": gate_status}
            approval_gate_findings.append(finding)
            if gate_status != "approved":
                _add(
                    blockers,
                    "pending_human_gate",
                    f"human_gate node is not approved (gate_status={gate_status!r})",
                    node_id=nid,
                )

    blob = json.dumps(workflow, ensure_ascii=False) + "\n" + "\n".join(all_node_text)
    lower_blob = blob.lower()

    _validate_required_capabilities(project_root, readiness_spec, blockers, warnings, external_tool_findings)
    if not scope_blockers and not shape_blockers:
        _validate_repair_loop_spec(readiness_spec, nodes, blockers, warnings)

    if "codex" in lower_blob or "visual-acceptance" in lower_blob or "screenshot" in lower_blob:
        codex_path = shutil.which("codex")
        external_tool_findings.append({"capability": "codex_cli", "path": codex_path,
                                       "reviewer_two_backend": "codex-cli" if codex_path else "session-subagent"})
        if not codex_path:
            warnings.append({"code": "missing_cross_platform_cli",
                             "message": "Codex CLI not found in PATH; visual gates run reviewer two as a second fresh-context sub-agent (ADR-0003)"})

    if "google" in lower_blob or "lyria" in lower_blob:
        has_key = bool(os.environ.get("GOOGLE_API_KEY"))
        external_tool_findings.append({"capability": "google_api_key", "present": has_key})
        if not has_key:
            _add(blockers, "missing_google_key", "GOOGLE_API_KEY is required by selected workflow")

    if "program-development-node-handoff.json" in lower_blob and "game-frontend" in lower_blob:
        if "runtime-gameplay-visual-acceptance" not in lower_blob:
            _add(
                blockers,
                "unexpanded_program_handoff",
                "game frontend handoff exists but runtime gameplay visual QA is not represented",
            )

    if "game_2d_production" in lower_blob or "game-2d-production" in lower_blob:
        if "game-2d-production-closure-qa" not in lower_blob and "2d-production-closure-qa" not in lower_blob:
            _add(
                blockers,
                "unexpanded_game_2d_production_handoff",
                "game 2D production handoff exists but 2D production closure QA is not represented",
            )

    status = READY_STATUS if not blockers else BLOCKING_STATUS
    return {
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "blockers": blockers,
        "warnings": warnings,
        "required_capabilities": external_tool_findings,
        "approval_gate_findings": approval_gate_findings,
        "non_interactive_findings": non_interactive_findings,
        "external_tool_findings": external_tool_findings,
        "fallback_findings": fallback_findings,
        "long_task_findings": long_task_findings,
        "recommended_pre_run_actions": list(dict.fromkeys(
            item["action"] for item in blockers if item.get("action"))),
    }


def write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# Unattended Run Readiness",
        "",
        f"Status: `{report['status']}`",
        f"Checked at: `{report['checked_at']}`",
        "",
        "## Blockers",
    ]
    if report["blockers"]:
        for blocker in report["blockers"]:
            node = f" `{blocker['node_id']}`" if blocker.get("node_id") else ""
            lines.append(f"- `{blocker['code']}`{node}: {blocker['message']}")
            if blocker.get("action"):
                lines.append(f"  - What to do: {blocker['action']}")
    else:
        lines.append("- None")
    lines.extend(["", "## Required Capabilities"])
    for item in report.get("required_capabilities", []):
        lines.append(f"- `{item.get('capability')}`: {json.dumps(item, ensure_ascii=False)}")
    lines.extend(["", "## Recommended Pre-Run Actions"])
    actions = report.get("recommended_pre_run_actions") or ["Ready for unattended /run."]
    for action in actions:
        lines.append(f"- {action}")
    _publish(path, "\n".join(lines) + "\n")


def _blocked_report(code: str, message: str) -> dict:
    """A current, structured refusal for a fault that has no per-node verdict."""
    return {
        "status": BLOCKING_STATUS,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "blockers": [{"code": code, "message": message, "action": BLOCKER_ACTIONS[code]}],
        "warnings": [],
        "required_capabilities": [],
        "approval_gate_findings": [],
        "non_interactive_findings": [],
        "external_tool_findings": [],
        "fallback_findings": [],
        "long_task_findings": [],
        "recommended_pre_run_actions": [BLOCKER_ACTIONS[code]],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.project_root)
    try:
        report = validate_unattended_readiness(root)
    except Exception as exc:
        # A gate that raises has decided nothing, and a traceback is not a verdict a host
        # can read. The refusal is published in the report's own shape so both hosts reach
        # it by the path they already use, and the stale report is replaced rather than
        # left standing as this run's answer.
        report = _blocked_report(
            "readiness_gate_error",
            f"The readiness gate could not reach a verdict on this project: "
            f"{type(exc).__name__}: {exc}. Nothing is admitted on an undecided gate.")
    if args.write_report:
        out = root / ".allforai/bootstrap/unattended-run-readiness.json"
        try:
            _write_json(out, report)
            write_markdown(root / ".allforai/bootstrap/unattended-run-readiness.md", report)
        except OSError as exc:
            report = _blocked_report(
                "unpublished_readiness_report",
                f"The readiness verdict could not be published to {out}: {exc}. Any report "
                f"still on disk is from an earlier run and does not describe this graph; "
                f"treat this refusal, not that file, as the current verdict.")
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
