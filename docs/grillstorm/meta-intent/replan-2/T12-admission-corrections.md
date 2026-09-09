# T12 admission corrections (#12 review blockers 1 and 5)

Worker checkout `/Users/aa/orca/workspaces/myskills/meta-intent-t12`, starting HEAD
`5cab4f8f`, uncommitted. Corrects the two #12 blockers from
`T11-T12-spec-review.md`: freshness was opt-in (blocker 1) and a malformed
declaration crashed the readiness and reconciliation gates (blocker 5).
`evidence_freshness.py`, `product_intent.py` and the dynamic-dependency tests
were not touched; they belong to root and the other worker.

## Rule now enforced by the copied public gates

A node is **intent-aware** when it carries non-empty `requirement_refs` and its
latest transition is not `completed`. Every intent-aware node must declare
`source_inputs`: a list of project-relative files, directories or globs, or an
explicit `[]` when no product source is relevant. `input_dependencies` and
`required_documents` follow the same shape when present. Absolute paths, `..`,
non-list values, empty strings and non-string entries are malformed.

Admission is computed once, in `check_artifacts.freshness_states`, and consumed
by all four gates:

| Admission | Meaning | bootstrap validator | readiness | check_artifacts | reconciliation |
|---|---|---|---|---|---|
| `declared` | `source_inputs` present and well-formed | passes shape | `stale_evidence` unless published and current | `all_exist` only when `valid` | `input_freshness` when not valid |
| `missing` | intent-aware node without `source_inputs`, or partial declaration | error naming node and field | blocker `missing_source_inputs` with `node_id` | `all_exist: false`, freshness `undeclared` | blocked, `missing_source_inputs` |
| `invalid` | malformed declaration on any field | error naming node and field | blocker `invalid_source_inputs` with `node_id`; report still written | `all_exist: false`, freshness `invalid` with reason | blocked, `invalid_source_inputs` |
| `legacy` | retained completed node with no declaration and no record | unchanged | warning `undeclared_source_inputs` | `all_exist` from artifacts, freshness `undeclared` | kept, freshness `undeclared` |

A malformed declaration anywhere withdraws verification from every declared node
in the workflow (`Freshness cannot be evaluated: malformed declaration on …`),
because the owned-input set is unknown and "uncertain" cannot be computed. If
`evaluate` itself raises, the same fail-closed `invalid` state is reported
rather than a traceback. A workflow with no declarations and no freshness state
keeps the pre-#12 gate behavior with `freshness: null`.

Legacy compatibility is deliberate and narrow: only retained completed nodes are
`legacy`, they are reported as `undeclared` (never `valid`), and reopening one
turns it back into intent-aware work that must declare. No provenance is
invented for old reports. Automatic whole-repository ownership is not offered;
the template guidance says not to declare the repository to silence drift.

## Files

Gates (owned): `check_artifacts.py` (admission policy, `freshness_states`,
`freshness_admits`, `input_declaration_errors`), `validate_bootstrap.py`
(shape and missing-declaration errors in `validate_workflow`),
`validate_unattended_readiness.py` (typed blockers/warnings, runs only on a
well-formed node list), `reconcile_bootstrap_workflow.py` (typed artifact and
plan reasons, including the no-candidate branch).

Templates: `skills/bootstrap/SKILL.md` (workflow example plus field guidance),
`knowledge/node-spec-template.md`, `knowledge/bootstrap-planning.md`,
`knowledge/orchestrator-template.md`, `knowledge/input-freshness.md`,
`codex/meta-skill/knowledge/orchestrator-template.md`,
`codex/meta-skill/skills/bootstrap.md`. Each names `source_inputs` and the
explicit-`[]` rule; a doc test pins that.

Tests: new `tests/unit/test_freshness_admission_corrections.py` (both host
adapter copies): review probe P4 replayed end to end (undeclared node rejected
at every gate, declared and published node admitted, later source edit traced
as stale), probe P3 replayed across nine malformed shapes and three fields, a
malformed sibling withdrawing a valid node's verification, retained legacy node
kept with a warning then refused after reopening, legacy workflow untouched, and
template declaration presence.

Shared fixture `test_bootstrap_scope.project()` now declares `source_inputs`
and publishes a verified contract through the copied freshness CLI (new
`publish_contract` helper; the verifier is the copied bootstrap validator, or a
workflow-shape check while a requirement is still pending). Existing tests that
change a consumed requirement or add a scoped node republish accordingly
(`test_journal_backed…`, `test_new_unscoped_work…`). `test_evidence_freshness.setup`
opts out of the fixture declaration with `source_inputs=None` so root's
scenarios keep building their own state; that is the only line changed there.

## Validation

TDD order: the new file was written first and failed on HEAD exactly as the
review probes did (`validate_bootstrap` rc 0 with no `source_inputs`; readiness
and reconciliation `TypeError` on `source_inputs: "orders.py"`), then the gates
were changed until it passed, then the shared fixture and dependent tests were
brought onto the enforced rule.

Commands and results in this checkout (other workers' uncommitted changes to
`evidence_freshness.py`, `product_intent.py` and their tests were present in
the tree at the same time; see the shared `git status`):

| Command | Result |
|---|---|
| `python3 -m pytest claude/meta-skill/tests/unit/test_freshness_admission_corrections.py -q` | 32 passed |
| `python3 -m pytest claude/meta-skill/tests/unit/test_bootstrap_scope.py claude/meta-skill/tests/unit/test_freshness_admission_corrections.py claude/meta-skill/tests/unit/test_product_intent_session.py claude/meta-skill/tests/unit/test_product_intent_resume.py claude/meta-skill/tests/unit/test_product_retained_scope.py claude/meta-skill/tests/unit/test_product_question_identity.py claude/meta-skill/tests/unit/test_run_policy_session.py claude/meta-skill/tests/unit/test_expand_game_2d_production.py claude/meta-skill/tests/unit/test_validate_bootstrap.py claude/meta-skill/tests/unit/test_check_artifacts.py claude/meta-skill/tests/unit/test_reconcile_bootstrap_workflow.py claude/meta-skill/tests/unit/test_validate_unattended_readiness.py -q` | 175 passed (145 with the malformed-workflow cases deselected, plus those 30 run separately) |
| `python3 -m pytest claude/meta-skill/tests/unit/test_run_policy_session.py -q` | 20 passed |
| `python3 -m pytest claude/meta-skill/tests/unit/test_evidence_freshness.py claude/meta-skill/tests/unit/test_dynamic_input_dependencies.py -q` | passed inside the 208-test scope/freshness run after the fixture opt-out |
| `node --test claude/meta-skill/knowledge/run-engine/tests/*.test.js` | 55 pass, 0 fail (no JS changed) |
| `uvx mypy --follow-imports=silent --check-untyped-defs --ignore-missing-imports` on the four gates | 11 errors, all pre-existing (ten `validate_bootstrap` annotations, one readiness nullable assignment); none in new code |
| `git diff --check` | clean |
| `python3 -m pytest claude/meta-skill/tests -q` | 439 passed in 105s (tree included other workers' uncommitted tests at that moment; root reruns before commit) |

Root runs the final full suite and commits; this report does not claim that.

## Limits and coordination

- Copied-CLI tests in temporary projects, not Claude or Codex host-dialogue proof.
- Root's `evidence_freshness.evaluate` still reports a retained legacy node as
  `stale` on the diagnostic `check` CLI, while the gates report `undeclared`.
  Shared API ask for root: have `evaluate` emit `undeclared` for a node with no
  declaration and no record so the diagnostic and the gates agree.
- `product_intent.plan` still copies whatever the planner sends; the gates now
  refuse a planned intent-aware node without `source_inputs`, so the other
  worker may want `plan` to reject the omission earlier with the same message.
- `_completed_nodes` mirrors `product_intent._retained_nodes` log folding for
  both native formats; it is duplicated rather than imported to keep
  `check_artifacts.py` dependency-free.
- Typecheck of the four gates reports only the eleven pre-existing errors
  recorded in `reviews/T12-replan2-implementation.md`; no new ones.
- No commit, stage, push, install or issue action was taken.
