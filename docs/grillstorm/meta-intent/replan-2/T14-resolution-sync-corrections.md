# T14 corrections — a decision outlives the verdict that prompted it (#14)

Base `9bade2ff`. Fixes the spec re-review's major (`T14-9bade-spec.md`) and the standards
re-review's documented-standard violation (`T14-9bade-standards.md`). Evidence is
copied-CLI in temporary projects on both host adapters (`HOSTS = ["claude", "codex"]`);
**no real Claude/Codex host dialogue proof is claimed** — #14 stands at 0/16 and the whole
#8 T15–T18 matrix at 0/60. Source edits were made with this harness's structured editing
tool; no `apply_patch` binary exists on this machine.

## The two defects

1. **A decided change reappeared as unknown drift.** `classification_basis` digested the
   whole `source_tree`, which — unlike `inventory` — counts the flow's own
   `exit_artifacts` and `required_documents`. `routed_external_changes` then grouped on
   `classification` alone and never consulted `change['resolution']`. So any project file
   moving dropped the standing verdict, and a change the user had already settled fell into
   the *unverified* group: the accept recovery ended `not_ready` at the point `11f9a44c`
   reached `ready`, a rejection lost its scoped `external_change_repair_pending`, a defer
   lost its "deferred (product-conflict)" context, and a verified `fact-update` was
   re-raised as unverified by the very document its own verdict told the flow to write.
2. **`undetermined_external_change` was undocumented.** Both `orchestrator-template.md`
   files enumerate the external-change blockers exhaustively ("All three…"), and this code
   emits a fourth. `input-freshness.md`'s outcome list omitted it too. Behaviour already
   failed closed through the generic not-ready rule, so this is an instruction correction.

## The separation

A verdict and a decision were being read as one thing. They are now distinct:

- **An undecided verdict** stands only while the basis it was established against does —
  unchanged.
- **A decided change** is routed by the decision, whatever a verdict currently says: an
  accepted one stops holding work, a rejected one keeps its scoped repair, a deferred one
  keeps its hold, and each keeps the finding it was decided against so the report still
  says what was found. Only revised confirmed intent retires a decision, through
  `carried_resolution` exactly as before.
- **The basis is what the flow consumes, not what it produces** (`inventory`, not
  `source_tree`). A verdict prescribes its own recovery — resynchronize the required
  documents and republish — so obeying it cannot invalidate it. `resolve_external_changes`
  still measures the whole `source_tree` for its "the acceptance moved its own subject"
  guard, which is unchanged.

Nothing was disabled: true source movement still drops an undecided verdict, changed
product intent is still never adopted, no stale acceptance is replayed for an undecided
change, and no user is sent back through an interview.

## Red → green

RED was captured at `9bade2ff` before any source edit, in this checkout, with
`pytest --tb=line`.

| Public-CLI regression (both adapters) | 9bade2ff | now |
|---|---|---|
| `test_an_accepted_change_recovers_once_its_required_document_is_synchronized` | fail | pass |
| `test_a_rejected_change_keeps_its_scoped_repair_while_other_documents_move` | fail | pass |
| `test_a_deferred_change_keeps_its_hold_and_its_context_while_other_source_moves` | fail | pass |
| `test_a_verified_fact_update_survives_synchronizing_the_document_it_requires` | fail | pass |

RED total: **8 failed, 34 deselected**. Each failed on the defect, not on setup: three
reported the spurious `unverified_external_change` blocker on `deliver-export`, and the
rejected/deferred pair reported the scoped blocker missing entirely.

Implemented in two slices — the decision-routing behavior first (accept, reject and defer
went green; the fact-update case stayed red), then the basis narrowing.

The accept regression drives the real recovery end to end: accept with explicit intent
`actions`, write the delivery's actual `required_documents` file, refreeze to v2, replan,
publish the contract, reach `ready` with **no** extra `external-changes` call, republish
evidence, and confirm exactly one `External source change` journal batch — the user is
asked once.

Prior defect tests are retained untouched and still pass:
`test_an_unwritable_store_keeps_the_conflict_it_could_not_record`,
`test_a_verdict_is_re_established_by_verifying_again_not_repeated_from_the_record`,
`test_a_classification_is_not_reused_once_the_source_it_was_established_against_moves`,
`test_a_gate_never_runs_project_acceptance_over_an_out_of_flow_edit`,
`test_drift_reaches_the_gates_as_unverified_and_verification_routes_it_to_its_owner`,
`test_unreadable_freshness_state_cannot_report_or_decide_external_changes`.

## Validation

| Command | Result |
|---|---|
| `pytest claude/meta-skill/tests/unit/{test_external_change_recovery,test_freshness_downgrade,test_corrupt_freshness_reads}.py -q` | 116 passed |
| `pytest claude/meta-skill/tests -q` | 647 passed (4:02) — 639 at `9bade2ff` plus the 8 new |
| `pytest codex/meta-skill/test_flow.py codex/meta-skill/test_install.py -q` | 35 passed |
| `node --test claude/meta-skill/knowledge/run-engine/tests/*.test.js` | 55 pass, 0 fail |
| `uvx mypy --ignore-missing-imports` on `evidence_freshness.py`, `validate_unattended_readiness.py`, `product_intent.py` | Success: no issues found in 3 source files |

The repository's own pre-commit hook is the final-state verification for this commit.

## Remaining limits

- A basis still cannot observe an installed dependency, a service or the environment. That
  residual is unchanged from `9bade2ff`: a memo can outlive the truth at the passive gates
  until someone re-runs the verification, bounded by publication re-executing the
  acceptance and by `external-changes` always verifying afresh.
- A verdict whose decision was **superseded** by revised confirmed intent is undecided
  again, so it follows the undecided rule: if project source also moved, it reaches the
  gates as `unverified_external_change` rather than as a reopened conflict. It still
  blocks, and re-running `external-changes` restores the conflict wording. Narrowing this
  further would require re-verifying inside a passive gate, which is exactly what
  `9bade2ff` forbade.
- The basis now moves when replanning changes which paths count as generated. That only
  ever drops an undecided verdict to unverified — fail-closed, never a replay.
- Copied-CLI only. Real host proof for #14 remains 0/16, and 0/60 across T15–T18.

## Files

`claude/meta-skill/scripts/orchestrator/evidence_freshness.py` (the `codex/` scripts tree
is a symlink to `claude/`, so both adapters move together);
`claude/meta-skill/knowledge/input-freshness.md`, both `orchestrator-template.md`;
`claude/meta-skill/tests/unit/test_external_change_recovery.py`.
`docs/grillstorm/meta-intent/replan-2/execution.json` is coordinator-owned and was neither
modified nor staged; the existing T14 review reports are untouched.

Final state: this commit, whose parent is `9bade2ff`.
