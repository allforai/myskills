# Product Design — Execution Playbook

> 10-phase orchestration: concept -> requirements -> map -> journey -> experience-map -> gate -> feature-gap -> design-audit — with explicit transition logic, parallel phase support, and verify loop protocol.

---

## Overview

This playbook defines the full product-design pipeline executed by the `product-design full` workflow. It is the detailed companion to `./commands/product-design.md` (which defines mode routing, phase summaries, and iron rules). This document focuses on **transition logic**, **artifact detection**, **parallel execution**, and **verify loop mechanics**.

---

## Phase Map (10 Phases)

```
Phase 0   Artifact Detection + Capability Scan
Phase 1   Product Concept (optional)
Phase 1.5 Concept Verify + Baseline Distillation
Phase 1.6 Requirements Confirmation (auto — Stage A→B→C, outputs requirements-brief.json)
Phase 2   Product Map
Phase 2.5 Map Verify + Consumer Maturity Audit
Phase 3   Journey Emotion
Phase 3.5 Journey Verify
Phase 4   Experience Map + Interaction Gate
Phase 4.5 Experience Verify
Phase 5   Feature Gap
Phase 5.5 Feature Gap Verify
Phase 6   Design Audit (Final)
```

---

## Phase 0: Artifact Detection + Capability Scan

### 0.1 Artifact Detection

Scan `.allforai/` directories to determine completion status of each phase:

| Phase | Artifact | Complete When |
|-------|----------|---------------|
| 1 | `.allforai/product-concept/` | directory exists |
| 1.5 | `.allforai/product-concept/concept-baseline.json` | file exists |
| 2 | `.allforai/product-map/task-inventory.json` | exists AND task count > 0 |
| 3 | `.allforai/experience-map/journey-emotion-map.json` | file exists |
| 4 | `.allforai/experience-map/experience-map.json` | exists AND screen count > 0 |
| 4 gate | `.allforai/experience-map/interaction-gate.json` | file exists |
| 5 | `.allforai/feature-gap/gap-tasks.json` | file exists |
| 6 | `.allforai/design-audit/audit-report.json` | file exists |

### 0.2 Mode Resolution

| User Input | Behavior |
|------------|----------|
| `full` or no args | Start from Phase 1 (or Phase 2 if `skip: concept`) |
| `resume` | Start from first incomplete phase |

### 0.3 Product Scale Pre-check

Before Phase 1, estimate product scale from user input (PRD/code/description):

| Scale | Roles | Modules | Action |
|-------|-------|---------|--------|
| Standard | 1-4 | 1-15 | Proceed normally |
| Large | 5-8 | 16-30 | Warn user, proceed (skills auto-batch) |
| Extra-large | >8 | >30 | Ask user whether to split into 2-3 independent products |

If user chooses to split, record in `.allforai/product-concept/scope-decisions.json` and execute Phase 1 for the first sub-product only.

### 0.4 External Capability Scan

Detect availability of external services. This is informational only — never blocks execution.

| Capability | Detection | Importance |
|------------|-----------|------------|
| OpenRouter (MCP) | `mcp__openrouter__ask_model` availability | Optional |
| OpenRouter (Script) | `OPENROUTER_API_KEY` env var | Optional |
| Stitch UI | `mcp__stitch__create_project` availability | Optional |
| Playwright | `mcp__playwright__browser_navigate` availability | Optional |
| 网络搜索 | Built-in, always available | Core |

Output a one-line-per-capability status table, then confirm execution plan.

### 0.5 Auto-mode Detection

After Phase 1 (product-concept), check `.allforai/product-concept/product-concept.json` for `pipeline_preferences` field:
- **Present** → Enable auto-mode: subsequent phases use three-tier checkpoint evaluation (ERROR/WARNING/PASS)
- **Absent** → Interactive mode (default behavior)

---

## Transition Protocol (applies to all phases)

### Verify Loop Template

Every generation phase runs the same verify pattern:

```
loop (max 3 rounds):
  1. python3 ../../shared/scripts/product-design/verify_review.py <BASE> --phase <PHASE> [--xv]
     → stdout JSON: artifact context + 4D/6V/closure review questions [+ XV cross-model opinion]
  2. LLM reads output, reviews against upstream baseline:
     - 4D: Correct conclusion? Evidence? Constraints identified? Decision grounded?
     - 6V: user/business/tech/ux/data/risk perspectives reasonable?
     - Closure: config/monitoring/exception/lifecycle/mapping/navigation complete?
     - XV (if available): second model opinion valid?
  3. Issues found → auto-fix source files → back to 1
     No issues → exit loop, proceed to next phase
```

### Verification Baseline Chain

| Phase | Current Artifact | Verification Baseline (upstream) |
|-------|-----------------|----------------------------------|
| 1 concept | product-concept.json | User requirements description |
| 2 product-map | task-inventory + business-flows | product-concept.json |
| 3 journey-emotion | journey-emotion-map.json | business-flows.json |
| 4 experience-map | experience-map.json | journey-emotion + task-inventory + entity-model |
| 5 feature-gap | gap-tasks.json | task-inventory + experience-map + business-flows |

### Phase Transition Rules

1. **Zero-pause transitions** — After checkpoint PASS, immediately load next phase skill and execute. Output only a one-line status summary (e.g., `Phase 3 done -> Phase 4`). Never ask "Continue?" or "Ready for next phase?"
2. **ERROR stops** — Only ERROR-level safety rail issues pause for user input
3. **WARNING logs** — Record in `.allforai/pipeline-decisions.json`, display one-line summary, continue
4. **PASS continues** — Auto-proceed with one-line summary

### Auto-mode Checkpoint Evaluation

| Level | Condition | Behavior |
|-------|-----------|----------|
| **ERROR** | Required field missing, reference broken, task count = 0, required file absent | **Stop and ask user**, show error details |
| **WARNING** | Recommended field missing, coverage below expectation, minor inconsistency | Log to `pipeline-decisions.json` (`decision: "auto_continued"`), show one-line, continue |
| **PASS** | All checks pass | Continue, show one-line summary |

---

## Phase 1: Product Concept (optional)

**Skip conditions**: User specified `skip: concept`, or resume mode with concept already complete.

**Execute**:
1. Load `./skills/product-concept.md`
2. Run the complete product-concept workflow

**Checkpoint**: concept output directory exists.

### Phase 1 — Step 2: concept-verify

Run unified verify loop (`--phase concept`).

**Closure focus**:
- pain-reliever bidirectional mapping
- gain-creator bidirectional mapping
- mechanism-JTBD mapping: any orphaned mechanisms?
- revenue-value mapping

### Phase 1 — Step 3: Concept Baseline Distillation

After verify loop passes, auto-extract compact baseline:

1. Read `.allforai/product-concept/product-concept.json` + `role-value-map.json` + `product-mechanisms.json`
2. LLM extracts fields per `skill-commons.md` fixed schema → `.allforai/product-concept/concept-baseline.json`
3. Keep under 2KB

**Checkpoint**: `concept-baseline.json` exists with `mission`, `roles`, `governance_styles` fields.

---

## Phase 1-2: pipeline-decisions Write

After concept and product-map complete, append to `.allforai/pipeline-decisions.json`:

```json
{"phase": "Phase 1 — concept", "decision": "auto_confirmed", "detail": "concept generated", "decided_at": "..."}
{"phase": "Phase 2 — product-map", "decision": "auto_confirmed", "detail": "tasks=N, roles=M, flows=K", "decided_at": "..."}
```

Deduplicate by `phase` field — re-runs replace existing entries.

---

## Phase 1.6: Requirements Confirmation

Skill: `./skills/requirements.md`

Auto-triggered after concept-baseline.json is written. No user action needed to start it.

Skip conditions:
- `.allforai/product-concept/requirements-brief.json` exists AND `confirmed_status` is `fully_confirmed` or `partially_confirmed` → skip (already confirmed)
- User explicitly passes `skip: requirements` → skip with warning

Stage sequence:
- Stage A: present core paths → wait for explicit confirmation
- Stage B: present standard modules → wait for explicit confirmation
- Stage C: ask up to 5 multiple-choice boundary questions

Output: `.allforai/product-concept/requirements-brief.json`

---

## Phase 2: Product Map

**Execute**:
1. Load `./skills/product-map.md`
2. Run complete product-map workflow
3. Append pipeline-decisions record (auto-mode)

**Checkpoint**:
- `task-inventory.json` exists, task count > 0
- `task-inventory-basic.json` and `task-inventory-core.json` exist
- Each task has `category` field (basic or core)
- `product-map.json` exists with `experience_priority` field (if product has consumer/mobile surface)

**Auto-mode**: task count = 0 → ERROR; category missing → WARNING; `experience_priority` missing with consumer surface → ERROR; otherwise → PASS.

### Phase 2 — Step 2: map-verify

Run verify loop (`--phase map`).

**Closure focus**:
- Four closure audits: config/monitoring/exception/lifecycle for each functional task
- mechanism-task mapping: every concept mechanism has corresponding task?
- task-flow mapping: high-frequency tasks appear in at least one business flow?

**Consumer maturity audit** (when `experience_priority.mode = consumer` or `mixed`):

LLM self-audit checklist (answer yes/no for each):
- User tasks only have "browse/submit/view" with no onboarding, ongoing relationship, progress tracking, recommendations, or incentives?
- Core objects only have CRUD without lifecycle flow (draft->active->complete->review->archive)?
- Missing notifications/reminders/history/return triggers?
- Business flows only have happy path without interruption recovery, failure retry, wait-for-feedback?

Issues found → verify loop failure → LLM thickens task-inventory and business-flows, then re-verify.

---

## Phase 3: Journey Emotion

**Step 1: Generate**
1. Load `./skills/journey-emotion.md`
2. Run complete journey-emotion workflow

**Step 2: Verify loop** (`--phase journey`)

**Closure focus**:
- Low-point-recovery closure: every emotional valley has intervention and recovery node?
- Journey start-end closure: clear endpoints? Positive ending emotion? (Peak-End Rule)
- Failure-continue closure: high-risk node failure can return to normal flow?

---

## Phase 4: Experience Map + Interaction Gate

### Phase 4 — Step 1: Generate

Load `./skills/experience-map.md`, execute per skill workflow. LLM leads screen design.

### Phase 4 — Step 1.5: Verify loop (`--phase experience`)

**Closure focus**:
- Navigation closure: every screen reachable and escapable, no dead ends
- State machine closure: every state has exit transition, no state deadlocks
- Error-recovery closure: every fallible operation has recovery path
- task-screen mapping closure: all core tasks have corresponding screens

### Phase 4 — Step 2: Interaction Gate

1. Load `./skills/interaction-gate.md`, execute per workflow
2. LLM analyzes experience-map + task-inventory, identifies interaction risks, generates gate report

**Checkpoint**: `.allforai/experience-map/interaction-gate.json` exists.

---

## Phase 5: Feature Gap

**Execute**:
1. Load `./skills/feature-gap.md`
2. Run complete feature-gap workflow
3. Output to `.allforai/feature-gap/`

**Checkpoint**: `gap-tasks.json` exists.

**Verify loop** (`--phase feature-gap`):

**Closure focus**:
- State machine reversibility: every reject/fail state has retry path?
- Exception coverage: high-frequency task exceptions handled?
- task-screen coverage: all core tasks have screens in experience-map?

---

## Phase 6: Design Audit (Final)

> Removed phases: wireframe generation/validation, use-case (task-inventory already contains use cases), ui-design (generated on demand in dev phase).

**Execute**:
1. Load `./skills/design-audit.md`

### Phase A (Script, serial): Deterministic checks

```bash
python3 ../../shared/scripts/product-design/gen_design_audit.py <BASE> [--mode auto]
```

Script runs trace, coverage, cross-check, continuity, fidelity, XV.
Output: `.allforai/design-audit/audit-report.json` (baseline report).

### Phase B (LLM, 3 parallel subagents): Semantic audit

Launch 3 subagents in parallel (if platform supports subagents; otherwise sequential):

| Subagent | Audit Dimension | Corresponding Steps | Shard File |
|----------|----------------|---------------------|------------|
| 1 | Pattern consistency + Innovation fidelity | Step 5 + Step 5.5 | `audit-shard-pattern.json` |
| 2 | Behavioral consistency | Step 5.6 | `audit-shard-behavioral.json` |
| 3 | Interaction type consistency | Step 5.7 | `audit-shard-interaction.json` |

Each subagent:
- Reads `audit-report.json` (Phase A baseline, read-only)
- Reads relevant upstream artifacts
- Writes its shard file
- Must NOT modify `audit-report.json` or other shards

### Phase C (Merge): Consolidated report

After all subagents complete:
1. Read baseline `audit-report.json` + 3 shard files
2. Merge shard sections into main report summary and issues
3. Regenerate `audit-report.md` (all dimensions)
4. Delete shard files

**quick mode**: Phase A only, skip Phase B/C.

**Auto-mode**: Audit executes normally. CONFLICT issues highlighted in summary. Auto-mode does not stop at final audit, but summary lists total accumulated WARNING count.

---

## Full Pipeline Execution Summary (mandatory output)

After all phases complete, output:

```
## Product Design Pipeline Summary

> Mode: {full/resume}
> Time: {start} — {end}

### Phase Status

| Phase | Stage | Status | Notes |
|-------|-------|--------|-------|
| 1 | concept | done/skipped | verify loop: X rounds |
| 2 | product-map | done | tasks: X, verify loop: X rounds |
| 3 | journey-emotion | done | — |
| 4 | experience-map | done | screens: X |
| 5 | feature-gap | done | gaps: X |
| 6 | design-audit | done | see final report |

### Final Audit Scores

- Trace: X ORPHAN
- Coverage: XX%
- Cross-check: X CONFLICT / X WARNING

### Output Files

> All artifacts in `.allforai/`
> Final report: `.allforai/design-audit/audit-report.md`
```

---

## Iron Rules

1. **Load skill per phase** — Do not skip steps or simplify flows. Execute each skill's complete workflow.
2. **Checkpoints must verify** — Validate artifact existence after each phase. Report failures to user.
3. **User can abort at any phase** — On checkpoint failure or user abort, save existing artifacts, output partial summary.
4. **Verify loop does not replace final audit** — Phase-internal verify loops ensure content correctness; comprehensive validation is Phase 6 design-audit's job.
5. **Read-only for upstream in design pipeline** — Later phases report upstream issues but do not auto-modify upstream artifacts. Exception: dev phase can back-fill upstream per reverse-backfill protocol (skill-commons section 5).
6. **Zero-pause phase transitions** — Never stop between phases to ask "Continue?" or "Review first?" After checkpoint PASS, immediately load and execute next phase skill. Only show one-line status. The only allowed pause is ERROR-level safety rail. Artifact review is optional (user can invoke `/review` anytime); orchestrator never proactively asks whether to review.
