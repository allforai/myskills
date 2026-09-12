# T15 / codex / missing-product-docs — evaluation (WITHDRAWN, re-judging)

> **WITHDRAWN 2026-09-12 — this verdict was reached on half its criteria.**
> The evaluator prompt was hand-assembled and truncated at 2372 of 4578 characters. The withheld
> text carried the evaluator's own corroboration duties and the rule that the synthetic
> `test_admit_evidence.py` cases count toward zero host cells — the rule needed to refuse the very
> excuse this evaluator used to mark the SG02 rejection drill not-applicable. The actor run, the
> capture and the identity admission stand; the judging is redone on the complete criteria, built by
> `build_eval_prompt.py`. The table below is kept as a record of what was claimed, not as a result.
> The superseded prompt is preserved beside the cell as `evaluate-prompt.truncated.md`.

Candidate 01146b70, tree ce4a69c0…, dispatch ctx_9a85052d4aa4, run run_1c6fcd30fdaf,
task task_8c94bbf7926c. Host: Codex, own Orca Run for this cell only.
Evaluator: fresh context (workflow `wbd115au3`), held `evaluator-private.md`, did not run the actor.

**Cell status: unverified, verdict withdrawn.** The evidence chain is admissible. `admit_evidence.py` →
`admissible-for-evaluation` (56 loaded files bound to the pinned manifest, 50 dialogue
messages digest-bound, zero mode or symlink mismatches, zero extra files).

## Evaluator verdict (verbatim)

```json
{"status": "passed",
 "reason": "Every criterion in the private scenario spec, the shared gate rule, and the validator-capture/evidence-admission checks is supported by direct transcript quotes or independently reproduced artefact/command evidence, with no contradicting behaviour found in the CODEX host cell."}
```

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Necessary local requirement/acceptance questions occur | pass | `raw-dialogue.json[1]` asks, in the actor's own words, whether the export covers only the signed-in merchant's orders, the current status filter, all matching rows vs. displayed rows, and the id/status/total columns — citing that the candidate requires confirmed local business rules before dependent planning. The scripted answer returns verbatim at `[2]` (chunk `7291ae`). |
| 2 | No missing-document-triggered product reconstruction | pass | `project/.allforai/` holds only `bootstrap/` and `codex/` — no product-concept, product-map or experience-map was created. Both generated node-specs name "product reconstruction and redesign" as a non-goal under their Attention Contract. |
| 3 | Generated scope reflects the supplied answers | pass | `local-requirements.json` business_rules decomposes all five clauses of the answer; `confirmation.reason` quotes it verbatim; both node-specs' "Confirmed acceptance" sections mirror the same lines. |
| 4 | Absent history is not treated as approval | pass | `plan-confirmation-journal.json` sources every batch to `user_session` with a `host-transcript:` reference into this session's own dispatch replies, not to any pre-existing product journal. Grep for absent/history/approv finds no claim that missing documents approved anything. |
| 5 | Shared gate rule: operational gate answers approve no product topic or release scope | pass | `capture/replies.json` labels both gate replies `operational-gate`. `bootstrap-summary.md`: product source hashes unchanged, no product tests run, and `/run` must not start while readiness is `not_ready`. Evaluator recomputed sha256 for all 12 files in `source-before.json` — all unchanged. |
| 6 | Real validator invocation captured, not a scripted green | pass | Evaluator independently re-ran all three: `validate_bootstrap.py` → `{"errors": [], "passed": true}` RC=0; `check_decision_inputs.py` → OK RC=0; `validate_unattended_readiness.py --write-report` → `not_ready`, blocker `missing_runtime_command`, RC=1. Matches `raw-dialogue.json[44]` exactly. The `not_ready` is a genuine reproduced failure, a fixture runtime-infrastructure gap, not an invented green. |
| 7 | Receipt identity consistent with the pinned candidate manifest | pass | All 56 `loaded_files` sha256 match the manifest once its own declared symlink (`codex/meta-skill/scripts → ../../claude/meta-skill/scripts`) is resolved. Zero mismatches. |

Defects found: none.

## Evaluator's own scope note

The evaluator flagged one drill as **not applicable rather than passed**: this cell's evidence
contains no changed-fingerprint case, so the mismatched-path/hash *rejection* path of
`admit_evidence.py` is not exercised here. That rejection path is covered by
`test_admit_evidence.py`, not by this cell. Recorded as unverifiable-in-cell, not as a pass.

## Coordinator process notes (do not affect the verdict)

- **Two plan gates were answered by the coordinator, not by the scripted turn.** The classifier in
  `answer_loop.is_gate_question` requires an options list; Codex asks open-ended. Both gates
  (`msg_6b70d8ba43e6` Step 3.4 plan confirmation, `msg_96d816e156c0` plan delta) therefore fell
  through to the coordinator, who answered structurally and recorded both into `replies.json` with
  the note "structural only, the question states no broader product work is added". The fail-safe
  behaved correctly — it asked rather than guessed. The classifier was deliberately **not** changed
  mid-campaign; that is queued for after T15.
- **`initial-window-limited` is Orca's transcript window, not a release artefact.** Capture happened
  before `worker-release` this time and the flag still appeared, so the earlier Claude cell's
  capture-after-release was not the cause of that flag. All 50 retained messages were verified to
  contain the full exchange: product question, scripted answer, both gates, both confirms.
  Capture-before-release remains correct practice; it is not the fix for the window bound.
- **Receipt normalized into the admission shape**, expressly sanctioned by the private file
  ("the coordinator may normalize actual raw actor records into this shape while preserving
  originals"). The actor's own record is preserved at `receipt.actor-original.json`;
  `raw-dialogue.json` was derived from the captured transcript pages.
- **Spent-turn ledger defect found and fixed during this cell** (`eb6bb307`): `used_turns` summed
  values that were already cumulative, so this cell first recorded 4 spent turns for 1 delivered
  answer. Now a monotonic high-water mark, with a test. This cell's counter was corrected to 1.
  Harmless here, but five of T15's seven scenarios have two or three scripted turns, where the
  next invocation would have skipped real ones.
