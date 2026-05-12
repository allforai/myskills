---
name: merchant-platform-ops-spec
description: Define ecommerce merchant, platform admin, operator, customer service, finance, audit, and permission boundary contracts.
---

# Merchant Platform Ops Spec Skill

> Internal sub-skill for app-domain/ecommerce pipelines. Status: bundled,
> domain-extension.

## Overview

Defines non-buyer operations for merchant-facing, platform-admin, customer
service, finance, audit, and moderation surfaces.

## Input Contract

Required: commerce registry, app surface topology, audience positioning, IA,
screen requirements, permissions/settings spec, and data model.

Optional: org structure, approval policy, settlement model, audit policy,
customer-service macros, merchant onboarding policy, and moderation rules.

## Output Contract

Writes `.allforai/app-domain/ecommerce/spec/merchant-platform-ops-spec.json`.

The spec must include `role_model`, `merchant_onboarding`, `merchant_console`,
`platform_admin_console`, `operator_workflows`, `customer_service_workflows`,
`finance_workflows`, `moderation_workflows`, `approval_flows`,
`rbac_permissions`, `audit_log_requirements`, `bulk_operations`,
`screen_refs`, `api_implications`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_surface_topology`, `blocked_by_permissions`.

## Invocation Contract

```json
{"skill":"app-domain/ecommerce/merchant-platform-ops-spec","mode":"spec_validate","input_paths":{"registry":".allforai/app-domain/ecommerce/commerce-domain-registry.json","topology":".allforai/app-design/spec/app-surface-topology-spec.json","audience":".allforai/app-design/concept/audience-positioning-spec.json","ia":".allforai/app-design/spec/information-architecture-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","permissions":".allforai/app-design/spec/permissions-notifications-settings-spec.json","data_model":".allforai/app-design/spec/data-model-spec.json"},"output_root":".allforai/app-domain/ecommerce/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every non-buyer actor has surface, permissions, allowed operations,
approval needs, audit events, and product verification path. Reject ops specs
that put merchant, customer service, finance, and super-admin into one
undifferentiated admin role.

Repair routing: missing surfaces route to app-surface-topology-spec; missing
permissions route to permissions-notifications-settings-spec; missing screens
route to screen-requirements-spec.

## Completion Conditions

Return `COMPLETED` when all non-buyer operations can be assigned to concrete
surfaces, roles, screens, APIs, and audit logs. Return `FAILED_VALIDATION` when
permission boundaries are unsafe or ambiguous.
