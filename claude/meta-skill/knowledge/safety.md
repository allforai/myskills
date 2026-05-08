# Safety Rules Template

> Used by bootstrap to generate the safety section of workflow.json.

## Default Configuration

```yaml
safety:
  loop_detection:
    warn_threshold: 3
    stop_threshold: 5
  max_global_iterations: 60  # REQUIRED: bootstrap must set this to max(60, node_count * 3)
  progress_monotonicity:
    check_interval: 5
    violation_action: "output current best + TODO list"
  max_concurrent_nodes: 3
  max_node_execution_time: 600
```

## Loop Detection

Hash input: `node_id + exit_artifacts existence check results (true/false per file path)`
Sliding window: last 10 iterations.
Does not include timestamps or other volatile data.

## Progress Monotonicity

`progress = len(completed_nodes) / len(total_nodes)`
`total_nodes` fixed at bootstrap time.
Checked every `check_interval` iterations.

**Carve-out for human gate nodes:** Nodes with `human_gate: true` and `gate_status == "in-review"` are excluded from the no-progress check — they are legitimately waiting for human approval, not stuck. Only count them as "no progress" if they remain `in-review` for more than `max_node_execution_time * 2` seconds without a gate status change.

## Dangerous Command Patterns

Blocked in generated node-specs:
- `rm` with `-rf` flags
- `sudo` usage
- `chmod 777`
- Writes to `/dev/`
- `mkfs`, `dd`, fork bombs
