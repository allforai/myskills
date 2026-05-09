# App Design Capability

> Covers the design phase for non-game app products. Parallel to `game-design.md`
> but tailored for SaaS, consumer apps, tools, and e-commerce products.
> Each node in this capability has `human_gate: true` and requires `discipline_owner` approval.

## Canonical Node Registry

Bootstrap uses this registry when `business_domain != "gaming"` and the goal includes design phases.

| Node ID | Discipline Owner | HTML Output | JSON Output | Blocked By |
|---------|-----------------|-------------|-------------|------------|
| `ia-design` | `lead-ux` | `app-design/ia-design.html` | `app-design/ia-design.json` | _(none — first node)_ |
| `user-flow-design` | `lead-ux` | `app-design/user-flow-design.html` | `app-design/user-flow-design.json` | `ia-design` |
| `interaction-design` | `lead-ux` | `app-design/interaction-design.html` | `app-design/interaction-design.json` | `user-flow-design` |
| `content-design` | `lead-content` | `app-design/content-design.html` | `app-design/content-design.json` | `ia-design` |
| `data-model-design` | `lead-engineer` | `app-design/data-model-design.html` | `app-design/data-model-design.json` | `ia-design` |
| `app-design-finalize` | `lead-pm` | `app-design/app-design-doc.html` | `app-design/app-design-doc.json` | ALL above |

**Required nodes (always included):** `ia-design`, `user-flow-design`, `interaction-design`, `app-design-finalize`

**Optional nodes:** `content-design` (content-heavy apps), `data-model-design` (data-intensive apps)

## Node Descriptions

### ia-design — Information Architecture

Goal: Define the app's structure — screens, navigation model, content hierarchy.

Inputs: `product-concept.json.must_have`, `product-concept.json.differentiators`

Output JSON schema:
```json
{
  "nav_model": "<tab | drawer | stack | hybrid>",
  "screens": [
    {
      "screen_id": "<slug>",
      "name": "<display name>",
      "purpose": "<one sentence>",
      "entry_points": ["<screen_id>"]
    }
  ],
  "primary_flows": ["<flow name>"]
}
```

HTML presentation: Screen map diagram + navigation model rationale.

### user-flow-design — User Flows

Goal: Map the step-by-step paths users take to complete core tasks.

Inputs: `ia-design.json.screens[]`, `product-concept.json.core_loop`

Output JSON schema:
```json
{
  "flows": [
    {
      "flow_id": "<slug>",
      "name": "<display name>",
      "trigger": "<entry screen_id>",
      "steps": [
        { "step": 1, "screen": "<screen_id>", "action": "<user action>", "outcome": "<result>" }
      ],
      "happy_path_length": 0,
      "error_paths": ["<description>"]
    }
  ]
}
```

HTML presentation: Flow diagrams per primary flow.

### interaction-design — Interaction Patterns

Goal: Define micro-interactions, states, and feedback patterns for key UI components.

Output JSON schema:
```json
{
  "components": [
    {
      "component_id": "<slug>",
      "name": "<display name>",
      "states": ["default", "hover", "active", "disabled", "loading", "error"],
      "feedback": "<how the component responds to user action>",
      "animation": "<none | subtle | prominent>"
    }
  ],
  "gesture_model": "<tap-only | swipe-primary | mixed>",
  "loading_strategy": "<skeleton | spinner | progressive>"
}
```

HTML presentation: Component state matrix + interaction annotations.

### content-design — Content Strategy (optional)

Goal: Define copy voice, content hierarchy, and microcopy patterns.

Inputs: `product-concept.json.target_users`, `ia-design.json.screens[]`

Output JSON schema:
```json
{
  "voice": "<formal | conversational | playful | authoritative>",
  "tone_by_context": {
    "onboarding": "<tone>",
    "error_states": "<tone>",
    "empty_states": "<tone>"
  },
  "microcopy_patterns": [
    { "context": "<screen or component>", "example": "<sample copy>" }
  ]
}
```

### data-model-design — Data Model (optional)

Goal: Define the core entities, relationships, and data flow for the app.

Inputs: `product-concept.json.must_have`, `ia-design.json.screens[]`

Output JSON schema:
```json
{
  "entities": [
    {
      "entity_id": "<slug>",
      "name": "<display name>",
      "fields": [{ "name": "<field>", "type": "<string | number | boolean | ref>", "required": true }],
      "relationships": [{ "entity": "<entity_id>", "type": "<one-to-many | many-to-many | belongs-to>" }]
    }
  ],
  "data_flow": "<client-first | server-first | hybrid>"
}
```

### app-design-finalize — Aggregation

Goal: Merge all approved design JSONs into `app-design-doc.json`.

Blocked by ALL other app-design nodes selected for this workflow (same pattern as `game-design-finalize`).

Output: `app-design/app-design-doc.json` — merged document with all schemas nested under their node IDs as top-level keys.

## Human Gate Protocol

Identical to `game-design.md` human gate protocol:
- Approval tracked in `.allforai/app-design/approval-records.json`
- Same `gate_status` lifecycle: `pending → in-review → approved | revision-requested`
- `discipline_owner` approves; `discipline_reviewers` are advisory only

Bootstrap initialises one `pending` record per selected app-design node at bootstrap time.

## Downstream Consumers

| Consumer | Reads from | Fields |
|----------|-----------|--------|
| `ui-design` | `ia-design.json` | `screens[]`, `nav_model` |
| `ui-design` | `user-flow-design.json` | `flows[]` → wireframe sequence |
| `product-verify` | `app-design-doc.json` | Expected screens and flows for verification |
| `concept-acceptance` | `app-design-doc.json` | Baseline for concept vs. implementation comparison |
| `concept-freeze` | `app-design-doc.json` | Included in concept contract if present |
