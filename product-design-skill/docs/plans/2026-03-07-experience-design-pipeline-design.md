# Experience Design Pipeline Redesign

> Date: 2026-03-07
> Status: Approved
> Scope: product-design-skill full pipeline restructure

## Goal

Transform the product-design pipeline from a feature-checklist approach to an experience-design approach. Replace screen-map with experience-map organized by operation lines, add journey-emotion-map as a human-decision prerequisite, and add an independent interaction quality gate.

## New Pipeline

```
Phase 1  product-concept              (unchanged)
Phase 2  product-map                  (unchanged)
Phase 3  journey-emotion-map          [NEW] human decision point
Phase 4  experience-map               [REPLACES screen-map]
Phase 4.5 interaction-quality-gate    [NEW] independent quality gate
Phase 5  use-case // feature-gap // ui-design  (parallel, input changed to experience-map)
Phase 6  feature-prune                (optional manual)
Phase 7  design-audit                 (upgraded audit dimensions)
```

No backward compatibility. Full replacement.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| screen-map disposition | A3: rename + restructure in-place | Clean break, no legacy confusion |
| journey-emotion-map placement | Separate Phase 3 before experience-map | Human decision point needs its own step |
| Quality gate placement | Independent Phase 4.5 | Not embedded in experience-map generation |
| Backward compatibility | None | Skill not in production yet |
| screen_index location | Inside experience-map.json | No independent consumption scenario |
| exception_states location | Node-level | Stronger association with operation context |
| non_negotiable format | String array | All items are non-negotiable; priority is meaningless |

## Data Structures

### journey-emotion-map.json

```json
{
  "journey_lines": [
    {
      "id": "JL01",
      "name": "New user registration to first order",
      "role": "R01",
      "emotion_nodes": [
        {
          "step": 1,
          "action": "Open homepage",
          "emotion": "curious",
          "intensity": 3,
          "risk": "Information overload causes confusion",
          "design_hint": "Focus on single CTA"
        }
      ],
      "human_decision": true
    }
  ],
  "decision_log": [
    {
      "line_id": "JL01",
      "user_adjustment": "step 3 intensity raised to 8, added safety-feel design hint",
      "timestamp": "2026-03-07T10:00:00Z"
    }
  ]
}
```

Fields:
- `emotion`: English keyword (curious / anxious / satisfied / frustrated etc.), no enum constraint
- `intensity`: 1-10, drives ui-design visual intensity
- `human_decision`: true = line requires human confirmation before entering experience-map
- `decision_log`: records human adjustments for audit traceability

### experience-map.json (replaces screen-map)

```json
{
  "operation_lines": [
    {
      "id": "OL01",
      "name": "New user first order",
      "source_journey": "JL01",
      "role": "R01",
      "nodes": [
        {
          "seq": 1,
          "id": "N01",
          "action": "Enter homepage",
          "emotion_state": "curious",
          "emotion_intensity": 3,
          "ux_intent": "Guide attention to core value",
          "screens": [
            {
              "id": "S001",
              "name": "Homepage",
              "route_type": "push",
              "non_negotiable": ["Single main CTA", "Core value visible within 3 seconds"]
            }
          ]
        }
      ],
      "continuity": {
        "total_steps": 5,
        "context_switches": 1,
        "wait_points": ["N04-payment-processing"],
        "quality_score": null
      }
    }
  ],
  "screen_index": {
    "S001": {"name": "Homepage", "appears_in": ["OL01.N01", "OL03.N01"]}
  }
}
```

Key structure:
- `operation_lines` is the top-level organizer, each line = one user journey
- `nodes` are operation nodes, each node carries 1-N screens
- `screen_index` maintains global screen ID uniqueness, records where each screen appears
- `exception_states` sink to node level (inside each node)
- `continuity` pre-fills line-level coherence metrics; `quality_score` back-filled by interaction-quality-gate

### interaction-quality-gate output

```json
{
  "gate_result": "pass",
  "lines": [
    {
      "line_id": "OL01",
      "steps": 5,
      "context_switches": 1,
      "wait_feedback_coverage": 1.0,
      "thumb_zone_compliance": 0.85,
      "score": 82,
      "issues": [
        {"node": "N03", "type": "thumb_zone", "detail": "Confirm button outside thumb zone"}
      ]
    }
  ],
  "threshold": 70,
  "recommendation": "pass, 1 issue to address in ui-design"
}
```

## UI Design Upgrade

### New Input Channels (on top of existing product-map)

| Input | Source | Purpose |
|-------|--------|---------|
| `emotion_state` + `intensity` | experience-map node | Visual hierarchy, color emotion, animation intensity |
| `ux_intent` | experience-map node | Component selection and layout strategy |
| `non_negotiable` | experience-map screen | Design constraints written into spec |
| `continuity` | experience-map line | Transition animation and navigation mode |
| `quality_gate.issues` | quality-gate output | Flag interaction issues needing special treatment |

### ui-design-spec.md New Fields (per screen section)

```markdown
## S001 Homepage

**Emotion Context**: curious (3/10) -> Design tone: relaxed exploration, low cognitive load
**Interaction Intent**: Guide attention to core value
**Non-negotiable**: Single main CTA, Core value visible within 3 seconds
**Quality Gate**: No issues

### Layout / Components / Interaction ... (existing content)

**Transition**: -> S002 Product List (push, slide-in from right)
**Continuity Constraint**: 5 steps in this operation line, currently step 1, keep navbar consistent
```

## Script Changes

### New Scripts

| Script | Output | Description |
|--------|--------|-------------|
| `gen_journey_emotion.py` | `journey-emotion-map.json` | Generate emotion journey from role-profiles + business-flows, pause for human confirmation |
| `gen_experience_map.py` | `experience-map.json` (with embedded screen_index) | Replace `gen_screen_map.py`, generate operation line structure from journey-emotion-map + task-inventory |
| `gen_interaction_gate.py` | `interaction-gate.json` | Calculate quality scores from experience-map continuity data, back-fill quality_score |

### Deleted Scripts

| Script | Reason |
|--------|--------|
| `gen_screen_map.py` | Fully replaced by `gen_experience_map.py` |
| `gen_screen_map_split.py` | Split logic merged into `gen_experience_map.py` |

### Modified Scripts

| Script | Changes |
|--------|---------|
| `_common.py` | Add `load_experience_map()`, `load_journey_emotion()`, `build_node_by_id()`; remove `load_screen_map()`, `build_screen_by_id()` |
| `gen_use_cases.py` | Input from experience-map, generate use cases by operation_line |
| `gen_feature_gap.py` | Screen coverage -> operation_line node coverage |
| `gen_feature_prune.py` | Frequency tiering based on operation_line occurrence |
| `gen_ui_design.py` | Core overhaul: receive emotion/ux_intent/non_negotiable/continuity/gate_issues, output upgraded spec |
| `gen_design_audit.py` | Cross-layer trace: node->screen->task, add continuity audit dimension |
| `gen_ui_stitch.py` | Stitch prompt generation includes emotion_state and ux_intent context |
| `gen_ui_components.py` | Component selection references ux_intent |

### Modified Skill Files

| File | Changes |
|------|---------|
| `skills/screen-map.md` | Rename to `skills/experience-map.md`, full rewrite |
| `skills/ui-design.md` | Add emotion/intent/constraint input channels, upgrade output format |
| `skills/design-audit.md` | Add continuity audit dimension, adjust trace logic |
| `skills/use-case.md` | Input reference changed to experience-map |
| `skills/feature-gap.md` | Same |
| `skills/feature-prune.md` | Same |
| `SKILL.md` | Update flow diagram and phase descriptions |
| New: `skills/journey-emotion.md` | Journey-emotion-map generation flow |
| New: `skills/interaction-gate.md` | Quality gate flow |

### Modified Docs

| File | Changes |
|------|---------|
| `docs/schemas/screen-map-schema.md` | Rewrite as `experience-map-schema.md` |
| New: `docs/schemas/journey-emotion-schema.md` | Emotion journey schema |
| New: `docs/schemas/interaction-gate-schema.md` | Quality gate schema |
| `docs/pipeline-analysis.md` | Update flow diagram |
