---
name: game-narrative-20-spec-dialogue-spec
description: Internal bundled meta-skill module for game-narrative/20-spec/dialogue-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Dialogue Spec Skill

> Internal sub-skill for game-narrative pipelines. Status: bundled, inactive, not wired.

## Overview

Defines dialogue nodes, speakers, triggers, variables, branches, emotion states,
and UI constraints before dialogue generation.

## Input Contract

Required: narrative tone and speaker/context list. Optional: quest specs,
portrait/expression manifests, level flow.

## Output Contract

Writes `.allforai/game-design/narrative/dialogue-spec.json` and
`.allforai/game-design/narrative/dialogue-spec-report.json`.

Dialogue nodes must include `dialogue_id`, `speaker_id`, `trigger_ref`,
`node_type`, `emotion`, `line_goal`, `branch_refs`, `variable_refs`,
`portrait_refs`, `audio_refs`, `ui_constraints`, `consumer_refs`, and
`state`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_tone`, `blocked_by_speaker_context`, `blocked_by_ui`.

Downstream consumers: `game-narrative/dialogue-generation`,
`game-narrative/text-consistency-qa`, `game-audio/sfx-spec`,
`game-audio/music-cue-spec`, `game-ui/ui-mockup-generation`, and runtime
dialogue import.

## Invocation Contract

```json
{"skill":"game-narrative/dialogue-spec","mode":"spec_validate","input_paths":{"narrative_tone":".allforai/game-design/narrative/narrative-tone-design.json","game_design_doc":".allforai/game-design/game-design-doc.json"},"output_root":".allforai/game-design/narrative"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check speaker IDs, trigger validity, branch targets, variable placeholders,
length limits, expression references, and tone coverage.

Repair routing: missing speaker, relationship, or voice data returns to
`narrative-tone-design`; invalid branch topology returns to this skill; missing
portrait or expression references route to `portrait-generation` or
`expression-set-generation`; UI overflow routes to this skill first unless the
UI layout omits required dialogue behavior.

## Completion Conditions

Return `COMPLETED` when dialogue spec validates. Return `FAILED_VALIDATION`
for missing speakers, invalid branches, missing context, or unverifiable UI
constraints.
