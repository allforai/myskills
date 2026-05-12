---
name: app-design-20-spec-data-model-spec
description: Internal bundled meta-skill module for app-design/20-spec/data-model-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Data Model Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

## Overview

Defines product-level data entities, fields, relationships, lifecycle,
ownership, permissions, and API implications.

## Input Contract

Required: job story spec, information architecture spec, and screen
requirements.

Optional: existing database schema, API docs, analytics events, auth model,
privacy constraints, import/export needs, and offline requirements.

## Output Contract

Writes `.allforai/app-design/spec/data-model-spec.json`.

Entities must include `entity_id`, `name`, `purpose`, `job_refs`,
`screen_refs`, `fields`, `relationships`, `lifecycle_states`, `ownership`,
`permission_rules`, `validation_rules`, `api_implications`, `retention_policy`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_screens`.

## Invocation Contract

```json
{"skill":"app-design/data-model-spec","mode":"spec_validate","input_paths":{"jobs":".allforai/app-design/concept/job-story-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json"},"output_root":".allforai/app-design/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every data field is used by a screen, flow, rule, or downstream API. Check
relationships have direction and cardinality. Reject entities with no lifecycle
or owner.

Repair routing: missing screen usage routes to screen-requirements-spec; missing
privacy or role rules route to permissions-notifications-settings-spec; API gaps
route to program-handoff-generation.

## Completion Conditions

Return `COMPLETED` when data can drive schema/API implementation. Return
`FAILED_VALIDATION` when entities are orphaned or permission ownership is
undefined.
