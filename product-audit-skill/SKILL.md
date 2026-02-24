---
name: product-audit
description: >
  Product audit suite with six skills: product-map (产品地图), screen-map (界面地图), use-case (用例集),
  feature-gap (功能查漏), feature-prune (功能剪枝), seed-forge (种子数据锻造).
  Run product-map first to build the foundation, then optionally run screen-map,
  then use other skills as needed.
version: "2.4.0"
---

# Product Audit — 产品审计套件

> 以产品地图为基础，系统化地查漏、剪枝、造数据。

## 包含的技能

### 1. product-map — 产品地图

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/product-map.md`

先搞清楚这个产品是什么，才能做其他分析。从代码读现状，用产品语言呈现。

- 识别所有用户角色，明确权限边界和 KPI
- 按角色展开任务（频次、风险、SLA、异常列表、验收标准）
- 冲突检测：发现任务级业务逻辑矛盾或 CRUD 缺口

```
/product-map              # 完整流程
/product-map quick        # 跳过冲突检测和约束识别
/product-map refresh      # 忽略缓存，重新分析
/product-map scope 退款管理  # 只梳理指定模块
```

### 2. screen-map — 界面与异常状态地图

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/screen-map.md`

以产品地图为基础，梳理每个任务对应的界面、按钮、导航路径，并映射异常状态（错误提示、空状态、表单校验、操作失败流程），输出界面交互地图。

- 梳理每个任务对应的界面和操作按钮（CRUD 分类、频次、层级）
- 帕累托分析：找出高频操作，检测是否被埋深
- 异常状态映射：每个界面的空状态、错误状态、权限不足状态
- 按钮级异常流程：每个操作的 on_failure、validation_rules、exception_flows
- 界面级冲突：冗余入口、高风险无确认、异常覆盖缺口

```
/screen-map              # 完整流程（界面梳理+冲突检测）
/screen-map quick        # 只梳理界面和按钮，跳过冲突检测
/screen-map scope 退款管理  # 只梳理指定模块的界面
```

### 3. use-case — 用例集

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/use-case.md`

以功能地图和界面地图为输入，推导完整用例，双格式输出。

- 四层树结构：角色 → 功能区 → 任务 → 用例
- 每任务生成：1 条正常流 + N 条异常流 + M 条边界用例
- JSON 机器版：完整字段，可供 AI agent 和自动化测试执行
- Markdown 人类版：每条用例一行（ID + 标题 + 类型），供 PM / QA 快速浏览

```
/use-case              # 完整流程
/use-case quick        # 只生成正常流，跳过异常流
/use-case scope 退款管理  # 只生成指定功能区的用例
```

### 4. feature-gap — 功能查漏

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-gap.md`

产品地图说应该有的，现在有没有？用户路径走得通吗？

- 任务完整性：CRUD 是否齐全，exceptions 和 acceptance_criteria 是否已填写
- 界面完整性（需 screen-map）：主操作是否存在，SILENT_FAILURE 和 UNHANDLED_EXCEPTION 检测
- 用户旅程（需 screen-map）：按角色走完整路径，四节点评分
- 缺口任务按频次排优先级

```
/feature-gap              # 完整查漏（任务+界面+旅程）
/feature-gap quick        # 只查任务和界面，跳过旅程
/feature-gap journey      # 只验证用户旅程
/feature-gap role 客服专员  # 只查指定角色
```

### 5. feature-prune — 功能剪枝

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-prune.md`

产品地图里有的，哪些该留、哪些推迟、哪些砍掉？

- 频次过滤：低频功能进入剪枝候选，高频功能受保护
- 场景对齐（需 screen-map）：不服务核心场景的功能列为 CUT 候选
- 竞品参考：同类产品同阶段的功能范围
- 分类：CORE / DEFER / CUT，最终决定权归用户

```
/feature-prune            # 完整剪枝（频次+场景+竞品）
/feature-prune quick      # 只看频次，跳过竞品
/feature-prune scope 用户管理  # 只剪枝指定模块
```

### 6. seed-forge — 种子数据锻造

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/seed-forge.md`

按产品地图，生成有业务逻辑、有人物关系、有时间分布的真实感种子数据。

- 角色驱动：按 role-profiles 创建各角色测试用户账号
- 频次决定数量：高频任务多生成，低频少生成（80/20 分布）
- 场景决定关联：按场景链路生成完整数据，时间戳连贯
- 约束决定规则：业务约束在数据中强制体现

```
/seed-forge               # 完整流程（映射→方案→风格→采集→灌入）
/seed-forge plan          # 只设计方案，不灌入
/seed-forge fill          # 加载已有方案，直接采集+灌入
/seed-forge clean         # 清理已灌入的种子数据
```

## 定位

```
product-audit（产品层）
├── product-map     产品是什么？谁在用？做什么？有何约束？   代码读现状 + PM 补业务视角
├── screen-map      在哪做？怎么做？出错怎么办？             以 task-inventory 为输入（可选）
├── use-case    推导完整用例，双格式输出（JSON 机器版 + Markdown 人类版）   基于 product-map + screen-map（可选）
├── feature-gap     地图说有的，有没有？旅程走得通吗？        基于 product-map + screen-map
├── feature-prune   地图里有的，该不该留？                   基于 product-map + screen-map
└── seed-forge      真实感种子数据                          基于 product-map + API 调用

deadhunt（代码层）  链接通不通？CRUD 全不全？                需要 Playwright
code-tuner（架构层）代码好不好？重复多不多？                 纯静态分析
```

## 推荐工作流

```
product-map（必须先跑）
    ↓ 输出 .allforai/product-map/product-map.json + task-inventory.json
    │
    ├── screen-map（可选，推荐）
    │       ↓ 输出 .allforai/screen-map/screen-map.json
    │
    ├── use-case（可选，需 product-map；有 screen-map 时更完整）
    │       ↓ 输出 .allforai/use-case/use-case-tree.json + use-case-report.md
    │
    ├── feature-gap（Step 1 基于 product-map，Step 2/3 需要 screen-map）
    ├── feature-prune（Step 1 基于 product-map，Step 2 需要 screen-map）
    └── seed-forge（只需 product-map）
```

## 文件结构

```
your-project/
└── .allforai/
    ├── product-map/
    │   ├── role-profiles.json          # 角色画像（权限边界、KPI）
    │   ├── task-inventory.json         # 任务清单（频次、风险、SLA、异常、验收标准）
    │   ├── business-flows.json         # 业务流（跨角色/跨系统链路）
    │   ├── business-flows-report.md    # 业务流摘要（人类可读）
    │   ├── business-flows-visual.svg   # 业务流泳道图（可视化）
    │   ├── conflict-report.json        # 任务级冲突与 CRUD 缺口
    │   ├── constraints.json            # 业务约束清单
    │   ├── product-map.json            # 汇总文件（供其他技能加载）
    │   ├── product-map-report.md       # 可读报告
    │   ├── product-map-visual.svg      # 角色-任务树（可视化）
    │   ├── competitor-profile.json     # 竞品功能概况（Step 0 草稿→Step 7 补全）
    │   ├── validation-report.json      # 三合一校验结果（机器可读）
    │   ├── validation-report.md        # 校验摘要（人类可读）
    │   └── product-map-decisions.json  # 用户决策日志
    ├── screen-map/
    │   ├── screen-map.json             # 界面地图（含 states、on_failure、exception_flows）
    │   ├── screen-conflict.json        # 界面级冲突 + 异常覆盖缺口
    │   ├── screen-map-report.md        # 可读报告
    │   └── screen-map-decisions.json   # 用户决策日志
    ├── use-case/
    │   ├── use-case-tree.json          # 机器可读：完整 4 层 JSON 树（Given/When/Then 全量）
    │   ├── use-case-report.md          # 人类可读：摘要级 Markdown（每条用例一行）
    │   └── use-case-decisions.json     # 用户决策日志（DEFERRED 记录）
    ├── feature-gap/
    │   ├── task-gaps.json              # 任务完整性检查结果
    │   ├── screen-gaps.json            # 界面与按钮完整性检查结果（需 screen-map）
    │   ├── journey-gaps.json           # 用户旅程验证结果（X/4 评分，需 screen-map）
    │   ├── gap-tasks.json              # 缺口任务清单（按频次排优先级）
    │   ├── flow-gaps.json              # 业务流链路完整性检查结果
    │   ├── gap-report.md               # 可读报告
    │   └── gap-decisions.json          # 用户确认记录
    ├── feature-prune/
    │   ├── frequency-tier.json         # 频次分层结果
    │   ├── scenario-alignment.json     # 场景对齐结果（需 screen-map）
    │   ├── competitive-ref.json        # 竞品参考数据
    │   ├── prune-decisions.json        # 用户分类决策日志
    │   ├── prune-tasks.json            # 剪枝任务清单（DEFER/CUT）
    │   └── prune-report.md             # 可读报告
    └── seed-forge/
        ├── model-mapping.json          # 代码实体 ↔ product-map 映射
        ├── api-gaps.json               # API 缺口报告
        ├── seed-plan.json              # 种子方案（用户/数量/链路/约束）
        ├── style-profile.json          # 行业风格
        ├── assets-manifest.json        # 素材清单
        ├── assets/                     # 下载的图片
        ├── forge-log.json              # 灌入日志
        └── forge-data.json             # 已创建数据清单
```

## 输出规范（全套件铁律）

**JSON 给机器，Markdown 给人类。**

| 文件类型 | 受众 | 密度 |
|----------|------|------|
| `*.json` | AI agent、自动化测试 | 完整字段，逐条可执行，无省略 |
| `*-report.md` | PM、QA、开发 | 摘要级，突出问题和结论，不列每条字段 |

所有技能的 Markdown 报告只呈现「有什么问题、结论是什么」，不重复 JSON 中已有的字段细节。完整数据始终在 JSON 文件中。
