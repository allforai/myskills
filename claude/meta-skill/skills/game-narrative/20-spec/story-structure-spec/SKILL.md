---
name: game-narrative-20-spec-story-structure-spec
description: Internal bundled meta-skill module for game-narrative/20-spec/story-structure-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Story Structure Spec Skill

> Internal sub-skill for game-narrative pipelines. Status: bundled, inactive, not wired.

## Overview

Defines acts, beats, branches, convergence, endings, emotional pacing, and
connections to quests, levels, and content packs.

## Input Contract

Required: world bible, character arcs, and narrative quest/context.

Optional: level design, content roadmap, dialogue spec, and player experience.

## Output Contract

Writes `.allforai/game-design/narrative/story-structure-spec.json` and a report.
Story beats include `beat_id`, `act`, `purpose`, `trigger`, `quest_refs`,
`character_refs`, `level_refs`, `branch_rules`, `convergence_rule`,
`emotion_target`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_world`.

## Invocation Contract

```json
{"skill":"game-narrative/story-structure-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/narrative"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check continuity, branch reachability, convergence, emotional pacing, and that
story beats map to playable or presentable game states.

Repair routing: missing characters route to character-arc-spec; missing quests
route to quest-chain-spec; missing triggers route to narrative-event-trigger-spec.

## Completion Conditions

Return `COMPLETED` when story structure is coherent and triggerable. Return
`FAILED_VALIDATION` when required beats are unreachable or contradictory.
