# Cocos Creator Runtime Specialization Knowledge

Use this knowledge when bootstrap detects a Cocos Creator game client or when
the selected runtime is `cocos`.

## Why Cocos Needs Specialization

Cocos Creator projects depend on scene files, component bindings, `.meta`/UUID
references, resources folders, creator settings, and editor/runtime build
behavior. Generic browser-canvas checks are not enough. A Cocos project can
render a canvas while loading the wrong scene, a prototype component, a debug
renderer, or unbound placeholder sprites.

Generate a project-local frontend runtime specialization:

```text
.allforai/bootstrap/specialized-skills/<specialization_id>-frontend-runtime/SKILL.md
```

## Required Cocos Runtime QA Probe

The specialized skill should require a QA-only runtime probe when visual
closure depends on Cocos scene/node/resource binding. The probe must be enabled
only in QA/dev execution and must never be accepted as a replacement for real
screenshots.

Recommended probe responsibilities:

- current scene name and active scene asset;
- whether active scene/component names match prototype/debug/sample patterns;
- visible node tree summary with key node paths;
- HUD/background/board/tile container presence;
- tile count and visible tile node count;
- each visible tile/icon/character/background SpriteFrame status;
- SpriteFrame asset name, uuid/path when available, and mapped
  `asset_id`/`runtime_id` when the project provides binding metadata;
- placeholder/fallback renderer flags;
- runtime errors and missing resource loader keys;
- screenshot task ids that the probe corresponds to.

Expose the probe to Playwright or the browser runner through a stable object
such as:

```text
window.__ALLFORAI_VISUAL_PROBE__
```

The object should be read-only from tests and should not mutate gameplay state.

## QA Build Enablement

Enable the probe only in QA/dev contexts, for example through Cocos env flags
and a project-specific QA flag:

```text
DEBUG/DEV build + ?allforai_qa=1
```

or an equivalent project-local test flag. The exact code is project-specific
and belongs in the generated specialized skill, not in global bundled skills.

The visual QA runner must capture both:

- real browser/engine screenshot evidence;
- probe JSON evidence for diagnosis and binding traceability.

Screenshots are authoritative for visual judgment. Probe data is supporting
evidence for root cause and repair routing.

## Release Build Gate

Release/production builds must prove the QA probe and prototype/debug entry
points are disabled or unreachable.

Required release checks:

- without QA flag, `window.__ALLFORAI_VISUAL_PROBE__` is absent or inert;
- production smoke scene is not `Prototype`, sample, debug, or test scene;
- known prototype/debug components such as `PrototypeBoard`,
  `debugRenderer`, `placeholderRenderer`, or project equivalents are not active
  in production smoke flow;
- production bundle/source map scan does not expose QA probe activation strings
  in a reachable path, or the project explains why an inert string remains;
- release screenshot still passes visual acceptance criteria without probe.

If these checks cannot run, return a blocking state. Do not substitute static
source inspection for runtime release smoke validation when a release command is
available.

## Cocos Repair Routing

Common root causes and repair targets:

| Finding | Repair target |
|---|---|
| wrong startup scene or preview URL loads `Prototype` | scene-flow spec, creator build settings, playable-client assembly |
| scene contains only `Canvas + Camera` | scene composition spec and Cocos scene assembly |
| `PrototypeBoard` or color-block renderer active | frontend code assembly and production scene binding |
| generated art exists but tile sprites are color blocks | asset import binding, resource loader mapping, engine-ready art manifest |
| SpriteFrame exists but is not visible | node binding, layer/order, camera/framing, atlas/import metadata |
| HUD missing | HUD/UI binding and scene composition |
| QA probe present in release | release build/export QA and build defines |

## Specialized Skill Requirements

The generated Cocos frontend-runtime specialization must include:

- Cocos version and runnable command evidence;
- production scene ids/names and prohibited prototype/debug scene ids/names;
- resource/asset loading conventions;
- scene/node paths for board, HUD, background, UI overlays, and VFX layers;
- runtime visual probe schema and enablement flag;
- Playwright or engine automation steps to capture screenshot plus probe JSON;
- release build/probe-disabled checks;
- failure codes for wrong entrypoint, prototype component, missing SpriteFrame,
  missing HUD, missing asset loader mapping, black/debug background, and release
  probe leakage;
- repair routing to global `game-frontend`, `game-2d-production`,
  `game-art`, and project-local implementation nodes.
