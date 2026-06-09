# megastorm Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `megastorm` — a Claude Code plugin (global command `/megastorm <goal>`) in the myskills repo that chains superpowers brainstorming/writing-plans/executing-plans into an autonomous, Workflow-driven pipeline for large goals.

**Architecture:** A plugin at `claude/megastorm/` with (1) three deterministic Python scripts (plan-task validation, task-DAG orchestration, closure checking) that are the testable core, (2) a `skills/megastorm.md` orchestration brain that drives the phase-by-phase CC Workflow pipeline, (3) six prompt-template knowledge files that inline the brainstorming/writing-plans/executing-plans methodologies into headless Workflow agents, and (4) JSON schemas pinning the agent contracts. The LLM produces structured JSON via Workflow `schema`; the Python scripts are pure functions over that JSON.

**Tech Stack:** Python 3 (`unittest`, mirroring `shared/scripts/orchestrator/` convention), Markdown skill/command files with YAML frontmatter, the built-in CC Workflow tool (`agent`/`pipeline`/`parallel`).

**Spec:** `docs/superpowers/specs/2026-06-09-megastorm-pipeline-design.md`

---

## File Structure

```
claude/megastorm/
├── .claude-plugin/
│   ├── plugin.json              # plugin manifest (v0.1.0)
│   └── marketplace.json         # marketplace listing
├── commands/
│   └── megastorm.md             # /megastorm command entry
├── skills/
│   └── megastorm.md             # orchestration brain: Phase -1..2, Workflow templates
├── knowledge/
│   ├── schemas.md               # escalation / closure-manifest / task / verdict JSON schemas
│   └── prompts/
│       ├── design-agent.md      # inlined brainstorming methodology + closure-manifest output
│       ├── plan-agent.md        # inlined writing-plans methodology + touched_paths/acceptance_cmd
│       ├── closure-critic.md    # 闭环 LLM critic
│       ├── reverse-critic.md    # 逆向 LLM critic
│       ├── executor.md          # inlined executing-plans discipline (Sonnet executor)
│       └── supervisor.md        # anti-fake-completion verifier (Opus)
└── scripts/
    ├── validate_plan_tasks.py   # §4.3: every task has non-empty touched_paths + acceptance_cmd
    ├── build_task_dag.py        # §4.5: topo layers + collision/isolation + mutual-write WARN + cycle/missing
    ├── check_closure.py         # §4.2: deterministic coverage / interface / orphan over manifests
    ├── check_skill_refs.py      # integration self-check: SKILL.md refs all resolve
    ├── test_validate_plan_tasks.py
    ├── test_build_task_dag.py
    ├── test_check_closure.py
    └── test_check_skill_refs.py
```

**Responsibility split:** scripts = deterministic pure functions over JSON (unit-tested). knowledge/prompts = the methodology the headless Workflow agents follow. skills/megastorm.md = the only orchestration prose, glues scripts + prompts + Workflow calls. Phase→primitive mapping is fixed by spec §0.

---

## Task 1: `validate_plan_tasks.py` — §4.3 plan hard-constraint

**Files:**
- Create: `claude/megastorm/scripts/validate_plan_tasks.py`
- Test: `claude/megastorm/scripts/test_validate_plan_tasks.py`

- [ ] **Step 1: Write the failing test**

```python
# claude/megastorm/scripts/test_validate_plan_tasks.py
import unittest
from validate_plan_tasks import validate_tasks


def _t(tid, paths=("a.py",), cmd="pytest a.py"):
    return {"id": tid, "touched_paths": list(paths), "acceptance_cmd": cmd}


class TestValidateTasks(unittest.TestCase):
    def test_all_valid(self):
        r = validate_tasks([_t("T1"), _t("T2", ("b.py",), "npm run build")])
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["errors"], [])

    def test_missing_touched_paths(self):
        r = validate_tasks([{"id": "T1", "acceptance_cmd": "pytest"}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("touched_paths" in e for e in r["errors"]))

    def test_empty_touched_paths(self):
        r = validate_tasks([{"id": "T1", "touched_paths": [], "acceptance_cmd": "x"}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("touched_paths" in e for e in r["errors"]))

    def test_missing_acceptance_cmd(self):
        r = validate_tasks([{"id": "T1", "touched_paths": ["a.py"]}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("acceptance_cmd" in e for e in r["errors"]))

    def test_blank_acceptance_cmd(self):
        r = validate_tasks([{"id": "T1", "touched_paths": ["a.py"], "acceptance_cmd": "  "}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("acceptance_cmd" in e for e in r["errors"]))

    def test_missing_id(self):
        r = validate_tasks([{"touched_paths": ["a.py"], "acceptance_cmd": "x"}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("id" in e for e in r["errors"]))

    def test_error_names_task(self):
        r = validate_tasks([_t("T1"), {"id": "T2"}])
        self.assertFalse(r["ok"])
        self.assertTrue(any("T2" in e for e in r["errors"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd claude/megastorm/scripts && python3 -m pytest test_validate_plan_tasks.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'validate_plan_tasks'`

- [ ] **Step 3: Write minimal implementation**

```python
# claude/megastorm/scripts/validate_plan_tasks.py
#!/usr/bin/env python3
"""§4.3 gate: every plan task MUST carry a non-empty touched_paths list and a
non-blank acceptance_cmd. touched_paths feeds the §4.5 concurrency DAG;
acceptance_cmd feeds the §4.6 anti-fake-completion supervisor's objective rerun.
Plans failing this are bounced back to the plan agent."""
import json
import sys


def validate_tasks(tasks):
    """Return {ok, errors}. Each task needs id, non-empty touched_paths, non-blank acceptance_cmd."""
    errors = []
    for i, t in enumerate(tasks):
        tid = t.get("id")
        label = tid if tid else f"<task #{i} missing id>"
        if not tid:
            errors.append(f"{label}: missing 'id'")
        paths = t.get("touched_paths")
        if not isinstance(paths, list) or len(paths) == 0:
            errors.append(f"{label}: missing or empty 'touched_paths'")
        cmd = t.get("acceptance_cmd")
        if not isinstance(cmd, str) or not cmd.strip():
            errors.append(f"{label}: missing or blank 'acceptance_cmd'")
    return {"ok": len(errors) == 0, "errors": errors}


def main(argv):
    path = argv[1] if len(argv) > 1 else "-"
    raw = sys.stdin.read() if path == "-" else open(path).read()
    tasks = json.loads(raw)
    if isinstance(tasks, dict):
        tasks = tasks.get("tasks", [])
    result = validate_tasks(tasks)
    if result["ok"]:
        print(f"OK: {len(tasks)} tasks each carry touched_paths + acceptance_cmd")
        return 0
    print("BLOCKED: plan tasks missing required fields (return to plan agent):")
    for e in result["errors"]:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd claude/megastorm/scripts && python3 -m pytest test_validate_plan_tasks.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add claude/megastorm/scripts/validate_plan_tasks.py claude/megastorm/scripts/test_validate_plan_tasks.py
git commit -m "feat(megastorm): plan-task validator (touched_paths + acceptance_cmd gate)"
```

---

## Task 2: `build_task_dag.py` — §4.5 deterministic orchestration

**Files:**
- Create: `claude/megastorm/scripts/build_task_dag.py`
- Test: `claude/megastorm/scripts/test_build_task_dag.py`

Output contract: `{ok, errors[], warnings[], layers[[id]], isolate[[a,b]]}` where `layers` are Kahn topo layers over `depends_on`, `isolate` are same-layer task pairs sharing any `touched_path` (need worktree isolation), `warnings` flag same-path mutual writers with no `depends_on`.

- [ ] **Step 1: Write the failing test**

```python
# claude/megastorm/scripts/test_build_task_dag.py
import unittest
from build_task_dag import build_dag


def _t(tid, paths, deps=None):
    return {"id": tid, "touched_paths": list(paths), "depends_on": list(deps or [])}


class TestBuildDag(unittest.TestCase):
    def test_linear_layers(self):
        tasks = [_t("a", ["x.py"]), _t("b", ["y.py"], ["a"]), _t("c", ["z.py"], ["b"])]
        r = build_dag(tasks)
        self.assertTrue(r["ok"], r["errors"])
        self.assertEqual(r["layers"], [["a"], ["b"], ["c"]])
        self.assertEqual(r["isolate"], [])

    def test_independent_same_layer_disjoint_files(self):
        tasks = [_t("a", ["x.py"]), _t("b", ["y.py"])]
        r = build_dag(tasks)
        self.assertEqual(sorted(r["layers"][0]), ["a", "b"])
        self.assertEqual(r["isolate"], [])

    def test_same_layer_file_collision_isolates(self):
        tasks = [_t("a", ["shared.py"]), _t("b", ["shared.py", "y.py"])]
        r = build_dag(tasks)
        self.assertEqual(sorted(r["layers"][0]), ["a", "b"])
        self.assertEqual([sorted(p) for p in r["isolate"]], [["a", "b"]])

    def test_collision_across_layers_not_isolated(self):
        # b depends on a, so they never run concurrently -> no isolation needed
        tasks = [_t("a", ["shared.py"]), _t("b", ["shared.py"], ["a"])]
        r = build_dag(tasks)
        self.assertEqual(r["isolate"], [])

    def test_mutual_write_no_dep_warns(self):
        tasks = [_t("a", ["shared.py"]), _t("b", ["shared.py"])]
        r = build_dag(tasks)
        self.assertTrue(any("shared.py" in w for w in r["warnings"]))

    def test_cycle_errors(self):
        tasks = [_t("a", ["x.py"], ["b"]), _t("b", ["y.py"], ["a"])]
        r = build_dag(tasks)
        self.assertFalse(r["ok"])
        self.assertTrue(any("cycle" in e for e in r["errors"]))

    def test_missing_dep_errors(self):
        tasks = [_t("a", ["x.py"], ["ghost"])]
        r = build_dag(tasks)
        self.assertFalse(r["ok"])
        self.assertTrue(any("ghost" in e for e in r["errors"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd claude/megastorm/scripts && python3 -m pytest test_build_task_dag.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build_task_dag'`

- [ ] **Step 3: Write minimal implementation**

```python
# claude/megastorm/scripts/build_task_dag.py
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
    return {"ok": True, "errors": errors, "warnings": warnings, "layers": layers, "isolate": isolate}


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd claude/megastorm/scripts && python3 -m pytest test_build_task_dag.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add claude/megastorm/scripts/build_task_dag.py claude/megastorm/scripts/test_build_task_dag.py
git commit -m "feat(megastorm): deterministic task-DAG builder (layers + collision isolation)"
```

---

## Task 3: `check_closure.py` — §4.2 deterministic closure lens

**Files:**
- Create: `claude/megastorm/scripts/check_closure.py`
- Test: `claude/megastorm/scripts/test_check_closure.py`

Inputs (assembled by the skill from Workflow structured outputs): `requirements` = all requirement IDs enumerated across module specs; `manifests` = per-design `{module, covers_req_ids[], exposes[], consumes[]}`. Deterministic checks: every requirement covered (forward); no design covers a ghost requirement (orphan→spec); every `consumes` matches some `exposes` (interface consistency). `exposes` never consumed = WARN (advisory). The prose-level "does the design truly satisfy the requirement" judgment stays in the LLM critic (Task on closure-critic.md), not here.

- [ ] **Step 1: Write the failing test**

```python
# claude/megastorm/scripts/test_check_closure.py
import unittest
from check_closure import check_closure


def _m(module, covers, exposes=(), consumes=()):
    return {"module": module, "covers_req_ids": list(covers),
            "exposes": list(exposes), "consumes": list(consumes)}


class TestCheckClosure(unittest.TestCase):
    def test_full_closure(self):
        reqs = ["R1", "R2", "R3"]
        manifests = [_m("a", ["R1", "R2"], exposes=["api:x"]),
                     _m("b", ["R3"], consumes=["api:x"])]
        r = check_closure(reqs, manifests)
        self.assertTrue(r["ok"], r["errors"])

    def test_uncovered_requirement(self):
        r = check_closure(["R1", "R2"], [_m("a", ["R1"])])
        self.assertFalse(r["ok"])
        self.assertTrue(any("R2" in e and "uncovered" in e for e in r["errors"]))

    def test_orphan_requirement_id(self):
        r = check_closure(["R1"], [_m("a", ["R1", "R9"])])
        self.assertFalse(r["ok"])
        self.assertTrue(any("R9" in e and "orphan" in e for e in r["errors"]))

    def test_dangling_consume(self):
        r = check_closure(["R1"], [_m("a", ["R1"], consumes=["api:ghost"])])
        self.assertFalse(r["ok"])
        self.assertTrue(any("api:ghost" in e for e in r["errors"]))

    def test_unconsumed_expose_warns(self):
        r = check_closure(["R1"], [_m("a", ["R1"], exposes=["api:unused"])])
        self.assertTrue(r["ok"], r["errors"])
        self.assertTrue(any("api:unused" in w for w in r["warnings"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd claude/megastorm/scripts && python3 -m pytest test_check_closure.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'check_closure'`

- [ ] **Step 3: Write minimal implementation**

```python
# claude/megastorm/scripts/check_closure.py
#!/usr/bin/env python3
"""§4.2 闭环 (closed-loop) deterministic lens. Operates on structured manifests the
design agents emit alongside their markdown (covers_req_ids / exposes / consumes),
NOT on prose. Checks: forward coverage (every spec requirement covered), no orphan
requirement ids (design->ghost req), interface consistency (every consume has a
matching expose). Unconsumed exposes are advisory WARNs. Prose-level 'does design
actually satisfy req' is the LLM critic's job, not this script's."""
import json
import sys


def check_closure(requirements, manifests):
    errors, warnings = [], []
    req_set = set(requirements)
    covered, exposes, consumes = set(), set(), set()
    for m in manifests:
        for rid in m.get("covers_req_ids", []):
            covered.add(rid)
            if rid not in req_set:
                errors.append(f"design '{m.get('module')}' covers orphan requirement '{rid}' (not in any spec)")
        for e in m.get("exposes", []):
            exposes.add(e)
        for c in m.get("consumes", []):
            consumes.add((m.get("module"), c))

    for rid in sorted(req_set - covered):
        errors.append(f"requirement '{rid}' is uncovered by any design")
    for module, c in sorted(consumes):
        if c not in exposes:
            errors.append(f"design '{module}' consumes '{c}' which no design exposes (dangling interface)")
    consumed_names = {c for _, c in consumes}
    for e in sorted(exposes - consumed_names):
        warnings.append(f"interface '{e}' is exposed but never consumed (possible orphan)")

    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}


def main(argv):
    if len(argv) < 3:
        print("usage: check_closure.py <requirements.json> <manifests.json>", file=sys.stderr)
        return 2
    requirements = json.load(open(argv[1]))
    manifests = json.load(open(argv[2]))
    if isinstance(requirements, dict):
        requirements = requirements.get("requirements", [])
    if isinstance(manifests, dict):
        manifests = manifests.get("manifests", [])
    r = check_closure(requirements, manifests)
    print(json.dumps(r, indent=2))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd claude/megastorm/scripts && python3 -m pytest test_check_closure.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add claude/megastorm/scripts/check_closure.py claude/megastorm/scripts/test_check_closure.py
git commit -m "feat(megastorm): deterministic closure lens (coverage/interface/orphan)"
```

---

## Task 4: `knowledge/schemas.md` — agent contracts

**Files:**
- Create: `claude/megastorm/knowledge/schemas.md`

- [ ] **Step 1: Write the file (complete content)**

````markdown
# megastorm — Workflow agent JSON schemas

These are the `schema` arguments passed to Workflow `agent()` calls. They force
structured output so the deterministic scripts have clean JSON to consume.

## escalation (spec §4 shared contract — every autonomous critic/fix agent returns this)
```json
{ "type": "object", "required": ["status"],
  "properties": {
    "status": { "type": "string", "enum": ["ok", "escalate"] },
    "reason": { "type": "string" },
    "evidence": { "type": "string" } } }
```
Rule: the skill (main session) reads the Workflow return; ANY `status:"escalate"`
halts the pipeline and renders `reason`+`evidence` to the human.

## design-manifest (spec §4.1 design agent emits one per module; feeds check_closure.py)
```json
{ "type": "object", "required": ["module", "design_path", "covers_req_ids", "exposes", "consumes"],
  "properties": {
    "module": { "type": "string" },
    "design_path": { "type": "string" },
    "covers_req_ids": { "type": "array", "items": { "type": "string" } },
    "exposes": { "type": "array", "items": { "type": "string" } },
    "consumes": { "type": "array", "items": { "type": "string" } } } }
```

## plan-task (spec §4.3; feeds validate_plan_tasks.py + build_task_dag.py)
```json
{ "type": "object", "required": ["id", "title", "touched_paths", "acceptance_cmd", "depends_on"],
  "properties": {
    "id": { "type": "string" },
    "title": { "type": "string" },
    "touched_paths": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
    "acceptance_cmd": { "type": "string" },
    "depends_on": { "type": "array", "items": { "type": "string" } } } }
```

## verdict (spec §4.6 supervisor — anti-fake-completion)
```json
{ "type": "object", "required": ["done", "rerun_exit_code", "evidence"],
  "properties": {
    "done": { "type": "boolean" },
    "rerun_exit_code": { "type": "integer" },
    "evidence": { "type": "string" },
    "refutation": { "type": "string" } } }
```
Rule: `done` is true ONLY if the supervisor independently reran `acceptance_cmd`
and got exit code 0 with the real output captured in `evidence`.
````

- [ ] **Step 2: Commit**

```bash
git add claude/megastorm/knowledge/schemas.md
git commit -m "feat(megastorm): agent JSON schemas (escalation/manifest/task/verdict)"
```

---

## Task 5: design + plan agent prompts

**Files:**
- Create: `claude/megastorm/knowledge/prompts/design-agent.md`
- Create: `claude/megastorm/knowledge/prompts/plan-agent.md`

These inline the brainstorming / writing-plans *methodology* so headless Workflow agents produce the same artifacts the interactive skills would, without blocking on a human (spec §0).

- [ ] **Step 1: Write `design-agent.md` (complete content)**

````markdown
# Design agent (Phase 1.1) — inlined brainstorming methodology

You are a headless design agent. You are given ONE module spec and the overview.
Produce a superpowers-style design document. You CANNOT ask the human anything —
all user decisions were front-loaded in Phase 0.

## Method (brainstorming, applied autonomously)
1. Read the module spec and the cross-module overview (interfaces of sibling modules).
2. Design units with clear boundaries: for each unit state what it does, its interface,
   its dependencies. Apply YAGNI — no unrequested features.
3. Cover: architecture, components, data flow, error handling, testing.
4. Write the design to `docs/superpowers/specs/<date>-<module>-design.md` (standard format).

## Decision boundary (spec §3 classifier)
- A choice that would change module boundaries / public interfaces / user-visible scope
  is a NEW HUMAN DECISION → do NOT decide it; return `status:"escalate"` with the question.
- A pure internal choice (naming, file org, private structures) → decide it, note it in the
  design's "Assumptions" section.

## Output (design-manifest schema + escalation)
Return JSON: `{status, module, design_path, covers_req_ids, exposes, consumes, reason?, evidence?}`
- `covers_req_ids`: the requirement IDs from the module spec this design satisfies.
- `exposes`: interfaces this module offers other modules (e.g. `api:createOrder`, `event:orderPaid`).
- `consumes`: interfaces this module needs from other modules.
- On a blocking new-human-decision: `status:"escalate"`, `reason` = the decision, `evidence` = context.
````

- [ ] **Step 2: Write `plan-agent.md` (complete content)**

````markdown
# Plan agent (Phase 1.3) — inlined writing-plans methodology

You are a headless planning agent. Given ONE module design, produce a superpowers-style
implementation plan as bite-sized TDD tasks. You CANNOT ask the human anything.

## Method (writing-plans, applied autonomously)
1. Map the files each task creates/modifies. One responsibility per file.
2. Decompose into bite-sized tasks: failing test → run-fail → implement → run-pass → commit.
3. No placeholders — every code step shows the actual code. DRY, YAGNI, TDD.
4. Write the plan to `docs/superpowers/plans/<date>-<module>-plan.md`.

## HARD CONSTRAINT (spec §4.3) — every task object MUST carry:
- `id`: stable task id, e.g. `T-<module>-01`.
- `title`: one line.
- `touched_paths`: every file the task creates/modifies (non-empty). Drives §4.5 concurrency.
- `acceptance_cmd`: a machine-checkable command that exits 0 iff the task is truly done
  (e.g. `python3 -m pytest path/test_x.py`, `npm run build`). Drives §4.6 supervisor.
- `depends_on`: ids of tasks that must complete first ([] if none).

## Output (array of plan-task schema + escalation)
Return JSON: `{status, plan_path, tasks: [ {id,title,touched_paths,acceptance_cmd,depends_on} ], reason?, evidence?}`
Escalate (don't guess) if the design is under-specified in a way that needs a human decision.
````

- [ ] **Step 3: Commit**

```bash
git add claude/megastorm/knowledge/prompts/design-agent.md claude/megastorm/knowledge/prompts/plan-agent.md
git commit -m "feat(megastorm): design + plan agent prompts (inlined methodology)"
```

---

## Task 6: closure + reverse critic prompts

**Files:**
- Create: `claude/megastorm/knowledge/prompts/closure-critic.md`
- Create: `claude/megastorm/knowledge/prompts/reverse-critic.md`

- [ ] **Step 1: Write `closure-critic.md` (complete content)**

````markdown
# Closure critic (Phase 1.2) — 闭环思维 (LLM half)

The deterministic half (coverage / interface / orphan) already ran via `check_closure.py`.
You judge the part scripts cannot: does each design *actually and adequately* satisfy the
spec requirements it claims to cover, and are cross-module interfaces semantically (not just
nominally) consistent?

## Check
- For each `covers_req_ids` claim: read the requirement and the design section. Is the
  requirement genuinely met, or only name-matched? Flag hollow coverage.
- For each exposes/consumes pair: do the two sides agree on shape/semantics, not just the name?
- Any design element that traces to NO requirement (dead design)?

## Self-fix loop (spec §4.2, ≤K rounds, K=3 for this stage)
If you find fixable gaps that need no new human decision, EDIT the design docs to close them.
Re-run only happens if you changed something.

## Output (escalation schema)
- All closed → `{status:"ok"}`.
- A gap needs a NEW human decision (module boundary / public interface / user-visible scope),
  or you cannot converge in K rounds → `{status:"escalate", reason, evidence}`.
````

- [ ] **Step 2: Write `reverse-critic.md` (complete content)**

````markdown
# Reverse critic (Phase 1.4) — 逆向思维

Work BACKWARD from the plans/designs to the specs. Do not read forward and nod along —
actively try to refute that this will work.

## Check (backward feasibility)
- Take each plan and ask: if an engineer executes these exact steps, do they end up
  satisfying the design and spec? Where does it break?
- Hunt hidden assumptions, missing prerequisites, infeasible steps, unhandled error/edge paths.
- For each `acceptance_cmd`: is it actually a meaningful check, or a tautology that would pass
  without the feature working? Flag weak acceptance commands (directly guards against §4.6 being gamed).

## Self-fix loop (spec §4.4, ≤K rounds, K=3 for this stage)
Fixable, no-new-decision issues → edit the spec/design/plan docs and re-run.

## Output (escalation schema)
- Sound → `{status:"ok"}`.
- Needs new human decision or non-convergent → `{status:"escalate", reason, evidence}`.
````

- [ ] **Step 3: Commit**

```bash
git add claude/megastorm/knowledge/prompts/closure-critic.md claude/megastorm/knowledge/prompts/reverse-critic.md
git commit -m "feat(megastorm): closure + reverse critic prompts"
```

---

## Task 7: executor + supervisor prompts

**Files:**
- Create: `claude/megastorm/knowledge/prompts/executor.md`
- Create: `claude/megastorm/knowledge/prompts/supervisor.md`

- [ ] **Step 1: Write `executor.md` (complete content)**

````markdown
# Executor agent (Phase 1.6) — inlined executing-plans discipline — MODEL: sonnet

You implement ONE task from a plan. You run on Sonnet (bulk mechanical work, token-thrifty).

## Discipline (executing-plans, applied per task)
1. Follow the task's TDD steps exactly: write the failing test, see it fail, implement
   minimally, see it pass, commit.
2. Touch ONLY the files in the task's `touched_paths`. If you must touch a file outside that
   set, stop and return `status:"escalate"` (it means the plan's touched_paths was wrong).
3. Run the task's `acceptance_cmd` yourself before claiming done. Do not claim done if it fails.

## Isolation
If told you are running in a worktree (`isolation:'worktree'`), work entirely within it;
the orchestrator merges after the supervisor confirms.

## Output
Return JSON: `{status:"ok"|"escalate", task_id, acceptance_cmd, self_reported_done, notes, reason?, evidence?}`.
Your self-report is NOT trusted — an independent supervisor will rerun acceptance_cmd. Do not
inflate. If blocked on a real ambiguity, escalate rather than guess.
````

- [ ] **Step 2: Write `supervisor.md` (complete content)**

````markdown
# Supervisor agent (Phase 1.6) — anti-fake-completion verifier — MODEL: default (Opus)

You independently verify ONE task the executor claims done. You are adversarial and you run
on the default model — verification rigor is the trust root; never trade it for tokens.

## Independence
You are given ONLY: the task definition, its `acceptance_cmd`, and the current repo state.
You are NOT given the executor's narrative or self-report. You do not trust claims; you trust
reruns. (This directly addresses the recorded #1 defect: verification that reads self-reports
instead of testing the running reality.)

## Verify
1. Rerun `acceptance_cmd` yourself. Capture the real exit code and stdout/stderr.
2. `done` is true ONLY if exit code == 0 AND the output shows the task's behavior genuinely works
   (not an empty/tautological pass).
3. Read the real diff: do the changes actually correspond to the task's intent, in the right files?
4. Default to disbelief: rerun failed / no acceptance_cmd / insufficient evidence → `done:false`.

## Output (verdict schema)
`{done, rerun_exit_code, evidence: "<real captured output>", refutation?}`.
On `done:false`, `refutation` says exactly what failed. The orchestrator bounces the task back
to the executor (shared soft-retry budget ≤2); still fake → escalate to the human.
````

- [ ] **Step 3: Commit**

```bash
git add claude/megastorm/knowledge/prompts/executor.md claude/megastorm/knowledge/prompts/supervisor.md
git commit -m "feat(megastorm): executor (sonnet) + supervisor (opus) prompts"
```

---

## Task 8: `skills/megastorm.md` — orchestration brain

**Files:**
- Create: `claude/megastorm/skills/megastorm.md`

This is the only orchestration prose. It references the scripts and prompts and contains the per-phase Workflow templates. It is written for the main session (which has the Workflow tool).

- [ ] **Step 1: Write the file (complete content)**

````markdown
---
name: megastorm
description: Drive a large goal end-to-end — decompose into modules, front-load all decisions via brainstorming, then autonomously produce designs, validate (closed-loop), plan, reverse-review, orchestrate, and concurrently execute with anti-fake-completion supervision. Explicitly invoked via /megastorm; heavy and token-intensive.
---

# megastorm — large-goal autonomous pipeline

**Invariant:** decisions front-loaded → autonomous → self-fix loop, escalate-to-stop.
All human interaction is in Phase 0. Phase 1 runs without human stops except on escalation.
Spec: `docs/superpowers/specs/2026-06-09-megastorm-pipeline-design.md`.

`$ROOT` = `${CLAUDE_PLUGIN_ROOT}`. Schemas: `$ROOT/knowledge/schemas.md`. Prompts: `$ROOT/knowledge/prompts/`.
Scripts: `$ROOT/scripts/`.

## Phase -1 — Preflight (main session)
Verify the Skill registry exposes `superpowers:brainstorming`, `superpowers:writing-plans`,
`superpowers:executing-plans` (namespaced — do NOT check `~/.claude/skills/<name>/` paths;
they live under the superpowers plugin cache and the version drifts). If any is missing, STOP
and tell the user to install the superpowers marketplace via `/plugin`. Do not proceed.

## Phase 0 — Decisions front-loaded (main session, INTERACTIVE)
1. Analyze current state: repo structure, recent commits, `docs/`. Summarize.
2. Decompose the goal into M modules + boundaries + inter-module deps by running
   `Skill: superpowers:brainstorming`. Get the user to approve the module breakdown.
   Write the draft overview to `docs/superpowers/specs/<date>-<goal>-overview.md` (module
   table + dependency graph). Each module spec MUST enumerate machine-readable requirement
   IDs (`R-<module>-NN`) — these feed the closure check.
3. For EACH module, run `Skill: superpowers:brainstorming` to produce a standard module
   spec/design; the user approves each. Done when all M specs exist and are approved.
4. **New-human-decision rule (boundary for Phase 1):** anything changing module boundaries,
   public/cross-module interfaces, or user-visible scope = escalate. Internal-only choices =
   the autonomous agents decide and log. This is what makes Phase 1 safe to run unattended.

After Phase 0, do not stop for the human until an escalation surfaces.

## Phase 1 — Autonomous pipeline (call Workflow once per stage; read result; decide next)
For every stage, read the Workflow return. If ANY agent returned `status:"escalate"`, HALT,
render `reason`+`evidence` to the user, get the decision, then re-run that stage. Otherwise continue.

Model policy: design / closure-critic / plan / reverse-critic / supervisor = default (Opus).
Executor = `{model:'sonnet'}`. (Token thrift on bulk coding only; verification stays Opus.)

### 1.1 Design — Workflow
Author a Workflow that `pipeline`s/`parallel`s over the M module specs; each `agent` uses
`$ROOT/knowledge/prompts/design-agent.md` and the design-manifest schema. Collect the manifests.

### 1.2 Closure check — deterministic then LLM
- Assemble `requirements.json` (all `R-*` ids from specs) and `manifests.json` (design manifests).
- Run `python3 $ROOT/scripts/check_closure.py requirements.json manifests.json`. If it BLOCKs,
  feed errors to a fix `agent` (design-agent prompt) and re-run, ≤3 rounds.
- Then run a Workflow `agent` with `closure-critic.md` for the prose-level judgment (≤3 rounds).
- Unresolved after rounds, or any escalate → HALT to user.

### 1.3 Plan — Workflow
`pipeline` over designs; each `agent` uses `plan-agent.md` and emits the plan-task array.
For each plan, run `python3 $ROOT/scripts/validate_plan_tasks.py <tasks.json>`; if BLOCKED,
bounce back to the plan agent until every task has `touched_paths` + `acceptance_cmd`.

### 1.4 Reverse review — Workflow
A Workflow `agent` with `reverse-critic.md` over all spec/design/plan docs (≤3 rounds, self-fix
or escalate).

### 1.5 Orchestrate — deterministic
Concatenate all plan tasks into one array, run
`python3 $ROOT/scripts/build_task_dag.py <all-tasks.json>`. BLOCK (cycle/missing dep) → fix via
plan agent. Keep `layers` (execution order) and `isolate` (same-layer file-colliding pairs).
Persist to `orchestration.json`. Surface any `warnings` in the final report.

### 1.6 Concurrent execute + supervise — Workflow
For each layer in order, `pipeline(tasks_in_layer, executeStage, verifyStage)`:
- executeStage: `agent(executor.md prompt, {model:'sonnet'})`. If this task id appears in any
  `isolate` pair, pass `{isolation:'worktree'}`.
- verifyStage: `agent(supervisor.md prompt, {schema: verdict})` — default model, fresh context,
  reruns `acceptance_cmd`. `done:false` → bounce to executor (shared soft-retry ≤2 per task);
  still false → escalate.
- Merge worktree-isolated tasks back only after the supervisor confirms `done:true`.

## Phase 2 — Report
Update the overview and write a final report: assumptions the autonomous agents made, all
escalation points + resolutions, the independently-verified completion list (distinguish
"executor-claimed" from "supervisor-confirmed"), DAG warnings, and learnings.

## Artifacts (superpowers-native)
One overview + standard superpowers docs:
`docs/superpowers/specs/<date>-<goal>-overview.md`, `...-<module>-design.md`,
`docs/superpowers/plans/<date>-<module>-plan.md`, plus machine `orchestration.json`.
````

- [ ] **Step 2: Verify frontmatter + references are well-formed**

Run: `python3 -c "import re,sys; t=open('claude/megastorm/skills/megastorm.md').read(); assert t.startswith('---'); assert 'name: megastorm' in t; assert 'description:' in t; print('frontmatter OK')"`
Expected: `frontmatter OK`

- [ ] **Step 3: Commit**

```bash
git add claude/megastorm/skills/megastorm.md
git commit -m "feat(megastorm): orchestration brain skill (Phase -1..2 + Workflow templates)"
```

---

## Task 9: plugin manifest + marketplace + command

**Files:**
- Create: `claude/megastorm/.claude-plugin/plugin.json`
- Create: `claude/megastorm/.claude-plugin/marketplace.json`
- Create: `claude/megastorm/commands/megastorm.md`

- [ ] **Step 1: Write `plugin.json`**

```json
{
  "name": "megastorm",
  "description": "Large-goal autonomous pipeline: decompose into modules, front-load decisions via brainstorming, then autonomously design → closed-loop validate → plan → reverse-review → orchestrate → concurrently execute with anti-fake-completion supervision. Global command /megastorm.",
  "version": "0.1.0",
  "author": { "name": "dv" }
}
```

- [ ] **Step 2: Write `marketplace.json`**

```json
{
  "name": "megastorm",
  "owner": {
    "name": "dv"
  },
  "plugins": [
    {
      "name": "megastorm",
      "version": "0.1.0",
      "source": "./",
      "description": "Chains superpowers brainstorming/writing-plans/executing-plans into a Workflow-driven pipeline for large goals. Explicit /megastorm trigger."
    }
  ]
}
```

- [ ] **Step 3: Write `commands/megastorm.md`**

```markdown
---
name: megastorm
description: Drive a large goal end-to-end — decompose, front-load decisions, then autonomously design/validate/plan/review/execute with supervision.
arguments:
  - name: goal
    description: The large goal to build out
    required: true
---

Invoke the megastorm skill to run the full large-goal pipeline for: $ARGUMENTS

> Read ${CLAUDE_PLUGIN_ROOT}/skills/megastorm.md and follow its protocol, starting at Phase -1 (preflight).
```

- [ ] **Step 4: Validate JSON**

Run: `python3 -c "import json; json.load(open('claude/megastorm/.claude-plugin/plugin.json')); json.load(open('claude/megastorm/.claude-plugin/marketplace.json')); print('JSON OK')"`
Expected: `JSON OK`

- [ ] **Step 5: Commit**

```bash
git add claude/megastorm/.claude-plugin/ claude/megastorm/commands/
git commit -m "feat(megastorm): plugin manifest, marketplace listing, /megastorm command"
```

---

## Task 10: integration self-check + install wiring

**Files:**
- Create: `claude/megastorm/scripts/check_skill_refs.py`
- Create: `claude/megastorm/scripts/test_check_skill_refs.py`
- Modify: `claude/install.sh:7` (the `for plugin in ...` loop)

This guards against the SKILL.md referencing a script/prompt file that doesn't exist (the run-engine "sync-check" spirit).

- [ ] **Step 1: Write the failing test**

```python
# claude/megastorm/scripts/test_check_skill_refs.py
import os
import unittest
from check_skill_refs import check_refs

HERE = os.path.dirname(__file__)
PLUGIN_ROOT = os.path.abspath(os.path.join(HERE, ".."))


class TestCheckRefs(unittest.TestCase):
    def test_real_plugin_refs_resolve(self):
        r = check_refs(PLUGIN_ROOT)
        self.assertTrue(r["ok"], r["missing"])

    def test_detects_missing(self):
        r = check_refs(PLUGIN_ROOT, extra_required=["knowledge/prompts/does-not-exist.md"])
        self.assertFalse(r["ok"])
        self.assertIn("knowledge/prompts/does-not-exist.md", r["missing"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd claude/megastorm/scripts && python3 -m pytest test_check_skill_refs.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'check_skill_refs'`

- [ ] **Step 3: Write minimal implementation**

```python
# claude/megastorm/scripts/check_skill_refs.py
#!/usr/bin/env python3
"""Integration self-check: every script + prompt the megastorm skill relies on must
exist on disk. Run after editing the skill or moving files (run-engine sync-check spirit)."""
import os
import sys

# The files skills/megastorm.md references via $ROOT/...
REQUIRED = [
    "knowledge/schemas.md",
    "knowledge/prompts/design-agent.md",
    "knowledge/prompts/plan-agent.md",
    "knowledge/prompts/closure-critic.md",
    "knowledge/prompts/reverse-critic.md",
    "knowledge/prompts/executor.md",
    "knowledge/prompts/supervisor.md",
    "scripts/validate_plan_tasks.py",
    "scripts/build_task_dag.py",
    "scripts/check_closure.py",
    "skills/megastorm.md",
    "commands/megastorm.md",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
]


def check_refs(plugin_root, extra_required=None):
    required = REQUIRED + list(extra_required or [])
    missing = [rel for rel in required if not os.path.isfile(os.path.join(plugin_root, rel))]
    return {"ok": len(missing) == 0, "missing": missing}


def main(argv):
    root = argv[1] if len(argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    r = check_refs(root)
    if r["ok"]:
        print(f"OK: all {len(REQUIRED)} referenced files present")
        return 0
    print("BLOCKED: skill references missing files:")
    for m in r["missing"]:
        print(f"  - {m}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd claude/megastorm/scripts && python3 -m pytest test_check_skill_refs.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Wire install.sh**

Modify `claude/install.sh` line 7 — change the plugin loop to include megastorm:

```bash
for plugin in meta-skill megastorm; do
```

(Registering the plugin via `claude plugin add` is what makes `/megastorm` globally available — no separate command install needed.)

- [ ] **Step 6: Run the full megastorm test suite + install dry check**

Run: `cd claude/megastorm/scripts && python3 -m pytest -v && cd - && grep -q "megastorm" claude/install.sh && echo "install wired"`
Expected: all tests PASS (21 total across the 4 test files) and `install wired`

- [ ] **Step 7: Commit**

```bash
git add claude/megastorm/scripts/check_skill_refs.py claude/megastorm/scripts/test_check_skill_refs.py claude/install.sh
git commit -m "feat(megastorm): integration self-check + install.sh wiring"
```

---

## Self-Review

**1. Spec coverage:**
- §0 primitives → Task 8 skill pins Workflow/skill boundary + model policy; prompts (Tasks 5–7) inline methodologies. ✓
- §1 packaging → Tasks 9–10 (manifest, command, install wiring; global command via plugin registration). ✓
- §2 preflight → Task 8 Phase -1 (namespaced registry check, no path hardcode). ✓
- §3 Phase 0 + new-human-decision rule → Task 8 Phase 0. ✓
- §4.1 design → Tasks 5 + 8.1.1. §4.2 closure → Task 3 (deterministic) + Task 6 (LLM) + 8.1.2. ✓
- §4.3 plan + touched_paths/acceptance_cmd → Tasks 1, 5, 8.1.3. ✓
- §4.4 reverse → Tasks 6, 8.1.4. §4.5 DAG → Task 2 + 8.1.5. ✓
- §4.6 execute + supervisor → Tasks 7, 8.1.6. ✓
- §5 report → Task 8 Phase 2. §6 artifacts → Task 8 Artifacts. §7 thinking semantics → Tasks 3/6 (closure), 6 (reverse). ✓
- Escalation contract → Task 4 schemas + Task 8 Phase 1 intro. ✓

**2. Placeholder scan:** No TBD/TODO. Every Python step has full code; every markdown file has full content; commands have exact expected output.

**3. Type consistency:** `touched_paths`/`acceptance_cmd`/`depends_on`/`id` consistent across schemas.md (Task 4), validate_plan_tasks.py (Task 1), build_task_dag.py (Task 2), plan-agent.md (Task 5). `covers_req_ids`/`exposes`/`consumes` consistent across schemas.md, check_closure.py (Task 3), design-agent.md (Task 5). `status`/`reason`/`evidence` escalation consistent across schemas.md and all prompts. verdict `done`/`rerun_exit_code`/`evidence` consistent (Task 4, Task 7 supervisor). check_skill_refs REQUIRED list matches the files created in Tasks 4–9. ✓

**Note on test count:** Task 1 (7) + Task 2 (7) + Task 3 (5) + Task 10 (2) = 21 tests.
````
