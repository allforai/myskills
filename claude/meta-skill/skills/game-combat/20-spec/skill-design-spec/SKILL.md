---
name: game-combat-20-spec-skill-design-spec
description: Internal bundled meta-skill module for game-combat/20-spec/skill-design-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Skill Design Spec Skill

> Internal sub-skill for game-combat pipelines. Status: bundled, inactive, not wired.

## Overview

Defines player skills and abilities: activation, targeting, cost, cooldown,
range, scaling, risk, reward, counterplay, feedback, and downstream assets.

## Input Contract

Required: combat spec or mechanics spec.

Optional: balance goals, damage formulas, progression spec, item/skill design
list, UI constraints, animation/VFX/audio requirements, and runtime input model.

## Output Contract

Writes `.allforai/game-design/combat/skill-design-spec.json` and a report.
Skills include `skill_id`, `role`, `activation_rule`, `targeting_rule`,
`cost_refs`, `cooldown`, `range`, `effect_rule`, `scaling_refs`, `counterplay`,
`readability_requirements`, `asset_requirements`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_combat`.

## Invocation Contract

```json
{"skill":"game-combat/skill-design-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/combat"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check each skill has purpose, activation, cost or limit, readable effect,
counterplay, and balance/data owner. Reject mechanically duplicate skills unless
they serve distinct build roles.

Repair routing: missing combat rules route to game-design/combat-spec; numeric
gaps route to game-balance; asset gaps route to game-art requirements.

## Completion Conditions

Return `COMPLETED` when skills are playable and readable. Return
`FAILED_VALIDATION` when required skills lack rules, limits, or counterplay.
