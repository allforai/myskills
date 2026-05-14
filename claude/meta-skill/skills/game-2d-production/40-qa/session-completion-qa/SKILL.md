---
name: game-2d-session-completion-qa
description: Validate that a 2D game session can launch, enter gameplay, complete, retry or continue, and exit without manual intervention.
---

# Session Completion QA

## Input Contract

Read session-flow contract, playable slice manifest, runtime profile, save state
contract when present, and UI screen map.

## Output Contract

Write `.allforai/game-2d/qa/session-completion-qa-report.json` with route
trace, screenshots, assertions, performance notes, blockers, and repair routing.

## Invocation Contract

Run against the target runtime. If the runtime cannot be launched or automated,
return a blocking status.

```json
{
  "skill": "game-2d-production/40-qa/session-completion-qa",
  "mode": "runtime_qa",
  "input_paths": [
    ".allforai/game-2d/spec/session-flow-contract.json",
    ".allforai/game-2d/assembly/playable-slice-manifest.json"
  ],
  "output_root": ".allforai/game-2d/qa"
}
```

## Automatic Validation

Automate launch, menu/start, gameplay entry, one completion outcome, retry or
continue, and exit/pause recovery. Capture runtime screenshots at each state.

## Completion Conditions

Complete when a full session path runs unattended and produces evidence.
