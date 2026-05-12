---
name: game-genre-common-20-spec-deck-building-spec
description: Internal bundled meta-skill module for game-genre-common/20-spec/deck-building-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Deck Building Spec Skill

> Internal sub-skill for game-genre-common pipelines. Status: bundled, inactive, not wired.

## Overview

Defines deck, card pool, hand, draw, discard, exhaust, upgrade, rarity, draft,
and build archetype rules.

## Input Contract

Required: item/skill design list or card content brief.

Optional: economy, progression, run structure, balance goals, collection system,
and UI requirements.

## Output Contract

Writes `.allforai/game-design/genre-common/deck-building-spec.json` and a report.
Entries include `deck_rule_id`, `deck_size`, `hand_rule`, `draw_rule`,
`discard_rule`, `card_pool_refs`, `rarity_rules`, `upgrade_rules`,
`archetype_refs`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_card_pool`.

## Invocation Contract

```json
{"skill":"game-genre-common/deck-building-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/genre-common"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check draw consistency, dead-hand risk, deck size constraints, card pool
coverage, build archetype viability, and UI readability.

Repair routing: card gaps route to item-skill-design-generation; numeric gaps
route to game-balance; UI gaps route to game-ui.

## Completion Conditions

Return `COMPLETED` when deck rules are playable. Return `FAILED_VALIDATION`
when deck flow can stall or lacks viable builds.
