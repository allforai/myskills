# Generate Artifacts Capability

> Capability reference for artifact generation (.allforai/ structured outputs).
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Transform discovery results (source-summary, file-catalog, code-index) into
standard .allforai/ artifacts that downstream nodes consume.

## Protocol

### Pre-step: Extraction Plan
LLM generates extraction-plan.json — project-specific rules for what to extract from which files.
Fields: role_sources, task_sources, flow_sources, screen_sources, usecase_sources,
constraint_sources, cross_cutting, abstraction_sources, asset_sources, dependency_map.

LLM also determines artifact list via `artifacts[]` field — standard web apps produce
task-inventory + flows + roles; game servers produce system-spec + config-schema; etc.

After extraction-plan generation, LLM reviews coverage gaps and supplements missing key_files
before proceeding.

### Per-Artifact Execution
For each artifact in extraction-plan.artifacts:
1. LLM reads sources (per extraction-plan, using source-summary + code-index as global context)
2. Generates per-module JSON fragments
3. UI closure validation (compare with screenshots/API logs from discovery)
4. 4D self-check (conclusion/evidence/constraint/decision)
5. Merge script aggregates fragments -> final artifact

### Experience-Map Adaptive Depth
For each screen, LLM decides stub (fast) or deep (full) analysis. Deep mode extracts:
- interaction_triggers (5 types: click/input/scroll/timer/remote-event)
- state_variants (including remote-event-driven states)
- render_rules
- global_components
- Interaction pattern self-review

### UI-Driven Closure (per module)
After generating each module's fragments, LLM checks corresponding screenshots + API logs:
- Functional closure: observed write ops → infer complementary read/modify/delete
- Interaction closure: observed UI state → infer paired states (loading → success/error/empty)
- API closure: captured API requests → infer complete operation set for the resource
- Data closure: fields shown in screenshots → verify corresponding fetch/compute/format logic

### Completeness Sweep (final step)
- Dimension A: Source coverage — iterate all source files, check covered/uncovered
- Dimension B: User experience — walk each role's journeys, verify screens/endpoints/states
- Reconcile: late-discovered items tagged `"source": "sweep"`

## Fragment Model

```
fragments/{roles,tasks,flows,screens,usecases,constraints}/
  M001.json, M002.json, ...  (per-module)
```

Merge scripts: cr_merge_roles.py, cr_merge_tasks.py, cr_merge_flows.py, etc.
Merge handles: deduplication by (name, owner_role), sequential ID assignment, case-insensitive matching.

Fragments are temporary — they live under `fragments/` for merge script consumption only,
not delivered to dev-forge as final products.

## Rules (Bootstrap Must Preserve)

1. **Extraction-plan drives generation**: Every step follows plan's file specs, not framework templates.
2. **Single LLM call = single target**: One artifact type, one module per call.
3. **Scripts merge, not LLM**: LLM generates fragments, scripts handle cross-module merge + ID assignment.
4. **LLM semantic judgment first**: protection_level, audience_type, render_as from LLM understanding of source semantics, not keyword matching. Scripts are fallback only.
5. **Business intent only**: Extract "what it does", not "how it's implemented". Implementation decisions filled by target stack.
6. **Abstraction transfer**: High-reuse source patterns must map to target equivalents via stack-mapping. Never expand a shared base class / mixin into N copies of duplicate code.
7. **UI-driven closure**: Compare fragments with screenshots to verify completeness. Dead code in source is not extracted.
8. **4D self-check per fragment**: Fix issues before merge, don't wait for Phase 4.
9. **Required downstream fields**: experience_priority (product-map), protection_level (task), audience_type (role), render_as (component) must all be generated — dev-forge depends on them end-to-end.
10. **Structured fields**: inputs/outputs/audit must use object format (not simple arrays); then (use-case) must be an array.
11. **Archetype-driven artifact freedom**: LLM decides artifact list based on project_archetype. Non-standard projects produce custom schemas (dag-spec, system-spec, command-tree, etc.) stored in `.allforai/code-replicate/`.
12. **Config-as-code**: Non-code config files (nginx.conf, routes.yaml, OpenAPI spec, rbac.yaml) may contain business logic. extraction-plan must include them with `"module": null`.

## Scripts Referenced

- cr_merge_roles.py, cr_merge_tasks.py, cr_merge_flows.py, cr_merge_screens.py
- cr_merge_usecases.py, cr_merge_constraints.py
- cr_gen_indexes.py, cr_gen_product_map.py
- cr_validate.py (schema validation)

## Archetype-Specific Artifact Selection

Standard merge scripts (cr_merge_*.py) only apply to web-app archetypes.
For non-standard projects, LLM outputs complete JSON artifacts directly
(no fragment-merge workflow).

| Archetype | Artifacts | Uses merge scripts? |
|-----------|-----------|-------------------|
| web-app | task-inventory, role-profiles, business-flows, experience-map, use-case-tree | Yes |
| cli | command-tree, command-flows, use-case-tree | No (LLM direct) |
| data-pipeline | dag-spec, transform-catalog | No |
| game | system-spec, config-schema, protocol-spec | No |
| library | api-surface, usage-patterns | No |
| microservice | service-boundary-map, contract-spec | No |

Non-standard artifacts are written to `.allforai/code-replicate/` (not product-map/).

## Composition Hints

### Single Node (default)
For small-to-medium projects: one generate-artifacts node produces all artifact types in sequence.

### Split into Multiple Nodes
For complex projects with many artifact types: split per artifact category (generate-artifacts-roles-tasks, generate-artifacts-flows-screens, generate-artifacts-usecases).

### Merge with Another Capability
For simple projects with few modules: merge product-analysis + generate-artifacts into a single node.
