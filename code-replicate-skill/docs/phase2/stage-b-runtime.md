# Phase 2 Stage B — 运行基础发现

> 项目靠什么跑？连接哪些服务？有什么定时任务？错误码怎么定义？

---

## 2.5 infrastructure-profile.json — 基础设施

LLM 读源码行为（不是包名匹配），理解项目依赖的**自研技术基础设施**。

每个组件记录：name, category（自由分类）, files, what_it_does, how_it_works, is_standard, cannot_substitute, migration_risk, migration_risk_reason。

自定义协议/加密/序列化组件**必须**输出 `protocol_spec`（帧格式 + 状态机 + 测试向量）。

**数据持久化必须拆分两层盘点**：
- **存储引擎**（SQLite/Hive/Realm/CoreData 等）— 通常 `cannot_substitute: false`（可以换引擎）
- **数据访问模式**（Repository/DAO/mixin 自动持久化/缓存策略等）— 通常 `cannot_substitute: true`，migration_risk 比引擎本身高得多。LLM 需要识别每个持久化表的读写模式（本地优先？API 优先？离线队列？）以及隐式持久化模式（mixin/decorator/AOP 自动挂载的持久化行为容易被当成普通方法调用而遗漏）

**实时推送分发必须单独盘点**：
如果源码有 WebSocket/长连接/SSE，LLM 追问：连接建立后服务端主动推什么？推送数据如何分发到各业务模块？推送是否触发本地持久化（不只是 UI 刷新）？推送分发管道是实时应用的核心 — 没有它 App 只能发不能收。

> Schema 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md#infrastructure-profile

## 2.6 env-inventory.json — 环境配置

LLM 读 `.env.example` + 代码中的环境变量引用 → 提取所有环境变量清单。

每个变量记录：key, purpose, category（自由分类）, secret, default_value（非敏感）, required, used_by。

**目的**：目标项目的 `.env.example` 从此产物直接生成。

## 2.7 third-party-services.json — 第三方服务

LLM 读源码中的外部服务调用（SDK 初始化、API 客户端、webhook 注册），提取服务清单。

每个服务记录：name, purpose, integration_type, config_env_vars（引用 env-inventory）, source_files, has_sandbox, migration_note。

**与 infrastructure-profile 的关系**：infrastructure-profile 记录**自研组件**，third-party-services 记录**外部服务**。

## 2.8 cron-inventory.json — 定时任务（仅 backend/fullstack）

LLM 读源码中的定时任务定义 → 提取任务清单。

每个任务记录：name, schedule, handler, purpose, retry_policy, source_file。

## 2.9 error-catalog.json — 错误码体系（仅 backend/fullstack）

LLM 读源码中的错误定义 → 提取结构化错误码清单。

记录：统一错误响应格式 + 每个错误码的 code, http_status, message, category, source_file。

**目的**：前端依赖后端错误码做条件处理。错误码变了 → 前端错误处理全部断裂。目标项目必须使用**相同的错误码数值和格式**。
