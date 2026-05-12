---
name: game-systems-40-qa-balance-sanity-qa
description: Internal bundled meta-skill module for game-systems/40-qa/balance-sanity-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Balance Sanity QA Skill

> Internal sub-skill for game-systems pipelines. Status: bundled, inactive, not wired.

## Overview

Runs first-pass sanity checks over economy, progression, combat, level flow, and
reward pacing to catch contradictions, exploits, and impossible states.

## Input Contract

Required: at least one systems spec. Optional: economy, progression, combat,
level flow, UI HUD, telemetry assumptions.

## Output Contract

Writes `.allforai/game-design/systems/balance-sanity-qa-report.json`.

Issue schema:

```json
{
  "issue_id": "balance_001",
  "severity": "blocker | major | minor | warning",
  "root_cause": "economy | progression | combat | level_flow | core_loop | unknown",
  "affected_specs": [],
  "evidence": [],
  "repair_target": "game-systems/economy-spec",
  "blocks_downstream": true
}
```

Downstream consumers: economy, progression, combat, level flow, quest text,
HUD/UI specs, runtime tuning import, and playtest QA.

## Invocation Contract

```json
{"skill":"game-systems/balance-sanity-qa","mode":"validate","input_paths":{"economy_spec":".allforai/game-design/systems/economy-spec.json","progression_spec":".allforai/game-design/systems/progression-spec.json","combat_spec":".allforai/game-design/systems/combat-spec.json","level_flow":".allforai/game-design/levels/level-flow-design.json"},"output_root":".allforai/game-design/systems"}
```

Supported modes: `validate`, `validate_specs_only`, `repair_targets`.

## Automatic Validation

Check impossible costs, runaway sources, dead progression, combat one-shots,
unreachable rewards, excessive grind, missing fail/retry, and cross-spec event
coverage.

Repair routing: every issue must name one repair target. Do not report broad
"balance feels wrong" findings without a spec path and failed invariant.

## Completion Conditions

Return `COMPLETED` when no blocker/major sanity issues remain. Return
`FAILED_VALIDATION` with repair targets for blockers.
