# Meta-Skill Capability Gaps 改进设计

> 基于 Telegram App 全量思维测试，修复 meta-skill 在基础设施、安全、实时通信、
> 技术规格转换、节点粒度、跨模块集成等方面的覆盖空白。

## 问题

用 Telegram 级别 IM 应用作为思维测试用例，对 meta-skill 全量 pipeline
做 dry-run 模拟。发现 6 个 High + 6 个 Medium 问题：

### High Severity

| # | 问题 | 根因 | 影响范围 |
|---|------|------|---------|
| H1 | 缺少基础设施架构 capability | 19 个 capability 聚焦产品+代码层，无架构基础设施层 | 需要实时通信/消息队列/对象存储的项目 |
| H2 | 缺少安全架构 capability | 安全只在 quality-checks 做表层检查 | 需要加密/认证/安全审计的项目 |
| H3 | 缺少实时通信 capability | IM/协作/游戏的核心需求无方法论覆盖 | 社交、协作、游戏类项目 |
| H4 | implement 节点粒度无强制拆分规则 | bootstrap 说 "LLM decides" 但无上界 | 复杂项目可能产生过大单节点 |
| H5 | 产品设计→技术规格断层 | 无 design-to-spec capability | 所有 create 目标的项目 |
| H6 | 跨模块集成缺少 stitch 机制 | stitch 只覆盖同模块内并行节点 | 所有多模块项目 |

### Medium Severity

| # | 问题 | 根因 |
|---|------|------|
| M1 | 缺少数据架构 capability | 存储策略/索引/分片无指导 |
| M2 | ui-design 缺少动效规格 | output 只有静态 screen spec |
| M3 | Step 1.5 技术栈问答缺少中间件/协议决策 | 模板固定，不可扩展 |
| M4 | Adaptive State Machine 偏向推荐系统 | 示例和术语以学习/个性化为主 |
| M5 | 缺少 domains/social-messaging.md | knowledge/domains/ 下无 IM 领域文件 |
| M6 | demo-forge 缺少「启动服务」前置步骤 | 隐含在 demo-forge 中但不明确 |

## 设计决策

| # | 决策 | 选择 | 原因 |
|---|------|------|------|
| D1 | 新 capability 风格 | 轻量参考型（~60-80行） | LLM 知识充足领域只需方法论框架，不需详细子阶段 |
| D2 | design-to-spec 定位 | 独立 capability | 方向与 product-analysis 相反（concept→spec vs code→understanding），输入不同（concept vs code），CLAUDE.md 已预留 `/design-to-spec` 位置 |
| D3 | 跨模块 stitch | 扩展 stitch 触发定义 | 修复成本远低于 E2E 发现后回溯 |
| D4 | 节点粒度 | 启发式自检 | 硬阈值难以定义合理 N，LLM 按复杂度自判更灵活 |
| D5 | 状态机检查 | 统一为通用状态机完整性检查 | 确定性业务状态机和自适应状态机的检查方法论一致（状态定义→转换→行为映射） |

## 方案

### 线 A：新增文件

#### A1: `capabilities/infra-design.md` — 基础设施架构

解决 H1。轻量参考型 capability，提供基础设施设计的方法论框架。

覆盖领域：
- 实时通信（WebSocket/gRPC/SSE/MQTT 选型）
- 消息队列（NATS/Kafka/RabbitMQ 选型）
- 对象存储（S3/MinIO/GCS 选型）
- CDN 与静态资源分发
- 推送服务（APNs/FCM/Web Push）
- 缓存层（Redis/Memcached）
- 负载均衡与服务发现

方法论锚点：12-Factor App、CAP 定理、Infrastructure as Code

组合提示：
- 单节点（默认）：一个 infra-design 节点覆盖全部基础设施决策
- 按子系统拆分：对于微服务架构，拆为 infra-realtime、infra-storage、infra-messaging
- 跳过：纯静态站点、CLI 工具

#### A2: `capabilities/security-design.md` — 安全架构

解决 H2。轻量参考型 capability。

覆盖领域：
- 认证方案（JWT/OAuth2/SSO/2FA/Passkeys）
- 授权模型（RBAC/ABAC/权限矩阵）
- 传输加密（TLS/mTLS）
- 端到端加密（Signal Protocol/MLS）
- 数据加密（at-rest encryption）
- 速率限制与 DDoS 防护
- 输入校验与注入防护（OWASP Top 10）
- 密钥管理（Vault/KMS/环境变量）

方法论锚点：STRIDE 威胁建模、OWASP Top 10、零信任架构

组合提示：
- 单节点（默认）：一个 security-design 节点做威胁建模 + 方案选型
- 合并：对于简单项目，可合并入 infra-design
- 跳过：内部工具、无用户数据的 CLI

#### A3: `capabilities/data-architecture.md` — 数据架构

解决 M1。轻量参考型 capability。

覆盖领域：
- 数据库选型（关系型/文档/时序/图）
- 存储策略（热/温/冷分离）
- 索引设计（B-tree/倒排/全文搜索/向量）
- 分片与分区策略
- 数据迁移与版本管理
- 备份与恢复
- 搜索基础设施（Elasticsearch/Meilisearch/Typesense）

方法论锚点：CQRS/Event Sourcing（适用时）、数据生命周期管理

组合提示：
- 单节点（默认）：一个 data-architecture 节点做全部数据层设计
- 合并：对于单数据库项目，可合并入 infra-design
- 跳过：无持久化的工具

#### A4: `capabilities/design-to-spec.md` — 产品概念→技术规格

解决 H5。轻量参考型 capability。

目标：将产品概念转化为实现可消费的技术规格，填补 concept-crystallization 和
implement 之间的断层。

输入：
- product-concept.json（功能定义、角色、业务流程）
- experience-map（如果存在）
- infra-design 产物（如果存在）

输出：
| Output | What |
|--------|------|
| `api-spec.json` | API 端点定义（路由、方法、请求/响应 schema）|
| `db-schema.md` | 数据库表/集合设计、关系、索引 |
| `protocol-spec.md` | 实时通信协议（WebSocket 消息类型、事件格式）— 仅当项目需要时 |

方法论指导：
- API 先行：先定义接口契约，再实现
- Schema 从实体推导：product-concept 中的实体 → 表设计
- 协议从交互推导：experience-map 中的实时交互 → 协议消息类型
- 版本策略：API 版本前缀、schema migration 编号

组合提示：
- 单节点（默认）：一个 design-to-spec 节点输出全部技术规格
- 按模块拆分：对 monorepo 可按服务拆分（spec-user-service、spec-messaging-service）
- 跳过：goals 不包含 create/rebuild 时

Downstream Consumers：
| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `api-spec.json` | `endpoints[]` | translate (implement nodes) | required | implement 节点需要知道要实现哪些端点 |
| `api-spec.json` | `endpoints[].request_schema`, `response_schema` | demo-forge | required | demo-forge 按 schema 构造 API 请求 |
| `db-schema.md` | 表定义 | translate (implement nodes) | required | 实现需要知道数据模型 |
| `protocol-spec.md` | 消息类型 | translate (implement nodes) | optional | 仅实时通信项目需要 |

#### A5: `domains/social-messaging.md` — IM 领域知识

解决 M5。领域知识文件，当 bootstrap 检测 business_domain = social 且
产品愿景包含 IM/聊天/消息关键词时加载。

覆盖的 IM 特有设计模式：
- 消息同步协议（timeline-based sync、cursor-based pagination）
- 消息状态流转（sent → delivered → read）
- 在线状态与 last seen 同步
- 已读回执（单聊 vs 群聊差异）
- 输入指示器（typing indicator）
- 群成员管理（角色层级、权限矩阵）
- 频道模型（广播 vs 讨论、订阅/取消订阅）
- Bot API 设计模式（webhook vs long polling、命令解析）
- 端到端加密（密钥交换、前向安全）
- 消息搜索（全文索引、按发送者/日期/媒体类型过滤）
- 媒体消息处理（缩略图生成、渐进式加载、过期策略）
- 贴纸/表情系统（贴纸包管理、自定义表情）

每个模式包含：what（是什么）+ why（为什么 IM 需要）+ check（bootstrap 检查项）。

### 线 B：修改现有文件

#### B1: 节点粒度启发式自检（修改 `skills/bootstrap.md` Step 3.1）

解决 H4。在 Step 3.1 末尾、3.2 之前插入：

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

#### B2: 跨模块 stitch 扩展（修改 `skills/bootstrap.md`）

解决 H6。修改现有 Integration Stitch Node 段落，扩展触发条件：

当前触发条件：
> When 2+ implementation nodes run in parallel within the same module

扩展为：
> When 2+ implementation nodes run in parallel AND share interface contracts
> (API endpoints, WebSocket message types, shared data models).
> This includes both intra-module (files in same codebase) and cross-module
> (API ↔ client) integration.

新增 cross-module-stitch 描述：

```markdown
**Cross-Module Stitch Node (MANDATORY for multi-module projects):**
When the project has separate API and client modules (web/mobile), the workflow
MUST include a `cross-module-stitch` node after all implement + intra-module
stitch nodes complete, BEFORE compile-verify.

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

Exit artifact: `.allforai/bootstrap/cross-module-stitch-report.json`
```

#### B3: 状态机检查泛化（修改 `skills/bootstrap.md` Step 3.1）

解决 M4。将 Adaptive State Machine Check 重命名并扩展：

标题从：
> **Adaptive State Machine Check (MANDATORY):**

改为：
> **State Machine Completeness Check (MANDATORY):**

扩展 scope 描述，明确覆盖两类状态机：

```markdown
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
```

检查方法论不变（State Definition → Transitions → Behavior Mapping），
但示例扩展为包含两类。

#### B4: ui-design 动效规格（修改 `capabilities/ui-design.md`）

解决 M2。在 Required Outputs 表增加一行：

```markdown
### Optional Outputs

| Output | When |
|--------|------|
| `preview/*.html` | Interactive HTML previews (if user wants visual validation) |
| `art-direction.md` | For games or visually-driven products |
| `interaction-spec.md` | For products with significant dynamic interactions (IM, collaborative tools, games). Covers: transition animations, gesture interactions, real-time update patterns, micro-interactions, loading/skeleton states with timing. |
```

#### B5: Step 1.5 技术决策扩展（修改 `skills/bootstrap.md`）

解决 M3。在「无代码」分支的问答模板末尾增加可选部分：

```markdown
5. 基础设施需求（可选，复杂项目建议回答）：
   实时通信：___ （如 WebSocket/gRPC/SSE/无）
   消息队列：___ （如 Kafka/NATS/Redis Pub-Sub/无）
   文件存储：___ （如 S3/MinIO/本地/无）
   搜索引擎：___ （如 Elasticsearch/Meilisearch/无）
```

标记为「可选」，简单项目可跳过。bootstrap 在 Step 3 中会根据回答
（或缺失回答）决定是否生成 infra-design 节点。

## 不做的事

- 不改 orchestrator-template.md — 执行逻辑不变
- 不改 diagnosis.md — 诊断协议已经足够通用
- 不为新 capability 定义详细子阶段 — 轻量参考型只提供方法论框架
- 不增加 Step 1.5 的必填问题 — 用可选扩展避免简单项目负担
- 不处理 M6（demo-forge 启动服务前置步骤）— 这属于 runtime environment node 的职责，已由 Step 1.5.1 覆盖（bootstrap 会生成 setup-env 节点，该节点负责启动服务）

## 改动文件清单

| 文件 | 操作 | 解决问题 |
|------|------|---------|
| `claude/meta-skill/knowledge/capabilities/infra-design.md` | 新增 | H1, H3 |
| `claude/meta-skill/knowledge/capabilities/security-design.md` | 新增 | H2 |
| `claude/meta-skill/knowledge/capabilities/data-architecture.md` | 新增 | M1 |
| `claude/meta-skill/knowledge/capabilities/design-to-spec.md` | 新增 | H5 |
| `claude/meta-skill/knowledge/domains/social-messaging.md` | 新增 | M5 |
| `claude/meta-skill/skills/bootstrap.md` | 修改 | H4, H6, M3, M4 |
| `claude/meta-skill/knowledge/capabilities/ui-design.md` | 修改 | M2 |

## 验收标准

对 Telegram App 重新做思维测试，检查：

1. **H1-H3 消除**：bootstrap 为 Telegram 生成 infra-design、security-design 节点，
   且节点内容引用了对应 capability 的方法论锚点
2. **H4 消除**：bootstrap 的 implement 节点被拆分为多个子系统节点
   （如 implement-auth、implement-messaging、implement-groups 等）
3. **H5 消除**：concept-crystallization 和 implement 之间存在 design-to-spec 节点，
   产出 api-spec.json 和 db-schema.md，被 implement 节点通过 Context Pull 消费
4. **H6 消除**：workflow 包含 cross-module-stitch 节点，检查 API ↔ Web ↔ Mobile 接口一致性
5. **M2 消除**：ui-design 节点的 node-spec 中包含 interaction-spec.md 作为可选输出
6. **M4 消除**：状态机检查识别出消息送达状态（sent→delivered→read）和在线状态等业务状态机
7. **M5 消除**：bootstrap Step 2.2 加载 social-messaging.md 领域知识
