# T12 corrupt-read corrections (#12 recheck C2)

Worker checkout `/Users/aa/orca/workspaces/myskills/meta-intent-t12`, candidate
`90257b15`, uncommitted. Corrects C2 from `T11-T12-spec-recheck.md`: the copied
freshness CLI raised an uncaught `AttributeError` when
`.allforai/bootstrap/observed-input-dependencies.json` (the dynamic-read
register written by the `read` operation) was malformed. Owned files only:
`evidence_freshness.py`, new `test_corrupt_freshness_reads.py`, this report.
Templates, other scripts and the shared reports are root's.

## Rule now enforced by the copied freshness CLI

The register must be an object keyed by non-empty node ids, each value a list
of non-empty relative project paths without `..`. Unparseable JSON, a list,
string, number or null at the top level, and a malformed node entry are all
refused with `{"status": "invalid", "reason": "Malformed observed-input
dependencies (.allforai/bootstrap/observed-input-dependencies.json): …"}`,
exit 1, empty stderr. A well-formed entry for a node the workflow no longer
lists is retained provenance, not corruption; its paths stay in the owned-input
set.

The register is never treated as empty. Every consumer goes through one
validated loader, `observed_reads`: `snapshot` (observe, read, publish and
evaluate), `dependencies`, `evaluate`'s owned-input set, the observe-time
`extra` merge, and the `read` write path inside the publication lock. The
validator runs before any write, so the corrupt file, prior observations,
`evidence-freshness.json` and reports stay byte-identical for repair. Nothing
in the CLI repairs or removes the file; the reason text tells the operator to
repair or remove it after review.

Producer publication and freshness scope are unchanged: the gates still
consume `check_artifacts.freshness_states`, whose existing `evaluate` failure
path turns the raised `ValueError` into `invalid` for every admitted node
(`Freshness cannot be evaluated: freshness evaluation failed: Malformed
observed-input dependencies …`); readiness reports `stale_evidence` with that
message, `check_artifacts` reports `all_exist: false`, reconciliation blocks
and invalidates, and the bootstrap validator does not crash.

## TDD record

Red (`test_corrupt_freshness_reads.py` against candidate `90257b15`):
36 failed, 2 passed. The CLI seams (`observe`, `read`, `check`, `publish`)
crashed with `AttributeError: 'list' object has no attribute 'get'` /
`'values'` for list and scalar top levels, and with `TypeError` sorting
non-string entries; string node values were silently split into characters and
accepted. The gate suites already failed closed but named the Python error, not
the file. The 2 passing cases were the retained unknown-node regression on both
hosts.

Green after adding `observed_reads` and routing all five consumers through it:
38 passed. Coverage, each on both host script paths (Codex `scripts` is a
symlink to the Claude tree):

| Scenario | Seam | Assertion |
|---|---|---|
| 13 corrupt shapes: list, list of paths, string, number, null; node value string, object, null; entry number, empty, absolute, `..`; empty node id | `observe`, `read`, `check`, `publish` | `invalid`, reason names the file, exit 1, no stderr, no `observation`/`content`/`nodes` key, bootstrap tree byte-identical |
| `{not json` | same four operations | same |
| list of paths, node value string, entry number | `check_artifacts`, readiness `--write-report`, reconciliation `--write`, bootstrap validator | `all_exist: false`, freshness `invalid` naming the file, `not_ready` with the node's blockers naming the file, `blocked`/`invalidate`, register untouched |
| corrupt then repaired register | `check`, `read` | evidence `valid` again, `read` works, editing the read file turns evidence `stale` and `all_exist: false` |
| entry for a retired node | `check` | evidence stays `valid`, the retired node's path is owned, no `uncertain_inputs` |

Regression (`validation-commands.md` #9–#12 suites plus `test_bootstrap_scope`,
`test_product_intent_session` and the new file): 392 passed, 8 failed. All 8
failures are in `test_product_intent_resume`, `test_product_intent_session` and
`test_intent_review_corrections`, and every one reports the message `Legacy
journal choice evidences the goal only …`, which exists only in the other
worker's uncommitted `product_intent.py` diff (C1). None of the 13 freshness,
gate or reopen suites failed. `py_compile` passes on both owned Python files;
no mypy/pyright/ruff is installed in this environment, so no static typecheck
ran.

No host-dialogue claim: everything above exercises copied CLIs in temporary
projects.

## Root follow-up

After worker settlement, root changed only the recovery guidance: restore recorded
dependencies before retrying, not remove the register as a generic repair. The
worker observations above describe its original candidate. Root also ran
`uvx mypy --follow-imports=silent --check-untyped-defs` on
`evidence_freshness.py`: success, no issues. Combined regression remains a
separate root checkpoint after the product-intent worker settles.

Root reran the entire new corrupt-read suite after that wording change:
**38 passed in 10.92s**. This is still copied-CLI evidence only.
