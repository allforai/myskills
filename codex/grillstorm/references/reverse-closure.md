# Reverse Closure

Design the run backward from observable completion:

```text
goal complete
<- runtime behavior proved
<- integrated code globally verified
<- every work unit independently supervised
<- published tickets and executable workflow preserve approved tasks
<- workflow dependencies and integration are sound
<- tasks completely realize the specs
<- modules/interfaces form a stable closed graph
<- specs express the approved goal
<- Grill resolved the human decisions
```

Do not advance when an arrow cannot be demonstrated.

## Outcome-first record

Before decomposing modules, record in `program-spec.md` or the compact route state:

- observable user outcome;
- required real side effects;
- success, empty, degraded, failure, and recovery behavior;
- automated proof and human-only reality gates;
- global completion evidence.

Use this record to derive module boundaries and test seams. Do not invent acceptance only
after implementation tasks exist.

## Early reuse radar

Before freezing the initial module graph, inspect the current repository and write
`reviews/reuse-radar.md` for `program`, or a compact state entry for smaller routes.

Inventory:

- existing deep modules and callable interfaces;
- domain policies, algorithms, state machines, adapters, and integration boundaries;
- duplicated knowledge or invariant enforcement already present;
- approved requirements likely to share a capability;
- third-party libraries already selected by the project.

Classify each candidate `reuse`, `extend`, `possible-extract`, or `keep-local`. This is a
non-binding radar, not permission to create a module. Final extraction waits for complete
consumer specs and the abstraction gate.

## Local then global

Apply the same pattern at both design levels:

- close each module spec before moving on, then reverse-Grill and independently close the
  complete spec graph;
- close each module's task document before moving on, then reverse-Grill and independently
  review the complete task graph from global acceptance back to prerequisite work.

Local closure catches defects cheaply. Global closure catches cross-module gaps that no
single module can see. At both spec and task levels, the reverse Grill turns newly exposed
product/design ambiguity into one recommended question at a time; independent critics check
that the answers did not merely make the documents look complete.

After tickets and the machine DAG exist, run a third reverse Grill over the executable
projection. Its narrower purpose is to prove the tracker and scheduler preserve the closed
task graph and catch projection, dependency, resource, proof, or operational gaps before
launch.

## Revision and invalidation

Persist monotonic revisions in `state.json`:

```json
{
  "spec_revision": 3,
  "task_revision": 2,
  "workflow_revision": 2,
  "launch_revision": 1
}
```

Every downstream artifact records the upstream revision it was generated from.

- Spec change: invalidate affected module approvals, every derived task, workflow, and
  launch contract.
- Task change: invalidate tracker synchronization for affected tasks, workflow, and launch
  contract.
- Workflow change: invalidate its dry-run report and launch contract.
- Launch-policy change: invalidate only launch approval unless it changes scope/spec/tasks.
- Model-role mapping, model-source evidence, or launcher capability change: invalidate the
  local model-policy binding and every worker fingerprint; do not resume old workers under
  a new model. A verified cross-host continuation may retain the goal launch approval when
  it resolves inside the approved recommendation ladder; record the rebinding as an
  autonomous infrastructure decision.

Mark stale artifacts explicitly; never silently edit them in place and retain an approved
status. Regenerate only the affected subgraph, then rerun its local and global gates. No
worker may execute when task/workflow revisions do not match the current spec revision.
The approved model ladder is part of `launch_revision`; each host's effective mapping and
worker fingerprint are local bindings beneath that revision.

## External interaction

Expose only decisions and compact gate summaries:

```text
goal decisions
-> module/spec confirmation
-> newly surfaced closure decisions
-> task/execution summary
-> one launch approval
-> final report or handoff
```

Internal critic findings, deterministic graph repairs, path collisions, and ordinary test
failures do not require user interaction unless they expose a new pre-launch product or
boundary decision.
