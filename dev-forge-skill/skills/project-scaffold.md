---
name: project-scaffold
description: >
  Use when the user wants to "generate project scaffold", "create project skeleton",
  "scaffold from template", "generate boilerplate", "create mock server",
  "脚手架生成", "生成项目骨架", "创建项目模板", "生成 mock 后端",
  or needs to generate actual project files (directories, configs, boilerplate code)
  based on project-manifest and tech stack templates.
  Requires project-manifest.json and design docs from design-to-spec.
version: "1.2.0"
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

## 增强协议（WebSearch + 4E+4V + OpenRouter）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：
- `"{framework} starter template {year}"`
- `"{framework} boilerplate best practices {year}"`
- `"{tech-stack} recommended packages {year}"`

**4E+4V 重点**：
- **E2 Provenance**: 生成的桩文件保留 provenance 注释（`// Source: design.md entity: order`）
- **E3 Guardrails**: 验证中间件桩文件包含 `// TODO: implement rules from T001.rules[1,2]` 占位

**OpenRouter 依赖检查**：
- **`dependency_check`** (GPT) — Step 3 生成 package.json 后，将依赖列表发送给 GPT 审查：
  - 主要依赖是否有已知弃用（deprecated）或安全漏洞
  - 版本号是否严重过时（落后 2+ 大版本）
  - 依赖间是否有已知兼容性冲突
  - 输出: `{ "outdated": [...], "deprecated": [...], "conflicts": [...] }`
  - 有问题 → 在输出进度中标注告警，记录到 build-log.json（不停）
- OpenRouter 不可用 → 跳过检查

---

## 脚手架生成原则

> 以下原则在各步骤中强制执行，生成的脚手架必须符合这些规则。

| 原则 | 对应步骤 | 具体规则 |
|------|---------|---------|
| 约定优于配置 | Step 2 | 模板预定义目录结构（`controllers/` `services/` `entities/`）和命名约定（`user.entity.ts`），生成的代码零配置即可 `pnpm dev` 启动 |
| 每文件单一职责 | Step 2 | 一个 entity 一个文件、一个 service 一个文件。禁止 God file（单文件超 300 行则应拆分） |
| Mock 简单可用 | Step 4 | mock-server 数据不需要完美，但必须覆盖所有 API 端点且格式正确。前端能立即连接开发。**mock fixture 使用 happy-path 正常值**，不需要边界值/极值/异常数据（边界值由 seed-forge 种子数据负责） |
| 先通后优 | 整体策略 | scaffold 先打通最小路径（路由 → handler → 200 响应），让 `pnpm dev` + `curl` 能通。业务逻辑后续填充 |
| 只生成 spec 要求的 | Step 1 | 只生成 design.md 中定义的 entity/endpoint/page 对应的文件。不预设未出现在 spec 中的抽象层（如未要求 cache 就不生成 cache 层） |
| 关注点分离目录 | Step 2 | 后端: `entities/` `services/` `controllers/` `dto/` `middleware/` 严格分层。前端: `components/` `pages/` `hooks/` `services/` 分离 |
| 跨项目类型统一 | Step 2 | shared-types 提取所有子项目共享的 entity 类型和 enum。各子项目 import from `@shared/types`，禁止本地重复定义 |
| Mock 与真实后端同接口 | Step 4 | mock-server 端点路径和响应格式与后端 design.md 完全一致。前端切换 mock/真实后端只需改 `BASE_URL` 环境变量 |

---

## 工作流

```
前置: 加载
  project-manifest.json → 子项目列表 + monorepo 配置
  各子项目 tech-profile.json → 技术栈配置
  各子项目 design.md → 数据模型 + API 端点/页面路由
  templates/stacks.json → 技术栈注册表
  .allforai/seed-forge/seed-plan.json → mock 数据蓝本（可选）
  forge-decisions.json → technical_spikes 数组（可选，用于 SDK 依赖注入）
  ↓
前置: 上游过期检测
  加载输入文件时，比较关键上游文件的修改时间与本技能上次输出的生成时间：
  - design.md 在 scaffold-manifest.json 生成后被更新
    → ⚠ 警告「design.md 在 scaffold-manifest.json 生成后被更新，数据可能过期，建议重新运行 design-to-spec」
  - project-manifest.json 在 scaffold-manifest.json 生成后被更新
    → ⚠ 警告「project-manifest.json 在 scaffold-manifest.json 生成后被更新，数据可能过期，建议重新运行 project-setup」
  - 仅警告不阻断，用户可选择继续或先刷新上游
  ↓
  执行模式: Step 1 不确认, Step 6 自动验证（不停）
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
  → 输出进度「Step 1 脚手架规划 ✓ {N} 文件 ({breakdown by sub-project})」（不停）
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
  → 输出进度: 「Step 2 Monorepo 根 ✓ {N} 文件」
  ↓
Step 3: 子项目骨架生成（逐子项目）
  按模板规则创建:
    目录结构
    配置文件（package.json / tsconfig.json / 框架配置）
    入口文件
    数据模型桩（仅类型定义和字段，无业务逻辑）
    路由桩（仅端点注册，handler 为 TODO 占位）
    组件桩（前端：仅空组件文件 + 导入导出）
    Spike SDK 依赖注入（forge-decisions.json 存在 technical_spikes 时）:
      过滤 affected_tasks 与当前子项目任务有交集的 spike（通过 task-index.json 模块→任务映射解析）
      每个匹配 spike 的 decision.sdk → 追加到 package.json dependencies
      例: spike.sdk = "openai" → dependencies: { "openai": "^4.x" }
      例: spike.sdk = "azure-cognitiveservices-speech" → dependencies: { "microsoft-cognitiveservices-speech-sdk": "^1.x" }
      spike.status = "tbd" 或 decision.sdk 为空 → 跳过 SDK 注入，在 package.json 添加 TODO 注释: `// TODO: TS{N} 技术方案待定，确认后补充依赖`
  → 写入文件 → 记入 scaffold-manifest.json
  → 输出进度: 「Step 3 子项目骨架 ✓ {N} 文件 × {M} 子项目」
  ↓
Step 3.5: 依赖交叉检查（OpenRouter 可用时）
  收集所有子项目 package.json / requirements.txt / go.mod / pubspec.yaml 的依赖列表
  调用: mcp__plugin_product-design_openrouter__ask_model(task: "structured_output", model_family: "gpt", temperature: 0.1)
  审查: 弃用包、严重过时版本、已知兼容性冲突
  有问题 → 输出告警表:
    | 子项目 | 依赖 | 问题 | 建议 |
    |--------|------|------|------|
    | api-backend | express@3.x | 落后 2 大版本 | 升级到 express@4.x |
    → 记录告警到 build-log.json（不停，不自动修改依赖版本）
  无问题 → 输出: 「Step 3.5 依赖检查 ✓ 无告警」
  OpenRouter 不可用 → 跳过，输出: 「Step 3.5 ⊘ 跳过」
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
  → 输出进度: 「Step 4 Mock 后端 ✓ {N} 文件, {M} 端点」
  ↓
Step 5: E2E 测试骨架生成
  创建 e2e/:
    playwright.config.ts（多子项目端口配置）
    scenarios/（空目录，e2e-verify 阶段填充）
    fixtures/（空目录）
  → 写入文件
  → 输出进度: 「Step 5 E2E 骨架 ✓」
  ↓
Step 6: 启动验证
  Forge 编排模式（自动验证）:
    Bash: pnpm install（自动执行，检查退出码）
    Bash: 启动 mock-server（后台）
    Bash: curl -s -o /dev/null -w "%{http_code}" http://localhost:4000/health
    全部通过 → 输出: 「Step 6 启动验证 ✓ 依赖安装成功, mock-server 可达」（不停）
    失败 → 记录失败到 build-log.json，继续下一阶段（不停）
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

已有文件一律跳过。仅在空缺位置补充。出现冲突时记录到 build-log.json，跳过冲突文件。

### 3. Mock 数据来自 seed-forge

mock-server 的 fixture 数据优先使用 seed-plan.json。无 seed-plan 时使用最小占位数据。

### 4. 文件清单全记录

每个生成的文件都记入 scaffold-manifest.json，包含路径、来源、子项目归属。

### 5. 启动验证是必须的

Step 6 启动验证必须执行。自动执行验证（pnpm install + mock 启动 + health check），失败时记录到 build-log.json 继续（不停）。验证步骤本身不可省略。
