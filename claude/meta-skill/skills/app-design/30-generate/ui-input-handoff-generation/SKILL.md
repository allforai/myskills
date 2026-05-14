---
name: app-design-30-generate-ui-input-handoff-generation
description: Internal bundled meta-skill module for app-design/30-generate/ui-input-handoff-generation; use within generated bootstrap node-specs when this exact contract is selected.
---

# UI Input Handoff Generation Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

## Overview

Generates the structured handoff consumed by UI design: screens, flows,
states, copy, priorities, interaction behavior, accessibility, and design
constraints.

## Input Contract

Required: app surface topology, information architecture, user flows, screen
requirements, content model, interaction patterns, and feature priority.

Optional: audience positioning, brand preferences, data model, permissions
spec, monetization spec, existing design system, platform guidelines, and
Stitch UI MCP availability.

## Output Contract

Writes:

- `.allforai/app-design/handoff/ui-design-input-handoff.json`
- `.allforai/app-design/handoff/ui-design-input-handoff-report.json`

Handoff must include `surface_inventory`, `screen_inventory`, `flow_inventory`,
`state_matrix`, `copy_requirements`, `interaction_requirements`,
`accessibility_requirements`, `responsive_or_platform_rules`,
`design_system_scope`, `priority_and_release_scope`, `optional_stitch_mockups`,
`open_questions`, `blocked_items`, `state`, and `consumer_refs`.

`optional_stitch_mockups` must use this shape:

```json
{
  "status": "used | skipped_optional | failed_nonblocking",
  "tool": "stitch-ui",
  "project_id": null,
  "mockup_refs": [],
  "screen_refs": [],
  "reason": "Stitch unavailable, skipped because optional"
}
```

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_spec_gap`.

## Invocation Contract

```json
{"skill":"app-design/ui-input-handoff-generation","mode":"generate_validate","input_paths":{"topology":".allforai/app-design/spec/app-surface-topology-spec.json","ia":".allforai/app-design/spec/information-architecture-spec.json","flows":".allforai/app-design/spec/user-flow-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json","content":".allforai/app-design/spec/content-model-spec.json","interaction":".allforai/app-design/spec/interaction-pattern-spec.json"},"output_root":".allforai/app-design/handoff"}
```

Supported modes: `generate_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every UI-facing surface, screen, breakpoint/platform variant, and state
has source refs, copy/data/action requirements, and priority. Reject handoffs
that require UI designers to infer missing behavior from conversation history
or from a different surface.

## Optional Stitch UI Enhancement

When Stitch UI MCP is available, this skill may create high-fidelity app screen
mockups for UI designers and downstream frontend implementers. This is an
optional enhancement path, not a readiness blocker and not a replacement for the
structured UI handoff.

Use Stitch only for app screens, flows, responsive layouts, dashboards, forms,
lists, details, onboarding, settings, and commerce surfaces. Do not use Stitch
to generate production art assets or engine-ready runtime assets.

If Stitch succeeds, record `optional_stitch_mockups.status="used"`,
`project_id`, `mockup_refs`, and the screen ids covered.

If Stitch is unavailable, unauthenticated, rate-limited, or fails, record
`optional_stitch_mockups.status="skipped_optional"` or
`failed_nonblocking` with a reason and continue with the textual handoff. Do not
return `FAILED_VALIDATION` solely because Stitch is unavailable.

Do not return `FAILED_VALIDATION` solely because Stitch is unavailable.

Repair routing: screen gaps route to screen-requirements-spec; copy gaps route
to content-model-spec; interaction gaps route to interaction-pattern-spec.

## Completion Conditions

Return `COMPLETED` when UI design can proceed without unstated product
decisions. Return `FAILED_VALIDATION` when key screens or states lack source
requirements.
