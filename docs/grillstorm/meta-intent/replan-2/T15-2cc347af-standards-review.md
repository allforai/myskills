# Standards review — 2cc347af (since e30ccc7c)

Independent review of `git diff e30ccc7c...2cc347af`. Fixed-commit sources read via `git archive`; probes run on a scratch copy only.

## Hard violations

**1. `engine-core.js:453` / `run-engine.workflow.js:463` — the repair `continue` swallows two terminal signals.**
```js
      continue   // after every hard failure was routed to a repair loop
    }
    if (outcomes.some(r => r && routeOutcome(r) === 'accepted')) {
```
When one wave carries both a routed QA failure and another node's `accepted` / `iteration_repair_stopped` result, `continue` skips both checks below it. An `iteration_repair_stopped` node is already committed into `done`, so it never reappears. Scratch probe on the exact snapshot: five nodes, `iter` returning `iteration_repair_stopped` in the same wave as the QA failure → `runEngine` returns `{"status":"complete"}`. This breaches `orchestrator-template.md` ("never waive, downgrade, or hide a gap") and the `on_needs_iteration` policy contract at line 62.

**2. `flow-template.py:298,332` — repair budget is per repair node, not per QA node.**
```python
def repair_attempts_spent(workflow, repair_node_id) -> int:
    return sum(1 for entry in workflow.get("transition_log", [])
               if entry.get("node") == repair_node_id and entry.get("status") == "completed")
```
`codex/meta-skill/knowledge/orchestrator-template.md:104` promises each failed QA node "at most `max_attempts` attempts". With one `repair_node_id` serving `qa_node_ids: [verifyA, verifyB]` and `max_attempts: 2`, two attempts spent on `verifyA` leave `verifyB` zero. Probed: `SELECTED = verifyA`, `BLOCKED = ['repair']`. `engine-core.js:437` keys attempts `${repair_node_id}::${qa_node_id}` — the two orchestrators disagree on the same declared spec.

**3. Both `orchestrator-template.md` files claim the loop is "already shape-validated by `validate_unattended_readiness.py`".** `_validate_repair_loop_spec` checks `repair_node_id`, node membership and both edges; it never inspects `max_attempts`, which the QA skill (`bootstrap-node-expansion-qa/SKILL.md:244`) requires to be bounded. An unbounded/absent budget silently falls back to a default.

## Heuristic smells

- **Divergent Change / contract drift.** `engine-core.js` gates repair on `NON_QA_FAILURE_TYPES` (`safety_warning`, `exhausted_retries`, …); `flow-template.py:302 qa_report_usable` has no analogue, and the Codex doc drops that clause. Same declaration, two admission rules.
- **Duplicated Code / efficiency.** `first_pending_node` and `blocked_pending_nodes` each call `_pending_state`, which recomputes `independent_artifact_gate` for every node; `main():802-804` calls both.
- **Mysterious Name.** `MAX_CONSECUTIVE_FAILURES_PER_NODE` reused as the repair-loop default (`flow-template.py:295`); JS names it `DEFAULT_REPAIR_ATTEMPTS`.

## Compliant

`engine-core.js` ↔ `run-engine.workflow.js` duplication is the sanctioned verbatim mirror (`run-engine/README.md`); the sync-check passes and 70/70 matches the updated README. New blocker codes follow the skill's "Allowed blocker codes" convention.
