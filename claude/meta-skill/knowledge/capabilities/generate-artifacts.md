# Generate Artifacts Capability

> Transform analysis results into structured .allforai/ artifacts for downstream consumption.
> Internal execution is LLM-driven — no fixed generation sequence.

## Goal

Transform discovery + analysis results into structured, machine-readable artifacts
that downstream nodes (translate, rebuild, demo-forge, ui-design) consume.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What | Consumed by |
|--------|------|-------------|
| `product-map.json` | Unified view: roles → tasks → flows → screens | all downstream |
| `view-objects.json` | Per-role UI bindings (what each screen shows for each role) | translate, rebuild, ui-design |
| `entity-model.json` | Data model with entities, fields, relationships, constraints | rebuild, demo-forge |
| `use-case-tree.json` | Finalized 4-layer use case tree (if not already complete) | test-verify |

### Required Quality

- Every entity has CRUD coverage in task-inventory
- Every screen maps to at least one task
- Every flow has corresponding use cases
- Entity model supports all business flows end-to-end
- `experience_priority`, `protection_level`, `audience_type`, `render_as` fields generated
- Structured fields: inputs/outputs/audit as objects, not simple arrays

## Methodology Guidance (not steps)

- **Entity model is the most critical artifact** — it drives API and mobile data layer
- **Business intent only**: Extract "what it does", not "how it's implemented"
- **Abstraction transfer**: High-reuse source patterns must map to target equivalents
- **UI-driven closure**: Compare artifacts with screenshots/API logs to verify completeness
- **4D self-check per fragment**: Fix issues during generation, not after
- **Archetype-driven artifact freedom**: Non-standard projects produce custom schemas

## Specialization Guidance

| Archetype | Artifacts | Output Location |
|-----------|-----------|-----------------|
| Web/Mobile app | task-inventory, role-profiles, business-flows, experience-map, use-cases | Standard `.allforai/product-map/` merge |
| CLI | command-tree, command-flows, use-cases | `.allforai/generate-artifacts/` LLM direct |
| Data pipeline | dag-spec, transform-catalog | `.allforai/generate-artifacts/` LLM direct |
| Game | system-spec.json, config-schema.json (loot tables, level data, balance), protocol-spec.md (if multiplayer) | `.allforai/game-design/` |
| Library/SDK | api-surface.json, usage-patterns.json | `.allforai/generate-artifacts/` LLM direct |
| Background service (Celery/BullMQ/Sidekiq) | task-spec.json (task names, arg schemas, retry policies), queue-topology.json | `.allforai/generate-artifacts/` LLM direct |
| KMM (Kotlin Multiplatform) | entity-model.json (shared once), per-platform view-objects (ios-view-objects.json, android-view-objects.json) | `.allforai/product-map/` for shared; `.allforai/generate-artifacts/` for platform views |
| GitHub Action | action-spec.json (inputs, outputs, runs config), workflow-examples.md | `.allforai/generate-artifacts/` LLM direct |

**view-objects.json note**: Only generate for projects with UI screens. Background services, CLI tools, and Library/SDK archetypes skip view-objects.json entirely — their Downstream Consumers (translate) do not need per-screen bindings.

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `product-map.json` | all fields | translate, ui-design | required | Unified view of roles/tasks/flows drives implementation and UI design |
| `view-objects.json` | `screens[].bindings` | translate, ui-design | required | Per-role UI bindings specify what each screen shows and what data it needs |
| `entity-model.json` | `entities[]`, `relationships[]` | translate, demo-forge | required | Data model is the foundation for API schema, ORM, and seed data |
| `use-case-tree.json` | `cases[].given_when_then` | test-verify, product-verify | required | 4-layer use case tree provides acceptance test specifications |

## Knowledge References

### Phase-Specific:
- experience-map-schema.md: three-layer structure for experience-map output
- journey-emotion-schema.md: emotion baseline validation for experience-map fragments
- cross-phase-protocols.md §Upstream-Baseline-Validation: verify fragments against upstream

## Composition Hints

### Single Node (default)
For small-to-medium projects.

### Split into Multiple Nodes
For complex projects: split per artifact category.

### Merge with Another Capability
For simple projects: merge product-analysis + generate-artifacts into one node.
