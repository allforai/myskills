---
name: app-design-10-concept-audience-positioning-spec
description: Internal bundled meta-skill module for app-design/10-concept/audience-positioning-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Audience Positioning Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

## Overview

Defines who the app is for, why they choose it, what context they use it in,
and which human preferences must shape design decisions.

## Input Contract

Required: product concept baseline, target users, business goal, and platform
constraints.

Optional: market research, competitor list, user interviews, accessibility
constraints, brand tone, monetization intent, and regional constraints.

## Output Contract

Writes `.allforai/app-design/concept/audience-positioning-spec.json`.

Audience entries must include `audience_id`, `segment`, `job_context`,
`motivation`, `current_alternative`, `decision_criteria`,
`trust_or_risk_concerns`, `accessibility_needs`, `preference_signals`,
`business_fit`, `non_target_users`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_concept`.

## Invocation Contract

```json
{"skill":"app-design/audience-positioning-spec","mode":"spec_validate","input_paths":{"concept":".allforai/product-concept/concept-baseline.json"},"output_root":".allforai/app-design/concept"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check each audience has a clear job context, motivation, decision criteria, and
non-target boundary. Reject generic personas without actionable design impact.

Repair routing: vague audience routes to product-concept; missing preferences
route to concept Q&A; compliance or accessibility gaps route to relevant
specialist design nodes.

## Completion Conditions

Return `COMPLETED` when audience positioning can drive IA, flows, UI, content,
and implementation priorities. Return `FAILED_VALIDATION` when the audience is
too generic to constrain design.
