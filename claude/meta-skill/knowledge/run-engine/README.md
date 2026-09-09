# run-engine

Deterministic Workflow-based executor for meta-skill `/run` (Phase B).
Authority: `docs/adr/0001-bootstrap-free-planning.md`. Retired design notes live
under `docs/superpowers/retired/`.

## Files
- `engine-core.js` — canonical logic (pure fns + `runEngine`). Edit logic HERE.
- `run-engine.workflow.js` — Workflow shell; inlines `engine-core.js` verbatim
  between `// <<<ENGINE-CORE-START>>>` / `// <<<ENGINE-CORE-END>>>`. After editing
  `engine-core.js`, copy the marker region into the shell, then run sync-check.
- `tests/` — L1 unit, L2 fake-agent integration, sync-check; `tests/L3-runbook.md` for real-agent E2E.
  `tests/declared-loop.test.js` is the exception to "fake agent": it builds a fully
  declared project and answers the gate from the real `check_artifacts.py` and
  `evidence_freshness.py` (`tests/real-gate.js`), because the declared repair loop's
  boundary only exists once freshness is real.

## Run tests (L1 + L2 + sync-check)
    node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'

(Node v26+ resolves a bare directory path as a single require() target, not a
test-glob root — use the quoted glob form above. Currently 95/95 green.)

All suites must be green before invoking the Workflow shell in a real run.
