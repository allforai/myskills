---
name: cr-backend
description: >
  Use when user wants to "replicate backend", "API rewrite", "后端复刻", "微服务迁移",
  "reverse engineer API", "clone backend", "port backend to", "migrate backend",
  "rewrite server", "服务端复刻", "接口迁移", or mentions converting existing
  backend/API/microservice code to a different tech stack while preserving behavior.
version: "1.0.0"
---

# 后端复刻分析视角

## 概述

后端复刻专注于从服务端代码中提取完整的业务行为描述。分析目标是理解"系统做了什么"而非"用了什么框架"，确保迁移到任何目标技术栈时业务逻辑零丢失。

---

## 分析视角

### 入口层

接收外部请求的边界 — 系统与外界的所有接触点：

- **HTTP 路由**：路径、方法、参数绑定、请求/响应格式
- **RPC 定义**：服务接口声明、方法签名、序列化协议
- **消息消费者**：队列/主题订阅、消息格式、消费确认机制
- **CLI 命令**：命令名称、参数定义、输出格式
- **定时任务入口**：调度规则、触发条件、任务参数

> 入口层回答的问题：系统对外暴露了哪些能力？每个能力的输入输出契约是什么？

### 服务层

业务逻辑编排 — 系统的核心决策和协调逻辑：

- **事务边界**：哪些操作必须原子执行、回滚策略
- **外部服务调用**：调用了哪些第三方/内部服务、调用参数、响应处理
- **异步任务发起**：哪些操作被异步化、任务参数、完成回调
- **重试策略**：失败时的重试逻辑、退避策略、最大重试次数
- **业务规则**：条件判断、状态流转、计算逻辑

> 服务层回答的问题：每个入口背后的业务逻辑是什么？决策链条如何流转？

### 数据层

持久化操作 — 系统如何存储和检索数据：

- **实体定义**：数据模型、字段类型、关系映射、约束条件
- **查询模式**：常用查询的形状（过滤、排序、分页、聚合）
- **迁移脚本**：Schema 演进历史、数据迁移逻辑
- **缓存策略**：缓存对象、失效规则、缓存穿透处理

> 数据层回答的问题：系统持久化了什么数据？数据之间的关系是什么？

### 横切层

贯穿所有层的基础设施关注点：

- **认证/授权链**：身份验证方式、权限检查逻辑、角色定义
- **中间件管道**：请求处理管道的顺序和职责
- **错误处理策略**：错误分类、错误码定义、错误响应格式
- **日志策略**：日志级别、结构化日志字段、审计日志
- **配置管理**：环境变量、配置文件、Feature Flag

> 横切层回答的问题：系统的安全边界在哪？错误如何传播？运行时行为如何控制？

---

## Phase 2b 补充指令

模块摘要（source-summary.json 的 modules[]）时，额外提取以下后端特有信息：

### API 端点清单
```
每个端点记录：
- method: HTTP 方法（GET/POST/PUT/DELETE 等）
- path: 路由路径（含路径参数）
- auth: 是否需要认证（yes/no/optional）
- summary: 一句话描述端点用途
```

### 数据实体清单
```
每个实体记录：
- name: 实体名称
- key_fields: 关键字段列表（名称+类型）
- relations: 与其他实体的关系（1:N, N:M 等）
```

### 认证机制摘要
```
记录：
- auth_type: 认证方式（JWT/Session/OAuth/API Key 等）
- role_model: 角色模型描述
- permission_granularity: 权限粒度（API 级/资源级/字段级）
```

---

## Phase 3-pre: 生成 extraction-plan

LLM 读取 source-summary.json，基于对**当前后端项目**的理解，生成 extraction-plan.json：

- `role_sources`：哪些文件定义了角色/权限？（可能是 RBAC 配置、中间件、Decorator、Annotation...取决于项目）
- `task_sources`：哪些文件定义了业务入口？（可能是 Controller、Handler、gRPC Service、CLI Command、Cron Job...取决于项目）
- `flow_sources`：哪些文件包含业务编排逻辑？（可能是 Service 方法、Saga、Pipeline...取决于项目）
- `usecase_sources`：哪些文件包含条件分支和错误处理？（同 task_sources 的深层分析）
- `constraint_sources`：哪些文件包含校验规则和硬约束？（可能是 Validator、Schema、Middleware...取决于项目）
- `cross_cutting`：跨模块关注点（认证、日志、错误处理）在哪些文件中？

**禁止套用框架模板** — 必须从 source-summary 的实际模块结构、key_files 中推断。

## Phase 3: 按 extraction-plan 生成片段

按 extraction-plan 中指定的文件和提取方式，逐模块生成 JSON 片段。

### 后端分析要点

以下是后端项目常见但**不一定存在**的模式。LLM 应在 extraction-plan 中标注本项目实际使用的模式，而非假设所有项目都有：

- **异步操作**：队列消费者和定时任务可能是独立 task — 如果项目有异步机制，extraction-plan 中应标注
- **隐式流程**：中间件链可能构成隐式业务流 — 如果项目使用中间件管道，extraction-plan.cross_cutting 中应记录
- **数据约束**：数据库 Schema 约束可能是 constraints 来源 — 如果项目有 ORM/迁移脚本，extraction-plan.constraint_sources 中应指向
- **错误码体系**：错误码定义可能暗示异常场景 — 如果项目有统一错误码，extraction-plan.usecase_sources 中应包含

---

## 加载核心协议

> 核心协议详见 ./skills/code-replicate-core.md
