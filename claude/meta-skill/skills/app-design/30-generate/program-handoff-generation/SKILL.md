# Program Handoff Generation Skill

> Internal sub-skill for app-design pipelines. Status: bundled, inactive, not wired.

## Overview

Generates downstream implementation-node handoff for frontend, backend, data,
auth, notification, payment, settings, and QA work.

## Input Contract

Required: app design registry, feature priority, screen requirements, data
model, user flows, and permissions/settings spec when applicable.

Optional: monetization spec, content model, interaction pattern spec, target
stack, existing codebase analysis, and UI handoff.

## Output Contract

Writes:

- `.allforai/app-design/handoff/program-development-node-handoff.json`
- `.allforai/app-design/handoff/program-development-node-handoff-report.json`

Implementation entries must include `node_id`, `discipline`, `purpose`,
`source_refs`, `input_artifacts`, `expected_outputs`, `validation_required`,
`runtime_or_tooling_requirements`, `blocked_by`, `risk`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_spec_gap`.

## Invocation Contract

```json
{"skill":"app-design/program-handoff-generation","mode":"generate_validate","input_paths":{"registry":".allforai/app-design/app-design-registry.json","priority":".allforai/app-design/spec/feature-priority-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","data_model":".allforai/app-design/spec/data-model-spec.json","flows":".allforai/app-design/spec/user-flow-spec.json"},"output_root":".allforai/app-design/handoff"}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every `must` feature has at least one implementation node and every
implementation node has inputs, outputs, and validation evidence. Reject vague
handoffs such as "build app" without source refs.

Repair routing: missing feature scope routes to feature-priority-spec; missing
data/API details route to data-model-spec; missing validation routes to flow QA
or product-verify planning.

## Completion Conditions

Return `COMPLETED` when program development can start from structured nodes.
Return `FAILED_VALIDATION` when must-have features lack implementable handoff.
