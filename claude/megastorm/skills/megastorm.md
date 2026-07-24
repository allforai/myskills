---
name: megastorm
description: Drive a large goal end-to-end — decompose into modules, front-load all decisions via brainstorming, then autonomously design, validate, plan, reverse-review, orchestrate, concurrently execute, and independently verify. Explicitly invoked via /megastorm; heavy and token-intensive.
---

# Megastorm

Large-goal autonomous pipeline:

`decide → specify → close → plan → reverse-review → DAG → execute → verify → report`

**Invariant:** decisions are front-loaded, execution is autonomous, failures self-correct or
are explicitly deferred, and every autonomous choice is disclosed at close. Phase 0 is the
only ordinary human-interaction phase. Phase 1 never pauses for a new decision or approval.

`$ROOT` = `${CLAUDE_PLUGIN_ROOT}`.

## Load Policy

This file is the router and contract. For every full Megastorm run, read
`$ROOT/knowledge/execution-playbook.md` before Phase -1 and follow it exactly. Load these only
when their stage needs them:

- `$ROOT/knowledge/schemas.md` for registries, manifests, tasks, verdicts, and ledgers.
- `$ROOT/knowledge/prompts/*.md` immediately before authoring the matching Workflow stage.
- `$ROOT/scripts/` when running the deterministic gates named by the playbook.

Do not preload every prompt or repeat their contents in generated orchestration scripts beyond
what that stage requires.

## Entry State

- **New goal:** run Phases -1, 0, 1, and 2.
- **Already approved specs and frozen registry:** validate the artifacts and authority envelope,
  then resume at the first incomplete Phase 1 gate.
- **Existing `orchestration.json` and ledgers:** reconcile registry, DAG, task IDs, Git evidence,
  and recorded statuses, then resume the dependency-ready loop. Never replay confirmed work merely
  to reconstruct context.

## Phase Gates

### Phase -1: Preflight

Verify the required namespaced superpowers skills and probe the environment's real acceptance
capabilities. Record available, flaky, and absent capabilities in the overview. Missing required
skills is a hard stop; absent runtime capabilities become explicit reality gates, never fabricated
proof.

### Phase 0: Decide and Freeze

Interactively:

1. Inspect the repository, history, and existing docs.
2. Brainstorm and approve module boundaries, dependencies, milestone scope, and granularity.
3. Brainstorm and approve one standard design spec per module.
4. Reconcile all specs and mint the single frozen requirements/interface registry.
5. Resolve and freeze explicit THINK, VERIFY, and BULK model literals.
6. Persist the decision envelope and initialize the decision ledger.
7. For eliminate-a-class goals, create an exhaustive census before deriving tasks.

**Exit:** every in-scope requirement has an ID; every plausible cross-module interface is in the
closed vocabulary; specs and boundaries are approved; models and authority are frozen; no known
ordinary decision is left for Phase 1.

### Phase 1: Build Autonomously

Run the playbook stages in order:

1. Parallel module design.
2. Deterministic closure check, then independent closure critique.
3. Per-module implementation planning and task validation.
4. Whole-plan reverse review.
5. Deterministic DAG construction.
6. Dependency-ready concurrent execution with fresh-context supervision.

Every stage must satisfy its deterministic and independent-review exit gates before the next
stage. Persist self-contained stage scripts and machine-readable state so a run can resume without
conversation memory.

### Phase 2: Close Honestly

Update the overview and emit the final report with:

- supervisor-confirmed completion, separately from executor claims;
- autonomous decisions and outcomes, each exactly once;
- escalations, deferred branches, and complete skipped-dependent chains;
- reality-gated items with concrete human/hardware/external runbooks;
- DAG warnings, assumptions, and completeness confidence;
- for class-elimination goals, the rerun census result.

End the run after the report. `/cross-exam` remains an explicit, separate command.

## Hard Rules

- Never silently substitute or inherit a model. Use the Phase 0 frozen literal in every `agent()`.
- Never send large stage payloads through Workflow args. Persist a self-contained script and use
  `scriptPath`.
- Never ask the user during Phase 1. Choose the best authorized recommendation, record it, and
  continue; if authority is insufficient, defer only that branch and its dependents.
- Never edit `decision-ledger.json` directly. Use `decision_ledger.py record/finalize`; if neither
  its normal ledger nor emergency journal is writable, stop new mutations and close with a
  degraded report.
- Never treat infrastructure failure as business failure or spend business retry budget on it.
- Never treat environmental proof failure as a code defect. Record a reality gate and keep
  independent/downstream work running when committed interfaces exist.
- Never claim completion from executor prose, a vacuous test, task counts, or missing evidence.
  Supervisors rerun real acceptance commands; runtime-facing functionality must actually run.
- Never hide skipped, deferred, unverified, or census-unknown work inside a green percentage.
- Never invent fallback output, success states, evidence, or compatibility behavior. Errors remain
  errors and are surfaced at the boundary where they occur.
- Worktree isolation is valid only when the target repository is the session cwd. Otherwise use
  serialized main-tree writes for collision groups.

## Artifacts

Use superpowers-native docs plus machine state:

- `docs/superpowers/specs/<date>-<goal>-overview.md`
- `docs/superpowers/specs/<date>-<module>-design.md`
- `docs/superpowers/plans/<date>-<module>-plan.md`
- run-local registry, decision, escalation, reality-gate, retry, and task-state ledgers
- `orchestration.json`
