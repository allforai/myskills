# Translate Capability

> Generate target platform code from source code + .allforai/ artifacts.
> Internal execution is LLM-driven — strategy selected per component.

## Goal

Generate target platform code from source code + .allforai/ artifacts.
Strategy selection per component, compile-verify loop per module.

## Prerequisites / Context Pull

| Artifact | Source | Field | Required | When |
|----------|--------|-------|----------|------|
| `source-summary.json` | discovery | `tech_stacks`, `modules` | required | always — tech stack drives strategy selection and build commands |
| `file-catalog.json` | discovery | `modules[].key_files` | required | always — translate reads source files from this catalog |
| `reuse-assessment.json` | discovery | `per_component` | optional | translate/rebuild goals — determines reuse vs rebuild per component |
| `prune-tasks.json` | feature-prune | `decisions[].included` | optional | when feature-prune node exists — scope gate for implementation |
| `entity-model.json` | generate-artifacts | `entities[]`, `relationships[]` | required | create/rebuild goals — data model foundation for ORM/migrations |
| `product-map.json` | generate-artifacts | all fields | required | create/rebuild goals — drives component scope and order |
| `api-spec.json` | design-to-spec | `endpoints[]` | required | create/rebuild goals when design-to-spec is present |
| `db-schema.md` | design-to-spec | table definitions | required | create/rebuild goals when design-to-spec is present |
| `protocol-spec.md` | design-to-spec | message types | optional | realtime projects (WebSocket/gRPC/SSE) only |

**Existing code conflict resolution**: Before writing any file, check whether a target file already exists. If yes: diff against intended output. Minor divergence → emit `TODO(merge-conflict)` comment at the diff site and proceed. Structural divergence (different architecture) → raise as UPSTREAM_DEFECT and pause — do not overwrite silently.

## What LLM Must Accomplish (not how)

### Required Outcomes

- Target project scaffold initialized and building
- All components translated with appropriate strategy
- Compile-verify loop passed for each component
- Route parity verified (every source route has a target equivalent)
- Model-to-route traceability verified
- Prune scope respected: load `.allforai/feature-prune/prune-tasks.json` before planning component scope. Only implement tasks where `decisions[].included = true`. Tasks with `included = false` must NOT be implemented — create a `TODO(excluded-by-prune)` comment at most.
- `translation-manifest.json` written to `.allforai/translate/translation-manifest.json` on completion — records each module's status and output path for compile-verify and product-verify consumption.

### Strategy Selection (per component, LLM decides)

| Complexity | Strategy | LLM Input | Output |
|-----------|----------|-----------|--------|
| Low (pure UI, no logic) | direct_translate | Source code + mapping | Syntax-converted code |
| Medium (stateful, controllable) | translate_with_adapt | Source code + target patterns | Translated + restructured |
| High (complex business, cross-module) | intent_rebuild | .allforai/ artifacts (not source) | Native target code from intent |

### Required Quality

- Compile after every component — don't batch
- `TODO(migration)` for unmappable items — not silent skip
- Abstraction preservation — don't expand shared base classes into N copies
- Route parity — every source route/endpoint has a target equivalent
- Consumer-priority: if experience_priority = consumer/mixed, UI completion bar is higher

## Methodology Guidance (not steps)

- **Scaffold first**: Initialize target project, verify it builds before any translation
- **Topological order**: Translate by dependency (foundations first, UI last)
- **Compile after every component**: Catch errors early
- **intent_rebuild reads artifacts, not source**: Prevents copying technical debt
- **Round-based checkpointing**: Persist progress after each round

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Upstream-Baseline-Validation: verify translated code against product artifacts
- experience-map-schema.md: screen contracts for UI translation

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| source code files | implementation files per module | compile-verify | required | 编译验证需要全部源代码文件存在 |
| source code files | implementation files per module | spec-compliance-verify | required | Spec 合规验证需要对照代码与设计规格 |

## Composition Hints

### Split into Multiple Nodes (default)
ALWAYS split per target platform: translate-ios, translate-api, translate-web.

### Single Node
Only for single-platform projects with a small codebase.
