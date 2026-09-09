# T16 actor launch request

## Launch suspended — candidate acceptance withdrawn

Do not launch the packets listed below. Later host evaluations and repair reviews
found unresolved production defects. Their old commit, hashes and paths remain
historical evidence, not permission for new launches or pass admission. After the
repairs are accepted, regenerate and re-fingerprint a fresh candidate, update the
bindings, and rerun the required host scenarios. See `results.json` field
`candidate_acceptance_withdrawal` and `../T15-coordinator-boundary-review.md`.

## Historical launch binding — superseded by the suspension above

Historical prompt files:

- claude T16/no-answer: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/claude/no-answer/actor-input.md`
  Resume: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/claude/no-answer/actor-input-phase2.md`
- codex T16/no-answer: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/codex/no-answer/actor-input.md`
  Resume: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/codex/no-answer/actor-input-phase2.md`
- claude T16/partial-resume: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/claude/partial-resume/actor-input.md`
- codex T16/partial-resume: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/codex/partial-resume/actor-input.md`
- claude T16/reverse-prior-decision: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/claude/reverse-prior-decision/actor-input.md`
- codex T16/reverse-prior-decision: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/codex/reverse-prior-decision/actor-input.md`
- claude T16/legacy-provenance: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/claude/legacy-provenance/actor-input.md`
- codex T16/legacy-provenance: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/codex/legacy-provenance/actor-input.md`
- claude T16/removed-not-resurrected: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/claude/removed-not-resurrected/actor-input.md`
- codex T16/removed-not-resurrected: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/codex/removed-not-resurrected/actor-input.md`
- claude T16/discussion-preserves-source: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/claude/discussion-preserves-source/actor-input.md`
- codex T16/discussion-preserves-source: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/codex/discussion-preserves-source/actor-input.md`
- claude T16/unattended-pending: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/claude/unattended-pending/actor-input.md`
  Resume: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/claude/unattended-pending/actor-input-phase2.md`
- codex T16/unattended-pending: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/codex/unattended-pending/actor-input.md`
  Resume: `/private/tmp/meta-intent-host-campaign.XX6yRo/T16/codex/unattended-pending/actor-input-phase2.md`

Candidate `e30ccc7cec9120815f0d9bc92204adf465f666d4` includes accepted #9–#14
implementation and main `4e34c684`. Fresh packet root:
`/private/tmp/meta-intent-host-campaign.XX6yRo/T16`.
Candidate tree SHA-256:
`c1114a94d89c2ea8d8e7bc8c496576b9750957e347769980dc75dee006704fc4`.

Use the current `results.json` cell paths and this root's manifest, never the old
paths below. Every cell remains unverified. Historical trust/quota observations
must be revalidated on these projects; do not bypass a security prompt. Deliver
the entire current cell's actor-input.md verbatim. The remaining text preserves
the original preparation history and the unchanged blind-testing protocol.

Prepared by the dispatched T16 worker (evaluation role). **The coordinator alone launches the
scenario actors.** This file carries only launch inputs; the evaluator oracle and the scripted
user replies stay in `evaluator-private.md` and are never sent to a tested context.

## Candidate under test

- Accepted producer commit: `0340eccf277f6727b2b49e67a45178f1c57b9a7c`
  (`#11` implementation `d622402cb1f5cc2b34a53854deaf058c41a4c676` + boundary report
  `3c6e12019cc638153459944d91bf94279402b768`, integrated as this commit)
- Exported candidate root: `/private/tmp/meta-intent-T16-0340eccf/candidate`
- Candidate tree SHA-256: `768193be0fbb8e327eba26c4f3c4e0484b17a99b1edd1e002d646a422e917d40`
- Manifest: `/private/tmp/meta-intent-T16-0340eccf/candidate-manifest.json`
- Claude entry: `candidate/claude/meta-skill/skills/bootstrap/SKILL.md`
  SHA-256 `700729ec58f46e6411d0dc8693a3ab594b0847dc14aa67012e238ae2d1b7971e`
- Codex entry: `candidate/codex/meta-skill/SKILL.md`
  SHA-256 `526dc0958a9c174a07d9b98d54de8cd1f2561790dbbf759853b45e13086c6065`

The integration full regression was still running when this candidate was assigned, so 0340eccf is the accepted producer for testing, not final joint acceptance.

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
| `T16/no-answer` | claude | `/private/tmp/meta-intent-T16-0340eccf/claude/no-answer/project` | `/private/tmp/meta-intent-T16-0340eccf/claude/no-answer/actor-input.md` | `/private/tmp/meta-intent-T16-0340eccf/claude/no-answer/actor-input-phase2.md` |
| `T16/no-answer` | codex | `/private/tmp/meta-intent-T16-0340eccf/codex/no-answer/project` | `/private/tmp/meta-intent-T16-0340eccf/codex/no-answer/actor-input.md` | `/private/tmp/meta-intent-T16-0340eccf/codex/no-answer/actor-input-phase2.md` |
| `T16/partial-resume` | claude | `/private/tmp/meta-intent-T16-0340eccf/claude/partial-resume/project` | `/private/tmp/meta-intent-T16-0340eccf/claude/partial-resume/actor-input.md` | — |
| `T16/partial-resume` | codex | `/private/tmp/meta-intent-T16-0340eccf/codex/partial-resume/project` | `/private/tmp/meta-intent-T16-0340eccf/codex/partial-resume/actor-input.md` | — |
| `T16/reverse-prior-decision` | claude | `/private/tmp/meta-intent-T16-0340eccf/claude/reverse-prior-decision/project` | `/private/tmp/meta-intent-T16-0340eccf/claude/reverse-prior-decision/actor-input.md` | — |
| `T16/reverse-prior-decision` | codex | `/private/tmp/meta-intent-T16-0340eccf/codex/reverse-prior-decision/project` | `/private/tmp/meta-intent-T16-0340eccf/codex/reverse-prior-decision/actor-input.md` | — |
| `T16/legacy-provenance` | claude | `/private/tmp/meta-intent-T16-0340eccf/claude/legacy-provenance/project` | `/private/tmp/meta-intent-T16-0340eccf/claude/legacy-provenance/actor-input.md` | — |
| `T16/legacy-provenance` | codex | `/private/tmp/meta-intent-T16-0340eccf/codex/legacy-provenance/project` | `/private/tmp/meta-intent-T16-0340eccf/codex/legacy-provenance/actor-input.md` | — |
| `T16/removed-not-resurrected` | claude | `/private/tmp/meta-intent-T16-0340eccf/claude/removed-not-resurrected/project` | `/private/tmp/meta-intent-T16-0340eccf/claude/removed-not-resurrected/actor-input.md` | — |
| `T16/removed-not-resurrected` | codex | `/private/tmp/meta-intent-T16-0340eccf/codex/removed-not-resurrected/project` | `/private/tmp/meta-intent-T16-0340eccf/codex/removed-not-resurrected/actor-input.md` | — |
| `T16/discussion-preserves-source` | claude | `/private/tmp/meta-intent-T16-0340eccf/claude/discussion-preserves-source/project` | `/private/tmp/meta-intent-T16-0340eccf/claude/discussion-preserves-source/actor-input.md` | — |
| `T16/discussion-preserves-source` | codex | `/private/tmp/meta-intent-T16-0340eccf/codex/discussion-preserves-source/project` | `/private/tmp/meta-intent-T16-0340eccf/codex/discussion-preserves-source/actor-input.md` | — |
| `T16/unattended-pending` | claude | `/private/tmp/meta-intent-T16-0340eccf/claude/unattended-pending/project` | `/private/tmp/meta-intent-T16-0340eccf/claude/unattended-pending/actor-input.md` | `/private/tmp/meta-intent-T16-0340eccf/claude/unattended-pending/actor-input-phase2.md` |
| `T16/unattended-pending` | codex | `/private/tmp/meta-intent-T16-0340eccf/codex/unattended-pending/project` | `/private/tmp/meta-intent-T16-0340eccf/codex/unattended-pending/actor-input.md` | `/private/tmp/meta-intent-T16-0340eccf/codex/unattended-pending/actor-input-phase2.md` |

## Two-phase cells

`no-answer` and `unattended-pending` are defined by what survives a context boundary. Run phase 1
from `actor-input.md`; then, **without reusing that session**, launch a second actor on the *same
project directory* with `actor-input-phase2.md`. The second actor must inherit only what phase 1
persisted on disk — no transcript, no summary, no hint that a first phase existed.

## Follow-up user turns

Several cells only finish across more than one turn, and one is defined by being interrupted before
any answer arrives. When an actor asks a question, relay the question text to the evaluator and send
back the reply the evaluator supplies, verbatim. The evaluator holds the per-scenario reply script
and the pass criteria privately; relaying through the evaluator is what keeps the tested context
blind. For at least one cell the correct action is to send **no reply at all** — the evaluator will
say so; do not improvise an answer to keep an actor moving.

## Known launch blockers (do not bypass)

- New synthetic Claude projects stop at the workspace trust prompt.
- Codex quota.

Neither may be worked around. A cell that cannot be launched stays `unverified` with the blocker
recorded; missing ability is never a pass.

## Return path

For each launched cell the evaluator needs: host, session identity, the raw dialog, the actor's
`receipt.json`, the tool records, and the project tree after the run. Admit identity with
`../T15/admit_evidence.py <manifest> <candidate_root> <receipt>` before any semantic judgement.
Cells stay `unverified` until that evidence exists; one host's session is never recorded as the
other host's coverage.
