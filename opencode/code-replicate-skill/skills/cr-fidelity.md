---
name: cr-fidelity
description: >
  Use when user wants to "verify replication fidelity", "check replication quality",
  "compare source vs target", "fidelity check", "check if migration is complete",
  or mentions verifying that target code faithfully reproduces source code behavior
  after code-replicate + dev-forge.
version: "2.0.0"
---

# Fidelity Verification — CR Fidelity v2.0

> Source vs target code fidelity closed-loop verification. Adaptive dimensions — verify whatever artifacts exist.

## Flow

| Stage | Name | Description |
|-------|------|-------------|
| 0 | Preparation | Build traceability index + adaptive dimension selection |
| A | Static Analysis | Score per selected dimensions |
| A2 | Runtime Verification | Build -> smoke -> test vectors -> protocol compatibility |
| B | Repair | Fix per gap list (runtime priority) |
| C | Re-score | Re-evaluate scores, if below threshold return to B |

`full` = 0 -> A -> A2 -> B -> C loop (max 3 rounds)
`analyze` = 0 -> A -> A2
`fix` = B -> C (based on last analysis)

---

## Stage 0: Preparation

### Build Traceability Index

> As previously defined: read dev-forge trace files -> fidelity-index.json + abstraction inheritance chain index

### Adaptive Dimension Selection

LLM scans `.allforai/` artifacts, decides which verification dimensions to enable based on **actually existing artifacts**:

```
Check task-inventory.json     -> exists? -> Read static-dimensions.md -> enable F1
Check source-summary.data_entities -> non-empty? -> enable F2
Check business-flows.json     -> exists? -> enable F3
Check role-profiles.json      -> exists? -> enable F4
Check use-case-tree.json      -> exists? -> enable F5
Check source-summary.abstractions -> non-empty? -> enable F6
Check constraints.json        -> exists? -> enable F7
Check infrastructure-profile.json -> exists? -> enable F8

Check experience-map.json     -> exists? -> Read ui-dimensions.md -> enable U1-U6

Check target project buildable?         -> Read runtime-verification.md -> enable R1
Check test-vectors.json       -> exists? -> enable R3
Check stack-mapping compatibility: exact -> enable R4
Check infrastructure-profile has data persistence? -> enable R5 behavior scenarios

Check infrastructure-profile has event bus? -> F9 event coverage enabled
Check infrastructure-profile has data persistence? -> F10 enabled (in static-dimensions.md)
Check infrastructure-profile has cannot_substitute? -> Read infra-critical-dimensions.md -> enable I1-I5
Check project_archetype has core algorithms? -> Read algorithm-dimensions.md -> enable A1-A3
Check project_archetype has ABI compatibility? -> Read abi-dimensions.md -> enable B1-B4
```

**archetype judgment is LLM semantic understanding** — read `replicate-config.project_archetype` free-text description, judge whether algorithms/ABI are involved. Not keyword matching.

**Don't hardcode "frontend uses U dimensions, backend uses F dimensions"** — purely decided by artifact existence. A backend BFF project with experience-map will enable U dimensions. A frontend App with local database will enable F2.

### Input (Three-Layer Loading)

**Resident layer** (~30KB): source-summary summary, product-map summary, stack-mapping platform_adaptation, fidelity-index, fidelity-report

**Dimension layer** (loaded on demand):
> Details: `./docs/fidelity/static-dimensions.md`
> Details: `./docs/fidelity/ui-dimensions.md`
> Details: `./docs/fidelity/runtime-verification.md`

**Target code layer**: precisely read via fidelity-index, no full scan

---

## Stage A: Static Analysis

LLM scores per Stage 0 selected dimensions.

**F dimensions** (code/business layer):
> Details: `./docs/fidelity/static-dimensions.md`

**U dimensions** (UI layer, only when experience-map exists):
> Details: `./docs/fidelity/ui-dimensions.md`

**A dimensions** (algorithm consistency, only when archetype contains core algorithms):
> Details: `./docs/fidelity/algorithm-dimensions.md`

**I dimensions** (critical infrastructure, only when infrastructure-profile has cannot_substitute components):
> Details: `./docs/fidelity/infra-critical-dimensions.md`

**B dimensions** (ABI compatibility, only when archetype is SDK/Library):
> Details: `./docs/fidelity/abi-dimensions.md`

**Attention restoration** (only consumer/mixed and experience-map exists):
- If `platform_adaptation` exists -> use `attention_threshold_override`
- Otherwise use default thresholds
- Not counted in overall score, listed in warnings

---

## Stage A2: Runtime Verification

> Details: `./docs/fidelity/runtime-verification.md`

---

## Stages B + C: Repair Loop

> Details: `./docs/fidelity/repair-protocol.md`

---

## Overall Scoring

```
Static score = (valid F* + valid U* + valid I* + valid A* + valid B* sum) / valid dimension count
Runtime score = (valid R* sum) / valid runtime dimension count
Overall score = static score x 0.5 + runtime score x 0.5

Special rule: I dimension (critical infrastructure) has any one scored 0
  -> Overall score marked as CRITICAL_INFRA_FAILURE
  -> Regardless of how high other dimensions score, report first line shows red warning
  -> Repair stage prioritizes I dimension gaps
```

---

## Output

Written to `.allforai/code-replicate/fidelity-report.json` + `fidelity-report.md`

---

## Relationship with Upstream/Downstream

```
code-replicate path (replication):
  code-replicate -> design-to-spec -> task-execute
      |
  cr-fidelity (code-level fidelity — replication-specific, not testing)
      |
  product-verify (functional acceptance — shared by both paths)
      |
  testforge (test quality — shared by both paths)
      |
  cr-visual (visual fidelity — after tests pass, App stable for screenshots)

product-design path (creation):
  product-design -> design-to-spec -> task-execute
      |
  product-verify -> testforge
```

**cr-fidelity is replication path specific**, verifying "does target code reproduce source code".
product-verify and testforge are **shared by both paths**, artifact-source agnostic.
cr-fidelity **does not do testing** — post-repair verification is re-scoring, not running tests.

---

## Load Core Protocol

> Core protocol details: `./skills/code-replicate-core.md`
