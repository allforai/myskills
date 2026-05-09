# Text Consistency QA Skill

> Internal sub-skill for game-narrative pipelines. Status: bundled, inactive, not wired.

## Overview

Validates narrative, dialogue, quest, tutorial, UI, and reward text for tone,
terminology, variable safety, length, continuity, and localization readiness.

## Input Contract

Required: text manifest or specs. Optional: narrative tone, UI layout, dialogue
manifest, quest text spec.

## Output Contract

Writes `.allforai/game-design/narrative/text-consistency-qa-report.json`.

Issues must include `issue_id`, `text_id`, `source_path`, `severity`,
`root_cause`, `expected_rule`, `actual_text`, `repair_target`,
`consumer_refs`, and `blocks_runtime`.

Allowed root causes: `narrative_tone`, `dialogue_spec`,
`dialogue_generation`, `quest_text_spec`, `ui_constraints`,
`localization_constraints`, `runtime_import`, and `unknown`.

## Invocation Contract

```json
{"skill":"game-narrative/text-consistency-qa","mode":"validate","input_paths":{"narrative_tone":".allforai/game-design/narrative/narrative-tone-design.json","dialogue_manifest":".allforai/game-design/narrative/dialogue-generation-manifest.json","quest_text_spec":".allforai/game-design/narrative/quest-text-spec.json"},"output_root":".allforai/game-design/narrative"}
```

Supported modes: `validate`, `validate_specs_only`, `repair_targets`.

## Automatic Validation

Check tone drift, terminology drift, missing variables, unsafe placeholders,
length overflow, duplicate lines, branch continuity, and UI constraints.

Each blocker or major issue must name one upstream repair target. Route tone and
terminology failures to `narrative-tone-design`, branch or trigger failures to
`dialogue-spec`, generated line wording failures to `dialogue-generation`, quest
objective failures to `quest-text-spec`, and text fit failures to the owning
text spec before changing UI layout.

## Completion Conditions

Return `COMPLETED` when no blocker/major text issues remain. Return
`FAILED_VALIDATION` with repair targets for blockers.
