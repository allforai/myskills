# T15 independent review — shared structural gate parity

Read-only review of `git diff 47ea2855 --`. Ownership: the shared structural gate, its two consumers,
their tests, the CLAUDE/AGENTS inventories, the execution ledger. No source modified, no other report read.

## Blocking defect

**B1 — the new run-boundary gate raises instead of blocking on a malformed node list, and leaves a
stale `ready` report on disk.** `structural_gate_blockers` runs at
`validate_unattended_readiness.py:331`, before any shape check, and
`effect_stage_ownership_findings` sorts a map keyed by raw `node_id`
(`validate_bootstrap.py:1825`). A graph mixing a string and a non-string `node_id` makes `sorted()`
raise `TypeError` — contradicting the guarantee the same commit added at `validate_bootstrap.py:1819`
("a malformed node list yields no structural finding here … rather than raising out of the caller").

Repro: bootstrap dir with `{"nodes":[{"node_id":1,…},{"node_id":"b",…}]}` plus a minimal readiness
spec and a pre-existing `unattended-run-readiness.json` of `{"status":"ready"}`; run
`validate_unattended_readiness.py . --write-report` → `TypeError: '<' not supported between instances
of 'str' and 'int'`, exit 1, no JSON, stale `ready` file untouched. Regression: the 47ea2855 build on
the same fixture returns `status=not_ready` with `missing_bootstrap_validator`/`missing_node_spec`.

Both drivers still fail closed on the exit code (`run_preflight` → 6; the Claude prompt requires "the
command succeeds"), so no proven completion hole — but Claude's readiness verdict is a model handed a
traceback *plus* a surviving `ready` report, and the typed blocker list is lost. Fix: drop non-string
ids as `repair_loop_declaration_findings` already does, or gate after the shape check.

## No finding elsewhere

- Bootstrap-CLI output byte-identical to 47ea2855 on closure-not-blocked and unowned-effect fixtures;
  `_rendered` reproduces the old `code: message` prefix exactly.
- Canonical loop → no finding. Empty `closure_node_ids`, transitively-only-blocked closure,
  non-existent / self / parallel owner each yield one correctly anchored finding; `nodes` as a dict
  yields none, as documented. The stricter direct `closure hard_blocked_by QA` edge (which forced the
  `test_validate_unattended_readiness.py` fixture change) has spec basis: repair is dispatched *on* QA
  failure, so transitive blocking would not hold closure.
- Parity: Codex reaches the same implementation via `flow-template.py:1099` and `:1160`; no second copy.
  `plan_confirmation_blockers` still runs ahead of it. Inventories accurate; `validate_bootstrap.py` is
  in both copy lists and genuinely consumed by `flow.py`.
- Ledger fix holds and is test-bound. Non-blocking: `correction_verification_checkpoint.base_commit`
  still pins 2cc347af while `active` pins 47ea2855.

## Proof limits

Scoped runs only: `test_planning_audit_contracts.py` 21, `codex/meta-skill/test_flow.py` 108,
`test_campaign_acceptance.py` 5 — all passed. No combined regression, no actual host session; the
fail-closed behaviour under B1 is read from code, not observed on a host.
