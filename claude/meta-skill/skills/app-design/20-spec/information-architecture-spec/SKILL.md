---
name: app-design-20-spec-information-architecture-spec
description: Internal bundled meta-skill module for app-design/20-spec/information-architecture-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Information Architecture Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

## Overview

Defines app navigation, screen hierarchy, route taxonomy, entry points, and
information grouping.

## Input Contract

Required: job story spec, product concept baseline, and target platforms.

Optional: existing sitemap, app analytics, content model, data model, role
model, permission model, and localization constraints.

## Output Contract

Writes `.allforai/app-design/spec/information-architecture-spec.json`.

Outputs must include `nav_model`, `route_groups`, `screens`, `entry_points`,
`role_visibility`, `deep_link_rules`, `empty_state_targets`, `search_or_filter`,
`state`, and `consumer_refs`.

Screen entries must include `screen_id`, `name`, `purpose`, `job_refs`,
`parent_ref`, `route`, `primary_actions`, `data_refs`, and `downstream_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_jobs`.

## Invocation Contract

```json
{"skill":"app-design/information-architecture-spec","mode":"spec_validate","input_paths":{"jobs":".allforai/app-design/concept/job-story-spec.json"},"output_root":".allforai/app-design/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every primary job has an entry point and reachable screen path. Reject
orphan screens, circular navigation, hidden required actions, and routes with
no job or data purpose.

Repair routing: missing jobs route to job-story-spec; missing data ownership
routes to data-model-spec; overloaded navigation routes to feature-priority-spec.

## Completion Conditions

Return `COMPLETED` when IA can drive UI design and route implementation. Return
`FAILED_VALIDATION` when primary jobs cannot be reached.
