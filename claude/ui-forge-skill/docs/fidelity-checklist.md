# UI Forge Fidelity Checklist

Use this checklist before choosing `restore` or `polish`.

## 1. Baseline Availability

- Is `ui-design-spec.json` available?
- Is `tokens.json` available?
- Is `component-spec.json` available?
- Are reference screenshots available?
- If none exist, fall back to code-context-only refinement and bias toward `polish`.

## 2. Layout And Hierarchy Drift

- Does the screen preserve the expected information hierarchy?
- Are primary and secondary regions in the intended order?
- Has density drifted materially from the expected design?
- Are scanning paths still obvious?

## 3. Component Language Drift

- Do repeated UI patterns still look and behave like one system?
- Are button shapes, card treatments, inputs, and panels consistent?
- Are component variants aligned with the component contract?

## 4. Token Drift

- Are colors, spacing, radius, shadows, and typography using tokens where expected?
- Have hardcoded values replaced tokenized rules?
- Does the page visually belong to the same design system as neighboring screens?

## 5. State Fidelity

- Do loading, empty, error, disabled, and success states match the intended system quality?
- Are feedback cues too weak, too strong, or inconsistent with the design baseline?
- Are critical actions still visually prioritized correctly in all states?

## 6. Interaction Fidelity

- Are hover, focus, active, and transition behaviors aligned with the intended tone?
- Did implementation regress affordance or clarity?
- Is motion helping comprehension rather than adding noise?

## 7. Decision Rule

Choose `restore` when one or more of these are true:

- layout drift is material
- component language drift is material
- token drift is obvious
- screenshot/spec mismatch is obvious
- visible states no longer feel like the same product

Choose `polish` only when:

- the screen is already broadly faithful to the design baseline, or
- no trusted baseline exists and the task is purely implementation-stage refinement

## 8. Non-Negotiables

- Do not change business flow just to improve visuals.
- Do not introduce new product requirements.
- Do not hide fidelity issues under decorative polish.
- Restore first, then polish.
