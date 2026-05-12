---
name: cart-checkout-payment-spec
description: Define ecommerce cart, checkout, address, invoice, payment, price snapshot, idempotency, and failure recovery contracts.
---

# Cart Checkout Payment Spec Skill

> Internal sub-skill for app-domain/ecommerce pipelines. Status: bundled,
> domain-extension.

## Overview

Defines the buyer purchase conversion contract from product selection through
payment result and order creation.

## Input Contract

Required: commerce registry, catalog spec, promotion/pricing spec if selected,
user flows, screen requirements, data model, and permissions/settings spec.

Optional: payment provider constraints, tax/invoice rules, address format,
guest checkout policy, wallet/store-credit policy, and region/currency rules.

## Output Contract

Writes `.allforai/app-domain/ecommerce/spec/cart-checkout-payment-spec.json`.

The spec must include `cart_model`, `checkout_steps`, `address_rules`,
`invoice_rules`, `shipping_option_rules`, `price_calculation_sequence`,
`order_price_snapshot`, `payment_methods`, `payment_state_machine`,
`idempotency_rules`, `timeout_and_release_rules`, `failure_recovery`,
`screen_refs`, `api_implications`, `test_scenarios`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_catalog`,
`blocked_by_pricing`.

## Invocation Contract

```json
{"skill":"app-domain/ecommerce/cart-checkout-payment-spec","mode":"spec_validate","input_paths":{"registry":".allforai/app-domain/ecommerce/commerce-domain-registry.json","catalog":".allforai/app-domain/ecommerce/spec/catalog-merchandising-spec.json","pricing":".allforai/app-domain/ecommerce/spec/promotion-pricing-membership-spec.json","flows":".allforai/app-design/spec/user-flow-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","data_model":".allforai/app-design/spec/data-model-spec.json"},"output_root":".allforai/app-domain/ecommerce/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check price calculation is server-authoritative and produces an immutable order
snapshot. Check each payment transition has trigger, actor, idempotency key,
timeout behavior, retry behavior, and user-visible state. Reject checkout flows
without stock reservation/release semantics and failed-payment recovery.

Repair routing: missing price rules route to promotion-pricing-membership-spec;
missing SKU availability routes to catalog-merchandising-spec; missing screens
route to screen-requirements-spec; missing API implications route to
commerce-program-handoff-extension.

## Completion Conditions

Return `COMPLETED` when cart, checkout, payment, and order-creation contracts
can be implemented and verified end to end. Return `FAILED_VALIDATION` when
price, stock, or payment state ownership is unclear.
