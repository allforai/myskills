# T11 legacy profile authority corrections (C1')

Base: candidate `ed430dfc` in this checkout. Owned edits:

- `claude/meta-skill/scripts/orchestrator/product_intent.py` (the Codex adapter reaches it
  through the `codex/meta-skill/scripts` symlink, so both host copies run the same code)
- new `claude/meta-skill/tests/unit/test_legacy_profile_authority.py`
- one narrow fixture change in `test_bootstrap_scope.py` (listed below, authorized by the
  spec review's "full-payload projections stay accepted")
- protocol pointers: `knowledge/bootstrap-planning.md` § requirement scope,
  `knowledge/product-intent-confirmation.md` `resume` bullet, `skills/bootstrap/SKILL.md`
  legacy-documents paragraph, `codex/meta-skill/skills/bootstrap.md` same paragraph
- this report

No staging, commit, reset, config, push, install or issue mutation. `check_decision_inputs.py`
needed no change: it already skips orphan detection while scope blockers exist, and the
journal reached through a verified projection is still counted as consumed.

## C1': the documented hand projection borrowed authority from a goal-only journal choice

`T11-T12-spec-final.md` C1' / `-repro.md`: on the documented route (`task_route:
local-change`, `task_scope.requirement_refs` into `local-requirements.json`, no
`intent_session_path`), `validate_scope` only checked that the referenced journal decision
existed and was a confirmed user-session choice. A decision whose `chosen` differed
entirely from the requirement goal, plus model-invented `acceptance` and an added scope
area, passed all three gates with readiness `ready`, and `resume` returned no topics
because it defaulted to the product concept. `admit` refused the existing file, so there
was no interactive recovery at all.

Red first (`test_legacy_profile_authority.py`, 10 of 12 cases failed on both hosts: every
gate exit 0 on the repro shape, resume empty). Minimal green:

- The journal block of `validate_scope` is extracted into `_journal_decision` (unchanged
  structural checks; forged references still raise into `invalid_scope`) followed by the new
  `_journal_payload`: a decision carrying `intent` must equal the projection; a goal-only
  decision must record the projection's `goal` and `confirmation.reason` and then raises
  `LegacyProjection`. Both outcomes become `pending_requirement` bound to the consuming
  nodes (message names the unconfirmed `scope`, `business_rules`, `acceptance`, or the
  goal/reason mismatch). Unrelated retained work stays executable.
- `_session_path` decides which intent file a session operates on: the marker is
  authoritative; without it, an existing `local-requirements.json` with requirements on a
  non-product route is the legacy local history. `resume`, `decide`, `freeze` and `plan`
  use it; `draft` and `admit` keep naming their own route, so a lingering pending local
  file never blocks a product draft.
- `_discussion` verifies a legacy (marker-less) file with `_hand_projection`, exactly the
  gate rule: actual user-turn references and full-payload journal decisions stay
  confirmed; a matching goal-only choice is exposed pending with `legacy_reuse`
  (evidenced `goal`; unconfirmed `scope`, `business_rules`, `acceptance`) and its retained
  confirmation; a mismatched or invalid one is pending with its reason and no
  `legacy_reuse`. Hand-projected items have no `topic`; they are grouped under
  `local-requirements` in the output only. No whole-product questions are generated.
- `decide` `confirm` on such an item already recorded the full payload, kept the old
  reference as `prior_confirmation`, and left earlier journal batches untouched; with the
  session path fix it now writes to the legacy local file in place (same id and revision,
  no marker, profile byte-identical), after which all three gates pass and `resume` is
  empty. A later local `freeze` records `intent_session_path`, so the session contract
  (`_local_contract`, drift checks) applies from then on.
- `admit` still refuses an existing local file; its error now points at `resume`.
- Coordinator follow-up (removed history): `_hand_projection` takes the same status set
  as `_confirmed`, and `_verified` selects the rule by route. On a legacy file a removed
  item with a user-turn reference or a full-payload journal decision resumes as removed
  history (no topic, no pending), a removed item with invalid provenance (for example
  `source: code`) is pending with its reason and no `legacy_reuse`, and `decide` uses the
  same rule so `confirm` cannot silently restore a verified removal; only an explicit
  `restore` records revision 2. Earlier journal batches stay byte-identical.
- Coordinator follow-up (mixed legacy transition): pinned as
  `test_mixed_legacy_history_enters_the_session_lifecycle_without_an_interview`. With a
  user-turn confirmed item, a goal-only pending item and a user-turn removed item, confirming
  only the pending item leaves resume empty and the hand-route gates consistent (the
  decision-input gate names the journal as unwired until the plan consumes the new
  decision, the T9 rule). **Limit, reported not broadened:** a local `freeze` is
  journal-backed and still calls canonical `_confirmed` (unchanged, strict), so it refuses a
  user-turn item until that item is recorded once. The test drives that recording with the
  original user turn as the batch `user_reference` and the recorded reason, and asserts the
  payload (goal, scope, rules, acceptance) is unchanged, the new confirmation and journal
  batch cite that turn, and the old confirmation is kept as `prior_confirmation`: this is
  recording an already evidenced payload, not obtaining fresh approval, and no question is
  asked. The freeze error now names the item and that action instead of the product-route
  wording.
  After the freeze records the marker, a removal excluded at that freeze is skipped by
  `_discussion`'s re-verification (it authorizes nothing and is hidden by the exclusion
  anyway), so verified removed history stays `removed` in `history` instead of being
  re-labelled pending under the session rule. Plan and the three gates then pass; the
  journal is `prior, projection, record, local-scope` with the prior batch byte-identical.

Coverage in the new file (both hosts): goal-only matching journal with invented acceptance
and added scope area blocks all gates with node-bound `pending_requirement` (not
`invalid_scope`), readiness `not_ready`, files untouched, resume exposes `legacy_reuse`
with goal, confirmation and history kept, no questions; mismatched goal-only journal
blocks and resumes pending without `legacy_reuse`, journal unchanged; one `confirm`
recovers gates and readiness in place, old batch byte-identical, then freeze marks the
session and plan/gates pass; full-payload journal projection accepted at gates and on
resume, and a drifted acceptance loses it; actual user-turn projection accepted at gates
and resumes empty; `admit` still refuses and writes nothing; removed legacy history with
full-payload, user-turn or invalid provenance (resume state, refused `confirm`, explicit
`restore`, files and old batch untouched).

## Existing test adjustment (narrow, justified)

| Test | Before | After |
|---|---|---|
| `test_bootstrap_scope.py::test_journal_backed_local_requirement_is_consumed_at_all_public_gates` | goal-only journal decision | the decision carries the full `intent` payload, which is what a journal-backed hand projection now needs to be authoritative; every assertion (gates pass, files untouched, journal consumed, orphan detection) unchanged |

Negative cases were not weakened: all ten forged-reference faults still resolve to
`invalid_scope` (`test_forged_journal_reference_cannot_authorize_local_requirement`), and
the session-route goal-only rule from the previous report is untouched.

## Verification

| Check | Result |
|---|---|
| `python3 -m pytest claude/meta-skill/tests/unit/test_legacy_profile_authority.py -q` | red 10 failed / 2 passed before the fix; green 20 passed after (6 added for the removed-history follow-up, 2 for the mixed transition, each red first) |
| focused #11 set (`test_bootstrap_scope`, `test_product_intent_resume`, `test_product_intent_session`, `test_intent_review_corrections`, `test_local_reopen_scope`, `test_legacy_projection_authority`, `test_legacy_profile_authority`, `test_freeze_idempotence`, `test_run_policy_session`) plus `test_validate_bootstrap`, `test_validate_unattended_readiness` and the #12 suites (`test_evidence_freshness`, `test_dynamic_input_dependencies`, `test_local_freshness_provenance`, `test_freshness_admission_corrections`, `test_freshness_diagnostic`, `test_freshness_downgrade`, `test_gate_project_root`, `test_corrupt_freshness_reads`), final state | 479 passed, 0 failed (158s), both host copies, on the final `product_intent.py`; the new suite was rerun alone after its last test-only edit (20 passed) |
| `uvx mypy --follow-imports=silent --check-untyped-defs --ignore-missing-imports` on `product_intent.py` | no issues |
| `git diff --check` | clean |

Remaining: none in the owned scope. Root owns the final full suite, review and commit.
The minor (c) freshness-register note in the spec recheck and #13–#18 were not touched.
