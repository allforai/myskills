# Root runtime progress — not acceptance

The grill-with-docs decisions in ADRs 0004–0007 and the complete remediation plan were approved for implementation. Work remains on the integration branch; main is unchanged.

## Implemented and locally checked

- Claude now waits for a wave safety barrier before publishing completions. A safety latch prevents subsequent node retries/gates after a halt is observed; already executing work is awaited, not claimed cancelled.
- Safety warnings on hard QA results are handled before repair routing, so the warning cannot disappear behind an ordinary QA verdict.
- Handled failures are identified by a union of node identities rather than adding overlapping category counts.
- Shared repairs only charge funded QA obligations. Delivery does not reopen an exhausted sibling's QA obligation merely because it shares the repair node.
- Ordinary report-backed QA failures block their dependency chain while independent branches can continue. Infrastructure/authority/policy failures still stop the run.
- `run_safety.py` persists an accumulated safety quarantine atomically with file/directory fsync and never changes completion state or deletes outputs. A failed publication retains its lock as an admission fence. Readiness consumption is assigned to the structural-gate worker.
- Both bootstrap asset-copy inventories include the authorization and safety helpers and preserve accounting/quarantine across re-bootstrap.

## Evidence

Three new safety tests failed before the runtime change: early sibling completion, safety warning on a hard QA result opening repair, and a sibling retrying after halt. The asymmetric-budget test reproduced charging attempt 3 under budget 2. The independent-branch test reproduced prematurely stopping unrelated work after ordinary QA failure. All now pass.

Latest root Node run: `node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'` — **109 passed**, 3772.757083 ms, including workflow mirror synchronization. Safety-helper suite: `python3 -B -m pytest claude/meta-skill/tests/unit/test_run_safety.py -q` — **6 passed**, 0.06 s.

Additional regression: a result naming a different node previously committed that identity and repeatedly dispatched the original node. The first uncapped probe exhausted its test process heap; it was rerun with an explicit wave cap, failed deterministically, and now passes with the engine rejecting a mismatched result identity. A missing quarantine persistence receipt is also explicitly tested as a blocker.

Root independently reproduced a remaining test-loader defect: after loading the Claude readiness test module, binding the shared `check_artifacts` module globally and calling readiness on its minimal fixture raises `ImportError` for `document_verification_errors`. The isolation worker received this deferred-import reproduction; initial-load-only isolation is not accepted.

These are deterministic tests, not actual Claude Workflow/Codex host acceptance. The shared scenario JSON is a scenario contract, not by itself an executed parity test. The new authorization helper is still under construction and not yet consumed by the drivers; legacy charge code remains pending replacement. Quarantine recovery and end-to-end persistence need independent verification.

## Parallel ownership

Three Opus workers were started through Orca: authorization foundation `ctx_a4b208370c55`, import isolation `ctx_9d7a52e384b3`, structural gates `ctx_51bb7288559e`. Root owns the runtime work described above and shared asset inventories. The next Codex integration task is `task_e2fa1fc55b4d`, not yet dispatched at this checkpoint.

Two first-start attempts failed before input acceptance with `terminal_handle_stale` (`ctx_59e098d3411b`, `ctx_fc74f00b6a66`). Replacement dispatches were accepted. Release checks on the failed starts returned `retained/no_owned_resource` with no process action; no raw terminal close was substituted.

Coordinator mail remained unread during workers' long verification calls. Root inspected the exact inbox read-only and sent one lightweight terminal wake-up per exact worker, instructing it only to check its structured inbox under the existing Dispatch. No task was reinjected and no ownership transfer or restart was requested.
