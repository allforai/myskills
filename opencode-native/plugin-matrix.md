# Plugin Compatibility Matrix

| Plugin | Skills wrapped | Commands wrapped | Depends on `.allforai/` | Extra runtime coupling | OpenCode readiness |
|---|---:|---:|---|---|---|
| product-design | 9 | 3 | Yes | Web search, MCP, interactive checkpoints | Playbook ready |
| dev-forge | 4 | 4 | Yes | Playwright, orchestration, delegated loops | Playbook ready |
| demo-forge | 4 | 1 | Yes | Media generation, uploads, Playwright | Playbook ready |
| code-tuner | 1 phase root + references | 1 | Yes | Minimal | Playbook ready |
| ui-forge | 1 | 1 | Optional / project-local context | Focused but interactive | Playbook ready |
| code-replicate | 7 | 3 | Yes | Interactive extraction planning | Playbook ready |

Readiness meanings:

- `Wrapper ready`: OpenCode entry points exist and point to source workflows.
- `Playbook ready`: wrapper coverage plus a OpenCode-friendly execution playbook
  exists for practical use.

