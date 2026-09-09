---
status: accepted
---

# Separate safety stopping, repair authorization, and QA obligations

The user accepted Q6–Q8 in the grill-with-docs session. A safety halt stops new dispatch across the current run, while ordinary QA failure blocks the related dependency chain. In-flight tasks should be cancelled where safely supported; otherwise they may finish, but their outputs must be quarantined from acceptance until revalidated. This does not assume that both hosts expose cancellation or can undo work already performed.

Repair budget is consumed by a durably recorded authorization, with a unique identity and idempotent accounting. No automatic refund is granted after a crash, even if execution might not have started; if recovery cannot establish whether execution occurred, it must stop for reconciliation rather than blindly replay. This favors preventing duplicate side effects and excess repair over automatic continuation.

A node may have different roles across repair loops, but a repairer may not independently accept its own work for the same acceptance obligation. Outcomes are tracked against the specific QA obligation; success in one role cannot cancel another role's blocker or a safety halt. Cross-loop roles remain supported rather than banning a currently valid graph shape to hide a failure-accounting defect.

These are target contracts, not claims about the current implementation. Historical recovery and the verification plan were subsequently accepted in Q9–Q10; see ADR 0007 and the systematic remediation plan.
