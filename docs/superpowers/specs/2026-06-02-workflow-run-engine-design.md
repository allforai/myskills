# Workflow-Based `/run` Engine — Design Spec

**Date:** 2026-06-02
**Status:** Design (pending implementation plan)
**Scope:** `claude/meta-skill/` — rewrite the `/run` execution engine on top of Claude Code's `Workflow` tool.
**Platform:** Claude Code only. Codex/OpenCode retain the existing markdown loop (see Non-Goals).

---

## 1. Problem & Intent

### 1.1 Current state

The meta-skill already implements a hand-rolled orchestration runtime:

- `bootstrap` analyzes a target project and generates `.allforai/bootstrap/workflow.json` (a node DAG) plus `node-specs/*.md`.
- `/run` is a **model-driven loop**: the main-loop Claude reads `workflow.json`, picks the next ready node, dispatches a subagent, then hand-edits `transition_log` to record the result.

Problems with the model-driven loop:

1. **Burns main-context tokens** and is fragile across context compaction (Claude can lose track of "where am I in the run").
2. **Non-deterministic bookkeeping**: Claude may pick the wrong node, forget to record a transition, or mis-parse exit-artifact gates.
3. **Serial bias**: parallelism depends on a runtime judgment that, in a single Claude loop, usually degrades to serial — so `alignment_refs` siblings rarely actually run concurrently.

### 1.2 Design intent (user-stated, non-negotiable)

> **All human decisions happen up front. The long task does not stop in the middle to ask the human.**

This drives the whole architecture, taken to its conclusion: **all human interaction is consolidated into `/bootstrap`** (goal + A0 audit + Phase A decisions), and **`/run` is fully autonomous from start to finish** — the engine runs the entire DAG with zero human stops. The only halt is a catastrophic `UNRESOLVED` failure.

### 1.3 Goals

- Replace the `/run` execution loop with a **deterministic Workflow-based engine** (a generic JS interpreter of `workflow.json`).
- Make `alignment_refs` siblings **actually run in parallel**.
- Move **all human-decision points up front** and conduct them via a brainstorming-lite protocol.
- Add **planning-time audits**: a node-granularity audit (G0, right-size nodes for single-task attention) and a decision-coverage audit (A0, catch decisions before the run, not during it).
- Keep `workflow.json` as the single durable ground truth; make the engine **idempotent** against it (cross-session safe).

---

## 2. Non-Goals

- **Tri-platform parity.** Platform priority is **CC first, Codex second, OpenCode least**. We do **not** compromise CC's optimal design to keep the other two in sync. Codex/OpenCode keep their markdown loop and simply **ignore CC-only superset fields** in `workflow.json`. Capabilities expressible only in the JS engine are CC-only by design.
- **Replacing `workflow.json` as the schema/ground truth.** The Workflow engine is an *executor* that reads/writes the same file.
- **Replacing Claude-driven failure diagnosis.** Hard failures still surface to `diagnosis.md` (the engine routes, it does not diagnose).
- **A general workflow authoring tool.** This is one specific engine for meta-skill's generated DAGs.

---

## 3. Architecture Overview

### 3.1 Three-phase model

```
╔═══ /bootstrap  (ALL human interaction lives here) ═══════════╗
║  confirm goal (Step 1.5)  → analyze → generate nodes          ║
║        │                                                      ║
║        ▼                                                      ║
║  G0  Node-Granularity Audit ── right-size each node to its    ║
║        attention budget; split-too-coarse + merge-too-fine    ║
║        → granularity-audit.json ; restructures the DAG        ║
║        │                                                      ║
║        ▼                                                      ║
║  A0  Decision-Coverage Audit ── dual-angle (concept ⨁ node)   ║
║        → decision-coverage.json ; missing → Phase A queue     ║
║        │                                                      ║
║        ▼                                                      ║
║  Phase A  Decision Gathering  (interactive · the ONLY place   ║
║        │   humans are asked)                                  ║
║        │   brainstorming-lite per decision node → artifacts   ║
║        │   pre-run predictable expanders to surface early     ║
╚══════════════════════════════════════════════════════════════╝
        │  all decision artifacts on disk
╔═══ /run  (FULLY AUTONOMOUS · zero interaction) ══════════════╗
║  Phase B  Autonomous Execution  (LONG TASK · zero human stops)║
║        │   Workflow engine runs the full DAG to completion    ║
║        │   soft fail → self-heal ; hard fail → Claude diagnose ║
║        │   emergent decision → assume + declare (no stop)     ║
║        │   only UNRESOLVED halts                              ║
║        ▼                                                      ║
║  Phase C  Report  → assumed decisions + UNRESOLVED + learning ║
╚══════════════════════════════════════════════════════════════╝
```

**Ordering note (G0 before A0):** granularity restructuring splits/merges nodes, which changes *which* decisions live on *which* node. So right-size the nodes first (G0), then audit decision coverage over the right-sized graph (A0), then gather decisions (Phase A).

**Command boundary:** **All human interaction is consolidated into `/bootstrap`** — goal confirmation (existing Step 1.5), the G0/A0 audits, and Phase A decision-gathering. `/bootstrap` exits only when every decision artifact is on disk. `/run` is then **fully autonomous from start to finish** — no questions, no stops (except catastrophic `UNRESOLVED`). It can be backgrounded and left unattended. User-facing flow is unchanged: still `/bootstrap` then `/run`; the shift is that `/bootstrap` absorbs all decisions and `/run` becomes a pure long-running autonomous task.

Trade-off: `/bootstrap` grows from "quick analysis" into "analysis + gather all decisions"; in return `/run` needs zero human attention.

### 3.2 Layer responsibilities

| Layer | Responsibility | Implementation |
|-------|----------------|----------------|
| `/bootstrap` skill (main-loop Claude) | Confirm goal; generate nodes; run G0 granularity audit (restructure DAG); run A0 decision-coverage audit; run Phase A brainstorming-lite → write all decision artifacts | markdown skill |
| `/run` skill (main-loop Claude) | Drive Phase B → C autonomously; on `needs_diagnosis` run `diagnosis.md`; resume the engine between segments — no human interaction | markdown skill |
| Workflow engine (`run-engine.workflow.js`) | Read DAG → topo-schedule → run ready nodes in parallel → validate → self-heal soft failures → commit → return on completion/hard-failure | one **generic** JS interpreter in plugin `knowledge/run-engine/` (NOT `knowledge/engine/` — `knowledge/engines/` already exists for game-engine knowledge files; avoid the near-collision) |
| Engine-core (`engine-core.js`) | Pure decision logic (no `agent()` calls) | plain JS module, unit-tested |
| Node subagents | Read node-spec, do file I/O, run validation, return schema-validated result | `agent(spec, {schema})` |

### 3.3 Foundations (the four invariants)

1. **CC-first superset schema.** `workflow.json` base fields are read by all platforms; CC-only fields (`closure_verify`, `soft_retry_max`, `decision_mode`, …) are consumed only by the JS engine and ignored elsewhere.
2. **`workflow.json` idempotency.** `transition_log` is the durable skip-list. Nodes already `completed` are skipped on re-entry. Workflow's `resumeFromRunId` cache is an *optimization only* — losing it (cross-session) re-runs only the cheap `load-DAG` agent, never completed business nodes.
3. **Engine routes, never diagnoses.** Intelligence is pushed down into each node subagent's `blocking_findings` self-report flag; the engine routes purely on `outcome` + flag.
4. **Hybrid failure recovery.** Soft failures (placeholder / missing field) self-heal in-engine; hard failures (cross-node root cause) surface to Claude. Convergence cap: same root cause ≥ 2 diagnoses → `UNRESOLVED`, halt with best-effort output + TODO.

---

## 4. Component Design

### 4.1 Data contracts (the two schemas)

The engine recognizes only two structured objects; everything else is plain JS (unit-testable).

```js
// load-DAG agent returns this
const DAG_SCHEMA = {
  type: 'object',
  required: ['nodes', 'completed'],
  properties: {
    nodes: { type: 'array', items: { type: 'object',
      required: ['node_id','capability','hard_blocked_by','exit_artifacts'],
      properties: {
        node_id:         { type: 'string' },
        capability:      { type: 'string' },
        hard_blocked_by: { type: 'array', items: { type: 'string' } },
        alignment_refs:  { type: 'array', items: { type: 'string' } },
        exit_artifacts:  { type: 'array', items: { type: 'object' } }, // {path, validation_commands}
        node_spec_path:  { type: 'string' },
        profile_slice:   { type: 'object' },   // bootstrap-profile fields this node needs (tech stack, scenario, paths)
        // —— CC-first superset (other platforms ignore) ——
        decision_mode:   { type: 'string', enum: ['brainstorm','none'] },
        decision_inputs: { type: 'array', items: { type: 'string' } }, // required decision-<x>.json paths (former human_gate)
        closure_verify:  { type: 'array', items: { type: 'string' } }, // ['audio','save-load','2d-placeholder']
        soft_retry_max:  { type: 'integer' }                           // default 2
      } } },
    completed:        { type: 'array', items: { type: 'string' } },  // idempotent skip-list (from transition_log)
    expanders:        { type: 'array', items: { type: 'string' } },  // NEW field bootstrap must emit (see §4.2.2)
    applied_expanders:{ type: 'array', items: { type: 'string' } }   // expanders already run (cross-session skip — fix C5)
  }
}

// each node subagent returns this
const NODE_RESULT_SCHEMA = {
  type: 'object',
  required: ['node_id','outcome','artifacts_written','blocking_findings'],
  properties: {
    node_id:           { type: 'string' },
    outcome:           { type: 'string', enum: ['passed','soft_fail','hard_fail'] },
    artifacts_written: { type: 'array', items: { type: 'string' } },
    blocking_findings: { type: 'array', items: { type: 'object' } },
      // [{type:'placeholder'|'failed_validation'|'cross_node'|..., detail, suspected_root_node?}]
    assumed_decisions: { type: 'array', items: { type: 'object' } }, // emergent decisions assumed by this node (fix C1) — engine, not subagent, persists them
    summary:           { type: 'string' }
  }
}
```

`outcome` is decided by the node subagent (only it can read files / run `validation_commands` — engine scripts cannot touch the filesystem). The engine reads `outcome` + `blocking_findings` for routing only.

**On `human_gate` removal (reviewer reconciliation).** The current `workflow.json` carries `human_gate: true` + an interactive approval-record/web-dashboard loop. In this design that runtime concept is **removed** — it contradicts "zero stops in `/run`". A former human-gated node is re-expressed as a normal node with `decision_inputs: ['…/decision-<x>.json']`: the *direction* it used to gate is now decided up front in Phase A (generation-before), and the decision artifact becomes a **required input** the node subagent reads. The engine has **no gate function** and `computeReady` does **not** consult any approval state. If a `decision_inputs` artifact is missing at runtime, the node subagent returns `hard_fail` (a planning bug — Phase A should have produced it). Bootstrap asserts, before `/run`, that every `decision_inputs` reference has a corresponding artifact on disk.

**On `profile_slice`.** load-DAG copies only the `bootstrap-profile.json` fields a node actually needs (tech stack, scenario, target paths) into `profile_slice`, so the engine never re-reads the profile and node subagents get their context inline.

### 4.2 Engine seven parts (`run-engine.workflow.js`, Phase B)

1. **load-DAG** — one agent reads `workflow.json` (+ slices `bootstrap-profile.json` into each node's `profile_slice`) → `DAG_SCHEMA`. Build `done = new Set(dag.completed)` from `transition_log` (status `completed`).
2. **expand** — `dag.expanders` is a **new field bootstrap emits** listing the project-local expander scripts that apply (today expansion is hardcoded — e.g. `expand_game_2d_production.py` invoked imperatively in `orchestrator-template.md`; this design promotes it to a declared list). For each expander **not already in `dag.applied_expanders`** (fix C5 — cross-session double-expansion guard), an agent **runs the script** (it mutates `workflow.json` in place, the existing behavior — file I/O stays in the agent, not the engine script) and returns the resulting node set; the same agent records the expander into `applied_expanders`. The engine reconciles in-memory via the pure `mergeExpanded(nodes, newNodes)` (skips existing `node_id`, idempotent on re-entry). **Boundary:** the script owns `workflow.json` mutation; `mergeExpanded` only updates the engine's in-memory `dag.nodes`. Expander scripts MUST be file-idempotent (re-running adds no duplicate nodes); the `applied_expanders` skip is belt-and-suspenders for the non-idempotent case. This is the "plan auto-updates during the run" capability.
3. **computeReady** — `nodes.filter(n => !done.has(n.node_id) && n.hard_blocked_by.every(d => done.has(d)))`. **`alignment_refs` do NOT block** — present them as read-if-available; this is the source of free parallelism. No approval/gate state is consulted (see human_gate removal note above).
4. **pipeline batch** — the ready batch flows through a `pipeline()` (run → commit), no barrier on *running*: a node that passes starts committing while siblings still run. **Commits are serialized** through a single-writer queue (fix C1) — see §4.4.
5. **runNode** — dispatch the node-spec (+ `profile_slice` + read `decision_inputs`) as a subagent with `NODE_RESULT_SCHEMA`; internal soft-retry loop (≤ `soft_retry_max`, default 2) with progressively stricter prompts; includes `closure_verify` instructions when present. A node that must assume an emergent decision (§5) returns it in `assumed_decisions[]` — it does **not** write any file itself (fix C1); the engine persists it during the serialized commit.
6. **commit** — on pass, a commit agent appends to `transition_log` (+ any `assumed_decisions` to `assumed-decisions.json`) and `done.add(node_id)`. **All commit agents run through a serialization queue so writes to `workflow.json` never overlap** (fix C1): each commit `await`s the previous one. Logical "commit immediately" is preserved (a passed node enqueues its commit at once); only the physical writes are serialized. Per-node, never batched — crash/re-entry loses zero progress.
7. **exits** — Phase B has **two** exits: `complete` (all done) and `needs_diagnosis` (always carrying a non-empty `hardFailures[]`). A **stuck graph** (ready set empty but nodes remain — a `hard_blocked_by` cycle or a dep on a missing/expander-introduced node, with no real hard failures) is surfaced as `needs_diagnosis` with a **synthesized `deadlock` hard failure** naming the stuck nodes (fix C3) — never an empty-`hardFailures` return. There is no `gates_pending` exit: decisions are front-loaded, so a missing `decision_inputs` artifact mid-run is a planning bug surfaced as a hard failure.

### 4.3 Soft/hard routing (`routeOutcome`, the hybrid heart)

Two rules, applied to a failed node's `blocking_findings`:

1. Any finding with `type:'cross_node'` or a `suspected_root_node` → **hard fail immediately** (do not retry; the root cause is elsewhere).
2. Otherwise (placeholder / missing field / failed validation) → **soft fail**; retry the same node ≤ `soft_retry_max` with a stricter prompt; on exhaustion → hard fail.

The engine **trusts the subagent's self-reported flag**. Mislabel risk is bounded: a mislabeled `cross_node`-as-soft wastes at most `soft_retry_max` retries, then converts to hard and surfaces to Claude anyway — it never deadlocks.

**Note on `failed_validation`.** A failed `validation_command` is soft by default (rule 2), but it can also stem from an upstream cause. The node subagent MUST attach `suspected_root_node` when it attributes a validation failure elsewhere — otherwise the engine pointlessly retries `soft_retry_max` times before giving up. "Soft vs hard" is the subagent's call via the flag, not the finding `type`.

### 4.4 pipeline shape (v1) + commit serialization (fix C1)

```js
// commit serialization queue: physical writes to workflow.json never overlap,
// even though runNode of siblings runs concurrently.
let commitQueue = Promise.resolve()
function serializeCommit(fn) {
  commitQueue = commitQueue.then(fn, fn)   // chain regardless of prior outcome
  return commitQueue
}

const outcomes = await pipeline(
  runnable,
  node   => runNode(node, agent),                                       // stage 1: execute (+ soft retry) — concurrent
  result => routeOutcome(result) === 'done'
              ? serializeCommit(() => commitNode(result, agent, done)).then(() => result)
              : result,                                                  // stage 2: commit-on-pass, SERIALIZED
  result => routeOutcome(result) === 'done' ? null : result             // stage 3: collect failures
)
const hardFailures = outcomes.filter(r => r && routeOutcome(r) === 'hard')
```

`pipeline` (not `parallel`) is in v1 by decision: `runNode` of siblings overlaps, but each `commitNode` chains onto the previous through `serializeCommit`, so the file-write race (C1) cannot occur. The concurrency/commit timing here is the **primary test focus** (see §7, Layer 2).

### 4.5 Main-loop exit handling (`/run` skill)

```
invoke Workflow(run-engine) → {status, ...}
├─ complete         → run learning-protocol → done ✅
└─ needs_diagnosis  → read hardFailures + diagnosis_history
                      → GLOBAL cap (fix L1): total diagnosis rounds ≥ 5 → UNRESOLVED, halt
                      → diagnosis.md: locate root-cause node (Claude, autonomous — no human stop)
                      → per-cause cap: same root cause ≥2 → UNRESOLVED, halt with best output + TODO
                      → else repair_plan:
                          1. reset_set = {root-cause node(s)} ∪ transitive downstream
                             (compute_reset_closure.py — every node reachable via hard_blocked_by; fix C2)
                          2. remove reset_set from completed (transition_log)
                          3. resume engine
```

**Two convergence caps (fix L1).** The per-root-cause cap (≥2 same cause → UNRESOLVED) does not catch *oscillating* root causes (A→B→A, each cause counted once). A **global cap** — total diagnosis rounds across the whole `/run` ≥ 5 → UNRESOLVED regardless of cause — bounds the diagnosis-resume big loop unconditionally.

**Repair must cascade (fix C2).** Resetting only the root-cause node leaves its already-`completed` descendants standing on stale upstream. The repair removes the **transitive downstream closure** (`compute_reset_closure.py`, a Python helper in the `/run` main loop — repair is Claude-driven, not engine-driven) from `completed`, so every consumer of regenerated output re-runs. This restores the reconciliation cascade the old markdown loop had ("node goal modified → clear its transition_log entry").

Resume: same-session uses `resumeFromRunId` (cached `agent()` calls return instantly); cross-session re-invokes fresh and relies on `workflow.json` idempotency.

### 4.6 G0 — Node-Granularity Audit (within `/bootstrap`, before A0)

Runs **inside `/bootstrap`**, immediately after node generation and **before A0**. Right-sizes each node to its attention budget so single-task focus is optimal.

**Premise: granularity quality is U-shaped, not monotonic.** Too coarse → attention dilution / context overflow / quality drop. Too fine → coordination cost explodes (more node-specs, more exit contracts, more handoffs → more field-drift), and cross-node coherence collapses (no agent holds the whole picture; integration/stitch bugs multiply). The target is **right-sized** (one coherent, independently-deliverable, independently-testable responsibility that fits the attention budget), **not minimal**.

**Bidirectional audit**, measured against each node's Attention Contract (Primary outcome / Context budget / Non-goals — existing node-spec fields):

- **Too coarse → split.** Signals: multiple primary outcomes, exceeds context budget, bundles independent concerns. Action: split into right-sized nodes, regenerate their specs/exit-contracts/dependencies.
- **Too fine → merge.** Signals: no standalone deliverable, exists only to feed one sibling, exit artifact is a fragment. Action: merge into the coherent parent.
- **Right-sized → pass.**

**Handling:** the audit **acts non-interactively** (splits/merges) right after node generation, reusing bootstrap's node-generation machinery; it then **batches** its non-trivial restructures into the Phase A interactive window for confirmation (so all human interaction still happens in one place, even though G0 runs earlier). Output `granularity-audit.json` = `{ split: [...], merged: [...], kept: [...] }` with rationale per change. **Convergence cap:** at most 2 restructure passes, then accept and log residual outliers (prevents split→audit→split loops).

**Staleness guard (fix R1).** A0 (next step) audits decision coverage over the G0-restructured graph, but G0's restructures are only *confirmed* later in Phase A. If a Phase A confirmation **overturns** a G0 split/merge, the node set A0 audited is now stale → **A0 must re-run** on the corrected graph before Phase A finalizes. (Cheap; bounded by the rarity of overturns.)

### 4.7 A0 — Decision-Coverage Audit (within `/bootstrap`, after G0, before Phase A)

Runs **inside `/bootstrap`**, after G0 (over the right-sized graph) and before Phase A. **Dual-angle**, union the results:

- **Agent 1 (concept completeness):** enumerate every direction/intent fork implied by the source concept artifacts (art style, monetization model, tech selection, tone, scope tradeoffs, …).
- **Agent 2 (node reverse-inference):** scan generated nodes/node-specs for implicit choices not marked `decision_mode: brainstorm`.

Output `decision-coverage.json` = `{ captured: [...], missing: [...] }` (each `missing` entry carries a rationale **and a `consumer_node` — which node will read this decision**). `missing` decisions are folded into the Phase A queue. Mirrors the existing `coverage-matrix.json` pattern.

**Wiring closure (fix C4).** Identifying a decision is not enough — it must be *wired* to a consumer. For every captured/missing decision, A0 records `consumer_node`; Phase A then sets that node's `decision_inputs` to the produced `decision-<id>.json`. A closure check (extends the §4.1 invariant) asserts **bidirectionally**: every gathered `decision-*.json` is referenced by ≥1 node's `decision_inputs`, AND every `decision_inputs` path has a producer. An orphan decision (gathered, unwired) or an unidentified need both fail the check before `/run`.

### 4.8 Phase A — brainstorming-lite (within `/bootstrap`)

Runs **inside `/bootstrap`** (the final interactive step), iterating the decision queue (generated `decision_mode: brainstorm` nodes + A0 `missing`). A lightweight protocol distilled from the `brainstorming` skill: one question at a time, surface intent, 2–3 options with tradeoffs, incremental confirmation — converging to a **decision artifact** (`.allforai/<domain>/decision-<node>.json`) consumed by the downstream generation node as a required input. **No spec doc, no reviewer loop, no writing-plans handoff** (those are the full skill's ceremony; omitted here for high-frequency in-run decisions).

### 4.8.5 Final gate — three-lens DAG validation (节点生成验证, post-design addition)

The final step of `/bootstrap` (after Phase A, before `/run` is offered) validates the **generated node graph** through the same three lenses used to harden this very design (§8.1) — turning the method into a built-in step. Purpose: **shift structural failures LEFT** — catch them at planning time instead of mid-run as a C3 `deadlock`, preserving "autonomous run, zero surprises". It also restores the graph-structure check the `validate_bootstrap` refactor (`717bc93`) removed.

| Lens | Checks | Mode | Disposition |
|------|--------|------|-------------|
| 🔗 闭环 | `decision_inputs` exist + no orphan decisions (C4) | deterministic (`check_decision_inputs.py`) | **BLOCK** |
| 🔁 大小循环 | no `hard_blocked_by` cycle; no dependency on a non-existent node | deterministic (`validate_dag_structure.py`: Kahn topo + missing-dep scan) | **BLOCK** |
| 🔄 逆向 | artifact closure, dead nodes, goal-traceback, weakest-link/SPOF — reading node-specs backwards from the goal | LLM critic → `dag-critique.json` | **WARN** |

**Why the lens split is forced by the schema.** Cycle + missing-dep are pure graph ops on `hard_blocked_by` (deterministic, unit-tested). Artifact-closure / dead-node detection need a per-node *consumes* set, which the node schema does not carry — so they fall to the LLM critic, which reads the node-specs' prose. Deterministic lenses hard-block (a cycle is unambiguously a deadlock); the LLM lens only warns (avoid false-positive gating). `/run` is offered iff the two deterministic lenses pass.

### 4.9 Phase C — Report

Surface: (a) decisions auto-assumed mid-run by Phase B (assume + declare) — read from `assumed-decisions.json` (see §5), (b) any `UNRESOLVED` nodes with TODO, (c) learning extraction into `.allforai/bootstrap/learned/`.

---

## 5. Emergent-decision policy (the one real tension)

"Decisions all up front" vs "plan grows during the run" conflict only when a mid-run expander creates a node needing a decision Phase A never covered. Two-tier policy:

1. **Pre-expand in Phase A** as much as predictable, so most emergent decisions are surfaced and decided before Phase B.
2. **Residual (truly runtime-dependent):** Phase B **assumes a sensible default + declares it** — the node subagent **returns** `{node_id, decision, default_chosen, rationale}` in its `NODE_RESULT.assumed_decisions[]` (it does NOT write the file itself — fix C1). The **engine persists it during the serialized commit** to `.allforai/bootstrap/assumed-decisions.json`, so concurrent nodes never race on that file either. Then continues. Never stops. Phase C surfaces the file. (Consistent with Codex's assume+declare philosophy.)

---

## 6. Data & file contracts

- `workflow.json` — base schema + CC-only superset fields (`decision_mode`, `decision_inputs`, `closure_verify`, `soft_retry_max`, `expanders`) per §4.1. Single durable ground truth. (`human_gate`/`approvals` no longer used at runtime — see §4.1 reconciliation.)
- `granularity-audit.json` — G0 output (`split`/`merged`/`kept`).
- `decision-coverage.json` — A0 output.
- `.allforai/<domain>/decision-<node>.json` — Phase A decision artifacts (referenced by node `decision_inputs`).
- `.allforai/bootstrap/assumed-decisions.json` — mid-run assume+declare log (§5), surfaced in Phase C.
- `transition_log[]` / `diagnosis_history[]` — engine commit + failure log.
- JSON = machine-readable (complete fields); `*-report.md` = human summary (no duplicated JSON).

---

## 7. Testing strategy

Three layers, cheap → expensive (mirrors the repo's `py_compile` + partial-source `exec()` discipline, ported to JS).

### Layer 1 — pure-logic unit tests (no agents)
Extract decision logic into `engine-core.js` pure functions; the Workflow script is a thin shell that calls them.

| Function | Asserts |
|----------|---------|
| `computeReady(nodes, done)` | hard_blocked_by gating; `alignment_refs` non-blocking; completed skipped; **no** approval/gate state consulted |
| `routeOutcome(result)` | cross_node/suspected_root_node → hard; placeholder/failed_validation (no root flag) → soft; passed → done |
| `mergeExpanded(nodes, newNodes)` | idempotent (existing id not duplicated) |
| `pickExit(remaining, hardFails)` | hardFail → needs_diagnosis; all done → complete; stuck (remaining, no hardFail) → needs_diagnosis (no `gates_pending`) |
| `convergenceCheck(history, rootCause)` | same root cause ≥2 → UNRESOLVED (per-cause cap) |
| `serializeCommit(fn)` | commit chain never overlaps (fix C1) — second commit awaits first |

(No `gateBlocked` unit — `human_gate` is removed at runtime, §4.1. The repair-cascade closure (fix C2) is **not** an engine-core function — repair runs in the `/run` main loop, so it's a Python helper `compute_reset_closure.py` (Plan 2). The "every `decision_inputs` artifact exists" + "no orphan decisions" closure check (fix C4) and the **global** diagnosis cap (fix L1) also live in the `/run`/bootstrap layer, not the engine.)

Run: `node --check run-engine.workflow.js` (syntax) + extract-and-`node --test` (function level).

### Layer 2 — fake-agent integration (the pipeline focus)
Inject a fake `agent()` returning scripted `NODE_RESULT`s, with manually-resolved promises to control completion order (no `Date`/`setTimeout` in the sandbox). Four assertions on fixture {A fast-pass, B soft-fail-then-pass, C cross_node hard-fail}:

1. **No cross-talk** — committing A while C is still running appends only A to `transition_log`; `done` gains only A.
2. **Retry isolation** — B's one retry leaves A/C untouched; A/C each `runNode` exactly once.
3. **Hard-fail bubbles** — C (cross_node) is not retried → `hardFailures` → `pickExit` = `needs_diagnosis`.
4. **Mid-batch commit doesn't corrupt the in-flight batch** — the round's `runnable` is locked at the top of the `while`; A's mid-pipeline commit updates `done` but does not change the current round's set; recompute happens next round only.
5. **Commit serialization (fix C1)** — with two passing siblings whose commit agents are gated on manually-resolved promises, assert the second `commitNode` does not start until the first resolves (writes never overlap).
6. **Stuck-graph exit (fix C3)** — a DAG whose only remaining node depends on a missing id returns `needs_diagnosis` with a non-empty `hardFailures` carrying a `deadlock` finding (never `undefined`).

### Layer 3 — real-agent end-to-end (dedicated fixture)
A purpose-built mini fixture `workflow.json` (7 nodes) exercising every path. Real agents; **token cost acceptable because it tests the engine, not a real user project** — may be run repeatedly.

```
n1 plain pass
n2,n3 siblings (alignment_refs) → verify true parallelism; n3 seeds a placeholder → verify soft self-heal
n4 has decision_inputs (former human_gate) → artifact present from Phase A → verify it runs without stopping;
   a variant with the artifact deleted → verify hard_fail (missing-decision = planning bug), not a stop
n5 seeds cross_node → n1 → verify needs_diagnosis + diagnosis resets n1 AND its downstream
   closure (compute_reset_closure n1 = n2,n3,n4,n5,n6) + rerun (fix C2 — not just n1)
n6 depends on n4 + n5 → verify dependency unlock
expander adds n7 at runtime → verify "plan auto-updates during run"; re-invoke and verify the
   expander is NOT re-applied (applied_expanders skip; fix C5)
```

Pass criteria: engine invoked ≥2× (initial → post-diagnosis resume); final `transition_log` all completed, zero placeholder residue; n7 expanded + executed exactly once; diagnosis reset cascaded to n1's descendants; kill-and-reinvoke mid-run does not re-run completed nodes (idempotency).

### Definition of Done
- L1 + L2 (incl. assertions 5–6) green; L3 fixture passes a full real run.
- Version bumped in all three places: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and **a new `version:` field added to `skills/bootstrap.md` YAML frontmatter** (decision for R3 — the frontmatter `version:` is the canonical third location; the old body header `# Bootstrap Protocol vX.Y.Z` is retired to a non-authoritative comment). All three carry the identical string.

---

## 8. Locked decisions (traceability)

1. Route: direct engine rewrite (not incremental).
2. CC-first superset schema, dual executor; never compromise CC for parity.
3. Phases: `/bootstrap` = goal + nodes + G0 granularity audit + A0 decision-coverage audit + Phase A decisions (all interaction); `/run` = Phase B autonomous → Phase C report.
4. **All human interaction consolidated into `/bootstrap`**; `/run` is fully autonomous, zero interaction (only UNRESOLVED halts).
5. Decision timing: generation-before (decisions upstream → decision artifacts).
6. brainstorming-lite (distilled protocol), not the full brainstorming skill.
7. Emergent decisions: pre-expand in Phase A, residual → assume+declare in Phase C.
8. Engine routes only; trusts subagent `blocking_findings` flag.
9. Hybrid failure recovery; convergence cap = 2 per root cause.
10. `pipeline` in v1 (run→commit, no barrier).
11. `workflow.json` idempotent skip-list; resume cache optional.
12. A0 dual-angle audit (concept-completeness ⨁ node-reverse-inference).
13. Testing: 3 layers; L3 freely re-runnable on dedicated fixture; DoD bumps 3 version locations.
14. G0 node-granularity audit: bidirectional (split-too-coarse + merge-too-fine), acts on the DAG, runs before A0; target right-sized (U-curve), not minimal; ≤2 restructure passes.
15. `human_gate` removed at runtime — re-expressed as `decision_inputs` required artifacts produced in Phase A; engine has no gate function.

### 8.1 Three-lens audit fixes (big/small-loop · closure · reverse-thinking)

| ID | Lens | Hole | Fix |
|----|------|------|-----|
| **L1** | big-loop | diagnosis-resume loop has only a per-root-cause cap → oscillating causes never converge | **global** cap: total diagnosis rounds ≥ 5 → UNRESOLVED (§4.5) |
| **L2** | small-loop | brainstorming-lite "ask again on new fork" unbounded | cap forks per decision (§4.8 / brainstorming-lite.md) |
| **C1** | closure | parallel commit agents + node subagents race-write `workflow.json` / `assumed-decisions.json` | `serializeCommit` queue; assumed decisions returned in `NODE_RESULT`, engine persists during serialized commit (§4.2.6, §4.4, §5) |
| **C2** | closure | repair resets only root node, leaving stale completed descendants | reset the **transitive downstream closure** (`compute_reset_closure.py`, /run layer) (§4.5) |
| **C3** | closure | stuck-graph exit returns `needs_diagnosis` with no `hardFailures` → handler breaks | synthesize a `deadlock` hard failure (§4.2.7) |
| **C4** | closure | a gathered decision may be unwired to any consumer node | A0 records `consumer_node`; Phase A sets `decision_inputs`; bidirectional orphan check (§4.7) |
| **C5** | closure | cross-session reload re-runs file-mutating expander → double-expansion | `applied_expanders` skip + require file-idempotent expanders (§4.1, §4.2.2) |
| **R1** | reverse | Phase A overturning a G0 restructure leaves A0 coverage stale | re-run A0 after any overturn (§4.6) |
| **R2** | reverse | L3 fixture path ≠ engine's canonical `workflow.json` path | L3 stages the fixture at `.allforai/bootstrap/workflow.json` (Plan 1 runbook) |
| **R3** | reverse | bootstrap version location undecided (drifted) | add canonical `version:` to bootstrap.md frontmatter (§7 DoD) |

---

## 9. Open items for the implementation plan

- Exact file naming under `claude/meta-skill/knowledge/run-engine/` (avoid the existing `knowledge/engines/` game-engine dir) and how the `/run` skill instructs the Workflow call.
- Migration: keep the old markdown loop available as fallback during rollout, or hard cut-over on CC.
- Bootstrap node generation must learn to emit the new superset fields: `decision_mode`, `decision_inputs`, `closure_verify`, `soft_retry_max`, and the `expanders` list (promoting today's hardcoded `expand_*.py` invocations to a declared list).
- How `closure_verify` enum values (`audio`/`save-load`/`2d-placeholder`) map to the existing closure-gate capability nodes (`bootstrap.md` audio/2D production closure QA) vs. become inline subagent instructions.
- G0 granularity audit: concrete split/merge thresholds and how it reuses bootstrap's node-generation machinery to regenerate specs after a restructure.
- Bootstrap-time invariant check: every node's `decision_inputs` artifacts exist before `/run` is allowed to start.
- Codex/OpenCode: confirm they gracefully ignore the new superset fields (no parsing errors).
```
