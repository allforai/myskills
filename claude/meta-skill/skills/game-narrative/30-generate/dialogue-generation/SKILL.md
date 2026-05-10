# Dialogue Generation Skill

> Internal sub-skill for game-narrative pipelines. Status: bundled, inactive, not wired.

## Overview

Generates dialogue lines, barks, tutorial lines, and variants from
`dialogue-spec.json` and narrative tone.

## Input Contract

Required: dialogue spec and narrative tone. Optional: quest text spec,
portrait/expression manifests, localization constraints.

## Output Contract

Writes `.allforai/game-design/narrative/dialogue-generation-manifest.json` and
`.allforai/game-design/narrative/dialogue-generation-report.json`.

Manifest entries must include `dialogue_id`, `speaker_id`, `line_id`, `text`,
`variables`, `emotion`, `portrait_ref`, `audio_ref`, `ui_constraints`, `state`,
and `validation`.

Allowed states: `draft`, `validated`, `needs_revision`, `localization_ready`,
`blocked_by_missing_source`, `failed_validation`.

Downstream consumers: `game-narrative/text-consistency-qa`,
`game-audio/sfx-spec`, `game-ui/ui-mockup-generation`, runtime dialogue import,
localization import, and playtest QA.

## Invocation Contract

```json
{"skill":"game-narrative/dialogue-generation","mode":"generate_validate","input_paths":{"dialogue_spec":".allforai/game-design/narrative/dialogue-spec.json","narrative_tone":".allforai/game-design/narrative/narrative-tone-design.json"},"output_root":".allforai/game-design/narrative"}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check speaker voice, variables, branch coverage, line length, forbidden terms,
continuity, expression references, and localization readiness.

If text fails UI length constraints, repair the line text before changing layout
unless the layout spec is missing required text behavior.

Repair routing: root causes for failed outputs must be classified as `dialogue_generation`,
`dialogue_spec`, `narrative_tone`, `portrait_expression_art`,
`ui_constraints`, `localization_constraints`, or `runtime_import`. Generated
lines cannot become `localization_ready` until text consistency QA passes.

## Completion Conditions

Return `COMPLETED` when dialogue manifest/report validate. Return
`FAILED_VALIDATION` when required dialogue is missing, placeholder-only, fails
text consistency, or cannot be validated.
