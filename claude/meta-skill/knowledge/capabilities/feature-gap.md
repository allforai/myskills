# Feature Gap Capability

> Detect missing features by cross-referencing product artifacts. Finds CRUD gaps,
> journey dead-ends, and screen coverage holes.

## Purpose

After product-analysis produces roles/tasks/flows/experience-map, verify completeness
by checking that every entity has full CRUD, every journey reaches a conclusion,
and every screen state is handled.

## Protocol

### CRUD Completeness
For each data entity in task-inventory:
- Check: Create, Read, Update, Delete operations exist?
- Missing operations → gap (unless intentionally excluded, e.g., immutable audit logs)

### Journey Walkthrough
For each business flow:
- Walk from start to end: every step has a screen? every decision has both branches?
- Dead-end flows → gap

### Screen State Coverage
For each screen in experience-map:
- Check: empty, loading, error, success, permission-denied states exist?
- Missing states → gap

### Gap Scoring
Each gap scored by:
- Severity: core (blocks main flow) / important (affects UX) / minor (edge case)
- Effort: low / medium / high

Output: `.allforai/feature-gap/gap-report.json` + `gap-tasks.json` (actionable task list)

## Rules (Must Preserve)

1. **Entity-driven CRUD check**: Don't just check API endpoints — check from the entity perspective.
2. **Journey completeness**: Every flow must have a defined end state (success or explicit failure).
3. **State coverage**: Consumer-facing screens MUST have all 4 states. Admin screens need at minimum error + success.
4. **Gaps generate tasks**: Every gap becomes an actionable task in gap-tasks.json.

## Composition Hints

### Single Node (default)
Run after product-analysis + generate-artifacts are complete.

### Merge with Product Analysis
For simple projects: gap analysis as the final step of product-analysis node.

### Split by Dimension
For very large projects: separate CRUD-gap, journey-gap, and screen-gap nodes.
