# Dev Forge — Execution Playbook

> Detailed phase orchestration with explicit transition logic for the full project forge pipeline.

---

## Overview

The dev-forge pipeline consists of 8 phases (Phase 0-8) plus an intermediate Phase 4.5. Each phase has explicit entry conditions, execution steps, quality gates, and transition logic.

```
Phase 0  产物检测 + Preflight
  ↓ (product-design artifacts exist)
Phase 1  技术风险调研 (Technical Spike)
  ↓ (all spikes confirmed or TBD)
Phase 2  项目引导 (Project Setup)
  ↓ (project-manifest.json exists, ≥1 sub-project)
Phase 3  设计转规格 (Design to Spec)
  ↓ (all sub-projects have requirements + design + tasks + shared-utilities-plan)
Phase 4  任务执行 (Task Execute)
  ↓ (CORE tasks completed, lint pass)
Phase 4.5  接缝门禁 + 深度审计 (Seam Gate)
  ↓ (deadhunt critical=0, fieldcheck critical=0, core pages pass)
Phase 5  验证闭环 (4-Agent Parallel Scan)
  ↓ (verify-tasks resolved, smoke tests pass)
Phase 6  演示数据方案 (Demo Forge Design)
  ↓ (demo-plan.json exists or skipped)
Phase 7  跨端验证 (Conditional E2E)
  ↓ (E2E pass rate ≥80%, only if Phase 5 != completed)
Phase 8  最终报告 (Final Report)
```

---

## Phase Transition Rules

### Iron Rule: Zero-Pause Phase Transitions

Phase transitions MUST NOT pause for user confirmation. When a quality gate passes (or fails with issues recorded), immediately load and execute the next phase. The only exceptions:
- User explicitly requests to stop (Iron Rule #2)
- ERROR-level security guardrail triggers

Output a single status line at each transition: `Phase N ✓ → Phase N+1`

### Iron Rule: Not-Tested ≠ Skipped ≠ Passed

| Status | Meaning | Downstream Effect |
|--------|---------|-------------------|
| `completed` / `PASS` | Tested and passed | Subsequent validation can be skipped |
| `not_tested` | Could not execute (env unavailable) | MUST be retested later; never treat as pass |
| `skipped` | User chose to skip | MUST execute corresponding validation later |
| `FAIL` | Tested and failed | Generate fix tasks, fix, regress |

---

## Phase 0: Artifact Detection + Preflight

### Entry Condition
- User invokes `project-forge full` or `project-forge existing`

### Execution Steps

1. **Product-design artifact check**
   - Verify `.allforai/product-map/product-map.json` exists
   - If missing → terminate with message: "Run /product-design full first"

2. **Artifact probe** — scan completion flags for all 10 artifact categories (product-design through testforge E2E)

3. **Scale check** — read task count from task-inventory.json, sub-project count from project-manifest.json
   - task > 200 or sub-project > 6 → inform user about auto-batching
   - task > 500 → suggest splitting first

4. **Interactive mode detection** — read `__orchestrator_auto` from product-concept.json
   - `true` → auto mode (zero decision pauses)
   - `false` or absent → interactive mode (decisions pause for user)

5. **Experience priority inheritance** — if product-map.json has `experience_priority.mode = consumer | mixed`, write it to forge-decisions.json and derive `consumer_apps` list

6. **External capability probe**
   - Playwright: detect `mcp__playwright__browser_navigate` availability
   - Maestro: detect `which maestro` CLI
   - OpenRouter: detect `mcp__ai-gateway__ask_model` availability
   - Output status table; do not block Phase 1-4 for missing capabilities

7. **Preflight preference collection** (Step 2a-2d)
   - Infer endpoint types from role-profiles.json
   - Generate recommended config (backend, frontend, mobile, monorepo, auth)
   - Auto mode: adopt recommendations, write forge-decisions.json
   - Interactive mode: present table, wait for user confirmation

### Quality Gate
- product-design artifacts exist → PASS
- forge-decisions.json created with preflight → PASS

### Transition → Phase 1
- Auto mode: immediate
- Interactive mode: after user confirms preflight

---

## Phase 1: Technical Spike Analysis

### Entry Condition
- Phase 0 passed

### Skip Condition
- No non-CRUD tech points detected in task-inventory.json → skip to Phase 2

### Execution Steps

1. **Auto-detect** — scan task-inventory.json for 8 categories (ai_llm, speech, payment, push, algorithm, realtime, file_storage, oauth)

2. **Parallel WebSearch** — launch N parallel agents (one per spike category), each performing 2-3 rounds of WebSearch

3. **XV cross-validation** (optional) — if OpenRouter available, send each spike to a different model for validation

4. **Present comparison tables** — 2-3 options per spike with vendor/cost/complexity/compatibility

5. **User selection**
   - Auto mode: adopt all recommended options
   - Interactive mode: user confirms or adjusts per-spike

6. **Credential collection** (Step 4.5) — for confirmed spikes requiring external services, collect sandbox credentials in one batch

7. **Generate coding principles** — universal (4 mandatory) + project-specific (from spikes + constraints)

### Quality Gate
- All spikes confirmed or marked TBD
- Coding principles: universal ≥4, each confirmed spike has implementation_principles

### Transition → Phase 2
- Write technical_spikes + coding_principles to forge-decisions.json
- `phase_status.phase_1 = completed`

---

## Phase 2: Project Setup

### Entry Condition
- Phase 1 completed or skipped

### Execution Steps
- Load `skills/project-setup.md` and execute its workflow
- full mode → project-setup new
- existing mode → project-setup existing

### Quality Gate
- ≥1 sub-project defined
- Each sub-project has template_id
- Module coverage = 100%

### Transition → Phase 3
- project-manifest.json exists
- FAIL → record issues, continue with problems

---

## Phase 3: Design to Spec + Shared Utilities

### Entry Condition
- Phase 2 passed (project-manifest.json exists)

### Execution Steps
- Load `skills/design-to-spec.md` and execute Step 1-7
- Phase A (backend) → Phase B (frontend parallel) → Step 5-7 (cross-project)
- Step 7: shared utilities analysis + B1 task injection

### Quality Gate
- Each sub-project has requirements.md + design.md + tasks.md
- shared-utilities-plan.json exists
- All SU-xxx have B1 tasks
- No broad tasks like "implement XX system"

### Transition → Phase 4
- FAIL → record issues, continue

---

## Phase 4: Task Execution

### Entry Condition
- Phase 3 passed (all spec files exist)

### Pre-check (full mode only)
- Check each sub-project base_path for existing code
- Auto mode: backup to `.pre-forge-bak`, start clean
- Interactive mode: ask user (backup/incremental/abort)

### Execution Steps
- Load `skills/task-execute.md`
- Step 0: Initialize build-log.json, group by Round, auto-shard large Rounds (>30 tasks)
- Step 0.5: Auto-generate .env files
- Per Round: Step 1 (strategy) → Step 1.5-1.9 (context injection) → Step 2 (execute) → Step 3 (quality checks) → Step 4 (incremental verify)

### Quality Gate
- All CORE tasks marked completed in build-log.json
- Lint passes
- Tests pass (or skipped with record)

### Transition → Phase 4.5
- FAIL → record failed/skipped tasks, continue

---

## Phase 4.5: Seam Gate + Depth Audit (NOT SKIPPABLE)

### Entry Condition
- Phase 4 completed (build-log.json has ≥1 completed Round)

### Execution Steps

1. **Step 4.5.1**: Start all sub-project dev servers

2. **Step 4.5.2**: Parallel agents
   - Agent 1: `deadhunt static` — dead links + CRUD gaps
   - Agent 2: `fieldcheck full` — UI↔API↔Entity field consistency

3. **Step 4.5.3**: Fix critical issues directly in code

4. **Step 4.5.3.5**: Auth chain E2E verification (if auth exists)
   - Login → get token → call protected API → verify 200

5. **Step 4.5.4**: Seam smoke test + UI performance baseline
   - Playwright: real login → visit core pages → verify data visible
   - Measure load time (data_visible_ms); >5s = WARNING, >10s = investigate

6. **Step 4.5.5**: Depth audit (Hollow Shell Detection)
   - Check callback connectivity, data binding completeness, core feature coverage
   - Fix HOLLOW_CALLBACK, STUB_LOGIC, MOCK_DATA, INCOMPLETE_CORE

### Quality Gate
- deadhunt critical = 0
- fieldcheck critical = 0
- Core page seam smoke all pass
- Core page first-data-visible < 5s (WARNING, not blocking)

### Transition → Phase 5
- FAIL → fix and rerun (max 3 rounds)

---

## Phase 5: Verification Closure (4-Agent Parallel Scan)

### Entry Condition
- Phase 4.5 passed
- build-log.json exists with ≥1 completed Round (HARD prerequisite)

### Execution Steps

1. **Step 0.5**: Abstraction gate (code-tuner Phase 2+3 on files_modified)
   - CRITICAL → generate B-REFACTOR tasks
   - WARNING → record in forge-report Tech Debt section

2. **Step 1**: 4-Agent parallel scan (single message, 4 Agent calls)
   - Agent 1: product-verify full (load `skills/product-verify.md`)
   - Agent 2: testforge E2E chain (load `commands/testforge.md`)
   - Agent 3: deadhunt static or full (load `commands/deadhunt.md`)
   - Agent 4: fieldcheck full (load `commands/fieldcheck.md`)

3. **Step 1.5**: LLM smoke test generation + execution
   - Step 1.5a: LLM analyzes runtime risks
   - Step 1.5b: Generate executable smoke tests (3 layers: process/connection/data)
   - Step 1.5c: Execute and collect results
   - Step 1.5d: Determine Phase 5 verification level

4. **Step 2**: Aggregate all findings
   - No fixes needed → PASS
   - Fixes needed → Step 3

5. **Step 3**: Generate fix tasks (IMPLEMENT / FIX_FAILING / FIX_REQUIRED / deadhunt / fieldcheck)

6. **Step 4**: Execute fixes via task-execute

7. **Step 5**: Regression (scope mode on fixed task_ids)

### Quality Gate
- verify-tasks: IMPLEMENT + FIX_FAILING = 0
- testforge: FIX_REQUIRED = 0
- deadhunt: no critical dead links
- fieldcheck: no critical field inconsistencies
- smoke-test: FAIL = 0

### Phase 5 Status Determination
- All PASS + smoke all PASS → `phase_5 = completed`
- All PASS + smoke has NOT_TESTED → `phase_5 = not_tested`
- Static PASS + dynamic FAIL → `phase_5 = static_pass`

### Transition → Phase 6
- `completed` → Phase 6
- `not_tested` → Phase 6, but Phase 7 MUST execute later
- Record known issues in forge-decisions.json

---

## Phase 6: Demo Data Plan

### Entry Condition
- Phase 5 completed or passed with issues

### Execution Steps
- Prompt user to run `/demo-forge design`
- This is an external plugin (demo-forge-skill/); only plan design here

### Quality Gate
- demo-plan.json exists in `.allforai/demo-forge/`
- OR user chooses to skip

### Transition → Phase 7
- Skip → `phase_6 = skipped`

---

## Phase 7: Cross-Platform E2E (Conditional)

### Entry Condition
Check Phase 5 status:
- `completed` → SKIP Phase 7, go to Phase 8
- `static_pass` → MUST execute Phase 7
- `not_tested` → MUST execute Phase 7
- `skipped` → execute Phase 7

### Execution Steps
- Load `commands/testforge.md`, execute Phase 4 Path B (E2E chain forge)
- Requires all sub-project apps running

### Quality Gate
- E2E pass rate ≥ 80%
- All FIX_REQUIRED classified

### Transition → Phase 8

---

## Phase 8: Final Report

### Entry Condition
- All previous phases completed

### Execution Steps
- Read all phase artifacts
- Generate `forge-report.json` (machine) + `forge-report.md` (human)
- Report includes:
  - Execution summary (mode, sub-projects, task counts)
  - Per-phase status with quality gate results
  - Per-sub-project status (type, stack, tasks, completion, E2E)
  - Pending items: DEFER tasks, E2E failures, NOT_TESTED items
  - Negative-space supplements discovered during development
  - Next steps checklist

### Output
```
.allforai/project-forge/
├── forge-report.json    # Full report (machine-readable)
└── forge-report.md      # Human-readable summary
```

---

## Skill-Level Orchestration Detail

### design-to-spec — Role Separation Architecture

Four roles execute in sequence with independence guarantees:

| Role | Input | Output | Isolation Rule |
|------|-------|--------|---------------|
| Architect | product-map + entity-model | requirements.md + design.md | Generates only |
| Decomposer | design.md + requirements.md | tasks.md (B0-B5) | Reads design, generates tasks |
| Auditor | all outputs + product-map | validation findings → corrections | MUST be separate agent from Architect/Decomposer |
| Enricher | design + tasks + product-map | event-schema + task-context | Independent, can parallel with Auditor |

**Execution order**: Phase A (backend) completes → Phase B (all frontends parallel)

**Scale adaptation**: >5 modules per sub-project → auto-batch (3-5 modules per batch), all roles partition by module group

### task-execute — Round-Based Iteration

Per-Round cycle:
1. Strategy inference (serial if file overlap, parallel if isolated sub-projects)
2. Context injection (API contract binding, experience DNA, task-context)
3. Read-before-write (mandatory: read existing code → summarize → then write)
4. Execute tasks (delegate to subagent or parallel agents)
5. Quality checks (lint + test + security scan in parallel)
6. Incremental verification (existence via product-verify scope + correctness via CC1-CC7)

**Consumer-app checkpoints**: After last frontend B2 Round for consumer_apps, global self-check for main-line clarity, state system, and continuous relationship touchpoints.

### product-verify — Multi-Stage Verification

Static stages (parallelizable):
- S0: Bidirectional traceability matrix
- S1: Semantic task coverage (LLM-driven)
- S1.5: Feature depth verification (concept-baseline)
- S2: UI component fidelity (6V)
- S2.5: Product polish review (consumer_apps only)
- S3: Guardrail logic coverage (3-level)
- S4: Extra code AI triage
- S5: Cross-model XV
- S6: Journey-level verification
- S7: Seed-test coverage matrix

Dynamic stages:
- D0: App reachability pre-check
- D1: Test sequence generation
- D2/D3: Normal flow + E2E flow (parallel Playwright contexts)
- D3.5-D3.9: Cognitive walkthrough, UI liveness, data flow tracing, state machine completeness, constraint penetration
- D4: 6V failure diagnosis
- D5: Dynamic 4D coverage closure

---

## Error Recovery & Resume

### Resume Detection
Each phase checks for existing artifacts:
- Phase present and complete → skip
- Phase partially complete → resume from incomplete step
- Phase missing → execute from beginning

### Failure Handling
- Single task failure → isolate, skip dependents, continue siblings
- Phase failure → record in forge-decisions.json, continue with problems (never block)
- External service unavailable → degrade gracefully, mark `not_tested`

### Decision Tracking
All user decisions recorded in `forge-decisions.json` with:
- Step identifier
- Decision value
- Timestamp
- Source (user/auto/upstream)
