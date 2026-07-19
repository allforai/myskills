#!/usr/bin/env python3
"""Transactional candidate admission for Megastorm integration refs.

This module is intentionally independent from ``run_layers.py``.  Callers supply
their durable event writer and may inject a command runner for deterministic tests.
"""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Callable, Mapping, Sequence


class CandidateIntegrationError(RuntimeError):
    def __init__(self, message, evidence=None):
        super().__init__(message)
        self.evidence = evidence or {}


class PostMergeCheckFailure(CandidateIntegrationError):
    pass


class CASConflict(CandidateIntegrationError):
    """The integration ref changed; the candidate must be rebuilt and rechecked."""


@dataclass(frozen=True)
class Check:
    name: str
    argv: tuple


@dataclass(frozen=True)
class AdmissionResult:
    task_id: str
    transaction_id: str
    candidate_commit: str
    integration_commit: str
    merge_complete: bool
    dependents_ready: bool
    evidence: Mapping


def subprocess_runner(argv, cwd):
    return subprocess.run(list(argv), cwd=str(cwd), capture_output=True, text=True)


def _run(runner, argv, cwd, *, operation, allow_failure=False):
    result = runner(tuple(argv), Path(cwd))
    code = getattr(result, "returncode", None)
    if not isinstance(code, int):
        raise CandidateIntegrationError(f"{operation}: command runner returned no exit code")
    record = {
        "operation": operation,
        "argv": list(argv),
        "exit_code": code,
        "stdout": (getattr(result, "stdout", "") or "")[-4000:],
        "stderr": (getattr(result, "stderr", "") or "")[-4000:],
    }
    if code != 0 and not allow_failure:
        raise CandidateIntegrationError(f"{operation} failed", record)
    return result, record


def _rev_parse(runner, repo, revision):
    result, _ = _run(runner, ("git", "rev-parse", "--verify", revision), repo,
                     operation=f"resolve {revision}")
    value = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40,64}", value):
        raise CandidateIntegrationError(f"resolve {revision}: invalid object id")
    return value.lower()


def _safe_component(value):
    safe = re.sub(r"[^A-Za-z0-9._-]", "-", value)
    if not safe or safe in {".", ".."}:
        raise CandidateIntegrationError("task/transaction id is unsafe for a candidate ref")
    return safe


def _check_evidence(check, record):
    encoded = ((record["stdout"] or "") + "\0" + (record["stderr"] or "")).encode()
    return {"name": check.name, "argv": list(check.argv),
            "exit_code": record["exit_code"],
            "output_sha256": hashlib.sha256(encoded).hexdigest(),
            "stdout": record["stdout"], "stderr": record["stderr"]}


def _quarantine(event_writer, evidence):
    evidence = dict(evidence)
    evidence["quarantined"] = True
    try:
        event_writer("candidate-quarantined", evidence)
    except Exception as exc:  # quarantine must remain visible even if its event sink fails
        evidence["quarantine_event_error"] = str(exc)
    return evidence


def _cleanup(runner, repo, candidate_ref, worktree, worktree_root):
    records = []
    _, record = _run(runner, ("git", "worktree", "remove", "--force", str(worktree)),
                     repo, operation="remove candidate worktree", allow_failure=True)
    records.append(record)
    _, record = _run(runner, ("git", "update-ref", "-d", candidate_ref), repo,
                     operation="delete candidate ref", allow_failure=True)
    records.append(record)
    shutil.rmtree(worktree_root, ignore_errors=True)
    return records


def admit_candidate(
    *, repo, integration_ref, expected_integration_commit, task_commit, task_id,
    transaction_id, contract_hash, post_merge_checks: Sequence[Check], event_writer,
    command_runner=subprocess_runner, task_base_commit=None, post_merge_validator=None,
):
    """Check a candidate and CAS-publish it; never release dependents before completion."""
    repo = Path(repo).resolve()
    expected = _rev_parse(command_runner, repo, expected_integration_commit)
    task = _rev_parse(command_runner, repo, task_commit)
    task_base = _rev_parse(command_runner, repo, task_base_commit or expected)
    current = _rev_parse(command_runner, repo, integration_ref)
    if current != expected:
        raise CASConflict("integration ref no longer matches expected parent",
                          {"expected_parent": expected, "observed_parent": current,
                           "requires_recheck": True})
    for ancestor, descendant, label in (
            (task_base, task, "task commit is not rooted at its frozen task baseline"),
            (task_base, expected, "integration no longer contains the frozen task baseline")):
        check, record = _run(
            command_runner, ("git", "merge-base", "--is-ancestor", ancestor, descendant),
            repo, operation="verify task ancestry", allow_failure=True)
        if check.returncode != 0:
            raise CandidateIntegrationError(label, record)

    task_component = _safe_component(task_id)
    transaction_component = _safe_component(transaction_id)
    candidate_ref = f"refs/megastorm/candidates/{task_component}/{transaction_component}"
    worktree_root = Path(tempfile.mkdtemp(prefix=f"megastorm-candidate-{task_component}-"))
    worktree = worktree_root / "worktree"
    evidence = {"task_id": task_id, "transaction_id": transaction_id,
                "expected_parent": expected, "task_commit": task,
                "task_base_commit": task_base,
                "candidate_ref": candidate_ref, "worktree": str(worktree),
                "contract_hash": contract_hash, "checks": []}
    try:
        _run(command_runner, ("git", "update-ref", candidate_ref, expected, ""), repo,
             operation="create candidate ref")
        _run(command_runner, ("git", "worktree", "add", "--detach", str(worktree), expected),
             repo, operation="create candidate worktree")
        _run(command_runner, ("git", "merge", "--no-ff", "--no-edit", task), worktree,
             operation="merge task into candidate")
        candidate = _rev_parse(command_runner, worktree, "HEAD")
        _run(command_runner, ("git", "update-ref", candidate_ref, candidate, expected), repo,
             operation="advance candidate ref")
        evidence["candidate_commit"] = candidate

        if post_merge_validator is not None:
            evidence["artifact_admission"] = post_merge_validator(worktree, expected)

        for check in post_merge_checks:
            result, record = _run(command_runner, check.argv, worktree,
                                  operation=f"post-merge check: {check.name}",
                                  allow_failure=True)
            check_record = _check_evidence(check, record)
            evidence["checks"].append(check_record)
            if result.returncode != 0:
                raise PostMergeCheckFailure(
                    f"post-merge check failed: {check.name}", _quarantine(event_writer, evidence))

        intent = dict(evidence)
        event_writer("merge-intent", intent)  # must durably return before CAS
        cas, cas_record = _run(
            command_runner, ("git", "update-ref", integration_ref, candidate, expected), repo,
            operation="publish candidate with CAS", allow_failure=True)
        if cas.returncode != 0:
            conflict = dict(evidence)
            conflict["cas"] = cas_record
            conflict["observed_parent"] = _rev_parse(command_runner, repo, integration_ref)
            conflict["requires_recheck"] = True
            raise CASConflict("integration CAS conflict; candidate requires recheck",
                              _quarantine(event_writer, conflict))
        complete = {**intent, "integration_commit": candidate}
        event_writer("merge-complete", complete)  # dependents remain blocked until return
        cleanup = _cleanup(command_runner, repo, candidate_ref, worktree, worktree_root)
        return AdmissionResult(task_id, transaction_id, candidate, candidate, True, True,
                               {**complete, "cleanup": cleanup})
    except (PostMergeCheckFailure, CASConflict):
        raise
    except Exception:
        # Preserve candidate ref/worktree as crash and recovery evidence.
        raise


def recover_intent(*, repo, integration_ref, intent, event_writer, event_exists,
                   command_runner=subprocess_runner):
    """Idempotently finish a durable intent or require a fresh candidate recheck."""
    required = {"task_id", "transaction_id", "expected_parent", "candidate_commit",
                "candidate_ref", "contract_hash", "checks", "worktree"}
    if not isinstance(intent, dict) or not required.issubset(intent):
        raise CandidateIntegrationError("merge intent is incomplete")
    for check in intent["checks"]:
        if check.get("exit_code") != 0:
            raise CandidateIntegrationError("merge intent contains failed check evidence")
        encoded = ((check.get("stdout") or "") + "\0" +
                   (check.get("stderr") or "")).encode()
        if check.get("output_sha256") != hashlib.sha256(encoded).hexdigest():
            raise CandidateIntegrationError("merge intent check evidence hash mismatch")
    complete_key = (intent["task_id"], intent["transaction_id"],
                    intent["candidate_commit"])
    current = _rev_parse(command_runner, repo, integration_ref)
    expected = intent["expected_parent"]
    candidate = intent["candidate_commit"]
    if current == expected:
        if _rev_parse(command_runner, repo, intent["candidate_ref"]) != candidate:
            raise CandidateIntegrationError("candidate ref no longer matches durable intent")
        cas, record = _run(
            command_runner, ("git", "update-ref", integration_ref, candidate, expected), repo,
            operation="recover candidate CAS", allow_failure=True)
        if cas.returncode != 0:
            raise CASConflict("recovery CAS conflict; candidate requires recheck",
                              _quarantine(event_writer,
                                          {**intent, "cas": record,
                                           "requires_recheck": True}))
        current = candidate
    elif current != candidate:
        raise CASConflict("integration moved beyond durable intent; candidate requires recheck",
                          _quarantine(event_writer,
                                      {**intent, "observed_parent": current,
                                       "requires_recheck": True}))
    if not event_exists("merge-complete", complete_key):
        event_writer("merge-complete", {**intent, "integration_commit": candidate,
                                         "recovered": True})
    worktree = Path(intent["worktree"])
    if (not worktree.is_absolute() or worktree.name != "worktree" or
            not worktree.parent.name.startswith("megastorm-candidate-")):
        raise CandidateIntegrationError("merge intent contains unsafe candidate worktree")
    cleanup = _cleanup(command_runner, repo, intent["candidate_ref"], worktree,
                       worktree.parent)
    return AdmissionResult(intent["task_id"], intent["transaction_id"], candidate,
                           current, True, True,
                           {**intent, "recovered": True, "cleanup": cleanup})
