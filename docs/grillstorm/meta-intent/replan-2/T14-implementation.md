# External source change recovery (#14 v2) — implementation report

Producer base: accepted `1ed30ee5819adf95cf4f2b64c08956ec4c751b1d` on the
integration branch `j08069099777/grillstorm-meta-intent`. Scope is #14 v2 only.
No issue is closed, nothing is pushed, no installation or main merge occurred.

## What was built

One vertical slice at the pre-agreed seam: the copied bootstrap/resume gate CLIs
and their observable JSON I/O. No new plugin, no new copied script, no parallel
acceptance system.

**Detection (`evidence_freshness.py`, new `external-changes` operation).**
At the bootstrap/resume boundary it compares each published evidence record with
the current source and reports, per change, the changed facts, the confirmed
product decisions that consume them, the required fact documents, the dependent
tasks and the bound acceptance artifacts. It is the same boundary comparison the
protocol already uses; nothing watches the repository in the background.

**Classification is verification, not a semantic guess.** The oracle is the
delivery's own recorded acceptance argv, re-executed against the changed code:

- it still passes → `fact-update`; the change is implementation only and is
  synchronized by refreshing the required documents and republishing evidence;
- it fails → `product-conflict`; changed code never becomes the desired behavior;
- source no node declares → `uncertain`, reported against every delivery whose
  provenance it touches, so missing mapping is stated rather than assumed harmless.

A change identity binds the node, the confirmed baseline version and the current
content of the changed files, so a later edit is a different change and an earlier
decision cannot travel to it.

**Decision (`product_intent.py`, new `external-change` operation).** A conflict is
settled only by an explicit user decision carrying an actual user reference and reason:

- `accept` requires the explicit desired intent the change establishes whenever the
  change touches confirmed decisions; those actions go through the ordinary `decide`
  path and one journal batch tagged with the change. The baseline version then
  advances through the existing refreeze → replan → resynchronize → reverify loop.
- `reject` keeps the confirmed baseline, records the decision, and produces a scoped
  implementation repair task (node, changed files, the confirmed acceptance to
  restore). `external_change_repair_pending` holds the node until that acceptance
  republishes.
- `defer` — and an interrupted interaction that records nothing — retains the
  conflict and its context, blocks only the dependent work, and leaves unrelated
  valid records and their node-specs untouched.

**Gates.** `repair_responsibility` returns `interactive-bootstrap` /
`product-decision` for an undecided conflict; `validate_unattended_readiness.py`
adds `unresolved_external_change` and `external_change_repair_pending`. Unattended
execution reports and refuses; it never interviews and never assumes acceptance.
A Run Policy `accept` is a run choice and does not settle a product conflict.
Completion still flows only through the existing #13 freshness, document-check and
artifact gates and the #11 journal/scope authorities.

**Fail-closed.** An unreadable freshness record makes the comparison undeterminable:
the CLI returns `invalid` and no decision can be recorded against it, rather than
reporting a reassuring empty result.

## Files

- `claude/meta-skill/scripts/orchestrator/evidence_freshness.py`
- `claude/meta-skill/scripts/orchestrator/product_intent.py`
- `claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py`
- `claude/meta-skill/tests/unit/test_external_change_recovery.py` (new)
- `claude/meta-skill/knowledge/input-freshness.md`,
  `claude/meta-skill/knowledge/orchestrator-template.md`,
  `claude/meta-skill/skills/bootstrap/SKILL.md`,
  `codex/meta-skill/knowledge/orchestrator-template.md`,
  `codex/meta-skill/skills/bootstrap.md`

Codex consumes the same helpers through its `scripts` symlink and halts on the same
readiness preflight, so parity is behavioral, not a second implementation. Every new
test is parametrized over both host adapters.

## Verification

- New behavior suite: 16 cases (8 scenarios × claude/codex) pass.
- `python3 -m pytest claude/meta-skill/tests/unit codex/meta-skill/test_flow.py -q`:
  **649 passed in 212.40s**, no failures. The Codex packs run clean separately too
  (`test_flow.py` + `test_install.py`: 35 passed).
- Commit hook on the candidate: 621 canonical tests passed in 208.01s and every
  repository validator reported ok.
- Node run-engine tests: `node --test tests/*.test.js` — 55 passed.
- `python3 -m py_compile` clean on the three changed scripts; `git diff --check` clean.
- **Typecheck limitation, reported honestly:** no static type checker is installed in
  this checkout (`mypy`, `pyright` and `ruff` are all absent and PEP 668 blocks
  installing one). The "three core-file typechecks" of earlier reports could not be
  reproduced here; only byte-compilation was run. Pre-existing type diagnostics
  elsewhere in the tree are unchanged by this work.

One regression was found and fixed during the run: a corrupt freshness record made
the readiness gate crash through the new detection path. Detection now fails closed
with a stated reason, and `test_freshness_downgrade.py` passes unchanged.

## Limits

These are copied-CLI tests in temporary projects. They do not prove a real Claude or
Codex host session chooses a meaningful acceptance argv, and actual host dialogue
proof remains outside this ticket. The classification is only as strong as the
acceptance the user confirmed: a weak recorded acceptance classifies a real product
change as a fact update. That is the same dependency the #13 completion gate already
has, and it is deliberate — the alternative would be a synthetic semantic oracle,
which this ticket excludes. Visual-file migration (#27 → #40 → #41) is untouched.
