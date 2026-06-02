# L3 Runbook — Real-Agent End-to-End

Run inside a real Claude Code session (the Workflow tool requires the harness).
Token cost is acceptable: this tests the engine, not a user project.

## Setup
1. Stage the fixture at the engine's canonical path (fix R2 — `loadDagPrompt` reads
   `.allforai/bootstrap/workflow.json`, NOT the fixtures dir):
   `mkdir -p .allforai/bootstrap .allforai/_l3 && cp claude/meta-skill/knowledge/run-engine/tests/fixtures/mini-workflow.json .allforai/bootstrap/workflow.json`
2. Ensure `.allforai/_l3/decision-n4.json` EXISTS (Phase A would have produced it):
   `{"decision":"variant-A","rationale":"L3 fixture preset"}`
3. Node subagents are "noop": each writes its `exit_artifacts` path with `{"ok":true}` and returns
   `{node_id, outcome:"passed", artifacts_written:[...], blocking_findings:[]}` — EXCEPT the seeded behaviors below.

## Seeded behaviors (to exercise every path)
- **n3**: first attempt returns `outcome:"soft_fail"` with a `placeholder` finding; retry returns `passed`. → verifies soft self-heal.
- **n5**: returns `outcome:"soft_fail"` with `{type:"cross_node", suspected_root_node:"n1"}`. → verifies hard-fail → needs_diagnosis. After diagnosis removes n1 from `completed` and reruns, n5 returns `passed`.
- **expander mk_n7**: appends `n7` (hard_blocked_by `["n6"]`). → verifies "plan auto-updates during run".

## Pass criteria
- [ ] Engine invoked ≥2× (initial run → post-diagnosis resume).
- [ ] n2 and n3 ran concurrently (both ready after n1; check phase/log output).
- [ ] Final `transition_log` marks n1..n7 all `completed`; no `placeholder` residue in any artifact.
- [ ] n4 ran without any stop (its `decision_inputs` artifact was present).
- [ ] Deleting `decision-n4.json` and re-running yields a `hard_fail` for n4 (planning bug), NOT a stop.
- [ ] n7 was expanded and executed.
- [ ] Kill mid-run and re-invoke: already-`completed` nodes are NOT re-run (idempotency).
