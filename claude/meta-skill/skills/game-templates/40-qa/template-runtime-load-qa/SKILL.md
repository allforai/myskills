# Template Runtime Load QA Skill

> Internal sub-skill for game-templates pipelines. Status: bundled, inactive, not wired.

## Overview

Validates that template instances can be parsed, resolved, and loaded by the
frontend/runtime data layer or adapter without substituting static inspection
for executable evidence.

## Input Contract

Required: template instances, frontend/runtime profile, game data binding spec
or runtime loader contract, and reference closure QA report.

Optional: build/test commands, loader logs, schema parser output, runtime smoke
test, Playwright/browser evidence, and engine CLI evidence.

## Output Contract

Writes `.allforai/game-templates/qa/template-runtime-load-qa-report.json`.

Verdicts must include `template_id`, `template_kind`, `loader_target`,
`validation_method`, `status`, `evidence_paths`, `parse_errors`,
`resolution_errors`, `missing_refs`, `repair_target`, and `blocks_runtime`.

Allowed statuses: `load_ready`, `load_ready_with_warnings`, `needs_revision`,
`missing_template`, `loader_unavailable`, `failed_validation`.

## Invocation Contract

```json
{
  "skill": "game-templates/template-runtime-load-qa",
  "mode": "validate",
  "input_paths": {
    "instances": ".allforai/game-templates/instances",
    "frontend_runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "game_data_binding": ".allforai/game-frontend/bindings/game-data-binding-spec.json",
    "closure_report": ".allforai/game-templates/qa/template-reference-closure-qa-report.json"
  },
  "output_root": ".allforai/game-templates/qa"
}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Run the strongest available parser, loader, adapter dry-run, frontend data
binding probe, or runtime smoke test. Static JSON validation alone is diagnostic
only when a runtime loader is required. If no loader can run, return
`loader_unavailable`.

Repair routing: parse errors route to schema or instances; unresolved refs route
to reference binding; loader mismatches route to game-frontend data binding or
runtime loader contracts.

## Completion Conditions

Return `COMPLETED` when templates can load or only non-blocking warnings remain.
Return `FAILED_VALIDATION` when required templates cannot parse, resolve, load,
or produce executable evidence.
