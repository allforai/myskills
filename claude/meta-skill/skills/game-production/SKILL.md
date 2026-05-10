# Game Production Skill Map

> Internal bundled routing map for game-related sub-skill packs.
> Status: bundled, inactive, not wired.

## Purpose

Game Production is the ownership map for all game-related sub-skills. Use it
when deciding where a new game sub-skill belongs or when checking whether a
node should call design, art, UI, audio, content, level, systems, balance,
combat, narrative, liveops, onboarding, genre-common, frontend, or runtime
skills.

This pack does not execute production work. It prevents category drift.

## Ownership Map

| Pack | Owns | Does not own |
|---|---|---|
| `game-design` | Product design contracts, player promise, core loop, modes, objectives, meta game, final cross-phase handoff. | Runtime architecture, concrete art generation, UI implementation, audio production. |
| `game-systems` | Gameplay system rules and product-facing system specs shared across genres. | Engine-specific implementation and backend services. |
| `game-level` | Level flow, layout, blockout, encounter placement, playability QA. | Tileset image production and runtime map importer code. |
| `game-content` | Content registry, taxonomy, content list generation, coverage QA. | Visual generation and code import. |
| `game-narrative` | Tone, quests, dialogue, story consistency, text generation. | Dialogue runtime implementation unless delegated by a program node. |
| `game-ui` | Game UI structure, screen layout, UI assets, UI consistency, UI import readiness. | General website/app UI outside game context. |
| `game-art` | Visual assets, style tokens, source strategy, image/animation/VFX production, atlas, import QA, engine-ready art manifest. | Gameplay implementation and runtime systems. |
| `game-audio` | Music/SFX/voice style, cue specs, generated audio manifests, audio QA. | Audio engine integration code unless delegated by runtime. |
| `game-frontend` | Playable client assembly, asset/UI/animation/VFX bindings, scene composition, browser/engine smoke tests, visual runtime regression QA. | Product design, art generation, backend/security architecture. |
| `game-balance` | Numeric tuning, curves, simulations, balance QA. | Economy/product purpose and runtime code. |
| `game-combat` | Combat-specific rules, timing, hit readability, combat QA. | General system design and engine implementation. |
| `game-onboarding` | FTUE/tutorial product flow and onboarding QA. | Generic app onboarding. |
| `game-liveops` | Seasons, events, offers, retention calendars, liveops QA. | Backend service deployment. |
| `game-genre-common` | Reusable genre pattern contracts and genre-specific QA. | Project-specific final design ownership. |
| `game-runtime` | Program/runtime/server/simulation/security implementation contracts and executable validation paths. | Product intent, visual asset creation, and pure design methodology. |

## Boundary Rules

- Product/design skills define what the player should experience and what
  acceptance means.
- Art/UI/audio skills produce media assets plus manifests and import evidence.
- Frontend skills bind approved contracts into a runnable client and prove it
  with logs, screenshots, probes, and input smoke tests.
- Runtime skills define how approved product and asset contracts become
  executable systems.
- A downstream skill may consume an upstream contract, but must not rewrite the
  upstream owner’s decisions.
- If validation cannot run, return a blocking state. Do not substitute prose,
  static inspection, or generic fallback evidence.

## Cross-Phase Contracts

Game design exits through:

```text
.allforai/game-design/game-design-doc.json
.allforai/game-design/design/art-input-handoff.json
.allforai/game-design/design/program-development-node-handoff.json
```

Game art exits to program/runtime through:

```text
.allforai/game-design/art/export/engine-ready-art-output-contract.json
.allforai/game-runtime/art/engine-ready-art-manifest.json
.allforai/game-design/art/qa/runtime-import-check-report.json
```

Program development must consume art through `runtime_id`, `asset_id`, and
manifest references from the engine-ready art manifest. Hardcoded raw asset
paths are a contract violation.

Engine differences are handled by:

```text
game-art/20-spec/engine-export-profile
-> game-art/40-qa/runtime-import-check
-> game-art/40-qa/engine-ready-art-output-contract
-> game-frontend/20-spec/asset-import-binding-spec
```

Do not duplicate art skills per engine by default. Add an engine-specific
adapter only when the profile/manifest/adapter path cannot express or validate
the target import behavior.

Game frontend exits through:

```text
.allforai/game-frontend/assembly/playable-client-assembly-report.json
.allforai/game-frontend/qa/playable-smoke-test-report.json
.allforai/game-frontend/qa/playability-probe-report.json
.allforai/game-frontend/qa/visual-runtime-regression-report.json
.allforai/game-frontend/qa/frontend-performance-budget-report.json
.allforai/game-frontend/qa/frontend-build-export-report.json
```

Frontend completion requires a runnable client validation path. If the client
cannot run, frontend QA must block instead of accepting source inspection.
