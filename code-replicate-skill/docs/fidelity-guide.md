# Fidelity Level Guide

Fidelity controls the **depth of analysis** and which fields are populated in the standard allforai artifacts. Higher fidelity means more fields per artifact — not more files.

---

## Decision Tree

```
Do you need the API interface contract preserved exactly?
├── No (can redesign the interface) → interface
└── Yes → Does the business logic need to match?
            ├── No (only the surface contract) → interface
            └── Yes → Does the internal architecture need to match?
                        ├── No (same behavior, new structure) → functional
                        └── Yes → Must edge cases and bugs be replicated?
                                    ├── No → architecture
                                    └── Yes → exact
```

---

## Level Overview

### interface

**Goal:** Replicate the external API surface — endpoints, parameters, responses, status codes.

**Use when:**
- Backend rewrite, frontend unchanged
- Protocol migration (REST to GraphQL, preserve semantics)
- Microservice split, external interface stays the same

**Analysis time:** Fast (10–30 min)

### functional

**Goal:** Replicate business behavior — logic branches, data flow, error handling, side effects.

**Use when:**
- Tech stack migration (Python to Go, PHP to Node.js)
- Same-stack framework upgrade (Express to Fastify)
- Monolith to microservice split, preserving business logic

**Analysis time:** Medium (30–90 min)

### architecture

**Goal:** Replicate module structure, layering, dependency graph, design patterns.

**Use when:**
- Large-scale refactoring while preserving architectural decisions
- Team onboarding — understand architecture before migrating
- Introducing DDD / Clean Architecture based on existing structure

**Analysis time:** Long (1–3 hours)

### exact

**Goal:** 100% behavioral fidelity — including known bugs, edge cases, undocumented behavior.

**Use when:**
- Client code cannot be modified, server must behave identically
- Compliance / audit requirements (behavior must be traceable)
- Critical systems (payments, inventory) with zero regression tolerance

**Warning:** This level replicates known bugs. The replicate report marks each bug for user decision (replicate / fix). Use only for critical modules.

**Analysis time:** Very long (3+ hours, scales with codebase size)

---

## Artifact Field Matrix by Fidelity

All levels produce the same standard allforai artifacts. Fidelity controls which fields are populated.

### product-map/task-inventory.json

| Field | interface | functional | architecture | exact |
|-------|-----------|------------|--------------|-------|
| id, name, owner_role | Y | Y | Y | Y |
| inputs, outputs | Y | Y | Y | Y |
| main_flow | - | Y | Y | Y |
| exceptions | - | Y | Y | Y |
| rules | - | Y | Y | Y |
| acceptance_criteria | - | Y | Y | Y |
| module, prerequisites | - | - | Y | Y |
| cross_dept | - | - | Y | Y |
| flags (bug_replicate, edge_case) | - | - | - | Y |

### product-map/role-profiles.json

All fidelity levels produce role-profiles. `interface` includes basic role names and permissions. `functional+` adds detailed permission matrices and role hierarchies.

### product-map/business-flows.json

| Field | interface | functional | architecture | exact |
|-------|-----------|------------|--------------|-------|
| flow_id, name, steps | - | Y | Y | Y |
| trigger, outcome | - | Y | Y | Y |
| handoff detail (system, role, data) | - | - | Y | Y |

### use-case/use-case-tree.json

| Field | interface | functional | architecture | exact |
|-------|-----------|------------|--------------|-------|
| use_case_id, name, actor | - | Y | Y | Y |
| preconditions, main_flow | - | Y | Y | Y |
| alternative_flows | - | Y | Y | Y |
| exception_flows | - | - | Y | Y |

### product-map/constraints.json

Only produced at **exact** level. Contains known bugs marked as constraints, edge-case behaviors, and undocumented behaviors that must be preserved.

### task flags (exact only)

At exact level, tasks gain additional flags:
- `bug_replicate: true/false` — whether a known bug should be replicated
- `edge_case_coverage: [list]` — specific edge cases this task must handle
- `undocumented_behavior: [list]` — behaviors found in code but not in docs
