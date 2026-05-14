# Godot Runtime Specialization Knowledge

Use this knowledge when bootstrap detects a Godot game client or when the
selected runtime is `godot_2d`, `godot_3d`, or `godot`.

## Why Godot Needs Specialization

Godot projects are more text-readable than many engines, but runtime visual QA
still needs engine-aware evidence. A project can launch successfully while
loading a prototype scene, missing production textures, using placeholder
TileSets, or rendering the wrong CanvasLayer/HUD.

Generate a project-local frontend runtime specialization:

```text
.allforai/bootstrap/specialized-skills/<specialization_id>-frontend-runtime/SKILL.md
```

## Required Godot Runtime QA Probe

The specialized skill should require a QA-only probe when visual closure
depends on scene tree, resource, TileMap, Sprite, animation, or UI binding.
The probe must support diagnosis but must never replace real screenshots.

Recommended probe responsibilities:

- current scene path and scene name;
- whether the active scene path/name matches prototype/debug/test patterns;
- scene tree summary with important node paths and types;
- active `Camera2D`/`Camera3D` and viewport/canvas information;
- `CanvasLayer`, HUD, and primary `Control` node visibility;
- `TileMap`/`TileMapLayer` nodes, TileSet resource paths, used layer count, and
  visible tile cell count;
- `Sprite2D`, `AnimatedSprite2D`, `TextureRect`, `MeshInstance3D`, and
  `AnimationPlayer` resource binding status;
- missing/null textures, missing SpriteFrames, missing materials, and invalid
  animation clips;
- production asset path traceability to project binding metadata when present;
- placeholder/debug node flags;
- gameplay state and screenshot task id.

Expose probe evidence through a project-local JSON file, stdout marker, HTTP
debug endpoint, or browser bridge when the export target supports it. Prefer a
stable object/key only in QA builds, such as:

```text
ALLFORAI_VISUAL_PROBE
```

## QA Build Enablement

Enable the probe only in debug/QA execution:

```text
godot --path <project> -- --allforai-qa
```

or an equivalent project-local argument/environment flag. The exact GDScript,
autoload, or plugin code belongs in the generated specialized skill, not in
global bundled skills.

The visual QA runner must capture:

- real screenshot evidence from the Godot window/web export;
- probe JSON evidence for scene/resource binding diagnosis.

Screenshots are authoritative for visual judgment. Probe data only supports
root cause and repair routing.

## Release Export Gate

Release/export presets must prove QA probe behavior is absent or unreachable.

Required release checks:

- release starts from the production main scene, not a prototype/test scene;
- QA probe flag is ignored or unavailable in release;
- debug overlays, editor-only nodes, and test autoloads are disabled;
- exported project does not expose a reachable QA endpoint/object;
- release screenshot passes visual acceptance criteria without using probe;
- production assets are loaded from expected `res://` paths or export bundles.

If release validation cannot run when an export command exists, return a
blocking state instead of substituting static file inspection.

## Godot Repair Routing

| Finding | Repair target |
|---|---|
| wrong startup scene | project settings, scene-flow spec, playable-client assembly |
| prototype/test `.tscn` active | scene-flow and frontend code assembly |
| TileMap uses placeholder TileSet | asset import binding, TileSet resource mapping, engine-ready art manifest |
| Sprite/AnimatedSprite has null texture/frames | asset import binding and resource loader mapping |
| HUD missing or hidden | HUD/UI binding and scene composition |
| camera frames wrong area | scene composition or input-camera binding |
| probe reachable in release | release build/export QA and export preset configuration |

## Specialized Skill Requirements

The generated Godot frontend-runtime specialization must include:

- Godot version and runnable command evidence;
- main scene path and prohibited prototype/test scene patterns;
- expected scene tree paths for gameplay root, board/world, HUD, camera, VFX,
  and UI overlays;
- resource loading conventions for `res://` paths, TileSets, textures,
  SpriteFrames, animations, and export presets;
- runtime visual probe schema and QA enablement flag;
- screenshot plus probe capture commands;
- release export/probe-disabled checks;
- failure codes for wrong scene, prototype node, missing texture, missing
  TileSet, missing HUD, camera framing error, and release probe leakage;
- repair routing to global `game-frontend`, `game-2d-production`, `game-art`,
  and project-local implementation nodes.
