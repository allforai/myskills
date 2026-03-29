# Product Analysis Capability

> Capability reference for product analysis (product-map, journey-emotion, experience-map, use-cases).
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Produce business-level artifacts: roles, tasks, business flows, experience maps, use cases.
Input depends on the entry path:
- **From code (goal=analyze/translate/rebuild)**: source-summary.json + code analysis
- **From scratch (goal=create)**: product-concept.json + domain knowledge + user vision

Output is the same regardless of input path.

## Sub-Phases

### Product Map

**From existing code:**
- Role identification (from auth/permission code)
- Task expansion (from handlers/routes/pages)
- Constraint extraction (from validation rules)
- Business flow construction (from service orchestration)
- Data model mapping (from ORM/schema definitions)

**From scratch (no code):**
- Role identification (from product vision + domain knowledge)
- Task brainstorm (from user stories + domain patterns)
- Constraint definition (from business rules + compliance requirements)
- Business flow design (from user journeys)
- Data model design (from entities identified in tasks)

**Common to both paths:**
- Conflict detection: task-level logic contradictions + CRUD gaps
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

## Non-Web-App Archetypes

The sub-phases above are designed for web/mobile apps. For other project types,
bootstrap generates a DIFFERENT product-analysis node-spec:

### CLI Tool
- No roles (single user type). Skip role identification.
- **Command tree** replaces task-inventory: each subcommand = one task
- **Command flow** replaces business-flows: command pipelines and sequencing
- No experience-map (no UI). No journey-emotion.
- Use cases = command scenarios (happy path + error cases per subcommand)
- Output: command-tree.json, command-flows.json (instead of standard artifacts)

### Data Pipeline
- No roles. No experience-map.
- **DAG spec** replaces business-flows: pipeline stages and dependencies
- **Transform catalog** replaces task-inventory: each transform = one task
- Output: dag-spec.json, transform-catalog.json

### Game Server
- Roles = player types (not auth roles)
- **System spec** (ECS systems) replaces task-inventory
- **Config schema** (game balance tables) replaces constraints
- **Protocol spec** (client-server wire format) as additional artifact

### Library / SDK
- No roles. No flows.
- **API surface** replaces task-inventory: exported functions/types
- **Usage patterns** replaces use-cases: how consumers use the API
- Output: api-surface.json, usage-patterns.json

## Composition Hints

### Single Node (default)
For single-domain apps and simple products: one product-analysis node runs all sub-phases sequentially.

### Split into Multiple Nodes
For large apps with distinct business domains: one product-analysis node per domain (product-analysis-orders, product-analysis-inventory, product-analysis-payments).

### Merge with Another Capability
For simple projects with few roles and screens: merge product-analysis + generate-artifacts into a single node.
