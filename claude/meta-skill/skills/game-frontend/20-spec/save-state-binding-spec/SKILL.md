# Save State Binding Spec Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Defines frontend save/local state bindings for settings, progress, unlocked
content, checkpoint state, accessibility preferences, and smoke-test reset
behavior.

## Input Contract

Required: frontend runtime profile, game design doc, progression/objective
requirements, and target platform storage constraints.

Optional: program handoff, economy/progression specs, UI settings screens,
existing save code, backend account requirements, and privacy constraints.

## Output Contract

Writes:

- `.allforai/game-frontend/bindings/save-state-binding-spec.json`
- `.allforai/game-frontend/bindings/save-state-binding-report.json`

Bindings must include `state_id`, `state_kind`, `source_requirement`,
`storage_target`, `schema`, `default_value`, `migration_policy`,
`reset_policy`, `privacy_notes`, `validation_probe`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_progression_contract`, `blocked_by_storage_policy`,
`blocked_by_runtime_profile`.

## Invocation Contract

```json
{
  "skill": "game-frontend/save-state-binding-spec",
  "mode": "spec_validate",
  "input_paths": {
    "runtime_profile": ".allforai/game-frontend/env/frontend-runtime-profile.json",
    "game_design_doc": ".allforai/game-design/game-design-doc.json",
    "program_handoff": ".allforai/game-design/design/program-development-node-handoff.json"
  },
  "output_root": ".allforai/game-frontend/bindings"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every persistent frontend state has owner, schema, default, reset,
save/load probe, and privacy/storage policy. Local-only saves must not imply
server account guarantees.

Repair routing: missing progression state routes to progression/objective spec;
missing settings UI routes to game-ui; unsupported storage routes to frontend
runtime detection.

## Completion Conditions

Return `COMPLETED` when required state can be saved, loaded, reset, and probed.
Return `FAILED_VALIDATION` when persistence is required but schema, storage, or
validation is missing.
