# AGENTS.md — Meta-Skill Generator (Codex)

> Codex-native adapter entry for the meta-skill generator.
> The canonical workflow graph contract is `workflow.json`.

## Commands

| Command | Purpose |
|---------|---------|
| `bootstrap` | Analyze a target project, generate project-specific node-specs, `.allforai/bootstrap/workflow.json`, and a Codex run entry |
| `setup` | Detect and configure optional external capabilities and MCP-backed services |
| `journal` | Record product decisions into `.allforai/product-concept/decision-journal.json` |
| `journal-merge` | Merge journal decisions into `product-concept.json` and emit `concept-drift.json` |

## Generated Outputs

```text
.allforai/bootstrap/
  bootstrap-profile.json
  product-summary.json
  workflow.json
  node-specs/*.md
  scripts/
  protocols/

.allforai/codex/
  flow.py

.codex/commands/
  run.md
```

## Contract Notes

- `workflow.json` is the forward contract.
- `state-machine.json` may only be read for backward compatibility during migration.
- The generated Codex orchestrator entry is `.codex/commands/run.md`, not `.claude/commands/run.md`.
- Shared contracts belong under `.allforai/bootstrap/`; Codex-only runtime helpers belong under `.allforai/codex/`.

## Shared Asset Strategy

This Codex adapter intentionally reuses the Claude meta-skill knowledge, helper scripts,
tests, and MCP gateway from the same repository so capability content stays aligned.
Platform-specific behavior is handled by Codex-local wrapper files in this directory.

## Codex-Only Extensions

Codex may carry local specialization guidance without forcing the same change onto other platforms.

Current local extension:

- `knowledge/im-specialization.md` for research-first realtime messaging specialization
- `knowledge/product-inference.md` for evidence-backed reverse-product summaries
- `knowledge/flow-template.py` for Codex-only non-stop workflow execution
