# Feature Prune Capability

> Prioritize and scope gap-tasks by frequency, value, and effort.
> Internal execution is LLM-driven — scoring weights adapt to project type.

## Goal

Filter gap-tasks down to an implementable scope. Assign frequency tiers,
make explicit include/exclude decisions, and produce a prune-tasks contract
that translate and ui-design consume as their scope boundary.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `prune-tasks.json` | Include/exclude decision for every gap task, with reason |
| `frequency-tier.json` | Frequency tier assignment per task (P0/P1/P2/P3) |

**prune-tasks.json field schema:**
```json
{
  "decisions": [
    {
      "task_id": "<string — MUST match gaps[].task_ref in gap-tasks.json OR tasks[].id in task-inventory.json>",
      "included": "<boolean — true = implement, false = exclude from this release>",
      "reason": "<string — why included or excluded>",
      "tier": "<enum: P0 | P1 | P2 | P3 — optional, from frequency-tier.json>"
    }
  ]
}
```

`task_id` is a foreign key to `gap-tasks.gaps[].task_ref` (preferred) or `task-inventory.tasks[].id`.
Every task from gap-tasks MUST have an explicit decision — no silent omissions.
`included = false` tasks are NOT deleted — they are preserved with reason for audit trail.

### Required Quality

- Every gap-tasks entry has an explicit `included` decision
- No task silently omitted — if not in decisions[], that is a contract violation
- Reasons are meaningful (not "low priority" alone — must reference effort/value/frequency data)
- At least one P0 task must be `included = true`, or explicitly justify why no P0 tasks exist

## Methodology Guidance (not how)

- **Frequency first**: High-frequency tasks get P0/P1 by default unless effort is prohibitive
- **Consumer maturity bar**: For consumer products, flow-completeness tasks are P0 even if low frequency
- **Scope gate**: The total included scope should be achievable within the project's constraints — don't include everything by default
- **Audit trail**: excluded tasks must have reasons — they inform future releases

## Knowledge References

### Phase-Specific:
- consumer-maturity-patterns.md: consumer maturity scoring for tier assignment
- feature-gap.md: upstream gap-tasks schema (task_ref FK source)

## Composition Hints

### Single Node (default)
Run after feature-gap. Produces the scope boundary consumed by translate and ui-design.

### Merge with Feature Gap
For simple projects: prune as the final step of feature-gap node.

### Split by Domain
For large products: prune-consumer, prune-merchant, prune-admin as separate nodes
to allow different stakeholders to make scope decisions independently.
