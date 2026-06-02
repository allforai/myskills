# brainstorming-lite

A distilled decision protocol for Phase A of `/bootstrap`. Use it to resolve ONE
decision into ONE artifact. It borrows the brainstorming method (intent first,
options with tradeoffs, incremental confirmation) but omits the heavy ceremony:
**no spec doc, no reviewer loop, no writing-plans handoff.**

## When to use
For each item in the Phase A decision queue (nodes with `decision_mode: "brainstorm"`
plus A0 `missing` entries). High-frequency, lightweight, converges fast.

## Protocol (per decision)
1. State the decision and why it matters (one sentence).
2. Surface intent with ONE question at a time (prefer multiple-choice). Never batch.
3. Offer 2–3 options with concrete tradeoffs; lead with a recommendation + reason.
4. Confirm incrementally; iterate only if the answer reveals a new fork.
5. Write the decision artifact and stop — do NOT generate the downstream work.

## Output contract
Write `.allforai/<domain>/decision-<id>.json`:
```json
{
  "id": "<decision id>",
  "decision": "<the chosen direction>",
  "rationale": "<why, in the user's framing>",
  "options_considered": ["<a>", "<b>"]
}
```
Validate with `validate_decision_artifact` before moving to the next decision.

## Hard rules
- One question per message.
- **Fork cap (fix L2): at most 3 follow-up forks per decision.** If a decision hasn't
  converged after 3 forks, pick the leading option, record it with a "low-confidence" note,
  and move on — never loop indefinitely on one decision.
- Generation-before: this runs BEFORE the node that consumes the decision.
- Stay in `/bootstrap`; `/run` must never reach a brainstorming step.
