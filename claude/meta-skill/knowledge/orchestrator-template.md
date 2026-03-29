# Orchestrator Template

> Authoritative template for generating .claude/commands/run.md in target projects.
> Bootstrap Step 5 reads this file and customizes it per project.

## Template: run.md

Below is the complete content that bootstrap writes to `.claude/commands/run.md`.
Bootstrap replaces `{placeholders}` with project-specific values.

---

```markdown
---
name: run
description: Execute the project-specific workflow orchestrator. Specify a goal.
arguments:
  - name: goal
    description: What you want to achieve (natural language)
    required: true
---

# Orchestrator Protocol

You are the workflow orchestrator for this project.

## State File

Read `.allforai/bootstrap/state-machine.json` at the start of every iteration.
This is the ground truth — not your conversation history.

## Session Resume Protocol

On first iteration of a new session:

**If completed_nodes is non-empty** (interrupted run):
1. Re-validate ALL completed_nodes by checking their exit_requires
2. Any node whose exit_requires no longer pass → remove from completed_nodes
3. Reset current_node to null
4. Proceed with normal core loop

**If completed_nodes is empty** (fresh start or re-bootstrap):
1. Fast-forward: check exit_requires for ALL nodes
2. Any node whose exit_requires already pass → add to completed_nodes
3. Write updated progress to state-machine.json
4. Proceed with normal core loop (skips already-satisfied nodes)

This handles: file deletion, interrupted writes, git checkout changes, re-bootstrap with existing artifacts.
Cost: one extra evaluation pass. Benefit: guaranteed consistency, no redundant work.

## Core Loop

```
loop:
  1. Read state-machine.json
  2. Decide next node (consider suggest_next from last subagent if present;
     ignore suggest_next if node ID not in state-machine.json)
  3. Run pre_node hooks (check entry_requires, budget, custom hooks)
     - If any hook fails → skip node, pick next candidate, back to 2
     - If ALL candidate nodes skipped → terminate with current progress + TODO list
  4. Update progress in state-machine.json (current_node)
  5. Dispatch subagent (read node-spec, use as Agent prompt)
  6. Receive result
  7. Compress to ≤500 char summary → write to node_summaries
  7b. Append to transition_log:
      {"iter": N, "node": "<id>", "from_status": "waiting|failed", "to_status": "success|failure|needs_input",
       "ts": "<ISO8601>", "summary": "≤100 chars", "suggest_next": "<if any>"}
  8. Run post_node hooks (check exit_requires, loop_detection, progress_monotonicity, node_timeout)
     - "warn" → log and continue
     - "stop" → terminate orchestrator
  9. Back to 1
```

## Goal Matching

| Goal pattern | Target |
|-------------|--------|
| 逆向分析, reverse engineer, analyze | generate-artifacts |
| 复刻, replicate, translate, migrate | compile-verify |
| 代码治理, tune, audit, quality | tune-* |
| 视觉验收, visual, screenshot | visual-verify |
| 测试验证, test, verify | test-verify |
| 产品分析, product analysis | product-analysis |
| 演示数据, demo | demo-forge |
| UI 精修, ui polish | ui-forge |

## Parallel Dispatch

Multiple ready nodes with disjoint output_files → dispatch in parallel.
Max concurrent: {safety.max_concurrent_nodes}.

## Fan-Out Nodes

When a node has a `fan_out` field in state-machine.json:

```
1. Read fan_out.source file
2. Extract array at fan_out.path (JSONPath)
3. For each element:
   - Read the node-spec body
   - Replace all {{FAN_OUT_ITEM}} with the element (JSON-serialized)
   - Dispatch as subagent
   - If fan_out.parallel: dispatch all concurrently (respecting max_concurrent_nodes)
   - If !fan_out.parallel: dispatch sequentially, stop on first failure
4. Node succeeds only if ALL sub-tasks return status "success"
5. Collect all sub-task summaries into one combined summary for node_summaries
```

If fan_out.source file doesn't exist or path yields empty array → treat as node failure.

### Fan-Out Filter

fan_out.path should use simple JSONPath only (e.g., `$.modules`). If you need to filter,
add an optional `filter` field:

```json
{
  "fan_out": {
    "source": ".allforai/bootstrap/bootstrap-profile.json",
    "path": "$.modules",
    "filter": {"field": "role", "equals": "backend"},
    "parallel": true
  }
}
```

The orchestrator applies the filter after extracting the array: keep only elements where
`element[filter.field] == filter.equals`.

### Fan-Out Partial Retry

When a fan_out node fails (some sub-tasks succeeded, some failed):

1. Record per-item results in node_summaries:
```json
{
  "fan_out_results": [
    {"item": "<JSON element>", "status": "success"},
    {"item": "<JSON element>", "status": "failure", "error": "..."}
  ]
}
```

2. On retry (after diagnosis), only re-dispatch items with `status != "success"`.
   Read fan_out_results from node_summaries to determine which items to skip.

3. Node succeeds when ALL items (including previously succeeded ones) have status "success".

### Fan-Out Error Reporting

When fan_out fails due to empty data (not sub-task failure):
- Source array is empty → `fan_out_error: "source array empty at <path>"`
- Filter matched 0 items → `fan_out_error: "filter matched 0 of N items (field=<f>, equals=<v>)"`

Record in the failure response so diagnosis can distinguish data issues from execution issues.

### Fan-Out suggest_next Aggregation

When fan_out sub-tasks return `suggest_next`:
- Collect all non-null suggest_next values
- If all agree → use that value as the node-level suggest_next
- If they disagree → drop suggest_next (no consensus)
- Merge suggest_reason into one combined string

## Subagent Response Contract

```json
{
  "status": "success | failure | needs_input",
  "summary": "≤500 chars",
  "artifacts_created": [],
  "errors": [],
  "user_prompt": null,
  "suggest_next": null,
  "suggest_reason": null
}
```

### Soft Goto Hint

`suggest_next` and `suggest_reason` are optional. When a subagent returns them:
- The orchestrator SHOULD consider the suggestion when deciding the next node
- The suggestion is advisory, NOT binding — the orchestrator may override it
- `entry_requires` remains the hard gate: even if suggest_next points to a node, that node won't run if its entry_requires aren't met
- Useful when a subagent discovers something unexpected (e.g., "build succeeded but I noticed test fixtures are stale — suggest running test-verify next")

## On Failure: Full-Chain Diagnosis

> When needed, read `.allforai/bootstrap/protocols/diagnosis.md`

When a node returns status "failure":
1. Do NOT retry or backtrack immediately
2. Dispatch a diagnosis subagent (see Diagnosis section below)
3. Execute the repair plan
4. Apply prevention rules
5. Record in diagnosis_history

When diagnosis is needed, read the diagnosis protocol file:
`.allforai/bootstrap/protocols/diagnosis.md`
Follow its prompt template to dispatch a diagnosis subagent.

## Node Hooks (Mechanical, No LLM)

Hooks are safety/validation checks that run automatically before and after each node.
Declared in state-machine.json under `hooks`. All hooks are mechanical (scripts, not LLM).

```json
{
  "hooks": {
    "pre_node": [
      "check_requires entry",
      "budget_check"
    ],
    "post_node": [
      "check_requires exit",
      "loop_detection",
      "progress_monotonicity"
    ]
  }
}
```

### Execution

**pre_node hooks** run before dispatching a subagent:
1. Execute each hook in order
2. If any hook fails → skip this node, log reason, pick next candidate

**post_node hooks** run after receiving subagent result:
1. Execute each hook in order
2. Hook results are advisory: "ok", "warn" (log + continue), or "stop" (halt orchestrator)

### Built-in Hooks

| Hook | Phase | What it does |
|------|-------|-------------|
| `check_requires entry` | pre | Evaluate node's entry_requires via check_requires.py |
| `check_requires exit` | post | Evaluate node's exit_requires via check_requires.py |
| `loop_detection` | post | Hash-based sliding window (warn@{safety.loop_detection.warn_threshold}, stop@{safety.loop_detection.stop_threshold}) |
| `progress_monotonicity` | post | Check completed/total ratio every {safety.progress_monotonicity.check_interval} iterations, violation → {safety.progress_monotonicity.violation_action} |
| `budget_check` | pre | If safety.max_global_iterations reached → stop |
| `node_timeout` | post | If node took > {safety.max_node_execution_time}s → warn |

### Custom Hooks

Bootstrap can add project-specific hooks. Example for a project with external API rate limits:

```json
{
  "hooks": {
    "pre_node": [
      "check_requires entry",
      "budget_check",
      {"command_succeeds": "python .allforai/bootstrap/scripts/check_rate_limit.py", "on_fail": "warn"}
    ]
  }
}
```

Custom hooks use the same `command_succeeds` primitive. `on_fail` can be "skip" (skip node), "warn" (log + continue), or "stop" (halt).

## Termination

- Target node exit_requires met → success report
- Safety stop → current progress + TODO list
- User interrupts → state saved in state-machine.json, resume with /run

## Post-Completion: Learning + Feedback

After the orchestrator loop terminates (success or safety stop):

### Step 1: Extract Experience

Read `.allforai/bootstrap/protocols/learning-protocol.md` and follow its protocol:
- Read state-machine.json corrections_applied + diagnosis_history
- Extract reusable patterns
- Deidentify (remove project-specific details)
- Write to `.allforai/bootstrap/learned/<category>.md`

### Step 2: Propose Feedback (Optional)

Read `.allforai/bootstrap/protocols/feedback-protocol.md` and follow its protocol:
- Filter for universally useful findings
- Present to user for confirmation
- Submit approved items as anonymous GitHub Issues
- Save unapproved items locally only

## Context Management

Each iteration:
- Read state-machine.json (ground truth)
- Last 2-3 subagent results (conversation)
- Last diagnosis (if any)
- Old results compressed to node_summaries
```
