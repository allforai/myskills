---
description: "Demo forge full pipeline: design → media → execute → verify, multi-round iteration to 95% pass rate. Modes: full / design / media / execute / verify / clean / status"
---

# Demo Forge — Full Pipeline Orchestration

## Mode Detection

Determine the workflow mode from the user's natural language:

- **No specific request or "full"** → full pipeline: Phase 0 → 1 → 2 → 3 → 4 → (4.5) → 5
- **"design" or "plan demo data"** → design only: Phase 0 → 1
- **"media" or "collect images"** → media only: Phase 0 → 2
- **"execute" or "populate data"** → execute only: Phase 0 → 3
- **"verify" or "check demo"** → verify only: Phase 0 → 4
- **"clean"** → load demo-execute clean mode, remove populated data
- **"status"** → scan artifacts, report completion status per phase

## Execution Flow

1. Read the file at `./SKILL.md` for the complete workflow overview and skill descriptions
2. Read the file at `./execution-playbook.md` for orchestration rules, phase transitions, quality gates, and iteration logic
3. Execute Phase 0 (pre-flight checks, capability detection, runtime info collection)
4. Load phase-specific skill files as needed during execution
5. Enforce quality gates between phases -- do not skip
6. Display the final report summary in the conversation

## Reference Documents (load as needed)

- `./SKILL.md` -- workflow overview, skill descriptions, output structure
- `./execution-playbook.md` -- orchestration rules, phase transitions, iteration logic
- `./skills/demo-design.md` -- Phase 1: data plan design
- `./skills/media-forge.md` -- Phase 2: media acquisition + processing + upload
- `./skills/demo-execute.md` -- Phase 3: data generation + population
- `./skills/demo-verify.md` -- Phase 4: Playwright verification + issue routing
- `./docs/media-processing.md` -- media processing command reference

## Phase 0 Pre-flight (mandatory for all modes)

### Upstream Check

Verify product-map artifacts exist:
- `.allforai/product-map/task-inventory.json` (required)
- `.allforai/product-map/role-profiles.json` (required)

Missing → abort, tell the user to run product-map first.

### Artifact Scan for Resume

Check `.allforai/demo-forge/` for existing artifacts:

| Artifact | Phase | Complete When |
|----------|-------|---------------|
| `demo-plan.json` | Phase 1 | File exists with non-empty entities array |
| `assets-manifest.json` + `upload-mapping.json` | Phase 2 | Both exist, `external_url_count=0` |
| `forge-data.json` | Phase 3 | File exists with non-empty records array |
| `verify-report.json` | Phase 4 | File exists |

For full mode, skip already-completed phases (show one-line summary). For single-phase modes, always execute.

### Runtime Info Collection

For execute / verify / full modes, gather:
- **Application URL**: Ask the user for the application URL (e.g., `http://localhost:3000`)
- **Login credentials**: Reuse from `demo-plan.json` if available, otherwise ask

## Phase Execution

For each phase, load the corresponding skill file for detailed rules and steps.

Quality gates between phases are mandatory -- do not proceed if gate fails.

Between phases, do not ask for confirmation. Proceed automatically after Phase 0 info collection.

## Report Output Requirements (mandatory)

After completing the pipeline, display the final report directly in the conversation:

```
=== Demo Forge Completion Report ===

Iteration rounds: {total_rounds}
Pass rate progression: Round 0 ({rate_0}%) → ... → Round N ({rate_n}%)
Final pass rate: {final_rate}% (excluding DEFERRED_TO_DEV)
DEFERRED_TO_DEV tasks: {dev_task_count}
Known issues: {known_issue_count}

Demo Login Credentials:
| Role | Username | Password | Entry URL |
|------|----------|----------|-----------|
| ... | ... | ... | ... |

> Full artifacts: .allforai/demo-forge/
```

Do NOT just say "report saved". Show the summary with actionable details.
