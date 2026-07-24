# Grilling Protocol

This preserves the complete behavioral core of Matt Pocock's `grilling` skill and adds
finite closure rules for a resumable multi-module run.

## Core protocol

Interview the user relentlessly about every aspect of the goal until shared understanding
is reached. Walk down each branch of the decision tree, resolving dependencies between
decisions one by one. For every question, provide a recommended answer.

Ask exactly one question per turn and wait for feedback before continuing. Multiple
questions at once are bewildering and make accepted decisions ambiguous.

If a fact can be found by exploring the environment, filesystem, tools, code, tests, or
docs, look it up instead of asking. Decisions belong to the user: put each decision to
them and wait for the answer.

Do not implement the goal until the user confirms shared understanding.

## Question shape

Use this compact shape:

```text
Question: <one decision>
Recommendation: <the answer you recommend>
Tradeoff: <the most important consequence>
```

Do not present a questionnaire. Alternatives are useful only when they represent real
tradeoffs. Lead with the recommendation.

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

At program and module boundaries, summarize accepted decisions and remaining open branches.
Ask whether shared understanding has been reached only when the closure checks are green.
