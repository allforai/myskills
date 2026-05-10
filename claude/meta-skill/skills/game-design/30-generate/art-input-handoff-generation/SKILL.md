# Production Handoff Generation Skill

> Internal sub-skill for game-design pipelines. Status: bundled, inactive, not wired.

## Overview

Aggregates game concept and game planning outputs into one validated upstream
input package for game art, game UI, animation, VFX, icon, tileset, audio, and
runtime/program development pipelines.

This skill does not design art, generate images, or implement code. It
serializes product and planning decisions, verifies traceability to their source
contracts, writes human-readable handoff documentation, and emits downstream
development node contracts so art and program implementation can consume stable
inputs without reading conversation state.

## Input Contract

Required: product/game concept, game-design registry, audience positioning,
genre hybridization when used, player experience contract, pillars, core loop,
mechanics, progression, economy, level, combat, content taxonomy, narrative
quest, and human visual preference notes.

Optional: game modes, objective system, difficulty experience, generated enemy
list, item/skill list, level plans, narrative world/character/story artifacts,
onboarding, liveops, genre-common contracts, target engine/runtime constraints,
platform constraints, accessibility constraints, reference images, negative
references, existing project art, implementation stack, target engine,
networking constraints, save/data constraints, build/test commands, and
production budget.

## Output Contract

Writes:

- `.allforai/game-design/design/art-input-handoff.json`
- `.allforai/game-design/design/art-input-handoff-report.json`
- `.allforai/game-design/design/game-planning-handoff.md`
- `.allforai/game-design/design/program-development-node-handoff.json`

`art-input-handoff.json` includes `handoff_id`, `source_refs`, `product_context`,
`audience_context`, `human_preferences`, `genre_and_view_implications`,
`gameplay_readability_requirements`, `world_and_tone_context`,
`character_requirements`, `environment_requirements`, `ui_requirements`,
`icon_item_requirements`, `animation_requirements`, `vfx_requirements`,
`audio_visual_sync_requirements`, `level_and_camera_requirements`,
`content_asset_requirements`, `runtime_constraints`,
`accessibility_constraints`, `asset_priority_hints`, `unknowns`,
`blocked_requirements`, `consumer_refs`, and `state`.

`game-planning-handoff.md` is a human-readable document for art, UI, audio, and
program teams. It includes a concise project summary, player experience,
gameplay pillars, mode/loop summary, content scope, art-impacting requirements,
runtime-impacting requirements, open risks, and links to source artifacts. It
must not introduce requirements that are absent from JSON source artifacts.

`program-development-node-handoff.json` includes `handoff_id`, `source_refs`,
`target_engine`, `runtime_assumptions`, `implementation_nodes`,
`data_contracts`, `asset_import_contracts`, `ui_runtime_contracts`,
`audio_runtime_contracts`, `test_nodes`, `blocked_nodes`, and `state`.

`asset_import_contracts` must reference the game-art exit artifacts that
program/runtime nodes consume:

- `.allforai/game-design/art/export/engine-ready-art-output-contract.json`
- `.allforai/game-runtime/art/engine-ready-art-manifest.json`
- `.allforai/game-design/art/qa/runtime-import-check-report.json`

Each asset import contract includes `contract_id`, `source_requirements`,
`required_art_manifest`, `runtime_manifest`, `runtime_import_report`,
`consumer_runtime_nodes`, `accepted_states`, `blocking_states`,
`validation_required`, and `repair_target`. Runtime implementation nodes must
use `runtime_id` and `asset_id` from the engine-ready manifest, not hardcoded
raw file paths.

Each `implementation_node` includes `node_id`, `node_type`, `owner_hint`,
`source_requirements`, `input_artifacts`, `output_artifacts`, `dependencies`,
`runtime_acceptance`, `test_command_or_validation_path`, `blocks`, and
`repair_target`.

Allowed `node_type` values: `runtime_architecture`, `core_loop_runtime`,
`input_controls`, `camera_runtime`, `combat_runtime`, `economy_runtime`,
`progression_runtime`, `objective_runtime`, `level_runtime`, `content_runtime`,
`inventory_runtime`, `crafting_runtime`, `building_runtime`, `social_runtime`,
`achievement_runtime`, `dialogue_runtime`, `ui_runtime`, `audio_runtime`,
`asset_import_runtime`, `save_load_runtime`, `telemetry_runtime`,
`network_runtime`, `qa_runtime`.

Every requirement entry in any handoff must include `requirement_id`, `source_skill`,
`source_artifact`, `source_ref`, `player_facing_purpose`, `art_impact`,
`program_impact`, `required_consumer`, `priority`, `acceptance_signal`, and
`repair_target`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_concept`, `blocked_by_missing_planning`,
`blocked_by_preference_gap`, `blocked_by_traceability_gap`,
`failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-design/art-input-handoff-generation",
  "mode": "generate_validate",
  "input_paths": {
    "product_concept": ".allforai/product-concept.json",
    "registry": ".allforai/game-design/design/game-design-registry.json",
    "audience_positioning": ".allforai/game-design/design/audience-positioning-spec.json",
    "player_experience": ".allforai/game-design/design/player-experience-contract.json",
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json",
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json",
    "human_preferences": ".allforai/game-design/art/human-preferences.json",
    "target_runtime": ".allforai/runtime/target-runtime.json"
  },
  "output_root": ".allforai/game-design/design"
}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`,
`repair_targets`.

## Automatic Validation

Check that all art-affecting and program-affecting decisions from concept and
planning are present, source-traceable, and actionable:

- audience and platform imply style complexity, readability, and UI density;
- genre hybridization implies view mode, camera, visual vocabulary, and asset
  categories;
- core loop and mechanics imply player action readability, feedback channels,
  animation, VFX, and icon needs;
- combat implies telegraphs, hit reactions, status readability, enemy
  silhouettes, and VFX/audio sync;
- level and camera constraints imply tiles, props, backgrounds, parallax,
  environment readability, and collision-significant visuals;
- content taxonomy implies concrete characters, enemies, items, skills, UI
  screens, icons, VFX, audio hooks, and asset IDs;
- narrative/world context implies palette, material, costume, location,
  portrait, dialogue, and tone constraints;
- human visual preferences are explicit enough for downstream style tokens and
  image-generation prompts;
- systems, modes, objectives, economy, progression, content, and levels imply
  concrete implementation nodes with inputs, outputs, dependencies, runtime
  acceptance, and executable validation paths;
- every program development node maps back to source planning requirements
  rather than being invented as generic engineering work;
- every asset import runtime node references the engine-ready art manifest and
  runtime import report when art is required by the game;
- every art/audio/UI/runtime consumer can identify which handoff entries it
  owns and what evidence will close the work.

Reject handoffs that only summarize the game at a high level. The output must
contain asset-affecting and program-affecting requirements with `source_ref`
and `repair_target`.

If a required design artifact is missing, return
`blocked_by_missing_planning` or `FAILED_VALIDATION`; do not infer missing game
planning from genre convention. If human visual preferences are missing or
contradictory, return `blocked_by_preference_gap`; do not invent preferences.
If a program development node lacks source requirements, output artifacts, or
validation path, mark it blocked; do not create a generic implementation node
that hides the missing planning contract.
If a program node consumes art but no engine-ready art manifest or runtime
import report is declared, mark `asset_import_runtime` blocked instead of
letting program development hardcode asset paths.

Repair routing: missing product concept routes to `product-concept`; missing
IDs route to `game-design-registry`; missing audience/style constraints route
to `audience-positioning-spec`; missing hybrid/view implications route to
`genre-hybridization-spec`; missing readability routes to
`player-experience-contract` or `core-game-loop-spec`; missing content assets
route to `content-taxonomy-spec`; missing combat visuals route to `combat-spec`;
missing level/camera visuals route to `level-design-spec`; missing narrative
tone routes to `narrative-quest-spec` or `game-narrative`; missing UI
requirements route to `game-ui`; preference gaps route to human preference
collection before `game-art`; missing runtime implementation contracts route to
the owning game-design/system/content/level/narrative skill before program
development.

## Completion Conditions

Return `COMPLETED` when the handoff gives downstream art skills enough
traceable product, gameplay, content, preference, runtime, implementation-node,
and acceptance context to proceed. Return `FAILED_VALIDATION` when required
concept/planning inputs are missing, when art or program requirements are not
source-traceable, when development nodes lack validation paths, or when human
preferences are absent or contradictory.
