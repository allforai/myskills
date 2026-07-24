# Adaptive Routing

Choose by work shape, not by lines changed or an arbitrary task count. Routing is an
orchestration choice, so select and record the recommendation without asking the user.
Every route preserves the original atomic skill semantics.

## Routes

### `diagnostic`

Use when the goal is a reported bug, regression, failure, or performance problem whose
expected behavior is already mostly known.

```text
setup if missing
-> compact grill-with-docs for symptom, expected behavior, and allowed scope
-> diagnosing-bugs
-> regression TDD at the discovered correct seam
-> focused/type/full checks
-> independent Standards || Spec review
-> repair
-> commit
```

Use the existing issue as the spec source when it is sufficient. Run `to-spec` only when
grilling reveals missing product behavior that needs a durable spec. Do not create a catalog.

### `direct`

Use when all are true:

- one coherent user-visible behavior;
- one owning module;
- an existing or obvious test seam;
- no cross-module public contract, schema migration, or deployment choreography;
- implementation fits a few vertical red-green slices in one focused context.

```text
setup if missing
-> compact grill-with-docs
-> compact spec closure + abstraction review
-> to-spec + publish ready-for-agent
-> one launch approval
-> implement directly from spec with TDD
-> focused/type/full checks
-> independent Standards || Spec review
-> repair
-> commit
```

Do not create tracker tickets, a catalog, or per-module task documents.

### `ticketed`

Use when the goal remains within one delivery context but needs several independently
verifiable vertical slices, prefactoring, or explicit blocking order.

```text
setup if missing
-> grill-with-docs
-> spec closure + abstraction review
-> to-spec + publish ready-for-agent
-> to-tickets + publish blocking edges
-> compact catalog for resume
-> one launch approval
-> concurrently implement the ready frontier with isolated worktrees and TDD
-> focused/type/full checks
-> independent Standards || Spec review
-> repair
-> commit
```

Use tracker tickets as the work units. Create a compact catalog only when execution can span
contexts; do not manufacture module specs for a naturally single-module change.

### `program`

Use when any is true:

- multiple modules have distinct ownership or can be grilled independently;
- public/cross-module interfaces must be designed or changed;
- data migration, compatibility, rollout, or multiple environments require coordination;
- the decision tree or implementation cannot fit safely in one context;
- several module-level task sets have meaningful dependency edges.

Run the complete Grillstorm phases: top-level grill, per-module grills, program/module
specs, closed-loop and abstraction review, final spec publication, tracker tickets, catalog,
per-module execution documents, launch contract, concurrent ready-set implementation in
isolated worktrees, review, repair, runtime validation, and commit.

## Promotion

Promote automatically:

- `diagnostic -> direct` when the fix requires newly specified behavior.
- `direct -> ticketed` when multiple independently useful slices or blocking edges emerge.
- `ticketed -> program` when module ownership, cross-module contracts, or multi-context
  execution emerges.

Never silently compress work to stay in a smaller route. Record promotion evidence in
`state.json` and continue from existing approved artifacts without restarting.

Do not demote after implementation starts. Before launch, demotion is allowed only when
exploration proves the apparent complexity does not exist; record why.

## Shared guarantees

All routes:

- discover facts instead of asking;
- grill one decision at a time and maintain domain docs;
- agree test seams before TDD;
- publish specs/tickets when that route includes those stages;
- run typechecking, focused tests, and the full required suite;
- use independent two-axis review;
- record unforeseen recommended decisions;
- produce evidence and an execution report;
- commit owned changes after review unless the front-loaded Git policy says otherwise.
- use worktree-isolated ready-set concurrency only when the route is eligible and the host
  can provide genuinely independent workers.
