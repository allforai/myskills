# Discovery Capability

> Understand an existing project. Bootstrap generates project-specific discovery nodes.
> Internal execution is LLM-driven — no fixed phase sequence.

## Goal

Build a complete understanding of the project: structure, modules, tech stack,
infrastructure, abstractions, cross-cutting concerns, and reuse potential.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What | Why downstream needs it |
|--------|------|------------------------|
| `source-summary.json` | Module inventory, tech stacks, architecture pattern | product-analysis needs to know what exists |
| `file-catalog.json` | Key files per module with business intent | generate-artifacts needs to read source |
| `infrastructure-profile.json` | DB, cache, auth, storage, background jobs | setup-runtime-env needs to know what to configure |

For rebuild/translate goals, also:

| Output | What | Why |
|--------|------|-----|
| `reuse-assessment.json` | Per-component: reuse / adapt / remove / new | rebuild nodes need to know what to keep |

### Required Coverage

- File coverage >= 50% per module (header scan for uncovered files)
- Infrastructure components documented (what user sees if missing, periodic behaviors, lifecycle)
- Config-as-code included (nginx.conf, routes.yaml, OpenAPI spec = potential business logic)
- Event bus inventory (if exists: all event types + publishers + subscribers)
- Implicit behaviors documented (mixin/decorator/annotation-driven auto-CRUD, auto-sync, etc.)

### Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `source-summary.json` | `tech_stacks` | translate, compile-verify, quality-checks | required | 翻译策略和编译验收都依赖技术栈 |
| `source-summary.json` | `modules` | product-analysis, generate-artifacts | required | 模块边界是产物分析和代码生成的基础 |
| `source-summary.json` | `architecture_pattern` | product-analysis | optional | 有助于识别设计模式，缺失时用代码读取兜底 |
| `source-summary.json` | `detected_patterns` | product-analysis, translate | optional | 辅助推断业务意图和翻译复杂度 |
| `file-catalog.json` | `modules[].key_files` | translate, generate-artifacts | required | 代码生成需要知道读哪些源文件 |
| `infrastructure-profile.json` | `databases`, `caches`, `auth` | demo-forge, test-verify | required | demo 数据填充和测试都需要知道基础设施 |
| `reuse-assessment.json` | `per_component` | translate | optional | 缺失时按全量翻译降级 |

## Methodology Guidance (not steps)

LLM should apply these principles, in whatever order makes sense:

- **Breadth first, depth second**: Scan directories before reading file internals
- **Infrastructure before business**: Understand the runtime foundation before business logic
- **Never skip by name**: Can't guess importance from filename — sample-read first
- **Quiz validation**: After reading a key file, ask 3 self-check questions to verify understanding
- **Config is code**: Configuration files may contain business logic
- **Cross-cutting first**: Middleware, auth, logging affect everything — understand early

## Specialization Guidance

LLM specializes discovery based on project type:

| Project Type | Discovery Focus |
|-------------|----------------|
| Monolith | One pass, all layers |
| Microservices | Per-service discovery, then cross-service dependencies |
| Monorepo | Per-package/workspace, shared dependencies |
| Mobile app | Platform-specific patterns, offline data layer |
| Game | Asset pipeline, game loop, state management, config tables |
| SDK/Library | Public API surface, test suite, documentation, examples |

## Knowledge References

### Phase-Specific:
- experience-map-schema.md: understand target schema for downstream consumption
- governance-styles.md §Operation-Profiles: identify role operation patterns during discovery

## Composition Hints

### Single Node (default)
For monoliths and small-to-medium projects.

### Split into Multiple Nodes
For microservices: one discovery node per service.
For monorepos: one discovery node per package/workspace.

### Merge with Another Capability
For very simple projects (< 20 files): merge discovery + product-analysis into a single node.
