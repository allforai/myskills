# Superstorm Execution Playbook

Normative detail for the Superstorm skill. `$ROOT` = `${CLAUDE_PLUGIN_ROOT}`.

**Invariant:** decisions front-loaded → autonomous → self-fix loop → disclose at close.
All ordinary human interaction ends with Phase 0.

## Contents

- Phase -1: preflight and environment capabilities
- Phase 0: modules, specs, registry, models, authority, and census
- Phase 1: closure, plans, DAG, concurrent execution, and supervision
- Phase 2: evidence-backed closeout

## Phase -1: Preflight

Verify the Skill registry exposes the namespaced skills `superpowers:brainstorming`,
`superpowers:writing-plans`, and `superpowers:executing-plans`. Do not inspect fixed cache paths.
If any is missing, stop and tell the user to install the superpowers marketplace.

Probe and record `## Environment capabilities` in the overview:

- display/UI or stable headless display;
- launchable simulator/emulator;
- reachable real hardware or physical I/O;
- reachable shared/external systems and credentials.

Classify each `available`, `flaky`, or `absent`. Planning must mark proof that depends on a
flaky/absent capability as a reality-gate candidate; never plan proof this environment cannot run.

## Phase 0: Decisions Front-loaded

This phase is interactive.

1. Inspect repository structure, recent commits, and `docs/`; summarize the current state.
2. Run `superpowers:brainstorming` to decompose the goal into modules, boundaries, dependencies,
   and milestone scope. Write the approved draft to
   `docs/superpowers/specs/<date>-<goal>-overview.md`; put deferred scope in `## Roadmap`.
3. Audit granularity and get the adjusted breakdown approved:
   - **Size:** estimate plan size. Past roughly 20 tasks, look for a cohesion seam; split only
     where each interface stays on one side and each half has its own acceptance. A cohesive
     module that is simply large stays whole — never defer user-visible scope to satisfy a count.
   - **Cohesion:** one module has one concern; a description requiring "and" twice suggests a split.
   - **Balance:** merge candidates that would share most interfaces.
   Present `module → estimated size → verdict → action`.
4. Run `superpowers:brainstorming` for every module until all module specs are approved.
5. As the single registry owner, reconcile the specs and write one JSON registry into the overview
   between `<!-- superstorm-registry:start -->` and `<!-- superstorm-registry:end -->` (runs
   started before the rename carry `megastorm-registry` markers; read them the same way), per
   `$ROOT/knowledge/schemas.md`:
   - `requirements`: one `R-<module>-NN` ID for every requirement;
   - `interfaces`: a generous closed vocabulary of `<kind>:<lowerCamelCaseName>`, where `kind` is
     `api`, `event`, `data`, or `ui`.
   Workers never extend the frozen vocabulary. In Phase 1 only the main orchestrator may revise an
   exact evidence-backed contract after persisting an authorized decision; otherwise defer it.
6. Freeze the model policy, with a recommendation. Default: every `agent()` omits `model` and
   inherits the session model — designers, critics, planners, supervisors and executors alike.
   Judgment roles (design, closure and reverse critics, plan, supervisor) never run below the
   session model: a supervisor weaker than the code it verifies is not a trust root, and a
   planner that misses a seam costs a whole module. The only optional downgrade is the executor.
   Read the Workflow tool's current `model` enum, order it by what you know of those models, and
   name the tier one step below the session model (never the cheapest: implementation is the most
   agentic work in the run). Present two concrete options and say which you recommend and why:
   - **A evidence-first:** all roles inherit the session model.
   - **B cost-first:** executors run on `<next tier down>`; every other role inherits.
   Recommend B when the user mentioned cost or the plan fans out many small, well-specified
   tasks; recommend A when tasks are exploratory, cross-cutting, or UI-driving, where a weaker
   executor is more likely to fail and be redispatched on the session model, which costs more
   than it saved. The literal comes from the enum read now, never from memory or from this file;
   say that the ordering is your knowledge, not a price list. Record the outcome in the registry
   `models` field (`executor`: literal or `"session"`; `recommended`; the user's words; time). A
   thrifty request is answered here and nowhere else.
7. Set `<run-dir>` to the versionable
   `docs/superpowers/runs/<date>-<goal>/`. Persist its `decision-envelope.json` with scope, write
   roots, destructive limits,
   external systems, network, secrets, spending, model substitutions, and acceptance authority.
   Also freeze a machine-load policy: explicit `max_concurrency` when known, or permission for the
   orchestrator to select and record a safe value from observed CPU/memory and acceptance-command
   cost. Phase 1 never asks for this value.
   Initialize with:
   `python3 $ROOT/scripts/decision_ledger.py init <run-dir> <envelope.json>`.
8. For a goal that eliminates or enforces a whole class, create an exhaustive census before tasks:
   enumerate every operation, endpoint, entry point, RPC, handler, or hook, then map each member to
   a task or verified-clean evidence. A smell-based audit cannot prove an absent call or effect.

After Phase 0, never ask, request approval, wait for input, or return at a stage boundary. Rank
unseen choices by authority, safety, reversibility, repository convention, blast radius, evidence,
maintenance cost, then stable name. Persist the recommended authorized choice before acting. If no
option is authorized, gather only non-mutating evidence, defer that branch, transitively skip its
dependents, and continue independent work.

## Phase 1: Autonomous Pipeline

`status:"escalate"` is a decision proposal at every stage. Select, record, apply, and finalize
the best authorized recommendation; otherwise defer only the affected branch. In stage 1.6 an
executor escalation that carries `proposed_touched_paths` is resolved the same way (see
Escalation below); only an escalation with no authorized resolution skips its dependent chain.

Every autonomous decision MUST use `decision_ledger.py record` before its action and
`decision_ledger.py finalize` after the observable outcome. Never edit `decision-ledger.json`
directly. The script owns authority-basis validation, the single-writer lock, monotonic IDs, three
atomic write attempts, emergency-journal fallback, and one-time finalization. If both the normal
ledger and emergency journal are unwritable, perform no further mutations: retain a schema-complete
degraded in-memory record, drain no new work, and transition directly to the Phase 2 degraded
report. Lack of durable decision state never grants permission to continue mutating.

Every Workflow stage must:

- persist all task data inline in a self-contained, rerunnable `.js`/`.mjs` stage script and launch
  it via `scriptPath`; never pass large stage payloads through Workflow args;
- pass `model` only where the frozen policy names a literal (executors under option B); every
  other `agent()` omits `model` and inherits; record the effective model of every dispatch in the
  task state so the report can say who produced which evidence;
- persist machine state needed to resume without conversation memory.

At each stable stage boundary, persist the current registry, task/DAG inputs, stage status, ledger
pointers, source commit, and integration commit under `<run-dir>`, then commit them with the
project artifacts. Push only when the run's authority permits it. Same-host recovery may use
`resumeFromRunId`; cross-host recovery must use the versioned run directory plus reachable Git
commits and must redispatch only work not supported by reconciled Git/evidence. A transcript or
task-state claim alone is never portable completion proof.

On a `size_warning`, split only at a stable package/component, independent-acceptance, or
non-cyclic interface boundary; prefer the lowest touched-path cut and then canonical path name.
Record the split. If no such boundary exists, record the size as an accepted assumption and keep
the module whole; a count never justifies deferring scope or cutting an interface in two.

Model failure or a defective return from a downgraded executor: retry once on the same model, then
redispatch on the session model and record `first_model` on the task. Falling back to the session
model is always authorized; moving to any other model mid-run is not. Never pause for approval.

### 1.1 Design

Use Workflow `parallel`/`pipeline` across all module specs. Each agent receives the module spec, the
complete frozen registry, `$ROOT/knowledge/prompts/design-agent.md`, and the design-manifest schema;
no `model` argument (inherit). Collect every manifest.

### 1.2 Closure

Extract the registry JSON between its markers; write `requirements.json`, `registry.json`, and
`manifests.json`. Run:

```bash
python3 $ROOT/scripts/check_closure.py requirements.json manifests.json registry.json
```

On uncovered/orphan requirements or dangling/off-registry interfaces, feed errors to a design fix
agent and rerun, at most three rounds. Then run a fresh agent (inherit) with
`$ROOT/knowledge/prompts/closure-critic.md` for prose-level closure, also at most three rounds.
Unresolved findings require an authorized fix/replan or a deferred affected branch.

### 1.3 Plan

Run one plan agent per design (inherit) using `$ROOT/knowledge/prompts/plan-agent.md`. Each emits the
plan-task array. Validate every plan:

```bash
python3 $ROOT/scripts/validate_plan_tasks.py <tasks.json> registry.json
```

Bounce hard failures (missing `touched_paths`, blank `acceptance_cmd`, off-registry
`implements`/`requires`) to the plan agent. Vacuous-runner findings are warnings: forward them to
the plan agent once, but the authority on a zero-test pass is the supervisor's rerun, not a regex. Cross-module order comes from those
tags; `depends_on` is intra-module. Handle any `size_warning` as above. Proof requiring an unavailable
device, external system, or physical capability uses `reality_gate:true` and a non-empty
`runbook_ptr` with exact human verification steps.

### 1.4 Reverse Review

Run one fresh agent (inherit) with `$ROOT/knowledge/prompts/reverse-critic.md` over every spec, design, and
plan. Self-fix and rerun for at most three rounds, then apply escalation semantics.

### 1.5 Orchestrate

Concatenate tasks and run:

```bash
python3 $ROOT/scripts/build_task_dag.py <all-tasks.json>
```

A cycle, missing dependency, or unimplemented required interface blocks and returns to planning.
Persist `orchestration.json`, including:

- `effective_deps`: explicit dependencies plus derived interface edges;
- `isolate_groups`: file/resource collision mutex groups;
- `resource_groups`: shared-resource mutex groups;
- `layers`: informational only, never scheduling barriers.

Surface DAG warnings in Phase 2.

### 1.6 Execute and Supervise

Persist `retry-ledger.json`, `escalation-ledger.json`, `reality-gate-ledger.json`, and
`task-state.json`.

**Ready scheduling**

- A task is ready when every `effective_deps` ID is supervisor-confirmed `done:true` or is a
  committed `reality_gated` implementation.
- Dispatch every ready task immediately; recompute readiness after every confirmation. Do not add
  a skill-level cap over the Workflow platform cap.
- If acceptance commands contain machine-heavy local work such as full builds, whole suites, or
  Docker builds, apply the Phase 0 machine-load policy. If no explicit value was frozen, select a
  safe recommendation from observed CPU/memory and command cost, persist it as an autonomous
  decision, and continue without asking. Never silently cap.
- At most one task per isolate/resource group may be in flight. Waiting on a mutex consumes no
  concurrency slot and follows declaration order.

**Isolation and Git**

Workflow `isolation:'worktree'` isolates only the session cwd. If the target repository is not the
session cwd, disable worktree isolation and serialize collision groups against the main tree. If it
is the cwd, run each colliding task in its own worktree and merge only after supervisor
confirmation, before the next group member. Safety-commit confirmed main-tree work before creating
or merging worktrees; never assume executors committed.

**Execution and verification**

- Executor: `$ROOT/knowledge/prompts/executor.md`, `model` only if the frozen policy names an
  executor literal, plus worktree isolation when valid.
- Supervisor: fresh context, `$ROOT/knowledge/prompts/supervisor.md`, verdict schema, no `model`
  argument; rerun the real `acceptance_cmd`.
- A business failure gets the initial attempt plus at most two retries. Read and update the retry
  ledger; after the third failed dispatch, escalate.
- Infrastructure failure (process/provider/network/null result) uses separate backoff, e.g. one
  then five minutes, and never consumes business retries. After about three consecutive
  infrastructure failures for the dispatch, escalate.
- A `vacuous:true` verdict returns to the executor with an explicit requirement to create the named
  test with at least one real assertion and prove a non-zero executed-test count.

**Escalation**

An executor escalation with `proposed_touched_paths` is a plan defect, not a task failure:

1. check every proposed path against the envelope's write roots and against the `touched_paths`
   of every in-flight and ready task (`isolate_groups`);
2. no collision and inside authority → `decision_ledger.py record`, extend the task's
   `touched_paths`, recompute `isolate_groups`, redispatch the task (no business retry consumed),
   `finalize` on the supervisor's verdict;
3. a collision → wait for the colliding task's confirmation, then redispatch; outside authority →
   defer as below.

For exhausted business retries, or an escalation with no authorized resolution:

1. append `{task_id, reason, evidence, retries, hypotheses_tried?, proposed_touched_paths?}` to the
   escalation ledger;
2. mark every transitive dependent `skipped(blocked_by=<task_id>)`;
3. continue all independent ready work;
4. report the escalation and complete skipped chain in Phase 2.

**Reality gates**

A `reality_gate:true` task gets one autonomous acceptance attempt. On
`reality_gated:true` environmental failure:

- do not retry or spend business budget;
- do not skip dependents: committed interface output satisfies the DAG;
- append `{task_id, reason, runbook_ptr}` to the reality-gate ledger.

A plain `done:false` is a code defect and follows business retries. Reality-gated work is
implementation committed, proof pending: it is neither autonomously verified nor failed. It does
not block module release judgment or downstream work that consumes the committed interface.

**Observations**

Append every `observations[]` entry from a verdict to `<run-dir>/observations-ledger.json` with the
verdict's `task_id` and timestamp. An entry with `scope: "task:<id>"` on a task already confirmed
`done:true` is a decision: record via `decision_ledger.py` whether to reopen that task (redispatch
with the observation as refutation input; its dependents are not skipped while it reruns) or to
carry the finding to Phase 2; never leave it unrecorded. `scope: "repo"` entries feed the Phase 2
completeness section and, for class goals, the census rerun.

**Persistent observability**

Write every transition atomically to `task-state.json`:

```json
{"task_id":{"status":"done|failed|skipped|reality_gated","attempts":1,"last_evidence_excerpt":"...","last_ts":"..."}}
```

While Workflow runs, schedule a roughly ten-minute watchdog over four progress signals:
target-repo commits, Workflow transcript mtimes, per-task log mtimes (executors and supervisors
tee long acceptance and build output to `<run-dir>/logs/<task_id>.log`), and worktree file
mtimes. A task is stalled only when none of the four has moved for its threshold. The threshold
is per task: the run default (about 35 minutes) or 1.5 times the acceptance command's known
cost, whichever is larger; record the threshold in `task-state.json` when the task is dispatched.
A transcript that keeps growing while commits, logs and files do not move is thrash, not
progress. On a stall, stop and `resumeFromRunId` from the persisted stage script and count it as
an infrastructure failure. This is same-host recovery. For another host, use the versioned
boundary checkpoint described above; never reference a machine-local Workflow run ID.

For a multi-hour shared-remote run, an optional dedicated integration worktree may repeatedly merge
origin, run the full build/test suite, and push only green results. It never uses an executor tree.

## Phase 2: Report

Update the overview and write the final report. Merge the normal decision ledger, emergency
journal, and degraded in-memory records so every decision appears exactly once.

Mandatory sections:

- **Autonomous decisions:** options, recommendation, reason, risk, authority basis, outcome, and
  affected artifacts.
- **Assumptions made.**
- **Deferred by authority boundary:** fallback, reason, and complete dependent skip chains.
- **Verified completion:** distinguish executor claims from supervisor-confirmed real acceptance.
- **Escalations and skips:** render the full escalation ledger as
  `N done / M skipped via K escalations`; never use a bare completion percentage.
- **Reality gate:** separate autonomously verified work from human/hardware/external proof pending;
  include every reason and concrete `runbook_ptr`. Never say the feature works while this list is
  non-empty.
- **Observations:** every entry of `observations-ledger.json` with its disposition (reopened,
  carried, folded into the census); an observation is never silently absent.
- **Completeness confidence:** for class goals, rerun and cite the census with population and
  disposition. If based on an audit or unknown enumeration, state `Completeness unverified`, claim
  only instances fixed, and name the census as an outstanding gate.
- DAG warnings and learnings.

End the run after delivering the report. Do not invoke, suggest, or invite `/cross-exam`; it runs
only on explicit user request.

## Artifacts

- `docs/superpowers/specs/<date>-<goal>-overview.md`
- `docs/superpowers/specs/<date>-<module>-design.md`
- `docs/superpowers/plans/<date>-<module>-plan.md`
- `docs/superpowers/runs/<date>-<goal>/` for versioned boundary state
- `orchestration.json` and run-local machine ledgers
