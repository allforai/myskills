---
name: search-discovery-spec
description: Define ecommerce search, browse, filter, sort, recommendation, ranking intent, and no-result recovery contracts.
---

# Search Discovery Spec Skill

> Internal sub-skill for app-domain/ecommerce pipelines. Status: bundled,
> domain-extension.

## Overview

Defines buyer discovery behavior across search, category browse, filters,
ranking, recommendation slots, campaign entrances, and recovery states.

## Input Contract

Required: commerce registry, catalog spec, app IA, user flows, screen
requirements, and content model.

Optional: search logs, analytics funnels, SEO rules, recommendation constraints,
campaign plan, content-commerce requirements, and marketplace ranking policy.

## Output Contract

Writes `.allforai/app-domain/ecommerce/spec/search-discovery-spec.json`.

The spec must include `entry_points`, `query_behavior`, `filter_facets`,
`sort_options`, `ranking_intent`, `recommendation_slots`, `category_browse`,
`campaign_discovery`, `empty_no_result_recovery`, `personalization_rules`,
`analytics_events`, `screen_refs`, `api_implications`, `state`, and
`consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_catalog`.

## Invocation Contract

```json
{"skill":"app-domain/ecommerce/search-discovery-spec","mode":"spec_validate","input_paths":{"registry":".allforai/app-domain/ecommerce/commerce-domain-registry.json","catalog":".allforai/app-domain/ecommerce/spec/catalog-merchandising-spec.json","ia":".allforai/app-design/spec/information-architecture-spec.json","flows":".allforai/app-design/spec/user-flow-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","content":".allforai/app-design/spec/content-model-spec.json"},"output_root":".allforai/app-domain/ecommerce/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every discovery entry point leads to a screen, flow, and measurable event.
Check every facet maps to catalog attributes or derived business rules. Reject
ranking rules that conflict with compliance, merchant fairness, sponsored
placement disclosure, or sold-out visibility rules.

Repair routing: missing catalog fields route to catalog-merchandising-spec;
missing discovery screens route to screen-requirements-spec; missing event
ownership routes to program handoff.

## Completion Conditions

Return `COMPLETED` when search/browse/recommendation can drive buyer UI,
backend query contracts, analytics, and product verification. Return
`FAILED_VALIDATION` when filters or ranking cannot be traced to catalog data.
