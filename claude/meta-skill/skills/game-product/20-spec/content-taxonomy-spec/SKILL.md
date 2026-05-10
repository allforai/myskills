# Content Taxonomy Spec Skill

> Internal sub-skill for game-product pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the product taxonomy for content: characters, enemies, items, skills,
levels, quests, events, UI surfaces, art, audio, and runtime requirements.

## Input Contract

Required: registry, core loop, and at least one of mechanics/progression/level
design/combat/economy specs.

Optional: narrative quest spec, player experience contract, art direction,
engine export constraints, and existing asset registry.

## Output Contract

Writes:

- `.allforai/game-design/content/content-taxonomy-spec.json`
- `.allforai/game-design/content/content-taxonomy-report.json`

Entries must include `content_id`, `content_kind`, `source_system_refs`,
`gameplay_role`, `required_fields`, `data_table_requirements`,
`asset_requirements`, `ui_requirements`, `vfx_requirements`,
`animation_requirements`, `audio_requirements`, `level_requirements`,
`runtime_system_requirements`, `owner_skill_refs`, `state`, and
`consumer_refs`.

Allowed content kinds: `character`, `enemy`, `item`, `equipment`, `skill`,
`status`, `resource`, `level`, `quest`, `dialogue`, `event`, `building`,
`tile`, `prop`, `ui_surface`, `vfx`, `audio`, `runtime_system`, `other`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_system`, `blocked_by_orphan_content`.

## Invocation Contract

```json
{
  "skill": "game-product/content-taxonomy-spec",
  "mode": "spec_validate",
  "input_paths": {
    "registry": ".allforai/game-design/product/game-design-registry.json",
    "core_loop": ".allforai/game-design/product/core-game-loop-spec.json",
    "mechanics": ".allforai/game-design/systems/mechanics-spec.json"
  },
  "output_root": ".allforai/game-design/content"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every content entry traces to a system or loop, every art/UI/audio
requirement has an owner, and no gameplay system references missing content.
Reject orphan content unless explicitly marked optional flavor.

Repair routing: missing system refs route to the owning spec; art requirements
route to `game-art/asset-registry`; UI requirements route to `game-ui/ui-registry`;
audio requirements route to `game-audio/audio-registry`.

## Completion Conditions

Return `COMPLETED` when content coverage is traceable and downstream-owned.
Return `FAILED_VALIDATION` when required content is orphaned or missing owners.
