# product-design — 产品设计套件

**版本：v4.0.0**

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
| 梳理界面与异常状态 | `/experience-map` |
| 生成可执行用例（机器+人类双格式） | `/use-case` |
| 做查漏决策 | `/feature-gap` |
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
    ├── experience-map（必须，建体验地图）
    │       ↓ 输出 .allforai/experience-map/experience-map.json
    │
    ├── use-case（可选，生成用例集）
    │       ↓ 输出 .allforai/use-case/use-case-tree.json（机器）+ use-case-report.md（人类）
    │
    ├── 功能查漏   — 地图说有的，现在有没有？（Step 2/3 需要 experience-map）
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

### experience-map — 体验地图

> 以产品地图为基础，梳理界面、按钮和异常状态，输出界面交互地图。

- **界面**：每个任务对应哪些页面，每个页面的核心目的是什么
- **按钮**：每个页面上的操作，CRUD 分类、操作频次、点击层级、是否需要二次确认
- **异常状态**：空状态、加载状态、错误状态、权限不足状态
- **异常流程**：每个操作的失败反馈（on_failure）、前端校验（validation_rules）、异常响应（exception_flows）
- **帕累托分析**：自动找出 20% 高频操作，检测高频操作是否被埋深
- **界面级冲突**：冗余入口、高风险无确认、SILENT_FAILURE、UNHANDLED_EXCEPTION

### use-case — 用例集

> 以功能地图和体验地图为输入，推导完整用例，双格式输出。

- **树结构**：角色 → 功能区 → 任务 → 用例（4 层）
- **JSON 机器版**：完整 Given/When/Then，含 screen_ref、逐条可验证的 then，供 AI agent 执行
- **Markdown 人类版**：每条用例一行（ID + 标题 + 类型），不重复字段细节

### feature-gap — 功能查漏

> 产品地图说应该有的，现在有没有？用户路径走得通吗？

### ui-design — UI 设计规格

> 从产品地图 + 体验地图推导高层 UI 设计规格，结合风格选择和设计原则，输出设计规格文档 + 按角色拆分的 HTML 预览。

### design-audit — 设计审计

> 跨层校验产品设计全链路一致性：逆向追溯、覆盖洪泛、横向一致性。

- **逆向追溯**：下游产物（experience-map、use-case、gap）引用的 task_id 是否在 task-inventory 中存在
- **覆盖洪泛**：每个 task 是否被下游层完整消费（有 screen、有用例、有 gap 检查）
- **横向一致性**：高频任务点击深度过深 = 警告

---

## 定位

```
product-design（产品层）
├── product-concept 想做什么产品？                       搜索+选择题引导
├── product-map     产品是什么？谁在用？做什么？          代码读现状 + PM 补业务视角
├── experience-map  在哪做？怎么做？出错怎么办？          以 task-inventory 为输入（必须）
├── use-case        推导完整用例，双格式输出               基于 product-map + experience-map
├── feature-gap     地图说有的，有没有？                  基于 product-map + experience-map
├── ui-design       高层 UI 设计规格                     基于 product-map + experience-map
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

### 第二步（可选）：建立体验地图

```bash
/experience-map              # 完整流程（界面梳理+异常状态+冲突检测）
/experience-map quick        # 只梳理界面和按钮，跳过冲突检测
/experience-map scope 退款管理  # 只梳理指定模块的界面
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
    ├── experience-map/
    │   ├── experience-map.json         # 体验地图
    │   ├── screen-conflict.json        # 界面级冲突
    │   ├── experience-map-report.md    # 可读报告
    │   └── experience-map-decisions.json # 用户决策日志
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
    └── design-audit/
        ├── audit-report.json           # 全量校验结果
        └── audit-report.md             # 可读摘要
```

---

## 核心原则

1. **product-map 是基础** — 其他技能都以产品地图为输入，先建图再分析
2. **experience-map 是必须层** — 与 product-map 共同构成完整产品地图，feature-gap Step 2/3、use-case validation、ui-design 均依赖其数据
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

## 深入文档

| 文档 | 说明 |
|------|------|
| [快速开始指南](docs/full-pipeline-quickstart.md) | Full Pipeline 四层联动操作指南 |
| [流程分析](docs/pipeline-analysis.md) | 各阶段输入输出依赖与编排逻辑 |
| [经典设计理论](docs/product-design-principles.md) | 9 条设计思想的理论来源与落地 |
| [信息保真方法论](docs/information-fidelity.md) | 4D + 6V + XV 三支柱详解 |
| [防御性规范](docs/defensive-patterns.md) | 7 个通用防御模式 |
| [技能通用增强协议](docs/skill-commons.md) | WebSearch + 4D+6V + XV 共享框架 |

