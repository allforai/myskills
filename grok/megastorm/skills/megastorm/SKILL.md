---
name: megastorm
description: Use when the user explicitly invokes Megastorm for a large multi-module delivery goal in official Grok Build.
---

# Megastorm for Grok Build

Drive the goal through the complete parity protocol. Task-list success is not
proof of goal completion.

## Hard gates

1. Run Phase -1 capability classification before planning.
2. Finish Phase 0 with the user: module boundaries, granularity, proof limits,
   capability authorizations, model/effort mapping, and frozen registry.
3. For class-elimination or “all/every/no remaining” claims, build and reconcile
   an exhaustive census. Representative search cannot prove completeness.
4. Use fresh native Grok subagents for Phase 1.1–1.5. Do not let one context
   design, implement, and approve its own work.
5. Use `$GROK_PLUGIN_ROOT/scripts/run_layers.py` for Phase 1.6. Prose must not
   drive the long execution loop.
6. Keep Cross-exam independent and explicit; never auto-run it.

Read `$GROK_PLUGIN_ROOT/execution-playbook.md` and follow every phase. Use the
prompts, schemas, deterministic gates, and model example in the plugin root.

## Safety and evidence

The runner must verify the actual Grok launcher and fully resolved configuration,
then constrain children to isolated task worktrees. Existing user changes are
never staged, stashed, committed, reset, or overwritten. Do not rationalize
ambient `--yolo`, hooks, MCPs, network, credentials, or external commands as
authorized merely because the current session has them.
Phase 0 saves `grok inspect --json` as the `--effective-config` artifact and the
explicit allowlist as `--approved-capabilities`; execution refuses to start
without the resolved-config artifact.

Executor claims are not acceptance. A fresh supervisor reruns acceptance and
returns structured evidence. Keep business failure, infrastructure failure, and
reality-gated proof separate. Never downgrade a model silently.

Phase 2 reports verified, reality-gated, escalated, and skipped counts; complete
skip chains; runbooks; completeness confidence; and census reconciliation.
Official-host conformance is a separate status and remains unverified unless a
supported real Grok CLI passes the documented probes and fixtures.

## Red flags

- “The deadline makes Phase -1 disproportionate.”
- “The same agent knows the code best, so self-review is enough.”
- “The user launched with these permissions, so inherit them.”
- “All planned tasks passed, therefore every instance is fixed.”

Any red flag means stop and return to the missing gate.
