# Economy Spec Skill

> Internal sub-skill for game-systems pipelines. Status: bundled, inactive, not wired.

## Overview

Defines resources, currencies, sinks, sources, prices, rewards, inventory
constraints, shop/crafting rules, and economy events.

## Input Contract

Required: core loop or economy context. Optional: progression spec, UI registry,
item art/icon manifests.

## Output Contract

Writes `.allforai/game-design/systems/economy-spec.json` and
`.allforai/game-design/systems/economy-report.json`.

Economy schema:

```json
{
  "schema_version": "1.0",
  "resources": [
    {
      "resource_id": "coins",
      "kind": "currency | consumable | material | energy | score",
      "sources": [],
      "sinks": [],
      "starting_amount": 0,
      "min": 0,
      "max": null,
      "ui_refs": [],
      "icon_refs": [],
      "events": []
    }
  ],
  "transactions": []
}
```

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_loop`.

Downstream consumers: `game-systems/balance-sanity-qa`,
`game-systems/progression-spec`, `game-ui/ui-mockup-generation`,
`game-narrative/quest-text-spec`, `icon-generation`, `item-art-generation`, and
runtime economy import.

## Invocation Contract

```json
{"skill":"game-systems/economy-spec","mode":"spec_validate","input_paths":{"core_loop":".allforai/game-design/systems/core-loop-design.json","game_design_doc":".allforai/game-design/game-design-doc.json"},"output_root":".allforai/game-design/systems"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check source/sink balance, negative-resource paths, price ranges, reward
coverage, UI/icon references, exploit risks, and placeholder values.

Every resource must map to at least one source or explicit external grant, one
display rule, and one failure behavior for insufficient funds when spendable.

Repair routing: missing source/sink semantics return to `core-loop-design`;
invalid prices or grants repair here; missing icon/item references route to
`icon-generation` or `item-art-generation`; text or UI failures route to
`quest-text-spec` or the owning UI spec.

## Completion Conditions

Return `COMPLETED` when economy spec validates. Return `FAILED_VALIDATION` when
source/sink rules, numeric tuning, display rules, or item/icon references are
missing or unverifiable.
