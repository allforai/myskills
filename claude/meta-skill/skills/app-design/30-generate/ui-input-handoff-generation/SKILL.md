# UI Input Handoff Generation Skill

> Internal sub-skill for app-design pipelines. Status: bundled, inactive, not wired.

## Overview

Generates the structured handoff consumed by UI design: screens, flows,
states, copy, priorities, interaction behavior, accessibility, and design
constraints.

## Input Contract

Required: information architecture, user flows, screen requirements, content
model, interaction patterns, and feature priority.

Optional: audience positioning, brand preferences, data model, permissions
spec, monetization spec, existing design system, and platform guidelines.

## Output Contract

Writes:

- `.allforai/app-design/handoff/ui-design-input-handoff.json`
- `.allforai/app-design/handoff/ui-design-input-handoff-report.json`

Handoff must include `screen_inventory`, `flow_inventory`, `state_matrix`,
`copy_requirements`, `interaction_requirements`, `accessibility_requirements`,
`priority_and_release_scope`, `open_questions`, `blocked_items`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_spec_gap`.

## Invocation Contract

```json
{"skill":"app-design/ui-input-handoff-generation","mode":"generate_validate","input_paths":{"ia":".allforai/app-design/spec/information-architecture-spec.json","flows":".allforai/app-design/spec/user-flow-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","content":".allforai/app-design/spec/content-model-spec.json","interaction":".allforai/app-design/spec/interaction-pattern-spec.json"},"output_root":".allforai/app-design/handoff"}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every UI-facing screen and state has source refs, copy/data/action
requirements, and priority. Reject handoffs that require UI designers to infer
missing behavior from conversation history.

Repair routing: screen gaps route to screen-requirements-spec; copy gaps route
to content-model-spec; interaction gaps route to interaction-pattern-spec.

## Completion Conditions

Return `COMPLETED` when UI design can proceed without unstated product
decisions. Return `FAILED_VALIDATION` when key screens or states lack source
requirements.
