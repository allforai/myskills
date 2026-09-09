# Test import isolation — workstream 6

Scope of this task: workstream 6 of `systematic-remediation-plan.md` — *"Isolate test imports and
identify ownership of divergent shared/host validators rather than weakening fixtures or production
gates to make combined tests green. Verify individual suites and the combined collection
environment."*

No production validator was edited. No assertion was weakened or deleted. The two divergent
`validate_bootstrap` contracts are unchanged and are now pinned as distinct by a regression.

## 1. The defect, reproduced

`shared/scripts/orchestrator/` and `claude/meta-skill/scripts/orchestrator/` each ship a module
named `validate_bootstrap`, and also `check_artifacts`, `check_requires` and `loop_detection`. The
two `validate_bootstrap` modules implement deliberately different contracts: the shared one is the
portable minimum for generated projects (`node:` frontmatter), the Claude one owns `node_id`, the
attention contract, and the `GAME_2D_PRODUCTION_*` constants.

Both suites reached their module through a bare top-level name — the shared suite relied on pytest
prepending its own directory, the Claude suite ran `sys.path.insert(0, "../../scripts/orchestrator")`
first. Whichever suite pytest collected first won `sys.modules["validate_bootstrap"]` for the whole
process, and the `sys.path.insert` was never undone.

Baseline, before any change in this task:

| Command | Result |
|---|---|
| `pytest claude/meta-skill/tests/unit/test_validate_bootstrap.py shared/scripts/orchestrator/test_validate_bootstrap.py` | `7 failed, 40 passed` — shared tests ran against the Claude validator |
| `pytest shared/scripts/orchestrator/test_validate_bootstrap.py claude/meta-skill/tests/unit/test_validate_bootstrap.py` | `1 error during collection` — `ImportError: cannot import name 'GAME_2D_PRODUCTION_REQUIRED_NODES' from 'validate_bootstrap' (shared/scripts/orchestrator/validate_bootstrap.py)` |
| `pytest claude/meta-skill/tests shared/scripts/orchestrator` | `8 failed, 926 passed` |
| `pytest shared/scripts/orchestrator claude/meta-skill/tests` | `29 errors during collection`, run interrupted |

The 29 collection errors were 27 × `GAME_2D_PRODUCTION_REQUIRED_NODES`, 1 × `plan_confirmation_blockers`
and 1 × `GAME_2D_PRODUCTION_REQUIRED_ARTIFACTS`, all reported against the *shared* file — the Claude
suite importing the shared module by name. Most were collateral: 27 modules reach
`validate_bootstrap` transitively through `test_bootstrap_scope` / `test_freshness_downgrade`.

A second, less obvious contamination path was found while fixing the first: the production modules
import their own siblings **at call time**, not only at module import —
`validate_unattended_readiness:432 from check_artifacts import ...`,
`check_artifacts:271,609,625 from evidence_freshness import ...`. A test that loads a module
correctly can therefore still pull a sibling from whatever directory happens to be on `sys.path`
when the call runs. Any fix that only corrects import-time resolution is incomplete.

## 2. The fix

`shared/scripts/orchestrator/_module_isolation.py` (new) is the single authoritative loader.

- `load(directory, *names)` imports the named modules out of one explicit directory, then removes
  every top-level name that import created and restores whatever was bound before. Modules are
  memoised per `(directory, name)`, so repeated loads in one process hand back the same object and
  classes stay comparable across test modules. Modules that must agree on shared state are requested
  in a single call.
- `bound(directory)` binds that directory's names for one scope. This exists only because of the
  call-time sibling imports above: the window has to be open while the validator's code runs, not
  only while it is first imported.

Two `conftest.py` files open that window per test and close it after, so between tests no bare name
is bound at all:

- `shared/scripts/orchestrator/conftest.py`
- `claude/meta-skill/tests/conftest.py`

`claude/meta-skill/tests/module_isolation.py` (new) binds the plugin's own `scripts/orchestrator`
directory to the shared loader. It does not copy the loader — there is one implementation of the
isolation rule, not one per host. Tests are only ever run from a repo checkout, never from the
installed plugin cache, so the reference across trees is safe.

Every bare same-name import and every `sys.path` mutation in the two scoped suites was replaced:

- `shared/scripts/orchestrator/`: 11 test modules (`test_capture_reverify`, `test_check_decision_inputs`,
  `test_check_requires`, `test_compute_reset_closure`, `test_integration`, `test_loop_detection`,
  `test_superset_tolerance`, `test_validate_audit_outputs`, `test_validate_bootstrap`,
  `test_validate_dag_structure`, `test_verification_honesty`), covering `capture_evidence`,
  `check_decision_inputs`, `check_evidence`, `check_requires`, `compute_completeness`,
  `compute_reset_closure`, `loop_detection`, `reverify`, `validate_audit_outputs`,
  `validate_bootstrap`, `validate_dag_structure` — including two imports written inside test bodies.
- `claude/meta-skill/tests/unit/`: 17 test modules. All 18 `sys.path.insert` call sites in the suite
  are gone (the one remaining `sys.path.insert` string in `test_delivery_closure.py` is source code
  written into a temporary project's own script, not this process's path).
- `test_record_meta_skill_feedback.py` and `test_validate_unattended_readiness.py` also patched their
  targets through a bare module name (`monkeypatch.setattr("record_meta_skill_feedback._run", ...)`,
  `import validate_unattended_readiness as m`). Both now patch the loaded module object. Same
  assertions, same targets.

Nothing about what the tests assert changed; only how they reach the module under test.

## 3. The regression

`shared/scripts/orchestrator/test_module_isolation.py` (new, 9 tests):

- **Ownership** — the shared suite's `validate_bootstrap` is the shared file; every contaminable bare
  name visible during a shared test resolves inside the shared directory.
- **The exact failure** — with the Claude module already bound as `sys.modules["validate_bootstrap"]`,
  a shared load still returns the shared file, and the unrelated pre-existing binding is restored
  rather than rewritten.
- **No residue** — after a foreign binding scope closes, `sys.path` is unchanged, no module name
  leaked, and no contaminable name still resolves into the Claude tree. This is what a later suite
  inherits.
- **Contracts stay distinct** — the two validators are different module objects from different files;
  the portable node spec the shared validator accepts is still refused by the Claude gate; only the
  Claude validator owns `GAME_2D_PRODUCTION_REQUIRED_NODES`. Isolation preserves the divergence
  instead of papering over it, so a future attempt to "fix" a combined run by relaxing either
  contract fails here.
- **Combined collection order** — a subprocess runs the two same-named suites together in both
  orders and requires exit code 0 from each. This is the direct proof that the combined order no
  longer imports the Claude `validate_bootstrap` for shared tests; both of these subprocess runs
  failed before the fix (rows 1 and 2 of the baseline table).

## 4. Verification

Deferred-sibling coverage was raised by the coordinator during this task and matches the second
contamination path found above. Two regressions pin it directly: with the **shared** `check_artifacts`
deliberately bound as `sys.modules["check_artifacts"]`, calling the loaded Claude
`validate_unattended_readiness` inside the scope returns a normal report, and outside the scope the
same call raises `ImportError: cannot import name 'document_verification_errors' from 'check_artifacts'
(shared/scripts/orchestrator/check_artifacts.py)` — the negative control that proves the scope is
load-bearing rather than decorative. Isolation therefore holds for the lifetime of the call, not only
for the initial import.

| Run | Result |
|---|---|
| `pytest shared/scripts/orchestrator` (isolated) | **133 passed** |
| `pytest shared/scripts/orchestrator/test_module_isolation.py` (the new regression) | **11 passed** |
| `pytest claude/meta-skill/tests` (isolated) | 3 failed, **996 passed** |
| `pytest claude/meta-skill/tests shared/scripts/orchestrator` (order A) | 3 failed, **1129 passed** |
| `pytest shared/scripts/orchestrator claude/meta-skill/tests` (order B) | 3 failed, **1129 passed** |

The two collection orders now produce identical results, and the combined result equals the sum of the
isolated ones. That is the property this workstream owed: collection order no longer changes any
verdict.

### Pending, not mine to fix

The three failures are the same three in all three runs — they are not order-dependent and they
appear in the Claude suite on its own:

```
claude/meta-skill/tests/unit/test_repair_authorization.py::test_concurrent_distinct_dispatches_cannot_overspend_a_budget
claude/meta-skill/tests/unit/test_repair_authorization.py::test_concurrent_replays_of_one_dispatch_charge_exactly_once
claude/meta-skill/tests/unit/test_repair_authorization.py::test_concurrent_writers_never_leave_a_partial_entry
```

They fail with `repair_authorization.Refusal: Authorization … does not distinguish started from
settled; whether its execution began is unknown` — in-flight work of the concurrent
repair-authorization workstream (workstream 3), not an import fault. That file already loads its
module through `..module_isolation`. Left untouched and reported as pending.

`test_planning_audit_contracts.py` produced six failures in an earlier combined run whose collected
parametrisation did not match the file on disk; the file was being edited concurrently mid-run. It
passes in all three final runs. No assertion in either concurrently-owned file was changed.

## 5. Surveyed, out of scope

Same-name collisions outside the two suites this task owns. All reproduced, none fixed here; each
would take the same `load()`/`bound()` pattern.

1. **`shared/scripts/` data-transform suites.** `code-replicate/_common.py` and
   `product-design/_common.py` are different modules with one name.
   `pytest shared/scripts/code-replicate shared/scripts/product-design` → `1 error during collection`:
   `ImportError: cannot import name 'load_full_context' from '_common'
   (shared/scripts/code-replicate/_common.py)`. Each suite passes alone.
2. **Mirrored plugin packs.** `claude/grillstorm`, `codex/grillstorm`, `claude/superstorm`,
   `codex/superstorm-skill`, `codex/cross-exam-skill` and `shared/visual-acceptance` are deliberate
   copies, so ~25 module basenames repeat (`build_task_dag`, `host_command`, `model_policy`,
   `artifact_gateway`, `validate_plan_tasks`, `matrix`, `validation`, …). Collecting them together
   gives **38 collection errors**. This is the largest remaining instance and needs a decision on
   whether the mirrors stay duplicated at all before it is worth mechanising.
3. **`docs/grillstorm/meta-intent/replan-2/T15…T18`.** Four copies each of `test_prepare_packets.py`
   and `test_results_pin.py` with no `__init__.py`, so collecting the tree gives **6 collection
   errors** (`import file mismatch`). Individually: T15 23 passed, T16 22 passed, T17 31 passed,
   T18 30 passed / 1 failed (`test_the_reference_candidate_is_never_recorded_as_accepted`,
   pre-existing and unrelated). These are the host-acceptance packet dirs owned by the acceptance
   campaign; adding `__init__.py` per directory would fix collection without touching their content,
   but the directories are under concurrent edit and were left alone.

## 6. Note for workstream 2

The call-time sibling imports are not only a test problem. `validate_unattended_readiness` and
`check_artifacts` resolve `check_artifacts` and `evidence_freshness` by bare name from inside their
own function bodies, so in production they work only when their directory happens to be on
`sys.path` at the moment the call runs — and, in a process where two hosts' trees are both reachable,
they can bind the other host's module. Nothing was changed here; workstream 2 owns whether these
become package-relative imports.

## 7. Files

New:

- `shared/scripts/orchestrator/_module_isolation.py` — the loader (`load`, `bound`, `module_dir`)
- `shared/scripts/orchestrator/conftest.py` — per-test binding scope for the shared suite
- `shared/scripts/orchestrator/test_module_isolation.py` — the 11-test regression
- `claude/meta-skill/tests/module_isolation.py` — binds the plugin's script dir to the shared loader
- `claude/meta-skill/tests/conftest.py` — per-test binding scope for the plugin suite

Changed (import sections and monkeypatch targets only; no assertion, fixture or production change):

- `shared/scripts/orchestrator/`: `test_capture_reverify.py`, `test_check_decision_inputs.py`,
  `test_check_requires.py`, `test_compute_reset_closure.py`, `test_integration.py`,
  `test_loop_detection.py`, `test_superset_tolerance.py`, `test_validate_audit_outputs.py`,
  `test_validate_bootstrap.py`, `test_validate_dag_structure.py`, `test_verification_honesty.py`
- `claude/meta-skill/tests/unit/`: `test_analyze_skill_update_impact.py`, `test_check_artifacts.py`,
  `test_check_artifacts_measurement.py`, `test_expand_game_2d_production.py`,
  `test_freshness_admission_corrections.py`, `test_freshness_downgrade.py`,
  `test_reconcile_bootstrap_workflow.py`, `test_record_meta_skill_feedback.py`, `test_run_logging.py`,
  `test_validate_art_pipeline.py`, `test_validate_bootstrap.py`,
  `test_validate_game_2d_production_pipeline.py`, `test_validate_game_creative_pipeline.py`,
  `test_validate_game_frontend_pipeline.py`, `test_validate_skills.py`,
  `test_validate_specialization_contracts.py`, `test_validate_unattended_readiness.py`
