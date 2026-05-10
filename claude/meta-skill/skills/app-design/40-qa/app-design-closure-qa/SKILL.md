# App Design Closure QA Skill

> Internal sub-skill for app-design pipelines. Status: bundled, inactive, not wired.

## Overview

Runs final closure over app design contracts before approval, UI handoff, and
program implementation handoff.

## Input Contract

Required: app design registry, audience positioning, job stories, IA, flows,
feature priorities, screen requirements, UI handoff, and program handoff.

Optional: content model, data model, interaction patterns, permissions/settings
spec, monetization spec, flow coverage QA report, and approval records.

## Output Contract

Writes `.allforai/app-design/qa/app-design-closure-qa-report.json`.

Report must include `closure_status`, `artifact_coverage`, `traceability`,
`handoff_readiness`, `approval_blockers`, `missing_contracts`,
`repair_targets`, `downstream_risks`, `state`, and `consumer_refs`.

Allowed states: `passed`, `needs_revision`, `blocked_by_missing_artifact`.

## Invocation Contract

```json
{"skill":"app-design/app-design-closure-qa","mode":"validate","input_paths":{"registry":".allforai/app-design/app-design-registry.json","ui_handoff":".allforai/app-design/handoff/ui-design-input-handoff.json","program_handoff":".allforai/app-design/handoff/program-development-node-handoff.json"},"output_root":".allforai/app-design/qa"}
```

Supported modes: `validate`, `repair_check`.

## Automatic Validation

Check concept-to-job-to-flow-to-screen-to-data-to-handoff traceability. Check
no must-have feature is missing from UI or program handoff. Check approval
records are present for selected human-gate nodes.

Repair routing: missing UI requirements route to ui-input-handoff-generation;
missing implementation nodes route to program-handoff-generation; missing
source contracts route to the owning app-design spec skill.

## Completion Conditions

Return `COMPLETED` when app design is closed for downstream work. Return
`FAILED_VALIDATION` when any must-have requirement lacks a source, handoff, or
validation path.
