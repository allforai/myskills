---
name: project-scaffold
description: >
  Use when the user wants to "generate project scaffold", "create project skeleton",
  "scaffold from template", "generate boilerplate", "create mock server",
  "脚手架生成", "生成项目骨架", "创建项目模板", "生成 mock 后端",
  or needs to generate actual project files (directories, configs, boilerplate code)
  based on project-manifest and tech stack templates.
  Requires project-manifest.json and design docs from design-to-spec.
version: "1.0.1"
---

# Project Scaffold — 脚手架生成

> 按技术栈模板生成项目骨架 + Mock 后端，让代码可以立即启动

## 目标

以 `project-manifest.json` + 技术栈模板 + `design.md` 为输入，生成：

1. **Monorepo 根配置** — workspace 配置 + 共享包 + 基础配置文件
2. **各子项目骨架** — 目录结构 + 配置文件 + 入口文件 + 数据模型桩
3. **Mock 后端** — Express 服务 + 路由映射 + fixture 数据
4. **E2E 测试骨架** — Playwright 配置 + 场景目录

---

## 定位

```
design-to-spec（规格层）   project-scaffold（实现层）   Phase 4 任务执行
requirements/design/tasks   目录+配置+入口+模型桩        填充业务代码
文档层面                    文件层面                     代码层面
```

**前提**：
- 必须有 `.allforai/project-forge/project-manifest.json`
- 必须有各子项目的 `design.md`（至少有数据模型和 API 端点/页面路由）
- 推荐有 `.allforai/seed-forge/seed-plan.json`（mock 数据更丰富）

---

## 快速开始

```
/project-scaffold           # 全量生成
/project-scaffold full      # 同上
/project-scaffold sp-001    # 仅指定子项目
```

---

## 增强协议（WebSearch + 4E+4V）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：
- `"{framework} starter template {year}"`
- `"{framework} boilerplate best practices {year}"`
- `"{tech-stack} recommended packages {year}"`

**4E+4V 重点**：
- **E2 Provenance**: 生成的桩文件保留 provenance 注释（`// Source: design.md entity: order`）
- **E3 Guardrails**: 验证中间件桩文件包含 `// TODO: implement rules from T001.rules[1,2]` 占位

---

## 脚手架理论支持

> 详见 `docs/dev-forge-principles.md` — 中段：规格与实现

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|---------|---------|
| **Convention over Configuration** (DHH, 2004) | Step 2 文件生成 | 模板预定义目录结构和命名约定，零配置即可运行 |
| **Unix Philosophy** (McIlroy, 1978) | Step 2 文件生成 | 每文件单一职责；小模块组合而非大基类继承 |
| **Worse is Better** (Gabriel, 1989) | Step 3 Mock 生成 | 简单优先：mock-server 数据不完美但前端能立即开发 |
| **Tracer Bullet** (Hunt & Thomas, 1999) | 整体策略 | scaffold 先打通端到端最小路径（路由→handler→响应），再填充业务 |
| **YAGNI** (Jeffries, 1999) | Step 1 脚手架规划 | 只生成当前 spec 要求的文件，不为假设的未来需求预设抽象层 |
| **Separation of Concerns** (Dijkstra, 1974) | Step 2 目录结构 | models / services / controllers / views 按关注点分离 |
| **DRY** (Hunt & Thomas, 1999) | Step 1 Monorepo 根 | shared-types 提取公共类型，消除跨子项目的重复定义 |
| **Hexagonal Architecture** (Cockburn, 2005) | Step 3 Mock 后端 | mock 与真实后端是同一端口的不同适配器，前端代码无需修改 |

---

## 工作流

```
前置: 加载
  project-manifest.json → 子项目列表 + monorepo 配置
  各子项目 tech-profile.json → 技术栈配置
  各子项目 design.md → 数据模型 + API 端点/页面路由
  templates/stacks.json → 技术栈注册表
  .allforai/seed-forge/seed-plan.json → mock 数据蓝本（可选）
  ↓
Step 0: 模板加载
  逐子项目:
    从 tech-profile.json 获取 template_id
    从 stacks.json 获取 template_file 路径
    用 Read 加载对应 .md 模板文件
  → 模板全部就绪
  ↓
Step 1: 脚手架规划（逐子项目）
  new 模式:
    按模板定义的目录结构 → 完整文件清单
    配置文件（package.json / tsconfig / 框架配置）
    入口文件（main.ts / app.module.ts / layout.tsx）
    数据模型桩（从 design.md entities → ORM model / TypeScript interface）
    路由桩（从 design.md endpoints → 路由文件 + 空 handler）
  existing 模式:
    扫描已有目录结构
    与模板定义 diff → 仅补缺文件列表
    绝不覆盖已有文件
  → 展示将创建的文件清单 → AskUserQuestion 用户确认
  ↓
Step 2: Monorepo 根配置生成
  读取 templates/monorepo.md
  按 manifest.monorepo.tool 选择配置:
    pnpm-workspace → pnpm-workspace.yaml + package.json
    turborepo → turbo.json + package.json
    nx → nx.json + package.json
    manual → 仅 package.json（部分 workspace）
  生成:
    根 package.json（workspace 脚本）
    tsconfig.base.json（JS/TS 项目）
    .eslintrc.js / .prettierrc
    .gitignore
    .env.example
  生成 packages/shared-types/:
    从 design.md 的数据模型 → entities.ts + api-types.ts + enums.ts
  → 写入文件 → 记入 scaffold-manifest.json
  ↓
Step 3: 子项目骨架生成（逐子项目）
  按模板规则创建:
    目录结构
    配置文件（package.json / tsconfig.json / 框架配置）
    入口文件
    数据模型桩（仅类型定义和字段，无业务逻辑）
    路由桩（仅端点注册，handler 为 TODO 占位）
    组件桩（前端：仅空组件文件 + 导入导出）
  → 写入文件 → 记入 scaffold-manifest.json
  ↓
Step 4: Mock 后端生成
  读取 templates/mock-server.md
  从后端子项目的 design.md 提取 API 端点列表
  生成 apps/mock-server/:
    server.js（Express 入口）
    routes.json（端点 → 响应映射）
    middleware/（auth + delay + cors + image-proxy）
    fixtures/（各实体的 mock 数据 JSON）
    package.json
  数据来源:
    有 seed-plan.json → 按其数量设计和实体结构生成 fixture
    无 seed-plan.json → 每实体 3-5 条最小数据
  图片处理:
    fixtures/image-map.json → 图片 ID → 真实 URL 映射
    middleware/image-proxy.js → /api/images/{id} 代理
  → 写入文件 → 记入 scaffold-manifest.json
  ↓
Step 5: E2E 测试骨架生成
  创建 e2e/:
    playwright.config.ts（多子项目端口配置）
    scenarios/（空目录，e2e-verify 阶段填充）
    fixtures/（空目录）
  → 写入文件
  ↓
Step 6: 启动验证
  提示用户:
    1. 安装依赖: pnpm install（或对应包管理器）
    2. 启动 mock-server: pnpm mock
    3. 验证: curl http://localhost:4000/health
  等待用户确认结果
  → 记录验证结果到 build-log.json
```

---

## scaffold-manifest.json

记录每个生成的文件，供后续追踪：

```json
{
  "generated_at": "ISO8601",
  "mode": "new | existing",
  "files": [
    {
      "path": "apps/api-backend/src/entities/order.entity.ts",
      "sub_project": "sp-001",
      "type": "entity-stub",
      "source": "design.md entity: order",
      "overwritten": false
    }
  ],
  "stats": {
    "total_files": 85,
    "by_sub_project": {
      "api-backend": 30,
      "merchant-admin": 25,
      "mock-server": 15,
      "shared": 10,
      "e2e": 5
    }
  }
}
```

---

## New vs Existing 模式

| 维度 | New | Existing |
|------|-----|----------|
| 目录创建 | 全量 | 仅补缺 |
| 配置文件 | 全量 | 仅补缺，不覆盖 |
| 数据模型 | 全量生成 | 仅新增的 entity |
| 路由桩 | 全量生成 | 仅新增的端点 |
| Mock 数据 | 全量 | 合并到已有 fixtures |
| package.json | 新建 | 追加依赖（不改已有） |

**existing 模式核心原则**：**绝不覆盖已有文件**。仅在缺失位置添加新文件。

---

## 输出文件

```
{project-root}/
├── package.json                    # Monorepo 根（Step 2）
├── {workspace-config}              # Step 2
├── tsconfig.base.json              # Step 2
├── .env.example                    # Step 2
├── apps/
│   ├── {sub-project}/              # Step 3（每个子项目）
│   └── mock-server/                # Step 4
├── packages/
│   └── shared-types/               # Step 2
├── e2e/                            # Step 5
└── .allforai/project-forge/
    └── sub-projects/{name}/
        ├── scaffold-manifest.json  # 文件清单
        └── build-log.json          # 构建日志
```

---

## 5 条铁律

### 1. 骨架是桩，不是实现

脚手架只生成目录结构、配置文件、入口文件、数据模型桩（字段定义）、路由桩（空 handler）。业务逻辑由 Phase 4 任务执行阶段填充。

### 2. existing 绝不覆盖

已有文件一律跳过。仅在空缺位置补充。出现冲突时向用户报告，由用户决定。

### 3. Mock 数据来自 seed-forge

mock-server 的 fixture 数据优先使用 seed-plan.json。无 seed-plan 时使用最小占位数据。

### 4. 文件清单全记录

每个生成的文件都记入 scaffold-manifest.json，包含路径、来源、子项目归属。

### 5. 启动验证是必须的

Step 6 必须提示用户安装依赖并启动 mock-server 验证。不可跳过。
