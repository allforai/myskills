# M2 experience-intent — task contracts

Design: `docs/superpowers/specs/2026-09-18-experience-intent-design.md` (sections "需求" and "Detailed design").
Registry: `docs/superpowers/runs/2026-09-18-product-experience-overhaul/registry.json`.
Branch `product-experience-overhaul`. The orchestrator commits; executors run no git mutation.

Unit labels (U1..U9), assumption labels (A1..A11) and test-case numbers below refer to the design's
"Detailed design". The design is the authority for every shape, literal and error message; this plan
states what must be true per task, how it is proven, and what may be written.

## Ground rules for every task

- All acceptance commands run with cwd = repository root. `T/` below abbreviates
  `claude/meta-skill/tests/unit/`; the task JSON carries the full paths.
- Tests are selected by explicit pytest node id (`file::test_name`, which collects both `host`
  parametrizations). A missing test makes pytest exit 4, so no command can pass on zero tests.
- Test first: add the named test cases, watch them fail for the stated reason, then make them pass.
- New tests live in `T/test_experience_direction.py`, written in the subprocess style of
  `test_product_intent_session.py` (`invoke/draft/decide`, `@pytest.mark.parametrize("host", ["claude", "codex"])`),
  importing `project, write, gate, confirm_plan, publish_contract` from `.test_bootstrap_scope` and
  `ATTENTION_CONTRACT_BODY` from `.test_validate_bootstrap`. Private helpers of the new file
  (`proposal`, `propose`, `new_product_draft`, `set_mode`, `cli`, `plan_request`) are specified in design U9;
  each task adds the helpers it first needs.
- Fixture wording stays headless (design A10): no helper text may contain an M1 UI term
  (`screen`, `frontend`, `界面`, `页面`, ...), and no profile module may have `role` in `{frontend, mobile}`.
  Assertions are never weakened to accommodate M1/M3 checks.
- Never touch: `validate_bootstrap.py`, `validate_meta_contracts.py`, `knowledge/bootstrap-planning.md`,
  `tests/unit/test_validate_bootstrap.py`, `tests/unit/test_bootstrap_scope.py`, `skills/bootstrap/SKILL.md`,
  `check_decision_inputs.py`, `validate_unattended_readiness.py`, `check_artifacts.py`, any codex/pi twin file.
  `tests/unit/test_evidence_freshness.py` has two known failures (`cannot_claim_completion[claude|codex]`); do not edit it.
- Hard invariants (design "Architecture"): proposals never enter `requirements[]`; an intent item is fully
  formed before the existing `copy.deepcopy(item)` writes it to the journal and is never mutated afterwards;
  old items never get injected fields (all new reads use `.get`); the journal batch schema is unchanged.
- All new rejections are `ValueError`, surfaced by the existing `__main__` as `{"status": "blocked"}` + exit 1;
  validation precedes a single write, so a rejected request leaves `CONCEPT` and `JOURNAL` byte-identical.

## Task graph

```
T-M2-01 ─▶ T-M2-02 ─▶ T-M2-03 ─▶ T-M2-04 ─▶ T-M2-05 ─▶ T-M2-06 ─▶ T-M2-07 ─┐
   │                                                        └──▶ T-M2-08 ──┤
   └──▶ T-M2-09 ───────────────────────────────────────────────────────────┴▶ T-M2-10
```

`product_intent.py` and `test_experience_direction.py` are shared by most tasks, so the chain is serial by
path collision as well as by dependency. No task is reality-gated: every acceptance is a subprocess/unit test,
a validator run or a literal check.

Test-case split relative to the design's 14 cases: design case 8 and case 9 each mix `select`, `delegate` and
disclosure behaviour. They are split along task seams (cases 8a/8, 9a/9 below). No assertion is dropped; the
file ends with 16 test functions.

---

## T-M2-01 Topic `experience-direction`, test mirror and the two broken session tests

Requirements: R-M2-01, R-M2-09, R-M2-10 (design U1, U7).

Behaviour: `TOPICS` in `product_intent.py` contains `"experience-direction"` immediately before `"tradeoffs"`,
and `EXPERIENCE_TOPIC = "experience-direction"` exists for later units. A draft lacking that topic yields the
pending question `gap-experience-direction` through the existing gap loop; no new freeze logic is added
(headless products exclude the gap with a reason under the existing full-coverage rule).
The test mirror at `test_product_intent_session.py:13` matches. The two tests the insertion really breaks are
repaired without changing their meaning: `test_revised_baseline_…` uses
`kept = [t for t in TOPICS if t not in ("business-loop", "tradeoffs")]` for both the confirm list and `include`;
`test_four_explicit_operations_…` expects `["scenarios", "core-problem", "experience-direction", "tradeoffs"]`.
The five assertion sites named by R-M2-10 are mirror-driven and stay unedited (design spec correction 1).

Test intent: case 1 `test_topic_is_listed_before_tradeoffs_and_missing_direction_is_a_gap` asserts the script's
`TOPICS` equals the mirror, that the new topic sits directly before `tradeoffs`, and that `new_product_draft()`
output contains `gap-experience-direction`. It fails today because the topic does not exist. The session and
intent-review files prove the mirror change broke nothing else.

Acceptance:
```
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_topic_is_listed_before_tradeoffs_and_missing_direction_is_a_gap claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_intent_review_corrections.py
```

Write set: `claude/meta-skill/scripts/orchestrator/product_intent.py`,
`claude/meta-skill/tests/unit/test_product_intent_session.py`,
`claude/meta-skill/tests/unit/test_experience_direction.py` (create).

## T-M2-02 Proposal storage, validation, id namespace and operation `propose`

Requirements: R-M2-02, R-M2-03 (design U2, U3). Implements `data:experienceProposals`, `api:productIntentPropose`.

Contract:
- Request `{operation: "propose", proposals: [...], recommended_id, rationale}`.
- A proposal's key set is exactly
  `id, title, who, circumstance, core_loop_feel, first_minute, return_reason, goal` (non-empty text),
  `anti_goals, tradeoffs, scope, business_rules, acceptance` (non-empty lists of non-empty strings) and
  `comparable: {product, approach}` (both non-empty text). Extra keys (`origin`, `status`, `confirmation`,
  `round`, `recommended`, ...) are rejected.
- Stored element of `product-concept.json.experience_proposals[]` = the input fields +
  `origin: "model-proposal"` + `round: int >= 1` + `recommended: bool`; the recommended one also carries
  `rationale`. The array is append-only; a repeated `propose` opens `round = max + 1`.
- Validation order and messages as in design U3 (product session required, 2–3 proposals, distinct ids,
  exactly one recommended, non-empty rationale, then `_validate_question_ids`). Nothing reads or writes the
  decision journal and no `user_reference` is required.
- `_validate_question_ids` additionally enforces that proposal ids are unique among proposals of all rounds,
  intent ids and question ids (message: `Proposal identities must be unique and separate from intent and
  question identities`); existing messages are unchanged and a missing key is a no-op.
- Helpers `_proposal(value) -> dict` and `_current_proposals(concept) -> list` (highest round, `[]` if none).
- `propose` returns `_discussion(root, concept)` (enriched in T-M2-03).

Test intent:
- case 2 `test_propose_validates_count_recommendation_and_fields`: 1 and 4 proposals, foreign `recommended_id`,
  empty `rationale`, each missing field, empty list field, `comparable` without a sub-key and extra keys
  (`origin`, `status`) are each rejected with exit 1, `CONCEPT` bytes unchanged and no `JOURNAL` file. This
  proves validate-then-write and that a host cannot smuggle authority fields into a proposal.
- case 4 `test_proposal_identity_is_unique_across_proposals_intents_and_questions`: a proposal id colliding
  with an intent id, a question id, or an earlier round's proposal id is rejected.
- case 5 `test_proposal_cannot_be_confirmed_or_frozen`: after a successful `propose`, `confirm` of a proposal id
  exits 1 and a `freeze` whose `include` names a proposal id exits 1 with no baseline file. No new rejection
  branch is written for this; the test proves the "proposals are not intents" invariant. The same test asserts
  the stored shape (`origin`, `round == 1`, exactly one `recommended`, `rationale` on it) so that the success
  path is proven in this task.

Acceptance:
```
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_propose_validates_count_recommendation_and_fields claude/meta-skill/tests/unit/test_experience_direction.py::test_proposal_identity_is_unique_across_proposals_intents_and_questions claude/meta-skill/tests/unit/test_experience_direction.py::test_proposal_cannot_be_confirmed_or_frozen claude/meta-skill/tests/unit/test_product_question_identity.py
```

Write set: `product_intent.py`, `test_experience_direction.py`.

## T-M2-03 `_discussion` / `resume` present the current proposal round

Requirements: R-M2-03, R-M2-09 (design U6).

Behaviour: under the `experience-direction` topic, `_discussion` adds `proposals` (current round only),
`recommended_id` and `rationale`; the topic is listed even with no items/questions while proposals exist and no
confirmed direction does. The returned object gains `experience_proposals` (all rounds) only when that array is
non-empty. With no proposals, output is byte-identical to today (design A6).

Test intent: case 3 `test_propose_stores_rounds_without_journal_and_resume_presents_current_round` asserts round 1
storage with no journal, a second `propose` with new ids giving `round == 2` while round 1 is preserved verbatim,
`resume` showing only round 2 with correct `recommended_id`/`rationale`, and `propose` before `draft` rejected.
`test_product_intent_resume.py` proves the old resume output is unchanged.

Acceptance:
```
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_propose_stores_rounds_without_journal_and_resume_presents_current_round claude/meta-skill/tests/unit/test_product_intent_resume.py
```

Write set: `product_intent.py`, `test_experience_direction.py`.

## T-M2-04 `decide` action `select` and the experience-direction intent

Requirements: R-M2-04 (design U4). Implements `api:productIntentSelect`, `data:experienceDirectionIntent`.
Requires `data:experiencePriority` (the gate test writes `experience_priority.mode = consumer` in the shape M1 defines).

Contract:
- Action `{"operation": "select", "proposal_id": ..., "reason": ...}` (key is `operation`, not `op`).
- `_direction_intent(concept, concept_path, action, op) -> dict` applies design U4 rules 1–6 in order: product
  session only; a current round must exist (`No current experience proposals; propose before select or
  delegate`); `proposal_id` must be in the current round (`Select one proposal of the current round`);
  at most one confirmed proposal-derived direction (`An experience direction is already selected; remove it
  before choosing another`); id `experience-direction-<proposal_id>` must be unused.
- Resulting item, fixed before the journal copy:
  `{id, topic: "experience-direction", goal, scope, business_rules, acceptance, revision: 1,
  origin: "model-proposal", evidence: [], status: "confirmed", proposal_id, who, circumstance,
  confirmation: <existing batch stamp, source "user">}`. No `auto_decided` for `select`.
- Journal decision: `operation == "select"`, `question == item.id`, `chosen == item.goal`, `supersedes None`,
  `intent == item`.
- The fallback error text lists all nine actions
  (`…confirm/add/adjust/remove/answer/reopen/restore/select/delegate…`).
- `select` does not close `gap-experience-direction`; the host adds an `answer` in the same batch (A3).
  A same-batch `adjust` on `experience-direction-<proposal_id>` uses the existing revision chain, no new code.

Test intent:
- case 6 `test_selected_direction_freezes_and_passes_all_public_gates`: `set_mode(consumer)`, `propose`, one
  batch of `select` + `answer gap-experience-direction` + `confirm` of the other topics; asserts every item
  field above (including `who`/`circumstance` equal to the proposal's), the journal decision, then
  `freeze` → `plan` → `confirm_plan` → `publish_contract` → all three public gates exit 0. This proves the item
  satisfies `_confirmed`'s whole-dict equality and that its `acceptance` reaches node acceptance.
- case 7 `test_select_then_adjust_in_one_batch_keeps_revision_lineage`: two revisions (`superseded`, `confirmed`),
  the new one keeps `origin`/`proposal_id`, and freezes.
- case 9a `test_select_needs_a_current_round_proposal_and_a_free_direction_slot`: `select` with no proposals,
  with an old-round id, and with a direction already selected each exit 1 with files unchanged.

Acceptance:
```
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_selected_direction_freezes_and_passes_all_public_gates claude/meta-skill/tests/unit/test_experience_direction.py::test_select_then_adjust_in_one_batch_keeps_revision_lineage claude/meta-skill/tests/unit/test_experience_direction.py::test_select_needs_a_current_round_proposal_and_a_free_direction_slot
```

Write set: `product_intent.py`, `test_experience_direction.py`.

## T-M2-05 `decide` action `delegate`

Requirements: R-M2-05 (design U4). Implements `api:productIntentDelegate`.

Contract: `{"operation": "delegate", "reason": ...}` takes the current round's recommended proposal; a
`proposal_id` on the action is rejected (`Delegate takes the recommended proposal; use select to name one`);
no current round is rejected. The item equals the `select` shape plus `auto_decided: true`, and its
`confirmation` carries `delegated: true` (set on the batch stamp before it is attached). Journal
`operation == "delegate"`. `user_reference` stays the existing non-empty check; its truthfulness is a protocol
obligation (T-M2-09).

Test intent:
- case 8a `test_delegate_records_the_recommended_proposal_as_an_auto_decision`: after `delegate` the item's
  content equals the recommended proposal's `goal/scope/business_rules/acceptance/who/circumstance`,
  `auto_decided is True`, `confirmation.delegated is True`, `confirmation.user_reference` is the batch's, the
  journal decision has `operation == "delegate"` and `intent == item`, and the item freezes.
- case 9 `test_delegate_and_select_need_a_current_proposal_round`: with no proposals both actions exit 1 and
  files are unchanged; `delegate` carrying `proposal_id` is rejected.

Acceptance:
```
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_delegate_records_the_recommended_proposal_as_an_auto_decision claude/meta-skill/tests/unit/test_experience_direction.py::test_delegate_and_select_need_a_current_proposal_round
```

Write set: `product_intent.py`, `test_experience_direction.py`.

## T-M2-06 Read-only disclosure `--delegations`

Requirements: R-M2-07 (design U5b, script half). Implements `data:delegationDisclosure`.

Contract: public `delegations(root) -> {"status": "delegations", "delegations": [...]}`; one entry per latest
confirmed intent with `auto_decided is True`:
`{id, revision, proposal_id, proposal_title, user_reference, reason}`. `user_reference`/`reason` come from the
revision whose `confirmation.delegated is True` (fallback: the item itself); `proposal_title` is the matching
proposal's `title` or `null`. Missing concept file → empty list. Writes nothing.
CLI: `product_intent.py <root> --delegations` maps to `{"operation": "delegations"}`, dispatched at the top of
`session()`; exit 0; a corrupt concept file takes the existing `blocked` + exit 1 path.

Test intent: case 8 `test_delegate_records_auto_decision_and_is_disclosed`: after a delegation the CLI exits 0 and
lists id, `proposal_title`, `user_reference`, `reason`, with `CONCEPT`/`JOURNAL` bytes identical before and
after; after a later-batch `adjust` the entry is still listed and `user_reference` is still the delegation turn
(proves the revision-chain lookup); an item produced by `select` is never listed.

Acceptance:
```
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_delegate_records_auto_decision_and_is_disclosed
```

Write set: `product_intent.py`, `test_experience_direction.py`.

## T-M2-07 Blocker `ui_product_without_experience_direction`

Requirements: R-M2-06, R-M2-01 (design U5a). Requires `data:experiencePriority`.

Contract: `_experience_direction_blockers(root, profile, refs) -> list`, registered by one line in the product-route
branch of `validate_scope` after `_product_contract`. It returns one global blocker (no `node_id`) with code
`ui_product_without_experience_direction` when `profile.experience_priority.mode` is `consumer` or `mixed` and no
`requirement_refs` entry resolves to a latest intent with `topic == "experience-direction"`,
`status == "confirmed"` and matching `revision`. Missing/invalid `mode`, `admin`, `none` and the `local-change`
route never produce it. A confirmed direction of any origin satisfies it. The three public gates and `plan`
pick it up through `validate_scope`; their files are not edited. The code is a new literal whose legal set is
defined by `product_intent.py` itself (blocker codes are free-form dict values there; no enum file to update).

Test intent:
- case 10 `test_ui_product_without_direction_is_blocked_at_every_gate`: a product frozen with
  `gap-experience-direction` excluded plans and publishes while the code does not apply; after
  `set_mode("consumer")` each of the three gates exits 1 with the code on stdout, the same for `"mixed"`, and a
  re-run of `plan` under `consumer` is refused with the code.
- case 11 `test_direction_gate_stays_silent_when_it_does_not_apply`: `none`, `admin` and missing field never show
  the code; the `local-change` workflow of `project()` under `consumer` never shows it; a headless product
  (`mode == none`, gap excluded, `not_applicable.experience` reasoned) freezes and passes all three gates.

Acceptance:
```
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_ui_product_without_direction_is_blocked_at_every_gate claude/meta-skill/tests/unit/test_experience_direction.py::test_direction_gate_stays_silent_when_it_does_not_apply
```

Write set: `product_intent.py`, `test_experience_direction.py`.

## T-M2-08 Run summary and completion text disclose delegations

Requirements: R-M2-07 (design U5b, summary and template half; A9).

Contract:
- `summarize_run_log.py`: top-level `try: from product_intent import delegations as _delegations` /
  `except ImportError: _delegations = None`. `summarize()` gains key `delegations` (list; `[]` when unavailable),
  and on `(OSError, ValueError, TypeError, KeyError, AttributeError, IndexError)` also `delegations_error: str`.
  `write_reports()` appends `## Delegated Decisions` after "Recent Failures": one line per entry
  ``- `<id>` proposal=`<proposal_title>` user_turn=`<user_reference>` reason=`<reason>` ``, `- none` when empty,
  plus `- unreadable: <error>` when `delegations_error` is set. `schema_version` stays `"1.0"`.
- `knowledge/orchestrator-template.md`, `## Post-Completion`: a new step 0b between "Run log summary" and
  "Mark concept drift resolved" that runs `python3 .allforai/bootstrap/scripts/product_intent.py . --delegations`
  and requires the completion text to print, under the heading `Decisions you delegated to the model`, each
  entry's id, proposal title, user turn and reason, or `No delegated decisions.`; it runs on success and on early
  stop and asks no question. No existing sentence is removed or reworded.

Test intent: case 13 `test_run_summary_and_completion_text_disclose_delegations` (not host-parametrized) loads
`product_intent` and `summarize_run_log` through `tests/module_isolation.load`, builds a `tmp_path` with a
delegated item, and asserts `summary["delegations"]` has one entry and `run-summary.md` contains
`## Delegated Decisions` and the proposal title; with no concept file it asserts `[]` and `- none`. It also reads
the canonical template and asserts `--delegations` and `Decisions you delegated to the model` appear after
`## Post-Completion`. `test_run_logging.py` guards the summary regression and `validate_meta_contracts.py`
proves no pinned template literal was lost.

Acceptance:
```
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_run_summary_and_completion_text_disclose_delegations claude/meta-skill/tests/unit/test_run_logging.py && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

Write set: `claude/meta-skill/scripts/orchestrator/summarize_run_log.py`,
`claude/meta-skill/knowledge/orchestrator-template.md`, `test_experience_direction.py`.

## T-M2-09 Protocol text `product-intent-confirmation.md`

Requirements: R-M2-01, R-M2-08 (design U8, items 1–8).

Contract (local replacements and additions only):
1. prose topic list names "experience direction" before tradeoffs;
2. the action sentence becomes: recommendations, displayed defaults, omitted answers and silence are not
   actions; `` `select` and `delegate` are actions ``;
3. origin list: `model-proposal` appears only on proposals and proposal-derived items; `draft` still accepts only
   `inference`, `unknown`, `user-request`;
4. topic list gains `experience-direction` between `business-loop` and `tradeoffs`, with the distinction from the
   `experience` stage / `not_applicable` key, and the headless rule (exclude `gap-experience-direction` at
   `freeze` with a reason);
5. a `propose` entry after `resume` (request shape, field table, 2–3 / exactly one recommended / rationale,
   rounds, no journal, what `resume` returns);
6. the `decide` catalogue gains `select` and `delegate` (request key `operation`; derived id
   `experience-direction-<proposal_id>`; carried `who`/`circumstance`; `auto_decided` and
   `confirmation.delegated` for delegate; `user_reference` must be the real user turn of the delegating
   utterance; same-batch `adjust`; same-batch `answer` closing `gap-experience-direction`; rejection without a
   current round; `remove` before re-selecting);
7. a section `## Experience direction proposals` after "Discussion responsibility": trigger (product route and
   `experience_priority.mode != none` → `propose` is mandatory before discussing the topic), quality bar
   (who / circumstance with scale and frequency / feeling / return reason before features; one mature comparable
   product; directions differ in direction, not size; `acceptance` is observable experience criteria),
   the no-literal-translation rule with the "fragmented learning / 碎片化学习" example, self-check against
   `consumer-maturity-patterns.md` §B (The Compressed Admin Panel, The Concept Demo, Feature Checklist Design),
   the authority boundary and `--delegations` disclosure (naming follows `defensive-patterns.md` Pattern H);
8. the CLI section notes `--delegations` is a read-only entry.

Every line mentioning `experience_priority` must contain the literal `experience_priority.mode` (M1 invariant).

Test intent: case 14 `test_protocol_text_names_the_new_topic_and_actions` (not host-parametrized) asserts the
canonical file contains `experience-direction`, `` `select` and `delegate` are actions ``, `model-proposal`,
`## Experience direction proposals`, `consumer-maturity-patterns.md`, `--delegations`, and no longer contains
`omitted answers and silence are not actions.`. The grep clause proves the M1 same-line invariant for this file;
the validator proves no pinned contract literal was lost.

Acceptance:
```
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_protocol_text_names_the_new_topic_and_actions && ! grep -n "experience_priority" claude/meta-skill/knowledge/product-intent-confirmation.md | grep -v "experience_priority.mode" | grep -q . && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

Write set: `claude/meta-skill/knowledge/product-intent-confirmation.md`, `test_experience_direction.py`.

## T-M2-10 Backward compatibility proof and module regression

Requirements: R-M2-09, R-M2-10.

Behaviour: a concept and journal produced before this module read without drift, and the whole module passes
its design acceptance. Any defect found here is fixed inside the write set without weakening a test.

Test intent: case 12 `test_pre_existing_concept_and_journal_read_without_drift`: after `draft`, delete
`gap-experience-direction` from the concept file (a pre-module concept), run confirm/freeze/plan, and assert all
three gates exit 0; `resume` output has no `experience_proposals` key and no topic entry has `proposals`;
`resume` and `--delegations` leave `CONCEPT`/`JOURNAL` byte-identical; no item carries `proposal_id` or
`auto_decided`. The remaining commands are the design's module acceptance: the full new file, the ten
product-intent regression files (baseline 172 passed before this module; all must pass), the run-logging
regression, the one mirror-driven `test_evidence_freshness.py` test selected by node id (its two known failures
are not selected), and the contract validator.

Acceptance:
```
python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py::test_pre_existing_concept_and_journal_read_without_drift && python3 -m pytest -q claude/meta-skill/tests/unit/test_experience_direction.py && python3 -m pytest -q claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_product_intent_resume.py claude/meta-skill/tests/unit/test_freeze_idempotence.py claude/meta-skill/tests/unit/test_product_question_identity.py claude/meta-skill/tests/unit/test_product_retained_scope.py claude/meta-skill/tests/unit/test_intent_review_corrections.py claude/meta-skill/tests/unit/test_legacy_profile_authority.py claude/meta-skill/tests/unit/test_legacy_projection_authority.py claude/meta-skill/tests/unit/test_local_reopen_scope.py claude/meta-skill/tests/unit/test_acceptance_allocation.py claude/meta-skill/tests/unit/test_run_logging.py claude/meta-skill/tests/unit/test_evidence_freshness.py::test_selected_intent_payload_drift_in_real_producer_baseline_is_stale && python3 claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py
```

Write set: `test_experience_direction.py`, `product_intent.py` (fixes only).

---

## Requirement coverage

| Requirement | Tasks |
|---|---|
| R-M2-01 | T-M2-01, T-M2-07 (headless exclusion), T-M2-09 |
| R-M2-02 | T-M2-02 |
| R-M2-03 | T-M2-02, T-M2-03 |
| R-M2-04 | T-M2-04 |
| R-M2-05 | T-M2-05 |
| R-M2-06 | T-M2-07 |
| R-M2-07 | T-M2-06, T-M2-08 |
| R-M2-08 | T-M2-09 |
| R-M2-09 | T-M2-01, T-M2-03, T-M2-10 |
| R-M2-10 | T-M2-01 … T-M2-10 |

## Interface ownership

| Interface | Task |
|---|---|
| `data:experienceProposals` | T-M2-02 |
| `api:productIntentPropose` | T-M2-02 |
| `api:productIntentSelect` | T-M2-04 |
| `data:experienceDirectionIntent` | T-M2-04 |
| `api:productIntentDelegate` | T-M2-05 |
| `data:delegationDisclosure` | T-M2-06 |
| consumes `data:experiencePriority` | T-M2-04, T-M2-07 |
