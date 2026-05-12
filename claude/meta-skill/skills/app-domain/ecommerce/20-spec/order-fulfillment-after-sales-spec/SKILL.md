---
name: order-fulfillment-after-sales-spec
description: Define ecommerce order lifecycle, fulfillment, logistics, receipt, refund, return, exchange, dispute, and after-sales contracts.
---

# Order Fulfillment After-Sales Spec Skill

> Internal sub-skill for app-domain/ecommerce pipelines. Status: bundled,
> domain-extension.

## Overview

Defines the post-purchase lifecycle shared by buyer UI, merchant operations,
platform operations, customer service, finance, logistics, and verification.

## Input Contract

Required: commerce registry, cart/checkout/payment spec, catalog spec, merchant
ops spec, user flows, screen requirements, and data model.

Optional: logistics provider rules, warehouse constraints, refund provider
rules, dispute policy, auto-confirm rules, and customer-service workflows.

## Output Contract

Writes `.allforai/app-domain/ecommerce/spec/order-fulfillment-after-sales-spec.json`.

The spec must include `order_state_machine`, `order_item_state_machine`,
`fulfillment_flow`, `logistics_status_mapping`, `receipt_rules`,
`cancellation_rules`, `refund_rules`, `return_rules`, `exchange_rules`,
`dispute_rules`, `service_intervention_rules`, `finance_settlement_impacts`,
`notifications`, `screen_refs`, `api_implications`, `test_scenarios`, `state`,
and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_checkout_payment`, `blocked_by_ops`.

## Invocation Contract

```json
{"skill":"app-domain/ecommerce/order-fulfillment-after-sales-spec","mode":"spec_validate","input_paths":{"registry":".allforai/app-domain/ecommerce/commerce-domain-registry.json","checkout":".allforai/app-domain/ecommerce/spec/cart-checkout-payment-spec.json","catalog":".allforai/app-domain/ecommerce/spec/catalog-merchandising-spec.json","ops":".allforai/app-domain/ecommerce/spec/merchant-platform-ops-spec.json","flows":".allforai/app-design/spec/user-flow-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","data_model":".allforai/app-design/spec/data-model-spec.json"},"output_root":".allforai/app-domain/ecommerce/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every order and order-item state has allowed transitions, actor,
permission, trigger, side effects, notification needs, and terminal states.
Check refund/return/exchange paths handle full, partial, rejected, timeout, and
manual-review outcomes. Reject lifecycle specs that cannot distinguish payment
status, fulfillment status, and after-sales status.

Repair routing: missing payment states route to cart-checkout-payment-spec;
missing role ownership routes to merchant-platform-ops-spec; missing screens
route to screen-requirements-spec.

## Completion Conditions

Return `COMPLETED` when downstream code can implement order lifecycle and
product verification can test purchase, fulfillment, cancellation, refund,
return, exchange, and dispute paths. Return `FAILED_VALIDATION` when state
machines are incomplete or mixed together.
