---
name: game-frontend-20-spec-runtime-debug-bridge-contract
description: Internal bundled meta-skill module for game-frontend/20-spec/runtime-debug-bridge-contract; use when a game/app runtime needs a QA-only debug bridge or MCP-readable interface for scene trees, runtime-created objects, asset bindings, logs, screenshots, invariants, and safe diagnostic actions.
---

# Runtime Debug Bridge Contract Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive,
> not wired.

## Overview

Defines a QA-only runtime debug bridge that lets automation, Codex CLI, Claude
Code, or a future MCP server query the actual running game/app instead of
guessing from static source files. This is required when important visible
objects are created at runtime and static review cannot prove the real scene,
node/object tree, asset bindings, or state invariants.

The bridge is diagnostic. It must not become a hidden runtime editor that fixes
the game only in memory. Durable fixes must still land in source, scene,
prefab/resource files, data tables, or asset binding contracts.

## Input Contract

Required:

- frontend runtime profile and automation surface;
- scene flow, scene composition, asset import binding, gameplay-system binding,
  HUD/UI binding, and visual acceptance criteria;
- project-local frontend runtime specialization when engine/genre-specific
  behavior is involved.

Optional:

- engine-specific knowledge such as Cocos, Godot, Unity, Phaser, web canvas, or
  custom native runtime notes;
- existing Playwright/engine test commands;
- runtime logs and previous QA reports;
- release build/export profile.

## Output Contract

Writes:

```text
.allforai/game-frontend/bindings/runtime-debug-bridge-contract.json
.allforai/game-frontend/bindings/runtime-debug-bridge-contract.md
```

The JSON contract must include:

```json
{
  "schema_version": "1.0",
  "bridge_id": "glow-island-cocos-runtime-debug-bridge",
  "enabled_only_in": ["qa", "dev"],
  "access_paths": ["browser_window", "websocket", "local_http", "mcp_server", "engine_test_api"],
  "read_capabilities": [
    "get_scene_info",
    "get_scene_tree",
    "get_visible_objects",
    "get_asset_bindings",
    "get_game_state",
    "get_runtime_logs",
    "get_invariants",
    "capture_screenshot"
  ],
  "diagnostic_capabilities": [
    "highlight_object",
    "toggle_debug_overlay",
    "step_frame",
    "trigger_test_action",
    "reload_test_scene"
  ],
  "mutation_policy": {
    "runtime_mutation_default": "forbidden",
    "allowed_runtime_mutations": [],
    "durable_fix_required": true
  },
  "probe_schema_ref": ".allforai/game-frontend/bindings/runtime-debug-bridge-probe-schema.json",
  "release_gate": {
    "probe_unreachable_in_release": true,
    "qa_flags_disabled_in_release": true,
    "release_scan_terms": []
  },
  "failure_codes": [],
  "repair_routes": []
}
```

## Invocation Contract

```json
{
  "skill": "game-frontend/runtime-debug-bridge-contract",
  "mode": "write_contract",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json",
    "asset_bindings": ".allforai/game-frontend/bindings/asset-import-binding-spec.json",
    "visual_criteria": ".allforai/visual-qa/visual-acceptance-criteria.json",
    "specialized_runtime": ".allforai/bootstrap/specialized-skills/<specialization_id>-frontend-runtime/SKILL.md"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `write_contract`, `validate_existing`, `repair_existing`.

## Capability Policy

Default allowed capabilities:

- read scene/screen/route and active runtime profile;
- read runtime-created object/entity/node tree;
- read visible objects with screen bounds, layer/z-order, ids, and asset refs;
- read asset loader/binding status;
- read game state and gameplay invariants;
- read runtime logs and errors;
- capture screenshots or screenshot task metadata;
- highlight an object or toggle a QA overlay for diagnosis;
- trigger declared test actions and reload declared test scenes.

Default forbidden capabilities:

- changing production scene graph permanently from the bridge;
- replacing Sprite/Texture/Material/Prefab/TileSet only in memory as a "fix";
- modifying game state to bypass broken logic outside declared test actions;
- accepting a runtime mutation as closure evidence;
- enabling bridge access in release/production builds.

If a project needs mutation for diagnosis, the specialized runtime skill must
declare the exact operation, safety limit, reset behavior, and proof that the
durable fix is later applied to source/assets. Otherwise return
`blocked_by_unsafe_runtime_mutation`.

## MCP Bridge Shape

If an MCP server is used, it should wrap the same QA bridge contract rather than
invent engine-specific semantics. Recommended read-only tools:

- `get_scene_info`
- `get_scene_tree`
- `get_visible_objects`
- `get_asset_bindings`
- `get_game_state`
- `get_runtime_logs`
- `get_invariants`
- `capture_screenshot`

Recommended diagnostic tools:

- `highlight_object`
- `toggle_debug_overlay`
- `trigger_test_action`
- `reload_test_scene`

MCP tools must return paths or compact JSON, not huge screenshots or logs in the
chat payload. Screenshots and large logs should be written to files and
referenced by path for Codex CLI batch review.

## Release Gate

The contract must define how release validation proves the bridge is disabled
or unreachable. Required checks:

- QA bridge flag does not enable in release;
- browser/window/local HTTP/WebSocket/MCP access is unavailable or inert in
  release;
- QA-only components/scripts/autoloads/MonoBehaviours are inactive or compiled
  out;
- production smoke screenshot passes visual acceptance without bridge support;
- release build/export scan records whether QA bridge activation strings remain
  and whether they are reachable.

If release gate cannot run when a release command exists, return
`blocked_by_unverified_release_bridge_gate`.

## Automatic Validation

Validate that:

1. the bridge has at least one executable access path in QA/dev;
2. read capabilities cover scene, visible objects, asset bindings, logs, and
   invariants needed by visual/runtime QA;
3. mutation policy forbids direct display-object fixes by default;
4. screenshot evidence remains mandatory and is not replaced by probe output;
5. release gate disables or blocks bridge access in production;
6. failure codes and repair routes are mapped to frontend, game-art,
   game-2d-production, or project-local implementation nodes.

## Completion Conditions

Return `COMPLETED` when the contract defines a safe QA bridge, evidence paths,
read/diagnostic capabilities, mutation limits, MCP shape when applicable, and
release gate.

Return `UPSTREAM_DEFECT` when runtime profile, scene/asset bindings, visual
criteria, or specialization are too incomplete to define the bridge.

Return `FAILED_VALIDATION` when the bridge cannot support required runtime QA,
allows unsafe mutation, or has no release-disable proof.
