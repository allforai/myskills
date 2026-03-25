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

### product-map/product-map.json

| Field | interface | functional | architecture | exact |
|-------|-----------|------------|--------------|-------|
| experience_priority | Y | Y | Y | Y |
| summary | Y | Y | Y | Y |
| roles, tasks (embedded) | Y | Y | Y | Y |
| conflicts | - | - | Y | Y |
| constraints | - | - | - | Y |

`experience_priority` is **always generated** — dev-forge reads `mode` to control consumer maturity checks across design-to-spec, task-execute, and product-verify.

### product-map/task-inventory.json

| Field | interface | functional | architecture | exact |
|-------|-----------|------------|--------------|-------|
| id, name, owner_role, category | Y | Y | Y | Y |
| inputs (structured), outputs (structured) | Y | Y | Y | Y |
| value, protection_level | Y | Y | Y | Y |
| main_flow | - | Y | Y | Y |
| exceptions, rules | - | Y | Y | Y |
| acceptance_criteria | - | Y | Y | Y |
| config_items, audit | - | Y | Y | Y |
| module, prerequisites | - | - | Y | Y |
| cross_dept | - | - | Y | Y |
| flags (bug_replicate, edge_case) | - | - | - | Y |

**New fields (v2.1+):**
- `protection_level` — `core` / `defensible` / `nice_to_have` — dev-forge XV audit routing depends on this
- `inputs` — structured object: `{fields: [], defaults: {}}`
- `outputs` — structured object: `{states: [], messages: [], records: [], notifications: []}`
- `audit` — `{recorded_actions: [], fields_logged: []}`
- `config_items` — array of `{param, current, config_level}`
- `value` — business value description

### product-map/role-profiles.json

| Field | interface | functional | architecture | exact |
|-------|-----------|------------|--------------|-------|
| id, name, audience_type | Y | Y | Y | Y |
| permission_boundary, kpi | Y | Y | Y | Y |
| operation_profile | - | Y | Y | Y |

**New fields (v2.1+):**
- `audience_type` — `consumer` / `professional` — dev-forge consumer_apps identification depends on this
- `operation_profile` — `{frequency, density, screen_granularity, high_frequency_tasks, design_principle}` (optional, inferred from source code patterns)

### product-map/business-flows.json

| Field | interface | functional | architecture | exact |
|-------|-----------|------------|--------------|-------|
| flow_id, name, description | - | Y | Y | Y |
| nodes (task_ref, role, seq) | - | Y | Y | Y |
| node handoff (mechanism, data) | - | - | Y | Y |
| systems, confirmed, gap_count | - | Y | Y | Y |

**New fields (v2.1+):**
- `systems` — `{current, linked[]}` — identifies system boundaries
- `description` — 2-3 sentence flow description
- `confirmed` — boolean user confirmation flag
- `gap_count` — count of gap nodes per flow
- `node.handoff` — `{mechanism, data}` or null for cross-role transitions

### use-case/use-case-tree.json

| Field | interface | functional | architecture | exact |
|-------|-----------|------------|--------------|-------|
| id, role_id, task_id, type | - | Y | Y | Y |
| given, when, then (array) | - | Y | Y | Y |
| functional_area_id/name | - | Y | Y | Y |
| innovation_use_case | - | - | Y | Y |

**Format change (v2.5.0+):** Output is now a **flat `use_cases` array** (not nested tree). Each entry has explicit `role_id`, `functional_area_id`, `functional_area_name`, `task_id`, `task_name` fields. `then` is always an array of assertion strings.

**Type enum expanded:** `happy_path` / `exception` / `boundary` / `validation` / `journey_guidance` / `result_visibility` / `continuity` / `entry_clarity` / `innovation_mechanism` / `innovation_boundary` / `state_transition` / `state_timeout` / `state_compensation`

### experience-map/experience-map.json (frontend/fullstack stub)

| Field | interface | functional | architecture | exact |
|-------|-----------|------------|--------------|-------|
| operation_lines > nodes > screens | Y (stub) | Y (stub) | Y (stub) | Y (stub) |
| components[].render_as | Y | Y | Y | Y |
| layout_type, layout_description | Y | Y | Y | Y |
| states (structured dict) | Y | Y | Y | Y |
| data_fields (structured objects) | Y | Y | Y | Y |
| emotion_design | - | - | - | - |
| view_modes | - | - | - | - |
| screen_index | Y | Y | Y | Y |

**New fields (v2.1+):**
- `components[]` — structured array with `type`, `purpose`, `behavior`, `data_source`, `render_as` (12-value enum)
- `render_as` — `data_table` / `input_form` / `key_value` / `bar_chart` / `search_filter` / `action_bar` / `tab_nav` / `media_grid` / `card_grid` / `tree_view` / `timeline` / `text_block`
- `layout_type` + `layout_description` — semantic layout names (not generic)
- `states` — structured dict: `{empty, loading, error, success, ...business_states}`
- `data_fields[]` — structured objects: `{name, label, type, input_widget, required}`
- `flow_context` — `{prev, next}` screen navigation
- `screen_index` — top-level quick lookup index

Note: `emotion_design` and `view_modes` are **not generated** by code-replicate (design-side fields). LLM fragments may include them if detected in source code; otherwise they are left as null.

### product-map/constraints.json

Only produced at **exact** level. Contains known bugs marked as constraints, edge-case behaviors, and undocumented behaviors that must be preserved.

### task flags (exact only)

At exact level, tasks gain additional flags:
- `bug_replicate: true/false` — whether a known bug should be replicated
- `edge_case_coverage: [list]` — specific edge cases this task must handle
- `undocumented_behavior: [list]` — behaviors found in code but not in docs
