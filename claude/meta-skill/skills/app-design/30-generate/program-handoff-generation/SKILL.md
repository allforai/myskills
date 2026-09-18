---
name: app-design-30-generate-program-handoff-generation
description: Generate implementation-node handoff for every deployable surface and runtime module (frontend, mobile, desktop, backend, BaaS, data, auth, payment, QA); writes handoff/program-development-node-handoff.json.
---

# Program Handoff Generation Skill

> Internal sub-skill for app-design pipelines. Status: bundled.

## Overview

Generates downstream implementation-node handoff for every deployable app
surface and runtime module: frontend, mobile, desktop, backend, BaaS,
serverless, data, auth, notification, payment, settings, shared packages, and
QA work.

## Input Contract

Required: app design registry, app surface topology, feature priority, screen
requirements, data model, user flows, and permissions/settings spec when
applicable.

Optional: monetization spec, content model, interaction pattern spec, target
stack, existing codebase analysis, UI handoff, and domain handoff extensions
such as `.allforai/app-domain/ecommerce/handoff/commerce-program-handoff-extension.json`.

## Output Contract

Writes:

- `.allforai/app-design/handoff/program-development-node-handoff.json`
- `.allforai/app-design/handoff/program-development-node-handoff-report.json`

Implementation entries must include `node_id`, `surface_id`, `module_path`,
`surface_type`, `tech_stack`, `discipline`, `purpose`, `source_refs`,
`input_artifacts`, `expected_outputs`, `validation_required`,
`runtime_or_tooling_requirements`, `hard_blocked_by`, `compile_node_ref`,
`test_node_refs`, `product_verify_refs`, `runtime_smoke_ref`, `risk`, `state`,
and `consumer_refs`.

When a domain handoff extension exists, implementation entries must preserve its
module IDs, state-machine IDs, API requirements, and product-verify requirements
in `source_refs` and `input_artifacts`. Do not flatten domain-specific modules
such as catalog, checkout, payment, order, after-sales, merchant ops, or risk
into a generic "business logic" node.

The handoff JSON also carries top-level `settings_items[]` and
`service_endpoints[]`. `settings_items[]` carries every entry of the
permissions/settings spec's `settings_groups[].items[]` verbatim: `setting_id`,
`audience`, `provisioning`, `surface`, and `requirement_ref` are copied exactly
as the spec wrote them. `service_endpoints[]` carries the app surface
topology's `service_endpoints` entries verbatim in the same way. An
implementation entry that implements a settings item or consumes an endpoint
names that `setting_id` or `endpoint_id` in its `source_refs`. Audience is
never rewritten, narrowed, or guessed at handoff time: an item whose `audience`
or `provisioning` is missing upstream stays missing here and is reported.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_spec_gap`.

## Invocation Contract

```json
{"skill":"app-design/program-handoff-generation","mode":"generate_validate","input_paths":{"registry":".allforai/app-design/app-design-registry.json","topology":".allforai/app-design/spec/app-surface-topology-spec.json","priority":".allforai/app-design/spec/feature-priority-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","data_model":".allforai/app-design/spec/data-model-spec.json","flows":".allforai/app-design/spec/user-flow-spec.json","domain_handoff_extensions":[".allforai/app-domain/ecommerce/handoff/commerce-program-handoff-extension.json"]},"output_root":".allforai/app-design/handoff"}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every `must` feature has at least one implementation node on every
applicable surface. Check every surface from app-surface-topology has compile,
test, product-verify, and runtime-smoke strategy unless explicitly
not-applicable. Reject vague handoffs such as "build app" without source refs,
surface IDs, module paths, tech stack, and validation evidence.
If a domain handoff extension is present, check every domain module and
state-machine requirement is consumed by at least one implementation entry and
one verification entry.
Check every settings item in the permissions/settings spec appears in
`settings_items[]`. A non-`end-user` item is never assigned as interface work
to an implementation entry on an end-user surface; it may only be assigned as
configuration-injection work on an entry that names its `provisioning`
(`build-time`, `remote-config`, or `deploy-env`).

Repair routing: missing surface/module ownership routes to
app-surface-topology-spec; missing feature scope routes to feature-priority-spec;
missing data/API details route to data-model-spec; missing domain module detail
routes to the owning app-domain skill; missing validation routes to flow QA or
product-verify planning. A settings item missing `audience` or `provisioning`
routes to permissions-notifications-settings-spec; a service endpoint missing
either field routes to app-surface-topology-spec.

## Completion Conditions

Return `COMPLETED` when program development can start from structured nodes.
Return `FAILED_VALIDATION` when must-have features lack implementable handoff.
