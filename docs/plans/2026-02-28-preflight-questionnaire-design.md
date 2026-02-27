# Preflight 问卷前置 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 dev-forge Phase 1 中 6 个纯偏好问题前置到 Phase 0，通过单轮推荐+确认模式一次收集，减少流水线中间交互。

**Architecture:** 在 `project-forge.md` Phase 0 新增 Preflight 步骤，从 product-map 推断端类型并生成推荐配置写入 `forge-decisions.json`。`project-setup.md` 启动时检测 preflight 字段，存在则跳过对应 AskUserQuestion。

**Tech Stack:** Markdown skill files (Claude Code plugin prompt engineering)

---

### Task 1: 在 project-forge.md Phase 0 新增 Preflight 问卷段落

**Files:**
- Modify: `dev-forge-skill/commands/project-forge.md:73-127`

**Step 1: 在 Phase 0 标题下方添加 Preflight 子段落**

在 `project-forge.md` 第 126 行（`向用户展示探测结果 + 执行计划，确认后开始。`）之前，插入新的 `### Preflight 技术偏好收集` 段落。

将现有的：

```markdown
向用户展示探测结果 + 执行计划，确认后开始。
```

替换为：

```markdown
### Preflight 技术偏好收集

> 目标：前置收集所有纯偏好问题，避免后续阶段中断。

**Step 2a: 推断端类型**

读取 `.allforai/product-map/role-profiles.json`：

| 条件 | 推断端类型 |
|------|-----------|
| 始终 | `backend` |
| 有 consumer 类角色 | `web-customer` |
| 有 producer / admin 类角色 | `admin` |
| 有 mobile 标记 或 screen-map 中有 mobile 界面 | `mobile-native` |

读取 `${CLAUDE_PLUGIN_ROOT}/templates/stacks.json`，按端类型过滤可选技术栈。

**Step 2b: 生成推荐配置**

基于以下规则生成推荐值（优先级：用户偏好 > 智能推断 > 默认值）：

| 配置项 | 推荐规则 |
|--------|---------|
| 后端技术栈 | 用户偏好（如 MEMORY 记录 Go+Gin → `go-gin`）> stacks.json 中 type=backend 第一个 |
| 后端架构 | product-map 聚合根 > 5 或跨域交互多 → DDD；否则 → 三层架构 |
| DDD 时 CQRS | 默认 false |
| 前端技术栈 (admin/consumer) | 后端选 Vue 系 → Nuxt；否则 → Next.js |
| 移动端技术栈 | 用户偏好（如 Flutter）> flutter（默认） |
| Monorepo 工具 | 全 TS → pnpm-workspace；混合语言 → manual；子项目 > 4 → turborepo |
| 状态管理 | React 系 → Zustand；Vue 系 → Pinia；Angular → 跳过 |
| 服务端缓存 | TanStack Query（React / Vue 通用） |
| 认证策略 | 多角色权限 → JWT；简单场景 → Session |

**Step 2c: 展示推荐配置 + 用户确认**

向用户展示推荐配置表：

~~~markdown
## Preflight — 技术偏好

从产品地图分析，你的产品需要 {N} 个端：

| 端 | 推荐技术栈 | 理由 |
|---|---|---|
| 后端 API | {stack} ({arch}) | {reason} |
| 管理后台 | {stack} | {reason} |
| 消费者 Web | {stack} | {reason} |
| 移动端 | {stack} | {reason} |

| 配置项 | 推荐值 |
|---|---|
| Monorepo | {tool} |
| 状态管理 | {lib} |
| 服务端缓存 | {lib} |
| 认证策略 | {strategy} |
~~~

AskUserQuestion：
- **全部确认** → 写入 forge-decisions.json，继续
- **逐项调整** → 对需要调整的项逐个 AskUserQuestion（仅展示 stacks.json 中该端类型的可选项），调整完后写入

**Step 2d: 写入 forge-decisions.json**

将确认后的配置写入 `forge-decisions.json` 的 `preflight` 字段（结构见下方 Task 2）。

---

向用户展示探测结果 + 执行计划（含 preflight 结果摘要），确认后开始。
```

**Step 2: 验证编辑**

Read `dev-forge-skill/commands/project-forge.md` 确认新段落在 Phase 0 内、Phase 1 之前。

**Step 3: Commit**

```bash
git add dev-forge-skill/commands/project-forge.md
git commit -m "feat(dev-forge): add preflight questionnaire to Phase 0"
```

---

### Task 2: 更新 forge-decisions.json schema 增加 preflight 字段

**Files:**
- Modify: `dev-forge-skill/commands/project-forge.md:101-124`

**Step 1: 扩展 JSON schema**

将 `project-forge.md` 中 `forge-decisions.json` 的 JSON 示例（约第 105-123 行）替换为包含 `preflight` 的完整结构：

将现有的：

```json
{
  "forge_run": {
    "mode": "full | existing | resume",
    "started_at": "ISO8601",
    "product_source": ".allforai/product-map/product-map.json"
  },
  "phase_status": {
    "phase_1": "pending | completed | skipped",
    "phase_2": "pending | completed | skipped",
    "phase_2_5": "pending | completed | skipped",
    "phase_3": "pending | completed | skipped",
    "phase_4": "pending | in_progress | completed",
    "phase_4_5": "pending | in_progress | completed | skipped",
    "phase_5": "pending | completed | skipped",
    "phase_6": "pending | completed"
  },
  "decisions": []
}
```

替换为：

```json
{
  "forge_run": {
    "mode": "full | existing | resume",
    "started_at": "ISO8601",
    "product_source": ".allforai/product-map/product-map.json"
  },
  "preflight": {
    "inferred_endpoints": ["backend", "admin", "web-customer", "mobile-native"],
    "tech_preferences": {
      "backend": {
        "template_id": "go-gin",
        "architecture": "three-layer",
        "cqrs": false
      },
      "admin": {
        "template_id": "nextjs",
        "state_management": "zustand",
        "server_cache": "tanstack-query"
      },
      "web-customer": {
        "template_id": "nextjs",
        "state_management": "zustand",
        "server_cache": "tanstack-query"
      },
      "mobile-native": {
        "template_id": "flutter"
      }
    },
    "monorepo_tool": "manual",
    "auth_strategy": "jwt",
    "confirmed_at": "ISO8601"
  },
  "phase_status": {
    "phase_1": "pending | completed | skipped",
    "phase_2": "pending | completed | skipped",
    "phase_2_5": "pending | completed | skipped",
    "phase_3": "pending | completed | skipped",
    "phase_4": "pending | in_progress | completed",
    "phase_4_5": "pending | in_progress | completed | skipped",
    "phase_5": "pending | completed | skipped",
    "phase_6": "pending | completed"
  },
  "decisions": []
}
```

**Step 2: Commit**

```bash
git add dev-forge-skill/commands/project-forge.md
git commit -m "feat(dev-forge): add preflight field to forge-decisions.json schema"
```

---

### Task 3: 在 project-setup.md 添加 preflight 读取逻辑

**Files:**
- Modify: `dev-forge-skill/skills/project-setup.md:80-130`

**Step 1: 在工作流顶部添加 preflight 检测前置步骤**

在 `project-setup.md` 的 `## 工作流` 段落（第 80 行），将现有的流程图起始部分替换为包含 preflight 检测的版本。

将现有的：

```
前置: 加载 .allforai/product-map/product-map.json
      加载 .allforai/product-map/task-index.json（索引优先）
      若不存在 → 提示先运行 /product-map，终止
      ↓
Step 0: 模式识别
```

替换为：

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
```

**Step 2: 标注 Step 1 中 monorepo 工具选择为可跳过**

将现有的：

```
  AskUserQuestion: 确认/调整子项目列表
  AskUserQuestion: 选择 monorepo 工具 (pnpm workspace / Turborepo / Nx / 手动管理)
```

替换为：

```
  AskUserQuestion: 确认/调整子项目列表
  AskUserQuestion: 选择 monorepo 工具 (pnpm workspace / Turborepo / Nx / 手动管理)
    → 若有 preflight → 跳过，使用 preflight.monorepo_tool
```

**Step 3: 标注 Step 2 中技术栈选择为可跳过**

将现有的：

```
Step 2: 技术栈选择（逐子项目）
  对每个子项目:
    读取 templates/stacks.json → 过滤匹配 type 的模板
    AskUserQuestion: 从预设模板中选择
    → 记录选择到 tech-profile.json
```

替换为：

```
Step 2: 技术栈选择（逐子项目）
  对每个子项目:
    读取 templates/stacks.json → 过滤匹配 type 的模板
    AskUserQuestion: 从预设模板中选择
      → 若有 preflight → 跳过，使用 preflight.tech_preferences[子项目type].template_id
    → 记录选择到 tech-profile.json
```

**Step 4: 标注 Step 4 中 auth 策略为可跳过**

将现有的：

```
Step 4: 基础配置
  每子项目自动分配: 端口号（基于 stacks.json 默认端口，避免冲突）、base path
  AskUserQuestion: 确认 auth 策略 (JWT / Session / OAuth / 无)
  AskUserQuestion: 确认端口和配置
```

替换为：

```
Step 4: 基础配置
  每子项目自动分配: 端口号（基于 stacks.json 默认端口，避免冲突）、base path
  AskUserQuestion: 确认 auth 策略 (JWT / Session / OAuth / 无)
    → 若有 preflight → 跳过，使用 preflight.auth_strategy
  AskUserQuestion: 确认端口和配置
```

**Step 5: Commit**

```bash
git add dev-forge-skill/skills/project-setup.md
git commit -m "feat(dev-forge): project-setup reads preflight, skips pre-answered questions"
```

---

### Task 4: 标注后端架构和前端状态管理为可跳过

**Files:**
- Modify: `dev-forge-skill/skills/project-setup.md:264-308`

**Step 1: 标注后端架构选择为可跳过**

将现有的（约第 264-266 行）：

```markdown
AskUserQuestion 在后端子项目的 Step 2 中：
- "后端架构模式？" → 三层架构 (推荐: CRUD 为主) / DDD (推荐: 复杂业务)
- 选择 DDD 时追问: "是否启用 CQRS？" → 是 / 否
```

替换为：

```markdown
AskUserQuestion 在后端子项目的 Step 2 中：
- "后端架构模式？" → 三层架构 (推荐: CRUD 为主) / DDD (推荐: 复杂业务)
  → 若有 preflight → 跳过，使用 preflight.tech_preferences.backend.architecture
- 选择 DDD 时追问: "是否启用 CQRS？" → 是 / 否
  → 若有 preflight → 跳过，使用 preflight.tech_preferences.backend.cqrs
```

**Step 2: 标注前端状态管理和缓存为可跳过**

将现有的（约第 305-308 行）：

```markdown
AskUserQuestion 在前端子项目的 Step 2 中：
- "状态管理方案？" → 列出与框架匹配的选项
- "服务端缓存方案？" → TanStack Query (推荐) / SWR / 手动管理
- 选择后记录到 manifest 的 `state_management` 字段
```

替换为：

```markdown
AskUserQuestion 在前端子项目的 Step 2 中：
- "状态管理方案？" → 列出与框架匹配的选项
  → 若有 preflight → 跳过，使用 preflight.tech_preferences[子项目type].state_management
- "服务端缓存方案？" → TanStack Query (推荐) / SWR / 手动管理
  → 若有 preflight → 跳过，使用 preflight.tech_preferences[子项目type].server_cache
- 选择后记录到 manifest 的 `state_management` 字段
```

**Step 3: Commit**

```bash
git add dev-forge-skill/skills/project-setup.md
git commit -m "feat(dev-forge): mark arch/state-mgmt/cache questions as preflight-skippable"
```

---

### Task 5: 更新铁律 #2 + 版本号

**Files:**
- Modify: `dev-forge-skill/skills/project-setup.md:9,366-368`

**Step 1: 更新铁律 #2 适配 preflight**

将现有的：

```markdown
### 2. 每步确认，不跳步

每个 Step 完成后展示摘要，等用户确认后才进入下一步。
```

替换为：

```markdown
### 2. 每步确认，不跳步（preflight 除外）

每个 Step 完成后展示摘要，等用户确认后才进入下一步。
例外：若 `forge-decisions.json` 中存在 `preflight` 且 `confirmed_at` 非空，标记为「若有 preflight → 跳过」的 AskUserQuestion 直接使用 preflight 值，不再询问。
```

**Step 2: Bump version**

将第 9 行 `version: "1.0.1"` 改为 `version: "1.1.0"`。

**Step 3: Commit**

```bash
git add dev-forge-skill/skills/project-setup.md
git commit -m "feat(dev-forge): update iron rule #2 for preflight, bump to v1.1.0"
```

---

### Task 6: 更新六阶段架构图

**Files:**
- Modify: `dev-forge-skill/commands/project-forge.md:32-69`

**Step 1: 更新架构图中 Phase 0 描述**

将现有的：

```
│  Phase 0: 产物检测 + 模式路由                                │
```

替换为：

```
│  Phase 0: 产物检测 + 模式路由 + Preflight 偏好收集           │
```

**Step 2: Commit**

```bash
git add dev-forge-skill/commands/project-forge.md
git commit -m "docs(dev-forge): update architecture diagram for preflight"
```
