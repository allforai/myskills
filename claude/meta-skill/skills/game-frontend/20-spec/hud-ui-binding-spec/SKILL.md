---
name: game-frontend-20-spec-hud-ui-binding-spec
description: Internal bundled meta-skill module for game-frontend/20-spec/hud-ui-binding-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# HUD UI Binding Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Maps game UI/HUD design and art assets into frontend runtime screens, overlays,
safe areas, data bindings, interaction states, and validation probes.

## Input Contract

Required: frontend runtime profile, scene composition spec, game UI registry or
UI design contract, and asset import bindings.

Optional: game design doc, icon manifest, visual style tokens, localization
keys, accessibility constraints, and existing UI code.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/hud-ui-binding-spec.json`
- `.allforai/game-frontend/bindings/hud-ui-binding-report.json`

HUD bindings must include `screen_id`, `scene_refs`, `ui_elements`,
`data_sources`, `asset_refs`, `layout_zone`, `safe_area_rule`,
`interaction_states`, `visibility_rules`, `accessibility_rules`,
`validation_probe`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_ui_contract`, `blocked_by_asset_binding`,
`blocked_by_scene_composition`.

## Invocation Contract

```json
{
  "skill": "game-frontend/hud-ui-binding-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json",
    "asset_bindings": ".allforai/game-frontend/bindings/asset-import-binding-spec.json",
    "ui_registry": ".allforai/game-design/ui/ui-registry.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that required HUD/screens have data sources, layout zones, asset refs,
states, and screenshot probes. UI must not cover required gameplay visibility
unless the source UI contract explicitly says so.

Repair routing: missing UI definition routes to `game-ui`; missing icons route
to `game-art/icon-generation`; scene overlap routes to scene composition.

## Completion Conditions

Return `COMPLETED` when UI can be rendered and probed in the client. Return
`FAILED_VALIDATION` when required HUD/screen data, assets, or safe-area rules
are missing.
