# Codex Test Prompts Audit

Date: 2026-03-26

Scope:
- `docs/test-prompts/codex-test-project1-fresheats.md`
- `docs/test-prompts/codex-test-project2-teampulse.md`
- `docs/test-prompts/codex-test-project3-replication.md`
- `docs/test-prompts/codex-test-project4-pulsecrm-ui.md`
- `docs/test-prompts/codex-test-project5-markethub-demo.md`

Method:
- Read each test prompt
- Cross-check against current `codex/` plugin entry points and execution playbooks
- Validate whether the requested phases, artifacts, and quality gates are consistent with the current Codex-native implementation
- Fix prompt definitions when they were clearly out of sync with implementation

Important limitation:
- This audit validates prompt-to-implementation consistency
- It does not execute Codex itself in this environment

## Summary

| Prompt | Status | Assessment |
|-------|--------|------------|
| Project 1: FreshEats | PASS with caveats | Prompt now matches the current product-design pipeline and a partial dev-forge smoke scope |
| Project 2: TeamPulse | PASS with caveats | Prompt now includes the required product-map bootstrap before dev-forge |
| Project 3: Replication | PASS | Prompt matches current code-replicate flow and uses range-based assertions |
| Project 4: PulseCRM UI Restore | PASS | Prompt matches current ui-forge positioning and execution playbook |
| Project 5: MarketHub Demo Forge | PASS | Prompt matches current demo-forge prerequisites, iteration model, and artifact contracts |

## What Was Fixed

### 1. FreshEats

Files:
- [codex-test-project1-fresheats.md](/Users/aa/allforai/myskills/docs/test-prompts/codex-test-project1-fresheats.md)

Fixes applied:
- Removed the non-existent `feature-prune` requirement from the Codex product-design expectation
- Aligned the pipeline with the current `concept-baseline` and `Stitch decision point` phases
- Replaced outdated expected outputs with current ones:
  - `gap-tasks.json`
  - `ui-design-spec.json`
  - `tokens.json`
- Reframed `project-forge` as a partial smoke test instead of a full completion test

Current assessment:
- Usable as a scenario prompt
- Not a full end-to-end acceptance test for complete dev-forge completion

### 2. TeamPulse

Files:
- [codex-test-project2-teampulse.md](/Users/aa/allforai/myskills/docs/test-prompts/codex-test-project2-teampulse.md)

Fixes applied:
- Added the minimal `.allforai/product-map/` bootstrap required by current `dev-forge`
- Kept code-tuner as a simulated scenario test with approximate scoring
- Adjusted expected file count to reflect the added bootstrap artifacts

Current assessment:
- Usable for thought-experiment smoke validation
- `code-tuner` remains the more reliable half of this prompt

### 3. Replication

Files:
- [codex-test-project3-replication.md](/Users/aa/allforai/myskills/docs/test-prompts/codex-test-project3-replication.md)

Fixes applied:
- Replaced exact artifact counts with lower-bound assertions:
  - at least 8 tasks
  - at least 10 use cases
  - at least 12 downstream tasks
- Kept the flow aligned with discovery-driven reverse engineering

Current assessment:
- Best candidate for the first real Codex smoke run

### 4. PulseCRM UI Restore

Files:
- [codex-test-project4-pulsecrm-ui.md](/Users/aa/allforai/myskills/docs/test-prompts/codex-test-project4-pulsecrm-ui.md)

Fixes applied:
- Added a dedicated prompt for `ui-forge`
- Bound the scenario to post-implementation refinement only
- Aligned expected triage/output with `ui-forge` execution playbook

Current assessment:
- Good prompt for validating positioning, mode routing, and guardrails

### 5. MarketHub Demo Forge

Files:
- [codex-test-project5-markethub-demo.md](/Users/aa/allforai/myskills/docs/test-prompts/codex-test-project5-markethub-demo.md)

Fixes applied:
- Added a dedicated prompt for `demo-forge`
- Aligned the scenario with current prerequisites and runtime assumptions
- Matched expected artifacts to current `demo-forge` output contract
- Kept assertions shape-based rather than overly deterministic

Current assessment:
- Good prompt for validating runtime assumptions, degradation chains, and iterative verification

## Practical Recommendation

For the first real Codex smoke sequence, use this order:

1. `codex-test-project3-replication.md`
2. `codex-test-project2-teampulse.md` (`code-tuner` section first)
3. `codex-test-project5-markethub-demo.md`
4. `codex-test-project4-pulsecrm-ui.md`
5. `codex-test-project1-fresheats.md`
