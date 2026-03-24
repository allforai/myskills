# Demo Forge For Codex Native

This document defines the Codex-native orchestration contract for the demo
pipeline.

## Modes

| Mode | Meaning |
|---|---|
| `full` or unspecified | design -> media -> execute -> verify with iterative repair |
| `design` | plan demo data only |
| `media` | acquire, generate, process, and upload media only |
| `execute` | generate and inject demo data only |
| `verify` | verify demo behavior and asset integrity only |
| `clean` | remove demo data only when explicitly requested |
| `status` | summarize artifact and readiness state only |

## Native execution rules

- use the playbook as the phase-order authority
- require explicit runtime inputs such as app URL when execute or verify modes
  need them
- clearly separate unavailable capability from failed execution
- do not claim demo readiness when verification did not run

## Phase routing

- `design` -> `./skills/demo-design.md`
- `media` -> `./skills/media-forge.md`
- `execute` -> `./skills/demo-execute.md`
- `verify` -> `./skills/demo-verify.md`

## Core outputs

- `.allforai/demo-forge/demo-plan.json`
- `.allforai/demo-forge/assets-manifest.json`
- `.allforai/demo-forge/upload-mapping.json`
- `.allforai/demo-forge/forge-data.json`
- `.allforai/demo-forge/verify-report.json`
- `.allforai/demo-forge/round-history.json`
