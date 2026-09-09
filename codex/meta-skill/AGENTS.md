# AGENTS.md — Meta-Skill Generator (Codex)

> Codex-native adapter entry for the meta-skill generator.
> The canonical workflow graph contract is `workflow.json`.
> Former layer plugins are capabilities under this adapter, not separate install units.

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
  plan-confirmation.json
  plan-confirmation-journal.json
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
- Generated run and `flow.py` consume the current orchestrator helpers: `product_intent.py`, `evidence_freshness.py`, `repair_authorization.py`, `run_safety.py`, `validate_bootstrap.py`, `validate_unattended_readiness.py`, `check_artifacts.py`, `record_run_event.py`, `summarize_run_log.py`, and any `workflow.json.expanders`.

## Shared Asset Strategy

This Codex adapter intentionally reuses the Claude meta-skill knowledge, skills, helper
scripts, tests, and MCP gateway so capability content stays aligned. In a source checkout,
the canonical root is `../../claude/meta-skill/`; a standalone installation carries the
same semantic source under `./canonical/`. Platform-specific behavior is handled by
Codex-local wrapper files in this directory.

Installation separates discovery from payload: `skills/meta-skill/` contains one routing
entry; `skill-bundles/meta-skill/` contains this adapter and canonical assets. The router
sets the bundle root for all relative paths. Never link the full bundle back into `skills/`.

## Codex-Only Extensions

Codex may carry local specialization guidance without forcing the same change onto other platforms.

Current local extension:

- `knowledge/im-specialization.md` for research-first realtime messaging specialization
- `knowledge/replication-specialization.md` for fidelity-oriented replication and migration specialization
- `knowledge/product-inference.md` for evidence-backed reverse-product summaries
- `knowledge/flow-template.py` for Codex-only non-stop workflow execution
