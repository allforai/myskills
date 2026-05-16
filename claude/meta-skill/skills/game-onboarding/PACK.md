---
name: game-onboarding
description: Internal bundled meta-skill module for game-onboarding; use within generated bootstrap node-specs when this exact contract is selected.
---

# Game Onboarding Skill Pack

> Internal bundled sub-skill pack for meta-skill. Status: bundled, inactive, not wired.

## Purpose

Game Onboarding owns first-session and FTUE design contracts: initial promise,
tutorial steps, feature unlock teaching, friction risks, and validation.

## Current Children

| Layer | Child skill | Responsibility |
|---|---|---|
| `10-design` | `first-session-experience-spec` | First-session goal, promise, emotion, duration, and success criteria. |
| `20-spec` | `tutorial-step-spec` | Tutorial steps, triggers, instructions, skip rules, and recovery. |
| `20-spec` | `feature-unlock-teaching-spec` | Feature unlock order, teaching context, reinforcement, and gating. |
| `40-qa` | `ftue-friction-qa` | Drop-off, cognitive load, input, UI, pacing, and blocker QA. |

## Canonical Invocation Paths

```text
${CLAUDE_PLUGIN_ROOT}/skills/game-onboarding/10-design/first-session-experience-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-onboarding/20-spec/tutorial-step-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-onboarding/20-spec/feature-unlock-teaching-spec/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/game-onboarding/40-qa/ftue-friction-qa/SKILL.md
```

## Layering Rules

Dependencies flow from concept to spec to QA. Onboarding must not invent core
mechanics; it teaches and validates mechanics declared by game-design/system
skills.
