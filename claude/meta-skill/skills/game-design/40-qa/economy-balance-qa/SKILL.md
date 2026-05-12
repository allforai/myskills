---
name: game-design-40-qa-economy-balance-qa
description: Internal bundled meta-skill module for game-design/40-qa/economy-balance-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Economy Balance QA Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Validates economy source/sink closure, affordability, inflation, exploit loops,
resource deadlocks, and monetization constraints.

## Input Contract

Required: economy spec and core game loop spec.

Optional: progression spec, item/skill set, data tables, monetization policy,
and target session/reward model.

## Output Contract

Writes `.allforai/game-design/systems/economy-balance-qa-report.json`.

Issues must include `issue_id`, `resource_id`, `severity`, `qa_axis`,
`expected`, `actual`, `root_cause`, `repair_target`, `blocks_runtime`, and
`consumer_refs`.

Allowed root causes: `missing_source`, `missing_sink`, `unreachable_cost`,
`inflation_risk`, `exploit_loop`, `resource_deadlock`, `monetization_conflict`,
`unknown`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_spec`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-design/economy-balance-qa",
  "mode": "validate",
  "input_paths": {
    "economy": ".allforai/game-design/systems/product-economy-spec.json",
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json"
  },
  "output_root": ".allforai/game-design/systems"
}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check every spendable resource has reachable sources and meaningful sinks.
Exploit suspicion must be reported with a repair target; do not accept
unbounded generation or impossible prices as final.

Repair routing: source/sink defects route to `economy-spec`; cost pacing
defects route to `progression-spec`; item price defects route to
`item-skill-design-generation`.

## Completion Conditions

Return `COMPLETED` when economy has no blocker flow issues. Return
`FAILED_VALIDATION` when resources can deadlock, inflate, or exploit.
