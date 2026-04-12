# Data Architecture Capability

> Design data layer: database selection, storage strategy, indexing,
> sharding, search infrastructure, migration, backup.
> Internal execution is LLM-driven — data architecture adapts to project entities and scale.

## Goal

Design the data persistence and retrieval layer. Select databases, define storage
strategies, plan indexes and search infrastructure, and produce a data architecture
document that implementation nodes consume.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `data-architecture.json` | Data layer decisions: DB choice, storage strategy, index plan, search infra |
| `data-architecture.md` | Human-readable data architecture document |

### Design Dimensions (LLM selects which apply)

| Dimension | Options to evaluate | Applies when |
|-----------|-------------------|-------------|
| Primary database | PostgreSQL / MySQL / MongoDB / DynamoDB / CockroachDB | Always (if product persists data) |
| Secondary/specialized DB | Redis / TimescaleDB / Neo4j / InfluxDB | Product has time-series, graph, or cache-heavy patterns |
| Storage strategy | Hot/warm/cold tiering / TTL-based expiry / archival | Product accumulates data over time |
| Index design | B-tree / GIN / GiST / composite / partial | Product has complex queries |
| Full-text search | Elasticsearch / Meilisearch / Typesense / PG tsvector | Product needs search beyond simple WHERE clauses |
| Vector search | pgvector / Pinecone / Weaviate / Qdrant | Product uses AI embeddings or semantic search |
| Sharding & partitioning | Horizontal sharding / table partitioning / read replicas | Product expects large data volume |
| Migration strategy | Framework migration tool / raw SQL versioned / schema-first | Always (if using relational DB) |
| Backup & recovery | Automated snapshots / point-in-time recovery / export | Production deployments |

### Required Quality

- Every entity from product-concept has a defined storage location
- Access patterns are identified (which queries are hot? which are analytical?)
- Index strategy matches the access patterns (not just "add indexes")
- Data lifecycle is defined (how long is data kept? what triggers archival/deletion?)

## Interaction Mode

**Search-driven selection questions (mandatory for each relevant dimension):**

For each design dimension that applies to this project, LLM MUST:

1. **WebSearch** 1-2 rounds: benchmarks, production case studies, and scale-specific comparisons for the candidate technologies
2. **Present 2-4 options** as a selection question, each with:
   - Technology name + one-line positioning (e.g., "Meilisearch — instant setup, <10M docs, typo-tolerant")
   - Evidence from search ("Benchmark: Meilisearch 50ms p99 at 5M docs vs ES 120ms with tuning")
   - Fit assessment for THIS project ("your entity count is ~500K, full-text on 3 fields — PG tsvector is sufficient, no external service needed")
3. **User selects** — LLM does NOT decide for the user
4. **"Other" response** → WebSearch with user's input → new selection question with refined options

**When to skip interaction:**
- Dimension has only one viable option (e.g., framework's built-in migration tool)
- User already specified the technology in bootstrap Step 1.5
- **Decision already made in product-concept tech-architecture sub-phase** — load `tech-architecture.json` and inherit those choices. Only ask about schema design, index strategy, and configuration details, not the technology selection itself.
- Project scale makes the choice obvious AND there's no meaningful tradeoff (state the decision with rationale, user can override)

## Methodology Guidance (not steps)

- **Access pattern driven**: Choose DB and design schema based on how data is queried, not how it's structured
- **CQRS consideration**: If read patterns differ greatly from write patterns, consider separating read/write models
- **Event Sourcing consideration**: If audit trail or temporal queries are important, consider event log as source of truth
- **Data lifecycle management**: Define retention policies upfront — storage costs compound
- **Migration safety**: Every schema change must be backward-compatible or have a rollback plan

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Upstream-Baseline-Validation: data schema consistency checks

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `data-architecture.json` | DB choice, storage strategy | translate (implement nodes) | required | 实现需要知道用什么数据库和存储策略来写 ORM/migration |
| `data-architecture.json` | index plan | design-to-spec | optional | db-schema.md 生成时参考索引规划 |
| `data-architecture.json` | search infrastructure | translate (implement nodes) | optional | 搜索相关实现需要知道用 ES 还是 PG tsvector |

## Composition Hints

### Single Node (default)
One data-architecture node covers all data layer decisions.

### Merge with Infrastructure
For single-database projects: merge data decisions into infra-design node.

### Skip Entirely
For stateless tools, CLI utilities, or projects where data layer is already defined and not changing.
