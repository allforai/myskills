---
name: code-tuner-codex
description: >
  Use this skill when the user asks to "analyze server code quality",
  "check architecture compliance", "find duplicate code", "detect code duplication",
  "review backend architecture", "optimize server code", "code tuning",
  "refactor my backend", "audit code architecture", "code quality review",
  "assess technical debt", "check if code follows three-tier architecture",
  "check DDD compliance", "find abstraction opportunities", "analyze validation logic",
  or mentions server-side code optimization, backend refactoring,
  architectural violations, layered architecture review, or technical debt assessment.
  Supports three-tier, two-tier, and DDD architectures across any language.
---

# Code-Tuner (Codex Native)

## Role

Server-side code quality analyzer: architecture compliance, duplication detection,
abstraction analysis, and validation standards. Produces a scored report (0-100)
with actionable refactoring tasks.

## Available Workflows

| Mode | Phases | Description |
|------|--------|-------------|
| full (default) | 0 > 1 > 2 > 3 > 4 | Complete analysis |
| compliance | 0 > 1 > 4 | Architecture compliance only |
| duplication | 0 > 2 > 4 | Duplication detection only |
| abstraction | 0 > 3 > 4 | Abstraction analysis only |
| report | 4 | Regenerate report from existing phase data |

## Lifecycle Modes

- **pre-launch** (default): aggressive optimization suggestions
- **maintenance**: conservative suggestions, risk-assessed

Default to pre-launch unless the user clearly indicates a live/production system.

## Quick Start

Read `./execution-playbook.md` for phase-by-phase orchestration instructions.
Read `./SKILL.md` for domain knowledge, scoring criteria, and key principles.

## Key Principles

- **Backend only** -- refuse frontend-only, documentation, or config-only repositories
- **Read-only** -- output reports and task lists; never auto-refactor code
- **Two modes throughout** -- every finding includes both pre-launch and maintenance suggestions
- **Names do not matter, responsibilities do** -- identify layers by dependency direction and code role, not directory names
- **Detect both under-abstraction and over-abstraction** -- missing abstractions and unnecessary abstractions are both problems
