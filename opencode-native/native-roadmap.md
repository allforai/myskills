# OpenCode Native Roadmap

This roadmap defines the order for turning wrapper coverage into real
OpenCode-friendly execution support.

## Phase 1: Read-heavy native workflows

Priority:

1. `code-tuner` (playbook added)
2. `ui-forge` (playbook added)
3. `code-replicate` (playbook added)

Goal:

- Convert wrapper-only usage into repeatable OpenCode-friendly execution playbooks.
- Keep source plugin outputs and artifact contracts stable.

## Phase 2: Orchestrated workflows

Priority:

1. `product-design` (playbook added)
2. `dev-forge` (playbook added)
3. `demo-forge` (playbook added)

Goal:

- Replace host-specific orchestration semantics with OpenCode operating rules.
- Explicitly document dependency checks, user decision points, and downgrade
  paths.

## Phase 3: Shared-core extraction

Goal:

- Move reusable docs, schemas, and scripts into a shared core only after the
  wrappers have proven stable.
- Leave existing Claude/OpenCode paths intact through adapter shells.

