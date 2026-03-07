# Journey Emotion Map Schema

> Output: `.allforai/experience-map/journey-emotion-map.json`

## Top-Level

| Field | Type | Description |
|-------|------|-------------|
| `journey_lines` | array | Journey lines, each mapping a user flow's emotional arc |
| `decision_log` | array | Human adjustment records |
| `generated_at` | string | ISO 8601 timestamp |

## journey_lines[]

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `JL01`, `JL02`, ... |
| `name` | string | Journey description |
| `role` | string | Role ID |
| `source_flow` | string | Reference to business-flow ID |
| `emotion_nodes` | array | Ordered emotion nodes |
| `human_decision` | boolean | Whether human confirmation is required |

## emotion_nodes[]

| Field | Type | Description |
|-------|------|-------------|
| `step` | integer | Step number |
| `action` | string | User action description |
| `emotion` | string | Emotion keyword (no enum constraint) |
| `intensity` | integer | 1-10 scale |
| `risk` | string | UX risk at this step |
| `design_hint` | string | Design suggestion |

## decision_log[]

| Field | Type | Description |
|-------|------|-------------|
| `line_id` | string | Journey line ID |
| `user_adjustment` | string | Description of human adjustment |
| `timestamp` | string | ISO 8601 timestamp |
