---
name: game-2d-production
description: Internal bundled meta-skill pack for assembling, validating, and closing a playable 2D game vertical slice from approved design, art, UI, audio, frontend, and runtime contracts.
---

# Game 2D Production

## Purpose

`game-2d-production` owns the final 2D game production closure layer. It takes
approved design, art, UI, audio, template, level, frontend, and runtime
contracts and proves that they form a playable vertical slice in the target 2D
runtime.

This pack consumes `game-art`, `game-ui`, `game-audio`, and `game-frontend`
outputs, then proves them in runtime. This pack is not genre-specific. It must not encode 连连看, match-3,
tower-defense, rhythm, card, roguelike, platformer, or any project-specific
state machine globally. If the core loop, difficulty proof, asset readability,
or input model is genre-tight, bootstrap must generate a project-local
specialized skill under `.allforai/bootstrap/specialized-skills/` and this pack
must consume that specialized contract.

## Current Children

| Child | Owns | Canonical path |
|---|---|---|
| `runtime-profile` | Detect 2D runtime commands, viewport, engine, platform, and automation surface. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/00-env/runtime-profile/SKILL.md` |
| `view-mode-runtime-contract` | Convert side/top/isometric/fixed-room/board/grid view needs into camera, coordinates, sorting, layer, and scale rules. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/20-spec/view-mode-runtime-contract/SKILL.md` |
| `core-loop-playable-contract` | Define the minimum playable input, rule, feedback, win/loss, progression, and save loop. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/20-spec/core-loop-playable-contract/SKILL.md` |
| `asset-runtime-binding-contract` | Bind engine-ready art, UI, animation, VFX, and audio manifests to runtime ids, anchors, pivots, atlases, and events. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/20-spec/asset-runtime-binding-contract/SKILL.md` |
| `input-feedback-contract` | Define input gestures/buttons/keyboard/touch plus immediate visual/audio feedback and readability timing. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/20-spec/input-feedback-contract/SKILL.md` |
| `session-flow-contract` | Define launch, menu, start, level, gameplay, pause, win, lose, retry, next, and completion flow. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/20-spec/session-flow-contract/SKILL.md` |
| `playable-slice-assembly` | Assemble a runnable 2D playable slice from approved contracts and game-frontend outputs. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/30-generate/playable-slice-assembly/SKILL.md` |
| `core-loop-playability-qa` | Validate input-to-state-to-feedback-to-outcome behavior with runtime evidence. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/40-qa/core-loop-playability-qa/SKILL.md` |
| `asset-binding-visual-qa` | Validate that generated/imported assets are actually bound, visible, readable, and not placeholders. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/40-qa/asset-binding-visual-qa/SKILL.md` |
| `session-completion-qa` | Validate a complete session path: start, play, finish, retry/continue, and exit. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/40-qa/session-completion-qa/SKILL.md` |
| `2d-production-closure-qa` | Final 2D closure gate across design, art, UI, audio, frontend, runtime, screenshots, build, and test evidence. | `${CLAUDE_PLUGIN_ROOT}/skills/game-2d-production/40-qa/2d-production-closure-qa/SKILL.md` |

## Input Contract

Required upstream artifacts:

- `.allforai/game-design/game-design-doc.json`
- `.allforai/game-design/design/program-development-node-handoff.json`
- `.allforai/game-runtime/art/engine-ready-art-manifest.json`
- `.allforai/game-design/art/export/engine-ready-art-output-contract.json`
- `.allforai/game-frontend/assembly/playable-client-assembly-report.json`
- `.allforai/game-frontend/qa/runtime-gameplay-visual-acceptance-report.json`
- Runtime command and screenshot capability from the project bootstrap profile.

Optional upstream artifacts include approved UI, audio, template, level,
balance, content, and project-local specialized-skill outputs.

## Output Contract

The pack exits through:

```text
.allforai/game-2d/env/2d-runtime-profile.json
.allforai/game-2d/spec/view-mode-runtime-contract.json
.allforai/game-2d/spec/core-loop-playable-contract.json
.allforai/game-2d/spec/asset-runtime-binding-contract.json
.allforai/game-2d/spec/input-feedback-contract.json
.allforai/game-2d/spec/session-flow-contract.json
.allforai/game-2d/assembly/playable-slice-manifest.json
.allforai/game-2d/assembly/playable-slice-assembly-report.json
.allforai/game-2d/qa/core-loop-playability-qa-report.json
.allforai/game-2d/qa/asset-binding-visual-qa-report.json
.allforai/game-2d/qa/session-completion-qa-report.json
.allforai/game-2d/qa/2d-production-closure-report.json
.allforai/game-2d/qa/2d-production-closure.html
```

## Invocation Contract

Invoke this pack only after game-design handoff requires `game_2d_production`
or the project is known to run as a 2D client. Run children in table order.
Downstream implementation nodes may split the children into separate tasks, but
must preserve their output paths and blocking statuses.

```json
{
  "skill": "game-2d-production",
  "mode": "2d_production_closure",
  "input_paths": [
    ".allforai/game-design/game-design-doc.json",
    ".allforai/game-design/design/program-development-node-handoff.json",
    ".allforai/game-frontend/assembly/playable-client-assembly-report.json"
  ],
  "output_root": ".allforai/game-2d"
}
```

## Automatic Validation

Validation must include runtime screenshot evidence, functional assertions, and
Codex CLI screenshot review where visible gameplay is involved; do not accept
static review, logs, source inspection, DOM state, canvas probes, or manifest
presence as a replacement for visible runtime evidence.

Blocking statuses:

- `blocked_by_unrunnable_client`
- `blocked_by_missing_runtime_command`
- `blocked_by_missing_screenshot`
- `blocked_by_missing_codex_cli`
- `blocked_by_missing_visual_model_capability`
- `blocked_by_missing_upstream_contract`
- `failed_validation`

## Completion Conditions

The 2D production slice is complete only when `2d-production-closure-qa`
reports no blocker or major findings, all required runtime screenshots exist,
the core loop is playable, assets are bound through `runtime_id` and `asset_id`,
and session flow can start, play, finish, retry or continue without manual
intervention.
