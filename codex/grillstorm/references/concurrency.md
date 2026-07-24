# Concurrent Workflow

Use this protocol only after the launch contract is approved. It adds scheduling and
isolation; it does not replace Grillstorm's specs, TDD, review, or completion gates.

## Eligibility

- `diagnostic` and `direct`: keep implementation sequential. Run the independent Standards
  and Spec reviews concurrently when fresh-context agents are available.
- `ticketed`: enable concurrent execution when at least two ready tickets are independent.
- `program`: enable concurrent execution by default.

Concurrency means dispatch every dependency-ready task, not every task in the run. A task
with unsatisfied `effective_deps` must wait. Tasks sharing a physical resource must also
wait on that resource's mutex.

## Frozen workflow inputs

Before dispatch, create these inside the run directory:

```text
tasks/workflow-tasks.json
tasks/interfaces.json
tasks/orchestration.json
tasks/workflow-simulation.json
workflow-state.json
workflow-events.jsonl
workflow-report.json
```

Apply the frozen `THINK`, `BUILD`, and `VERIFY` mapping from `model-policy.md` to every
agent call. Capability resolution happens before launch; execution never chooses a new
fallback.

Each task in `workflow-tasks.json` contains:

```json
{
  "id": "T-module-01",
  "title": "vertical outcome",
  "requirements": ["R-module-01"],
  "touched_paths": ["src/file.ts", "tests/file.test.ts"],
  "acceptance_cmd": "the focused non-vacuous check",
  "depends_on": [],
  "implements": ["api:example"],
  "requires": [],
  "resources": [],
  "reality_gate": false,
  "artifact_contract": {}
}
```

`depends_on` records explicit task ordering. `implements` and `requires` use the frozen
interface registry and create derived cross-module edges. `resources` names exclusive
non-file resources such as `sim:default`, `stack:test`, or `db:migration`.

Build the deterministic inputs with the bundled scripts:

```bash
python3 <skill>/scripts/validate_plan_tasks.py tasks/workflow-tasks.json tasks/interfaces.json
python3 <skill>/scripts/build_artifact_contracts.py tasks/workflow-tasks.json tasks/workflow-tasks.frozen.json
mv tasks/workflow-tasks.frozen.json tasks/workflow-tasks.json
python3 <skill>/scripts/build_task_dag.py tasks/workflow-tasks.json > tasks/orchestration.json
python3 <skill>/scripts/simulate_workflow.py \
  tasks/orchestration.json tasks/workflow-tasks.json \
  --output tasks/workflow-simulation.json
```

Any validation error, cycle, missing dependency, or unimplemented required interface blocks
launch and returns to task planning. Do not repair the graph in a worker.

Review the simulation before launch. It must expose the initial ready set, informational
dependency waves, maximum ready width, resource mutexes, path merge groups, derived edges,
unreachable tasks, and each task's downstream failure blast radius. Simulation dispatches no
agent and mutates no Git state.

## Worktree model

Create one run-owned integration ref/worktree from the frozen starting commit. Every ready
task branches into its own task worktree from the current integration baseline. Executors
write only inside their task worktree.

Worktrees permit all ready writers to execute concurrently, including tasks whose expected
paths overlap. They do not remove semantic dependencies or merge conflicts:

1. executor completes one task with TDD and runs its focused acceptance;
2. an independent fresh-context supervisor receives only the task and task worktree;
3. supervisor reruns acceptance and rejects vacuous or out-of-contract changes;
4. confirmed candidates enter a serialized integration queue;
5. integrate against the latest integration ref, rerun post-merge acceptance, then publish
   the new integration ref atomically;
6. a conflict or stale-baseline failure reopens only that task for replay and revalidation.

`isolate_groups` emitted for overlapping paths are merge-collision hints in the default
all-worktree mode, not execution mutexes. Only `resource_groups` block concurrent dispatch.
The compatibility `groups` mode may serialize path groups when a host cannot isolate every
writer.

Every confirmed candidate receives a marker commit named
`grillstorm-confirmed: <task-id>`; a locally sound task waiting on a human-only reality gate
uses `grillstorm-reality-gated: <task-id>`. These markers are the portable completion
authority shared by Claude and Codex.

Never stage, stash, commit, or modify the user's checked-out worktree. Pre-existing dirty
files remain untouched. Do not merge the integration ref into the user's branch until all
applicable global checks and final two-axis review pass.

## Cross-host continuation

Claude and Codex controller files are not wire-compatible merely because both are named
`workflow-state.json`. At a host switch, quiesce dispatch and export
`execution-checkpoint.json` with `scripts/portable_checkpoint.py`.

The checkpoint binds frozen tasks/orchestration, revision counters, baseline/integration
commits, completed task IDs, and their supervised Git markers. The target verifies those
bindings, creates a fresh controller state/event log, recreates the integration ref at the
portable commit, re-resolves its local model policy, and schedules only remaining ready
tasks. Unmerged source worktrees are discarded and their tasks rerun.

A host/model rebinding is logged as an autonomous infrastructure decision. It does not
reopen product decisions or require another launch question when it remains inside the
approved recommendation ladder.

## Ready-set controller

Persist every dispatch, verdict, retry, merge intent, merge completion, escalation, skip,
and reality gate atomically. Recompute the ready set after each confirmed merge. Do not use
layer barriers.

Use separate budgets:

- infrastructure failure: retry twice without consuming the business budget;
- business/supervisor rejection: return feedback to a fresh executor, at most two retries;
- exhausted task: mark escalated, skip its transitive dependents, continue independent work;
- reality gate: integrate sound local implementation, record proof pending, and allow
  dependents whose code contract is satisfied.

Machine-heavy commands can exhaust local resources. If detected, use the launch contract's
`max_concurrency`; otherwise dispatch all ready tasks up to the host Workflow/subagent cap.
Never silently lower an approved cap.

## Claude

When the native Workflow API is available, author one Workflow whose controller maintains
the ready set:

- use `parallel` for all currently ready task agents;
- use `pipeline` only for executor -> supervisor -> serialized integration of one task;
- request `isolation: 'worktree'` for every writer;
- keep integration publication in the controller, never in workers;
- resume using `workflow-state.json`, not conversation history.

Use the exact Phase 0 literals in each call: closure/replan agents use `THINK`, writers use
`BUILD`, and supervisors/reviewers use `VERIFY`. The current preferred mapping is
Fable 5 / Sonnet 5 / Opus 4.8 when those literals are exposed by the Workflow model enum.

If native Workflow or worktree isolation is unavailable, use the bundled deterministic
runner only when a compatible headless Codex command is explicitly configured. Otherwise
fall back to sequential execution and record `concurrency_unavailable`; never simulate
independence in one context.

## Codex

Prefer native fresh-context subagents when the host exposes them. The root agent owns the
ready-set controller and Git integration; each executor and supervisor works in its assigned
task worktree and cannot edit control-plane artifacts.

For a durable headless run, use the bundled runner. The launch approval is the human
confirmation for the frozen model policy; never choose new model tiers mid-run.

```bash
POLICY_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/grillstorm/<goal-slug>"
python3 <skill>/scripts/prepare_codex_policy.py "$POLICY_DIR"
python3 <skill>/scripts/run_layers.py \
  tasks/orchestration.json tasks/workflow-tasks.json \
  --models "$POLICY_DIR/models.json" \
  --prompts <skill>/prompts \
  --root <repo-root> \
  --state workflow-state.json \
  --events workflow-events.jsonl \
  --report workflow-report.json \
  --model-policy-artifact "$POLICY_DIR/model-policy.json" \
  --model-sources "$POLICY_DIR/model-sources.json" \
  --policy-key-file "$POLICY_DIR/policy.key"
```

The command above is the conservative inherited form. A tiered run is allowed only after
all effective model sources are proven unlocked:

```bash
python3 <skill>/scripts/prepare_codex_policy.py "$POLICY_DIR" \
  --model-sources-input /private/model-sources.json \
  --think-model gpt-5.6-sol \
  --build-model gpt-5.6-luna \
  --verify-model codex-auto-review
```

If the active launcher does not expose Luna, resolve BUILD to `gpt-5.6-terra` before launch.
Partial mappings, unknown ownership, or locked sources fail closed to prevent a model flag
from being silently ignored or overridden.

The runner owns ready scheduling, task and integration worktrees, artifact admission,
fresh-context supervision, retry ledgers, transactional merge, recovery, and the retained
integration ref. `prepare_codex_policy.py` conservatively inherits the active host model and
binds it to the launch contract unless a fully evidenced tiered mapping is supplied. It
never selects or downgrades models during execution. The preparation script refuses to
store its integrity key inside a Git repository. For cross-machine resume,
transfer the policy directory through private configuration sync or start a fresh
supervision pass from the retained integration ref. Supply a `max_concurrency` only when the
launch contract selected one.

## Closure

After the concurrent runner finishes:

1. run the full suite and cross-module/runtime acceptance in the integration worktree;
2. run independent Standards and Spec reviews over the fixed integration ref;
3. repair and revalidate through the same task isolation where ownership is clear;
4. merge the verified integration ref into the authorized target branch;
5. update catalog/state and include concurrency, retries, conflicts, skips, reality gates,
   and the final integration SHA in `execution-report.md`.

Worker completion, a green focused test, or a successful Git merge is never global
completion.
