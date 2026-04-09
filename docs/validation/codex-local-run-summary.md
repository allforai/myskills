# Codex Local Run Summary

Date: 2026-03-26

This file records what was actually executed in the local workspace during the Codex support validation pass.

Important limitation:
- These are local script/doc checks
- They are not real end-to-end Codex runs against the thought-experiment projects

## Executed Checks

### 0. Codex meta-skill parity surface check

Execution method:
- Run `python3 shared/scripts/orchestrator/check_codex_meta_skill_parity.py`

Result:
- PASS

Observed result:
- `codex/meta-skill` now exposes `SKILL.md`, `.mcp.json`, install script, command wrappers, and bootstrap adapter
- Codex adapter documents `workflow.json` as the canonical bootstrap graph
- generated Codex run entry path is documented as `.codex/commands/run.md`
- no Codex-local adapter files reference `${CLAUDE_PLUGIN_ROOT}`
- Codex bootstrap now wires a generic high-risk specialization hook plus an IM / realtime specialization guide
- specialization guidance follows a research-first rule instead of hardcoded template-first planning

Conclusion:
- `codex/meta-skill` is no longer a placeholder-only surface
- basic contract-level parity checks now have executable evidence
- Codex-only specialization extensions are also mechanically validated

### 0.1 Codex generated-run template smoke

Execution method:
- Run `python3 shared/scripts/orchestrator/smoke_codex_generated_run.py`

Result:
- PASS

Observed result:
- Codex orchestrator template materialized into a temporary target project as `.codex/commands/run.md`
- generated run content references `.allforai/bootstrap/workflow.json`
- generated run content references project-local `check_artifacts.py` and `node-specs/`
- generated run content no longer references `.claude/commands/run.md`
- generated run content no longer references `${CLAUDE_PLUGIN_ROOT}`

Conclusion:
- the Codex-native generated run template is not only documented, but can be rendered into the expected target-project location without leaking Claude-only paths

### 0.2 Codex IM specialization hook check

Execution method:
- Run `python3 shared/scripts/orchestrator/check_codex_im_specialization.py`

Result:
- PASS

Observed result:
- Codex high-risk specialization guidance exists
- Codex IM specialization guidance exists
- the high-risk hook encodes research-first behavior
- IM specialization defines a mandatory responsibility floor
- Codex bootstrap adapter explicitly wires the high-risk hook and IM specialization path

Conclusion:
- the new Codex-only IM specialization extension is not just documented; it is mechanically connected into the bootstrap adapter

### 0.3 Codex product-inference contract check

Execution method:
- Run `python3 shared/scripts/orchestrator/check_product_summary.py /Users/aa/workspace/babylon1/.allforai/bootstrap/product-summary.json`

Result:
- PASS

Observed result:
- `babylon1` bootstrap output now includes `product-summary.json`
- the product summary includes a non-empty `product_shape`
- the product summary includes 7 evidence entries and 8 core systems
- confidence is recorded and valid

Conclusion:
- reverse-product inference is now represented as a concrete bootstrap artifact, not just an analysis pattern
- Codex can emit and validate an evidence-backed product summary on a real target project

### 1. Code-Replicate script test suite

Execution method:
- Run each `codex/code-replicate-skill/scripts/test_*.py` file directly with `python3`

Result:
- PASS

Files covered:
- `test_common.py`
- `test_cr_discover.py`
- `test_cr_gen_indexes.py`
- `test_cr_gen_product_map.py`
- `test_cr_gen_report.py`
- `test_cr_gen_usecase_report.py`
- `test_cr_merge_constraints.py`
- `test_cr_merge_flows.py`
- `test_cr_merge_roles.py`
- `test_cr_merge_screens.py`
- `test_cr_merge_tasks.py`
- `test_cr_merge_usecases.py`
- `test_cr_validate.py`
- `test_e2e.py`
- `test_new_functions.py`

Observed result:
- All direct script test runs completed with `OK`
- Warnings printed by some tests were non-fatal and expected by the test scenarios

Conclusion:
- `code-replicate` currently has the strongest local executable validation coverage in the Codex tree

### 2. Product-Design full-context script test

Execution method:
- Run `codex/product-design-skill/scripts/test_full_context.py` directly with `python3`

Result:
- PASS

Observed result:
- `Ran 6 tests`
- `OK`

Conclusion:
- `product-design` has at least one working local script-level validation path

### 3. UI-Forge eval asset structure check

Execution method:
- Parse `codex/ui-forge-skill/evals/evals.json`

Result:
- PASS

Observed result:
- JSON parsed successfully
- Top-level keys present: `skill_name`, `evals`

Conclusion:
- `ui-forge` has at least one structured evaluation asset present and parseable

### 4. Core entry-point existence check

Execution method:
- Verify existence of:
  - all 6 plugin `AGENTS.md`
  - all 5 Codex test prompts

Result:
- PASS

Conclusion:
- The Codex plugin entry-point set and current thought-experiment prompt set are complete at the file level

### 5. Generic fixture validation runs

Execution method:
- Create `fixtures/codex/` generic minimal fixtures
- Run `code-replicate` generators and validator against:
  - `fixtures/codex/minimal-product-map`
  - `fixtures/codex/minimal-replicate-source`

Result:
- PASS

Observed result:
- `minimal-product-map` generated `task-index.json` and `flow-index.json`
- `minimal-product-map` validated successfully
- `minimal-replicate-source` generated `product-map.json`, `task-index.json`, and `flow-index.json`
- `minimal-replicate-source` validated successfully with `--fullstack`

Conclusion:
- Generic, stack-agnostic fixtures now exist on disk and are not just planned
- `code-replicate` has real compatibility evidence against reusable fixture inputs

## Blockers Encountered

### Missing `pytest`

Attempted:
- `python3 -m pytest ...`

Result:
- FAIL due to environment

Error:
- `No module named pytest`

Impact:
- Could not use the repository's pytest-oriented execution flow directly
- Worked around this for script-based tests by executing test files directly with `python3`

## Overall Execution Assessment

Actually executed and passed:
- `code-replicate` script tests
- `product-design` full-context test
- `ui-forge` eval JSON parse
- file-level existence checks for all plugin entry points and prompts
- generic fixture runs for `minimal-product-map` and `minimal-replicate-source`

Not actually executed yet:
- `dev-forge` end-to-end flow
- `demo-forge` runtime flow
- `code-tuner` analysis scenario
- real Codex runs for any of the 5 thought-experiment projects

## Best Supported by Actual Local Execution Evidence

1. `code-replicate`
2. `product-design` (partial script coverage only)
3. `ui-forge` (asset-level check only)

## Next Real Execution Targets

1. `codex-test-project3-replication.md`
2. `codex-test-project2-teampulse.md` (`code-tuner` section first)
3. `codex-test-project5-markethub-demo.md`
