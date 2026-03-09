# Pipeline Data Flow Unification — Design

## Problem

Each `gen_*.py` script is an island — it reads only its direct inputs (product-map + experience-map) and ignores sibling artifacts. This causes:

1. **Artifact isolation**: gen_ui_design doesn't read entity-model / api-contracts / view-objects / behavioral-standards / pattern-catalog, so UI and data model are disconnected.
2. **XV result waste**: xv-review.json files are written but never consumed downstream.
3. **Review feedback dead-end**: review-feedback.json produces text suggestions but doesn't inject constraints into the next generation round.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Loading strategy | One-shot full load | All JSON files < 2MB total; lazy loading adds complexity for no gain |
| Constraint file layout | Per-tab split files | Git-friendly diffs; clear ownership; no write conflicts |
| Constraint lifecycle | Manual clear (auto on all-approved) | Human constraints stay active until human is satisfied |
| XV consumption | Collect all `*-xv-review.json` | high=warning, critical=constraint-level, low/medium=audit-only |

## Module 1: `load_full_context()` in `_common.py`

### Interface

```python
class FullContext:
    tasks: dict          # {id: task} from task-inventory.json
    roles: dict          # {id: name} from role-profiles.json
    flows: list          # from business-flows.json
    entity_model: dict   # from entity-model.json (or None)
    api_contracts: list  # from api-contracts.json (or [])
    view_objects: list   # from view-objects.json (or [])
    experience_map: dict # from experience-map.json (or None)
    screens: dict        # {id: screen} extracted from experience_map
    interaction_gate: dict  # from interaction-gate.json (or None)
    pattern_catalog: dict   # from pattern-catalog.json (or None)
    behavioral_standards: dict  # from behavioral-standards.json (or None)
    concept: dict        # from product-concept.json (or None)
    xv_findings: list    # collected from all *-xv-review.json
    constraints: list    # collected from constraints/*.json

    def get_constraints(self, target: str) -> list:
        """Filter constraints by target (e.g. 'ui-design')."""

    def get_xv_findings(self, source_phase: str) -> list:
        """Filter XV findings by source phase."""

    def vo_for_screen(self, screen_id: str) -> list:
        """Match view objects to a screen via its task refs."""

    def api_for_screen(self, screen_id: str) -> list:
        """Match API endpoints to a screen via its task refs."""


def load_full_context(base) -> FullContext:
    """One-shot load of all generated artifacts."""
```

### What it does NOT do

- Does not replace existing specialized loaders (`load_task_inventory` etc.)
- Does not validate data (that's design-audit's job)
- Does not change script input/output contracts

## Module 2: `constraints/` directory

### File layout

```
.allforai/constraints/
├── concept.json
├── map.json
├── wireframe.json
├── ui.json
├── data-model.json
└── spec.json
```

### Constraint entry format

```json
{
  "source_tab": "wireframe",
  "created_at": "2026-03-09T...",
  "constraints": [
    {
      "id": "wireframe_pin_003",
      "target": "ui-design",
      "screen_id": "S005",
      "category": "layout",
      "constraint": "Login button must be at page bottom for thumb reach",
      "severity": "must"
    }
  ]
}
```

### ID generation

`{tab}_{pin_id}` or `{tab}_{node_id}` — idempotent, re-processing same feedback produces same IDs.

### Target enum

`product-concept`, `product-map`, `experience-map`, `ui-design`, `use-case`, `feature-gap`, `feature-prune`

### Cleanup

Tab all-approved → delete that tab's constraint file. All files gone = zero constraints.

## Module 3: Script consumption plan

### gen_ui_design.py (biggest beneficiary)

| Source | Injection point | Effect |
|--------|----------------|--------|
| `ctx.view_objects` | screen sections/layout | Form field names from VO, not guessed |
| `ctx.entity_model` | field types, required/optional | Form input types align with entity definitions |
| `ctx.api_contracts` | action button bindings | Button labels match API endpoint names |
| `ctx.behavioral_standards` | loading/error/empty states | Unified behavior standards injected per screen |
| `ctx.pattern_catalog` | screen layout patterns | MG2-L screens reference PT-CRUD layout suggestions |
| `ctx.get_constraints("ui-design")` | hard override | Human review requirements enforced |
| `ctx.xv_findings` | warning comments | XV issues annotated in spec |

### gen_ui_stitch.py (prompt enhancement)

| Source | Injection point | Effect |
|--------|----------------|--------|
| `ctx.vo_for_screen(sid)` | Prompt Layer 2 | "Data fields: username(string, required)" from VO |
| `ctx.api_for_screen(sid)` | Prompt Layer 2 | "API: POST /users → loading → success/error" |
| `ctx.behavioral_standards` | Prompt Layer 1 | "Loading: skeleton screen, not spinner" |
| `ctx.get_constraints("ui-design")` | Highest priority layer | "MUST: login button at bottom" |

### gen_use_cases.py (boundary conditions from entity model)

| Source | Injection point | Effect |
|--------|----------------|--------|
| `ctx.entity_model` | validation rules | "Username length 2-50" from entity constraints |
| `ctx.api_contracts` | when_steps | API call steps match real endpoints |
| `ctx.get_constraints("use-case")` | hard override | Human-specified use case adjustments |

### gen_feature_gap.py (coverage checks)

| Source | Injection point | Effect |
|--------|----------------|--------|
| `ctx.entity_model` | entity coverage check | "Order entity has 6 fields, UI shows 3" |
| `ctx.api_contracts` | API coverage check | "5 of 34 endpoints unreferenced by any screen" |
| `ctx.get_constraints("feature-gap")` | hard override | Human-marked "not a gap" |

### gen_interaction_gate.py (XV consumption)

| Source | Injection point | Effect |
|--------|----------------|--------|
| `ctx.xv_findings` | gate score adjustment | XV usability issues lower node gate scores |

### gen_feature_prune.py, gen_design_audit.py

Add `ctx = C.load_full_context(base)`, consume constraints. gen_design_audit already reads most artifacts, only needs constraint reading.

## Module 4: XV result propagation

### Collection

`load_full_context()` scans `.allforai/` for all `*-xv-review.json` files, normalizes into:

```python
{
    "source_phase": "experience-map",
    "task_type": "wireframe_usability_review",
    "severity": "high",
    "finding": "S005 login page missing password visibility toggle",
    "screen_id": "S005",
}
```

### Consumption rules

- `severity=high` → downstream scripts treat as warning (written to output, not blocking)
- `severity=critical` → constraint-level (equivalent to human constraint)
- `severity=low/medium` → only surfaced in design-audit summary

### What it does NOT do

- Does not change existing XV call logic (scripts continue calling XV independently)
- Does not auto-convert XV findings to constraints (avoids AI overriding human intent)

## Module 5: `/review process` constraint generation

### Flow

```
/review process <tab>
  → read <tab>-review/review-feedback.json
  → filter needs_revision entries
  → analyze target per comment (pin category / node type)
  → write constraints/<tab>.json (idempotent IDs)
  → output human-readable fix suggestions (existing behavior)
  → print "Written N constraints to constraints/<tab>.json"
```

### Cleanup flow

```
/review process <tab>
  → all approved → delete constraints/<tab>.json
  → print "<tab> review all passed, constraints cleared"
```
