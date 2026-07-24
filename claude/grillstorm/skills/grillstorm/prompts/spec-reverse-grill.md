# Reverse Spec Grill

Inspect the frozen program spec and every module spec as one system. Work backward from each
observable global outcome and identify unresolved issues that could make the design
incomplete, contradictory, unsafe, or impossible to prove.

Apply these lenses:

1. **Problem closure:** actors, outcomes, scope/non-goals, success, empty, degraded, failure,
   recovery, and real side effects.
2. **Domain/design closure:** terminology, ownership, boundaries, invariants, state
   transitions, data lifecycle, dependency direction, interfaces, errors, compatibility,
   migration, rollback, and observability.
3. **Cross-spec consistency:** program/module claims, producer/consumer contracts, shared
   data, error semantics, lifecycle, and acceptance behavior agree.
4. **Exceptional behavior:** invalid input, partial failure, timeout, cancellation, retry,
   idempotency, concurrency/race, stale data, external outage, permission denial, cleanup,
   degraded operation, and recovery.
5. **Reuse and abstraction:** existing modules can be reused or extended; duplicated stable
   policy/invariants may justify a deep shared module; speculative abstraction stays local.
6. **Proof closure:** every behavior has the highest useful test seam, runtime observation,
   and completion evidence; every proposed artifact traces to an approved outcome.

Classify every issue:

- `discover`: answer from repository, tools, or authoritative documentation;
- `spec-repair`: approved intent already determines the correction;
- `decision`: multiple materially different product/design answers remain.

Do not turn discoverable facts or mechanical corrections into user questions. For each true
decision, propose one recommended answer, its main tradeoff, and affected artifacts. Order
decisions by dependency and blast radius so the orchestrator asks exactly one at a time.

Return only:

```json
{
  "status": "closed|needs_work",
  "reverse_outcomes_checked": ["outcome or requirement ID"],
  "issues": [
    {
      "id": "SG-01",
      "lens": "problem|design|consistency|exception|abstraction|proof",
      "classification": "discover|spec-repair|decision",
      "broken_reverse_chain": "proof <- behavior <- interface/state <- owner <- requirement",
      "question": "empty unless classification is decision",
      "recommended_answer": "answer or repair",
      "main_tradeoff": "short tradeoff",
      "affected_artifacts": ["paths or IDs"],
      "blocks": ["issue IDs"]
    }
  ]
}
```

Return `closed` only after every lens was applied to every global outcome and no unresolved
issue remains.
