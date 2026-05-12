---
name: app-design-20-spec-content-model-spec
description: Internal bundled meta-skill module for app-design/20-spec/content-model-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Content Model Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

## Overview

Defines content entities, voice, microcopy, empty/error/loading copy,
localization hooks, and editorial ownership.

## Input Contract

Required: audience positioning spec, information architecture spec, and screen
requirements when available.

Optional: brand voice, localization plan, legal copy, SEO needs, CMS schemas,
support policies, and content inventory.

## Output Contract

Writes `.allforai/app-design/spec/content-model-spec.json`.

Outputs must include `voice_principles`, `content_entities`,
`microcopy_patterns`, `screen_copy_requirements`, `empty_error_loading_copy`,
`localization_keys`, `editorial_ownership`, `legal_or_policy_refs`, `state`,
and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_audience`,
`blocked_by_screen_requirements`.

## Invocation Contract

```json
{"skill":"app-design/content-model-spec","mode":"spec_validate","input_paths":{"audience":".allforai/app-design/concept/audience-positioning-spec.json","ia":".allforai/app-design/spec/information-architecture-spec.json","screens":".allforai/app-design/spec/screen-requirements-spec.json"},"output_root":".allforai/app-design/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check required screens have copy responsibilities for titles, labels, empty
states, error states, success feedback, and destructive actions. Reject generic
copy tone that conflicts with audience or trust needs.

Repair routing: missing audience tone routes to audience-positioning-spec;
missing screen context routes to screen-requirements-spec; legal gaps route to
permissions-notifications-settings-spec.

## Completion Conditions

Return `COMPLETED` when copy and content models are traceable to screens and
users. Return `FAILED_VALIDATION` when critical app states lack user-facing copy.
