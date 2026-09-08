# Corrections after the 2916e183 independent review

The original Standards and Spec reports remain unchanged. Standards found no
hard breach; two documentation judgements and five optional code-smell findings
do not require a broad refactor. Spec accepted C1-prime but reported A1 (recording
could invent a new consent source) and a minor invalid-removal recovery issue.

## A1: preserve the original consent source while recording

For a valid, confirmed legacy user-turn item, `decide confirm` now requires the
original user reference and recorded reason. It still records the unchanged
payload once and preserves `prior_confirmation`; it is not new consent. Invalid
provenance and journal-backed pending projections still require actual fresh
decisions through their existing recovery paths.

Four copied-CLI cases (two adapters × independently changed reference/reason)
first reproduced the accepted fabricated source, then verify rejection without
any file change and successful recording with the original source and reason.
These and the mixed legacy transition passed: 6 passed in 2.24s.

## C1 minor: confirm a removal without activating the requirement

An unverified tombstone may now receive an explicit `remove` decision directly.
It preserves the old removed revision and appends a confirmed removed revision;
there is no active intermediate revision. Confirmed removals and frozen-excluded
removals still cannot be silently revived. The protocol names the direct removal
action. Two adapter cases first reproduced the refusal, then passed with removal
history intact and no pending topic for the verified removal.

The added cases first failed (6 failed / 20 deselected in 0.95s); all 26 legacy
profile tests now pass in 9.55s. Product-intent typechecking and diff check are
clean. A fresh full regression on 2026-09-09 passed: 607 tests in 170.15s
(`python3 -m pytest claude/meta-skill/tests/unit codex/meta-skill/test_flow.py -q`).
The 55 Node run-engine tests also passed. `uvx mypy --follow-imports=silent
--check-untyped-defs` found no issues in product_intent.py, evidence_freshness.py
and check_artifacts.py. The prior interrupted run is not counted.
Fixed-candidate independent review remains pending. The pre-existing
bare `intent_scope` diagnostic before freeze is recorded as a minor usability
observation, not a reason to invent a new planning route.

No actual host evidence is claimed; the 60-cell matrix is still unverified.
