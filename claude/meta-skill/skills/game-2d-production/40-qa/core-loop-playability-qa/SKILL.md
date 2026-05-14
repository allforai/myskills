---
name: game-2d-core-loop-playability-qa
description: Validate that the 2D playable slice responds to input, changes state, shows feedback, and reaches outcome conditions.
---

# Core Loop Playability QA

## Input Contract

Read core-loop playable contract, input-feedback contract, playable slice
manifest, runtime profile, and project-local specialized QA guidance.

## Output Contract

Write `.allforai/game-2d/qa/core-loop-playability-qa-report.json` with action
trace, assertions, screenshot manifest, pass/fail/blocker status, and repair
recommendations. Findings must be classified into `code_gaps`, `asset_gaps`,
`contract_gaps`, and `environment_blockers`.

## Invocation Contract

Use executable runtime automation. Do not accept design text or source
inspection as a substitute for gameplay evidence.

```json
{
  "skill": "game-2d-production/40-qa/core-loop-playability-qa",
  "mode": "runtime_qa",
  "input_paths": [
    ".allforai/game-2d/spec/core-loop-playable-contract.json",
    ".allforai/game-2d/assembly/playable-slice-manifest.json"
  ],
  "output_root": ".allforai/game-2d/qa"
}
```

## Automatic Validation

For every required loop step, run input automation, assert state changes, and
capture before/after runtime screenshots. Visible gameplay acceptance must use
functional assertions and Codex CLI screenshot review.

## Completion Conditions

Complete only when the core loop can be played from input to outcome, or when a
specific blocker is reported with a repair class. Implementation defects must be
listed in `code_gaps` so `game-2d-production/40-qa/code-repair-loop` can repair
and rerun affected QA. Do not hide code defects as generic blockers.
