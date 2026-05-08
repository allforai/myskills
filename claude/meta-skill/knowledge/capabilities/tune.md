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
- Output: `.allforai/code-tuner/tuner-profile.json`

### Phase 1: Architecture Compliance

- Load rules per architecture type:
  - T-01~T-06: 3-tier rules
  - W-01~W-03: 2-tier rules
  - D-01~D-04: DDD rules
  - G-01~G-06: universal rules (all architectures)
- Special T-03: Entry direct-to-Data access — valid for simple CRUD, violation for business logic
- Special G-04/G-05/G-06: layered validation (format at entry, business rules at business layer, none at data)
- Output: `.allforai/code-tuner/phase1-compliance.json`

### Phase 2: Duplication Detection

- 4-layer scan: API/Entry, Service/Business, Data/Query, Utility
- >70% structural similarity = candidate duplicate
- Output: `.allforai/code-tuner/phase2-duplicates.json`

### Phase 3: Abstraction Analysis

- Vertical: similar classes -> base class opportunity
- Horizontal: scattered code -> shared method opportunity
- Over-abstraction: 1 impl + 1 call site + transparent passthrough = over-engineered
- Output: `.allforai/code-tuner/phase3-abstractions.json`

### Phase 4: Synthesis

- 5D scoring: compliance(25%) + duplication(25%) + abstraction(20%) + validation(15%) + data-model(15%)
- Output: `.allforai/code-tuner/tuner-report.md` + `.allforai/code-tuner/tuner-tasks.json`

**tuner-tasks.json field schema:**
```json
{
  "compliance_score": "<number 0-100>",
  "duplication_score": "<number 0-100>",
  "abstraction_score": "<number 0-100>",
  "validation_score": "<number 0-100>",
  "data_model_score": "<number 0-100>",
  "composite_score": "<number 0-100 — compliance*0.25 + duplication*0.25 + abstraction*0.20 + validation*0.15 + data_model*0.15>",
  "tuner_tasks": [
    {
      "id": "<string>",
      "phase": "<enum: compliance | duplication | abstraction | validation | data-model>",
      "severity": "<enum: critical | major | minor>",
      "description": "<string>",
      "file": "<string — file:line>"
    }
  ]
}
```
`compliance_score`, `duplication_score`, `abstraction_score` are the three primary scores
consumed by launch-prep as a baseline reference.

## Two Modes

| Mode | Refactor Style | Violation Tagging | Task Order |
|------|---------------|-------------------|-----------|
| pre-launch | Aggressive: rewrite, merge, reorganize | MUST-FIX | By quality impact (biggest first) |
| maintenance | Conservative: extract methods, preserve structure | TECH-DEBT + risk assessment | By change risk (safest first) |

## Rules

1. **Backend or library code**: Applies to backend services, CLI tools, library/SDK packages. Frontend-only repos (no business logic) and documentation repos are rejected.
2. **Understand-then-scan**: LLM reads project rules once, then batch scans.
3. **No auto-refactoring**: Report + task list only. No code changes.
4. **Pre-launch vs maintenance**: Each finding carries both aggressive and conservative variants.
5. **Responsibility over naming**: Layer assignment by dependency patterns and code responsibility, not folder names.
6. **Over-abstraction detection**: Simultaneously check "should abstract" and "shouldn't have abstracted".

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `.allforai/code-tuner/tuner-tasks.json` | `compliance_score`, `duplication_score`, `abstraction_score` | launch-prep | optional | 上架准备检查代码治理基准分（可接受门槛） |
| `.allforai/code-tuner/tuner-tasks.json` | `tuner_tasks[]` | (human review) | optional | 治理任务列表供人工排期，无自动下游消费者 |

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
