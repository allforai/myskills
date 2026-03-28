---
name: code-tuner
description: >
  Use this skill when the user asks to "analyze server code quality",
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

# Code-Tuner -- Server-Side Code Tuning

## Core Philosophy

Same functionality, less code = higher quality. Measured across five dimensions:

- **Duplication rate** -- quantity and distribution of similar code segments
- **Abstraction level** -- number of functions/classes/files needed for a single feature
- **Cross-layer call depth** -- how many layers a request traverses to reach logic
- **File dispersion** -- how many files contain related logic
- **Validation standards** -- whether validation logic is in the correct layer and unified

Analyzes backend code only. Covers Entry (API), Business (Service), Data (Repository), and Utility layers.

---

## Two Lifecycle Modes

| | Pre-launch | Maintenance |
|---|---|---|
| Refactoring advice | Aggressive: rewrite, merge, reorganize directories | Conservative: extract shared methods, extract interfaces, keep existing structure |
| Architecture violations | Label as `MUST-FIX` | Label as `TECH-DEBT` with risk assessment |
| Duplicated code | Suggest merging into one place | Suggest extracting shared method, keep original call sites |
| Task ordering | By code quality impact (biggest first) | By change risk (safest first) |

---

## Workflow Overview

```
Phase 0: Project Profile --> confirm/infer
     |
Phase 1: Architecture Compliance Check
     |
Phase 2: Duplication Detection
     |
Phase 3: Abstraction Opportunity Analysis
     |
Phase 4: Scoring + Report + Refactoring Task List
```

---

### Phase 0: Project Profile

> See `./references/phase0-profile.md`

Identify tech stack, infer architecture type, map layers, identify modules, scan data model.

**Key principle:** Layer mapping is based on logical roles (Entry / Business / Data / Utility), not directory names. Analyze dependency direction and code responsibilities to determine which layer each directory belongs to. Different projects use different names -- names do not matter, responsibilities and dependency direction do.

Entity classes and database table structures are the most important server-side information. Scan all entities, relationships, DTO/VO distribution.

Output `tuner-profile.json`. Architecture type + layer mapping + module list + data model must be confirmed. Confirm with user only if architecture type cannot be reliably inferred from code analysis.

> Cross-language directory mapping reference: `./references/layer-mapping.md`

---

### Phase 1: Architecture Compliance Check

> See `./references/phase1-compliance.md`

Load rules by architecture type, check dependency direction, layer responsibilities, validation placement.

**Rule categories:**
- **T-01 to T-06** -- Three-tier architecture rules
- **W-01 to W-03** -- Two-tier architecture rules
- **D-01 to D-04** -- DDD rules
- **G-01 to G-06** -- Universal rules (all architectures)

**Special rules:**
- **T-03**: When Entry layer directly accesses Data layer, determine if reasonable. Simple CRUD (no business logic, no composite calls, no transaction requirements) = OK, not a violation. Contains business logic = violation, should be in Business layer.
- **G-04/G-05/G-06**: Layered validation principle (lenient-in, strict-out). Format validation in Entry layer (because Business layer can be called by multiple entries). Business rule validation in Business layer. Data layer does no business validation.

Output `phase1-compliance.json`.

---

### Phase 2: Duplication Detection

> See `./references/phase2-duplicates.md`

Four scanning dimensions:

1. **API/Entry layer duplication** -- multiple endpoints doing highly similar things (export, pagination, CRUD)
2. **Business layer duplication** -- similar methods across Services, copy-paste with only entity name changed
3. **Data layer duplication** -- similar queries, repeated pagination logic, DTO/VO field overlap > 70%
4. **Utility duplication** -- functionally identical tool methods, reimplementing existing library capabilities

Detection method: Extract structural signatures (param types > operation sequence > return type), mark as candidate duplicate when similarity > 70%.

If a Service method only passes through to Repository (no business logic), suggest removing it and having Entry call Data directly.

Output `phase2-duplicates.json`.

---

### Phase 3: Abstraction Opportunity Analysis

> See `./references/phase3-abstractions.md`

Five analysis types:

1. **Vertical abstraction** -- multiple classes with highly similar structure > extract base class
2. **Horizontal abstraction** -- similar code fragments scattered across files > extract shared method
3. **Interface consolidation** -- multiple APIs with same logic but different entities > parameterize
4. **Validation logic** -- validation placement, duplication, lenient-in/strict-out, error response consistency
5. **Over-abstraction detection (reverse check)** -- interfaces with only 1 implementation, utility methods called only once, layer-by-layer passthrough with no added value, excessively deep inheritance

Output `phase3-abstractions.json`.

---

### Phase 4: Scoring + Report

> See `./references/phase4-report.md`

**Five-dimension scoring (each 0-100, weighted total):**

| Dimension | Weight |
|-----------|--------|
| Architecture compliance | 25% |
| Code duplication rate | 25% |
| Abstraction quality | 20% |
| Validation standards | 15% |
| Data model quality | 15% |

Output `tuner-report.md` (summary + problem list + heatmap + detailed findings) and `tuner-tasks.json` (actionable refactoring task list).

---

## File Structure

```
your-project/
+-- .allforai/code-tuner/
    +-- tuner-profile.json        # Phase 0: Project profile
    +-- phase1-compliance.json    # Phase 1: Architecture violations
    +-- phase2-duplicates.json    # Phase 2: Duplication results
    +-- phase3-abstractions.json  # Phase 3: Abstraction opportunities
    +-- tuner-report.md           # Phase 4: Comprehensive report
    +-- tuner-tasks.json          # Phase 4: Refactoring task list
```

---

## Key Principles

1. **Backend projects only** -- Non-backend projects (frontend, Markdown, documentation repos, etc.) are not suitable; inform the user and do not analyze
2. **Phase 0 profile must be confirmed** -- Getting architecture type wrong invalidates all subsequent analysis
3. **No auto-refactoring** -- Only output reports and task lists; user decides what to execute
4. **Two modes throughout** -- Every finding provides different suggestions for both modes
5. **Lenient-in, strict-out** -- Format validation in Entry layer, business validation in Business layer, Data layer does not cross boundaries
6. **Simple passthrough can skip layers** -- Pure CRUD with no business logic allows Entry to call Data directly
7. **No over-abstraction** -- Simultaneously detect "should abstract but did not" and "should not abstract but did"
8. **Names do not matter, responsibilities do** -- Identify layers by dependency patterns, not directory names

---

## Execution Engine Phase Declarations

```yaml
# execution-engine: ./docs/execution-engine.md

phases:
  - id: profile
    subagent_task: "项目画像：探测技术栈、架构类型、分层结构、模块划分"
    input: ["项目代码库"]
    output: ".allforai/code-tuner/tuner-profile.json"
    rules: ["./references/phase0-profile.md", "./references/layer-mapping.md"]

  - id: compliance
    subagent_task: "架构合规检查：依赖方向、分层规则、跨架构通用规则"
    input: [".allforai/code-tuner/tuner-profile.json", "项目代码库"]
    output: ".allforai/code-tuner/phase1-compliance.json"
    rules: ["./references/phase1-compliance.md"]
    depends_on: [profile]

  - id: duplicates
    subagent_task: "重复检测：API/Service/Data/Utility 四层扫描"
    input: [".allforai/code-tuner/tuner-profile.json", "项目代码库"]
    output: ".allforai/code-tuner/phase2-duplicates.json"
    rules: ["./references/phase2-duplicates.md"]
    depends_on: [profile]

  - id: abstractions
    subagent_task: "抽象分析：垂直/水平/接口合并/验证逻辑/过度抽象"
    input: [".allforai/code-tuner/tuner-profile.json", "项目代码库"]
    output: ".allforai/code-tuner/phase3-abstractions.json"
    rules: ["./references/phase3-abstractions.md"]
    depends_on: [profile]

  - id: report
    subagent_task: "综合报告：5维评分 + 热力图 + 重构任务清单"
    input: [".allforai/code-tuner/phase1-compliance.json", ".allforai/code-tuner/phase2-duplicates.json", ".allforai/code-tuner/phase3-abstractions.json"]
    output: ".allforai/code-tuner/tuner-report.md, .allforai/code-tuner/tuner-tasks.json"
    rules: ["./references/phase4-report.md"]
    depends_on: [compliance, duplicates, abstractions]
```

## full Mode Execution

Read `./docs/execution-engine.md` for the dispatch protocol.

The main flow operates as a pure dispatcher:
1. Topological sort by phases depends_on
2. Dispatch subagents per phase (or parallel), using the task template from the protocol
3. Collect phase summaries, selectively inject into next phase
4. On UPSTREAM_DEFECT, route back per protocol
5. compliance / duplicates / abstractions can be dispatched in parallel after profile completes

---

## Usage Examples

### Scenario 1: New project full analysis

```
Analyze my project with code-tuner.
Project path: /path/to/project.
Project status: pre-launch.
```

### Scenario 2: Maintenance project

```
Run code-tuner on my project.
Project path: /path/to/project.
Project is in maintenance/production.
```

### Scenario 3: Single phase only

```
Run code-tuner duplication detection only.
Project path: /path/to/project.
Profile is at .allforai/code-tuner/tuner-profile.json.
```

### Scenario 4: Specific module analysis

```
Run code-tuner on the order module only.
Project path: /path/to/project.
Only scan src/modules/order directory.
```
