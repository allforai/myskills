# App Design Registry Skill

> Internal sub-skill for app-design pipelines. Status: bundled, inactive, not wired.

## Overview

Creates the app design registry: product type, target surfaces, selected
design nodes, owners, artifact paths, approval records, and downstream
consumers.

## Input Contract

Required: product concept baseline or reverse-product inference, business
domain, target platforms, and user goal.

Optional: existing app screens, analytics, support tickets, competitor notes,
technical stack, compliance constraints, brand preferences, and localization
needs.

## Output Contract

Writes `.allforai/app-design/app-design-registry.json`.

Registry entries must include `app_type`, `target_platforms`, `design_nodes`,
`discipline_owners`, `artifact_index`, `approval_record_path`,
`downstream_consumers`, `state`, and `missing_inputs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_concept`.

## Invocation Contract

```json
{"skill":"app-design/app-design-registry","mode":"design_validate","input_paths":{"concept":".allforai/product-concept/concept-baseline.json"},"output_root":".allforai/app-design"}
```

Supported modes: `design_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every selected app-design node has an owner, output path, approval
record, and downstream consumer. Verify optional nodes are selected only when
their triggering conditions exist.

Repair routing: missing product intent routes to product-concept; missing
platform or stack routes to bootstrap profile; ownership conflicts route to
app-design registry repair.

## Completion Conditions

Return `COMPLETED` when selected design scope is explicit and all downstream
handoff paths are indexed. Return `FAILED_VALIDATION` when scope or owners are
ambiguous.
