# Demo Forge — Execution Playbook

Phase orchestration for the demo forge pipeline. Target: **95% verification pass rate** when runtime access and verification tooling are available.
When they are not, the workflow must record reduced coverage and unresolved runtime-dependent scope explicitly.

---

## Phase 0: Detection + Initialization

### 0-A Upstream Check

Required files:
```
.allforai/product-map/task-inventory.json
.allforai/product-map/role-profiles.json
```
Missing -> abort, prompt to run product-map first.

### 0-B Artifact Scan

Scan `.allforai/demo-forge/` to determine phase completion:

| Artifact | Phase | Complete When |
|----------|-------|---------------|
| `demo-plan.json` | 1 Design | File exists, entities array non-empty |
| `assets-manifest.json` + `upload-mapping.json` | 2 Media | Both exist, `external_url_count=0` |
| `forge-data.json` | 3 Execute | File exists, records array non-empty |
| `verify-report.json` | 4 Verify | File exists |

### 0-C External Capability Check

| Capability | Importance | Degradation |
|-----------|------------|-------------|
| Playwright | Phase 4 required | Block verify, prompt install |
| Brave Search | Phase 2 recommended | Degrade to web search |
| AI Image Gen | Phase 2 optional | Imagen 4 -> GPT-5 Image -> FLUX 2 Pro -> skip |
| AI Video Gen | Phase 2 optional | Veo 3.1 -> Kling -> skip |

### 0-D Initialize

- Ensure `.allforai/demo-forge/` directory exists
- Initialize or update `round-history.json`

### 0-E Runtime Info Collection

For `execute` / `verify` / `full` modes, collect:
- **Application URL** (e.g., `http://localhost:3000`) — check `round-history.json` first, assume localhost:3000 if not found, declare the assumption
- **Login credentials** — reuse from `demo-plan.json` if available

Write collected info to `round-history.json` `runtime_config`.

---

## Phase 1: Design

Load skill: `skills/demo-design.md`

Execute full workflow (Step 0 -> Step 2.5).

**Quality Gate:**
- `demo-plan.json` exists
- `demo-plan.json` entities array length > 0
- Every entity has `records_count > 0`

PASS -> Phase 2 | FAIL -> abort with report

---

## Phase 2: Media

Load skill: `skills/media-forge.md`

**Pre-check:**
- `demo-plan.json` must exist
- If no media fields in plan -> skip Phase 2, proceed to Phase 3

Execute full pipeline (M1 -> M6).

**Quality Gate:**
- `assets-manifest.json` exists
- `upload-mapping.json` exists
- `upload-mapping.json` `validation.external_url_count === 0`
- No `UPLOAD_FAILED` status

PASS -> Phase 3 | FAIL -> abort with report

---

## Phase 3: Execute

Load skill: `skills/demo-execute.md`

**Pre-check:**
- `demo-plan.json` must exist
- If media fields exist: `upload-mapping.json` must exist
- Application URL must be collected (Phase 0-E)

Execute full workflow (E1 -> E4).

**Quality Gate:**
- `forge-data.json` exists
- `forge-data.json` record count > 0
- No `CHAIN_FAILED` in `forge-log.json`

PASS -> Phase 4 | FAIL -> abort with report

---

## Phase 4: Verify

Load skill: `skills/demo-verify.md`

**Pre-check:**
- `forge-data.json` must exist
- Application URL must be accessible

Execute full verification (V1 -> V8).

**Quality Gate:**
- `verify-report.json` exists
- Target `pass_rate >= 95%` (excluding `DEFERRED_TO_DEV`) when verify coverage is available
- If verify coverage is reduced by missing runtime or optional tooling, record achieved pass rate plus untestable scope explicitly

PASS -> Phase 5 | FAIL -> Phase 4.5

---

## Phase 4.5: Iterative Fix (max 3 rounds)

### 4.5-A Read Issues

Read `verify-issues.json`, group by `route_to`:

| route_to | Action |
|----------|--------|
| `design` | Re-enter `skills/demo-design.md` (incremental) |
| `media` | Re-enter `skills/media-forge.md` (incremental) |
| `execute` | Re-enter `skills/demo-execute.md` (incremental) |
| `dev_task` | Generate B-FIX tasks, mark DEFERRED_TO_DEV |
| `skip` | Record but do not process |

### 4.5-B Execute Fixes

Process in order: design -> media -> execute -> dev_task.

### 4.5-C Regression Verify

Re-run `skills/demo-verify.md`:
- Scope: fixed items + regression sampling
- Skip DEFERRED_TO_DEV items

### 4.5-D Iteration Control

- `pass_rate >= 95%` -> Phase 5
- `pass_rate < 95%` and round < 3 -> back to 4.5-A
- round >= 3 -> output remaining as known issues, proceed to Phase 5

### 4.5-E Update History

Update `round-history.json` with phases executed, issues addressed, verify results.

---

## Phase 5: Final Report

### 5-A Summary

```
=== Demo Forge Completion Report ===

Iteration rounds: {total_rounds}
Pass rate trend: Round 0 ({rate_0}%) -> ... -> Round N ({rate_n}%)
Final pass rate: {final_rate}% (excluding DEFERRED_TO_DEV)
Untestable scope: {untestable_scope_count}
DEFERRED_TO_DEV tasks: {dev_task_count}
Known issues (unresolved): {known_issue_count}
```

### 5-B Login Credentials Table

Extract role accounts from `demo-plan.json`:

```
| Role | Username | Password | Entry URL |
|------|----------|----------|-----------|
```

### 5-C Update round-history.json

Write final status: `passed | passed_with_known_issues | max_rounds_reached`.

---

## round-history.json Structure

```json
{
  "runtime_config": {
    "app_url": "http://localhost:3000",
    "collected_at": "ISO8601"
  },
  "rounds": [
    {
      "round": 0,
      "started_at": "ISO8601",
      "phases_executed": ["design", "media", "execute", "verify"],
      "verify_result": {
        "total_checks": 86,
        "passed": 71,
        "failed": 15,
        "deferred_to_dev": 2,
        "pass_rate": "82.6%"
      }
    }
  ],
  "final_status": "passed",
  "total_rounds": 2,
  "dev_tasks_generated": 2,
  "known_issues": []
}
```

---

## Iron Rules

1. **Quality gates are mandatory** — each phase must pass before the next begins, or report why a runtime-dependent gate could not be fully exercised
2. **Orchestrator is navigator** — load skill files, do not implement logic directly
3. **`.allforai/` is the contract** — all artifacts read/write through `.allforai/demo-forge/`
4. **User can abort at any phase** — re-run `full` mode to restart
5. **`dev_task` does not block iteration** — code bugs route to dev-forge, demo-forge continues its own loop
