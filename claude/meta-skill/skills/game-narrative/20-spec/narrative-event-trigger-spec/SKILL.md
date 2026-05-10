# Narrative Event Trigger Spec Skill

> Internal sub-skill for game-narrative pipelines. Status: bundled, inactive, not wired.

## Overview

Defines narrative triggers, conditions, flags, variables, rewards, UI cues, and
runtime handoff for story and quest events.

## Input Contract

Required: story structure or quest chain spec.

Optional: dialogue spec, level plan, progression spec, runtime event system, and
localization constraints.

## Output Contract

Writes `.allforai/game-design/narrative/narrative-event-trigger-spec.json` and
a report. Triggers include `trigger_id`, `event_ref`, `condition`, `flag_reads`,
`flag_writes`, `cooldown`, `failure_behavior`, `ui_requirements`,
`runtime_requirements`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_story`.

## Invocation Contract

```json
{"skill":"game-narrative/narrative-event-trigger-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/narrative"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check triggers are reachable, flags are typed, loops cannot fire infinitely, and
failure behavior is explicit.

Repair routing: unreachable beats route to story-structure-spec; missing
dialogue routes to dialogue-spec; runtime gaps route to implementation QA.

## Completion Conditions

Return `COMPLETED` when narrative events are triggerable and safe. Return
`FAILED_VALIDATION` when trigger conditions are impossible or unsafe.
