#!/usr/bin/env python3
"""§4.5 orchestration: turn validated plan tasks into a deterministic execution
DAG. Ordering comes from explicit depends_on PLUS derived interface edges (no prose
parsing): a task that `requires` registry interface X depends on every task that
`implements` X — this is how CROSS-MODULE ordering enters the DAG, since parallel
per-module plan agents cannot know each other's task ids. A required interface with
no implementing task anywhere is a hard error (the plan missed work).

Concurrency safety targets a DEPENDENCY-READY scheduler (skill §1.6), not layer
barriers: two tasks may run concurrently iff neither is a DAG ancestor of the other
(layers are emitted as informational output only). Any such concurrent-possible pair
sharing a touched_path OR a declared `resources` entry (shared physical resource:
simulator / shared test stack / prod SSH) is folded into `isolate_groups`.
In Grillstorm's default all-worktree mode, path groups are merge-collision hints and may
execute concurrently; `resource_groups` remain runtime mutexes. Compatibility group mode
serializes every isolate group. `effective_deps` (explicit + derived) is what the ready-set
loop consumes. Same-path writers with no dependency ordering are ambiguous -> WARN."""
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


def _interface_edges(tasks):
    """Derive (task_id, depends_on_id) edges from implements/requires interface
    tags. Self-edges are skipped (a task may build and consume its own interface).
    Returns (edges, errors); a required interface nobody implements is an error."""
    impl = {}
    for t in tasks:
        for x in t.get("implements", []) or []:
            impl.setdefault(x, []).append(t["id"])
    edges, errors = [], []
    for t in tasks:
        for x in t.get("requires", []) or []:
            providers = impl.get(x)
            if not providers:
                errors.append(
                    f"task '{t['id']}' requires interface '{x}' but no task implements it "
                    f"(the exposing module's plan missed work, or the tag is wrong)")
                continue
            for p in providers:
                if p != t["id"]:
                    edges.append((t["id"], p))
    return edges, errors


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


def _ancestors(eff_deps):
    """Transitive ancestor sets over the effective dep map {tid: [dep_ids]}.
    Decides which pairs can EVER run concurrently under a dependency-ready
    scheduler: concurrent-possible iff neither is an ancestor of the other."""
    memo = {}

    def anc(tid):
        if tid in memo:
            return memo[tid]
        memo[tid] = set()  # cycle guard; real cycles already errored upstream
        s = set()
        for d in eff_deps.get(tid, []):
            s.add(d)
            s |= anc(d)
        memo[tid] = s
        return s

    for tid in eff_deps:
        anc(tid)
    return memo


def build_dag(tasks):
    errors, warnings = [], []
    for tid, missing in _missing_deps(tasks):
        errors.append(f"task '{tid}' depends_on missing task '{missing}'")
    derived, ierrs = _interface_edges(tasks)
    errors.extend(ierrs)
    extra = {}
    for tid, dep in derived:
        extra.setdefault(tid, set()).add(dep)
    # effective deps = explicit depends_on + derived interface edges
    aug = [dict(t, depends_on=sorted(set(t.get("depends_on") or []) | extra.get(t["id"], set())))
           for t in tasks]
    layers, cyclic = _layers(aug)
    if cyclic:
        errors.append(f"dependency cycle among tasks: {', '.join(cyclic)}")
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings, "layers": [],
                "isolate": [], "isolate_groups": [], "effective_deps": {},
                "resource_groups": {}}

    effective_deps = {t["id"]: list(t["depends_on"]) for t in aug}
    reality_gate_flags = {t["id"]: bool(t.get("reality_gate", False)) for t in tasks}
    reality_gate_tasks = sorted(tid for tid, enabled in reality_gate_flags.items()
                                if enabled)
    ancestors = _ancestors(effective_deps)
    paths_by_id = {t["id"]: set(t.get("touched_paths", [])) for t in tasks}
    res_by_id = {t["id"]: set(t.get("resources", []) or []) for t in tasks}
    isolate = []
    # Concurrent-possible = no dependency path either way (ready-set scheduling;
    # same-layer is NOT the criterion — cross-layer independents overlap too).
    for a, b in itertools.combinations([t["id"] for t in tasks], 2):
        if a in ancestors[b] or b in ancestors[a]:
            continue  # dep-ordered, never concurrent
        shared_paths = paths_by_id[a] & paths_by_id[b]
        shared_res = res_by_id[a] & res_by_id[b]
        if not shared_paths and not shared_res:
            continue
        isolate.append(sorted([a, b]))
        if shared_paths:
            warnings.append(
                f"tasks '{a}' and '{b}' both write {sorted(shared_paths)} with no "
                f"dependency ordering; run in separate worktrees and serialize integration")
    # Per-resource mutex sets (declaration order); single-user resources need no mutex.
    resource_groups = {}
    for t in tasks:
        for rname in t.get("resources", []) or []:
            resource_groups.setdefault(rname, []).append(t["id"])
    resource_groups = {k: v for k, v in resource_groups.items() if len(v) > 1}
    # Union-find the isolate PAIRS (file- AND resource-colliding) into connected
    # GROUPS — §1.6 serializes each group (declaration order; worktree isolation +
    # merge-after-confirm only when target repo == session cwd). Pairs alone are not
    # enough: a–b and b–c colliding means all three must serialize relative to b.
    # Conservative (safe) grouping over max parallelism.
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
            "layers": layers, "isolate": isolate, "isolate_groups": isolate_groups,
            "effective_deps": effective_deps, "resource_groups": resource_groups,
            "reality_gate_flags": reality_gate_flags,
            "reality_gate_tasks": reality_gate_tasks,
            "derived_edges": sorted([list(e) for e in set(derived)])}


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
