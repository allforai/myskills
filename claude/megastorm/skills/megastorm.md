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
   table + dependency graph).
3. For EACH module, run `Skill: superpowers:brainstorming` to produce a standard module
   spec/design; the user approves each. Done when all M specs exist and are approved.
4. **Mint the frozen registry (YOU, the main session, are the single owner — not the
   brainstorming skill, not the design agents).** After all specs are approved, read them and
   write the registry into the overview wrapped in `<!-- megastorm-registry:start -->` /
   `<!-- megastorm-registry:end -->` markers (a plain ```json object between them), per
   `$ROOT/knowledge/schemas.md`. Contents: `requirements` = an `R-<module>-NN` ID for every
   requirement across the specs; `interfaces` = the closed vocabulary of cross-module interface
   names using the grammar `<kind>:<name>` (kind ∈ api/event/data/ui, lowerCamelCase).
   This registry is FROZEN before Phase 1 — the design fan-out reads it, never extends it.
   **Err toward a generous interface vocabulary:** a too-thin registry makes the parallel design
   fan-out throw escalations (each missing interface is a new-human-decision), bouncing control
   back to you repeatedly and partly defeating "decisions front-loaded." Enumerate every plausible
   cross-module interface now. (Without this single owner, every design `covers_req_ids` becomes
   an orphan and the §4.2 closure gate fails closed on every run — the reverse-review's top finding.)
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
`$ROOT/knowledge/prompts/design-agent.md` and the design-manifest schema. **Pass every design
agent the frozen `megastorm-registry` block** (requirements + interfaces) so `covers_req_ids`
and exposes/consumes are drawn from the closed vocabulary, not invented. Collect the manifests.

### 1.2 Closure check — deterministic then LLM
- Extract the registry deterministically: locate the text between
  `<!-- megastorm-registry:start -->` and `<!-- megastorm-registry:end -->` in the overview,
  strip the ```json fence lines, `json.loads` it, then write its `requirements` array to
  `requirements.json` and its `interfaces` array to `registry.json`. Write the collected design
  manifests to `manifests.json`.
- Run `python3 $ROOT/scripts/check_closure.py requirements.json manifests.json registry.json`.
  If it BLOCKs (uncovered req / orphan / dangling or off-registry interface), feed errors to a
  fix `agent` (design-agent prompt) and re-run, ≤3 rounds.
- Then run a Workflow `agent` with `$ROOT/knowledge/prompts/closure-critic.md` for the prose-level judgment (≤3 rounds).
- Unresolved after rounds, or any escalate → HALT to user.

### 1.3 Plan — Workflow
`pipeline` over designs; each `agent` uses `$ROOT/knowledge/prompts/plan-agent.md` and emits the plan-task array.
For each plan, run `python3 $ROOT/scripts/validate_plan_tasks.py <tasks.json>`; if BLOCKED,
bounce back to the plan agent until every task has `touched_paths` + `acceptance_cmd`.

### 1.4 Reverse review — Workflow
A Workflow `agent` with `$ROOT/knowledge/prompts/reverse-critic.md` over all spec/design/plan docs (≤3 rounds, self-fix
or escalate).

### 1.5 Orchestrate — deterministic
Concatenate all plan tasks into one array, run
`python3 $ROOT/scripts/build_task_dag.py <all-tasks.json>`. BLOCK (cycle/missing dep) → fix via
plan agent. Keep `layers` (execution order) and `isolate` (same-layer file-colliding pairs).
Persist to `orchestration.json`. Surface any `warnings` in the final report.

### 1.6 Concurrent execute + supervise — Workflow
Maintain a scratch `retry-ledger.json` (`{task_id: retries}`) — the soft-retry budget is
unenforceable without it (a stateless prose loop drifts). Process layers in DAG order. **Within
a layer, use `build_task_dag`'s output fields directly:**
- **Non-colliding tasks** (id in NO `isolate_groups` entry): run them together via
  `pipeline(tasks, executeStage, verifyStage)` — no shared files, safe with no barrier.
- **Each `isolate_groups` entry** (a connected component of file-colliding tasks): run that
  group's tasks **sequentially in the given (declaration) order**, each in its own
  `agent(..., {isolation:'worktree'})`; after the supervisor confirms `done:true`, **merge that
  worktree back to the main tree before starting the next task in the group.** Do NOT use the
  barrier-less `pipeline` to merge colliding worktrees — it has no serialization point.

Stages:
- executeStage: `agent($ROOT/knowledge/prompts/executor.md prompt, {model:'sonnet'})` (+ `{isolation:'worktree'}` for group members).
- verifyStage: `agent($ROOT/knowledge/prompts/supervisor.md prompt, {schema: verdict})` — default model, fresh context,
  reruns `acceptance_cmd`. On `done:false`: read the task's `retries` from the ledger;
  **if `retries < 2` → increment and bounce to executor; if `retries == 2` → escalate.** This is
  spec §4.6's "soft-retry ≤2" = the initial attempt plus at most 2 retries (3 dispatches total).

## Phase 2 — Report
Update the overview and write a final report: assumptions the autonomous agents made, all
escalation points + resolutions, the independently-verified completion list (distinguish
"executor-claimed" from "supervisor-confirmed"), DAG warnings, and learnings.

## Artifacts (superpowers-native)
One overview + standard superpowers docs:
`docs/superpowers/specs/<date>-<goal>-overview.md`, `...-<module>-design.md`,
`docs/superpowers/plans/<date>-<module>-plan.md`, plus machine `orchestration.json`.
