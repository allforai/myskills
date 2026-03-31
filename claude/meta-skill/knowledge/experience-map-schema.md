# Experience Map Schema

> Extracted from product-design-skill: experience-map.md + docs/experience-map/output-schema.md + interaction-gate.md

---

## Purpose

Transforms journey-emotion data and product-map artifacts into a three-layer experience structure: operation_lines > nodes > screens. LLM freely designs each interface based on product semantics, then self-validates against hard constraints.

Output file: `.allforai/experience-map/experience-map.json`

---

## Three-Layer Hierarchy

```
operation_lines[]                 -- Business flow mapped to interaction sequence
  └── nodes[]                    -- Individual steps within the flow
        └── screens[]            -- Actual UI screens the user interacts with
```

Each operation_line has at least one node. Each node has at least one screen. Screens are embedded as **complete objects** (not references) -- downstream tools read directly from `node.screens[].id`.

---

## Full JSON Schema

```json
{
  "operation_lines": [
    {
      "id": "OL001",
      "name": "string — operation line description",
      "source_journey": "string — reference to journey_line ID (e.g. JL01)",
      "role": "string — role ID",
      "quality_score": "integer (optional) — 0-100, written by interaction-gate",
      "nodes": [
        {
          "seq": "integer — sequential position in this operation line",
          "id": "string — node ID (e.g. N001)",
          "action": "string — user action at this step",
          "screens": [
            {
              "id": "string — S001 format",
              "name": "string — screen name in product language",
              "description": "string — 2-3 sentences: purpose + design intent (why this design)",
              "platform": "string — mobile-ios | desktop-web",
              "app": "string — independent application name (website, merchant, admin, etc.)",
              "layout_type": "string — semantic layout name from business purpose",
              "layout_description": "string — 1-2 sentences: specific spatial layout, unique per screen",
              "interaction_type": "string — from renderer support list",
              "tasks": ["string — task_id references"],
              "actions": ["string — user-performable operations"],
              "components": [
                {
                  "type": "string — LLM-named component",
                  "purpose": "string — what it does",
                  "behavior": "string — how it behaves on interaction",
                  "data_source": "string — data origin",
                  "render_as": "string — wireframe rendering directive"
                }
              ],
              "interaction_pattern": "string — 1-2 sentences describing the interaction model",
              "emotion_design": {
                "source_emotion": "string — delighted|satisfied|neutral|frustrated|anxious|angry",
                "source_hint": "string — original design_hint from journey-emotion",
                "design_response": "string — concrete design decision (actionable, not abstract)",
                "visual_tone": "string — celebratory|calm_reassuring|efficient_focused|warm_friendly|neutral_professional",
                "interaction_density": "string — low|medium|high"
              },
              "states": {
                "empty": "string — screen-specific empty state",
                "loading": "string — screen-specific loading behavior",
                "error": "string — screen-specific error handling",
                "success": "string — screen-specific success feedback",
                "business_state_example": "string — at least 1 business-specific state"
              },
              "view_modes": [
                {
                  "id": "string — snake_case identifier",
                  "label": "string — human-readable mode name",
                  "trigger": "string — user action that activates this mode",
                  "layout": "string — which regions visible, proportions",
                  "active_components": ["string — component types visible"],
                  "available_actions": ["string — actions available in this mode"]
                }
              ],
              "data_fields": [
                {
                  "name": "string — snake_case field identifier",
                  "label": "string — user-visible label",
                  "type": "string — string|number|boolean|date|enum|array|image|rich_text",
                  "input_widget": "string — text_input|textarea|number_input|select|multi_select|toggle|date_picker|file_upload|rich_editor|readonly",
                  "required": "boolean"
                }
              ],
              "flow_context": {
                "prev": "string|null — previous screen ID",
                "next": "string|null — next screen ID",
                "entry_points": ["string — screen IDs that navigate here"],
                "exit_points": ["string — screen IDs reachable from here"]
              },
              "vo_ref": "string (optional) — view object reference",
              "api_ref": "string (optional) — API endpoint reference",
              "source_refs": ["string (optional) — D2 evidence URLs"],
              "_pattern": ["string (auto) — functional pattern IDs, Step 3.6"],
              "_pattern_group": "string (auto) — pattern group ID, Step 3.6",
              "_behavioral": ["string (auto) — behavioral category IDs, Step 3.6"],
              "_behavioral_standards": "object (auto) — behavioral standard mappings, Step 3.6"
            }
          ]
        }
      ]
    }
  ],
  "screen_index": {
    "S001": "// complete screen object duplicate, keyed by screen ID for fast lookup"
  }
}
```

---

## Per-Screen Field Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `S001` format |
| `name` | string | Screen name in product language |
| `description` | string | 2-3 sentences: purpose and design intent (why, not just what) |
| `platform` | string | `mobile-ios` or `desktop-web` |
| `app` | string | Independent application name. Derived from **node role**, not operation line role. `app` != `platform` |
| `layout_type` | string | Semantic layout name from business purpose (e.g., `auth_card`, `priority_queue`, `structured_editor`, `visual_card_grid`, `status_timeline`). Must NOT copy interaction_type or be generic |
| `layout_description` | string | 1-2 sentences: specific spatial layout with region positions, size ratios, visual weights. Unique per screen |
| `interaction_type` | string | From renderer support list (see below). Affects wireframe layout template selection |
| `tasks` | array | Referenced task_id array |
| `actions` | array | User-performable operations list |
| `components` | array | LLM-designed component objects (see components section) |
| `interaction_pattern` | string | 1-2 sentences describing the interaction model |
| `states` | object | Screen states with 4 base + business-specific states |
| `flow_context` | object | Navigation context (prev/next/entry_points/exit_points) |
| `data_fields` | array | Data field objects displayed/operated on this screen |

### Recommended Fields

| Field | Type | Description |
|-------|------|-------------|
| `emotion_design` | object or null | Structured emotion-based design decisions. Null when no upstream emotion ref |
| `vo_ref` | string | Associated view object |
| `api_ref` | string | Associated API endpoint |
| `source_refs` | array | D2 evidence URLs for design decisions |

### Conditional Fields

| Field | Type | Condition |
|-------|------|-----------|
| `view_modes` | array | Required when `screen_granularity = multi_function_per_page` |

### Auto-Generated Fields (Step 3.6)

| Field | Type | Description |
|-------|------|-------------|
| `_pattern` | array | Functional pattern ID array |
| `_pattern_group` | string | Pattern group ID |
| `_behavioral` | array | Behavioral category ID array |
| `_behavioral_standards` | object | Behavioral standard mappings |

---

## Component Structure

```json
{
  "type": "string — LLM-named component (free naming)",
  "purpose": "string — what this component does",
  "behavior": "string — how it behaves on interaction",
  "data_source": "string — where data comes from",
  "render_as": "string — wireframe rendering directive"
}
```

### render_as Values

Every component **must** include `render_as`. LLM selects based on the component's actual business purpose, not its name.

| render_as | Wireframe Representation | Use For | Never Use For |
|-----------|------------------------|---------|---------------|
| `data_table` | Header + multi-row data + pagination | Lists, tables, matrices, queues | Button groups, tabs, single values |
| `input_form` | Label + input/selector arrangement | **Multi-field** forms, editors, config pages | Single selector, sort toggle, simple switch |
| `key_value` | Label-value horizontal pairs | Detail panels, overview info, summary cards | Tab switching, button groups |
| `bar_chart` | Bar chart placeholder + metric labels | KPIs, statistics, charts, trends, dashboards | Regular lists |
| `search_filter` | Search box + filter tags | Search bars, filter panels, sidebar filters | -- |
| `action_bar` | Button row (primary + secondary) | Toolbars, action areas, submit bars, **single selectors, sort toggles, steppers, button groups** | -- |
| `tab_nav` | Tab switching strip | Tab navigation, **status tabs**, step bars, category switches | Never substitute with key_value or data_table |
| `media_grid` | Image/video placeholder grid | Albums, image uploads, media display | -- |
| `card_grid` | Card grid (image + text) | Product cards, recommendations, content feeds | -- |
| `tree_view` | Indented hierarchical nodes | Category trees, org structures, folders | -- |
| `timeline` | Dot-line timeline | **Progress tracking, logistics, operation history** | Not for quantity steppers or button actions |
| `text_block` | Plain text paragraph | Descriptions, empty state hints, notification content | Not for actionable components |

**Selection principles**:
1. What is the component's primary interaction? Click buttons -> `action_bar`; fill multi-field -> `input_form`; view multi-row data -> `data_table`
2. Single control or compound? Single dropdown/switch/button -> `action_bar`; multiple input fields -> `input_form`
3. Switching components always use `tab_nav`
4. Statistics/chart components always use `bar_chart`

---

## data_fields Format

Each element must be a structured object (never a plain string). Downstream wireframe renderer depends on this format.

```json
{
  "name": "scenario_title",
  "label": "Scenario Title",
  "type": "string",
  "input_widget": "text_input",
  "required": true
}
```

| Field | Description |
|-------|-------------|
| `name` | Field identifier (snake_case, maps to entity-model field name) |
| `label` | User-visible label |
| `type` | `string` / `number` / `boolean` / `date` / `enum` / `array` / `image` / `rich_text` |
| `input_widget` | `text_input` / `textarea` / `number_input` / `select` / `multi_select` / `toggle` / `date_picker` / `file_upload` / `rich_editor` / `readonly` (display-only) |
| `required` | Whether the field is mandatory |

Only list fields core to the screen, not exhaustive. LLM selects `type` and `input_widget` from entity-model and view-object semantics.

---

## emotion_design Format

Must be a structured object, never a plain string. Null/omit when no upstream emotion reference exists.

```json
{
  "source_emotion": "anxious",
  "source_hint": "User's first payment, worried about security and amount",
  "design_response": "Emphasize security badges (lock icon + Stripe brand), large font payment confirmation, clear progress bar",
  "visual_tone": "calm_reassuring",
  "interaction_density": "low"
}
```

| Field | Description |
|-------|-------------|
| `source_emotion` | From upstream `_emotion_ref.emotion`: delighted / satisfied / neutral / frustrated / anxious / angry |
| `source_hint` | From upstream `_emotion_ref.design_hint` (quoted or summarized) |
| `design_response` | LLM's concrete design decision for this emotion (1-2 sentences, must be actionable, not abstract) |
| `visual_tone` | `celebratory` (achievement) / `calm_reassuring` (safety) / `efficient_focused` (productivity) / `warm_friendly` (approachable) / `neutral_professional` (standard) |
| `interaction_density` | `low` (few actions, whitespace, single CTA) / `medium` (standard) / `high` (data-dense, batch ops) |

---

## States Format

Object with key=state name, value=screen-specific interaction description.

### 4 Mandatory Base States

| State | Description |
|-------|-------------|
| `empty` | What appears when no data exists (specific illustration, specific CTA). Must be unique per screen |
| `loading` | How loading manifests (skeleton screen, spinner, shimmer). Screen-specific |
| `error` | Error handling behavior (specific error types, retry mechanism). Screen-specific |
| `success` | Success feedback (toast, animation, redirect). Screen-specific |

Values must **not** be copy-pasted across screens. Each screen describes its own specific behavior.

### Business-Specific States (at least 1 per screen)

| Screen Type | Required Business States |
|-------------|------------------------|
| Approval/status transition screens | `pending`, `approved`, `rejected` |
| Payment screens | `processing_payment`, `payment_failed`, `payment_timeout` |
| Real-time communication screens | `connecting`, `connected`, `disconnected` |
| Async computation screens | `calculating`, `generating`, `syncing` |
| Any other | At least 1 relevant to the screen's business purpose |

### States vs View Modes

- **States**: Data conditions (empty, loading, error). Can occur within any view_mode.
- **View Modes**: Interaction-triggered layout changes (list -> detail panel). Describe structural changes, not data conditions.

---

## view_modes Format

Describes **intra-screen view transitions** -- how the same page changes structure based on user actions.

```json
{
  "id": "full_list",
  "label": "Full list view",
  "trigger": "Initial load / clear filters",
  "layout": "All tabs highlighted, table shows all records, no right panel",
  "active_components": ["record-tabs", "search-bar", "record-table", "pagination"],
  "available_actions": ["Search", "Switch tab", "Click row to view details"]
}
```

| Field | Description |
|-------|-------------|
| `id` | snake_case identifier |
| `label` | Human-readable mode name |
| `trigger` | User action that activates this mode |
| `layout` | Which regions visible, proportions, positioning |
| `active_components` | Component types visible (references `components[].type`) |
| `available_actions` | Actions available in this mode |

**Rules**:
- **Required** when role has `screen_granularity = "multi_function_per_page"` (typically merchant/admin)
- First view_mode is the default/initial view
- View modes form a directed graph: each mode's `trigger` indicates reachability
- Mobile single-task screens may omit
- Complementary to `states`: different states can occur within the same view_mode

---

## Hard Constraints

| Constraint | Rule | Rationale |
|-----------|------|-----------|
| **Platform** | consumer role -> `mobile-ios` single-column layout; professional role -> `desktop-web` sidebar layout | Physical device differences |
| **App ownership** | Every screen must have `app` field. In cross-role flows, screen app is derived from **node role**, not operation line's main role | merchant and admin are different deployable apps even if both desktop-web |
| **Task coverage** | Every task from task-inventory.json must appear in at least one screen's `tasks` array | Functional completeness |
| **Business flow continuity** | Adjacent tasks in a business flow must have navigable paths between their screens (via `flow_context`) | Flow reachability |

---

## State Variants

Every screen defines state variants covering these scenarios:

| Variant | Purpose | Required? |
|---------|---------|-----------|
| `empty` | No data to display; guide user to action | Yes (base) |
| `loading` | Data being fetched; prevent interaction confusion | Yes (base) |
| `error` | Operation failed; provide recovery path | Yes (base) |
| `success` | Operation completed; confirm and guide next | Yes (base) |
| `offline` | Network unavailable; show cached data or offline message | Recommended for mobile |
| Business states | Context-dependent (pending, processing, expired, etc.) | At least 1 per screen |

---

## Interaction Gate Score Feedback

After experience-map generation, `interaction-gate` evaluates each operation line on 4 dimensions:

| Dimension | Weight | Evaluates |
|-----------|--------|-----------|
| `step_count` | 30pts | Fewer steps = higher score; deducted past reasonable threshold |
| `context_switches` | 25pts | Fewer role/page/modal switches = higher score |
| `wait_feedback` | 25pts | Async operations with clear wait states and feedback = higher score |
| `thumb_zone` | 20pts | Mobile high-frequency actions reachable by thumb = higher score |

**Total**: 0-100. **Default threshold**: 70. Below threshold -> `fail`.

**Feedback mechanism**:
1. Interaction-gate writes `quality_score` into each operation line in experience-map.json
2. Failed lines require user decision: adjust the design or accept the score
3. In auto-mode, lines scoring < 50 still require human confirmation (severe UX defects)

**Consumer-mode additional checks** (when `experience_priority.mode = consumer | mixed`):
- **Mainline clarity**: Can the user know the core goal within 2 seconds?
- **Next-step guidance**: After current action, does the user know what's next?
- **Retention hooks**: Does the flow include return/continuous-use cues?
- **Low-attention adaptation**: Does mobile scenario require excessive memory or back-and-forth?

---

## Relationship to Upstream Journey-Emotion

```
journey-emotion-map.json           experience-map.json
├── journey_lines[]           -->  ├── operation_lines[]
│   ├── id: JL01              -->  │   ├── source_journey: JL01
│   ├── role: R001            -->  │   ├── role: R001
│   └── emotion_nodes[]       -->  │   └── nodes[].screens[]
│       ├── emotion           -->  │       ├── emotion_design.source_emotion
│       ├── design_hint       -->  │       ├── emotion_design.source_hint + design_response
│       ├── intensity         -->  │       ├── influences interaction_density + visual_tone
│       └── risk              -->  │       └── influences states + error prevention patterns
```

**Mapping rules**:
- Every `journey_line` must produce at least one `operation_line` (completeness check)
- `emotion_nodes[].emotion` and `design_hint` flow into screen `emotion_design` fields
- `risk=high/critical` nodes must produce screens with explicit error prevention, confirmation flows, and reversibility
- Emotion arc across a journey line (e.g., anxious -> satisfied -> delighted) must be visible in the screen sequence's progressive design -- not all screens tonally identical
- Journey-emotion quality directly determines experience-map validation precision: if all emotions are neutral/intensity=3, the validation baseline has no signal

**Validation loop** (experience-map Step 3):
LLM loads journey-emotion-map.json alongside experience-map.json and checks:
1. **Emotion intent landed?** -- design_hint reflected in emotion_design and interaction_pattern
2. **High-risk nodes protected?** -- error prevention, confirmation, reversibility present
3. **Emotion arc coherent?** -- interface sequence shows progressive experience
4. **Journey lines complete?** -- every journey_line has a corresponding operation_line

---

## interaction_type Renderer Support List

Screens must select from this list. Free design intent goes in `description` and `interaction_pattern`.

| Type | Name | Layout Slots | Use For |
|------|------|-------------|---------|
| **MG1** | Read-only list | header, filter-chips, read-only-list, pagination | Browse-only lists, logs |
| **MG2-L** | CRUD list | header, search-bar, filter-chips, table, pagination, action-bar | Data tables with CRUD |
| **MG2-C** | Create form | header, form-body, field-group, action-bar | New entity forms |
| **MG2-E** | Edit form | header, form-body, field-group, action-bar | Edit entity forms |
| **MG2-D** | Detail page | header, detail-fields, action-bar | Read-only entity detail |
| **MG2-ST** | State transition | header, detail-fields, state-badge, action-bar | Approval/rejection triggers |
| **MG3** | State machine list | header, state-tabs, table, action-bar | Status-tabbed list + inline actions |
| **MG4** | Approval queue | header, pending-badge, approval-cards, action-bar | Pending/approved queues |
| **MG5** | Master-detail | header, master-info, sub-tabs, sub-list | Parent entity + child tabs |
| **MG6** | Tree management | header, tree-toolbar, tree-view | Hierarchical CRUD |
| **MG7** | Dashboard | header, kpi-cards, charts, date-filter | KPIs + charts |
| **MG8** | Config page | header, config-sections, save-bar | Grouped settings |
| **SY1** | Onboarding | illustration, step-content, dots, action-bar | Step-by-step guide |
| **SY2** | Wizard form | progress-steps, form-body, action-bar | Multi-step forms |
| **CT1** | Content feed | search-bar, filter-chips, feed-cards | Searchable card feeds |
| **CT2** | Content reader | cover-image, title, meta, body-content, action-bar | Immersive reading, chat |
| **CT3** | Profile page | avatar-header, profile-fields, action-bar | User profile |
| **CT4** | Card flip | progress, card-main, action-buttons | Swipe/flip per-item review |
| **CT5** | Media player | player-screen, progress-bar, controls | Audio/video playback |
| **CT6** | Gallery | gallery-grid, action-bar | Image grid + lightbox |
| **CT7** | Search results | search-bar, filter-chips, results-list, pagination | Search + filter + results |
| **EC1** | Item detail | product-image, title-price, specs, features, action-bar | Product/pricing page |
| **EC2** | Checkout | item-list, total, payment-options, action-bar | Cart/payment flow |
| **WK3** | Document editor | editor-toolbar, editor-area, preview, status-bar | Dual-pane editor |
| **SB1** | Submit form | form-body, action-bar | Feedback/report/apply |
| **RT4** | Notification center | notif-tabs, notif-list | Categorized notifications |

**Selection guide**:
- Chat/conversation -> **CT2** (body-content renders chat bubbles)
- Workspace/editor -> **WK3** (editor-area + preview dual-pane)
- Dashboard/monitoring -> **MG7** (KPI + charts)
- AI generation flow -> **SY2** (wizard) or **SB1** (submit + result)
- Approval workspace -> **MG4** or **MG3**
- Log viewer -> **MG1**
- Registration/login -> **MG2-C**
- Subscription/payment -> **EC1** + **EC2**

---

## Backend Screen Archetype (multi_function_per_page)

For professional roles with `screen_granularity = "multi_function_per_page"`:

**Core principle**: Same-entity CRUD operations merge into **one screen** with different `view_modes`.

| Aspect | Backend (multi_function) | Frontend (single_task) |
|--------|------------------------|----------------------|
| Same-entity CRUD | One screen: list + modal create + detail panel + inline ops | Multiple screens with navigation |
| Create action | Same-page modal/drawer | Independent full-screen form |
| Detail view | Side panel, list remains visible | Independent full-screen page |
| Batch operations | Checkboxes + batch action bar | Rare, per-item |
| Navigation | Sidebar menu, content area switches | Depth navigation, bottom tabs |
| Data density | High-density tables, multi-column, compact | Low-density cards, whitespace |

**Merge algorithm** (LLM must execute for backend roles after skeleton generation):
1. Identify same-entity screens (entity-model reference)
2. Merge list/create/edit/detail/status-change into one screen
3. Convert original interaction_types to view_modes
4. Merged screen's interaction_type = list type (MG2-L or MG3), tasks = union of all original tasks

---

## Layout Differentiation Principle

`interaction_type` is the renderer's template selector, **not the screen's design identity**. Same interaction_type must produce different layouts for different business purposes.

**Business Purpose Three Questions** (answer before designing each screen):

| Question | Determines |
|----------|-----------|
| 1. User's **core purpose** at this screen? | Primary vs secondary region split |
| 2. What **information structure** serves this purpose? | Component organization |
| 3. How does this info structure organize in **physical space**? | layout_type selection |

**Self-check after batch generation**:
1. No single `layout_type` > 15% of total screens -- review if exceeded
2. Same `interaction_type` screens with component jaccard similarity > 50% must justify
3. `layout_type` must never copy `interaction_type` names

---

## Consumer Maturity Patterns (experience_priority.mode = consumer | mixed)

LLM evaluates which patterns apply per product (not a checklist):

| Pattern | Description | Screen Type |
|---------|-------------|-------------|
| First-run onboarding | Goal setting / preference collection | onboarding wizard |
| Personalized main line | Dynamic home based on user state | smart home / today feed |
| Process experience | Real-time progress, interactive stages | live tracking / challenge |
| Completion ritual | Celebration / review / share after core action | completion / review |
| Streak/achievement | Consecutive use, milestones, levels | streak / achievements |
| Smart reminders | Behavior-based push notifications | notification center |
| Social layer | Follow / feed / compare / challenge | social feed |
| Progress dashboard | Long-term goal visualization | progress dashboard |
| Immersive consumption | Full-screen distraction-free content | immersive reader / player |
| Creator tools | In-app creation with preview and undo | canvas / editor |
| Decision funnel | Multi-step decisions with reinforcement | cart -> checkout -> confirm |

**Applicability test**: Would the user see this pattern as making the product more professional or less credible? Match pattern tone to product domain.
