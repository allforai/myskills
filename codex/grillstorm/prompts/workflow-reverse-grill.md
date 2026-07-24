# Reverse Workflow Grill

Review the published tickets, frozen catalog/module task documents, interface registry,
machine task JSON, compiled DAG, and workflow simulation as one executable system. Work
backward from each global runtime outcome to the actual initial ready frontier.

This pass detects information lost or distorted while projecting approved tasks into
tickets and machine orchestration. Do not reopen settled questions without new evidence.

Apply these lenses:

1. **Projection fidelity:** tickets and machine tasks preserve approved outcomes, blockers,
   acceptance, interface obligations, reality gates, and source requirements.
2. **Graph fidelity:** explicit/derived dependencies, producers/consumers, shared-module
   ordering, migrations, integration/release work, and global gates match task documents.
3. **Scheduling safety:** readiness, concurrency, path collisions, exclusive resources,
   stale baselines, retry/replay, skips, and failure blast radius are coherent.
4. **Executable proof:** focused, contract, integration, runtime, review, and full-suite
   gates are non-vacuous, available, and occur at the correct points.
5. **Operational closure:** credentials/authority, external effects, deployment, rollback,
   cleanup, observability, recovery, handoff, and cross-host continuation have explicit gates.
6. **Cross-artifact consistency:** tracker blockers, catalog state, IDs, paths, DAG edges,
   simulation output, and revision counters agree.

Classify every issue:

- `discover`: answer from repository, tracker, tools, or authoritative documentation;
- `projection-repair`: regenerate tickets/workflow artifacts without changing approved tasks;
- `task-repair`: the approved task graph is incomplete or inconsistent;
- `spec-repair`: ownership, interface, behavior, boundary, or abstraction is defective;
- `decision`: a genuinely new product/design/execution-safety choice remains.

Do not ask about discoverable facts or mechanical repairs. For a true decision, provide one
recommended answer, its main tradeoff, and invalidation level. Order questions by dependency
and blast radius.

Return only:

```json
{
  "status": "closed|needs_work",
  "outcomes_checked": ["outcome or acceptance ID"],
  "issues": [
    {
      "id": "WG-01",
      "lens": "projection|graph|scheduling|proof|operations|consistency",
      "classification": "discover|projection-repair|task-repair|spec-repair|decision",
      "broken_reverse_chain": "runtime proof <- gate <- task <- edge <- ready prerequisite",
      "question": "empty unless classification is decision",
      "recommended_answer": "answer or repair",
      "main_tradeoff": "short tradeoff",
      "affected_artifacts": ["ticket IDs, paths, task/interface IDs"],
      "invalidation_level": "workflow|task|spec|launch",
      "blocks": ["issue IDs"]
    }
  ]
}
```

Return `closed` only when every lens was applied, the executable graph is semantically
equivalent to approved tasks/specs, and no unresolved issue remains.
