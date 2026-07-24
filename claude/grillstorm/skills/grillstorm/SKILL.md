---
name: grillstorm
description: Adaptive, self-contained end-to-end software delivery pipeline that works backward from observable completion, routes small fixes through only the necessary Matt Pocock skill stages, and gives large goals intensive one-question-at-a-time grilling, module specs, interfaces, and test seams. It runs local and global spec closure, reuses or extracts justified modules before consumers, runs local and reverse task closure, simulates the workflow, then performs worktree-isolated concurrent coding, independent supervision, testing, diagnosis, review, repair, runtime validation, and commit. Also provides durable cross-machine handoff and resume modes. Use when the user explicitly invokes grillstorm, wants the complete scattered Grill workflow behind one entry point, wants to decide everything up front and approve one uninterrupted implementation run, or asks Grillstorm to hand off or resume work.
---

# Grillstorm

Turn a large goal into decisions first, an execution contract second, and verified code last.

**Invariant:** discover facts -> grill and freeze all known human decisions -> one launch
approval -> autonomously recommend and record unforeseen decisions -> implement, review,
repair, and prove without interrupting the run.

**No internal fallback:** never turn a failure into default, empty, stale, cached, mocked,
partial, or successful behavior; never bypass a contract/gate or silently downgrade an
approved implementation. Retry the same contract, repair, replan, or create a gap. Only
explicitly approved product degradation is valid behavior.

Resolve all linked files relative to this `SKILL.md`. This skill is self-contained and
must not require external `grill-me`, `grilling`, `domain-modeling`, `to-spec`,
`setup-matt-pocock-skills`, `to-tickets`, `implement`, `tdd`, `diagnosing-bugs`, or
`code-review` skills.

Read `references/upstream-flow.md` first. Its parity rules are binding: Grillstorm may
sequence, repeat per module, persist, resume, and autonomously repair the original workflow,
but must not replace an original stage with a different methodology.

## Entry modes

- **Run:** `$grillstorm <goal>` starts a new adaptively routed delivery run or resumes the
  matching unfinished run.
- **Audit completed delivery:** `$grillstorm audit [run path]` enters Phase 7 directly for
  an implementation-complete run, preserving its frozen delivery evidence. This is a mode
  of the existing command, not another command entry.
- **Handoff:** `$grillstorm handoff [next-session focus]` reads `references/handoff.md`,
  writes a durable repository checkpoint, optionally updates the configured tracker when
  authorized, reports its portability status, and stops. Use `$grillstorm handoff local`
  only for a temporary same-machine handoff. Do not run setup, planning, or implementation
  in either handoff mode.
- **Resume from handoff:** `$grillstorm resume <handoff path>` reads the handoff in its
  declared order, then follows its durable run pointers and resumes from `state.json`.
  When source and target hosts differ, verify `execution-checkpoint.json`, create a fresh
  target-host workflow state and model policy, and continue only from its confirmed
  integration commit. The handoff is a context boundary, not a new source of truth.

Use handoff when the user pauses, requests a fresh context, changes machine/agent/model, or
the current session cannot safely finish the next work unit. Starting a fresh session is
what releases conversation context; writing a handoff does not erase the current session.

## Artifacts

For the `program` route, create one resumable run at `docs/grillstorm/<goal-slug>/`:

```text
state.json
decisions.md
program-spec.md
modules/<module-id>-spec.md
tasks/catalog.md
tasks/<module-id>.md
tasks/workflow-tasks.json
tasks/interfaces.json
tasks/orchestration.json
tasks/workflow-simulation.json
launch-contract.md
autonomous-decisions.md
reviews/reuse-radar.md
reviews/standards.md
reviews/spec.md
reviews/spec-grill.md
reviews/spec-closure.md
reviews/task-grill.md
reviews/task-closure.md
reviews/workflow-grill.md
reviews/workflow-dry-run.md
reviews/runtime.md
reviews/logic-alignment.md
reviews/feature-state-completeness.md
reviews/outcome-probe.md
requirements-state-registry.json
probes/sampling-frame.md
probes/probe-plan.json
probes/probe-results.jsonl
probes/probe-state.json
probes/evidence/<probe-id>/*
probes/rounds/<round-id>.md
gaps/catalog.md
gaps/<gap-id>.md
gaps/gap-manifest.json
workflow-state.json
workflow-events.jsonl
workflow-report.json
execution-checkpoint.json
model-policy.md
execution-report.md
```

`catalog.md` is the sole execution index. Each module task file is independently
executable. Do not create one monolithic task document.

Compact routes create only the artifacts required by `references/routing.md`; do not emit
empty program-scale placeholders. All routes keep minimal route and resume state.

Update `state.json` after every accepted answer and phase transition. Record the phase,
current module, approved modules, invalidated modules, execution status, and monotonic
`spec_revision`, `task_revision`, `workflow_revision`, and `launch_revision`. On invocation,
resume an unfinished matching run instead of restarting unless the user requests a new run.
The delivery run and each post-delivery audit/remediation cycle have separate lifecycle
states. An audit may append its status and child pointers to a completed parent, but never
reopens or rewrites the parent's delivery history.

## Token discipline

- Keep this file as the orchestrator. Read only the reference for the active phase.
- During a module grill, load only `program-spec.md`, `decisions.md`, the current module,
  and contracts that touch it.
- During outcome critique, load only one probe evidence bundle, its approved intent, and
  related prior answers; do not replay the whole delivery.
- Persist the accepted answer immediately, then rely on the artifact instead of replaying
  conversation history.
- Never ask for facts available from the repository, tools, documentation, or existing
  artifacts.
- Ask one decision question per turn. Do not bundle questions.
- Stop grilling a branch once its closure checklist is satisfied.
- Reference existing artifacts instead of duplicating their prose.

## Phase -1: Set up the repository

Read `references/project-setup.md` and run its setup before creating a Grillstorm run.
Reuse valid existing `docs/agents/` configuration; do not ask the same setup questions on
every invocation.

Explore first, then resolve only missing configuration one section and one question at a
time: issue tracker, triage label vocabulary, domain-doc layout, and the repository
instruction file to update. Show the complete draft once, obtain confirmation, then write
the setup artifacts.

This phase reproduces `setup-matt-pocock-skills` locally. Never require users to install or
invoke it separately.

## Phase 0: Orient

Inspect repository instructions, structure, code, tests, docs, current terminology, and
recent relevant changes. Detect an existing run. Establish the goal and execution mode:
`full` by default, `plan-only` only when explicitly requested, or `resume`.

Initialize the artifact directory and state. Do not ask the user to repeat discoverable
repository facts. Capture the starting Git ref and pre-existing dirty paths so autonomous
work never overwrites, stages, or misattributes user changes.

Read `references/routing.md`, classify the work from repository evidence, record the route
and reasons in `state.json`, and follow only that route's stages. Announce the selected route
briefly; do not ask the user to choose an internal workflow. Promote automatically when new
evidence exceeds the current route. Never force a small change through program-scale
catalog ceremony.

Read `references/reverse-closure.md`. Before module decomposition, define observable global
completion, real side effects, failure/recovery behavior, and proof. Run the early reuse
radar against the repository. Persist `reviews/reuse-radar.md` for `program`, or a compact
state entry for smaller routes. Treat extraction candidates as non-binding until complete
consumer specs exist.

Read `references/model-policy.md`. Resolve the route-aware `THINK`, `BUILD`, and `VERIFY`
roles from current host capabilities, record their exact effective model literals and
evidence, and freeze them as part of the one launch contract. Do not ask a separate model
question unless the user explicitly overrides the recommendation.

## Phase 1: Grill the program

Run this program-scale form only for the `program` route. Compact routes still run the same
`grill-with-docs` discipline, but only across decisions relevant to their smaller scope.

Read `references/grilling.md`, `references/domain-modeling.md`, and
`references/spec-and-seams.md`. Load `references/supporting-disciplines.md` only when
research, a prototype, or codebase-design work is actually needed.

Grill the top-level goal one question at a time. Resolve problem, user-visible scope,
non-goals, module decomposition, ownership boundaries, dependency direction,
cross-module interfaces, highest useful test seams, and the outcome-first completion record.
Use the reuse radar when proposing boundaries. For every question, include a recommended
answer and its main tradeoff.

Write decisions as they are accepted. Maintain the repository glossary and sparse ADRs
using the bundled domain-modeling protocol.

Synthesize `program-spec.md` using the bundled template. Present a compact module,
interface, and test-seam summary. Continue grilling unresolved branches. Phase 1 ends only
when the user confirms shared understanding and approves the program spec.

## Phase 2: Grill each module

Run this phase only for the `program` route. Other routes have one natural work scope and
must not invent modules merely to satisfy this template.

Process modules in dependency order. For the current module:

1. Explore its present code and prior test patterns.
2. Load only relevant parent decisions and interface contracts.
3. Grill unresolved behavior, states, errors, data ownership, integration obligations,
   migration concerns, observability, and acceptance behavior one question at a time.
4. Write `modules/<module-id>-spec.md`.
5. Run the module closure checklist and fix local gaps.
6. Ask for confirmation that this module has reached shared understanding.

If an answer changes a frozen boundary, public interface, or user-visible scope, update
`program-spec.md` and invalidate every affected downstream module spec. Re-grill those
modules; never silently patch around contract drift.

After every module reaches shared understanding, persist the approved local program and
module specs. Do not publish tickets or begin execution planning yet.

## Phase 2.5: Close the spec graph and front-load abstractions

Run the full pass for `program`; run its compact single-scope form for `direct` and
`ticketed` before their final `to-spec` publication. Read
`references/spec-closure-and-abstraction.md` and, when module/seam design is implicated, the
codebase-design section of `references/supporting-disciplines.md`.

Freeze the locally approved program/module spec snapshot, then run
`prompts/spec-reverse-grill.md` in a fresh `THINK` context. Work backward from every global
outcome using problem, domain/design, cross-spec consistency, exception, reuse/abstraction,
and proof lenses.

Resolve `discover` and unambiguous `spec-repair` findings without asking the user. For every
true unresolved product/design decision, re-enter the bundled Grill loop: ask exactly one
question, provide one recommended answer and its main tradeoff, persist the answer
immediately, invalidate/update affected specs, then continue with the next dependency-ready
question. Write the issue inventory, evidence, answers, and repairs to
`reviews/spec-grill.md`.

When the reverse Grill has no unresolved issue, run the closure and abstraction critics
independently in separate fresh `THINK` contexts. Trace every requirement through ownership,
interfaces, failure behavior, test seams, runtime observation, and completion evidence, then
trace every proposed artifact back to an approved requirement.

Inspect the existing codebase for reusable modules before extracting a new one. When a new
deep module is justified, specify it completely, place it before its consumers, update all
affected contracts and seams, resolve only newly introduced user decisions, and rerun the
reverse Grill plus both critics. Do not defer an undecided shared-module extraction into
implementation tasks.

Write `reviews/spec-closure.md`. After any answer or repair, discard all prior global
verdicts and rerun the complete reverse Grill and both independent critics. This phase ends
only when the reverse Grill is closed, both critics have zero blocking findings, and the
full spec graph is stable.

Export `requirements-state-registry.json` from the closed requirement matrix. Give every
requirement a stable ID, source pointer, and explicit applicable states with risk. Freeze it
at the current `spec_revision`; later probe sampling must use this registry rather than
re-enumerating requirements from memory.

Then run the original `to-spec` synthesis discipline without another broad interview:
finalize the specs, publish or update the final spec in the configured issue tracker, and
apply its configured `ready-for-agent` label.

## Phase 3: Build and grill task documents

Run the full catalog plus per-module document form only for the `program` route. For
`ticketed`, use the compact tracker-ticket/catalog form in `routing.md`. Skip this phase for
`direct` and `diagnostic`.

After the spec closure and abstraction gate passes, read `references/task-documents.md`.

Create:

- `tasks/catalog.md`: goal, source artifacts, module DAG, interface registry, test-seam
  registry, execution frontier, per-module status, and global completion gates.
- `tasks/<module-id>.md`: the complete executable tasks for exactly one module.

Each task must declare its outcome, dependencies, touched paths, implementation steps,
test seam, acceptance command, expected evidence, and status. Prefer end-to-end vertical
slices. Keep interface-producing tasks ahead of consumers.

For each module task document, grill only unresolved task-level decisions: granularity,
blocking edges, implementation constraints, migration order, environment access,
destructive/external actions, runtime acceptance, Git policy, and completion gates. Update
the document after each answer, then run its local closure before moving to the next module.

After the catalog and all directory/module task documents are locally closed, freeze the
planning snapshot. Run `prompts/task-reverse-grill.md` in a fresh `THINK` context, working
backward from every global runtime outcome through integration ownership, directories,
consumers, interface producers, shared modules, migrations, configuration, deployment,
cleanup, and prerequisites.

Resolve `discover`, `task-repair`, and unambiguous `spec-repair` findings without asking the
user. For every true unresolved product/design decision, re-enter the bundled Grill loop:
ask exactly one question, provide one recommended answer and its main tradeoff, persist the
answer immediately, update/invalidate affected artifacts, then continue with the next
dependency-ready question. Write the issue inventory, answers, repairs, and checked exception
lenses to `reviews/task-grill.md`.

When the reverse Grill has no unresolved issue, run the independent
`prompts/task-closure-critic.md` in another fresh `THINK` context and write
`reviews/task-closure.md`.

If global task closure exposes a spec, boundary, ownership, interface, behavior, or abstraction
defect, increment `spec_revision`, mark affected task/workflow/launch artifacts stale, return
to Phase 2.5, and regenerate only the affected subgraph. Never repair an architectural gap
only in task prose.

For task-level defects, repair and locally re-close the affected catalog/module documents,
then rerun both the reverse Grill and the independent global closure critic from final
outcomes. Do not publish tickets or compile the workflow until the reverse Grill is closed
and the fresh critic verdict has no blocking finding, orphan task, orphan directory, or
catalog/document/DAG disagreement.

Then publish every approved vertical-slice ticket to the configured tracker in dependency
order, using native blocking links where available and the original minimal ticket format.
Store tracker identifiers in `catalog.md`. The richer per-module task files are Grillstorm's
long-run execution layer; they do not replace the original tracker tickets.

For `ticketed` and `program`, read `references/concurrency.md`. Only after task closure,
generate and validate the machine workflow inputs, then run the bundled deterministic
workflow simulator without agents or Git mutation. Store its raw output in
`tasks/workflow-simulation.json` and summarize initial readiness, dependency waves, resource
mutexes, merge-collision groups, unreachable work, and failure blast radius in
`reviews/workflow-dry-run.md`. Repair and repeat until the simulation closes.

After tickets are published and the DAG/simulation close deterministically, freeze that
projection and run `prompts/workflow-reverse-grill.md` in a fresh `THINK` context. Work
backward from global runtime proof through actual gates, machine tasks, compiled edges,
tracker blockers, resources, and the initial ready frontier. Check projection fidelity,
graph/scheduling safety, executable proof, operational closure, and cross-artifact
consistency.

Resolve discoveries and projection-only repairs internally. A task-level issue returns to
the task reverse Grill and closure gate; a spec-level issue returns to Phase 2.5. Ask exactly
one recommended Grill question only for a genuinely new decision. Write findings, answers,
repairs, and the final verdict to `reviews/workflow-grill.md`.

After any repair, regenerate affected tickets/workflow artifacts, rerun deterministic
validation/simulation, and rerun the complete workflow reverse Grill. Phase 3 ends only when
task closure, simulation, and workflow reverse Grill are closed at matching revisions.

Concurrency is an execution choice derived from the approved graph; do not ask a second
launch question for it.

## Phase 4: Freeze and launch

Perform an adversarial readiness pass over the entire artifact graph:

- every requirement has an implementation task and observable proof;
- every interface has one producer, known consumers, and a contract test;
- every user-visible state has runtime acceptance;
- migrations, compatibility, rollback, security, data handling, and deployment choices are
  settled where relevant;
- commands and required environment capabilities are available or have explicit reality gates;
- spec/task/workflow revisions match and no artifact is stale;
- workflow simulation has no unreachable task or hidden resource/merge constraint;
- workflow reverse Grill proves tickets and the executable DAG preserve approved tasks;
- no open decision can change scope, boundaries, interfaces, acceptance, or execution safety.

Establish a launch contract containing the frozen decisions, allowed autonomous choices,
authorized side effects, Git policy, reality gates, autonomous decision policy, and exact
completion definition. Include the frozen model-role mapping and capability evidence. Ask
one final question: approve this launch contract and start the uninterrupted run?

For `direct` and `diagnostic`, present the same contract as one compact launch summary and
store it in `state.json`; do not create program-scale documents. For `ticketed` and
`program`, write `launch-contract.md`.

After approval, do not ask implementation questions. For any unforeseen decision, choose
the recommended option using the autonomous decision policy, update affected artifacts,
record it in `autonomous-decisions.md`, and continue.

## Phase 5: Implement, review, and prove

Skip this phase in `plan-only` mode. After approval, read
`references/execution.md`, `references/implementation-and-diagnosis.md`, and
`references/review-and-validation.md`. For an eligible `ticketed` or `program` run, also
read `references/concurrency.md`. Execute without further routine confirmation.

Work the route's execution source: the diagnosed fix and regression seam for `diagnostic`,
the approved spec for `direct`, tracker tickets and compact catalog for `ticketed`, or the
module catalog for `program`. For every work unit, write the production code and its
behavioral tests. Run red-green cycles at approved seams, diagnose failures with a tight
feedback loop, and record commands and evidence immediately.

Run routine implementation workers as `BUILD`. Run supervisors, acceptance reruns, and the
final Standards and Spec reviews as fresh `VERIFY` contexts that receive repository state
and frozen acceptance inputs, never executor narrative. Use `THINK` only for synthesis,
closure, or replan work. Do not silently substitute models after launch.

At each applicable work-unit or module gate, run focused tests, typechecking/static checks,
interface contract tests, and relevant runtime acceptance. Then review the diff against
both repository standards and the approved spec. Fix every blocking finding and repeat the
failed gate.

After all work units, run full-suite checks plus applicable integration and real user-flow
validation. Review the complete diff against standards and spec in separate passes, repair
findings, and rerun affected checks until closure.

Never pause merely because an unforeseen product, architecture, boundary, interface, or
acceptance decision appears. Choose the recommended option, preferring compatibility,
reversibility, minimal scope, and existing project conventions. Update and revalidate every
affected downstream artifact, increment the appropriate revision, rerun the affected
closure/simulation gates, then continue. Never execute stale task or workflow revisions.

When an action requires unavailable credentials or explicit authority for destructive,
production, paid, or external effects, choose the safest non-destructive path: finish all
local implementation and proof possible, create an exact reality-gate runbook, and continue
independent work. Never invent authorization or claim that gate passed.

After all review and verification gates pass, follow the original `implement` closeout and
commit Grillstorm-owned work to the current branch. Phase 3 must front-load any user
exception to committing. Never push, deploy, or modify production/external systems unless
the launch contract explicitly authorizes it.

## Phase 6: Complete the delivery run

Write `execution-report.md` with completed modules, acceptance evidence, unresolved or
human-only gates, review findings and fixes, deviations, and exact resume pointers.
Include an `Autonomous decisions` section listing each unforeseen decision, recommendation,
alternatives considered, rationale, affected artifacts/code, and validation performed.

**Document production is never delivery completion.** Set `delivery_status: complete` and
the delivery run's overall `status: complete` only when required code exists, every task and
catalog gate has evidence, blocking review findings are fixed, the full required test suite
passes, runtime behavior is proven or explicitly reality-gated, and the execution report is
durable. Record the terminal commit and completion time. This is a real endpoint and is not
revoked by later critique.

If work remains for another session, or the user requests a clean context boundary, run the
bundled handoff mode after updating `state.json` and the execution report. After reporting
the completed delivery, start the independent post-delivery audit cycle below when requested
or when the default full workflow continues with the user present.

## Post-delivery audit cycle: Probe, Grill, and discover gaps

This cycle is linked to, but not a phase that blocks or reopens, the completed delivery run.
Invoke it with `$grillstorm audit [run path]`, or enter it immediately after reporting
delivery completion when the user is present and did not opt out. Read
`references/post-delivery-probing.md`.

In a fresh `THINK` context, use `prompts/probe-sampler.md` and the frozen
`requirements-state-registry.json` to construct the full sampling frame and a stratified,
risk-weighted round across two axes:

- **logic alignment:** whether domain logic, ownership, algorithms, policies, interfaces,
  state/lifecycle, and architecture match what the user intended;
- **feature/state completeness:** whether functionality and details work across all
  applicable success, empty, loading, degraded, invalid, denied, failure, retry,
  concurrency, migration, rollback, cleanup, and recovery states.

Persist the human view in `probes/sampling-frame.md` and the machine contract in
`probes/probe-plan.json`. Validate the registry and plan with
`scripts/validate_probe_artifacts.py` before execution.

Execute each selected probe in a fresh `VERIFY` context using
`prompts/probe-executor.md`. Logic-alignment probes inspect and hash only the declared code
and documentation evidence. Feature/state probes must start and exercise the real runnable
target through a browser, API, CLI, public library, data, device, or external-system surface.
Source inspection or tests alone cannot pass a feature probe; unavailable runtime becomes a
blocking gap in the runnable system or its required verification environment.

Append admitted evidence to `probes/probe-results.jsonl` and store captured artifacts under
`probes/evidence/<probe-id>/`. Validate results after every round with the run directory as
`--evidence-root`; the validator must read and rehash every cited file. Write cumulative human
views to `reviews/logic-alignment.md` and `reviews/feature-state-completeness.md`. Green
samples never imply exhaustive coverage.

For one probe at a time, use `prompts/outcome-critique-grill.md` and the bundled Grill
protocol to show a compact intended-versus-observed evidence bundle. Ask the user exactly
one fault-finding question with a recommended judgment and tradeoff. Persist the answer
before showing the next sample. Distinguish an approved-intent gap from a new preference;
do not silently expand scope.

For every confirmed gap seed, use `prompts/gap-expander.md` in a fresh `THINK` context to
search related invariants, transitions, interfaces, consumers, sibling surfaces, error/
recovery patterns, duplicated implementations, and test seams. Convert candidates into
new probes, verify them, and group only confirmed instances into gap families.

Run at least two rotating rounds. Continue until two consecutive rounds produce no new gap
family, no new blocking member of an existing family, and no unexplored registry cell.
Then ask one final Grill question confirming practical saturation. Write each round to
`probes/rounds/<round-id>.md`, persist counters/fingerprints in
`probes/probe-state.json`, and validate saturation mechanically before writing the cumulative
audit to `reviews/outcome-probe.md`.

Give the audit cycle its own `audit_status: in_progress|clean|gaps`, timestamps, and resume
pointer. Close it as `clean` only when every applicable registry cell has real accepted
evidence and no confirmed gap remains. Missing environment, failed startup, or unavailable
evidence is a blocking gap, never a successful or terminal exemption. Write
`gaps/catalog.md` and one `gaps/<gap-id>.md` per family, close the audit as `gaps`, then write
and validate `gaps/gap-manifest.json` before creating a linked remediation delivery run
using the gap catalog as discovery input. Update every manifest entry with the child run ID
and state path, then rerun the validator with `--require-child-links`; an unlinked gap is not
a completed audit handoff.

Route each remediation run by its real blast radius and run the normal spec/task/execution
closure cycle. It has its own endpoint and may later start another audit cycle. Append audit
and child pointers to the parent state/report as metadata only; never change its
`delivery_status: complete` or rewrite its historical specs/tasks.

## Bundled sources

The bundled workflow reproduces and adapts project setup, Grill, domain-modeling, spec,
ticketing, implementation, TDD, diagnosis, codebase design, research, prototyping,
merge-conflict resolution, and code-review methods under the MIT license. See
`references/third-party-notices.md`.
