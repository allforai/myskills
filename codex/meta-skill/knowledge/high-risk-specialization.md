# High-Risk Specialization Hook (Codex)

> Codex-only bootstrap hook for domains where generic planning regularly underestimates hidden complexity.

## Purpose

Bootstrap should remain research-first and LLM-driven for most projects.

However, some domains have a repeated failure pattern:

- the first workflow draft looks superficially complete
- critical infrastructure or consistency responsibilities are omitted
- Step 3.5 or late verification discovers the omissions too late

For these domains, bootstrap should apply a **high-risk specialization hook**.

## Hook Semantics

When a project matches a high-risk domain:

1. research first: study the real project and product shape before freezing workflow assumptions
2. let the LLM infer the workflow from evidence
3. inject a minimum responsibility floor for that domain
4. validate that the generated workflow covers that floor

Important:

- the hook defines responsibilities, not exact node names
- the LLM may merge or split nodes
- the LLM may not omit the required responsibilities once the domain is confirmed

## Current Supported High-Risk Domains

### `im_realtime`

Guidance file:

- `./im-specialization.md`

Use when the product is a realtime messaging / multi-client chat system.

### `replication_migration`

Guidance file:

- `./replication-specialization.md`

Use when the project's primary goal is to reproduce, port, or migrate an existing
product or client with high fidelity.

## Future Domain Shape

Every future high-risk domain file should provide:

1. detection signals
2. mandatory logical responsibilities
3. hard validation rules
4. node-spec upgrade requirements

Suggested future candidates:

- fintech_transactional
- healthcare_workflow
- marketplace_logistics
- collaborative_editor
- streaming_media

## Bootstrap Rule

Bootstrap should:

- detect whether any high-risk domain applies
- load the corresponding specialization guidance
- append the responsibility floor at planning time
- still allow research and LLM synthesis to decide the final workflow shape

## Validation Rule

For any triggered high-risk domain:

- generated workflow must include the domain's mandatory responsibility floor
- generated node-specs must include the domain's required invariants or failure modes
