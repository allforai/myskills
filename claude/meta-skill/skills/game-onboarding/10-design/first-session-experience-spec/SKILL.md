# First Session Experience Spec Skill

> Internal sub-skill for game-onboarding pipelines. Status: bundled, inactive, not wired.

## Overview

Defines the first-session experience: opening promise, first goal, emotional
arc, expected duration, success criteria, failure recovery, and handoff to the
main loop.

## Input Contract

Required: player experience contract and core game loop spec.

Optional: UI flow, mechanics spec, level design spec, narrative tone, platform
input model, and analytics goals.

## Output Contract

Writes `.allforai/game-design/onboarding/first-session-experience-spec.json`
and a report. Entries include `session_id`, `opening_promise`, `first_goal`,
`learning_objectives`, `emotion_beats`, `duration_budget`, `success_criteria`,
`failure_recovery`, `handoff_loop_ref`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_loop`.

## Invocation Contract

```json
{"skill":"game-onboarding/first-session-experience-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/onboarding"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that the first session teaches only required concepts, has one clear
first goal, avoids overload, and reaches the core loop. Missing evidence is a
blocker, not a reason to invent a proxy.

Repair routing: loop gaps route to core-loop spec; UI confusion routes to
game-ui flow/layout; teaching gaps route to tutorial-step-spec.

## Completion Conditions

Return `COMPLETED` when the first session is coherent and measurable. Return
`FAILED_VALIDATION` when the first session cannot reach a playable loop.
