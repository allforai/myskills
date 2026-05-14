---
name: game-2d-view-mode-runtime-contract
description: Convert a 2D game's view mode into runtime camera, coordinate, sorting, scale, and layer requirements.
---

# View Mode Runtime Contract

## Input Contract

Read game concept/design docs, art direction, level contracts, UI contracts, and
runtime profile.

## Output Contract

Write `.allforai/game-2d/spec/view-mode-runtime-contract.json` with:

- `view_mode`: `side | top_down | isometric | fixed_room | board_grid | card_table | hybrid_2d`
- coordinate system, origin, tile/grid size when applicable
- camera behavior and safe area
- layer order and sorting rules for background, gameplay, actors, VFX, UI, overlays
- scale/readability rules for target viewports.

## Invocation Contract

Keep this generic. If the view mode requires genre-specific spatial rules,
reference the project-local specialized skill instead of embedding them here.

```json
{
  "skill": "game-2d-production/20-spec/view-mode-runtime-contract",
  "mode": "write_contract",
  "input_paths": [
    ".allforai/game-design/game-design-doc.json",
    ".allforai/game-2d/env/2d-runtime-profile.json"
  ],
  "output_root": ".allforai/game-2d/spec"
}
```

## Automatic Validation

Check that every visible runtime layer has owner, z-order, scale policy, and
screenshot acceptance criteria. Missing layer or scale policy is
`failed_validation`.

## Completion Conditions

Complete when frontend and art binding nodes can use the contract without
guessing camera, layer, or coordinate behavior.
