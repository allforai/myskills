#!/usr/bin/env python3
"""Run-owned Orca packet/admission checks; never launches agents or writes product code."""
import argparse
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
CAP = 3
ROLES = {"build", "evaluator", "subject", "supervisor", "standards", "spec"}


def admission(role, live, pending_aux=False):
    if role not in ROLES or any(item["role"] not in ROLES for item in live):
        raise ValueError("unknown role")
    if len(live) >= CAP:
        return False
    evaluators = sum(item["role"] == "evaluator" for item in live)
    if role == "evaluator":
        return evaluators == 0 and len(live) <= CAP - 2 and not pending_aux
    if role == "build":
        return not pending_aux and not (evaluators and len(live) >= CAP - 1)
    return True


def packet(task_id, role):
    if role == "subject" or role not in ROLES:
        raise ValueError("subjects require raw isolated briefs; no oracle packet")
    tasks = json.loads((RUN / "tasks/workflow-tasks.json").read_text())
    task = next(t for t in tasks if t["id"] == task_id)
    binding = json.loads((RUN / "tasks/dispatch-bindings.json").read_text())
    refs = task["dispatch_inputs"]
    for ref in refs:
        actual = hashlib.sha256((RUN / ref["path"]).read_bytes()).hexdigest()
        if actual != binding["files"].get(ref["path"]):
            raise ValueError("stale dispatch input: " + ref["path"])
    return {
        "task_id": task_id, "role": role, "spec_revision": 2,
        "task_revision": 1, "workflow_revision": 2, "task": task,
        "input_hashes": {ref["path"]: binding["files"][ref["path"]] for ref in refs},
        "prompt": (
            "Read every dispatch_inputs file completely; task document focus is section "
            + task_id + ". Resolve paths under " + str(RUN)
            + ". These are mandatory approved scope, purpose, failure, runtime and review obligations, "
            "not optional background. Use source body AND comments. Preserve exact frozen artifact "
            "contract. Builders use official TDD; evaluators execute the complete scenario matrix "
            "on actual candidate-loaded Claude and Codex with oracle withheld from subjects. "
            "Supervisors independently rerun acceptance and inspect real evidence; no executor "
            "narrative. Standards/Spec review the fixed candidate diff on their separate axes. "
            "No marker/merge/main/tracker/push/install by workers. Follow dispatch-contract.md "
            "for completion and side effects. Controller supplies candidate/base SHA and assigned "
            "worktree; do not change referenced frozen control artifacts."
        ),
    }


def dry_run():
    # Reproduce the reported waiting-evaluator frontier without launching any agent.
    live = []
    trace = []
    for task_id in ("T15", "T16", "T17"):
        allowed = admission("evaluator", live)
        trace.append({"task": task_id, "role": "evaluator", "admitted": allowed})
        if allowed:
            live.append({"id": task_id, "role": "evaluator"})
    assert [item["id"] for item in live] == ["T15"]
    assert admission("subject", live, pending_aux=True)
    live.append({"id": "T15-claude", "role": "subject"})
    assert not admission("build", live, pending_aux=True)
    live.pop()  # actual controller releases a settled subject before admitting more work
    assert admission("subject", live, pending_aux=True)
    live.append({"id": "T15-codex", "role": "subject"})
    live.pop()
    live.pop()  # evaluator persisted evidence and settled; no held review wait
    assert admission("supervisor", live, pending_aux=True)
    live.append({"id": "verify-T15", "role": "supervisor"})
    live.pop()
    assert admission("standards", live, pending_aux=True)
    live.append({"id": "standards-T15", "role": "standards"})
    assert admission("spec", live, pending_aux=True)
    live.append({"id": "spec-T15", "role": "spec"})
    live.clear()
    trace.append({"task": "T15", "event": "subjects_then_supervision_parallel_reviews_then_serial_merge"})
    assert admission("evaluator", live)
    trace.append({"task": "T16", "role": "evaluator", "admitted": True})
    # One evaluator reserves auxiliary capacity; two finite builders delay its admission.
    assert not admission("evaluator", [{"role": "build"}, {"role": "build"}])
    assert admission("build", [{"role": "evaluator"}])
    assert not admission("build", [{"role": "evaluator"}, {"role": "build"}])
    assert not admission("build", [{"role": "build"}], pending_aux=True)
    assert admission("spec", [{"role": "evaluator"}, {"role": "standards"}])
    assembled = {task_id: packet(task_id, "evaluator" if task_id == "T15" else "build")
                 for task_id in ("T9", "T15")}
    assert all(item["input_hashes"] and "Read every dispatch_inputs" in item["prompt"]
               for item in assembled.values())
    t15 = assembled["T15"]["task"]
    assert "T15/new-product" in t15["required_scenarios"]
    assert len(t15["required_scenarios"]) == 7
    return {"ok": True, "cap": CAP, "role_trace": trace,
            "progress": "T16 then T17 each reuses the same released evaluator/subject/review slots",
            "assembled_payloads": assembled, "runtime_proof": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["assemble", "admission", "dry-run"])
    parser.add_argument("--task")
    parser.add_argument("--role")
    parser.add_argument("--live", default="[]")
    parser.add_argument("--pending-aux", action="store_true")
    args = parser.parse_args()
    if args.command == "assemble":
        result = packet(args.task, args.role)
    elif args.command == "admission":
        result = {"admitted": admission(args.role, json.loads(args.live), args.pending_aux)}
    else:
        result = dry_run()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
