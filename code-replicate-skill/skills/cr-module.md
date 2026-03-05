---
name: cr-module
description: >
  Use when user wants to "replicate module", "模块复刻", "复刻某个模块",
  "migrate specific module", "extract module", "模块迁移",
  "replicate specific feature", or mentions replicating a subset of code
  with attention to dependency boundaries.
version: "1.0.0"
---

# CR Module — 模块级复刻（依赖边界处理）

> 先加载协议基础: `${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md`

> **Phase 委托**：本技能覆盖 Phase 1/2/3/4/6 的模块特有部分（依赖边界扫描与决策）。Phase 1/3/5/7 的基础流程由 core 协议处理。Phase 4 根据项目类型复用 cr-backend 或 cr-frontend 逻辑。

模块级逆向分析：在标准模块分析基础上，**主动扫描并展示外部依赖** — 代码依赖、事件/消息依赖、共享层依赖。解决"模块边界不干净"的问题。

---

## 与 scope=modules 的区别

| 维度 | scope=modules（现有） | cr-module（本技能） |
|------|---------------------|-------------------|
| 依赖边界 | 不处理，只分析指定目录 | **主动扫描并展示外部依赖** |
| 事件驱动 | 不追踪 | **扫描 emit/publish/subscribe 模式** |
| 共享层 | 不处理 | **列出共享中间件/类型/数据表** |
| Phase 3 | 确认纳入模块 | **确认纳入模块 + 依赖边界决策** |
| 产物 | 标准产物 | 标准产物 + `module-boundaries.json` |

---

## Phase 1 Preflight

在 core Preflight 基础上，额外收集：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 目标模块路径 | {module_path} | 必填，要复刻的模块目录（如 `src/modules/user`） |
| 项目类型 | {project_type} | Phase 2 自动检测（后端/前端） |

**`--module` 参数**为必填，指定要复刻的模块路径。可指定多个：`--module src/user --module src/auth`。

写入 `replicate-config.json`，`scope = modules`，`scope_detail` 为模块路径列表。

---

## Phase 2：源码解构 + 依赖边界扫描

### 2a-2c. 标准扫描

根据检测到的项目类型，复用 cr-backend 或 cr-frontend 的 Phase 2 逻辑，**扫描整个项目**（需要全局上下文）。

### 2d. 外部依赖扫描（cr-module 独有）

对目标模块的每个文件，扫描 import/require 语句：

- 引用目标模块内部文件 → **内部依赖**（正常，不记录）
- 引用目标模块外部文件 → **外部依赖**，记录到 `external_dependencies`

分类规则：
- 第三方包（node_modules / pip packages）→ 标记为 `third_party`，不视为模块依赖
- 项目内其他模块 → 标记为 `module_dependency`
- 项目共享层（utils/common/shared）→ 标记为 `shared_dependency`

### 2e. 事件/消息依赖扫描（cr-module 独有）

搜索以下模式：

```
发出事件: emit|publish|dispatch|fire|trigger|send + 事件名
监听事件: on|subscribe|listen|handle|consume + 事件名
```

对每个匹配：
- 记录事件名 + 方向（publish/subscribe）
- 追踪事件在其他模块中的 publish/subscribe 对应方，确定关联模块

### 2f. 共享层识别（cr-module 独有）

扫描目标模块引用的：

| 共享资源类型 | 检测方式 |
|------------|---------|
| 共享中间件 | auth guard、logger、error handler — 从 middleware/guard 目录或装饰器引用 |
| 共享类型/DTO/enum | 从 `shared/`、`common/`、`types/` 目录引用的类型定义 |
| 共享数据库表 | ORM 关联（外键、join 查询、relation 装饰器） |
| 共享配置 | 环境变量引用、feature flag、全局配置 |

输出进度「Phase 2 ✓ 目标模块: {module_names} | 外部依赖: {N} 个模块 | 事件: {N} publish / {N} subscribe | 共享层: {N} 项」。

---

## Phase 3：目标确认 + 依赖边界决策（增强）

在 core Phase 3 基础上，额外展示依赖边界信息并收集决策：

```markdown
### 模块依赖边界

目标模块: {module_name}（{module_path}）

#### 直接代码依赖（import）

| 外部模块 | 引用方式 | 建议 |
|---------|---------|------|
| auth | UserService → AuthService.validateToken() | 纳入 / 标记为外部接口 |
| notification | UserService → NotificationService.sendEmail() | 纳入 / 标记为外部接口 |

#### 事件依赖（异步）

| 事件 | 方向 | 关联模块 | 建议 |
|------|------|---------|------|
| UserCreated | publish | order, analytics, notification | 记录事件契约，不纳入消费者 |
| PaymentCompleted | subscribe | payment | 记录事件契约 |

#### 共享层依赖

| 共享资源 | 类型 | 建议 |
|---------|------|------|
| AuthGuard | 中间件 | 标记为前置依赖 |
| BaseEntity | 共享类型 | 纳入 |
| users 表 ↔ orders 表 (FK) | 数据关联 | 标记外键关系 |
```

### 依赖边界决策选项

对每个外部依赖，用 `AskUserQuestion` 收集决策（合并到 Phase 3 确认中）：

| 决策 | schema key | 含义 | 复刻时处理 |
|------|-----------|------|-----------|
| **纳入** (include) | `include` | 将该模块也加入分析范围 | Phase 4 一并分析 |
| **标记为外部接口** (external_interface) | `external_interface` | 只记录接口签名，不分析实现 | 复刻时作为 mock/stub |
| **标记为事件契约** (event_contract) | `event_contract` | 只记录事件 schema | 不纳入生产/消费逻辑 |
| **标记为前置依赖** (prerequisite) | `prerequisite` | 记录依赖关系，复刻时必须先满足 | 生成前置条件清单 |

决策写入 `replicate-config.json` 的 `module_boundary_decisions` 字段。

---

## Phase 4：深度分析

根据项目类型复用 cr-backend 或 cr-frontend 的 Phase 4 逻辑，分析范围包括：
- 目标模块（必须）
- Phase 3 决策为"纳入"的外部模块
- Phase 3 决策为"外部接口"的模块 → 仅提取接口签名

对"外部接口"的模块：
- 只扫描目标模块实际调用的方法/函数
- 生成接口签名（函数名 + 参数类型 + 返回类型）
- 不分析实现逻辑，标注 `[EXTERNAL_INTERFACE]`

---

## Phase 6：生成产物（增强）

除标准产物外，新增 `module-boundaries.json`。

> 完整 module-boundaries.json 格式详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（Module 边界产物）
```

### 产物目录

```
.allforai/
├── product-map/
│   ├── task-inventory.json
│   ├── business-flows.json          ← functional+
│   └── constraints.json             ← exact
├── use-case/
│   └── use-case-tree.json           ← functional+
└── code-replicate/
    ├── replicate-config.json
    ├── source-analysis.json
    ├── api-contracts.json
    ├── behavior-specs.json          ← functional+
    ├── arch-map.json                ← architecture+
    ├── bug-registry.json            ← exact
    ├── module-boundaries.json       ← cr-module 独有
    ├── stack-mapping.json
    ├── stack-mapping-decisions.json
    └── replicate-report.md
```

### replicate-report.md 模块专有部分

在标准报告基础上追加模块边界摘要：

```markdown
## 模块边界摘要

| 维度 | 数量 |
|------|------|
| 目标模块 | {N} |
| 外部依赖（纳入） | {N} |
| 外部依赖（接口） | {N} 个接口签名 |
| 事件契约 | {N} publish / {N} subscribe |
| 共享依赖 | {N} |
| 数据关联 | {N} 表间关系 |

### 复刻前置条件

以下依赖必须在目标项目中先满足：

1. **AuthGuard** — 认证中间件（目标栈等价物需先实现）
2. **users 表** — 数据库表结构（含外键关系）
3. **PaymentCompleted 事件** — 需订阅此事件（来自 payment 模块）
```
