# T11 local-change reopen corrections (#11 node scoping on the local route)

Base: the current uncommitted T12 correction tree in this checkout (HEAD `5cab4f8f`
plus the peer edits listed by `git status`). Owned files: the shared
`claude/meta-skill/scripts/orchestrator/product_intent.py` (the Codex adapter reaches
it through the `codex/meta-skill/scripts` symlink), the new public regression file
`claude/meta-skill/tests/unit/test_local_reopen_scope.py` (visible to both hosts
through the `codex/meta-skill/tests` symlink), and this report. No other source or
test was edited. No staging, commit, reset, push, install or issue mutation. These
are copied-CLI seam tests in temporary projects, not host-dialogue proof.

## Finding: a reopened local intent blocked the whole plan

`T11-spec-corrections.md` bound per-intent drift to consuming nodes on the product
route only and recorded that the local-change route still raised globally
(`Local scope selects stale intent`, `Local projection differs from the confirmed
scope`, `Local work depends on an unresolved decision`). The #11 criterion does not
exempt the local route: an unresolved dependency keeps its dependent work
unexecutable while unrelated work is not invalidated merely because of that question.

Reproduced through the copied `product_intent.py` CLI on both host copies with the
actual operations: `admit` two disjoint local intents (`export`, `archive`) and a
question `retention` that depends on `archive`; `decide` confirm both and answer the
question; `freeze` both; `plan` `node-a` (export) and `node-b` (archive); publish both
contracts through the copied freshness CLI; all three gates ready. Reopening `archive`
or `retention` then produced one global `invalid_scope` blocker without `node_id` on
every gate, so `node-a` was invalidated too.

## Change

`validate_scope` now sends the local route through `_local_contract`, which has the
same two levels as `_product_contract`:

- Freeze-level problems still raise and surface as one global `invalid_scope`:
  unverifiable journal provenance of the frozen local scope (`_discussion` keeps
  checking the freeze batch, including a later user decision that supersedes it),
  a task scope whose refs differ from the frozen refs, and a frozen scope whose
  intents do not match its refs.
- Per-intent drift is bound to consumers through the shared `_intent_drift`
  helper, extracted unchanged in logic from `_product_contract` and parametrised by
  label (`Product` / `Local`) and requirement path: a reopened intent (latest
  revision pending) is `pending_requirement`; an adjusted, removed, restored or
  silently changed one is `stale_requirement`; a journal choice that no longer
  verifies is `pending_requirement` with its reason; a pending question an included
  intent depends on is `pending_requirement` naming the unresolved decision; a node
  consuming an excluded intent is `scope_requirement_unwired`; a node whose goals or
  acceptance no longer equal the confirmed intent is `stale_requirement` for that
  node. Retained completed nodes stay exempt exactly as before.

The shared per-reference loop in `validate_scope` was already scoped by the prior
correction; the local route now reaches it as the product route does. Its journal
structure checks and the superseded-decision check keep raising globally because the
existing `test_forged_journal_reference_cannot_authorize_local_requirement` contract
asserts `invalid_scope` for them; those tests are not mine to change.

Product-route behavior is unchanged: codes, `node_id` binding and message text
(`Product intent …`) are the same strings the existing product tests read.

## Regression file

`test_local_reopen_scope.py`, both hosts:

- Reopening `archive` or `retention`: readiness `not_ready`, every blocker carries
  `node_id: node-b`, `pending_requirement` present, no `invalid_scope`;
  `validate_bootstrap` and `check_decision_inputs` name `node-b` and never `node-a`;
  refreeze and replan are refused while pending. After the user confirms or answers,
  refreeze (scope version 2) plus replan plus actual republication of `node-b` alone
  returns all gates to ready; `node-a`'s Node-spec bytes and contract are unchanged
  (freshness binds each node to its own requirement ids, so `node-a` never needed
  reverification).
- Forged status on the reopened revision, a silent acceptance edit of the confirmed
  revision, and a silently appended revision each block `node-b` only with
  `stale_requirement`.
- A missing freeze batch, a task scope differing from the frozen refs, and a later
  user decision superseding the frozen scope each stay a single global
  `invalid_scope` without `node_id`.

## TDD and validation

1. Wrote the regression file first and ran it against the unmodified helper:
   **10 failed, 4 passed** (the four freeze-level global cases were already correct).
2. Implemented `_local_contract` and the `_intent_drift` extraction.
3. `python3 -m pytest claude/meta-skill/tests/unit/test_local_reopen_scope.py -q`:
   **16 passed** on both host copies.
4. `uvx mypy --follow-imports=silent --check-untyped-defs claude/meta-skill/scripts/orchestrator/product_intent.py`:
   no issues. `git diff --check` on the helper: clean.
5. Related suites (`test_bootstrap_scope`, `test_intent_review_corrections`,
   `test_product_intent_session`, `test_product_intent_resume`,
   `test_product_retained_scope`, `test_product_question_identity`,
   `test_run_policy_session`, `test_local_freshness_provenance`,
   `test_evidence_freshness`, `test_dynamic_input_dependencies`,
   `test_freshness_admission_corrections`): **332 passed, 2 failed** on the first run
   and 4 failed when the failing test was rerun alone. The failures are
   `test_invalid_history_replaces_ready_report_and_corrected_history_reenters`
   (`number-history`, `array-node-id`, both hosts): the readiness gate prints a
   traceback from the transition-log folding in the peer's uncommitted
   `check_artifacts.py` (`for event in workflow.get("transition_log") or []`,
   `TypeError`) before scope rejection is reported. Attribution: the same four
   cases fail identically in a scratch copy of the tree with HEAD's
   `product_intent.py` substituted, so this change neither causes nor hides them.
   The gate worker owns that file.
6. `node --test claude/meta-skill/knowledge/run-engine/tests/*.test.js`: 55 pass, 0 fail
   (no JS changed).
7. Worker-run full test `python3 -m pytest claude/meta-skill/tests -q` on the live tree with
   every peer edit present: **480 passed, 4 failed** in 154s; the four failures were
   exactly the attributed transition-log cases above and nothing else. After the gate
   worker's later edit to `check_artifacts.py`, the same test and this regression file
   rerun together: **48 passed** (32 history cases plus the 16 here).
8. Independent recheck (fresh-context agent, read-only, its own reproduction script
   under the session scratchpad, different intent and node names): reproduced the
   admit, decide, freeze, plan, publish, reopen, recover and tamper sequence on both
   host copies; after the reopen the blockers were `pending_requirement`,
   `stale_requirement` and `stale_evidence`, all bound to the consuming node, with no
   `invalid_scope`; recovery returned every gate to ready with the unrelated Node-spec
   bytes unchanged; the journal-pointer tamper gave one global `invalid_scope`. Its
   edge probes (hand-edited acceptance scoped to that node, reopened intent with no
   consumer blocking globally, retained node exempt, excluded-intent node unwired)
   matched intent. Its diff review found no regression and confirmed the product
   route unchanged (`test_intent_review_corrections.py` 30/30). Counts: 62 passed on
   the three intent suites, 352 passed on the wider related suites. It noted, not as
   a blocker: a hand-edited journal decision that supersedes one intent's confirmation
   still reaches the shared per-reference loop's global raise (pre-existing and pinned
   by the forged-journal test, see above); a reopen yields both a `pending_requirement`
   and a `stale_requirement` entry for the same node; the "both hosts" evidence is the
   symlinked script directory, not separately maintained code.

## Remaining

Coordinator attribution correction: the suite in item 7 was run by this worker,
not by the root coordinator. Item 8 used a Claude-native `Agent` subagent outside
the approved Orca task/dispatch graph; its observations are supplemental only,
not formal independent acceptance. It finished before the worker settled and
the worker terminal was released. Root will rerun formal parallel Standards and
Spec reviews through Orca against the committed candidate; no host proof is
credited to the extra recheck.

- Host-dialogue proof for the interactive reopen prompt stays with #16/#17.
- Readiness exit status is global by design of the readiness report; the run
  engines' per-node skipping is not implemented here and was not requested.
- The transition-log traceback in `check_artifacts.py` is a peer item; scope
  validation already rejects the malformed history, so the gate result is still
  `not_ready`, but the traceback on stderr fails the existing test.
