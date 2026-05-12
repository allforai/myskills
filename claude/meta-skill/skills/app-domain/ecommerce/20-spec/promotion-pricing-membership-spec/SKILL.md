---
name: promotion-pricing-membership-spec
description: Define ecommerce pricing, promotion, coupon, campaign, membership, points, stacking, and settlement-impact contracts.
---

# Promotion Pricing Membership Spec Skill

> Internal sub-skill for app-domain/ecommerce pipelines. Status: bundled,
> domain-extension.

## Overview

Defines commercial rules that affect price presentation, checkout calculation,
campaign operations, membership benefits, and settlement.

## Input Contract

Required: commerce registry, catalog spec, monetization/subscription spec if
present, screen requirements, data model, and merchant ops spec.

Optional: campaign calendar, coupon examples, membership levels, points policy,
tax policy, shipping fee policy, marketplace commission policy, and settlement
rules.

## Output Contract

Writes `.allforai/app-domain/ecommerce/spec/promotion-pricing-membership-spec.json`.

The spec must include `base_price_rules`, `price_display_rules`,
`promotion_types`, `coupon_rules`, `campaign_rules`, `membership_rules`,
`points_rules`, `stacking_rules`, `exclusion_rules`, `calculation_order`,
`rounding_precision`, `settlement_impacts`, `refund_impacts`, `screen_refs`,
`api_implications`, `test_scenarios`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_catalog`,
`blocked_by_ops`.

## Invocation Contract

```json
{"skill":"app-domain/ecommerce/promotion-pricing-membership-spec","mode":"spec_validate","input_paths":{"registry":".allforai/app-domain/ecommerce/commerce-domain-registry.json","catalog":".allforai/app-domain/ecommerce/spec/catalog-merchandising-spec.json","ops":".allforai/app-domain/ecommerce/spec/merchant-platform-ops-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","data_model":".allforai/app-design/spec/data-model-spec.json"},"output_root":".allforai/app-domain/ecommerce/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every discount has eligibility, owner, start/end, stackability, budget or
limit, refund impact, and display rule. Check calculation order is deterministic
and uses integer minor units or explicit precision. Reject rules where frontend
can authoritatively decide final payable amount.

Repair routing: missing SKU/product applicability routes to
catalog-merchandising-spec; missing admin ownership routes to
merchant-platform-ops-spec; missing checkout display routes to
cart-checkout-payment-spec.

## Completion Conditions

Return `COMPLETED` when pricing can be calculated, displayed, tested, audited,
and reconciled. Return `FAILED_VALIDATION` when promotion stacking or settlement
impact is undefined.
