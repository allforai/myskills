# Monetization Spec Skill

> Internal sub-skill for game-liveops pipelines. Status: bundled, inactive, not wired.

## Overview

Defines revenue model, offers, SKUs, ads, battle pass, gacha, value anchors,
regional constraints, and fairness rules.

## Input Contract

Required: player experience contract and economy spec.

Optional: content roadmap, progression curve, legal/regional policy, platform
store constraints, and target revenue model.

## Output Contract

Writes `.allforai/game-design/liveops/monetization-spec.json` and a report.
Entries include `model`, `offer_id`, `price`, `value`, `availability`,
`purchase_limit`, `reward_refs`, `disclosure_requirements`, `fairness_rules`,
`state`, and `consumer_refs`.

Allowed states: `not_applicable`, `draft`, `validated`, `needs_revision`,
`blocked_by_policy`, `blocked_by_economy`.

## Invocation Contract

```json
{"skill":"game-liveops/monetization-spec","mode":"spec_validate","input_paths":{},"output_root":".allforai/game-design/liveops"}
```

Supported modes: `spec_validate`, `not_applicable`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that monetization does not contradict player promise, economy balance,
regional disclosure, or fairness constraints.

Repair routing: economy conflicts route to economy-source-sink or reward-pricing
specs; fairness conflicts route to monetization-fairness-qa.

## Completion Conditions

Return `COMPLETED` when monetization is fair and traceable or not applicable.
Return `FAILED_VALIDATION` when revenue design blocks player trust or legality.
