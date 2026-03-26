---
name: cr-visual
description: >
  Use when user wants to "compare UI visually", "visual fidelity", "screenshot comparison",
  "UI fidelity", "visual comparison", "screenshot diff",
  or mentions comparing source and target app screenshots for UI fidelity.
version: "2.0.0"
---

# Visual Fidelity — CR Visual v2.0 (Sub-Agent Architecture)

> Source App vs Target App screen-by-screen screenshot/recording -> compare -> fix -> re-compare -> until visually consistent

## Positioning

cr-visual is the **last step** in the replication flow — executed after cr-fidelity + product-verify + testforge all pass.

```
cr-fidelity -> product-verify -> testforge -> cr-visual (here)
```

**Prerequisite**: tests all green, App can run stably.

## Modes

- `full` = capture -> compare -> report -> repair loop (up to 30 rounds)
- `analyze` = capture -> compare -> report (no code fixes)
- `fix` = repair based on last report

## Sub-Agent Architecture

> **Why split**: A single agent handling screenshot capture, structural comparison, data audit, linkage verification, report generation, and repair loop simultaneously -> attention dilution, later steps (data integrity, linkage) easily get neglected. After splitting, each agent focuses on exactly one thing.

```
cr-visual orchestrator (this file)
  |-- capture agent -------- Steps 1-3 (screenshot capture)
  |-- per-screen parallel dispatch:
  |   |-- structural agent -- Step 4 (structural comparison)
  |   |-- data-integrity agent -- Step 4.5 (data integrity audit)
  |   +-- linkage agent ---- Step 4.6 (linkage verification, when linkage_verify exists)
  |-- report agent --------- Step 5 (merge scores + generate report)
  +-- repair agent --------- Steps 6-7 (repair loop, full/fix mode only)
```

## Auto-Exclusion Rules

**Platform differences**: `stack-mapping.json` has `platform_adaptation` -> differences matching `ux_transformations` are auto-marked `not_a_gap`.

**Multi-role**: `role-view-matrix.json` exists -> screenshot per role and compare separately.

**Interaction behavior**: `interaction-recordings.json` exists -> execute the same business flow chains, five-layer verification:
1. Static pages: screenshot comparison
2. CRUD full state: flow chain covers lifecycle
3. Dynamic effects: recording comparison
4. API logs: request comparison
5. Combined: milestone screenshots + API all consistent = high

---

## Execution Protocol: Plan -> Execute -> Verify

### Phase A: Screenshot Capture

```
1. Read ./docs/cr-visual/step-capture.md
2. Dispatch capture Agent:
   - Input: experience-map.json, route-map.json, replicate-config.json
   - Output: screens[] screenshot path mapping
   - Failure condition: no screenshots available -> error exit
```

### Phase B: Task Planning (critical addition)

> Do not jump straight to comparison. First enumerate "what to do", generating an explicit task checklist.

```
1. Read ./docs/cr-visual/step-plan.md
2. Dispatch plan Agent:
   - Input: screens[] + experience-map + interaction-recordings + target source code path
   - Execute: scan source code per screen, enumerate data-binding controls + linkage relationships
   - Output: visual-task-plan.json (subtask checklist per screen)
3. Display task summary: "20 screens, 67 subtasks: 20 structural + 35 data-integrity + 12 linkage"
```

### Phase C: Execute by Checklist (task-driven dispatch)

Read visual-task-plan.json, dispatch Agents grouped by subtask type:

```
For each screen (or each batch of 5 screens):

Agent 1 — structural (always dispatched):
  Read ./docs/cr-visual/step-structural.md
  Input: source + target screenshots + platform_adaptation
  Output: structural_score + differences
  On completion: update task-plan VT-xxx-S status -> completed

Agent 2 — data-integrity (only when screen has data_integrity subtasks):
  Read ./docs/cr-visual/step-data-integrity.md
  Input: source + target screenshots + target code + **control checklist for this screen** (from task-plan)
  Output: data_integrity_score + data_integrity_gaps[]
  On completion: update each VT-xxx-D* status
  Screen has no data_integrity subtask -> do not dispatch (save agent)

Agent 3 — linkage (only when screen has linkage subtasks):
  Read ./docs/cr-visual/step-linkage.md
  Input: linkage subtask checklist + target App URL
  Output: linkage_score + linkage_results[]
  On completion: update each VT-xxx-L* status
  Screen has no linkage subtask -> do not dispatch

Parallelism strategy: 3 agents for the same screen run in parallel; structural has no dependencies,
data-integrity and linkage may need to operate the target App -> serialize within same screen or coordinate as needed.
```

### Phase D: Verification (prevent omissions)

```
1. Read visual-task-plan.json -> check all subtask statuses
2. Statistics:
   - completed: N
   - failed: M (comparison failed, needs repair)
   - skipped: K (with skip reason)
   - pending: P (should not exist — if present, an agent missed execution)
3. pending > 0 -> dispatch supplementary agents for missed subtasks
4. All non-pending -> proceed to report phase
```

### Phase E: Merge Scores + Report

```
Read ./docs/cr-visual/step-report.md
Merge formula:
  final_score = structural_score - data_integrity_penalties - linkage_penalties
  final_score = max(0, final_score)
  match_level: >=90 -> high | >=60 -> medium | >=30 -> low | <30 -> mismatch

Write: visual-report.json + visual-report.md
Report includes task completion rate: "67/67 subtasks completed, 0 skipped"
```

### Phase F: Repair Loop (full/fix mode only)

```
Read ./docs/cr-visual/step-repair.md
Dispatch repair Agent:
  Input: visual-report.json + visual-task-plan.json
  Repair priority: fix subtasks by failed status one by one
  After each subtask fix -> re-screenshot -> re-compare -> update task-plan status
  Exit: all subtasks completed and score = high, or 30 round limit
```

---

## Attention Safeguard Mechanism

| Mechanism | Effect |
|-----------|--------|
| **Task checklist driven** | Agent executes by checklist, impossible to "forget to check" |
| **Verification phase checks pending** | Missed subtasks are auto-discovered and supplemented |
| Each agent only loads its own step-*.md | Narrow context, high focus |
| **On-demand dispatch** (no controls -> no agent) | Reduces wasted work |
| structural / data-integrity / linkage run in parallel | No interference, each executes deeply |
| repair agent fixes by subtask one by one | Impossible to miss items needing repair |

---

## Limitations

- LLM visual comparison is **subjective** — report includes screenshot paths, user should review
- Requires App to run and be navigable to each page (needs test accounts/data)
- Mobile screenshots depend on platform-specific UI automation tools or user manual screenshots
- Interaction behavior comparison depends on `interaction-recordings.json` — without this file, only static screenshot comparison

---

## Load Core Protocol

> Core protocol details: `./skills/code-replicate-core.md`
