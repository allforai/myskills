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
| `monetization-design` | `lead-pm` | `app-design/monetization-design.html` | `app-design/monetization-design.json` | `ia-design` |
| `app-design-finalize` | `lead-pm` | `app-design/app-design-doc.html` | `app-design/app-design-doc.json` | ALL above |

**Required nodes (always included):** `ia-design`, `user-flow-design`, `interaction-design`, `app-design-finalize`

**Optional nodes:** `content-design` (content-heavy apps), `data-model-design` (data-intensive apps), `monetization-design` (paid/subscription apps)

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

## Sub-Skill Mapping

Bootstrap MUST generate thin delegating node-specs for app-design nodes. Each
node-spec reads the listed child skill `SKILL.md` files and follows their input,
output, validation, and repair contracts.

| Node ID | Required child skills |
|---------|----------------------|
| `ia-design` | `app-design/00-env/app-design-registry`, `app-design/10-concept/audience-positioning-spec`, `app-design/10-concept/job-story-spec`, `app-design/20-spec/app-surface-topology-spec`, `app-design/20-spec/information-architecture-spec`, `app-design/20-spec/feature-priority-spec` |
| `user-flow-design` | `app-design/20-spec/user-flow-spec`, `app-design/20-spec/screen-requirements-spec`, `app-design/40-qa/flow-coverage-qa` |
| `interaction-design` | `app-design/20-spec/interaction-pattern-spec`, `app-design/20-spec/permissions-notifications-settings-spec` |
| `content-design` | `app-design/20-spec/content-model-spec` |
| `data-model-design` | `app-design/20-spec/data-model-spec` |
| `monetization-design` | `app-design/20-spec/monetization-subscription-spec` |
| `app-design-finalize` | `app-design/30-generate/ui-input-handoff-generation`, `app-design/30-generate/program-handoff-generation`, `app-design/40-qa/app-design-closure-qa` |

Optional child skill selection:

- Add `content-design` for content-heavy, editorial, marketing, CMS, SEO,
  onboarding-heavy, education, or support-heavy apps.
- Add `data-model-design` for database-backed, workflow, admin, CRUD, analytics,
  import/export, offline-first, or permission-heavy apps.
- Add `monetization-design` when subscription, paid tiers, trial, paywall,
  credits, billing, marketplace, or app-store purchase language is present.

## Domain Extension Hooks

App-design remains domain-neutral. When the primary business domain has a
bundled app-domain skill pack, bootstrap should run that pack as a domain
extension and feed its handoff into `app-design-finalize`.

| Business domain | Domain skill pack | Domain handoff consumed by app-design |
|-----------------|-------------------|----------------------------------------|
| `ecommerce`, `b2c-commerce`, `marketplace`, `retail-commerce` | `app-domain/ecommerce` | `.allforai/app-domain/ecommerce/handoff/commerce-program-handoff-extension.json` |

Domain extensions refine business objects and state machines; app-design still
owns surfaces, screens, flows, UI handoff, and final program handoff.

### app-design-finalize — Aggregation

Goal: Merge all approved design JSONs into `app-design-doc.json`, then generate
downstream UI and program implementation handoffs and run closure QA.

Blocked by ALL other app-design nodes selected for this workflow (same pattern as `game-design-finalize`).

Required outputs:

- `.allforai/app-design/app-design-doc.json` — merged document with all schemas
  nested under their node IDs as top-level keys.
- `.allforai/app-design/app-design-doc.html` — human review summary.
- `.allforai/app-design/handoff/ui-design-input-handoff.json`
- `.allforai/app-design/handoff/program-development-node-handoff.json`
- `.allforai/app-design/qa/app-design-closure-qa-report.json`

The program handoff is the bridge into development planning. Downstream
frontend, backend, mobile, data, integration, compile, test, product-verify,
and runtime-smoke nodes must reference this artifact when it exists.

When domain handoff extensions exist, `app-design-finalize` must preserve them
as explicit `domain_handoff_refs` in `app-design-doc.json` and as
`input_artifacts`/`source_refs` in `program-development-node-handoff.json`.

## App Shape Specialization

App-design must specialize by deployable surface and runtime shape before
implementation nodes are planned. Do not collapse these into a generic
"frontend/backend" split:

| Shape | Required planning behavior |
|-------|----------------------------|
| Pure client | Generate client UI/state/storage/import/export validation; suppress backend/API assumptions. |
| Pure backend/API | Mark UI surfaces not applicable; generate API/admin/contract/test handoff only. |
| Single frontend + backend | Separate client, API/data, compile, test, product-verify, and runtime-smoke handoffs. |
| Multiple frontends + unified backend | Emit one implementation/test/verify path per surface plus shared backend contract checks. |
| Admin/operator/partner consoles | Treat each console as its own frontend surface with role-specific IA, permissions, and product verification. |
| Mobile + website + backend | Emit platform-native mobile UI verification, web Playwright verification, and backend API verification separately. |
| BaaS/serverless | Treat cloud service/emulator as backend runtime; do not invent a separate backend module unless code exists. |
| Desktop app | Specialize Electron/Tauri/native desktop build and UI automation separately from web. |

`app-surface-topology-spec.json` is the source of truth for these distinctions.
`program-development-node-handoff.json` must preserve the same `surface_id` and
module boundaries so bootstrap can create concrete implementation and QA nodes.

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
| `product-verify` | `handoff/program-development-node-handoff.json` | Implementation and validation-node coverage |
| `concept-acceptance` | `app-design-doc.json` | Baseline for concept vs. implementation comparison |
| `concept-freeze` | `app-design-doc.json` | Included in concept contract if present |
| implementation nodes | `handoff/program-development-node-handoff.json` | Source refs, inputs, outputs, runtime/tooling requirements, validation paths |
