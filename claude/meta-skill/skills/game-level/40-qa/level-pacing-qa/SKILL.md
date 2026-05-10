# Level Pacing QA Skill

> Internal sub-skill for game-level pipelines. Status: bundled, inactive, not wired.

## Overview

Validates level pacing across teaching, encounters, rewards, rest points,
difficulty spikes, psychological curve, and objective progress.

## Input Contract

Required: level flow design, level layout spec, teaching beats, encounter
placement, reward placement when applicable, and level difficulty budget when
the game has explicit difficulty targets.

Optional: blockout previews, playtest traces, progression curve, and combat
balance report.

## Output Contract

Writes `.allforai/game-design/levels/level-pacing-qa-report.json`. Issues
include `issue_id`, `level_id`, `region_ref`, `severity`, `pacing_axis`,
`budget_ref`, `psychological_axis`, `expected`, `actual`, `root_cause`,
`repair_target`, `blocks_runtime`, and `consumer_refs`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_missing_evidence`, `failed_validation`.

## Invocation Contract

```json
{"skill":"game-level/level-pacing-qa","mode":"validate","input_paths":{"difficulty_budget":".allforai/game-design/levels/level-difficulty-budget-spec.json"},"output_root":".allforai/game-design/levels"}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check teaching density, encounter spacing, reward cadence, rest beats,
difficulty spikes, and objective clarity. If blockout/playtest evidence is
required but unavailable, report missing evidence.

When a difficulty budget exists, compare actual encounters, hazards, rewards,
recovery beats, retry cost, and spike deltas against budget entries. A level
with acceptable average pacing can still fail if any region violates spike
limits or lacks counterplay/recovery for its pressure budget.

Also compare psychological curve expectations: entry emotion, target emotion,
tension, cognitive load, relief windows, confidence recovery, frustration risk,
motivation payoff, and fatigue risk. A level should fail pacing QA if it stacks
high stress or high cognitive load without recovery, teaches and tests too much
at once, or lacks evidence for declared psychological outcomes.

Validate `pacing_phase` order against the methodology in
`level-difficulty-budget-spec`: safe introduction before learning, learning
before confirmation, confirmation before peak tests, and release/recovery after
high pressure unless an explicit endurance budget exists. Flag random rewards,
unreadable danger, hidden pressure, missing anticipation, and failure-cost /
recovery mismatches.

Repair routing: teaching defects route to teaching-beat-spec; encounter defects
route to encounter-placement-spec; reward defects route to
reward-placement-spec; budget defects route to level-difficulty-budget-spec.

## Completion Conditions

Return `COMPLETED` when level pacing has no blocker issues. Return
`FAILED_VALIDATION` when a level has unplayable pacing or unverifiable evidence.
