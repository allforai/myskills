# T13 corrective-delta standards review — c77323da

Scope: `git diff 000c9242...HEAD`, one commit. Report-only; no source, test, or
repo state touched. Baseline: CLAUDE.md, CONTEXT.md, `codex/meta-skill/AGENTS.md`,
ADR-0001/0003. Root reports treated as claims, not evidence.

## Verified

- `claude/.../validate_bootstrap.py:1073` adds `document_verification` to the
  existing spec/workflow parity tuple. Guarded by `if field in node`, so nodes
  and old projects that never declare it are unaffected — no API or legacy
  regression.
- `codex/.../flow-template.py:26` adds `accepted_with_gaps` to the local
  reporting set. The real gate is `independent_artifact_gate` →
  `check_artifacts.py`, which already blocked that value; the change is
  reporting-only, exactly as the commit message says.
- The accept path (`handle_iteration`, flow-template.py:599) writes the status
  nested inside `decisions[]`, not as a top-level `status`, so the new blocking
  value does not break qualified acceptance.
- Ran the added tests (read-only): `codex/meta-skill/test_flow.py` 25 passed;
  `test_document_verification_must_match_the_node_spec` 4 passed. Both reject
  missing and changed commands and accept the restored contract.

## Documented-rule breach

**`AGENTS.md` Contract Notes / Shared Asset Strategy** — generated `flow.py` is
declared to consume `check_artifacts.py` "so capability content stays aligned",
yet flow-template.py keeps a second `BLOCKING_STATUS_VALUES`. After this delta it
still omits `existence_only`, `not_good_enough`, `quality_failed`. An artifact
carrying those statuses is still listed in `artifacts_created` (flow-template.py:776)
and produces no `readiness_errors` line (:801) — the same defect class the delta
fixes, still live for three values.

## Judgements (optional)

- **Duplicated Code / Shotgun Surgery.** Blocking statuses exist in three code
  sets plus two prose lists; this delta edited three sites for one value.
  `reconcile_bootstrap_workflow.py:30` diverges from `check_artifacts.py` by ten
  values. Fix: one shared source, imported or generated.
- **Asymmetric parity guard.** `validate_bootstrap.py:1073` compares only when
  the field is in the workflow node. A node-spec declaring `document_verification`
  the workflow lacks still passes, so the promised check never runs. Pre-existing
  shape, now widened to a fourth field.
- Docs read consistently; the new `node-spec-template.md` sentence restates
  `bootstrap/SKILL.md:604` but a template legitimately restates its contract.

No host execution proof (0/60) was available; nothing above depends on one.
