---
description: "全流程编排：product-design → dev-forge → deadhunt → code-tuner，四层联动。支持 full / resume 模式，existing 标记现有代码项目"
argument-hint: "[mode: full|resume] [existing] [skip: layer]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion"]
---

# Full Pipeline — 全流程编排

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

> **跨插件调用约定**：本命令是「导航员」。
> - Layer 1（product-design）在本插件内执行，可用 `${CLAUDE_PLUGIN_ROOT}/skills/` 路径加载技能。
> - Layer 2-4（dev-forge、deadhunt、code-tuner）为独立插件，物理路径不可预测。编排命令提示用户执行对应斜杠命令，通过 `.allforai/` 产物作为层间合约。

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 新项目，从头执行全流程
- **`full existing`** → 现有代码项目，product-concept 以 reverse mode 从代码反推概念，之后正常从上往下走
- **`full skip: layer`** → 从头执行，但跳过指定层（如 `skip: deadhunt`）
- **`resume`** → 检测已有产物，从第一个未完成阶段开始

> **现有项目同样从上往下**：用户加 `existing` 标记后，Phase 1 的 `product-concept` 会以 reverse mode 从代码反推产品概念，概念确立后 product-map → screen-map → … 正常从上往下走，流程与新项目完全一致。

## 四层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Full Pipeline (全流程)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Layer 1: Product Design (产品设计层)                 │  │
│  │  委托 /product-design full 执行 8 阶段               │  │
│  │  concept → product-map → screen-map → use-case       │  │
│  │  → feature-gap → feature-prune → ui-design → audit  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓ 质量门禁                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Layer 2: Dev Forge (开发层)                         │  │
│  │  提示用户执行 /seed-forge + /product-verify          │  │
│  │  seed-forge 模式: full|plan|fill|clean               │  │
│  │  product-verify 模式: static|dynamic|full|refresh    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓ 质量门禁                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Layer 3: DeadHunt (QA层)                           │  │
│  │  提示用户执行 /deadhunt                              │  │
│  │  Phase 0→1→2→3→4→5 (6阶段)                         │  │
│  │  模式: static|deep|full|incremental                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓ 质量门禁                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Layer 4: Code Tuner (架构层)                       │  │
│  │  提示用户执行 /code-tuner                            │  │
│  │  Phase 0→1→2→3→4 (5阶段)                           │  │
│  │  模式: full|compliance|duplication|abstraction|report │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 编排流程

```
Phase 0: 产物探测 + 初始化
  扫描 .allforai/，标记哪些层已完成
  读取用户参数，确定 project_type（existing / greenfield）
  full 模式 → 从 Phase 1 开始
  resume 模式 → 从第一个未完成阶段开始
  ↓ 初始化全局决策追踪文件（含 project_type）
Phase 1: Layer 1 - Product Design
  用户指定 existing → product-concept 进入 reverse mode（代码反推概念）
  未指定 existing → product-concept 正常 forward mode
  概念确立后，product-map / screen-map / ... 正常从上往下走
  完成后记录决策到 global-decisions.json
  ↓ 质量门禁检查（PASS/FAIL）
Phase 2: Layer 2 - Dev Forge
  提示用户执行 /seed-forge 和 /product-verify
  读取 .allforai/seed-forge/ 和 .allforai/product-verify/ 产出
  记录未实现任务，反馈到 feature-gap
  ↓ 质量门禁检查（实现率 >= 90%）
Phase 3: Layer 3 - DeadHunt
  提示用户执行 /deadhunt
  读取 .allforai/deadhunt/output/ 产出
  记录问题，反馈到 product-design
  ↓ 质量门禁检查（无 P0 级问题）
Phase 4: Layer 4 - Code Tuner
  提示用户执行 /code-tuner
  读取 .allforai/code-tuner/ 产出
  记录架构问题
  ↓ 质量门禁检查（架构评分 >= 70）
Phase 5: 跨层一致性检查
  合并所有层的审计结果
  检查跨层冲突
  生成最终报告
  ↓ 输出最终报告 + 全流程摘要
```

---

## Phase 0：产物探测 + 初始化

### 产物探测

扫描以下目录，判断每个层的完成状态：

| 层 | 阶段 | 完成标志 |
|----|------|----------|
| Layer 1 | concept | `.allforai/product-concept/` 存在 |
| Layer 1 | product-map | `.allforai/product-map/task-inventory.json` 存在且 task 数 > 0 |
| Layer 1 | screen-map | `.allforai/screen-map/screen-map.json` 存在且 screen 数 > 0 |
| Layer 1 | use-case | `.allforai/use-case/use-case-tree.json` 存在 |
| Layer 1 | feature-gap | `.allforai/feature-gap/gap-tasks.json` 存在 |
| Layer 1 | feature-prune | `.allforai/feature-prune/prune-decisions.json` 存在 |
| Layer 1 | ui-design | `.allforai/ui-design/ui-design-spec.md` 存在 |
| Layer 1 | design-audit | `.allforai/design-audit/audit-report.json` 存在 |
| Layer 2 | seed-forge | `.allforai/seed-forge/seed-plan.json` 存在 |
| Layer 2 | product-verify | `.allforai/product-verify/verify-tasks.json` 存在 |
| Layer 3 | deadhunt | `.allforai/deadhunt/output/fix-tasks.json` 存在 |
| Layer 4 | code-tuner | `.allforai/code-tuner/tuner-report.md` 存在 |

### 项目类型

由用户参数决定 `project_type`：

| 用户参数 | project_type | Phase 1 行为 |
|----------|-------------|-------------|
| 包含 `existing` | **existing** | product-concept 进入 reverse mode（代码反推概念） |
| 不包含 `existing` | **greenfield** | product-concept 正常 forward mode（引导式发现） |

> 此标记只影响 Phase 1 中 `product-concept` 的执行模式，后续所有阶段流程不变。

### 模式处理

**full 模式**：从 Phase 1 开始，逐层执行。
**resume 模式**：从第一个未完成阶段开始。

### 初始化全局决策追踪

创建/更新 `.allforai/full-pipeline/global-decisions.json`：

```json
{
  "pipeline_run": {
    "mode": "full|resume",
    "project_type": "greenfield|existing",
    "started_at": "ISO8601",
    "skip_layers": []
  },
  "decisions": {
    "T008": {
      "task_id": "T008",
      "task_name": "任务名",
      "product-layer": {
        "prune_decision": "CORE|DEFER|CUT",
        "prune_reason": "原因",
        "audit_status": "PASS|FAIL|WARNING"
      },
      "dev-layer": {
        "verify_status": "IMPLEMENTED|NOT_IMPLEMENTED|PARTIAL",
        "verify_reason": "原因"
      },
      "qa-layer": {
        "deadhunt_status": "OK|ISSUE_FOUND",
        "deadhunt_issues": []
      },
      "code-layer": {
        "tuner_status": "OK|VIOLATION|DUPLICATE",
        "tuner_issues": []
      },
      "overall_status": "HEALTHY|NEEDS_ATTENTION|CRITICAL"
    }
  }
}
```

向用户展示探测结果，确认执行计划后开始。

---

## Phase 1：Layer 1 - Product Design

### 执行方式

**委托 `/product-design full`（或 `resume`）执行**，不在此处重新定义 8 阶段流程。

- full 模式 → 执行 `/product-design full`
- resume 模式且 Layer 1 部分完成 → 执行 `/product-design resume`
- skip: product-design → 跳过此层

`/product-design full` 是本插件内的命令，通过 `${CLAUDE_PLUGIN_ROOT}/skills/` 路径加载各阶段技能，包含完整的 Phase 0-8 流程（概念发现 → 产品地图 → 界面地图 → 用例集 → 功能查漏 → 功能剪枝 → UI设计 → 设计审计）。

### 现有项目：代码 → 产品概念 → 正常流程

当用户指定 `existing` 时，`product-concept` 进入 **reverse mode**：

```
代码（路由/权限/菜单/数据模型）
  ↓ product-concept reverse mode 反推
产品概念（使命/角色/痛点/商业模式）
  ↓ 概念确立，后续与 greenfield 完全一致
product-map → screen-map → use-case → feature-gap → feature-prune → ui-design → audit
```

reverse mode 的关键行为：
1. **扫描代码**：读取路由、权限守卫、菜单配置、数据模型，提取角色和功能模块
2. **搜索验证**：基于反推结果 WebSearch 竞品和行业趋势，补充代码中没有的商业层信息
3. **用户确认**：AskUserQuestion 确认反推出的问题域、角色、价值主张是否准确
4. **概念结晶**：输出 `product-concept.json`（`mode: "reverse"`）

> 概念确立后，`product-map` 的 Step 0 同样会读取代码（路由→任务、权限→角色），但有了概念层的战略上下文，提取出的任务列表会更完整、更有业务语义。这就是「从上往下」的价值——哪怕代码已经存在，也先建立概念层的全局视角。

### 决策记录

`/product-design full` 完成后，读取各阶段产出，更新 `global-decisions.json`：

```json
{
  "decisions": {
    "T001": {
      "product-layer": {
        "prune_decision": "CORE",
        "prune_reason": "高频核心功能",
        "audit_status": "PASS"
      }
    }
  }
}
```

### 质量门禁

Layer 1 完成后，检查以下条件：

| 条件 | 标准 | 失败处理 |
|------|------|----------|
| design-audit 逆向追溯 | ORPHAN = 0 | 向用户报告，询问是否继续 |
| design-audit 覆盖洪泛 | 覆盖率 >= 80% | 向用户报告，询问是否继续 |
| design-audit 横向一致性 | CONFLICT = 0 | 向用户报告，建议修复 |
| CORE 任务数量 | > 0 | 向用户报告，异常 |

**质量门禁 PASS** → 进入 Layer 2
**质量门禁 FAIL** → 向用户展示问题，询问是否：
- 修复问题后继续
- 带问题继续（记录风险）
- 中止流程

---

## Phase 2：Layer 2 - Dev Forge

### 前置检查

检查 `product-map` 是否存在（`.allforai/product-map/task-inventory.json`），不存在则中止。

### 执行方式

> Layer 2 属于 `dev-forge-skill` 独立插件，无法通过 `${CLAUDE_PLUGIN_ROOT}` 直接加载。
> 编排命令提示用户执行对应斜杠命令，然后读取 `.allforai/` 下的产出。

**Step 1：执行 seed-forge**

提示用户：

```
请执行 /seed-forge 生成种子数据。
推荐模式: /seed-forge full
完成后请回到此处继续。
```

等待用户确认后，读取 `.allforai/seed-forge/` 验证产出：
- `seed-plan.json` — 种子方案
- `forge-log.json` — 灌入日志
- `forge-data.json` — 灌入数据
- `api-gaps.json` — API 缺口

**Step 2：执行 product-verify**

提示用户：

```
请执行 /product-verify 进行产品验收。
推荐模式: /product-verify full（静态+动态）
完成后请回到此处继续。
```

等待用户确认后，读取 `.allforai/product-verify/` 验证产出：
- `static-report.json` — 静态扫描报告
- `dynamic-report.json` — 动态验证报告
- `verify-tasks.json` — 验收任务清单
- `verify-report.md` — 人类可读报告

### 反馈到 product-design

读取 `.allforai/product-verify/verify-tasks.json`，筛选 `type: "IMPLEMENT"` 的任务（= 未实现任务）：

1. 更新 `global-decisions.json`：
   ```json
   {
     "decisions": {
       "T005": {
         "dev-layer": {
           "verify_status": "NOT_IMPLEMENTED",
           "verify_reason": "代码中未找到对应实现"
         }
       }
     }
   }
   ```
2. 建议用户重新运行 `/feature-gap` 补齐缺口

### 质量门禁

| 条件 | 标准 | 失败处理 |
|------|------|----------|
| CORE 任务实现率 | >= 90% | 向用户报告，列出未实现的 CORE 任务 |
| 种子数据覆盖 | >= 80% CORE 任务 | 向用户报告，建议补充 |

**质量门禁 PASS** → 进入 Layer 3
**质量门禁 FAIL** → 向用户展示问题，询问是否继续

---

## Phase 3：Layer 3 - DeadHunt

### 前置检查

检查 `product-map` 和 `screen-map` 是否存在，不存在则中止。

### 执行方式

> Layer 3 属于 `deadhunt-skill` 独立插件。

**DeadHunt 完整流程（6 阶段）**：
- Phase 0: 项目分析
- Phase 1: 静态分析
- Phase 2: 制定测试计划
- Phase 3: 深度测试
- Phase 4: 报告生成
- Phase 5: 补充回归测试

模式：`static`（Phase 0→1→4）| `deep`（Phase 0→2→3→4→5）| `full`（全部 6 阶段）| `incremental`（变更模块）

提示用户：

```
请执行 /deadhunt 进行链路验证。
推荐模式: /deadhunt full
完成后请回到此处继续。
```

等待用户确认后，读取 `.allforai/deadhunt/output/` 验证产出：
- `fix-tasks.json` — 修复任务清单
- `validation-report-*.md` — 各客户端详细报告

### 反馈到 product-design

读取 `.allforai/deadhunt/output/fix-tasks.json`，按问题类型分类：

1. 更新 `global-decisions.json`：
   ```json
   {
     "decisions": {
       "S012": {
         "qa-layer": {
           "deadhunt_status": "ISSUE_FOUND",
           "deadhunt_issues": [
             {
               "type": "DEAD_LINK",
               "detail": "链路详情",
               "intent": "FIX"
             }
           ]
         }
       }
     }
   }
   ```
2. 建议用户：
   - 死链问题 → 修复链路（Layer 2）或从 screen-map 移除（Layer 1）
   - CRUD 缺口 → 重新运行 `/feature-gap` 补齐
   - Ghost features → 从 product-map 中移除

### 质量门禁

| 条件 | 标准 | 失败处理 |
|------|------|----------|
| P0 级问题 | 0 | 强制中止，必须修复 |
| P1 级问题 | <= 3 | 向用户报告，建议修复 |
| CORE 任务 CRUD 完整性 | 100% | 向用户报告，建议补齐 |

**质量门禁 PASS** → 进入 Layer 4
**质量门禁 FAIL** → 向用户展示问题，根据严重度决定是否中止

---

## Phase 4：Layer 4 - Code Tuner

### 前置检查

检查项目代码是否存在，不存在则中止。

### 执行方式

> Layer 4 属于 `code-tuner-skill` 独立插件。

**Code Tuner 完整流程（5 阶段）**：
- Phase 0: 项目画像
- Phase 1: 架构合规检查
- Phase 2: 重复检测
- Phase 3: 抽象机会分析
- Phase 4: 综合评分 + 报告 + 重构任务清单

模式：`full`（全部 5 阶段）| `compliance`（Phase 0→1→4）| `duplication`（Phase 0→2→4）| `abstraction`（Phase 0→3→4）| `report`（重新生成 Phase 4）

提示用户：

```
请执行 /code-tuner 进行架构分析。
推荐模式: /code-tuner full
完成后请回到此处继续。
```

等待用户确认后，读取 `.allforai/code-tuner/` 验证产出：
- `tuner-profile.json` — 项目画像
- `phase1-compliance.json` — 架构合规
- `phase2-duplicates.json` — 重复检测
- `phase3-abstractions.json` — 抽象分析
- `tuner-report.md` — 综合报告
- `tuner-tasks.json` — 重构任务清单

### 反馈到 product-design

读取 `.allforai/code-tuner/tuner-tasks.json`，按问题类型分类：

1. 更新 `global-decisions.json`：
   ```json
   {
     "decisions": {
       "T010": {
         "code-layer": {
           "tuner_status": "VIOLATION",
           "tuner_issues": [
             {
               "type": "COMPLIANCE",
               "detail": "跳层调用",
               "severity": "HIGH"
             }
           ]
         }
       }
     }
   }
   ```
2. 评估架构问题对产品层的影响（是否需要调整任务定义）

### 质量门禁

| 条件 | 标准 | 失败处理 |
|------|------|----------|
| 架构评分 | >= 70 | 向用户报告，列出主要违规 |
| 关键违规 | 0 | 向用户报告，建议修复 |

**质量门禁 PASS** → 进入 Phase 5
**质量门禁 FAIL** → 向用户展示问题，询问是否继续

---

## Phase 5：跨层一致性检查

### 合并所有层的审计结果

加载以下文件：
- `.allforai/design-audit/audit-report.json` — 设计审计
- `.allforai/product-verify/verify-tasks.json` — 开发验收任务
- `.allforai/product-verify/verify-report.md` — 开发验收报告
- `.allforai/deadhunt/output/fix-tasks.json` — QA 修复任务
- `.allforai/deadhunt/output/validation-report-*.md` — QA 验证报告
- `.allforai/code-tuner/tuner-tasks.json` — 架构重构任务
- `.allforai/code-tuner/tuner-report.md` — 架构报告

### 检查跨层冲突

| 冲突类型 | 描述 | 严重度 |
|----------|------|--------|
| gap × prune | feature-gap 报缺口，feature-prune 标 CUT | CONFLICT |
| verify × prune | CORE 任务未实现 | CONFLICT |
| deadhunt × screen | screen-map 中的界面链路问题 | CONFLICT |
| tuner × product | 架构违规影响产品功能 | WARNING |

### 生成最终全流程报告

**输出文件**：
- `.allforai/full-pipeline/pipeline-report.json` — 全量报告（机器可读）
- `.allforai/full-pipeline/pipeline-report.md` — 人类可读摘要
- `.allforai/full-pipeline/global-decisions.json` — 全局决策追踪

**JSON Schema**：

```json
{
  "pipeline_run": {
    "mode": "full|resume",
    "project_type": "greenfield|existing",
    "started_at": "ISO8601",
    "completed_at": "ISO8601",
    "duration_seconds": 3600,
    "skip_layers": []
  },
  "layers": {
    "product-design": {
      "status": "COMPLETED|SKIPPED|FAILED",
      "quality_gate": "PASS|FAIL",
      "key_metrics": {
        "tasks": 150,
        "screens": 80,
        "use_cases": 300
      },
      "artifacts": [
        ".allforai/design-audit/audit-report.json"
      ]
    },
    "dev-forge": {
      "status": "COMPLETED|SKIPPED|FAILED",
      "quality_gate": "PASS|FAIL",
      "key_metrics": {
        "seed_records": 5000,
        "implementation_rate": "95%"
      },
      "artifacts": [
        ".allforai/seed-forge/seed-plan.json",
        ".allforai/product-verify/verify-tasks.json"
      ]
    },
    "deadhunt": {
      "status": "COMPLETED|SKIPPED|FAILED",
      "quality_gate": "PASS|FAIL",
      "key_metrics": {
        "issues_found": 2,
        "p0_issues": 0
      },
      "artifacts": [
        ".allforai/deadhunt/output/fix-tasks.json"
      ]
    },
    "code-tuner": {
      "status": "COMPLETED|SKIPPED|FAILED",
      "quality_gate": "PASS|FAIL",
      "key_metrics": {
        "score": 85,
        "violations": 5,
        "duplicates": 12
      },
      "artifacts": [
        ".allforai/code-tuner/tuner-report.md",
        ".allforai/code-tuner/tuner-tasks.json"
      ]
    }
  },
  "cross_layer_conflicts": [
    {
      "type": "gap × prune",
      "severity": "CONFLICT",
      "task_id": "T008",
      "description": "feature-gap 报此任务有缺口，但 feature-prune 标为 CUT",
      "suggested_action": "建议保留此功能，优先补齐实现"
    }
  ],
  "summary": {
    "total_tasks": 150,
    "healthy_tasks": 140,
    "needs_attention_tasks": 8,
    "critical_tasks": 2,
    "overall_health_score": 93
  }
}
```

**Markdown 报告结构**：

```markdown
# 全流程执行报告

## 执行摘要

- 执行模式: {full/resume}
- 执行时间: {开始时间} — {结束时间}（{耗时}）
- 总体健康评分: {0-100}

## 各层状态

| 层 | 状态 | 质量门禁 | 关键指标 |
|----|------|----------|----------|
| Product Design | 完成/跳过/失败 | PASS/FAIL | 任务: X, 界面: X |
| Dev Forge | 完成/跳过/失败 | PASS/FAIL | 种子数据: X, 实现率: XX% |
| DeadHunt | 完成/跳过/失败 | PASS/FAIL | 问题: X, P0: X |
| Code Tuner | 完成/跳过/失败 | PASS/FAIL | 评分: X, 违规: X |

## 跨层冲突

### CONFLICT（必须修复）
| # | 冲突类型 | 任务 | 说明 | 建议操作 |
|---|----------|------|------|----------|
| ... | ... | ... | ... | ... |

### WARNING（建议关注）
| # | 冲突类型 | 任务 | 说明 |
|---|----------|------|------|
| ... | ... | ... | ... |

## 需要关注的任务

| 任务ID | 任务名 | 问题数 | 严重度 | 建议 |
|--------|--------|--------|--------|------|
| T008 | 任务名 | 3 | CRITICAL | 优先修复 |

## 下一步行动

1. [ ] 修复 X 个 CONFLICT 级冲突
2. [ ] 补齐 X 个未实现的 CORE 任务
3. [ ] 修复 X 个 P0 级问题
4. [ ] 优化 X 处架构违规

## 详细报告

- 产品设计: `.allforai/design-audit/audit-report.json`
- 开发验收: `.allforai/product-verify/verify-report.md`
- QA验证: `.allforai/deadhunt/output/validation-report-*.md`
- 架构分析: `.allforai/code-tuner/tuner-report.md`
```

---

## 全流程执行摘要（强制输出）

所有阶段完成后，在对话中输出全流程摘要：

```
## 全流程执行摘要

> 执行模式: {full/resume}
> 总体健康评分: {0-100}

### 各层状态

| 层 | 状态 | 质量门禁 | 关键指标 | 备注 |
|----|------|----------|----------|------|
| Product Design | 完成/跳过 | PASS/FAIL | 任务: X, 界面: X | {备注} |
| Dev Forge | 完成/跳过 | PASS/FAIL | 种子: X, 实现率: XX% | {备注} |
| DeadHunt | 完成/跳过 | PASS/FAIL | 问题: X, P0: X | {备注} |
| Code Tuner | 完成/跳过 | PASS/FAIL | 评分: X, 违规: X | {备注} |

### 跨层冲突

- CONFLICT: X 处
- WARNING: X 处

### 需要关注的任务

- CRITICAL: X 个
- NEEDS_ATTENTION: X 个
- HEALTHY: X 个

### 产出文件

> 全部产出位于 `.allforai/` 目录下
> 全流程报告: `.allforai/full-pipeline/pipeline-report.md`
> 全局决策: `.allforai/full-pipeline/global-decisions.json`
```

---

## 铁律

### 1. 层层递进，不跳过质量门禁

每层完成后必须通过质量门禁才能进入下一层。质量门禁失败时，向用户报告问题，由用户决定是否带问题继续。

### 2. 反馈循环基于真实产出

各层反馈信息来自各插件的真实产出文件（`verify-tasks.json`、`fix-tasks.json`、`tuner-tasks.json`），汇总到 `global-decisions.json`，不额外生成中间文件。

### 3. 用户可在任意阶段中止

检查点失败或用户主动中止时，保存已有产出，输出部分摘要。

### 4. 幂等性

多次运行结果一致。不产生副作用，每次运行都是全新的独立执行。

### 5. 全局决策追踪是唯一真相来源

所有层的决策都汇聚到 `global-decisions.json`，这是整个流程的决策真相来源。
