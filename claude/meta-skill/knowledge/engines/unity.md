# Unity Runtime Specialization Knowledge

Use this knowledge when bootstrap detects a Unity game client or when the
selected runtime is `unity_2d`, `unity_3d`, or `unity`.

## Why Unity Needs Specialization

Unity projects can run a valid build while loading the wrong Scene, a sample
Scene, placeholder Prefabs, missing Sprite references, missing Materials, or
QA-only MonoBehaviours. Generic browser/canvas checks do not expose enough
binding detail.

Generate a project-local frontend runtime specialization:

```text
.allforai/bootstrap/specialized-skills/<specialization_id>-frontend-runtime/SKILL.md
```

## Required Unity Runtime QA Probe

The specialized skill should require a QA-only runtime probe when visual
closure depends on Unity Scene, GameObject, Prefab, Sprite, Tilemap, Animator,
Addressables, or UI binding. The probe supports root-cause diagnosis and must
not replace real screenshot evidence.

Recommended probe responsibilities:

- active Scene name, path, and build index;
- whether the loaded Scene matches prototype/sample/debug/test patterns;
- loaded additive Scenes;
- Camera and Cinemachine active camera status when applicable;
- Canvas/HUD/UI root visibility and screen-space/camera-space mode;
- key GameObject paths, active state, layer, tag, and component summary;
- SpriteRenderer, UI Image, Tilemap, Animator, ParticleSystem, MeshRenderer, and
  Material binding status;
- Sprite/Texture/Material/Prefab names and asset keys when available;
- Addressables/Resources/AssetBundle key load status;
- missing script, missing reference, null sprite/texture/material, and pink
  shader/material diagnostics;
- visible production asset count and traceability to project binding metadata;
- gameplay state and screenshot task id.

Expose probe evidence through a QA-only HTTP/debug bridge, log JSON marker,
file output, or WebGL browser object when the target supports it.

## QA Build Enablement

Enable the probe only in QA/development builds:

```text
DEVELOPMENT_BUILD or UNITY_EDITOR + ALLFORAI_QA
```

or an equivalent project-local scripting define/build flag. The exact C# probe
code belongs in the generated specialized skill, not in global bundled skills.

The visual QA runner must capture:

- real screenshot evidence from the player, WebGL browser canvas, simulator, or
  editor play mode;
- probe JSON evidence for Scene/GameObject/resource binding diagnosis.

Screenshots are authoritative for visual judgment. Probe data is supporting
evidence for root cause and repair routing.

## Release Build Gate

Release builds must prove QA probe behavior is absent or unreachable.

Required release checks:

- release starts from the production Scene in build settings;
- sample/prototype/test Scenes are not reachable from release startup flow;
- QA-only MonoBehaviours or probe bridges are absent, inactive, or compiled out;
- `ALLFORAI_QA`, debug endpoints, and probe objects are unavailable in release;
- Addressables/Resources do not expose test-only visual assets in production
  paths unless explicitly allowed;
- release screenshot passes visual acceptance criteria without probe evidence.

If release validation cannot run when a build command exists, return a blocking
state instead of substituting static inspection.

## Unity Repair Routing

| Finding | Repair target |
|---|---|
| wrong Scene loaded | scene-flow spec, build settings, playable-client assembly |
| sample/prototype Scene active | scene-flow and frontend code assembly |
| SpriteRenderer/UI Image missing Sprite | asset import binding, Addressables/Resources mapping, engine-ready art manifest |
| Tilemap uses placeholder TileBase/Sprite | asset import binding and Tilemap resource mapping |
| Material/shader missing or pink | asset import binding, material generation/import, graphics settings |
| HUD/Canvas missing | HUD/UI binding and scene composition |
| camera frames wrong layer/area | scene composition or input-camera binding |
| QA probe reachable in release | release build/export QA and scripting define/build settings |

## Specialized Skill Requirements

The generated Unity frontend-runtime specialization must include:

- Unity version and runnable build/playmode command evidence;
- production Scene names/paths/build indices and prohibited sample/prototype
  Scene patterns;
- expected GameObject paths for gameplay root, board/world, HUD, cameras, VFX,
  and UI overlays;
- asset loading conventions for Addressables, Resources, AssetBundles,
  SpriteAtlas, Tilemap, Animator, and Prefabs;
- runtime visual probe schema and QA enablement flag;
- screenshot plus probe capture commands;
- release build/probe-disabled checks;
- failure codes for wrong Scene, prototype object, missing Sprite, missing
  Tilemap asset, missing HUD, missing Material, camera framing error, and
  release probe leakage;
- repair routing to global `game-frontend`, `game-2d-production`, `game-art`,
  and project-local implementation nodes.
