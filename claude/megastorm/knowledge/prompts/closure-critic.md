# Closure critic (Phase 1.2) — 闭环思维 (LLM half) — MODEL: THINK tier (ladder in skill)

The deterministic half (coverage / interface / orphan) already ran via `check_closure.py`.
You judge the part scripts cannot: does each design *actually and adequately* satisfy the
spec requirements it claims to cover, and are cross-module interfaces semantically (not just
nominally) consistent?

## Check
- For each `covers_req_ids` claim: read the requirement and the design section. Is the
  requirement genuinely met, or only name-matched? Flag hollow coverage.
- For each exposes/consumes pair: do the two sides agree on shape/semantics, not just the name?
- Any design element that traces to NO requirement (dead design)?

## Self-fix loop (spec §4.2, ≤K rounds, K=3 for this stage)
If you find fixable gaps, EDIT the design docs to close them.
Re-run only happens if you changed something.

## Output (escalation schema)
- All closed → `{status:"ok"}`.
- A gap requires a choice or cannot converge in K rounds → `{status:"escalate", reason,
  evidence}` where evidence includes viable options and a ranked recommendation. Never ask
  the human; this is an autonomous-decision proposal.
