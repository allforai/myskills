---
name: app-design-20-spec-feature-priority-spec
description: Internal bundled meta-skill module for app-design/20-spec/feature-priority-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Feature Priority Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

## Overview

Defines MVP scope, release cuts, priority rationale, dependency order,
non-goals, and tradeoffs.

## Input Contract

Required: product concept baseline and job story spec.

Optional: business KPIs, technical constraints, monetization spec, market
research, timeline, team capacity, and compliance constraints.

## Output Contract

Writes `.allforai/app-design/spec/feature-priority-spec.json`.

Feature entries must include `feature_id`, `job_refs`, `priority`,
`release_phase`, `rationale`, `dependency_refs`, `risk`, `defer_reason`,
`non_goal_boundary`, `acceptance_signal`, `state`, and `consumer_refs`.

Allowed priorities: `must`, `should`, `could`, `defer`, `out_of_scope`.
Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_jobs`.

## Invocation Contract

```json
{"skill":"app-design/feature-priority-spec","mode":"spec_validate","input_paths":{"jobs":".allforai/app-design/concept/job-story-spec.json","concept":".allforai/product-concept/concept-baseline.json"},"output_root":".allforai/app-design/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every must-have concept feature has a priority and every `must` feature
maps to a job, acceptance signal, and dependency order. Reject unbounded MVPs.

Repair routing: unclear value routes to product-concept; missing job purpose
routes to job-story-spec; technical dependency gaps route to program handoff.

## Completion Conditions

Return `COMPLETED` when scope can drive implementation sequencing. Return
`FAILED_VALIDATION` when MVP or non-goals are ambiguous.
