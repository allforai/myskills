---
name: game-runtime
description: Internal bundled meta-skill module for game-runtime; use within generated bootstrap node-specs when this exact contract is selected.
---

# Game Runtime Skill Pack

> Internal bundled sub-skill pack for meta-skill.
> Status: bundled, inactive, not wired.

## Purpose

Game Runtime owns implementation-facing game program contracts that are not
game product design, game art, or UI art. It converts approved game-planning
requirements into runtime, server, simulation, and security specs that
programmers can implement and automatically validate.

Use this pack when a node requires technical ownership for:

- networking and authority;
- matchmaking services;
- procedural generators;
- AI simulation and behavior implementation;
- anti-cheat/security architecture.
- importing engine-ready art assets into runtime code.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `20-spec` | `network-architecture-spec` | Runtime networking topology, authority, replication, latency, reconnect, persistence, and executable validation. |
| `20-spec` | `matchmaking-service-spec` | Queue service rules, rating inputs, party/region/platform logic, backfill, observability, and service validation. |
| `20-spec` | `procedural-generator-spec` | Generator architecture, seed replay, constraints, rejection rules, sample validation, and debug output. |
| `20-spec` | `ai-faction-runtime-spec` | AI behavior/runtime implementation contract, simulation budget, readable state, and test scenarios. |
| `20-spec` | `anti-cheat-architecture-spec` | Threat controls, trusted boundaries, detection signals, privacy constraints, penalties, and security validation. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-runtime/20-spec/network-architecture-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-runtime/20-spec/matchmaking-service-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-runtime/20-spec/procedural-generator-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-runtime/20-spec/ai-faction-runtime-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-runtime/20-spec/anti-cheat-architecture-spec/SKILL.md
```

## Boundary

Game design defines product intent and player-facing rules. Game runtime defines
how those rules become executable systems. If a runtime validation cannot run,
return a blocking validation status; do not substitute prose or weaker evidence.

Runtime code consumes art through:

```text
.allforai/game-runtime/art/engine-ready-art-manifest.json
```

The manifest is produced by `game-art/40-qa/engine-ready-art-output-contract`.
Runtime nodes must reference `runtime_id`, `asset_id`, manifests, atlas frames,
animation clips, UI refs, VFX configs, and fallback status from that file.
Hardcoded raw image paths are a contract violation. Client-side visual binding,
scene assembly, input/camera wiring, HUD overlay, and playable smoke tests live
in `game-frontend`.
