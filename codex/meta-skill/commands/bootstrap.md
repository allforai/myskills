---
description: "Analyze the target project and generate Codex-native bootstrap products plus a generated run entry."
---

# Bootstrap

## Path Convention

All paths are relative to this plugin root: `codex/meta-skill/`.

## Codex Adapter Rule

The canonical bootstrap protocol lives at:

- `./skills/bootstrap.md`

That adapter file binds the shared meta-skill protocol to Codex by applying these rules:

- use `workflow.json` as the canonical bootstrap graph
- write the generated run entry to `.codex/commands/run.md`
- resolve plugin assets through repository-relative paths instead of a Claude-specific plugin-root variable
- standardize generated `node-specs/*.md` around `## Spec / ## Design / ## Task` sections during Phase 1 migration
- when the project is clearly a replication / migration workflow, prefer implementation-oriented parity nodes over long planning-only chains

## Execution

Read `./skills/bootstrap.md` and follow its protocol.
