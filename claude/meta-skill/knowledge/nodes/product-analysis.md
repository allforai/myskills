# Product Analysis Node Template

> How to analyze a project's business domain and produce product artifacts.
> Covers: product-map, journey-emotion, experience-map, use-cases.

## Purpose

Transform source code understanding into business-level artifacts: roles, tasks,
business flows, experience maps, use cases. These artifacts are consumed by
downstream nodes (generate-artifacts, translate, demo-forge).

## Sub-Phases

### Product Map
- Role identification (from auth/permission code)
- Task expansion (from handlers/routes/pages)
- Constraint extraction (from validation rules)
- Business flow construction (from service orchestration)
- Conflict detection: task-level logic contradictions + CRUD gaps
- Data model mapping (from ORM/schema definitions)
- View object generation (per-role UI bindings)
- experience_priority classification: consumer / admin / mixed

Output: role-profiles.json, task-inventory.json, business-flows.json, constraints.json, product-map.json

### Journey-Emotion (if consumer or mixed)
- Per-role end-to-end emotional journey (touchpoints, emotional valence)
- Emotion low points and peak moments identification
- Anxiety / frustration / satisfaction annotation per touchpoint

Output: journey-emotion-map.json

### Experience Map (if frontend exists)
- Screen inventory (from pages/routes)
- Component mapping (from UI components)
- State variants per screen (empty/loading/error/success)
- Interaction triggers (click/input/scroll/timer/remote-event)
- Global components (nav, toast, modal)
- Button-level exception flows (on_failure, validation_rules, exception_flows)
- Screen-level conflict detection (redundant entries, unconfirmed high-risk ops, unhandled exceptions)
- If experience_priority = consumer|mixed: first-screen main path, next-step guidance, return motivation, mobile rhythm, state system maturity

Output: experience-map.json, screen-conflict.json

### Interaction Gate (quality gate after experience-map)
- Interaction consistency, usability, accessibility compliance check
- Gate: downstream sub-phases only proceed on pass

Output: interaction-gate.json

### Use Cases
- 4-layer tree: role -> functional area -> task -> use case
- Per task: 1 happy path + N exception flows + M boundary cases
- Given/When/Then format

Output: use-case-tree.json

### Feature Gap (optional, complements use-cases)
- Task completeness: CRUD coverage, exception/acceptance-criteria populated
- Screen completeness: primary operations exist, SILENT_FAILURE / UNHANDLED_EXCEPTION detection
- Journey walkthrough: per-role end-to-end path, 4-node scoring
- Gap tasks ranked by frequency

Output: task-gaps.json, screen-gaps.json, journey-gaps.json, gap-tasks.json

### Design Audit (cross-layer consistency)
- Reverse tracing: downstream artifacts have upstream sources
- Coverage flood: upstream nodes fully consumed downstream
- Horizontal consistency: adjacent layers have no contradictions

Output: audit-report.json

## Rules (Bootstrap Must Preserve)

1. **experience_priority classification**: consumer (end-user facing) / admin (professional) / mixed. Drives maturity thresholds downstream.
2. **Closure validation**: From observed features, infer complementary operations (CRUD completeness, error states, validation).
3. **Product language**: Artifacts speak in business terms (roles, tasks, flows), not technical terms.
4. **Exception mapping**: Every screen has empty/error/permission states.
5. **Button-level exception flows**: Every operation has on_failure, validation_rules, exception_flows.
6. **Structured fields**: inputs/outputs/audit as objects (not simple arrays).
7. **Required downstream fields**: experience_priority, protection_level, audience_type, render_as must be generated.
8. **4D self-check**: Each generated fragment checked for conclusion/evidence/constraint/decision completeness.
9. **Journey-emotion before experience-map**: Emotional journey must precede experience-map when consumer/mixed — it informs interaction quality expectations.
10. **Interaction gate is mandatory**: experience-map must pass the gate before use-case / feature-gap / ui-design sub-phases begin.
11. **Conflict detection at two layers**: task-level (product-map) and screen-level (experience-map) conflicts both surface independently.
12. **Consumer maturity bar**: consumer/mixed products evaluated against mature product standards — not just "feature exists" but "flow feels complete".

## What Bootstrap Specializes

- Business domain context (from bootstrap-profile.json: ecommerce, fintech, healthcare...)
- Which sub-phases are relevant (backend-only skips journey-emotion + experience-map + interaction-gate)
- Domain-specific role templates (ecommerce: buyer/seller/admin; healthcare: patient/doctor/admin)
- Domain-specific flow patterns (ecommerce: browse->cart->order->pay->fulfill)
- experience_priority preset (consumer-facing apps default to `consumer` or `mixed`)
