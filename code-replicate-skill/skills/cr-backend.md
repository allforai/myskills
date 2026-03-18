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

## Phase 3 推断策略

从后端源码推断标准产物时，按以下策略映射：

| 产物 | 从什么推断 |
|------|-----------|
| role-profiles | 认证/授权代码中的角色定义、权限检查、RBAC 配置。每个角色的权限范围→responsibilities，可访问端点→task 关联 |
| task-inventory | 入口层的每个端点/命令 → 一个 task。参数→inputs，响应→outputs，错误处理→exceptions，中间件→prerequisites |
| business-flows | 服务层的调用链 → flow。跨服务调用序列→主线步骤，中间件→横切流，事务边界→原子步骤组 |
| use-case-tree | 入口层的条件分支→boundary，错误路径→exception，正常流→happy_path。HTTP 状态码 2xx→成功场景，4xx→边界，5xx→异常 |
| constraints | 硬编码的业务规则→exact 模式约束。校验逻辑（长度/格式/范围）→输入约束，限流规则→性能约束，权限规则→安全约束 |

### 后端特有推断注意事项

- **异步操作**：队列消费者和定时任务也是 task，不要遗漏
- **隐式流程**：中间件链构成的隐式业务流（如：认证→限流→日志→处理→审计）需要显式记录
- **数据约束**：数据库 Schema 中的约束（NOT NULL、UNIQUE、CHECK）是 constraints 的重要来源
- **错误码体系**：错误码定义暗示了所有可能的异常场景，是 use-case exception 的补充来源

---

## 加载核心协议

> 核心协议详见 ${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md
