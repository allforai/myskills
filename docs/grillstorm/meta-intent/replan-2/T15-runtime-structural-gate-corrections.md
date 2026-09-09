# T15 — runtime structural gate corrections (spec finding 1)

Base `47ea2855`. Repairs finding 1 of `T15-47ea2855-spec-review.md`: *"`/run` does not enforce the
new structural gates on Claude (partial)"*. Findings 2 (repair-budget accounting) and 3 (candidate
freshness ledger) are out of this scope and untouched here.

## The defect

`bootstrap-node-expansion-qa/SKILL.md` states the structural gates are decided by the copied
`validate_bootstrap.py` "at both the bootstrap and `/run` boundaries". They were not.
`validate_repair_loop_declaration` and `validate_effect_stage_ownership` were reachable only from
`validate_bootstrap.main()`. Codex's `/run` runs that CLI (`flow-template.py:1042`), Claude's runs the
readiness gate alone (`orchestrator-template.md:36`), and the readiness gate imported only
`plan_confirmation_blockers`. A `downstream_effect_owner` naming a missing node, or a declared loop
with no closure holder, executed unblocked on Claude — breaking #13 "Claude 与 Codex 的实际入口和生成
产物消费同一权威规则".

## The change

One canonical implementation, two consumers. No rule is restated.

- `validate_bootstrap.py`: the two gates now build typed findings (`{code, message, node_id?}`) —
  `repair_loop_declaration_findings`, `effect_stage_ownership_findings`. The public
  `validate_repair_loop_declaration` / `validate_effect_stage_ownership` become one-line rendering
  wrappers over them, so the bootstrap CLI's `code: message` strings are unchanged byte for byte.
  This is the file's existing idiom (`plan_confirmation_findings` / `validate_plan_confirmation`).
- `validate_bootstrap.py`: new `structural_gate_blockers(project_root)`, the run-time entry, mirroring
  the existing `plan_confirmation_blockers(project_root)` beside it.
- `validate_unattended_readiness.py`: `blockers.extend(structural_gate_blockers(project_root))`,
  placed with the other "`/run` must not assume bootstrap ran and passed" re-checks. Four lines.
- `effect_stage_ownership_findings` now guards a non-list `nodes` the way the repair-loop gate already
  did. A run-time entry reaches it on whatever the graph currently holds; before this it raised
  `TypeError` out of the readiness CLI on `{"nodes": null}` / `{"nodes": false}`.

Both adapters ship one file: `codex/meta-skill/scripts` is a symlink to `claude/meta-skill/scripts`,
so `validate_bootstrap.py` and `validate_unattended_readiness.py` are the same inodes on both hosts.
No adapter copy was edited into agreement; there is nothing to keep in sync.

Nothing was added to the readiness gate's own rule set: `_validate_repair_loop_spec` (graph edges,
budget) is unchanged, and every confirmation, provenance and freshness check is untouched.

## Files

- `claude/meta-skill/scripts/orchestrator/validate_bootstrap.py`
- `claude/meta-skill/scripts/orchestrator/validate_unattended_readiness.py`
- `claude/meta-skill/tests/unit/test_planning_audit_contracts.py` (new runtime-parity tests)
- `claude/meta-skill/tests/unit/test_validate_unattended_readiness.py` (fixture correction, below)

No driver file, skill document, orchestrator template, commit, install or host launch.

## Red / green evidence

New tests in `test_planning_audit_contracts.py`, each parametrized `host=claude|codex`; the fixture
copies that host's public script tree into `.allforai/bootstrap/scripts/` and runs the public CLI as
`/run` does.

Red at `47ea2855` + tests only (`pytest -k "run_refuses or run_accepts"`), 4 failed / 2 passed:

```
test_run_refuses_a_repair_loop_with_no_closure_holder[claude]  FAILED
  AssertionError: ['stale_evidence', 'stale_evidence', 'stale_evidence']   # then, after the
  fixture published its contracts: no structural code at all
test_run_refuses_an_effect_deferred_to_a_node_that_cannot_prove_it[claude] FAILED
  AssertionError: 'unowned_effect_stage' in ['stale_evidence']
test_run_accepts_the_canonical_declared_loop[claude|codex]      PASSED
```

The positive case passed red and green: the fix refuses the unroutable graphs without narrowing the
routable one.

Green after the change — the readiness CLI's own stdout, exit 1:

```
# repair loop with no closure holder (sole blocker)
{"code": "undeclared_repair_loop_routing",
 "message": "required_repair_loops[0] names repair node 'repair-export' with no closure_node_ids;
             nothing waits for the QA rerun",
 "node_id": "repair-export"}
# and the bootstrap CLI on the same fixture, exit 1, identical rule:
{"errors": ["undeclared_repair_loop_routing: required_repair_loops[0] names repair node
             'repair-export' with no closure_node_ids; nothing waits for the QA rerun"]}

# downstream_effect_owner naming a missing node (sole blocker)
{"code": "unowned_effect_stage",
 "message": "workflow.json deliver-export defers its effect proof to non-existent node 'no-such-node'",
 "node_id": "deliver-export"}
```

Both refusal tests assert the structural code is the **only** blocker, so the refusal is this rule and
not incidental staleness. The valid canonical loop returns exit 0, `status: ready`, zero blockers.

Suites:

| Suite | Result |
|---|---|
| `test_planning_audit_contracts.py` (6 new + 15 existing) | 21 passed |
| `test_validate_unattended_readiness.py`, `test_validate_bootstrap.py`, `test_acceptance_allocation.py`, `test_plan_confirmation_gate.py`, `test_planning_audit_contracts.py` | 108 passed |
| `test_bootstrap_scope.py` | 142 passed |
| `claude/meta-skill/tests/unit` (full) | 812 passed in 286s (806 at `47ea2855` + 6 new) |
| `codex/meta-skill/test_flow.py -k "readiness or bootstrap or gate or declared"` | 14 passed |

## Two regressions the gate exposed, and how they were resolved

1. `test_bootstrap_scope.py::test_malformed_workflow_...[null-nodes, boolean-nodes]` — the readiness
   CLI raised `TypeError: 'NoneType' object is not iterable` on stderr. A real defect in the newly
   shared function, not a test artifact: fixed in `effect_stage_ownership_findings` (shape guard
   above), which also hardens the bootstrap entry.
2. `test_validate_unattended_readiness.py::test_unattended_readiness_accepts_a_bounded_repair_loop`
   and `..._warns_when_a_repair_budget_is_omitted` — their fixture's `closure-qa` was
   `hard_blocked_by: ["runtime-repair"]` only. That is precisely the shape the canonical rule refuses
   (`test_closure_that_never_waits_for_the_qa_rerun_is_refused`, shipped at `2cc347af`): closure would
   fire on the repair alone, without the QA rerun. The fixture, not the rule, was wrong under parity;
   it now also waits on `runtime-qa`. No production behavior was relaxed to make it pass.

## Remaining limits

- **Not fixed here.** Findings 2 (repair-budget accounting diverges between adapters) and 3 (candidate
  freshness ledger contradicts itself) are untouched; they belong to other owners.
- **Codex driver tests are red from concurrent in-flight work, not from this change.**
  `codex/meta-skill/test_flow.py` reports 7 failures (`test_a_repair_attempt_that_delivers_nothing...`,
  `test_a_shared_repair_node_budgets_each_qa_node_separately`, `test_a_spent_budget_survives_a_restart`).
  All assert on `flow.repair_progress` accounting, and `codex/meta-skill/knowledge/flow-template.py`
  is modified in the working tree by the worker who owns finding 2. The validator-adjacent subset of
  that file (14 tests) passes. Re-run the whole file after both workers settle.
- **Adapter parity is proved at the copied public CLI, not by a live host run.** Both hosts execute
  the same file (symlinked tree), and the tests exercise each host's tree through `subprocess`, but no
  Claude `/run` or Codex `codex exec` session was launched — consistent with this task's no-host-launch
  boundary. The 60 host cells at `actual_host_passed: 0` noted in the spec review are unchanged.
- **A concurrent worker is editing the drivers.** `orchestrator-template.md`, `flow-template.py` and
  `run-engine/*` are modified in this shared working tree by the finding-2 owner. This repair sits
  below them at the validator, so it holds whichever way those templates land; if that worker also
  routes Claude's `/run` through `validate_bootstrap.py`, the rule is still decided once here and the
  two entries agree rather than duplicating.
- **The scope of the parity claim.** Claude's `/run` now decides the same repair-loop routing and
  deferred-effect ownership rules as bootstrap and Codex. It still does not run every check
  `validate_bootstrap.main()` performs (node-spec coverage, approval records, domain flow validators);
  closing that fully would mean the readiness gate calling the bootstrap CLI outright, which is a
  driver-level decision and was not made here.
- **`unowned_effect_stage` now has two producers** — `product_intent.validate_scope` (the owner must
  carry this node's confirmed requirements) and this structural gate (the owner must exist, run later,
  and prove an effect). They are different rules under one code, as before this change; readiness can
  now emit both in one report.
