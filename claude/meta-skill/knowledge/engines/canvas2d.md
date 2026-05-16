# Canvas2D Runtime Specialization Knowledge

Use this knowledge when bootstrap detects a Canvas2D, Web Canvas, or WebView
Canvas game client, or when the selected runtime renders gameplay through
`HTMLCanvasElement.getContext("2d")`.

## Why Canvas2D Needs Specialization

Canvas2D is easy for an LLM to edit, but hard to validate from structure alone.
Most defects are integration and runtime-effect defects: modules exist but are
not wired, audio buffers are not loaded, VFX systems are dead code, DPR
coordinates render off-screen on mobile, and gameplay rules live as implicit
domain assumptions rather than explicit contracts.

Generate a project-local frontend runtime specialization:

```text
.allforai/bootstrap/specialized-skills/<specialization_id>-frontend-runtime/SKILL.md
```

## Required Canvas2D Runtime Contracts

The specialized skill must define these project-specific contracts:

- production entrypoint and boot sequence;
- module interface cards for every public runtime module;
- module consumer wiring proofs for new modules;
- rewrite compatibility checks for existing module exports;
- Canvas coordinate system, CSS size, backing-store size, DPR policy, and safe
  resize path;
- runtime probe schema exposed to browser automation;
- gameplay rule constraints for the selected genre;
- screenshot tasks for DPR 1, DPR 2, and DPR 3 when mobile/WebView is a target;
- I/O effect probes for audio, network, storage, or file/resource loading.

## Canvas2D Game Client Capability Profile

This is the Canvas2D game-client profile used by bootstrap for mature
product-level node expansion.

Bootstrap must not treat a Canvas2D game as a generic web frontend. When the
project is a Canvas2D game client, especially a mobile/WebView target, generate
or require a game-client profile that expands beyond scaffold/build/smoke. The
profile should create project-specific node-specs for every selected item below
unless the product concept explicitly excludes it:

| Node family | Required when | Responsibility |
|---|---|---|
| `runtime-core` | always | boot sequence, renderer, scene manager, progress/save manager, shared input |
| `interface-cards` | always | canonical public module signatures and rewrite compatibility |
| `asset-bundle` | visual/audio assets exist or are generated | manifest, preload groups, decoded resource proof |
| `level-data` | level/progression game | level tables, solvability seeds, difficulty metadata |
| `scene-*` | each product scene/screen | intro/map/level-select/gameplay/dialog/shop/settings/etc. |
| `gameplay-system-*` | each core mechanic | matcher/BFS, combo, obstacle, special tiles, scoring, win/loss |
| `audio-system` | any BGM/SFX requirement | Web Audio preload, cue triggers, runtime effect probe |
| `vfx-system` | any VFX requirement | VFX module, production import/init, trigger coverage |
| `backend-client` | sync/IAP/cloud/profile exists | offline-first client, sync, receipt or entitlement boundaries |
| `platform-plugins` | mobile shell exists | Capacitor/Cordova/native bridge setup and plugin probes |
| `browser-qa` | runnable web target | Playwright gameplay smoke with screenshots and runtime probe |
| `visual-qa` | visible gameplay | multi-scene Codex visual review and repair routing |
| `gameplay-quality-qa` | playable mechanics | rule invariants, solvability, legal-action proof |
| `audio-qa` | audio-system selected | decoded buffers and production trigger proof |
| `performance-qa` | Canvas or mobile target | FPS/memory/render pressure and DPR screenshot QA |
| `art-quality-qa` | generated/imported art | target-size readability and runtime asset binding |
| `platform-build-*` | mobile target | iOS/Android build/simulator evidence, not only browser smoke |
| `qa-repair-loop` | two or more QA nodes | read all QA reports, repair, rerun affected evidence |
| `concept-acceptance` | production/launch/unattended | final weighted product acceptance against concept/art/runtime |

The generated nodes should use project-specific names, but the graph shape must
cover these families. If bootstrap cannot determine whether a family applies,
it should add a blocked planning item or a profile gap report instead of
silently omitting the family.

## Profile Dependency Rules

- Scene nodes depend on runtime-core, asset-bundle, interface-cards, and the
  relevant gameplay/UI/audio bindings.
- Gameplay scene depends on the concrete gameplay systems it calls.
- Browser/mobile QA depends on all scene/system nodes that are in the target
  slice.
- Platform build nodes depend on browser QA and runtime smoke unless the target
  runtime has no browser preview.
- `qa-repair-loop` depends on every QA node and must precede
  `concept-acceptance`.
- `concept-acceptance` depends on repair loop, platform builds, visual QA,
  audio QA, gameplay QA, and performance QA when those scopes exist.

## Interface Cards

Each public module/class used across nodes needs a canonical interface card
under `.allforai/game-frontend/interfaces/` or a project-local equivalent. The
card must include:

- module path and import specifier;
- exported names and default export status;
- constructor signature;
- key method signatures;
- required initialization order;
- side effects and owned resources;
- consumers that must import/call it;
- runtime probe fields proving it is active.

Subsequent node-specs must reference the interface card instead of restating the
signature manually. Rewriting an existing module must preserve all imported
exports unless every consumer is updated in the same node and the compile check
proves the migration.

## Module Wiring Gate

Creating a file is not completion. For every newly created runtime module, the
assembly or stitch node must prove:

- at least one production consumer imports it;
- the consumer calls its constructor or initialization/load function;
- the module is reachable from the production boot path;
- a runtime probe or test demonstrates the initialized instance is active;
- dead-code modules are reported as `code_gaps`, not accepted as warnings.

## I/O Runtime-Effect QA

For I/O features, mocks only prove structure. Required effect evidence:

- audio: real audio files fetched/decoded, `AudioBuffer` or equivalent is not
  null, unlock/user-gesture policy is handled, `AudioContext.state` is valid for
  the test, and the cue can be triggered from production scene code;
- network: real request path or local test server response is observed;
- storage: write/read round trip against the actual runtime storage API;
- resource loading: manifest key resolves to decoded runtime object, not only a
  path string.

## Canvas2D DPR QA

Canvas2D projects that target mobile or WebView must run screenshot QA with
`deviceScaleFactor` values that include `1` and the highest target mobile DPR
such as `3`. The test must verify:

- canvas CSS size and backing-store size are consistent with DPR policy;
- drawing coordinates are in logical pixels unless the renderer contract says
  otherwise;
- the central gameplay region is non-black/nonblank;
- primary board/HUD elements are visible within viewport bounds;
- before/after gameplay screenshots remain framed after resize/orientation.

If DPR screenshots cannot be captured, return a blocking state. Do not rely on
desktop DPR 1 screenshots for mobile Canvas2D acceptance.

## Gameplay Rule Constraints

Genre-specific rules must be written into the core-loop contract. For
path-connection matching / Onet / 连连看, include:

- board dimensions and shape mask;
- which cells are occupied, empty, null, blocked, or traversable;
- whether null/shape holes are traversable by pathfinding;
- outside-board path policy;
- max-turn rule and path visualization rule;
- initial board solvability and at least one known matchable pair;
- visible board boundary/frame requirements so players understand the play
  area.

Playability QA must prove at least one initially matchable pair exists and that
the pair actually connects through the runtime matcher.

## Repair Routing

| Finding | Repair target |
|---|---|
| module exists but no production import/call | playable-client assembly or stitch node |
| deleted export used by consumer | interface card plus module rewrite repair |
| audio function callable but silent | audio binding and I/O runtime-effect QA |
| VFX module dead code | animation/VFX binding and stitch node |
| DPR 3 black/offscreen screenshot | renderer coordinate/DPR contract |
| shape holes block legal Onet path | core-loop contract and runtime matcher |
| board boundary invisible | scene composition and HUD/UI binding |
