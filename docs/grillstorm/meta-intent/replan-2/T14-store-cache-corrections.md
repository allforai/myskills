# T14 corrections — external-change store, cache and gate execution (#14)

Base `11f9a44c` (source identical to `00b5caad`). Fixes the standards re-review's hard
breach and both spec re-review majors. Evidence is copied-CLI in temporary projects on
both host adapters (`HOSTS = ["claude", "codex"]`); **real Claude/Codex host dialogue
proof is not claimed here**: #14's T18 host proof stands at 0/16, and the whole #8
T15–T18 matrix at 0/60. Source and report edits were made with this harness's `Edit` and
`Write` tools; no `apply_patch` binary is available on this machine.

## The three defects

1. **An unwritable store erased detected conflicts** (standards re-review).
   `external_conflicts` wrapped `resolve_external_changes`, which *writes* the store, and
   swallowed `OSError` into `{}`. A non-writable `.allforai/bootstrap/` deleted the
   conflict from `check`, `check_artifacts.py`, reconciliation and readiness.
2. **A memoized classification was never re-verified** (spec Finding 1). The verdict was
   keyed by `change_identity` alone, which excludes the acceptance argv and everything
   the acceptance reads — including paths `inventory` skips (`node_modules`, `.venv`). A
   live product conflict was reported as a verified implementation fact, with no way to
   force re-verification.
3. **A passive gate executed the project's acceptance and destroyed an out-of-flow edit**
   (spec Finding 2). Because `external_conflicts` classified, `validate_unattended_readiness`,
   `evaluate`/`check` and `check_artifacts.py` ran the recorded argv against live source. A
   self-healing acceptance (regenerate, then verify) reverted the user's edit and returned
   `ready`.

## The separation

Three responsibilities were being carried by one function. They are now distinct:

- **Detection** (`detect_external_changes`) — a pure comparison, unchanged.
- **Standing verdicts** (`standing_changes`) — reads the recorded store and keeps a verdict
  only while its `classification_basis` (the recorded acceptance argv plus the project
  `source_tree`) still holds. Executes nothing. A change with no standing verdict carries
  `classification: None`.
- **Verification** (`resolve_external_changes`, reached only by `{"operation":"external-changes"}`)
  — the one path that executes the delivery's recorded acceptance, because running project
  argv against live source is an act, not an observation. It always verifies afresh rather
  than repeating a memo.
- **Cache persistence** (`cache_classifications`) — best-effort: a store the project cannot
  write costs a rerun, never a deleted conflict. **Decision persistence is unchanged and
  still fail-closed**: only `product_intent._external_change` writes a resolution, and an
  `OSError` there surfaces as `{"status":"blocked"}` with rc 1, so a decision that cannot be
  recorded never passes as consent.

Gates consume both groups through `routed_external_changes`: standing conflicts route to
`interactive-bootstrap` (`product-decision`) exactly as before, and unknown drift becomes
its own state — readiness blocker `unverified_external_change`, `external: unverified` on
`check` and `check_artifacts.py` nodes, `external_change: unverified` on reconciliation
items. Repair routing for unknown drift stays with the owning node, so an implementation
fact still recovers through documents and republication with **no product interview**.
`external_conflicts` no longer swallows an undeterminable comparison; readiness reports it
as `undetermined_external_change` instead of crashing or reading it as clear.

`source_tree` was split out of `inventory` so the basis is workflow-independent: replanning
or refreezing must not look like the source moved.

## Residual limits (stated, not fixed)

- A basis cannot observe an installed dependency, a service or the environment. A memo can
  therefore outlive the truth at the *passive* gates until someone re-runs the verification.
  Two things bound the damage: publication re-executes the acceptance, so a false
  `fact-update` cannot close a delivery, and re-running `external-changes` always verifies
  afresh. Covered by `test_a_verdict_is_re_established_by_verifying_again_not_repeated_from_the_record`,
  which asserts the stale-memo window as well as the recovery.
- The explicit verification still executes project argv, so a self-healing acceptance can
  move the source there. That run records no verdict and reports the move; the source is
  left in the post-command state, **not** restored to its pre-run bytes, because rolling
  it back would hide the move and discard a change nobody decided.
- No `--reverify` flag was added: re-running the operation *is* the fresh verification.

## Red → green

RED was captured by extracting `00b5caad` with `git archive` into a temporary tree (`GIT_*`
stripped, checkout untouched) and running the final test files there.

| Command | 00b5caad | candidate |
|---|---|---|
| `pytest claude/meta-skill/tests/unit/{test_external_change_recovery,test_freshness_downgrade,test_corrupt_freshness_reads}.py -q` | **18 failed, 90 passed** | 108 passed |
| `pytest claude/meta-skill/tests -q` | — | **639 passed** (3:53) |
| `pytest codex/meta-skill/test_flow.py codex/meta-skill/test_install.py -q` | — | 35 passed |
| `.githooks/pre-commit` (py_compile, 639 unit tests, 8 validators, node_id invariant) | — | ok |
| `node --test claude/meta-skill/knowledge/run-engine/tests/*.test.js` (run by the coordinator in the integration checkout, not by this worker) | — | 55 passed, 0 failed, exit 0 (44.97 ms) |

RED tests, all parametrized over both adapters:

- `test_an_unwritable_store_keeps_the_conflict_it_could_not_record` — defect 1.
- `test_a_verdict_is_re_established_by_verifying_again_not_repeated_from_the_record` — defect 2,
  regressing an installed dependency under `node_modules/` that no fingerprint can observe.
- `test_a_classification_is_not_reused_once_the_source_it_was_established_against_moves` — the
  observable half of defect 2, found while auditing: source the acceptance reads but this
  delivery does not declare.
- `test_a_gate_never_runs_project_acceptance_over_an_out_of_flow_edit` — defect 3, driving
  `check_artifacts.py`, readiness, `check` and reconciliation directly and asserting
  `orders.py` still holds exactly the user's bytes.
- `test_drift_reaches_the_gates_as_unverified_and_verification_routes_it_to_its_owner` —
  replaces the previous "gates classify" test with the observe-then-verify contract.
- `test_unreadable_freshness_state_cannot_report_or_decide_external_changes` — strengthened
  with the `undetermined_external_change` blocker.

Two existing tests were adjusted to the new contract, neither weakened:
`test_corrupt_freshness_reads.py` now tolerates a project-wide blocker beside the node-scoped
ones (and additionally asserts *every* blocker names the register), and
`test_freshness_downgrade.py` expects `unverified_external_change` beside `stale_evidence` for
an out-of-flow edit.

## Typecheck

`uvx mypy --ignore-missing-imports` on `evidence_freshness.py`, `validate_unattended_readiness.py`,
`product_intent.py`:

- mypy **2.3.1** (current unpinned): `Success: no issues found in 3 source files`, on both the
  candidate and the `00b5caad` baseline.
- mypy **1.13.0**: one error, `product_intent.py:1147 Dict entry 2 has incompatible type
  "str": "bool"` — reproduced identically on the baseline, so it predates this work and was
  not silenced.

No Node change was made. `shared/mcp-ai-gateway` declares no `test` script; the existing
Node regression suite lives at `claude/meta-skill/knowledge/run-engine/tests` and its run
above is coordinator-supplied evidence, attributed as such.

## Files

`claude/meta-skill/scripts/orchestrator/evidence_freshness.py`,
`validate_unattended_readiness.py`, `reconcile_bootstrap_workflow.py` (the `codex/` scripts
tree is a symlink to `claude/`, so both adapters move together);
`claude/meta-skill/knowledge/input-freshness.md`, both `orchestrator-template.md`,
`claude/meta-skill/skills/bootstrap/SKILL.md`, `codex/meta-skill/skills/bootstrap.md`;
tests as listed above. `docs/grillstorm/meta-intent/replan-2/execution.json` is
coordinator-owned and was neither staged nor modified.
