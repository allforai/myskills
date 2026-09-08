# T17 actor launch request

Prepared by the dispatched T17 worker (evaluation role). **The coordinator alone launches the
scenario actors.** This file carries only launch inputs; the evaluator criteria and the scripted
user replies stay in `evaluator-private.md` and are never sent to a tested context.

## Candidate under test — refresh before launching

The packets below were exported from the **preliminary** producer
`1ed30ee5819adf95cf4f2b64c08956ec4c751b1d` while the `#14` repair was still in flight.

- Exported candidate root: `/private/tmp/meta-intent-T17-1ed30ee5/candidate`
- Candidate tree SHA-256: `9f4945c479cdfc7560d92481c96d087223060285afa0d40a6357a97f1cd14480`
- Manifest: `/private/tmp/meta-intent-T17-1ed30ee5/candidate-manifest.json`
- Claude entry: `candidate/claude/meta-skill/skills/bootstrap/SKILL.md`
  SHA-256 `80e85064e59bf3b9c48b35948f06a30cf4f4be2d95f2169866e7a96087fcc37f`
- Codex entry: `candidate/codex/meta-skill/SKILL.md`
  SHA-256 `526dc0958a9c174a07d9b98d54de8cd1f2561790dbbf759853b45e13086c6065`

**Do not launch an actor against this tree.** Re-run

```
python3 docs/grillstorm/meta-intent/replan-2/T17/prepare_packets.py \
    /private/tmp/meta-intent-T17-<final-short-sha> --candidate <final repaired commit>
```

from a checkout that contains the final accepted repaired commit, then re-pin `results.json`,
this file and `evaluator-private.md` to the new tree hash. Evidence gathered against the
preliminary tree hash is preparation only and is never counted toward the 16 cells.

## What to send each actor

Send the **entire contents of that cell's prompt file, byte for byte, and nothing else**. It
already names the candidate entry, the candidate root, the project path, the receipt path, the
no-install rule and the single user turn. Do not add the scenario name, the requirement ids, this
file, the issue text, other cells' material, or any expectation of the outcome.

Each actor needs a fresh context and an independent session identity, and must be able to reach
the coordinator with its dispatch `ask` command.

## Cells

| Scenario | Host | Project | Prompt file | Second-phase prompt |
|---|---|---|---|---|
| `T17/two-dirty-states` | claude | `/private/tmp/meta-intent-T17-1ed30ee5/claude/two-dirty-states/project` | `/private/tmp/meta-intent-T17-1ed30ee5/claude/two-dirty-states/actor-input.md` | — |
| `T17/two-dirty-states` | codex | `/private/tmp/meta-intent-T17-1ed30ee5/codex/two-dirty-states/project` | `/private/tmp/meta-intent-T17-1ed30ee5/codex/two-dirty-states/actor-input.md` | — |
| `T17/baseline-only-change` | claude | `/private/tmp/meta-intent-T17-1ed30ee5/claude/baseline-only-change/project` | `/private/tmp/meta-intent-T17-1ed30ee5/claude/baseline-only-change/actor-input.md` | — |
| `T17/baseline-only-change` | codex | `/private/tmp/meta-intent-T17-1ed30ee5/codex/baseline-only-change/project` | `/private/tmp/meta-intent-T17-1ed30ee5/codex/baseline-only-change/actor-input.md` | — |
| `T17/generated-sync-no-loop` | claude | `/private/tmp/meta-intent-T17-1ed30ee5/claude/generated-sync-no-loop/project` | `/private/tmp/meta-intent-T17-1ed30ee5/claude/generated-sync-no-loop/actor-input.md` | `/private/tmp/meta-intent-T17-1ed30ee5/claude/generated-sync-no-loop/actor-input-phase2.md` |
| `T17/generated-sync-no-loop` | codex | `/private/tmp/meta-intent-T17-1ed30ee5/codex/generated-sync-no-loop/project` | `/private/tmp/meta-intent-T17-1ed30ee5/codex/generated-sync-no-loop/actor-input.md` | `/private/tmp/meta-intent-T17-1ed30ee5/codex/generated-sync-no-loop/actor-input-phase2.md` |
| `T17/tests-pass-docs-stale` | claude | `/private/tmp/meta-intent-T17-1ed30ee5/claude/tests-pass-docs-stale/project` | `/private/tmp/meta-intent-T17-1ed30ee5/claude/tests-pass-docs-stale/actor-input.md` | — |
| `T17/tests-pass-docs-stale` | codex | `/private/tmp/meta-intent-T17-1ed30ee5/codex/tests-pass-docs-stale/project` | `/private/tmp/meta-intent-T17-1ed30ee5/codex/tests-pass-docs-stale/actor-input.md` | — |
| `T17/transitive-unrelated-impact` | claude | `/private/tmp/meta-intent-T17-1ed30ee5/claude/transitive-unrelated-impact/project` | `/private/tmp/meta-intent-T17-1ed30ee5/claude/transitive-unrelated-impact/actor-input.md` | — |
| `T17/transitive-unrelated-impact` | codex | `/private/tmp/meta-intent-T17-1ed30ee5/codex/transitive-unrelated-impact/project` | `/private/tmp/meta-intent-T17-1ed30ee5/codex/transitive-unrelated-impact/actor-input.md` | — |
| `T17/copied-old-evidence` | claude | `/private/tmp/meta-intent-T17-1ed30ee5/claude/copied-old-evidence/project` | `/private/tmp/meta-intent-T17-1ed30ee5/claude/copied-old-evidence/actor-input.md` | — |
| `T17/copied-old-evidence` | codex | `/private/tmp/meta-intent-T17-1ed30ee5/codex/copied-old-evidence/project` | `/private/tmp/meta-intent-T17-1ed30ee5/codex/copied-old-evidence/actor-input.md` | — |
| `T17/unchanged-idempotency` | claude | `/private/tmp/meta-intent-T17-1ed30ee5/claude/unchanged-idempotency/project` | `/private/tmp/meta-intent-T17-1ed30ee5/claude/unchanged-idempotency/actor-input.md` | `/private/tmp/meta-intent-T17-1ed30ee5/claude/unchanged-idempotency/actor-input-phase2.md` |
| `T17/unchanged-idempotency` | codex | `/private/tmp/meta-intent-T17-1ed30ee5/codex/unchanged-idempotency/project` | `/private/tmp/meta-intent-T17-1ed30ee5/codex/unchanged-idempotency/actor-input.md` | `/private/tmp/meta-intent-T17-1ed30ee5/codex/unchanged-idempotency/actor-input-phase2.md` |
| `T17/uncertain-impact` | claude | `/private/tmp/meta-intent-T17-1ed30ee5/claude/uncertain-impact/project` | `/private/tmp/meta-intent-T17-1ed30ee5/claude/uncertain-impact/actor-input.md` | — |
| `T17/uncertain-impact` | codex | `/private/tmp/meta-intent-T17-1ed30ee5/codex/uncertain-impact/project` | `/private/tmp/meta-intent-T17-1ed30ee5/codex/uncertain-impact/actor-input.md` | — |

## Two-phase cells

`generated-sync-no-loop` and `unchanged-idempotency` are defined by what happens when the same
work is entered a second time. Run phase 1 from `actor-input.md`; then, **without reusing that
session**, launch a second actor on the *same project directory* with `actor-input-phase2.md`. The
second actor must inherit only what phase 1 persisted on disk — no transcript, no summary, no hint
that a first phase existed.

## Follow-up user turns

Several cells only finish across more than one turn, and one delivers a user who pushes back on
the correct answer. When an actor asks a question, relay the question text to the evaluator and
send back the reply the evaluator supplies, verbatim. The evaluator holds the per-scenario reply
script and the pass criteria privately; relaying through the evaluator is what keeps the tested
context blind. Never improvise an answer to keep an actor moving.

## Known launch blockers (do not bypass)

- The final repaired candidate is not accepted yet; the packets must be re-exported from it first.
- New synthetic Claude projects stop at the workspace trust prompt.
- Codex quota on the previously observed account. This is a recorded observation, not a permanent
  or universal condition; recheck it at launch time rather than assuming it.

None may be worked around. A cell that cannot be launched stays `unverified` with the blocker
recorded; missing ability is never a pass.

## Return path

For each launched cell the evaluator needs: host, session identity, the raw dialog, the actor's
`receipt.json`, the tool records, and the project tree after the run. Admit identity with
`../T15/admit_evidence.py <manifest> <candidate_root> <receipt>` before any semantic judgement, and
capture the worker pages with `../T15/capture_worker.py <dispatch> <output>`. Cells stay
`unverified` until that evidence exists; one host's session is never recorded as the other host's
coverage.
