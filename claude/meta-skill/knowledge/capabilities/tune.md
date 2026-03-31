# Tune Capability

> Capability reference for architecture compliance, duplication detection, and abstraction analysis.
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Audit target code quality across 4 dimensions: compliance, duplication,
abstraction, validation. Output: scored report + task list.

## Core Principle

Same functionality, less code = higher quality. Five measurement dimensions:
duplication rate, abstraction level, cross-layer call depth, file scatter,
validation placement correctness.

## Phases

### Phase 0: Project Profile

- Detect architecture type (3-tier, 2-tier, DDD, modular)
- Map logical layers (Entry/Business/Data/Utility) by dependency direction (not folder names)
- Scan all entities, relations, DTO/VO distribution
- **User confirms profile before proceeding** (last human gate)
- Output: tuner-profile.json

### Phase 1: Architecture Compliance

- Load rules per architecture type:
  - T-01~T-06: 3-tier rules
  - W-01~W-03: 2-tier rules
  - D-01~D-04: DDD rules
  - G-01~G-06: universal rules (all architectures)
- Special T-03: Entry direct-to-Data access — valid for simple CRUD, violation for business logic
- Special G-04/G-05/G-06: layered validation (format at entry, business rules at business layer, none at data)
- Output: phase1-compliance.json

### Phase 2: Duplication Detection

- 4-layer scan: API/Entry, Service/Business, Data/Query, Utility
- >70% structural similarity = candidate duplicate
- Output: phase2-duplicates.json

### Phase 3: Abstraction Analysis

- Vertical: similar classes -> base class opportunity
- Horizontal: scattered code -> shared method opportunity
- Over-abstraction: 1 impl + 1 call site + transparent passthrough = over-engineered
- Output: phase3-abstractions.json

### Phase 4: Synthesis

- 5D scoring: compliance(25%) + duplication(25%) + abstraction(20%) + validation(15%) + data-model(15%)
- Output: tuner-report.md + tuner-tasks.json

## Two Modes

| Mode | Refactor Style | Violation Tagging | Task Order |
|------|---------------|-------------------|-----------|
| pre-launch | Aggressive: rewrite, merge, reorganize | MUST-FIX | By quality impact (biggest first) |
| maintenance | Conservative: extract methods, preserve structure | TECH-DEBT + risk assessment | By change risk (safest first) |

## Rules

1. **Backend code only**: Frontend/docs repos rejected.
2. **Understand-then-scan**: LLM reads project rules once, then batch scans.
3. **No auto-refactoring**: Report + task list only. No code changes.
4. **Pre-launch vs maintenance**: Each finding carries both aggressive and conservative variants.
5. **Responsibility over naming**: Layer assignment by dependency patterns and code responsibility, not folder names.
6. **Over-abstraction detection**: Simultaneously check "should abstract" and "shouldn't have abstracted".

## Knowledge References

### Phase-Specific:
- governance-styles.md: governance compliance checking
- design-audit-dimensions.md: pattern and behavioral consistency

## Composition Hints

### Single Node (default)
For quick audits and small codebases: one tune node runs all four phases sequentially.

### Split into Multiple Nodes
For deep analysis on large codebases: split per phase (tune-compliance, tune-duplication, tune-abstraction) to allow focused iteration on each dimension independently.

### Merge with Another Capability
Rarely merged. Tune is an independent audit capability that runs after implementation is complete. Keep separate.
