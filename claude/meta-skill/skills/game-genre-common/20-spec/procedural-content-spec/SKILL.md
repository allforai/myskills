# Procedural Content Spec Skill

> Internal sub-skill for game-genre-common pipelines. Status: bundled, inactive, not wired.

## Overview

Defines seeded procedural content rules, constraints, distributions, rejection
rules, validation criteria, and repair loops for maps, runs, loot, encounters,
quests, or factions.

## Input Contract

Required: content taxonomy and target procedural content type.

Optional: run structure, level layout, drop tables, encounter placement,
content roadmap, and target engine constraints.

## Output Contract

Writes `.allforai/game-design/genre-common/procedural-content-spec.json` and a
report. Generators include `generator_id`, `seed_rule`, `content_kind`,
`input_pool_refs`, `distribution_rules`, `hard_constraints`, `soft_constraints`,
`rejection_rules`, `validation_rules`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_content_pool`.

## Invocation Contract

```json
{"skill":"game-genre-common/procedural-content-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/genre-common"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check determinism, seed replay, pool coverage, impossible constraints,
distribution ranges, and validation method. Missing executable validation must
be reported, not substituted.

Repair routing: pool gaps route to content registry; level constraints to
game-level; reward/drop issues to game-balance.

## Completion Conditions

Return `COMPLETED` when procedural rules are deterministic and verifiable.
Return `FAILED_VALIDATION` when constraints cannot generate valid content.
