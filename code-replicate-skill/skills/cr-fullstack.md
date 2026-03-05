---
name: cr-fullstack
description: >
  Use when user wants to "replicate full project", "综合复刻", "全栈复刻",
  "前后端一起迁移", "fullstack rewrite", "clone entire project",
  "replicate both frontend and backend", or mentions analyzing both
  frontend and backend code together for cross-layer consistency.
version: "1.0.0"
---

# CR Fullstack — 综合复刻（前后端交叉验证）

> 先加载协议基础: `${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md`

> **Phase 委托**：本技能覆盖 Phase 1（增强）/2/3（增强）/4/6/7 的 fullstack 特有部分。Phase 1/3/5/7 的基础流程由 core 协议处理，本技能在其基础上增强（额外收集双栈路径、额外展示交叉验证信息等）。

综合逆向分析：在后端 + 前端**各自**分析的基础上，增加**交叉验证层** — API 绑定、Schema 对齐、约束一致性、认证传播、错误映射。不是"跑两遍"，而是单次分析 + 交叉验证。

---

## 项目类型检测

Phase 2 完成双栈识别后，确认项目结构属于以下类型之一：

| 类型 | 检测特征 | 处理方式 |
|------|---------|---------|
| **Monorepo** | 根目录下 `backend/`/`server/`/`api/` + `frontend/`/`client/`/`web/`/`app/` | 自动识别前后端路径 |
| **单目录全栈** | Next.js（`app/api/` + `app/`）、Nuxt（`server/` + `pages/`） | 按文件类型分区 |
| **多仓库** | 用户指定两个路径或 URL | 分别 clone/读取 |

**降级检测**：若只发现一端（仅后端或仅前端）→ 输出提示：

```markdown
### 仅检测到{backend/frontend}代码

路径: {path}（{stack}）
建议：运行 `/cr-backend` 或 `/cr-frontend` 替代。

若确实包含前后端代码，请手动指定路径：
`/cr-fullstack ./src --backend-path server --frontend-path client`
```

---

## Phase 1 Preflight（增强）

在 core Preflight 基础上，额外收集：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 后端路径 | {backend_path} | 后端代码目录（相对于源码根目录） |
| 前端路径 | {frontend_path} | 前端代码目录（相对于源码根目录） |
| 后端目标技术栈 | {backend_target_stack} | 后端用什么技术栈重写 |
| 前端目标技术栈 | {frontend_target_stack} | 前端用什么技术栈重写 |

**自动检测逻辑**：
- 扫描根目录结构，匹配常见 monorepo 模式
- 单目录全栈项目（如 Next.js）→ 按文件类型分区（`app/api/`=后端，其余=前端）
- 若只发现一端 → 提示用户确认，或降级为 `/cr-backend` / `/cr-frontend`

写入 `replicate-config.json`，`project_type = fullstack`，新增 `backend_path`、`frontend_path`、`backend_target_stack`、`frontend_target_stack` 字段。

---

## Phase 2：双栈源码解构（自动执行，不停顿）

### 2a. 后端扫描

复用 cr-backend Phase 2 逻辑（技术栈识别 + 模块树 + 代码规模），结果写入 `backend/source-analysis.json`。

### 2b. 前端扫描

复用 cr-frontend Phase 2 逻辑（技术栈识别 + 组件树 + 代码规模），结果写入 `frontend/source-analysis.json`。

### 2c. 基础设施扫描（fullstack 独有）

扫描以下非代码文件，提取基础设施行为：

| 文件 | 提取内容 |
|------|---------|
| `docker-compose.yml` / `docker-compose.*.yml` | 服务依赖图、端口映射、环境变量、卷挂载 |
| `nginx.conf` / `Caddyfile` / `traefik.yml` | 反向代理路由、重写规则、CORS 配置 |
| `crontab` / `*.cron` / 代码中的 cron 表达式 | 定时任务清单 |
| `.env` / `.env.example` | 环境变量清单（不含值，只列 key + 用途推断） |
| `Makefile` / `Procfile` | 进程管理、启动命令 |
| k8s manifests（若有） | 服务拓扑、资源配额、健康检查 |

写入 `.allforai/code-replicate/infrastructure.json`。

输出进度「Phase 2 ✓ 后端: {N} 模块 | {backend_stack} | 前端: {N} 模块 | {frontend_stack} | 基础设施: {N} 项」。

---

## Phase 3：目标确认（增强）

在 core Phase 3 基础上，额外展示：

```markdown
### 双栈概览

| 维度 | 后端 | 前端 |
|------|------|------|
| 源技术栈 | {backend_stack} | {frontend_stack} |
| 模块数 | {N} | {N} |
| 路由/端点数 | {N}± | 页面数 {N}± |
| 目标技术栈 | {backend_target 或 待定} | {frontend_target 或 待定} |

### 初步 API 绑定

前端调用的后端端点（快速扫描，Phase 4 会深入分析）：

| 前端调用 | 后端端点 | 状态 |
|---------|---------|------|
| userApi.login() | POST /api/auth/login | ✅ matched |
| orderApi.list() | GET /api/orders | ✅ matched |
| reportApi.export() | GET /api/reports/export | ⚠️ 后端无此端点 |

### 基础设施概览

| 组件 | 用途 | 复刻建议 |
|------|------|---------|
| Docker Compose | 开发环境编排 | 生成等价配置 |
| Nginx | 反向代理 + CORS | 记录路由规则 |
| Cron | 每日报表生成 | 转为目标栈定时任务 |
```

用户确认：后端目标技术栈 + 前端目标技术栈 + 业务方向 + 复刻范围。

---

## Phase 4：深度分析（分层执行）

### 4a. 后端深度分析

复用 cr-backend Phase 4 逻辑（API 合约、行为规格、架构地图、Bug 注册表），产物写入 `backend/` 命名空间。

### 4b. 前端深度分析

复用 cr-frontend Phase 4 逻辑（组件与 API 合约、行为规格、架构地图、Bug 注册表），产物写入 `frontend/` 命名空间。

### 4c. 交叉验证层（fullstack 核心价值）

**4c-1. API 绑定分析 → `api-bindings.json`**

匹配前端 API 调用与后端端点：
- 从 `frontend/api-contracts.json` 提取所有 API 调用点（URL + method）
- 从 `backend/api-contracts.json` 提取所有端点（path + method）
- 自动匹配，标注状态：
  - `matched` — 前后端对应
  - `unmatched_frontend` — 前端调了但后端无此端点
  - `unmatched_backend` — 后端有但前端从不调用
- 对已匹配的：比对 request shape 和 response shape，标注 `shape_mismatch`

**4c-2. 数据 Schema 对齐 → `schema-alignment.json`**

从后端 ORM entity 和前端 TypeScript 类型/Props 提取字段：
- 自动匹配同名字段
- 标注不一致：类型不匹配（timestamp vs number）、后端有前端无（internal）、前端期望后端不返回

**4c-3. 约束一致性 → `constraint-reconciliation.json`**

对每条业务规则，检查在哪些层执行：
- **DB 层**：唯一约束、外键、check constraint
- **后端代码层**：validation、guard、exception
- **前端 UI 层**：form validation、disabled state
- 标注缺口：前端无校验但后端有 → 可接受（服务端兜底）；后端无但前端有 → 风险（可绕过）

**4c-4. 认证流程追踪 → `auth-propagation.json`**

追踪完整 token 生命周期：
- **后端**：签发（login）→ 验证（guard/middleware）→ 刷新（refresh endpoint）→ 注销（blacklist）
- **前端**：存储（localStorage/cookie）→ 注入（interceptor/header）→ 刷新（401 retry）→ 清除（logout）
- 标注断裂点（如：后端支持 refresh 但前端未实现自动刷新）

**4c-5. 错误处理对齐 → `error-mapping.json`**

匹配后端异常与前端 catch 处理：
- 后端返回 409 ConflictException → 前端是否处理 409？
- 后端返回 500 → 前端是否有通用错误兜底？
- 前端处理了 422 → 后端是否会抛 422？
- 标注：`handled` / `unhandled` / `no_backend_source`

### 4d. XV 跨模型验证（fullstack 增强）

先执行 core XV 的调用 1（行为遗漏检测）和调用 2（跨栈语义漂移风险），再执行以下 2 次 fullstack 专用调用：

| # | task_type | 发送内容 |
|---|-----------|---------|
| 3 | `api_binding_completeness` | 后端端点列表 + 前端 API 调用列表 + 已匹配绑定 |
| 4 | `schema_alignment_review` | 后端 entity 定义 + 前端类型定义 + 已匹配字段 |

Prompt 模板：

调用 3（API 绑定完整性）：
```
后端端点: {backend_endpoints_summary}
前端调用: {frontend_api_calls_summary}
已匹配: {matched_bindings}
未匹配: {unmatched_list}

请识别：
1. 未匹配项中是否有"间接调用"（如通过 WebSocket/SSE 而非 REST）
2. 是否有动态构造的 URL 被遗漏
3. 未匹配的后端端点是否可能被第三方/移动端调用
限 300 字。
```

调用 4（Schema 对齐审查）：
```
后端 Entity: {entity_fields_summary}
前端类型: {frontend_types_summary}
已对齐字段: {aligned_fields}
不一致项: {mismatches}

请识别：
1. 字段名不同但语义相同的漏匹配（如 created_at vs createdAt）
2. 嵌套对象/数组的深层 Schema 不一致
3. 枚举值集合是否前后端一致
限 300 字。
```

---

## Phase 6：生成产物（增强）

> **⚠️ 路径提醒**：fullstack 模式下，除 `code-replicate/` 产物外，还要写入 `.allforai/product-map/`（task-inventory、business-flows、constraints）和 `.allforai/use-case/`（use-case-tree）。task-inventory 中的任务使用 `backend:`、`frontend:`、`fullstack:` 前缀。

除后端/前端各自产物外，新增 fullstack 专有产物：

| 产物 | 路径 | 说明 |
|------|------|------|
| API 绑定 | `code-replicate/api-bindings.json` | 前端调用 ↔ 后端端点映射 |
| Schema 对齐 | `code-replicate/schema-alignment.json` | 数据模型前后端一致性 |
| 约束一致性 | `code-replicate/constraint-reconciliation.json` | 业务规则执行覆盖 |
| 认证传播 | `code-replicate/auth-propagation.json` | 完整 token 生命周期 |
| 错误映射 | `code-replicate/error-mapping.json` | 异常处理前后端对齐 |
| 基础设施 | `code-replicate/infrastructure.json` | 非代码行为（cron/nginx/docker） |
| 综合报告 | `code-replicate/fullstack-report.md` | 统一报告（替代两份独立报告） |

### 产物存储：完整路径清单

```
.allforai/
├── product-map/                       ← ⚠️ 注意：不是 code-replicate/ 下
│   ├── task-inventory.json            ← 所有模式（含 backend:/frontend:/fullstack: 前缀任务）
│   ├── business-flows.json            ← functional+
│   └── constraints.json               ← exact
├── use-case/                          ← ⚠️ 注意：不是 code-replicate/ 下
│   └── use-case-tree.json             ← functional+
└── code-replicate/
    ├── backend/
    │   ├── source-analysis.json
    │   ├── api-contracts.json
    │   ├── behavior-specs.json        ← functional+
    │   ├── arch-map.json              ← architecture+
    │   └── bug-registry.json          ← exact
    ├── frontend/
    │   ├── source-analysis.json
    │   ├── api-contracts.json
    │   ├── behavior-specs.json        ← functional+
    │   ├── arch-map.json              ← architecture+
    │   └── bug-registry.json          ← exact
    ├── api-bindings.json              ← fullstack 交叉层
    ├── schema-alignment.json
    ├── constraint-reconciliation.json
    ├── auth-propagation.json
    ├── error-mapping.json
    ├── infrastructure.json
    ├── replicate-config.json
    ├── stack-mapping.json
    ├── stack-mapping-decisions.json
    └── fullstack-report.md            ← 替代 replicate-report.md
```

### fullstack-report.md 模板

```markdown
# 全栈复刻报告

## 基本信息

| 项目 | 值 |
|------|----|
| 后端源技术栈 | {backend_stack} |
| 前端源技术栈 | {frontend_stack} |
| 后端目标技术栈 | {backend_target_stack} |
| 前端目标技术栈 | {frontend_target_stack} |
| 信度等级 | {fidelity} |
| 分析时间 | {datetime} |

## 后端分析摘要

- API 端点: {N} 个
- 业务行为: {N} 个（functional+）
- 架构模式: {list}（architecture+）

## 前端分析摘要

- 组件: {N} 个
- 页面/路由: {N} 个
- API 调用点: {N} 个

## 交叉验证摘要

| 维度 | 总数 | 一致 | 不一致 | 缺口 |
|------|------|------|--------|------|
| API 绑定 | {N} | {N} matched | {N} mismatch | {N} unmatched |
| Schema 对齐 | {N} fields | {N} aligned | {N} type_mismatch | {N} missing |
| 约束一致性 | {N} rules | {N} 全层覆盖 | {N} 部分覆盖 | {N} 单层仅有 |
| 认证传播 | {N} steps | {N} 完整 | {N} 断裂 | - |
| 错误处理 | {N} codes | {N} handled | {N} unhandled | - |

## 信息失真风险点

| 类型 | 位置 | 描述 | 处理方式 |
|------|------|------|---------|
| ... | | | |

## 下一步

使用 dev-forge 流水线继续：
- `/design-to-spec`   ← 生成目标技术栈实现规格
- `/task-execute`     ← 逐任务生成代码
```

---

## Phase 7：交接

> fullstack 模式生成 `fullstack-report.md` **替代**标准模式的 `replicate-report.md`。不重复生成两份报告。

统一报告（单份 `fullstack-report.md`），包含后端 + 前端 + 交叉验证三部分摘要。

`task-inventory.json` 中的任务分为三类：
- `backend:` 前缀 — 后端任务
- `frontend:` 前缀 — 前端任务
- `fullstack:` 前缀 — 交叉层发现的对齐任务（如"修复 API 绑定不一致"）
