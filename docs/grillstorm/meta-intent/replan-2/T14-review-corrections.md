# T14 review corrections — #14 defects fixed on top of 5c02e24c

Two reviewers read #14 v2 at `5c02e24c` and reported the same first defect from two
angles, plus a second one and two minor items:

- `T14-5c02-spec.md` Finding 1 / `T14-5c02-standards.md` breach 1 — a recorded
  external-change resolution is orphaned when any later freeze advances the baseline
  version, so a settled rejection or deferral is asked again and its scoped repair
  stops blocking.
- `T14-5c02-spec.md` Finding 2 — the `/run` readiness path consumes a detection store
  that `/run` never refreshes, so drift that nobody detected first is reported as
  node-owned `stale_evidence` instead of returning to the interactive product decision.
- Minor: a dead docstring in `classify_external_change`, and the unmapped-source
  `owned` computation duplicated between `unmapped_changes` and `evaluate`.

Both reviewer reports are kept verbatim beside this one as the evidence they are.

## What changed

**Change identity is the delivery plus the changed source content.**
`change_identity(node_id, fingerprints)` no longer digests `baseline_version`. A later
edit is still different content and therefore a different change; advancing the
baseline version for other work no longer renames an unchanged one.

**A resolution binds the confirmed requirement content it was decided against,
not the baseline version.** Detection records the node's selected requirement digests
as `requirement_binding`; `carried_resolution` carries a decision forward while that
content is unchanged and retires it into `superseded_resolutions` when the user
revises those very requirements, in which case the change is presented for a fresh
decision and readiness says it was reopened. This keeps the guard the baseline
binding was there for — old consent never answers a semantically different question —
without letting an unrelated refreeze erase a decision. `_external_change` records the
binding after the accepted intent actions are applied, so a decision is never
superseded by its own effect.

**The gates run the boundary comparison themselves.** `external_conflicts` now calls the
shared `resolve_external_changes`, so `check`, `check_artifacts.py`, reconciliation and
readiness detect, classify and settle drift without an earlier explicit
`external-changes` invocation. Classification executes the delivery's own recorded
acceptance once per change identity and is reused afterwards, so repeated boundary
checks on unchanged source are stable and leave the store byte-identical. Nothing here
interviews, decides, or writes the decision journal; a passing acceptance stays a
`fact-update` owned by its node.

Minor items: the `classify_external_change` docstring moved above the `record is None`
guard (it was a no-op expression), and the duplicated `owned` computation became
`owned_inputs(root, workflow, state)`, called from both places.

`validate_unattended_readiness.py`'s uncommitted `raw_nodes` narrowing was already
approved and is preserved unchanged; the readiness edit here only distinguishes
deferred / reopened / undecided in the blocker message.

## RED → GREEN

Tests are at the agreed public CLI seam: the copied bootstrap/resume and gate CLIs
driven in temporary projects, parametrized over both host adapters.

RED, before the fix (`pytest tests/unit/test_external_change_recovery.py -k "survives_the_next_baseline_freeze or supersedes_the_earlier or without_a_prior_detection_call or keeps_its_node_owner"`) — 6 failed, 2 passed:

- `test_a_rejected_change_survives_the_next_baseline_freeze` — after the freeze the
  change identity moved from `fdb47f296e7d…` to `5855a7d4166d…` with
  `status: conflict` and `resolution: null`: the rejection was orphaned exactly as
  both reviewers reported.
- `test_a_revised_confirmed_intent_supersedes_the_earlier_decision` — the opposite
  hole: the rejection was still applied verbatim (`status: decided`) after the user
  revised the requirement it preserved.
- `test_drift_reaches_the_product_decision_owner_without_a_prior_detection_call` —
  `StopIteration`: readiness reported no `unresolved_external_change` blocker at all.
- `test_implementation_only_drift_keeps_its_node_owner_at_the_same_gates` passed
  before and after; it is the guard that the refresh never turns a verified
  implementation fact into a product question.

GREEN, after the fix:

| Command | Result |
|---|---|
| `python3 -m pytest tests/unit/test_external_change_recovery.py -q` (claude/meta-skill) | 26 passed |
| `python3 -m pytest tests/unit -q -p no:randomly` | 631 passed (baseline at 5c02e24c: 621 passed) |
| `python3 -m pytest codex/meta-skill/test_flow.py codex/meta-skill/test_install.py -q` | 35 passed |
| `uvx mypy --follow-imports=silent --check-untyped-defs` on `evidence_freshness.py`, `product_intent.py`, `validate_unattended_readiness.py` | Success: no issues found in 3 source files |
| `validate_meta_contracts.py .`, `validate_generalization_boundaries.py .`, `validate_specialization_contracts.py .` (repo root) | exit 0 |
| `validate_skills.py .` (repo root) | exit 1, 575 lines — byte-identical to the same run against a `git archive HEAD` extraction, so pre-existing and untouched by this change |

New coverage, both adapters: rejection surviving its own journal batch's freeze and a
later unrelated freeze, with the repair blocker and the "already rejected" refusal
intact and the repair still closing the delivery; supersession by a revised
requirement with the earlier decision preserved as history; drift routed to
`interactive-bootstrap` at readiness, artifacts and reconciliation with no prior
detection call, stable on repeat and decidable straight from that boundary;
implementation-only drift keeping its node owner; and a corrupt change store reopening
the conflict instead of claiming a decision. The pre-existing accept-propagation,
defer-resume, unmapped-uncertainty and unreadable-state tests still pass, with the
defer test's stored resolution updated for the new `requirement_binding` field and the
unreadable-state test strengthened to assert the readiness gate fails closed with
blockers rather than only a nonzero exit.

## Limitations

- These are copied-CLI tests in temporary projects. They are not real Claude or Codex
  host dialogue evidence; the host proof #14 still needs remains pending and this
  change does not supply it.
- Codex parity here is structural: `codex/meta-skill/scripts` and `tests` are symlinks
  to the Claude tree, so both adapters run the same helpers, and the tests are
  parametrized over both hosts. The Codex-side prose was updated to match.
- `validate_skills.py` fails at the repo root for reasons that predate this work
  (orphan bundled skills, cross-adapter duplicate names); it was verified unchanged,
  not fixed.
- `shared/mcp-ai-gateway` has no `node_modules` in this checkout and no install was
  performed, so its build was not run. Nothing in this change touches it.
- Classification now runs inside the boundary gates. It executes each drifted
  delivery's own recorded acceptance once per change identity and reuses the result,
  which is bounded and deterministic, but it does mean `check`, `check_artifacts.py`
  and readiness can execute a project's acceptance argv where previously only the
  explicit `external-changes` operation did.
