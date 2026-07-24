#!/usr/bin/env python3
"""Create and verify platform-neutral Grillstorm execution checkpoints."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


class CheckpointError(RuntimeError):
    pass


def _canonical_hash(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def workflow_fingerprint(tasks, orchestration):
    return _canonical_hash({"tasks": tasks, "orchestration": orchestration})


def _git(repo, *args):
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise CheckpointError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _task_statuses(repo, baseline, integration, task_ids):
    _git(repo, "merge-base", "--is-ancestor", baseline, integration)
    subjects = _git(repo, "log", "--format=%s", f"{baseline}..{integration}")
    valid = set(task_ids)
    statuses = {}
    for subject in subjects.splitlines():
        for prefix, status in (
            ("grillstorm-confirmed: ", "done"),
            ("grillstorm-reality-gated: ", "reality_gated"),
        ):
            if subject.startswith(prefix):
                task_id = subject[len(prefix):]
                if task_id in valid:
                    statuses[task_id] = status
    return statuses


def _check_dependency_closure(completed, orchestration):
    deps = orchestration.get("effective_deps") or {}
    for task_id in completed:
        missing = set(deps.get(task_id, ())) - set(completed)
        if missing:
            raise CheckpointError(
                f"completed task {task_id} lacks completed dependencies: {sorted(missing)}"
            )


def create_checkpoint(workflow_state, run_state, tasks, orchestration, repo, source_host):
    task_ids = {task["id"] for task in tasks}
    run_id = workflow_state.get("run_id")
    baseline = workflow_state.get("baseline_commit")
    integration_ref = workflow_state.get("integration_ref")
    if not run_id or not baseline or not integration_ref:
        raise CheckpointError("workflow state lacks run_id, baseline_commit, or integration_ref")
    integration = _git(repo, "rev-parse", "--verify", integration_ref)
    statuses = _task_statuses(repo, baseline, integration, task_ids)
    recorded = set(workflow_state.get("completed", ()))
    if recorded != set(statuses):
        raise CheckpointError(
            "workflow completed set does not match supervised integration markers"
        )
    _check_dependency_closure(recorded, orchestration)
    revisions = {
        key: run_state.get(key)
        for key in ("spec_revision", "task_revision", "workflow_revision", "launch_revision")
    }
    if any(not isinstance(value, int) for value in revisions.values()):
        raise CheckpointError("run state lacks integer revision counters")
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "source_host": source_host,
        "baseline_commit": baseline,
        "integration_commit": integration,
        "completed": sorted(recorded),
        "task_statuses": statuses,
        "workflow_fingerprint": workflow_fingerprint(tasks, orchestration),
        "revisions": revisions,
    }
    payload["checkpoint_fingerprint"] = _canonical_hash(payload)
    return payload


def validate_checkpoint(checkpoint, tasks, orchestration, repo, expected_revisions=None):
    if checkpoint.get("schema_version") != 1:
        raise CheckpointError("unsupported checkpoint schema")
    fingerprint = checkpoint.get("checkpoint_fingerprint")
    unsigned = {key: value for key, value in checkpoint.items()
                if key != "checkpoint_fingerprint"}
    if fingerprint != _canonical_hash(unsigned):
        raise CheckpointError("checkpoint fingerprint mismatch")
    if checkpoint.get("workflow_fingerprint") != workflow_fingerprint(tasks, orchestration):
        raise CheckpointError("checkpoint workflow inputs differ")
    task_ids = {task["id"] for task in tasks}
    completed = set(checkpoint.get("completed", ()))
    if not completed.issubset(task_ids):
        raise CheckpointError("checkpoint contains unknown completed tasks")
    if expected_revisions is not None and checkpoint.get("revisions") != expected_revisions:
        raise CheckpointError("checkpoint revisions differ")
    statuses = _task_statuses(
        repo,
        checkpoint["baseline_commit"],
        checkpoint["integration_commit"],
        task_ids,
    )
    if completed != set(statuses) or statuses != checkpoint.get("task_statuses"):
        raise CheckpointError("checkpoint completion evidence differs from Git markers")
    _check_dependency_closure(completed, orchestration)
    return {
        "run_id": checkpoint["run_id"],
        "baseline_commit": checkpoint["baseline_commit"],
        "portable_integration_commit": checkpoint["integration_commit"],
        "completed": sorted(completed),
        "portable_checkpoint_fingerprint": fingerprint,
    }


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_atomic(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--workflow-state", required=True)
    create.add_argument("--run-state", required=True)
    create.add_argument("--tasks", required=True)
    create.add_argument("--orchestration", required=True)
    create.add_argument("--repo", required=True)
    create.add_argument("--source-host", choices=("claude", "codex"), required=True)
    create.add_argument("--output", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--checkpoint", required=True)
    verify.add_argument("--tasks", required=True)
    verify.add_argument("--orchestration", required=True)
    verify.add_argument("--repo", required=True)
    args = parser.parse_args(argv)
    try:
        tasks = _read(args.tasks)
        if isinstance(tasks, dict):
            tasks = tasks.get("tasks", [])
        orchestration = _read(args.orchestration)
        if args.command == "create":
            payload = create_checkpoint(
                _read(args.workflow_state),
                _read(args.run_state),
                tasks,
                orchestration,
                args.repo,
                args.source_host,
            )
            _write_atomic(args.output, payload)
        else:
            print(json.dumps(
                validate_checkpoint(_read(args.checkpoint), tasks, orchestration, args.repo),
                indent=2,
            ))
    except (OSError, ValueError, KeyError, CheckpointError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
