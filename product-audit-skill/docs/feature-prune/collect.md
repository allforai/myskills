# Step 0: 项目画像 & 功能收集

> feature-prune 的第一步：搞清楚项目有哪些功能（计划的+已实现的），合并为全量清单。
> 不做价值判断，只做功能发现 + 合并 + 复杂度信号采集。

---

## 1. 项目画像（轻量版）

检测逻辑与 feature-audit 的 Step 0 完全一致，参见 `${CLAUDE_PLUGIN_ROOT}/docs/sources.md` 的技术栈检测表和 Monorepo 检测。此处不再重复。

输出字段保持一致：`tech_stack`, `monorepo`, `route_files`, `menu_files`, `api_files`。

---

## 2. 功能收集

两条并行轨道同时执行，各自独立产出功能列表，最终在第 3 节合并。

### 2.1 Track A: 从需求文档提取计划功能

来源与 feature-audit 完全一致，按优先级从高到低扫描：

| 优先级 | 来源类型 | 扫描目标 | Glob 模式 | 提取内容 |
|--------|----------|----------|-----------|----------|
| 1 | PRD / 需求文档 | 正式需求文档 | `docs/**/*.md`, `**/prd.*`, `**/PRD.*`, `**/requirements.*`, `**/spec.*` | 功能名、描述、来源 file:line |
| 2 | README | Features / 功能章节 | `README.md`, `readme.md` | 功能名、描述、来源 file:line |
| 3 | OpenAPI / Swagger | API 规范文档 | `swagger.*`, `openapi.*`, `**/swagger/**`, `**/api-docs/**` | tag 分组、endpoint、summary、来源 file:line |
| 4 | CHANGELOG | 版本变更记录 | `CHANGELOG.md`, `changelog.md`, `HISTORY.md` | `Added` / `新增` 章节条目、来源 file:line |

#### 提取规则

```
对每个来源文件：
  1. 按 feature-audit sources.md 中定义的提取方式解析
  2. 对每个提取到的功能点，记录：
     - feature_name: 功能名称
     - description: 功能描述（一句话）
     - source_file_line: 来源文件路径 + 行号（如 docs/prd.md:23）
  3. 来自 PRD 的功能点 confidence=high，来自 README/CHANGELOG 的 confidence=medium
```

### 2.2 Track B: 从代码提取已实现功能

根据项目画像中检测到的技术栈，定向扫描以下代码结构：

| 扫描目标 | 适用框架 | 扫描方式 | 提取内容 |
|----------|----------|----------|----------|
| 路由 / 页面 | Next.js, React, Vue, Angular, Nuxt | 见 `sources.md` 技术栈检测表的 Route 文件列 | route_path, component_file |
| API Controllers / Handlers | NestJS, Express, Spring Boot, Django, Go | 见 `sources.md` 技术栈检测表的 API 定义文件列 | endpoint, method, handler_file |
| 菜单 / 导航 | 所有前端框架 | 见 `sources.md` 技术栈检测表的 Menu/Nav 文件列 | menu_name, path |

#### 提取规则

```
对每个扫描到的代码入口：
  1. 识别功能边界：
     - 一个路由 / 页面 → 一个功能入口
     - 一组关联 API endpoints（相同 controller / 相同 resource） → 一个功能模块
     - 一个菜单项 → 一个用户可见功能
  2. 对每个功能，记录：
     - feature_name: 从路由名 / controller 名 / 菜单名推导
     - evidence:
         route: "路由路径 → 组件文件"
         component: "组件文件:行号"
         api: "METHOD /api/path"
     - complexity_signals:
         files_involved: 该功能涉及的文件数（组件、service、store、util 等）
         endpoints: 该功能对应的 API endpoint 数
         special_tech: 特殊技术列表（WebSocket, cron, 第三方集成, 实时推送, 文件上传等）
  3. 所有代码推导功能 confidence=medium（无文档佐证时降为 low）
```

#### 复杂度信号识别

```
special_tech 检测规则（正则扫描功能相关文件）：
  - WebSocket     → /websocket|socket\.io|ws:\/\//i
  - Cron / 定时任务 → /cron|schedule|@Cron|setInterval.*\d{4,}/i
  - 第三方集成     → /stripe|paypal|twilio|sendgrid|aws-sdk|aliyun|wechat/i
  - 实时推送       → /SSE|EventSource|server-sent|realtime|pusher/i
  - 文件上传       → /multer|upload|multipart|formdata.*file/i
  - 队列 / 消息    → /bull|rabbitmq|kafka|redis.*queue|amqp/i
```

---

## 3. 功能合并

将 Track A（计划功能）和 Track B（已实现功能）合并为统一的全量功能清单。

### 3.1 匹配策略

```
对 Track A 中的每个计划功能 P 和 Track B 中的每个实现功能 I：

  匹配条件（满足任一即视为匹配）：
  1. 名称相似度 → Levenshtein 或关键词重叠率 >= 0.6
  2. 路由关联   → P 的描述中提及的路径 与 I 的 route 匹配
  3. 关键词重叠 → P 的 description 分词 与 I 的 feature_name + evidence 关键词重叠 >= 2

  匹配优先级：
  1. 精确名称匹配 > 路由关联 > 关键词重叠
  2. 一个计划功能可匹配多个实现功能（1:N），反之亦然
  3. 出现歧义时 → 标记 match_confidence=low，留待用户确认
```

### 3.2 标记规则

合并后，每个功能标记 `source_type`：

| source_type | 含义 | 来源情况 | 标记说明 |
|-------------|------|----------|----------|
| `both` | 计划且已实现 | Track A + Track B 均找到 | 链接 planned_source + implemented_evidence |
| `planned` | 仅在文档中 | 仅 Track A 找到 | 标注 "未找到对应实现" |
| `implemented` | 仅在代码中 | 仅 Track B 找到 | 标注 "未在需求源中提及" |

### 3.3 合并流程

```
1. 以 Track A 功能列表为基准
2. 对 Track B 每个功能，尝试匹配 Track A 中的条目
   - 匹配成功 → 合并为 source_type=both，关联双方证据
   - 匹配失败 → 新增为 source_type=implemented
3. Track A 中未被匹配的 → 标记为 source_type=planned
4. 生成统一 ID（F-001, F-002, ...），按 category 分组
5. category 推导规则：
   - 有 PRD 的 → 使用 PRD 中的模块划分
   - 无 PRD 的 → 按路由前缀 / controller 名 / 菜单层级自动归类
```

---

## 4. 复杂度信号采集

对合并后的每个功能，无论 source_type，统一采集复杂度信号。

### 4.1 采集规则

| 信号 | 类型 | 采集方式 |
|------|------|----------|
| `files_involved` | number | 统计与该功能关联的所有文件数（组件、service、store、hook、util、style、test） |
| `endpoints` | number | 统计该功能对应的 API endpoint 数量 |
| `special_tech` | string[] | 扫描功能相关文件，匹配 special_tech 检测规则（见 2.2 节） |

### 4.2 不同 source_type 的处理

```
source_type=both:
  - files_involved → 从 implemented_evidence 关联文件直接统计
  - endpoints → 从 API evidence 直接统计
  - special_tech → 扫描关联文件

source_type=implemented:
  - 同 both，从代码证据直接采集

source_type=planned:
  - files_involved → 估算值，标记 estimated=true
  - endpoints → 从 PRD 描述推断（如 "提供 CRUD 接口" → endpoints=4）
  - special_tech → 从 PRD 描述关键词匹配（如 "实时通知" → ["realtime"]）
  - 所有字段追加 confidence=low
```

### 4.3 估算规则（planned only）

```
基于描述关键词的粗略估算：
  - "CRUD" / "增删改查"      → endpoints=4, files_involved=6
  - "列表" / "查询"           → endpoints=1, files_involved=3
  - "导入导出" / "import/export" → endpoints=2, files_involved=4, special_tech=["file-upload"]
  - "仪表盘" / "dashboard"    → endpoints=3, files_involved=8
  - "通知" / "消息"           → endpoints=2, files_involved=5, special_tech=["realtime"]
  - 无法推断                  → files_involved=0, endpoints=0, special_tech=[], estimated=true
```

---

## 5. 用户确认点（User Checkpoints）

Step 0 结束前，必须向用户确认以下内容。**不要自动跳过确认。**

### 5.1 功能清单确认

```
已收集到以下功能清单：

总计: 20 个功能
  - 计划 + 已实现 (both): 12
  - 仅在文档中 (planned): 3
  - 仅在代码中 (implemented): 5

[分类展示功能列表]

请确认：
- 功能清单是否完整？有遗漏的功能吗？
- 分类是否合理？需要调整吗？
- planned 功能是否确实未实现？还是实现方式不同、未被检测到？
- implemented 功能是否确实不在需求中？还是需求表述不同？
```

### 5.2 复杂度信号确认

```
以下功能检测到特殊技术依赖：

1. [F-003] 实时消息 → special_tech: ["WebSocket", "realtime"]
2. [F-007] 数据导出 → special_tech: ["file-upload"]
3. [F-012] 定时报表 → special_tech: ["cron"]

以下 planned 功能的复杂度为估算值（标记 ⚠）：
1. [F-018] 权限管理 → files_involved≈8, endpoints≈4 (estimated)

请确认：
- 特殊技术标记是否准确？
- 估算值是否合理？
```

### 5.3 等待用户回复

```
收到用户确认后：
- confirmed_by_user = true
- 根据用户反馈更新功能列表（增删改）
- 如果用户补充了遗漏功能 → 追加到 features 列表，标记 source_type=user_added
- 进入 Step 1（功能评估）
```

---

## 6. 输出格式

Step 0 的最终输出为 `feature-list.json`，结构如下：

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
    "monorepo": false,
    "route_files": [
      "app/page.tsx",
      "app/dashboard/page.tsx",
      "app/admin/users/page.tsx"
    ],
    "menu_files": [
      "src/config/menu.ts"
    ],
    "api_files": [
      "src/users/users.controller.ts",
      "src/auth/auth.controller.ts"
    ]
  },
  "features": [
    {
      "id": "F-001",
      "name": "用户登录",
      "source_type": "both",
      "planned_source": "docs/prd.md:23",
      "implemented_evidence": {
        "route": "/login → src/pages/Login.tsx",
        "component": "src/pages/Login.tsx:1",
        "api": "POST /api/auth/login"
      },
      "category": "用户管理",
      "complexity_signals": {
        "files_involved": 5,
        "endpoints": 1,
        "special_tech": []
      }
    },
    {
      "id": "F-002",
      "name": "数据导出",
      "source_type": "planned",
      "planned_source": "docs/prd.md:45",
      "implemented_evidence": null,
      "category": "数据管理",
      "complexity_signals": {
        "files_involved": 4,
        "endpoints": 2,
        "special_tech": ["file-upload"],
        "estimated": true,
        "confidence": "low"
      },
      "notes": "未找到对应实现"
    },
    {
      "id": "F-003",
      "name": "系统健康检查",
      "source_type": "implemented",
      "planned_source": null,
      "implemented_evidence": {
        "route": "/api/health",
        "component": null,
        "api": "GET /api/health"
      },
      "category": "系统运维",
      "complexity_signals": {
        "files_involved": 2,
        "endpoints": 1,
        "special_tech": []
      },
      "notes": "未在需求源中提及"
    }
  ],
  "summary": {
    "total": 20,
    "planned_only": 3,
    "implemented_only": 5,
    "both": 12
  },
  "confirmed_by_user": false,
  "created_at": "2026-02-24T10:00:00Z"
}
```

### 6.1 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `project_profile` | object | 项目画像，结构与 feature-audit 的 `audit-sources.json` 一致 |
| `features[].id` | string | 功能唯一 ID，格式 `F-001` |
| `features[].name` | string | 功能名称 |
| `features[].source_type` | string | `both` / `planned` / `implemented` |
| `features[].planned_source` | string \| null | 需求来源 file:line，无则为 null |
| `features[].implemented_evidence` | object \| null | 代码证据（route, component, api），无则为 null |
| `features[].category` | string | 功能分类（从 PRD 模块或路由前缀推导） |
| `features[].complexity_signals` | object | 复杂度信号：files_involved, endpoints, special_tech |
| `features[].complexity_signals.estimated` | boolean | 是否为估算值（仅 planned 功能） |
| `features[].notes` | string | 备注（如 "未找到对应实现"、"未在需求源中提及"） |
| `summary.total` | number | 功能总数 |
| `summary.planned_only` | number | 仅在文档中的功能数 |
| `summary.implemented_only` | number | 仅在代码中的功能数 |
| `summary.both` | number | 计划且已实现的功能数 |
| `confirmed_by_user` | boolean | 用户是否已确认。Step 0 完成前必须为 true |

---

## 附录：Quick Reference

### Step 0 执行顺序

```
1. 项目画像        → 检测技术栈、monorepo、关键文件（复用 feature-audit 逻辑）
2. Track A 扫描    → 从需求文档提取计划功能（PRD → README → OpenAPI → CHANGELOG）
3. Track B 扫描    → 从代码提取已实现功能（路由、页面、API controller）
4. 功能合并        → 匹配 + 标记 source_type（both / planned / implemented）
5. 复杂度信号采集  → 对每个功能采集 files_involved, endpoints, special_tech
6. 用户确认        → 展示合并清单，等待确认
7. 输出 feature-list.json → 交给 Step 1
```

### 耗时预期

| 项目规模 | 预计耗时 |
|----------|---------|
| 小型项目 (< 50 files) | < 15s |
| 中型项目 (50-500 files) | 15-45s |
| 大型 monorepo (500+ files) | 45-90s |

核心原则：**只收集，不判断。价值评估留给 Step 1+。**

---

> **铁律速查** — 详见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-audit.md` 的「5 条铁律」章节。
> 本步骤强相关：**来源绑定**（每个功能必须记录 planned_source 或 implemented_evidence，不允许无来源功能项）、**保守分类**（匹配不确定时标 match_confidence=low，source_type 不确定时优先标 planned 或 implemented 而非 both）。
