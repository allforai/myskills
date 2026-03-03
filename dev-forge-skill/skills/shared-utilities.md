---
name: shared-utilities
description: >
  Use when "分析共享工具", "共享层规划", or automatically called by project-forge Phase 5.
  Analyzes existing code inventory and cross-task patterns to identify shared utilities,
  research third-party libraries, and inject B1 foundation tasks before coding begins.
version: "1.0.0"
---

# Shared Utilities — 共享工具分析与注入

> 扫描已有代码 + 跨任务模式分析 + 三方库选型 → 用户确认 → 生成共享层任务注入 B1

## 目标

在编码开始前识别项目中的重复需求，通过统一共享层避免"同功能多套路"：

1. **扫描已有** — existing 模式下盘点已有工具库存（new 模式跳过）
2. **模式分析** — 扫描所有子项目 tasks.md，识别跨任务重复需求
3. **三方调研** — WebSearch 调研推荐库，确认选型方向
4. **用户确认** — ONE-SHOT 展示分析结果，收集三方库决策（唯一停顿点）
5. **注入任务** — 生成共享工具 B1 任务和 `_Leverage_` 补丁，写入 `tasks-supplement.json`（不修改原 tasks.md）

---

## 定位

```
Phase 3: design-to-spec → 各子项目 tasks.md      ← 输入
Phase 5: shared-utilities → 分析 + 注入任务       ← 本技能
Phase 6: project-scaffold → 脚手架生成             ← 下游
Phase 7: task-execute → 编写代码                   ← 消费 SU-xxx B1 任务
```

**前提**：
- 必须有各子项目的 `tasks.md`（来自 design-to-spec）
- 必须有 `project-manifest.json`（来自 project-setup）

---

## 理论基础

本技能的抽象决策基于以下原则：

- **DRY（Don't Repeat Yourself）** — 检测重复代码/逻辑，提取为共享工具
- **三次法则（Rule of Three）** — 模式出现 3 次及以上才考虑抽象，避免过早抽象
- **错误的抽象比重复更危险（Sandi Metz）** — 每个候选 SU 必须经用户确认，强制抽象可能引入错误耦合
- **库评估四维度** — 维护活跃度、社区规模、类型安全、包体积影响，WebSearch 获取实时数据

---

## 工作流

```
Preflight: 读取模式（new/existing）+ 检查 tasks.md 存在性
    ↓ 自动
Step 1: 已有代码扫描（existing 模式执行，new 模式跳过）
    ↓ 自动
Step 2: 跨任务模式分析（扫描所有子项目 tasks.md）
    ↓ 自动
Step 3: 三方库调研（WebSearch，自动）
    ↓ 自动
Step 4: ONE-SHOT 用户确认（唯一停顿点）
    ↓ 用户确认后
Step 5: 注入任务 + 写入产物（自动，不停顿）
```

---

## Preflight: 前置检查

读取 `.allforai/project-forge/project-manifest.json`，获取所有子项目列表。

检查各子项目 tasks.md 是否存在：
- 存在 → 继续
- 不存在 → 输出「请先完成 Phase 3（design-to-spec），再运行 Phase 5」，终止

### 上游过期检测

加载输入文件时，比较关键上游文件的修改时间与本技能上次输出的生成时间：
- tasks.md（任一子项目）在 shared-utilities-plan.json 生成后被更新
  → ⚠ 警告「tasks.md 在 shared-utilities-plan.json 生成后被更新，数据可能过期，建议重新运行 design-to-spec」
- 仅警告不阻断，用户可选择继续或先刷新上游

读取模式（来自 forge-decisions.json 的 `forge_run.mode`）：
- `existing` → 执行 Step 1（已有代码扫描），再执行 Step 2-5
- `new` / 未设置 → 跳过 Step 1，直接从 Step 2 开始

---

## Step 1: 已有代码扫描（existing 模式）

> 目标：盘点项目已有的工具函数、服务封装、三方依赖，避免重造轮子。

扫描项目代码，提取工具库存。**扫描目标**（按优先级）：

| 优先级 | 目标位置 | 识别内容 |
|--------|---------|---------|
| 1 | `utils/` `helpers/` `common/` `shared/` `pkg/` | 工具函数 |
| 2 | `services/` | 外部服务封装（email、sms、storage…） |
| 3 | `middleware/` `interceptors/` `guards/` | 横切关注点 |
| 4 | `package.json` / `go.mod` / `requirements.txt` | 已有三方依赖 |

每个已有工具记录为 EU-xxx（Existing Utility）：

```json
{
  "id": "EU-001",
  "type": "email-service | validator | http-client | pagination | logger | ...",
  "location": "src/utils/email.ts",
  "coverage": "发送模板邮件、HTML 邮件",
  "quality": "good | needs-refactor | partial",
  "usable_as_is": true
}
```

**质量评估标准**：
- `good`：有完整类型定义、有错误处理、无明显技术债
- `needs-refactor`：功能可用但缺少类型/错误处理，或与项目规范不符
- `partial`：仅覆盖部分场景，需要补充

输出：`.allforai/project-forge/existing-utilities-index.json`

```json
{
  "scanned_at": "ISO8601",
  "project_root": "./",
  "existing_utilities": [
    {
      "id": "EU-001",
      "type": "...",
      "location": "...",
      "coverage": "...",
      "quality": "good | needs-refactor | partial",
      "usable_as_is": true
    }
  ]
}
```

---

## Step 2: 跨任务模式分析

> 目标：扫描所有子项目 tasks.md，识别跨任务重复需求，匹配已有实现。

### 两阶段加载

**Phase 1 — 索引扫描**：
若 `task-index.json` 或 `tasks.json` 存在：
- 从索引读取任务标题和文件路径列表
- 基于关键词匹配（Step 2 的 8 类模式）筛选候选任务
- 仅对候选任务所在的 tasks.md 加载完整内容

**Phase 2 — 详情加载**：
- 仅加载候选任务的完整描述和文件列表
- 非候选任务保持索引级信息

**回退**：索引不存在 → 全量扫描所有 tasks.md（向后兼容）

扫描所有子项目 tasks.md，检测以下模式类型（扫描任务标题 + Files 字段 + 实现要点关键词）：

| 模式类型 | 检测关键词 | 阈值 |
|---------|---------|------|
| 外部服务 | 邮件/email、短信/sms、推送/push、支付/payment、存储/storage | 2+ 任务 |
| 校验逻辑 | 手机号、邮箱、金额、身份证、格式化 | 3+ 任务 |
| HTTP 客户端 | 外部 API、第三方接口 | 2+ 任务 |
| 分页 | list、分页、page、offset | 3+ 任务 |
| 错误格式 | 错误码、error format、统一响应 | 3+ 任务 |
| 日志 | logger、log、日志 | 3+ 任务 |
| 缓存 | cache、Redis | 2+ 任务 |
| 文件上传 | upload、multipart、文件 | 2+ 任务 |
| 日期处理 | date、时间格式、时区 | 3+ 任务 |

对每个检测到的模式：
- 有 `EU-xxx` 匹配（Step 1 扫描到的已有实现）→ 标记 `REUSE:EU-xxx`，不进入 Step 3
- 无已有实现 → 标记 `NEW`，进入 Step 3 调研

---

## Step 3: 三方库调研（WebSearch，自动）

> 目标：对每个 NEW 类型，WebSearch 调研推荐库，确认选型方向。

**搜索词模板**（基于 preflight 已选技术栈动态拼接）：

```
"{framework} {utility_type} best library {year}"
```

**推荐方向参考**（WebSearch 确认后使用）：

| 类型 | Node.js/TS | Python | Go |
|------|-----------|--------|-----|
| 校验 | class-validator / zod | pydantic | go-playground/validator |
| HTTP client | axios / got | httpx | resty |
| 日期 | dayjs / date-fns | python-dateutil | carbon |
| 日志 | pino / winston | loguru | zap |
| 邮件 | nodemailer | fastapi-mail | gomail |
| 文件上传 | multer | python-multipart | standard lib |
| 分页 | 3行自实现 | 3行自实现 | 3行自实现 |
| 缓存 | ioredis / node-cache | redis-py | go-redis |

每个 NEW 类型给出 1-2 个推荐选项（含推荐理由），供 Step 4 用户决策。

---

## Step 4: ONE-SHOT 用户确认（唯一停顿点）

### Auto-mode 处理

当 `__orchestrator_auto: true` 时（由 project-forge 编排器传入），Step 4 **自动采纳推荐选项（选项 A）**，不停顿：
- 每个 SU-xxx 自动选择推荐库（Step 3 的第一推荐）
- 输出一行摘要：「✓ auto-mode: SU-001=class-validator, SU-002=自实现, SU-003=ExceptionFilter」
- 仅当检测到 **ERROR 级冲突**（如推荐库已停维、与已有依赖版本冲突）时才停顿询问用户

### 非 auto-mode

展示完整分析结果，一次性收集用户决策。

**展示格式**：

```markdown
## Phase 5 — 共享工具分析

### 已有代码可复用（{N} 项）
| ID | 类型 | 位置 | 质量 | 处理方式 |
|----|------|------|------|---------|
| EU-001 | email-service | src/utils/email.ts | good | 直接复用 |
| EU-002 | pagination | src/utils/page.ts | needs-refactor | 复用但重构 |

### 需要新建的共享工具（{N} 项）
| ID | 类型 | 被依赖任务数 | 推荐库 | 备选库 |
|----|------|------------|--------|--------|
| SU-001 | 手机号/邮箱校验 | 8 个任务 | class-validator | zod |
| SU-002 | 分页 helper | 12 个任务 | 3行自实现 | 三方库 |
| SU-003 | 统一错误格式 | 全部任务 | 自实现 ExceptionFilter | http-errors |
```

用 **AskUserQuestion** 对每个 SU-xxx 提问（一次性收集所有决策），选项格式：

```
选项 A: 使用 {推荐库}（{推荐理由}）
选项 B: 使用 {备选库}（{备选理由}）
选项 C: 自行实现（适合 {场景}）
```

**已有代码（EU-xxx）无需确认，直接采用。**

### 规模自适应

根据候选模式数量调整 Step 4 展示策略：
- **小规模**（≤10 个候选模式）：完整详情表格
- **中规模**（11-25 个候选模式）：按类型分组，展开重点项
- **大规模**（>25 个候选模式）：Top-10（按依赖任务数排序）+ 统计摘要

---

## Step 5: 注入任务 + 写入产物（自动，不停顿）

用户确认后，自动执行以下操作，不再停顿。

### 5a. 生成共享工具 B1 任务

为每个 SU-xxx 生成原子任务，写入 `.allforai/project-forge/tasks-supplement.json`（**不修改**原始 tasks.md，上游产物只读）：

```json
{
  "created_at": "ISO8601",
  "source": "shared-utilities",
  "b1_tasks": [
    {
      "id": "1.x",
      "sub_project": "api-backend",
      "title": "创建 {utility_type} 共享工具",
      "files": ["src/utils/{name}.ts", "src/utils/index.ts"],
      "details": "封装 {library}，导出统一接口和类型定义",
      "shared_utility_ref": "SU-001",
      "risk": "MEDIUM"
    }
  ],
  "leverage_patches": [
    {
      "task_id": "2.3",
      "append_leverage": ["SU-001 (class-validator)", "SU-003 (ExceptionFilter)"]
    }
  ],
  "refactor_tasks": [
    {
      "id": "1.x",
      "sub_project": "api-backend",
      "title": "重构 {utility_type}（EU-{id}）以符合项目规范",
      "files": ["{existing_location}"],
      "details": "补充类型定义和错误处理",
      "shared_utility_ref": "EU-001",
      "risk": "LOW"
    }
  ]
}
```

**task-execute 加载时合并**：task-execute 启动时检查 `tasks-supplement.json` 是否存在，若存在则：
- 将 `b1_tasks` 追加到后端子项目 tasks 的 Batch 1 末尾
- 将 `leverage_patches` 中的引用合并到对应任务的 `_Leverage_` 字段
- 将 `refactor_tasks` 追加到 Batch 1（EU-xxx 复用已有，quality=needs-refactor 时）

### 5b. _Leverage_ 补丁（写入 supplement，不修改原文件）

扫描所有子项目 tasks.md，找到 `affects_tasks` 中匹配的任务 ID，将 SU-xxx 引用记录到 `tasks-supplement.json` 的 `leverage_patches` 数组：

```json
{
  "task_id": "2.3",
  "append_leverage": ["SU-001 (class-validator)", "SU-003 (ExceptionFilter)"]
}
```

**不原地修改 tasks.md**。task-execute 在加载任务时自动合并 supplement 中的 leverage 补丁。

### 5c. 写入 `shared-utilities-plan.json`

```json
{
  "created_at": "ISO8601",
  "mode": "new | existing",
  "existing_utilities": [
    {
      "id": "EU-001",
      "type": "email-service",
      "location": "src/utils/email.ts",
      "quality": "good",
      "action": "reuse | refactor"
    }
  ],
  "shared_utilities": [
    {
      "id": "SU-001",
      "type": "validator",
      "library": "class-validator",
      "decision": "use-third-party | self-implement",
      "b1_task_id": "1.5",
      "affects_tasks": ["2.3", "2.7", "3.1"]
    }
  ],
  "tasks_updated": 24,
  "b1_tasks_added": 4
}
```

**输出**：`Phase 5 ✓ {N} 共享工具（复用 {M} 现有 + 新建 {K}），{P} 个任务更新了 _Leverage_`，自动继续。

---

## 输出文件

```
.allforai/project-forge/
├── shared-utilities-plan.json          # 主产物，Phase 5 完成标志
├── tasks-supplement.json               # B1 任务 + _Leverage_ 补丁（task-execute 加载时合并）
└── existing-utilities-index.json       # existing 模式下的已有工具清单（Step 1）
```

各子项目 tasks.md **不被修改**。B1 任务和 _Leverage_ 补丁写入 `tasks-supplement.json`，由 task-execute 在加载时动态合并。

---

## 3 条铁律

### 1. 用户只停顿一次（auto-mode 零停顿）

Step 4 是唯一的用户交互点。Step 1-3 全自动执行，Step 5 用户确认后全自动完成，不再询问。auto-mode 下 Step 4 也自动采纳推荐选项，实现全流程零停顿。

### 2. 不重复盘点

EU-xxx（已有实现）直接采用，不进入三方库调研。SU-xxx（新建）才需要 Step 3 调研。

### 3. 共享层放 B1

所有共享工具任务注入 B1（Foundation 层），确保在 B2/B3 业务代码编写前完成，形成可复用基础。
