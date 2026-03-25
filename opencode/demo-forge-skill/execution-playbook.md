# Demo Forge Execution Playbook

Detailed orchestration guide for the demo-forge workflow on OpenCode.

## When to Use

Use this workflow when the user wants to:
- prepare a demo-ready environment with realistic data
- design demo data plans from product-map artifacts
- acquire and upload media assets for demo
- populate an application with demo data
- verify demo data quality with Playwright

Do NOT use it for:
- generating development seed data (use dev-forge seed-forge instead)
- testing or QA (use dev-forge e2e-verify instead)
- production data migration

## Phase Table

| Phase | Goal | Outputs | Completion Signal |
|-------|------|---------|-------------------|
| 0 | Pre-flight + init | `round-history.json` initialized | Upstream check passed, capabilities detected |
| 1 | Data plan design | `demo-plan.json`, `model-mapping.json`, `api-gaps.json`, `style-profile.json` | `demo-plan.json` exists with entities count > 0 |
| 2 | Media acquisition | `assets/`, `assets-manifest.json`, `upload-mapping.json` | `upload-mapping.json` exists with `external_url_count=0` |
| 3 | Data population | `forge-data-draft.json`, `forge-data.json`, `forge-log.json` | `forge-data.json` exists with records count > 0 |
| 4 | Playwright verify | `verify-report.json`, `verify-issues.json`, `screenshots/` | `verify-report.json` exists |
| 4.5 | Iterative fix | Updated artifacts per route | pass_rate >= 95% or max 3 rounds |
| 5 | Final report | Updated `round-history.json` | Report displayed in conversation |

## Mode Routing

Determine execution mode from the user's natural language:

| User intent | Mode | Phases |
|-------------|------|--------|
| "demo forge", "full demo", no specific request | full | 0 → 1 → 2 → 3 → 4 → (4.5) → 5 |
| "design demo data", "plan demo" | design | 0 → 1 |
| "collect media", "demo images" | media | 0 → 2 |
| "populate demo", "fill data" | execute | 0 → 3 |
| "verify demo", "check demo quality" | verify | 0 → 4 |
| "clean demo data" | clean | Load demo-execute clean mode |
| "demo status" | status | Scan artifacts, report progress |

## Phase 0: Pre-flight + Initialization

### 0-A Upstream Check

product-map artifacts must exist:
```
.allforai/product-map/task-inventory.json  # required
.allforai/product-map/role-profiles.json   # required
```
Missing → abort, tell the user to run product-map first.

### 0-B Artifact Scan

Scan `.allforai/demo-forge/` for existing artifacts to determine phase completion:

| Artifact | Phase | Complete When |
|----------|-------|---------------|
| `demo-plan.json` | Phase 1 Design | File exists with non-empty entities array |
| `assets-manifest.json` + `upload-mapping.json` | Phase 2 Media | Both exist with `external_url_count=0` |
| `forge-data.json` | Phase 3 Execute | File exists with non-empty records array |
| `verify-report.json` | Phase 4 Verify | File exists |

### 0-C External Capability Detection

Detect external capabilities and output status:

| Capability | Detection | Importance | Degradation |
|------------|-----------|------------|-------------|
| Playwright | `mcp__playwright__browser_navigate` tool available | Phase 4 required | Block verify, prompt install |
| Brave Search | `brave_web_search` available or `BRAVE_API_KEY` set | Phase 2 recommended | Degrade to 网络搜索 |
| AI Image Gen | `generate_image` / `openrouter_generate_image` / `flux_generate_image` any available | Phase 2 optional | Imagen 4 → GPT-5 Image → FLUX 2 Pro → skip |
| AI Video Gen | `generate_video` / `kling_generate_video` any available | Phase 2 optional | Veo 3.1 → Kling → skip |

Output format:
```
External capabilities:
  Playwright     ✓ ready     Verification (Phase 4 required)
  Brave Search   ✗ not ready Media search (degrade to 网络搜索)
  AI Image Gen   ✗ not ready Imagen 4 / GPT-5 Image / FLUX 2 Pro (degrade to search)
  AI Video Gen   ✗ not ready Veo 3.1 / Kling (degrade to Playwright recording)
```

Interactive install guidance:
- **Playwright not ready + full/verify mode**: Ask the user "Playwright is required for verification. Would you like me to install it, skip verification, or see details?"
- **Playwright not ready + design/media/execute mode**: One-line notice only, do not block
- **Brave/Google AI not ready**: Suggest running setup to configure API keys

### 0-D Initialization

- Ensure `.allforai/demo-forge/` directory exists
- Initialize or update `round-history.json` (create empty structure if missing)

### 0-E Runtime Info Collection

For `execute` / `verify` / `full` modes, collect:
- **Application URL**: Ask the user for the application access URL (e.g., `http://localhost:3000`)
- **Login credentials**: Reuse from `demo-plan.json` role accounts if available, otherwise ask

Write collected info to `round-history.json` under `runtime_config`.

## Phase 1: Design (Data Plan)

> Load skill: `./skills/demo-design.md`

### Execution

Load demo-design skill and execute the full workflow (Step 0 → Step 2.5).

### Quality Gate

- `demo-plan.json` exists
- `demo-plan.json` entities array length > 0
- Each entity has `records_count > 0`

**PASS** → proceed to Phase 2
**FAIL** → abort, report missing items

## Phase 2: Media (Acquisition + Processing + Upload)

> Load skill: `./skills/media-forge.md`

### Pre-check

- `demo-plan.json` must exist (Phase 1 complete)
- `demo-plan.json` has media field annotations (Step 1-M output)

No media fields → skip Phase 2, proceed to Phase 3.

### Execution

Load media-forge skill and execute full pipeline (M1 → M6).

### Quality Gate

- `assets-manifest.json` exists
- `upload-mapping.json` exists
- `upload-mapping.json` has `validation.external_url_count === 0` (hard check)
- `upload-mapping.json` has no `UPLOAD_FAILED` status

**PASS** → proceed to Phase 3
**FAIL** → abort, report unmet conditions

## Phase 3: Execute (Data Generation + Population)

> Load skill: `./skills/demo-execute.md`

### Pre-check

- `demo-plan.json` must exist
- If media fields exist: `upload-mapping.json` must exist
- Application URL must be collected (Phase 0-E)

### Execution

Load demo-execute skill and execute full workflow (E1 → E4).

### Quality Gate

- `forge-data.json` exists
- `forge-data.json` record count > 0
- `forge-log.json` has no `CHAIN_FAILED` status (chain-level failure)

**PASS** → proceed to Phase 4
**FAIL** → abort, report population failures

## Phase 4: Verify

> Load skill: `./skills/demo-verify.md`

### Pre-check

- `forge-data.json` must exist
- Application URL must be accessible

### Execution

Load demo-verify skill and execute full verification (V1 → V7).

### Quality Gate

- `verify-report.json` exists
- Exclude `DEFERRED_TO_DEV` items when calculating pass rate
- `pass_rate >= 95%` (excluding DEFERRED_TO_DEV)

**PASS** → proceed to Phase 5 (final report)
**FAIL** → proceed to Phase 4.5 (iterative fix)

## Phase 4.5: Iterative Fix

When verify does not reach 95% pass rate. Max 3 auto-iteration rounds (Round 0 initial + Round 1-2 fix rounds).

### 4.5-A Read Issue List

Read `verify-issues.json`, group by `route_to`:

| route_to | Handling |
|----------|----------|
| `design` | Re-enter `./skills/demo-design.md` (incremental mode, modify only affected parts of demo-plan) |
| `media` | Re-enter `./skills/media-forge.md` (incremental mode, re-acquire/re-process/re-upload problem items) |
| `execute` | Re-enter `./skills/demo-execute.md` (incremental mode, supplement missing/fix derived) |
| `dev_task` | Generate fix tasks, write to `.allforai/project-forge/sub-projects/{name}/tasks.md`, mark `DEFERRED_TO_DEV` |
| `skip` | Record but do not process |

### 4.5-B Execute Fixes by Route

Process groups in order:

1. **design group** → load `./skills/demo-design.md`, pass issue items, incrementally modify `demo-plan.json`
2. **media group** → load `./skills/media-forge.md`, pass issue items, re-acquire/re-process/re-upload
3. **execute group** → load `./skills/demo-execute.md`, pass issue items, supplement/fix
4. **dev_task group** → generate structured tasks (dev-forge tasks.md format), append to project tasks.md B-FIX round. Mark as `DEFERRED_TO_DEV` in demo-forge, do not block own iteration

### 4.5-C Regression Verify

After fixes, re-run verify:
- Load `./skills/demo-verify.md`
- Scope: fixed items + regression (spot-check passed items)
- `dev_task` items skipped (already DEFERRED_TO_DEV)

### 4.5-D Iteration Control

- Check pass rate (excluding DEFERRED_TO_DEV)
- `pass_rate >= 95%` → exit iteration, proceed to Phase 5
- `pass_rate < 95%` and current round < 3 → return to 4.5-A for next round
- Current round >= 3 → output remaining issues as known issues, proceed to Phase 5

### 4.5-E Update Iteration History

After each round, update `round-history.json`:
- Record phases executed this round
- Record issue IDs addressed this round
- Record this round's verify result

## Phase 5: Final Report

### 5-A Summary Table

Display the following summary:

```
=== Demo Forge Completion Report ===

Iteration rounds: {total_rounds}
Pass rate progression: Round 0 ({rate_0}%) → Round 1 ({rate_1}%) → ... → Round N ({rate_n}%)
Final pass rate: {final_rate}% (excluding DEFERRED_TO_DEV)
DEFERRED_TO_DEV tasks: {dev_task_count}
Known issues (unresolved): {known_issue_count}
```

### 5-B Demo Login Credentials Table

Extract role accounts from `demo-plan.json`, display credentials:

```
| Role | Username | Password | Entry URL |
|------|----------|----------|-----------|
| Admin | admin@demo.com | demo123 | {app_url}/admin |
| User | user1@demo.com | demo123 | {app_url}/ |
```

### 5-C Update round-history.json

Write final status:
```json
{
  "final_status": "passed | passed_with_known_issues | max_rounds_reached",
  "total_rounds": 2,
  "dev_tasks_generated": 3,
  "known_issues": []
}
```

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
    },
    {
      "round": 1,
      "started_at": "ISO8601",
      "phases_executed": ["design", "media", "execute", "verify"],
      "issues_addressed": ["VI-001", "VI-002", "VI-003"],
      "verify_result": {
        "total_checks": 86,
        "passed": 82,
        "failed": 2,
        "deferred_to_dev": 2,
        "pass_rate": "97.6%"
      }
    }
  ],
  "final_status": "passed",
  "total_rounds": 2,
  "dev_tasks_generated": 2,
  "known_issues": []
}
```

## Iron Rules

1. **Quality gates are mandatory** — each phase's completion signal must be satisfied before proceeding
2. **Orchestrator is the navigator** — load skill files, do not implement logic directly
3. **`.allforai/` is the inter-layer contract** — all artifacts read/write through `.allforai/demo-forge/`
4. **User can abort at any phase** — to re-execute, run full mode from the beginning
5. **`dev_task` does not block own iteration** — code issues route to dev-forge, demo-forge continues its own iteration loop
