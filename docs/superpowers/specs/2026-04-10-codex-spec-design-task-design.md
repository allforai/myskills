# Codex Meta-Skill Spec / Design / Task Protocol

Date: 2026-04-10
Status: Draft
Scope: `codex/meta-skill` only

## Goal

Evolve the current Codex bootstrap contract from:

- `workflow.json`
- `node-specs/*.md`

into a clearer three-layer protocol:

- `spec`
- `design`
- `task`

without breaking the current runnable surface.

## Current Problem

Today each generated `node-spec` carries three responsibilities at once:

1. specification
2. solution/design reasoning
3. executable task contract

This works for small flows, but causes drift in larger workflows:

- acceptance rules mix with implementation notes
- design tradeoffs are hard to update without mutating the spec itself
- runtime task retries have no clean, separate execution contract
- failed and retried work is only visible in `transition_log`, not in task artifacts

## Desired Model

### 1. Workflow Layer

`workflow.json` remains the orchestration contract.

It should continue to define:

- `id`
- `goal`
- `exit_artifacts`
- `transition_log`

It should not become the place for design rationale or task instructions.

### 2. Spec Layer

Each node gets a stable specification artifact:

- `.allforai/bootstrap/specs/<node-id>.md`

Purpose:

- define the node contract
- define required outputs
- define acceptance / invariants / failure modes
- remain relatively stable across retries

The spec answers:

- what must be true when this node is done
- what evidence is in scope
- what artifacts are required
- what constraints cannot be violated

### 3. Design Layer

Each node may get a design artifact:

- `.allforai/bootstrap/designs/<node-id>.md`

Purpose:

- record the current proposed approach
- capture tradeoffs and alternatives
- let design evolve without rewriting the spec

The design answers:

- how this node is currently intended to be solved
- why this approach was chosen
- which alternatives were rejected
- which open risks remain

This file is optional for trivial nodes and expected for non-trivial nodes.

### 4. Task Layer

Each node gets an execution contract artifact:

- `.allforai/bootstrap/tasks/<node-id>.md`

Purpose:

- translate spec + design into current executable work
- define the concrete next action
- support retries, decomposition, and incremental execution

The task answers:

- what to do now
- what files or systems to inspect or modify
- what local checks to run
- what completion signal to record

This is the most volatile layer.

## Compatibility Rule

The current `node-specs/*.md` remain the canonical runtime input during migration.

Phase 1 compatibility model:

- `node-specs/<node-id>.md` stays required
- bootstrap may additionally emit:
  - `specs/<node-id>.md`
  - `designs/<node-id>.md`
  - `tasks/<node-id>.md`

During this phase:

- `node-spec` acts as the compatibility envelope
- `spec/design/task` act as internal split artifacts

The generated run entry should continue to read `node-specs/` first until migration is complete.

## Recommended Migration Shape

### Phase 1: Structured Node-Spec

Keep one file, but standardize three sections:

- `## Spec`
- `## Design`
- `## Task`

This is the lowest-risk upgrade because it preserves current runtime behavior.

Recommended body shape:

```md
---
node: infer-product-shape
---

# Node

## Spec

- goal
- required evidence
- required exit artifacts
- invariants / acceptance

## Design

- proposed approach
- alternatives considered
- major tradeoffs
- open risks

## Task

- immediate actions
- concrete file targets
- local verification
- completion marker
```

### Phase 2: Dual Write

Bootstrap writes both:

- `node-specs/<node-id>.md`
- `specs/<node-id>.md`
- `designs/<node-id>.md`
- `tasks/<node-id>.md`

Rules:

- `node-spec` becomes a generated compatibility summary
- `spec/design/task` become the internal source-of-truth

### Phase 3: Run Upgrade

Generated run logic changes from:

- read `node-specs/<node-id>.md`

to:

1. read `specs/<node-id>.md`
2. if present, read `designs/<node-id>.md`
3. read `tasks/<node-id>.md`
4. execute the task contract

`node-specs/` can then be deprecated or retained as a generated human-readable bundle.

## File Responsibilities

### Spec File

Minimum required sections:

- `Goal`
- `Inputs / Evidence`
- `Exit Artifacts`
- `Acceptance`
- `Failure Modes`

### Design File

Minimum recommended sections:

- `Approach`
- `Tradeoffs`
- `Alternatives`
- `Open Risks`

### Task File

Minimum required sections:

- `Immediate Objective`
- `Actions`
- `Target Files / Surfaces`
- `Checks`
- `Completion Condition`

## Runtime Semantics

### Spec

Stable over retries.

Should only change when:

- goals change
- acceptance changes
- scope changes

### Design

Mutable across retries.

Should change when:

- a better approach is found
- a prior design fails
- newly discovered evidence changes the plan

### Task

Highly mutable.

Should change when:

- the node is retried
- the work is split
- the next concrete action changes

## Transition Log Relationship

`transition_log` remains attached to `workflow.json`, but the three-layer model clarifies what each transition refers to:

- `spec` says what completion means
- `design` says how the attempt was planned
- `task` says what was actually attempted
- `transition_log` records the outcome

This makes failed recovery cleaner:

- failed task does not imply failed spec
- failed design can be replaced without rewriting the node goal
- completed transition can point to artifacts that satisfy the spec even after earlier failed tasks

## Product-Inference Example

For node `infer-product-shape`:

- `specs/infer-product-shape.md`
  - define evidence requirements and output schema for `product-summary.json`
- `designs/infer-product-shape.md`
  - explain why protocol + UI + runtime evidence are enough for current inference
- `tasks/infer-product-shape.md`
  - tell Codex to inspect `Launch.ts`, `main_appd.lua`, `roc.msg`, and selected UI pages now

This is cleaner than storing all three ideas in one freeform `node-spec`.

## Validation Implications

Phase 1 validators should only require:

- `workflow.json`
- `node-specs/*.md`

Optional additive validators may check:

- `specs/*.md`
- `designs/*.md`
- `tasks/*.md`

Phase 2 validators should add:

- node ids match across all emitted layers
- `tasks/<node-id>.md` exists for executable nodes
- `specs/<node-id>.md` includes acceptance language
- `designs/<node-id>.md` is optional, but required for high-risk or non-trivial nodes

## Codex-Specific Recommendation

Codex should adopt the following migration path:

1. standardize `## Spec / ## Design / ## Task` sections inside current node-specs
2. add optional dual-write for `specs/`, `designs/`, `tasks/`
3. keep generated run on `node-specs/` until compatibility checks are stable
4. only then upgrade run to read split artifacts directly

This gives Codex the benefits of a cleaner protocol without destabilizing the current bootstrap surface.

## Acceptance For This Design

This design is successful if:

- Codex can keep current `workflow.json + node-specs` compatibility
- future work can separate stable spec from mutable design/task state
- retries and failures become easier to reason about
- product-inference, high-risk specialization, and future domain hooks all have a cleaner place to attach design rationale without bloating the spec
