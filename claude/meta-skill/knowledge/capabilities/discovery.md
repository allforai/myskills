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
