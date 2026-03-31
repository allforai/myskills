# Feature Gap Capability

> Detect missing features by cross-referencing product artifacts.
> Internal execution is LLM-driven — dimensions and checks are project-specific.

## Goal

Verify completeness of product artifacts before code is written. Find CRUD gaps,
journey dead-ends, screen state holes, and unhandled exceptions.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `gap-report.json` | Gaps found across all checked dimensions |
| `gap-tasks.json` | Actionable tasks for each gap, scored by severity × effort |

### Check Dimensions (LLM selects which apply)

LLM decides which dimensions to check based on the project's entity model, flows, and screens.
These are TYPES of checks, not a fixed checklist:

| Dimension | What to check | Applies when |
|-----------|--------------|-------------|
| CRUD completeness | Every entity has all needed operations | Always |
| Journey completeness | Every flow has a defined end state, both branches at decisions | Has business flows |
| Screen state coverage | empty/loading/error/success/(offline) states exist | Has UI screens |
| Consumer maturity | Flows feel complete, not just "feature exists" | experience_priority = consumer/mixed |
| Offline coverage | Core flows work offline | Offline-first products |
| Error recovery | Every error state has a recovery path | Always |
| Permission coverage | Every role can only access what they should | Multi-role products |

### Required Quality

- Every gap becomes an actionable task in gap-tasks.json
- Gaps scored: severity (core/important/minor) × effort (low/medium/high)
- No core-severity gaps left unaddressed in the plan

## Methodology Guidance (not steps)

- **Entity-driven**: Check from the entity perspective, not the API perspective
- **Journey-driven**: Walk each flow end-to-end, verify every step has a screen
- **Consumer maturity bar**: For consumer products, "feature exists" is not enough — "flow feels complete"
- **Gaps generate tasks**: Don't just find gaps — create actionable tasks with clear scope

## Knowledge References

### Phase-Specific:
- experience-map-schema.md §States: screen state coverage requirements
- journey-emotion-schema.md: journey completeness validation
- consumer-maturity-patterns.md: consumer maturity gap detection

## Composition Hints

### Single Node (default)
Run after product-analysis + generate-artifacts.

### Merge with Product Analysis
For simple projects: gap analysis as the final step of product-analysis node.
