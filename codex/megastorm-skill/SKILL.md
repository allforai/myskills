---
name: megastorm
description: "Drive a large goal end-to-end — decompose into modules, front-load all human decisions, then autonomously design, validate (closed-loop), plan, reverse-review, orchestrate a task DAG, and concurrently execute with anti-fake-completion supervision. Heavy and token-intensive; use when the user explicitly invokes megastorm with a big multi-module goal."
---

# megastorm — large-goal autonomous pipeline (Codex)

**Invariant:** decisions front-loaded → autonomous → self-fix loop → disclose at close.
All human interaction happens in Phase 0; afterwards never stop for a new decision,
approval, escalation, or stage boundary. Unknown choices use the recommended authorized
option, are recorded, and are disclosed in Phase 2.

Read `execution-playbook.md` IN THIS SKILL DIRECTORY and follow it phase by phase.
Everything you need sits beside it:

- `prompts/` — 6 prompts for headless `codex exec` agents (design / closure-critic /
  plan / reverse-critic / executor / supervisor)
- `schemas.md` — JSON contracts (registry, design-manifest, plan-task, verdict)
- `scripts/check_closure.py`, `scripts/validate_plan_tasks.py`,
  `scripts/build_task_dag.py` — deterministic gates
- `scripts/run_layers.py` — the §1.6 execute+supervise runner (the long loop is NEVER
  driven by prose; this script owns ready-set scheduling, mutex groups, worktrees, the
  retry ledger, skip-on-escalation, autonomous decision records, and fresh-context supervision)
- `scripts/decision_ledger.py` — run-scoped authority envelope and autonomous decisions
- `models.example.json` — tier mappings used only when Phase 0 proves every effective
  model source is unlocked; otherwise freeze `inherited` and add no model override

Parity target: Claude Megastorm v0.16.0. This Codex-native port includes environment
capability classification, census-backed completeness, reality-gate accounting, separate
infrastructure/business failures, safe run-owned Git integration, and unattended decision
disclosure. Independent workflows are never invoked or suggested automatically after Phase 2.

Do not start any design or implementation before Phase 0 is complete (module
breakdown approved, granularity review done, registry frozen, models resolved).

Codex host inheritance is a security boundary. Preserve the current direct command and its
arguments. A custom alias/wrapper is replayed only with an explicit versioned wrapper contract;
unknown wrapper/profile/config model ownership forces `inherited`. Before workers run, freeze a
human-confirmed model-policy artifact. Workers are untrusted: they may emit `needs_replan`, but
must never edit DAG/tasks/models/prompts/runner/state/policy. Admit only strict schema-bound output
and operation-level artifact contracts, then publish through checked candidate refs with CAS.
All owned automation uses `python3` or `sys.executable` for macOS compatibility.
