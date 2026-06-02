#!/usr/bin/env python3
"""Three-lens structural validation of a generated workflow.json DAG.

Deterministic half of the bootstrap DAG-validation gate. Catches — at PLANNING
time — the structural defects that would otherwise surface mid-run as a C3
`deadlock` / needs_diagnosis, violating the "autonomous run, no surprises" goal:

  - 大小循环 (loop):  no dependency cycle in hard_blocked_by; no node depends on
                       a non-existent node_id (both => guaranteed runtime deadlock).

The 闭环 (artifact-closure) and 逆向 (dead-node / goal-traceback) lenses need the
node-specs' prose (the schema has no `consumes` field), so they live in the LLM
reverse-critic step of the gate, not here.
"""
import json
import sys


def find_missing_deps(nodes):
    """Return [(node_id, missing_dep_id)] for hard_blocked_by referencing absent nodes."""
    ids = {n["node_id"] for n in nodes}
    out = []
    for n in nodes:
        for d in n.get("hard_blocked_by", []) or []:
            if d not in ids:
                out.append((n["node_id"], d))
    return out


def find_cycles(nodes):
    """Return the sorted node_ids that cannot be topologically ordered (in or
    downstream of a hard_blocked_by cycle). [] means the graph is acyclic.

    Missing deps are filtered out here (reported separately by find_missing_deps),
    so a node depending only on a ghost id is NOT flagged as a cycle."""
    ids = {n["node_id"] for n in nodes}
    deps = {n["node_id"]: [d for d in (n.get("hard_blocked_by", []) or []) if d in ids]
            for n in nodes}
    indeg = {nid: len(ds) for nid, ds in deps.items()}
    dependents = {nid: [] for nid in deps}
    for nid, ds in deps.items():
        for d in ds:
            dependents[d].append(nid)
    queue = [nid for nid, deg in indeg.items() if deg == 0]
    processed = 0
    while queue:
        cur = queue.pop()
        processed += 1
        for dep in dependents[cur]:
            indeg[dep] -= 1
            if indeg[dep] == 0:
                queue.append(dep)
    if processed == len(nodes):
        return []
    return sorted(nid for nid, deg in indeg.items() if deg > 0)


def validate_dag_structure(workflow):
    """Return {ok, errors} for the deterministic structural lenses (hard errors)."""
    nodes = workflow.get("nodes", [])
    errors = []
    for nid, missing in find_missing_deps(nodes):
        errors.append(f"node '{nid}' hard_blocked_by missing node '{missing}'")
    cyc = find_cycles(nodes)
    if cyc:
        errors.append(f"dependency cycle among nodes: {', '.join(cyc)}")
    return {"ok": len(errors) == 0, "errors": errors}


def main(argv):
    base = argv[1] if len(argv) > 1 else "."
    import os
    wf_path = os.path.join(base, ".allforai/bootstrap/workflow.json")
    with open(wf_path) as f:
        workflow = json.load(f)
    result = validate_dag_structure(workflow)
    if result["ok"]:
        print("OK: DAG structurally sound (no cycles, no missing deps)")
        return 0
    print("BLOCKED: DAG structural errors (fix before /run):")
    for e in result["errors"]:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
