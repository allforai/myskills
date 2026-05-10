# Genre Fit QA Skill

> Internal sub-skill for game-genre-common pipelines. Status: bundled, inactive, not wired.

## Overview

Validates whether selected genre-common contracts fit the selected genre,
player promise, session model, and production scope.

## Input Contract

Required: player experience contract, genre selection or scenario template, and
selected genre-common specs.

Optional: concrete genre pack outputs, game design closure report, playtest
evidence, and production constraints.

## Output Contract

Writes `.allforai/game-design/genre-common/genre-fit-qa-report.json`. Issues
include `issue_id`, `spec_ref`, `genre_ref`, `severity`, `fit_axis`,
`expected`, `actual`, `root_cause`, `repair_target`, `blocks_design`, and
`consumer_refs`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_genre`, `failed_validation`.

## Invocation Contract

```json
{"skill":"game-genre-common/genre-fit-qa","mode":"validate","input_paths":{},"output_root":".allforai/game-design/genre-common"}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check whether selected shared patterns are appropriate, over-scoped, missing
required genre expectations, or contradictory with player/session goals.

Repair routing: wrong pattern selection routes to genre routing; oversized
patterns route to owning spec; missing player promise routes to player
experience contract.

## Completion Conditions

Return `COMPLETED` when shared genre patterns fit the selected genre. Return
`FAILED_VALIDATION` when selected patterns contradict the genre promise.
