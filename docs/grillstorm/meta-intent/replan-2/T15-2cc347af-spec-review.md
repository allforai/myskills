# Spec review — 2cc347af (since e30ccc7c)

Independent review against #8/#9/#13 and T15-codex-missing-docs-evaluation §5.1–5.4.
Read-only; this file is the only one written. Probes ran from scratch copies.

## Implemented and verified

§5.1 route exists end-to-end in both engines: a failed QA node with a report satisfies only
its declared `repair_node_id`; an undeclared successor never advances on a failed dependency;
closure waits for the QA node itself, not the repair (`engine-core.js:112-137`,
`flow-template.py:324-382`). §5.3 and §5.4 audit items and their blocker codes were added.

## Findings

1. **Budget not bounded across restarts (Claude).** `repairAttempts` is a per-process `Map`;
   `loadDagPrompt` never asks for prior attempts and `repairRoutePrompt`'s "attempt N of M"
   is written to `transition_log` and never read back. Probe: three resumes of the same
   `max_attempts: 2` loop dispatched repair 2/2/2 — cumulative 6, status `needs_diagnosis`
   each time. Codex persists it (`repair_attempts_spent`, transition_log), so the two engines
   apply different budgets — against #9/#13's "两端使用相同权威规则".
2. **Codex admits stale and non-QA verdicts.** `qa_report_usable` (`flow-template.py:303-321`) checks only that the exit
   artifacts exist and parse — no binding to the current run or inputs, and no equivalent of
   Claude's `NON_QA_FAILURE_TYPES`. Probe with an empty `transition_log` and a leftover
   `verify.json`: `status: failed`, `failed_env` and `blocked` all route to `repair`. Claude
   uses the node's own in-wave result, and its template calls environment/authority failures
   "never a repair route". Contradicts #13's freshness and the engines' shared rule.
3. **New blocker codes are prose only.** `undeclared_repair_loop_routing`,
   `unowned_effect_stage`, `missing_document_contract` appear only in
   `bootstrap-node-expansion-qa/SKILL.md`; no validator or fixture. #9/#13 ask for behavior
   coverage, "不仅断言提示词文本".
4. **Delta rule has no baseline.** Step 3.4 presents the node list in chat; nothing persists
   the confirmed set, so Phase A has nothing to diff. `/run` gating (`SKILL.md:695-696`) still
   keys on the three lenses plus the node-spec audit, not on delta acceptance.
5. **`continue` skips wave exits.** A routed QA failure bypasses the `accepted_with_gaps` and
   `iteration_repair_stopped` returns. Probe: the gap-accepted node was re-dispatched 3×,
   re-running the `on_needs_iteration` policy event each time.
6. **Tests do not reach these.** Every Claude repair test uses `completed: []` (no resume);
   the Codex test named "with a current report" only writes a file. 70/70 and 36 passed green.

No unrequested scope found.
