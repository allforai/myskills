---
name: game-content-20-spec-quest-chain-spec
description: Internal bundled meta-skill module for game-content/20-spec/quest-chain-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Quest Chain Spec Skill

> Internal sub-skill for game-content pipelines. Status: bundled, inactive, not wired.

## Overview

Defines quest chains, prerequisites, objectives, rewards, narrative beats,
level refs, and progression gates.

## Input Contract

Required: content registry and narrative quest spec or quest brief.

Optional: level design, economy, progression, dialogue spec, and content roadmap.

## Output Contract

Writes `.allforai/game-design/content/quest-chain-spec.json` and a report.
Quest chain entries include `chain_id`, `quest_ids`, `prerequisites`,
`objectives`, `reward_refs`, `narrative_refs`, `level_refs`, `failure_rules`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_missing_quest`, `blocked_by_reward`.

## Invocation Contract

```json
{"skill":"game-content/quest-chain-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/content"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check prerequisite reachability, objective clarity, reward validity, narrative
continuity, and absence of dead-end quest states.

Repair routing: narrative gaps route to narrative-quest/story specs; reward gaps
route to economy or reward-pricing; level gaps route to game-level.

## Completion Conditions

Return `COMPLETED` when quest chains are reachable and reward-complete. Return
`FAILED_VALIDATION` when a required quest chain can dead-end.
