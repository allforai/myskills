# brainstorming-lite

Use only in `/bootstrap` Phase A for the decision queue defined in
[bootstrap-audits.md](bootstrap-audits.md), including `decision_mode: "brainstorm"`
nodes and A0 `missing` entries. Resolve each decision before its consumer runs.
Keep the protocol out of `/run`. Skip spec writing, reviewer loops, planning handoff,
and downstream work.

1. Group independent decisions by domain into one message per topic. Defer any
   decision whose options depend on an earlier answer.
   Grouping reduces back-and-forth while letting the user choose each answer.
2. For each decision, explain why it matters in one sentence. Give 2–3 options
   with concrete tradeoffs and explain the recommended default. Let the user
   accept all defaults at once or choose per item.
3. Follow up only on new forks revealed by the answer. Ask each dependent fork
   in sequence, up to three per decision. If the third leaves the decision open,
   record the leading option with a `low-confidence` note and move on.
4. Record each decision and its answer in a separate
   `.allforai/<domain>/decision-<id>.json`. Run `validate_decision_artifact`
   before moving to the next decision.

```json
{
  "id": "<decision id>",
  "decision": "<the chosen direction>",
  "rationale": "<why, in the user's framing>",
  "options_considered": ["<a>", "<b>"]
}
```
