# T18 actor launch request

## Current launch binding — candidate 01146b70e1fe018effbf83dbb678277b657a3783

Candidate commit: `01146b70e1fe018effbf83dbb678277b657a3783` (main; #9–#14 audit-proved, ADR-0008 merged, 1166 unit tests green).
Packet root: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18`
Candidate tree SHA-256: `ce4a69c0f3137e0be15ec61939140b8291e5f6d6ee62ba2c4556af9de4ee81f2`
Claude entry: `candidate/claude/meta-skill/skills/bootstrap/SKILL.md`
Codex entry:  `candidate/codex/meta-skill/SKILL.md`

Every cell is `unverified` until a real host session runs it and a fresh-context evaluator
judges the raw dialogue. Deliver each cell's `actor-input.md` verbatim and nothing else.

The reference export further below (`5c02e24c`) is still **not** launch input.

Prompt files for this candidate:

- claude T18/fact-only-vs-behavior: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/claude/fact-only-vs-behavior/actor-input.md`
- codex T18/fact-only-vs-behavior: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/codex/fact-only-vs-behavior/actor-input.md`
- claude T18/accept-full-recovery: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/claude/accept-full-recovery/actor-input.md`
- codex T18/accept-full-recovery: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/codex/accept-full-recovery/actor-input.md`
- claude T18/reject-repair-full-recovery: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/claude/reject-repair-full-recovery/actor-input.md`
- codex T18/reject-repair-full-recovery: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/codex/reject-repair-full-recovery/actor-input.md`
- claude T18/defer: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/claude/defer/actor-input.md`
- codex T18/defer: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/codex/defer/actor-input.md`
- claude T18/interrupted-recovery: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/claude/interrupted-recovery/actor-input.md`
- codex T18/interrupted-recovery: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/codex/interrupted-recovery/actor-input.md`
- claude T18/unattended-conflict: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/claude/unattended-conflict/actor-input.md`
  Resume: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/claude/unattended-conflict/actor-input-phase2.md`
- codex T18/unattended-conflict: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/codex/unattended-conflict/actor-input.md`
  Resume: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/codex/unattended-conflict/actor-input-phase2.md`
- claude T18/report-only-not-done: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/claude/report-only-not-done/actor-input.md`
- codex T18/report-only-not-done: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/codex/report-only-not-done/actor-input.md`
- claude T18/stable-repeat: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/claude/stable-repeat/actor-input.md`
- codex T18/stable-repeat: `/private/tmp/meta-intent-host-campaign.pGw3c0/T18/codex/stable-repeat/actor-input.md`

Everything below this section is history. Its commit, hashes and paths are preserved as the
record of earlier preparations and failed launches; they are never launch input and no evidence
gathered against them counts for this candidate.

## Historical launch binding — superseded by the binding above

Historical prompt files:

- claude T18/fact-only-vs-behavior: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/claude/fact-only-vs-behavior/actor-input.md`
- codex T18/fact-only-vs-behavior: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/codex/fact-only-vs-behavior/actor-input.md`
- claude T18/accept-full-recovery: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/claude/accept-full-recovery/actor-input.md`
- codex T18/accept-full-recovery: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/codex/accept-full-recovery/actor-input.md`
- claude T18/reject-repair-full-recovery: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/claude/reject-repair-full-recovery/actor-input.md`
- codex T18/reject-repair-full-recovery: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/codex/reject-repair-full-recovery/actor-input.md`
- claude T18/defer: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/claude/defer/actor-input.md`
- codex T18/defer: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/codex/defer/actor-input.md`
- claude T18/interrupted-recovery: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/claude/interrupted-recovery/actor-input.md`
- codex T18/interrupted-recovery: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/codex/interrupted-recovery/actor-input.md`
- claude T18/unattended-conflict: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/claude/unattended-conflict/actor-input.md`
  Resume: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/claude/unattended-conflict/actor-input-phase2.md`
- codex T18/unattended-conflict: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/codex/unattended-conflict/actor-input.md`
  Resume: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/codex/unattended-conflict/actor-input-phase2.md`
- claude T18/report-only-not-done: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/claude/report-only-not-done/actor-input.md`
- codex T18/report-only-not-done: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/codex/report-only-not-done/actor-input.md`
- claude T18/stable-repeat: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/claude/stable-repeat/actor-input.md`
- codex T18/stable-repeat: `/private/tmp/meta-intent-host-campaign.XX6yRo/T18/codex/stable-repeat/actor-input.md`

Candidate `e30ccc7cec9120815f0d9bc92204adf465f666d4` includes accepted #9–#14
implementation and main `4e34c684`. Fresh packet root:
`/private/tmp/meta-intent-host-campaign.XX6yRo/T18`.
Candidate tree SHA-256:
`c1114a94d89c2ea8d8e7bc8c496576b9750957e347769980dc75dee006704fc4`.

Use the current `results.json` cell paths and this root's manifest, never the old
paths below. Every cell remains unverified. Historical trust/quota observations
must be revalidated on these projects; do not bypass a security prompt. Deliver
the entire current cell's actor-input.md verbatim. The remaining text preserves
the original preparation history and the unchanged blind-testing protocol.

Prepared by the dispatched T18 worker (evaluation role). **The coordinator alone launches the
scenario actors.** This file carries only launch inputs; the evaluator oracle and the scripted user
replies stay in `evaluator-private.md` and are never sent to a tested context.

## Do not launch this export

The export described below is bound to `5c02e24cf993c36591458f87f1c7dcfb66be3a35`, a development
reference for the external-change API only. That commit was never accepted. Do not launch actors
against it and do not record evidence from it.

The four steps this section required before any actor runs are now satisfied by the current
launch binding at the top of this file, and only by it:

1. Take the fixed, accepted `#14` candidate commit — `01146b70e1fe018effbf83dbb678277b657a3783`.
2. Re-export: `python3 prepare_packets.py <new packet root> --candidate <fixed sha>` — done into
   `/private/tmp/meta-intent-host-campaign.pGw3c0/T18`.
3. Record the new packet root, the new candidate tree SHA-256 and both entry SHA-256 values in
   `results.json` (`launch_candidate`, `launch_candidate_tree_sha256`, `launch_packet_root`) — done.
4. Launch from the regenerated cell paths, not from the reference paths below.

## Reference export (preparation output, not launch input)

- Reference commit: `5c02e24cf993c36591458f87f1c7dcfb66be3a35` — **not accepted**
- Reference root: `/private/tmp/meta-intent-T18-5c02e24c/candidate`
- Reference tree SHA-256: `ef02cd1aa0f078c89dcc5689f5b1c8af8e24e9a490863af5f139ae09cc292bfb`
- Manifest: `/private/tmp/meta-intent-T18-5c02e24c/candidate-manifest.json`
- Claude entry: `candidate/claude/meta-skill/skills/bootstrap/SKILL.md`
  SHA-256 `1741fbc13f23108c0ae79205521b40679e02859de467f8dee6978e28bf63baf5`
- Codex entry: `candidate/codex/meta-skill/SKILL.md`
  SHA-256 `526dc0958a9c174a07d9b98d54de8cd1f2561790dbbf759853b45e13086c6065`

## What to send each actor

Send the **entire contents of that cell's prompt file, byte for byte, and nothing else**. It already
names the candidate entry, the candidate root, the project path, the receipt path, the no-install
rule and the single user turn. Do not add the scenario name, the requirement ids, this file, the
issue text, other cells' material, or any expectation of the outcome.

Each actor needs a fresh context and an independent session identity, and must be able to reach the
coordinator with its dispatch `ask` command.

## Cells (reference paths; regenerate before launching)

| Scenario | Host | Project | Prompt file | Second-phase prompt |
|---|---|---|---|---|
| `T18/fact-only-vs-behavior` | claude | `/private/tmp/meta-intent-T18-5c02e24c/claude/fact-only-vs-behavior/project` | `/private/tmp/meta-intent-T18-5c02e24c/claude/fact-only-vs-behavior/actor-input.md` | — |
| `T18/fact-only-vs-behavior` | codex | `/private/tmp/meta-intent-T18-5c02e24c/codex/fact-only-vs-behavior/project` | `/private/tmp/meta-intent-T18-5c02e24c/codex/fact-only-vs-behavior/actor-input.md` | — |
| `T18/accept-full-recovery` | claude | `/private/tmp/meta-intent-T18-5c02e24c/claude/accept-full-recovery/project` | `/private/tmp/meta-intent-T18-5c02e24c/claude/accept-full-recovery/actor-input.md` | — |
| `T18/accept-full-recovery` | codex | `/private/tmp/meta-intent-T18-5c02e24c/codex/accept-full-recovery/project` | `/private/tmp/meta-intent-T18-5c02e24c/codex/accept-full-recovery/actor-input.md` | — |
| `T18/reject-repair-full-recovery` | claude | `/private/tmp/meta-intent-T18-5c02e24c/claude/reject-repair-full-recovery/project` | `/private/tmp/meta-intent-T18-5c02e24c/claude/reject-repair-full-recovery/actor-input.md` | — |
| `T18/reject-repair-full-recovery` | codex | `/private/tmp/meta-intent-T18-5c02e24c/codex/reject-repair-full-recovery/project` | `/private/tmp/meta-intent-T18-5c02e24c/codex/reject-repair-full-recovery/actor-input.md` | — |
| `T18/defer` | claude | `/private/tmp/meta-intent-T18-5c02e24c/claude/defer/project` | `/private/tmp/meta-intent-T18-5c02e24c/claude/defer/actor-input.md` | — |
| `T18/defer` | codex | `/private/tmp/meta-intent-T18-5c02e24c/codex/defer/project` | `/private/tmp/meta-intent-T18-5c02e24c/codex/defer/actor-input.md` | — |
| `T18/interrupted-recovery` | claude | `/private/tmp/meta-intent-T18-5c02e24c/claude/interrupted-recovery/project` | `/private/tmp/meta-intent-T18-5c02e24c/claude/interrupted-recovery/actor-input.md` | — |
| `T18/interrupted-recovery` | codex | `/private/tmp/meta-intent-T18-5c02e24c/codex/interrupted-recovery/project` | `/private/tmp/meta-intent-T18-5c02e24c/codex/interrupted-recovery/actor-input.md` | — |
| `T18/unattended-conflict` | claude | `/private/tmp/meta-intent-T18-5c02e24c/claude/unattended-conflict/project` | `/private/tmp/meta-intent-T18-5c02e24c/claude/unattended-conflict/actor-input.md` | `/private/tmp/meta-intent-T18-5c02e24c/claude/unattended-conflict/actor-input-phase2.md` |
| `T18/unattended-conflict` | codex | `/private/tmp/meta-intent-T18-5c02e24c/codex/unattended-conflict/project` | `/private/tmp/meta-intent-T18-5c02e24c/codex/unattended-conflict/actor-input.md` | `/private/tmp/meta-intent-T18-5c02e24c/codex/unattended-conflict/actor-input-phase2.md` |
| `T18/report-only-not-done` | claude | `/private/tmp/meta-intent-T18-5c02e24c/claude/report-only-not-done/project` | `/private/tmp/meta-intent-T18-5c02e24c/claude/report-only-not-done/actor-input.md` | — |
| `T18/report-only-not-done` | codex | `/private/tmp/meta-intent-T18-5c02e24c/codex/report-only-not-done/project` | `/private/tmp/meta-intent-T18-5c02e24c/codex/report-only-not-done/actor-input.md` | — |
| `T18/stable-repeat` | claude | `/private/tmp/meta-intent-T18-5c02e24c/claude/stable-repeat/project` | `/private/tmp/meta-intent-T18-5c02e24c/claude/stable-repeat/actor-input.md` | — |
| `T18/stable-repeat` | codex | `/private/tmp/meta-intent-T18-5c02e24c/codex/stable-repeat/project` | `/private/tmp/meta-intent-T18-5c02e24c/codex/stable-repeat/actor-input.md` | — |

## The two-phase cell

`unattended-conflict` is defined by what survives a context boundary. Run phase 1 from
`actor-input.md`; then, **without reusing that session**, launch a second actor on the *same project
directory* with `actor-input-phase2.md`. The second actor must inherit only what phase 1 persisted on
disk — no transcript, no summary, no hint that a first phase existed.

## Follow-up user turns

Most cells only finish across more than one turn. When an actor asks a question, relay the question
text to the evaluator and send back the reply the evaluator supplies, verbatim. The evaluator holds
the per-scenario reply script and the pass criteria privately; relaying through the evaluator is what
keeps the tested context blind. For some cells the correct action is to send **no reply at all** —
the evaluator will say so; do not improvise an answer to keep an actor moving.

## Known launch blockers (do not bypass, do not assume)

Two blockers stopped earlier launches. They are recorded as **historic and unrevalidated**: neither
may be reported as a current fact without being rechecked at launch time.

- New synthetic Claude projects previously stopped at the workspace trust prompt. Recheck by opening
  one regenerated cell project on a real Claude host and recording what actually happens.
- Codex launches were previously refused for quota. Recheck by attempting one regenerated Codex cell
  and recording the actual response.

Neither may be worked around. A cell that cannot be launched stays `unverified` with the observed
blocker recorded; missing ability is never a pass.

## Return path

For each launched cell the evaluator needs: host, session identity, the raw dialog, the actor's
`receipt.json`, the tool records, and the project tree after the run. Admit identity with
`../T15/admit_evidence.py <manifest> <candidate_root> <receipt>` against the **regenerated** manifest
before any semantic judgement. Cells stay `unverified` until that evidence exists; one host's session
is never recorded as the other host's coverage.
