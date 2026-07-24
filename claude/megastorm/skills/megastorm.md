---
name: megastorm
description: Drive a large goal end-to-end — decompose into modules, front-load all decisions via brainstorming, then autonomously produce designs, validate (closed-loop), plan, reverse-review, orchestrate, and concurrently execute with anti-fake-completion supervision. Explicitly invoked via /megastorm; heavy and token-intensive.
---

# megastorm — large-goal autonomous pipeline

**Invariant:** decisions front-loaded → autonomous → self-fix loop → disclose at close.
All human interaction is in Phase 0. Phase 1 never stops for a new decision or approval.
Spec: `docs/superpowers/specs/2026-06-09-megastorm-pipeline-design.md`.

`$ROOT` = `${CLAUDE_PLUGIN_ROOT}`. Schemas: `$ROOT/knowledge/schemas.md`. Prompts: `$ROOT/knowledge/prompts/`.
Scripts: `$ROOT/scripts/`.

## Phase -1 — Preflight (main session)
Verify the Skill registry exposes `superpowers:brainstorming`, `superpowers:writing-plans`,
`superpowers:executing-plans` (namespaced — do NOT check `~/.claude/skills/<name>/` paths;
they live under the superpowers plugin cache and the version drifts). If any is missing, STOP
and tell the user to install the superpowers marketplace via `/plugin`. Do not proceed.

**Environment-capability probe (decides what can be autonomously proven).** Before the run,
probe which acceptance capabilities THIS environment can actually exercise, and record the
result into the overview (a `## Environment capabilities` section). This is what lets the §1.3
plan agent tag `reality_gate` accurately — **so it never plans a proof this environment cannot
run.** Probe, generically (do not assume any specific stack):
- **Display/UI:** is there a real display or stable headless display server for UI/E2E, or is
  the environment headless with no GUI surface?
- **Device/simulator:** is a device simulator/emulator installed AND launchable to a steady
  state here, or unavailable / flaky to boot?
- **Real hardware / physical I/O:** any real peripheral, sensor, or physical-I/O path
  reachable, or none?
- **Shared/external systems:** are the shared test stacks, external live services, or their
  credentials reachable from here, or absent?
Summarize each as available / flaky / absent. Any acceptance that would depend on an
absent-or-flaky capability is a `reality_gate` candidate the plan agent should mark in §1.3.

## Phase 0 — Decisions front-loaded (main session, INTERACTIVE)
1. Analyze current state: repo structure, recent commits, `docs/`. Summarize.
2. Decompose the goal into M modules + boundaries + inter-module deps by running
   `Skill: superpowers:brainstorming`. Get the user to approve the module breakdown.
   Write the draft overview to `docs/superpowers/specs/<date>-<goal>-overview.md` (module
   table + dependency graph). **If the goal is too big for one run, cut it here:** milestone-1
   scope = this megastorm run; everything deferred goes into a `## Roadmap` section of the
   overview (future runs).
3. **Granularity review (dedicated step — do not skip):** before brainstorming individual
   modules, audit the approved breakdown itself, module by module:
   - **Size:** estimate each module's plan size; anything that smells like > 20 tasks gets
     split or deferred to `## Roadmap` NOW — §1.3 has a hard size check, and an oversized
     module discovered there is a guaranteed halt with no automatic recovery.
   - **Cohesion:** one module = one cohesive subsystem with a single concern; a module whose
     one-line description needs "and" twice is two modules.
   - **Balance (don't over-split either):** every new boundary becomes registry interfaces
     and cross-module decisions; if two candidate modules would share most of their
     interfaces, merge them.
   Present the audit as a table (module → est. size → verdict → action) and get the human to
   approve the adjusted breakdown before proceeding.
4. For EACH module, run `Skill: superpowers:brainstorming` to produce a standard module
   spec/design; the user approves each. Done when all M specs exist and are approved.
5. **Mint the frozen registry (YOU, the main session, are the single owner — not the
   brainstorming skill, not the design agents).** After all specs are approved, read them and
   write the registry into the overview wrapped in `<!-- megastorm-registry:start -->` /
   `<!-- megastorm-registry:end -->` markers (a plain ```json object between them), per
   `$ROOT/knowledge/schemas.md`. Contents: `requirements` = an `R-<module>-NN` ID for every
   requirement across the specs; `interfaces` = the closed vocabulary of cross-module interface
   names using the grammar `<kind>:<name>` (kind ∈ api/event/data/ui, lowerCamelCase).
   This registry is FROZEN to workers before Phase 1 — design agents never extend it.
   During Phase 1 only the main orchestrator may revise an exact evidence-backed contract,
   and only after persisting an in-envelope autonomous decision record; otherwise defer the branch.
   **Err toward a generous interface vocabulary:** a too-thin registry makes the parallel design
   fan-out throw escalations (each missing interface is a new-human-decision), bouncing control
   back to you repeatedly and partly defeating "decisions front-loaded." Enumerate every plausible
   cross-module interface now. (Without this single owner, every design `covers_req_ids` becomes
   an orphan and the §4.2 closure gate fails closed on every run — the reverse-review's top finding.)
6. **Resolve the three model tiers** (rules in "Model tiers" under Phase 1): take each tier's
   preferred model from the Workflow tool's current `model` enum; AskUserQuestion only if a
   preferred name is missing, or to record an explicitly requested thrifty run. Freeze the three
   literals into the registry's `models` field.
7. **Freeze the authority and decision policy.** Persist `<run-dir>/decision-envelope.json`
   with scope, write roots, destructive-operation limits, external systems, network, secrets,
   spending, model substitutions, and acceptance authority. Initialize `decision-ledger.json`
   with `python3 $ROOT/scripts/decision_ledger.py init <run-dir> <envelope.json>`.
   This is the last ordinary human decision point.

8. **Eliminate-a-class goals need a CENSUS, not an audit (anti-fake-completion at the SET level).**
   When the goal is to remove/eliminate/harden a CLASS — every fabrication, every fake-success,
   every swallowed error of kind K, every operation of type T that must reach effect M — the task
   list MUST be derived from an EXHAUSTIVE ENUMERATION of that class, not from a smell-based audit.
   Pattern-matching (grep the bad shape: `try?`, `isAtEnd ? default`, hardcoded sample data) finds
   members that have a *tell*; it is structurally blind to members whose defect is an ABSENCE — an
   operation that shows success but never calls the server looks EXACTLY like correct code, so no
   grep, no passing test, and no per-task mutation will ever surface it. Absence is invisible; only
   a coverage method finds it. So for a class goal, produce a **census artifact FIRST**: enumerate
   the full population (every operation / endpoint / entry point / RPC), then check each against its
   contract. The cheapest, sharpest census tool is the **dead-endpoint sweep** — a server-contract
   method (RPC, handler, hook) that is *defined but has zero production call sites* is a
   fake-success smoking gun (someone built the capability and then faked it locally instead of
   calling it). Every census member then maps to a task OR is marked verified-clean-with-evidence.
   A run whose task set was NOT backed by such a census carries LOW completeness confidence into
   Phase 2 (the class is "instances-fixed", NOT "class-eliminated") — see Phase 2. Corollary for
   the decomposition: prefer building "every write operation reaches a real effect or is explicitly
   `localOnly`" as a *structural, machine-checkable invariant* over relying on future vigilance —
   fake-success has no tell, so the only durable defense is making it either unrepresentable or
   mechanically detectable.

After Phase 0, do not ask, request approval, wait for input, or return at a stage boundary.
Every unseen choice becomes an autonomous decision record: rank viable options by authority,
safety, reversibility, repository convention, blast radius, evidence, maintenance cost, then
stable name; persist the recommended in-envelope choice before acting. If no option is
authorized, collect only non-mutating evidence, defer that branch, transitively skip its
dependents, and continue everything independent. Phase 2 discloses all such choices.

## Phase 1 — Autonomous pipeline (call Workflow once per stage; read result; decide next)
For stages **1.1–1.5**, `status:"escalate"` means **decision proposed**, never "ask the human."
The main session generates alternatives, selects the highest-ranked authorized recommendation,
records it through `decision_ledger.py`, applies/fixes/replans, finalizes the record with an
artifact/event reference, and continues. If none is authorized, record `deferred`, skip only the
affected branch and dependents, and continue.
(**§1.6 is the exception**: execution-phase escalations do NOT halt the line — see "Escalation
semantics" in §1.6: record, transitively skip dependents, keep the rest running, report in Phase 2.)

**Workflow invocation rules (apply to EVERY stage):**
- **Inline task data into script files; launch via `scriptPath`.** Do NOT pass stage payloads
  (module lists, task arrays, registry blocks) through Workflow `args` — in a real 277-task run,
  `args.modules` arrived `undefined` mid-pipeline. Write each stage's data INLINE into the
  orchestration script file itself (a generated `.js`/`.mjs` per stage is fine), then start the
  Workflow with `scriptPath`. The script must be self-contained: re-readable, re-runnable,
  resumable without the session's memory.
- **Model literals are always explicit.** Every `agent()` call writes its tier's frozen literal,
  e.g. `{model:'opus'}`. NEVER write `'default'` and NEVER omit `model` — both inherit the
  *session* model, so a non-Opus session silently runs supervisors/critics on the wrong model.

`module-too-large` is resolved autonomously: split at the first stable package/component,
independent-acceptance, or non-cyclic interface boundary; then prefer the lowest touched-path
cut and canonical path name. Record the split. If every split changes user-visible scope,
defer only the excess branch.

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
  verification rigor is the trust root; must never resolve weaker than BULK. In `agent()` calls
  this is always the explicit literal (e.g. `{model:'opus'}`) — never `'default'`, never omitted
  (see "Workflow invocation rules" above; inherited session models are a silent downgrade).
- **BULK（执行）** = prefer `sonnet`; candidate `haiku`. Used by executor — token thrift on
  bulk mechanical coding only.

Downgrade rules — only Phase 0-authorized substitutions:
- Phase 0 may authorize explicit fallback literals and ordering. The orchestrator never uses
  an unlisted model.
- Record every substituted tier in the decision ledger and Phase 2 report.
- **Mid-run model failure:** retry, then use only a substitution explicitly authorized by the
  frozen decision envelope and record it. Without an authorized substitution, defer the
  affected branch and continue; never silently downgrade and never pause for approval.

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
- Unresolved after rounds becomes a recorded autonomous fix/replan decision or a deferred
  affected branch; it never halts for user input.

### 1.3 Plan — Workflow
`pipeline` over designs; each `agent` uses `$ROOT/knowledge/prompts/plan-agent.md` with `{model: THINK}` and emits the plan-task array.
For each plan, run `python3 $ROOT/scripts/validate_plan_tasks.py <tasks.json> registry.json`
(registry.json from §1.2 — validates `implements`/`requires` against the frozen vocabulary);
if BLOCKED, bounce back to the plan agent until every task has `touched_paths` +
`acceptance_cmd` + on-registry interface tags.
Deterministic size check: a validated plan with > 20 tasks invokes the autonomous split rule
above; record the chosen seam or defer only the excess branch.

### 1.4 Reverse review — Workflow
A Workflow `agent` with `$ROOT/knowledge/prompts/reverse-critic.md` and `{model: THINK}` over all spec/design/plan docs
(≤3 rounds, self-fix or escalate).

### 1.5 Orchestrate — deterministic
Concatenate all plan tasks into one array, run
`python3 $ROOT/scripts/build_task_dag.py <all-tasks.json>`. Cross-module ordering comes from
the derived interface edges (`requires` → `implements` join over the registry vocabulary) —
this is the ONLY mechanism ordering tasks across modules, since `depends_on` is intra-module.
BLOCK (cycle / missing dep / required interface nobody implements) → fix via plan agent.
Keep `effective_deps` (explicit `depends_on` + derived interface edges — what §1.6's ready-set
scheduler consumes), `isolate_groups` (file/resource-colliding groups; serialize), and
`resource_groups` (per-resource mutex sets). `layers` is still emitted but is informational
only — §1.6 no longer drains layer barriers. Persist to `orchestration.json`. Surface any
`warnings` in the final report.

### 1.6 Concurrent execute + supervise — Workflow
Maintain a scratch `retry-ledger.json` (`{task_id: retries}`) — the soft-retry budget is
unenforceable without it (a stateless prose loop drifts).

**Scheduling — dependency-ready, not layer barriers.** Do NOT drain `layers` as barriers — a
single slow task then stalls every same-layer sibling (in a real 277-task run this idled most
of the fleet). The orchestration script runs a **ready-set loop** over `orchestration.json`:
- A task is READY when every id in its `effective_deps` entry is supervisor-confirmed
  (`done:true`). A dep that was escalated/skipped never satisfies readiness — the dependent is
  skipped too (see "Escalation semantics" below).
- Dispatch **every ready task immediately — no skill-level in-flight cap.** Executor and
  supervisor agents are LLM calls, not machine-bound work; the platform Workflow cap
  (min(16, CPU cores − 2) per workflow) already queues any excess, so an extra cap here only
  idles the fleet. Whenever a task confirms, recompute the ready set and dispatch the new
  ready tasks — no barrier, no waiting for siblings.
- **Machine-heavy exception (warn, don't silently throttle):** if tasks run heavy LOCAL work
  (full builds, whole-suite tests, docker builds — typically visible in `acceptance_cmd` or
  the task description), uncapped dispatch can thrash the machine. When authoring the
  Workflow, scan the task list for such work; if found, WARN the user before launching and
  honor a user-chosen `max_concurrency` (a simple in-flight counter in the script). Never
  lower the cap yourself without telling the user.
- **Mutex discipline (preserves the isolate-group serial semantics):** at most ONE in-flight
  task per `isolate_groups` entry and per `resource_groups` entry, members dispatched in
  declaration order. A ready task whose group has a sibling in flight (or a pending merge)
  simply waits — it is not dispatched until the group frees (and when a user cap is active,
  it must not hold a slot while waiting).

**Worktree isolation — know what it actually isolates.** Workflow `isolation:'worktree'`
snapshots the SESSION's repo (the cwd this skill runs in), NOT an arbitrary target repo. If
the repo being built is not the session cwd, worktree isolation buys nothing — DISABLE it and
run each collision group's tasks **serially against the main tree** (the mutex discipline
above already guarantees one writer at a time). That main-tree-serial mode is the safe
default for collision groups; only use worktree-per-task + merge-after-confirm when the
target repo IS the session cwd:
- **Worktree mode** (target repo == session cwd): each group member runs in its own
  `agent(..., {isolation:'worktree'})`; after the supervisor confirms `done:true`, **merge
  that worktree back to the main tree before starting the next task in the group.** Do NOT
  use the barrier-less `pipeline` to merge colliding worktrees — it has no serialization point.
- **Main-tree commit discipline (learned from a live Codex-port run):** never rely on
  executors committing their own work — an uncommitted main tree poisons every later
  worktree branch/merge ("untracked working tree files would be overwritten"). YOU
  safety-commit the main tree (`git add -A && git commit`) after each confirmed
  free task and again right before every worktree merge.

**Infrastructure failure ≠ business failure.** An agent process dying, provider quota
exhaustion, a network error, or a `null`/`undefined` agent return is an INFRASTRUCTURE
failure, not evidence the task is hard: do NOT decrement that task's soft-retry budget.
Re-dispatch the same task with backoff (e.g. 1 min, then 5 min); only after ~3 consecutive
infrastructure failures on the same dispatch treat it as an escalation (record per the
semantics below). Burning the 2-retry budget on a flaky network turns transient noise into
fake "task is impossible" verdicts.

**Escalation semantics (execution phase — record, skip, keep going).** Unlike §1.1–1.5, one
escalating task must not park hundreds of independent ones. When an executor returns
`status:"escalate"` or a task exhausts its soft-retry budget:
1. **Record (记账):** append to a scratch `escalation-ledger.json`:
   `{task_id, reason, evidence, retries, hypotheses_tried?}`.
2. **Transitively skip (传递跳过):** walk `effective_deps` forward and mark every transitive
   dependent `skipped(blocked_by=<task_id>)` — they are never dispatched.
3. **Keep running:** the ready-set loop continues for everything else.
4. **Report at close (收尾呈报):** after the loop drains, surface the full ledger — every
   escalation with its reason/evidence AND its complete skipped chain — in the Phase 2 report.
   Skipped work is enumerated, never silently folded into "done".

**Reality-gate handling (实现已交,自主证明待人工 — must NOT block the line).** A
`reality_gate:true` task gets at most ONE autonomous acceptance attempt. When the supervisor
returns a verdict with `reality_gated:true` (acceptance failed for environmental reasons, not a
code defect — see prompts/supervisor.md):
- **Do NOT soft-retry** it (no retry-budget burn — the failure is environmental, not a hard task).
- **Do NOT transitively skip its dependents.** The implementation is committed, so the DAG
  treats the task's interface output as satisfied; dependents stay `ready` and keep running.
  (This is the precise failure mode this release exists to kill — see §1.6.c / Phase 2.)
- **Record it** in a scratch `reality-gate-ledger.json`: `{task_id, reason, runbook_ptr}`
  (`runbook_ptr` points at the human-acceptance runbook the plan agent wrote into the plan
  markdown). This ledger feeds the Phase 2 (b) reality-gate list.
- A plain `done:false` (no `reality_gated`) on a `reality_gate` task is a real code defect and
  is soft-retried like any other task — `reality_gate` only changes the ENVIRONMENTAL-failure path.

**Persistent task-state ledger (mid-run observability).** As the ready-set loop runs, write a
`task-state.json` to disk on every status transition:
`{task_id: {status: "done"|"failed"|"skipped"|"reality_gated", attempts, last_evidence_excerpt, last_ts}}`.
This makes a mid-run completeness census and a "re-run only what remains" restart a single file
read rather than an archaeology dig through transcripts. (Learned the hard way: when verdicts
carried no `task_id` and the Workflow only returned its ledger at the very end, the run was
unobservable mid-flight, and cached replays were misread as fresh progress. The on-disk ledger
closes that observability gap and pairs with the watchdog's `resumeFromRunId` resume.)

**External watchdog (main session — survive zombie runs).** While a §1.6 Workflow runs, the
main session does not just block on the result: schedule a periodic wakeup (e.g. every 10
minutes via ScheduleWakeup) and on each tick check two liveness signals — the target repo's
commit stream (`git log -1 --format=%ct` advancing) and the Workflow run's transcript
directory mtimes. **Stall criteria:** > 35 min with no agent activity on either signal; OR a
single agent transcript growing past ~3 MB with no new commits (a context-thrash loop). On
stall: `TaskStop` the stuck run, then resume the Workflow from the persisted stage script
with `resumeFromRunId` — the ledgers + `orchestration.json` make the loop re-enterable, which
is exactly why the stage script must be self-contained (see "Workflow invocation rules").

**Green-push companion (long pipelines, optional).** For multi-hour runs feeding a shared
remote, start a background loop alongside §1.6: fetch/merge `origin` into a **dedicated
integration worktree** (never the executors' tree), run the full build + test suite there,
and push ONLY when everything is green. The remote keeps moving during the run, and a red
tree is never pushed. The loop has no knowledge of individual tasks — it is a pure
repo-level companion.

Stages:
- executeStage: `agent($ROOT/knowledge/prompts/executor.md prompt, {model: BULK})` (+ `{isolation:'worktree'}` for group members).
- verifyStage: `agent($ROOT/knowledge/prompts/supervisor.md prompt, {schema: verdict, model: VERIFY})` — fresh context,
  reruns `acceptance_cmd`. On `done:false`: read the task's `retries` from the ledger;
  **if `retries < 2` → increment and bounce to executor; if `retries == 2` → escalate** (per
  the escalation semantics above: record in the ledger, skip dependents, keep the line
  running). This is spec §4.6's "soft-retry ≤2" = the initial attempt plus at most 2 retries
  (3 dispatches total) — and it counts BUSINESS failures only; infrastructure failures
  re-dispatch without touching the budget (see above).
- **Vacuous auto-recovery:** if the verdict has `vacuous:true` (acceptance passed only because
  0 tests ran), the bounce to the executor MUST append the anti-vacuous instruction — *"the
  acceptance selects tests by name and matched 0; create the named test with ≥1 real assertion
  and confirm a non-zero executed-test count."* Do not escalate a `vacuous` failure to the human
  until the soft-retry budget is genuinely exhausted — it is almost always self-fixable, and the
  deterministic `validate_plan_tasks.py` gate should have caught it at §1.3 anyway.

**Module release judgment (G8) — split in two; a reality gate must NOT block it.** A module's
release-readiness judgment is computed from its gates, but the gates fall into TWO classes:
- **Autonomously-provable gates (blocking):** every non-`reality_gate` task in the module must
  be supervisor-confirmed `done:true`. These genuinely gate the module's release judgment.
- **Reality-gate items (non-blocking):** every `reality_gate` task that came back
  `reality_gated:true` goes onto the Phase 2 (b) human-acceptance list. It does **NOT** block
  the module's release judgment and does **NOT** block downstream.

**Cross-module downstream depends on outputs, never on a release judgment.** A downstream
module depends on the *artifacts/interfaces* (`implements`/`requires`) an upstream module
produces — NOT on whether the upstream module "passed G8". So even when an upstream module's
UI/E2E gate is reality-gated and awaiting human verification, every downstream module that only
needs the upstream's committed interface keeps advancing.

**Failure mode this release exists to prevent (write it down):** a single environmental gate
(a flaky simulator/UI gate / a device-bound acceptance) must NEVER block a module's release
judgment NOR transitively skip the entire downstream chain. In a prior large run, device-bound
acceptances flaked, soft-retried to exhaustion, drove 0 modules to release-ready, and every
cross-module downstream was then transitively skipped — one environmental problem paralyzed the
whole closeout. The reality-gate path (one autonomous attempt → ledger → human list, never a
soft-retry, never a dependent skip) is the fix.

## Phase 2 — Report
Update the overview and write a final report: assumptions the autonomous agents made, all
escalation points + resolutions, the independently-verified completion list (distinguish
"executor-claimed" from "supervisor-confirmed"), DAG warnings, and learnings.

The report MUST merge normal ledger, emergency-journal, and degraded in-memory decision records
and include: **Autonomous decisions** (options, chosen recommendation, reason, risk, authority
basis, outcome, affected artifacts), **Assumptions made**, and **Deferred by authority boundary**
(fallback, reason, and complete skipped-dependent chains). Every decision appears exactly once.

After delivering the report, end the megastorm run. Do not invoke, suggest, or invite
`/cross-exam`; it remains a separate command that runs only when the user explicitly requests it.
For an eliminate-a-class goal (Phase 0 step 8), treat "class eliminated" as UNPROVEN until the
Phase 0 census is rerun against the delivered tree and confirms no class member was missed. Never
let the run's own "N/N done" stand in for that census.

**Mandatory escalation + skip accounting (from §1.6).** The report MUST render the full
`escalation-ledger.json`: every execution-phase escalation (task id, reason, evidence,
retries, hypotheses tried) AND, for each one, its complete transitively-skipped chain
(`skipped(blocked_by=...)` tasks). Completion percentages are computed over dispatched tasks
only and must state the skipped count alongside — "N done / M skipped via K escalations",
never a bare "N done".

**Mandatory "Reality gate" section.** Every report MUST split completion into two explicit lists:
(a) **autonomously verified** — the supervisor reran the real `acceptance_cmd` and it genuinely
passed; and (b) **requires human / hardware / external verification** — anything whose real-world
success cannot be proven in CI/simulator (live media, real devices, third-party prod systems,
physical I/O). **The (b) list is fed by `reality-gate-ledger.json`** (§1.6): every
`reality_gated:true` task, with its recorded reason and the `runbook_ptr` to the
human-acceptance runbook the plan agent wrote into the plan markdown. For every item in (b),
emit (or point at) that concrete runbook (exact steps, what to observe, pass criteria). **"All
tasks green" must NEVER be presented as "the feature works" when (b) is non-empty.** Mechanical
task-completion ≠ verified capability; conflating them is the precise honesty failure megastorm
exists to prevent. Reality-gated items in (b) are "implementation committed, proof pending" —
they are NOT counted as failures and NOT counted as autonomously-verified done.

**Mandatory "Completeness confidence" section (SET-level anti-fake-completion).** Per-task
supervision proves each task was done right; it says nothing about whether the task SET was the
right set. A green "N/N done" is itself a fake-completion when the population was under-enumerated —
the run reports the goal met while whole class members were never ticketed. So every report MUST
state, explicitly: was the task set derived from an **exhaustive census** (Phase 0 step 8:
enumerate-the-population-then-check-each, e.g. a dead-endpoint sweep) or from a **smell-based
audit** (grep the bad shape)? 
- **Census-backed** → you may state the class is covered, and cite the census (population size, how
  each member was dispositioned: task vs verified-clean).
- **Audit-based (or unknown)** → completeness is UNVERIFIED. The report must say so in these words,
  must NOT present "N/N done" as "the class is eliminated", and must identify the census sweep as
  the outstanding gate. This is the exact trap the pipeline exists to avoid at the task
  level, applied one level up: absence has no tell, so an unproven-complete set is guilty until a
  coverage method proves it innocent.

## Artifacts (superpowers-native)
One overview + standard superpowers docs:
`docs/superpowers/specs/<date>-<goal>-overview.md`, `...-<module>-design.md`,
`docs/superpowers/plans/<date>-<module>-plan.md`, plus machine `orchestration.json`.
