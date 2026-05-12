---
name: game-runtime-20-spec-anti-cheat-architecture-spec
description: Internal bundled meta-skill module for game-runtime/20-spec/anti-cheat-architecture-spec; use within generated bootstrap node-specs when this exact contract is selected.
---

# Anti-Cheat Architecture Spec Skill

> Internal sub-skill for game-runtime pipelines. Status: bundled, inactive, not wired.

## Overview

Defines security-facing anti-cheat architecture: trusted boundaries, threat
controls, server validation, client hardening expectations, telemetry signals,
privacy constraints, false-positive handling, penalty/appeal integration, and
automated validation. This is a program/security contract, not a product design
promise.

## Input Contract

Required: game mode spec, network architecture spec or multiplayer brief,
economy/progression value surfaces when present, and platform policy.

Optional: matchmaking service spec, account/social model, monetization
constraints, regional privacy/compliance notes, engine security capability
report, and incident response requirements.

## Output Contract

Writes:

- `.allforai/game-runtime/security/anti-cheat-architecture-spec.json`
- `.allforai/game-runtime/security/anti-cheat-architecture-report.json`

Threat controls must include `threat_id`, `protected_surface`,
`trusted_boundary`, `server_validation`, `client_controls`,
`detection_signal_refs`, `false_positive_risk`, `privacy_constraints`,
`penalty_integration`, `appeal_integration`, `observability`,
`verification_path`, `state`, and `consumer_refs`.

Allowed states: `draft`, `validated`, `needs_revision`,
`blocked_by_network_architecture`, `blocked_by_policy`,
`blocked_by_security_tooling`, `blocked_by_validation_unavailable`.

## Invocation Contract

```json
{
  "skill": "game-runtime/anti-cheat-architecture-spec",
  "mode": "spec_validate",
  "input_paths": {
    "game_modes": ".allforai/game-design/systems/game-mode-spec.json",
    "network_architecture": ".allforai/game-runtime/network/network-architecture-spec.json",
    "economy": ".allforai/game-design/systems/product-economy-spec.json"
  },
  "output_root": ".allforai/game-runtime/security"
}
```

Supported modes: `spec_validate`, `validate_existing`, `repair_existing`.

## Automatic Validation

Check that every competitive, networked, tradable, monetized, or ranked surface
has a trusted boundary, control, signal, policy, and verification path. If
security tooling or runtime execution is unavailable, return a blocking status.

Repair routing: missing threat promise routes to game design; missing authority
routes to `network-architecture-spec`; service abuse routes to
`matchmaking-service-spec`; unverifiable controls route to implementation
feasibility QA.

## Completion Conditions

Return `COMPLETED` when anti-cheat controls are implementable and verifiable.
Return `FAILED_VALIDATION` when a protected surface lacks controls, signals,
policy integration, or validation.
