# T13 corrective-delta spec review (candidate c77323da, base 000c9242)

Reviewed `git diff 000c9242...HEAD` (one commit, HEAD verified
`c77323dab5a0266ab18bd24fbe08c75add4732c8`) against GitHub #13 (v2, label
`ready-for-agent`, no comments). `T13-parity-corrections.md` treated as claims;
sibling current review not read. Source, tests, Git state and the issue untouched.

## Verdict

Both prior partials are closed. No missing, partial or wrong requirement work,
no scope creep, no new completion shortcut, no unrequested restriction.

## Partial 1 — "Claude 与 Codex …消费同一权威规则"

All three cited Codex surfaces now carry `accepted_with_gaps`:
`flow-template.py:26` `BLOCKING_STATUS_VALUES`, the generated worker prompt rule 6
(`flow-template.py:532`), and `orchestrator-template.md:116` resume guidance.
The value matches the authoritative gate (`check_artifacts.py:20`,
`reconcile_bootstrap_workflow.py:40`), so this narrows the Codex report path to
the existing rule rather than adding a new one — no unrequested restriction.
`test_flow.py:58` first fails on the old code (status blocking is the only signal;
`gaps` is empty) and passes after, with `status: passed` still ready.

## Partial 2 — Node-spec parity for `document_verification`

`validate_bootstrap.py:1073` now parity-checks the fourth field, matching
SKILL.md:604 "Mirror all four in the Node-spec frontmatter";
`node-spec-template.md:9,13` names it and its per-document meaning ("mirror the
workflow's command unchanged"), which is exactly the equality the validator
enforces. Codex needs no template edit — `codex/.../bootstrap.md:299` defers to
the canonical contract and `flow-template.py:469` runs the same validator.

Regression shape is safe: the check is guarded by `if field in node`, so nodes
without the field (old or source-less projects) are unaffected, and a workflow
declaring `required_documents` without checks is still refused earlier by
`missing_document_verification`. Existing three-field behaviour unchanged.

## Evidence (re-run independently)

`test_delivery_closure.py` + `codex/meta-skill/test_flow.py`: **47 passed**.
Full `claude/meta-skill/tests/unit` + `test_flow.py`: **604 passed in 186.06s**.
Both match the claims. Copied-CLI runs only; host evidence remains 0/60, and the
delta does not claim otherwise.

## Observations (non-blocking)

- The 4-case parametrisation asserts only the bootstrap gate; that is the single
  point where node-spec parity lives for all four fields, so scope is right.
- `bootstrap-node-expansion-qa/SKILL.md:207` still enumerates blocking QA statuses
  without `accepted_with_gaps`. Pre-existing guidance text, not a gate.
- One cosmetic trailing-blank-line removal in `node-spec-template.md`.
