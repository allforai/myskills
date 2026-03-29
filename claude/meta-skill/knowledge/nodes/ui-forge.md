# UI Forge Node Template

> Post-implementation UI refinement: fidelity check, restore, polish.

## Purpose

After code is functionally complete, verify UI matches design spec,
restore deviations, then polish visual quality.

## Positioning

UI Forge is not a product design plugin and not a first-time implementation
orchestrator. It only handles UI quality issues after functionality is complete:

- Pages are usable but visual quality is low
- Pages are functionally correct but deviate from design spec / tokens / screenshots
- Need to increase production quality without changing business semantics

## Phases

### Phase 1: Fidelity Check

Compare current implementation vs design baseline:
- Design spec files (`.allforai/ui-design/`)
- Token/design system definitions
- Reference screenshots

Output: `.allforai/ui-forge/fidelity-assessment.json`

### Phase 2: Restore

Fix deviations to match design spec:
- Apply correct token values
- Restore layout to spec dimensions
- Align component behavior to spec

Input: fidelity-assessment.json + design spec
Output: code changes

### Phase 3: Polish

After alignment is confirmed:
- Visual hierarchy and depth
- Responsive layout refinement
- State design (empty, loading, error, success, disabled)
- Micro-interactions and transition timing

Input: design spec + codebase
Output: code changes

## Rules

1. **Restore before polish**: Align to design before enhancing.
2. **No business logic changes**: UI-only modifications, no interface contract changes.
3. **Spec/token/component are binding constraints**: Not suggestions.
4. **Function-first**: Feature must be complete before UI tuning.
5. **Non-invasive by default**: Do not rewrite page semantics or business flows.

## What Bootstrap Specializes

- Design spec file locations
- Token/design system references
- UI framework (Tailwind, styled-components, SwiftUI modifiers...)
- Component library patterns
