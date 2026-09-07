---
name: grillstorm
description: Official-skill orchestrator plus concurrent unattended execution for Claude and Codex. Routes design through installed Matt Pocock skills and executes approved work in isolated worktrees. Use only when the user explicitly invokes $grillstorm, including its audit, handoff, and resume modes. Same delivery shape as superstorm (front-loaded decisions, DAG, concurrent worktrees) but design runs through the official grilling → to-spec → to-tickets → tdd → code-review chain; use meta-skill bootstrap + run when the project needs product/experience/art design first.
---

# Grillstorm

Turn goals into frozen decisions, executable contracts, verified code, and evidence.

## Invariants

0. Official design skills may ask. After those stages complete, subject to safety, authority,
   and honest evidence, run unattended to a terminal state. Execution may not reopen grilling.
1. Discover facts; official Grill freezes human decisions; freeze one launch contract;
   implement and prove with Grillstorm execution.
2. Ask every currently independent decision in one numbered frontier round, each with a
   recommendation and its main tradeoff. Never ask a question whose prerequisite is unsettled.
3. Persist each accepted answer immediately; artifacts, not conversation, are durable truth.
4. After the last official design confirmation, adopt and record every unforeseen
   in-scope decision without interrupting. Revalidate everything it affects.
5. Never ask for facts available from the repository, tools, documentation, or run artifacts.
6. Never turn failure into default, empty, stale, cached, mocked, partial, or successful
   behavior. Retry the same contract, repair, replan, or create a gap. Only explicitly
   approved product degradation is valid.
7. Documents are not delivery. Code and real acceptance evidence are required.
8. Reconstruct why material code and requests exist. Preserve confirmed purpose with the
   fewest necessary concepts, not merely the fewest lines.

Resolve links relative to this file. Read `references/upstream-flow.md` and
`references/official-skills.md` first. Load official skills by name for setup, grilling,
domain modeling, spec publication, ticketing, TDD, code-review, and diagnosis. Never invoke
official `implement`. Reverse-grill, routing, DAG, concurrency, resume, and handoff stay
Grillstorm-owned.

## Modes

- `$grillstorm <goal>`: start or resume an adaptively routed delivery.
- `$grillstorm audit [run path]`: audit a completed delivery through Phase 7.
- `$grillstorm handoff [focus]`: follow `references/handoff.md`, write a portable checkpoint,
  optionally update the authorized tracker, report portability, and stop.
- `$grillstorm handoff local`: temporary same-machine handoff.
- `$grillstorm resume <handoff>`: read the handoff in order, follow its state pointers, verify
  any cross-host `execution-checkpoint.json`, and resume from confirmed Git state.

Handoff is a context boundary, not a new source of truth. Use it for pauses, fresh sessions,
host/model changes, or when the next work unit cannot finish safely.

## State And Context

Program runs live under `docs/grillstorm/<goal-slug>/`. `state.json` records route, phase,
resume pointer, statuses, and monotonic `spec_revision`, `task_revision`,
`workflow_revision`, and `launch_revision`. Update it after every accepted answer and phase
transition. Resume a matching unfinished run unless the user requests a new one.

Each phase owns its artifacts:

| Phase | Durable outputs |
|---|---|
| Orient | `state.json`, `decisions.md`, `reviews/reuse-radar.md`, model policy |
| Specs | `program-spec.md`, `modules/*-spec.md`, spec reviews, requirement-state registry |
| Tasks | catalog, one task file per module, tickets, interfaces, DAG, simulation, task/workflow reviews |
| Launch | compact state contract or `launch-contract.md` |
| Execute | workflow state/events/report, autonomous decisions, code/test/runtime evidence |
| Complete | `execution-report.md`, terminal commit and delivery status |
| Audit | probe plans/results/evidence, audit reviews, gap manifest, child-run pointers |

Compact routes create only required outputs from `references/routing.md`. Never emit empty
program placeholders or one monolithic task document.

Load only the active phase's reference, current scope, touching contracts, and required
evidence. During a module Grill, load only parent decisions, that module, and touching
interfaces. During critique, load one probe bundle and its approved intent. Point to existing
artifacts instead of copying them.

## Phase -1: Setup

Read `references/official-skills.md` and `references/project-setup.md`. If official skills
are missing, ask to install them and run `scripts/install_official_skills.py` on yes. Load
official `setup-matt-pocock-skills` when `docs/agents/` is missing or invalid. Reuse a valid
existing setup. Ask only the questions that official setup asks.

**Exit:** required official skills are installed and required repository configuration exists
and is durable.

## Phase 0: Orient And Route

Inspect instructions, code, tests, docs, terminology, Git state, and existing runs. Capture
the starting ref and pre-existing dirty paths. Default to `full`; use `plan-only` only when
explicitly requested.

Read:

- `references/orientation-and-intent.md`: build `reviews/orientation.md`, trace real call
  paths/effective configuration/test proof and material intent, then dispatch
  `prompts/orientation-critic.md` in a fresh `THINK` context. Repair and independently confirm
  within its `1 / 2 / 3` budget. Do not choose a route while orientation is open.
- `references/reverse-closure.md`: define observable completion, side effects,
  failure/recovery, proof, and an early reuse radar.
- `references/model-policy.md`: freeze the model policy — all roles inherit the host model
  unless the user, given the stated recommendation, chooses a next-tier-down `BUILD` from the
  host's model list. No model name lives in the skill; never substitute after launch except back
  to the host model.
- `references/routing.md`: only after orientation closes, choose `diagnostic`, `direct`,
  `ticketed`, or `program` from the verified baseline; announce, do not ask. Promote when scope
  grows.

**Exit:** independently closed orientation and intent evidence, route, completion target, reuse
candidates, model policy, and clean ownership baseline are durable.

## Phase 1: Grill The Goal

Compact routes Grill only their natural scope. For `program`, follow `references/grilling.md`
and load official `grill-with-docs` or official `grilling` plus `domain-modeling`. Load
`references/supporting-disciplines.md` only when official `research`, `prototype`, or
`codebase-design` is needed.

Resolve user outcome, scope/non-goals, domain language, modules, ownership, dependency
direction, interfaces, test seams, states, failure behavior, and completion proof. Persist
accepted decisions and synthesize `program-spec.md`. Official grilling may confirm shared
understanding. For every material request, separate the proposed mechanism from its pain,
underlying purpose, protected constraint, and observable acceptance. Prefer the smallest
purpose-complete option and persist its purpose chain.

**Exit:** every material human decision required by the official grill is answered and
persisted; the program spec is internally closed.

## Phase 2: Grill Modules

For `program`, process modules in dependency order. Explore the current code, load only
touching decisions/contracts, run official grilling for unresolved behavior and integration
obligations, write `modules/<id>-spec.md`, and allow the official skill's own exit
confirmation.

A changed scope, boundary, or public interface invalidates the parent and every affected
downstream spec. Update and re-Grill them; never patch around drift.

**Exit:** every module spec is locally closed at the same spec revision. When the last official
design confirmation is done, ordinary interaction ended there; all later in-scope execution
decisions are autonomous and disclosed at completion.

## Phase 2.5: Close The Spec Graph

Read `references/spec-closure-and-abstraction.md`, `references/failure-proportionality.md`, and
`references/review-budgets.md`. Run
`prompts/spec-reverse-grill.md` in a
fresh `THINK` context, then independent spec-closure and abstraction critics. Resolve facts
and unambiguous repairs internally. A reverse-grill finding that is a true new product
decision goes back to official grilling. After official design is closed, adopt recommended
in-scope repairs inside the frozen authority envelope, persist them in
`autonomous-decisions.md`, invalidate affected artifacts, and rerun all global verdicts
without asking the user.

Require every material requirement and abstraction to cite an authoritative purpose chain from
`references/orientation-and-intent.md`. Reject literal compliance that misses the purpose and
reject complexity with no current consumer or protected invariant.

Inspect existing reuse before extracting. Any justified shared module must be fully
specified, placed before consumers, and included in interfaces and test seams before task
planning.

Write `reviews/spec-grill.md` and `reviews/spec-closure.md`. Export
`requirements-state-registry.json` with stable requirement/source/state/risk cells at the
current spec revision. Then load official `to-spec` for publication and the configured
`ready-for-agent` label. Official `to-spec` may confirm seams.

**Exit:** reverse Grill has no unresolved issue; both critics have no blocking finding; the
spec graph, abstractions, and registry are stable; official publication is done.

## Phase 3: Close Tasks And Workflow

Skip for `direct`/`diagnostic`; read `references/review-budgets.md` and use the compact form from `references/routing.md` for
`ticketed`. For `program`, read `references/task-documents.md` and create:

- `tasks/catalog.md`, the sole execution index;
- `tasks/<module-id>.md`, independently executable vertical tasks for one module.

Each task declares requirements, outcome, dependencies, paths, interfaces, failure contract,
test seam, steps, runtime check, acceptance command/evidence, and status.

After local task closure:

1. Run `prompts/task-reverse-grill.md`, then an independent task-closure critic.
2. Route spec/boundary/abstraction defects back to Phase 2.5; repair task defects locally.
3. Load official `to-tickets` to publish tracker tickets. Official `to-tickets` may quiz
   granularity. Preserve richer module task files locally.
4. For `ticketed`/`program`, read `references/concurrency.md`; validate tasks/interfaces,
   compile the DAG, and run deterministic simulation.
5. Run `prompts/workflow-reverse-grill.md` over tickets, DAG, resources, gates, and runtime
   proof. Route defects backward to their owning phase.
6. After any repair, regenerate affected projections and rerun the complete relevant gates.

Write task/workflow Grill, closure, and dry-run reviews. Bound exceptional-behavior expansion with
`references/failure-proportionality.md` and validate `reviews/failure-classification.json` before
closure.

Every material task traces requirement -> purpose -> observable outcome. Task and workflow reviews
apply purpose-complete minimalism symmetrically to additions and deletions.

**Exit:** task closure, official tickets, machine inputs, simulation, and workflow reverse Grill are
closed at matching revisions with no unreachable work or missing proof.

## Phase 4: Freeze And Launch

Adversarially verify requirement-to-task-to-proof coverage; producer/consumer/interface
coverage; runtime states; migration/security/rollback/deployment choices; environment
capabilities; revision consistency; simulation; and zero open execution-changing decision.

Freeze decisions, model roles, side-effect authority, Git policy, autonomous decision policy,
and exact completion in a compact state contract or `launch-contract.md`, then enter Phase 5
immediately. Do not ask for a redundant start approval, offer an "open now" choice, or pause at
this stage boundary: the decisions already approved during official design authorize the run.

Implementation does not ask routine questions. Record unforeseen choices in
`autonomous-decisions.md`, update revisions and dependencies, and rerun affected closure. For
each choice, consider viable options, adopt the recommended option that remains inside the launch
authority, record its assumptions/risk/affected artifacts before acting, and record its outcome
afterward. Never pause merely because the choice concerns product behavior, architecture,
boundaries, interfaces, or replanning.

Do not load official `grilling`, `grill-me`, `grill-with-docs`, `to-spec`, `to-tickets`, or
`implement` after launch. Official `tdd`, `code-review`, and `diagnosing-bugs` remain available
as execution methods.

**Exit:** one internally consistent launch contract, persisted and launched without another
question.

## Phase 5: Implement, Review, Prove

Skip in `plan-only`. Read `references/execution.md`,
`references/implementation-and-diagnosis.md`, and
`references/review-and-validation.md`; also read `references/concurrency.md` for eligible
ticketed/program runs.

Implement production code and behavioral tests at approved seams using official `tdd`.
`BUILD` writers operate
from frozen tasks; fresh `VERIFY` supervisors rerun acceptance from repository state, never
executor narrative. Use `THINK` only for synthesis, closure, or replan. Run focused,
contract, module, integration, full-suite, and real runtime checks as applicable. After each
verified work unit and at global close, load official `code-review` for independent Standards
and Spec reviews; repair and repeat to closure. On a hard bug, load official
`diagnosing-bugs`.

Unavailable authority for destructive, paid, production, or external action is not
permission. Gather only non-mutating evidence for that action, record the affected branch as
deferred, transitively skip only its dependents, and continue every independent authorized branch.
Where useful, complete the local reversible implementation and write an exact reality-gate
runbook without performing the unauthorized action. Preserve the failure and exact evidence;
never claim a pass. Commit only Grillstorm-owned work under the approved Git policy. Never push
or deploy without authority.

**Exit:** all applicable work-unit and global gates pass on current revisions.

## Phase 6: Complete Delivery

Write `execution-report.md`: completed scope, proof, reviews/repairs, deviations, autonomous
decisions, corrected misunderstandings, material intent classifications and simplifications,
remaining gates, and resume pointers.

Set `delivery_status: complete` and overall delivery `status: complete` only when required
code exists, tasks/catalog are evidenced, blocking findings are fixed, required suites pass,
runtime behavior is proven, and the report/terminal commit are durable. This is the delivery
endpoint; a later audit appends history but does not rewrite it.

If incomplete after all viable branches drain, update state/report with every deferred/skipped
chain and a precise resume pointer. Do not use handoff merely because one branch is blocked or an
unforeseen decision arose. Handoff occurs only on explicit user request or when a terminal
infrastructure failure makes all further safe progress impossible. Phase 6 is the default
unattended endpoint. Enter Phase 7 only when the user explicitly requests `$grillstorm audit`;
never continue into an interactive audit implicitly.

## Phase 7: Audit Outcomes

Read `references/post-delivery-probing.md` and only its named prompts. Use the frozen
requirement-state registry as the census. Logic probes may inspect code/documents; feature
probes must start and exercise the real browser, API, CLI, public library, data, device, or
external development surface. Static evidence cannot pass functionality.

Validate plans, admitted files and hashes, results, saturation, and gap manifests with
`scripts/validate_probe_artifacts.py`. Grill one evidence bundle at a time. Expand confirmed
seeds to related candidates and verify them before grouping gap families.

The audit closes only as `clean` or `gaps`. Missing runtime/environment/evidence is a gap,
not a terminal exemption. `clean` requires accepted evidence for every applicable registry
cell. `gaps` requires a validated manifest and a linked remediation delivery run for every
gap; validate child links with `--require-child-links`. Each remediation run follows the
normal routed cycle and has its own endpoint.

## License

See `references/third-party-notices.md` for bundled upstream attribution.
