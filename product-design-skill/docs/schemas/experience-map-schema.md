# Experience Map Schema

> Output: `.allforai/experience-map/experience-map.json`

## Top-Level

| Field | Type | Description |
|-------|------|-------------|
| `operation_lines` | array | Operation lines, each representing a user journey |
| `screen_index` | object | `{screen_id: {name, appears_in[]}}` — global screen lookup |
| `generated_at` | string | ISO 8601 timestamp |

## operation_lines[]

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `OL01`, `OL02`, ... |
| `name` | string | Journey description |
| `source_journey` | string | Reference to journey-emotion-map line ID (e.g. `JL01`) |
| `role` | string | Role ID |
| `nodes` | array | Ordered operation nodes |
| `continuity` | object | Line-level coherence metrics |

## nodes[]

| Field | Type | Description |
|-------|------|-------------|
| `seq` | integer | Step sequence number |
| `id` | string | `N0101`, `N0102`, ... (derived from JL ID + step) |
| `action` | string | User action description |
| `emotion_state` | string | Emotion keyword (curious, anxious, satisfied, etc.) |
| `emotion_intensity` | integer | 1-10 scale |
| `ux_intent` | string | Design intent for this node |
| `screens` | array | Screens associated with this node |
| `exception_states` | array | Exception states for this node |

## screens[]

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `S001`, `S002`, ... |
| `name` | string | Screen name |
| `description` | string | Screen purpose |
| `route_type` | string | Navigation type (push, modal, overlay, replace) |
| `tasks` | array | Task IDs referenced by this screen |
| `actions` | array | Action objects with label, crud, frequency, task_ref |
| `primary_action` | string | Primary action label |
| `non_negotiable` | array | String array of design constraints |

## continuity

| Field | Type | Description |
|-------|------|-------------|
| `total_steps` | integer | Number of nodes in this line |
| `context_switches` | integer | Number of context switches |
| `wait_points` | array | Node IDs with wait states |
| `quality_score` | integer/null | Back-filled by interaction-quality-gate |

## screen_index

```json
{
  "S001": {
    "name": "Homepage",
    "appears_in": ["OL01.N0101", "OL03.N0301"]
  }
}
```
