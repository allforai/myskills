# T15 actor launch request

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
