---
name: game-2d-core-loop-playable-contract
description: Define the minimum playable 2D core loop that runtime QA must prove with input, state, feedback, outcome, and progression evidence.
---

# Core Loop Playable Contract

## Input Contract

Read approved core loop, mechanics, level, balance, onboarding, and frontend
binding specs.

## Output Contract

Write `.allforai/game-2d/spec/core-loop-playable-contract.json` with:

- `loop_steps`: input, rule evaluation, state change, feedback, reward/failure
- minimum playable scenario and deterministic seed when applicable
- win, lose, retry, next, and progression conditions
- required telemetry/probe assertions
- gameplay invariants that must hold before and after core actions
- explicit game-rule constraints for pathfinding, collision, selection,
  boundary, and empty/null states when applicable
- screenshot checkpoints before and after meaningful player actions.

## Invocation Contract

Do not design new gameplay here. Convert approved design into executable proof
requirements.

```json
{
  "skill": "game-2d-production/20-spec/core-loop-playable-contract",
  "mode": "write_contract",
  "input_paths": [
    ".allforai/game-design/game-design-doc.json",
    ".allforai/game-2d/spec/view-mode-runtime-contract.json"
  ],
  "output_root": ".allforai/game-2d/spec"
}
```

## Automatic Validation

Reject contracts that only describe intent. Each loop step must map to at least
one runtime assertion and one visible screenshot checkpoint when the step is
visible to the player.

The contract must include `gameplay_invariants` for the target loop. Examples:
board/grid games must declare board dimensions, expected occupied/empty counts,
coordinate bounds, legal node/id naming, selection state, refill/drop
conservation, and disallowed values such as `undefined`, `NaN`, or
`[object Object]`/`[object Set]` in runtime ids. Action games must declare
player/enemy/resource/health/projectile invariants. UI-heavy games must declare
list/item count and selected item invariants.

For path-connection matching / Onet / 连连看 and similar board games, the
contract must include a `pathfinding_rules` or equivalent section covering:
which cells are occupied, empty, null, shape holes, blocked, or traversable;
whether null/shape-hole cells can be crossed; outside-board routing policy;
maximum turn count; known initially matchable pair; expected path visualization;
and visible board boundary/frame requirements. Missing these rules is
`FAILED_VALIDATION`, not an implementation detail to infer later.

If the approved design is genre-tight, the project-local specialized runtime
skill must define concrete invariant probes. A generic QA node must not invent
weak invariants after the fact.

## Completion Conditions

Complete when QA can run the loop without human guidance and determine pass,
fail, or blocked.
