---
name: game-2d-input-feedback-contract
description: Define 2D input actions and their immediate visual, audio, animation, and state feedback expectations.
---

# Input Feedback Contract

## Input Contract

Read interaction design, mechanics spec, UI contract, audio cues, VFX specs,
and runtime profile.

## Output Contract

Write `.allforai/game-2d/spec/input-feedback-contract.json` with:

- input actions by platform: pointer, touch, keyboard, controller, or hybrid
- targeting/selection rules and invalid action feedback
- expected feedback latency and visible response frames
- audio/VFX/animation cue ids
- screenshot checkpoints for normal, hover/pressed, selected, invalid, success, and failure states.

## Invocation Contract

Keep controls generic unless a project-local specialized skill defines
genre-specific gesture or targeting behavior.

```json
{
  "skill": "game-2d-production/20-spec/input-feedback-contract",
  "mode": "write_contract",
  "input_paths": [
    ".allforai/game-design/game-design-doc.json",
    ".allforai/game-2d/spec/core-loop-playable-contract.json"
  ],
  "output_root": ".allforai/game-2d/spec"
}
```

## Automatic Validation

Every player action must have runtime input automation and visible or audible
feedback. Missing feedback is `failed_validation`.

## Completion Conditions

Complete when automated tests can prove that player inputs produce the expected
state and feedback.
