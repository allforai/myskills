# Code-Tuner Execution Playbook (Codex Native)

Phase-by-phase orchestration for the code-tuner workflow.

## Phase Overview

| Phase | Goal | Outputs | Completion Signal |
|-------|------|---------|-------------------|
| 0 | Project profile | `tuner-profile.json`, `tuner-decisions.json` | Profile confirmed (or inferred) |
| 1 | Architecture compliance | `phase1-compliance.json` | All rules checked, violations recorded |
| 2 | Duplication detection | `phase2-duplicates.json` | All four layers scanned |
| 3 | Abstraction analysis | `phase3-abstractions.json` | Five analysis dimensions complete |
| 4 | Report + scoring | `tuner-report.md`, `tuner-tasks.json` | Scores computed, report written |

All outputs are written to `.allforai/code-tuner/` in the target project.

---

## Pre-flight: Project Type Validation

Before any phase, confirm the target is a backend-capable repository by scanning
for at least one server-side config file:

- `pom.xml`, `build.gradle`, `build.gradle.kts` (Java)
- `go.mod` (Go)
- `package.json` with backend framework deps (Node.js)
- `requirements.txt`, `pyproject.toml`, `setup.py`, `manage.py` (Python)
- `*.csproj`, `*.sln` (.NET)
- `Cargo.toml` (Rust)
- `composer.json` (PHP)
- `Gemfile` (Ruby)

If none found, inform the user and stop. Do not force-analyze non-backend projects.

---

## Mode Routing

Determine mode from user request context:

- No specific mode or "full" -> Phase 0 > 1 > 2 > 3 > 4
- "compliance" -> Phase 0 > 1 > 4
- "duplication" -> Phase 0 > 2 > 4
- "abstraction" -> Phase 0 > 3 > 4
- "report" -> Phase 4 only (from existing artifacts)

Determine lifecycle from user context:

- Default: `pre-launch` (aggressive optimization)
- If user mentions maintenance, production, or live system: `maintenance` (conservative)
- If unclear, assume `pre-launch`

---

## Phase 0: Project Profile

**Reference:** `./references/phase0-profile.md` and `./references/layer-mapping.md`

**Objectives:**

1. Detect tech stack (language, framework, build tool)
2. Infer architecture type (three-tier / two-tier / DDD / mixed)
3. Map actual directories to logical layers (Entry / Business / Data / Utility)
4. Identify business modules
5. Scan data model (entities, relationships, DTO/VO distribution)
6. Assess project scale (files, lines, modules, entities)

**Upstream consumption chain (check in order):**

1. `.allforai/code-tuner/tuner-profile.json` (own cache)
2. `.allforai/project-forge/project-manifest.json` (from project-setup)
3. `.allforai/project-forge/forge-decisions.json` (from project-setup)
4. Auto-detection (scan code)
5. Ask user only when architecture type cannot be reliably inferred

**Output:** `.allforai/code-tuner/tuner-profile.json`

**Decision logging:** Record confirmed decisions in `.allforai/code-tuner/tuner-decisions.json`.

**Completion:** Profile assembled with all required fields. Confirm with user only
if architecture type is ambiguous (mixed) or auto-detection confidence is low.
For clear-cut cases (obvious three-tier Spring Boot, standard Go Gin layout, etc.),
declare the assumption and proceed.

---

## Phase 1: Architecture Compliance

**Reference:** `./references/phase1-compliance.md`

**Objectives:**

1. Load rules for the detected architecture type
2. Check dependency direction between layers
3. Check layer responsibility violations
4. Check validation placement (format in Entry, business in Business, none in Data)
5. Flag violations by rule ID with severity

**Rule categories:**
- T-01 to T-06: three-tier rules
- W-01 to W-03: two-tier rules
- D-01 to D-04: DDD rules
- G-01 to G-06: universal rules (all architectures)

**Output:** `.allforai/code-tuner/phase1-compliance.json`

**Completion:** All applicable rules evaluated, violations array populated, summary counts computed.

---

## Phase 2: Duplication Detection

**Reference:** `./references/phase2-duplicates.md`

**Objectives:**

1. Scan Entry layer for repeated API patterns (export, pagination, CRUD endpoints)
2. Scan Business layer for similar service methods and passthrough detection
3. Scan Data layer for similar queries and DTO/VO field overlap (Jaccard > 70%)
4. Scan Utility layer for duplicate tool classes

**Method:** Extract structural signatures (param types > operation sequence > return type),
compare via edit distance. Threshold: 70% similarity.

**Output:** `.allforai/code-tuner/phase2-duplicates.json`

**Completion:** All four layers scanned, duplicate pairs and passthrough services recorded.

---

## Phase 3: Abstraction Analysis

**Reference:** `./references/phase3-abstractions.md`

**Objectives:**

1. Vertical abstraction: find classes with > 60% structural overlap for base class extraction
2. Horizontal abstraction: find code fragments repeated across >= 3 files
3. Interface consolidation: find similar APIs differing only by entity type
4. Validation logic: check placement, duplication, consistency
5. Over-abstraction detection: single-implementation interfaces, single-call utilities, deep passthrough chains

**Output:** `.allforai/code-tuner/phase3-abstractions.json`

**Completion:** All five dimensions analyzed, opportunities and anti-patterns recorded.

---

## Phase 4: Report + Scoring

**Reference:** `./references/phase4-report.md`

**Objectives:**

1. Compute five-dimension scores (deduction-based, each 0-100):
   - Architecture compliance (25%)
   - Code duplication (25%)
   - Abstraction quality (20%)
   - Validation standards (15%)
   - Data model quality (15%)
2. Generate weighted total score
3. Produce `tuner-report.md` with summary, problem list, heatmap, detailed findings
4. Produce `tuner-tasks.json` with prioritized refactoring tasks
5. If previous report exists, include trend comparison

**Output:** `.allforai/code-tuner/tuner-report.md` and `.allforai/code-tuner/tuner-tasks.json`

**Completion:** Report written. Present a summary in the conversation including:
total score, per-dimension scores, all Critical issues, top Warning issues,
and the top-3 priority tasks.

---

## Orchestration Rules

1. **Move phase-to-phase without user confirmation.** Only pause to ask when a
   missing answer would materially corrupt the next phase (e.g., architecture type
   is genuinely ambiguous).
2. **Resume mode:** If phase output files already exist in `.allforai/code-tuner/`,
   skip completed phases. For report mode, read existing phase JSONs directly.
3. **Keep analysis read-only.** Never modify project source code. Only write to
   `.allforai/code-tuner/`.
4. **Dual-mode suggestions.** Every finding must include both `pre-launch` and
   `maintenance` recommendations.

## Final Response Contract

After analysis, provide:

- The selected mode and lifecycle
- A concise score summary table
- The highest-severity findings with file paths
- The location of generated report artifacts

If no findings are discovered, state that explicitly and note any coverage gaps.
