---
name: project-setup
description: >
  Use when the user wants to "set up project structure", "split into sub-projects",
  "choose tech stack", "configure monorepo", "project setup", "项目引导",
  "拆分子项目", "选技术栈", "配置 monorepo", "项目结构设计",
  or needs to plan how to organize a multi-project codebase from product-design artifacts.
  Requires product-map to have been run first.
version: "1.2.0"
---

# Project Setup — 项目引导

> 从产品地图到项目结构：交互式引导拆分子项目、选择技术栈、分配模块

## 目标

以 `product-map` 为蓝本，引导用户完成从产品设计到项目结构的转化：

1. **拆子项目** — 按角色和端类型拆分（后端 API、管理后台、消费者端、移动端…）
2. **选技术栈** — 从预设模板中选择，记录完整技术配置
3. **分配模块** — product-map 中的模块/任务分配到对应子项目
4. **配置基础** — 端口号、base path、auth 策略、monorepo 工具
5. **输出 manifest** — 生成 project-manifest.json，下游 skill 消费

---

## 定位

```
product-map（产品长什么样）   project-setup（代码怎么组织）   design-to-spec（具体怎么做）
角色/任务/流程/约束           拆子项目/选技术栈/分模块        生成 requirements/design/tasks
产品层                       架构层                          规格层
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。

---

## 快速开始

```
/project-setup              # 新项目，从空白开始
/project-setup new          # 同上
/project-setup existing     # 已有项目，扫描代码 → 识别缺口
```

---

## 增强协议（WebSearch + 4E+4V）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：
- `"{tech-stack} project structure best practices {year}"`
- `"monorepo vs polyrepo {language} {year}"`
- `"{framework} clean architecture layout {year}"`

**4E+4V 重点**：
- **E4 Context**: manifest 中的 `decision_rationale` 保留技术选型理由（为什么选这个栈、为什么这样拆）
- **E2 Provenance**: 每个子项目的 assigned_modules 可追溯到 product-map 模块 ID

---

## 架构决策理论支持

> 详见 `docs/dev-forge-principles.md` — 前段：架构决策

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|---------|---------|
| **Unix Philosophy** (McIlroy, 1978) | Step 1 子项目拆分 | "做一件事做好"：每子项目只承担一个职责 |
| **Conway's Law** (Conway, 1968) | Step 1 子项目拆分 | 按角色/团队边界拆分，架构映射组织结构 |
| **Bounded Context** (Evans, 2003) | Step 3 模块分配 | 同一业务概念在不同端可有不同视角 |
| **Twelve-Factor App** (Wiggins, 2011) | Step 4 基础配置 | 配置外置(.env)、端口绑定、依赖隔离 |
| **C4 Model** (Brown, 2018) | Step 5 manifest 生成 | manifest 对应 C4 的 Container 层视图 |
| **Microservices Patterns** (Richardson, 2018) | Step 1 子项目拆分 | 按业务能力 / 按子域 / 按技术栈的拆分策略 |

---

## 工作流

```
前置: 加载 .allforai/product-map/product-map.json
      加载 .allforai/product-map/task-index.json（索引优先）
      若不存在 → 提示先运行 /product-map，终止
      ↓
前置: Preflight 偏好检测
      读取 .allforai/project-forge/forge-decisions.json → preflight 字段
      若 preflight 存在且 confirmed_at 非空:
        → preflight 模式：后续 Step 中标记「若有 preflight → 跳过」的 AskUserQuestion 直接读取 preflight 值
        → 输出: 「检测到 Preflight 偏好配置，以下选择将自动应用: {摘要}」
      若 preflight 不存在:
        → 兼容模式：所有 AskUserQuestion 正常执行（向后兼容单独 /project-setup）
      ↓
Step 0: 模式识别
  existing 模式: 扫描工作目录下的 package.json / requirements.txt / go.mod / pom.xml 等
    → 自动检测已有子项目和技术栈
    → 与 product-map 模块对照，识别缺口
  new 模式: 从空白开始
  → 若从 project-forge 编排调用（forge-decisions.json 存在）→ 模式已确定，跳过
  → 若单独 /project-setup → AskUserQuestion 确认模式
  ↓
Step 1: 子项目拆分 + Monorepo 工具选择
  分析 product-map 中的角色和模块
  按角色类型提出拆分建议:
    consumer 角色 → 消费者前端
    producer 角色 → 管理后台
    admin 角色 → 管理后台（可与 producer 合并）
    全部角色共享 → API 后端
    有移动端需求 → 移动端子项目
  → 生成子项目列表（不停，汇总到 Step 5）
  AskUserQuestion: 选择 monorepo 工具 (pnpm workspace / Turborepo / Nx / 手动管理)
    → 若有 preflight → 跳过，使用 preflight.monorepo_tool
  → 每个子项目: id, name, type(backend/admin/web-customer/web-mobile/mobile-native)
  ↓
Step 2: 技术栈选择（逐子项目）
  对每个子项目:
    读取 templates/stacks.json → 过滤匹配 type 的模板
    AskUserQuestion: 从预设模板中选择
      → 若有 preflight → 跳过，使用 preflight.tech_preferences[子项目type].template_id
    → 记录选择到 tech-profile.json
  ↓
Step 3: 模块分配（逐子项目）
  读取 task-index.json → 展示模块列表
  智能推荐:
    后端: 默认分配全部模块（API 服务全部业务）
    admin 前端: 分配 producer/admin 角色的模块
    consumer 前端: 分配 consumer 角色的模块
    mobile: 分配移动端相关模块
  → 按智能推荐分配（不停，汇总到 Step 5）
  → 检查: 所有模块都被分配了吗？有遗漏则提示
  ↓
Step 4: 基础配置
  每子项目自动分配: 端口号（基于 stacks.json 默认端口，避免冲突）、base path
  AskUserQuestion: 确认 auth 策略 (JWT / Session / OAuth / 无)
    → 若有 preflight → 跳过，使用 preflight.auth_strategy
  → 自动分配端口（不停，汇总到 Step 5）
  ↓
Step 5: 生成 manifest + 汇总确认
  写入 project-manifest.json + project-manifest-report.md
  展示完整汇总表:
    | 子项目 | 类型 | 技术栈 | 模块 | 端口 |
    | 配置: Monorepo / Auth |
    | 模块覆盖率 |
  → AskUserQuestion: 确认 / 调整（逐项修改后重新生成 manifest）
```

---

## project-manifest.json 结构

```json
{
  "version": "1.0.0",
  "created_at": "ISO8601",
  "mode": "new | existing",
  "product_source": ".allforai/product-map/product-map.json",
  "monorepo": {
    "tool": "pnpm-workspace | turborepo | nx | manual",
    "root_name": "{project-name}"
  },
  "auth_strategy": "jwt | session | oauth | none",
  "sub_projects": [
    {
      "id": "sp-001",
      "name": "api-backend",
      "type": "backend",
      "stack": {
        "template_id": "nestjs-typeorm",
        "framework": "NestJS",
        "orm": "TypeORM",
        "database": "PostgreSQL",
        "architecture": "three-layer | ddd"
      },
      "port": 3001,
      "base_path": "./apps/api-backend",
      "is_existing": false,
      "assigned_modules": ["M001", "M002", "M003"],
      "assigned_roles": ["R001", "R002", "R003"],
      "status": "pending"
    },
    {
      "id": "sp-002",
      "name": "merchant-admin",
      "type": "admin",
      "stack": {
        "template_id": "nextjs",
        "framework": "Next.js 14",
        "css": "Tailwind CSS",
        "state_management": "zustand | redux-toolkit | jotai | context"
      },
      "port": 3000,
      "base_path": "./apps/merchant-admin",
      "is_existing": false,
      "assigned_modules": ["M001", "M003"],
      "assigned_roles": ["R001"],
      "state_management": {
        "library": "zustand",
        "pattern": "分模块 store，按功能切片"
      },
      "status": "pending"
    }
  ],
  "decisions": []
}
```

---

## 后端架构选择

后端子项目在 Step 2 中额外询问架构模式：

### 三层架构（Three-Layer）

```
适用: 中小型项目、CRUD 为主的业务

Controller → Service → Repository
  路由层      业务层     数据层

目录结构:
  src/
  ├── controllers/    # 处理 HTTP 请求/响应
  ├── services/       # 业务逻辑
  ├── repositories/   # 数据访问 (ORM 操作)
  ├── entities/       # 数据模型
  ├── dto/            # 数据传输对象
  └── middleware/      # 中间件

特点:
  - 简单直观，团队上手快
  - 每层单一职责
  - Service 可调用多个 Repository
  - Controller 不直接调用 Repository
```

### DDD（领域驱动设计）

```
适用: 复杂业务逻辑、多聚合根、跨域交互频繁

目录结构:
  src/
  ├── domain/              # 领域层（核心）
  │   ├── {aggregate}/
  │   │   ├── entities/    # 聚合根 + 实体
  │   │   ├── value-objects/  # 值对象
  │   │   ├── events/      # 领域事件
  │   │   ├── repository.interface.ts  # 仓储接口
  │   │   └── service.ts   # 领域服务
  │   └── shared/          # 共享内核
  │       └── base-entity.ts
  ├── application/         # 应用层
  │   ├── {use-case}/
  │   │   ├── command.ts   # 命令
  │   │   ├── handler.ts   # 命令处理器
  │   │   └── dto.ts       # 应用 DTO
  │   └── shared/
  │       └── event-bus.ts
  ├── infrastructure/      # 基础设施层
  │   ├── persistence/     # ORM 实现
  │   │   └── {aggregate}.repository.ts
  │   ├── messaging/       # 事件总线实现
  │   └── external/        # 外部服务集成
  └── interfaces/          # 接口层
      ├── http/
      │   ├── controllers/
      │   └── dto/         # 接口 DTO（区别于领域/应用 DTO）
      └── grpc/

特点:
  - 业务逻辑集中在 domain 层
  - 聚合根保护数据一致性
  - 领域事件驱动跨聚合通信
  - 仓储接口定义在 domain，实现在 infrastructure
  - CQRS 可选（读写分离）
```

AskUserQuestion 在后端子项目的 Step 2 中：
- "后端架构模式？" → 三层架构 (推荐: CRUD 为主) / DDD (推荐: 复杂业务)
  → 若有 preflight → 跳过，使用 preflight.tech_preferences.backend.architecture
- 选择 DDD 时追问: "是否启用 CQRS？" → 是 / 否
  → 若有 preflight → 跳过，使用 preflight.tech_preferences.backend.cqrs

---

## 前端状态管理选择

前端子项目在 Step 2 中额外询问状态管理方案：

### 状态管理方案对比

| 方案 | 适用场景 | 特点 |
|------|---------|------|
| **Zustand** | 中小型项目，轻量级需求 | 极简 API，无 boilerplate，TypeScript 友好，分 slice 组织 |
| **Redux Toolkit** | 大型项目，复杂状态流 | 标准化流程，强大的 DevTools，中间件生态 |
| **Jotai** | 原子化状态，组件级粒度 | 原子模型，按需订阅，避免不必要重渲染 |
| **React Context** | 简单共享状态（auth/theme） | 内置方案，无额外依赖，适合少量全局状态 |
| **Pinia** (Vue) | Vue 3 项目标准方案 | Vue 官方推荐，Composition API 友好 |

### 状态分层策略

```
无论选择哪种方案，状态都按以下层次组织:

1. 服务端状态（Server State）
   → React Query / SWR / TanStack Query
   → 缓存 API 响应、自动重验证、乐观更新
   → 占总状态 70%+，不放入状态管理库

2. 全局 UI 状态（Global UI State）
   → 状态管理库 (Zustand / Redux / Pinia)
   → auth token、用户信息、主题偏好、侧边栏折叠
   → 少量，稳定不变

3. 局部组件状态（Local State）
   → useState / useReducer / ref()
   → 表单输入、下拉展开、模态框显隐
   → 不进入全局状态
```

AskUserQuestion 在前端子项目的 Step 2 中：
- "状态管理方案？" → 列出与框架匹配的选项
  → 若有 preflight → 跳过，使用 preflight.tech_preferences[子项目type].state_management
- "服务端缓存方案？" → TanStack Query (推荐) / SWR / 手动管理
  → 若有 preflight → 跳过，使用 preflight.tech_preferences[子项目type].server_cache
- 选择后记录到 manifest 的 `state_management` 字段

---

## existing 模式处理

```
Step 0 扫描策略:
  1. Glob 工作目录下的 package.json / requirements.txt / go.mod / pom.xml / Cargo.toml
  2. 每个找到的项目配置文件 → 推测技术栈
  3. 读取路由/菜单/权限配置 → 推测子项目类型
  4. 与 product-map 模块对照:
     - 已实现的模块 → 标记 is_existing: true
     - 未实现的模块 → 标记为缺口，需要新建或补充
  5. 向用户展示检测结果，确认后继续
```

---

## 输出文件

```
.allforai/project-forge/
├── project-manifest.json           # 主产物
├── project-manifest-report.md      # 人类版
├── forge-decisions.json            # 用户决策记录
└── sub-projects/
    └── {name}/
        └── tech-profile.json       # 技术栈详细配置
```

### tech-profile.json

```json
{
  "sub_project_id": "sp-001",
  "sub_project_name": "api-backend",
  "type": "backend",
  "template_id": "nestjs-typeorm",
  "architecture": "three-layer",
  "framework": "NestJS",
  "language": "typescript",
  "orm": "TypeORM",
  "database": "PostgreSQL",
  "port": 3001,
  "auth_strategy": "jwt",
  "additional_config": {}
}
```

---

## 5 条铁律

### 1. 只问选择题，不问开放题

所有问题基于 product-map 分析和 stacks.json 生成选项。用户只需选择。

### 2. 阶段末汇总确认

中间步骤连续执行不停顿。Step 5 展示完整汇总，用户一次确认或逐项调整。
偏好类问题（技术栈/架构/状态管理/缓存/认证）由 `forge-decisions.json` 的 `preflight` 提供，不再询问。
单独 `/project-setup`（无 forge-decisions.json）时，Step 0 保留模式确认。

### 3. 模块必须全覆盖

Step 3 结束后，task-index 中的所有模块都必须被分配到至少一个子项目。未覆盖的模块必须在用户确认下解决。

### 4. 技术栈选择基于模板

只推荐 stacks.json 中已注册的技术栈。如果用户需要未注册的技术栈，记录需求但提示模板尚不支持自动脚手架。

### 5. manifest 是合约

project-manifest.json 是 project-setup 与下游 skill（design-to-spec、project-scaffold）的唯一合约。所有项目结构信息都在这个文件中。
