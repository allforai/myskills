---
name: app-design-20-spec-user-flow-spec
description: Internal bundled meta-skill module for app-design/20-spec/user-flow-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# User Flow Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

## Overview

Defines step-by-step user flows for primary jobs, including happy paths,
alternate paths, empty states, error states, recovery, and completion signals.

## Input Contract

Required: job story spec and information architecture spec.

Optional: data model, permission/settings spec, monetization spec, analytics
events, existing journey maps, and support pain points.

## Output Contract

Writes `.allforai/app-design/spec/user-flow-spec.json`.

Flows must include `flow_id`, `job_ref`, `entry_screen`, `steps`,
`happy_path_length`, `alternate_paths`, `error_paths`, `empty_states`,
`recovery_paths`, `exit_conditions`, `analytics_events`, `state`, and
`consumer_refs`.

Step entries must include `step_id`, `screen_ref`, `user_action`,
`system_response`, `data_or_permission_refs`, `validation_rules`, and
`feedback_required`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_ia`.

## Invocation Contract

```json
{"skill":"app-design/user-flow-spec","mode":"spec_validate","input_paths":{"jobs":".allforai/app-design/concept/job-story-spec.json","ia":".allforai/app-design/spec/information-architecture-spec.json"},"output_root":".allforai/app-design/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every primary job has a happy path, at least one failure/recovery path,
and a completion signal. Reject flows that depend on screens absent from IA or
actions with no visible feedback.

Repair routing: missing screens route to information-architecture-spec; missing
data or permissions route to data-model-spec or permissions-notifications-settings-spec.

## Completion Conditions

Return `COMPLETED` when flows are implementable and testable. Return
`FAILED_VALIDATION` when core tasks lack recovery or completion conditions.
