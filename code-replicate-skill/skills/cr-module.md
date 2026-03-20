---
name: cr-module
description: >
  Use when user wants to "replicate module", "模块复刻", "复刻某个模块",
  "migrate specific module", "extract module", "模块迁移",
  "replicate specific feature", or mentions replicating a subset of code
  with attention to dependency boundaries.
version: "1.0.0"
---

# 模块复刻分析视角

## 概述

模块复刻分析指定模块并主动扫描其外部依赖边界。与 scope=modules 的区别：cr-module 不仅分析目标模块本身，还主动发现、展示并帮助用户决策所有依赖关系，解决"模块边界不干净"的问题。

---

## 分析视角

模块复刻根据目标模块类型，复用 cr-backend 或 cr-frontend 的分析视角。在此基础上额外关注：

### 依赖边界视角

模块与外部世界的连接点：

- **代码依赖**：import/require 其他模块的代码（函数、类、常量、类型）
- **事件依赖**：emit/publish/dispatch 的事件被哪些模块消费，subscribe/listen 了哪些外部事件
- **共享层依赖**：使用的共享基础设施（认证、日志、配置、数据库表、类型定义）
- **数据依赖**：读写其他模块"拥有"的数据表或缓存键
- **接口依赖**：实现或调用其他模块定义的接口/协议

> 边界视角回答的问题：这个模块如果被"拔出来"，哪些连接会断？

---

## Phase 2 增强

在 core 的 Phase 2 基础上增加以下模块特有步骤：

### 2a. 全项目扫描

- 需要全局视角以发现依赖关系，因此先扫描整个项目结构
- 但 `key_files` 只深读目标模块内的文件（控制分析成本）
- 其他模块只读入口文件和导出定义（足以识别依赖接口）

### 2b. 依赖边界扫描

系统性扫描三类依赖：

**代码依赖**
- 目标模块 import/require 了哪些外部模块的代码
- 外部模块 import/require 了目标模块的哪些导出

**事件依赖**
- 目标模块 emit/publish/dispatch 的事件 → 哪些外部模块在消费
- 目标模块 subscribe/listen 的事件 → 来自哪些外部模块

**共享层依赖**
- 共享的认证/授权机制
- 共享的日志/配置基础设施
- 共享的类型定义/接口
- 共享的数据库表（多个模块读写同一张表）

---

## Phase 2d 增强

### 依赖矩阵展示

向用户展示依赖矩阵，格式：

```
目标模块: [module-name]

代码依赖:
  → module-A: 调用 3 个函数, 使用 2 个类型
  → module-B: 调用 1 个函数
  ← module-C: 被调用 2 个导出函数

事件依赖:
  → event:order.created → module-D 消费
  ← event:payment.completed ← module-E 发布

共享层依赖:
  ↔ shared/auth: 使用认证中间件
  ↔ shared/db: 共享 users 表
```

### 依赖决策收集

对每个外部依赖，收集用户决策（或基于规则自动推荐）：

| 决策类型 | 含义 | 处理方式 |
|---------|------|---------|
| `include` | 一起分析和复刻 | 纳入目标模块范围，完整分析 |
| `external_interface` | 只记录签名 | 记录函数签名/类型定义，不分析实现 |
| `event_contract` | 只记录事件 Schema | 记录事件名称和数据格式 |
| `prerequisite` | 标记为前置条件 | 记录为 task.prerequisites，不分析 |

### source-summary.json 增强

模块级增强字段写入 modules[] 内：

```
modules[target].dependencies: [
  {
    "target": "module-A",
    "type": "code|event|shared",
    "direction": "outbound|inbound|bidirectional",
    "details": "调用 getUserById, formatDate",
    "boundary_decision": "include|external_interface|event_contract|prerequisite"
  }
]
```

---

## Phase 3-pre: 生成 extraction-plan（模块增强）

除了 cr-backend/cr-frontend 的标准 extraction-plan 字段，模块模式额外生成：

- `boundary_interfaces`：目标模块对外暴露的接口清单（来自 Phase 2d 依赖矩阵）
- `external_deps_mapping`：每个外部依赖的处理决策（include / external_interface / event_contract / prerequisite）

## Phase 3: 按 extraction-plan 生成片段

- 只为目标模块 + `include` 决策的模块生成完整产物
- `external_interface` 依赖：记录在相关 task 的 `prerequisites` 字段中
- `event_contract` 依赖：记录事件名称和数据格式
- `prerequisite` 依赖：记录为前置条件
- task-inventory 中与外部依赖相关的 task 增加 `external_deps` 字段列出依赖清单

---

## 加载核心协议

> 核心协议详见 ${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md
