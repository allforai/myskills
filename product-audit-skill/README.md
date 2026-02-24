# product-audit — 产品审计套件

**版本：v2.4.0**

Claude Code 插件，以产品地图为基础，系统化地查漏、剪枝、造数据。

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
    └── seed-forge — 按地图生成真实感种子数据
```

---

## 包含的技能

### product-map — 产品地图

> 先搞清楚这个产品是什么，才能做其他分析。

从代码读现状，用产品语言呈现，让 PM 确认并补充业务视角，形成「现状 + 期望」的完整产品地图。

- **角色**：识别所有用户角色，明确权限边界和 KPI
- **任务**：按角色展开，每个任务包含触发条件、频次、风险、SLA、主流程、规则、异常列表、验收标准
- **冲突检测**：发现任务级业务逻辑矛盾或 CRUD 缺口
- **约束**：合规要求、不可逆操作、审批分级等业务规则

输出产品地图供所有其他技能直接加载，无需重复分析。

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
- **正常流**：从 main_flow 和 outputs 推导，每任务 1 条
- **异常流**：从 exceptions 推导，每条异常 1 条用例
- **边界用例**：从 rules 中提取边界语义（≥ / ≤ / 幂等 / 超时）
- **JSON 机器版**：完整 Given/When/Then，含 screen_ref、逐条可验证的 then，供 AI agent 执行
- **Markdown 人类版**：每条用例一行（ID + 标题 + 类型），不重复字段细节

### feature-gap — 功能查漏

> 产品地图说应该有的，现在有没有？用户路径走得通吗？

以 `product-map` 为基准，检查每个任务、界面、按钮的完整性。

- **任务完整性**：CRUD 是否齐全，exceptions 和 acceptance_criteria 是否填写
- **界面完整性**（需 screen-map）：主操作是否存在，SILENT_FAILURE 和 UNHANDLED_EXCEPTION 检测
- **用户旅程**（需 screen-map）：按角色走完整路径，四节点评分（入口→主操作→反馈→结果可见）
- 缺口任务按频次排优先级，高频任务的缺口排在前面

### feature-prune — 功能剪枝

> 产品地图里有的，哪些该留、哪些推迟、哪些砍掉？

以 `product-map` 的频次数据为基础，评估每个功能的去留。

- **频次过滤**：低频功能自动进入剪枝候选，高频功能受保护
- **场景对齐**（需 screen-map）：不服务于核心场景的功能，列为 CUT 候选
- **竞品参考**：同类产品同阶段的功能范围，辅助判断
- 分类：`CORE`（必须保留）/ `DEFER`（推迟）/ `CUT`（移除），最终决定权归用户

### seed-forge — 种子数据锻造

> 按产品地图，生成有业务逻辑、有人物关系、有时间分布的真实感种子数据。

- **角色驱动**：按 `role-profiles` 创建各角色的测试用户账号
- **频次决定数量**：高频任务多生成数据，低频任务少生成，符合二八分布
- **场景决定关联**：按场景链路生成完整数据（父→子→关联），时间戳连贯，不随机拼凑
- **约束决定规则**：金额上限、审批链、不可逆状态等业务约束在数据中强制体现
- 竞品图片优先，Unsplash/Pexels 兜底；通过 API 灌入，直连数据库清理

---

## 定位

```
product-audit（产品层）
├── product-map     产品是什么？谁在用？做什么？    代码读现状 + PM 补业务视角
├── screen-map      在哪做？怎么做？出错怎么办？    以 task-inventory 为输入（可选）
├── 功能查漏        地图说有的，有没有？             基于 product-map + screen-map
├── 功能剪枝        地图里有的，该不该留？           基于 product-map + screen-map
└── seed-forge      真实感种子数据                  基于 product-map + API 调用

deadhunt（代码层）  链接通不通？CRUD 全不全？        需要 Playwright
code-tuner（架构层）代码好不好？重复多不多？         纯静态分析
```

---

## 安装

```bash
claude plugin add /path/to/product-audit-skill
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

### 第三步：按需选择

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

# 种子数据 — 造数据
/seed-forge               # 完整流程（映射→方案→风格→采集→灌入）
/seed-forge plan          # 只设计方案，不灌入
/seed-forge fill          # 加载已有方案，直接采集+灌入
/seed-forge clean         # 清理已灌入的种子数据
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

---

## 核心原则

1. **product-map 是基础** — 其他技能都以产品地图为输入，先建图再分析
2. **screen-map 是可选增强层** — 界面分析独立运行，feature-gap Step 2/3 和 feature-prune Step 2 需要它
3. **频次驱动一切** — 高频操作受保护不剪枝，缺口按频次排优先级，种子数据按频次分配数量
4. **每步用户确认** — 所有分类和决策都需要用户确认，用户是权威
5. **只标不改** — 发现问题只报告，不执行任何代码修改或删除
6. **业务语言呈现** — 输出全程使用业务语言，不出现接口地址、组件名等工程术语
7. **异常覆盖是质量指标** — 每个功能点的异常情况和验收标准是产品完整性的核心体现
8. **JSON 给机器，Markdown 给人** — JSON 完整字段无省略，Markdown 摘要级突出结论，细节不重复

---

## License

MIT
