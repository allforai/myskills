---
name: app-design-20-spec-permissions-notifications-settings-spec
description: Internal bundled meta-skill module for app-design/20-spec/permissions-notifications-settings-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Permissions Notifications Settings Spec Skill

> Internal sub-skill for app-design pipelines. Status: bundled, bootstrap-wired, invoked by app-design node-specs.

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

Repair routing: missing data purpose routes to data-model-spec; missing user
benefit routes to job-story-spec; legal/compliance ambiguity blocks rather than
guessing.

## Completion Conditions

Return `COMPLETED` when trust-sensitive behaviors are explicit and testable.
Return `FAILED_VALIDATION` when consent, denial, or opt-out paths are missing.
