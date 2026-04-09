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
