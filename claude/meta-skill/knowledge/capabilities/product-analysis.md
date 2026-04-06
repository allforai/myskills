# Product Analysis Capability

> Produce business-level artifacts from code or concept. Bootstrap generates project-specific
> analysis nodes. Internal execution is LLM-driven — no fixed sub-phase sequence.

## Goal

Produce business-level artifacts: roles, tasks, flows, experience maps, use cases.
These artifacts describe WHAT the product does in business terms, not HOW it's implemented.

## Input Paths

| Path | Input | When |
|------|-------|------|
| From code | source-summary.json + code reading + **concept-baseline.json** | goal = analyze / translate / rebuild |
| From concept | product-concept outputs + domain knowledge | goal = create |
| Hybrid | concept + code (rebuild with concept change) | goal = rebuild with new concept |

Output is the same regardless of input path.

**Concept-baseline dependency (for analyze goal):**
When goal = analyze, product-analysis SHOULD load `concept-baseline.json` if it exists
(produced by the upstream reverse-concept node). This baseline provides the independent
"what the product should do" reference that prevents product-analysis from being circular
(just listing what code does without evaluating completeness or intent).

With concept-baseline loaded, product-analysis can:
- Verify extracted tasks cover all Jobs in the baseline
- Check that role permissions match governance styles
- Flag features that exist in code but aren't aligned with the mission
- Flag JTBD from the baseline that have no corresponding code implementation

Without concept-baseline (backward compatibility), product-analysis still works
but produces purely descriptive artifacts without evaluative judgment.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What | Minimum |
|--------|------|---------|
| `role-profiles.json` | Who uses this product (roles, permissions, audience_type) | >= 2 roles |
| `task-inventory.json` | What can be done (tasks with inputs/outputs/constraints) | >= 10 tasks |
| `business-flows.json` | How tasks connect into user journeys | >= 5 flows |
| `experience-map.json` | What screens exist, what states, what interactions | >= 5 screens |
| `use-case-tree.json` | Given/When/Then scenarios (happy + exception + boundary) | >= 15 cases |

### Optional Outputs (LLM decides based on project type)

| Output | When to include |
|--------|----------------|
| `journey-emotion-map.json` | Consumer/mixed products (experience_priority != admin) |
| `interaction-gate.json` | After experience-map, always for consumer products |
| `constraints.json` | When business rules are complex |

### Required Quality

- `experience_priority` classified: consumer / admin / mixed
- Every task has inputs, outputs, and at least one constraint
- Every screen has state variants (empty/loading/error/success minimum)
- Every flow has a defined end state
- Consumer products: evaluated against consumer maturity patterns, not just "feature exists"

## Methodology Guidance (not steps)

LLM should apply these principles in whatever order and combination works:

- **Closure thinking**: If there's a "create", infer "read/update/delete". If there's a "buy", infer "refund"
- **Product language**: Artifacts speak in business terms, not technical terms
- **Exception mapping**: Every operation has on_failure, validation_rules, exception_flows
- **Journey-emotion informs experience**: Emotional journey should inform interaction quality expectations
- **Interaction gate before downstream**: Experience-map quality checked before use-cases/UI-design proceed
- **Conflict detection at two layers**: Task-level contradictions AND screen-level contradictions
- **4D self-check per fragment**: conclusion / evidence / constraint / decision

## Specialization Guidance

| Archetype | Analysis Differences |
|-----------|---------------------|
| **Web/Mobile app** | Standard: roles, tasks, flows, screens, use-cases |
| **CLI tool** | No roles (single user). Command tree replaces tasks. No screens. |
| **Data pipeline** | No roles. DAG spec replaces flows. Transform catalog replaces tasks. |
| **Game** | Roles = player types. System spec replaces tasks. Config schema replaces constraints. |
| **Library/SDK** | No roles. API surface replaces tasks. Usage patterns replace use-cases. |

For non-standard archetypes, LLM outputs custom schemas — not forced into the web-app mold.

## Knowledge References

### Phase-Specific:
- journey-emotion-schema.md: output schema for journey-emotion (if included)
- experience-map-schema.md: output schema for experience-map, three-layer structure
- governance-styles.md: governance style classification drives screen/role generation
- consumer-maturity-patterns.md: consumer maturity bar for experience-map evaluation
- design-audit-dimensions.md §Interaction-Gate: scoring model for interaction gate
- product-design-theory.md §Phase-2-3-4: Story Mapping, RACI, Nielsen Heuristics, Service Blueprint, INVEST

## Composition Hints

### Single Node (default)
For single-domain apps and simple products.

### Split into Multiple Nodes
For large apps with distinct business domains: one per domain.

### Merge with Another Capability
For simple projects: merge product-analysis + generate-artifacts into one node.
