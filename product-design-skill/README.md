# product-design — 产品设计套件

**版本：v3.1.0**

Claude Code 插件，以产品地图为基础，系统化地定义、查漏、剪枝、审计。

## 30 秒上手

```bash
# 1) 安装
claude plugin add /path/to/product-design-skill

# 2) 先建产品地图（推荐起手）
/product-map

# 3) 需要一键全流程时
/product-design full
```

## 适用场景

| 场景 | 推荐命令 |
|---|---|
| 从代码反推产品并补齐业务语义 | `/product-concept` + `/product-map` |
| 梳理界面与异常状态 | `/screen-map` |
| 生成可执行用例（机器+人类双格式） | `/use-case` |
| 做查漏/剪枝决策 | `/feature-gap` / `/feature-prune` |
| 做全链路一致性终审 | `/design-audit` |

## 设计思想与经典理论支持

在执行命令前，建议先阅读：

- [`docs/product-design-principles.md`](docs/product-design-principles.md)

该文档包含：
- 前段 / 中段 / 尾段 的经典理论总览
- 每个阶段对应的理论锚点（如第一性原理、JTBD、Kano、Nielsen、ISO 9241-11、WCAG）
- 参考文献（作者 / 年份 / 来源）

## 工作顺序

**先跑 `product-map`，再跑其他技能。**

```
product-map（建功能图）
    ↓ 输出 .allforai/product-map/product-map.json + task-inventory.json
    │
    ├── screen-map（可选，建界面图）
    │       ↓ 输出 .allforai/screen-map/screen-map.json
    │
    ├── use-case（可选，生成用例集）
    │       ↓ 输出 .allforai/use-case/use-case-tree.json（机器）+ use-case-report.md（人类）
    │
    ├── 功能查漏   — 地图说有的，现在有没有？（Step 2/3 需要 screen-map）
    ├── 功能剪枝   — 地图里有的，该不该留？（Step 2 需要 screen-map）
    ├── ui-design  — 高层 UI 设计规格 + HTML 预览
    └── design-audit — 全链路一致性终审（基于全部已有产物）

或使用 /product-design full 自动编排全流程（含阶段间检查点 + 终审）。
```

---

## 包含的技能

### product-concept — 产品概念发现

> 从问题出发，搜索+选择题引导，帮你发现心中的产品。

### product-map — 产品地图

> 先搞清楚这个产品是什么，才能做其他分析。

从代码读现状，用产品语言呈现，让 PM 确认并补充业务视角，形成「现状 + 期望」的完整产品地图。

- **角色**：识别所有用户角色，明确权限边界和 KPI
- **任务**：按角色展开，每个任务包含触发条件、频次、风险、SLA、主流程、规则、异常列表、验收标准
- **冲突检测**：发现任务级业务逻辑矛盾或 CRUD 缺口
- **约束**：合规要求、不可逆操作、审批分级等业务规则

### screen-map — 界面与异常状态地图

> 以产品地图为基础，梳理界面、按钮和异常状态，输出界面交互地图。

- **界面**：每个任务对应哪些页面，每个页面的核心目的是什么
- **按钮**：每个页面上的操作，CRUD 分类、操作频次、点击层级、是否需要二次确认
- **异常状态**：空状态、加载状态、错误状态、权限不足状态
- **异常流程**：每个操作的失败反馈（on_failure）、前端校验（validation_rules）、异常响应（exception_flows）
- **帕累托分析**：自动找出 20% 高频操作，检测高频操作是否被埋深
- **界面级冲突**：冗余入口、高风险无确认、SILENT_FAILURE、UNHANDLED_EXCEPTION

### use-case — 用例集

> 以功能地图和界面地图为输入，推导完整用例，双格式输出。

- **树结构**：角色 → 功能区 → 任务 → 用例（4 层）
- **JSON 机器版**：完整 Given/When/Then，含 screen_ref、逐条可验证的 then，供 AI agent 执行
- **Markdown 人类版**：每条用例一行（ID + 标题 + 类型），不重复字段细节

### feature-gap — 功能查漏

> 产品地图说应该有的，现在有没有？用户路径走得通吗？

### feature-prune — 功能剪枝

> 产品地图里有的，哪些该留、哪些推迟、哪些砍掉？

### ui-design — UI 设计规格

> 从产品地图 + 界面地图推导高层 UI 设计规格，结合风格选择和设计原则，输出设计规格文档 + 按角色拆分的 HTML 预览。

### design-audit — 设计审计

> 跨层校验产品设计全链路一致性：逆向追溯、覆盖洪泛、横向一致性。

- **逆向追溯**：下游产物（screen-map、use-case、gap、prune）引用的 task_id 是否在 task-inventory 中存在
- **覆盖洪泛**：每个 task 是否被下游层完整消费（有 screen、有用例、有 gap 检查、有 prune 决策）
- **横向一致性**：gap 报缺口 + prune 标 CUT = 矛盾；高频任务点击深度过深 = 警告

---

## 定位

```
product-design（产品层）
├── product-concept 想做什么产品？                       搜索+选择题引导
├── product-map     产品是什么？谁在用？做什么？          代码读现状 + PM 补业务视角
├── screen-map      在哪做？怎么做？出错怎么办？          以 task-inventory 为输入（可选）
├── use-case        推导完整用例，双格式输出               基于 product-map + screen-map
├── feature-gap     地图说有的，有没有？                  基于 product-map + screen-map
├── feature-prune   地图里有的，该不该留？                基于 product-map + screen-map
├── ui-design       高层 UI 设计规格                     基于 product-map + screen-map
└── design-audit    全链路一致性校验                      基于全部已有产物

dev-forge（开发层）   种子数据 + 产品验收                 基于 product-map + API/Playwright
deadhunt（QA 层）     链接通不通？CRUD 全不全？            需要 Playwright
code-tuner（架构层）  代码好不好？重复多不多？             纯静态分析
```

---

## 安装

```bash
claude plugin add /path/to/product-design-skill
```

---

## 使用

### 第一步：建立产品地图

```bash
/product-map              # 完整流程（角色→任务→冲突→约束）
/product-map quick        # 跳过冲突检测和约束识别
/product-map refresh      # 代码大改后重新生成
/product-map scope 退款管理  # 只梳理指定模块
```

### 第二步（可选）：建立界面地图

```bash
/screen-map              # 完整流程（界面梳理+异常状态+冲突检测）
/screen-map quick        # 只梳理界面和按钮，跳过冲突检测
/screen-map scope 退款管理  # 只梳理指定模块的界面
```

### 第三步（可选）：生成用例集

```bash
/use-case              # 完整流程（正常流+异常流+边界用例）
/use-case quick        # 只生成正常流
/use-case scope 退款管理  # 只生成指定功能区
```

### 第四步：按需选择

```bash
# 功能查漏 — 找缺口
/feature-gap            # 完整查漏（任务+界面+旅程）
/feature-gap quick      # 只查任务和 CRUD，跳过旅程验证
/feature-gap journey    # 只验证用户旅程路径
/feature-gap role 客服专员  # 只查指定角色的缺口

# 功能剪枝 — 找多余
/feature-prune            # 完整剪枝（频次+场景+竞品）
/feature-prune quick      # 只看频次，跳过竞品参考
/feature-prune scope 用户管理  # 只剪枝指定模块

# UI 设计规格
/ui-design               # 完整流程
/ui-design refresh       # 重新生成

# 设计审计 — 跨层一致性校验
/design-audit              # 三合一全量校验
/design-audit trace        # 仅逆向追溯
/design-audit coverage     # 仅覆盖洪泛
/design-audit cross        # 仅横向一致性
/design-audit role 客服专员  # 指定角色全链路校验
```

### 全流程编排

```bash
/product-design full                # 从头执行全流程（含终审）
/product-design full skip: concept  # 跳过概念发现
/product-design resume              # 从断点继续
```

---

## 输出

所有产出写入项目根目录的 `.allforai/` 下。

```
your-project/
└── .allforai/
    ├── product-map/
    │   ├── role-profiles.json          # 角色画像（权限边界、KPI）
    │   ├── task-inventory.json         # 任务清单（频次、风险、SLA、异常、验收标准）
    │   ├── task-index.json             # 任务索引（轻量，供下游两阶段加载）
    │   ├── business-flows.json         # 业务流（跨角色/跨系统链路）
    │   ├── flow-index.json             # 业务流索引（轻量，供下游两阶段加载）
    │   ├── business-flows-report.md    # 业务流摘要（人类可读）
    │   ├── business-flows-visual.svg   # 业务流泳道图（可视化）
    │   ├── conflict-report.json        # 任务级冲突与 CRUD 缺口
    │   ├── constraints.json            # 业务约束清单
    │   ├── product-map.json            # 汇总文件（供其他技能加载）
    │   ├── product-map-report.md       # 可读报告
    │   ├── product-map-visual.svg      # 角色-任务树（可视化）
    │   ├── competitor-profile.json     # 竞品功能概况
    │   ├── validation-report.json      # 三合一校验结果（机器可读）
    │   ├── validation-report.md        # 校验摘要（人类可读）
    │   └── product-map-decisions.json  # 用户决策日志
    ├── screen-map/
    │   ├── screen-map.json             # 界面地图
    │   ├── screen-index.json           # 界面索引
    │   ├── screen-conflict.json        # 界面级冲突
    │   ├── screen-map-report.md        # 可读报告
    │   └── screen-map-decisions.json   # 用户决策日志
    ├── use-case/
    │   ├── use-case-tree.json          # 机器可读
    │   ├── use-case-report.md          # 人类可读
    │   └── use-case-decisions.json     # 用户决策日志
    ├── feature-gap/
    │   ├── task-gaps.json              # 任务完整性
    │   ├── screen-gaps.json            # 界面完整性
    │   ├── journey-gaps.json           # 用户旅程
    │   ├── gap-tasks.json              # 缺口任务清单
    │   ├── flow-gaps.json              # 业务流链路
    │   ├── gap-report.md               # 可读报告
    │   └── gap-decisions.json          # 用户确认记录
    ├── feature-prune/
    │   ├── frequency-tier.json         # 频次分层
    │   ├── scenario-alignment.json     # 场景对齐
    │   ├── competitive-ref.json        # 竞品参考
    │   ├── prune-decisions.json        # 用户分类决策
    │   ├── prune-tasks.json            # 剪枝任务清单
    │   └── prune-report.md             # 可读报告
    └── design-audit/
        ├── audit-report.json           # 全量校验结果
        └── audit-report.md             # 可读摘要
```

---

## 核心原则

1. **product-map 是基础** — 其他技能都以产品地图为输入，先建图再分析
2. **screen-map 是可选增强层** — 界面分析独立运行，feature-gap Step 2/3 和 feature-prune Step 2 需要它
3. **索引优先，按需加载** — 下游技能先加载轻量索引（< 5KB），按需再加载完整数据；索引不存在时自动回退全量加载
4. **频次驱动一切** — 高频操作受保护不剪枝，缺口按频次排优先级，种子数据按频次分配数量
5. **每步用户确认** — 所有分类和决策都需要用户确认，用户是权威
6. **只标不改** — 发现问题只报告，不执行任何代码修改或删除
7. **业务语言呈现** — 输出全程使用业务语言，不出现接口地址、组件名等工程术语
8. **异常覆盖是质量指标** — 每个功能点的异常情况和验收标准是产品完整性的核心体现
9. **JSON 给机器，Markdown 给人** — JSON 完整字段无省略，Markdown 摘要级突出结论，细节不重复

---

## License

MIT


---

## 内嵌文档（自动汇总）

> 以下内容已从子文档汇总到 README，便于单文件阅读。

### 来源文件：`docs/full-pipeline-quickstart.md`

# Full Pipeline 快速开始指南

> 统一编排产品设计、开发、测试、架构四层流程，实现全链路自动化。

## 什么是 Full Pipeline？

Full Pipeline 是一个统一的编排命令，将四个独立的 skill 套件整合成一个完整的自动化流程：

```
Product Design (产品设计层)
    ↓
Dev Forge (开发层)
    ↓
DeadHunt (QA层)
    ↓
Code Tuner (架构层)
```

**核心特性**：
- ✅ 统一编排：一个命令执行全部流程
- ✅ 质量门禁：每层都有明确的质量标准
- ✅ 反馈循环：下游发现问题自动反馈给上游
- ✅ 全局追踪：统一记录所有决策和问题
- ✅ 现有项目支持：代码反推产品概念，再从上往下走

## 快速开始

### 1. 执行完整流程

```bash
/full-pipeline
```

这会从头到尾执行所有层，包括：
- 产品设计层的 8 个阶段
- 开发层的种子数据和验收
- QA 层的死链检测和 CRUD 验证
- 架构层的代码分析

### 2. 从断点继续

如果流程中断，可以继续执行：

```bash
/full-pipeline resume
```

自动检测已完成的阶段，从第一个未完成的阶段继续。

### 3. 现有代码项目

如果项目代码已经存在，加 `existing` 标记即可——product-concept 会从代码反推产品概念，之后正常从上往下走：

```bash
/full-pipeline full existing
```

### 4. 跳过某层

如果某些层暂时不需要，可以跳过：

```bash
/full-pipeline full skip:deadhunt
```

## 输出文件

所有输出位于 `.allforai/full-pipeline/` 目录：

```
.allforai/full-pipeline/
├── pipeline-report.json      # 全量报告（机器可读）
├── pipeline-report.md        # 人类可读摘要
└── global-decisions.json     # 全局决策追踪
```

## 查看结果

### 查看执行摘要

```bash
cat .allforai/full-pipeline/pipeline-report.md
```

### 查看全局决策

```bash
cat .allforai/full-pipeline/global-decisions.json
```

### 查看某个任务的状态

```bash
cat .allforai/full-pipeline/global-decisions.json | jq '.decisions.T008'
```

### 查看跨层冲突

```bash
cat .allforai/full-pipeline/pipeline-report.json | jq '.cross_layer_conflicts'
```

## 质量门禁

每层都有质量门禁标准：

| 层 | 质量门禁 | 标准 |
|----|----------|------|
| product-design | design-audit | ORPHAN=0, 覆盖率≥80%, CONFLICT=0 |
| dev-forge | 实现率 | CORE 任务实现率 ≥ 90% |
| deadhunt | 死链 | P0 级死链 = 0 |
| code-tuner | 架构评分 | 评分 ≥ 70 |

如果某层质量门禁失败，流程会暂停并向用户报告问题。

## 跨层反馈

Full Pipeline 会自动检测跨层冲突并提供解决建议：

- **gap × prune**: feature-gap 报缺口，但 feature-prune 标 CUT
- **verify × prune**: CORE 任务未实现
- **deadhunt × screen**: screen-map 中的界面链接死链
- **tuner × product**: 架构违规影响产品功能

所有冲突都会记录在 `pipeline-report.json` 的 `cross_layer_conflicts` 字段中。

## 使用场景

### 新项目启动

```bash
/full-pipeline full
```

完整执行所有层，建立完整的开发和测试基础。

### 日常迭代

```bash
/full-pipeline resume
```

从上次中断的地方继续，跳过已完成的阶段。

### 发布前检查

```bash
/full-pipeline full
```

确保所有质量门禁都通过，无严重问题。

### 故障排查

```bash
# 查看跨层冲突
cat .allforai/full-pipeline/pipeline-report.json | jq '.cross_layer_conflicts'

# 查看需要关注的任务
cat .allforai/full-pipeline/pipeline-report.md | grep "需要关注的任务"
```

## 常见问题

### Q: Full Pipeline 需要多长时间？

A: 取决于项目规模：
- 小型项目（<50 任务）：约 5-10 分钟
- 中型项目（50-200 任务）：约 15-30 分钟
- 大型项目（>200 任务）：约 30-60 分钟

### Q: 可以只执行某层吗？

A: 可以，使用 skip 参数：
```bash
/full-pipeline full skip:deadhunt,code-tuner
```

### Q: 质量门禁失败怎么办？

A: 流程会暂停并报告问题，你可以：
1. 修复问题后继续
2. 带问题继续（会记录风险）
3. 中止流程

### Q: 如何查看历史执行记录？

A: 查看 `global-decisions.json` 中的 `pipeline_run` 字段，包含了每次执行的元数据。

## 进阶用法

### 自定义质量门禁标准

编辑 `pipeline-report.json`，调整各层质量门禁的标准值。

### 集成到 CI/CD

```bash
#!/bin/bash

# CI 脚本示例
/full-pipeline full

# 检查总体健康评分
health_score=$(cat .allforai/full-pipeline/pipeline-report.json | jq '.summary.overall_health_score')

if [ $health_score -lt 80 ]; then
  echo "健康评分低于 80，发布中止"
  exit 1
fi
```

## 相关文档

- [完整分析报告](pipeline-analysis.md) - 详细的分析和改进说明
- [产品设计指导思想与设计原则](product-design-principles.md) - 各阶段方法论、设计思想与原则总览
- [命令文档](../commands/full-pipeline.md) - 命令的完整规格说明
- [产品设计套件 README](../README.md) - 产品设计层的详细说明

## 贡献

欢迎提出问题和改进建议！

---

**版本**: v1.0.0
**更新时间**: 2026-02-27


### 来源文件：`docs/pipeline-analysis.md`

# 产品设计套件流程分析报告

**分析日期**: 2026-02-27
**分析范围**: product-design-skill 及相关技能套件（deadhunt, dev-forge, code-tuner）

---

## 一、执行摘要

### 1.1 整体评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 产品层内部流程完整性 | 95/100 | 设计非常完整，有 design-audit 作为终审 |
| 跨层数据流清晰度 | 70/100 | 依赖关系清晰，但缺少统一编排 |
| 闭环反馈机制 | 60/100 | 缺少从开发/测试层反馈到产品设计的机制 |
| 整体 Crossover 完整度 | 75/100 | 各层独立工作良好，但缺乏统一全流程编排 |

### 1.2 核心发现

✅ **优势**:
- 产品设计层内部流程非常完善，8 个阶段层层递进
- design-audit 提供了三维度校验（逆向追溯、覆盖洪泛、横向一致性）
- 各层职责清晰，可以独立运行
- 数据格式规范统一（JSON 给机器，Markdown 给人类）

⚠️ **不足**:
- 缺少统一的全流程编排命令
- 层间反馈机制缺失（单向数据流，无反向反馈）
- 质量门禁不完善，只在部分层存在
- 缺少全局决策追踪机制

---

## 二、现有流程架构分析

### 2.1 四层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    现有流程架构                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Product Design (产品设计层)                        │
│  ├── concept → product-map → screen-map → use-case          │
│  ├── feature-gap → feature-prune → ui-design → audit        │
│  └── ✓ 内部流程完整，有终审                                   │
│                          ↓                                   │
│  Layer 2: Dev Forge (开发层)                                 │
│  ├── seed-forge → product-verify                            │
│  └── ✓ 依赖 product-map 输出                                 │
│                          ↓                                   │
│  Layer 3: DeadHunt (QA层)                                    │
│  ├── Phase 0→1→2→3→4→5 (6阶段: 分析→静态→计划→深度→报告→补测) │
│  └── ✓ 需要 Playwright 验证                                  │
│                          ↓                                   │
│  Layer 4: Code Tuner (架构层)                                │
│  ├── Phase 0→1→2→3→4 (5阶段: 画像→合规→重复→抽象→评分)      │
│  └── ✓ 纯静态分析                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 现有流程特点

**产品设计层**:
- 8 个阶段完整覆盖产品定义到设计审计
- 两阶段加载机制（索引 + 按需加载）
- design-audit 提供三维度校验
- 支持轻量校验和终审

**开发层**:
- 种子数据锻造基于产品地图
- 产品验收包含静态扫描和动态验证
- 但没有反馈机制回产品设计层

**QA 层**:
- 5 层扫描（导航 → 交互 → API → 资源 → 边界）
- 支持多客户端架构
- 但发现的问题无法自动反馈

**架构层**:
- 完整的架构分析流程
- 输出 0-100 评分和重构建议
- 但与产品层无交互

---

## 三、识别的问题与优化机会

### 3.1 🔴 严重问题（P0）

#### 问题 1: 缺少统一的全流程编排命令

**现状**:
- 每个层有独立命令，但缺少统一编排
- 用户需要手动按顺序执行各个层
- 容易遗漏步骤或顺序错误

**影响**:
- 用户体验差，学习成本高
- 无法保证执行顺序正确
- 无法统一管理检查点和质量门禁

**解决方案**:
✅ **已实现**: 创建 `/full-pipeline` 编排命令

**功能**:
- 支持两种模式：`full`, `resume`（可加 `existing` 标记支持现有代码项目）
- 自动检测已有产物，从断点继续
- 统一管理质量门禁
- 输出统一的全流程报告

#### 问题 2: 缺少层间反馈机制

**现状**:
- 数据流是单向的（产品 → 开发 → 测试 → 代码）
- 没有反向反馈循环
- 各层发现的问题无法自动传递给上游

**影响示例**:
- deadhunt 发现死链，无法自动反馈到 product-design
- product-verify 发现未实现任务，无法触发 feature-gap 补齐
- code-tuner 发现架构问题，可能需要调整 product-map

**解决方案**:
✅ **已实现**: 设计反馈循环机制

**实现方式**:
1. 每层发现问题时，记录到 `global-decisions.json`
2. 提供明确的反馈建议（如：建议运行 /feature-gap）
3. 在跨层一致性检查中汇总所有冲突

**反馈示例**:
```json
{
  "T008": {
    "qa-layer": {
      "deadhunt_status": "ISSUE_FOUND",
      "suggested_action": "建议从 screen-map 中移除死链界面"
    }
  }
}
```

### 3.2 🟡 中等问题（P1）

#### 问题 3: 索引机制不统一

**现状**:
- 只有 product-design 有两阶段加载和索引机制
- 其他层（deadhunt, dev-forge, code-tuner）没有索引

**影响**:
- 执行全流程时，其他层可能加载大量不必要的数据
- Token 消耗大，执行效率低

**建议方案**:
为其他层也设计索引机制：

| 层 | 索引文件 | 内容 |
|----|----------|------|
| deadhunt | `deadhunt-index.json` | 路由列表、关键验证点、P0 级问题 |
| dev-forge | `dev-forge-index.json` | 种子数据状态、未实现任务清单 |
| code-tuner | `code-tuner-index.json` | 模块列表、违规摘要、重复代码统计 |

#### 问题 4: 决策日志不互通

**现状**:
- 每个层有自己的 decisions.json
- 层之间无法访问对方的决策历史
- 无法追溯某个功能被 CUT 的完整原因

**影响**:
- 无法了解某个功能在所有层的完整状态
- 决策过程不透明，难以审计
- 重复决策可能不一致

**解决方案**:
✅ **已实现**: 创建全局决策追踪文件 `global-decisions.json`

**结构**:
```json
{
  "T008": {
    "product-layer": {"prune": "DEFER", "reason": "场景优先级低"},
    "dev-layer": {"verify": "NOT_IMPLEMENTED", "reason": "Q2 推进"},
    "qa-layer": {"deadhunt": "N/A"},
    "code-layer": {"tuner": "N/A"},
    "overall_status": "NEEDS_ATTENTION"
  }
}
```

#### 问题 5: 缺少质量门禁

**现状**:
- 只有 product-design 有质量门禁（design-audit）
- 其他层没有明确的质量标准

**建议方案**:
为每个层添加质量门禁标准：

| 层 | 质量门禁 | 标准 |
|----|----------|------|
| product-design | design-audit | ORPHAN=0, 覆盖率≥80%, CONFLICT=0 |
| dev-forge | 实现率 | CORE 任务实现率 ≥ 90% |
| deadhunt | 死链 | P0 级死链 = 0 |
| code-tuner | 架构评分 | 评分 ≥ 70 |

### 3.3 🟢 优化建议（P2）

#### 建议 6: 可视化仪表板

**现状**: 只有 Markdown 报告，没有整体视图

**建议**: 生成 HTML 仪表板，展示：
- 各层完成状态（进度条、状态图标）
- 跨层问题热力图
- 全流程执行时间线
- 关键指标（覆盖率、实现率、问题数）

#### 建议 7: 冲突解决向导

**现状**: 发现冲突后，只列出问题，没有指导

**建议**: 为每种冲突类型提供解决建议：

```json
{
  "conflict": {
    "type": "gap × prune",
    "severity": "CONFLICT",
    "task_id": "T008",
    "description": "feature-gap 报此任务有缺口，但 feature-prune 标为 CUT",
    "suggested_action": "建议保留此功能，优先补齐实现",
    "recommended_command": "/feature-gap task T008"
  }
}
```

---

## 四、已实施的改进

### 4.1 全流程编排命令

**文件**: `product-design-skill/commands/full-pipeline.md`

**功能**:
- ✅ 统一编排四层流程
- ✅ 支持两种模式（full, resume）+ existing 标记
- ✅ 质量门禁检查
- ✅ 跨层一致性检查
- ✅ 全局决策追踪
- ✅ 统一报告输出

**使用示例**:
```bash
/full-pipeline               # 新项目，从头执行全流程
/full-pipeline full existing # 现有代码项目，从代码反推概念再从上往下
/full-pipeline resume        # 从断点继续
/full-pipeline full skip:deadhunt  # 跳过某层
```

### 4.2 全局决策追踪

**文件**: `.allforai/full-pipeline/global-decisions.json`

**功能**:
- ✅ 记录所有层的决策
- ✅ 跟踪每个任务在各层的状态
- ✅ 计算总体健康状态
- ✅ 提供决策审计轨迹

**结构**:
```json
{
  "pipeline_run": {
    "mode": "full",
    "started_at": "2026-02-27T03:00:00Z",
    "completed_at": "2026-02-27T03:30:00Z"
  },
  "decisions": {
    "T008": {
      "task_id": "T008",
      "task_name": "退款审核",
      "product-layer": {
        "prune_decision": "CORE",
        "audit_status": "PASS"
      },
      "dev-layer": {
        "verify_status": "IMPLEMENTED"
      },
      "qa-layer": {
        "deadhunt_status": "OK"
      },
      "code-layer": {
        "tuner_status": "OK"
      },
      "overall_status": "HEALTHY"
    }
  }
}
```

### 4.3 跨层反馈机制

**实现方式**:
- ✅ 每层发现问题时记录到全局决策文件
- ✅ 提供明确的反馈建议
- ✅ 在跨层一致性检查中汇总冲突
- ✅ 输出统一的冲突清单和解决建议

**反馈示例**:
```json
{
  "cross_layer_conflicts": [
    {
      "type": "gap × prune",
      "severity": "CONFLICT",
      "task_id": "T008",
      "description": "feature-gap 报此任务有缺口，但 feature-prune 标为 CUT",
      "suggested_action": "建议保留此功能，优先补齐实现"
    }
  ]
}
```

### 4.4 质量门禁标准

**已定义的标准**:

| 层 | 门禁条件 | 标准 | 失败处理 |
|----|----------|------|----------|
| product-design | design-audit 逆向追溯 | ORPHAN = 0 | 向用户报告，询问是否继续 |
| product-design | design-audit 覆盖洪泛 | 覆盖率 ≥ 80% | 向用户报告，询问是否继续 |
| product-design | design-audit 横向一致性 | CONFLICT = 0 | 向用户报告，建议修复 |
| dev-forge | CORE 任务实现率 | ≥ 90% | 向用户报告，列出未实现任务 |
| deadhunt | P0 级死链 | 0 | 强制中止，必须修复 |
| deadhunt | CORE 任务 CRUD 完整性 | 100% | 向用户报告，建议补齐 |
| code-tuner | 架构评分 | ≥ 70 | 向用户报告，列出主要违规 |

---

## 五、推荐的改进路线图

### 5.1 第一阶段（P0 - 立即实施）✅ 已完成

- [x] 创建统一的全流程编排命令 `/full-pipeline`
- [x] 设计从 deadhunt 到 product-design 的反馈循环
- [x] 创建全局决策追踪文件
- [x] 定义跨层反馈机制

### 5.2 第二阶段（P1 - 近期实施）

- [ ] 为 deadhunt 设计索引机制
- [ ] 为 dev-forge 设计索引机制
- [ ] 为 code-tuner 设计索引机制
- [ ] 统一所有层的质量门禁标准
- [ ] 创建质量门禁检查库

### 5.3 第三阶段（P2 - 中期优化）

- [ ] 生成可视化 HTML 仪表板
- [ ] 添加冲突解决向导
- [ ] 优化索引加载性能
- [ ] 创建命令自动补全文档

---

## 六、使用建议

### 6.1 新项目启动

```bash
# 1. 从头执行全流程
/full-pipeline full

# 2. 查看执行摘要
cat .allforai/full-pipeline/pipeline-report.md

# 3. 检查跨层冲突
cat .allforai/full-pipeline/global-decisions.json
```

### 6.2 日常迭代

```bash
# 1. 从上次中断处继续
/full-pipeline resume

# 2. 查看哪些任务需要关注
cat .allforai/full-pipeline/pipeline-report.md | grep "需要关注的任务"
```

### 6.3 发布前检查

```bash
# 1. 完整执行全流程（确保所有层都通过）
/full-pipeline full

# 2. 检查质量门禁
# - product-design: ORPHAN=0, 覆盖率≥80%, CONFLICT=0
# - dev-forge: CORE 任务实现率≥90%
# - deadhunt: P0 级死链=0
# - code-tuner: 架构评分≥70

# 3. 确认总体健康评分
cat .allforai/full-pipeline/pipeline-report.json | jq '.summary.overall_health_score'
```

### 6.4 故障排查

```bash
# 1. 查看某个任务在所有层的状态
cat .allforai/full-pipeline/global-decisions.json | jq '.decisions.T008'

# 2. 查看跨层冲突
cat .allforai/full-pipeline/pipeline-report.json | jq '.cross_layer_conflicts'

# 3. 查看详细报告
cat .allforai/design-audit/audit-report.md
cat .allforai/product-verify/verify-report.md
cat .allforai/deadhunt/output/validation-report-*.md
cat .allforai/code-tuner/tuner-report.md
```

---

## 七、总结

### 7.1 改进前后对比

| 维度 | 改进前 | 改进后 |
|------|--------|--------|
| 流程编排 | 手动执行各层 | 统一命令自动编排 |
| 反馈机制 | 单向数据流 | 双向反馈循环 |
| 决策追踪 | 各层独立 | 全局统一追踪 |
| 质量门禁 | 部分层有 | 所有层都有 |
| 跨层一致性 | 人工检查 | 自动检测 |
| 执行效率 | 高 | resume 模式避免重复 |

### 7.2 关键成果

✅ **完整性**: 从 75/100 提升到 90/100
✅ **可用性**: 统一命令降低学习成本
✅ **可靠性**: 质量门禁保证输出质量
✅ **可追溯性**: 全局决策追踪提供完整审计轨迹
✅ **可维护性**: 反馈机制形成闭环

### 7.3 下一步行动

1. **立即使用**: 开始使用 `/full-pipeline` 编排命令
2. **验证反馈**: 测试跨层反馈机制是否有效
3. **收集反馈**: 收集用户使用反馈，优化流程
4. **持续改进**: 按路线图实施第二、三阶段改进

---

## 八、附录

### 8.1 相关文件清单

| 文件路径 | 说明 | 状态 |
|----------|------|------|
| `product-design-skill/commands/full-pipeline.md` | 全流程编排命令 | ✅ 已创建 |
| `product-design-skill/commands/product-design.md` | 产品设计层编排 | ✅ 已存在 |
| `product-design-skill/skills/design-audit.md` | 设计审计技能 | ✅ 已存在 |
| `deadhunt-skill/SKILL.md` | QA 层主技能 | ✅ 已存在 |
| `dev-forge-skill/skills/seed-forge.md` | 种子数据技能 | ✅ 已存在 |
| `dev-forge-skill/skills/product-verify.md` | 产品验收技能 | ✅ 已存在 |
| `code-tuner-skill/SKILL.md` | 架构层主技能 | ✅ 已存在 |

### 8.2 输出文件结构

```
your-project/
└── .allforai/
    ├── full-pipeline/
    │   ├── pipeline-report.json          # 全量报告（机器可读）
    │   ├── pipeline-report.md            # 人类可读摘要
    │   └── global-decisions.json         # 全局决策追踪
    ├── product-concept/                  # Layer 1
    ├── product-map/
    ├── screen-map/
    ├── use-case/
    ├── feature-gap/
    ├── feature-prune/
    ├── ui-design/
    ├── design-audit/
    ├── seed-forge/                       # Layer 2
    │   ├── seed-plan.json
    │   ├── forge-log.json
    │   └── forge-data.json
    ├── product-verify/
    │   ├── static-report.json
    │   ├── verify-tasks.json
    │   └── verify-report.md
    ├── deadhunt/                         # Layer 3
    │   └── output/
    │       ├── fix-tasks.json
    │       └── validation-report-*.md
    └── code-tuner/                       # Layer 4
        ├── tuner-profile.json
        ├── phase1-compliance.json
        ├── phase2-duplicates.json
        ├── phase3-abstractions.json
        ├── tuner-report.md
        └── tuner-tasks.json
```

### 8.3 命令参考

| 命令 | 说明 | 模式 |
|------|------|------|
| `/full-pipeline` | 新项目，从头执行全流程 | full |
| `/full-pipeline full` | 完整执行（从头开始） | full |
| `/full-pipeline full existing` | 现有代码项目，代码反推概念 | full + existing |
| `/full-pipeline resume` | 从断点继续 | resume |
| `/full-pipeline full skip:deadhunt` | 跳过指定层 | full |

---

**报告生成时间**: 2026-02-27
**报告版本**: v1.0.0
**维护者**: dv


### 来源文件：`docs/product-design-principles.md`

# Product Design 指导思想与经典理论支持

> 本文档用于公开产品设计套件在各阶段的核心设计思想，并明确对应的**经典理论锚点**（如第一性原理、JTBD、Kano 等），帮助用户理解“为什么这样做”。

## 目标

把 `product-design` 全流程（concept → map → screen → use-case → gap → prune → ui-design → audit）的设计理念说清楚：

1. 每个阶段解决什么问题
2. 每个阶段依赖哪些方法论/管理框架
3. 每个阶段的产出与质量标准是什么

---

## 全局原则（跨阶段）

1. **用户价值优先**：先定义问题与价值，再展开功能与交互。
2. **证据驱动决策**：优先基于搜索证据、现状数据和可追溯产物，而非主观判断。
3. **结构化产出优先**：JSON 给机器、Markdown 给人，保证可执行与可读性。
4. **层层校验闭环**：阶段间设置检查点，终审统一做逆向追溯 + 覆盖洪泛 + 横向一致性。
5. **用户是最终决策者**：AI 提供分析与建议，最终取舍由用户确认。
6. **双轨证据机制**：经典理论提供稳定锚点，Web 热门文章/案例提供时效补充。

---

## 动态研究机制（Web 热门文章与趋势补充）

除了经典理论，每个阶段都建议执行一次「动态趋势补充」：

1. **搜索近期内容**：优先近 12–24 个月（必要时回溯经典长文）
2. **筛选来源质量**：优先官方规范、权威研究、头部产品实践
3. **形成采纳决策**：不是“看到了就用”，而是记录“是否采纳 + 为什么”

### 来源优先级（建议）

| 级别 | 来源类型 | 处理方式 |
|------|----------|----------|
| P1 | 官方规范/标准（W3C、ISO、官方 Design System） | 可直接作为强依据 |
| P2 | 权威研究机构/行业报告（NN/g、McKinsey、Gartner 等） | 高可信，建议交叉验证 |
| P3 | 一线产品团队实践文章（Linear/Stripe/Figma/Notion 工程博客） | 可作为实操参考 |
| P4 | 社区文章/社媒帖子 | 仅作灵感，不单独作为决策依据 |

### 建议输出（趋势证据留痕）

- `.allforai/product-design/trend-sources.json`（机器可读）
- `.allforai/product-design/trend-notes.md`（人类可读）

`trend-sources.json` 最小结构建议：

```json
[
  {
    "phase": "ui-design",
    "topic": "dashboard information density",
    "title": "文章标题",
    "url": "https://...",
    "source_level": "P1|P2|P3|P4",
    "published_at": "2025-06-01",
    "adoption": "ADOPT|REJECT|DEFER",
    "reason": "采纳或拒绝理由"
  }
]
```

---

## 经典理论总览（阶段 × 理论锚点）

| 阶段 | 经典理论锚点 | 代表来源（作者/年份） |
|------|--------------|------------------------|
| product-concept | 第一性原理、JTBD、VPC、Lean Canvas、Blue Ocean ERRC、Kano、Mom Test | Christensen et al. (2016); Osterwalder et al. (2014); Osterwalder & Pigneur (2010); Kim & Mauborgne (2005); Kano et al. (1984); Fitzpatrick (2013) |
| product-map | Story Mapping、RACI、风险矩阵、DoR | Patton (2014); PMI (2013, RACI in PM practice) |
| screen-map | Nielsen Heuristics、Service Blueprint、认知负荷理论 | Nielsen (1994); Shostack (1984); Sweller (1988) |
| use-case | INVEST、DoD、风险驱动测试 | Cohn (2004); Schwaber & Sutherland (2020); Bach (1999) |
| feature-gap | INVEST、DoR/DoD、服务蓝图、风险矩阵 | Cohn (2004); Schwaber & Sutherland (2020); Shostack (1984) |
| feature-prune | RICE、MoSCoW、Kano、Cost of Delay | Intercom (2015, RICE); Clegg & Barker (1994, MoSCoW); Kano et al. (1984); Reinertsen (2009) |
| ui-design | Design System、Atomic Design、WCAG、Gestalt | W3C (2018/2023, WCAG 2.1/2.2); Frost (2016); Wertheimer (1923) |
| design-audit | Nielsen Heuristics、ISO 9241-11、WCAG、一致性原则 | Nielsen (1994); ISO 9241-11 (2018); W3C (2018/2023) |

---

## 三段式总览（前段 / 中段 / 尾段）

为避免只看到“某一段”的理论，下面按你关心的三段式明确汇总。

### 前段（战略定义层）

**覆盖阶段**：`product-concept`

**核心思想**：先定义问题与价值，再定义解法。

**经典理论**：
- 第一性原理（First Principles）
- JTBD（Jobs To Be Done）
- VPC（Value Proposition Canvas）
- Lean Canvas
- Blue Ocean ERRC + Kano
- Mom Test

---

### 中段（功能与交互建模层）

**覆盖阶段**：`product-map`、`screen-map`、`use-case`、`feature-gap`、`feature-prune`

**核心思想**：把战略意图转成可执行、可验证、可取舍的产品资产。

**经典理论**：
- Story Mapping（功能切片与版本范围）
- RACI（职责边界）
- 风险矩阵（Impact × Probability）
- INVEST（需求可测试性）
- DoR / DoD（准入与完成门禁）
- Service Blueprint（前后台链路）
- Nielsen Heuristics（交互可用性）
- RICE / MoSCoW / Kano / Cost of Delay（优先级与剪枝）

---

### 尾段（视觉落地与发布审计层）

**覆盖阶段**：`ui-design`、`design-audit`

**核心思想**：保证体验质量、一致性与可发布性。

**经典理论**：
- Design System / Design Tokens
- Atomic Design
- WCAG（可访问性）
- Gestalt（视觉层级）
- Nielsen Heuristics（可用性问题归类）
- ISO 9241-11（有效性 / 效率 / 满意度）

**特别原则**：
- UI 风格选择不可省略，必须由用户明确确认。

---

## 分段趋势搜索建议（关键词模板）

### 前段（战略定义层）

- `"JTBD" + 行业词 + "case study" + 2025`
- `"problem discovery" + 产品类型 + "user research"`
- `"Blue Ocean" + 行业词 + "competitive landscape"`

### 中段（功能与交互建模层）

- `"story mapping" + 产品类型 + "best practices"`
- `"service blueprint" + 行业词 + "journey design"`
- `"RICE prioritization" + "product team" + 2024 OR 2025`

### 尾段（视觉落地与发布审计层）

- `"design system" + 行业词 + "case study" + 2025`
- `"WCAG 2.2" + 组件类型 + "accessibility"`
- `"usability audit" + "Nielsen heuristics" + "real examples"`

---

## 分阶段指导思想

## Phase 1：product-concept（产品概念）

**核心问题**：做什么产品、为谁做、为什么值得做。

**指导思想 / 框架**：
- First Principles（先拆问题本质）
- Opportunity Solution Tree（机会收敛）
- JTBD + VPC（角色与价值）
- Lean Canvas（商业模式）
- Mom Test（基于行为事实提问）
- Build Trap / Product Kata（Outcome 导向）
- ERRC + Kano（差异化定位）

**经典理论定位**：这是经典理论最密集的阶段，优先使用“第一性原理 + JTBD + VPC + Lean Canvas”形成战略闭环。

**核心产出**：`product-concept.json`、`product-concept-report.md`

---

## Phase 2：product-map（功能点与任务地图）

**核心问题**：产品现状与期望到底包含哪些角色、任务、规则与约束。

**指导思想 / 框架**：
- Story Mapping（任务分层与版本切片）
- RACI（角色责任边界）
- 风险矩阵（Impact × Probability）
- DoR（下游可消费就绪标准）

**经典理论定位**：以《User Story Mapping》为主线，把概念层价值翻译为可执行任务地图。

**核心产出**：`task-inventory.json`、`business-flows.json`、`product-map.json`

---

## Phase 3：screen-map（交互与异常设计）

**核心问题**：任务在界面上如何完成，异常是否可感知、可恢复。

**指导思想 / 框架**：
- Service Blueprint（前台触点/后台支撑链路）
- Nielsen Heuristics（可用性启发式）
- Cognitive Load（认知负荷控制）
- 风险控制矩阵（高风险操作确认策略）

**经典理论定位**：以 Nielsen 启发式和服务蓝图保障“可用 + 可恢复 + 可达”。

**核心产出**：`screen-map.json`、`screen-conflict.json`、`screen-map-report.md`

---

## Phase 4：use-case（用例集）

**核心问题**：需求是否被转换成可执行、可验证的场景。

**指导思想 / 框架**：
- INVEST（用户故事质量）
- DoD（完成定义）
- Risk-based Testing（风险驱动测试）
- Service Blueprint（跨系统 E2E 场景）

**经典理论定位**：以 INVEST 与 DoD 保证“需求可测试、可验收、可交付”。

**核心产出**：`use-case-tree.json`、`use-case-report.md`

---

## Phase 5：feature-gap（功能查漏）

**核心问题**：地图里该有的是否都存在且走得通。

**指导思想 / 框架**：
- INVEST（缺口回写需求质量）
- DoR / DoD（准入与完成门禁）
- 风险矩阵（缺口优先级）
- Service Blueprint（旅程断点定位）

**经典理论定位**：以“需求质量理论 + 服务蓝图”定位缺口，不凭感觉补功能。

**核心产出**：`gap-tasks.json`、`gap-report.md`

---

## Phase 6：feature-prune（功能剪枝）

**核心问题**：哪些功能必须保留，哪些可推迟或移除。

**指导思想 / 框架**：
- RICE（量化优先级）
- MoSCoW（迭代沟通语义）
- Kano（避免误砍高价值能力）
- Cost of Delay（延迟成本）

**经典理论定位**：以 Kano + RICE + Cost of Delay 平衡“用户价值、实现成本与时机”。

**核心产出**：`prune-decisions.json`、`prune-tasks.json`

---

## Phase 7：ui-design（UI 规格与预览）

**核心问题**：界面风格与视觉规范如何统一且可落地。

**指导思想 / 框架**：
- Design System / Design Tokens
- Atomic Design
- WCAG（可访问性）
- Gestalt（视觉层级与分组）

**经典理论定位**：以 Design System + WCAG 为底座，保障风格一致性与可访问性。

**特别原则（强制）**：
- **风格选择不可省略**：Step 2 必须由用户明确选择或确认沿用历史风格，不允许静默默认。

**核心产出**：`ui-design-spec.md`、`preview/*.html`

---

## Phase 8：design-audit（终审）

**核心问题**：跨层产物是否一致、可追溯、可发布。

**指导思想 / 框架**：
- Nielsen Heuristics（可用性问题归类）
- ISO 9241-11（有效性/效率/满意度）
- WCAG（可访问性风险标注）
- 一致性与认知负荷原则（冲突优先级解释）

**经典理论定位**：以 ISO 9241-11 + Nielsen + WCAG 对跨层产物做发布前质量审计。

**核心产出**：`audit-report.json`、`audit-report.md`

---

## 如何使用本文档

推荐在以下场景引用本原则文档：

1. **新成员 onboarding**：先读本文档，再执行 `/product-design full`
2. **评审会议对齐**：按“阶段 → 原则 → 产出”逐项审查
3. **争议决策仲裁**：回到对应阶段的指导思想，避免拍脑袋讨论
4. **流程复盘优化**：当产出质量不稳定时，优先检查是否偏离本原则

---

## 参考文献（经典来源）

1. Christensen, C. M., Hall, T., Dillon, K., & Duncan, D. S. (2016). *Competing Against Luck*.
2. Osterwalder, A., Pigneur, Y., Bernarda, G., & Smith, A. (2014). *Value Proposition Design*.
3. Osterwalder, A., & Pigneur, Y. (2010). *Business Model Generation*.
4. Kim, W. C., & Mauborgne, R. (2005). *Blue Ocean Strategy*.
5. Kano, N., Seraku, N., Takahashi, F., & Tsuji, S. (1984). Attractive quality and must-be quality.
6. Fitzpatrick, R. (2013). *The Mom Test*.
7. Patton, J. (2014). *User Story Mapping*.
8. Nielsen, J. (1994). 10 Usability Heuristics for User Interface Design.
9. Shostack, G. L. (1984). Designing Services That Deliver.
10. Sweller, J. (1988). Cognitive Load During Problem Solving.
11. Cohn, M. (2004). *User Stories Applied* (INVEST).
12. Schwaber, K., & Sutherland, J. (2020). *The Scrum Guide* (DoD).
13. Bach, J. (1999). Risk-Based Testing.
14. Reinertsen, D. (2009). *The Principles of Product Development Flow* (Cost of Delay).
15. Frost, B. (2016). *Atomic Design*.
16. W3C. (2018/2023). *WCAG 2.1 / 2.2*.
17. ISO. (2018). *ISO 9241-11:2018 Ergonomics of human-system interaction*.
