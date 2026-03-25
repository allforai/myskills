# Code-Replicate Execution Playbook (Codex Native)

Phase-by-phase orchestration for the code-replicate workflow.

## Phase Overview

| Phase | Goal | Key Outputs | Completion Signal |
|-------|------|-------------|-------------------|
| 1 | Preflight | `replicate-config.json`, fragments dirs | Config written, source accessible |
| 2 | Discovery + Confirm | `source-summary.json`, `infrastructure-profile.json`, `stack-mapping.json`, visual captures | User confirmation (last interaction) |
| 3 | Generate | Standard `.allforai/` artifacts (role-profiles, task-inventory, business-flows, etc.) | All extraction-plan artifacts merged |
| 4 | Verify & Handoff | `replicate-report.md`, validated artifacts | Schema valid, 6V audit complete |

All outputs are written to `.allforai/` in the target project.

---

## Pre-flight: Parameter Collection

Determine from user request context:

- **mode**: interface / functional (default) / architecture / exact
- **path**: local path or Git URL (supports HTTPS, SSH, GitHub shorthand, `#branch` suffix)
- **type**: backend / frontend / fullstack / module (auto-detect if not specified)
- **scope**: full / modules / feature

If parameters are missing, assume: mode=functional, type=auto-detect, scope=full.
Only ask the user when the source path is entirely absent (no reasonable default).

For Git URLs, clone to temp directory before proceeding.

---

## Resume Mode

Check `.allforai/code-replicate/replicate-config.json` for `progress` field.
If present, resume from `current_step`. Each completed step is recorded immediately.

- `--from-step 2.5` resumes from Step 2.5, clearing later progress
- `--from-phase 3` resumes from Phase 3, keeping all Phase 2 artifacts

---

## Phase 1: Preflight

**Reference:** `./skills/code-replicate-core.md` (Phase 1 section)

1. Check for existing replicate-config.json (resume detection)
2. Resolve source path (local or git clone)
3. Auto-detect project type if not specified (scan for routes/controllers vs components/pages)
4. Collect missing parameters -- assume defaults where reasonable:
   - Fidelity: functional (most common)
   - Type: auto-detect from codebase
   - Scope: full
   - Target stack: ask only if cross-stack migration
   - Business direction: replicate (default)
   - Source app info: ask if frontend/fullstack (needed for screenshots)
5. Write `replicate-config.json` to `.allforai/code-replicate/`
6. Create fragment directory structure

---

## Phase 2: Discovery + Confirm

Four stages, 15 steps. Move autonomously through each stage.

### Stage A -- Structure Discovery (Steps 2.1-2.4)

**Reference:** `./docs/phase2/stage-a-structure.md`

| Step | Output | Action |
|------|--------|--------|
| 2.1 | discovery-profile.json | LLM reads root directory, generates module discovery rules |
| 2.2 | source-summary.json skeleton | `cr_discover.py` scans files |
| 2.3 | source-summary.json (initial) | LLM reads key_files per module, generates file cards + Quiz verification |
| 2.3.5 | Coverage scan | Head-scan unread files, discover missed components, coverage >= 50% |
| 2.3.7 | file-catalog + code-index | Assemble structured knowledge base from all file cards |
| 2.4 | project_archetype | LLM identifies core value type |

Script: `python3 ../../shared/scripts/code-replicate/cr_discover.py <source_path> <output_path> [--profile <profile_path>]`

### Stage B -- Runtime Discovery (Steps 2.5-2.9)

**Reference:** `./docs/phase2/stage-b-runtime.md`

Steps 2.5-2.9 are independent and can run in parallel for large projects.

| Step | Output | Action |
|------|--------|--------|
| 2.5 | infrastructure-profile.json | Infrastructure inventory (read code behavior, not package names) |
| 2.6 | env-inventory.json | Environment variables from .env + code references |
| 2.7 | third-party-services.json | External service integrations |
| 2.8 | cron-inventory.json | Scheduled tasks (backend/fullstack only) |
| 2.9 | error-catalog.json | Error code system (backend/fullstack only) |

### Stage C -- Resource Discovery (Steps 2.10-2.13)

**Reference:** `./docs/phase2/stage-c-resources.md`

| Step | Output | Action |
|------|--------|--------|
| 2.10 | asset-inventory.json | Frontend assets: copy/transform/replace classification |
| 2.11 | seed-data-inventory.json | Backend seed data + schema extraction |
| 2.12 | abstractions + cross_cutting | Reuse patterns, cross-cutting concerns, architecture style |
| 2.12.5 | role-view-matrix.json | Per-role UI visibility differences (frontend/fullstack) |
| 2.12.8 | interaction-recordings.json | End-to-end business flow chains (frontend/fullstack) |
| 2.13 | visual/source/ | Multi-role screenshots + interaction recordings + API logs |

### Stage D -- Confirm + Mapping (Steps 2.14-2.15)

**Reference:** `./docs/phase2/stage-d-confirm.md`

| Step | Output | Action |
|------|--------|--------|
| 2.14 | User confirmation | Present findings. Assume acceptance unless critical ambiguity |
| 2.15 | stack-mapping.json | Cross-stack mapping (only for cross-stack migration) |

**After Phase 2: no more configuration questions.**

---

## Phase 3: Generate (Silent)

**Reference:** `./skills/code-replicate-core.md` (Phase 3 section), `./docs/phase3/standard-artifact-steps.md`

### Step 3-pre: Extraction Plan

LLM reads source-summary.json and generates `extraction-plan.json` with:
- Source file mappings for roles, tasks, flows, screens, use-cases, constraints
- `artifacts` list: LLM decides what to produce based on project_archetype
- `dependency_map`: module dependencies from code analysis

### Artifact Generation

For each artifact in extraction-plan.artifacts:
1. LLM reads specified source files per module
2. Generates JSON fragment per module
3. **UI closure check**: cross-reference Phase 2.13 screenshots/API logs
4. **4D self-check**: conclusion / evidence / constraints / decisions
5. Merge via script (standard artifacts) or LLM direct output (custom artifacts)

Standard artifact scripts at `../../shared/scripts/code-replicate/`:
- `cr_merge_roles.py`, `cr_merge_screens.py`, `cr_merge_tasks.py`
- `cr_merge_flows.py`, `cr_merge_usecases.py`, `cr_merge_constraints.py`
- `cr_gen_usecase_report.py`, `cr_gen_indexes.py`, `cr_gen_product_map.py`

Generation order (dependency chain): roles > screens > tasks > flows > use-cases > constraints > indexes > product-map

### Context per LLM call
- source-summary.json (~4-8 KB, always loaded)
- code-index.json (~5-10 KB, always loaded)
- file-catalog module slice (~3-8 KB, per extraction-plan module)
- Target schema definition (~2-4 KB, on demand)

---

## Phase 4: Verify & Handoff

**Reference:** `./docs/phase4/verify-handoff.md`

| Step | Action |
|------|--------|
| 4a | `cr_validate.py` schema check + inner-loop fix (max 3 rounds, monotonic decrease) |
| 4b | 6V multi-dimensional audit (user/business/tech/data/ux/risk) |
| 4b.5 | Attention management evaluation (consumer/mixed modes only) |
| 4c | XV cross-validation (optional, requires OPENROUTER_API_KEY) |
| 4d | Outer loop: intent fidelity verification against source-summary (max 1 round, gap <= 20%) |
| 4e | Generate replicate-report.md |
| 4f | Handoff: artifact list + next steps recommendation |

Script: `python3 ../../shared/scripts/code-replicate/cr_validate.py <base_path>`
Script: `python3 ../../shared/scripts/code-replicate/cr_gen_report.py <base_path>`

---

## CR-Fidelity Workflow

**Reference:** `./skills/cr-fidelity.md`, `./docs/fidelity/` directory

| Phase | Action |
|-------|--------|
| 0 | Build traceability index + adaptive dimension selection |
| A | Static analysis: score enabled dimensions (F1-F10, U1-U7, I1-I5, A1-A3, B1-B4) |
| A2 | Runtime verification: build > smoke > test vectors > protocol compat |
| B | Fix gaps (runtime-first priority, max 20 CODE_FIX + 5 ARTIFACT_GAP per round) |
| C | Re-score, convergence control (max 3 rounds, monotonic improvement) |

Modes: `full` = 0>A>A2>B>C loop, `analyze` = 0>A>A2, `fix` = B>C from last report.

---

## CR-Visual Workflow

**Reference:** `./skills/cr-visual.md`

| Step | Action |
|------|--------|
| 1 | Screen list from experience-map + route mapping |
| 2 | Source app screenshots (Phase 2 captures preferred, or live capture) |
| 3 | Target app screenshots (LLM selects automation tool per tech stack) |
| 4 | LLM per-screen structural comparison (not pixel-level) |
| 5 | Report: visual-report.json + visual-report.md |
| 6-7 | Fix loop: repair lowest-score screen > rebuild > re-screenshot > re-compare (target: all screens = high) |

Platform adaptation rules from stack-mapping.json auto-exclude expected cross-platform differences.
