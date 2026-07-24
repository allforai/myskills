---
name: grillstorm
description: Self-contained, adaptive Grill delivery for Claude and Codex. Routes small work through only needed stages and drives large goals through one-question grilling, modular specs, interface/test seams, global closure, task/DAG simulation, supervised worktree execution, runtime proof, durable handoff, and post-delivery gap audits. Use when the user invokes Grillstorm, wants the scattered Matt Pocock workflow behind one autonomous entry, wants decisions front-loaded before one uninterrupted implementation run, or asks to audit, hand off, or resume a run.
---

# Grillstorm

Turn goals into frozen decisions, executable contracts, verified code, and evidence.

## Invariants

1. Discover facts; Grill and freeze human decisions; approve one launch; implement and prove.
2. Ask one decision question at a time with a recommendation and its main tradeoff.
3. Persist each accepted answer immediately; artifacts, not conversation, are durable truth.
4. For unforeseen decisions after launch, adopt and record the recommended choice without
   interrupting. Revalidate everything it affects.
5. Never ask for facts available from the repository, tools, documentation, or run artifacts.
6. Never turn failure into default, empty, stale, cached, mocked, partial, or successful
   behavior. Retry the same contract, repair, replan, or create a gap. Only explicitly
   approved product degradation is valid.
7. Documents are not delivery. Code and real acceptance evidence are required.

Resolve links relative to this file. Read `references/upstream-flow.md` first; its parity
rules are binding. This skill embeds the original setup, Grill, domain, spec, ticket,
implementation, TDD, diagnosis, and review disciplines. Do not require their external skills
or replace their methods.

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

Read `references/project-setup.md`. Reuse valid `docs/agents/` configuration. Explore first;
ask only for missing tracker, label, domain-doc, or repository-instruction decisions, one at
a time. Confirm the complete draft once, then write it. This embeds
`setup-matt-pocock-skills`.

**Exit:** required repository configuration exists and is confirmed.

## Phase 0: Orient And Route

Inspect instructions, code, tests, docs, terminology, Git state, and existing runs. Capture
the starting ref and pre-existing dirty paths. Default to `full`; use `plan-only` only when
explicitly requested.

Read:

- `references/routing.md`: choose `diagnostic`, `direct`, `ticketed`, or `program` from
  evidence; announce, do not ask. Promote when scope grows.
- `references/reverse-closure.md`: define observable completion, side effects,
  failure/recovery, proof, and an early reuse radar.
- `references/model-policy.md`: resolve and freeze effective `THINK`, `BUILD`, and `VERIFY`
  literals. Ask only for an explicit override; never substitute models after launch.

**Exit:** route, completion target, reuse candidates, model policy, and clean ownership
baseline are durable.

## Phase 1: Grill The Goal

Compact routes Grill only their natural scope. For `program`, read `references/grilling.md`,
`references/domain-modeling.md`, and `references/spec-and-seams.md`; load
`references/supporting-disciplines.md` only when research, prototyping, or codebase design is
needed.

Resolve user outcome, scope/non-goals, domain language, modules, ownership, dependency
direction, interfaces, test seams, states, failure behavior, and completion proof. Write
decisions as accepted and synthesize `program-spec.md`.

**Exit:** the user confirms shared understanding and the program spec.

## Phase 2: Grill Modules

For `program`, process modules in dependency order. Explore the current code, load only
touching decisions/contracts, Grill unresolved behavior and integration obligations, write
`modules/<id>-spec.md`, run local closure, and confirm shared understanding.

A changed scope, boundary, or public interface invalidates the parent and every affected
downstream spec. Update and re-Grill them; never patch around drift.

**Exit:** every module spec is locally closed at the same spec revision.

## Phase 2.5: Close The Spec Graph

Read `references/spec-closure-and-abstraction.md`. Run `prompts/spec-reverse-grill.md` in a
fresh `THINK` context, then independent spec-closure and abstraction critics. Resolve facts
and unambiguous repairs internally. For each true new decision, re-enter the one-question
Grill, persist it, invalidate affected artifacts, and rerun all global verdicts.

Inspect existing reuse before extracting. Any justified shared module must be fully
specified, placed before consumers, and included in interfaces and test seams before task
planning.

Write `reviews/spec-grill.md` and `reviews/spec-closure.md`. Export
`requirements-state-registry.json` with stable requirement/source/state/risk cells at the
current spec revision. Then perform the bundled `to-spec` publication and configured
`ready-for-agent` label.

**Exit:** reverse Grill has no unresolved issue; both critics have no blocking finding; the
spec graph, abstractions, and registry are stable.

## Phase 3: Close Tasks And Workflow

Skip for `direct`/`diagnostic`; use the compact form from `references/routing.md` for
`ticketed`. For `program`, read `references/task-documents.md` and create:

- `tasks/catalog.md`, the sole execution index;
- `tasks/<module-id>.md`, independently executable vertical tasks for one module.

Each task declares requirements, outcome, dependencies, paths, interfaces, failure contract,
test seam, steps, runtime check, acceptance command/evidence, and status.

After local task closure:

1. Run `prompts/task-reverse-grill.md`, then an independent task-closure critic.
2. Route spec/boundary/abstraction defects back to Phase 2.5; repair task defects locally.
3. Publish minimal tracker tickets and preserve richer module task files locally.
4. For `ticketed`/`program`, read `references/concurrency.md`; validate tasks/interfaces,
   compile the DAG, and run deterministic simulation.
5. Run `prompts/workflow-reverse-grill.md` over tickets, DAG, resources, gates, and runtime
   proof. Route defects backward to their owning phase.
6. After any repair, regenerate affected projections and rerun the complete relevant gates.

Write task/workflow Grill, closure, and dry-run reviews.

**Exit:** task closure, tickets, machine inputs, simulation, and workflow reverse Grill are
closed at matching revisions with no unreachable work or missing proof.

## Phase 4: Freeze And Launch

Adversarially verify requirement-to-task-to-proof coverage; producer/consumer/interface
coverage; runtime states; migration/security/rollback/deployment choices; environment
capabilities; revision consistency; simulation; and zero open execution-changing decision.

Freeze decisions, model roles, side-effect authority, Git policy, autonomous decision policy,
and exact completion in a compact state contract or `launch-contract.md`. Ask one final
question to approve the uninterrupted run.

After approval, implementation does not ask routine questions. Record unforeseen choices in
`autonomous-decisions.md`, update revisions and dependencies, and rerun affected closure. For
each choice, consider viable options, adopt the recommended option that remains inside the launch
authority, record its assumptions/risk/affected artifacts before acting, and record its outcome
afterward. Never pause merely because the choice concerns product behavior, architecture,
boundaries, interfaces, or replanning.

**Exit:** one approved, internally consistent launch contract.

## Phase 5: Implement, Review, Prove

Skip in `plan-only`. Read `references/execution.md`,
`references/implementation-and-diagnosis.md`, and
`references/review-and-validation.md`; also read `references/concurrency.md` for eligible
ticketed/program runs.

Implement production code and behavioral tests at approved seams. `BUILD` writers operate
from frozen tasks; fresh `VERIFY` supervisors rerun acceptance from repository state, never
executor narrative. Use `THINK` only for synthesis, closure, or replan. Run focused,
contract, module, integration, full-suite, and real runtime checks as applicable. Run
independent Standards and Spec reviews; repair and repeat to closure.

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
decisions, remaining gates, and resume pointers.

Set `delivery_status: complete` and overall delivery `status: complete` only when required
code exists, tasks/catalog are evidenced, blocking findings are fixed, required suites pass,
runtime behavior is proven, and the report/terminal commit are durable. This is the delivery
endpoint; a later audit appends history but does not rewrite it.

If incomplete after all viable branches drain, update state/report with every deferred/skipped
chain and a precise resume pointer. Do not use handoff merely because one branch is blocked or an
unforeseen decision arose. Handoff occurs only on explicit user request or when a terminal
infrastructure failure makes all further safe progress impossible. After completion, enter Phase
7 when requested or when the default full workflow continues with the user present.

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
