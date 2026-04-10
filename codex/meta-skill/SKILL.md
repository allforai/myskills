---
name: meta-skill
description: >
  Codex-native adapter for the myskills meta-skill generator. Analyze a target project,
  generate project-specific node-specs plus .allforai/bootstrap/workflow.json, and emit
  a Codex run entry at .codex/commands/run.md. Bootstrap also emits a research-backed
  product inference summary for reverse-product understanding. Use bootstrap to generate
  the workflow, then invoke the generated run entry to execute it.
version: "0.4.0-codex.1"
---

# Meta-Skill v0.4.0-codex.1

> Unified workflow generator for Codex: bootstrap a project once, then execute the generated run entry.
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

## Shared Semantic Assets

The Codex adapter reuses the repository's shared meta-skill content through local links:

- `./knowledge/` -> canonical meta-skill knowledge base
- `./skills/` -> canonical meta-skill protocol source plus Codex wrapper guidance
- `./scripts/` -> bootstrap/orchestrator helpers
- `./tests/` -> prompts, expected outputs, and fixtures
- `./mcp-ai-gateway/` -> MCP-backed optional capability gateway

Platform-specific behavior is defined only by Codex-local files in this directory.

## Codex-Specific Specialization

This Codex adapter adds specialization guidance that does not require changing other platform versions.

Current Codex-only extension:

- `knowledge/high-risk-specialization.md` for generic high-risk domain hooks
- `knowledge/im-specialization.md` for realtime messaging / Telegram-class products
- `knowledge/replication-specialization.md` for fidelity-oriented replication and migration workflows
- `knowledge/product-inference.md` for research-first reverse-product inference
- `knowledge/flow-template.py` for Codex non-stop workflow execution
