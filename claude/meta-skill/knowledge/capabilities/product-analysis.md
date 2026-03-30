# Product Analysis Capability (Composite)

> This capability has been split into 3 independent nodes for graph-based state transitions.
> Bootstrap should use the 3 sub-capabilities instead of this file for node generation.
> This file remains as a reference index.

## 3-Node Split

| Node | Capability File | Produces | Depends On |
|------|----------------|----------|------------|
| product-analysis-core | product-analysis-core.md | role-profiles, task-inventory, business-flows, constraints | source-summary OR product-concept |
| product-analysis-ux | product-analysis-ux.md | journey-emotion-map, experience-map, interaction-gate | product-analysis-core output |
| product-analysis-verify | product-analysis-verify.md | use-case-tree, gap-tasks, audit-report | core + ux output |

## Data Flow (Push + Pull)

```
product-analysis-core
  writes: .allforai/product-map/*.json
  pushes: summary to node_summaries (≤500 chars, routing only)
       │
       ▼ (pull: ux reads product-map/*.json)
product-analysis-ux
  writes: .allforai/experience-map/*.json
  pushes: summary to node_summaries
       │
       ▼ (pull: verify reads product-map/*.json + experience-map/*.json)
product-analysis-verify
  writes: .allforai/use-case/*.json + .allforai/feature-gap/*.json + .allforai/design-audit/*.json
```

## Backtrack Paths (Graph, Not Linear)

```
verify → ux    : missing screens, incomplete states, gate re-evaluation
verify → core  : missing tasks, unassigned roles, incomplete flows
ux     → core  : unmapped roles, missing tasks, incomplete flows
```

These backtracks are handled by the orchestrator's diagnosis protocol.
Each backtrack is a state transition visible in transition_log.

## When to Merge Back to 1 Node

Bootstrap may merge all 3 into a single node for:
- Very simple projects (<5 roles, <20 tasks, <10 screens)
- Non-frontend projects (CLI, data pipeline, library) where ux is skipped entirely

## Non-Web-App Archetypes

See each sub-capability file for archetype-specific behavior.
For CLI/pipeline/library: ux node is skipped, core + verify run with archetype-specific outputs.
