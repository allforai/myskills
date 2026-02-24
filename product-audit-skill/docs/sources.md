# Step 0: 项目画像 & 需求源发现

> feature-audit 插件的第一步：先搞清楚项目是什么、需求从哪来。
> 不做重量级分析，只做快速 profiling + source discovery。

---

## 1. 项目画像（轻量版）

目标：用最少的 I/O 判断项目技术栈、结构、关键文件位置。

### 1.1 检测流程

```
1. 读 package.json / pom.xml / build.gradle / requirements.txt / go.mod → 判断语言和框架
2. 检查顶层目录结构 → 判断 monorepo（apps/*, packages/*, projects/*）
3. 根据框架类型，定向扫描路由文件、菜单配置、API 定义
```

### 1.2 技术栈检测表

| Framework | 识别方式 | Route 文件 | Menu/Nav 文件 | API 定义文件 |
|-----------|---------|-----------|---------------|-------------|
| **Next.js** | `next` in dependencies | `app/**/page.{tsx,jsx}`, `pages/**/*.{tsx,jsx}` | `components/**/nav*`, `components/**/sidebar*`, `components/**/menu*` | `app/api/**/route.ts`, `pages/api/**/*.ts` |
| **React (CRA/Vite)** | `react-router-dom` in deps | `src/router.*`, `src/routes/**/*`, `src/App.tsx` 中的 `<Route>` | `src/**/menu*`, `src/**/nav*`, `src/**/sidebar*` | N/A (看后端) |
| **Vue (Vue Router)** | `vue-router` in deps | `src/router/**/*`, `src/router/index.{ts,js}` | `src/**/menu*`, `src/layout/**/*` | N/A (看后端) |
| **Nuxt** | `nuxt` in dependencies | `pages/**/*.vue` (文件系统路由) | `layouts/**/*.vue`, `components/**/nav*` | `server/api/**/*.ts` |
| **Angular** | `@angular/core` in deps | `**/*-routing.module.ts`, `app-routing.module.ts` | `**/*nav*`, `**/*menu*`, `**/*sidebar*` | N/A (看后端) |
| **NestJS** | `@nestjs/core` in deps | `**/*.controller.ts` | N/A | `**/*.controller.ts`, `swagger` 配置 |
| **Express** | `express` in deps | `routes/**/*`, `src/routes/**/*` | N/A | `routes/**/*`, `swagger.*` |
| **Spring Boot** | `pom.xml` with spring-boot | `**/*Controller.java` | N/A | `**/*Controller.java`, `swagger-config.*` |
| **Django** | `django` in requirements | `**/urls.py` | N/A | `**/urls.py`, `**/views.py` |
| **Go (Gin/Echo)** | `go.mod` with gin/echo | `**/*router*`, `**/*route*` | N/A | `**/handler*`, `docs/swagger.*` |

### 1.3 Monorepo 检测

```
检查以下目录是否存在：
- apps/*          → Turborepo / Nx 风格
- packages/*      → 通用 monorepo
- projects/*      → Angular workspace
- services/*      → 微服务结构
- lerna.json       → Lerna
- pnpm-workspace.yaml → pnpm workspace
- nx.json          → Nx
- turbo.json       → Turborepo
```

如果是 monorepo，需要对每个 app/service 分别做画像。

---

## 2. 需求源扫描

按优先级从高到低扫描。找到高优先级来源后，低优先级作为补充而非替代。

### 2.1 扫描优先级表

| 优先级 | 来源类型 | 扫描目标 | Glob 模式 | 提取内容 | 提取方式 |
|--------|----------|----------|-----------|----------|----------|
| 1 | PRD / 需求文档 | 正式需求文档 | `docs/**/*.md`, `**/prd.*`, `**/PRD.*`, `**/requirements.*`, `**/spec.*`, `**/specification.*` | 功能点列表、用户故事、验收标准 | 解析 markdown 标题层级（h2/h3），提取功能名 + 描述 |
| 2 | README | 项目 README 的功能描述 | `README.md`, `readme.md` | Features / 功能 章节下的列表项 | 定位 `## Features` 或 `## 功能` 章节，提取 bullet list |
| 3 | OpenAPI / Swagger | API 规范文档 | `swagger.*`, `openapi.*`, `**/swagger/**`, `**/api-docs/**`, `**/openapi/**` | API endpoints、操作描述、tags 分组 | 解析 YAML/JSON，提取 paths + operationId + summary + tags |
| 4 | CHANGELOG | 版本变更记录 | `CHANGELOG.md`, `changelog.md`, `HISTORY.md` | 功能新增记录（`Added` / `新增` 章节） | 解析 Keep a Changelog 格式，提取 `### Added` 下的条目 |
| 5 | 路由定义 | 前端/后端路由 | 见技术栈检测表 | 路由路径 + 路由名称 + 关联组件/handler | 解析 AST 或正则匹配 `path:`, `Route`, `@Get()` 等 |
| 6 | 菜单 / 导航配置 | UI 侧边栏、导航 | 见技术栈检测表 | 菜单项名称、层级结构、关联路由 | 解析 menu config 对象/数组，提取 `name`, `title`, `path` |
| 7 | 测试描述 | 测试用例标题 | `**/*.test.*`, `**/*.spec.*`, `**/test/**/*`, `**/tests/**/*`, `**/__tests__/**/*` | 功能维度的测试描述 | 提取 `describe('...')` 和 `it('...')` 的字符串参数 |

### 2.2 各来源详细提取规则

#### Priority 1: PRD / 需求文档

```
扫描: docs/**/*.md, **/prd.*, **/PRD.*, **/requirements.*
提取逻辑:
  1. 找到文件后，解析 markdown 结构
  2. h2 (##) 视为功能模块
  3. h3 (###) 视为子功能
  4. bullet list 视为功能点
  5. 如果有 "用户故事" / "User Story" 格式 → 提取 "As a... I want... So that..."
输出: { feature_name, description, sub_features[], acceptance_criteria[] }
```

#### Priority 2: README

```
扫描: README.md
提取逻辑:
  1. 定位 "## Features" / "## 功能" / "## What it does" 等章节
  2. 提取该章节下的 bullet list（- 或 *）
  3. 嵌套 list 视为子功能
输出: { feature_name, description }
```

#### Priority 3: OpenAPI / Swagger

```
扫描: swagger.{json,yaml,yml}, openapi.{json,yaml,yml}, **/swagger/**, **/api-docs/**
提取逻辑:
  1. 解析 OpenAPI spec
  2. 按 tags 分组 → 每个 tag 视为一个功能模块
  3. 每个 path + method → 视为一个功能点
  4. 提取 summary, description, operationId
输出: { module (tag), endpoint, method, summary, description }
```

#### Priority 4: CHANGELOG

```
扫描: CHANGELOG.md
提取逻辑:
  1. 按版本号分段
  2. 提取 "### Added" / "### 新增" 下的条目
  3. 忽略 "### Fixed" / "### Changed"（不是新功能）
输出: { version, feature_name, description }
```

#### Priority 5: 路由定义

```
根据技术栈选择对应的解析策略：

Next.js (App Router):
  扫描 app/**/page.tsx → 目录路径即路由路径
  提取: 路由路径, page 组件名

Vue Router:
  扫描 src/router/index.ts
  正则: /path:\s*['"]([^'"]+)['"]/  +  /name:\s*['"]([^'"]+)['"]/  +  /component:\s*.*?(['"].*?['"]|import\()/
  提取: path, name, component

React Router:
  扫描 src/router.* 或 src/routes/*
  正则: /<Route\s+path=["']([^"']+)["']/  或  /path:\s*['"]([^'"]+)['"]/
  提取: path, element/component

Angular:
  扫描 *-routing.module.ts
  正则: /path:\s*['"]([^'"]+)['"]/  +  /component:\s*(\w+)/
  提取: path, component

输出: { route_path, route_name, component, file }
```

#### Priority 6: 菜单 / 导航配置

```
扫描: **/menu*, **/nav*, **/sidebar*（结合技术栈）
提取逻辑:
  1. 找到菜单配置数组/对象
  2. 提取 name/title/label, path/route, icon, children
  3. children 递归处理
输出: { menu_name, path, children[], icon }
```

#### Priority 7: 测试描述

```
扫描: **/*.test.*, **/*.spec.*, **/__tests__/**
提取逻辑:
  1. 正则匹配 describe('...') 和 it('...')
  2. describe 视为功能模块
  3. it 视为功能点 / 行为描述
  4. 嵌套 describe 视为子模块
正则:
  /describe\(\s*['"`](.+?)['"`]/g
  /it\(\s*['"`](.+?)['"`]/g
输出: { module (describe), behavior (it), file }
```

---

## 3. 无文档场景（No-Doc Fallback）

当 Priority 1-4 均未找到有效内容时，触发无文档降级策略。

### 3.1 降级流程

```
if (PRD 文档未找到 && README 无 Features 章节 && 无 OpenAPI && 无 CHANGELOG) {
  // 进入无文档模式
  code_derived = true

  // 依赖以下来源推导功能清单：
  sources = [路由定义, 菜单/导航配置, README (整体), 测试描述]

  // 推导逻辑：
  // 1. 路由 → 每个路由路径视为一个页面/功能入口
  // 2. 菜单 → 菜单项视为用户可见的功能点
  // 3. 测试描述 → describe 标题视为功能模块

  // 合并去重：路由 path 和菜单 path 做 join，测试 describe 做模糊匹配
}
```

### 3.2 必须告知用户

进入无文档模式时，**必须**输出以下提示：

```
⚠ 未找到 PRD 或需求文档。
以下功能清单从代码推导而来，非来自需求文档。请确认是否准确，是否有遗漏。

推导来源：路由文件、菜单配置、测试描述
置信度：低（code-derived）
```

### 3.3 标记规则

所有从代码推导的功能项，必须标记：

```json
{
  "feature_name": "用户管理",
  "source": "code-derived",
  "derived_from": ["route:/admin/users", "menu:用户管理", "test:describe('UserManagement')"],
  "confidence": "low"
}
```

与之对比，来自 PRD 的功能项：

```json
{
  "feature_name": "用户管理",
  "source": "prd",
  "source_file": "docs/prd.md",
  "confidence": "high"
}
```

---

## 4. 用户确认点（User Checkpoints）

Step 0 结束前，必须向用户确认以下内容。**不要自动跳过确认。**

### 4.1 需求源确认

```
已发现以下需求来源：

1. [PRD] docs/prd.md (23 个功能点)
2. [OpenAPI] swagger.yaml (15 个 endpoints)
3. [路由] src/router/index.ts (18 条路由)
4. [菜单] src/config/menu.ts (12 个菜单项)

请确认：
- 以上需求源是否正确？有遗漏或已过时的吗？
- 有没有其他需求文档需要纳入？（例如 Confluence 页面、Notion 文档等外部来源）
```

### 4.2 项目结构确认

```
检测到项目结构：

技术栈: Next.js 14 (App Router) + NestJS
Monorepo: Yes (apps/web, apps/api)
路由文件: apps/web/app/**/page.tsx (18 files)
菜单文件: apps/web/src/config/menu.ts
API 定义: apps/api/src/**/*.controller.ts (8 files)

请确认：
- 以下路由/菜单文件是否准确反映了项目结构？
- 是否有已废弃的路由或页面需要排除？
```

### 4.3 等待用户回复

```
收到用户确认后：
- confirmed_by_user = true
- 更新 requirement_sources 的 status 字段
- 如果用户补充了外部来源 → 记录到 external_sources 字段
- 进入 Step 1（功能清单提取）
```

---

## 5. 输出格式

Step 0 的最终输出为 `audit-sources.json`，结构如下：

```json
{
  "project_profile": {
    "tech_stack": {
      "language": "TypeScript",
      "frontend": {
        "framework": "Next.js",
        "version": "14.x",
        "router_type": "app"
      },
      "backend": {
        "framework": "NestJS",
        "version": "10.x"
      }
    },
    "monorepo": true,
    "monorepo_tool": "turborepo",
    "apps": [
      { "name": "web", "path": "apps/web", "type": "frontend" },
      { "name": "api", "path": "apps/api", "type": "backend" }
    ],
    "route_files": [
      "apps/web/app/page.tsx",
      "apps/web/app/dashboard/page.tsx",
      "apps/web/app/admin/users/page.tsx"
    ],
    "menu_files": [
      "apps/web/src/config/menu.ts"
    ],
    "api_files": [
      "apps/api/src/users/users.controller.ts",
      "apps/api/src/auth/auth.controller.ts"
    ]
  },
  "requirement_sources": [
    {
      "type": "prd",
      "file": "docs/prd.md",
      "priority": 1,
      "status": "confirmed",
      "feature_count": 23
    },
    {
      "type": "openapi",
      "file": "swagger.yaml",
      "priority": 3,
      "status": "confirmed",
      "endpoint_count": 15
    },
    {
      "type": "route",
      "file": "apps/web/app/**/page.tsx",
      "priority": 5,
      "status": "confirmed",
      "route_count": 18
    },
    {
      "type": "menu",
      "file": "apps/web/src/config/menu.ts",
      "priority": 6,
      "status": "confirmed",
      "item_count": 12
    },
    {
      "type": "test",
      "file": "**/*.test.ts",
      "priority": 7,
      "status": "auto-detected",
      "describe_count": 30
    }
  ],
  "external_sources": [],
  "code_derived": false,
  "confirmed_by_user": false,
  "created_at": "2026-02-24T10:00:00Z"
}
```

### 5.1 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `project_profile.tech_stack` | object | 技术栈信息，含前端/后端框架及版本 |
| `project_profile.monorepo` | boolean | 是否为 monorepo 结构 |
| `project_profile.route_files` | string[] | 路由文件路径列表 |
| `project_profile.menu_files` | string[] | 菜单/导航配置文件路径列表 |
| `project_profile.api_files` | string[] | API 定义文件路径列表 |
| `requirement_sources[].type` | string | 来源类型: `prd`, `readme`, `openapi`, `changelog`, `route`, `menu`, `test` |
| `requirement_sources[].priority` | number | 优先级 1-7，数字越小优先级越高 |
| `requirement_sources[].status` | string | `auto-detected` / `confirmed` / `excluded` |
| `code_derived` | boolean | 是否进入了无文档降级模式 |
| `confirmed_by_user` | boolean | 用户是否已确认。Step 0 完成前必须为 true |
| `external_sources` | array | 用户补充的外部来源（Confluence、Notion 等） |

---

## 附录：Quick Reference

### Step 0 执行顺序

```
1. 项目画像 → 检测技术栈、monorepo、关键文件
2. 需求源扫描 → 按优先级 1-7 扫描
3. 无文档判断 → 如果 P1-P4 为空，标记 code_derived=true
4. 用户确认 → 展示结果，等待确认
5. 输出 audit-sources.json → 交给 Step 1
```

### 耗时预期

| 项目规模 | 预计耗时 |
|----------|---------|
| 小型项目 (< 50 files) | < 10s |
| 中型项目 (50-500 files) | 10-30s |
| 大型 monorepo (500+ files) | 30-60s |

核心原则：**快进快出，不做深度分析。深度分析留给 Step 1+。**

---

> **铁律速查** — 详见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-audit.md` 的「5 条铁律」章节。
> 本步骤强相关：**来源绑定**（每条需求源必须记录 file:line）、**保守分类**（不确定来源是否有效就标 needs_confirmation）。
