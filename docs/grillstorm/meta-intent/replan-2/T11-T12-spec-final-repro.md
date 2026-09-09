# Repro for C1' (T11-T12-spec-final.md)

Both host copies (Codex `scripts` is a symlink). Uses the `project(confirmed=True)` fixture from
`tests/unit/test_bootstrap_scope.py`: `task_route: local-change`, `task_scope.requirement_refs`
→ `local-requirements.json#export`, no `intent_session_path` (the shape SKILL.md §1.6 documents).

1. Write `.allforai/product-concept/decision-journal.json`:
   `{"schema_version":"1.0","batches":[{"batch_id":"prior","source":"user_session","user_reference":"old turn",
   "decisions":[{"question":"Export which orders?","chosen":"Something else entirely","rationale":"Privacy"}]}]}`
2. In `local-requirements.json#export` set `confirmation` to
   `{"source":"user","reference":".allforai/product-concept/decision-journal.json#prior/decisions/0",
   "decision_id":"prior/decisions/0","reason":"Privacy"}`, `acceptance: ["MODEL-INVENTED acceptance"]`,
   `scope: ["orders","MODEL-ADDED-area"]`; set the node's `acceptance` to any text; rewrite its node-spec.
3. Observe + publish the node contract (`evidence_freshness.py` observe/publish with the bootstrap validator).
4. Run `validate_bootstrap.py`, `check_decision_inputs.py`, `validate_unattended_readiness.py --write-report`.

Observed: all exit 0; `unattended-run-readiness.json` `status: ready`, `blockers: []`;
`product_intent.py {"operation":"resume"}` → `topics: []`.
Expected (#11): the projection is pending with `legacy_reuse` until an explicit `confirm`, as the
`admit` route now does for the identical data (probe P1b: pending, freeze blocked).
