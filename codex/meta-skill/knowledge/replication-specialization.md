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
- user goal contains `还原`, `高还原`, `faithful`, `像原版`, `mobile`, `手游`, or similar fidelity language
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

If the repository already contains recent parity reports, validation notes, or acceptance documents,
bootstrap should treat them as evidence inputs and move quickly to the next repair or fidelity slice
instead of generating multiple "preserve current baseline" nodes.

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

When the source product is mobile-first and UI fidelity matters, the workflow must also cover:

8. capture source UI structure and interaction evidence before UI implementation
9. preserve source information architecture and touch-first interaction assumptions unless the user explicitly allows adaptation
10. verify UI fidelity separately from generic runtime validation

These are logical responsibilities. The LLM may choose any node count or naming scheme, but it may not erase these responsibilities by folding them into a broad "port runtime" or "validate parity" node with no explicit UI-fidelity contract.

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

For mobile high-fidelity replication, prefer this upgraded shape:

1. `lock-replication-boundary`
2. `map-legacy-evidence`
3. `capture-mobile-ui-evidence`
4. `expand-parity-coverage`
5. `port-core-runtime`
6. `implement-ui-fidelity-slice`
7. `verify-ui-fidelity`
8. `validate-local-runtime`
9. `parity-acceptance`

Equivalent names are acceptable if the responsibilities remain explicit.

Important:

- the upgraded shape is an example, not a mandatory fixed node list
- what is mandatory is the presence of distinct source-evidence, source-led UI implementation, and UI verification responsibilities
- if the LLM chooses fewer nodes, each merged node must still make those responsibilities explicit in both acceptance criteria and tasks
- if the repository already has current parity and validation artifacts, skip redundant baseline-documentation nodes unless those artifacts are stale or contradictory

## Guardrails

- Do not turn a replication project into a fresh product-design exercise.
- Do not prioritize backend redesign when the stable backend is already declared.
- Do not spend multiple early nodes restating the same migration boundary.
- Do not omit direct implementation nodes once enough evidence exists.
- Prefer parity reports that point to concrete implementation work, not just audits.
- Do not replace a mobile source UI with a desktop-first dashboard, browser-native overlay, or free-form control panel unless the user explicitly asks for adaptation.
- Do not treat "same features exist" as sufficient evidence of UI parity.
- Do not let the target runtime or rendering stack dictate the information architecture when fidelity is the stated goal.
- Do not narrow the user's objective from "faithful mobile-client reproduction" to "playable slice" unless the user explicitly approves that scope reduction.
- Do not let concrete target file guesses prematurely freeze the implementation before UI evidence responsibilities have been satisfied.
- Do not insert multiple documentation-only baseline nodes ahead of the next repair slice when the current repository already has usable parity evidence.

## Node-Spec Upgrades

When this specialization is active, generated node-specs should emphasize:

- source evidence files or modules
- target surfaces to update
- fidelity constraints
- explicit non-goals
- runnable verification signals

For UI-related replication nodes, generated node-specs should also emphasize:

- source platform and input model
- screen hierarchy and page-entry relationships
- overlay versus full-screen behavior in the source
- forbidden redesign moves
- explicit deviation logs for anything that is still not matched

Implementation-oriented node-specs should usually answer:

- what source behavior is being reproduced
- where that behavior should live in the target
- what counts as parity for this node
- what local smoke or artifact proves completion

UI fidelity nodes should additionally answer:

- which source screens or flows are being matched
- which target surfaces must stay structurally aligned
- which touch interactions or state transitions must remain source-native
- what evidence proves structural or visual fidelity beyond raw functionality

## Validation Rules

When replication / migration specialization is triggered:

- the workflow must contain at least one implementation-oriented parity node
- the workflow must not consist entirely of planning / audit nodes
- at least one node must target runtime or behavioral porting
- at least one node must target user-facing parity
- at least one node must validate a runnable local path
- if the source is mobile-first and UI fidelity matters, at least one node must capture UI evidence before implementation
- if the source is mobile-first and UI fidelity matters, at least one node must verify UI fidelity separately from runtime validation
- if `design_freedom = none`, UI implementation nodes must be framed as source-led reproduction, not reinterpretation
- if the source is mobile-first and UI fidelity matters, the workflow may not consist only of boundary -> backlog -> runtime implementation -> runtime validation -> acceptance; it must include explicit UI-fidelity responsibilities beyond generic playability checks
- if recent parity reports already exist, no more than one lightweight refresh node should appear before the next implementation or repair node unless stale evidence truly blocks execution
