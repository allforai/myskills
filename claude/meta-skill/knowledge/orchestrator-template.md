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

On first iteration of a new session (iteration_count > 0 in progress):
1. Re-validate ALL completed_nodes by checking their exit_requires
2. Any node whose exit_requires no longer pass → remove from completed_nodes
3. Reset current_node to null
4. Proceed with normal core loop (will naturally re-dispatch regressed nodes)

This handles: file deletion, interrupted writes, git checkout changes.
Cost: one extra evaluation pass. Benefit: guaranteed consistency.

## Core Loop

```
loop:
  1. Read state-machine.json
  2. Mechanically evaluate requires:
     python .allforai/bootstrap/scripts/check_requires.py \
       .allforai/bootstrap/state-machine.json <node-id> --type exit --json
  3. Decide next node (LLM reasoning when needed)
  4. Update progress in state-machine.json
  5. Dispatch subagent (read node-spec, use as Agent prompt)
  6. Receive result
  7. Compress to ≤500 char summary → write to node_summaries
  8. Safety checks
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

## Subagent Response Contract

```json
{
  "status": "success | failure | needs_input",
  "summary": "≤500 chars",
  "artifacts_created": [],
  "errors": [],
  "user_prompt": null
}
```

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

## Safety Checks (Mechanical, Every Iteration)

### Loop Detection
hash = node_id + exit_requires evaluation (true/false per condition)
Sliding window: last 10 iterations
warn_threshold: {safety.loop_detection.warn_threshold}
stop_threshold: {safety.loop_detection.stop_threshold}

### Progress Monotonicity
progress = completed_nodes / total_nodes
Check every {safety.progress_monotonicity.check_interval} iterations
Violation → {safety.progress_monotonicity.violation_action}

### Node Timeout
max_node_execution_time: {safety.max_node_execution_time} seconds

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
