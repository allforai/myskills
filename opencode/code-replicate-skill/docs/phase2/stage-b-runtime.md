# Phase 2 Stage B — 运行基础发现

> 项目靠什么跑？连接哪些服务？有什么定时任务？错误码怎么定义？

---

## 2.5 infrastructure-profile.json — 基础设施

LLM 读源码行为（不是包名匹配），理解项目依赖的**自研技术基础设施**。

每个组件记录：name, category（自由分类）, files, what_it_does, how_it_works, is_standard, cannot_substitute, migration_risk, migration_risk_reason。

**LLM 必须对每个组件追问三个深层问题**：

**① 缺了它用户会看到什么？（`if_missing`）**
不只记录"组件做什么"，还要记录"没有它会怎样"。这决定了迁移优先级 — "缺了连接断开用户不知道"比"缺了日志少一行"严重得多。

**② 有没有周期性/后台行为？（`periodic_behaviors`）**
很多组件不是"调一次就完"而是有持续运行的后台行为（定时心跳、Token 自动续约、连接重试、缓存清理、数据定期同步）。这些后台行为最容易被遗漏 — 看代码时不像显式的函数调用那么明显。

**③ 在 App 生命周期各阶段做什么？（`lifecycle`）**
组件在启动/运行中/切后台/恢复前台/关闭这 5 个阶段可能有不同行为。当前分析只描述"运行中"阶段，其他阶段的行为（如切后台时降低心跳频率、恢复前台时重新检查连接）全部被忽略。

自定义协议/加密/序列化组件**必须**输出 `protocol_spec`（帧格式 + 状态机 + 测试向量）。

**数据持久化必须拆分两层盘点**：
- **存储引擎**（SQLite/Hive/Realm/CoreData 等）— 通常 `cannot_substitute: false`（可以换引擎）
- **数据访问模式**（Repository/DAO/mixin 自动持久化/缓存策略等）— 通常 `cannot_substitute: true`，migration_risk 比引擎本身高得多。LLM 需要识别每个持久化表的读写模式（本地优先？API 优先？离线队列？）以及隐式持久化模式（mixin/decorator/AOP 自动挂载的持久化行为容易被当成普通方法调用而遗漏）

**实时推送分发必须单独盘点**：
如果源码有 WebSocket/长连接/SSE，LLM 追问：连接建立后服务端主动推什么？推送数据如何分发到各业务模块？推送是否触发本地持久化（不只是 UI 刷新）？推送分发管道是实时应用的核心 — 没有它 App 只能发不能收。

**事件总线必须列出事件清单**：
如果源码有 EventBus/EventDispatcher/MessageBus/事件系统，不只记录"有一个事件总线"，还要列出**所有事件类型 + 发布者 + 订阅者**。事件是跨模块联动的管道 — 源码 80 个事件类型目标只实现了 11 个 = 大量跨模块联动断裂。

**隐式行为必须显式标注**：
很多框架通过 mixin/decorator/注解/钩子产生**代码文本中看不到的行为**（如混入一个类自动获得 CRUD 方法、注册一个钩子自动同步远程数据到本地）。LLM 分析时容易把这些当成"普通方法调用"。对每个识别到的隐式行为模式，记录：隐式获得了什么能力、目标栈如果没有等价机制需要手动实现什么。

> Schema details: `./docs/schema-reference.md#infrastructure-profile`

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
