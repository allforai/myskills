# Project Forge — 用户指南

> 从产品设计产物到可运行的 Monorepo 项目：自动化锻造全流程

## 概述

Project Forge 是 dev-forge-skill 的核心能力，将产品设计产物（`.allforai/product-map/` 等）自动转化为可运行的项目代码。

### 能力矩阵

| 技能 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **project-setup** | 拆子项目 + 选技术栈 | product-map | project-manifest.json |
| **design-to-spec** | 生成 spec 文档 | manifest + product-map | requirements + design + tasks |
| **project-scaffold** | 生成项目骨架 | manifest + design + templates | 代码文件 + mock-server |
| **e2e-verify** | 跨端 E2E 测试 | manifest + business-flows | e2e-report |

### 前提条件

必须先完成产品设计流程：
```
/product-design full    # 生成 product-map, screen-map, use-case 等产物
```

---

## 快速开始

### 一键全流程

```
/project-forge full          # 新项目，全流程
/project-forge existing      # 已有项目，gap 模式
/project-forge resume        # 从上次中断处继续
```

### 分步执行

```
/project-setup               # Step 1: 拆子项目 + 选技术栈
/design-to-spec              # Step 2: 生成 spec 文档
/seed-forge plan             # Step 2.5: 种子数据方案
/project-scaffold            # Step 3: 生成项目骨架
# Phase 4: 按 tasks.md 执行（使用 superpowers）
/e2e-verify                  # Step 5: 跨端 E2E 验证
```

---

## 全流程管线

```
/project-forge full

Phase 0 ── 产物检测 + 模式路由
            ↓
Phase 1 ── 项目引导 (project-setup)
            交互式: 拆子项目 → 选技术栈 → 分模块
            输出: project-manifest.json
            ↓ 质量门禁
Phase 2 ── 设计转规格 (design-to-spec)
            product-design 产物 → spec 文档
            输出: requirements.md + design.md + tasks.md
            ↓ 质量门禁
Phase 2.5 ── 种子数据方案
            提示运行 /seed-forge plan
            输出: seed-plan.json
            ↓
Phase 3 ── 脚手架生成 (project-scaffold)
            模板 → 项目骨架 + mock-server
            输出: 代码文件 + apps/mock-server/
            ↓ 质量门禁
Phase 4 ── 任务执行
            按 Round 依赖顺序:
            R0: Monorepo Setup
            R1: Foundation (并行)
            R2: Backend API ∥ Frontend UI (连 mock)
            R3: api-client + Integration (切换真实后端)
            R4: Testing
            ↓ 质量门禁
Phase 5 ── 跨端验证 (e2e-verify)
            business-flows → E2E 场景 → Playwright
            输出: e2e-report
            ↓
Phase 6 ── 最终报告
```

---

## 支持的技术栈

### 后端

| ID | 技术栈 | 语言 |
|----|--------|------|
| nestjs-typeorm | NestJS + TypeORM + PostgreSQL | TypeScript |
| spring-boot-jpa | Spring Boot + JPA + PostgreSQL | Java |
| flask-sqlalchemy | Flask + SQLAlchemy + PostgreSQL | Python |
| django-rest | Django + DRF + PostgreSQL | Python |
| go-gin | Go + Gin + GORM + PostgreSQL | Go |
| fastapi | FastAPI + SQLAlchemy + PostgreSQL | Python |
| rails-postgres | Ruby on Rails + PostgreSQL | Ruby |
| laravel | Laravel + Eloquent + PostgreSQL | PHP |

### Web 前端

| ID | 技术栈 | 渲染 |
|----|--------|------|
| nextjs | Next.js 14 (App Router) + Tailwind | SSR/SSG/CSR |
| nuxt | Nuxt 3 + Tailwind | SSR/SSG/CSR |
| angular | Angular + Angular Material | CSR |
| sveltekit | SvelteKit + Tailwind | SSR/SSG/CSR |
| vite-react | Vite + React + Tailwind (SPA) | CSR |
| vite-vue | Vite + Vue 3 + Tailwind (SPA) | CSR |

### 移动端

| ID | 技术栈 | 平台 |
|----|--------|------|
| react-native-expo | React Native + Expo | iOS + Android |
| flutter | Flutter + Dart | iOS + Android |

### Monorepo 工具

| 工具 | 适用场景 |
|------|---------|
| pnpm workspace | 纯 JS/TS 项目，轻量 |
| Turborepo | JS/TS 项目，需构建缓存 |
| Nx | 大型多语言项目 |
| 手动管理 | 混合语言（Go/Java + JS） |

---

## 子项目类型

| 类型 | 说明 | Batch 结构 |
|------|------|-----------|
| **backend** | API 服务端 | B1→B2→B4→B5（无 B3 UI） |
| **admin** | 管理后台 | B1→B3→B4→B5（无 B2 API） |
| **web-customer** | 消费者 Web | B1→B3→B4→B5 + SEO/性能 |
| **web-mobile** | H5 / PWA | B1→B3→B4→B5 + PWA/离线 |
| **mobile-native** | RN / Flutter | B1→B3→B4→B5 + 原生特性 |

---

## 产物目录结构

```
.allforai/project-forge/
├── project-manifest.json           # 总清单
├── project-manifest-report.md      # 人类版
├── forge-decisions.json            # 全程决策记录
├── forge-report.json               # 最终报告（机器版）
├── forge-report.md                 # 最终报告（人类版）
├── e2e-scenarios.json              # 跨端场景
├── e2e-report.json                 # E2E 结果（机器版）
├── e2e-report.md                   # E2E 结果（人类版）
└── sub-projects/
    └── {name}/
        ├── tech-profile.json       # 技术栈配置
        ├── requirements.md         # 需求文档
        ├── design.md               # 设计文档
        ├── tasks.md                # 任务列表
        ├── scaffold-manifest.json  # 脚手架清单
        └── build-log.json          # 构建日志
```

---

## Mock 后端工作机制

Phase 3 生成的 mock-server 让前端可以在后端 API 完成前开始开发：

```
前端 B3 阶段 ────→ mock-server (localhost:4000)
                    ├── routes.json (API 映射)
                    ├── fixtures/ (mock 数据)
                    └── middleware/image-proxy (图片代理)

后端 B2 完成后 ───→ 切换环境变量
前端 B4 阶段 ────→ 真实后端 (localhost:3001)
```

**图片代理**：前端代码中使用 `/api/images/{id}`，mock-server 代理到网络图片 URL，切换到真实后端后路径不变。

---

## 自定义模板指南

### 模板文件结构

每个技术栈模板是一个 `.md` 文件，包含以下章节：

```markdown
# {Framework} + {ORM} 模板

## 目录结构
## 数据模型生成规则（product-map entity → ORM model）
## 路由生成规则（task → API route / page route）
## 配置文件模板（package.json / tsconfig / 框架配置等）
## 命名约定（文件名 / 变量名 / 表名）
## Batch 结构（该技术栈的 B1-B5 内容）
```

### 添加新模板的步骤

1. 在 `templates/backend/` 或 `templates/web/` 或 `templates/mobile/` 下创建 `.md` 文件
2. 参考已有模板（如 `nestjs-typeorm.md`、`nextjs.md`）编写内容
3. 在 `templates/stacks.json` 中注册新条目
4. 测试：运行 `/project-scaffold` 验证模板生成效果

### 模板编写原则

- **具体文件路径**：模板中的目录结构和文件名必须是可直接创建的具体路径
- **映射规则明确**：从 product-map entity/task/screen 到框架概念的映射必须有明确规则
- **配置可用**：package.json 等配置文件必须包含正确的依赖版本
- **命名一致**：文件名、类名、路由名的命名约定必须自洽

---

## 理论驱动的决策

Dev Forge 的每个阶段都扎根于经典软件工程理论，并通过 WebSearch 补充最新实践。

| 阶段 | 核心理论 |
|------|---------|
| project-setup | Unix Philosophy（做一件事做好）、Conway's Law（架构映射组织）、DDD Bounded Context |
| design-to-spec | Clean Architecture（依赖向内）、Hexagonal Architecture（端口与适配器）、API-First、C4 Model |
| project-scaffold | Convention over Configuration、Worse is Better（简单优先）、Tracer Bullet（曳光弹）、YAGNI |
| e2e-verify | Test Pyramid / Trophy、BDD（Given/When/Then）、Contract Testing |
| seed-forge | Boundary Value Analysis、Equivalence Partitioning |
| product-verify | ATDD、Heuristic Evaluation、Shift-Left Quality |

每个 skill 执行时会通过 WebSearch 搜索最新趋势文章，搜索结果记录到 `trend-sources.json`，标注 ADOPT / REJECT / DEFER。

> 详见 `docs/dev-forge-principles.md` — 完整理论映射与参考文献

---

## 常见问题

### Q: 已有项目如何使用？

```
/project-forge existing
```

Phase 1 会扫描已有代码，自动检测技术栈和子项目结构。Phase 3 仅补缺文件，绝不覆盖已有代码。

### Q: 如何跳过某个阶段？

在 `/project-forge full` 执行过程中，每个阶段的质量门禁处可以选择跳过。也可以分步执行（单独运行各 `/xxx` 命令）。

### Q: 如何添加不在列表中的技术栈？

1. 创建模板文件并注册到 stacks.json
2. 或者在 project-setup 中选择最接近的模板，Phase 3 后手动调整

### Q: Phase 4 选哪种执行方式？

- **subagent-driven-development**：首次使用推荐，每个任务有审查环节
- **dispatching-parallel-agents**：模块独立性好时推荐，速度快
- **手动执行**：想精细控制每个任务时使用
