---
name: game-2d-playable-slice-assembly
description: Assemble the approved 2D contracts into a runnable playable vertical slice in the target client/runtime.
---

# Playable Slice Assembly

## Input Contract

Read all `.allforai/game-2d/spec/*.json` contracts, game-frontend assembly
reports, engine-ready art manifest, UI/audio manifests, runtime profile, and
project-local specialized skills when present.

## Output Contract

Write:

- `.allforai/game-2d/assembly/playable-slice-manifest.json`
- `.allforai/game-2d/assembly/playable-slice-assembly-report.json`

The manifest must list runtime entrypoint, scenes/screens, bound assets,
automation commands, screenshots to capture, and known blockers.

## Invocation Contract

Use the target project code and runtime. Do not accept a separate static demo
as proof unless the handoff explicitly defines that demo as the target runtime.

```json
{
  "skill": "game-2d-production/30-generate/playable-slice-assembly",
  "mode": "assemble_runtime_slice",
  "input_paths": [
    ".allforai/game-2d/spec/core-loop-playable-contract.json",
    ".allforai/game-2d/spec/asset-runtime-binding-contract.json",
    ".allforai/game-frontend/assembly/playable-client-assembly-report.json"
  ],
  "output_root": ".allforai/game-2d/assembly"
}
```

## Automatic Validation

Run build/start smoke commands from the runtime profile. If the project cannot
run, emit `blocked_by_unrunnable_client`. Missing runtime artifacts are
`failed_validation`.

## Completion Conditions

Complete when a runnable slice exists or a blocking report explains exactly
which upstream or runtime contract prevents assembly.
