# Product Analysis Core Capability

> Capability reference for the foundation layer of product analysis:
> role identification, task expansion, business flows, constraints.
> This is the first of 3 product-analysis nodes.

## Purpose

Produce the business foundation: who uses the system, what they do, and how work flows.
All downstream nodes (ux, verify, implement, translate) depend on these artifacts.

## Entry Path

- **From code with extraction**: reads `.allforai/code-replicate/extracted/` (generate-artifacts output) as initial input, then refines with business analysis
- **From code without extraction**: reads source-summary.json directly + code analysis
- **From scratch (goal=create)**: reads product-concept.json + domain knowledge

Output is the same regardless of entry path. When extracted/ exists, pa-core
enriches it (adds missing roles, CRUD closure, business flows). When it doesn't,
pa-core generates from scratch.

## Sub-Phases

### Role Identification

**From code:** Extract from auth/permission code, route guards, role enums.
**From scratch:** Derive from product vision + domain patterns.

- Classify experience_priority: consumer / admin / mixed
- Each role: id, name, description, permissions, primary_tasks

### Task Expansion

**From code:** Extract from handlers/routes/pages/controllers.
**From scratch:** Brainstorm from user stories + domain patterns.

- Per task: id, name, owner_role, CRUD type, inputs, outputs, validation_rules
- Closure validation: infer complementary operations (create→read→update→delete)
- Conflict detection: task-level logic contradictions + CRUD gaps

### Business Flows

**From code:** Extract from service orchestration, state machines, event handlers.
**From scratch:** Design from user journeys.

- Per flow: id, name, steps (ordered task references), decision points, error branches
- Every flow has a defined end state

### Constraints

**From code:** Extract from validation rules, business logic guards.
**From scratch:** Define from business rules + compliance requirements.

### Data Model

**From code:** Extract from ORM/schema definitions.
**From scratch:** Derive from entities identified in tasks.

## Output Files (exit_requires)

All written to `.allforai/product-map/`:
- `role-profiles.json`
- `task-inventory.json`
- `business-flows.json`
- `constraints.json`
- `product-map.json` (summary index)

## Data Contract — What Downstream Nodes Pull

| Consumer | Pulls | Why |
|----------|-------|-----|
| product-analysis-ux | role-profiles, task-inventory, business-flows | Needs roles for journey-emotion, tasks for experience-map screens |
| product-analysis-verify | role-profiles, task-inventory, business-flows | Needs all three for use-case tree + feature-gap coverage |
| implement / translate | task-inventory, business-flows | Needs to know what to build |
| ui-design | role-profiles, task-inventory | Needs roles for per-role previews, tasks for screen specs |

## Backtrack Triggers

Other nodes may trigger a backtrack to this node when:
- **product-analysis-ux** discovers screens that don't map to any role → missing role
- **product-analysis-verify** finds CRUD operations without corresponding tasks → missing task
- **feature-gap** detects flows with undefined end states → incomplete business-flows

On re-execution: re-read source (code or concept), regenerate affected artifacts,
preserve unchanged artifacts.

## Rules (Bootstrap Must Preserve)

1. **experience_priority classification mandatory**: Drives all downstream maturity thresholds.
2. **Closure validation**: Infer complementary CRUD operations from observed features.
3. **Product language**: Business terms (roles, tasks, flows), not technical terms.
4. **Structured fields**: inputs/outputs/audit as objects, not simple arrays.
5. **4D self-check**: Each fragment checked for conclusion/evidence/constraint/decision completeness.
6. **Conflict detection**: Task-level contradictions surface here, not downstream.

## Non-Web-App Archetypes

| Archetype | Replaces roles with | Replaces tasks with | Replaces flows with |
|-----------|--------------------|--------------------|---------------------|
| CLI | Single user type (skip) | command-tree.json | command-flows.json |
| Data pipeline | Single user type (skip) | transform-catalog.json | dag-spec.json |
| Game server | Player types | system-spec.json | protocol-spec.json |
| Library/SDK | Single consumer (skip) | api-surface.json | usage-patterns.json |

## Composition Hints

### Single Node (default)
One node for single-domain apps. All sub-phases run sequentially within one subagent.

### Split by Domain
Large apps with distinct business domains: product-analysis-core-orders, product-analysis-core-payments.

### Merge
Very simple projects (<5 roles, <20 tasks): merge with product-analysis-ux into a single node.
