---
name: catalog-merchandising-spec
description: Define B2C catalog, SPU/SKU, category, attribute, listing, review, and merchandising contracts for ecommerce product design.
---

# Catalog Merchandising Spec Skill

> Internal sub-skill for app-domain/ecommerce pipelines. Status: bundled,
> domain-extension.

## Overview

Defines the product catalog contract that buyer, merchant, platform admin,
search, checkout, inventory, and order flows must share.

## Input Contract

Required: commerce registry, app surface topology, information architecture,
screen requirements, and data model spec.

Optional: existing catalog schema, product feed samples, category taxonomy,
attribute dictionary, brand rules, moderation rules, and SEO needs.

## Output Contract

Writes `.allforai/app-domain/ecommerce/spec/catalog-merchandising-spec.json`.

The spec must include `catalog_model`, `spu_sku_model`, `category_model`,
`attribute_model`, `brand_model`, `inventory_visibility`, `product_lifecycle`,
`listing_review_flow`, `merchandising_slots`, `admin_operations`,
`merchant_operations`, `buyer_touchpoints`, `data_model_extensions`,
`screen_refs`, `api_implications`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_registry`,
`blocked_by_data_model`.

## Invocation Contract

```json
{"skill":"app-domain/ecommerce/catalog-merchandising-spec","mode":"spec_validate","input_paths":{"registry":".allforai/app-domain/ecommerce/commerce-domain-registry.json","topology":".allforai/app-design/spec/app-surface-topology-spec.json","ia":".allforai/app-design/spec/information-architecture-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","data_model":".allforai/app-design/spec/data-model-spec.json"},"output_root":".allforai/app-domain/ecommerce/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every buyer-visible product field has a source of truth, admin/merchant
owner, validation rule, and screen/API consumer. Check SKU attributes determine
price, inventory, fulfillment eligibility, and order snapshot behavior. Reject
catalog models that cannot represent off-shelf, sold-out, draft, pending review,
rejected, and deleted states.

Repair routing: missing screens route to screen-requirements-spec; missing
entities route to data-model-spec; missing merchant/admin ownership routes to
merchant-platform-ops-spec.

## Completion Conditions

Return `COMPLETED` when product listing, detail, management, review, and order
snapshot consumers can all use the catalog contract. Return `FAILED_VALIDATION`
when SPU/SKU semantics or lifecycle states are ambiguous.
