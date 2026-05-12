---
name: game-runtime-20-spec-procedural-generator-spec
description: Internal bundled meta-skill module for game-runtime/20-spec/procedural-generator-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Procedural Generator Spec Skill

> Internal sub-skill for game-runtime pipelines. Status: bundled, inactive, not wired.

## Overview

Defines executable procedural generation architecture: seed replay, generator
stages, content pools, constraints, rejection rules, debug visualization,
sample validation, and import/runtime contracts.

## Input Contract

Required: core loop, level design spec or content taxonomy, objective system
spec, difficulty spec, and runtime/engine constraints.

Optional: economy spec, enemy list, item/skill list, art constraints,
procedural design brief, replay/share needs, and telemetry requirements.

## Output Contract

Writes:

- `.allforai/game-runtime/simulation/procedural-generator-spec.json`
- `.allforai/game-runtime/simulation/procedural-generator-report.json`

Generators must include `generator_id`, `generated_scope`, `seed_contract`,
`pipeline_stages`, `input_pools`, `constraints`, `guarantees`,
`rejection_criteria`, `debug_visualization`, `sample_count`,
`validation_metrics`, `runtime_import_contract`, `test_command_or_validation_path`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_content_pool`, `blocked_by_runtime_unknown`,
`blocked_by_validation_unavailable`.

## Invocation Contract

```json
{
  "skill": "game-runtime/procedural-generator-spec",
  "mode": "spec_validate",
  "input_paths": {
    "level_design": ".allforai/game-design/systems/level-design-spec.json",
    "objectives": ".allforai/game-design/systems/objective-system-spec.json",
    "difficulty": ".allforai/game-design/systems/difficulty-experience-spec.json"
  },
  "output_root": ".allforai/game-runtime/simulation"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Generate or inspect sample outputs when tooling exists. Validate reachability,
objective satisfaction, content legality, difficulty distribution, reward
placement, deterministic replay when required, and debug visibility. If samples
cannot be generated, return a blocking status.

Repair routing: missing content pools route to game-design content taxonomy;
invalid spatial rules route to level design; runtime gaps route to implementation
feasibility QA.

## Completion Conditions

Return `COMPLETED` when generator specs are executable and sample-verifiable.
Return `FAILED_VALIDATION` when generated output can be invalid without a
declared rejection or test path.
