# T12 admission downgrade corrections (#12 legacy-downgrade holes)

Worker checkout `/Users/aa/orca/workspaces/myskills/meta-intent-t12`, starting HEAD
`5cab4f8f`, on top of the uncommitted T12 correction tree. Follows
`T12-admission-corrections.md`. Owned files: `check_artifacts.py`, new
`tests/unit/test_freshness_downgrade.py`, this report. `evidence_freshness.py`,
`product_intent.py`, the other gates and every existing test were not touched.
`codex/meta-skill/scripts` is a symlink to the Claude scripts, so both hosts run
the same gate code; the tests vary the host through the native transition-log
shape and the Codex flow producer.

## Holes probed

Both were reproduced red on the current tree by the new test file (27 of 27
scenarios failed before the fix; 36 pass after, including the regressions added
during the fix).

1. **Completion label exempted current work.** `freshness_admission` treated
   every node whose latest transition was `completed` as not intent-aware, so a
   node consuming the current task scope with no `source_inputs` became `legacy`
   as soon as a completed entry existed in `transition_log`. Adding completed
   history to newly scoped undeclared work bypassed the declaration at every gate.
2. **Legacy admitted evaluated results.** `freshness_admits` returned true for
   any `admission: legacy`, whatever the status. A previously published node
   that lost its `source_inputs` was `legacy`, still recorded, so it fell through
   to the evaluated `stale` state and was admitted anyway. The same path admitted
   a legacy node whose evaluation had failed (`status: invalid`) after the
   freshness state file was corrupted.

A third weakness surfaced while closing them: `_recorded_nodes` swallowed an
unreadable state file as "nothing recorded", which is what let a corrupt record
turn into an admitted legacy node.

## Rule now enforced

Admission is decided from current scope refs and recorded provenance, never from
the completion label alone:

| Node without `source_inputs` | Admission |
|---|---|
| consumes `requirement_refs` and is not completed | `missing` (unchanged) |
| completed, consumes a ref in the profile's current `task_scope.requirement_refs` | `missing` (new) |
| completed, `requirement_refs` present but scope unknown (profile missing or malformed) | `missing`, fail closed (new) |
| has a record in `evidence-freshness.json` (nodes or contracts bucket) | `missing`, reason names the withdrawn declaration (new) |
| completed, refs absent, empty or outside the current scope, no record | `legacy` (unchanged) |

`freshness_admits` admits `None` (pre-freshness workflow), `declared` + `valid`,
and `legacy` + `undeclared` only. Legacy with any evaluated status, a missing
admission with any status, an unknown status, or a non-dict value all fail
closed.

`freshness_states` treats an unreadable or unknown-shaped
`evidence-freshness.json` (not JSON, non-object root, a bucket that is not an
object, an entry that is not an object) as a global failure: every node that is
not already `missing` or `invalid` gets `status: invalid` with
`Freshness cannot be evaluated: freshness state unreadable: …`. Readiness reports
it as `stale_evidence`, reconciliation as `input_freshness`. Restoring the file
restores both admissions without republishing.

`_completed_nodes` now ignores malformed history entries (non-list log,
non-dict entries, non-string node ids) instead of raising; scope validation
already rejects such history, and an unreadable label cannot exempt work from
declaring. This was needed because the fix computes the completed set eagerly,
which the previous short-circuit never reached on a declared node.

`freshness_admission` gained an optional `project_root`. `validate_bootstrap.py`
still calls it without one, so the profile and state are read from the working
directory, which is where the generated runtime runs its gates and where the
copied-CLI tests run them. The other three gates pass their project root.

Legacy behavior is preserved deliberately: the `historical_refs` absent, empty
and out-of-scope variants stay `legacy`, are reported `undeclared` with the
`undeclared_source_inputs` warning, pass `check_artifacts` and reconcile as
`keep`, and gain no record when the current source changes. No provenance is
invented; the pre-#12 `freshness: null` path for a workflow with no declarations
and no state file is unchanged.

## Tests

`tests/unit/test_freshness_downgrade.py`, both hosts unless noted:

- published, completed node loses `source_inputs` after its source changed:
  refused as `missing` at all four gates, re-admitted after redeclaring and
  republishing;
- same withdrawal after the task scope moved on to another requirement (record
  outranks scope);
- completed history added to scoped undeclared work, on the existing node and on
  a newly appended node: still `missing` at all four gates, status `undeclared`;
- retained history with absent, empty and out-of-scope refs stays legacy and
  warning-only, before and after a current-source edit (the edit blocks only the
  declared current node);
- six corrupt or unknown state-file shapes fail every node closed and recover
  when the file is restored;
- `freshness_admits` table (single host, direct import);
- nine malformed history shapes never complete scoped undeclared work (direct
  import).

## Validation

| Command | Result |
|---|---|
| `python3 -m pytest claude/meta-skill/tests/unit/test_freshness_downgrade.py -q` on HEAD tree before the fix | 27 failed |
| same after the fix | 36 passed |
| `python3 -m pytest claude/meta-skill/tests -q` before any change (baseline) | 441 passed |
| `python3 -m pytest claude/meta-skill/tests -q` after the fix | 493 passed in 144s (tree also held other workers' newly added tests at that moment; root reruns before commit) |
| `node --test claude/meta-skill/knowledge/run-engine/tests/*.test.js` | 55 pass, 0 fail (no JS changed) |
| `uvx mypy --follow-imports=silent --check-untyped-defs --ignore-missing-imports` on `check_artifacts.py` | no issues |
| `git diff --check` | clean |

The first post-fix full run failed four `test_bootstrap_scope` malformed-history
cases with a traceback from the eager completed-set fold; the `_completed_nodes`
hardening above fixed them and the file was rerun green with the new suite.

## Limits and coordination

- Copied-CLI tests in temporary projects; no actual Claude or Codex host
  dialogue was run and none is claimed.
- The bootstrap validator's call site could not be changed, so its scope and
  record lookup depends on the working directory. Run from elsewhere it degrades
  to fail-closed on completed scoped nodes when the profile is not found; the
  readiness, artifact and reconciliation gates do not depend on this. Root may
  want `validate_bootstrap.validate_workflow` to pass its project root.
- Unknown scope (profile missing or without a `task_scope.requirement_refs`
  list) treats completed consumers of any requirement as current work. This is
  the intended fail-closed direction; product_intent already rejects scoped
  nodes without `task_scope`, so it only bites projects that were invalid anyway.
- `evidence_freshness.evaluate` was not changed; the diagnostic `check` CLI does
  not apply the gate admission rule and can still report a withdrawn-declaration
  node as `stale` rather than `undeclared`.
- No existing test or fixture needed changes. No commit, stage, reset, push,
  install or issue action was taken; root runs the final suite and commits.
