---
status: accepted
---

# Building blocks are asked before the run

ADR-0011 made bootstrap ask every user-visible rule before an unattended `/run`. Its decision rehearsal asks only about rules a user would meet; "a choice that only shapes internals" is explicitly not a question. In a real product bootstrap that meant about 60 questions, of which only five were technical, and those five came from the concept pass at direction level. Every other building block — client state management, the cache, file storage, the component library, and so on — was left to whichever node met it first, overnight.

Those choices are the person's even though no end user sees them. They decide what the person has to run, pay for, maintain and hire for, and changing one later means rework in every node built on it. A run that picks them is a run whose result the person may not be able to keep.

## Decision

**A. Rehearsal gains a stack angle.** In the same pass as decision rehearsal, for every node that designs, builds or styles the product, the reader also answers: *which building blocks would I have to pick that these do not settle?* A building block is something the work is built on and later nodes inherit: the game engine; the client framework, state management, routing, component library, styling approach and visual style; the server language and framework, database, cache, file or object storage, queue, realtime transport and authentication; the API style, hosting and deployment, build and test tooling. The list illustrates. The test is whether changing the choice later means rework in nodes that build on it. Each block is asked once, at the first node that would pick it, with 2–3 options, trade-offs and a recommendation.

Not questions: a block the existing code already uses, unless the baseline asks to move off it; a block the baseline, journal, profile or experience direction already names; a choice inside a settled block (a table's columns, a store's module layout, a component's props), which stays the node's own work. Leaving a block out (no cache, no queue, no component library) is a choice too: each omission is listed with the questions as a recommendation the person confirms or overrides. Thought testing showed why: without that sentence the reader judged "no cache needed at this scale" and the person never saw it. The person may hand a layer back ("you pick"); that is recorded with the recommendation as the decision and `delegated: true`.

Phase A asks building blocks by layer (engine and client, server, storage, UI style), asking a block others depend on before them.

**B. A block the rehearsal missed does not stop the run.** Unlike a product rule, a node may pick a building block. It picks the option that fits the existing code and settled inputs and discloses it: on Claude as an `assumed_decisions` entry with `kind: "building_block"`, read at the end of the run; on Codex as a run warning naming the block. The next interactive bootstrap can turn it into a question.

The angle shares the `node-rehearsal` provenance of ADR-0011, so coverage, staleness and validation are unchanged.

## Cross-host (ADR-0004)

| Decision | Claude | Codex | Pi |
|---|---|---|---|
| A | Canonical `bootstrap-audits.md` A0 and Phase A | Same, `skills/bootstrap.md` names it | Same, bootstrap SKILL names it |
| B | `engine-core.js` node prompt | `flow.py` prompt item 9 | No engine of its own |

## Consequences

- Bootstrap asks more questions on a product with no existing code. Answers by layer and "you pick" keep that bounded.
- A project with established code is asked little: what it already uses is settled.
