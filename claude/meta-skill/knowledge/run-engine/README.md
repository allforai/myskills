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
  `evidence_freshness.py`, and every ledger prompt from the real
  `repair_authorization.py` (`tests/real-gate.js`), because the declared repair loop's
  boundary only exists once freshness and the budget ledger are real.
- `tests/ledger-double.js` — the one mock boundary for repair accounting, used by the L2
  suites so a many-wave run does not spawn a Python process per ledger call. It
  re-implements only the helper's decisions; `declared-loop.test.js` runs the helper
  itself, and that test wins if the two ever disagree.

## Run tests (L1 + L2 + sync-check)
    node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'

(Node v26+ resolves a bare directory path as a single require() target, not a
test-glob root — use the quoted glob form above.)

Nodes execute concurrently, but completion publication waits for a wave safety
barrier. A late safety halt withholds all same-wave completions; in-flight outputs
require quarantine and revalidation. Pipeline stages themselves have no barrier.

Repair budgets are not this engine's arithmetic and are not summarized out of
`workflow.json`. They live in `.allforai/bootstrap/repair-authorizations.json` and are
reached only by running `repair_authorization.py` through an agent prompt — this engine
has no filesystem, so every ledger operation is a deterministic CLI call whose verdict is
returned verbatim and then checked. Consumption is read first; only a ledger that does not
exist may be initialized, and the helper itself proves the workflow is untouched before it
records zero. A grant is charged before the work and is never permission to run; a
separate launch claim succeeds exactly once. Only an execution this engine watched end is
settled — an unknown outcome, a crash, or a safety quarantine leaves the grant unresolved,
and the next run stops for reconciliation rather than replaying or refunding it.

All suites must be green before invoking the Workflow shell in a real run.
