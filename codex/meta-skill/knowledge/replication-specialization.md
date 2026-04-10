# Replication / Migration Specialization (Codex)

> Codex-only bootstrap guidance for projects whose primary goal is to reproduce,
> port, or migrate an existing product or client with high fidelity.

## When to Trigger

Apply this specialization when the project intent is clearly one of:

- deep reproduction / high-parity rewrite
- legacy-to-new-stack client migration
- porting an existing app, module, or runtime while keeping another surface stable
- rebuilding behavior from a read-only evidence source

Common evidence signals:

- user goal contains `replicate`, `复刻`, `migration`, `port`, `parity`, `rewrite client`
- repository docs mention `legacy`, `migration plan`, `parity report`, `evidence source`
- there is an explicit old project path or read-only reference repo
- the target repo keeps one runtime stable while replacing another

Examples:

- keep existing backend, rewrite client in a new engine
- keep service contracts, replace frontend stack
- port a legacy app into a new runtime without inventing new features

## Core Principle

Research first, then execute.

Do not spend the entire workflow on planning documents once the rewrite boundary is
clear. A replication workflow should usually have:

1. one boundary-lock node
2. one evidence/parity capture node
3. direct implementation nodes
4. runtime/parity validation

The workflow may still include analysis artifacts, but analysis must serve execution.

## Mandatory Responsibility Floor

Once replication / migration intent is confirmed, the generated workflow must cover
all of these responsibilities:

1. lock the rewrite boundary
2. map legacy evidence to target surfaces
3. identify parity gaps between source and target
4. port or reproduce the core runtime behavior
5. port or reproduce the core user-facing flows
6. validate local runnable parity on at least one end-to-end path
7. record remaining fidelity gaps and non-goals

These are responsibilities, not exact node names.

## Preferred Workflow Shape

For replication projects, bootstrap should prefer implementation-oriented node shapes
over a long planning chain.

Recommended progression:

1. `lock-replication-boundary`
   - freeze what remains stable
   - freeze what is being rewritten
   - freeze what acts as evidence only
2. `map-legacy-evidence`
   - extract gameplay / UI / protocol / asset responsibilities from the source
3. `expand-parity-coverage`
   - identify the concrete missing target capabilities
4. `port-core-runtime`
   - implement the core interactive or business loop
5. `port-ui-and-progression`
   - implement the main user-facing progression and control flows
6. `validate-local-runtime`
   - verify one repeatable local end-to-end path
7. `parity-acceptance`
   - summarize achieved fidelity, remaining gaps, and next repair targets

Equivalent names are acceptable if the responsibilities remain explicit.

## Guardrails

- Do not turn a replication project into a fresh product-design exercise.
- Do not prioritize backend redesign when the stable backend is already declared.
- Do not spend multiple early nodes restating the same migration boundary.
- Do not omit direct implementation nodes once enough evidence exists.
- Prefer parity reports that point to concrete implementation work, not just audits.

## Node-Spec Upgrades

When this specialization is active, generated node-specs should emphasize:

- source evidence files or modules
- target surfaces to update
- fidelity constraints
- explicit non-goals
- runnable verification signals

Implementation-oriented node-specs should usually answer:

- what source behavior is being reproduced
- where that behavior should live in the target
- what counts as parity for this node
- what local smoke or artifact proves completion

## Validation Rules

When replication / migration specialization is triggered:

- the workflow must contain at least one implementation-oriented parity node
- the workflow must not consist entirely of planning / audit nodes
- at least one node must target runtime or behavioral porting
- at least one node must target user-facing parity
- at least one node must validate a runnable local path
