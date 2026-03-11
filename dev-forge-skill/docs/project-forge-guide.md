# Project Forge — 用户指南

> 从产品设计产物到可运行的 Monorepo 项目：自动化锻造全流程

## 概述

Project Forge 是 dev-forge-skill 的核心能力，将产品设计产物（`.allforai/product-map/` 等）自动转化为可运行的项目代码。

### 能力矩阵

| 技能 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **project-setup** | 拆子项目 + 选技术栈 | product-map | project-manifest.json |
| **design-to-spec** | 生成 spec 文档 | manifest + product-map | requirements + design + tasks |
| **task-execute** | 逐任务执行代码（R0 含项目初始化） | manifest + design + tasks | 项目代码 + build-log |
| **e2e-verify** | 跨端 E2E 测试 | manifest + business-flows | e2e-report |
| **product-verify** | 静态+动态产品验收 | product-map + code | verify-report |

### 前提条件

必须先完成产品设计流程：
```
/product-design full    # 生成 product-map, experience-map, use-case 等产物
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
/task-execute                # Step 3: 按 tasks.md 执行（R0 项目初始化 → R1-R4 业务实现）
/e2e-verify                  # Step 4: 跨端 E2E 验证
/product-verify              # Step 5: 产品验收（静态+动态）
```

---

## 全流程管线

```
/project-forge full

Phase 0 ── 产物检测 + 模式路由
            ↓
Phase 1 ── 项目引导 (project-setup)
            语义分析: 拆子项目 → 选技术栈 → 分模块
            输出: project-manifest.json
            ↓ 质量门禁
Phase 2 ── 设计转规格 (design-to-spec)
            FVL: LLM 生成 → LLM 审计 → XV 交叉验证 → 自动修正
            后端 Step 3b 完成后前端并行启动（与后端审计并行）
            输出: requirements.md + design.md + design.json + tasks.md
            ↓ 质量门禁
Phase 3 ── 任务执行 (task-execute)
            分析依赖图动态生成 Round 结构（不固定 B0-B5）
            质量检查三路并行（lint ∥ test ∥ security）
            ↓ 质量门禁
Phase 4 ── 验证闭环 (product-verify + e2e-verify)
            S1-S4 四路并行 Subagent + D2∥D3 并行 Playwright
            静态+动态验收 → 修复 → 回归
            ↓ 质量门禁
Phase 5 ── 演示数据方案 (demo-forge design)
            代码稳定后设计演示数据
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
        └── build-log.json          # 构建日志
```

---

---

## 理论驱动的决策

Dev Forge 的每个阶段都扎根于经典软件工程理论，并通过 WebSearch 补充最新实践。

| 阶段 | 核心理论 |
|------|---------|
| project-setup | Unix Philosophy（做一件事做好）、Conway's Law（架构映射组织）、DDD Bounded Context |
| design-to-spec | Clean Architecture（依赖向内）、Hexagonal Architecture（端口与适配器）、API-First、C4 Model |
| e2e-verify | Test Pyramid / Trophy、BDD（Given/When/Then）、Contract Testing |
| task-execute | Incremental XV、Contract Drift Sync、DevSecOps Shift-Left |
| product-verify | ATDD、Heuristic Evaluation、Shift-Left Quality |

每个 skill 执行时会通过 WebSearch 搜索最新趋势文章，搜索结果记录到 `trend-sources.json`，标注 ADOPT / REJECT / DEFER。

> 详见 `docs/dev-forge-principles.md` — 完整理论映射与参考文献

---

## 常见问题

### Q: 已有项目如何使用？

```
/project-forge existing
```

Phase 1 会扫描已有代码，自动检测技术栈和子项目结构。existing 模式下只执行缺口任务。

### Q: 如何跳过某个阶段？

在 `/project-forge full` 执行过程中，每个阶段的质量门禁处可以选择跳过。也可以分步执行（单独运行各 `/xxx` 命令）。

### Q: 如何添加不在列表中的技术栈？

在 project-setup 中选择最接近的技术栈，task-execute 的 LLM 会根据 design.md + context7 文档搜索自动适配框架约定。

### Q: task-execute 选哪种执行方式？

- **subagent-driven-development**：首次使用推荐，每个任务有审查环节
- **dispatching-parallel-agents**：模块独立性好时推荐，速度快
- **手动执行**：想精细控制每个任务时使用
