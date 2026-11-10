---
status: accepted
---

# A run repairs without rewriting its plan

A real overnight `/run` exposed three ways a run's own repair machinery worked against it.

1. **A delivery was read as a failure.** A declared repair node did all its fixes. Then its freshness publish was refused, because the QA node it repairs goes stale until that node reruns. That refusal is built into the loop (ADR-0005). The node reported the refusal as its own `hard_fail`. The Claude engine took it at its word before the independent gate measured anything, and it did the same when the gate step labelled the stale upstream `hard_fail`. Every attempt was charged, the QA node never reran, and the loop ended "exhausted".
2. **Diagnosis had nowhere to put its findings.** After `needs_diagnosis`, the repair plan reached the re-dispatched root node only if someone edited its node-spec. Under ADR-0011 an edited node-spec makes decision coverage stale, so every diagnosis forced a new rehearsal, and the rehearsal asked about whatever the edit had introduced.
3. **Resets and re-bootstraps rewrote history by hand.** Resetting a diagnosed closure meant hand-editing `transition_log`. A re-bootstrap that wrote `workflow.json` from the template dropped the log, and the validator only caught that afterwards.

The same run also stopped twice on questions that bootstrap could have asked:

- A node added an anti-abuse guard that changed a settled user-visible rule. The guard withheld an outcome the rules grant.
- A settled acceptance criterion contradicted a documented limit of the host platform.

## Decision

**A. A delivery dispatch is judged by measurement only.** When a node runs as the repair node of an open loop, its own verdict is not evidence. A self-reported failure, or a gate step that calls the stale upstream `hard_fail`, goes to the existing measurement, `measuredDelivery`. A delivery is still exactly what ADR-0005 defines: the declared artifacts were newly written, and the node is withheld by its own QA node and nothing else. Structural failures (`NON_QA_FAILURE_TYPES`) and a product-decision gap remain the node's own verdict. The dispatch prompt also tells the node that a refused publish is expected. The Codex driver already worked this way: it records its own measured transition over the worker's. A shared contract scenario now pins both hosts to it.

**B. Diagnosis writes corrections, not node-specs.** Each repair-plan step goes to `.allforai/bootstrap/diagnosis-corrections/<node_id>.json`. Every dispatched node is told to read its file and treat it as binding, as it treats its node-spec. The file is removed when the node completes, and `diagnosis_history` keeps the record. A correction refines how a node meets its spec. It never settles a user-visible rule. A root cause that needs one is an unresolved product decision (ADR-0011 D). Node-specs change only at interactive bootstrap, where rehearsal covers the change.

**C. Reset and re-bootstrap have official operations.**
- `compute_reset_closure.py --apply --diagnosis <ref>` marks the closure's completed transitions `superseded` and names the diagnosis. Nothing is deleted. Every reader that counts `completed` sees the reset without changes, and the Codex driver treats a node whose latest transition is `superseded` as not done.
- `reconcile_bootstrap_workflow.py --candidate-workflow … --write` carries the current run history into the candidate verbatim: `transition_log`, `diagnosis_history`, `corrections_applied` and `repair_routes`. `transition_log_missing_for_delivered_nodes` stays as the backstop.

**D. Two generic rules close the gaps behind the two questions.**
- A guard is not a rule change (Pattern I). Protection may refuse, delay, flag or rate-limit inside the settled rules. Protection that would change one of those rules is never applied. It also does not stop the node: the node finishes with the guards that fit and returns the stronger option as a non-blocking safety warning for the next bootstrap. It becomes an unresolved product decision only when the settled rules cannot be built at all without that choice. Thought testing showed why the second half matters: without it, a node turned "stronger protection would be nice" into blocking gaps, which is another way to stop overnight.
- Decision rehearsal (ADR-0011 B) also asks which settled requirement the node could not meet, given the constraints in what it reads. A contradiction between a settled requirement and a platform limit is a Phase A question, not something discovered during the run.

## Cross-host (ADR-0004)

| Decision | Claude | Codex | Pi |
|---|---|---|---|
| A | `engine-core.js` | Already correct; covered by a test | No engine of its own |
| B | Engine prompt plus the commit step | `flow.py` prompt item 10 plus clearing on completion | Template sentence |
| C | Shared scripts | Shared scripts | Shared scripts |
| D | Canonical knowledge | Same knowledge | Same knowledge |

## Consequences

- Repair loops spend their budget on attempts that really failed. A repair that delivered always gets its QA rerun.
- A diagnosis no longer forces a new A0 rehearsal on its own.
- A project mid-run keeps working. Hand-written `superseded` entries already match the official shape, and corrections in node-specs from before this ADR still apply. They just stale coverage, as they did before.
