---
name: commerce-flow-coverage-qa
description: Validate that B2C commerce-domain specs close all core buyer, merchant, admin, payment, order, after-sales, risk, and downstream handoff loops.
---

# Commerce Flow Coverage QA Skill

> Internal sub-skill for app-domain/ecommerce pipelines. Status: bundled,
> domain-extension.

## Overview

Runs closure QA for ecommerce-domain contracts before downstream UI/code work
starts.

## Input Contract

Required: commerce registry, all selected commerce specs, commerce program
handoff extension, app surface topology, app screen requirements, and app data
model.

Optional: app-design UI handoff, app-design program handoff, app closure QA
report, existing test plan, API docs, provider sandbox docs, compliance
checklist, and analytics event plan.

## Output Contract

Writes `.allforai/app-domain/ecommerce/qa/commerce-flow-coverage-qa-report.json`.

The report must include `coverage_matrix`, `missing_domain_contracts`,
`state_machine_findings`, `role_surface_findings`, `handoff_findings`,
`verification_findings`, `blocked_items`, `repair_routes`, `state`, and
`consumer_refs`.

Allowed states: `passed`, `failed`, `needs_revision`, `blocked_by_missing_artifact`.

## Invocation Contract

```json
{"skill":"app-domain/ecommerce/commerce-flow-coverage-qa","mode":"validate","input_paths":{"registry":".allforai/app-domain/ecommerce/commerce-domain-registry.json","catalog":".allforai/app-domain/ecommerce/spec/catalog-merchandising-spec.json","search":".allforai/app-domain/ecommerce/spec/search-discovery-spec.json","checkout":".allforai/app-domain/ecommerce/spec/cart-checkout-payment-spec.json","orders":".allforai/app-domain/ecommerce/spec/order-fulfillment-after-sales-spec.json","ops":".allforai/app-domain/ecommerce/spec/merchant-platform-ops-spec.json","pricing":".allforai/app-domain/ecommerce/spec/promotion-pricing-membership-spec.json","risk":".allforai/app-domain/ecommerce/spec/commerce-risk-compliance-spec.json","handoff":".allforai/app-domain/ecommerce/handoff/commerce-program-handoff-extension.json","topology":".allforai/app-design/spec/app-surface-topology-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","data_model":".allforai/app-design/spec/data-model-spec.json"},"output_root":".allforai/app-domain/ecommerce/qa"}
```

Supported modes: `validate`, `repair_check`.

## Automatic Validation

Verify these loops are closed:

- Discovery to product detail to cart to checkout to payment to order.
- Order to fulfillment to receipt to review and after-sales.
- Merchant catalog/order/settlement operations to platform audit.
- Admin/customer-service intervention to permission and audit logs.
- Promotion/pricing rules to checkout calculation, refund, and settlement.
- Risk/compliance events to manual review, security inputs, and verification.
- Every commerce requirement to app screen, data/API implication, downstream
  implementation owner, and product-verify scenario.

Do not pass QA by narrative explanation. Every pass must cite source artifacts
and specific IDs. If an artifact is missing or unparseable, return
`blocked_by_missing_artifact`.

## Completion Conditions

Return `COMPLETED` only when the report state is `passed`. Return
`FAILED_VALIDATION` when any core commerce loop, role, state machine, or
downstream handoff is not traceable.
