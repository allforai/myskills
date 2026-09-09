# T15 planning-gate corrections — spec-review findings 3 and 4

Scope: the two planning-only findings in `T15-2cc347af-spec-review.md`.

- **Finding 4 — "Delta rule has no baseline."** Step 3.4 presented a node list in chat and
  nothing persisted it, so Phase A's post-confirmation delta rule had nothing to diff, and
  `/run` gating keyed on the three lenses plus the node-spec audit rather than on delta
  acceptance.
- **Finding 3 — "New blocker codes are prose only."** `undeclared_repair_loop_routing`,
  `unowned_effect_stage` and `missing_document_contract` existed only in
  `bootstrap-node-expansion-qa/SKILL.md`; no validator, no fixture.

Base: `2cc347af`, working tree shared with the decision and runtime editors. No commits.

## Finding 4 — the confirmed plan is now a record, and both boundaries judge it

### The contract

`.allforai/bootstrap/plan-confirmation.json` holds the graph actually presented, revision by
revision:

```json
{"schema_version": "1.0", "confirmations": [
  {"revision": 1, "stage": "step-3.4", "presented_at": "<iso8601>",
   "plan": {"<node_id>": ["<hard_blocked_by node ids>"]},
   "confirmation": {"source": "user",
                    "reference": ".allforai/bootstrap/plan-confirmation-journal.json#<batch>/decisions/<i>",
                    "reason": "<what the user was shown and why they accepted it>"}},
  {"revision": 2, "stage": "phase-a-delta", "plan": {"...": []},
   "delta": {"added": [], "removed": [], "rewired": []}, "confirmation": {"...": "..."}}]}
```

**Provenance is resolved, not asserted.** The reference selects one decision in
`.allforai/bootstrap/plan-confirmation-journal.json` — a schema-1.0 journal in the same
batch/decision shape as the product decision journal — and is verified by the contract the
gates already enforce, `product_intent._journal_decision`: a `user_session` batch, an
explicit `question`/`chosen`, not pending, not removed, not superseded, inside the project.
The decision's `intent` must be `{"plan": <the presented graph>}`, so the reference binds the
user's recorded choice to that exact node set and those exact edges. A product-journal
reference is accepted when the plan was genuinely confirmed there; planning never writes the
product decision journal for a plan or run choice (per root, and because the corpus asserts a
run-policy flow creates no product journal). `source: "user"` over free text, an
`approved: true` flag and an empty file are all refused.

**Malformed graphs are refused, not repaired.** `_plan_shape_errors` rejects a null, a string,
a mixed or blank edge list, a repeated edge and an edge pointing outside the recorded plan,
in both the record and the referenced decision's `intent`, before any comparison. Sanitizing
those into `[]` would let a malformed record compare equal to a valid plan and become
authority (root's read-only probe, msg_46b660104827).

**History is append-only.** Revisions are numbered in order and never renumbered; a later
revision records the next graph and does not supersede the earlier one, so earlier history
stays valid and unchanged nodes are never re-confirmed. Supersession is how a confirmation is
*retracted*, and a retracted revision invalidates the chain from that point. A revision whose
plan equals the previous one is not a revision; a revision whose declared `delta` differs from
the recomputed one is refused.

**Completed work.** An unrecorded plan is demanded of the nodes that have yet to execute, so
legitimate finished history is left alone. Completion is never an exemption from a *change*:
a node added or re-wired after the confirmed revision is reported even once it is marked
complete, or mutating and then completing a record would license any graph change after the fact.

### Where it is enforced

`plan_confirmation_findings(bdir)` produces typed findings; `validate_plan_confirmation` renders
them for the bootstrap validator CLI, and `plan_confirmation_blockers(project_root)` returns
`{code, message, node_id}` blockers in the readiness report's own shape.

- `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py` — the bootstrap gate, also the
  gate the Codex flow already runs (`flow-template.py`).
- `claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py` — two lines (import
  + `blockers.extend(plan_confirmation_blockers(project_root))`), added under root's explicit
  authorization in msg_1981b0041a79, so `/run` does not assume bootstrap ran and passed.

Codes, all routed back to interactive `/bootstrap` Phase A in their message text:
`unconfirmed_plan` (no record covering unfinished work), `invalid_plan_confirmation`
(unresolvable provenance, malformed recorded graph, rewritten or misstated history),
`unconfirmed_plan_delta` (bound to each node added or re-wired since the confirmed revision;
removals reported once).

A malformed workflow root reaches the readiness gate directly, so the new checks fail closed
rather than raising — caught by the existing corpus (`malformed_workflow` parametrization) and
fixed.

## Finding 3 — the three codes, split into what a gate can decide and what it cannot

The task's instruction was to separate structured enforceable contracts from semantic Task
prose. The split is now stated in `bootstrap-node-expansion-qa/SKILL.md` as a table, and the
left column is enforced at the public bootstrap gate:

| Code | Enforced structurally (new) | Left to the audit's judgment (labelled) |
|---|---|---|
| `undeclared_repair_loop_routing` | A declared `required_repair_loops` entry with no `qa_node_ids` (nothing routes into the repair), no `closure_node_ids` (nothing waits for the QA rerun), a repair node listed as its own QA or closure node, or a closure node whose `hard_blocked_by` omits the loop's QA node (it would close on the repair alone). Complements `validate_unattended_readiness.py`, which checks the opposite direction | Whether a graph shape *is* a QA loop that needs declaring at all. A repair node's other `hard_blocked_by` edges are legitimate data dependencies, so "an undeclared edge" is not a sound structural signal and no such rule was added |
| `unowned_effect_stage` | The new optional `downstream_effect_owner` field (workflow + node-spec frontmatter, mirrored): the named node must exist, not be the node itself, run after it through `hard_blocked_by`, and carry its own `## Effect Verification`; declared on one side only is refused | Whether a node's Effect Verification demands proof its own stage cannot produce, so a deferral or a merge was needed at all |
| `missing_document_contract` | A `required_documents` entry with no `document_verification` argv (existing `check_artifacts` contract, now proven at the planning gate) and — new — a document contract declared on the node-spec but absent from the workflow node, which no gate could see before | Whether a node's Task prose promises a document it never declared. **No rule was added making every `documentation` responsibility require a new fact document**: a node may own updates to documents that already exist, and that rule would be a false finding |

## Files

Owned and changed:

- `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py` — plan-confirmation gate,
  repair-loop routing check, effect-owner check, two-directional node-spec contract mirror.
- `claude/meta-skill/knowledge/bootstrap-audits.md` — Phase A: the record's schema, provenance,
  append-only semantics, completed-work rule, and the codes; pre-`/run` gate list.
- `claude/meta-skill/skills/bootstrap/SKILL.md` — Step 3.4 persists the record;
  `downstream_effect_owner` in the CC-superset fields; re-bootstrap preserve list; 6.3 outputs.
- `claude/meta-skill/knowledge/node-spec-template.md` — `downstream_effect_owner` frontmatter.
- `claude/meta-skill/skills/meta-orchestration/40-qa/bootstrap-node-expansion-qa/SKILL.md` —
  the enforced/judged table.
- `codex/meta-skill/skills/bootstrap.md` — same contract on the Codex entry.
- `claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py` — the two
  authorized lines only; the `max_attempts` hunk in that file is the runtime editor's.

Tests: `claude/meta-skill/tests/unit/test_plan_confirmation_gate.py` (new, 34),
`claude/meta-skill/tests/unit/test_planning_audit_contracts.py` (new, 15), plus explicit
`confirm_plan(...)` calls at the scripted plan-presentation step of the existing corpus
(`test_bootstrap_scope.py` and nine files that re-plan through the copied CLI).

Per root's msg_19d9bbd61456 there is **no** implicit confirmation in a generic helper: `write`,
`gate`, `publish_contract` and `invoke` stay raw seams, and `confirm_plan` is called only where
a scripted dialogue presents a plan. Every negative test generates a plan successfully and then
takes the refusal at the public boundaries.

`test_plan_confirmation_gate.py` covers, all through the copied `validate_bootstrap.py` and
`validate_unattended_readiness.py`, each after a plan was generated successfully:

- absent confirmation record → `unconfirmed_plan`, bound to the unfinished node;
- an approval flag, an empty record, an empty plan and a bare boolean → refused;
- fabricated references: free text, an arbitrary file, a missing batch, a missing decision
  index, a path outside the project;
- a batch that is not a confirmed user session, and a *retracted* (superseded) confirmation;
- a decision that records another graph;
- malformed recorded graphs and malformed recorded `intent` graphs — null, string, mixed,
  blank, outside-plan and repeated edges — refused rather than sanitized;
- a node added after the confirmation (holding only that node, not the confirmed one), the
  same node marked completed, a re-wired dependency, and a dropped node;
- the confirmed delta recovering the plan while revision 1 stays byte-identical (append-only
  history accepted), a revision that misstates its delta, a re-confirmation that changes
  nothing, and a renumbered history with a revision removed;
- the two acceptance cases: an exactly confirmed plan passes both boundaries, and finished
  history with no record is left alone.

`test_planning_audit_contracts.py` covers the three blocker codes: a fully declared loop
accepted; loops with no QA source, no closure holder, a repair node as its own QA or closure,
and a closure that never waits for the QA rerun; a correct effect deferral accepted; effect
owners that are empty, missing, the node itself, a parallel sibling, one whose spec has no
Effect Verification, and one declared on the node-spec alone; a promised document without its
verification argv (then accepted once mapped); and a document contract declared only on the
node-spec.

## Verification

Commands, from `claude/meta-skill` unless noted, `python3 -B`, `--tb=line`:

- `python3 -B -m pytest tests/unit -q` → **746 passed** (4m39s).
- `codex/meta-skill`: `python3 -B -m pytest test_flow.py test_install.py -q` → **105 passed**.
- repo root: `python3 -B -m pytest shared/scripts/orchestrator -q` → **122 passed**.
- repo root: `python3 -B claude/meta-skill/scripts/orchestrator/validate_meta_contracts.py` → exit 0.

Red baseline, in a scratch copy of the tree with only `validate_bootstrap.py` and
`validate_unattended_readiness.py` reset to `2cc347af`: the two new files are **44 failed,
5 passed**. The 5 that pass at HEAD are the acceptance cases that must pass on both sides
(`test_a_confirmed_plan_passes_both_public_boundaries`,
`test_finished_history_without_a_record_is_left_alone`,
`test_a_fully_declared_repair_loop_is_accepted`,
`test_a_deferred_effect_needs_a_downstream_owner_that_proves_it`) plus
`test_a_promised_document_needs_its_verification_argv`, whose mapping direction was already
enforced through `check_artifacts.document_verification_errors`.

## Honest residuals

1. **No host retest.** Everything here is copied-CLI seam evidence in temporary projects. The
   semantic half of all three audit codes — is this shape a QA loop, did this node need to
   defer its effect, does this Task promise a document — remains LLM-dependent and unproven
   until an actual host run. The real-host campaign fixtures and candidate exports were not
   touched and no host pass is claimed.
2. **Enforcement trigger.** The plan-confirmation gate applies to any workflow whose
   `bootstrap-profile.json` declares a canonical `task_route`. A plan with no profile at all is
   a legacy input whose provenance `validate_scope` already reports; that is the same trust
   boundary the existing scope gate uses, not a new hole, but it is a boundary.
3. **`check_decision_inputs.py` and the planning journal.** The planning journal is a distinct
   file from the product decision journal, so the decision-input gate's orphan rule does not
   see it today. If that gate is ever taught to classify journals by shape rather than path, it
   must count the plan-confirmation record as the planning journal's consumer. Decision-owner
   territory; flagged, not touched.
4. **`shared/scripts/orchestrator/validate_bootstrap.py`** is a much older, already divergent
   copy at `2cc347af` (1406 differing lines before this change) and was left alone. Pre-existing
   drift, already flagged by another worker for `check_decision_inputs.py`.
5. **Repair-loop freshness interaction (msg_f517881f7c44).** The runtime worker reproduced a
   real contradiction: the loop requires `repair.hard_blocked_by = [qa]`, while
   `evidence_freshness` treats every `hard_blocked_by` edge as an evidence dependency, so a
   failing QA node makes the repair unable to publish and therefore unable to complete. As
   planning-contract owner I answered (msg_af9c261fd10a): take the driver-side signal — count
   the attempt by the repair's delivery of its own declared `exit_artifacts`, transition still
   failed, node still incomplete — and do **not** fork the meaning of `hard_blocked_by` inside
   `evidence_freshness`. The planning contracts are unchanged for it: repair `hard_blocked_by`
   its QA node, closure `hard_blocked_by` both the repair and every QA node in the loop.
6. `T15-acceptance-allocation-analysis.md` was read as unresolved context only; no scope was
   expanded from it, no requirement acceptance equality or stage coverage was loosened, and no
   pending user choice was made.
