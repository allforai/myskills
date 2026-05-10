# Quest Text Spec Skill

> Internal sub-skill for game-narrative pipelines. Status: bundled, inactive, not wired.

## Overview

Defines quest, objective, tutorial, reward, error, and progression text
contracts with variables, states, and UI length limits.

## Input Contract

Required: gameplay objectives or progression context plus narrative tone.
Optional: level flow, economy/progression specs, UI layout constraints.

## Output Contract

Writes `.allforai/game-design/narrative/quest-text-spec.json` and
`.allforai/game-design/narrative/quest-text-report.json`.

Quest text entries must include `text_id`, `quest_or_objective_ref`, `kind`,
`game_state`, `tone_ref`, `variables`, `max_chars`, `ui_surface_ref`,
`reward_refs`, `progression_refs`, `localization_notes`, `consumer_refs`, and
`state`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_progression`, `blocked_by_level_flow`, `blocked_by_ui`.

Downstream consumers: `game-narrative/dialogue-generation`,
`game-narrative/text-consistency-qa`, `game-ui/ui-mockup-generation`,
`game-systems/progression-spec`, and runtime localization import.

## Invocation Contract

```json
{"skill":"game-narrative/quest-text-spec","mode":"spec_validate","input_paths":{"narrative_tone":".allforai/game-design/narrative/narrative-tone-design.json","level_flow":".allforai/game-design/levels/level-flow-design.json","ui_layout":".allforai/game-design/ui/screen-layout-spec.json"},"output_root":".allforai/game-design/narrative"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check objective coverage, variables, UI length limits, state variants, reward
copy, tutorial clarity, and terminology.

Repair routing: missing objective or reward context returns to
`progression-spec` or `economy-spec`; unclear objective copy returns here;
length overflow returns here before UI changes; missing UI surface rules return
to `game-ui/screen-layout-spec`; terminology drift returns to
`narrative-tone-design`.

## Completion Conditions

Return `COMPLETED` when quest text spec validates. Return `FAILED_VALIDATION`
when required quest, objective, tutorial, reward, or UI text is missing,
placeholder-only, or unverifiable.
