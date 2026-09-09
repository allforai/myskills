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
| #11 legacy projection authorization boundary | `python3 -m pytest claude/meta-skill/tests/unit/test_legacy_projection_authority.py -q` |
| #11/#12 unchanged scope freeze idempotence | `python3 -m pytest claude/meta-skill/tests/unit/test_freeze_idempotence.py -q` |
| #12 input drift, publication races and Git containment | `python3 -m pytest claude/meta-skill/tests/unit/test_evidence_freshness.py -q` |
| #12 dynamically read and globbed producer dependencies | `python3 -m pytest claude/meta-skill/tests/unit/test_dynamic_input_dependencies.py -q` |
| #12 local baseline provenance | `python3 -m pytest claude/meta-skill/tests/unit/test_local_freshness_provenance.py -q` |
| #12 declaration admission and malformed inputs | `python3 -m pytest claude/meta-skill/tests/unit/test_freshness_admission_corrections.py -q` |
| #12 diagnostic provenance status | `python3 -m pytest claude/meta-skill/tests/unit/test_freshness_diagnostic.py -q` |
| #12 declaration downgrade and legacy boundary | `python3 -m pytest claude/meta-skill/tests/unit/test_freshness_downgrade.py -q` |
| #12 CLI target-root resolution | `python3 -m pytest claude/meta-skill/tests/unit/test_gate_project_root.py -q` |
| #12 corrupt dynamic-read register and recovery | `python3 -m pytest claude/meta-skill/tests/unit/test_corrupt_freshness_reads.py -q` |
| #13 implementation, document sync and re-acceptance closure | `python3 -m pytest claude/meta-skill/tests/unit/test_delivery_closure.py -q` |

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

## T15 packet preparation (not host proof)

`python3 -m pytest docs/grillstorm/meta-intent/replan-2/T15 -q` checks only packet
export and evidence-capture helpers. The exporter now requires an explicit
`--candidate <commit>` and resolves it once to a full Git commit before creating
the destination. Both manifest commit fields identify that exported commit;
they do not assert implementation acceptance. Use the coordinator-accepted
candidate for actual actors, not a stale installation or the former hardcoded
`88e7beca` preparation snapshot.

Root TDD for this correction: the new CLI test first failed because omitting
the candidate silently exported the old version; after the correction, all 3
export tests passed in 34.29s. Export tests verify source bytes, manifest
identity, executable mode and symlink targets, and still report `executed: 0`.
No scenario input or evaluator criterion was changed.
The complete preparation-only suite after the exporter change passed:
**17 passed in 35.68s**. It still does not execute any actor.
