---
name: app-design-20-spec-permissions-notifications-settings-spec
description: Define account, consent, permissions, privacy controls, notifications, settings, preference management, and trust-sensitive flows; writes spec/permissions-notifications-settings-spec.json.
---

# Permissions Notifications Settings Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled.

## Overview

Defines account, consent, permissions, privacy controls, notifications,
settings, preference management, and trust-sensitive flows.

## Input Contract

Required: job story spec, data model spec when available, and target platforms.

Optional: compliance constraints, auth provider, notification channels, payment
provider, enterprise policy, accessibility settings, and localization needs.

## Output Contract

Writes `.allforai/app-design/spec/permissions-notifications-settings-spec.json`.

Outputs must include `account_model`, `permission_requests`, `consent_flows`,
`privacy_controls`, `notification_rules`, `settings_groups`,
`preference_defaults`, `opt_out_paths`, `audit_or_policy_refs`,
`trust_risks`, `state`, and `consumer_refs`.

Every settings item lives in `settings_groups[].items[]` and is
`{setting_id, label, audience, surface, provisioning?, requirement_ref?}`.
`audience` is exactly one of `end-user`, `operator` (the deploying party), or
`developer`. `provisioning` is one of `build-time`, `remote-config`, or
`deploy-env`; it is required when `audience` is not `end-user` and is absent on
`end-user` items. `surface` is a topology `surface_id` or `"none"`; a
non-`end-user` item may only name `"none"` or a surface whose `surface_type` is
`admin_console`, `operator_console`, or `cli`. `requirement_ref` is the id of a
confirmed requirement and is required only for the Pattern J exception:
operator-natured content (service addresses, credentials) marked `end-user`
because a confirmed requirement demands self-hosting. See
`knowledge/defensive-patterns.md` Pattern J (Audience Isolation).

Allowed states: `draft`, `validated`, `needs_revision`, `blocked_by_data_model`.

## Invocation Contract

```json
{"skill":"app-design/permissions-notifications-settings-spec","mode":"spec_validate","input_paths":{"jobs":".allforai/app-design/concept/job-story-spec.json","data_model":".allforai/app-design/spec/data-model-spec.json"},"output_root":".allforai/app-design/spec"}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check every sensitive permission has timing, user benefit, denial behavior, and
settings control. Reject notification or data access rules without opt-out or
policy rationale.

Reject any settings item without `audience`, or whose `audience` is outside
`end-user` / `operator` / `developer`. Reject a non-`end-user` item that lacks
`provisioning`, or whose `provisioning` is outside `build-time` /
`remote-config` / `deploy-env`. Reject a non-`end-user` item whose `surface` is
an end-user surface — only `"none"` or an `admin_console`, `operator_console`,
or `cli` surface is allowed. Reject operator-natured content marked `end-user`
without a `requirement_ref`.

Repair routing: missing data purpose routes to data-model-spec; missing user
benefit routes to job-story-spec; legal/compliance ambiguity blocks rather than
guessing. An audience that cannot be decided from the inputs is never guessed:
record `needs_revision` and route to job-story-spec / the product concept.

## Completion Conditions

Return `COMPLETED` when trust-sensitive behaviors are explicit and testable.
Return `FAILED_VALIDATION` when consent, denial, or opt-out paths are missing,
or when any settings item lacks an audience.
