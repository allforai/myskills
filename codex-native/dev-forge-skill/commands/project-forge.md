# Project Forge For Codex Native

This document defines the main Codex-native entry contract for the dev-forge
pipeline.

## Modes

| Mode | Meaning |
|---|---|
| `full` or unspecified | fresh run across all forge phases |
| `existing` or `full existing` | gap-fill an existing codebase |
| `resume` | continue from the first incomplete forge phase |

## Execution authority

- use `../execution-playbook.md` for phase routing, prerequisites, and report
  rules
- use `../skills/` and the native validation commands for deeper sub-workflows

## Core outputs

- `.allforai/project-forge/`
- `.allforai/product-verify/`
- `.allforai/deadhunt/`
- `.allforai/testforge/`
- `.allforai/demo-forge/` when handoff is prepared
