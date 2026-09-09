# Environment baseline

Starting ref: 81acdddca29ab6dde95a1ab72decc2067f3a0f9a.

- Shared pytest unit suite: 100 passed, exit0, 0.28s.
- Codex flow/install pytest: 31 passed, exit0, 1.26s.
- unittest discovery at tests root: no tests, exit5; rejected as acceptance.
- Orca runtime 1.4.197 ready; Run run_a2a61121adfb.
- Fresh Codex orientation dispatch ctx_1b9dfaf196d3 independently ran real helper tests.
- Fresh Claude dispatch ctx_e53bbe574a03 ran pwd and git rev-parse HEAD, matching the integration worktree and frozen ref; worker_done succeeded; released with transcript captured.
- CLI versions: Claude Code 2.1.263; codex-cli 0.153.4.
- These prove tools can launch, not meta-skill feature acceptance.
- Claude run-engine node --test suite: 55 passed, 0 failed/0 skipped; includes L1/L2 and inlined-engine sync checks. Fake-agent cases remain deterministic tests, not actual host acceptance. Combined baseline 186 tests.

Original checkout subsequently acquired unrelated cross-exam/superstorm/visual-acceptance and marketplace changes from another actor. They are not this run's work and will not be staged, overwritten or cleaned. Integration remains at the frozen starting ref with only run-owned docs. Re-evaluate target-branch state before any final integration; do not absorb unrelated changes.
