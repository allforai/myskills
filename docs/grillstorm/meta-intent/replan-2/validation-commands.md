# Current implementation validation commands

The approved execution protocol is `implement`; `execution.json` records its
current DAG. The original `../tasks/` catalog and frozen ticket documents are
historical artifacts, not executable dispatch instructions for this revision.
Their proposed `test_bootstrap_resume.py` and `test_bootstrap_freshness.py` names
were not the final test organization. Preserve those original artifacts and
fingerprints; use this map for the delivered implementation instead.

Run from the development checkout root:

| Coverage | Command |
|---|---|
| #11 confirmation resume and legacy admission | `python3 -m pytest claude/meta-skill/tests/unit/test_product_intent_resume.py -q` |
| #11 once-per-session Run Policy | `python3 -m pytest claude/meta-skill/tests/unit/test_run_policy_session.py -q` |
| #11 independent review regressions | `python3 -m pytest claude/meta-skill/tests/unit/test_intent_review_corrections.py -q` |
| #11 local reopen isolation and recovery | `python3 -m pytest claude/meta-skill/tests/unit/test_local_reopen_scope.py -q` |
| #12 input drift, publication races and Git containment | `python3 -m pytest claude/meta-skill/tests/unit/test_evidence_freshness.py -q` |
| #12 dynamically read and globbed producer dependencies | `python3 -m pytest claude/meta-skill/tests/unit/test_dynamic_input_dependencies.py -q` |
| #12 local baseline provenance | `python3 -m pytest claude/meta-skill/tests/unit/test_local_freshness_provenance.py -q` |
| #12 declaration admission and malformed inputs | `python3 -m pytest claude/meta-skill/tests/unit/test_freshness_admission_corrections.py -q` |
| #12 diagnostic provenance status | `python3 -m pytest claude/meta-skill/tests/unit/test_freshness_diagnostic.py -q` |
| #12 declaration downgrade and legacy boundary | `python3 -m pytest claude/meta-skill/tests/unit/test_freshness_downgrade.py -q` |
| #12 CLI target-root resolution | `python3 -m pytest claude/meta-skill/tests/unit/test_gate_project_root.py -q` |

These suites exercise copied public helpers for both adapters. They are not
real Claude/Codex dialogue evidence and cannot discharge #15–#18 or any cell of
the 60-cell scenario matrix. Review reports preserve their original findings;
correction reports and independent rechecks establish resolutions separately.

Standards-review disposition: the Codex helper inventory omission is corrected
in `codex/meta-skill/AGENTS.md`. The historical command-name finding is addressed
by this current command map, not by rewriting the frozen past. The numbered
observation/publication messages in `knowledge/input-freshness.md` specify the
public API lifecycle and its invariants; they do not prescribe product design
choices or a fixed workflow graph.
