# Template Inheritance Spec Skill

> Internal sub-skill for game-templates pipelines. Status: bundled, inactive, not wired.

## Overview

Defines base templates, variants, inheritance, override rules, merge policy,
reference override policy, and cycle prevention.

## Input Contract

Required: template registry and template schemas.

Optional: content taxonomy, existing template instances, balance tiers,
difficulty variants, skin/cosmetic variants, localization variants, and runtime
loader constraints.

## Output Contract

Writes:

- `.allforai/game-templates/schemas/template-inheritance-spec.json`
- `.allforai/game-templates/schemas/template-inheritance-report.json`

Rules must include `template_kind`, `base_template_policy`, `variant_policy`,
`overrideable_fields`, `locked_fields`, `merge_strategy`, `ref_override_policy`,
`cycle_detection`, `runtime_resolution_policy`, `state`, and `repair_target`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_schema`, `blocked_by_runtime_loader`.

## Invocation Contract

```json
{
  "skill": "game-templates/template-inheritance-spec",
  "mode": "spec_validate",
  "input_paths": {
    "registry": ".allforai/game-templates/template-registry.json",
    "schemas": ".allforai/game-templates/schemas"
  },
  "output_root": ".allforai/game-templates/schemas"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that inheritance has deterministic resolution, no cycles, no hidden
required fields, and no illegal override of locked source refs. Runtime loader
must know whether templates are pre-flattened or resolved at load time.

Repair routing: illegal overrides route to template schema; runtime resolution
gaps route to game-frontend/game-runtime loader contracts.

## Completion Conditions

Return `COMPLETED` when inheritance can be resolved deterministically. Return
`FAILED_VALIDATION` when cycles, ambiguous merges, or illegal overrides exist.
