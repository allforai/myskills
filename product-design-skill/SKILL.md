---
name: product-design
description: >
  Product design suite with sixteen skills: product-concept (产品概念), concept-review (概念审核), market-validate (市场验证),
  product-map (产品地图), map-review (地图审核), journey-emotion (情绪旅程),
  experience-map (体验地图, 支持 --variants), interaction-gate (交互质量门禁),
  design-pattern (设计模式), behavioral-standards (行为规范),
  wireframe-review (线框交互审核), use-case (用例集),
  feature-gap (功能查漏), feature-prune (功能剪枝), ui-design (UI设计规格, 支持 --variants), design-audit (设计审计).
  Pipeline: concept → concept-review → map → map-review → experience-map → wireframe-review (structure lock) →
  [use-case ∥ gap ∥ ui-design] → ui-review (visual) → audit.
  Use /product-design full to run the full pipeline with checkpoints.
version: "4.5.1"
---

# Product Design — 产品设计套件

> 以产品地图为基础，系统化地定义、查漏、剪枝、审计。

## 包含的技能

### 1. product-concept — 产品概念发现

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/product-concept.md`

从问题出发，搜索+选择题引导，帮你发现心中的产品。

```
/product-concept          # 完整流程
/product-concept reverse  # 从已有产品反推概念
```

### 1.5. concept-review — 概念脑图审核

> 详见 `${CLAUDE_PLUGIN_ROOT}/commands/concept-review.md`

concept 完成后，启动交互式脑图审核服务器，以树形结构展示产品概念（定位、角色、商业模式、机制、创新概念），用户可在节点上标注评论、标记通过或需修改。概念审核是必须环节。

```
/concept-review          # 启动脑图审核服务器（localhost:18900）
/concept-review process  # 读取反馈，汇总修改建议
```

### 1.6. market-validate — 市场验证

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/market-validate.md`

在概念确认后、产品地图之前，用 Brave 搜索 + 跨模型验证来验证产品概念的市场可行性。

- 市场趋势与竞品格局分析（至少 3 个直接竞品 + 2 个替代方案）
- 角色与需求验证（每个角色的 viability_score）
- 商业模式压力测试（定价基准 + 单位经济可行性）
- 每条结论附带来源 URL

```
/market-validate          # 完整流程（需先完成 /product-concept）
```

### 2. product-map — 产品地图

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

### 2.5. map-review — 产品地图脑图审核

> 详见 `${CLAUDE_PLUGIN_ROOT}/commands/map-review.md`

product-map 完成后，启动交互式脑图审核服务器，以树形结构展示角色列表、核心/基本任务（频次+风险标签）、业务流（步骤+角色流转+GAP 标记），用户可在节点上标注评论。地图审核是必须环节。

```
/map-review              # 启动脑图审核服务器（localhost:18901）
/map-review process      # 读取反馈，汇总修改建议
```

### 3. journey-emotion — 情绪旅程地图

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/journey-emotion.md`

以产品地图为基础，绘制每个角色的端到端情绪旅程，标注触点情绪（期待、满意、焦虑、沮丧），识别情绪低谷和高峰时刻，输出情绪旅程地图。

```
/journey-emotion          # 完整流程
```

### 4. experience-map — 体验地图

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/experience-map.md`

以产品地图为基础，梳理每个任务对应的界面、按钮、导航路径，并映射异常状态（错误提示、空状态、表单校验、操作失败流程），输出体验地图。

- 梳理每个任务对应的界面和操作按钮（CRUD 分类、频次、层级）
- 帕累托分析：找出高频操作，检测是否被埋深
- 异常状态映射：每个界面的空状态、错误状态、权限不足状态
- 按钮级异常流程：每个操作的 on_failure、validation_rules、exception_flows
- 界面级冲突：冗余入口、高风险无确认、异常覆盖缺口

```
/experience-map              # 完整流程（界面梳理+冲突检测）
/experience-map quick        # 只梳理界面和按钮，跳过冲突检测
/experience-map scope 退款管理  # 只梳理指定模块的界面
```

### 4.5. interaction-gate — 交互质量门禁

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/interaction-gate.md`

在体验地图完成后、进入下游技能前，执行交互质量门禁检查，验证界面交互的一致性、可用性和无障碍合规，输出门禁报告。

```
/interaction-gate          # 完整流程
```

### 4b. design-pattern — 设计模式抽象

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/design-pattern.md`

扫描 task-inventory + experience-map，识别 8 类功能模式（CRUD台、列表+详情、审批流等），输出 pattern-catalog.json。

### 4c. behavioral-standards — 产品行为规范

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/behavioral-standards.md`

扫描 experience-map 检测跨界面行为不一致（删除确认、空状态、加载模式、错误展示等），提出产品级标准，输出 behavioral-standards.json。

```
/behavioral-standards    # 完整流程
```

### 4d. wireframe-review — 线框交互审核

> 详见 `${CLAUDE_PLUGIN_ROOT}/commands/wireframe-review.md`

在 experience-map + interaction-gate 完成后、视觉设计之前，启动低保真线框审核服务器。验证 IA 结构、屏幕流转和功能完整性。反馈按类别路由到上游（product-map / experience-map / concept），审核通过后结构锁定。

```
/wireframe-review          # 启动线框审核服务器（localhost:18902）
/wireframe-review process  # 读取反馈，汇总修复建议
```

### 5. use-case — 用例集

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/use-case.md`

以功能地图和体验地图为输入，推导完整用例，双格式输出。

- 四层树结构：角色 → 功能区 → 任务 → 用例
- 每任务生成：1 条正常流 + N 条异常流 + M 条边界用例
- JSON 机器版：完整字段，可供 AI agent 和自动化测试执行
- Markdown 人类版：每条用例一行（ID + 标题 + 类型），供 PM / QA 快速浏览

```
/use-case              # 完整流程
/use-case quick        # 只生成正常流，跳过异常流
/use-case scope 退款管理  # 只生成指定功能区的用例
```

### 6. feature-gap — 功能查漏

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-gap.md`

产品地图说应该有的，现在有没有？用户路径走得通吗？

- 任务完整性：CRUD 是否齐全，exceptions 和 acceptance_criteria 是否已填写
- 界面完整性（需 experience-map）：主操作是否存在，SILENT_FAILURE 和 UNHANDLED_EXCEPTION 检测
- 用户旅程（需 experience-map）：按角色走完整路径，四节点评分
- 缺口任务按频次排优先级

```
/feature-gap              # 完整查漏（任务+界面+旅程）
/feature-gap quick        # 只查任务和界面，跳过旅程
/feature-gap journey      # 只验证用户旅程
/feature-gap role 客服专员  # 只查指定角色
```

### 7. feature-prune — 功能剪枝

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-prune.md`

产品地图里有的，哪些该留、哪些推迟、哪些砍掉？

- 频次过滤：低频功能进入剪枝候选，高频功能受保护
- 场景对齐（需 experience-map）：不服务核心场景的功能列为 CUT 候选
- 竞品参考：同类产品同阶段的功能范围
- 分类：CORE / DEFER / CUT，最终决定权归用户

```
/feature-prune            # 完整剪枝（频次+场景+竞品）
/feature-prune quick      # 只看频次，跳过竞品
/feature-prune scope 用户管理  # 只剪枝指定模块
```

### 8. ui-design — UI 设计规格

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/ui-design.md`

从产品地图 + 体验地图推导高层 UI 设计规格，结合风格选择和设计原则，输出设计规格文档 + 按角色拆分的 HTML 预览。

```
/ui-design               # 完整流程
/ui-design refresh       # 重新生成
```

### 8.5 ui-review — UI 审核迭代

> 详见 `${CLAUDE_PLUGIN_ROOT}/commands/ui-review.md`

启动本地审核服务器，浏览所有界面设计、标注 pin 评论，提交反馈后局部迭代。

```
/ui-review               # 启动审核服务器（localhost:18903）
/ui-review process       # 读取反馈，重跑需修改的界面
```

### 9. design-audit — 设计审计

> 详见 `${CLAUDE_PLUGIN_ROOT}/skills/design-audit.md`

跨层校验产品设计全链路一致性，三个维度：逆向追溯（下游产物有无源头）、覆盖洪泛（上游节点是否被完整消费）、横向一致性（相邻层有无矛盾）。

- 自动探测已有产物，按已有层决定校验范围
- 只读不改，审计结果输出 JSON + Markdown
- 支持指定角色做全链路校验

```
/design-audit              # 三合一全量校验
/design-audit trace        # 仅逆向追溯
/design-audit coverage     # 仅覆盖洪泛
/design-audit cross        # 仅横向一致性
/design-audit role 客服专员  # 指定角色全链路校验
```

## 全流程编排

使用 `/product-design full` 串联全部技能 + 阶段间检查点 + 终审：

```
/product-design full                # 从头执行全流程
/product-design full skip: concept  # 跳过概念发现
/product-design resume              # 从断点继续
```

流程：concept → **concept-review（概念审核）** → **market-validate** → product-map → **map-review（地图审核）** → journey-emotion → experience-map → interaction-gate → **wireframe-review（结构锁定门）** → **Stitch 决策点** → [use-case ∥ feature-gap ∥ ui-design] → **ui-review（视觉审核）** → design-audit，每阶段间插入检查点验证产出完整性。

> **wireframe-review**（Phase 5）：低保真线框审核，验证 IA/流程/功能。反馈路由到 product-map / experience-map / concept。通过后结构锁定，才进入视觉设计。

> **Stitch 决策点**（Phase 5.5）：wireframe-review 通过后、进入 Phase 6-8 并行执行前，检查 Stitch MCP 可用性。不可用时 AskUserQuestion 三选一（上传设计稿 / 跳过视觉验收 / 配置 Stitch）。选择跳过时记入 pipeline-decisions（`stitch_skipped`），design-audit 标记 `stitch_skipped: true`。

## 工具配置

```
/setup                     # 一站式检测和配置所有外部能力
/update-all                # 更新所有已安装的插件、MCP 服务和技能
/update-all --dry-run      # 仅查看当前状态，不执行更新
```

## 定位

```
product-design（产品层）
├── product-concept   想做什么产品？                       搜索+选择题引导
├── concept-review    概念对不对？用户确认了吗？             脑图审核（必须）
├── market-validate   这个方向值得做吗？                   Brave搜索 + 跨模型验证
├── product-map       产品是什么？谁在用？做什么？有何约束？ 代码读现状 + PM 补业务视角
├── map-review        地图对不对？角色/任务/流程确认了吗？   脑图审核（必须）
├── journey-emotion 用户情绪在哪里起伏？                   基于 product-map
├── experience-map  在哪做？怎么做？出错怎么办？           基于 product-map + journey-emotion
├── interaction-gate 交互质量达标了吗？                    基于 experience-map（门禁）
├── design-pattern  重复模式抽象                          基于 task-inventory + experience-map
├── behavioral-standards 跨界面行为一致性                  基于 experience-map
├── wireframe-review 线框交互审核（结构锁定门）             基于 experience-map（低保真 review）
├── use-case        推导完整用例，双格式输出               基于 product-map + experience-map
├── feature-gap     地图说有的，有没有？旅程走得通吗？      基于 product-map + experience-map
├── feature-prune   地图里有的，该不该留？                 基于 product-map + experience-map
├── ui-design       高层 UI 设计规格 + HTML 预览           基于 product-map + experience-map
└── design-audit    全链路一致性校验                       基于全部已有产物

dev-forge（开发层）   种子数据 + 产品验收                  基于 product-map + API/Playwright
deadhunt（QA 层）     链接通不通？CRUD 全不全？             需要 Playwright
code-tuner（架构层）  代码好不好？重复多不多？              纯静态分析
```

## 索引与按需加载

大型产品（400+ 任务）下，全量加载 `task-inventory.json` 消耗 50K+ tokens。引入轻量索引 + 两阶段加载协议，大幅节省上下文开销。

### 三个索引文件

| 索引文件 | 生产者 | 内容 | 体积（400 任务） |
|----------|--------|------|-------------------|
| `task-index.json` | product-map Step 6 | id, task_name, frequency, owner_role, risk_level，按模块分组 | ~4KB |
| `flow-index.json` | product-map Step 6 | id, name, node_count, gap_count, roles | ~2KB |
| `screen-index.json` | experience-map Step 1 | id, name, task_refs, action_count, has_gaps，按模块分组 | ~3KB |

### 两阶段加载协议

```
Phase 1: 加载索引（始终安全，< 5KB）
Phase 2: 根据技能 / Step / 模式决定是否加载完整数据、加载哪个模块
```

### 向后兼容

索引不存在 → 回退全量加载，行为与旧版完全一致。旧版 product-map 生成的产出无索引文件，所有消费者显式回退。

## 预置脚本

Phase 3-9 的纯转换脚本已预置到 `${CLAUDE_PLUGIN_ROOT}/scripts/`，随插件部署：

| 脚本 | Phase | 关键修复 |
|------|-------|---------|
| `_common.py` | 共享 | 字段常量、数据加载器、pipeline-decisions 去重写入 |
| `gen_journey_emotion.py` | 3 journey-emotion | 角色情绪旅程绘制、触点标注、低谷识别 |
| `gen_experience_map.py` | 4 experience-map | 任务→界面分组、CRUD 推断、flags 计算、pareto 分析 |
| `gen_interaction_gate.py` | 4.5 interaction-gate | 交互一致性、可用性、无障碍门禁检查 |
| `gen_use_cases.py` | 5 use-case | 用 `s.get("tasks", [])` 替代硬编码 `task_refs` |
| `gen_feature_gap.py` | 6 feature-gap | 防御性检查 `is_primary`/`on_failure` 缺失 |
| `gen_feature_prune.py` | 7 feature-prune | 接受 `--strategy` 参数覆盖策略 |
| `gen_ui_design.py` | 8 ui-design | 风格参数化 `--style` |
| `gen_behavioral_standards.py` | 4.6 behavioral-standards | 9 类行为不一致检测 + screen 标签映射 |
| `gen_design_audit.py` | 9 design-audit | 修复 `gaps[:30)` 语法错误 |

**统一接口**：
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_xxx.py <BASE_PATH> [--mode auto]
```

自动模式下优先使用预置脚本；不存在时回退到 LLM 生成（向后兼容）。

---

## 推荐工作流

```
product-concept（可选，从 0 开始时必跑）
    ↓ 输出 .allforai/product-concept/product-concept.json
    │
market-validate（可选，验证概念市场可行性）
    ↓ 输出 .allforai/market-validate/market-validation.json
    │
product-map（必须先跑）
    ↓ 输出 .allforai/product-map/product-map.json + task-inventory.json
    │
    ├── journey-emotion（情绪旅程）
    │       ↓ 输出 .allforai/journey-emotion/
    │
    ├── experience-map（必须，支持 --variants N 多方案发散）
    │       ↓ 输出 .allforai/experience-map/experience-map.json
    │
    ├── interaction-gate（交互质量门禁，基于 experience-map）
    │
    ├── use-case（可选，需 product-map；有 experience-map 时更完整）
    │       ↓ 输出 .allforai/use-case/use-case-tree.json + use-case-report.md
    │
    ├── feature-gap（Step 1 基于 product-map，Step 2/3 需要 experience-map）
    ├── feature-prune（Step 1 基于 product-map，Step 2 需要 experience-map）
    ├── ui-design（需 product-map + experience-map，支持 --variants N 多风格发散）
    └── design-audit（终审，基于全部已有产物）

推荐流程：[product-concept → concept-review → market-validate →] product-map → map-review → journey-emotion → experience-map → wireframe-review → [use-case ∥ feature-gap ∥ ui-design] → ui-review → design-audit

或使用 /product-design full 自动编排全流程（含阶段间检查点 + 终审）。
```

## 文件结构

```
your-project/
└── .allforai/
    ├── market-validate/
    │   ├── market-validation.json    # 市场验证全量结果（竞品、角色、商业模式）
    │   ├── competitor-matrix.json    # 竞品矩阵（定位、定价、优劣势）
    │   └── validation-report.md     # 可读报告
    ├── concept-review/
    │   └── review-feedback.json        # 概念脑图审核反馈（nodes + status + comments）
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
    │   ├── competitor-profile.json     # 竞品功能概况（Step 0 草稿→Step 7 补全）
    │   ├── validation-report.json      # 三合一校验结果（机器可读）
    │   ├── validation-report.md        # 校验摘要（人类可读）
    │   └── product-map-decisions.json  # 用户决策日志
    ├── product-map-review/
    │   └── review-feedback.json        # 产品地图脑图审核反馈（nodes + status + comments）
    ├── journey-emotion/
    │   ├── journey-emotion.json        # 情绪旅程地图（触点情绪、低谷、高峰）
    │   └── journey-emotion-report.md   # 可读报告
    ├── experience-map/
    │   ├── experience-map.json         # 体验地图（含 states、on_failure、exception_flows）
    │   ├── screen-index.json           # 界面索引（轻量，供下游两阶段加载）
    │   ├── screen-conflict.json        # 界面级冲突 + 异常覆盖缺口
    │   ├── experience-map-report.md    # 可读报告
    │   └── experience-map-decisions.json # 用户决策日志
    ├── interaction-gate/
    │   ├── interaction-gate.json       # 交互质量门禁结果
    │   └── interaction-gate-report.md  # 可读报告
    ├── wireframe-review/
    │   └── review-feedback.json        # 线框审核反馈（pins + status + category）
    ├── use-case/
    │   ├── use-case-tree.json          # 机器可读：完整 4 层 JSON 树（Given/When/Then 全量）
    │   ├── use-case-report.md          # 人类可读：摘要级 Markdown（每条用例一行）
    │   └── use-case-decisions.json     # 用户决策日志（DEFERRED 记录）
    ├── feature-gap/
    │   ├── task-gaps.json              # 任务完整性检查结果
    │   ├── screen-gaps.json            # 界面与按钮完整性检查结果（需 experience-map）
    │   ├── journey-gaps.json           # 用户旅程验证结果（X/4 评分，需 experience-map）
    │   ├── gap-tasks.json              # 缺口任务清单（按频次排优先级）
    │   ├── flow-gaps.json              # 业务流链路完整性检查结果
    │   ├── gap-report.md               # 可读报告
    │   └── gap-decisions.json          # 用户确认记录
    ├── behavioral-standards/
    │   ├── behavioral-standards.json    # 行为规范目录（JSON 机器版，含 screen 标签映射）
    │   └── behavioral-standards-report.md # 人类可读摘要
    ├── feature-prune/
    │   ├── frequency-tier.json         # 频次分层结果
    │   ├── scenario-alignment.json     # 场景对齐结果（需 experience-map）
    │   ├── competitive-ref.json        # 竞品参考数据
    │   ├── prune-decisions.json        # 用户分类决策日志
    │   ├── prune-tasks.json            # 剪枝任务清单（DEFER/CUT）
    │   └── prune-report.md             # 可读报告
    └── design-audit/
        ├── audit-report.json           # 全量校验结果（机器可读）
        └── audit-report.md             # 人类可读摘要
```

## 输出规范（全套件铁律）

**JSON 给机器，Markdown 给人类。**

| 文件类型 | 受众 | 密度 |
|----------|------|------|
| `*.json` | AI agent、自动化测试 | 完整字段，逐条可执行，无省略 |
| `*-report.md` | PM、QA、开发 | 摘要级，突出问题和结论，不列每条字段 |

所有技能的 Markdown 报告只呈现「有什么问题、结论是什么」，不重复 JSON 中已有的字段细节。完整数据始终在 JSON 文件中。
