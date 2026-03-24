# OpenCode Migration Inventory

This document inventories the current plugin surface and the OpenCode migration
status.

## Plugin summary

| Plugin | Root wrapper | Source of truth | Migration difficulty | Notes |
|---|---|---|---|---|
| product-design | `opencode-native/product-design-skill/` | `product-design-skill/` | High | Heavy orchestration, many interactive checkpoints |
| dev-forge | `opencode-native/dev-forge-skill/` | `dev-forge-skill/` | High | Command-led orchestration, cross-plugin routing |
| demo-forge | `opencode-native/demo-forge-skill/` | `demo-forge-skill/` | High | Media tooling and Playwright-heavy |
| code-tuner | `opencode-native/code-tuner-skill/` | `code-tuner-skill/` | Low | Read-heavy, least runtime-coupled |
| ui-forge | `opencode-native/ui-forge-skill/` | `ui-forge-skill/` | Medium | Focused workflow, still command-routed |
| code-replicate | `opencode-native/code-replicate-skill/` | `code-replicate-skill/` | Medium | Structured but interactive |

## Host-specific constructs to translate

| Construct | Meaning in source plugins | OpenCode translation |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | Plugin root path variable | Repository-relative path from wrapper |
| `AskUserQuestion` | Structured user decision point | Ask directly only if blocking |
| `allowed-tools` | Claude command capability contract | Informational only |
| `$ARGUMENTS` | Slash-command arguments | Parse from natural-language request |
| `/foo` | Workflow label | Named workflow, not literal shell command |
| `Task` / `Agent` | Claude orchestration primitives | Use OpenCode subagents only when needed |

## Current compatibility level

- Wrapper coverage: all plugin roots, all skill files, all command files.
- Runtime parity: partial.
- Safe to use without breaking existing Claude/OpenCode paths: yes.

## Next migration targets

1. Make `code-tuner` executable as a OpenCode-friendly analysis workflow.
2. Make `ui-forge` and `code-replicate` executable as OpenCode-friendly guided
   workflows.
3. Replace Claude-specific orchestration assumptions in `product-design`,
   `dev-forge`, and `demo-forge` with OpenCode operating rules.

