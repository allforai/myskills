# T18 actor launch request

Prepared by the dispatched T18 worker (evaluation role). **The coordinator alone launches the
scenario actors.** This file carries only launch inputs; the evaluator oracle and the scripted user
replies stay in `evaluator-private.md` and are never sent to a tested context.

## Do not launch this export

`#14` is under active production repair and is **not accepted**. The export described below is bound
to `5c02e24cf993c36591458f87f1c7dcfb66be3a35`, a development reference for the external-change API
only. Do not launch actors against it and do not record evidence from it.

Before any actor runs:

1. Take the fixed, accepted `#14` candidate commit.
2. Re-export: `python3 prepare_packets.py <new packet root> --candidate <fixed sha>`.
3. Record the new packet root, the new candidate tree SHA-256 and both entry SHA-256 values in
   `results.json` (`launch_candidate`, `launch_candidate_tree_sha256`, `launch_packet_root`).
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
