# Product Design For Codex Native

This document defines the main Codex-native entry contract for the product
design pipeline.

## Modes

| Mode | Meaning |
|---|---|
| `full` or unspecified | run the full product-design pipeline |
| `full skip: concept` | skip concept discovery and start from product map |
| `resume` | continue from the first incomplete phase |

## Execution authority

- use `../execution-playbook.md` for phase order, prerequisites, and outputs
- use the phase-specific skill docs under `../skills/` when deeper behavior is
  needed

## Core outputs

- `.allforai/product-concept/`
- `.allforai/product-map/`
- `.allforai/experience-map/`
- `.allforai/feature-gap/`
- `.allforai/design-audit/`
