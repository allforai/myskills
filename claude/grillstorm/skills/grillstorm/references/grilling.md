# Grilling Protocol

This preserves the complete behavioral core of Matt Pocock's `grilling` skill and adds
finite closure rules for a resumable multi-module run.

## Core protocol

Interview the user relentlessly about every aspect of the goal until shared understanding
is reached. Map the work as a design tree: every decision branches into the decisions that
depend on it.

Work the tree in rounds. The frontier is every decision whose prerequisites are settled.
Ask the whole frontier in one numbered round, then wait for the user's answers before
recomputing it. A question that depends on another open question belongs to a later round.
If the user answers only part of a round, persist those answers and keep the unanswered
questions open; never guess them.

If a fact can be found by exploring the environment, filesystem, tools, code, tests, or
docs, look it up instead of asking. A running fact investigation is an unsettled prerequisite:
defer only its downstream questions and ask the rest of the ready frontier. Decisions belong
to the user: put every ready decision to them and wait for the answer.

Do not implement until every material decision is answered. The answer to each decision is its
approval; do not ask for a later summary, document, phase, or start confirmation.

## Intent before mechanism

For every material request, distinguish the proposed mechanism from the behavior or pain,
underlying purpose, protected constraint, and observable success. When plausible purposes would
change scope, architecture, public interfaces, acceptance, or authority, make the purpose the
frontier decision. Otherwise adopt the evidenced interpretation.

State the inferred purpose before the question and recommend the smallest purpose-complete option.
Persist a purpose chain with source `evidence_verified|user_confirmed`, why requested, evidence,
protected constraint, rejected alternative/tradeoff, and observable acceptance. Confirmation
accepts the purpose and tradeoff, not merely the initial mechanism.

Stop asking why at an observable outcome, a non-negotiable safety/compatibility/legal/operational
constraint, or when another answer would not change a material decision. Record uncertainty rather
than inventing deeper purpose.

## Question shape

Use this compact round shape. Separate questions with a horizontal rule:

```text
❓ **Q1** - **<question title>**: <one independent decision, with real choices when useful>

➡️ <the answer you recommend>
Tradeoff: <the most important consequence>

---

❓ **Q2** - **<question title>**: <another independent decision>

➡️ <the answer you recommend>
Tradeoff: <the most important consequence>
```

Do not present a flat questionnaire: every question in a round must be independently answerable
from the settled tree. Alternatives are useful only when they represent real tradeoffs. Lead
with the recommendation.

## Decision order

Resolve high-leverage branches before dependent details:

1. Desired outcome and user-visible behavior
2. Scope and explicit non-goals
3. Domain concepts and ownership
4. Module boundaries and dependency direction
5. Public and cross-module interfaces
6. Failure behavior and state transitions
7. Test seams and acceptance evidence
8. Operational constraints and migration

## Closure

A branch is closed when:

- its decision is recorded;
- dependent decisions are either resolved or explicitly out of scope;
- terminology is unambiguous;
- behavior can be observed at an agreed test seam; and
- no contradiction remains with code, glossary, ADRs, or another approved module.

Do not keep asking cosmetic or internal implementation questions after closure. Internal
naming, private data structures, and local file organization are autonomous unless they
affect an approved boundary or acceptance criterion.

At program and module boundaries, persist accepted decisions and remaining open branches
internally. The Grill closes when the frontier is empty. Green closure advances automatically
without a separate shared-understanding or start confirmation.
