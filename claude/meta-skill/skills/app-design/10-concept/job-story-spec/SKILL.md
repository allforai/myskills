# Job Story Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, inactive, not wired.

## Overview

Turns app intent into concrete jobs, use cases, triggers, desired outcomes,
success signals, and failure/recovery expectations.

## Input Contract

Required: audience positioning spec and product concept baseline.

Optional: analytics funnels, support cases, workflow notes, domain rules,
existing IA, and business KPIs.

## Output Contract

Writes `.allforai/app-design/concept/job-story-spec.json`.

Job stories must include `job_id`, `audience_ref`, `situation`, `trigger`,
`motivation`, `desired_outcome`, `primary_success_signal`,
`failure_modes`, `recovery_expectations`, `frequency`, `priority`,
`screen_refs`, `data_refs`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_audience`, `blocked_by_concept`.

## Invocation Contract

```json
{"skill":"app-design/job-story-spec","mode":"spec_validate","input_paths":{"audience":".allforai/app-design/concept/audience-positioning-spec.json","concept":".allforai/product-concept/concept-baseline.json"},"output_root":".allforai/app-design/concept"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that each must-have feature maps to at least one job story and each
primary job has a trigger, outcome, failure mode, and measurable signal. Reject
feature lists that lack user situation or outcome.

Repair routing: missing audience routes to audience-positioning-spec; missing
feature purpose routes to product-concept; missing recovery routes to
user-flow-spec.

## Completion Conditions

Return `COMPLETED` when jobs can drive flows, screen requirements, priorities,
and verification. Return `FAILED_VALIDATION` when jobs are unmeasurable or not
traceable to users.
