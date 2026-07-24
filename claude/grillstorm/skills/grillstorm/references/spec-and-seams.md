# Program And Module Specs

Synthesize approved decisions; do not use spec writing as another broad interview. Grill
only unresolved decisions.

## Test-seam rule

Prefer an existing seam over a new one and the highest stable seam that proves external
behavior. Use as few seams as practical. A seam is useful only when the repository can
exercise it deterministically or when a clearly labeled human reality gate exists.

For each seam, record:

- ID and owner module
- observable behavior
- entry point or interface
- existing test prior art
- automated command, or exact human runbook
- failures it cannot detect

Confirm the proposed seam with the user because it determines what "done" means.

## `program-spec.md`

```markdown
# <Goal> Program Spec

## Problem Statement
## Solution
## User Stories
## In Scope
## Out of Scope
## Domain Language

## Modules
| ID | Module | Owns | Does not own | Depends on |

## Interface Registry
| ID | Kind/name | Producer | Consumers | Input | Output | Errors/versioning |

## Test-Seam Registry
| ID | Owner | Observable behavior | Entry point | Proof command/runbook |

## Dependency Graph
## Program Acceptance
## Implementation Decisions
## Open Decisions
```

Module IDs and interface IDs are stable after approval. Interface names use
`<kind>:<name>`, where kind is `api`, `event`, `data`, or `ui`.

## `modules/<module-id>-spec.md`

```markdown
# <Module> Spec

## Outcome
## Source Requirements
## Responsibilities
## Non-Responsibilities
## Domain Terms
## User-Visible Behavior
## States And Failure Behavior
## Data Ownership
## Interfaces Exposed
## Interfaces Consumed
## Test Seams
## Migration And Compatibility
## Observability
## Acceptance Criteria
## Out of Scope
## Decisions And Assumptions
## Open Decisions
```

## Module closure checklist

- Every responsibility maps to a program requirement.
- Every exposed interface has a named consumer or an explicit external caller.
- Every consumed interface has exactly one owner.
- Producer and consumer agree on semantics, shape, failure behavior, and compatibility.
- User-visible success, empty, loading, degraded, and error states are settled where relevant.
- Data ownership and write authority are unambiguous.
- Acceptance criteria are observable through named test seams.
- No open decision changes a boundary, interface, scope, or acceptance criterion.

If a module fails closure, continue grilling it. Do not hide unresolved decisions as
implementation assumptions.
