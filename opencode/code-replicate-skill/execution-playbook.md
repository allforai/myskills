# Code Replicate — Execution Playbook

> OpenCode orchestration guide for the 4-phase code replication pipeline.

---

## Phase Table

| Phase | Goal | Key Outputs | Completion Signal |
|-------|------|-------------|-------------------|
| 1 — Preflight | Collect parameters, clone source | `replicate-config.json`, fragments directory structure | Config written with all parameters |
| 2 — Discovery + Confirm | Scan source, build knowledge base, user confirms | `source-summary.json`, `discovery-profile.json`, `infrastructure-profile.json`, `file-catalog.json`, `code-index.json`, `stack-mapping.json` | User confirmation received (last interaction) |
| 3 — Generate | Extract artifacts per extraction-plan | Standard `.allforai/` artifacts (task-inventory, role-profiles, business-flows, use-case-tree, experience-map, etc.) | All artifacts merged and written |
| 4 — Verify & Handoff | Validate, audit, report | `replicate-report.md`, validated artifacts | Report generated, handoff complete |

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
