---
name: app-design-40-qa-flow-coverage-qa
description: Internal bundled meta-skill module for app-design/40-qa/flow-coverage-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Flow Coverage QA Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

## Overview

Validates that app flows cover jobs, screens, data, permissions, empty/error
states, and recovery paths.

## Input Contract

Required: job story spec, information architecture spec, user flow spec, and
screen requirements spec.

Optional: content model, data model, permissions/settings spec, monetization
spec, and analytics plan.

## Output Contract

Writes `.allforai/app-design/qa/flow-coverage-qa-report.json`.

Issues must include `issue_id`, `severity`, `job_ref`, `flow_ref`,
`screen_ref`, `coverage_axis`, `expected`, `actual`, `root_cause`,
`repair_target`, `blocks_downstream`, and `consumer_refs`.

Allowed states: `passed`, `needs_revision`, `blocked_by_missing_artifact`.

## Invocation Contract

```json
{"skill":"app-design/flow-coverage-qa","mode":"validate","input_paths":{"jobs":".allforai/app-design/concept/job-story-spec.json","ia":".allforai/app-design/spec/information-architecture-spec.json","flows":".allforai/app-design/spec/user-flow-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json"},"output_root":".allforai/app-design/qa"}
```

Supported modes: `validate`, `repair_check`.

## Automatic Validation

Check every primary job has reachable screens, happy path, error path, empty
state, recovery path, and completion signal. Check every flow step has data,
copy, action, and feedback ownership when required.

Repair routing: missing jobs route to job-story-spec; missing screens route to
information-architecture-spec; missing states route to screen-requirements-spec.

## Completion Conditions

Return `COMPLETED` when no blocker coverage issues remain. Return
`FAILED_VALIDATION` when primary app tasks cannot be completed or recovered.
