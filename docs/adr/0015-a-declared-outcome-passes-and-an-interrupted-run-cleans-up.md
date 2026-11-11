---
status: accepted
---

# A declared outcome passes, and an interrupted run cleans up after itself

A live product run stopped on four faults that were the run's own, not the product's.

1. A node finished with a status its exit declared in `accepted_statuses` and the checker accepted, but the engine's independent gate was told that any conditional, partial or fallback wording means "repair". It spent the node's three repair attempts on a verdict the plan had already accepted, and the same gate re-ran that node at every restart.
2. A node repairing its own findings edited a file an upstream node produces. The upstream evidence went stale from outside and the run needed a diagnosis to find out why.
3. After a re-bootstrap, files left by nodes that had not yet run in the new cycle were still on disk. An early node read one; freshness recorded its producer as an upstream the scheduler never orders first, and the publish was refused.
4. An engine interrupted mid-wave left the reads its nodes had registered and the evidence they had published, with no transition recorded. Readiness then blocked the restart until someone cleaned the files by hand.

## Decision

**A. The exit declaration is the acceptance.** The gate accepts a report status that `check_artifacts.py` prints as `declared_status.accepted`. It still returns "repair" for gaps, an undeclared conditional status, a placeholder, or a degradation the report does not record. A completion with known limits has to be declared as one: the exit lists the status in `limited_statuses` as well, and the checker then requires `known_limits`, a non-empty list of `{limit, evidence}`. A status in the checker's blocking list can never be declared accepted.

**B. A node writes only what it owns.** The node prompt and the repair prompt both say so: exit artifacts, required documents and declared `parallel_write_scopes`. A defect in another node's file is reported as `cross_node` with `suspected_root_node`, and the owner repairs it.

**C. A file is an input only once its producer has published it.** The freshness `read` refuses a path whose producing node has no valid evidence, answers `unpublished_producer`, records nothing and returns no content. A node the reader is ordered after is exempt, so a repair still reads the failed report it answers. Nothing is moved or deleted: the leftover stays on disk until its own node overwrites it.

**D. A driver brackets what it dispatches.** `begin-wave` keeps each node's evidence, contract and registered reads; `end-wave` forgets them once the driver has seen the attempt end. `recover-waves`, run at the next start, returns every node of a wave that never closed to what it had, unless a completed transition was recorded for it since.

## Alternatives rejected

- Teaching the gate a project's own key for allowed limits. The key was invented by one generated plan; the declaration every plan already has is `accepted_statuses`.
- Quarantining leftover artifacts at the start of a cycle. An exit artifact can be product source that existed before the run, and moving it is not recoverable by the node that owns it.
- Writing a `dispatched` transition instead of a separate marker. Every reader of `transition_log` would have to learn a status that is neither completed nor failed.

## Cross-host (ADR-0004)

| Decision | Claude | Codex | Pi |
|---|---|---|---|
| A | `gateNodePrompt`, also used by the inherit check | The checker alone gates; no change beyond the shared checker | Same as Codex |
| B | `runNodePrompt`, `repairPrompt` | `build_prompt` item 11 | Pi Dispatch worker rule |
| C | Shared `evidence_freshness.py` | Same | Same |
| D | Engine calls `recover-waves` before loading, `begin-wave` / `end-wave` around each wave | `flow.py`: preflight recovers, dispatch begins, recording a transition ends | The orchestrator session sends the three operations itself |

## Consequences

- A project bootstrapped earlier needs its scripts refreshed by `/bootstrap` to get the new freshness operations; without them the engine's wave calls fail harmlessly and nothing is recovered.
- A plan that wants a limited completion to pass must declare it in `limited_statuses`; an accepted status that only sounds limited is still judged by the gate.
- A safety halt returns before recording transitions on Codex, so its nodes' records are rolled back at the next start. They were quarantined pending revalidation anyway.
- Each wave on the Claude engine costs two more short agent calls.
