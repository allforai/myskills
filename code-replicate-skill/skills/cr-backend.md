---
name: cr-backend
description: >
  Use when user wants to "replicate backend", "API rewrite", "后端复刻", "微服务迁移",
  "reverse engineer API", "clone backend", "port backend to", "migrate backend",
  "rewrite server", "服务端复刻", "接口迁移", or mentions converting existing
  backend/API/microservice code to a different tech stack while preserving behavior.
version: "1.0.0"
---

# CR Backend — 后端复刻

> 先加载协议基础: `${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md`

后端专用逆向分析：API 合约、Service 业务逻辑、ORM 映射、中间件链、微服务契约。

---

## 项目类型检测表

Phase 2 完成技术栈识别后，确认项目属于以下类型之一：

| 类型 | 检测特征 | 分析重心 |
|------|---------|---------|
| **后端 API** | `routes/`、`controllers/`、`middleware/`、`services/`、ORM 配置、`main.go/app.py/index.ts` 入口 | API 合约、业务逻辑、ORM 映射、中间件链 |
| **微服务** | `.proto` 文件、消息队列 consumer/producer、`saga/`、事件定义文件 | 服务契约（proto/schema）、消息格式、事件流、幂等性 |

**混合单体检测**：若发现前端代码（`components/`、`pages/`、`store/`、`hooks/`、路由配置文件）→ 输出提示：

```markdown
### 检测到混合单体项目

前端部分: {path}（{frontend_stack}）
建议：对前端部分单独运行 `/cr-frontend` 分析。
```

---

## Phase 2：源码解构（后端版，自动执行，不停顿）

### 1a. 技术栈识别

扫描以下文件识别技术栈（优先顺序：依赖文件 > 目录结构 > 文件扩展名）：

| 文件 | 技术栈 |
|------|--------|
| `package.json` | Node.js；框架从 dependencies 推断（Express/NestJS/Fastify/Koa） |
| `requirements.txt` / `pyproject.toml` | Python；框架从依赖推断（Django/FastAPI/Flask） |
| `go.mod` | Go；框架从 import 路径推断（Gin/Echo/Fiber） |
| `pom.xml` / `build.gradle` | Java/Kotlin（Spring Boot/Ktor） |
| `composer.json` | PHP（Laravel/Symfony） |
| `Gemfile` | Ruby（Rails/Sinatra） |
| `Cargo.toml` | Rust（Actix/Axum） |
| `.csproj` / `.sln` | C#（ASP.NET Core） |

记录到 `source_analysis.json` 的 `source_stack` 字段，附证据 `[CONFIRMED:file]`。

### 1b. 模块树提取

扫描目录结构，识别后端典型模块模式：

```
controllers/ | routes/ | handlers/    → 路由/控制器层
services/ | usecases/ | domain/       → 业务逻辑层
repositories/ | models/ | entities/   → 数据访问层
middleware/ | guards/ | interceptors/ → 中间件层
config/ | settings/                   → 配置层
```

对每个模块生成条目（含 id, name, path, inferred_responsibility, confidence, evidence, key_files 字段）。模块职责无法确定时：标注 `"confidence": "low"` + `[INFERRED]`，加入歧义 log，**不停下询问**。

> 模块条目格式详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（模块树条目）

### 1c. 代码规模评估

统计：总文件数、代码行数（估算）、路由数量（估算）、模块数量。

写入 `.allforai/code-replicate/source-analysis.json`，输出进度「Phase 2 ✓ {N} 模块 | {N}± 路由 | {source_stack} | 类型: 后端」。

**下一步**：进入 Phase 3 目标确认（见 core 协议）— 展示源码全貌，让用户确认复刻范围、目标技术栈、业务方向，确认后自动继续 Phase 4。

---

## Phase 4：信度专项分析 — 后端 API 项目

按信度等级叠加执行（每个模式包含上一级全部内容）。所有歧义收集到内部 `ambiguity_log`，不停下询问。

### 粒度适配

根据 Phase 3 确定的 `analysis_granularity`（scope=full 时按代码规模自动判定）：
- **fine**：逐个端点完整分析（4D + 6V），逐个 Service 函数追踪完整 flow 步骤
- **standard**：逐个端点分析，高风险项完整 6V，普通项省略 ux/risk 视角
- **coarse**：按模块聚合，仅高频/高风险端点做完整分析，其余提取签名 + 关键约束（省略 flow 步骤和低优先级视角）

### 所有模式：API 合约分析 → `api-contracts.json`

对每个路由文件提取端点条目（含 4D + 6V 字段：endpoint_id, method, path, source_file, source_line, auth_required, request, responses, confidence, source_refs, constraints, decision_rationale, viewpoints）。

若响应状态码与实际异常处理不一致 → 标注 `[CONFLICT]`，加入 ambiguity_log，**不停下**。

> 完整端点 JSON 示例详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（api-contracts.json）

额外关注：
- **认证中间件链**（JWT/Session/OAuth 如何注入、哪些路由受保护）
- **数据库事务边界**（哪些操作是原子的、嵌套事务策略）
- **外部服务调用**（第三方 API、消息队列 publish、webhook）

---

### functional 模式加：行为规格分析 → `behavior-specs.json`

对每个 Service 函数提取业务逻辑路径（含 4D + 6V 字段：behavior_id, name, source_file, source_line, flow, error_handling, confidence, source_refs, constraints, decision_rationale, viewpoints）。

无测试覆盖的行为 → 标注 `[UNTESTED]`，加入 ambiguity_log，继续。

> 完整行为 JSON 示例详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（behavior-specs.json）

---

### architecture 模式加：架构地图 → `arch-map.json`

提取分层结构（layers）、检测到的模式（patterns_detected）、模块依赖（dependencies）、横切关注点（cross_cutting: logging, auth, caching 等）。

发现架构歧义（如：无法确定是否有多个入口点） → 若 `ambiguity_policy = strict` 且影响架构走向 → 即时停下询问；否则标注加入 log 继续。

> 完整架构地图 JSON 示例详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（arch-map.json）

---

### exact 模式加：Bug 注册表 → `bug-registry.json`

逐一记录发现的 bug（含 bug_id, type, location, description, evidence, confidence, evidence_sources, replicate_decision 字段）。

**后端典型 bug 类型**（重点扫描）：
- 竞态条件（并发写入无锁保护）
- 事务遗漏（多步操作非原子）
- 认证绕过（路由遗漏 auth guard）
- SQL 注入 / ORM 不安全查询
- 分页 off-by-one
- 时区处理不一致

若 `bug_replicate_default = ask` → 将每个 bug 的决策加入 Phase 5 的"待确认列表"，不即时停下。

> 完整 bug 条目 JSON 示例详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（bug-registry.json）

---

## Phase 4（微服务项目）：服务契约分析

若 Phase 2 检测到微服务类型，Phase 4 替换为服务契约分析：

| 维度 | 分析内容 | 对应产物 |
|------|---------|---------|
| **服务契约** | gRPC proto 定义 / REST API / GraphQL schema | `api-contracts.json`（服务间接口） |
| **消息格式** | 消息队列 payload 结构、topic 命名、序列化格式 | `behavior-specs.json` 消息流 |
| **事件定义** | 领域事件 schema、事件版本、消费者清单 | `arch-map.json` 事件流 |
| **幂等性** | 哪些操作有幂等保障，幂等键策略 | `behavior-specs.json` |
| **服务依赖图** | 服务间调用关系、循环依赖检测 | `arch-map.json` |

---

### Phase 4 完成

写入所有 JSON 文件，更新 `replicate-config.json`，输出进度「Phase 4 ✓ {N} 端点 | {N} 行为 | {N} 歧义待确认」，自动继续 Phase 4 XV（或 Phase 5）。

---

## Phase 6：生成 allforai 产物（后端专有部分）

> 6a/6e/6f 由 core 统一生成，以下为后端特有产物。

### 6b. `product-map/business-flows.json`（functional+ 模式）

从 `behavior-specs.json` 中的 Service 调用链提取，转换为 product-map 兼容格式（与 `/product-map` 产出结构一致）。

重点：
- Service → Service 调用链作为业务流程主线
- 中间件链作为横切流程
- 事务边界标注（原子操作范围）

### 6c. `use-case/use-case-tree.json`（functional+ 模式）

从业务行为生成用例树，格式兼容 product-design `use-case/` 目录。

后端用例来源：
- 每个 API 端点 → 一个用例
- Service 内部的条件分支 → 用例的备选流
- 错误处理 → 异常流

### 6d. `product-map/constraints.json`（exact 模式）

将 `bug-registry.json` 中 `replicate_decision: "replicate"` 的 bug 转为约束（含 constraint_id, source_bug, description, enforcement, affects）。
