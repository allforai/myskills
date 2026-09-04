---
name: meta-skill
description: >
  Explicitly invoked Codex adapter for the myskills product pipeline. Use only when the
  user invokes $meta-skill or asks to bootstrap a project that needs product, experience,
  art, or game design before implementation and verification. Generate project-specific
  node-specs, .allforai/bootstrap/workflow.json, and .codex/commands/run.md. For one large
  engineering goal without a product-design phase, use megastorm or grillstorm instead.
metadata:
  version: "0.13.0-codex.1"
---

# Meta-Skill v0.13.0-codex.1

> Unified workflow generator for Codex: bootstrap a project once, then execute the generated run entry.
> User-invoked only. Do not start bootstrap implicitly; the user must invoke `$meta-skill` or explicitly ask to bootstrap the project.
> Layer plugins (product-design, dev-forge, demo-forge, code-tuner, code-replicate, ui-forge) are capabilities inside this adapter, not separate Codex skills.
> Specialization is research-first: use real project evidence and LLM synthesis whenever possible, with hard responsibility packs only for high-risk domains.

## Commands

| Command | Purpose |
|---------|---------|
| `bootstrap [path]` | Analyze target project, generate node-specs + `workflow.json` + `.codex/commands/run.md` |
| `setup [check\|reset\|update]` | Detect and configure optional external capabilities |
| `journal [topic]` | Record product decisions from the current conversation into a decision journal |
| `journal-merge` | Merge journal decisions into the current product concept and emit drift metadata |

## Architecture

```text
Layer 1: Generator (bootstrap)
  Lightweight analysis -> project-specific node-specs + workflow.json

Layer 2: Orchestrator (generated run entry)
  Codex-native run command at .codex/commands/run.md
  Reads .allforai/bootstrap/workflow.json and dispatches nodes
```

## Generated Run Contract

- Bootstrap writes the orchestrator entry to `.codex/commands/run.md` inside the target project.
- The generated run entry is a Codex markdown command, not a Claude command.
- Shared workflow contracts remain under `.allforai/bootstrap/`.
- Codex-only runtime helpers should be written under `.allforai/codex/` to avoid mixing platform-specific files with shared bootstrap artifacts.
- Bootstrap should also write `.allforai/bootstrap/product-summary.json` when the project can be reverse-inferred from repository evidence.
- The generated `.allforai/codex/flow.py` is a Codex-only supervisor: it uses `transition_log` as runtime state, stops after repeated node failures, and records `diagnosis_history` instead of looping forever.
- Generated run and `flow.py` share the current orchestrator contract: `workflow.json`, copied `scripts/orchestrator` helpers, unattended-readiness preflight, and `check_artifacts.py` as the completion gate. They do not invoke the Claude Workflow JS engine.

## Canonical Semantic Assets

The Codex adapter reuses the Claude meta-skill as its canonical semantic source:

- source checkout: `../../claude/meta-skill/`
- installed snapshot: `./canonical/`
- `./skills/bootstrap.md` -> Codex substitutions layered over the canonical bootstrap protocol
- `./knowledge/` -> Codex-local extensions plus compatibility links
- `./scripts/` -> bootstrap/orchestrator helpers
- `./tests/` -> prompts, expected outputs, and fixtures
- `./mcp-ai-gateway/` -> MCP-backed optional capability gateway

The installer materializes canonical `skills/` and `knowledge/` into the snapshot so the
skill remains usable without the source repository. Platform-specific behavior remains in
Codex-local files.

## Codex-Specific Specialization

This Codex adapter adds specialization guidance that does not require changing other platform versions.

Current Codex-only extension:

- `knowledge/high-risk-specialization.md` for generic high-risk domain hooks
- `knowledge/im-specialization.md` for realtime messaging / Telegram-class products
- `knowledge/replication-specialization.md` for fidelity-oriented replication and migration workflows
- `knowledge/product-inference.md` for research-first reverse-product inference
- `knowledge/flow-template.py` for Codex non-stop workflow execution
