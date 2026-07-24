# Megastorm Execution Playbook

Normative detail for the Megastorm skill. `$ROOT` = `${CLAUDE_PLUGIN_ROOT}`.

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
   - **Size:** estimate plan size; split or defer anything likely to exceed 20 tasks.
   - **Cohesion:** one module has one concern; a description requiring "and" twice suggests a split.
   - **Balance:** merge candidates that would share most interfaces.
   Present `module → estimated size → verdict → action`.
4. Run `superpowers:brainstorming` for every module until all module specs are approved.
5. As the single registry owner, reconcile the specs and write one JSON registry into the overview
   between `<!-- megastorm-registry:start -->` and `<!-- megastorm-registry:end -->`, per
   `$ROOT/knowledge/schemas.md`:
   - `requirements`: one `R-<module>-NN` ID for every requirement;
   - `interfaces`: a generous closed vocabulary of `<kind>:<lowerCamelCaseName>`, where `kind` is
     `api`, `event`, `data`, or `ui`.
   Workers never extend the frozen vocabulary. In Phase 1 only the main orchestrator may revise an
   exact evidence-backed contract after persisting an authorized decision; otherwise defer it.
6. Resolve model tiers from the Workflow tool's current `model` enum and freeze explicit literals
   in the registry:
   - **THINK:** prefer `fable`, then offer `opus → sonnet`;
   - **VERIFY:** prefer `opus`, then offer `fable → sonnet`; never weaker than BULK;
   - **BULK:** prefer `sonnet`, then offer `haiku`.
   Candidate order is a recommendation, not automatic fallback. If the preferred literal is
   unavailable, ask now and record the choice. An explicitly requested thrifty run is also frozen
   now.
7. Set `<run-dir>` to the versionable
   `docs/superpowers/runs/<date>-<goal>/`. Persist its `decision-envelope.json` with scope, write
   roots, destructive limits,
   external systems, network, secrets, spending, model substitutions, and acceptance authority.
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

For stages 1.1-1.5, `status:"escalate"` is a decision proposal. Select, record, apply, and finalize
the best authorized recommendation; otherwise defer only the affected branch. Stage 1.6 records an
escalating task, skips its dependent chain, and keeps the rest running.

Every Workflow stage must:

- persist all task data inline in a self-contained, rerunnable `.js`/`.mjs` stage script and launch
  it via `scriptPath`; never pass large stage payloads through Workflow args;
- give every `agent()` its frozen explicit model literal; never omit `model` or use `"default"`;
- persist machine state needed to resume without conversation memory.

At each stable stage boundary, persist the current registry, task/DAG inputs, stage status, ledger
pointers, source commit, and integration commit under `<run-dir>`, then commit them with the
project artifacts. Push only when the run's authority permits it. Same-host recovery may use
`resumeFromRunId`; cross-host recovery must use the versioned run directory plus reachable Git
commits and must redispatch only work not supported by reconciled Git/evidence. A transcript or
task-state claim alone is never portable completion proof.

On `module-too-large`, split at the first stable package/component, independent-acceptance, or
non-cyclic interface boundary; prefer the lowest touched-path cut and then canonical path name.
Record the split. If every split changes user-visible scope, defer only excess scope.

Model failure: retry, then use only a substitution explicitly authorized by the frozen envelope and
record it. Without one, defer the branch. Never silently downgrade or pause for approval.

### 1.1 Design

Use Workflow `parallel`/`pipeline` across all module specs. Each agent receives the module spec, the
complete frozen registry, `$ROOT/knowledge/prompts/design-agent.md`, the design-manifest schema, and
`{model: THINK}`. Collect every manifest.

### 1.2 Closure

Extract the registry JSON between its markers; write `requirements.json`, `registry.json`, and
`manifests.json`. Run:

```bash
python3 $ROOT/scripts/check_closure.py requirements.json manifests.json registry.json
```

On uncovered/orphan requirements or dangling/off-registry interfaces, feed errors to a design fix
agent and rerun, at most three rounds. Then run a THINK agent with
`$ROOT/knowledge/prompts/closure-critic.md` for prose-level closure, also at most three rounds.
Unresolved findings require an authorized fix/replan or a deferred affected branch.

### 1.3 Plan

Run one THINK plan agent per design using `$ROOT/knowledge/prompts/plan-agent.md`. Each emits the
plan-task array. Validate every plan:

```bash
python3 $ROOT/scripts/validate_plan_tasks.py <tasks.json> registry.json
```

Bounce failures to the plan agent until every task has `touched_paths`, a non-vacuous
`acceptance_cmd`, and on-registry `implements`/`requires` tags. Cross-module order comes from those
tags; `depends_on` is intra-module. Apply the >20-task split rule. Proof requiring an unavailable
device, external system, or physical capability uses `reality_gate:true` and a non-empty
`runbook_ptr` with exact human verification steps.

### 1.4 Reverse Review

Run one THINK agent with `$ROOT/knowledge/prompts/reverse-critic.md` over every spec, design, and
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
  Docker builds, warn before launch and honor a user-chosen `max_concurrency`; never silently cap.
- At most one task per isolate/resource group may be in flight. Waiting on a mutex consumes no
  concurrency slot and follows declaration order.

**Isolation and Git**

Workflow `isolation:'worktree'` isolates only the session cwd. If the target repository is not the
session cwd, disable worktree isolation and serialize collision groups against the main tree. If it
is the cwd, run each colliding task in its own worktree and merge only after supervisor
confirmation, before the next group member. Safety-commit confirmed main-tree work before creating
or merging worktrees; never assume executors committed.

**Execution and verification**

- Executor: `$ROOT/knowledge/prompts/executor.md`, `{model: BULK}`, plus worktree isolation when
  valid.
- Supervisor: fresh context, `$ROOT/knowledge/prompts/supervisor.md`, verdict schema,
  `{model: VERIFY}`; rerun the real `acceptance_cmd`.
- A business failure gets the initial attempt plus at most two retries. Read and update the retry
  ledger; after the third failed dispatch, escalate.
- Infrastructure failure (process/provider/network/null result) uses separate backoff, e.g. one
  then five minutes, and never consumes business retries. After about three consecutive
  infrastructure failures for the dispatch, escalate.
- A `vacuous:true` verdict returns to the executor with an explicit requirement to create the named
  test with at least one real assertion and prove a non-zero executed-test count.

**Escalation**

For executor escalation or exhausted business retries:

1. append `{task_id, reason, evidence, retries, hypotheses_tried?}` to the escalation ledger;
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

**Persistent observability**

Write every transition atomically to `task-state.json`:

```json
{"task_id":{"status":"done|failed|skipped|reality_gated","attempts":1,"last_evidence_excerpt":"...","last_ts":"..."}}
```

While Workflow runs, schedule a roughly ten-minute watchdog. Check target-repo commit progress and
Workflow transcript mtimes. Stop and `resumeFromRunId` from the persisted stage script after more
than 35 minutes with neither signal, or when one transcript exceeds roughly 3 MB without commits.
This is same-host recovery. For another host, use the versioned boundary checkpoint described
above; never reference a machine-local Workflow run ID.

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
