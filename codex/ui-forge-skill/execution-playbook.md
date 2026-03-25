# UI Forge — Execution Playbook

Layer 1 orchestration for the ui-forge workflow.

## Prerequisites

- Target frontend screen or component exists and is functionally usable
- The primary user task can be completed end-to-end on the target screen

If prerequisites are not met, stop and recommend returning to implementation flow.

## Phase 1: Triage

### 1.1 Identify Target

Determine the target screen or component from the user's request. When the user
does not specify explicitly, assume the most recently modified frontend files in the
working directory. If ambiguous and no reasonable assumption can be made, ask.

### 1.2 Check Design Baseline

Look for these artifacts in order:

1. `.allforai/ui-design/ui-design-spec.json`
2. `.allforai/ui-design/tokens.json`
3. `.allforai/ui-design/component-spec.json`
4. `.allforai/ui-design/screenshots/`
5. `.allforai/experience-map/experience-map.json`

Record: baseline present or absent.

### 1.3 Assess Functional Completeness

The screen is NOT functionally complete when any of these are true:

- Main route or entry point does not render correctly
- Primary user task cannot be completed end-to-end
- Real or mocked data flow is still broken
- Loading / empty / error states are missing for the main path
- Core actions exist visually but are not wired to real behavior

If incomplete, stop. Do not use UI refinement to hide unfinished implementation.

### 1.4 Report Triage

Output this block before any editing:

```
Baseline: present | absent
Functional Completeness: complete | incomplete
Drift Assessment: low | medium | high
Chosen Mode: restore | polish | stop
```

## Phase 2: Mode Selection

| Condition | Mode |
|-----------|------|
| Functionally incomplete | `stop` |
| Baseline exists + drift medium/high | `restore` |
| Baseline exists + drift low | `polish` |
| No baseline exists | `polish` |
| Mixed drift | Two-phase: restore then polish |

## Phase 3: Execute

### restore mode

Read `docs/fidelity-checklist.md` for the full checklist.

Priority order:
1. Fix layout and information hierarchy drift
2. Fix component language drift
3. Normalize token usage
4. Fix state presentation drift
5. Fix interaction fidelity

### polish mode

Priority order:
1. Strengthen typography hierarchy
2. Improve spacing rhythm and grouping
3. Enforce token usage
4. Improve component affordance and state clarity
5. Add restrained motion where it supports comprehension
6. Improve responsive balance

### Two-phase execution

When drift is mixed:
- Phase A: restore meaningful fidelity gaps
- Phase B: apply limited polish that does not re-open drift

State phases explicitly in output.

## Phase 4: Guardrails

Do NOT change:
- Task flow
- Field meaning
- API behavior
- Routing semantics
- Permissions logic

If a UI improvement requires any of these changes, call it out explicitly and
assume the change should NOT be made unless it is clearly blocking.

## Phase 5: Verify

Check against chosen mode:

- `restore`: closer to spec/tokens/screenshots, less drift, same product behavior
- `polish`: better visual quality, better interaction clarity, same product behavior, no new drift

Engineering quality checks:
- No broken responsive layout
- No missing visible states
- No token drift introduced by hardcoded values
- No unnecessary component duplication
- No accessibility regression in focus, contrast, labels, or feedback

## Phase 6: Report

Output shape:
1. Triage block
2. Chosen mode and rationale
3. Files changed
4. Restore work completed (if any)
5. Polish work completed (if any)
6. Constraints respected
7. Remaining gaps or tradeoffs

## Reference Documents

- Skill definition: `skills/ui-forge.md`
- Fidelity checklist: `docs/fidelity-checklist.md`
- Input contract: `docs/input-contract.md`
- Positioning: `docs/positioning.md`
- Eval prompts: `docs/eval-prompts.md`
