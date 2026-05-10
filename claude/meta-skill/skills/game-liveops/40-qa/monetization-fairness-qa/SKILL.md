# Monetization Fairness QA Skill

> Internal sub-skill for game-liveops pipelines. Status: bundled, inactive, not wired.

## Overview

Validates monetization fairness, P2W risk, pressure tactics, value disclosure,
regional constraints, and player trust.

## Input Contract

Required: monetization spec and economy/reward specs.

Optional: retention loops, task spec, event spec, platform policy, and regional
legal constraints.

## Output Contract

Writes `.allforai/game-design/liveops/monetization-fairness-qa-report.json`.
Issues include `issue_id`, `offer_id`, `severity`, `fairness_axis`, `expected`,
`actual`, `root_cause`, `repair_target`, `blocks_release`, and `consumer_refs`.

Allowed statuses: `passed`, `passed_with_warnings`, `needs_revision`,
`blocked_by_policy_evidence`, `failed_validation`.

## Invocation Contract

```json
{"skill":"game-liveops/monetization-fairness-qa","mode":"validate","input_paths":{},"output_root":".allforai/game-design/liveops"}
```

Supported modes: `validate`, `repair_targets`.

## Automatic Validation

Check pay-to-win, unclear value, excessive pressure, manipulative streaks,
regional disclosure gaps, and conflicts with player experience. If legal policy
evidence is unavailable, report it as missing evidence.

Repair routing: offer defects route to monetization-spec; economy pressure
routes to economy-source-sink or reward-pricing; retention pressure routes to
retention-loop-spec.

## Completion Conditions

Return `COMPLETED` when monetization has no blocker fairness risks. Return
`FAILED_VALIDATION` when monetization undermines fairness or disclosure.
