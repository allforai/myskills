# T11/T12 spec final recheck (candidate ed430dfc)

HEAD verified `ed430dfcebed485b913b54d7785f02cc86998303`; fixed diff `90257b15...HEAD`; only expected untracked reports. Independent scratch probes (`probe.py`, `probe2.py`, GIT_* stripped) drove the copied CLIs and three public gates on both host copies. Copied-CLI evidence only; #15–#18 stay unverified. Standards report not consumed.

## Prior findings

| # | Status |
|---|---|
| A1 identical re-freeze | Fixed. Reversed include order, new batch id, other reason → `unchanged: true`, tree byte-identical, gates ready (product and local). Add+exclude, adjust, reopen, tampered scope batch, or any later journal batch → version 2, gates block until replan. |
| C2 corrupt read register | Fixed at `observe`/`read`/`check`/`publish` (structured `invalid`, exit 1, no stderr, files untouched), at the three gates and reconciliation; likewise corrupt `evidence-freshness.json` and observation files. Repair restores the dependency. |
| C1 goal-only legacy authority | Fixed on `admit`, `draft`, stored `resume`, `freeze` and contract gates: item returns `pending` with `legacy_reuse`, freeze refuses, one `confirm` records the payload and retains `prior_confirmation`. **Open on the sibling documented route, see C1'.** |

## (a) Missing / partial

**C1'. Hand-projected legacy profile still authorizes unevidenced acceptance.** Spec #11: "没有确认来源的旧代码推断不能伪装为已批准需求"; "旧 concept／baseline 有可信确认记录时按相关范围复用". `bootstrap-planning.md` § requirement scope and SKILL.md §1.6 still document writing `local-requirements.json` by hand with `confirmation.reference` = an existing journal decision and a profile without `intent_session_path`. On that route `validate_scope` only checks the decision exists; probe P1: goal-only decision whose `chosen` differs entirely from the requirement goal, model-invented `acceptance` and an added scope area → all three gates exit 0, readiness `ready`, `resume` shows nothing pending. This is an approved documented path, not tampering, and #9's `test_journal_backed_local_requirement…` locks it. Codex's `journal` command produces exactly such goal-only batches. Repro: `T11-T12-spec-final-repro.md`. Resolution must keep T9-SPEC-01 (full-payload or user-turn projections stay accepted) and must not rewrite historical journals.

## (b) Scope creep

None; the helper extraction and template wording serve the fixes.

## (c) Implemented-looking wrong behavior

**Minor.** Template says malformed state "block even retained nodes", but an all-legacy workflow with no `evidence-freshness.json` returns `{}` from `freshness_states` before reading the register: corrupt register → `check_artifacts` `all_exist: true`, reconciliation `keep`. Reachable only if a read-registered node was replanned away unpublished. Not blocking.

## Acceptance

A1 and C2 accepted. C1 accepted on every CLI route but not closed: C1' is a narrow gate/doc gap on the documented hand-projection route and blocks #11 C1 closure. Independent of #15–#18.
