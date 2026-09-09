# T15 — repair-budget parity corrections (fixed-review finding 2, base 47ea2855)

Repairs `T15-47ea2855-spec-review.md` finding 2, "Repair-budget accounting differs between
adapters (wrong implementation)", against program-spec **O3 / R30** — "Claude and Codex have
identical authority/routing/readiness semantics".

Owned files only: `codex/meta-skill/knowledge/flow-template.py`, `codex/meta-skill/test_flow.py`,
both `knowledge/orchestrator-template.md` repair-budget sections, `claude/.../run-engine/engine-core.js`
with its exact `run-engine.workflow.js` mirror, and `claude/.../run-engine/tests/repair-loop.test.js`.
No shared validator, helper, or unrelated file was touched; nothing was committed, installed, pushed,
or launched against a host.

## 1. What actually diverged

Not a wording mismatch. The two adapters charged a repair attempt at different points in the
node lifecycle, from different durable records, and therefore reached different remaining budgets
from the same run.

| | Claude (`engine-core.js` @47ea2855) | Codex (`flow-template.py` @47ea2855) |
|---|---|---|
| Durable ledger | `transition_log` entries for the QA node with `status: "failed"` | `transition_log` entries for the repair node that `repair_delivered()` |
| Charged at | route admission, before the repair ever ran | after the repair ran **and delivered** |
| Repair that errors / writes nothing | 1 attempt, then the whole run → `needs_diagnosis` | 0 attempts; the repair is re-dispatched, bounded only by the generic `MAX_CONSECUTIVE_FAILURES_PER_NODE` |
| Interruption between route and executor | attempt spent | attempt not spent |
| Invalid `max_attempts` | nothing routed → QA failure → `needs_diagnosis` | nothing routed → the QA node is silently **re-run** |
| Unreadable attempt ledger | hard failure, no node runs | not detected |

Same fixture, same decisions, different budgets and different terminal states — the O3 proof
obligation fails on the accounting boundary itself, so no amount of template rewording fixes it.

## 2. The accounting contract chosen, and why

> **One repair attempt is spent when the run authorizes a dispatch of a declared repair node
> against a specific failing QA node, recorded durably before that dispatch's executor runs.**
> Not when the QA node fails, not when the repair succeeds, not when it delivers.

Durable ledger, identical on both hosts: `workflow.json` → `repair_routes[]`, append-only entries
of `{repair_node_id, qa_node_id, attempt, dispatched_at}`. Spent budget for a loop is the count of
entries matching that `(repair_node_id, qa_node_id)` pair.

Four reasons this boundary and not another:

1. **Termination.** `max_attempts` exists to bound unattended work. A budget charged on delivery is
   conditional on success, so the exact failure modes that need bounding — a repair whose executor
   errors, or that runs and writes nothing — cost nothing and can repeat. A budget must bound
   attempts; whether an attempt achieved anything is a different question, still answered by
   `repair_delivered` / `measuredDelivery` and finally by the QA rerun.
2. **Crash safety, in the safe direction.** Writing the authorization *before* the work is the only
   ordering that cannot under-count. Over-counting the one attempt that was cut short costs one
   dispatch; under-counting re-grants an attempt whose partial edits may already be in the tree.
3. **Route-open is not dispatch.** Charging at route admission (the old Claude boundary) bills a
   decision that may never be acted on. Charging at dispatch makes route-open and charge coincide
   on Codex, where routing is recomputed each iteration and only becomes an event when the driver
   dispatches — so the same instant exists on both hosts and can be pinned by a test.
4. **One record answers both questions.** `repair_routes` says why a repair ran and how much budget
   is left. The QA node's failed `transition_log` entry goes back to being only the QA node's own
   history, which is what it is on Codex anyway.

Invalid `max_attempts` (declared but not a positive integer): **diagnosis on both, never a re-run.**
It is a planning error. Re-running the QA node reproduces the identical failure with nothing able to
fix it, and buries the planning error in a busy run. Claude stops the run with that QA failure;
Codex blocks the node and reports it, naming the loop under `unbounded_repair_loops`. Both planner
validators still reject the shape before the run — this path is only reached if one gets past them.

## 3. Runtime semantics after the change (both hosts)

Every row was investigated as runtime behaviour, not as documentation.

| Scenario | Attempts spent | Lifecycle boundary |
|---|---|---|
| QA fails → repair delivers → QA reruns → passes | 1 | at the repair dispatch |
| Repair delivers, QA reruns and fails again | 1 per dispatch, up to `max_attempts` | at each repair dispatch |
| Repair executor errors | 1 | at the dispatch — charged before the executor |
| Repair runs and writes nothing / only touches a file / writes a blocked report | 1 | at the dispatch |
| Interrupted between authorization and executor | 1 (already durable) | at the dispatch |
| Interrupted after route-open, before any dispatch | 0 | nothing was authorized |
| Restart mid-loop | re-derived from `repair_routes`, identical to before the restart | — |
| One repair node serving several QA nodes | 1 of *each* answered QA node's own budget | one charge per pair, per dispatch |
| Budget spent, QA node still failing | no further dispatch | `needs_diagnosis` (Claude) / blocked-and-diagnosed repeated failure (Codex) |

Preserved unchanged: measured delivery (`measuredDelivery` on Claude, `repair_delivered` +
`attempt_evidence` on Codex) still decides *sequencing* — when the QA node reruns — at full strength;
no gate, freshness admission, or evidence rule was relaxed; `answered` on Codex remains
delivery-derived. Nothing falls back to legacy or model-claimed evidence anywhere in this change.

**One deliberate carve-out, symmetric by construction.** A repair-node failure carrying a
`NON_QA_FAILURE_TYPES` verdict (`invalid_artifact_gate`, `invalid_readiness_gate`, `deadlock`,
`safety_warning`, `needs_iteration`, `exhausted_retries`) stops the run immediately and is never
re-dispatched. These are structural, environmental or policy answers, not attempts that fell short;
re-dispatching a recorded safety halt would be a real regression. The same set already keeps those
verdicts from opening a repair route at all. Codex reaches the same stop through its own
run-warnings halt and preflight, which are checked before any node is dispatched.

**One residual, named rather than hidden.** Codex additionally applies its generic
`MAX_CONSECUTIVE_FAILURES_PER_NODE = 3` supervisory threshold to every node, so a declared
`max_attempts` above 3 can be cut short there. That bound predates this finding, applies to all
nodes rather than to repair loops, and is documented in the Codex template; equalising it would mean
importing a generic per-node failure threshold into the Claude engine, which is outside this repair.

## 4. Changes

### `codex/meta-skill/knowledge/flow-template.py`
- `repair_attempts_spent(workflow, repair, qa)` — new; counts the `repair_routes` ledger.
- `repair_progress(...)` — spent now comes from the ledger; `answered` stays delivery-derived and
  keeps its meaning (a delivered repair is judged by the QA rerun, never by another repair).
- `charge_repair_attempts(workflow_path, repair_node_id, qa_node_ids)` — new; appends one entry per
  answered QA node.
- `qa_nodes_routed_to(project_root, workflow, repair_node_id)` — new; the QA nodes a dispatch answers.
  Returns `[]` immediately for a node that is not a declared repair node, so the extra gate pass only
  costs anything on an actual repair dispatch (and never on the later finalizing dispatch, whose QA
  node has completed).
- `repair_ledger_unreadable(workflow)` — new; a present-but-malformed `repair_routes` blocks every
  node, matching `runEngine`'s `invalid_repair_attempt_history`. Absent is not unreadable.
- `unbounded_repair_loops(project_root)` — new; loops whose `max_attempts` cannot bound anything.
- `_pending_state` — blocks a QA node that has already failed under an unbounded loop; blocks
  everything on an unreadable ledger.
- `main()` — charges the dispatch immediately before `run_codex`; the blocked-node report now names
  `unbounded_repair_loops` and `invalid_repair_attempt_history`.

### `claude/meta-skill/knowledge/run-engine/engine-core.js` (+ verbatim mirror in `run-engine.workflow.js`)
- `loadDagPrompt` — `repair_attempts[]` is derived from `repair_routes[]`, explicitly not from
  `transition_log`; a malformed ledger omits the QA node rather than restarting it at 0, which the
  existing "missing history" check turns into a hard failure.
- `repairChargePrompt(...)` — new; appends the ledger entry before the repair node runs.
- `repairRoutePrompt(...)` — still records the QA node's failed transition, now explicitly *not* the
  budget entry.
- `runEngine` — the routing branch peeks the budget instead of charging it; the charge moved into the
  dispatch loop, before the `before` measurement; a repair-node hard failure inside its own funded
  loop is retained rather than terminal, subject to the `NON_QA_FAILURE_TYPES` carve-out.

### Templates
Both `orchestrator-template.md` files now state the same contract in their own voice: the charge
point, the `repair_routes` ledger, the two consequences (non-delivery costs an attempt; an
interruption keeps it), that route-open is not the charge, and the invalid-budget rule with each
host's terminal shape.

## 5. Red/green evidence

All commands run from the worktree root at `HEAD 47ea2855` plus these working-tree changes.

**Red — new tests against the pre-change implementations.**

Codex (`git checkout HEAD -- codex/meta-skill/knowledge/flow-template.py`, new tests kept):

```
python3 -m pytest codex/meta-skill/test_flow.py -q \
  -k "charged_before_its_executor or interrupted_repair_dispatch or invalid_budget_blocks or delivers_nothing"
→ 7 failed, 94 deselected
   test_a_repair_dispatch_is_charged_before_its_executor_runs
   test_an_interrupted_repair_dispatch_does_not_get_its_attempt_back
   test_an_explicitly_invalid_budget_blocks_a_failed_qa_node
   test_a_repair_attempt_that_delivers_nothing_never_releases_the_qa_rerun[writes-nothing|touches-only|executor-error|blocked-report]
```

Claude (`git checkout HEAD -- engine-core.js run-engine.workflow.js`, new tests kept):

```
node --test claude/meta-skill/knowledge/run-engine/tests/repair-loop.test.js
→ tests 32, pass 26, fail 6
   loadDagPrompt reads the spent budget from repair_routes, not from failed transitions
   repairChargePrompt writes the ledger entry before the repair node runs
   runEngine: the attempt is charged at the dispatch, after the route and before the work
   runEngine: a repair that never delivers spends the declared budget, then stops
   runEngine: an interrupted dispatch keeps its charge across a restart
   runEngine: one repair node serving two QA nodes budgets each of them separately
```

**Green — after the change.**

| Suite | Baseline @47ea2855 | After |
|---|---|---|
| `node --test 'claude/meta-skill/knowledge/run-engine/tests/**/*.test.js'` | 95/95 | **101/101** |
| `python3 -m pytest codex/meta-skill/test_flow.py -q` | 98/98 | **108/108** |
| `python3 -m pytest codex/meta-skill/tests/unit -q` (symlink; same dir as `claude/meta-skill/tests/unit`) | 812/812 | **812/812** |
| `python3 -m pytest codex/meta-skill/test_install.py -q` | — | **7/7** |
| `python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py` | passed | **passed** |
| `python3 shared/scripts/orchestrator/smoke_codex_generated_run.py` | passed | **passed** |

The `sync-check` test confirms `run-engine.workflow.js` inlines the `engine-core.js` marker region
verbatim; it failed after the engine edit and passes after the mirror, so the two are byte-identical.

**Tests added or rewritten**

Claude (`tests/repair-loop.test.js`, +6):
`loadDagPrompt reads the spent budget from repair_routes, not from failed transitions`;
`repairChargePrompt writes the ledger entry before the repair node runs`;
`the attempt is charged at the dispatch, after the route and before the work`;
`a repair that never delivers spends the declared budget, then stops`;
`a structural failure on the repair node stops the run without a retry`;
`an interrupted dispatch keeps its charge across a restart`; plus a per-pair charge assertion on the
existing shared-repair-node test.

Codex (`test_flow.py`, +10 including parametrisations):
`test_a_repair_dispatch_is_charged_before_its_executor_runs` (reads the ledger from inside the running
executor — what a restart would see if the process died there);
`test_an_interrupted_repair_dispatch_does_not_get_its_attempt_back`;
`test_an_explicitly_invalid_budget_blocks_a_failed_qa_node`;
`test_an_unreadable_repair_ledger_dispatches_nothing` (6 malformed shapes);
`test_an_absent_repair_ledger_is_a_run_that_has_charged_nothing`;
and `test_a_repair_attempt_that_delivers_nothing_never_releases_the_qa_rerun` rewritten to assert both
halves of the contract — the non-delivery never releases the QA rerun *and* it spends its attempt, so
the loop stops at the declared budget.

## 6. Scope boundaries observed

- Finding 1 (structural gates missing from Claude `/run`) belongs to another worker; no validator
  (`validate_bootstrap.py`, `validate_unattended_readiness.py`) or shared helper was edited here.
- Finding 3 (candidate-freshness ledger) is root's; `execution.json` and the results ledgers are
  untouched by this task.
- No commit, no `main`, no remote, no install, no host launch. Focused regressions only; the full
  fixed-ref suite is root's to combine.
