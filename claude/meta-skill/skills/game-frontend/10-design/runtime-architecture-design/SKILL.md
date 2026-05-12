---
name: game-frontend-10-design-runtime-architecture-design
description: Internal bundled meta-skill module for game-frontend/10-design/runtime-architecture-design; use within generated bootstrap node-specs when a game client needs frontend runtime architecture, module boundaries, engine adapter strategy, and runnable validation gates before implementation.
---

# Runtime Architecture Design Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the client-side runtime architecture before code assembly: engine
surface, scene model, game loop ownership, module boundaries, data/resource
flow, validation surfaces, and repair routes. This is not game design and not
backend architecture; it is the frontend implementation contract that consumes
game design, art, UI, audio, level, and template outputs.

This global skill must stay generic. When architecture choices depend on a
specific genre, engine/framework, platform, or existing project runtime code,
generate or read a project-local specialized skill under
`.allforai/bootstrap/specialized-skills/<specialization_id>-frontend-runtime/SKILL.md`
and let that file define the concrete scene flow, state machine, input model,
asset loading groups, runtime probes, and engine commands.

## Input Contract

Required: frontend runtime profile or project files, game design doc, program
development handoff when present, and selected target engine/runtime.

Optional: engine-ready art manifest, audio registry, level specs, puzzle/combat
mechanics specs, economy/progression specs, UI registry, backend schema,
existing client code, architecture concept validation output, and
`.allforai/bootstrap/specialized-skills/*-frontend-runtime/SKILL.md`.

## Output Contract

Writes:

- `.allforai/game-frontend/design/runtime-architecture-design.json`
- `.allforai/game-frontend/design/runtime-architecture-design-report.json`

The architecture must include `runtime_id`, `engine_family`,
`project_shape`, `module_boundaries`, `scene_ownership`, `game_loop_owner`,
`data_flow`, `asset_flow`, `event_bus_policy`, `state_ownership`,
`adapter_strategy`, `validation_surfaces`, `blocked_assumptions`,
`downstream_specs`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_runtime_profile`, `blocked_by_missing_handoff`,
`blocked_by_unrunnable_client`.

## Invocation Contract

```json
{
  "skill": "game-frontend/runtime-architecture-design",
  "mode": "design_validate",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "program_handoff": ".allforai/game-design/design/program-development-node-handoff.json",
    "architecture_gate": ".allforai/architecture/architecture-concept-validation.json"
  },
  "output_root": ".allforai/game-frontend/design"
}
```

Supported modes: `design_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that each declared module has one owner, inputs, outputs, validation
surface, and downstream consumer. Reject architectures that mix design
decisions into frontend ownership or rely on hidden globals without a state
model. The selected engine/runtime must have a runnable command or an explicit
blocked state from frontend-runtime-detection.

Specialization gate: if the game genre, engine/framework, input model, or
runtime code requires concrete rules that are not reusable across games, require
a project-local `*-frontend-runtime` specialized skill and reference it from the
architecture output. Do not encode Cocos/Phaser/Unity/Godot or genre-specific
state machines directly into this global skill.

Required module boundaries:

- boot/bootstrap
- asset loading
- scene flow
- game state
- gameplay systems
- UI/HUD
- animation/VFX
- audio
- save/settings
- diagnostics/test probes

Repair routing: missing runtime profile routes to `frontend-runtime-detection`;
missing game/product contracts route to game design finalization; missing art or
audio contracts route to their engine-ready manifests; unrunnable client routes
to runtime setup, not static review.

## Completion Conditions

Return `COMPLETED` when the frontend architecture has explicit module
boundaries and runnable validation gates. Return `FAILED_VALIDATION` when the
client architecture cannot be traced to approved contracts or cannot name a
validation surface.
