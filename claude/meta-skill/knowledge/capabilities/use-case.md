# Use-Case Capability (用例编写)

> Decide how the product will be tested while it is being built. This node writes the
> acceptance cases from the design — never from the code — beside the implementation nodes;
> product-verify walks them afterwards and shows each walk in frames.

## Goal

A test thought up at test time covers what the tester notices in the finished product. What the
code does not do is invisible there: nobody walks the empty list, the denied permission, the
second tap, because nothing on the screen suggests them. Cases written from the design, while the
code is still being written, say what should happen before anyone knows what does. The
implementation and the cases are then two readings of one design by two authors, and where they
disagree there is a finding — which is the point of having both.

So this node answers one question for product-verify, in advance and in full: **what will be
walked, starting from what state, and what must be seen at the end.** product-verify adds no case
and drops none.

## What it reads, and what it must not

- Reads the design: `business-flows.json`, `task-inventory.json`, `role-profiles.json`,
  `experience-map.json` (screens and their states), the app-design / ui-design / game-design specs
  the project has, and for a surface without an interface its command tree or API spec.
- **Never the code this run is writing**, an implementation node's report, or its notes. A case
  that was checked against the code first has already agreed with it. The node-spec says so, and
  the node is planned so it cannot wait for an implementation node (`validate_bootstrap.py`:
  `use_case_node_after_implementation`).
- When product-analysis already wrote business-level cases, they are the starting set: every
  existing `id` is kept with its meaning, and this node adds what the design now shows. A case the
  later design contradicts is not quietly rewritten — it is reported to the node that owns it.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `.allforai/use-case/use-case-tree.json` | The acceptance cases, in the `cases[]` schema of `product-analysis.md`, plus `uncovered[]` |
| `.allforai/use-case/use-case-report.md` | Human summary: what is covered, what is deliberately not, and why — never the cases restated |

`uncovered[]` holds what was looked at and left without a case, so an omission is a decision
somebody can read rather than a silence:

```json
{
  "cases": ["<product-analysis.md schema>"],
  "uncovered": [
    {"kind": "<enum: flow | screen | state | feedback>", "ref": "<the design id left without a case>", "reason": "<why no case is owed>"}
  ]
}
```

### Coverage (what must be true of the cases)

Counts are evidence of coverage, never a target. A case exists because the design names something
a user can do or meet; none is invented to fill a kind.

- **Every flow** has its happy case, and the exception and boundary cases its steps make possible.
  Every 高-risk task has a denied-permission case and a failed-after-partial-write case.
- **Every case can be walked.** `given` is a state the product can be put in, and says what puts it
  there when that is not obvious (seed data, a prior action, a role). `then` is something visible
  on a screen or readable in an output — never an internal state.
- **Interface cases** — owed whenever the design has screens, and the part most often left thin:
  - *Every screen* a role can reach appears in some case's `screen_refs`. A screen no case passes
    through is a case still owed, or a screen nobody needs — either is written down.
  - *Every state the design gives a screen* — empty, loading, error, success, no permission,
    offline, whatever this design names — has a case whose `given` puts the screen in that state.
    States are where an interface breaks unnoticed, because the happy walk never enters them.
  - *Every response the design promises to an action* — a message, a disabled control, a
    validation hint, a navigation, a changed number — is the `then` of some case. An action whose
    only checked result is "no error" is not covered.
  - *A `then` that happens in time* (an animation, a transition, something that appears and goes,
    a live update from elsewhere) says so in words — how long, in what order — so product-verify
    knows a still will not show it.
  - A role with no interface (`surface` says none) gets no interface case; its cases carry
    `screen_refs: []`.
- **Deferred work stays visible.** A case for a post-launch feature is kept with `deferred_by`,
  not deleted.

### Required Quality

- Every `flow_ref`, `task_refs[]`, `role_ref` and `screen_refs[]` value names an id that exists in
  the design artifacts; a case pointing at nothing is refused by its consumer.
- No two cases are the same walk under two ids, and no case bundles two outcomes that can fail
  separately.
- The report names every screen, state and promised response that ended in `uncovered[]`.

## Not this node's

Walking the cases, taking frames, recording, and any test code in the source tree belong to
product-verify and test-verify. This node writes under `.allforai/use-case/` only, so it shares no
write scope with the implementation nodes it runs beside.

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `.allforai/use-case/use-case-tree.json` | `cases[].id`, `given`, `when`, `then`, `screen_refs`, `deferred_by` | product-verify | required | product-verify walks every case under its id and renders `use-case-report.html`; a missing or malformed tree is this node's defect |

## Composition Hints

### Beside implementation (default)
`hard_blocked_by` the design nodes whose artifacts it reads and nothing else; it starts when the
implementation nodes start and neither waits for the other. Every product-verify node is
`hard_blocked_by` it. On a product with a designed interface it waits for the experience design,
since a UI case names real screens.

### Merge with Product Analysis
For a product with no interface and no separate design stage, product-analysis may write the
finished tree itself; the planning rule is satisfied by any producer that does not wait for
implementation.

### Split
A large product may split by role or client, each node writing its own fragment and one node
merging them into the tree; two nodes never write the tree itself.
