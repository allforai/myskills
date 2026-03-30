# Product Analysis Verify Capability

> Capability reference for the verification layer of product analysis:
> use-case tree, feature gap analysis, design audit.
> This is the third of 3 product-analysis nodes.

## Purpose

Verify that the product definition is complete and consistent before implementation begins.
This is the last checkpoint before code generation — gaps found here are cheap to fix,
gaps found during implementation are expensive.

## Data Dependencies (Pull)

This node reads from BOTH upstream nodes:

**From product-analysis-core** (`.allforai/product-map/`):
- `role-profiles.json` — roles for use-case tree top level
- `task-inventory.json` — tasks for CRUD coverage + use-case generation
- `business-flows.json` — flows for journey walkthrough

**From product-analysis-ux** (`.allforai/experience-map/`):
- `experience-map.json` — screens for screen completeness check
- `interaction-gate.json` — gate must have passed (entry_requires)
- `journey-emotion-map.json` — emotional low points inform priority of gaps

**If interaction-gate.json is missing or gate status ≠ pass, this node cannot start.**
The orchestrator's pre_node hook (`check_requires entry`) blocks execution.

## Sub-Phases

### Use-Case Tree

- 4-layer tree: role → functional area → task → use case
- Per task: 1 happy path + N exception flows + M boundary cases
- Format: Given / When / Then
- Cross-reference: every use-case traces back to a task in task-inventory
- Cross-reference: every screen in experience-map has at least one use-case covering it

Output: `.allforai/use-case/use-case-tree.json`

### Feature Gap Analysis

**Task completeness:**
- CRUD coverage: every entity has create/read/update/delete (or documented reason for omission)
- Exception criteria: every task has on_failure defined
- Acceptance criteria: every task has measurable success condition

**Screen completeness:**
- Primary operations exist for every screen
- SILENT_FAILURE detection: operations that fail without user feedback
- UNHANDLED_EXCEPTION detection: error paths not defined in experience-map

**Journey walkthrough:**
- Per-role end-to-end path: can each role complete their primary flow?
- Both decision branches: every decision point has both yes/no paths defined
- 4-node scoring: start → decision → action → result per journey segment

**Gap classification:**
- core / important / minor severity
- low / medium / high effort to fix
- Gap tasks ranked by frequency × severity

Output: `.allforai/feature-gap/task-gaps.json`, `screen-gaps.json`, `journey-gaps.json`, `gap-tasks.json`, `gap-report.md`

### Design Audit (cross-layer consistency)

Three sweep passes across ALL product artifacts:

**Reverse tracing:** Every downstream artifact has an upstream source.
- Every screen in experience-map → traceable to a task in task-inventory
- Every task in task-inventory → traceable to a role in role-profiles
- Every use-case → traceable to a task + screen

**Coverage flood:** Every upstream node is fully consumed downstream.
- Every role has at least one flow
- Every task appears in at least one screen
- Every flow is walkable (no dangling steps)

**Horizontal consistency:** Adjacent layers have no contradictions.
- task-inventory permissions ↔ role-profiles permissions
- experience-map states ↔ business-flows branches
- use-case preconditions ↔ task validation_rules

Output: `.allforai/design-audit/audit-report.json`, `audit-report.md`

## Output Files (exit_requires)

Written to 3 directories:
- `.allforai/use-case/use-case-tree.json`
- `.allforai/feature-gap/gap-tasks.json`, `gap-report.md`
- `.allforai/design-audit/audit-report.json`

## Data Contract — What Downstream Nodes Pull

| Consumer | Pulls | Why |
|----------|-------|-----|
| implement / translate | use-case-tree (testing reference), gap-tasks (known gaps to address) | Implementation should fix known gaps, tests should cover use-cases |
| ui-design | audit-report (confirms consistency before visual design) | Design spec built on verified foundation |
| product-verify | use-case-tree (verification script source) | Playwright tests derived from use-cases |
| test-verify | use-case-tree (test vector source) | Unit/integration tests derived from use-cases |
| demo-forge | gap-report (known limitations) | Demo avoids showcasing gaps |

## Backtrack Triggers

**This node may backtrack to product-analysis-ux when:**
- Use-case references a screen not in experience-map → missing screen
- Screen completeness check finds states not defined → incomplete experience-map
- Horizontal consistency finds interaction-gate violations missed → gate re-evaluation

**This node may backtrack to product-analysis-core when:**
- CRUD coverage finds entities without tasks → missing tasks in task-inventory
- Reverse tracing finds tasks not assigned to any role → missing role assignment
- Coverage flood finds roles with zero flows → incomplete business-flows

**No other node backtracks to this node** — this is the terminal verification step
for product analysis. If design-audit passes, the artifacts are ready for implementation.

## Rules (Bootstrap Must Preserve)

1. **Interaction gate prerequisite**: Cannot start if gate hasn't passed.
2. **Cross-reference mandatory**: Every use-case traces to task + screen.
3. **Both decision branches**: Every decision point has yes/no paths.
4. **Gap tasks are actionable**: Each gap has severity, effort, and a concrete fix description.
5. **Audit covers all 3 sweeps**: Reverse tracing + coverage flood + horizontal consistency.
6. **Consumer maturity bar applies**: Consumer/mixed gaps weighted higher than admin gaps.
7. **No silent gaps**: Every omission either has a gap-task or a documented reason.

## Non-Web-App Archetypes

| Archetype | Use-case tree | Feature gap | Design audit |
|-----------|--------------|-------------|-------------|
| CLI | Command scenarios | Command coverage (flags, error handling) | Command↔flow consistency |
| Data pipeline | Transform test cases | Stage coverage (input/output validation) | DAG↔transform consistency |
| Game server | Player interaction scenarios | System coverage (all ECS systems exercised) | Protocol↔system consistency |
| Library/SDK | API usage scenarios | API surface coverage (all exports tested) | API↔usage pattern consistency |

## Composition Hints

### Single Node (default)
One node for most projects. All 3 sub-phases run sequentially.

### Split by Dimension
Very large projects: split into product-analysis-usecases, product-analysis-gaps, product-analysis-audit.

### Skip Feature Gap
If user explicitly opts out of gap analysis: generate use-cases + audit only.

### Merge
Never merge with core or ux — this node needs their complete output to verify.
