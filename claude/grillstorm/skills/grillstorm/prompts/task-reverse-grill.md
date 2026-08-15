# Reverse Task Grill

Inspect the frozen catalog and every directory/module task document as one system. Work
backward from each observable global outcome and generate only unresolved issues that could
prevent correct implementation or proof.

Apply these lenses:

1. **Problem completeness:** missing user outcome, actor, state, requirement, non-goal, or
   success/empty/degraded/failure/recovery behavior.
2. **Design completeness:** missing owner, boundary, data flow, state transition, interface,
   invariant, algorithm/policy, compatibility rule, migration, rollback, or test seam.
3. **Consistency:** contradictions among specs, catalog, module tasks, directory ownership,
   interface/test registries, touched paths, dependency edges, resources, and acceptance.
4. **Exceptional behavior:** invalid input, partial failure, timeout, cancellation, retry,
   idempotency, concurrency/race, stale data, external dependency outage, permission denial,
   cleanup, observability, and recovery. Classify each mode against
   `references/failure-proportionality.md` before expanding it. Emit an issue only for modes
   whose table result is `full` or `guard-only`. Modes resolving to `none` are recorded as
   classification records, not issues.
5. **Execution reality:** unavailable tool/credential/environment, destructive or paid side
   effect, non-vacuous proof, integration ordering, and runtime validation.

Classify every issue:

- `discover`: answer from repository, tools, or authoritative documentation;
- `task-repair`: approved design is clear; repair task/catalog prose mechanically;
- `spec-repair`: approved intent is clear but the spec graph is incomplete;
- `decision`: multiple materially different product/design answers remain.

Do not turn discoverable facts or mechanical repairs into user questions. For each true
decision, propose one recommended answer, its main tradeoff, and the exact artifacts it
would change. Order decisions by dependency and blast radius so only one is asked at a
time.

Return only:

```json
{
  "status": "closed|needs_work",
  "reverse_outcomes_checked": ["outcome or acceptance ID"],
  "issues": [
    {
      "id": "RG-01",
      "lens": "problem|design|consistency|exception|execution",
      "classification": "discover|task-repair|spec-repair|decision",
      "broken_reverse_chain": "proof <- behavior <- task <- prerequisite",
      "question": "empty unless classification is decision",
      "recommended_answer": "answer or repair",
      "main_tradeoff": "short tradeoff",
      "blast_radius": "contract|module|local",
      "affected_artifacts": ["paths or IDs"],
      "blocks": ["issue IDs"]
    }
  ],
  "failure_classification": [
    {
      "mode": "timeout|partial-failure|race|stale-data|invalid-input|...",
      "outcome": "outcome or acceptance ID",
      "damage": "reenterable|durable|unknown",
      "reentry_proof": "re-entry point and how state converges on re-run",
      "frequency": "routine|rare",
      "frequency_basis": "structural|external-sla|no-recorded-occurrence",
      "frequency_basis_evidence": "the constraint, declared SLA, or inspected history source",
      "expansion": "full|guard-only|none",
      "note": "one line; the whole record when expansion is none"
    }
  ]
}
```

Return `closed` only when every lens was applied to every global outcome and no unresolved
issue remains. A lens is applied when every mode is classified, not when every mode is designed.
Order issues by `blast_radius` — `contract`, then `module`, then `local`.
