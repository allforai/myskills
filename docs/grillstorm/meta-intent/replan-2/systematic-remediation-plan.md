# Systematic execution-contract remediation

Status: Q1 scope is resolved by accepted Q3; Q2–Q10 decisions accepted in the grill-with-docs interview. The user confirmed the complete plan and authorized implementation, then requested maximum parallelism. Implementation is in progress; existing worktree edits predate this plan and are not evidence that this plan is implemented.

## Scope and boundaries

Boundedly refactor validation, repair dispatch, budget accounting, QA, stopping, and test isolation. Preserve Claude Workflow and the Codex executor; align business decisions for equivalent graphs, evidence, and events, not execution traces. Do not rewrite the whole meta-skill, weaken acceptance, or silently reset historical runs. ADRs 0004–0007 record the accepted trade-offs.

## Implementation workstreams

1. Establish explicit contract scenarios and canonical vocabulary for admission, repair authorization, delivery, independent QA acceptance, and stopping. Delivery must never stand in for acceptance. Map host-specific entry points to these contracts before changing them.
2. Make validation reject malformed input with a current structured verdict. Validate shape before semantic graph operations; stale ready files cannot grant admission, including when report generation fails. Keep deterministic shared rules in one authoritative implementation where host constraints permit.
3. Introduce uniquely identified, durable repair authorizations and idempotent per-QA accounting. A shared repair charges only the obligations authorized for that attempt, never exhausted siblings. Protect accounting against duplicate calls, partial multi-obligation updates, and concurrent writes; confirm durable authorization before execution. Recovery must not blindly replay uncertain execution or automatically refund an authorization.
4. Separate failure classification by obligation and node identity, not overlapping category counts. Preserve legitimate cross-loop roles while prohibiting self-acceptance for the same obligation. A safety halt stops new dispatch run-wide; ordinary QA failures block the related dependency chain. Safely cancel in-flight work where supported, otherwise isolate its results from acceptance pending revalidation.
5. Distinguish provably new runs from historical or uncertain state. Reconstruct old accounting only with complete uniquely attributable evidence and preserve provenance. Otherwise provide an actionable blocker; creating a separate new run requires explicit user confirmation.
6. Isolate test imports and identify ownership of divergent shared/host validators rather than weakening fixtures or production gates to make combined tests green. Verify individual suites and the combined collection environment.

The common contract/scenario work precedes host integration. After interfaces are fixed, disjoint host adaptations and test-isolation work can proceed in parallel; combined verification follows integration. Implementation-specific mechanisms must respect actual host capabilities, particularly Claude's delegated filesystem operations and cancellation limits.

## Accepted verification requirements (Q10)

- Common contract scenarios: both hosts agree on admission, exhausted and shared budgets, repair delivery versus QA acceptance, overlapping roles, and safety stopping.
- Fault and combination tests: interrupted accounting, duplicate requests, concurrent writes, stale ready evidence, missing/ambiguous historical accounting, and same-named module contamination. Also verify in-flight results cannot cross a safety halt into acceptance without revalidation.
- Actual-host acceptance: retain the original Claude/Codex campaign, including all 60 required cells. Simulated driver tests do not replace real host behavior. Export a fresh candidate and obtain fresh evidence; historical acceptance remains withdrawn.

## Completion boundary

Reproduce the known defects, demonstrate their corrections, run combined suites and independent review, and complete actual-host acceptance against the accepted candidate before merging to main. Preserve unrelated work and historical evidence; clean only validated task worktrees after the accepted merge. No remote push, trust bypass, or installation change is implied by this plan. External access or evidence blockers must be reported, not bypassed or relabeled as success.
