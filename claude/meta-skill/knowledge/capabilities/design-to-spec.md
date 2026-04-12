# Design-to-Spec Capability

> Convert product concept and design artifacts into technical specifications
> consumable by implementation nodes. Bridges the gap between "what to build"
> and "how to build it".

## Goal

Transform product-concept.json, experience-map, and infrastructure decisions into
concrete technical specifications: API endpoint definitions, database schemas, and
communication protocol specs. These become the single source of truth that all
implementation nodes consume via Context Pull.

## Prerequisites

1. product-concept.json exists (concept crystallization complete)
2. Experience map exists (optional but improves spec quality)
3. infra-design.json exists (optional — determines protocol choices)

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `api-spec.json` | API endpoint definitions: routes, methods, request/response schemas, auth requirements |
| `db-schema.md` | Database table/collection design: fields, types, relations, indexes, constraints |

### Optional Outputs

| Output | When |
|--------|------|
| `protocol-spec.md` | Realtime communication protocol: message types, event formats, connection lifecycle. Only when project uses WebSocket/gRPC streaming/SSE. |

### Required Quality

- Every entity in product-concept has corresponding DB tables/collections
- Every user-facing operation in experience-map has a corresponding API endpoint
- Request/response schemas have concrete field names and types (not "user object")
- API authentication requirements are specified per endpoint (public / auth required / role-restricted)
- DB indexes match the expected query patterns from the API spec

## Interaction Mode

**Key design decisions MUST be presented to the user for review before finalizing specs.**

Not every endpoint needs user confirmation — only the decisions that shape the
architecture and are hard to change later. LLM identifies and presents these as
structured selection questions.

### What requires user review:

**1. Core entity model (data structure)**
- Entity relationship choices: "订单和商品是多对多（订单行模式）还是嵌套文档？"
- State machine design: "订单状态流转：pending → paid → shipped → delivered → completed，退款从哪些状态可以触发？"
- Soft-delete vs hard-delete: "用户数据删除策略：逻辑删除（保留记录）还是物理删除（GDPR 合规）？"
- Polymorphism strategy: "通知类型（系统/订单/社交）用单表+type字段 还是 分表？"

**2. API architecture decisions**
- Resource naming & granularity: "商品搜索是 GET /products?q= 还是独立的 POST /search？"
- Batch vs single operations: "批量导入用单条循环还是 bulk endpoint？"
- Pagination strategy: "列表分页用 offset/limit 还是 cursor-based？（数据量大时 offset 性能差）"
- Auth boundary: "管理员操作走同一套 API 加权限 还是 独立的 /admin/ 路由？"

**3. Cross-module integration patterns**
- Sync vs async: "支付回调是同步等待还是 webhook 异步通知？"
- Data consistency: "跨服务数据一致性用分布式事务 还是 最终一致（saga）？"
- Event schema: "事件格式用 CloudEvents 标准 还是自定义 JSON？"

### How to present:

For each key decision, present as:
```
[决策点] 订单状态机设计

  a) 线性流转：pending → paid → shipped → delivered
     适合：简单电商，退款走独立流程
     
  b) DAG 流转：允许 paid → refunded, shipped → returned → refunded
     适合：有售后流程的平台，状态更复杂但覆盖真实场景
     
  c) 事件溯源：不存储状态，从事件流推导当前状态
     适合：需要完整审计轨迹、时间旅行查询

你的场景更适合哪个？
```

### When to skip:
- CRUD 标准实现（无争议的 REST 资源端点）
- 框架约定（如 Rails/Django 的默认模型结构）
- 已在 tech-architecture.json 中决定的事项

## Methodology Guidance (not steps)

- **Entity-first schema design**: Extract entities from product-concept → define DB tables → derive API endpoints from CRUD + business operations on those entities
- **API contract first**: Define the interface before implementation — consumers (web/mobile) and producers (backend) code against the same spec
- **Protocol from interactions**: For each realtime interaction in experience-map (chat, notifications, presence), define the message type, direction (client→server / server→client / bidirectional), and payload schema
- **Version strategy**: API routes use version prefix (e.g., `/v1/`). DB migrations use sequential numbering.
- **Consistency check**: Every API endpoint that writes data must correspond to a DB table. Every DB table should be reachable from at least one API endpoint.

## Downstream Consumers

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `api-spec.json` | `endpoints[]` | translate (implement nodes) | required | Implement nodes need to know which endpoints to build |
| `api-spec.json` | `endpoints[].request_schema`, `response_schema` | demo-forge | required | Demo-forge constructs API requests from schema definitions |
| `db-schema.md` | table definitions | translate (implement nodes) | required | Implement nodes need the data model to write ORM/migration code |
| `protocol-spec.md` | message types | translate (implement nodes) | optional | Only realtime projects need protocol implementation |

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Upstream-Baseline-Validation: spec must be consistent with product-concept
- defensive-patterns.md: error response schemas, pagination patterns

## Composition Hints

### Single Node (default)
One design-to-spec node outputs all technical specifications for the project.

### Split by Service
For monorepo with multiple services: spec-user-service, spec-messaging-service, spec-payment-service.

### Split by Role
For multi-role platforms (e.g., buyer + seller + admin): spec-buyer-api, spec-seller-api, spec-admin-api. Each role sees different endpoints, different data, and different permissions. A single api-spec.json may become unwieldy.

### Skip Entirely
When goals do not include create or rebuild (existing code already has implicit specs).
When translating between stacks (source code IS the spec).
