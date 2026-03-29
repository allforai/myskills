# Meta-Skill Plan 4: Orchestrator + Diagnosis

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Flesh out the orchestrator template and diagnosis protocol so the generated `/run` command can drive the full state machine with failure recovery.

**Architecture:** The orchestrator-template.md becomes the authoritative source for run.md generation. A new diagnosis.md knowledge file provides the full-chain diagnosis protocol. Bootstrap Step 5 references these instead of embedding the full template inline.

**Tech Stack:** Markdown knowledge files, Python (loop detection script)

**Spec:** `docs/superpowers/specs/2026-03-29-meta-skill-architecture-design.md` Sections 4, 9, 10

---

### Task 1: Refactor orchestrator-template.md into full run.md template

**Files:**
- Modify: `claude/meta-skill/knowledge/orchestrator-template.md`

Replace the current summary with the complete run.md template (currently embedded in bootstrap.md Step 5). This becomes the single source of truth.

- [ ] **Step 1: Read current bootstrap.md Step 5 content**

Read `claude/meta-skill/skills/bootstrap.md` and extract the full run.md template from Step 5.

- [ ] **Step 2: Write complete orchestrator-template.md**

Replace `claude/meta-skill/knowledge/orchestrator-template.md` with the full template. Structure:

```markdown
# Orchestrator Template

> Authoritative template for generating .claude/commands/run.md in target projects.
> Bootstrap Step 5 reads this file and customizes it per project.

## Template: run.md

Below is the complete content that bootstrap writes to `.claude/commands/run.md`.
Bootstrap replaces `{placeholders}` with project-specific values.

---

\```markdown
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

## Core Loop

\```
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
\```

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

\```json
{
  "status": "success | failure | needs_input",
  "summary": "≤500 chars",
  "artifacts_created": [],
  "errors": [],
  "user_prompt": null
}
\```

## On Failure: Full-Chain Diagnosis

> See diagnosis protocol loaded from knowledge/diagnosis.md

When a node returns status "failure":
1. Do NOT retry or backtrack immediately
2. Dispatch a diagnosis subagent (see Diagnosis section below)
3. Execute the repair plan
4. Apply prevention rules
5. Record in diagnosis_history

{DIAGNOSIS_PROTOCOL}

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

## Context Management

Each iteration:
- Read state-machine.json (ground truth)
- Last 2-3 subagent results (conversation)
- Last diagnosis (if any)
- Old results compressed to node_summaries
\```
```

- [ ] **Step 3: Update bootstrap.md Step 5 to reference template**

In `claude/meta-skill/skills/bootstrap.md`, replace the inline run.md content in Step 5 with a reference:

```markdown
## Step 5: Generate .claude/commands/run.md

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/orchestrator-template.md` for the complete template.

Replace these placeholders with project-specific values:
- `{safety.*}` → from state-machine.json safety section
- `{DIAGNOSIS_PROTOCOL}` → from `${CLAUDE_PLUGIN_ROOT}/knowledge/diagnosis.md`

Write the result to `.claude/commands/run.md` in the target project.
```

- [ ] **Step 4: Commit**

```bash
git add claude/meta-skill/knowledge/orchestrator-template.md claude/meta-skill/skills/bootstrap.md
git commit -m "refactor(orchestrator): orchestrator-template.md as single source of truth for run.md"
```

---

### Task 2: Create diagnosis.md knowledge file

**Files:**
- Create: `claude/meta-skill/knowledge/diagnosis.md`

Full-chain diagnosis protocol extracted from the spec (Section 9).

- [ ] **Step 1: Write diagnosis.md**

```markdown
# Full-Chain Diagnosis Protocol

> Dispatched when any node returns status "failure". Performs root cause analysis,
> same-class gap expansion, and generates a repair plan.

## When to Trigger

A node subagent returns `{ "status": "failure", "errors": [...] }`.
Do NOT retry or backtrack. Diagnose first.

## Diagnosis Subagent Prompt Template

```
You are diagnosing a workflow failure.

## Failure Context
- Failed node: {node_id}
- Error: {errors from subagent response}
- Iteration: {iteration_count}

## System State
- All node summaries: {node_summaries from state-machine.json}
- All node exit_requires: {extracted from state-machine.json nodes}
- Previous diagnoses: {diagnosis_history}

## Your Tasks

1. **Root Cause**: Trace from the failed node upstream. Which is the earliest
   node whose output is insufficient? Don't guess — read the actual artifact
   files via Read tool if needed.

2. **Impact Chain**: List all intermediate nodes between root cause and failure.

3. **Same-Class Expansion**: The specific gap you found — are there similar gaps
   elsewhere? If one API was missed, were other APIs in the same domain also missed?
   If one business flow is incomplete, are sibling flows also incomplete?

4. **Repair Plan**: Ordered list of nodes to re-run, from upstream to downstream.
   Each entry: node ID + specific action + what context to carry.
   Use `depends_on_previous: true` when a step needs the prior step's output.

5. **Prevention**: Should any node-spec's exit_requires or hints be tightened
   to prevent this class of failure in future iterations?

## Output Format

Return JSON:
```json
{
  "root_cause": {
    "node": "<node-id>",
    "description": "<what's wrong>"
  },
  "impact_chain": ["<node-id>", ...],
  "gaps_found": [
    { "domain": "<area>", "missing": ["<item>", ...], "severity": "high|medium|low" }
  ],
  "repair_plan": [
    { "node": "<node-id>", "action": "<what to do>", "depends_on_previous": true|false }
  ],
  "prevention": [
    { "node_spec": "<node-id>", "add_to_exit_requires": "<new condition>" },
    { "node_spec": "<node-id>", "add_to_hints": "<new hint>" }
  ]
}
```
```

## Repair Plan Execution

After diagnosis returns:

1. Orchestrator reads repair_plan
2. Executes each step in order:
   - Read the node-spec for that node
   - Dispatch subagent with the repair action as additional context
   - Carry gaps_found so the subagent knows the full scope
3. After each step, update state-machine.json progress
4. Apply prevention rules: Edit the affected node-spec files

## Re-Verification

After repair_plan completes:
- Re-evaluate the originally failed node's exit_requires
- If still failing → diagnose again (with updated context)
- diagnosis_history prevents re-diagnosing the same root cause

## Convergence Control

- Same root cause: max 2 diagnoses. 3rd → mark UNRESOLVED, output current best + TODO
- Repair plan length ≤ impact_chain length (can't be longer than the chain)
- Previously identified gaps must resolve (new gaps OK, old gaps can't recur)
- Repair step failure → new diagnosis, but nested depth max 1 level
- Each diagnosis record written to state-machine.json diagnosis_history
```

- [ ] **Step 2: Commit**

```bash
git add claude/meta-skill/knowledge/diagnosis.md
git commit -m "feat(knowledge): diagnosis.md — full-chain diagnosis protocol"
```

---

### Task 3: Create loop_detection.py helper script

**Files:**
- Create: `shared/scripts/orchestrator/loop_detection.py`
- Test: `shared/scripts/orchestrator/test_loop_detection.py`

Mechanical loop detection: hash(node_id + exit results), sliding window, warn/stop thresholds.

- [ ] **Step 1: Write tests**

```python
#!/usr/bin/env python3
"""Tests for loop_detection.py."""

import json
import os
import tempfile
import shutil
import unittest

from loop_detection import check_loop, record_iteration


class TestLoopDetection(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.history_path = os.path.join(self.tmpdir, "loop_history.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_no_loop_on_first(self):
        result = record_iteration(self.history_path, "node-a", [True, False])
        self.assertEqual(result["status"], "ok")

    def test_no_loop_different_nodes(self):
        for node in ["a", "b", "c"]:
            result = record_iteration(self.history_path, node, [True])
        self.assertEqual(result["status"], "ok")

    def test_warn_at_threshold(self):
        for _ in range(3):
            result = record_iteration(self.history_path, "stuck", [False])
        self.assertEqual(result["status"], "warn")

    def test_stop_at_threshold(self):
        for _ in range(5):
            result = record_iteration(self.history_path, "stuck", [False])
        self.assertEqual(result["status"], "stop")

    def test_different_results_no_loop(self):
        record_iteration(self.history_path, "node-a", [True, False])
        record_iteration(self.history_path, "node-a", [True, True])
        result = record_iteration(self.history_path, "node-a", [False, True])
        self.assertEqual(result["status"], "ok")

    def test_custom_thresholds(self):
        for _ in range(2):
            result = record_iteration(
                self.history_path, "node", [False],
                warn_threshold=2, stop_threshold=4
            )
        self.assertEqual(result["status"], "warn")

    def test_sliding_window(self):
        # Fill window with unique entries
        for i in range(10):
            record_iteration(self.history_path, f"node-{i}", [True])
        # Now repeat one — should not trigger warn because old entries fell out
        result = record_iteration(self.history_path, "new-stuck", [False])
        self.assertEqual(result["status"], "ok")

    def test_check_loop_without_recording(self):
        # Pre-fill history
        for _ in range(3):
            record_iteration(self.history_path, "stuck", [False])
        status = check_loop(self.history_path, "stuck", [False])
        self.assertEqual(status, "warn")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m unittest test_loop_detection -v
```

- [ ] **Step 3: Implement loop_detection.py**

```python
#!/usr/bin/env python3
"""Mechanical loop detection for the orchestrator.

Tracks iteration history as (node_id, exit_results_hash) entries in a sliding window.
Detects when the same state repeats beyond thresholds.

Usage:
  python loop_detection.py record <history-file> <node-id> <exit-results-json>
  python loop_detection.py check <history-file> <node-id> <exit-results-json>
"""

import hashlib
import json
import os
import sys


DEFAULT_WINDOW_SIZE = 10
DEFAULT_WARN_THRESHOLD = 3
DEFAULT_STOP_THRESHOLD = 5


def _make_hash(node_id: str, exit_results: list) -> str:
    """Deterministic hash of node_id + exit_requires evaluation results."""
    blob = json.dumps({"node": node_id, "results": exit_results}, sort_keys=True)
    return hashlib.md5(blob.encode()).hexdigest()[:12]


def _load_history(path: str) -> list:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_history(path: str, history: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f)


def record_iteration(
    history_path: str,
    node_id: str,
    exit_results: list,
    warn_threshold: int = DEFAULT_WARN_THRESHOLD,
    stop_threshold: int = DEFAULT_STOP_THRESHOLD,
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> dict:
    """Record an iteration and check for loops. Returns { status, hash, count }."""
    history = _load_history(history_path)
    h = _make_hash(node_id, exit_results)
    history.append(h)

    # Sliding window
    if len(history) > window_size:
        history = history[-window_size:]

    _save_history(history_path, history)

    count = history.count(h)
    if count >= stop_threshold:
        status = "stop"
    elif count >= warn_threshold:
        status = "warn"
    else:
        status = "ok"

    return {"status": status, "hash": h, "count": count}


def check_loop(
    history_path: str,
    node_id: str,
    exit_results: list,
    warn_threshold: int = DEFAULT_WARN_THRESHOLD,
    stop_threshold: int = DEFAULT_STOP_THRESHOLD,
) -> str:
    """Check if adding this iteration would trigger a loop, without recording."""
    history = _load_history(history_path)
    h = _make_hash(node_id, exit_results)
    count = history.count(h) + 1  # +1 for the hypothetical addition

    if count >= stop_threshold:
        return "stop"
    elif count >= warn_threshold:
        return "warn"
    return "ok"


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(f"Usage: {sys.argv[0]} record|check <history-file> <node-id> <exit-results-json>", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    history_path = sys.argv[2]
    node_id = sys.argv[3]
    exit_results = json.loads(sys.argv[4])

    if action == "record":
        result = record_iteration(history_path, node_id, exit_results)
        print(json.dumps(result))
        sys.exit(0 if result["status"] != "stop" else 1)
    elif action == "check":
        status = check_loop(history_path, node_id, exit_results)
        print(json.dumps({"status": status}))
        sys.exit(0 if status != "stop" else 1)
    else:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/aa/Documents/myskills/shared/scripts/orchestrator && python -m unittest test_loop_detection -v
```

Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add shared/scripts/orchestrator/loop_detection.py shared/scripts/orchestrator/test_loop_detection.py
git commit -m "feat(orchestrator): loop_detection.py — sliding window hash-based loop detection"
```

---

### Task 4: Update bootstrap to copy loop_detection.py

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md`

- [ ] **Step 1: Add loop_detection.py to Step 6.2 copy list**

In bootstrap.md Step 6.2, add:
```bash
cp ${CLAUDE_PLUGIN_ROOT}/../../shared/scripts/orchestrator/loop_detection.py .allforai/bootstrap/scripts/
```

And add to Step 6.3 file list:
```
7. `.allforai/bootstrap/scripts/loop_detection.py` (copied from plugin)
```

- [ ] **Step 2: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "fix(bootstrap): include loop_detection.py in script copy step"
```
