# T11 spec-review corrections: findings 2, 4, 6

Base: HEAD `5cab4f8f` in the T12 checkout. Scope is only the shared `claude/meta-skill/scripts/orchestrator/product_intent.py` (the Codex adapter reaches it through the `codex/meta-skill/scripts` directory symlink), the new public regression file `claude/meta-skill/tests/unit/test_intent_review_corrections.py` (visible to both hosts through the `codex/meta-skill/tests` symlink), and this report. No staging, commit, reset, push, install or issue mutation. Root owns `evidence_freshness.py`; the gate worker owns validators and templates; neither was edited. These are copied-CLI seam tests in temporary projects, not host-dialogue proof.

## Finding 4 (wrong behavior): reopening one intent blocked unrelated nodes

`_product_contract` now separates two levels:

- Freeze-level problems still raise and surface as global `invalid_scope`: missing or invalid baseline journal provenance, baseline not matching the journal decision, task scope differing from the frozen refs, baseline intents not matching its refs, workflow not consuming the current frozen baseline, missing stage applicability reasons, and missing full-process responsibilities. A new freeze without a replan therefore still blocks the whole plan until `plan` runs; that is the honest global freeze semantic and it lasts only across the bootstrap freeze-then-plan step.
- Per-intent drift returns blockers bound to the consuming nodes through `node_id`: a reopened intent (latest revision pending) gives `pending_requirement`, an adjusted, removed, restored or otherwise changed intent gives `stale_requirement`, an intent whose journal choice no longer verifies gives `pending_requirement` with the reason, and a pending question that an included intent depends on gives `pending_requirement` naming the unresolved decision. Node projection checks (excluded intent, goals or acceptance not equal to the confirmed intent) also bind to that node instead of raising.
- The shared per-reference loop in `validate_scope` (stale or duplicate revisions, invalid content, scope conflict, missing user confirmation) binds each blocker to the nodes that consume the reference through `_scoped`; a reference no current node consumes still blocks globally so silence is never approval.

Messages keep the words existing tests and readers look for (`unresolved`, `product`, the intent id, the node id). Blocker codes are existing ones; no new code was introduced. Retained completed nodes stay exempt exactly as before.

Regression (P1 shape): two product nodes on disjoint intents, contracts published through the copied freshness CLI, all three gates ready. Reopening `value-proposition` (node-b) or the `conflict` question (depends on `tradeoffs`, node-b) makes readiness `not_ready` with every blocker carrying `node_id: node-b` and none `invalid_scope`; `validate_bootstrap` and `check_decision_inputs` name node-b and never node-a. Refreezing while the intent is pending is refused. After the user confirms or answers, refreeze plus replan returns all gates to ready, node-a's Node-spec bytes are unchanged, and the workflow consumes baseline version 2. Tampering with the frozen baseline's confirmation stays a single global `invalid_scope` without `node_id`; editing node-b's acceptance in the plan blocks node-b only.

Not changed: the local-change route still raises globally in `validate_scope` when the local projection selects a stale or reopened intent (`Local scope selects stale intent`), because that path belongs to #9/#10 and the review scoped finding 4 to the product route. Readiness still returns exit 1 whenever any blocker exists; only the blocker attribution changed, since the runners and readiness report are owned elsewhere.

## Finding 2 (partial): product-route legacy choices were re-asked

`draft` no longer strips `confirmation` and forces `pending`. An item that claims `status: confirmed` or carries a `confirmation` goes through `_reuse_legacy_choice`, shared with `admit`: it stays confirmed only when `_confirmed` verifies canonical `decision-journal.json` schema-1.0 user-session provenance whose recorded choice and rationale equal the projection and is not superseded; otherwise it is persisted as `pending` with `pending_reason: Legacy intent needs user verification`. Items without any confirmation claim are provisional exactly as before. Revision must be a positive integer (default 1) so a legacy revision is preserved rather than reset. The journal is never modified by `draft`.

Regression (P5 shape): a product-reconstruction or new-product draft whose `target-users` item cites a valid prior journal choice is not re-asked, is stored confirmed, and freezes without a new decision while the prior batch stays byte-identical. Variants with a non-canonical reference (`bootstrap user turn 2`), `source: code`, a rationale the journal never recorded, a superseded decision, or no journal file are all stored pending with a reason, are re-asked, cannot be frozen, and freeze after one explicit confirm.

## Finding 6 (minor): invalid `run-policy.json` could not be repaired

`run_policy` reads the recorded file through `_recorded_policy`, which reports an unparsable or invalid file instead of trusting it. Then:

- `--run-policy` with an invalid file returns `needs_run_policy` (exit 1) with the standard questions and an `invalid_policy` reason, so the interactive entry asks again.
- `--policy-event` and any `run-event` request with an invalid file are refused (`blocked`); a `run-event` that carries answers is refused as well, so unattended execution never collects or repairs a policy.
- A `run-policy` request with complete valid answers and an actual `user_reference` rewrites `run-policy.json` and appends `{previous, reason, answers, user_reference}` to `.allforai/bootstrap/run-policy-repairs.json`. Missing user reference, incomplete or unknown answers, or a corrupt audit list are refused and leave the file unchanged.
- A valid recorded policy is still never replaced by later answers, and the initial collection path is unchanged.

Regression (P6 shape) covers a wrong value, a missing key, a non-object, and non-JSON content on both hosts, including the audit record and the later reuse of the repaired policy by `--run-policy` and `--policy-event`.

## TDD and validation

1. Wrote `test_intent_review_corrections.py` first and ran it against the unmodified helper: **28 failed, 2 passed** (the two passing cases are the freeze-level global guard, already correct).
2. Implemented the three corrections. During the run the shared fixture `test_bootstrap_scope.project` was changed concurrently by another worker (default `source_inputs=("orders.py",)` with a contract publication verified by `validate_bootstrap`) and the validator started requiring `source_inputs` on intent-aware nodes. The new tests therefore call the fixture with `source_inputs=None`, declare `source_inputs` explicitly in their own plan requests (the `plan` operation does not add inputs on its own), and publish contracts through the copied freshness CLI. One over-broad assertion of mine (expecting the word `product` in root's `stale_evidence` message) was narrowed to scope blockers.
3. Final focused run, `python3 -m pytest claude/meta-skill/tests/unit/test_intent_review_corrections.py -q`: **30 passed** on both host copies.
4. `uvx mypy --follow-imports=silent --check-untyped-defs claude/meta-skill/scripts/orchestrator/product_intent.py claude/meta-skill/scripts/check_decision_inputs.py`: **no issues in 2 files**. `git diff --check` on the two owned files: clean.
5. Attribution of related-suite failures: see the section below.

## Related suites and concurrent working-tree state

The shared checkout was being edited concurrently by root (`evidence_freshness.py`, `check_artifacts.py`, `reconcile_bootstrap_workflow.py`) and the gate worker (validators, templates, `test_bootstrap_scope.py`, `test_evidence_freshness.py`). To attribute failures honestly, the same seven related suites (`test_product_intent_session`, `test_product_intent_resume`, `test_product_retained_scope`, `test_product_question_identity`, `test_run_policy_session`, `test_bootstrap_scope`, `test_evidence_freshness`) were run twice against the same working-tree state: once in a scratch copy with `git show 5cab4f8f:claude/meta-skill/scripts/orchestrator/product_intent.py` substituted (the checkout source was never reverted), and once on the live tree with this change.

| Run | Result |
|---|---|
| Scratch copy, HEAD helper | 33 failed, 225 passed |
| Live tree, this change | 29 failed, 229 passed |
| Failures present only with this change | 0 |

The 29 remaining failures are identical between the two runs except four freshness tests that root's concurrent changes fixed in the meantime. Their causes are outside this change:

- `validate_bootstrap` now refuses plan nodes without `source_inputs` (`deliver-orders missing 'source_inputs'`, `export missing 'source_inputs'`). The existing product-route and local plan tests (`test_product_intent_session:76`, `test_product_intent_resume:98/179`, `test_product_retained_scope:68/126`, `test_product_question_identity:89`) never declare inputs. Whether `plan` should default them or the tests should declare them is the gate-worker coordination item; this change adds nothing on its own.
- Generated Codex driver exit codes (`test_run_policy_session:73/106/208`) changed with the concurrent `flow-template.py` / `check_artifacts.py` work.
- An earlier transient state of the shared fixture (contract publication verified by `validate_bootstrap` while the requirement was still pending) made 56 fixture-time failures; the gate worker has since changed the fixture and they no longer occur.


## Remaining

- Host-dialogue proof for the interactive entry (repair prompt, reopened-intent prompt) stays pending for #16/#17; nothing here claims it.
- Local-change route reopen still blocks globally (`validate_scope` local projection check); outside finding 4's product scope.
- Readiness exit status is global by design of the readiness report; per-node skipping by the run engines is not implemented here and was not requested.
- Any `plan`-side `source_inputs` defaulting stays with the gate worker via root; this change only preserves what the plan request declares.
