---
name: game-audio-00-env-audio-registry
description: Internal bundled meta-skill module for game-audio/00-env/audio-registry; use within generated bootstrap node-specs when this exact contract is selected.
---

# Audio Registry Skill

> Internal sub-skill for game-audio pipelines. Status: bundled, inactive, not wired.

## Overview

Defines canonical IDs, file prefixes, paths, lifecycle states, owners, and
consumers for SFX, music, ambience, UI sounds, and voice placeholders.

## Input Contract

Required: game event list or audio inventory. Optional: UI registry, VFX spec,
narrative tone, gameplay systems.

## Output Contract

Writes `.allforai/game-design/audio/audio-registry.json` and
`.allforai/game-design/audio/audio-registry-report.json`.

Registry entries must include `audio_id`, `file_prefix`, `kind`, `event_ref`,
`state`, `paths`, `consumers`, `variants`, and `validation`.

Allowed states: `planned`, `spec_ready`, `generated`, `approved`,
`needs_revision`, `automation_limited`.

## Invocation Contract

```json
{"skill":"game-audio/audio-registry","mode":"build_or_update","input_paths":{"game_design_doc":".allforai/game-design/game-design-doc.json","ui_registry":".allforai/game-design/ui/ui-registry.json","vfx_spec":".allforai/game-design/art/vfx/vfx-spec.json"},"output_root":".allforai/game-design/audio"}
```

Supported modes: `build_or_update`, `validate_existing`, `resolve_ids`.

## Automatic Validation

Check unique IDs, path roots, file prefixes, states, required event coverage,
and references from UI/VFX/gameplay events.

Downstream audio specs and runtime manifests must use `audio_id`, not display
names or raw filenames.

Repair routing: missing gameplay/UI/VFX event references return to the owning
event spec; duplicate IDs repair here; path or prefix collisions repair here;
missing final files route to `sfx-generation` or `music-prompt-generation` after
the registry ID remains stable.

## Completion Conditions

Return `COMPLETED` when registry and report validate. Return `UPSTREAM_DEFECT`
when no events or inventory can be resolved.
