# brainstorming-lite

A distilled decision protocol for Phase A of `/bootstrap`. Use it to resolve each
decision into ONE artifact, grouping independent decisions so the human answers a topic, not
a queue. It borrows the brainstorming method (intent first,
options with tradeoffs, incremental confirmation) but omits the heavy ceremony:
**no spec doc, no reviewer loop, no writing-plans handoff.**

## When to use
For each item in the Phase A decision queue (nodes with `decision_mode: "brainstorm"`
plus A0 `missing` entries). High-frequency, lightweight, converges fast.

## Protocol
1. Sort the queue into topics: decisions that share a domain and do not depend on each
   other's answers go in one message; a decision whose options change with another's answer
   waits for that answer.
2. One message per topic. For every decision in it: one sentence on why it matters, 2–3
   options with concrete tradeoffs, a recommended default and its reason. The human can accept
   all defaults in one reply or pick per item.
3. Confirm incrementally only where an answer reveals a new fork; serialize just that fork.
4. Write one decision artifact per decision and stop — do NOT generate the downstream work.

Twenty independent decisions asked one per message are twenty round-trips for the same
information; a capable planner groups them and the human keeps every choice.

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
- One topic per message; dependent forks are serialized, independent decisions are not.
- Every decision still gets its own artifact and its own recorded answer; batching the question
  never merges the records.
- **Fork cap (fix L2): at most 3 follow-up forks per decision.** If a decision hasn't
  converged after 3 forks, pick the leading option, record it with a "low-confidence" note,
  and move on — never loop indefinitely on one decision.
- Generation-before: this runs BEFORE the node that consumes the decision.
- Stay in `/bootstrap`; `/run` must never reach a brainstorming step.
