---
name: game-design-20-spec-economy-spec
description: Internal bundled meta-skill module for game-design/20-spec/economy-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Economy Spec Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines game design-level economy: resources, sources, sinks, rewards, prices,
inventory constraints, exchange rules, exploit risks, and UI/art/data needs.

## Input Contract

Required: core game loop spec and progression spec or explicit economy brief.

Optional: player experience contract, mechanics spec, content taxonomy,
item/skill generation output, monetization constraints, and runtime data format.

## Output Contract

Writes:

- `.allforai/game-design/systems/product-economy-spec.json`
- `.allforai/game-design/systems/product-economy-report.json`

Resources must include `resource_id`, `kind`, `sources`, `sinks`,
`starting_amount`, `min`, `max`, `earn_rate`, `spend_rate`, `price_refs`,
`reward_refs`, `ui_refs`, `icon_requirements`, `exploit_risks`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_loop`, `blocked_by_progression`.

## Invocation Contract

```json
{
  "skill": "game-design/economy-spec",
  "mode": "spec_validate",
  "input_paths": {
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json",
    "progression": ".allforai/game-design/systems/progression-spec.json"
  },
  "output_root": ".allforai/game-design/systems"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that spendable resources have sources and sinks, reward rates support the
session model, costs are reachable, and exploit loops are identified. Unknown
numeric values must be marked `needs_tuning`, not silently accepted as final.

Repair routing: missing resource purpose routes to `core-game-loop-spec`;
unreachable costs route to `progression-spec`; icon/UI gaps route to
`content-taxonomy-spec`.

## Completion Conditions

Return `COMPLETED` when resource flow is closed. Return `FAILED_VALIDATION`
when any mandatory resource can deadlock or inflate without a declared cap.
