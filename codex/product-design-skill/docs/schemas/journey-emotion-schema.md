# Journey Emotion Map Schema

> Output: `.allforai/experience-map/journey-emotion-map.json`

**强制约束**：顶层 key 必须是 `journey_lines`（不可用 `journeys`），子节点 key 必须是 `emotion_nodes`（不可用 `nodes`），每个 journey_line 必须有 `source_flow` 字段引用 business-flow ID。`_common.py` 会尝试兼容变体格式，但脚本输出应遵循规范。

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
