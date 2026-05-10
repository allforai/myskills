# Quest Pattern Spec Skill

> Internal sub-skill for game-genre-common pipelines. Status: bundled, inactive, not wired.

## Overview

Defines reusable quest pattern grammar such as fetch, escort, defend, explore,
investigate, craft, social, faction, timed, branching, and repeatable quests.

## Input Contract

Required: content registry and narrative/quest context.

Optional: level design, activity design, faction system, relationship system,
economy, and UI requirements.

## Output Contract

Writes `.allforai/game-design/genre-common/quest-pattern-spec.json` and a
report. Patterns include `pattern_id`, `objective_template`, `required_roles`,
`failure_rule`, `reward_rule`, `variation_axes`, `anti_repetition_rules`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_content`.

## Invocation Contract

```json
{"skill":"game-genre-common/quest-pattern-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/genre-common"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check each pattern has objective, roles, reward, fail state, variation, and
anti-repetition rule. Reject patterns that cannot map to available content.

Repair routing: content gaps route to content registry; reward gaps to economy;
narrative gaps to narrative quest/story specs.

## Completion Conditions

Return `COMPLETED` when quest patterns are reusable and owned. Return
`FAILED_VALIDATION` when patterns are repetitive or unmappable.
