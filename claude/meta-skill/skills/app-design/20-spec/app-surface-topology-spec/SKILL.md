---
name: app-design-20-spec-app-surface-topology-spec
description: Internal bundled meta-skill module for app-design/20-spec/app-surface-topology-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# App Surface Topology Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled,
> bootstrap-wired, invoked by app-design node-specs.

## Overview

Defines the app's deployable surfaces, client/backend shape, technology stacks,
shared modules, ownership boundaries, and specialization rules before UI,
data, and implementation handoff are generated.

## Input Contract

Required: product concept baseline, bootstrap profile modules, target
platforms, business roles, and user goal.

Optional: existing repo structure, monorepo/workspace config, design system,
auth provider, BaaS/serverless provider, admin roles, mobile/web/desktop
targets, and deployment constraints.

## Output Contract

Writes `.allforai/app-design/spec/app-surface-topology-spec.json`.

Surfaces must include `surface_id`, `surface_type`, `audience_refs`,
`platforms`, `tech_stack`, `module_path`, `runtime_shape`, `shared_refs`,
`backend_dependency`, `state_ownership`, `design_system_scope`,
`implementation_node_refs`, `compile_node_ref`, `test_node_refs`,
`product_verify_refs`, `state`, and `consumer_refs`.

Allowed `surface_type` values: `web_app`, `marketing_site`, `admin_console`,
`operator_console`, `partner_console`, `mobile_app`, `desktop_app`, `backend_api`,
`baas`, `serverless_functions`, `shared_package`, `cli`, `worker`, `unknown`.

Allowed `runtime_shape` values: `pure_client`, `pure_backend`, `client_backend`,
`multi_frontend_unified_backend`, `multi_frontend_multi_backend`, `baas_backed`,
`serverless`, `desktop_embedded_backend`, `monorepo_mixed`, `unknown`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_profile`.

## Invocation Contract

```json
{"skill":"app-design/app-surface-topology-spec","mode":"spec_validate","input_paths":{"concept":".allforai/product-concept/concept-baseline.json","bootstrap_profile":".allforai/bootstrap/bootstrap-profile.json"},"output_root":".allforai/app-design/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every user-facing surface has an audience, platform, tech stack, module
path or generation target, and validation path. Check every backend/shared
module has at least one consumer or explicit standalone reason. Reject generic
"frontend" or "backend" labels when multiple surfaces or roles exist.

For pure-client apps, require local persistence/offline/runtime validation
instead of API assumptions. For pure-backend apps, mark UI design not
applicable and route verification to API/contract tests. For multi-surface
apps, require each surface to have independent compile/test/product-verify
coverage and a shared design-system/data-contract strategy.

Repair routing: missing module evidence routes to bootstrap profile; missing
audience/role ownership routes to audience-positioning-spec; missing backend or
state ownership routes to data-model-spec; missing validation paths route to
program-handoff-generation.

## Completion Conditions

Return `COMPLETED` when downstream app-design and implementation nodes can
specialize per surface and technology stack. Return `FAILED_VALIDATION` when
the app shape is ambiguous enough that implementation nodes would be generic.
