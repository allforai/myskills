# Codex Megastorm and Cross-exam Parity Implementation Plan

1. Port v0.14 task, supervisor, planning, DAG, reality-gate, census, environment,
   and reporting contracts into the Codex skill and add parity tests.
2. Refactor `run_layers.py` around structured outcomes, independent retry budgets,
   reality-gate accounting, atomic state, durable events, timeouts, and cancellation.
3. Replace shared-main-tree execution with run-owned integration and task worktrees,
   checked refs, actual-diff validation, and safe publication/cleanup metadata.
4. Add `codex/cross-exam-skill` with Codex-native hard gate, intake protocol,
   census/deep-dive workflows, evidence schemas, deterministic renderer, and tests.
5. Update Megastorm documentation, schemas, prompts, version metadata, installation
   guidance, parity matrix, migration notes, and Cross-exam invitation.
6. Run focused unit/integration tests, full repository tests, static checks, dirty
   worktree/Git fault simulations, then perform a structured thought-test review
   against safety, interruption, stale-state, and fake-completion scenarios.
