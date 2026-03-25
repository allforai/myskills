# Interaction Quality Gate Schema

> Output: `.allforai/experience-map/interaction-gate.json`

## Top-Level

| Field | Type | Description |
|-------|------|-------------|
| `gate_result` | string | `pass` or `warn` |
| `lines` | array | Per-line evaluation results |
| `threshold` | integer | Score threshold (default 70) |
| `recommendation` | string | Summary recommendation |
| `generated_at` | string | ISO 8601 timestamp |

## lines[]

| Field | Type | Description |
|-------|------|-------------|
| `line_id` | string | Operation line ID |
| `steps` | integer | Total step count |
| `context_switches` | integer | Context switch count |
| `wait_feedback_coverage` | float | 0.0-1.0 coverage ratio |
| `thumb_zone_compliance` | float | 0.0-1.0 compliance ratio |
| `score` | integer | 0-100 composite score |
| `issues` | array | Issue objects |

## issues[]

| Field | Type | Description |
|-------|------|-------------|
| `node` | string | Node ID or `-` |
| `type` | string | Issue type (step_count, context_switch, thumb_zone) |
| `detail` | string | Human-readable description |

## Scoring Breakdown

| Dimension | Max Points | Criteria |
|-----------|-----------|----------|
| Step count | 30 | ≤7 steps = 30, ≤9 = 20, penalty above |
| Context switches | 25 | ≤2 = 25, penalty above |
| Wait feedback | 25 | Coverage ratio × 25 |
| Thumb zone | 20 | non_negotiable coverage × 20 |
