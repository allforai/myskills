# Wireframe Quality Upgrade — Data Model + 4D/6V/XV

> Design approved 2026-03-09

## Problem

The wireframe review server generates extremely rough wireframes — every screen shows a single gray "Content Area" box regardless of type. Screen names are generic (`{module}_screen`), descriptions are empty, no real data fields. Users cannot understand screen intent, leading to expensive late-stage requirement changes.

## Solution: 4-Layer Upgrade

### Layer 1: Data Modeling (product-map Step 7 + Step 8)

Insert two new steps into product-map, renumber validation to Step 9.

**Step 7 — Entity Model + API Contracts:**
- Input: task-inventory.json, business-flows.json, constraints.json, role-profiles.json
- Infer entities from task module groupings
- Extract fields from task names (nouns = fields, verbs = operations)
- Derive state machines from business-flow node sequences
- Generate API endpoints from task CRUD types + entity state transitions
- Output: `entity-model.json`, `api-contracts.json`, `data-model-report.md`

**Step 8 — View Objects (VO):**
- Input: entity-model.json, api-contracts.json, task-inventory.json
- Each task CRUD × entity → one VO (ListItemVO, DetailVO, CreateFormVO, EditFormVO, StateActionVO)
- Each VO field has: name, label, type, input widget, display format, required/optional, constraints
- Each VO has Action Bindings: buttons/links with full behavior chains
- Output: `view-objects.json`

**Action Binding structure per button/link:**
```json
{
  "id": "ACT001",
  "label": "button text",
  "type": "navigate | api_call | local_storage | composite",
  "trigger": "button | row_click | row_action | swipe | toolbar_button | fab",
  "precondition": {"field": "status", "op": "eq", "value": "paid"},
  "confirm": {"title": "...", "message": "..."},
  "input_form": {"fields": [...]},
  "api_ref": "API008",
  "api_params": {"id": "$row.id", "body": {"tracking_no": "$input.tracking_no"}},
  "on_success": {"action": "refresh_row", "toast": "...", "state_transition": {"from": "...", "to": "..."}},
  "on_error": {"action": "show_error"},
  "style": "primary | secondary | danger | ghost",
  "frequency": "high | medium | low"
}
```

**Action types:**
| type | key fields |
|------|-----------|
| navigate | target_screen, params, nav_mode, data_load |
| api_call | api_ref, api_params, on_success, on_error |
| local_storage | storage_op (target, method, value) |
| composite | steps[] (sequential sub-actions) |

**interaction_type inference from VO (not keyword guessing):**
| VO view_type | condition | interaction_type |
|---|---|---|
| list_item | no row_actions | MG1 |
| list_item | has row_actions | MG2-L |
| create_form | — | MG2-C |
| edit_form | — | MG2-E |
| detail | — | MG2-D |
| state_action | — | MG3 |
| approval | — | MG4 |
| list_item + detail combo | — | MG5 |
| dashboard aggregation | multi-entity readonly | MG7 |
| settings | key-value config | MG6 |

### Layer 2: data-model-review (New Review Gate)

Mind map review server on port 18904, same pattern as concept-review/map-review.

**Tree structure:**
```
root (数据模型)
├── Entity (E001 订单)
│   ├── 字段 group
│   │   ├── id: uuid (PK)
│   │   ├── status: enum [...] ✱必填
│   │   └── ...
│   ├── 状态机 group
│   │   ├── pending → paid (支付)
│   │   └── ...
│   ├── 接口 group
│   │   ├── GET /orders (列表)
│   │   ├── POST /orders (创建)
│   │   └── ...
│   └── 视图 group
│       ├── OrderListItem (VO001, MG2-L)
│       │   ├── field nodes (display format)
│       │   └── action nodes (binding details)
│       └── ...
├── Entity (E002 商品)
│   └── ...
└── 关系 (global)
    ├── 订单 1:N 商品项
    └── ...
```

**Node types:** root, entity, field-group, field, field-pk, field-fk, field-required, state-machine, transition, api-group, api, vo-group, vo, vo-field, action, relation-group, relation

**Feedback categories:** entity, api, vo, action, state-machine, product-map

**Feedback routing:**
- entity/api/state-machine → fix entity-model.json → re-run Step 7
- vo/action → fix view-objects.json → re-run Step 8
- product-map → go back to product-map → re-run full chain

### Layer 3: experience-map Consumes VO

Changes to `gen_experience_map.py`:
- Load view-objects.json (new dependency, optional fallback to current behavior)
- Match screen tasks → VO via source_tasks
- Screen fields populated from VO.fields (real data, not guessed)
- Screen name = VO.name_zh
- interaction_type = derived from VO.view_type
- flow_context = prev/next from operation line sequence
- states = from interaction_type defaults + VO customization

New screen fields:
```json
{
  "vo_ref": "VO001",
  "api_ref": "API001",
  "interaction_type": "MG2-L",
  "data_fields": [...],
  "flow_context": {"prev": [...], "next": [...], "entry_points": [...], "exit_points": [...]},
  "states": {"empty": "...", "loading": "...", "error": "...", "success": "..."}
}
```

### Layer 4: Wireframe Rendering (4D + 6V + XV)

**4A — Interaction-type templates:**

Each type family gets a distinct wireframe HTML template rendering real VO fields:

- MG1 (readonly list): search + filter chips + table headers from VO.fields + sample rows + pagination
- MG2-L (CRUD list): search + "New" button + filter + table with action column + pagination
- MG2-C (create form): form fields with labels, input types, required indicators from VO
- MG2-E (edit form): same as C with "prefill" indicators
- MG2-D (detail): field-value pairs in sections + action buttons
- MG3 (state machine): status tabs from entity state_machine + list + conditional action buttons
- MG4 (approval): pending count + queue cards + approve/reject buttons
- MG5 (master-detail): split layout
- CT/EC/WK/RT: content/commerce/collaboration templates
- Default fallback: enhanced current template

All templates show action buttons with API binding annotations (method + path + state transition).

**4B — 4D Panel (wireframe bottom):**
```
Data    — VO field names + R/W indicators
Action  — Action labels + API refs + frequency
State   — empty/loading/error/success descriptions
Flow    — prev screens ← current → next screens
```

**4C — 6V Tabs (detail page side panel):**
| Tab | Content |
|-----|---------|
| Structure | Screen sections from interaction_type template |
| Behavior | Interaction type details from interaction-types.md |
| Data | VO field list: name, type, required, input widget, display format |
| State | 4 state variants with key UI differences |
| Flow | Entry/exit points, prev/next screen links |
| Emotion | Emotion state, intensity, UX intent, non-negotiable, design hints |

**4D — XV Cross-validation (if OPENROUTER_API_KEY available):**
- wireframe_usability_review (gemini): per-screen usability issues
- wireframe_completeness_check (deepseek): missing screens/fields/coverage gaps
- wireframe_consistency_check (gpt): naming/type inconsistencies across screens
- Results shown as badge counts on dashboard cards + "XV Review" tab in detail page

## Pipeline After Changes

```
/product-concept → /concept-review (18900)
→ /product-map (Step 0–9) → /map-review (18901)
→ /journey-emotion → /experience-map (VO-bound) → /wireframe-review (18902, 4D+6V+XV, optional data-model-review 18904)
→ /use-case | /feature-gap | /feature-prune | /ui-design → /ui-review (18903)
→ /design-audit
```

## Output Files

### New files in .allforai/product-map/
- entity-model.json (Step 7)
- api-contracts.json (Step 7)
- data-model-report.md (Step 7)
- view-objects.json (Step 8)

### New files in .allforai/data-model-review/
- review-feedback.json

### New files in .allforai/wireframe-review/
- xv-review.json

### Modified files in .allforai/experience-map/
- experience-map.json (screens gain vo_ref, data_fields, interaction_type, flow_context, states)

## Code Changes

| File | Change |
|------|--------|
| `scripts/gen_data_model.py` | **NEW** — Step 7 entity + API inference |
| `scripts/gen_view_objects.py` | **NEW** — Step 8 VO generation with Action Bindings |
| `scripts/datamodel_review_server.py` | **NEW** — mind map review server (port 18904) |
| `commands/data-model-review.md` | **NEW** — /data-model-review command |
| `docs/schemas/data-model-schema.md` | **NEW** — entity/api/vo schema docs |
| `scripts/gen_experience_map.py` | **MODIFY** — consume VOs, bind real fields |
| `scripts/wireframe_review_server.py` | **MODIFY** — type-specific templates + 4D + 6V + XV |
| `scripts/_common.py` | **MODIFY** — new loaders + port constant |
| `skills/product-map.md` | **MODIFY** — add Step 7/8, renumber Step 9 |
| `skills/experience-map.md` | **MODIFY** — document VO consumption |
| `skills/wireframe-review.md` | **MODIFY** — document 4D/6V/XV |
| `SKILL.md` | **MODIFY** — update pipeline description |
