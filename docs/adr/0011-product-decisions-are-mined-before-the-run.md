---
status: accepted
---

# Product decisions are mined before the run, not discovered during it

An unattended `/run` stopped overnight at its second wave. Bootstrap had passed every gate: decision coverage, decision-input wiring, DAG, unattended readiness, node-spec audit. The product intent was frozen. Then a design node returned `unresolved_product_decision`. It needed a user-visible rule the frozen intent did not settle: whether one stateful thing the user owns is shared across a dimension the product has several instances of, or kept separately per instance. Its upstream concept node had correctly said this node must not choose. The engine treated the failure as `needs_diagnosis` and the whole run stopped, unrelated branches included. Nobody was there to answer.

Every part behaved as written. The fault was in what bootstrap never asked:

1. **A0 accepted an audit that did not happen.** `decision-coverage.json` was hand-written with `missing: []`. `validate_decision_coverage` checks shape only, so an empty audit and a thorough one look the same. Under ADR-0010, that is a verification that did not happen being read as one that found nothing.
2. **A0 looks at the wrong altitude.** Its angles enumerate direction-level forks (style, monetization, technology). Rule-level choices appear only when a design node starts to write rules. The product-intent protocol forbids that node from choosing them. Nothing before `/run` imagines doing each node's work to see what it would have to choose.
3. **No one crosses dimensions with state.** When the frozen intent introduces something the product has several instances of, each thing the product remembers about a user is either shared across those instances or kept per instance. That is a user-visible rule, it is asked nowhere, and its absence surfaces only at design time.
4. **One decision gap stops everything.** A product-decision failure is not a QA verdict, so it takes the generic `needs_diagnosis` exit, even though only its own subgraph depends on the answer.

## Boundary

`/run` is project-specialized: its node-specs, rules and questions are generated for one project. Bootstrap is not. Nothing added here may name a domain, a resource type or an example from any project. The bootstrap rules state what must be true of the result. The concrete questions come from reading this project's node-specs and frozen baseline.

## Decision

**A. Decision coverage carries checkable provenance (fixes 1).** `decision-coverage.json` records, for each pass, its angle, that it ran in a context independent of the planner, the inputs it read with their digests (the frozen baseline version, every node-spec in the current workflow), and when it ran. The validator rejects coverage without provenance, coverage with fewer than the two required angles, and coverage whose digests do not match the current workflow's node-specs and baseline version. An empty `missing` is accepted only with complete provenance. The readiness gate re-checks the digests itself (receiver side, ADR-0010), so a plan edited after A0 makes coverage stale rather than silently still valid. Provenance makes a skipped audit visible. It cannot prove an audit was diligent, and the ADR does not claim it can.

**B. Decision rehearsal replaces A0's second angle (fixes 2).** For every node that will produce or implement an end-user-visible rule, an independent context reads that node's spec, the frozen baseline and the decision journal, and answers only: *to do this work, what user-visible choices would I have to make that these do not settle?* It produces questions and no artifacts. Each question names its node, gives 2–3 options with a recommendation, and says what the node would otherwise be forced to invent. A choice the baseline or journal already settles is not a question. Rehearsal output is A0's node angle, under the same provenance rule. Its questions join the Phase A queue as `missing` entries with that node as `consumer_node`, and Phase A asks them in the same topic-batched turns. The host may run rehearsal on a cheaper model tier. The skill names no model. Rehearsal stops when it has nothing further that a node would have to invent, not when it has reached a count.

This is one artifact and one validator, not a new phase: A0 keeps its concept angle and its node angle becomes per-node rehearsal.

**C. Dimension × state crossing before freeze (fixes 3).** `product-intent-confirmation.md` gains one generic rule. The host identifies, from the draft, the *dimensions* (anything the product offers several instances of that a user moves between) and the *stateful things* (anything the product keeps about a user and shows back). Every pair the draft does not already settle becomes a scope question: shared, per instance, or a stated mix. The `draft` request carries both lists, and `product_intent.py` generates the pair questions as ordinary pending gap questions. `freeze` already refuses unanswered questions that are not explicitly excluded, so no new gate is needed. The CLI checks that the pairs were asked. Whether the host found every dimension and every stateful thing stays the host's semantic job, the same limit the quote validator already states, and rehearsal (B) is the second net. Pairs are presented grouped per dimension. An explicit batch answer such as "all shared except …" counts as an action.

**D. Fallback: a product-decision gap blocks its subgraph, not the run (fixes 4, secondary).** A node that owns a user-visible rule the frozen intent does not settle fails with only `unresolved_product_decision` findings, each carrying the decision it needs and at least two options it weighed, and writes them to `.allforai/bootstrap/product-decision-gaps/<node_id>.json`. Pattern I gaps (`unspecified_user_visible_decision`) keep their own route: an upstream design node can usually answer those. The failure is handled like a usable QA verdict. It blocks that node and its successors, and unrelated branches continue. When nothing runnable remains, the run ends `needs_product_decision` with the collected questions (Codex `flow.py` exit 7). Readiness refuses the next unattended run while a gap record remains. Interactive bootstrap asks the questions in Phase A, wires each answer into the node's `decision_inputs`, and removes the record. A finding without that structure is not trusted as one and still takes `needs_diagnosis`. No Run Policy key delegates a product decision. A recommendation nobody answered is not an action. That rule stays in force inside `/run`.

## Cross-host (ADR-0004)

Codex and Pi load the canonical bootstrap knowledge and scripts, so A, B and C reach them without separate rules. Their adapters only state how rehearsal gets an independent context: a Codex sub-agent, or Pi `pi-subagents`. A bare Pi runs rehearsal serially and discloses that it was not independent. Provenance records that as a distinct outcome, not as a pass. D changes a business decision about stopping. Both the Claude run engine and the Codex executor must implement it, and one shared contract scenario covers both: a product-decision gap on one branch, an unrelated branch completes, and the run ends `needs_product_decision`.

## What this reverses

- A0's shape-valid empty audit counting as decision coverage.
- Rule-level choices first appearing inside an unattended run.
- Treating a single product-decision gap as grounds to stop unrelated work.

## Consequences

- Bootstrap asks more questions up front. Grouping keeps the extra cost to a few turns. That is the trade the user asked for.
- Existing projects whose `decision-coverage.json` has no provenance fail readiness with `decision_coverage_unproven` and must rerun A0 (rehearsal included) from interactive bootstrap.
- Rehearsal cannot see choices that arise only from outputs produced at run time. D exists for those.
