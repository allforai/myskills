# UI Forge Execution Playbook For Codex Native

This playbook adapts `ui-forge` into a Codex-native post-implementation UI
refinement workflow.

## When to use

Use it when:

- a frontend screen already works end-to-end
- the user wants polish, stronger visual quality, or better state design
- the implementation drifted from screenshots, tokens, or UI specs

Do not use it when:

- the page is not functionally complete
- the route does not render correctly
- the main user task still fails
- real or mock data flow is still broken
- the user is actually asking for feature implementation

If any of those blocking conditions are true, stop and route the work back to
implementation first.

## Core rule

Restore fidelity first, then polish.

Codex should always begin with a triage block before editing:

```text
Baseline: present | absent
Functional Completeness: complete | incomplete
Drift Assessment: low | medium | high
Chosen Mode: restore | polish | stop
```

Also state one guardrail line:

- what will be improved
- what will not be changed

## Inputs to inspect

Read only what is needed, in this priority order:

1. current implementation files for the target screen/component
2. `.allforai/ui-design/ui-design-spec.json` if present
3. `.allforai/ui-design/tokens.json` if present
4. `.allforai/ui-design/component-spec.json` if present
5. `.allforai/ui-design/screenshots/` if present
6. `.allforai/experience-map/experience-map.json` if needed for behavior/state

If no trusted UI baseline exists, skip restoration logic and bias toward
`polish`.

## Mode selection

### `restore`

Choose this when:

- a trusted design baseline exists
- the implementation is visibly off-baseline
- tokens, hierarchy, spacing, density, or component language drift materially

Goal:

- reduce drift against the baseline without changing business semantics

### `polish`

Choose this when:

- the screen is already broadly aligned with the intended design
- the implementation works, but feels rough or unfinished

Goal:

- improve quality and finish without introducing new design drift

### `stop`

Choose this when:

- implementation completeness is not there yet
- UI work would become a disguise for unfinished product behavior

## Execution sequence

### Step 1: Boundary and completeness

Determine:

- target route, page, component, or file scope
- whether functionality is complete
- whether a design baseline exists
- which files are the real implementation surface

### Step 2: Fidelity check

If a baseline exists, compare implementation against it at four levels:

- layout and information hierarchy
- component language and density
- token usage and styling rules
- state presentation and interaction cues

Translate drift to:

- `low`
- `medium`
- `high`

### Step 3: Read constraints

Extract only the constraints needed for the target:

- layout pattern
- token rules
- component structure
- visual hierarchy
- state behavior
- responsive expectations

### Step 4: Refine in place

Preferred fix order:

1. hierarchy
2. spacing rhythm
3. token usage
4. component affordance
5. state clarity
6. restrained polish and motion

When drift is mixed:

- Phase A: restore
- Phase B: polish

Do not let Phase B reintroduce drift.

### Step 5: Preserve product intent

Do not change:

- task flow
- field meaning
- API behavior
- routing semantics
- permissions logic

If a visual request requires one of these changes, call that out explicitly.

### Step 6: Verify

Check that:

- responsive layout still works
- visible states remain complete
- token drift did not increase
- no unnecessary duplication was introduced
- focus, contrast, labels, and feedback did not regress

## Codex translation rules

- Treat `/ui-forge` as a named workflow, not a literal command.
- Use the source skill as the behavioral reference.
- Prefer minimal, local changes over redesigns.
- Keep business logic edits out of scope unless the user explicitly broadens the
  task.

## Final response contract

After finishing, Codex should report:

1. the triage block
2. selected mode and why
3. files changed
4. restore work completed, if any
5. polish work completed, if any
6. constraints preserved
7. remaining tradeoffs or gaps
