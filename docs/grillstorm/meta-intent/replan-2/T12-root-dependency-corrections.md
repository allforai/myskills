# Root freshness corrections after independent review

Reviewed base: `5cab4f8f1f8e7a31c988df7f26154132d0f86e31`.

## Producer dependencies

The coordinator reproduced a gap through the copied public helper in both
adapters: B read A's report, then A's source changed without changing the report
bytes. A became stale but B stayed valid. Declared globs had the same omission.
The durable dependency set now includes expanded declared inputs, dynamically
registered reads and retained observed inputs. Producer edges cover generated
exit artifacts and required documents. Adding a read cannot silently refresh
inputs already observed; it adds the producer edge and retains the original
observation's other content bindings.

Regression: `test_dynamic_input_dependencies.py` exercises A → B → C alongside
an unrelated branch, for both adapters, dynamic reads/declared globs and artifact/
document producers. Source drift must stale A/B/C, preserve the unrelated branch,
fail the copied completion gate and require each consumer's actual publication
after the producer is repaired. The initial dynamic-read probe failed on both
adapters; after artifact correction, four document cases still failed with B
incorrectly `valid`. After covering document producers all eight cases passed.

Another copied-CLI probe demonstrated premature consumer publication: B could
publish against stale A, then appear valid as soon as A was reverified. Both
adapters returned `valid` where rejection was required. Publication now requires
valid upstream evidence (or upstream contract readiness for contract publication).
Four regression cases cover both kinds on both adapters, including contract
readiness without falsely implying completion. All 12 dependency cases pass.

## Local baseline provenance

Independent Spec finding 3 is reproduced using real copied `admit`, `decide`
and `freeze` operations: local scope version 1 was observed as `null` on both
adapters. Observation now reads the active local `intent_scope`, without writing
the global baseline, and fingerprints the selected local baseline payload too.
Both regression cases changed from `None != 1` failures to passes.

## Targeted validation

- Original freshness suite plus the two new suites initially: 40 passed; after
  adding premature-publication rejection: 42 passed. The expanded dependency
  suite then passed all 12 cases, including the two contract-publication cases.
- `uvx mypy --follow-imports=silent --check-untyped-defs claude/meta-skill/scripts/orchestrator/evidence_freshness.py`: passed.
- These results precede the parallel intent/admission corrections. Combined
  suite and independent delta review remain required before implementation
  acceptance. None is actual Claude/Codex host-dialogue proof.

After the first parallel correction wave, the coordinator ran
`python3 -m pytest claude/meta-skill/tests/unit codex/meta-skill/test_flow.py -q`:
463 passed in 110.09 seconds; the run-engine suite passed all 55 tests. This
precedes the local-reopen and admission-downgrade boundary correction wave and
is not acceptance of those later edits.

The diagnostic CLI now reports never-observed, undeclared input provenance as
`undeclared`, not `stale` or `valid`. Two additional copied-CLI cases reproduced
the previous `stale` result and pass after correction. Diagnostic status alone
does not grant admission; scoped-work gates retain the declaration requirement.

The remaining bootstrap-validator call site now passes the actual project root
derived from its workflow path to admission. Two new public-CLI regressions
ran the same valid project from inside and outside its directory: the outside
invocation previously rejected retained historical work; both now pass without
changing the current-work declaration rule. This resolves the working-directory
limitation recorded in `T12-downgrade-corrections.md`.

Final combined coordinator run after both boundary workers settled:
`python3 -m pytest claude/meta-skill/tests/unit codex/meta-skill/test_flow.py -q`
passed **519 tests in 203.13 seconds**. The three core helpers
`product_intent.py`, `evidence_freshness.py` and `check_artifacts.py` passed
`uvx mypy --follow-imports=silent --check-untyped-defs`; `git diff --check`
was clean. Node engine tests remain 55/55 with no JS delta in this correction.
This is implementation regression evidence, pending formal committed-candidate
Standards/Spec review, not actual-host semantic acceptance.
