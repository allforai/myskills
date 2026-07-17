---
name: megastorm
description: "Drive a large goal end-to-end — decompose into modules, front-load all human decisions, then autonomously design, validate (closed-loop), plan, reverse-review, orchestrate a task DAG, and concurrently execute with anti-fake-completion supervision. Heavy and token-intensive; use when the user explicitly invokes megastorm with a big multi-module goal."
---

# megastorm — large-goal autonomous pipeline (Codex)

**Invariant:** decisions front-loaded → autonomous → self-fix loop, escalate-to-stop.
All human interaction happens in Phase 0; afterwards run without stopping except on
escalation. No automatic model downgrade, no automatic re-decomposition.

Read `execution-playbook.md` IN THIS SKILL DIRECTORY and follow it phase by phase.
Everything you need sits beside it:

- `prompts/` — 6 prompts for headless `codex exec` agents (design / closure-critic /
  plan / reverse-critic / executor / supervisor)
- `schemas.md` — JSON contracts (registry, design-manifest, plan-task, verdict)
- `scripts/check_closure.py`, `scripts/validate_plan_tasks.py`,
  `scripts/build_task_dag.py` — deterministic gates
- `scripts/run_layers.py` — the §1.6 execute+supervise runner (the long loop is NEVER
  driven by prose; this script owns ready-set scheduling, mutex groups, worktrees, the
  retry ledger, skip-on-escalation, and fresh-context supervision)
- `models.example.json` — copy to the project as `models.json`, fill REAL model names
  with the human in Phase 0 (placeholders refuse to run)

Parity target: Claude Megastorm v0.14.0. This Codex-native port includes environment
capability classification, census-backed completeness, reality-gate accounting, separate
infrastructure/business failures, safe run-owned Git integration, and an invitation to the
independent `cross-exam` Codex skill after Phase 2. Cross-exam is never auto-entered.

Do not start any design or implementation before Phase 0 is complete (module
breakdown approved, granularity review done, registry frozen, models resolved).
