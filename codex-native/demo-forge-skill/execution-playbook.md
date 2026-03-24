# Demo Forge Execution Playbook For Codex Native

This playbook adapts the source `demo-forge` plugin into a Codex-native
workflow while preserving the original `.allforai/demo-forge/` contract.

## When to use

Use this workflow when the user wants to:

- design realistic demo data from product artifacts
- acquire or generate demo media assets
- populate an application with demo-ready records
- verify demo quality through browser-driven review
- iterate until the demo environment is presentation-ready

Do not use it when:

- `.allforai/product-map/` prerequisite artifacts are missing
- the application is not implemented enough to accept data population
- no reachable app URL exists for execute or verify modes

## Workflow modes

| Requested mode | Meaning |
|---|---|
| `full` or unspecified | Run design -> media -> execute -> verify with iteration |
| `design` | Only create or revise the demo data plan |
| `media` | Only acquire, generate, process, and upload media assets |
| `execute` | Only generate and inject demo data |
| `verify` | Only run demo verification |
| `clean` | Remove previously injected demo data according to source workflow |
| `status` | Inspect progress and artifact state without changing outputs |

Treat source slash commands such as `/demo-forge verify` as workflow labels,
not literal commands.

## High-level phases

| Phase | Goal | Primary outputs |
|---|---|---|
| 0 | detect prerequisites, state, and runtime config | `round-history.json` runtime config |
| 1 | demo data design | `demo-plan.json`, `model-mapping.json`, `api-gaps.json` |
| 2 | media pipeline | `assets-manifest.json`, `upload-mapping.json`, `assets/` |
| 3 | data generation and injection | `forge-data.json`, `forge-log.json` |
| 4 | verification | `verify-report.json`, `verify-issues.json`, screenshots |
| 4.5 | iterative repair routing | updated plan, media, execute outputs, or deferred dev tasks |
| 5 | final summary | final state described from existing artifacts |

## Codex orchestration rules

- Keep the original `.allforai/demo-forge/` paths unchanged.
- Treat quality gates as real gates; do not mark a phase complete when its
  output contract is clearly broken.
- Ask the user only for missing runtime information such as app URL or login
  credentials when those are required for execute or verify modes.
- When media or AI tooling is unavailable, downgrade explicitly and record the
  limitation rather than pretending the full pipeline ran.

## Phase 0: Detect state and prerequisites

Objectives:

- confirm required upstream product artifacts exist
- inspect existing demo-forge outputs
- detect external capability readiness
- collect runtime config for execute and verify modes

Required upstream files:

- `.allforai/product-map/task-inventory.json`
- `.allforai/product-map/role-profiles.json`

Runtime requirements:

- execute and verify need a reachable application URL
- verify also needs browser automation capability

Primary output:

- `.allforai/demo-forge/round-history.json`

## Phase 1: Demo design

Primary source:

- `../../demo-forge-skill/skills/demo-design.md`

Objectives:

- derive demo accounts, volume, entity coverage, timeline distribution, and
  business-chain realism from product artifacts and the existing app
- identify model and API mappings
- surface API gaps that block realistic seeding

Outputs:

- `.allforai/demo-forge/demo-plan.json`
- `.allforai/demo-forge/model-mapping.json`
- `.allforai/demo-forge/api-gaps.json`

Quality check:

- `demo-plan.json` exists
- at least one entity is planned
- planned entities have non-zero record targets

## Phase 2: Media pipeline

Primary source:

- `../../demo-forge-skill/skills/media-forge.md`

Objectives:

- gather or generate media assets
- process assets into usable formats
- upload them into the target application when needed
- eliminate external hotlinks from the final mapping

Outputs:

- `.allforai/demo-forge/assets/`
- `.allforai/demo-forge/assets-manifest.json`
- `.allforai/demo-forge/upload-mapping.json`

Downgrade chain:

- Brave Search unavailable -> use ordinary web search
- AI image or video generation unavailable -> rely on search, existing assets,
  or skip unsupported asset classes with explicit reporting

Quality check:

- upload mapping exists
- `external_url_count` is zero
- failed uploads are either retried or explicitly reported

## Phase 3: Execute

Primary source:

- `../../demo-forge-skill/skills/demo-execute.md`

Objectives:

- generate deterministic demo data from the plan
- inject records by API or database strategy
- preserve relationships and derived fields

Outputs:

- `.allforai/demo-forge/forge-data-draft.json`
- `.allforai/demo-forge/forge-data.json`
- `.allforai/demo-forge/forge-log.json`

Quality check:

- injected record count is greater than zero
- chain-level failures are not silently ignored

## Phase 4: Verify

Primary source:

- `../../demo-forge-skill/skills/demo-verify.md`

Objectives:

- verify that the demo data actually renders and behaves correctly
- verify media integrity
- verify list/detail/business-flow realism
- identify issues and route them by repair owner

Outputs:

- `.allforai/demo-forge/verify-report.json`
- `.allforai/demo-forge/verify-issues.json`
- `.allforai/demo-forge/screenshots/`

Quality gate:

- pass rate should be at least 95 percent after excluding `DEFERRED_TO_DEV`
  issues from the denominator

## Phase 4.5: Iterative repair

Use this phase when verification does not meet the target threshold.

Routing model:

- `design` -> revise demo-plan inputs
- `media` -> reacquire, regenerate, or reupload assets
- `execute` -> regenerate or reinject data
- `dev_task` -> create tasks for the implementation workflow and mark them
  deferred to development
- `skip` -> log but do not block completion

Iteration rule:

- perform up to three repair rounds
- after each round, rerun verification on affected areas plus light regression
- if still below threshold after the final round, report the remaining known
  issues explicitly

## Phase 5: Final summary

At the end of a demo-forge run, Codex should summarize:

- selected mode
- completed and skipped phases
- runtime capability gaps
- final verification status
- the location of the key artifacts

## Clean and status behavior

- `clean` should be treated as a destructive workflow and only executed when
  the user clearly asked for cleanup
- `status` should be read-only and summarize artifact presence, readiness, and
  the most recent verification outcome

## Safety rules

- Do not invent application credentials.
- Do not claim media upload succeeded when URLs still point externally.
- Do not claim demo quality is ready if verification was skipped or unavailable.
