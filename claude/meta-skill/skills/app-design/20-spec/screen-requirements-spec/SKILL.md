# Screen Requirements Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, inactive, not wired.

## Overview

Defines per-screen requirements: purpose, data, actions, UI states,
validation, accessibility, analytics, and downstream UI/code handoff needs.

## Input Contract

Required: information architecture spec, user flow spec, and feature priority
spec.

Optional: content model, data model, interaction pattern spec, design system,
brand constraints, and analytics plan.

## Output Contract

Writes `.allforai/app-design/spec/screen-requirements-spec.json`.

Screen requirements must include `screen_id`, `purpose`, `priority`,
`job_refs`, `flow_refs`, `data_refs`, `content_refs`, `primary_actions`,
`secondary_actions`, `states`, `validation_rules`, `empty_error_loading`,
`accessibility_requirements`, `analytics_events`, `handoff_refs`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_ia`,
`blocked_by_flow`.

## Invocation Contract

```json
{"skill":"app-design/screen-requirements-spec","mode":"spec_validate","input_paths":{"ia":".allforai/app-design/spec/information-architecture-spec.json","flows":".allforai/app-design/spec/user-flow-spec.json","priority":".allforai/app-design/spec/feature-priority-spec.json"},"output_root":".allforai/app-design/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every IA screen has requirements and every user-flow step references a
screen with defined actions, states, and feedback. Reject screens with no job,
data, or action purpose.

Repair routing: missing route ownership routes to information-architecture-spec;
missing flow states route to user-flow-spec; missing copy/data routes to
content-model-spec or data-model-spec.

## Completion Conditions

Return `COMPLETED` when screens are ready for UI design and implementation.
Return `FAILED_VALIDATION` when screen states or actions are incomplete.
