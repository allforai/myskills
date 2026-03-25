---
name: code-tuner
description: >
  This skill should be used when the user asks to "analyze server code quality",
  "check architecture compliance", "find duplicate code", "detect code duplication",
  "review backend architecture", "optimize server code", "code tuning",
  "refactor my backend", "audit code architecture", "code quality review",
  "assess technical debt", "check if code follows three-tier architecture",
  "check DDD compliance", "find abstraction opportunities", "analyze validation logic",
  or mentions server-side code optimization, backend refactoring,
  architectural violations, layered architecture review, or technical debt assessment.
  Supports three-tier, two-tier, and DDD architectures across any language.
version: "2.0.0"
---

# Code-Tuner — Server-Side Code Quality Analysis

## Overview

Code-tuner analyzes backend codebases across five quality dimensions:

- **Duplication rate** — similar code segments, their count and distribution
- **Abstraction level** — number of functions/classes/files needed to accomplish the same task
- **Cross-layer call depth** — how many layers a request traverses to reach logic
- **File scatter** — how many files related logic is spread across
- **Validation discipline** — whether validation logic is in the correct layer and unified

Covers Entry (API), Business (Service), Data (Repository), and Utility layers. Only analyzes server-side code.

## Available Workflows

| Mode | Phases | Description |
|------|--------|-------------|
| full (default) | 0 → 1 → 2 → 3 → 4 | Complete analysis across all dimensions |
| compliance | 0 → 1 → 4 | Architecture compliance check only |
| duplication | 0 → 2 → 4 | Duplication detection only |
| abstraction | 0 → 3 → 4 | Abstraction opportunity analysis only |
| report | 4 only | Regenerate report from existing phase outputs |

## Lifecycle Modes

| Mode | Refactoring | Violations | Duplication | Task Ordering |
|------|-------------|------------|-------------|---------------|
| pre-launch (default) | Aggressive: rewrite, merge, reorganize | MUST-FIX | Merge into single location | By code quality impact (biggest first) |
| maintenance | Conservative: extract shared methods, keep structure | TECH-DEBT with risk assessment | Extract shared method, keep call sites | By change risk (safest first) |

Default to pre-launch unless the user clearly indicates a live production system.

## Workflow

### Phase 0: Project Profile

> Details: `./references/phase0-profile.md`

Identify tech stack, infer architecture type, map layers, identify modules, scan data model.

Key principle: layer mapping is based on logical roles (Entry / Business / Data / Utility), not directory names. Analyze dependency direction and code responsibilities to determine each directory's layer.

Entity classes and database table structures are the most important server-side information.

Output: `tuner-profile.json`. Architecture type + layer mapping + module list + data model must be confirmed by the user.

> Cross-language directory mapping reference: `./references/layer-mapping.md`

### Phase 1: Architecture Compliance

> Details: `./references/phase1-compliance.md`

Load rules by architecture type, check dependency direction, layer responsibilities, validation placement.

Rule categories: T-01~T-06 (three-tier), W-01~W-03 (two-tier), D-01~D-04 (DDD), G-01~G-06 (universal).

Output: `phase1-compliance.json`.

### Phase 2: Duplication Detection

> Details: `./references/phase2-duplicates.md`

Four scan dimensions: API/entry layer duplication, business layer duplication, data layer duplication, utility duplication.

Detection method: extract method structural signatures (parameter types → operation sequence → return type), mark as candidate duplicate when similarity > 70%.

Output: `phase2-duplicates.json`.

### Phase 3: Abstraction Opportunity Analysis

> Details: `./references/phase3-abstractions.md`

Five analysis types: vertical abstraction, horizontal abstraction, interface consolidation, validation logic, over-abstraction detection (reverse check).

Output: `phase3-abstractions.json`.

### Phase 4: Scoring + Report

> Details: `./references/phase4-report.md`

Five-dimension scoring (each 0-100, weighted total):

| Dimension | Weight |
|-----------|--------|
| Architecture compliance | 25% |
| Code duplication | 25% |
| Abstraction reasonableness | 20% |
| Validation discipline | 15% |
| Data model standards | 15% |

Output: `tuner-report.md` (summary + issue list + heatmap + detailed findings) and `tuner-tasks.json` (actionable refactoring task list).

## Key Principles

1. **Server-side projects only** — refuse non-backend projects (frontend, Markdown, documentation repos)
2. **Phase 0 requires user confirmation** — wrong architecture type leads to wrong analysis
3. **Read-only analysis** — only output reports and task lists; user decides what to execute
4. **Two modes throughout** — every finding includes different suggestions for both lifecycle modes
5. **Loose-in, strict-out** — format validation at entry layer, business validation at business layer, data layer stays in its lane
6. **Simple passthrough may skip layers** — pure CRUD with no business logic allows entry layer to call data layer directly
7. **No over-abstraction** — detect both "should abstract but didn't" and "shouldn't abstract but did"
8. **Names don't matter, responsibilities do** — identify layers by dependency patterns, not directory names

## File Structure

```
your-project/
└── .allforai/code-tuner/
    ├── tuner-profile.json        # Phase 0: project profile
    ├── tuner-decisions.json      # Phase 0: decision log
    ├── phase1-compliance.json    # Phase 1: architecture violations
    ├── phase2-duplicates.json    # Phase 2: duplication detection results
    ├── phase3-abstractions.json  # Phase 3: abstraction opportunities
    ├── tuner-report.md           # Phase 4: comprehensive report
    └── tuner-tasks.json          # Phase 4: refactoring task list
```

## Usage

### Full analysis of a new project

```
Analyze my backend project's code quality. The project is at /path/to/project. It's pre-launch.
```

### Maintenance-mode project

```
Run code-tuner on my project at /path/to/project. It's in production maintenance mode.
```

### Single phase only

```
Just run duplication detection on my project. The profile is already at .allforai/code-tuner/tuner-profile.json.
```

### Specific module analysis

```
Analyze only the order module with code-tuner. Project is at /path/to/project, focus on src/modules/order.
```

## Orchestration

For detailed phase execution logic, transition rules, and resume handling, see `./execution-playbook.md`.
