---
name: app-design-20-spec-monetization-subscription-spec
description: Internal bundled meta-skill module for app-design/20-spec/monetization-subscription-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Monetization Subscription Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

## Overview

Defines pricing, trials, subscription tiers, paywalls, entitlements,
cancellation, billing states, and monetization fairness.

## Input Contract

Required: product concept baseline, feature priority spec, and audience
positioning spec.

Optional: payment provider, business model, app store rules, refund policy,
analytics funnel, enterprise sales motion, and legal constraints.

## Output Contract

Writes `.allforai/app-design/spec/monetization-subscription-spec.json`.

Outputs must include `business_model`, `tiers`, `trial_rules`, `paywall_points`,
`entitlements`, `upgrade_downgrade_paths`, `cancellation_flow`,
`billing_states`, `fairness_constraints`, `analytics_events`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `not_applicable`,
`blocked_by_business_model`.

## Invocation Contract

```json
{"skill":"app-design/monetization-subscription-spec","mode":"spec_validate","input_paths":{"concept":".allforai/product-concept/concept-baseline.json","priority":".allforai/app-design/spec/feature-priority-spec.json","audience":".allforai/app-design/concept/audience-positioning-spec.json"},"output_root":".allforai/app-design/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

If monetization is present, check paid value maps to features, entitlements are
implementable, cancellation is reachable, and paywalls do not block critical
promised free value. If monetization is absent, mark `not_applicable`.

Repair routing: unclear pricing routes to product-concept; entitlement gaps
route to feature-priority-spec; payment implementation gaps route to program
handoff.

## Completion Conditions

Return `COMPLETED` when monetization is either explicitly not applicable or
fully specified. Return `FAILED_VALIDATION` when paid access rules are
ambiguous.
