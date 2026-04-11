# Code Replicate — Execution Playbook

> OpenCode orchestration guide for the 4-phase code replication pipeline.

---

## Phase Table

| Phase | Goal | Key Outputs | Completion Signal |
|-------|------|-------------|-------------------|
| 1 — Preflight | Collect parameters, clone source | `replicate-config.json`, `acceptance-ceiling.json`, fragments directory structure | Config written, **user confirmed fidelity ceiling** |
| 2 — Discovery + Confirm | Scan source, build knowledge base, user confirms | `source-summary.json`, `discovery-profile.json`, `infrastructure-profile.json`, `file-catalog.json`, `code-index.json`, `stack-mapping.json` | User confirmation received (last interaction) |
| 2.5 — Contract Extraction | Extract acceptance contracts from source | `acceptance-contracts.json` | All backend + UI contracts extracted |
| 3 — Generate + Reverse-Check | Extract artifacts per extraction-plan, diff against contracts | Standard `.allforai/` artifacts, `known_gaps.json` | All units pass diff or marked as known_gap |
| 4 — Verify & Handoff | Validate, audit, report | `replicate-report.md`, validated artifacts, gap pattern analysis | Schema valid, 6V audit + gap report complete |

---

## Artifact Detection for Resume Mode

Check `.allforai/code-replicate/replicate-config.json` for `progress` field:

```
progress.current_phase = 1 → Start from Phase 1
progress.current_phase = 2 → Resume Phase 2 from current_step
progress.current_phase = 3 → Resume Phase 3 from current artifact
progress.current_phase = 4 → Resume Phase 4
```

Key artifacts to check for resume:
- `replicate-config.json` exists → Phase 1 complete
- `source-summary.json` exists → Phase 2 Stage A complete
- `infrastructure-profile.json` exists → Phase 2 Stage B complete
- `file-catalog.json` exists → Phase 2.3.7 complete
- `stack-mapping.json` exists → Phase 2 complete
- `extraction-plan.json` exists → Phase 3-pre complete
- Standard artifacts in `product-map/` → Phase 3 steps complete
- `replicate-report.md` exists → Phase 4 complete

---

## Phase Transition Logic

### Phase 1 -> Phase 2

Automatic. No confirmation needed between phases.

Required state: `replicate-config.json` written with source_path, fidelity, project_type, scope, target_stack, business_direction.

### Phase 2 Stages (A -> B -> C -> D)

Automatic between stages. Stage B steps (2.5-2.9) can run in parallel for large projects.

- Stage A (2.1-2.4): Structure discovery — sequential
- Stage B (2.5-2.9): Runtime foundation — parallelizable
- Stage C (2.10-2.13): Resources — sequential (2.12.8 depends on earlier steps)
- Stage D (2.14-2.15): Confirm + mapping — sequential, **last user interaction**

### Phase 2 -> Phase 3

Automatic after user confirmation in 2.14.

Required state: source-summary, infrastructure-profile, file-catalog, code-index all exist. stack-mapping exists if cross-stack.

### Phase 3 -> Phase 4

Automatic after all artifacts generated and merged.

### Phase 4 Internal Loops

- Step 4a: Inner loop — max 3 rounds, monotonic error decrease
- Step 4d: Outer loop — max 1 round, gap additions <= 20% of total items

---

## Phase 3: Generate + Reverse-Check (Silent)

### Artifact Generation

For each artifact in extraction-plan.artifacts:
1. Load acceptance contracts for this module from `acceptance-contracts.json`
2. LLM reads specified source files per module
3. Generates JSON fragment per module
4. **UI closure check**: cross-reference Phase 2.13 screenshots/API logs
5. **4D self-check**: conclusion / evidence / constraints / decisions
6. **Reverse contract extraction**: extract contracts B from generated fragment
7. **Diff(A, B)**: compare extracted contracts B against source contracts A
   - Empty diff → pass, proceed to merge
   - Non-empty diff → fix → re-extract → max 3 rounds → mark as `known_gap` with full diff
8. Merge via script (standard artifacts) or LLM direct output (custom artifacts)

---

## Orchestration Rules

1. **Do not confirm between phases** — flow automatically from Phase 1 through Phase 4
2. **Only two user interaction points**: Phase 1 (parameter collection) and Phase 2.14 (discovery confirmation)
3. **After Phase 2.14, no more configuration questions** — everything runs silently
4. **Update progress after each step** — write to `replicate-config.json` for crash recovery
5. **Output progress indicators** — show phase/stage/step progress to user

## Parameter Collection (Phase 1)

When the user's request is missing required parameters, ask naturally in a single consolidated question. Required parameters:

1. **Source path** — local path or Git URL
2. **Fidelity level** — interface / functional / architecture / exact
3. **Project type** — backend / frontend / fullstack / auto-detect (default)
4. **Target stack** — same stack or specify target
5. **Business direction** — replicate / slim / extend

Only ask for parameters that cannot be inferred from the user's message.

### Step 1.2: Runability Assessment (Gate)

Before any analysis begins, evaluate whether source and target environments can run. Output `acceptance-ceiling.json` and present fidelity ceiling to user.

**Detection steps:**
1. Attempt source build: run build command (package.json scripts.build / go build / flutter build)
2. Check target env: target language runtime, framework CLI, database availability
3. Compute fidelity ceiling:

| Condition | UI Verification Capability | Fidelity Ceiling |
|-----------|---------------------------|-----------------|
| Source + target both runnable, screenshots available | Full runtime verification | ~100% |
| Runnable, no screenshot environment | Structural verification only | ~70% |
| Source or target cannot run | Static contract diff only | ~40% |

4. Write `acceptance-ceiling.json` to `.allforai/code-replicate/`
5. Present ceiling and `known_gaps` list to user
6. **Wait for explicit user confirmation before proceeding.** Stop if user declines.

```json
{
  "source_runnable": true,
  "source_build_cmd": "npm run build",
  "target_env_ready": false,
  "target_missing": ["Node.js 18+", "PostgreSQL"],
  "screenshot_available": false,
  "fidelity_ceiling": 0.7,
  "known_gaps": ["runtime UI verification", "visual diff against running target"],
  "user_confirmed": false,
  "confirmed_at": null
}
```

## Phase 2.5: Contract Extraction

**Reference:** `./docs/phase2/stage-e-contracts.md`

Runs immediately after Phase 2 Stage D confirm. Extracts acceptance contracts from source code — the oracle used by Phase 3 reverse-check.

| Step | Output | Action |
|------|--------|--------|
| 2.5.0 | dead_code_candidates.json | Entry point reachability scan: mark reachable / suspect_dead / unknown, filter dead code |
| 2.5.1 | backend_contracts[] | Per-endpoint: inputs, outputs, error conditions, side effects, cross-module rules (reachable only) |
| 2.5.2 | ui_contracts[] | Per-screen: states, user_actions (with preconditions), transitions, intent (reachable only) |
| 2.5.3 | acceptance-contracts.json | Merge and write; show dead code candidates to user for confirmation |

**Extraction principle: extract intent, not implementation.** Intent does not change when the stack changes; component code changes completely.
Cross-module implicit rules scattered across files must be consolidated into explicit contract items here.

Output: `.allforai/code-replicate/acceptance-contracts.json`

---

## Script Paths

All scripts are at `../../shared/scripts/code-replicate/`:

```bash
# Phase 2: Discovery
python3 ../../shared/scripts/code-replicate/cr_discover.py <source_path> <output_path> [--profile <profile_path>]

# Phase 3: Merge scripts
python3 ../../shared/scripts/code-replicate/cr_merge_roles.py <base_path> <fragments_dir>
python3 ../../shared/scripts/code-replicate/cr_merge_screens.py <base_path> <fragments_dir>
python3 ../../shared/scripts/code-replicate/cr_merge_tasks.py <base_path> <fragments_dir>
python3 ../../shared/scripts/code-replicate/cr_merge_flows.py <base_path> <fragments_dir>
python3 ../../shared/scripts/code-replicate/cr_merge_usecases.py <base_path> <fragments_dir>
python3 ../../shared/scripts/code-replicate/cr_merge_constraints.py <base_path> <fragments_dir>

# Phase 3: Generation scripts
python3 ../../shared/scripts/code-replicate/cr_gen_usecase_report.py <base_path>
python3 ../../shared/scripts/code-replicate/cr_gen_indexes.py <base_path>
python3 ../../shared/scripts/code-replicate/cr_gen_product_map.py <base_path>

# Phase 4: Validation & Report
python3 ../../shared/scripts/code-replicate/cr_validate.py <base_path>
python3 ../../shared/scripts/code-replicate/cr_gen_report.py <base_path>
```
