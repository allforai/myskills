---
name: commerce-program-handoff-extension
description: Generate a commerce-specific implementation and verification handoff extension that downstream frontend, backend, data, security, QA, and product verification nodes can consume.
---

# Commerce Program Handoff Extension Skill

> Internal sub-skill for app-domain/ecommerce pipelines. Status: bundled,
> domain-extension.

## Overview

Converts approved commerce-domain specs into concrete downstream development
and verification requirements. This complements, and must be referenced by,
app-design's `program-development-node-handoff.json`.

## Input Contract

Required: commerce registry and every selected commerce spec. Required app
inputs: app surface topology, app screen requirements, and app data model.

Optional: app-design program handoff if already produced, existing API docs,
database schema, payment/logistics provider docs, and deployment topology.

## Output Contract

Writes:

- `.allforai/app-domain/ecommerce/handoff/commerce-program-handoff-extension.json`
- `.allforai/app-domain/ecommerce/handoff/commerce-program-handoff-extension-report.json`

The handoff must include `domain_modules`, `entity_extensions`,
`state_machines`, `api_requirements`, `surface_requirements`,
`backend_requirements`, `admin_console_requirements`, `merchant_console_requirements`,
`integration_requirements`, `security_design_inputs`, `test_requirements`,
`product_verify_requirements`, `source_refs`, `blocked_items`, and `state`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_domain_specs`.

## Invocation Contract

```json
{"skill":"app-domain/ecommerce/commerce-program-handoff-extension","mode":"generate_validate","input_paths":{"registry":".allforai/app-domain/ecommerce/commerce-domain-registry.json","catalog":".allforai/app-domain/ecommerce/spec/catalog-merchandising-spec.json","search":".allforai/app-domain/ecommerce/spec/search-discovery-spec.json","checkout":".allforai/app-domain/ecommerce/spec/cart-checkout-payment-spec.json","orders":".allforai/app-domain/ecommerce/spec/order-fulfillment-after-sales-spec.json","ops":".allforai/app-domain/ecommerce/spec/merchant-platform-ops-spec.json","pricing":".allforai/app-domain/ecommerce/spec/promotion-pricing-membership-spec.json","risk":".allforai/app-domain/ecommerce/spec/commerce-risk-compliance-spec.json","topology":".allforai/app-design/spec/app-surface-topology-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","data_model":".allforai/app-design/spec/data-model-spec.json"},"output_root":".allforai/app-domain/ecommerce/handoff"}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every commerce module has at least one downstream implementation owner,
surface/API/data consumer, and verification requirement. Check state machines
map to APIs, persistence, UI states, and product-verify cases. Reject handoffs
that say only "implement ecommerce" or collapse buyer, merchant, admin, payment,
and after-sales into one generic feature.

If a required runtime/provider cannot be run or inspected, declare the affected
verification `unable_to_validate` and keep the downstream node blocked. Do not
replace it with weaker surrogate validation.

Repair routing: missing module refs route to the owning commerce spec; missing
surface refs route to app-design handoff; missing security refs route to
commerce-risk-compliance-spec and security-design.

## Completion Conditions

Return `COMPLETED` when downstream code nodes can plan concrete work for
commerce modules and verification nodes can assert domain behavior. Return
`FAILED_VALIDATION` when module-to-code or module-to-test traceability is absent.
