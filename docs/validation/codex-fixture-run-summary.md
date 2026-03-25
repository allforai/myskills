# Codex Fixture Run Summary

Date: 2026-03-26

This file records actual fixture-level validation runs added after the initial Codex document and prompt audit.

## Fixture Set Created

Created under `fixtures/codex/`:

- `minimal-product-map`
- `minimal-experience-chain`
- `minimal-ui-baseline`
- `minimal-project-forge`
- `minimal-runtime-config`
- `minimal-replicate-source`

Design intent:
- generic
- stack-agnostic
- minimal
- reusable across plugins

## Executed Runs

### 1. `minimal-product-map`

Commands executed:
- `python3 codex/code-replicate-skill/scripts/cr_gen_indexes.py fixtures/codex/minimal-product-map`
- `python3 codex/code-replicate-skill/scripts/cr_validate.py fixtures/codex/minimal-product-map`

Result:
- PASS

Observed outputs:
- generated `task-index.json`
- generated `flow-index.json`
- validation returned `valid: true`

Observed validation stats:
- `tasks: 3`
- `roles: 2`
- `flows: 2`
- `task_ref_coverage: 1.0`

Observed warnings:
- missing `constraints.json` is tolerated
- missing `experience-map.json` is tolerated

Interpretation:
- the generic upstream product-map fixture is already compatible with the current Codex `code-replicate` validation scripts
- this is enough to support prerequisite and contract-level checks for downstream consumers such as `dev-forge`

### 2. `minimal-replicate-source`

Commands executed:
- `python3 codex/code-replicate-skill/scripts/cr_gen_product_map.py fixtures/codex/minimal-replicate-source`
- `python3 codex/code-replicate-skill/scripts/cr_gen_indexes.py fixtures/codex/minimal-replicate-source`
- `python3 codex/code-replicate-skill/scripts/cr_validate.py fixtures/codex/minimal-replicate-source --fullstack`

Result:
- PASS

Observed outputs:
- generated `product-map.json`
- generated `task-index.json`
- generated `flow-index.json`
- validation returned `valid: true`

Observed validation stats:
- `tasks: 3`
- `roles: 2`
- `flows: 2`
- `task_ref_coverage: 1.0`

Observed warnings:
- missing `constraints.json` is tolerated
- missing `experience-map.json` is tolerated

Interpretation:
- the generic replicate-source fixture can already complete a minimal `code-replicate` handoff cycle
- the generated product-map side is compatible with the current validator

## Fixtures Created But Not Executed End-to-End Yet

These fixtures now exist, but this repository does not yet provide equally direct local execution paths for them:

- `minimal-experience-chain`
- `minimal-ui-baseline`
- `minimal-project-forge`
- `minimal-runtime-config`

Reason:
- the corresponding Codex plugins currently rely more on workflow docs, runtime orchestration, or human-in-the-loop execution than on standalone local scripts

## What This Changes

Before this pass:
- generic fixtures were only specified in documentation

After this pass:
- generic fixtures exist on disk
- at least two fixture families have been exercised with real commands
- Codex validation now has a reusable lower-level base that is not tied to one business domain or stack

## Remaining Gap

The remaining gap is no longer fixture definition.

The remaining gap is plugin-side executable harness coverage for:
- `dev-forge`
- `demo-forge`
- `code-tuner`
- `ui-forge` beyond asset parsing
- `product-design` beyond its current script test

## Current Verdict

The Codex support retrofit can now be considered:

- document-complete enough for review
- fixture-complete at the generic baseline level
- partially execution-validated

It is still not fully regression-complete across all six plugins.
