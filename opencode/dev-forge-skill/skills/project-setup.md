---
name: project-setup
description: >
  Use when the user wants to "set up project structure", "split into sub-projects",
  "choose tech stack", "configure monorepo", "project setup", "项目引导",
  "拆分子项目", "选技术栈", "配置 monorepo", "项目结构设计",
  or needs to plan how to organize a multi-project codebase from product-design artifacts.
  Requires product-map to have been run first.
version: "1.3.0"
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

## 增强协议（网络搜索 + 4E+4V）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**网络搜索关键词**：
- `"{tech-stack} project structure best practices {year}"`
- `"monorepo vs polyrepo {language} {year}"`
- `"{framework} clean architecture layout {year}"`

**4E+4V 重点**：
- **E4 Context**: manifest 中的 `decision_rationale` 保留技术选型理由（为什么选这个栈、为什么这样拆）
- **E2 Provenance**: 每个子项目的 assigned_modules 可追溯到 product-map 模块 ID

---

## 架构决策原则

> 以下原则在各步骤中强制执行，违反时向用户报告。

| 原则 | 对应步骤 | 具体规则 |
|------|---------|---------|
| 单一职责拆分 | Step 1 | 每子项目只承担一个端类型职责（backend/admin/mobile），禁止前后端混合在同一子项目 |
| 按角色边界拆分 | Step 1 | consumer 角色 → 消费者前端；producer/admin 角色 → 管理后台；共享 API → 后端。不同角色类型不混入同一前端 |
| 上下文隔离 | Step 3 | 同一业务实体在不同端可有不同字段视角（如 Order 在 admin 有审核字段，在 consumer 无）。跨子项目通过 shared-types 共享基础类型 |
| 配置外置 | Step 4 | 数据库/API 地址/密钥等全部走 `.env`，代码中禁止硬编码。每子项目独立 `.env.example` |
| 端口隔离 | Step 4 | 每子项目独占端口（从 stacks.json 默认端口分配），禁止端口冲突 |
| manifest 即合约 | Step 5 | 所有项目结构决策写入 project-manifest.json，下游 skill 只读 manifest，不从对话上下文推测 |

---

## 工作流

```
前置: 加载 .allforai/product-map/product-map.json
      加载 .allforai/product-map/task-index.json（索引优先）
      若不存在 → 提示先执行 product-map 工作流，终止
      ↓
前置: 上游过期检测
      加载输入文件时，比较关键上游文件的修改时间与本技能上次输出的生成时间：
      - product-map.json 在 project-manifest.json 生成后被更新
        → ⚠ 警告「product-map.json 在 project-manifest.json 生成后被更新，数据可能过期，建议重新运行 product-map」
      - 仅警告不阻断，用户可选择继续或先刷新上游
      ↓
前置: Preflight 偏好检测
      读取 .allforai/project-forge/forge-decisions.json → preflight 字段
      若 preflight 存在且 confirmed_at 非空:
        → 直接读取 preflight 值，跳过所有偏好选择（不停）
        → 输出: 「检测到 Preflight 偏好配置，以下选择将自动应用: {摘要}」
      若 preflight 不存在:
        → 自动采用推荐值（不停）：后端 Go+Gin、前端 Next.js、移动端 Flutter、Monorepo manual、Auth JWT
      ↓
Step 0: 模式识别
  existing 模式: 扫描工作目录下的 package.json / requirements.txt / go.mod / pom.xml 等
    → 自动检测已有子项目和技术栈
    → 与 product-map 模块对照，识别缺口
  new 模式: 从空白开始
  → 模式已确定（从参数或 forge-decisions.json 读取），自动继续（不停）
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
  自动选择 monorepo 工具: preflight.monorepo_tool（有 preflight 时）或 LLM 根据项目语言生态推理最适合的工具（不停）
  → 每个子项目: id, name, type(backend/admin/web-customer/web-mobile/mobile-native)
  ↓
Step 1.5: 架构 6V 审计 (Conway's Law Agent)
  调用 LLM Agent 对子项目拆分进行 XV 审计：
  1. **Role Isolation (V1)**: 验证子项目是否清晰隔离了不同角色（Consumer vs Admin）。
  2. **Bounded Context (V2)**: 验证模块分配是否符合领域驱动设计（DDD）的限界上下文。
  3. **Conway Conformity (V3)**: 验证系统架构是否正确映射了产品地图定义的组织/角色关系。
  4. **Communication Overhead (V4)**: 评估子项目间的通讯复杂度，预警过度耦合。
  5. **Tech Suitability (V5)**: 验证选定的子项目类型与模块功能的匹配度。
  6. **Module Coverage (V6)**: 检查是否有“孤儿模块”或被错误分配的边缘任务。
  → 发现严重冲突 → 触发「架构重构建议」并询问用户
  ↓
Step 2: 技术栈选择（逐子项目）
  对每个子项目:
    读取 templates/stacks.json → 过滤匹配 type 的模板
    自动选择: preflight.tech_preferences[子项目type].template_id（有 preflight 时）或推荐值（不停）
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
  每子项目自动分配: 端口号（LLM 根据技术栈常见默认端口推理，避免冲突）、base path
  自动选择 auth 策略: preflight.auth_strategy（有 preflight 时）或 LLM 根据项目类型推理最适合的方案（不停）
  → 自动分配端口（不停，汇总到 Step 5）
  ↓
Step 4.5: 开发者模式配置（Dev Mode）
  分析模块的实际外部服务集成，识别需要 dev bypass 的外部依赖：
    - 理解模块的业务语义，而非关键词匹配（如「支付」可能只是内部积分扣减，无需 bypass）
    - 为每个外部依赖推荐 bypass 策略和本地替代方案
    - bypass 配置值按项目域和地区生成，避免与真实数据冲突
  交互: 展示检测到的 bypass 列表，用户选择 A.全部接受 / B.逐项调整 / C.不启用
  安全等级: 固定 strict（接口隔离 + 构建时剔除 + CI 拦截）
  → 写入 forge-decisions.json#dev_mode（不停，汇总到 Step 5）
  ↓
Step 5: 生成 manifest + 汇总确认
  写入 project-manifest.json + project-manifest-report.md
  展示完整汇总表:
    | 子项目 | 类型 | 技术栈 | 模块 | 端口 |
    | 配置: Monorepo / Auth |
    | 模块覆盖率 |
    | 开发者模式：✅ 已启用（{N} 项 bypass：支付、短信、CAPTCHA）| 安全等级：strict |
    | （若未启用）开发者模式：❌ 未启用 |
  → 输出汇总进度「Phase 1 ✓ {N} 子项目, {M} 模块, 覆盖率 100%」（不停）
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
    "tool": "LLM 根据项目语言生态推理（如 pnpm-workspace / turborepo / nx / yarn-workspaces / cargo-workspaces / gradle / bazel / manual 等）",
    "root_name": "{project-name}"
  },
  "auth_strategy": "LLM 根据项目类型推理（如 jwt / session / oauth2 / passkey / api-key / none 等）",
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
  "dev_mode_ref": "forge-decisions.json#dev_mode",
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

后端子项目 Step 2 中自动选择：
- 后端架构模式: preflight.tech_preferences.backend.architecture（有 preflight 时）或按 product-map 复杂度推断（不停）
- CQRS: preflight.tech_preferences.backend.cqrs（有 preflight 时）或 false（不停）

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

前端子项目 Step 2 中自动选择：
- 状态管理: preflight.tech_preferences[子项目type].state_management（有 preflight 时）或按框架推荐（不停）
- 服务端缓存: preflight.tech_preferences[子项目type].server_cache（有 preflight 时）或 TanStack Query（不停）
- 记录到 manifest 的 `state_management` 字段

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
  5. 输出检测结果，自动继续（不停）
```

---

## Step 4.5 详细说明：开发者模式配置（Dev Mode）

识别项目中需要 dev bypass 的外部依赖，配置开发环境绕过策略。

**自动扫描**：从 Step 2 选定的技术栈 + Step 3 模块分配中，自动检测以下外部依赖类型：

| 依赖类型 | 检测方式 | 默认 bypass 策略 |
|---------|---------|-----------------|
| 支付网关 | 语义分析模块的外部支付集成 | `auto_callback` — 按项目域生成测试金额映射 |
| 短信/邮件验证 | 识别验证码发送逻辑 | `magic_value` — 按地区生成测试号段和验证码 |
| CAPTCHA | 识别人机验证集成 | `always_pass` — dev 环境跳过 |
| OAuth/第三方登录 | 识别社交登录/SSO 集成 | `test_account` — 预置测试账号 |
| 实名认证/KYC | 识别身份验证集成 | `always_pass` — dev 环境直接通过 |

> **检测原则**：分析模块业务语义，不依赖关键词匹配。以上仅为常见类型参考，实际按项目需求识别。

**交互**：

```
向用户展示选项并提问:
检测到以下外部依赖需要 dev bypass：

  1. ✅ 支付网关（auto_callback）
  2. ✅ 短信验证（magic_value: 138xxxx + "123456"）
  3. ✅ Google reCAPTCHA（always_pass）
  4. ❌ 文件上传 OSS（无需 bypass，用 MinIO）

选择：
  A. 全部接受（推荐）
  B. 逐项调整
  C. 不启用 dev mode
```

**安全等级**（不问用户，固定为 strict）：
- `strict`：接口隔离 + 构建时剔除 + CI 拦截（三重保护）

**写入 forge-decisions.json**：

```json
{
  "dev_mode": {
    "enabled": true,
    "safety_level": "strict",
    "bypasses": [
      {
        "type": "payment_gateway",
        "strategy": "auto_callback",
        "config": {
          "magic_amounts": "按项目域生成（避免与真实测试数据冲突）",
          "auto_callback_delay_ms": 1000,
          "env_flag": "DEV_PAYMENT_BYPASS"
        },
        "isolation": {
          "prod_file": "payment_alipay.go",
          "dev_file": "payment_dev.go",
          "guard": "build_tag"
        }
      },
      {
        "type": "sms_verification",
        "strategy": "magic_value",
        "config": {
          "magic_numbers": "按地区生成测试号段（避免与真实号码冲突）",
          "magic_code": "生成非常见密码的验证码",
          "env_flag": "DEV_SMS_BYPASS"
        },
        "isolation": {
          "prod_file": "sms_aliyun.go",
          "dev_file": "sms_dev.go",
          "guard": "build_tag"
        }
      }
    ],
    "ci_rules": {
      "block_bypass_in_prod_import": true,
      "scan_pattern": "_dev\\.(go|ts|tsx)$"
    }
  }
}
```

**不产生 bypass 的类型**（功能本身需要测试）：
- 文件上传 → 用 MinIO / 本地存储
- 消息推送 → 用本地模拟器
- 消息队列 → 用 Docker compose 本地 Redis/RabbitMQ
- 数据库 → 用 Docker compose 本地实例

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

中间步骤连续执行不停顿。Step 5 输出完整汇总，自动继续（不停）。
偏好类问题（技术栈/架构/状态管理/缓存/认证）由 `forge-decisions.json` 的 `preflight` 提供，不再询问。
单独 `/project-setup`（无 forge-decisions.json）时，Step 0 保留模式确认。

### 3. 模块必须全覆盖

Step 3 结束后，task-index 中的所有模块都必须被分配到至少一个子项目。未覆盖的模块自动分配到最匹配的子项目。

### 4. 技术栈选择基于模板

只推荐主流技术栈。如果用户需要小众技术栈，记录选择并继续，task-execute 的 LLM 会根据 design.md + 文档搜索自动适配。

### 5. manifest 是合约

project-manifest.json 是 project-setup 与下游 skill（design-to-spec、task-execute）的唯一合约。所有项目结构信息都在这个文件中。
