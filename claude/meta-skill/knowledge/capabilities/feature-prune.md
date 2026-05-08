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

### Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `.allforai/feature-prune/prune-tasks.json` | `decisions[].included` | translate, generate-artifacts | required | Only implement included=true features — prune scope gate before translate |
| `.allforai/feature-prune/prune-tasks.json` | `decisions[]` | generate-artifacts | required | Code generation task list must use pruned feature scope |
| `.allforai/feature-prune/prune-report.md` | — | product-verify | optional | Verification references prune decisions to understand excluded features |

## Methodology Guidance (not how)

- **Frequency first**: High-frequency tasks get P0/P1 by default unless effort is prohibitive (web/mobile apps only — see game exception below)
- **Consumer maturity bar**: For consumer products, flow-completeness tasks are P0 even if low frequency

**Game project prune criteria (`is_game_project = true`):**
Frequency-based P0/P1/P2/P3 tiers do NOT apply to game systems — game loops are the product, not measurable user tasks. Instead use: Core Loop (P0) → Meta Loop (P1) → Polish/Retention (P2) → Monetization/Social (P3). Never prune a system that is the only instance of a game state (e.g., "game over screen" cannot be P3). A retention mechanic (daily reward, streak) is P0 for casual-mobile, P2 for roguelike. IAP is P1 for casual-mobile (if platform supports it), P3 for story-driven games.

**Fantasy console constraint pruning (PICO-8, GBStudio):** The cartridge token/size limit IS the prune boundary. Tier assignment = by cartridge budget impact: P0 = core mechanic required for the game to be playable; P1 = features that fit within the cartridge limit; P2 = features that require token optimization to include; P3 = features that cannot fit without removing P0 content. Run token/size estimation before include/exclude decisions.


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
