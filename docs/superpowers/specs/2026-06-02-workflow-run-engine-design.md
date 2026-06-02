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
- Add a **planning-time decision-coverage audit** so decisions are caught before the run, not during it.
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

**Command boundary:** **All human interaction is consolidated into `/bootstrap`** — goal confirmation (existing Step 1.5), the A0 audit, and Phase A decision-gathering. `/bootstrap` exits only when every decision artifact is on disk. `/run` is then **fully autonomous from start to finish** — no questions, no stops (except catastrophic `UNRESOLVED`). It can be backgrounded and left unattended. User-facing flow is unchanged: still `/bootstrap` then `/run`; the shift is that `/bootstrap` absorbs all decisions and `/run` becomes a pure long-running autonomous task.

Trade-off: `/bootstrap` grows from "quick analysis" into "analysis + gather all decisions"; in return `/run` needs zero human attention.

### 3.2 Layer responsibilities

| Layer | Responsibility | Implementation |
|-------|----------------|----------------|
| `/bootstrap` skill (main-loop Claude) | Confirm goal; generate nodes; run A0 audit; run Phase A brainstorming-lite → write all decision artifacts | markdown skill |
| `/run` skill (main-loop Claude) | Drive Phase B → C autonomously; on `needs_diagnosis` run `diagnosis.md`; resume the engine between segments — no human interaction | markdown skill |
| Workflow engine (`run-engine.workflow.js`) | Read DAG → topo-schedule → run ready nodes in parallel → validate → self-heal soft failures → commit → return on completion/hard-failure | one **generic** JS interpreter in plugin `knowledge/engine/` |
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
  required: ['nodes', 'completed', 'approvals'],
  properties: {
    nodes: { type: 'array', items: { type: 'object',
      required: ['node_id','capability','hard_blocked_by','exit_artifacts'],
      properties: {
        node_id:         { type: 'string' },
        capability:      { type: 'string' },
        hard_blocked_by: { type: 'array', items: { type: 'string' } },
        alignment_refs:  { type: 'array', items: { type: 'string' } },
        exit_artifacts:  { type: 'array', items: { type: 'object' } }, // {path, validation_commands}
        human_gate:      { type: 'boolean' },
        node_spec_path:  { type: 'string' },
        // —— CC-first superset (other platforms ignore) ——
        decision_mode:   { type: 'string', enum: ['brainstorm','none'] },
        closure_verify:  { type: 'array', items: { type: 'string' } }, // ['audio','save-load','2d-placeholder']
        soft_retry_max:  { type: 'integer' }                           // default 2
      } } },
    completed: { type: 'array', items: { type: 'string' } },  // idempotent skip-list
    approvals: { type: 'object' },                            // {node_id: 'approved'|'pending'|...}
    expanders: { type: 'array', items: { type: 'string' } }
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
    summary:           { type: 'string' }
  }
}
```

`outcome` is decided by the node subagent (only it can read files / run `validation_commands` — engine scripts cannot touch the filesystem). The engine reads `outcome` + `blocking_findings` for routing only.

### 4.2 Engine seven parts (`run-engine.workflow.js`, Phase B)

1. **load-DAG** — one agent reads `workflow.json` + `bootstrap-profile.json` → `DAG_SCHEMA`. Build `done = new Set(dag.completed)`.
2. **expand** — for each `dag.expanders`, an agent runs the expander and returns new nodes; merge idempotently (`mergeExpanded` skips existing `node_id`). This is the "plan auto-updates during the run" capability.
3. **computeReady** — `nodes.filter(n => !done.has(n.node_id) && n.hard_blocked_by.every(d => done.has(d)))`. **`alignment_refs` do NOT block** — present them as read-if-available; this is the source of free parallelism.
4. **pipeline batch** — the ready batch flows through a `pipeline()` (run → commit), no barrier: a node that passes commits while siblings are still running.
5. **runNode** — dispatch the node-spec as a subagent with `NODE_RESULT_SCHEMA`; internal soft-retry loop (≤ `soft_retry_max`, default 2) with progressively stricter prompts; includes `closure_verify` instructions when present.
6. **commit** — on pass, an agent appends to `transition_log` immediately and `done.add(node_id)` (per-node, not batched — crash/re-entry loses zero progress).
7. **exits** — Phase B has **two** exits: `complete` (all done) and `needs_diagnosis` (hard failures collected). `gates_pending` is removed (decisions are front-loaded; an unsatisfied gate mid-run is a planning bug → treated as hard failure).

### 4.3 Soft/hard routing (`routeOutcome`, the hybrid heart)

Two rules, applied to a failed node's `blocking_findings`:

1. Any finding with `type:'cross_node'` or a `suspected_root_node` → **hard fail immediately** (do not retry; the root cause is elsewhere).
2. Otherwise (placeholder / missing field / failed validation) → **soft fail**; retry the same node ≤ `soft_retry_max` with a stricter prompt; on exhaustion → hard fail.

The engine **trusts the subagent's self-reported flag**. Mislabel risk is bounded: a mislabeled `cross_node`-as-soft wastes at most `soft_retry_max` retries, then converts to hard and surfaces to Claude anyway — it never deadlocks.

### 4.4 pipeline shape (v1)

```js
const outcomes = await pipeline(
  runnable,
  node   => runNode(node, done, dag),                                   // stage 1: execute (+ soft retry)
  result => result.outcome === 'passed'
              ? commitNode(result).then(() => result) : result,         // stage 2: commit-on-pass, no barrier
  result => result.outcome !== 'passed' ? result : null                 // stage 3: collect failures
)
const hardFailures = outcomes.filter(r => r && r.outcome === 'hard_fail')
```

`pipeline` (not `parallel`) is in v1 by decision. The concurrency/commit timing here is the **primary test focus** (see §7, Layer 2).

### 4.5 Main-loop exit handling (`/run` skill)

```
invoke Workflow(run-engine) → {status, ...}
├─ complete         → run learning-protocol → done ✅
└─ needs_diagnosis  → read hardFailures + diagnosis_history
                      → diagnosis.md: locate root-cause node (Claude, autonomous — no human stop)
                      → convergence cap: same root cause ≥2 → UNRESOLVED, halt with best output + TODO
                      → else repair_plan: remove root-cause node(s) from completed → resume engine
```

Resume: same-session uses `resumeFromRunId` (cached `agent()` calls return instantly); cross-session re-invokes fresh and relies on `workflow.json` idempotency.

### 4.6 A0 — Decision-Coverage Audit (within `/bootstrap`, before Phase A)

Runs **inside `/bootstrap`**, after node generation and before Phase A. **Dual-angle**, union the results:

- **Agent 1 (concept completeness):** enumerate every direction/intent fork implied by the source concept artifacts (art style, monetization model, tech selection, tone, scope tradeoffs, …).
- **Agent 2 (node reverse-inference):** scan generated nodes/node-specs for implicit choices not marked `decision_mode: brainstorm`.

Output `decision-coverage.json` = `{ captured: [...], missing: [...] }` (each `missing` entry carries a rationale). `missing` decisions are folded into the Phase A queue. Mirrors the existing `coverage-matrix.json` pattern.

### 4.7 Phase A — brainstorming-lite (within `/bootstrap`)

Runs **inside `/bootstrap`** (the final interactive step), iterating the decision queue (generated `decision_mode: brainstorm` nodes + A0 `missing`). A lightweight protocol distilled from the `brainstorming` skill: one question at a time, surface intent, 2–3 options with tradeoffs, incremental confirmation — converging to a **decision artifact** (`.allforai/<domain>/decision-<node>.json`) consumed by the downstream generation node as a required input. **No spec doc, no reviewer loop, no writing-plans handoff** (those are the full skill's ceremony; omitted here for high-frequency in-run decisions).

### 4.8 Phase C — Report

Surface: (a) decisions auto-assumed mid-run by Phase B (assume + declare), (b) any `UNRESOLVED` nodes with TODO, (c) learning extraction into `.allforai/bootstrap/learned/`.

---

## 5. Emergent-decision policy (the one real tension)

"Decisions all up front" vs "plan grows during the run" conflict only when a mid-run expander creates a node needing a decision Phase A never covered. Two-tier policy:

1. **Pre-expand in Phase A** as much as predictable, so most emergent decisions are surfaced and decided before Phase B.
2. **Residual (truly runtime-dependent):** Phase B **assumes a sensible default + declares it**, logs it, surfaces it in Phase C. Never stops. (Consistent with Codex's assume+declare philosophy.)

---

## 6. Data & file contracts

- `workflow.json` — unchanged base schema + CC-only superset fields (§4.1). Single durable ground truth.
- `decision-coverage.json` — A0 output.
- `.allforai/<domain>/decision-<node>.json` — Phase A decision artifacts.
- `transition_log[]` / `diagnosis_history[]` — engine commit + failure log.
- JSON = machine-readable (complete fields); `*-report.md` = human summary (no duplicated JSON).

---

## 7. Testing strategy

Three layers, cheap → expensive (mirrors the repo's `py_compile` + partial-source `exec()` discipline, ported to JS).

### Layer 1 — pure-logic unit tests (no agents)
Extract decision logic into `engine-core.js` pure functions; the Workflow script is a thin shell that calls them.

| Function | Asserts |
|----------|---------|
| `computeReady(nodes, done)` | hard_blocked_by gating; `alignment_refs` non-blocking; completed skipped |
| `gateBlocked(node, approvals)` | human_gate unapproved → true |
| `routeOutcome(result)` | cross_node/suspected_root_node → hard; placeholder → soft; passed → done |
| `mergeExpanded(nodes, newNodes)` | idempotent (existing id not duplicated) |
| `pickExit(ready, hardFails)` | hardFail → needs_diagnosis; all done → complete |
| `convergenceCheck(history, rootCause)` | same root cause ≥2 → UNRESOLVED |

Run: `node --check run-engine.workflow.js` (syntax) + extract-and-`node --test` (function level).

### Layer 2 — fake-agent integration (the pipeline focus)
Inject a fake `agent()` returning scripted `NODE_RESULT`s, with manually-resolved promises to control completion order (no `Date`/`setTimeout` in the sandbox). Four assertions on fixture {A fast-pass, B soft-fail-then-pass, C cross_node hard-fail}:

1. **No cross-talk** — committing A while C is still running appends only A to `transition_log`; `done` gains only A.
2. **Retry isolation** — B's one retry leaves A/C untouched; A/C each `runNode` exactly once.
3. **Hard-fail bubbles** — C (cross_node) is not retried → `hardFailures` → `pickExit` = `needs_diagnosis`.
4. **Mid-batch commit doesn't corrupt the in-flight batch** — the round's `runnable` is locked at the top of the `while`; A's mid-pipeline commit updates `done` but does not change the current round's set; recompute happens next round only.

### Layer 3 — real-agent end-to-end (dedicated fixture)
A purpose-built mini fixture `workflow.json` (7 nodes) exercising every path. Real agents; **token cost acceptable because it tests the engine, not a real user project** — may be run repeatedly.

```
n1 plain pass
n2,n3 siblings (alignment_refs) → verify true parallelism; n3 seeds a placeholder → verify soft self-heal
n4 human_gate → pre-satisfied by Phase A → verify no mid-run stop
n5 seeds cross_node → n1 → verify needs_diagnosis + diagnosis removes n1's completed + rerun
n6 depends on n4 + n5 → verify dependency unlock
expander adds n7 at runtime → verify "plan auto-updates during run"
```

Pass criteria: engine invoked ≥2× (initial → post-diagnosis resume); final `transition_log` all completed, zero placeholder residue; n7 expanded + executed; kill-and-reinvoke mid-run does not re-run completed nodes (idempotency).

### Definition of Done
- L1 + L2 green; L3 fixture passes a full real run.
- Version bumped in all three places (`plugin.json`, `marketplace.json`, `SKILL.md` frontmatter).

---

## 8. Locked decisions (traceability)

1. Route: direct engine rewrite (not incremental).
2. CC-first superset schema, dual executor; never compromise CC for parity.
3. Phases: `/bootstrap` = goal + nodes + A0 audit + Phase A decisions (all interaction); `/run` = Phase B autonomous → Phase C report.
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

---

## 9. Open items for the implementation plan

- Exact location/naming under `claude/meta-skill/knowledge/engine/` and how `/run` skill instructs the Workflow call.
- Migration: keep the old markdown loop available as fallback during rollout, or hard cut-over on CC.
- `decision_mode`/`closure_verify`/`soft_retry_max` field injection point in `bootstrap.md` node generation.
- Codex/OpenCode: confirm they gracefully ignore the new superset fields (no parsing errors).
```
