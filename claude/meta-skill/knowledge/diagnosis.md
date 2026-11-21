# Full-Chain Diagnosis Protocol

> Dispatched when any node returns status "failure". Performs root cause analysis,
> same-class gap expansion, and generates a repair plan.

## When to Trigger

A node subagent returns `{ "status": "failure", "errors": [...] }`.
Do NOT retry or backtrack. Diagnose first.

## Diagnosis Subagent Prompt Template

```
You are diagnosing a workflow failure.

## Failure Context
- Failed node: {node_id}
- Error: {errors from subagent response}
- Iteration: {iteration_count}

## System State
- All nodes: {nodes[] from workflow.json — id + goal + exit_artifacts per node}
- All node exit_artifacts: {extracted from workflow.json nodes[].exit_artifacts}
- Game-design gate state (if applicable): {records[] from .allforai/game-design/approval-records.json — check gate_status for any node with capability: game-design; revision-requested status not reset after re-execution is a common false-failure mode}
- Previous diagnoses: {diagnosis_history}

## Your Tasks

1. **Root Cause**: Trace from the failed node upstream. Which is the earliest
   node whose output is insufficient? Don't guess — read the actual artifact
   files via Read tool if needed.

   **Baseline first.** A node is the root cause of a failing check only if the
   check held before this run wrote anything, or the run's own writes are what
   broke it. Establish which from a recorded earlier state — the base commit, a
   wave baseline, an earlier evidence entry for the same check — and say what
   you read. A check that was already failing before any node of this run wrote
   is `failing_before`: no node of this run caused it, and blaming one spends
   its repair attempts on a defect it did not make. If a node of this workflow
   owns the failing code (its `parallel_write_scopes` cover it), that node
   repairs it and the repair action says the defect is inherited; if none does,
   the failure is out of scope (see Out-of-Scope Repairs). When no earlier state
   can be read, the baseline is `unknown` — write that, do not assume either way.
   Each failing check has its own baseline: checks that failed together can differ,
   and a mixed verdict is how an inherited failure gets charged to this run.

2. **Impact Chain**: List all intermediate nodes between root cause and failure.

3. **Same-Class Expansion**: The specific gap you found — are there similar gaps
   elsewhere? If one API was missed, were other APIs in the same domain also missed?
   If one business flow is incomplete, are sibling flows also incomplete?

4. **Repair Plan**: Ordered list of nodes to re-run, from upstream to downstream.
   Each entry: node ID + specific action + what context to carry.
   Use `depends_on_previous: true` when a step needs the prior step's output.

5. **Prevention**: Should any node-spec's exit_artifacts or hints be tightened
   to prevent this class of failure in future iterations?

## Output Format

Return JSON:
```json
{
  "root_cause": {
    "node": "<node-id>",
    "description": "<what's wrong>"
  },
  "baselines": [
    {
      "check": "<the failing check>",
      "state": "passing_before | failing_before | unknown",
      "basis": "<the earlier state read and where — commit, wave baseline, evidence entry — or why none could be read>"
    }
  ],
  "impact_chain": ["<node-id>", ...],
  "gaps_found": [
    { "domain": "<area>", "missing": ["<item>", ...], "severity": "high|medium|low" }
  ],
  "repair_plan": [
    { "node": "<node-id>", "action": "<what to do>", "depends_on_previous": true|false }
  ],
  "prevention": [
    { "node_spec": "<node-id>", "add_to_exit_artifacts": "<new file path to check>" },
    { "node_spec": "<node-id>", "add_to_hints": "<new hint>" }
  ]
}
```
```

## Repair Plan Execution

After diagnosis returns:

1. Orchestrator reads repair_plan and appends the diagnosis to `workflow.json diagnosis_history[]`.
2. For each step, writes `.allforai/bootstrap/diagnosis-corrections/<node>.json`:
   ```json
   { "node_id": "<node-id>", "diagnosis": "<diagnosis timestamp>",
     "corrections": [{ "action": "<repair action>", "root_cause": "<root_cause.description>",
                       "gaps": ["<gaps_found item>"], "prevention": "<hint, if any>" }] }
   ```
   The node reads this file when it is dispatched again and treats it as binding as its
   node-spec. The file is removed when the node completes; diagnosis_history keeps the record.
3. **Never edit node-specs during a run.** A node-spec changed after A0 makes decision
   coverage stale, and the next readiness check stops the run for a new rehearsal. A
   prevention rule that must outlive this run goes into the node-spec at the next
   interactive `/bootstrap`, where rehearsal covers it.
4. A correction refines how a node meets its spec. It never settles a user-visible rule. A
   root cause that needs one is a product decision: the node that owns the rule takes its
   recommended option and records it in `run-decisions/` (Pattern I), which is not a repair.
5. Reset the closure with `compute_reset_closure.py <workflow.json> --apply --diagnosis <ref> <root...>`;
   it marks completed transitions `superseded` and keeps them. Never rewrite `transition_log` by hand.
6. **After each successful repair step**, orchestrator appends to `workflow.json corrections_applied[]`:
   ```json
   { "node": "<node-id>", "what_was_wrong": "<root_cause.description>", "fix_applied": "<repair action taken>", "timestamp": "<ISO>" }
   ```

<a id="oracle"></a>
## A repair may not move the oracle

The check that failed is the oracle of its repair: the test's assertions, the lint or
type-check configuration, the acceptance criterion, the fixture or expected value a
comparison reads. A repair changes the product until the oracle passes, never the oracle
until the product passes. Deleting or skipping the failing test, loosening an assertion,
widening a tolerance, disabling a rule and regenerating an expected value from the
current output are all the same move, and a check that went green that way has proved
nothing.

The one exception is an oracle that is itself wrong — it contradicts a confirmed
requirement, or its harness cannot run on the target platform. That is a finding about
the oracle, not a repair of the product: the node names the requirement or the platform
fact the check contradicts, changes only what that justifies, and returns the change in
NODE_RESULT `assumed_decisions` (what was changed in the check and why), so whoever
verifies the node judges the change instead of inheriting it unseen. A repair plan step
whose action is to change a check carries the same justification.

## Re-Verification

After repair_plan completes:
- Re-evaluate the originally failed node's exit_artifacts existence check
- If still failing → diagnose again (with updated context)
- diagnosis_history prevents re-diagnosing the same root cause

## Diagnosis History Recording

Each diagnosis result is appended to `workflow.json diagnosis_history[]` by the orchestrator:

```json
{
  "timestamp": "<ISO timestamp>",
  "failed_node": "<node-id>",
  "root_cause": { "node": "<node-id>", "description": "<what's wrong>" },
  "impact_chain": ["<node-id>", "..."],
  "gaps_found": [{ "domain": "<area>", "missing": ["<item>"], "severity": "high|medium|low" }],
  "repair_plan": [{ "node": "<node-id>", "action": "<what to do>", "depends_on_previous": true }],
  "out_of_scope": false
}
```

## Convergence Control

- Same root cause: max 2 diagnoses. 3rd → mark UNRESOLVED, output current best + TODO
- Repair plan length ≤ impact_chain length (can't be longer than the chain)
- Previously identified gaps must resolve (new gaps OK, old gaps can't recur)
- Repair step failure → new diagnosis, but nested depth max 1 level
- Each diagnosis record written to workflow.json diagnosis_history

## Out-of-Scope Repairs

If the diagnosis identifies a root cause in a node that **does not exist** in the current
state machine (e.g., demo-forge fails because API is missing, but there is no translate
node to fix the code), or a `failing_before` failure in code no node of this workflow
owns, the orchestrator:

1. Marks the gap as UNRESOLVED
2. Records it in diagnosis_history with `"out_of_scope": true`
3. Outputs a clear TODO: "This issue requires [capability X] which is not in the current
   workflow. Re-run /bootstrap with goals including [X] to add the necessary nodes."
4. Does NOT attempt to create new nodes at runtime — node set is fixed at bootstrap time

This handles the scenario where a limited-scope workflow (e.g., goals: ["demo"]) encounters
issues that require capabilities from a broader scope (e.g., translate or tune).
