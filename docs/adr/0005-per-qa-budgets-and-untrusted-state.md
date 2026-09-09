---
status: accepted
---

# Preserve per-QA budgets and stop on untrusted state

The user accepted Q3–Q5 in the grill-with-docs session: perform a bounded refactor of validation, repair dispatch, accounting, QA, and stopping, including test isolation, without rewriting the entire engine or reducing actual Claude/Codex acceptance requirements.

QA obligations sharing a repair task retain independent budgets. An obligation with remaining budget may authorize further repair, but an exhausted sibling must not be charged again or silently treated as accepted; final acceptance still requires satisfying that sibling.

Untrusted state stops affected work: stale ready reports cannot authorize execution, and missing historical repair accounting cannot be interpreted as zero consumption. A provably new run may start at zero; an existing run must recover trustworthy state before resuming. This deliberately sacrifices automatic continuation when evidence is missing to preserve budget and acceptance guarantees.

Q6–Q8 were subsequently accepted and are recorded in ADR 0006. Historical recovery was accepted in Q9 and is recorded in ADR 0007. These decisions do not authorize implementation before the interview concludes.
