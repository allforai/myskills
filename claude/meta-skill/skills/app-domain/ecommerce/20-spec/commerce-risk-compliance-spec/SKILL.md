---
name: commerce-risk-compliance-spec
description: Define ecommerce fraud, abuse, payment risk, moderation, privacy, tax, invoice, and compliance checkpoints as product-domain requirements.
---

# Commerce Risk Compliance Spec Skill

> Internal sub-skill for app-domain/ecommerce pipelines. Status: bundled,
> domain-extension.

## Overview

Defines commerce risk and compliance as product requirements before technical
security design. It does not replace security implementation; it supplies the
business events, roles, decisions, and evidence needed by downstream security
and verification nodes.

## Input Contract

Required: commerce registry, checkout/payment spec, order/after-sales spec,
merchant ops spec, permissions/settings spec, and app surface topology.

Optional: region list, tax/invoice rules, privacy policy, payment provider
rules, fraud examples, content policy, sanctions/KYC requirements, and audit
retention policy.

## Output Contract

Writes `.allforai/app-domain/ecommerce/spec/commerce-risk-compliance-spec.json`.

The spec must include `risk_events`, `fraud_scenarios`, `abuse_controls`,
`payment_risk_controls`, `content_moderation_rules`, `privacy_controls`,
`tax_invoice_requirements`, `audit_evidence`, `manual_review_queues`,
`customer_notice_rules`, `security_design_inputs`, `verification_scenarios`,
`state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_payment`,
`blocked_by_ops`.

## Invocation Contract

```json
{"skill":"app-domain/ecommerce/commerce-risk-compliance-spec","mode":"spec_validate","input_paths":{"registry":".allforai/app-domain/ecommerce/commerce-domain-registry.json","checkout":".allforai/app-domain/ecommerce/spec/cart-checkout-payment-spec.json","orders":".allforai/app-domain/ecommerce/spec/order-fulfillment-after-sales-spec.json","ops":".allforai/app-domain/ecommerce/spec/merchant-platform-ops-spec.json","permissions":".allforai/app-design/spec/permissions-notifications-settings-spec.json"},"output_root":".allforai/app-domain/ecommerce/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check each risk event has trigger, actor, data needed, user impact, manual
review path, audit evidence, and downstream security/verification consumer.
Reject vague compliance notes that do not identify jurisdiction, event, or
surface. If the system cannot run provider or jurisdiction checks locally, mark
the compliance verification as unable to be automatically validated; do not
substitute generic QA.

Repair routing: missing payment events route to cart-checkout-payment-spec;
missing operational review queue routes to merchant-platform-ops-spec; missing
security implementation path routes to security-design.

## Completion Conditions

Return `COMPLETED` when risk/compliance requirements are traceable to business
events and downstream verification. Return `FAILED_VALIDATION` when payment,
privacy, or audit requirements are generic and untestable.
