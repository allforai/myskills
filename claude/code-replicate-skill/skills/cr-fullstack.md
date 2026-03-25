---
name: cr-fullstack
description: >
  Use when user wants to "replicate full project", "综合复刻", "全栈复刻",
  "前后端一起迁移", "fullstack rewrite", "clone entire project",
  "replicate both frontend and backend", or mentions analyzing both
  frontend and backend code together for cross-layer consistency.
version: "1.0.0"
---

# 全栈复刻分析视角

## 概述

全栈复刻委派 cr-backend + cr-frontend 分别扫描各自层，在此基础上额外执行交叉验证和基础设施扫描。目标不是"跑两遍"，而是单次协调分析 + 跨层一致性保障。

---

## 分析视角

全栈复刻继承后端四视角（入口层/服务层/数据层/横切层）和前端四视角（页面路由层/组件层/状态层/交互层），额外增加：

### 交叉验证视角

前后端之间的契约和一致性：

- **API 契约对齐**：前端调用的端点 vs 后端暴露的端点（路径/方法/参数/响应）
- **数据类型对齐**：前端类型定义 vs 后端实体字段（名称/类型/可选性）
- **认证传播**：后端的认证要求 vs 前端的 Token 管理和路由守卫
- **错误映射**：后端错误码/错误格式 vs 前端错误处理逻辑
- **实时通信**：WebSocket/SSE 的前后端事件名称和数据格式对齐

### 基础设施视角

支撑前后端运行的基础设施：

- **容器编排**：Docker 配置、服务间网络、构建流水线
- **反向代理**：API 网关、路径转发、CORS 配置
- **环境变量**：前后端各自的环境配置、共享配置
- **定时任务**：Cron 配置、调度系统
- **部署清单**：K8s/Compose 配置、服务依赖关系

---

## Phase 2 增强

在 core 的 Phase 2 基础上增加以下全栈特有步骤：

### 2a. 项目结构检测

自动检测项目类型：
- **Monorepo 模式**：检测 backend/ + frontend/（或 server/ + client/ 等变体）分离目录
- **单目录全栈模式**：前后端同目录（如 pages/ + api/ 共存的全栈框架）
- 记录检测结果到 source-summary.json 的 `project_structure` 字段

### 2b. 委派分层扫描

- 委派 cr-backend 的 Phase 2b 指令扫描后端部分
- 委派 cr-frontend 的 Phase 2b 指令扫描前端部分
- 两次扫描的模块摘要分别写入 source-summary.json

### 2c. 基础设施扫描

额外扫描并记录：
- Docker/容器编排配置
- 反向代理/API 网关配置
- 环境变量清单（前后端各自 + 共享）
- 定时任务配置
- CI/CD 流水线配置

### 2d. source-summary.json 增强字段

```
增加以下顶层字段：
- infrastructure: 基础设施配置摘要
- api_call_map: 前端→后端的 API 调用映射
  - frontend_component: 调用方组件
  - backend_endpoint: 被调方端点
  - data_shape: 请求/响应数据结构
  - auth_required: 是否需要认证
```

---

## Phase 3-pre: 生成 extraction-plan（全栈增强）

除了 cr-backend 和 cr-frontend 各自的 extraction-plan 字段，全栈模式额外生成：

- `api_contract_files`：前后端 API 契约文件（OpenAPI spec、GraphQL schema、tRPC router、或手写类型定义）
- `cross_layer_mapping`：前端调用文件 ↔ 后端处理文件的对应关系（LLM 从 source-summary.api_call_map 推断）

## Phase 3: 全栈增强

### task-inventory 增强

- 合并前后端 task，消除重复（同一业务操作的前后端 task 合并为一个）
- 每个 task 增加 `layer` 字段：
  - `backend` — 纯后端 task（定时任务、队列消费等）
  - `frontend` — 纯前端 task（纯 UI 交互、本地计算等）
  - `fullstack` — 跨前后端 task（用户操作→API→处理→响应→UI 更新）

### business-flows 增强

- 构建跨前后端的完整用户流程
- 每个 flow step 标注 layer（frontend/backend）

### 交叉一致性检查

LLM 基于 extraction-plan.cross_layer_mapping 检测实际不一致，写入 task/flow 的 `flags` 字段。常见但**不一定存在**的不一致类型：

- API 参数/响应不匹配
- 认证传播断裂
- 字段类型不一致
- 孤立端点（一端有、另一端未调用）
- 未处理的错误码

> **注意**：不假设所有项目都存在以上问题。LLM 根据实际代码判断。

---

## Phase 4 增强

- 验证脚本使用 `--fullstack` 标志运行
- 额外检查指标：
  - **API 调用匹配度**：前端调用的端点在后端是否都存在（及反向）
  - **字段对齐度**：跨前后端的同名数据结构字段是否一致
  - 匹配度/对齐度结果写入验证报告的 `cross_layer_validation` 节

---

## 加载核心协议

> 核心协议详见 ${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md
