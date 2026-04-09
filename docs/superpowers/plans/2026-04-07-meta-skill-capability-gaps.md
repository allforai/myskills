# Meta-Skill Capability Gaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 4 new capabilities + 1 domain knowledge file and fix 4 protocol issues in bootstrap.md and ui-design.md to close coverage gaps found in Telegram App thought test.

**Architecture:** New files follow existing lightweight capability format (~60-80 lines each). Bootstrap.md modifications are surgical insertions at specific anchoring points. No orchestrator or diagnosis protocol changes needed.

**Tech Stack:** Markdown files only (no code changes).

---

## File Structure

### New Files (5)

| File | Responsibility |
|------|---------------|
| `claude/meta-skill/knowledge/capabilities/infra-design.md` | Infrastructure architecture capability: realtime, queues, storage, CDN, push |
| `claude/meta-skill/knowledge/capabilities/security-design.md` | Security architecture capability: auth, encryption, rate limiting, OWASP |
| `claude/meta-skill/knowledge/capabilities/data-architecture.md` | Data architecture capability: DB selection, indexing, sharding, search |
| `claude/meta-skill/knowledge/capabilities/design-to-spec.md` | Concept-to-technical-spec capability: API spec, DB schema, protocol spec |
| `claude/meta-skill/knowledge/domains/social-messaging.md` | IM domain knowledge: message sync, read receipts, presence, E2E encryption |

### Modified Files (2)

| File | Changes |
|------|---------|
| `claude/meta-skill/skills/bootstrap.md` | 4 insertions: Node Scope Self-Check, Cross-Module Stitch, State Machine rename+expand, Step 1.5 infra questions |
| `claude/meta-skill/knowledge/capabilities/ui-design.md` | 1 insertion: interaction-spec.md in Optional Outputs |

---

### Task 1: Create infra-design capability

**Files:**
- Create: `claude/meta-skill/knowledge/capabilities/infra-design.md`

- [ ] **Step 1: Write the capability file**

```markdown
# Infrastructure Design Capability

> Design infrastructure architecture: realtime communication, message queues,
> object storage, CDN, push notifications, caching, load balancing.
> Internal execution is LLM-driven — infra choices adapt to project scale and requirements.

## Goal

Design the infrastructure layer that supports the application. Select appropriate
technologies for each concern, define integration patterns, and produce an
infrastructure architecture document that implementation nodes consume.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `infra-design.json` | Infrastructure decisions: technology choices, configuration requirements, integration patterns |
| `infra-design.md` | Human-readable infrastructure architecture document |

### Design Dimensions (LLM selects which apply)

| Dimension | Options to evaluate | Applies when |
|-----------|-------------------|-------------|
| Realtime communication | WebSocket / gRPC streaming / SSE / MQTT / Long polling | Product has live updates, chat, collaboration |
| Message queue | NATS / Kafka / RabbitMQ / Redis Pub-Sub / SQS | Product has async workflows, event-driven processing |
| Object storage | S3 / MinIO / GCS / Azure Blob | Product handles file uploads, media, documents |
| CDN & static assets | CloudFront / Cloudflare / Fastly / self-hosted | Product serves static content or media at scale |
| Push notifications | APNs / FCM / Web Push / OneSignal | Product has mobile apps or browser notifications |
| Caching | Redis / Memcached / application-level cache | Product has hot data or expensive queries |
| Load balancing | Nginx / HAProxy / cloud LB / service mesh | Product expects concurrent users |
| Service discovery | DNS / Consul / Kubernetes / etcd | Product has multiple services |

### Required Quality

- Every dimension relevant to the project has an explicit technology choice with rationale
- Choices are justified by project scale, team expertise, and operational complexity
- Integration patterns between components are defined (how does the API talk to the queue? how does the queue trigger the worker?)
- Development vs production configuration differences are noted

## Methodology Guidance (not steps)

- **Start from product requirements**: Read product-concept features that imply infra needs (realtime, notifications, file handling, search)
- **Right-size**: Don't recommend Kafka for a project that sends 10 messages/day. Match infra to expected scale.
- **12-Factor App principles**: Config in environment, stateless processes, disposable instances
- **CAP theorem awareness**: For distributed components, make explicit tradeoff (consistency vs availability)
- **Dev parity**: Infrastructure should be reproducible locally (Docker Compose, local emulators)

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Maximum-Realism: use real services when credentials exist
- defensive-patterns.md: fallback strategies when infra components are unavailable

## Composition Hints

### Single Node (default)
One infra-design node covers all infrastructure decisions for the project.

### Split by Subsystem
For microservice architectures: infra-realtime, infra-storage, infra-messaging as separate nodes.

### Merge with Another Capability
For simple projects with one database and no realtime: merge infra decisions into the setup-env node.

### Skip Entirely
For static sites, CLI tools, pure frontend apps with no backend, or SDK/library projects.
```

- [ ] **Step 2: Verify file exists and follows capability format**

Run: `head -5 claude/meta-skill/knowledge/capabilities/infra-design.md`
Expected: Shows the `# Infrastructure Design Capability` header and description line.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/capabilities/infra-design.md
git commit -m "feat(meta-skill): add infra-design capability (H1, H3)"
```

---

### Task 2: Create security-design capability

**Files:**
- Create: `claude/meta-skill/knowledge/capabilities/security-design.md`

- [ ] **Step 1: Write the capability file**

```markdown
# Security Design Capability

> Design security architecture: authentication, authorization, encryption,
> rate limiting, input validation, key management.
> Internal execution is LLM-driven — security posture adapts to project threat model.

## Goal

Identify security requirements, perform lightweight threat modeling, select
appropriate security mechanisms, and produce a security architecture document
that implementation and verification nodes consume.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `security-design.json` | Security decisions: auth scheme, encryption approach, threat mitigations |
| `security-design.md` | Human-readable security architecture document |

### Design Dimensions (LLM selects which apply)

| Dimension | Options to evaluate | Applies when |
|-----------|-------------------|-------------|
| Authentication | JWT / OAuth2 / SSO / 2FA / Passkeys / API keys | Product has user accounts |
| Authorization | RBAC / ABAC / permission matrix / row-level security | Product has multiple roles |
| Transport encryption | TLS / mTLS | Always (HTTPS minimum) |
| End-to-end encryption | Signal Protocol / MLS / custom | Product handles sensitive private communication |
| Data-at-rest encryption | DB-level / application-level / KMS-managed | Product stores PII or financial data |
| Rate limiting | Token bucket / sliding window / per-user / per-IP | Product has public API or user-facing endpoints |
| Input validation | Schema validation / sanitization / parameterized queries | Always (OWASP Top 10) |
| Key management | Environment vars / HashiCorp Vault / cloud KMS / keychain | Product uses API keys, encryption keys, or secrets |

### Required Quality

- Threat model covers at least the STRIDE categories relevant to the project
- Every authentication flow has a defined token lifecycle (issue, refresh, revoke)
- Sensitive data paths are identified (PII, credentials, payment data) with protection measures
- OWASP Top 10 mitigations are addressed for the project's tech stack

## Methodology Guidance (not steps)

- **STRIDE threat modeling**: For each component, consider Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege
- **OWASP Top 10**: Map to the project's specific tech stack (e.g., SQL injection for relational DB, XSS for web frontend)
- **Zero Trust principle**: Don't trust internal networks — authenticate and authorize every request
- **Least privilege**: Every component gets minimum permissions needed
- **Defense in depth**: Multiple layers of protection, not a single perimeter

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Safety: security-related safety rules
- defensive-patterns.md: fallback and error handling that doesn't leak information

## Composition Hints

### Single Node (default)
One security-design node covers threat modeling + mechanism selection for the entire project.

### Merge with Infrastructure
For simple projects (single web app, no E2E encryption): merge security decisions into infra-design.

### Skip Entirely
For internal tools with no user data, local-only CLI tools, or prototype/hackathon projects where security is explicitly deferred.
```

- [ ] **Step 2: Verify file exists**

Run: `head -5 claude/meta-skill/knowledge/capabilities/security-design.md`
Expected: Shows the `# Security Design Capability` header.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/capabilities/security-design.md
git commit -m "feat(meta-skill): add security-design capability (H2)"
```

---

### Task 3: Create data-architecture capability

**Files:**
- Create: `claude/meta-skill/knowledge/capabilities/data-architecture.md`

- [ ] **Step 1: Write the capability file**

```markdown
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

## Composition Hints

### Single Node (default)
One data-architecture node covers all data layer decisions.

### Merge with Infrastructure
For single-database projects: merge data decisions into infra-design node.

### Skip Entirely
For stateless tools, CLI utilities, or projects where data layer is already defined and not changing.
```

- [ ] **Step 2: Verify file exists**

Run: `head -5 claude/meta-skill/knowledge/capabilities/data-architecture.md`
Expected: Shows the `# Data Architecture Capability` header.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/capabilities/data-architecture.md
git commit -m "feat(meta-skill): add data-architecture capability (M1)"
```

---

### Task 4: Create design-to-spec capability

**Files:**
- Create: `claude/meta-skill/knowledge/capabilities/design-to-spec.md`

- [ ] **Step 1: Write the capability file**

```markdown
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

### Skip Entirely
When goals do not include create or rebuild (existing code already has implicit specs).
When translating between stacks (source code IS the spec).
```

- [ ] **Step 2: Verify file exists**

Run: `head -5 claude/meta-skill/knowledge/capabilities/design-to-spec.md`
Expected: Shows the `# Design-to-Spec Capability` header.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/capabilities/design-to-spec.md
git commit -m "feat(meta-skill): add design-to-spec capability (H5)"
```

---

### Task 5: Create social-messaging domain knowledge

**Files:**
- Create: `claude/meta-skill/knowledge/domains/social-messaging.md`

- [ ] **Step 1: Write the domain knowledge file**

Follow the format established by `knowledge/domains/gaming.md`: sections for domain-specific design patterns, each with what/why/check structure.

```markdown
# Social Messaging Domain Knowledge

> 即时通讯领域的产品设计知识包。
> Bootstrap Step 2.2 加载本文件 → Step 3 用本文件特化产品设计 + 实现 + 验证节点。
> 触发条件：business_domain = social 且产品愿景包含 IM/聊天/消息/通讯关键词。

---

## 一、IM 特有的设计模式

标准产品设计覆盖通用功能（CRUD、角色、旅程），但 IM 有独特的技术和产品模式，
需要专项引导。以下每个模式包含三部分：what（是什么）、why（为什么 IM 需要）、
check（bootstrap 检查项）。

### 1. 消息同步协议

**What:** 客户端如何获取新消息。两种主流方案：
- Timeline-based sync：服务端维护全局递增序列号，客户端同步到最新序列号
- Cursor-based pagination：按时间戳或消息 ID 分页拉取

**Why:** IM 的核心体验是"发出的消息对方立即看到"。同步协议决定延迟和可靠性。

**Check:**
- 产品概念中有"聊天"/"消息"功能 → workflow 必须包含 realtime infra 节点
- 选择 WebSocket/gRPC streaming/SSE 之一作为推送通道
- 定义离线消息缓存策略（客户端存储 vs 每次重新拉取）

### 2. 消息状态流转

**What:** 消息从发送到已读的状态机：
```
composing → sent → delivered → read
              ↓
           failed → retry
```

**Why:** 用户需要知道消息是否送达、对方是否已读。状态不全 = 用户焦虑。

**Check:**
- 每个状态有对应的 UI 指示器（✓ sent / ✓✓ delivered / 蓝色✓✓ read）
- 状态转换有对应的 API/WebSocket 事件
- 失败状态有重试机制和用户可见的错误提示

### 3. 在线状态与 Last Seen

**What:** 实时显示联系人是否在线，离线时显示最后活跃时间。

**Why:** 在线状态影响用户是否选择发消息。也是"社交存在感"的核心指标。

**Check:**
- 在线状态有更新机制（心跳/WebSocket 连接状态）
- Last seen 有隐私控制（可关闭/只对联系人可见）
- 状态变化有推送给相关联系人的机制

### 4. 已读回执

**What:** 通知发送者消息已被阅读。单聊直接标记，群聊需要聚合（3 人已读）。

**Why:** 已读回执是 IM 的差异化特性（WhatsApp 蓝勾 vs 微信无已读）。

**Check:**
- 单聊和群聊的已读逻辑是否分开处理
- 群聊已读是否有聚合显示（"5 人已读" 而非逐个列出）
- 用户是否可以关闭已读回执（隐私设置）

### 5. 输入指示器

**What:** 显示对方"正在输入..."的实时状态。

**Why:** 减少等待焦虑，增加对话的"在场感"。

**Check:**
- 输入事件通过 WebSocket 推送，不是轮询
- 有防抖机制（不是每次按键都发事件）
- 超时自动消失（对方停止输入 N 秒后隐藏）

### 6. 群成员管理

**What:** 群组的角色层级和权限矩阵：
```
owner → admin → member → restricted
  ↑        ↑        ↑
  全部权限   管理成员   只能发消息
```

**Why:** 群组越大，管理复杂度越高。权限不清 = 混乱。

**Check:**
- 权限矩阵是否完整（谁能邀请/踢人/修改信息/删除消息/禁言）
- 权限转移是否安全（owner 转让、admin 撤销）
- 大群（>200 人）是否有特殊限制（禁止全员 @、限制发送频率）

### 7. 频道模型

**What:** 单向广播频道 vs 可讨论频道（Telegram 模式）。

**Why:** 频道是 IM 从"通讯工具"变成"信息平台"的关键功能。

**Check:**
- 频道与群组在数据模型上是否分离（不同实体 vs 同一实体 + type 字段）
- 订阅/取消订阅的机制
- 频道消息与私聊消息是否共享消息模型
- 频道是否支持评论/讨论区（关联群组模式）

### 8. Bot API 设计

**What:** 允许第三方开发者创建自动化 Bot 的 API 体系。

**Why:** Bot 生态是 Telegram 的核心竞争力。Bot API 设计影响生态活跃度。

**Check:**
- Bot 接收消息的方式（webhook vs long polling）
- 命令解析格式（/command@botname 模式）
- Bot 权限范围（能读什么/能做什么）
- Bot 消息与普通消息在 UI 上的区分

### 9. 端到端加密

**What:** 消息在发送端加密、接收端解密，服务器无法读取明文。

**Why:** 隐私保护。Telegram Secret Chat / Signal / WhatsApp 的核心卖点。

**Check:**
- 密钥交换协议（Diffie-Hellman / X3DH）
- 前向安全（每条消息用不同密钥，历史不可回溯）
- 群聊加密方案（MLS / Sender Keys）
- 加密消息的搜索限制（服务端无法索引加密内容）

### 10. 消息搜索

**What:** 按关键词、发送者、日期、媒体类型搜索历史消息。

**Why:** IM 消息量巨大，搜索是查找信息的关键手段。

**Check:**
- 搜索索引方案（全文搜索引擎 vs DB LIKE）
- 搜索范围（全局 / 按会话 / 按联系人）
- 多语言分词支持
- 加密消息是否可搜索（仅客户端本地搜索）

### 11. 媒体消息处理

**What:** 图片/视频/音频/文件的发送、存储、展示。

**Why:** 现代 IM 中媒体消息占比 >50%。处理不好 = 卡顿、流量浪费。

**Check:**
- 缩略图生成（服务端生成，客户端直接展示小图）
- 渐进式加载（先模糊图再清晰图）
- 大文件上传（分片上传、断点续传）
- 媒体过期策略（是否永久存储、容量限制）

### 12. 贴纸与表情系统

**What:** 贴纸包管理、自定义表情、Emoji 反应。

**Why:** 贴纸是 IM 的情感表达工具，也是商业化渠道。

**Check:**
- 贴纸包的安装/卸载/分享机制
- 自定义表情（用户上传的小图作为 emoji）
- 消息反应（对消息添加 emoji 反应而非回复）
- 贴纸消息与文本消息在消息模型中的统一处理

---

## 二、IM 对标准产品设计阶段的影响

| 标准阶段 | IM 领域补充 |
|---------|-----------|
| user-role-definition | 增加 Bot 开发者角色；多客户端声明（Web + iOS + Android）是标配 |
| concept-crystallization | 增加自适应系统声明：消息状态流转、在线状态同步是业务状态机 |
| ui-design | 增加 interaction-spec：输入指示器动画、消息气泡入场、滑动回复手势 |
| feature-gap | 增加协议层检查：WebSocket 消息类型是否覆盖所有交互 |
| demo-forge | 数据需要时间序列连贯性：对话有上下文，不能随机填充 |

---

## 三、IM 对验证层的影响

| 标准验证 | IM 领域补充 |
|---------|-----------|
| product-verify | 增加 V8 实时验证：消息 A 发送 → B 端 <1s 内收到 |
| quality-checks | 增加协议一致性检查：API + WebSocket + 客户端消息类型枚举是否对齐 |
| demo-forge | 验证双向通信：A 发消息 → B 收到 → B 回复 → A 收到 |

---

## 四、IM 项目的典型节点图补充

标准的 "create" 流程会生成 product-concept → implement → verify 链路。
IM 项目额外需要：

| 补充节点 | 对应 capability | 理由 |
|---------|----------------|------|
| infra-realtime | infra-design | WebSocket/推送基础设施 |
| security-e2e-encryption | security-design | 端到端加密（如果产品需要） |
| design-message-protocol | design-to-spec | 消息类型、事件格式定义 |
| implement-bot-api | (project-specific) | Bot 平台是独立子系统 |
| cross-module-stitch | (stitch) | API ↔ Web ↔ Mobile 消息类型对齐 |
```

- [ ] **Step 2: Verify file exists and has all 12 patterns**

Run: `grep -c "^### " claude/meta-skill/knowledge/domains/social-messaging.md`
Expected: `12` (12 design patterns in section 一)

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/domains/social-messaging.md
git commit -m "feat(meta-skill): add social-messaging domain knowledge (M5)"
```

---

### Task 6: Add Node Scope Self-Check to bootstrap.md

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:625` (after State Machine Check ends at line 625, before `### 3.2 Write workflow.json` at line 626)

- [ ] **Step 1: Insert Node Scope Self-Check block**

Insert the following block between line 625 (`If behavior is supposed to adapt but always reads a hardcoded default → broken mapping.`) and line 626 (`### 3.2 Write workflow.json`):

```markdown

**Node Scope Self-Check (MANDATORY):**
After designing the node graph, LLM MUST review each implementation node and ask:
"Can a single subagent complete this node's goal in one execution with high quality?"

Signs that a node needs splitting:
- Node goal contains "and" connecting unrelated subsystems
  (e.g., "implement user auth AND messaging AND file storage")
- Node covers > 1 independent domain with no shared data model
- Estimated output exceeds what one subagent can reliably produce

If uncertain, split. Two focused nodes are better than one overloaded node.
Each split node gets its own node-spec, exit_artifacts, and verification.

```

- [ ] **Step 2: Verify the insertion is in the correct location**

Run: `grep -n "Node Scope Self-Check" claude/meta-skill/skills/bootstrap.md`
Expected: Shows the line number, which should be between the state machine check and `### 3.2`.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): add Node Scope Self-Check to bootstrap Step 3.1 (H4)"
```

---

### Task 7: Add Cross-Module Stitch to bootstrap.md

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:914` (after Enum Exhaustiveness Check ends at line 914, before `### 3.5 Coverage Self-Check` at line 916)

- [ ] **Step 1: Insert Cross-Module Stitch block**

Insert the following block after line 914 (`}`) — the closing of the enum_coverage JSON example — and before line 916 (`### 3.5 Coverage Self-Check`):

```markdown

**Cross-Module Stitch Node (MANDATORY for multi-module projects):**
When the project has separate API and client modules (web/mobile), the workflow
MUST include a `cross-module-stitch` node after all implement + intra-module
stitch nodes complete, BEFORE compile-verify.

This extends the intra-module stitch (above) to cover cross-module integration.
Intra-module stitch catches missing imports within one codebase; cross-module
stitch catches API contract mismatches between separate codebases.

The cross-module stitch node's job:
1. Read API node's exit artifacts (route definitions, response schemas)
2. Read each client node's exit artifacts (API call sites, type definitions)
3. For each API endpoint, verify all consuming clients:
   - Parse the response correctly (field names, types, nesting)
   - Handle all response states (success, error, empty, paginated)
   - Send correct request format (query params, body schema, auth headers)
4. For each WebSocket/realtime message type (if applicable):
   - Server sends it → all clients handle it
   - Client sends it → server processes it
5. Fix mismatches: update client code to match API contract
6. Produce cross-module-stitch-report.json

```
Parallel impl nodes → stitch-{module} → cross-module-stitch → compile-verify → E2E
```

Exit artifact: `.allforai/bootstrap/cross-module-stitch-report.json`

**Node-spec for cross-module stitch should include:**
- The API node's exit artifacts (route/schema definitions)
- All client nodes' exit artifacts (API call sites)
- design-to-spec artifacts if available (api-spec.json as reference contract)
- WebSocket/protocol message types (if applicable)

```

- [ ] **Step 2: Verify the insertion is in the correct location**

Run: `grep -n "Cross-Module Stitch" claude/meta-skill/skills/bootstrap.md`
Expected: Shows the line number, between enum coverage and Coverage Self-Check.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): add Cross-Module Stitch to bootstrap Step 3.1 (H6)"
```

---

### Task 8: Generalize State Machine Check in bootstrap.md

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:523-529` (Adaptive State Machine Check header and scope description)

- [ ] **Step 1: Rename header and expand scope**

Replace the current header and scope block at lines 523-529:

```markdown
**Adaptive State Machine Check (MANDATORY):**
> **Scope**: This check applies to EXISTING CODE — verifying that code already in the
> codebase correctly implements the state machine (state storage, transitions, behavior
> mappings). It runs during rebuild/translate goals when code exists. For NEW projects
> (goal=create), this check is N/A — Step 3.5 Level 4 handles coverage planning instead.

After pipeline checks, LLM MUST check for **adaptive state machines** defined
```

With:

```markdown
**State Machine Completeness Check (MANDATORY):**
> **Scope**: This check applies to EXISTING CODE — verifying that code already in the
> codebase correctly implements state machines (state storage, transitions, behavior
> mappings). It runs during rebuild/translate goals when code exists. For NEW projects
> (goal=create), this check is N/A — Step 3.5 Level 4 handles coverage planning instead.

This check covers TWO categories of state machines:

**Category 1: Business State Machines (deterministic)**
Systems with well-defined states and transition rules driven by system events.
Examples:
- Message delivery: sent → delivered → read
- Order lifecycle: created → paid → shipped → delivered → completed
- User status: online → idle → offline (with last_seen timestamp)
- Group membership: invited → member → admin → owner
- Content moderation: pending → approved / rejected

**Category 2: Adaptive State Machines (probabilistic)**
Systems where state evolves based on user behavior and influences system behavior.
Examples:
- Learning proficiency: beginner → intermediate → advanced
- Recommendation preferences: tracks interaction patterns → personalizes content
- Engagement scoring: activity frequency → notification cadence

After pipeline checks, LLM MUST check for **state machines** (both categories) defined
```

- [ ] **Step 2: Verify the rename**

Run: `grep -n "State Machine Completeness Check\|Adaptive State Machine Check" claude/meta-skill/skills/bootstrap.md`
Expected: Shows "State Machine Completeness Check" at the correct line. No remaining "Adaptive State Machine Check" on that line (note: Step 3.5 Level 4 may still reference "Adaptive" — that's a different section and is correct to keep since Level 4 specifically handles adaptive systems in product-concept.json).

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): generalize State Machine Check to cover business + adaptive (M4)"
```

---

### Task 9: Add infra questions to Step 1.5 in bootstrap.md

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:185` (after business domain question, before the closing ``` of the "no code" template)

- [ ] **Step 1: Insert optional infra questions**

Insert the following block between line 185 (`   a) 电商  b) 金融  c) 医疗  d) SaaS  e) 社交  f) 游戏  g) 其他：___`) and line 186 (the closing ``` of the template):

```markdown

5. 基础设施需求（可选，复杂项目建议回答）：
   实时通信：___（如 WebSocket/gRPC/SSE/无）
   消息队列：___（如 Kafka/NATS/Redis Pub-Sub/无）
   文件存储：___（如 S3/MinIO/本地/无）
   搜索引擎：___（如 Elasticsearch/Meilisearch/无）
```

- [ ] **Step 2: Verify the insertion**

Run: `grep -n "基础设施需求" claude/meta-skill/skills/bootstrap.md`
Expected: Shows the line number within the "no code" template block.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): add optional infra questions to Step 1.5 (M3)"
```

---

### Task 10: Add interaction-spec to ui-design capability

**Files:**
- Modify: `claude/meta-skill/knowledge/capabilities/ui-design.md:27-29` (Optional Outputs table)

- [ ] **Step 1: Add interaction-spec.md row**

Replace the current Optional Outputs section at lines 27-29:

```markdown
### Optional Outputs

| Output | When |
|--------|------|
| `preview/*.html` | Interactive HTML previews (if user wants visual validation) |
| `art-direction.md` | For games or visually-driven products |
```

With:

```markdown
### Optional Outputs

| Output | When |
|--------|------|
| `preview/*.html` | Interactive HTML previews (if user wants visual validation) |
| `art-direction.md` | For games or visually-driven products |
| `interaction-spec.md` | For products with significant dynamic interactions (IM, collaborative tools, games). Covers: transition animations, gesture interactions (swipe-to-reply, long-press menus), real-time update patterns (typing indicators, live cursors), micro-interactions (message send animation, pull-to-refresh), loading/skeleton states with timing. |
```

- [ ] **Step 2: Verify the addition**

Run: `grep "interaction-spec" claude/meta-skill/knowledge/capabilities/ui-design.md`
Expected: Shows the new row with `interaction-spec.md`.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/capabilities/ui-design.md
git commit -m "feat(meta-skill): add interaction-spec.md to ui-design Optional Outputs (M2)"
```

---

### Task 11: Final verification

- [ ] **Step 1: Verify all 5 new files exist**

Run: `ls -la claude/meta-skill/knowledge/capabilities/infra-design.md claude/meta-skill/knowledge/capabilities/security-design.md claude/meta-skill/knowledge/capabilities/data-architecture.md claude/meta-skill/knowledge/capabilities/design-to-spec.md claude/meta-skill/knowledge/domains/social-messaging.md`
Expected: All 5 files exist.

- [ ] **Step 2: Count total capabilities (should be 23)**

Run: `ls claude/meta-skill/knowledge/capabilities/*.md | wc -l`
Expected: `23` (was 19 + 4 new = 23)

- [ ] **Step 3: Count total domain files (should be 5)**

Run: `ls claude/meta-skill/knowledge/domains/*.md | wc -l`
Expected: `5` (was 4 + 1 new = 5)

- [ ] **Step 4: Verify bootstrap.md has all 4 insertions**

Run: `grep -c "Node Scope Self-Check\|Cross-Module Stitch Node\|State Machine Completeness Check\|基础设施需求" claude/meta-skill/skills/bootstrap.md`
Expected: `4`

- [ ] **Step 5: Verify ui-design.md has interaction-spec**

Run: `grep -c "interaction-spec" claude/meta-skill/knowledge/capabilities/ui-design.md`
Expected: `1`
