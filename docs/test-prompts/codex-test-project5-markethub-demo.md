# Codex Test — Project 5: MarketHub Demo Forge

## Context

You are testing the myskills plugin suite on the Codex platform. Plugins at `/path/to/myskills/codex/`.

Test project directory: `test-markethub-demo/`

## Goal

Validate the `demo-forge` plugin as a realistic demo-environment workflow:

- design believable demo data
- handle media fields with graceful degradation
- populate the app with deterministic but realistic records
- verify the result with iteration and issue routing

## Project Description

MarketHub is a marketplace product with both buyer-facing and operator-facing surfaces.

Available upstream state:
- `.allforai/product-map/task-inventory.json`
- `.allforai/product-map/role-profiles.json`
- `.allforai/product-map/business-flows.json`
- optional `.allforai/experience-map/experience-map.json`
- application code is complete
- application is running at `http://localhost:3000`

Core entities:
- users
- stores
- products
- categories
- carts
- orders
- payments
- reviews
- coupons
- banners

Media-heavy fields:
- store logo
- store cover image
- product gallery
- homepage banners

## Task

Read these files first:

- `codex/demo-forge-skill/AGENTS.md`
- `codex/demo-forge-skill/execution-playbook.md`
- `codex/demo-forge-skill/SKILL.md`

Then execute a thought-experiment run of `demo-forge full`.

## Expected Flow

1. Phase 0: detect prerequisites, runtime info, and external capabilities
2. Phase 1: generate `demo-plan.json`
3. Phase 2: generate media outputs or degrade gracefully when external tools are absent
4. Phase 3: generate and populate realistic demo data
5. Phase 4: verify using the verification workflow
6. If pass rate is below target, route issues by source phase and iterate

## Expected Output Artifacts

```text
.allforai/demo-forge/demo-plan.json
.allforai/demo-forge/assets-manifest.json
.allforai/demo-forge/upload-mapping.json
.allforai/demo-forge/forge-data.json
.allforai/demo-forge/forge-log.json
.allforai/demo-forge/verify-report.json
.allforai/demo-forge/verify-issues.json
.allforai/demo-forge/round-history.json
```

## Quality Criteria

- `demo-plan.json` covers all core entities and business chains
- media handling follows documented degradation chains instead of hard failing immediately
- `forge-data.json` contains realistic, cross-linked records
- verification targets `pass_rate >= 95%` excluding `DEFERRED_TO_DEV` when runtime/tool coverage is available
- if runtime/tool coverage is reduced, the workflow should report achieved pass rate plus untestable scope instead of claiming a full pass
- routing semantics are clear:
  - `design`
  - `media`
  - `execute`
  - `dev_task`
  - `skip`

## Acceptance Notes

- This is a scenario test, not a deterministic golden-output test
- Record lower-bound or shape-based expectations, not exact counts
- The workflow should assume reasonable defaults and declare them
- It should ask only when runtime information is truly blocking
