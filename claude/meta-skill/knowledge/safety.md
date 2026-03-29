# Safety Rules Template

> Used by bootstrap to generate the safety section of state-machine.json.

## Default Configuration

```yaml
safety:
  loop_detection:
    warn_threshold: 3
    stop_threshold: 5
  max_global_iterations: 30
  progress_monotonicity:
    check_interval: 5
    violation_action: "output current best + TODO list"
  max_concurrent_nodes: 3
  max_node_execution_time: 600
```

## Loop Detection

Hash input: `node_id + exit_requires evaluation results (true/false per condition)`
Sliding window: last 10 iterations.
Does not include timestamps or other volatile data.

## Progress Monotonicity

`progress = len(completed_nodes) / len(total_nodes)`
`total_nodes` fixed at bootstrap time.
Checked every `check_interval` iterations.

## Dangerous Command Patterns

Blocked in generated node-specs:
- `rm` with `-rf` flags
- `sudo` usage
- `chmod 777`
- Writes to `/dev/`
- `mkfs`, `dd`, fork bombs
