# Outcome Critique Grill

Given one completed probe evidence bundle, the approved intent, and prior critique answers,
form exactly one question that helps the user challenge either the implementation logic or
the delivered feature/state detail.

Do not ask for discoverable facts. Show only the minimum evidence needed to judge the
potential mismatch. Distinguish an approved-intent mismatch from a new preference. Lead
with the most diagnostic issue, not cosmetic polish.

Return only:

```json
{
  "probe_id": "P-001",
  "axis": "logic-alignment|feature-state-completeness",
  "evidence_summary": "intended versus observed",
  "question": "one decision or judgment question",
  "recommended_judgment": "confirmed|gap-seed|preference|reality-gate",
  "main_tradeoff": "consequence of the recommendation",
  "likely_gap_family": "stable family name or none",
  "next_if_confirmed": "related neighborhood to inspect"
}
```
