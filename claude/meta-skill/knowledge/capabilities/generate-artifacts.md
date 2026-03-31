# Generate Artifacts Capability

> Transform analysis results into structured .allforai/ artifacts for downstream consumption.
> Internal execution is LLM-driven — no fixed generation sequence.

## Goal

Transform discovery + analysis results into structured, machine-readable artifacts
that downstream nodes (translate, rebuild, demo-forge) consume.

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

| Archetype | Artifacts | Format |
|-----------|-----------|--------|
| Web/Mobile app | task-inventory, role-profiles, business-flows, experience-map, use-cases | Standard merge |
| CLI | command-tree, command-flows, use-cases | LLM direct |
| Data pipeline | dag-spec, transform-catalog | LLM direct |
| Game | system-spec, config-schema, protocol-spec | LLM direct |
| Library/SDK | api-surface, usage-patterns | LLM direct |

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
