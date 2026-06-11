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
   table + dependency graph). **If the goal is too big for one run, cut it here:** milestone-1
   scope = this megastorm run; everything deferred goes into a `## Roadmap` section of the
   overview (future runs). A module that already smells like 20+ tasks should be split or
   deferred NOW — it is far cheaper than the Phase 1 loop-back.
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
5. **Resolve the three model tiers** (rules in "Model tiers" under Phase 1): take each tier's
   preferred model from the Workflow tool's current `model` enum; AskUserQuestion only if a
   preferred name is missing, or to record an explicitly requested thrifty run. Freeze the three
   literals into the registry's `models` field.
6. **New-human-decision rule (boundary for Phase 1):** anything changing module boundaries,
   public/cross-module interfaces, or user-visible scope = escalate. Internal-only choices =
   the autonomous agents decide and log. This is what makes Phase 1 safe to run unattended.

After Phase 0, do not stop for the human until an escalation surfaces.

## Phase 1 — Autonomous pipeline (call Workflow once per stage; read result; decide next)
For every stage, read the Workflow return. If ANY agent returned `status:"escalate"`, HALT,
render `reason`+`evidence` to the user, get the decision, then re-run that stage. Otherwise continue.

**Module-too-large loop-back — the ONE sanctioned return to Phase 0.** Trigger: a design or
plan agent escalates with `reason:"module-too-large"`, or §1.3's deterministic check trips
(one module's validated plan > 20 tasks). Handling — do NOT just re-run the stage:
1. HALT. Re-run `Skill: superpowers:brainstorming` for THAT module only, with the human:
   split it into sub-modules, or defer scope to the overview's `## Roadmap` section.
2. Human approves the new breakdown. Update the module specs; re-mint ONLY the affected
   registry entries (new `R-<submodule>-NN` IDs and interfaces for the split parts; every
   other entry stays verbatim — do not reopen settled vocabulary).
3. Re-run §1.1→§1.3 for the new/changed modules only; untouched modules' designs and plans
   remain valid. Then continue forward.
Budget: at most ONE loop-back per original module. If a split product is still too large,
that is a scoping problem — stop and re-plan the roadmap with the human instead of looping.
Record every loop-back in the Phase 2 report.

Model tiers — three roles, never hardcoded to a model generation. Each tier has a preferred
model plus fallback candidates; the ladder is a RECOMMENDATION ORDER to present to the human,
never an auto-fall mechanism. Resolve in Phase 0, while the human is present: read the `model`
enum your Workflow tool currently advertises. For each tier, if the preferred name is in the
enum, use it. If it is NOT, do not silently fall down the ladder — AskUserQuestion with the
remaining candidates (plus "inherit session default") and record the choice. Freeze all three
resolved literals into the overview's registry block; every Phase 1 `agent()` call substitutes
its tier's frozen literal.
- **THINK（规划）** = prefer `fable`; candidates `opus → sonnet`. Used by design /
  closure-critic / plan / reverse-critic — thinking errors are the most expensive.
- **VERIFY（验收）** = prefer `opus`; candidates `fable → sonnet`. Used by supervisor —
  verification rigor is the trust root; must never resolve weaker than BULK.
- **BULK（执行）** = prefer `sonnet`; candidate `haiku`. Used by executor — token thrift on
  bulk mechanical coding only.

Downgrade rules — NO automatic downgrade; manual downgrade only:
- The orchestrator NEVER lowers a tier on its own — not for availability, not for cost, not
  mid-run. Every downgrade is a human decision.
- **Manual downgrade (allowed):** the human may pick a lower model for any tier — at Phase 0
  (e.g. an explicitly declared thrifty run) or at any escalation halt. Record it in the overview;
  list every below-preference tier in the Phase 2 report ("THINK ran on opus — human-approved").
- **Mid-run model failure (any tier, including BULK):** retry; if it keeps failing, HALT and
  escalate — the human decides whether to downgrade or stop. A silently weaker verifier (or
  planner) is worse than a stopped pipeline.

### 1.1 Design — Workflow
Author a Workflow that `pipeline`s/`parallel`s over the M module specs; each `agent` uses
`$ROOT/knowledge/prompts/design-agent.md` and the design-manifest schema, with `{model: THINK}`. **Pass every design
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
- Then run a Workflow `agent` with `$ROOT/knowledge/prompts/closure-critic.md` and `{model: THINK}` for the prose-level judgment (≤3 rounds).
- Unresolved after rounds, or any escalate → HALT to user.

### 1.3 Plan — Workflow
`pipeline` over designs; each `agent` uses `$ROOT/knowledge/prompts/plan-agent.md` with `{model: THINK}` and emits the plan-task array.
For each plan, run `python3 $ROOT/scripts/validate_plan_tasks.py <tasks.json>`; if BLOCKED,
bounce back to the plan agent until every task has `touched_paths` + `acceptance_cmd`.
Deterministic size check: a validated plan with > 20 tasks for one module = module-too-large →
take the loop-back above; do NOT bounce it to the plan agent (it cannot fix scoping).

### 1.4 Reverse review — Workflow
A Workflow `agent` with `$ROOT/knowledge/prompts/reverse-critic.md` and `{model: THINK}` over all spec/design/plan docs
(≤3 rounds, self-fix or escalate).

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
- executeStage: `agent($ROOT/knowledge/prompts/executor.md prompt, {model: BULK})` (+ `{isolation:'worktree'}` for group members).
- verifyStage: `agent($ROOT/knowledge/prompts/supervisor.md prompt, {schema: verdict, model: VERIFY})` — fresh context,
  reruns `acceptance_cmd`. On `done:false`: read the task's `retries` from the ledger;
  **if `retries < 2` → increment and bounce to executor; if `retries == 2` → escalate.** This is
  spec §4.6's "soft-retry ≤2" = the initial attempt plus at most 2 retries (3 dispatches total).
- **Vacuous auto-recovery:** if the verdict has `vacuous:true` (acceptance passed only because
  0 tests ran), the bounce to the executor MUST append the anti-vacuous instruction — *"the
  acceptance selects tests by name and matched 0; create the named test with ≥1 real assertion
  and confirm a non-zero executed-test count."* Do not escalate a `vacuous` failure to the human
  until the soft-retry budget is genuinely exhausted — it is almost always self-fixable, and the
  deterministic `validate_plan_tasks.py` gate should have caught it at §1.3 anyway.

## Phase 2 — Report
Update the overview and write a final report: assumptions the autonomous agents made, all
escalation points + resolutions, the independently-verified completion list (distinguish
"executor-claimed" from "supervisor-confirmed"), DAG warnings, and learnings.

**Mandatory "Reality gate" section.** Every report MUST split completion into two explicit lists:
(a) **autonomously verified** — the supervisor reran the real `acceptance_cmd` and it genuinely
passed; and (b) **requires human / hardware / external verification** — anything whose real-world
success cannot be proven in CI/simulator (live media, real devices, third-party prod systems,
physical I/O). For every item in (b), emit a concrete runbook (exact steps, what to observe, pass
criteria). **"All tasks green" must NEVER be presented as "the feature works" when (b) is
non-empty.** Mechanical task-completion ≠ verified capability; conflating them is the precise
honesty failure megastorm exists to prevent.

## Artifacts (superpowers-native)
One overview + standard superpowers docs:
`docs/superpowers/specs/<date>-<goal>-overview.md`, `...-<module>-design.md`,
`docs/superpowers/plans/<date>-<module>-plan.md`, plus machine `orchestration.json`.
