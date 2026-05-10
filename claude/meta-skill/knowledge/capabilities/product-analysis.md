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
| From app design | `.allforai/app-design/app-design-doc.json` + concept baseline when present | app projects after app-design |
| From game design | `.allforai/game-design/game-design-doc.json` + `.allforai/game-design/design/program-development-node-handoff.json` | game projects after game-design |
| Hybrid | concept + code (rebuild with concept change) | goal = rebuild with new concept |

Output is the same regardless of input path.

## Design Handoff Input Precedence

Product-analysis is the first major convergence point between app and game
pipelines. It must select the most specific approved upstream design artifact
before falling back to a generic concept baseline.

Input precedence:

1. **Game project after game-design:** read
   `.allforai/game-design/game-design-doc.json` and
   `.allforai/game-design/design/program-development-node-handoff.json`. Use
   `implementation_nodes` as the primary seed for `task-inventory.json`.
2. **App project after app-design:** read `.allforai/app-design/app-design-doc.json`
   and map screens, flows, IA, and interactions into roles, tasks, flows,
   experience map, and use cases.
3. **Generic concept/code path:** read `.allforai/product-concept/concept-baseline.json`
   when present, plus discovery/code evidence when analyzing existing code.

Do not merge incompatible baselines silently. If both app-design and
game-design artifacts exist, choose based on `bootstrap-profile.json.is_game_project`
and report the ignored branch as a warning. If the selected design artifact is
missing but approval records show the design phase should have completed, return
`UPSTREAM_DEFECT` instead of falling back to a weaker concept baseline.

Game mapping rules:
- `game-design-doc.json.player_roles[]` -> `role-profiles.json.roles[]`.
- `game-design-doc.json.systems[]` and `program-development-node-handoff.json.implementation_nodes[]` -> `task-inventory.json.tasks[]`.
- `program-development-node-handoff.json.dependencies` -> `business-flows.json.flows[]`.
- UI/HUD/menu/dialogue/inventory runtime nodes -> `experience-map.json.screens[]`.
- `runtime_acceptance` and `test_command_or_validation_path` -> `use-case-tree.json.cases[]`.

App mapping rules:
- app-design roles/personas -> `role-profiles.json.roles[]`.
- app-design features/interactions -> `task-inventory.json.tasks[]`.
- app-design user flows -> `business-flows.json.flows[]`.
- app-design screens/components/states -> `experience-map.json.screens[]`.
- app-design acceptance rules -> `use-case-tree.json.cases[]`.

**source-summary.json fields consumed (for analyze/translate/rebuild goals):**

| Field | Used for |
|-------|----------|
| `tech_stacks[]` | Determine analysis strategy (web-app vs game vs CLI) |
| `modules[]` | Scope of analysis — which modules to cover |
| `modules[].key_files[]` | Entry points for code reading |
| `architecture_pattern` | Select archetype-specific output schema (see Specialization Guidance) |
| `detected_patterns[]` | Identify domain-specific conventions (e.g., ECS for games, event-sourcing for backend) |
| `experience_priority` | Classification hint: consumer / admin / mixed |

**Archetype fallback rule**: If `source-summary.json` is absent (goal = create, or discovery was skipped), infer archetype from `product-concept.json.architecture_pattern`. If neither exists, default to `web-app` archetype and note the assumption in the output artifacts.

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

**task-inventory.json field schema (minimum required fields):**
```json
{
  "tasks": [
    {
      "id": "<string — unique, stable identifier. Used as FK by feature-gap.gaps[].task_ref>",
      "name": "<string>",
      "role_ref": "<string — MUST match a roles[].id in role-profiles.json>",
      "inputs": ["<string>"],
      "outputs": ["<string>"],
      "constraints": ["<string>"]
    }
  ]
}
```

**role-profiles.json field schema (minimum required fields):**
```json
{
  "roles": [
    {
      "id": "<string — unique identifier. Referenced by task-inventory.tasks[].role_ref>",
      "name": "<string>",
      "permissions": ["<string>"],
      "audience_type": "<enum: consumer | admin | operator | system>"
    }
  ]
}
```

`tasks[].id` and `roles[].id` are foreign key roots for all downstream capabilities.
Every capability that references a task or role MUST use these IDs.

### Optional Outputs (LLM decides based on project type)

| Output | When to include |
|--------|----------------|
| `journey-emotion-map.json` | Consumer/mixed products (experience_priority != admin) |
| `interaction-gate.json` | After experience-map, always for consumer products |
| `constraints.json` | When business rules are complex |

### Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `role-profiles.json` | `roles` | feature-gap, feature-prune, ui-design, generate-artifacts | required | 角色定义是所有下游功能和 UI 设计的基础 |
| `task-inventory.json` | `tasks` | feature-gap, feature-prune, generate-artifacts | required | 任务清单是功能差距分析和代码生成的输入 |
| `task-inventory.json` | `tasks[].id`, `tasks[].role_ref` | feature-gap, feature-prune | required | 外键引用，下游必须用这些 ID 保持一致性 |
| `business-flows.json` | `flows` | ui-design, generate-artifacts | required | 用户旅程定义 UI 结构和功能实现顺序 |
| `experience-map.json` | `screens` | ui-design, generate-artifacts, product-verify | required | 屏幕契约是 UI 设计和验收的基础 |
| `use-case-tree.json` | `cases` | test-verify, product-verify | required | 验收用例来自 Given/When/Then |
| `journey-emotion-map.json` | `stages` | ui-design | optional | 仅 consumer 产品有此产物；缺失时跳过情感设计维度 |

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
