# Combat Spec Skill

> Internal sub-skill for game-systems pipelines. Status: bundled, inactive, not wired.

## Overview

Defines combat actors, stats, actions, damage/heal rules, cooldowns, status
effects, telegraphs, hit reactions, and VFX/audio/UI event hooks.

## Input Contract

Required: core loop and combat context. Optional: VFX spec, motion design,
audio registry, UI HUD information, progression spec.

## Output Contract

Writes `.allforai/game-design/systems/combat-spec.json` and
`.allforai/game-design/systems/combat-report.json`.

Combat schema:

```json
{
  "schema_version": "1.0",
  "actors": [],
  "actions": [
    {
      "action_id": "basic_attack",
      "actor_ref": "player",
      "startup_ms": 120,
      "active_ms": 80,
      "recovery_ms": 180,
      "damage": {"kind": "flat | scaling | percent", "value": 1},
      "cooldown_ms": 500,
      "event_refs": {
        "motion": null,
        "vfx": null,
        "sfx": null,
        "hud": null
      }
    }
  ],
  "status_effects": []
}
```

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_core_loop`.

Downstream consumers: `game-systems/balance-sanity-qa`,
`motion-design`, `skeletal-animation`, `sprite-vfx-generation`,
`particle-system`, `trail-generation`, `game-audio/sfx-spec`,
`game-ui/ui-mockup-generation`, `game-level/level-layout-spec`, and runtime
combat import.

## Invocation Contract

```json
{"skill":"game-systems/combat-spec","mode":"spec_validate","input_paths":{"core_loop":".allforai/game-design/systems/core-loop-design.json","motion_design":".allforai/game-design/systems/motion-design.json","hud_information":".allforai/game-design/ui/hud-information-design.json"},"output_root":".allforai/game-design/systems"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check actor stats, action timing, damage bounds, cooldowns, status durations,
telegraph before damage, HUD/VFX/audio event coverage, and placeholder values.

Every player-facing combat event must expose references for motion, VFX, SFX,
and HUD when those packs are active. Damage events must occur after readable
telegraph or startup timing.

Repair routing: invalid actor/action semantics repair here; missing loop
purpose repairs `core-loop-design`; missing readable action timing repairs
`motion-design`; missing VFX/audio/UI references route to their owning spec
skills after the combat event IDs are stable.

## Completion Conditions

Return `COMPLETED` when combat spec validates. Return `COMPLETED_WITH_WARNINGS`
when numeric tuning is approximate but structurally valid.
