---
name: app-design-20-spec-app-surface-topology-spec
description: Define deployable surfaces, client/backend shape, technology stacks, shared modules, ownership boundaries, and specialization rules before UI, data, and implementation handoff; writes spec/app-surface-topology-spec.json.
---

# App Surface Topology Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled.

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

Outputs must also include top-level `service_endpoints`. The field is always
present; pure-client apps write `[]`. Each entry is
`{endpoint_id, purpose, consumer_surface_refs, audience, provisioning,
requirement_ref?}`. `audience` means "who supplies this value" and is exactly
one of `end-user`, `operator` (the deploying party, the default), or
`developer`; `provisioning` is one of `build-time`, `remote-config`, or
`deploy-env`. `requirement_ref` is the id of a confirmed requirement and is
required when `audience` is `end-user`. See
`knowledge/defensive-patterns.md` Pattern J (Audience Isolation).

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

Check every surface with a non-empty `backend_dependency` has a matching
`service_endpoints[]` entry whose `consumer_surface_refs` names that surface.
Reject any endpoint missing `audience` or `provisioning`. Reject an
`audience: "end-user"` endpoint without `requirement_ref`.

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
