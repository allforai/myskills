# T15 / codex / missing-product-docs — re-evaluation on complete criteria

Candidate 01146b70, tree ce4a69c0…, dispatch ctx_9a85052d4aa4, run run_1c6fcd30fdaf.
Evaluator: fresh context, held the complete criteria built by `build_eval_prompt.py`, did not run
the actor. Supersedes the withdrawn verdict in `codex-missing-product-docs.md`.

**Cell status: unverified.** `status: "unverified"`. Every scenario behaviour criterion passes on
quoted evidence and the rejection drill works, but two required corroborations could not be
performed at all. The withdrawal was correct: judging on complete criteria changed the outcome.

## What the complete criteria caught that the truncated ones did not

**1. Session identity is not independently corroborated (`unverifiable`).**
The receipt's `session_id` `01a093a5-…` appears *only* inside the actor's own output, derived by the
actor from `os.environ['CODEX_SESSION_ID']`. No coordinator-side record carries it: the dispatch,
run, capture index and reply log name only the run, task, dispatch and `processIncarnation`. The
evaluator also searched the Codex session store and found no rollout file for the date and no hit
for the id. Its UUIDv7 shape is plausibility, not corroboration.

This is the hole the truncated prompt hid, and it is a defect in the gate, not just this cell:
`admit_evidence.py` line 51 is `if not receipt.get("session_id")`. **A self-authored session id
passes admission.** So "admissible-for-evaluation" never did bind session identity for any cell.

**2. Dialogue completeness cannot be certified (`unverifiable`).**
The capture index declares its own limit: `full_dialogue_proven: false`, `initial-window-limited`,
`Oversized transcript text was clipped`, `Oversized tool input was clipped`, 50 messages with no
forward page. Concretely, the revision-2 confirmation chunk `54a7dd` that the actor's own
`plan-confirmation-journal.json` cites has **no observable tool-result** in the window — the single
occurrence of that id is inside the actor's later write. The substance is corroborated from the
coordinator's reply log, but the cited chunk is not, so completeness fails.

My earlier reading was wrong in an important way. I recorded that all 50 retained messages carried
the full exchange. They carry the *substance* of the exchange, but not every citation the artefacts
make, and the window provably starts after the entry-file reads.

The evaluator states the fix does **not** require re-running the actor: capture from message 1 with
unclipped tool output, paging backwards from the cursor the index already holds.

## What did pass, on quoted evidence

| Criterion | Verdict |
|---|---|
| Necessary local requirement/acceptance questions occur, before any planning artefact | pass |
| No missing-document-triggered product reconstruction | pass |
| Generated scope reflects the supplied answers | pass |
| Absent history is never claimed as approval | pass |
| Bootstrap planning only; no `/run`, no product implementation | pass |
| Run Policy values all within the allowed operational set, none escalated | pass |
| Real validator invocation captured; genuine failure preserved | pass |
| Failure attributed to missing runtime infrastructure, not product authority | pass |
| Receipt and raw reads match the pinned manifest | pass |
| **SG02 rejection drill actually exercised** | pass |
| Host identity corroborated against three coordinator-side records | pass |
| Loaded-file list complete for the captured window (51 of 56 corroborated outside the receipt) | pass |
| Turns and artefacts consistent with independent records | pass |
| `.git` exclusion moot here; all 12 source hashes unchanged | pass |
| Frozen evidence root unmodified by the evaluation | pass |

The rejection drill was performed this time rather than excused. On scratch copies: an altered
loaded-file path → `unverified` `["candidate-mismatch","changed-candidate"]` exit 1; an altered
sha256 → same, exit 1; unchanged receipt against a tree with one byte appended → `unverified`
`["changed-candidate"]` exit 1, and admitting again once the byte is restored. No semantic pass is
ever emitted. The drill works as designed.

## Defects recorded

1. **Campaign capture defect** (blocks certifying this cell; not a candidate defect). The only
   dialogue record is window-limited and clipped. Fixable by re-capturing backwards, not by
   re-running the actor.
2. **Campaign identity defect** (blocks the corroboration duty). Nothing binds the provider session
   id to the dispatch, and admission only checks the field is non-empty. The campaign needs a
   coordinator-side capture of worker identity at dispatch time.
3. **Candidate gap observed** (not a cell failure). The generated workflow names capabilities
   `implement` and `closure`, and neither has a template in the pinned candidate, while
   `product-verify.md` does exist. The actor reported `implement`'s absence honestly; it did not
   mention `closure`'s. This is a finding against the candidate to route to the owning ticket.

## Evaluator hygiene note

The evaluator observed 18 paths changing under the *sibling* Claude cell during its run and
correctly reported them as not its own. That is concurrent campaign activity, and it confirms the
per-cell isolation held: nothing it touched belonged to the cell it was judging.
