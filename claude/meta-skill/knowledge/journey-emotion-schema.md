# Journey Emotion Schema

> Extracted from product-design-skill: journey-emotion.md + docs/schemas/journey-emotion-schema.md

---

## Purpose

Maps emotional states onto business flow nodes. Takes `business-flows.json` and `role-profiles.json` as input, produces a journey emotion map that serves as both human-readable validation artifact and machine-consumable baseline for experience-map validation.

Output file: `.allforai/experience-map/journey-emotion-map.json`

---

## Full JSON Schema

```json
{
  "journey_lines": [
    {
      "id": "JL01",
      "name": "string — journey line description",
      "role": "string — single role ID (e.g. R001)",
      "source_flow": "string — reference to business-flow ID (e.g. F001)",
      "emotion_nodes": [
        {
          "step": "integer — sequential step number within this journey line",
          "action": "string — user action description",
          "role": "string — role ID of the actor at this step (must match parent journey_line.role)",
          "emotion": "string — one of 6 values: delighted | satisfied | neutral | frustrated | anxious | angry",
          "intensity": "integer — 1 to 8 scale",
          "risk": "string — one of 4 values: low | medium | high | critical",
          "design_hint": "string — required, 1-2 sentences, specific actionable design strategy",
          "source_refs": "array (optional) — D2 evidence sources for risk=high/critical nodes",
          "reasoning": "string (optional) — D4 explanation: why this emotion and not another"
        }
      ],
      "human_decision": "boolean — whether human confirmation was obtained"
    }
  ],
  "decision_log": [
    {
      "step": "string — workflow step reference (e.g. 'Step 3')",
      "flow_id": "string — business flow ID",
      "flow_name": "string — business flow name",
      "node_seq": "integer — emotion_node step number",
      "field": "string — which field was changed (emotion | intensity | risk | design_hint)",
      "original_value": "string — LLM-generated value",
      "new_value": "string — user-adjusted value",
      "decision": "string — modified | confirmed | auto_confirmed",
      "reason": "string — human rationale for the change",
      "decided_at": "string — ISO 8601 timestamp"
    }
  ],
  "generated_at": "string — ISO 8601 timestamp"
}
```

---

## Field Definitions

### journey_lines[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Format: `JL01`, `JL02`, ... Sequential ID. Cross-role splits use suffix: `JL01a`, `JL01b` |
| `name` | string | yes | Human-readable journey line description |
| `role` | string | yes | Single role ID. Each journey_line belongs to exactly one role |
| `source_flow` | string | yes | Reference to the originating business-flow ID. Multiple journey_lines can share the same source_flow (cross-role splits) |
| `emotion_nodes` | array | yes | Ordered array of emotion node objects |
| `human_decision` | boolean | yes | True after user reviews and confirms this line |

### emotion_nodes[]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step` | integer | yes | Sequential step number within this journey line |
| `action` | string | yes | Description of the user action at this step |
| `role` | string | yes | Role ID of the actor (must match parent `journey_line.role`) |
| `emotion` | string | yes | One of 6 emotion values (see vocabulary below) |
| `intensity` | integer | yes | 1-8 scale (see levels below) |
| `risk` | string | yes | One of 4 risk levels (see below) |
| `design_hint` | string | yes | 1-2 sentences of specific, actionable design strategy. Never empty |
| `source_refs` | array | optional | D2 evidence sources (URLs, research citations) for risk=high/critical nodes |
| `reasoning` | string | optional | D4 rationale: why this emotion was chosen over alternatives |

---

## Emotion Vocabulary (6 values)

| Value | Meaning | Typical Triggers |
|-------|---------|------------------|
| `delighted` | Joy, excitement, positive surprise | Core value delivery, achievement unlocked, unexpected reward |
| `satisfied` | Content, accomplished, calm positive | Task completed successfully, clear progress visible |
| `neutral` | Neither positive nor negative | Routine browsing, information viewing, low-stakes navigation |
| `frustrated` | Blocked, confused, struggling | Complex forms, unclear error messages, dead ends |
| `anxious` | Worried, uncertain, stressed | Payment, waiting for results, irreversible actions |
| `angry` | Irritated, hostile, strong negative | Data loss, repeated failures, unfair treatment, broken promises |

---

## Intensity Scale (8 levels, 1-8)

| Level | Label | Description |
|-------|-------|-------------|
| 1 | Barely perceptible | Almost no emotional reaction; purely mechanical interaction |
| 2 | Faint | Slight emotional coloring; user barely notices |
| 3 | Mild | Noticeable but not impactful; default for routine actions |
| 4 | Moderate | Clearly felt; user is aware of the emotional state |
| 5 | Pronounced | Affects user behavior; may cause hesitation or engagement |
| 6 | Strong | Significantly impacts decision-making; may trigger abandonment or loyalty |
| 7 | Intense | Dominates the experience; user will remember this moment |
| 8 | Overwhelming | Extreme reaction; defines the user's perception of the entire product |

**Distribution rule**: Intensity values should NOT cluster in the "safe zone" of 3-5. A well-annotated journey has a natural distribution reflecting actual scenario context -- peaks at value delivery, valleys at friction points.

---

## Risk Levels (4 values)

| Value | Meaning | Examples | Auto-mode behavior |
|-------|---------|---------|-------------------|
| `low` | Minimal impact if things go wrong | Browsing, viewing, casual navigation | Auto-confirmed |
| `medium` | Some friction or confusion possible | Form filling, navigation, content selection | Auto-confirmed |
| `high` | Significant user impact, possible churn | Payment, data submission, long async waits | Auto-confirmed |
| `critical` | Involves money, data deletion, or permission changes | Payment processing, account deletion, role/permission changes | **Must stop for human confirmation** even in auto-mode |

---

## Emotion Cliff Detection

**Definition**: Adjacent nodes with intensity difference >= 4 constitute an "emotion cliff" -- the experience feels broken to the user.

**Detection rule**: For each pair of adjacent `emotion_nodes` (step N and step N+1), check:
```
|intensity[N] - intensity[N+1]| >= 4  -->  WARNING
```

**Warning format**:
```
WARNING: Emotion cliff: Node N01 -> N02 (intensity 8 -> 3).
Experience may feel broken. Confirm if reasonable or add intermediate nodes.
```

**Resolution options**:
1. Insert intermediate nodes to smooth the transition
2. Adjust intensity values at the adjacent nodes
3. Accept the cliff with explicit human confirmation (some business scenarios legitimately produce sharp transitions, e.g., "payment confirmed" -> "waiting for delivery")

---

## Cross-Role Flow Splitting Rules

Each `journey_line` belongs to a **single role** (`role` field is single-valued).

When a business flow has `type: cross_role`, it must be split by participating roles into multiple journey_lines:

**Splitting algorithm**:
1. Identify all unique roles that act as `actor` in the business flow's nodes
2. For each role, create a separate journey_line containing only nodes where that role is the actor
3. Assign IDs with suffix: `JL01a`, `JL01b`, etc.
4. All split lines share the same `source_flow` value

**Example**: F001 (R2 generates -> R2 reviews -> R2 publishes -> R1 browses) splits into:
- `JL01a` (role=R2, source_flow=F001): Generate -> Review -> Publish
- `JL01b` (role=R1, source_flow=F001): Browse new content

**Post-split rules**:
- Each line independently evaluates its emotion arc and Peak-End Rule
- Lines with same `source_flow` but different `role` can be correlated back to the original cross-role flow by downstream tools
- Emotion arcs are evaluated per-line, not across the combined flow

---

## Emotion Inference Dimensions

LLM reasons about emotions using these dimensions (never fills defaults):

| Dimension | Guidance | Examples |
|-----------|----------|---------|
| **Psychological load of the action** | What cognitive/emotional burden does this action impose? | Form filling -> neutral; Payment -> anxious; Completing learning -> satisfied; Waiting for approval -> anxious |
| **Role's usage frequency** | How often does this role perform this action? | High-frequency operations should feel smoother (lower anxiety); low-frequency operations allow more guidance |
| **Position in business flow** | Where in the flow does this step sit? | Beginning = usually neutral; Climax (core value delivery) = usually delighted; Ending = needs positive closure (Peak-End Rule) |
| **Risk level** | What can go wrong and how bad is it? | Money/data deletion/permission changes -> risk increases; browsing/viewing -> risk stays low |
| **Design hint derivation** | What specific design strategy addresses this emotion? | Must give concrete suggestions, never abstract principles |

---

## Design Hints Derived from Emotion Patterns

When generating `design_hint`, LLM should apply these pattern-based strategies:

| Emotion Pattern | Design Strategy |
|----------------|-----------------|
| `anxious` + `intensity >= 5` | Add trust signals (security badges, brand logos), show progress indicators, provide clear reversibility messaging |
| `frustrated` + `intensity >= 5` | Simplify the interface, reduce required fields, add inline help, show clear error recovery paths |
| `angry` (any intensity) | Prioritize immediate resolution paths, provide human support escalation, acknowledge the problem explicitly |
| `delighted` + `intensity >= 6` | Design a celebration moment (completion animation, share prompt), reinforce the positive outcome |
| `neutral` sustained across 3+ nodes | Introduce micro-moments of delight to prevent monotony; add progress indicators to show advancement |
| Transition `anxious -> satisfied` | Design the transition point carefully: confirmation screen, success animation, "what happens next" clarity |
| Transition `neutral -> frustrated` | Pre-empt with guidance: contextual help, input validation, progressive disclosure |
| emotion cliff (diff >= 4) | Add buffering nodes: progress feedback, intermediate confirmations, "almost there" messaging |

---

## How Experience-Map Uses This as Validation Baseline

Journey-emotion output is the **validation baseline** for experience-map. During experience-map Step 3 validation loop, LLM loads `journey-emotion-map.json` and reviews the design output against four criteria:

1. **Did emotion intent land?** -- Each `emotion_node`'s `design_hint` should be substantively reflected in the corresponding screen's `emotion_design` and `interaction_pattern`. Not literal copying -- judge whether the design responds to the emotional need.

2. **Do high-risk nodes have protection?** -- `risk=high/critical` nodes: does the corresponding screen design include error prevention, confirmation dialogs, and reversibility?

3. **Is the emotion arc coherent?** -- The emotion transitions (e.g., anxious -> delighted) across an operation line: does the interface sequence show a corresponding experience progression? Or are all interfaces tonally identical?

4. **Are journey lines complete?** -- Does every `journey_line` have a corresponding `operation_line` in experience-map?

**Failure -> LLM corrects the corresponding screen -> re-validate (loop)**

The quality of journey-emotion annotations directly determines the precision of experience-map validation. Specific emotion annotations enable the validator to catch "design did not respond to emotional need" issues. If all emotions are neutral/intensity=3, the baseline has no signal and validation becomes meaningless.

---

## Schema Constraints Summary

| Constraint | Rule |
|-----------|------|
| Top-level key | Must be `journey_lines` (array), not `journeys` |
| Child node key | Must be `emotion_nodes` (array), not `nodes` |
| `source_flow` | Required on every journey_line |
| Role consistency | All `emotion_nodes` within a journey_line must have the same role as the parent `role` field |
| Emotion values | Must be context-based inference, not all neutral |
| `design_hint` | Required, never empty, must be actionable |
| Auto-mode critical | `risk=critical` nodes must stop for human confirmation even in auto-mode |
| Intensity distribution | Should not cluster in 3-5 safe zone |
