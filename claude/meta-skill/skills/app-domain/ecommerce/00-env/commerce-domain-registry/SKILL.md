---
name: commerce-domain-registry
description: Establish the B2C commerce domain scope, actors, platform type, required commerce modules, artifact paths, and downstream consumers for an ecommerce app-design workflow.
---

# Commerce Domain Registry Skill

> Internal sub-skill for app-domain/ecommerce pipelines. Status: bundled,
> domain-extension.

## Overview

Classifies the commerce product shape and selects required domain modules before
commerce specs are generated.

## Input Contract

Required: product concept, app surface topology, audience positioning, and job
story spec.

Optional: existing system docs, payment/logistics/provider constraints, SKU
model notes, marketplace/self-operated scope, compliance constraints, regions,
currencies, and human business preferences.

## Output Contract

Writes `.allforai/app-domain/ecommerce/commerce-domain-registry.json`.

The registry must include `platform_type`, `commerce_scope`, `actors`,
`surfaces`, `required_modules`, `optional_modules`, `artifact_index`,
`human_decisions`, `unknowns`, `downstream_consumers`, `state`, and
`consumer_refs`.

Allowed `platform_type`: `self_operated_b2c`, `marketplace_b2c`,
`hybrid_self_operated_marketplace`, `brand_store`, `multi_store`, `unknown`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_concept`.

## Invocation Contract

```json
{"skill":"app-domain/ecommerce/commerce-domain-registry","mode":"domain_scope_validate","input_paths":{"concept":".allforai/product-concept/concept-baseline.json","topology":".allforai/app-design/spec/app-surface-topology-spec.json","audience":".allforai/app-design/concept/audience-positioning-spec.json","jobs":".allforai/app-design/concept/job-story-spec.json"},"output_root":".allforai/app-domain/ecommerce"}
```

Supported modes: `domain_scope_validate`, `validate_existing`,
`repair_existing`.

## Automatic Validation

Check that buyer, platform operator, customer service, and finance ownership are
explicitly handled. If merchant-facing features exist, require merchant actor and
merchant/admin surfaces. Reject a registry that selects payment, logistics,
settlement, or after-sales modules without identifying responsible actors and
surfaces.

Repair routing: missing product scope routes to product concept; missing surface
ownership routes to app-surface-topology-spec; missing jobs route to
job-story-spec.

## Completion Conditions

Return `COMPLETED` when downstream commerce specs can be selected and every
selected module has an owner, input artifact, and output artifact. Return
`FAILED_VALIDATION` when the platform type or actor boundary is ambiguous.
