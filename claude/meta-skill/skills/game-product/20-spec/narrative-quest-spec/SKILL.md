# Narrative Quest Spec Skill

> Internal sub-skill for game-product pipelines. Status: bundled, inactive, not wired.

## Overview

Defines story, quest, objective, dialogue, trigger, reward, and branch contracts
for games that include narrative, missions, tutorials, or task chains.

## Input Contract

Required: player experience contract, core loop spec, and content taxonomy.

Optional: progression spec, level design spec, economy spec, character list,
dialogue tone, localization needs, and runtime quest system constraints.

## Output Contract

Writes:

- `.allforai/game-design/content/narrative-quest-spec.json`
- `.allforai/game-design/content/narrative-quest-report.json`

Quest entries must include `quest_id`, `quest_type`, `narrative_purpose`,
`start_trigger`, `objectives`, `success_conditions`, `failure_conditions`,
`reward_refs`, `level_refs`, `dialogue_requirements`, `character_refs`,
`branching_rules`, `ui_requirements`, `art_requirements`,
`localization_requirements`, `runtime_requirements`, `state`, and
`consumer_refs`.

Allowed states: `not_applicable`, `draft`, `validated`, `needs_revision`,
`blocked_by_missing_content`, `blocked_by_progression`.

## Invocation Contract

```json
{
  "skill": "game-product/narrative-quest-spec",
  "mode": "spec_validate",
  "input_paths": {
    "player_experience": ".allforai/game-design/product/player-experience-contract.json",
    "core_loop": ".allforai/game-design/product/core-game-loop-spec.json",
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json"
  },
  "output_root": ".allforai/game-design/content"
}
```

Supported modes: `spec_validate`, `not_applicable`, `validate_existing`,
`repair_existing`.

## Automatic Validation

Check that each quest has a trigger, objective, completion condition, reward,
UI affordance, and runtime owner. Narrative-only games must still define player
action and state progression.

Repair routing: missing content routes to `content-taxonomy-spec`; missing
rewards route to `economy-spec` or `progression-spec`; dialogue details route
to `game-narrative/dialogue-spec`.

## Completion Conditions

Return `COMPLETED` when quest/narrative structure is actionable or explicitly
not applicable. Return `FAILED_VALIDATION` when objectives, triggers, or rewards
cannot be resolved.
