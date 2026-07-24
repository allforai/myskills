# Catalog And Module Task Documents

Generate task documents only from approved specs. Do not invent new scope while planning.
Read `docs/agents/issue-tracker.md` and `docs/agents/triage-labels.md`; do not assume a
tracker or label vocabulary.

## `tasks/catalog.md`

This is the sole orchestration and resume index:

```markdown
# <Goal> Task Catalog

## Mode And Status
## Source Artifacts
## Frozen Decisions

## Module DAG
| Module | Task document | Depends on | State | Module gate |

## Interface Delivery
| Interface | Producer task | Consumer tasks | Contract test |

## Directory And Ownership Coverage
| Directory/surface | Owning module | Tasks | Integration owner | Acceptance seam |

## Test-Seam Delivery
| Seam | Owning tasks | Proof command/runbook | State |

## Ready Frontier
## Global Gates
## Runtime Acceptance
## Review Gates
## Execution Log
## Deviations And Waivers
## Autonomous Decisions
```

Module states are `pending`, `ready`, `in_progress`, `blocked`, `verified`, or `waived`.
`Ready Frontier` lists modules whose dependencies are verified.

## `tasks/<module-id>.md`

```markdown
# <Module> Tasks

## Outcome
## Source Spec
## Boundaries
## Interfaces
## Module Acceptance

## T-<module>-01: <Vertical outcome>

- Status: pending
- Depends on: none
- Requirements: <IDs>
- Interfaces: implements <IDs>; requires <IDs>
- Exclusive resources: <resource IDs or none>
- Test seam: <ID>
- Touched paths: <expected paths>
- Acceptance command: `<non-vacuous command>`
- Expected evidence: <test count/output/artifact>
- Runtime check: <command/flow or not-applicable reason>
- Failure contract: <typed visible failure, or explicitly approved and tested degradation>
- Review gate: standards + spec

### Steps
1. Add the failing behavioral test.
2. Run it and confirm the expected failure.
3. Implement the minimum behavior.
4. Run the focused check.
5. Stop the red-green cycle; defer refactoring to review and repair.

### Evidence
<filled during execution>
```

## Planning rules

- Prefer narrow, complete vertical slices over layer-by-layer work.
- A task must be independently verifiable and fit in one focused coding session.
- Put prefactoring first only when it makes a later behavioral change materially safer.
- Any module extracted during spec closure is an interface-producing predecessor; place its
  delivery and contract tests before every consumer migration.
- Every interface has one producing task; consumers depend on that production.
- Each acceptance command must select at least one real assertion and exit nonzero on failure.
- Every behavioral task includes production-code work; documentation alone cannot complete it.
- Every task names its failure contract. No task may authorize an implicit default, empty,
  stale, mock, no-op, partial-success, or silent alternate path.
- Use a human runbook only for proof that genuinely requires hardware, external systems, or
  visual judgment unavailable in the environment.
- Expected paths guide execution but do not authorize silent boundary changes.
- Every task declares exact `touched_paths`, `implements`, `requires`, and exclusive
  `resources` so the workflow can derive safe ordering and isolation.

## Machine workflow after closure

For an eligible `ticketed` or `program` run, emit `tasks/workflow-tasks.json` from the
approved task documents. Do not ask planning agents to reinterpret prose after approval.
Use `references/concurrency.md` as the schema and execution protocol.

Do not compile this workflow until every module task document and the global reverse task
review below have passed.

Run `validate_plan_tasks.py`, freeze each operation-level artifact contract with
`build_artifact_contracts.py`, then build `tasks/orchestration.json` with
`build_task_dag.py`. Run `simulate_workflow.py` and store its raw result in
`tasks/workflow-simulation.json`. Store derived edges, warnings, initial ready work,
resource mutexes, path merge groups, unreachable work, and failure blast radii in
`catalog.md` and `reviews/workflow-dry-run.md`.

After publishing tickets and compiling/simulating the DAG, run
`prompts/workflow-reverse-grill.md`. This is a projection audit, not another task-design
session: it checks that concise tickets and machine artifacts did not lose or distort
approved outcomes, blockers, interfaces, acceptance, resources, reality gates, or global
proof.

Write `reviews/workflow-grill.md`. Resolve `discover` and `projection-repair` issues
internally. Route `task-repair` through the task reverse Grill and closure critic; route
`spec-repair` through spec closure. Ask one recommended question at a time only for a
genuinely new decision exposed by the executable graph.

Any repair invalidates the previous workflow verdict. Regenerate the affected projection,
rerun validation and simulation, then rerun the workflow reverse Grill from global runtime
outcomes to the initial ready frontier.

The Markdown catalog remains the human-readable execution index.
`tasks/orchestration.json` is the machine scheduling source. If they disagree, stop before
dispatch and regenerate the machine files from the approved task documents.

## Local closure

Close each module task document before generating the next:

- every module acceptance criterion maps to a vertical task and proof;
- every local prerequisite and produced/consumed interface is represented;
- extracted shared modules precede consumer migration;
- every task declares paths, resources, acceptance, and runtime evidence;
- no task hides a spec decision.

## Global reverse closure

After the catalog and every directory/module task document are locally closed, freeze that
planning snapshot and run two distinct passes:

1. **Reverse Grill:** use `prompts/task-reverse-grill.md` to trace each global runtime
   outcome backward through integration tasks, directory ownership, consumers, interface
   producers, shared modules, migrations, configuration, deployment, cleanup, and
   prefactoring. Apply problem, design, consistency, exception, and execution-reality
   lenses.
2. **Independent closure:** after every discovered fact, repair, and Grill decision has
   been incorporated, use `prompts/task-closure-critic.md` from a fresh context to challenge
   the resulting complete graph.

Write `reviews/task-grill.md` with the issue inventory, evidence, questions, recommended
answers, accepted answers, and repairs. Ask the user only issues classified as true
decisions, exactly one at a time, using the original Grill recommendation/tradeoff format.
Discoverable facts and unambiguous repairs are resolved internally.

Write `reviews/task-closure.md` with the checked reverse chains, directory/module coverage
matrix, orphan report, critic findings, repairs, and final verdict. A
`repair_level: task` finding repairs and locally re-closes the catalog and affected task
documents. A `repair_level: spec` finding invalidates affected tasks and returns to the spec
closure and abstraction phase.

After any answer or repair, discard both prior global verdicts and rerun the reverse Grill
and complete independent review from final outcomes. Do not validate only the repaired
finding. Ticket publication and machine workflow compilation remain blocked until both
passes are closed with no unresolved decision, orphan task/directory, contradiction, or
blocking finding.

## Closure checklist

Before approval, verify:

1. Every program requirement appears in at least one module task.
2. Every module acceptance criterion has a task and proof.
3. Every interface producer precedes all consumers.
4. Every test seam is delivered and exercised.
5. The module DAG is acyclic.
6. No task depends on an unapproved decision.
7. No task claims completion through a vacuous command.
8. Every user-visible requirement has a runtime validation step.
9. Every module has standards-review and spec-review repair gates.
10. The global gate includes the full required suite and cross-module integration.
11. Concurrent tasks have declared paths/resources and no missing interface producer.
12. The machine DAG and artifact contracts validate without warnings being hidden.
13. Every extracted/reused abstraction follows the decision in `reviews/spec-closure.md`.
14. Every touched directory/surface has one owning module and an integration/acceptance path.
15. No task, generated artifact, migration, configuration, deployment, or cleanup step is
    disconnected from an approved outcome.
16. Published tickets and the compiled/simulated DAG are semantically equivalent to the
    approved catalog/module task documents.

Fix planning defects directly. Return to grilling for any defect that requires a new user
decision.

After the user approves the breakdown, publish one concise tracker ticket per vertical slice
in dependency order. Use native blocking/sub-issue relationships where available, otherwise
write `Blocked by` references. Apply the configured `ready-for-agent` label and store IDs/URLs
in `catalog.md`.

Published tracker tickets contain outcome, blockers, acceptance criteria, and parent only;
omit touched paths and code. The richer module documents are Grillstorm's long-task
execution layer.
