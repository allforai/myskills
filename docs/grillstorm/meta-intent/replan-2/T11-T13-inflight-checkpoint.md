# In-flight coordinator checkpoint

This is a read-only inspection of live worker changes, not independent review or
implementation acceptance. Accepted integration production remains `ed430dfc`.

## #11: legacy hand-projection recovery

Worker `ctx_8ae581fcb4a6` owns T12 correction files. The new public-CLI tests cover
goal-only and mismatched journal authority, in-place recovery, full-payload and
user-turn provenance, and removed history. The worker reported 18 focused cases
passing; root has not yet verified the final candidate.

Follow-up sent as `msg_d25e7f97c173`: `resume` accepts genuine user-turn legacy
projections, but `freeze` still requires canonical journal payloads. Check a
mixed legacy file after confirming only its pending item: can the valid item
remain reusable through freeze and plan without needless reconfirmation? Also
check that changing the session marker does not turn valid removed history into
pending work. Do not rewrite historical journal batches to manufacture authority.

## #13: document synchronization cannot be a fresh report alone

Worker `ctx_592495fd6926` owns T13. The inspected draft of
`test_delivery_closure.py` changes a document to claim that every account's orders
are returned, then republishes using a command checking only report `status` and
expects `valid`. That does not establish the ticket's required consistency.

Blocking follow-up `msg_5d27525e7e9e` asks for the decisive negative slice:
change source behavior, retain an outdated required document, observe the new
inputs and run code-only passing verification. The delivery must not complete.
Document synchronization and its verification must be grounded in current source,
not merely a new timestamp, hash, report, or declaration of responsibility.
Correcting the facts and actually reverifying must restore completion while
unrelated valid work stays valid. A candidate commit alone does not close this.

Builder produced `705ec156`, with 563 hook tests passing, without processing the
queued finding. Root did not accept or integrate it. The same exact terminal was
reused for correction Task `task_2515b182fb17`, Dispatch `ctx_a8e7d8ab1885`, before
acknowledging its completion delivery. The new task explicitly includes the
blocking counterexample and requires an inbox check before reporting completion.

The #11 worker has since settled and been released. Root's first 577-test run
passed, then a new post-freeze confirmation counterexample reproduced an
implicit restoration on both adapters. Root corrected it, with 20 legacy-profile
tests green; the combined meta-skill/Codex-flow regression and fixed-candidate
independent review are pending. See T12's `T11-legacy-profile-root-verification.md`.

The combined run then passed 601 tests in 165.89s. Candidate
`2916e1833fb3267b335b3d666d0831e52b03cb8e` was committed after 577 hook tests
passed in 165.78s and all hook validators passed. Node tests: 55 passed; three
core-file typechecks clean. Two independent review workers await capacity within
the existing three-worker limit. No candidate acceptance or integration implied.

## Runtime boundary

The #13 correction developer remains live. #15 evaluator `ctx_50de403c39ba` remains at Codex's
interactive model-choice prompt. The user must clear that prompt; no input bypass
or model change was applied. Actual host evidence is still **0/60**. No push,
main merge, installation, or issue closure is authorized by this checkpoint.
