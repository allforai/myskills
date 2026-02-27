---
name: task-execute
description: >
  Use when the user wants to "execute tasks from tasks.md", "run implementation round",
  "start coding from task list", "execute batch tasks", "resume implementation",
  "任务执行", "执行开发任务", "按任务列表写代码", "继续实现", "断点续作",
  or needs to systematically execute atomic tasks from tasks.md with progress tracking,
  automatic execution strategy selection, and per-round incremental verification.
  Requires tasks.md (from design-to-spec) and project-manifest.json (from project-setup).
version: "1.0.0"
---

# Task Execute — 任务执行与追踪

> 加载 tasks.md → 逐 Round 执行 → 进度追踪 → 增量验证

## 目标

以 `tasks.md` 和 `project-manifest.json` 为输入，系统化执行原子任务：

1. **自动编排** — 按 Round 结构分组任务，自动推断执行策略
2. **委托执行** — 将实际代码编写委托给 superpowers skill
3. **进度追踪** — 实时更新 build-log.json，支持断点续作
4. **增量验证** — 每 Round 完成后自动触发 lint/test + 增量 product-verify

---

## 定位

```
design-to-spec（规格层）   task-execute（执行层）   e2e-verify（验证层）
生成 tasks.md 任务列表     逐 Round 执行 + 追踪     跨端业务流验证
文档                      代码                     测试
```

**前提**：
- 必须有各子项目的 `tasks.md`（来自 design-to-spec）
- 必须有 `project-manifest.json`（来自 project-setup）
- 推荐有 `requirements.md`（增量验证用）

---

## 快速开始

```
/task-execute              # 从 Round 0 开始（或从 build-log 断点续作）
/task-execute round 2      # 仅执行指定 Round
/task-execute resume       # 从 build-log.json 断点续作（同无参数）
```

---

## 增强协议（WebSearch + 4E+4V）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：
- `"{framework} implementation patterns {year}"`
- `"{language} project structure conventions {year}"`

**4E+4V 重点**：
- **E3 Guardrails**: 执行任务时参照 `_Guardrails: T001.rules[1,2]_` 标注，确保业务规则落地
- **E4 Context**: `_Risk: HIGH_` 任务优先 review，执行后额外验证

---

## build-log.json

进度追踪的核心数据结构：

```json
{
  "version": "1.0.0",
  "started_at": "ISO8601",
  "updated_at": "ISO8601",
  "rounds": [
    {
      "round": 0,
      "name": "Monorepo Setup",
      "status": "pending | in_progress | completed | failed",
      "execution_strategy": "subagent-driven-development | dispatching-parallel-agents",
      "strategy_reason": "仅 3 个任务，串行更简单",
      "started_at": null,
      "completed_at": null,
      "tasks": [
        {
          "id": "0.1",
          "sub_project": "global",
          "title": "配置 monorepo workspace + 根配置文件",
          "status": "pending | in_progress | completed | failed | skipped",
          "started_at": null,
          "completed_at": null,
          "files_modified": [],
          "error": null
        }
      ],
      "quality_checks": {
        "lint": { "status": "pending | pass | fail | skipped", "output": null },
        "test": { "status": "pending | pass | fail | skipped", "output": null }
      },
      "verification": {
        "status": "pending | pass | fail | skipped",
        "scope": { "task_ids": [], "sub_projects": [] },
        "issues": []
      }
    }
  ],
  "summary": {
    "total_tasks": 0,
    "completed": 0,
    "failed": 0,
    "skipped": 0,
    "current_round": 0
  }
}
```

**写入位置**：`.allforai/project-forge/build-log.json`（全局，非按子项目拆分）。

---

## 工作流

```
前置: 加载
  各子项目 tasks.md → 解析全部任务（id / sub_project / files / batch）
  project-manifest.json → 子项目列表 + 类型
  build-log.json（若存在 → resume 模式）
  ↓
Step 0: 初始化
  build-log.json 不存在 → 初始化:
    按 Round 结构分组:
      Round 0: B0（全局 monorepo setup）
      Round 1: B1（各子项目 Foundation，并行）
      Round 2: B2（后端 API）∥ B3（前端 UI）
      Round 3: B4（Integration，等 B2 完成）
      Round 4: B5（Testing）
    写入 build-log.json（全部 pending）
  build-log.json 已存在 → resume:
    读取 summary.current_round
    增量检测: 重新解析各子项目 tasks.md，对比 build-log.json 已有 Round:
      发现新批次（如 B-FIX）不在 build-log.json 中
        → 追加为新 Round（round = max_round + 1）
        → 写入 build-log.json（新 Round 全部 pending）
      无新批次 → 跳过
    从第一个非 completed Round 继续
  确定起始 Round → 展示执行计划
  ↓
Step 1: 执行策略推断（每 Round 开始时）
  解析当前 Round 全部任务的 Files 字段
  构建 file → [task_id] 映射
  判断:
    有文件交叉 OR 任务数 <= 2
      → subagent-driven-development（串行，防冲突）
    无交叉且分属不同子项目
      → dispatching-parallel-agents（并行，快）
  记录 round.execution_strategy + strategy_reason
  展示: "Round {N}: {任务数} 个任务，策略: {策略}（{reason}）"
  ↓
Step 2: 逐任务执行
  subagent-driven-development 模式:
    按 id 顺序逐个执行
    每任务:
      task.status = in_progress, started_at = now
      调用 /subagent-driven-development 执行该任务
      成功 → task.status = completed, files_modified 从 git diff 提取
      失败 → task.status = failed, error 记录
      更新 build-log.json（实时写入，不等 Round 结束）
  dispatching-parallel-agents 模式:
    按 sub_project 分组，每组内按 id 顺序
    调用 /dispatching-parallel-agents 并行执行各组
    收集结果 → 逐任务更新 build-log.json
  失败处理:
    单任务失败 → 记录 error，继续同 Round 其他无依赖任务
    后续任务依赖失败任务的产出文件 → status = skipped
  ↓
Step 3: Round 质量检查
  Round 全部任务完成（或部分 failed/skipped）后:
    运行 lint → quality_checks.lint 更新
    lint 失败 → agent 自动修复 lint 问题 → 重跑
    运行 test → quality_checks.test 更新
    test 失败 → 记录失败测试，不阻塞（Round 级验证会捕获）
  ↓
Step 4: Round 增量验证
  quality_checks 完成后:
    收集本 Round 涉及的 task_id + sub_project
    写入 verification.scope
    调用 product-verify scope 模式:
      S1: Task → API 覆盖检查（仅 scope.task_ids）
      S3: 约束 → 代码覆盖检查（仅 scope.task_ids 关联的约束）
      S2/S4/Dynamic: 跳过（全量才有意义）
    结果写入 verification.issues
    verification.status = pass | fail
    展示验证结果（仅报告，不阻塞下一 Round）
  Round 结束:
    round.status = completed
    summary 更新: completed 计数, current_round++
  → 进入下一 Round 的 Step 1
```

---

## Resume 语义

```
/task-execute resume 行为:

读取 build-log.json
增量检测（修复轮次发现）:
  重新解析各子项目 tasks.md
  对比 build-log.json 中已有 Round 的任务 id 集合
  tasks.md 中存在 build-log 未收录的批次（如 Phase 4.5 追加的 B-FIX）
    → 追加为新 Round（round = max_round + 1, status = pending）
    → 更新 build-log.json + summary.total_tasks
  无新批次 → 跳过

找到 summary.current_round
检查该 Round:
  round.status = in_progress
    → 从第一个非 completed 任务继续
  round.status = failed
    → 重试 failed 任务（跳过已 completed 的）
  round.status = completed
    → 推进到下一 Round

任务级判定:
  status = completed + files_modified 非空 → 跳过（已完成）
  status = failed → 重新执行
  status = skipped → 检查依赖任务是否已修复，是则重新执行
  status = in_progress → 视为中断，重新执行
  status = pending → 正常执行
```

---

## 执行策略推断规则

| 条件 | 策略 | 理由 |
|------|------|------|
| Round 内任务的 Files 有交叉（同一文件出现在多个任务中） | subagent-driven-development | 文件冲突风险，必须串行 |
| Round 内任务分属不同子项目且文件无交叉 | dispatching-parallel-agents | 天然隔离，可并行 |
| Round 内只有 1-2 个任务 | subagent-driven-development | 并行无意义 |

**检测方式**：解析 Round 内所有任务的 `Files:` 行，构建 `file → [task_id]` 映射。任一文件对应多个 task_id → 有交叉。

---

## 输出文件

```
.allforai/project-forge/
├── build-log.json                  # 进度追踪（全局）
└── sub-projects/{name}/
    ├── tasks.md                    # 输入（来自 design-to-spec）
    └── requirements.md             # 增量验证参考
```

---

## 5 条铁律

### 1. 执行委托，不自己写代码

task-execute 是编排层，实际代码编写委托给 superpowers skill（subagent-driven-development 或 dispatching-parallel-agents）。不直接生成业务代码。

### 2. build-log 实时更新

每个任务状态变更立即写入 build-log.json，不等 Round 结束。中断后可精确 resume。

### 3. 策略自动推断，不问用户

根据文件交叉检测自动选择串行/并行策略。用户无需理解策略差异。

### 4. 验证仅报告，不阻塞

Round 增量验证发现问题时展示给用户，但不阻塞下一 Round 执行。问题汇总到 build-log.json 供后续处理。

### 5. 失败隔离

单任务失败不终止 Round。仅跳过依赖该任务产出文件的后续任务，其余继续执行。
