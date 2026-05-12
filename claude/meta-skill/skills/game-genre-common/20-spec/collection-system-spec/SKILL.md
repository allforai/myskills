---
name: game-genre-common-20-spec-collection-system-spec
description: Internal bundled meta-skill module for game-genre-common/20-spec/collection-system-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Collection System Spec Skill

> Internal sub-skill for game-genre-common pipelines. Status: bundled, inactive, not wired.

## Overview

Defines collectable catalogues, rarity, ownership, duplicates, completion,
display, rewards, album/book UI, and collection-driven progression.

## Input Contract

Required: content taxonomy or item/card/character list.

Optional: economy, progression, monetization, UI registry, art requirements, and
achievement system.

## Output Contract

Writes `.allforai/game-design/genre-common/collection-system-spec.json` and a
report. Collections include `collection_id`, `entry_refs`, `rarity_rules`,
`ownership_rules`, `duplicate_rules`, `completion_rewards`, `display_rules`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_content`.

## Invocation Contract

```json
{"skill":"game-genre-common/collection-system-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/genre-common"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check catalogue completeness, duplicate handling, rarity distribution, reward
purpose, and UI/art ownership.

Repair routing: content gaps route to content registry; rarity/reward gaps to
drop-table or reward-pricing; UI/art gaps to game-ui/game-art.

## Completion Conditions

Return `COMPLETED` when collection rules are complete and owned. Return
`FAILED_VALIDATION` when collection entries cannot be obtained or displayed.
