---
name: code-tuner
description: "Server-side code tuning: architecture compliance, duplication detection, abstraction analysis, validation standards. Modes: full / compliance / duplication / abstraction / report"
---

# Code-Tuner -- Server-Side Code Tuning

## Mode Routing

Determine execution mode from the user's request:

- **No mode specified or "full"** -> Complete analysis: Phase 0 > Phase 1 > Phase 2 > Phase 3 > Phase 4
- **"compliance"** -> Architecture compliance only: Phase 0 > Phase 1 > Phase 4
- **"duplication"** -> Duplication detection only: Phase 0 > Phase 2 > Phase 4
- **"abstraction"** -> Abstraction analysis only: Phase 0 > Phase 3 > Phase 4
- **"report"** -> Regenerate report: read existing phase outputs, regenerate Phase 4

## Lifecycle Mode

Determine from user context:

- **`pre-launch` (default)** -> Aggressive optimization suggestions
- **`maintenance`** -> Conservative optimization suggestions

If the user does not specify, assume pre-launch. Only ask when the answer is
genuinely ambiguous and would change the analysis approach.

## Pre-flight Check: Project Type Validation (mandatory)

Before any analysis, verify the target is a server-side code project.

**Detection method:** Scan project root for at least one of:
- `pom.xml`, `build.gradle`, `build.gradle.kts` (Java)
- `go.mod` (Go)
- `package.json` with backend framework deps -- express, nestjs, koa, fastify, etc. (Node.js)
- `requirements.txt`, `pyproject.toml`, `setup.py`, `manage.py` (Python)
- `*.csproj`, `*.sln` (C#/.NET)
- `Cargo.toml` (Rust)
- `composer.json` (PHP)
- `Gemfile` (Ruby)

**If no server-side config found:** Inform the user and stop. Do not proceed with any Phase.

Do not force-analyze non-backend projects. For frontend, Markdown, documentation,
or config-only repositories, the rule system does not apply and results would be meaningless.

---

## Execution Flow

1. **Run pre-flight check** (see above); abort if it fails
2. Read `./SKILL.md` for complete domain knowledge and key principles
3. Read the reference document for each phase as needed
4. Execute phases according to the selected mode
5. **After completion, output a full report summary in the conversation** (see "Report Output Requirements" below)

## Reference Documents (load as needed per phase)

- `./SKILL.md` -- Goals, key principles, workflow overview
- `./references/phase0-profile.md` -- Phase 0: Project profile details
- `./references/phase1-compliance.md` -- Phase 1: Architecture compliance rules
- `./references/phase2-duplicates.md` -- Phase 2: Duplication detection methods
- `./references/phase3-abstractions.md` -- Phase 3: Abstraction opportunity analysis
- `./references/phase4-report.md` -- Phase 4: Scoring and report generation
- `./references/layer-mapping.md` -- Cross-language layer mapping reference

## Phase 0 Execution Requirements

Phase 0 is required for all modes. Use the following priority chain to obtain profile
information. Decisions already available from upstream sources are adopted directly
(show a one-line summary); only missing or conflicting items require further action.

### Upstream Consumption Chain (Front-load Decisions)

```
Priority 1: .allforai/code-tuner/tuner-profile.json (own cache)
    | not found or stale
Priority 2: .allforai/project-forge/project-manifest.json (from project-setup)
    | not found
Priority 3: .allforai/project-forge/forge-decisions.json (from project-setup)
    | not found
Priority 4: Auto-detection (scan code to infer)
    | cannot infer
Priority 5: Ask the user (only when the answer would materially affect analysis)
```

**Field mapping:**

| Phase 0 Decision | project-manifest.json field | forge-decisions.json field |
|-------------------|----------------------------|---------------------------|
| tech-stack | `sub_projects[].tech_stack` | `tech_stack` |
| architecture-type | -- | `architecture_type` |
| layer-mapping | -- | `layer_mapping` |
| module-list | `sub_projects[].modules[]` | -- |
| data-model | -- | -- |

**Execution logic:**

1. Try reading `tuner-profile.json` -> exists and not stale -> show summary, skip Phase 0
2. Not found -> try `project-manifest.json` + `forge-decisions.json`
3. Extract mappable decisions from upstream, auto-fill (show source attribution)
4. Fill remaining gaps through auto-detection or asking the user
5. Once complete, write `tuner-profile.json`

Profile confirmation items:
1. Tech stack identification
2. Architecture type (three-tier / two-tier / DDD / mixed)
3. Layer mapping (actual directory -> logical role)
4. Module list
5. Data model overview (entity count, DTO/VO count, common fields)

Items obtained from upstream show source attribution. Confirm with user only if
architecture type is ambiguous or auto-detection confidence is low.

## Per-Phase Execution

For each phase, load the corresponding reference document for detailed rules and
detection methods. After each phase completes, write results to the corresponding
JSON file in `.allforai/code-tuner/`.

## Decision Log

When decisions are confirmed (either from upstream or user input), append to
`tuner-decisions.json`:

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

**Output path:** `.allforai/code-tuner/tuner-decisions.json`

**Decision points:** tech-stack, architecture-type, layer-mapping, module-list, data-model

**Resume mode:** When decisions.json exists, confirmed steps are skipped (show one-line
summary). Resume from the first step without a decision record.

---

## Report Output Requirements (mandatory)

After analysis, two things must happen:

### 1. Save Report Files

Write complete reports to `.allforai/code-tuner/`:
- `tuner-report.md` -- Comprehensive report
- `tuner-tasks.json` -- Refactoring task list
- `tuner-decisions.json` -- Decision log

### 2. Output Report Summary in Conversation

Do not just say "report complete" or "report saved". Present the following directly:

```
## Code Tuner Report Summary

> Analysis time: {time}
> Analysis mode: {full/compliance/duplication/abstraction}
> Lifecycle: {pre-launch/maintenance}
> Project scale: {files} files / {lines} lines / {modules} modules

### Overall Score

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Architecture compliance | XX/100 | 25% | XX |
| Code duplication rate | XX/100 | 25% | XX |
| Abstraction quality | XX/100 | 20% | XX |
| Validation standards | XX/100 | 15% | XX |
| Data model quality | XX/100 | 15% | XX |
| **Total** | | | **XX/100** |

### Issue Overview

| Severity | Count |
|----------|-------|
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
3. Re-run code-tuner report mode after fixes to check score changes

> Full report saved to: `.allforai/code-tuner/tuner-report.md`
> Task list: `.allforai/code-tuner/tuner-tasks.json`
```

**Key: The summary must include specific issue lists and fix suggestions, not just
statistics. The user should know what went wrong, where, and how to fix it after
reading the summary.**
