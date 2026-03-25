# Code-Tuner Execution Playbook

Detailed orchestration guide for the code-tuner workflow on OpenCode.

## When to Use

Use this workflow when the user wants to:
- assess backend architecture quality
- check layering or DDD compliance
- find duplicated backend logic
- identify abstraction or refactor opportunities
- generate a technical-debt report for server code

Do NOT use it for:
- frontend-only repositories
- documentation-only repositories
- design-only repositories

## Phase Table

| Phase | Goal | Outputs | Completion Signal |
|-------|------|---------|-------------------|
| 0 | Project profile | `tuner-profile.json`, `tuner-decisions.json` | User confirms profile |
| 1 | Architecture compliance | `phase1-compliance.json` | All rules checked, JSON written |
| 2 | Duplication detection | `phase2-duplicates.json` | All 4 scan dimensions complete, JSON written |
| 3 | Abstraction analysis | `phase3-abstractions.json` | All 5 analysis types complete, JSON written |
| 4 | Scoring + report | `tuner-report.md`, `tuner-tasks.json` | Report displayed in conversation |

## Mode Routing

Determine execution mode from the user's natural language:

| User intent | Mode | Phases |
|-------------|------|--------|
| "full analysis", "analyze my project", no specific request | full | 0 → 1 → 2 → 3 → 4 |
| "check compliance", "architecture check" | compliance | 0 → 1 → 4 |
| "find duplicates", "duplication check" | duplication | 0 → 2 → 4 |
| "abstraction analysis", "find refactor opportunities" | abstraction | 0 → 3 → 4 |
| "regenerate report", "update report" | report | 4 (from existing artifacts) |

## Lifecycle Detection

Parse lifecycle from user language:

- **pre-launch** (default): "new project", "not yet deployed", "before release", "pre-launch", or unspecified
- **maintenance**: "production", "live", "in maintenance", "already deployed", "running system"

If ambiguous, default to pre-launch. Only ask the user if their phrasing genuinely contradicts both modes.

## Pre-flight Check: Project Type Validation

Before any analysis, verify the target is a server-side project.

Scan the project root for at least one of:
- `pom.xml`, `build.gradle`, `build.gradle.kts` (Java)
- `go.mod` (Go)
- `package.json` with backend framework dependencies (Node.js)
- `requirements.txt`, `pyproject.toml`, `setup.py`, `manage.py` (Python)
- `*.csproj`, `*.sln` (.NET)
- `Cargo.toml` (Rust)
- `composer.json` (PHP)
- `Gemfile` (Ruby)

If none found, inform the user and stop:

> code-tuner is designed for server-side code (Java/Go/Node.js/Python/.NET/Rust/PHP/Ruby backend projects). No server-side tech stack configuration detected in this project.

## Artifact Detection for Resume

Before starting, check `.allforai/code-tuner/` for existing outputs:

| File | Meaning | Action |
|------|---------|--------|
| `tuner-profile.json` | Phase 0 complete | Show summary, ask user to confirm or redo |
| `tuner-decisions.json` | Partial Phase 0 decisions | Resume from first missing decision |
| `phase1-compliance.json` | Phase 1 complete | Skip Phase 1 (unless user requests re-run) |
| `phase2-duplicates.json` | Phase 2 complete | Skip Phase 2 (unless user requests re-run) |
| `phase3-abstractions.json` | Phase 3 complete | Skip Phase 3 (unless user requests re-run) |
| `tuner-report.md` | Phase 4 complete | Archive as `tuner-report-{timestamp}.md` before regenerating |

## Phase 0: Upstream Consumption Chain

Phase 0 gathers project profile information using this priority chain. For each decision item, use the highest-priority source available; only ask the user for items that cannot be resolved:

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

Field mapping from upstream sources:

| Phase 0 item | project-manifest.json field | forge-decisions.json field |
|-------------|--------------------------|--------------------------|
| tech-stack | `sub_projects[].tech_stack` | `tech_stack` |
| architecture-type | -- | `architecture_type` |
| layer-mapping | -- | `layer_mapping` |
| module-list | `sub_projects[].modules[]` | -- |
| data-model | -- | -- |

Display source attribution for auto-filled items (e.g., "tech-stack: Go (Gin) -- from project-manifest"). Present the full profile for user confirmation once before proceeding.

## Phase 0: Decision Log

Record each confirmed decision in `tuner-decisions.json`:

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

In resume mode, skip items that already have a decision record; show a one-line summary and continue from the first missing item.

## Orchestration Rules

1. **Do not ask for confirmation between phases** -- once the user confirms Phase 0, proceed through all remaining phases automatically.
2. **Ask only when blocking information is required** -- if a technical decision blocks the next phase and cannot be inferred, ask the user. Otherwise, make a reasonable assumption and note it.
3. **Write outputs immediately** -- save each phase's JSON output as soon as the phase completes, before starting the next phase.
4. **Phase 4 is always the final phase** -- regardless of mode, Phase 4 produces the report.
5. **Report mode (Phase 4 only)** -- requires existing phase output files. If any are missing, inform the user which phases need to run first.

## Phase Execution Details

### Phase 0 execution

Read the file at `./references/phase0-profile.md` for detailed detection rules.

1. Run pre-flight check (project type validation)
2. Check upstream sources per the consumption chain above
3. Auto-detect remaining items by scanning the codebase
4. Present the full profile to the user for confirmation
5. Write confirmed profile to `.allforai/code-tuner/tuner-profile.json`
6. Write decisions to `.allforai/code-tuner/tuner-decisions.json`

Profile confirmation must include:
1. Tech stack (language, framework, build tool)
2. Architecture type (three-tier / two-tier / DDD / mixed)
3. Layer mapping (actual directory -> logical role)
4. Module list
5. Data model overview (entity count, DTO/VO count, common base fields)

### Phase 1 execution

Read the file at `./references/phase1-compliance.md` for rule definitions.

Load rules matching the detected architecture type. Scan each layer's files for import/dependency patterns. Write violations to `.allforai/code-tuner/phase1-compliance.json`.

### Phase 2 execution

Read the file at `./references/phase2-duplicates.md` for detection methods.

Scan all four dimensions (entry, business, data, utility). Use structural signature comparison. Write results to `.allforai/code-tuner/phase2-duplicates.json`.

### Phase 3 execution

Read the file at `./references/phase3-abstractions.md` for analysis methods.

Analyze all five types (vertical, horizontal, API consolidation, validation, over-abstraction). Write results to `.allforai/code-tuner/phase3-abstractions.json`.

### Phase 4 execution

Read the file at `./references/phase4-report.md` for scoring formulas and report template.

1. Calculate five-dimension scores using deduction-based formulas
2. Generate weighted total score
3. If previous report exists, archive it and generate trend comparison
4. Write `tuner-report.md` and `tuner-tasks.json`
5. Display report summary directly in the conversation

## Report Output Requirements

After analysis, two things are mandatory:

### 1. Save report files

Write to `.allforai/code-tuner/`:
- `tuner-report.md` -- comprehensive report
- `tuner-tasks.json` -- refactoring task list

### 2. Display summary in conversation

Never just say "report saved". Display the full summary including:

- Total score and grade (A/B/C/D/F)
- Five-dimension score table
- All Critical issues with file paths
- Top 3 Warning issues with descriptions
- Duplication heatmap (which modules overlap most)
- Top 3 priority tasks for the current lifecycle mode
- File paths where reports are saved

## Final Response Contract

After analysis, provide:
- Selected mode and lifecycle
- Concise score summary with grade
- Highest-severity findings with file locations
- Location of generated report artifacts

If no findings are discovered, state that explicitly and mention any residual coverage gaps.
