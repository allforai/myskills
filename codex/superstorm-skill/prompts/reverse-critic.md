# Reverse critic (Phase 1.4) — 逆向思维 — MODEL: THINK tier (ladder in skill)

Work BACKWARD from the plans/designs to the specs. Do not read forward and nod along —
actively try to refute that this will work.

## Check (backward feasibility)
- Take each plan and ask: if an engineer executes these exact steps, do they end up
  satisfying the design and spec? Where does it break?
- Hunt hidden assumptions, missing prerequisites, infeasible steps, unhandled error/edge paths.
- For each `acceptance_cmd`: is it actually a meaningful check, or a tautology that would pass
  without the feature working? Flag weak acceptance commands (directly guards against §4.6 being gamed).

## Self-fix loop (spec §4.4, ≤K rounds, K=3 for this stage)
Fixable issues → edit the spec/design/plan docs and re-run.

## Output (escalation schema)
- Sound → `{status:"ok"}`.
- Requires a choice or is non-convergent → `{status:"escalate", reason, evidence}` with
  viable options and a ranked recommendation. Never request human input.
