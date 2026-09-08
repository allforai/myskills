# T11 legacy projection authority and freeze idempotence corrections (C1, A1)

Base: candidate `90257b15` in this shared checkout, with concurrent peer edits
(freshness worker, root template wording) left untouched. Owned edits:

- `claude/meta-skill/scripts/orchestrator/product_intent.py` (the Codex adapter reaches
  it through the `codex/meta-skill/scripts` symlink, so both host copies run the same code)
- new `claude/meta-skill/tests/unit/test_legacy_projection_authority.py`
- new `claude/meta-skill/tests/unit/test_freeze_idempotence.py`
- `claude/meta-skill/knowledge/product-intent-confirmation.md` (three paragraphs, listed below)
- narrow adjustments to three existing goal-only positive tests (listed below, authorized by root)
- this report

No staging, commit, reset, config, push or issue mutation. All tests drive the copied
public `product_intent.py`, `evidence_freshness.py` and the three public gates in
temporary projects on both host copies. They are copied-CLI seam tests, not
host-dialogue proof; #13–#18 remain pending.

## C1: a goal-only legacy journal choice authorized unrecorded scope, rules and acceptance

`T11-T12-spec-recheck.md` C1: a product draft or local `admit` item citing a schema-1.0
journal decision that records only `chosen` and `rationale` was stored `confirmed`,
never appeared in `discussion` topics, froze with no `decide`, planned, and every gate
reported ready; the node's `acceptance` was the model's invention. `_confirmed`
compared only goal and rationale for decisions without an `intent` payload.

Red first (`test_legacy_projection_authority.py`, 8 of 10 cases failed on both hosts:
the goal-only item was absent from topics and freeze succeeded). Minimal green:

- `_confirmed` still verifies the recorded choice and rationale, then raises the new
  `LegacyProjection` (a `ValueError`) whenever the decision has no `intent` payload.
  Every existing caller that catches `ValueError` therefore fails closed: `freeze`
  refuses the include, `_intent_drift` reports `pending_requirement` for the consuming
  nodes, `validate_scope` keeps its outer guard.
- `_reuse_legacy_choice` (shared by `admit` and `draft`) and `_discussion` (stored
  history on `resume`) catch `LegacyProjection` and expose the item as `pending` with
  `pending_reason` and `legacy_reuse: {reference, evidenced: ["goal"], unconfirmed:
  ["scope", "business_rules", "acceptance"]}`. The goal, revision and prior reference
  are kept for context, so nothing is re-interviewed and the local admission still
  asks no whole-product questions.
- `decide` `confirm` on such a pending item records the full payload in the journal,
  moves the historical reference to `prior_confirmation`, and drops the stale
  `pending_reason` / `legacy_reuse` markers. After that, freeze, plan and the three
  gates pass; the prior journal batch is byte-identical.
- A legacy decision that does record the complete `intent` payload is still reused
  with no new decision (`test_local_full_payload_history_is_reused_without_reconfirmation`).

Coverage in the new file: local admit goal-only (exposed, freeze blocked, readiness
blocked, journal untouched, confirm, provenance, freeze/plan/gates ready, node
acceptance equals the confirmed value); local full-payload reuse; product route
goal-only for `product-reconstruction` and `new-product`; a stored concept already
marked confirmed against a goal-only journal resumes pending without rewriting the file.

Negative cases were not weakened: non-canonical reference, `source: code`, different
rationale, superseded and missing journal still resolve to `pending` without
`legacy_reuse` and cannot freeze (`test_intent_review_corrections.py`), and the #9
legacy per-reference gate path for profiles without an intent session (goal-only
journal references on `local-requirements.json`) is untouched (`test_bootstrap_scope.py`).

## A1: an identical re-freeze appended a decision, bumped the version and forced a replan

Red first (`test_freeze_idempotence.py`, 8 of 12 cases failed: duplicate batch identity
or version 2 on an unchanged selection). Minimal green in `freeze`:

- Before the batch-identity check, if the previous frozen scope binds the same
  selection (`requirement_refs` and `intents` compared by id, so include order is
  irrelevant; `excluded` equal), the profile task scope still matches it, the scope
  batch still verifies through the extracted `_frozen_scope_batch` helper, and no
  journal batch was recorded after that scope batch, the CLI returns
  `{"status": "frozen", "baseline": <existing>, "unchanged": true}` and writes nothing.
- Otherwise the freeze proceeds exactly as before: a changed selection or exclusion,
  an adjusted intent revision, any later user decision (for example a reopened and
  re-answered question) or an unverifiable previous scope freezes the next version,
  and the gates block until the plan is regenerated.

Coverage: identical product re-freeze with a new or the same batch id converges
(files byte-identical, journal still two batches, all gates ready, no replan);
narrowed product selection is version 2 and blocks all gates; an adjusted intent with
the same selection is version 2 and recovers after replan; a re-answered question is
version 2; a tampered scope batch is not reused; the local route converges on the
same selection in a different include order and invalidates on a narrowed selection.

## Existing test adjustments (narrow, justified)

| Test | Before | After |
|---|---|---|
| `test_product_intent_resume.py::test_local_legacy_admission_reuses_only_supported_choice_and_preserves_old_documents[True]` | trusted goal-only item absent from topics; freeze without decide | item exposed with `legacy_reuse` and its retained confirmation; freeze blocked; confirm; then the original freeze/plan/gates/drift assertions unchanged. The `False` variant keeps its behavior and now asserts `legacy_reuse` is absent. |
| `test_product_intent_session.py::test_existing_canonical_user_choice_is_reused_without_new_intent_decision` | prior decision goal-only | prior decision carries the full `intent` payload, which is what "reuse without a new decision" now requires; assertions unchanged |
| `test_intent_review_corrections.py::test_product_draft_reuses_legacy_choice_only_with_canonical_journal_provenance` | trusted variants stored confirmed and froze | all variants pending and blocked; only trusted variants carry `legacy_reuse`, then confirm, freeze, `prior_confirmation` retained and journal batches `prior, projection, scope`; untrusted variants unchanged |

## Canonical doc edits (`product-intent-confirmation.md`)

- `draft` bullet: a legacy item stays confirmed only with a complete recorded `intent`;
  goal-only choices return pending with `legacy_reuse` and need one `confirm`, which
  retains `prior_confirmation`.
- `admit` bullet: same rule for the local route, explicitly without a whole-product interview.
- `freeze` bullet: identical re-freeze returns the existing version with `unchanged: true`;
  a changed selection, exclusion or revision freezes the next version and needs a replan.

## Verification

| Check | Result |
|---|---|
| `python3 -m pytest claude/meta-skill/tests/unit/test_legacy_projection_authority.py -q` | red 8 failed / 2 passed before the fix; green 10 passed after |
| `python3 -m pytest claude/meta-skill/tests/unit/test_freeze_idempotence.py -q` | red 8 failed / 4 passed, then 2 more red for the re-answered case; green 14 passed after |
| focused #9–#12 set (13 suites in `validation-commands.md` plus `test_bootstrap_scope`, `test_product_intent_session`, and the two new files) | 386 passed, 0 failed (134s), both host copies |
| `uvx mypy --follow-imports=silent --check-untyped-defs --ignore-missing-imports` on `product_intent.py` | no issues |
| `git diff --check` | clean |

Remaining: none in the owned scope. Root owns templates, integration of
`validation-commands.md`, final full suite and commit. C2 (freshness `observe`
traceback on corrupt dependencies) and C3 (duplicate pending/stale codes on reopen)
belong to the other worker and root respectively and were not touched here.
