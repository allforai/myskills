#!/usr/bin/env python3
"""§4.5 orchestration: turn validated plan tasks into a deterministic execution
DAG. Ordering comes ONLY from explicit depends_on (no prose parsing). touched_paths
drives concurrency safety: same-layer tasks sharing any path must run worktree-isolated
(spec §4.6). Same-path writers with no depends_on are ambiguous -> WARN + still isolate."""
import itertools
import json
import sys


def _missing_deps(tasks):
    ids = {t["id"] for t in tasks}
    out = []
    for t in tasks:
        for d in t.get("depends_on", []) or []:
            if d not in ids:
                out.append((t["id"], d))
    return out


def _layers(tasks):
    """Kahn layering over depends_on. Returns (layers, cyclic_ids).
    Missing deps are filtered (reported separately) so a ghost dep is not a cycle."""
    ids = {t["id"] for t in tasks}
    deps = {t["id"]: [d for d in (t.get("depends_on", []) or []) if d in ids] for t in tasks}
    indeg = {tid: len(ds) for tid, ds in deps.items()}
    dependents = {tid: [] for tid in deps}
    for tid, ds in deps.items():
        for d in ds:
            dependents[d].append(tid)
    layers = []
    ready = sorted([tid for tid, deg in indeg.items() if deg == 0])
    seen = 0
    while ready:
        layers.append(ready)
        seen += len(ready)
        nxt = []
        for tid in ready:
            for dep in dependents[tid]:
                indeg[dep] -= 1
                if indeg[dep] == 0:
                    nxt.append(dep)
        ready = sorted(nxt)
    cyclic = sorted(tid for tid, deg in indeg.items() if deg > 0)
    return layers, cyclic


def build_dag(tasks):
    errors, warnings = [], []
    for tid, missing in _missing_deps(tasks):
        errors.append(f"task '{tid}' depends_on missing task '{missing}'")
    layers, cyclic = _layers(tasks)
    if cyclic:
        errors.append(f"dependency cycle among tasks: {', '.join(cyclic)}")
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings, "layers": [], "isolate": []}

    by_id = {t["id"]: set(t.get("touched_paths", [])) for t in tasks}
    deps = {t["id"]: set(t.get("depends_on", []) or []) for t in tasks}
    isolate = []
    for layer in layers:
        for a, b in itertools.combinations(sorted(layer), 2):
            shared = by_id[a] & by_id[b]
            if shared:
                isolate.append([a, b])
                # same-layer => no dep ordering between them; if neither depends on
                # the other, ordering of writes to the shared path is undefined.
                if b not in deps[a] and a not in deps[b]:
                    warnings.append(
                        f"tasks '{a}' and '{b}' both write {sorted(shared)} with no depends_on; "
                        f"serialized by declaration order, run isolated")
    # Union-find the isolate PAIRS into connected GROUPS — §1.6 runs each group
    # sequentially (declaration order) with worktree isolation + merge-after-confirm.
    # Pairs alone are not enough: a–b and b–c colliding means all three must serialize
    # their merges relative to b. Conservative (safe) grouping over max parallelism.
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        parent[find(a)] = find(b)
    for a, b in isolate:
        union(a, b)
    groups = {}
    for node in {n for pair in isolate for n in pair}:
        groups.setdefault(find(node), []).append(node)
    # preserve declaration order within each group, deterministic group order
    order = {t["id"]: i for i, t in enumerate(tasks)}
    isolate_groups = sorted(
        (sorted(g, key=lambda i: order[i]) for g in groups.values()),
        key=lambda g: order[g[0]])

    return {"ok": True, "errors": errors, "warnings": warnings,
            "layers": layers, "isolate": isolate, "isolate_groups": isolate_groups}


def main(argv):
    path = argv[1] if len(argv) > 1 else "-"
    raw = sys.stdin.read() if path == "-" else open(path).read()
    tasks = json.loads(raw)
    if isinstance(tasks, dict):
        tasks = tasks.get("tasks", [])
    r = build_dag(tasks)
    print(json.dumps(r, indent=2))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
