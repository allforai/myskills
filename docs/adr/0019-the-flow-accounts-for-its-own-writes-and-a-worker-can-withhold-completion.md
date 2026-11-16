---
status: accepted
---

# The flow accounts for its own writes, and a worker's report can withhold completion

Four pieces of anonymous run feedback arrived on 2026-11-15. One is domain knowledge and went to `learned/blind-spots.md`. The other three were defects in what the run takes as proof.

1. A declared repair node rewrote source a completed consumer had judged, and the QA rerun failed. At the next start every file that differed from a published record counted as an external change. The consumer's recorded acceptance failed, because the defect was still there, so the change was classified a product conflict and the user was asked to accept, reject or defer a defect the run already knew about. Resetting the diagnosis closure did not help: the reset nodes' old evidence still blocked the start as `stale_evidence`.
2. On Codex a node is completed when the executor exits 0 and the artifact gate passes. A worker that stopped at a blocker and wrote `failed` exits 0, and artifacts from an earlier attempt still pass the gate. The driver overwrote the worker's `failed` with `completed` and deleted the diagnosis correction it had not applied.
3. On Codex an isolated parallel draft is a copy without `.git`. The freshness helper reads the source inventory from Git and falls back to a directory walk, so inside the draft an ignored build tree became product source and published records looked stale. On import, build output the draft produced was refused as an edit outside its write scope.

## Decision

**A. What changed while a wave was open is the flow's own write.** `begin-wave` fingerprints what a node can consume: product source and every exit artifact and required document. `end-wave` records in `.allforai/bootstrap/flow-writes.json` the content of each such file that changed. The boundary comparison leaves out a changed file whose current content is in that record. Its consumer is stale with the node as repair owner, and reruns. The record names content, so a later edit is external again. `recover-waves` drops the baseline of a wave nobody saw end and records nothing for it.

**B. A reset node's stale evidence does not block the start.** A node whose latest transition is `superseded` claims no completion, and the rerun the reset ordered is the repair. The artifact gate still withholds it until it republishes.

**C. On Codex the worker's terminal transition is read before the driver records its own.** An attempt is not completed when its worker wrote no transition for it, wrote a status other than `completed`, or wrote `completed` with an `error` or `blockers`. The driver records `failed` with `withheld_by_worker`; that node, and any node with a pending `diagnosis-corrections/<node_id>.json`, stays pending whatever the gate says about its artifacts. The report can only withhold: completion is still the gate's to grant. A parallel draft that reports failure gets no publication attempt. Repair delivery is measured as before.

**D. On Codex an isolated draft carries the project's source inventory.** The copy gets a fresh Git index naming the same tracked files and the project's local excludes, with no history and no objects. On import, a changed path outside the node's write scope that the project's ignore rules call generated is neither imported nor a violation. A declared path is imported whatever the ignore rules say, and a tracked file an ignore rule matches is source, so changing it outside the scope still refuses the whole patch.

## Alternatives rejected

- Treating every change inside another node's declared write scope as that node's delivery. Almost all source lies inside some implementation scope, so an edit made outside the flow would rarely be reported at all.
- Recording the writes of a wave that never closed. What changed between a dead driver and the next start cannot be told from an edit by the user.
- Accepting the external change on the user's behalf, or exempting the consumer from its acceptance. The first invents an approval; the second weakens the gate. Under A the consumer still has to rerun and pass.
- Exempting every node whose latest transition is `failed` from `stale_evidence`. A failed QA node recovers by observing its contract, which already works; only the reset had no path.
- Letting a worker's `completed` complete a node. The gate would stop being independent.
- Accepting an attempt with no terminal transition when its artifacts changed. The run prompt already requires the transition, and one rule is simpler than two.
- Copying `.git` into each draft. History can be many times the size of the tree, once per parallel node.

## Cross-host (ADR-0004)

| Decision | Claude | Codex | Pi |
|---|---|---|---|
| A, B | Shared `evidence_freshness.py` and `validate_unattended_readiness.py`; the engine already brackets each wave | Same scripts; `flow.py` already brackets each dispatch | Same scripts; the template already tells the orchestrator to bracket |
| C | Not needed: a worker returns a structured result and the engine records completion from it | `worker_veto` in `flow.py`, serial, parallel and inline-review revision | Not needed: the orchestrator reads the worker's reply |
| D | No isolated copies | `carry_source_inventory` and `project_ignored` in `flow.py` | No isolated copies |

## Consequences

- A project needs its scripts, and on Codex its `flow.py`, refreshed by `/bootstrap`. Changes made before that are not in the record and are still reported as external.
- An edit a user makes while a wave is open is recorded as the flow's. The node consuming it still reruns against its confirmed acceptance.
- A and the wave bracket hash the consumable tree at each `begin-wave` and `end-wave`, and the baseline is stored while a wave is open.
- On Pi the record exists only when the orchestrator sends the bracket calls its template asks for.
- A Codex worker that finishes its node and forgets the transition fails that attempt and is dispatched again.
- A draft worker that runs `git diff` in its copy gets an error, since the index has no objects. The draft prompt tells it not to use Git.
