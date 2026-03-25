---
description: "Server-side code quality analysis: architecture compliance, duplication detection, abstraction analysis, validation discipline. Modes: full / compliance / duplication / abstraction / report"
---

# Code-Tuner — Server-Side Code Quality Analysis

## Mode Detection

Determine the workflow mode from the user's natural language:

- **No specific request or "full"** → full analysis: Phase 0 → 1 → 2 → 3 → 4
- **"compliance" or "architecture check"** → compliance only: Phase 0 → 1 → 4
- **"duplication" or "find duplicates"** → duplication only: Phase 0 → 2 → 4
- **"abstraction" or "refactor opportunities"** → abstraction only: Phase 0 → 3 → 4
- **"report" or "regenerate report"** → report only: read existing phase outputs, regenerate Phase 4

## Lifecycle Detection

Parse lifecycle from user language:

- **pre-launch (default)** → aggressive optimization suggestions
- **maintenance** → conservative optimization suggestions

If the user does not specify, default to pre-launch.

## Pre-flight Check: Project Type Validation (mandatory)

Before any analysis, verify the target is a server-side code project.

Scan the project root for backend tech stack config files:
- `pom.xml`, `build.gradle`, `build.gradle.kts` (Java)
- `go.mod` (Go)
- `package.json` with backend framework dependencies (Node.js)
- `requirements.txt`, `pyproject.toml`, `setup.py`, `manage.py` (Python)
- `*.csproj`, `*.sln` (.NET)
- `Cargo.toml` (Rust)
- `composer.json` (PHP)
- `Gemfile` (Ruby)

If none found, inform the user and terminate. Do not force analysis on non-backend projects.

## Execution Flow

1. **Run pre-flight check** (see above) -- terminate if not a backend project
2. Read the file at `./SKILL.md` for the complete workflow overview and key principles
3. Read the file at `./execution-playbook.md` for orchestration rules and resume handling
4. Load phase-specific reference docs as needed during execution
5. Execute phases according to the selected mode
6. **Display the full report summary in the conversation** (see report output requirements below)

## Reference Documents (load as needed)

- `./SKILL.md` -- workflow overview, key principles, file structure
- `./execution-playbook.md` -- orchestration rules, phase transitions, resume logic
- `./references/phase0-profile.md` -- Phase 0: project profile detection rules
- `./references/phase1-compliance.md` -- Phase 1: architecture compliance rules
- `./references/phase2-duplicates.md` -- Phase 2: duplication detection methods
- `./references/phase3-abstractions.md` -- Phase 3: abstraction opportunity analysis
- `./references/phase4-report.md` -- Phase 4: scoring formulas and report template
- `./references/layer-mapping.md` -- cross-language layer mapping reference

## Phase 0 Execution

Phase 0 is mandatory for all modes. Use the upstream consumption chain to gather profile information -- adopt decisions already available from upstream sources, only ask the user for missing or conflicting items:

### Upstream Consumption Chain

```
Priority 1: .allforai/code-tuner/tuner-profile.json (own cache)
    ↓ not found or stale
Priority 2: .allforai/project-forge/project-manifest.json (project-setup output)
    ↓ not found
Priority 3: .allforai/project-forge/forge-decisions.json (project-setup decisions)
    ↓ not found
Priority 4: Auto-detect (scan code to infer)
    ↓ cannot infer
Priority 5: Ask the user directly
```

Field mapping:

| Phase 0 item | project-manifest.json field | forge-decisions.json field |
|-------------|--------------------------|--------------------------|
| tech-stack | `sub_projects[].tech_stack` | `tech_stack` |
| architecture-type | -- | `architecture_type` |
| layer-mapping | -- | `layer_mapping` |
| module-list | `sub_projects[].modules[]` | -- |
| data-model | -- | -- |

Items obtained from upstream sources should be displayed with a source tag (e.g., "tech-stack: Go (Gin) -- from project-manifest"). User confirms once, then proceed to subsequent phases.

Profile confirmation checklist:
1. Tech stack identification
2. Architecture type (three-tier / two-tier / DDD / mixed)
3. Layer mapping (actual directory -> logical role)
4. Module list
5. Data model overview (entity count, DTO/VO count, common base fields)

## Decision Log

Record each user confirmation in `.allforai/code-tuner/tuner-decisions.json`:

```json
{
  "decisions": [
    {
      "step": "Phase 0",
      "item_id": "tech-stack",
      "decision": "confirmed",
      "value": "...",
      "decided_at": "ISO8601"
    }
  ]
}
```

Decision items: `tech-stack`, `architecture-type`, `layer-mapping`, `module-list`, `data-model`.

Resume mode: when decisions.json exists, skip confirmed items (show one-line summary), resume from the first item without a decision record.

## Phase Execution

For each phase, read the corresponding reference document to get detailed rules and detection methods.

After each phase completes, write results to the corresponding JSON file in `.allforai/code-tuner/`.

Do not ask for confirmation between phases. Proceed automatically after Phase 0 is confirmed.

## Report Output Requirements (mandatory)

After analysis, you MUST do two things:

### 1. Save report files

Write to `.allforai/code-tuner/`:
- `tuner-report.md` -- comprehensive report
- `tuner-tasks.json` -- refactoring task list
- `tuner-decisions.json` -- decision log

### 2. Display report summary in the conversation

Do NOT just say "report saved". Display the following directly:

```
## Code Tuner Report Summary

> Analysis time: {time}
> Mode: {full/compliance/duplication/abstraction}
> Lifecycle: {pre-launch/maintenance}
> Project scale: {files} files / {lines} lines / {modules} modules

### Overall Score

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Architecture compliance | XX/100 | 25% | XX |
| Code duplication | XX/100 | 25% | XX |
| Abstraction reasonableness | XX/100 | 20% | XX |
| Validation discipline | XX/100 | 15% | XX |
| Data model standards | XX/100 | 15% | XX |
| **Total** | | | **XX/100** |

### Issue Overview

| Level | Count |
|-------|-------|
| Critical (must fix) | X |
| Warning (should fix) | X |
| Info (reference) | X |

### Critical Issues
(List each: rule ID, location, description, fix suggestion)

### Warning Issues
(List each)

### Duplication Heatmap
(Which modules have the most duplication between them)

### Next Steps
1. Fix Critical issues first
2. Follow task order in tuner-tasks.json
3. Re-run code-tuner report mode to check score changes

> Full report: `.allforai/code-tuner/tuner-report.md`
> Task list: `.allforai/code-tuner/tuner-tasks.json`
```

The summary must include specific issue lists and fix suggestions, not just statistics. The user should know what went wrong, where, and how to fix it after reading the summary.
