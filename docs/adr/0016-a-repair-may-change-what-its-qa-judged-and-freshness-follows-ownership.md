---
status: accepted
---

# A repair may change what its QA node judged, and freshness follows ownership

Two live product runs on 0.29.0 reported five faults. One was introduced by ADR-0015; the rest were older.

1. ADR-0015 B told every node to write only its own outputs. A declared design repair node exists to rewrite the specs its critique judged, which upstream nodes produce. It could no longer change anything, every dispatch ended `unmeasured_repair_delivery`, and the loop spent its budget. A repair that did change an upstream artifact left that producer stale, which withheld the repair for a reason other than its QA node, with the same result.
2. The engine tells a re-dispatched node to read `diagnosis-corrections/<node>.json` and deletes the file when the node completes. A node that registered the file as an input had stale evidence the moment it finished, so every diagnosis-driven rerun dead-ended.
3. The freshness `read` accepted a file produced by a completed node the reader is not ordered after. The next readiness check refused that recorded read as `dependency_outside_graph` and required an interactive bootstrap.
4. A node that wrote a shared file inside its own declared `parallel_write_scopes` staled unrelated nodes: the file was in their whole-tree snapshot and nobody had declared it as an input, so the change counted as unmapped for all of them.
5. Each input snapshot embedded the full snapshot of every upstream node, recursively, including the selected baseline text at every level. One node's record reached 10 MB, the state file 33–156 MB, and each observation file 30–41 MB. Observation files were never removed: 3.1 GB in one project.

## Decision

**A. The repair of an open loop may change what its QA node judged.** While a loop is open, its declared repair node may change an exit artifact or required document of a node the QA node is `hard_blocked_by`, directly or transitively — only a file a QA finding requires changed, never a decision input. It then republishes each node whose file it changed, with that node's own validation commands. Every other node keeps the ADR-0015 rule. A repair that changes project source still declares `parallel_write_scopes`; the game 2D expander now defaults its code repair node's scope to the scopes the plan already declares.

**B. A diagnosis correction is orchestration state.** `read` refuses `.allforai/bootstrap/diagnosis-corrections/` like the run's other bookkeeping, and the node is told to read it without registering.

**C. `read` refuses what readiness would refuse.** A path produced by a node the reader is not ordered after is refused whether or not that node has published: `unpublished_producer` when it has not, `producer_outside_graph` when it has. Nothing is recorded. A path already bound to the observation is left to the planning gates.

**D. A change inside a declared write scope belongs to its writer.** In the whole-tree comparison, a changed path inside another node's `parallel_write_scopes` is not an unmapped input of a node that neither declared it nor depends on the writer. The writer and its consumers are still invalidated, and a node's own scope never exempts it.

**E. An upstream is recorded as an identity.** A snapshot stores the digest of each upstream snapshot. A record in the old shape is compacted when compared, so it stays valid while nothing changed, and is rewritten compact the next time its node publishes. `recover-waves` deletes every observation file: no attempt survives to a start.

## Alternatives rejected

- Requiring every repair node to declare `parallel_write_scopes` over what it repairs, enforced by readiness. Design specs live under `.allforai/`, which a write scope may not name, so a design repair could never satisfy it.
- Letting the delivery measure accept a repair withheld by a producer it changed. The producer would stay stale and the QA rerun could not publish.
- Having readiness accept recorded reads of completed producers. The reader would then be bound to a node the scheduler does not order before it on the next rerun.
- Rewriting every stored record compact on the first write. The recorded binding identity of untouched nodes would change under them.
- Deleting an observation when it publishes. A node may publish again with the same observation after fixing an output.

## Cross-host (ADR-0004)

| Decision | Claude | Codex | Pi |
|---|---|---|---|
| A | `deliveryNote` grants it to the repair node of an open loop; `OWN_OUTPUTS_RULE` defers to it | `build_prompt` item 11 states the exception | Pi Dispatch worker rule states the exception |
| B | `runNodePrompt` | `build_prompt` item 10 | Safety section |
| C, D, E | Shared `evidence_freshness.py` | Same | Same |

## Consequences

- Decision A is prompt-level on all three hosts. Nothing verifies that a repair stayed within the files a finding names; a wrong edit shows up as the producer's validation failing or the QA rerun failing.
- A project needs its scripts refreshed by `/bootstrap` to get B–E. Its existing 30 MB observation files are removed at the first run start after that; its state file shrinks node by node as nodes publish again.
- A corrections file a node registered before the upgrade is still in that node's recorded inputs, so that node is stale once more and reruns.
- A node that read a sibling's published output without a declared edge used to finish and block the next start. It is now refused at the read, and must report the missing dependency if it cannot work without the file.
