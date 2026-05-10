# AI Faction Runtime Spec Skill

> Internal sub-skill for game-runtime pipelines. Status: bundled, inactive, not wired.

## Overview

Defines runtime implementation for faction AI: state model, behavior tree or
utility model, perception, resource simulation, decision cadence, difficulty
scaling, readable debug state, and automated scenario tests.

## Input Contract

Required: player experience contract, core loop, content taxonomy or faction
brief, difficulty spec, and runtime constraints.

Optional: economy spec, level/world map spec, combat spec, procedural generator
spec, narrative quest spec, and telemetry requirements.

## Output Contract

Writes:

- `.allforai/game-runtime/simulation/ai-faction-runtime-spec.json`
- `.allforai/game-runtime/simulation/ai-faction-runtime-report.json`

Faction runtime specs must include `faction_id`, `state_model`,
`decision_model`, `perception_inputs`, `resource_inputs`, `action_outputs`,
`decision_cadence`, `difficulty_scaling`, `readability_debug_state`,
`performance_budget`, `scenario_tests`, `test_command_or_validation_path`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_faction_design`, `blocked_by_runtime_scope`,
`blocked_by_validation_unavailable`.

## Invocation Contract

```json
{
  "skill": "game-runtime/ai-faction-runtime-spec",
  "mode": "spec_validate",
  "input_paths": {
    "content_taxonomy": ".allforai/game-design/content/content-taxonomy-spec.json",
    "difficulty": ".allforai/game-design/systems/difficulty-experience-spec.json",
    "core_loop": ".allforai/game-design/design/core-game-loop-spec.json"
  },
  "output_root": ".allforai/game-runtime/simulation"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that AI behavior has bounded simulation cost, readable debug output,
scenario tests, and player-facing fairness. If the model cannot be run in a
test scenario, return a blocking validation status.

Repair routing: missing faction fantasy routes to narrative/worldbuilding;
missing behavior constraints route to game design; runtime overload routes to
implementation feasibility QA.

## Completion Conditions

Return `COMPLETED` when faction AI can be implemented and scenario-tested.
Return `FAILED_VALIDATION` when behavior is unbounded, opaque, or untestable.
