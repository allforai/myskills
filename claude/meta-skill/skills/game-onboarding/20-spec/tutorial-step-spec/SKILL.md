# Tutorial Step Spec Skill

> Internal sub-skill for game-onboarding pipelines. Status: bundled, inactive, not wired.

## Overview

Defines tutorial steps, triggers, prompts, player actions, validation, skip
rules, recovery, and UI/narrative requirements.

## Input Contract

Required: first-session experience spec and mechanics spec.

Optional: UI flow, level plan, narrative tone, localization constraints, and
analytics events.

## Output Contract

Writes `.allforai/game-design/onboarding/tutorial-step-spec.json` and a report.
Steps include `step_id`, `teaches_feature`, `trigger`, `prompt`, `required_action`,
`success_check`, `failure_hint`, `skip_rule`, `ui_requirements`,
`level_requirements`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_mechanics`.

## Invocation Contract

```json
{"skill":"game-onboarding/tutorial-step-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/onboarding"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every tutorial step maps to a real mechanic, has an observable
success condition, and does not depend on unexplained controls.

Repair routing: missing mechanics route to mechanics spec; unclear prompts route
to narrative/UI skills; impossible checks route to implementation feasibility.

## Completion Conditions

Return `COMPLETED` when tutorial steps are teachable and verifiable. Return
`FAILED_VALIDATION` when a required step cannot be completed or checked.
