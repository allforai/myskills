# Dev Forge — Execution Playbook

> 8-phase pipeline from product design artifacts to running project.
> Each phase has entry conditions, execution steps, quality gates, and completion artifacts.

---

## Pipeline Overview

```
Phase 0: Detect + Route + Preflight
  |
Phase 1: Technical Spike Analysis
  | quality gate: all spikes confirmed or TBD
Phase 2: Project Setup (project-setup)
  | quality gate: >= 1 sub-project with tech stack, 100% module coverage
Phase 3: Design to Spec (design-to-spec + shared utilities)
  | quality gate: each sub-project has requirements.md + design.md + tasks.md
Phase 4: Task Execution (task-execute)
  | quality gate: CORE tasks completed, lint pass
Phase 4.5: Seam Gate + Depth Audit
  | quality gate: deadhunt/fieldcheck critical = 0, core pages pass smoke
Phase 5: Verification Loop (product-verify || testforge || deadhunt || fieldcheck)
  | quality gate: no unresolved IMPLEMENT/FIX_FAILING/critical issues
Phase 6: Demo Handoff (demo-forge design)
  | quality gate: demo-plan.json exists or skipped
Phase 7: Cross-Platform Verification (conditional)
  | quality gate: E2E pass rate >= 80%
Phase 8: Final Report
  | output: forge-report.md + forge-report.json
```

---

## Phase 0: Detect + Route + Preflight

**Purpose**: Scan existing artifacts, determine mode, collect tech preferences.

**Entry condition**: `.allforai/product-map/product-map.json` must exist.

**Steps**:
1. Scan `.allforai/` for artifact existence (see artifact table in AGENTS.md)
2. Detect mode: `full` (new project) or `existing` (gap mode)
3. Detect auto/interactive mode from `product-concept.json` → `__orchestrator_auto`
4. Infer endpoint types from `role-profiles.json`
5. Generate recommended tech config (backend, frontend, mobile, monorepo, auth)
6. Auto-mode: adopt recommendations; Interactive-mode: present table for confirmation
7. Write preflight to `forge-decisions.json`
8. If `experience_priority.mode = consumer|mixed`, derive `consumer_apps` list

**External capability check**:
- Playwright: required for Phase 5-8 verification
- OpenRouter: optional for XV cross-verification

**Completion**: `forge-decisions.json` exists with `preflight` field.

---

## Phase 1: Technical Spike Analysis

**Purpose**: Detect non-CRUD tech points, research options, collect decisions.

**Entry**: `./commands/project-forge.md` Phase 1 section.

**Skip condition**: No spike keywords detected in task-inventory.json.

**Steps**:
1. Scan task-inventory.json for spike keywords (AI/speech/payment/push/algorithm/realtime/storage/OAuth)
2. Execute parallel research agents (one per spike category) using web search
3. Optional: cross-model validation via OpenRouter
4. Present comparison tables (2-3 options per spike)
5. Auto-mode: adopt recommended options; Interactive-mode: wait for user selection
6. Collect external service credentials for sandbox testing
7. Generate coding principles (universal + project-specific)
8. Write to `forge-decisions.json` → `technical_spikes` + `coding_principles`

**Quality gate**: All spikes confirmed or marked TBD.

**Completion**: `forge-decisions.json` has `technical_spikes` array.

---

## Phase 2: Project Setup

**Purpose**: Split sub-projects, select tech stacks, assign modules.

**Entry**: Load and execute `./skills/project-setup.md`.

**Steps**: See project-setup.md workflow (Step 0 through Step 5).

**Quality gate**:
- >= 1 sub-project defined
- Each sub-project has a template_id
- 100% module coverage

**Completion**: `.allforai/project-forge/project-manifest.json` exists.

---

## Phase 3: Design to Spec + Shared Utilities

**Purpose**: Generate requirements + design + tasks per sub-project.

**Entry**: Load and execute `./skills/design-to-spec.md`.

**Parallel execution**:
- Phase A: Backend architect generates specs (sequential)
- Phase B: Frontend sub-projects generate specs in parallel (after backend design.md is ready)
- Step 7: Shared utilities analysis + B1 task injection

**Quality gate**:
- Each sub-project has requirements.md + design.md + tasks.md
- `shared-utilities-plan.json` exists
- All CORE tasks appear in tasks.md

**Completion**: Sub-project spec directories populated + `shared-utilities-plan.json`.

---

## Phase 4: Task Execution

**Purpose**: Execute atomic tasks from tasks.md with progress tracking.

**Entry**: Load and execute `./skills/task-execute.md`.

**Pre-check (full mode)**: Verify source code directories are empty. If old code exists, backup to `.pre-forge-bak`.

**Steps**:
- Step 0: Initialize build-log, group tasks into Rounds, auto-split large Rounds
- Step 0.5: Generate .env files for all sub-projects
- Per Round:
  - Step 1: Infer execution strategy (serial vs parallel)
  - Step 1.5-1.9: Context injection, API contract binding, read-before-write
  - Step 2: Execute tasks (delegate to coding agents)
  - Step 3: Quality checks (lint + test + security, in parallel)
  - Step 4: Incremental verification (existence + correctness CC1-CC7)

**Progress tracking**: Check `.allforai/project-forge/build-log.json` for round/task status.

**Quality gate**: CORE tasks completed, lint passing.

**Completion**: `build-log.json` exists with CORE tasks marked completed.

---

## Phase 4.5: Seam Gate + Depth Audit

**Purpose**: Verify frontend-backend connections before test phase.

**Steps**:
1. Start all sub-project dev servers
2. Execute in parallel: deadhunt static + fieldcheck full
3. Fix critical issues
4. Auth chain end-to-end verification
5. Seam smoke test + UI performance baseline (Playwright)
6. Depth audit: verify callbacks, data bindings, core feature completeness

**Quality gate**:
- deadhunt critical = 0
- fieldcheck critical = 0
- Core pages pass seam smoke test
- Core page first-data-visible < 5s (WARNING only above threshold)

**Completion**: All critical seam issues resolved.

---

## Phase 5: Verification Loop (4-Agent Parallel Scan)

**Purpose**: Full verification + completeness check + fix loop.

**Pre-check**: `build-log.json` must exist with at least one completed Round.

**Steps**:

Step 0.5: Abstraction gate (code-tuner Phase 2+3 on modified files)

Step 1: Dispatch 4 parallel agents:
- Agent 1: product-verify full (load `./skills/product-verify.md`)
- Agent 2: testforge E2E chain (load `./commands/testforge.md`)
- Agent 3: deadhunt static/full (load `./commands/deadhunt.md`)
- Agent 4: fieldcheck full (load `./commands/fieldcheck.md`)

Step 1.5: LLM smoke test generation + execution (runtime verification)

Step 2: Aggregate findings from all 4 agents + smoke tests

Step 3: Generate fix tasks (IMPLEMENT / FIX_FAILING / FIX_REQUIRED / deadhunt / fieldcheck)

Step 4: Execute fix round via task-execute

Step 5: Regression verification (scope mode on fixed task_ids)

**Quality gate**:
- verify-tasks.json: IMPLEMENT + FIX_FAILING = 0
- testforge: FIX_REQUIRED = 0
- deadhunt: no critical issues
- fieldcheck: no critical issues
- smoke-test: no FAIL

**Phase status values**: `completed` | `static_pass` | `not_tested` | `in_progress`

**Completion**: All verification artifacts exist with passing status.

---

## Phase 6: Demo Handoff

**Purpose**: Design demo data plan after code stabilizes.

**Action**: Prompt user to run demo-forge design (separate plugin).

**Quality gate**: `.allforai/demo-forge/demo-plan.json` exists (or user skips).

---

## Phase 7: Cross-Platform Verification (Conditional)

**Purpose**: E2E chain verification when Phase 5 did not achieve `completed` status.

**Condition**:
- Phase 5 `completed` → skip Phase 7
- Phase 5 `static_pass` / `not_tested` / `skipped` → must execute Phase 7

**Entry**: Load and execute `./commands/testforge.md` (Phase 4 Path B: E2E chain).

**Prerequisites**: All sub-project applications running.

**Quality gate**: E2E pass rate >= 80%.

---

## Phase 8: Final Report

**Purpose**: Aggregate all phase results into a comprehensive report.

**Output**:
- `.allforai/project-forge/forge-report.json` (machine-readable)
- `.allforai/project-forge/forge-report.md` (human-readable summary)

**Report sections**:
1. Execution summary (mode, sub-projects, task counts)
2. Phase status table (all 8 phases with quality gate results)
3. Sub-project status (type, stack, tasks, completion rate, E2E)
4. Pending items (DEFER tasks, E2E failures, NOT_TESTED items)
5. Negative space supplements (development-phase discoveries)
6. Next actions checklist
7. Output file index

---

## Mode Differences: New vs Existing

| Aspect | New (full) | Existing |
|--------|-----------|----------|
| Phase 1 spikes | Full research | Check existing deps first, skip covered spikes |
| Phase 2 setup | From scratch | Scan code, detect gaps |
| Phase 3 specs | Full generation | Gap-aware generation |
| Phase 4 source dirs | Must be empty (backup old code) | Work on existing code |
| Phase 4 execution | From Round 0 | Incremental |

---

## Resume Protocol

Resume detects the last completed phase from `forge-decisions.json` → `phase_status` and restarts from the first non-completed phase. Per-phase resume:

- **Phase 3**: Check each sub-project for requirements.md + design.md + tasks.md. Only regenerate missing.
- **Phase 4**: Read `build-log.json`, resume from first incomplete Round.
- **Phase 5**: Re-run verification if artifacts are stale (modified after last verification).

---

## Consumer/Mixed Mode

When `experience_priority.mode = consumer | mixed`:
- Phase 3: Must include user maturity requirements in frontend specs
- Phase 4: Cannot accept "page opens + API responds" as completion
- Phase 5: Must verify user-facing maturity (main flow, state system, feedback, retention hooks)
- Consumer apps identified in `forge-decisions.json` → `consumer_apps`
