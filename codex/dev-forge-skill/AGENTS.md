# Dev Forge — Agent Layer (AGENTS.md)

> Layer 0 entry point for Codex-native orchestration.
> Maps workflows to skill files, doc references, and artifact existence checks.

## Prerequisites

All workflows require `.allforai/product-map/product-map.json` to exist.
Run the product-design pipeline first if this artifact is missing.

---

## Workflows

### project-forge full

Full pipeline for new projects: spike → setup → spec → execute → verify → demo-handoff → report.

**Entry**: `./commands/project-forge.md`
**Phases**: See `./execution-playbook.md` for the 8-phase pipeline.
**Completion**: `.allforai/project-forge/forge-report.md` exists.

### project-forge existing

Same pipeline as `full`, but Phase 2 runs in existing mode (scans code for gaps).

**Entry**: `./commands/project-forge.md`
**Completion**: `.allforai/project-forge/forge-report.md` exists.

### project-forge resume

Resume from the last completed phase. Detects phase status from `forge-decisions.json`.

**Entry**: `./commands/project-forge.md`
**Detection**: Check `forge-decisions.json` → `phase_status` for first non-completed phase.

---

### design-to-spec

Convert product-design artifacts into per-sub-project requirements + design + tasks.

**Entry**: `./skills/design-to-spec.md`
**Prerequisites**: `.allforai/project-forge/project-manifest.json` exists.
**Completion**: Each sub-project directory has `requirements.md` + `design.md` + `tasks.md`.
**Parallel dispatch**: Backend-first (Phase A), then frontend sub-projects in parallel (Phase B).
**Role docs**:
- Architect: `./docs/design-to-spec/architect-steps.md`
- Decomposer: `./docs/design-to-spec/decomposer-steps.md`
- Auditor-Validate: `./docs/design-to-spec/auditor-validate.md`
- Auditor-Enrich: `./docs/design-to-spec/auditor-enrich.md`
- Enricher: `./docs/design-to-spec/enricher-steps.md`
- Batch structure: `./docs/execution-batches.md`

---

### task-execute

Systematically execute atomic tasks from tasks.md with progress tracking.

**Entry**: `./skills/task-execute.md`
**Prerequisites**: Sub-project `tasks.md` files + `project-manifest.json` exist.
**Completion**: `.allforai/project-forge/build-log.json` exists with CORE tasks completed.
**Progress tracking**: Check `.allforai/project-forge/build-log.json` and per-sub-project `build-log-{name}.json`.
**Quality docs**: `./docs/test-quality-review.md`

---

### testforge

Test-driven quality forging: audit + generate + fix loop across the full test pyramid.

**Entry**: `./commands/testforge.md`
**Modes**: `full` | `analyze` | `fix`
**Completion**: `.allforai/testforge/testforge-report.md` exists.
**Phase docs**:
- Phase 0: `./docs/testforge/phase0-profile.md`
- Phase 1: `./docs/testforge/phase1-vertical-audit.md`
- Phase 4: `./docs/testforge/phase4-forge-loop.md`
- Phase 6: `./docs/testforge/phase6-report.md`
- Iron rules: `./docs/testforge/iron-rules.md`

---

### deadhunt static

Static-only dead link hunting + CRUD completeness check.

**Entry**: `./commands/deadhunt.md` (mode: `static`)
**Completion**: `.allforai/deadhunt/output/validation-report-summary.md` exists.
**Phase docs**:
- Phase 0: `./docs/deadhunt/phase0-analyze.md`
- Phase 1: `./docs/deadhunt/phase1-static.md`
- Phase 4: `./docs/deadhunt/phase4-report.md`

### deadhunt deep

Deep testing only (requires Playwright or Patrol).

**Entry**: `./commands/deadhunt.md` (mode: `deep`)
**Prerequisites**: Playwright browser automation available.
**Phase docs**: `./docs/deadhunt/phase3-test.md` and sub-files in `./docs/deadhunt/phase3/`.

### deadhunt full

Complete validation: static + deep + supplement tests.

**Entry**: `./commands/deadhunt.md` (mode: `full`)
**Phase docs**: All deadhunt docs including `./docs/deadhunt/phase5-supplement-test.md`.

### deadhunt incremental

Incremental validation: only modules touched by recent git changes.

**Entry**: `./commands/deadhunt.md` (mode: `incremental`)

---

### fieldcheck full

Full 4-layer field consistency check: L1(UI) <-> L2(API) <-> L3(Entity) <-> L4(DB).

**Entry**: `./commands/fieldcheck.md` (scope: `full`)
**Completion**: `.allforai/deadhunt/output/field-analysis/field-report.md` exists.
**Detail docs**:
- Overview: `./docs/deadhunt/fieldcheck/overview.md`
- Extractors: `./docs/deadhunt/fieldcheck/extractors.md`
- Matching: `./docs/deadhunt/fieldcheck/matching.md`
- Report: `./docs/deadhunt/fieldcheck/report.md`

### fieldcheck frontend

Frontend only: L1(UI) <-> L2(API).

**Entry**: `./commands/fieldcheck.md` (scope: `frontend`)

### fieldcheck backend

Backend only: L2(API) <-> L3(Entity) <-> L4(DB).

**Entry**: `./commands/fieldcheck.md` (scope: `backend`)

### fieldcheck endtoend

End-to-end: L1(UI) <-> L4(DB).

**Entry**: `./commands/fieldcheck.md` (scope: `endtoend`)

---

### seed-forge

Generate development seed data. Documented in SKILL.md under seed-forge section.

---

### product-verify

Static + dynamic product acceptance against the product map.

**Entry**: `./skills/product-verify.md`
**Modes**: `static` | `dynamic` | `full` | `refresh` | `scope`
**Completion**: `.allforai/product-verify/verify-report.md` exists.
**Prerequisites**: `.allforai/product-map/product-map.json` exists.

---

## Artifact Existence Checks

The following artifact checks replace Task-based progress tracking:

| Artifact | Indicates |
|----------|-----------|
| `.allforai/product-map/product-map.json` | product-design completed |
| `.allforai/project-forge/project-manifest.json` | project-setup completed |
| `.allforai/project-forge/forge-decisions.json` | Phase 0/1 decisions recorded |
| `.allforai/project-forge/sub-projects/*/tasks.md` | design-to-spec completed |
| `.allforai/project-forge/shared-utilities-plan.json` | shared utilities analysis done |
| `.allforai/project-forge/build-log.json` | task-execute started/completed |
| `.allforai/product-verify/verify-report.md` | product-verify completed |
| `.allforai/deadhunt/output/validation-report-summary.md` | deadhunt completed |
| `.allforai/deadhunt/output/field-analysis/field-report.md` | fieldcheck completed |
| `.allforai/testforge/testforge-report.md` | testforge completed |
| `.allforai/demo-forge/demo-plan.json` | demo-forge design completed |
| `.allforai/project-forge/forge-report.md` | full pipeline completed |

---

## Doc Reference Map

| Doc Path | Used By |
|----------|---------|
| `./docs/skill-commons.md` | All skills (shared enhancement protocols) |
| `./docs/execution-batches.md` | design-to-spec (batch structure + parallel dispatch) |
| `./docs/primitive-impl-map.md` | design-to-spec (behavior primitive implementation) |
| `./docs/test-quality-review.md` | task-execute (B5 test quality audit) |
| `./docs/field-specs/image-field.md` | design-to-spec (image field spec) |
| `./docs/field-specs/video-field.md` | design-to-spec (video field spec) |
| `./docs/design-to-spec/*.md` | design-to-spec (role-specific steps) |
| `./docs/deadhunt/*.md` | deadhunt (phase-specific docs) |
| `./docs/deadhunt/fieldcheck/*.md` | fieldcheck (layer-specific docs) |
| `./docs/testforge/*.md` | testforge (phase-specific docs) |
