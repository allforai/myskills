# T15 actor launch request

## Launch suspended — candidate acceptance withdrawn

Do not launch the packets listed below. Later host evaluations and repair reviews
found unresolved production defects. Their old commit, hashes and paths remain
historical evidence, not permission for new launches or pass admission. After the
repairs are accepted, regenerate and re-fingerprint a fresh candidate, update the
bindings, and rerun the required host scenarios. See `results.json` field
`candidate_acceptance_withdrawal` and `../T15-coordinator-boundary-review.md`.

## Historical launch binding — superseded by the suspension above

Historical prompt files:

- claude T15/large-code-local-button: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/claude/large-code-local-button/actor-input.md`
- codex T15/large-code-local-button: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/codex/large-code-local-button/actor-input.md`
- claude T15/missing-product-docs: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/claude/missing-product-docs/actor-input.md`
- codex T15/missing-product-docs: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/codex/missing-product-docs/actor-input.md`
- claude T15/reshape-business-model: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/claude/reshape-business-model/actor-input.md`
- codex T15/reshape-business-model: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/codex/reshape-business-model/actor-input.md`
- claude T15/add-unimplemented-need: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/claude/add-unimplemented-need/actor-input.md`
- codex T15/add-unimplemented-need: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/codex/add-unimplemented-need/actor-input.md`
- claude T15/deny-inferred-intent: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/claude/deny-inferred-intent/actor-input.md`
- codex T15/deny-inferred-intent: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/codex/deny-inferred-intent/actor-input.md`
- claude T15/interrupted-confirmation: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/claude/interrupted-confirmation/actor-input.md`
- codex T15/interrupted-confirmation: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/codex/interrupted-confirmation/actor-input.md`
- claude T15/new-product: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/claude/new-product/actor-input.md`
- codex T15/new-product: `/private/tmp/meta-intent-host-campaign.XX6yRo/T15/codex/new-product/actor-input.md`

Candidate `e30ccc7cec9120815f0d9bc92204adf465f666d4` includes accepted #9–#14
implementation and main `4e34c684`. Fresh packet root:
`/private/tmp/meta-intent-host-campaign.XX6yRo/T15`.
Candidate tree SHA-256:
`c1114a94d89c2ea8d8e7bc8c496576b9750957e347769980dc75dee006704fc4`.

Use the current `results.json` cell paths and this root's manifest, never the old
paths below. Every cell remains unverified. Historical trust/quota observations
must be revalidated on these projects; do not bypass a security prompt. Deliver
the entire current cell's actor-input.md verbatim. The remaining text preserves
the original preparation history and the unchanged blind-testing protocol.

Prepared by the dispatched T15 worker (evaluation role). **The coordinator alone launches
the scenario actors.** This file carries only launch inputs; evaluator oracles stay private
and are never sent to a tested context.

## Candidate under test

- Accepted producer commit: `ed430dfcebed485b913b54d7785f02cc86998303`
- Exported candidate root: `/private/tmp/meta-intent-T15-ed430dfc/candidate`
- Candidate tree SHA-256: `27d6e62247293dbe1829b48b8741582290d718718c87ddc57eb6bbc26b8e4eb5`
- Manifest: `/private/tmp/meta-intent-T15-ed430dfc/candidate-manifest.json`
- Claude entry: `candidate/claude/meta-skill/skills/bootstrap/SKILL.md`
  SHA-256 `e7b83dd16490d8fbcf77c9c541ee59ffcf648cba2fdabd3eae6198009fc09068`
- Codex entry: `candidate/codex/meta-skill/SKILL.md`
  SHA-256 `526dc0958a9c174a07d9b98d54de8cd1f2561790dbbf759853b45e13086c6065`

The superseded `/private/tmp/meta-intent-T15-88e7beca` preparation carries zero host proof
and must not be launched.

## What to send each actor

Send the **entire contents of that cell's `actor-input.md`, byte for byte, and nothing else**.
It already names the candidate entry, candidate root, project path, receipt path, the
no-install rule, and the single user turn. Do not add the scenario name, the requirement
ids, this file, the issue text, other cells' material, or any expectation of the outcome.

Each actor needs a fresh context and an independent session identity, and must be able to
reach the coordinator with its dispatch `ask` command.

## Cells

| Scenario | Host | Project | Prompt file |
|---|---|---|---|
| `T15/large-code-local-button` | claude | `/private/tmp/meta-intent-T15-ed430dfc/claude/large-code-local-button/project` | `/private/tmp/meta-intent-T15-ed430dfc/claude/large-code-local-button/actor-input.md` |
| `T15/large-code-local-button` | codex | `/private/tmp/meta-intent-T15-ed430dfc/codex/large-code-local-button/project` | `/private/tmp/meta-intent-T15-ed430dfc/codex/large-code-local-button/actor-input.md` |
| `T15/missing-product-docs` | claude | `/private/tmp/meta-intent-T15-ed430dfc/claude/missing-product-docs/project` | `/private/tmp/meta-intent-T15-ed430dfc/claude/missing-product-docs/actor-input.md` |
| `T15/missing-product-docs` | codex | `/private/tmp/meta-intent-T15-ed430dfc/codex/missing-product-docs/project` | `/private/tmp/meta-intent-T15-ed430dfc/codex/missing-product-docs/actor-input.md` |
| `T15/reshape-business-model` | claude | `/private/tmp/meta-intent-T15-ed430dfc/claude/reshape-business-model/project` | `/private/tmp/meta-intent-T15-ed430dfc/claude/reshape-business-model/actor-input.md` |
| `T15/reshape-business-model` | codex | `/private/tmp/meta-intent-T15-ed430dfc/codex/reshape-business-model/project` | `/private/tmp/meta-intent-T15-ed430dfc/codex/reshape-business-model/actor-input.md` |
| `T15/add-unimplemented-need` | claude | `/private/tmp/meta-intent-T15-ed430dfc/claude/add-unimplemented-need/project` | `/private/tmp/meta-intent-T15-ed430dfc/claude/add-unimplemented-need/actor-input.md` |
| `T15/add-unimplemented-need` | codex | `/private/tmp/meta-intent-T15-ed430dfc/codex/add-unimplemented-need/project` | `/private/tmp/meta-intent-T15-ed430dfc/codex/add-unimplemented-need/actor-input.md` |
| `T15/deny-inferred-intent` | claude | `/private/tmp/meta-intent-T15-ed430dfc/claude/deny-inferred-intent/project` | `/private/tmp/meta-intent-T15-ed430dfc/claude/deny-inferred-intent/actor-input.md` |
| `T15/deny-inferred-intent` | codex | `/private/tmp/meta-intent-T15-ed430dfc/codex/deny-inferred-intent/project` | `/private/tmp/meta-intent-T15-ed430dfc/codex/deny-inferred-intent/actor-input.md` |
| `T15/interrupted-confirmation` | claude | `/private/tmp/meta-intent-T15-ed430dfc/claude/interrupted-confirmation/project` | `/private/tmp/meta-intent-T15-ed430dfc/claude/interrupted-confirmation/actor-input.md` |
| `T15/interrupted-confirmation` | codex | `/private/tmp/meta-intent-T15-ed430dfc/codex/interrupted-confirmation/project` | `/private/tmp/meta-intent-T15-ed430dfc/codex/interrupted-confirmation/actor-input.md` |
| `T15/new-product` | claude | `/private/tmp/meta-intent-T15-ed430dfc/claude/new-product/project` | `/private/tmp/meta-intent-T15-ed430dfc/claude/new-product/actor-input.md` |
| `T15/new-product` | codex | `/private/tmp/meta-intent-T15-ed430dfc/codex/new-product/project` | `/private/tmp/meta-intent-T15-ed430dfc/codex/new-product/actor-input.md` |

## Follow-up user turns

Several scenarios only finish across more than one turn, and one scenario is defined by
being interrupted before confirmation. When an actor asks a question, relay the question
text to the evaluator and send back the reply the evaluator supplies verbatim. The
evaluator holds the per-scenario reply script and the pass criteria privately, so relaying
through the evaluator is what keeps the tested context blind.

## Return path

For each launched cell the evaluator needs: host, session identity, the raw dialog, the
actor's `receipt.json`, the tool records, and the project tree after the run. Cells stay
`unverified` until that evidence exists; a Claude session is never recorded as Codex
coverage.
