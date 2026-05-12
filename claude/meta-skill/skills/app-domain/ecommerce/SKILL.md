---
name: app-domain-ecommerce
description: Define B2C e-commerce product-domain requirements, business objects, lifecycle flows, admin/merchant boundaries, and downstream handoff contracts before app UI or code implementation.
---

# E-Commerce Domain Skill Pack

> Internal bundled sub-skill pack for app-domain pipelines. Status: bundled,
> domain-extension, invoked when `business_domain` is ecommerce, marketplace,
> retail commerce, or ordinary B2C platform.

## Purpose

E-Commerce owns product-domain planning for B2C commerce before UI/code
implementation. It turns concept and app-design outputs into commerce-specific
business contracts: catalog, discovery, cart, checkout, payment, order,
fulfillment, after-sales, merchant/admin operations, pricing, promotion,
membership, risk, and downstream implementation handoff.

This pack does not implement code. It must produce machine-consumable contracts
that app-design, frontend, backend, data, QA, and product-verify nodes can read.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `00-env` | `commerce-domain-registry` | Commerce scope, platform type, actors, surfaces, selected domain modules, and artifact index. |
| `20-spec` | `catalog-merchandising-spec` | SPU/SKU, categories, attributes, brands, product status, listing, review, and merchandising rules. |
| `20-spec` | `search-discovery-spec` | Search, browse, filters, sort, recommendation slots, ranking intent, and no-result recovery. |
| `20-spec` | `cart-checkout-payment-spec` | Cart, checkout, address, invoice, payment, idempotency, price snapshot, and failure recovery. |
| `20-spec` | `order-fulfillment-after-sales-spec` | Order state machine, fulfillment, logistics, receipt, refund, return, exchange, and dispute flows. |
| `20-spec` | `merchant-platform-ops-spec` | Merchant, platform admin, operator, customer service, finance, audit, and permission boundaries. |
| `20-spec` | `promotion-pricing-membership-spec` | Price rules, coupon, campaign, membership, points, stacking, settlement impact, and fairness constraints. |
| `20-spec` | `commerce-risk-compliance-spec` | Fraud, abuse, payment risk, content moderation, privacy, tax/invoice, and compliance checkpoints. |
| `30-generate` | `commerce-program-handoff-extension` | Commerce-specific implementation and verification handoff extension for downstream code nodes. |
| `40-qa` | `commerce-flow-coverage-qa` | Closure QA across commerce objects, state machines, roles, screens, APIs, and validation nodes. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/app-domain/ecommerce/00-env/commerce-domain-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-domain/ecommerce/20-spec/catalog-merchandising-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-domain/ecommerce/20-spec/search-discovery-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-domain/ecommerce/20-spec/cart-checkout-payment-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-domain/ecommerce/20-spec/order-fulfillment-after-sales-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-domain/ecommerce/20-spec/merchant-platform-ops-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-domain/ecommerce/20-spec/promotion-pricing-membership-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-domain/ecommerce/20-spec/commerce-risk-compliance-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-domain/ecommerce/30-generate/commerce-program-handoff-extension/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/app-domain/ecommerce/40-qa/commerce-flow-coverage-qa/SKILL.md
```

## Shared Output Root

All children write under `.allforai/app-domain/ecommerce`.

`commerce-program-handoff-extension.json` is the bridge into implementation. It
must be merged or referenced by
`.allforai/app-design/handoff/program-development-node-handoff.json`.

## Boundary

Do not design general UI layout here; route screen structure to app-design. Do
not choose concrete database engines, payment providers, or framework code
unless already fixed by project context. Missing product decisions route back to
product concept or app-design; missing technical decisions route to downstream
implementation planning.
