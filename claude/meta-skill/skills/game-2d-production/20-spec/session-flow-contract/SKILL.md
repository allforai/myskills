---
name: game-2d-session-flow-contract
description: Define the full 2D session path from launch to gameplay completion, retry, continue, and exit.
---

# Session Flow Contract

## Input Contract

Read product flow, game modes, level spec, onboarding/FTUE, UI screen map, save
state contract, and runtime profile.

## Output Contract

Write `.allforai/game-2d/spec/session-flow-contract.json` with:

- launch, loading, menu, start, level/gameplay, pause, win, lose, retry, next, exit
- required screen ids and route/state ids
- blocking modal rules and recoverability
- save/resume requirement when applicable
- automated path and screenshot checkpoints.

## Invocation Contract

This contract is a runtime path spec, not a UI mockup document.

```json
{
  "skill": "game-2d-production/20-spec/session-flow-contract",
  "mode": "write_contract",
  "input_paths": [
    ".allforai/game-design/game-design-doc.json",
    ".allforai/game-frontend/bindings/scene-flow-spec.json"
  ],
  "output_root": ".allforai/game-2d/spec"
}
```

## Automatic Validation

Fail if there is no automated route from launch into gameplay and from gameplay
to at least one completion outcome.

## Completion Conditions

Complete when session QA can run without human navigation decisions.
