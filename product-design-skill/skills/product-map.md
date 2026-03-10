---
name: product-map
description: >
  Use when the user asks to "map the product", "list all features", "identify user roles",
  "build a product map", "understand the product",
  "产品地图", "功能点梳理", "用户角色识别", "建立产品地图",
  "列出所有功能", "产品现状分析", "理解产品结构",
  or mentions mapping product features, understanding user tasks,
  understanding what a product does, mapping features by user role, doing an initial product inventory,
  or building a foundation for feature gap detection, pruning, or seed data generation.
  Supports innovation boost mode: reads adversarial-concepts.json and marks innovation tasks with protection levels.
version: "2.6.0"
---

# Product Map — 产品地图梳理

> 读代码了解现状，用 PM 语言呈现，建立"现状 + 期望"的完整产品地图

## 目标

以代码为输入、以 PM 视角为准绳，梳理产品的完整现状：

1. **谁在用** — 识别用户角色，明确权限边界和 KPI
2. **做了什么** — 按角色提取核心任务，标注频次、风险、跨部门依赖、异常与验收标准
3. **有没有问题** — 检测任务级冲突、规则矛盾、CRUD 缺口
4. **受什么约束** — 识别合规、审计、业务约束

---

## 定位

```
product-map（现状+方向）      experience-map（必须）            feature-gap（对齐视角）      feature-prune（决策视角）
项目现在有什么？应该有什么？   界面、按钮、异常状态梳理        地图说有的，现在有没有？      地图里有的，该不该留？
代码读现状，PM 定方向          以 task-inventory 为输入     以 product-map 为基准        以 product-map 为锚点
输出产品地图（PM 语言呈现）    输出体验地图              输出缺口报告                 输出剪枝报告
```

**核心定位**：读代码了解现状，用 PM 语言呈现，让 PM 确认并补充业务视角，最终形成"现状 + 期望"的完整产品地图，用于指导项目未来发展方向。

**后续技能依赖**：`feature-gap`、`feature-prune`、`seed-forge` 均以 `.allforai/product-map/product-map.json` 为输入基准，无需重复分析。界面交互细节由 `experience-map` 技能单独梳理（必须运行，下游多个技能依赖其数据）。

---

## 快速开始

```
/product-map              # 完整流程（Step 0-9，无界面梳理）
/product-map quick        # 跳过冲突检测（Step 4）和约束识别（Step 5）
/product-map refresh      # 重新采集，忽略已有缓存
/product-map scope 退款管理  # 只梳理指定功能模块
```

## 增强协议（WebSearch + 4D+6V + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：`”story mapping” + 行业词 + “best practices” + 2025`

**4D+6V 重点**：每个任务补充 `source_refs`、`constraints`、`decision_rationale`；`task-inventory.json` 作为下游锚点，优先保证”可追溯 + 可解释”。

**XV 交叉验证**（Step 5 约束识别后）：

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| 任务完整性审查 | `task_completeness_review`→gemini | 角色列表 + 高频任务清单 + 已发现的冲突 | cross_model_review.missing_tasks |
| 隐藏冲突检测 | `conflict_detection`→gpt | 角色列表 + 高频任务 + 任务间依赖关系 + 业务规则 | cross_model_review.hidden_conflicts |

自动写入：遗漏任务提示、隐藏冲突（跨角色规则矛盾、状态流转死锁风险）。

## 中段经理理论支持（可选增强，不破坏现有流程）

为保证「概念 → 功能点 → 交互」阶段具备可审计的产品管理依据，product-map 可叠加以下理论锚点：

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|----------|----------|
| Story Mapping（Jeff Patton） | Step 2/3 | 任务按用户活动流分层：主干活动（backbone）→ 任务切片（slice）→ 版本范围 |
| RACI 职责矩阵 | Step 1/2 | 在角色与任务关系中明确 Responsible / Accountable / Consulted / Informed，减少角色边界冲突 |
| 风险矩阵（Impact × Probability） | Step 2/5 | 将 risk_level 的判定从主观高/中/低，改为可解释的概率×影响分档 |
| DoR（Definition of Ready） | Step 9 | 将 required 字段完整性视为进入下游（experience-map/use-case）的就绪门槛 |

> 建议：默认沿用现有流程；当团队需要更强「产品管理可追溯性」时启用本增强。

**scope 模式**：运行与 full 相同的 Step 序列，但在前置加载后先按关键词过滤 — 匹配 `task-inventory.json` 中 `name` 包含该关键词的任务，以及这些任务关联的角色和场景。后续所有 Step 仅处理过滤后的子集。输出文件中标注 `"scope": "{关键词}"`。若 `task-inventory.json` 尚不存在（首次运行），scope 过滤延迟到 Step 2 完成后执行，Step 0–2 按完整范围运行。

**refresh 模式**：忽略所有已有输出和决策缓存。将 `product-map-decisions.json` 重命名为 `.bak` 备份，然后从 Step 0 开始完整重新运行。refresh 完成后自动生成与上一版的 diff 摘要（新增/删除/变更的任务和流），写入 `refresh-diff.md`。适用于代码大改后需要全量重新分析的场景。

---

## 规模适配

Step 0 完成后，根据代码路由/菜单项数量自动判定产品规模，决定后续步骤的交互策略。

| 规模 | 判定条件 | 交互策略 |
|------|----------|----------|
| **小型** | 预估任务 ≤ 30 | 标准模式：逐项展示，逐步确认 |
| **中型** | 预估任务 31–80 | 摘要模式：展示按角色分组的摘要表 + 标记异常项，用户确认摘要级 |
| **大型** | 预估任务 > 80 | 自审计模式：生成 → 自动代码审计 → 标记差异 → 展示审计摘要 → 用户确认 |

**规模对各步骤的影响**：

| 步骤 | 小型 | 中型/大型 |
|------|------|-----------|
| Step 2 生成 | Write 工具直接写入 | **必须使用脚本生成**（Python/Node），避免 Write 工具超限 |
| Step 2 确认 | 展示完整任务表 | 展示角色×任务数摘要 + 审计发现的差异 |
| Step 3 确认 | 展示完整流列表 | 展示流摘要 + 自动检测的缺口 |
| Step 2/3 自审计 | 跳过（人工可覆盖） | **强制执行**自审计子步骤 |
| Step 9 完整性 | 逐项列出 | 仅列出 required 字段的缺失（推荐字段归为 INFO） |

**脚本生成指南**（中型/大型产品必读）：

当任务数 > 30 时，`task-inventory.json` 通常超过 Write 工具的输出限制。此时必须：
1. 先用 Write 工具生成一个 Python/Node 脚本（如 `gen_tasks.py`）
2. 脚本内以编程方式构建完整 JSON 数据结构
3. 用 Bash 执行脚本，将结果写入目标文件
4. 执行后用 Bash `wc -l` 和 `python -m json.tool` 验证文件完整性
5. 删除临时脚本

同理适用于 `business-flows.json`、`product-map.json`、`validation-report.json` 等大文件。

---

## 概念指导模式

当 `.allforai/product-concept/product-concept.json` 存在时，product-map 自动进入**概念指导模式**。此模式下 AI 拥有完整的产品战略上下文（角色、问题、价值主张、ERRC 矩阵、商业模式），可自主完成大部分步骤，**仅在发现「概念 vs 代码」差异时才暂停确认**。

### 激活条件

Step 0 开始前检查 `.allforai/product-concept/product-concept.json` 是否存在且 `version` 字段有效。若存在，加载全部字段，输出提示：「检测到产品概念文档，进入概念指导模式 — 自主执行，仅在 gap 处暂停确认」。

### 各步骤行为变化

| 步骤 | 标准模式 | 概念指导模式 |
|------|----------|-------------|
| **Step 0 项目画像** | 用户确认画像 | 从 concept 加载问题域+竞品，与代码画像合并，**仅展示 gap 列表**（concept 有代码无 / 代码有 concept 无），有 gap 时确认，无 gap 时自动通过 |
| **Step 1 角色识别** | 用户确认角色列表 | 从 concept.roles 映射，与代码推导角色交叉比对，**仅展示差异角色**（concept 有代码无 → 标记待实现；代码有 concept 无 → 标记待确认），有差异时确认，无差异时自动通过。同时从 concept 的 role_type 自动推导 audience_type |
| **Step 2 任务提取** | 用户确认任务清单 | 基于 concept.top_problems + ERRC 矩阵自动判定任务优先级，ERRC.eliminate 中的功能标记 `user_removed`，**仅展示 concept 无法覆盖的任务**（如代码中存在但 concept 未提及的功能），有此类任务时确认 |
| **Step 3 业务流** | 用户确认流列表 | 自主生成，**仅在发现 gap（MISSING_TASK / BROKEN_HANDOFF）时暂停确认** |
| **Step 4 冲突检测** | 用户确认冲突 | 自主执行，**仅在发现高严重度冲突时暂停确认**，中/低严重度自动记录 |
| **Step 5 约束识别** | 用户确认约束 | 从 concept.business_model 推导约束方向，自主生成，**仅在 code_status="missing" 的硬约束处暂停确认** |
| **Step 6 输出** | 直接输出 | 同标准模式 |
| **Step 7 数据建模** | 用户确认实体模型 | 从 concept 已有的业务实体定义自动推导，**仅在发现 concept 未覆盖的实体时暂停确认** |
| **Step 8 视图对象** | 用户确认 VO 列表 | 自主生成，**仅在 VO 与 concept 的界面描述有冲突时暂停确认** |
| **Step 9 校验** | 用户确认校验结果 | 跳过竞品差异（concept 已有 competitive_position），**仅在 ERROR 级问题处暂停确认**，WARNING/INFO 自动记录 |

### Gap 分类

概念指导模式下检测到的 gap 分两类：

| Gap 类型 | 含义 | 处理 |
|----------|------|------|
| **concept 有 → 代码无** | 产品概念中定义但代码未实现的角色/功能 | 自动标记 `status: "user_added"`，纳入地图，不暂停 |
| **代码有 → concept 无** | 代码中存在但产品概念未提及的角色/功能 | **暂停确认** — 可能是遗留代码需清理，也可能是 concept 遗漏 |

### 决策日志标记

概念指导模式下自动通过的步骤，在 `product-map-decisions.json` 中记录 `"decision": "concept_guided"`，与 `confirmed` / `auto_audited` 区分，便于回溯。

### 与历史决策共存

当 `product-concept.json` 和 `product-map-decisions.json` **同时存在**时：

**历史决策优先** — 已 `confirmed` / `concept_guided` / `auto_audited` 的 Step 全部自动跳过，仅输出一行摘要（如「Step 2 已确认，163 个任务，跳过」）；未确认的 Step 按概念指导模式执行（仅 gap 处暂停）。不重新走任何已完成步骤的确认流程。

### 创新概念处理（v2.0+）

当 `product-concept.json` 包含 `innovation_preferences` 字段或存在 `adversarial-concepts.json` 时：

**Step 2 任务提取增强**：
1. 读取 `adversarial-concepts.json` 中的 `concepts[]` 数组
2. 对每个 `protection_level="core"` 或 `"defensible"` 的创新概念：
   - 生成对应任务，标记 `status: "concept_defined"` + `innovation_task: true`
   - 代码中无此任务 → 自动添加，标记 `source: "innovation_concept"`
3. 在 `task-inventory.json` 顶层增加 `innovation_tasks` 数组引用

**Step 9 校验增强**：
- 创新功能不跟竞品比，跟概念文档比
- `competitor_diff` 部分排除 `innovation_tasks`
- 完整性扫描时，创新功能的缺失字段按 `protection_level` 差异化处理：
  - `core` → ERROR 级（必须填写完整）
  - `defensible` → WARNING 级
  - `experimental` → INFO 级

**输出增强**：
```json
// product-map.json 新增字段
"innovation_tasks": [
  {
    "task_id": "T001",
    "source": "concept_defined",
    "protection_level": "core",
    "innovation_score": 9,
    "adversarial_concept_ref": "IC001"
  }
]
```

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 0 竞品提问** | AskUserQuestion 询问竞品 | 读 `pipeline_preferences.competitors`：非空 → 直接填充 `competitor-profile.json`，跳过提问；空 → 记录 `competitors: []`，Step 9 Part 3 跳过竞品差异 |
| **Step 0 画像确认** | AskUserQuestion 确认 | 自动确认，记入 `pipeline-decisions.json`（`decision: "auto_confirmed"`） |
| **Step 1 角色确认** | AskUserQuestion 确认 | 自动确认 |
| **Step 2 任务确认** | AskUserQuestion 确认 | 自动确认 |
| **Step 3 业务流确认** | AskUserQuestion 确认 | 自动确认 |
| **Step 4 冲突确认** | AskUserQuestion 确认 | 自动确认（冲突记录到 decisions.json） |
| **Step 5 约束确认** | AskUserQuestion 确认 | 自动确认 |
| **Step 7 数据建模** | AskUserQuestion 确认 | 自动确认 |
| **Step 8 视图对象** | AskUserQuestion 确认 | 自动确认 |
| **Step 9 校验** | AskUserQuestion 确认 | ERROR 级问题（必填字段缺失、引用断裂）→ **停下来问用户**；WARNING/INFO → 记日志自动继续 |

**安全护栏**（自动模式下仍然停下来问用户）：
- task 数 = 0（Step 2 后检测）
- 必填字段缺失导致下游无法运行

**与概念指导模式叠加**：全自动模式与概念指导模式可同时激活。叠加时，概念指导模式的 gap 检测照常执行，但「gap 处暂停确认」变为自动确认（gap 记入 decisions.json）。仅 ERROR 级 gap（如代码有但 concept 无的关键功能）才停下来问。

---

## 工作流

```
Step 0: 项目画像
      读代码，提取技术栈、路由结构、权限系统、菜单配置
      转换为产品语言：有哪些功能模块、有哪些用户角色（草稿）
      判定产品规模（小型/中型/大型）
      → 用户确认画像是否准确
      ↓
Step 1: 用户角色识别
      从代码推导角色（权限枚举、守卫、角色配置）→ 转换为 PM 语言描述
      每角色：角色名 / 职责描述 / 权限边界 / KPI
      PM 可补充代码未体现的角色、删除已废弃的角色
      → 用户确认，生成 role-profiles.json
      ↓
Step 2: 核心任务提取（按角色展开）+ 自审计
      从代码提取每个角色的操作（路由、菜单项、权限点）→ 转换为业务任务描述
      每条任务使用功能点描述模板（见下方 Schema，区分 required / recommended 字段）
      【自审计】生成后自动扫描代码路由/Handler，比对任务覆盖率
      PM 可补充代码没有的任务（期望方向）、标记代码有但业务不需要的任务
      → 用户确认任务清单（含审计差异），生成 task-inventory.json
      ↓
Step 3: 业务流建模（所有模式均不可跳过）+ 自审计
      自动识别候选流 + 用户补充跨系统链路
      检测流缺口：MISSING_TASK / BROKEN_HANDOFF / INDEPENDENT_OPERATION / ORPHAN_TASK / MISSING_TERMINAL
      【自审计】生成后自动验证所有流节点 handoff 连续性
      → 用户确认，生成 business-flows.json + business-flows-report.md
      ↓
Step 4 & Step 5（可并行，互不依赖）
      ↓                              ↓
Step 4: 冲突 & 冗余检测         Step 5: 约束识别
      （quick 模式跳过）               （quick 模式跳过）
      检测任务级冲突 + CRUD 缺口       合规/审计 + 业务约束
      → conflict-report.json          → constraints.json
      ↓                              ↓
      ←——————————————————————————————→
      ↓
Step 6: 输出产品地图报告
      汇总所有已确认数据，生成 product-map.json 和 product-map-report.md
      ↓
Step 7: 数据建模
      从任务清单、业务流、约束条件推导后端实体模型和 API 契约
      → 用户确认，生成 entity-model.json + api-contracts.json + data-model-report.md
      ↓
Step 8: 视图对象
      从实体模型和 API 契约生成前端视图对象（View Object）
      → 用户确认，生成 view-objects.json
      ↓
Step 9: 校验
      完整性扫描 + 冲突重扫 + 竞品差异（Web 搜索）
      → 用户确认，生成 validation-report.json + validation-report.md
```

**核心原则：每个 Step 结束都有用户确认，用户是权威。**
**概念指导模式例外：有 product-concept.json 时，仅在 gap 处暂停确认（见「概念指导模式」章节）。**

---

### Step 0：项目画像

两类输入并行，相互补充：

| 类型 | 来源 | 说明 |
|------|------|------|
| 工程输入 | 代码（路由、菜单、权限配置、页面组件） | 了解项目现状，提取已有功能点 |
| 产品输入 | PRD、用户故事、原型图描述、PM 口述 | 补充业务语义，确认方向，标记差距 |

代码告诉我们**现在有什么**，PM 确认**应该有什么**。两者的差距就是需要改进的方向。

读取代码中的路由配置、菜单定义、权限枚举和守卫，将工程结构转换为产品语言：

- 有哪些功能模块（菜单项 → 功能区）
- 有哪些用户角色（权限枚举 → 角色草稿）
- 大致的操作入口分布

**规模判定**：统计代码中的路由/API 端点/菜单项总数，按规模适配表判定产品规模（小型/中型/大型）。在画像摘要中明确告知用户：「本产品预估 X 个任务，属于{规模}产品，后续将采用{交互策略}」。

**Fallback**：若代码中找不到路由配置、菜单定义或权限枚举（如纯后端服务、非标准框架），则切换为用户访谈模式 — 直接询问用户描述产品的主要模块、角色和功能，手动构建初始画像。标记 `analysis_mode: "interview"` 以区别于代码分析结果。

若用户提供 PRD 或原型图描述，同步读取，标记代码中尚未实现的功能模块（`status: user_added`）和已废弃的模块（`status: user_removed`）。

生成 `role-profiles.json` **草稿**（仅在对话中展示，Step 1 用户确认后才写入磁盘）。

**竞品提问**（画像确认前，先问两个问题）：

> 1. 这个产品主要对标哪些竞品？（例如：Shopify、有赞、微盟；或「暂时没有参照」也可以）
> 2. 对比维度是什么？（平台功能对标 / 用户体验对标 / 商业模式对标 / 全方位对标）

根据用户回答：
- **有竞品**：记录名字列表和对比维度，生成 `competitor-profile.json` 草稿（写名字 + `comparison_scope`），Step 9 再做 Web 搜索
- **无竞品**：记录 `competitors: []`，`analysis_status` 设为 `"skipped"`，Step 9 只做完整性 + 冲突校验，跳过竞品差异部分

生成 `competitor-profile.json` 草稿：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "competitors": ["Shopify", "有赞"],
  "comparison_scope": "platform_features",
  "analysis_status": "pending",
  "analyzed_at": null
}
```

> 草稿此时只写入名字和对比维度，Step 9 执行完后补全竞品功能数据，`analysis_status` 改为 `"completed"`。
> `analysis_status` 取值：`"pending"`（待分析）/ `"skipped"`（无竞品，Step 9 跳过竞品差异）/ `"completed"`（已完成）
> `comparison_scope` 取值：`"platform_features"`（平台功能对标）/ `"user_experience"`（用户体验对标）/ `"business_model"`（商业模式对标）/ `"comprehensive"`（全方位对标）

**用户确认**：这个项目的功能全景对吗？有没有遗漏的模块？规模判定是否合理？

---

### Step 1：用户角色识别

**角色粒度原则（必读）**：产品地图使用「概念层合并角色」，不使用 RBAC 的细分权限角色。

| 类型 | 示例 | 用途 |
|------|------|------|
| **概念层角色**（产品地图使用） | 买家 / 商户 / 平台管理员 | 任务归属、业务流节点、频次/风险分析 |
| **实现层角色**（RBAC 权限系统） | 商户编辑 / 审核员 / 客服 | 权限控制、屏幕设计，不进入产品地图主结构 |

若代码中存在细粒度的 RBAC 角色（如商户编辑/商户查看员/平台运营/平台客服），**聚合**为对应的概念层角色，用 `impl_roles` 字段记录映射关系，不在主角色列表中逐一拆分。

若无 `product-concept.json`，按业务端分组聚合：买家侧 / 商户侧 / 平台侧（超管 + 受限管理员），不按权限点一对一拆分。

从代码中的权限枚举、路由守卫、角色配置推导角色，补充业务语义：

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "roles": [
    {
      "id": "R001",
      "name": "客服专员",
      "description": "处理客户投诉、退款申请、订单异常",
      "permission_boundary": ["退款申请", "订单查询", "用户信息查询（脱敏）"],
      "kpi": ["处理时效 < 2h", "退款错误率 < 0.1%"],
      "audience_type": "professional",
      "status": "confirmed"
    }
  ]
}
```

**`audience_type` 字段**（recommended）：

标记角色面向的用户群体，供 experience-map 选择交互设计标准。

| 值 | 含义 | 适用场景 |
|----|------|----------|
| `consumer` | 消费侧用户（C端） | App 用户、网站访客、买家 |
| `professional` | 专业/内部用户（B端） | 运营后台、管理员、商户、客服 |

**推导规则**（按优先级）：
1. 若 `role-value-map.json` 存在且角色有 `role_type`：`consumer` → `consumer`，`producer` / `admin` → `professional`
2. 若无 product-concept，Step 1 确认时询问用户标注
3. 未标注时缺省，下游技能使用 default 阈值（v2.3.0 行为不变）

PM 可补充代码未体现的角色（业务上存在但权限系统未区分），也可删除已废弃角色。

**用户确认**：角色列表完整吗？职责描述准确吗？权限边界有没有遗漏？

输出：`.allforai/product-map/role-profiles.json`

---

### Step 2：核心任务提取

按角色展开，从路由、菜单项、权限点提取任务，转换为业务语言。

#### 任务字段分层

字段分为 **required**（必填，缺失视为质量问题）和 **recommended**（推荐，缺失仅提示）：

| 层级 | 字段 | 说明 |
|------|------|------|
| **required** | `id`, `name`, `owner_role`, `frequency`, `risk_level`, `main_flow`, `status`, `category` | 任务身份和核心属性，缺失将导致下游技能无法正常工作 |
| **recommended** | `value`, `approver_role`, `viewer_roles`, `cross_dept`, `cross_dept_roles`, `sla`, `prerequisites`, `rules`, `config_items`, `inputs`, `outputs`, `exceptions`, `audit`, `acceptance_criteria` | 丰富任务语义，提升地图质量，但非强制 |

**生成策略**：
- **小型产品（≤30 任务）**：尽量填写所有字段，包括 recommended
- **中型/大型产品（>30 任务）**：优先保证所有 required 字段完整；recommended 字段按优先级填写：高频+高风险任务填写全部 recommended 字段，中低频任务至少填写 `rules` 和 `exceptions`

#### 任务 Schema

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/task-schema.md

#### 任务分类规则（category）

每个任务必须标注 `category` 字段，分为两类：

| category | 含义 | 判定标准 | 典型模块 |
|----------|------|---------|---------|
| `basic` | 基本功能 — 换个产品一样需要 | 认证/账户/支付/管理/支持/引导/通知/反馈 | 注册登录、个人设置、订阅付费、系统管理、用户支持 |
| `core` | 核心功能 — 产品差异化价值 | 本产品独有或核心的业务能力 | 学习/对话/AI/内容创作/数据分析/游戏化 |

**判定优先级**（按顺序匹配，首条命中即停）：

1. 认证相关（注册/登录/重置密码/注销/SSO）→ `basic`
2. 支付相关（订阅/购买/退款/续费/账单）→ `basic`
3. 系统管理（配置参数/权限角色/用户账户管理）→ `basic`
4. 通用支撑（通知中心/意见反馈/新手引导/个人设置）→ `basic`
5. 其余 → `core`

**输出拆分**：Step 2 完成后，除 `task-inventory.json`（全量）外，额外生成：
- `task-inventory-basic.json` — 仅含 `category=basic` 的任务
- `task-inventory-core.json` — 仅含 `category=core` 的任务

两个拆分文件与全量文件共享同一 schema，仅在顶层增加 `"category"` 和 `"description"` 字段标识归属。

#### 配置级别（config_level）

任务的 `rules` 中涉及数值、策略、阈值等参数时，使用 `config_items` 字段标注每个可配置参数的实现级别。不同级别决定了参数的改动成本和管理方式。

| config_level | 含义 | 改动成本 | 示例 |
|-------------|------|----------|------|
| `frontend_hardcode` | 界面写死 | 前端发版 | 注册方式列表、排行榜维度、可选语言 |
| `code_constant` | 代码写死 | 后端发版 | AI难度适配范围、排行榜周期 |
| `config_file` | 启动配置文件（.env / config.yaml） | 重启/重新部署 | API Key、密码策略、支付渠道、推荐算法权重 |
| `general_config` | 通用配置模块（增删改查） | 热更新，运营后台可调 | 免费额度、告警阈值、审核时限、连胜恢复次数 |
| `dedicated_config` | 专用配置模块（专属管理界面） | 热更新，需专属界面 | 成就模板管理、订阅方案配置、场景难度定义、推送文案 |

**`config_items` 字段 Schema**：

```json
"config_items": [
  {
    "param": "参数名",
    "current": "当前值或待定",
    "config_level": "general_config"
  }
]
```

**生成策略**：
- 遍历每个任务的 `rules`，识别其中的数值/策略/阈值
- 对每个可配置参数，与用户确认其 config_level
- `task-inventory.json` 的顶层增加 `config_level_summary` 统计各级别数量
- Step 9 校验时，检查所有 `general_config` 参数是否被 R007（或同等管理员角色）的「配置系统参数」任务覆盖

#### 自审计子步骤（中型/大型产品强制执行）

任务清单初步生成后，执行代码路由审计：

1. **扫描代码路由/Handler**：遍历后端路由定义（如 Go 的 `router.Group` / Express 的 `app.get` / Next.js 的 `app/` 目录），提取所有 API 端点
2. **扫描前端菜单/页面**：遍历前端菜单配置和页面组件，提取所有用户可访问的操作入口
3. **交叉比对**：将扫描结果与已生成的任务清单比对，标记：
   - **代码有 → 任务无**：遗漏任务，自动补充并标记 `"source": "code_audit"`
   - **任务有 → 代码无**：用户期望功能，保留并标记 `status: "user_added"`
4. **展示审计结果**：在用户确认前，展示「自审计发现 X 个代码中存在但初始遗漏的功能」

审计结果记入 decisions.json，`decision` 类型为 `"auto_audited"`。

#### 调试支持任务（不可遗漏）

调试与开发辅助功能是产品的组成部分，必须纳入任务清单，不可因"纯工程工具"理由跳过。常见调试支持任务包括：

| 类别 | 示例 | 归属角色 |
|------|------|---------|
| 健康检查 | 查看系统健康状态、服务存活探针 | 管理员/运维 |
| 日志与监控 | 查看应用日志、追踪请求链路、查看错误报告 | 管理员/运维 |
| 特性开关 | 管理 Feature Flag、灰度发布控制 | 管理员 |
| 测试工具 | 重置测试数据、触发测试通知、模拟业务事件 | 开发/管理员 |
| 调试面板 | 查看队列状态、查看缓存状态、强制刷新配置 | 管理员/运维 |
| 数据修复 | 手动补偿数据、重触发失败任务 | 管理员/运维 |

**纳入规则**：
- 归属管理员角色（R003/R004 或专属运维角色），统一归入 `"module": "开发支持"` 或 `"module": "系统运维"`
- `frequency` 标注为「低」，`risk_level` 按实际情况标注（日志查看=低，数据修复=高）
- 自审计扫描路由时，`/debug/`、`/admin/dev/`、`/internal/`、`/health`、`/metrics` 路径下的端点均视为调试支持任务
- feature-prune 阶段可整体评估是否推迟，但 product-map 阶段必须完整收录

#### 闭环完整性审计（所有模式必须执行）

**原理**：产品中的每个功能都存在于大大小小的循环中，不存在孤立的功能。闭环思维要求：对每个任务，追问它在循环中的位置，检查循环是否完整。

**四类闭环**：

| 闭环类型 | 追问 | 示例 |
|---------|------|------|
| **配置闭环** | 这个功能靠什么运行？谁来配置它？ | 有「使用X」就要有「配置X」 |
| **监控闭环** | 这个功能运行得好不好？谁来看？ | 有「执行操作」就要有「查看效果/数据」 |
| **异常闭环** | 这个功能失败了怎么办？谁来处理？ | 有「正常路径」就要有「异常处理/回退」 |
| **生命周期闭环** | 这个东西创建了，最终去哪？ | 有「创建」就要有「归档/过期/清理」 |

**审计方法**：

1. 遍历 `product_mechanisms` 中提到的每个能力/服务/技术
2. 遍历已生成任务清单中的每个功能任务
3. 对每个功能任务，逐一追问四类闭环：
   - **配置闭环**：该功能依赖的外部服务/能力/算法，是否有对应的配置管理任务？
   - **监控闭环**：该功能的运行效果，是否有对应的数据查看/统计任务？
   - **异常闭环**：该功能失败时的处理，是否体现在某个任务的 main_flow 或 exceptions 中？
   - **生命周期闭环**：该功能产生的数据/内容，是否有过期/清理/归档机制？
4. 缺失的闭环环节 → 补充对应任务或在已有任务中补充 main_flow 步骤
5. 展示：「闭环审计：X 个任务已检查，Y 个闭环缺失已补充」

**用户确认**：任务清单完整吗？审计发现的遗漏是否都应纳入？

输出：`.allforai/product-map/task-inventory.json`（全量）、`.allforai/product-map/task-inventory-basic.json`（基本功能）、`.allforai/product-map/task-inventory-core.json`（核心功能）

---

### Step 3：业务流建模

Step 2 完成后执行，所有模式均不可跳过。

#### 预置脚本（优先使用）

检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_business_flows.py` 是否存在：
- **存在** → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_business_flows.py <BASE>`
- **不存在** → 回退到 LLM 生成（向后兼容）

预置脚本从 task-inventory 自动识别候选流、验证交接连续性、检测孤立/幽灵状态，生成 business-flows.json + 泳道图 SVG。

#### 候选流自动识别

Claude 分析 `task-inventory.json`，寻找任务间的状态衔接关系：若任务 A 的 `outputs.states` 与任务 B 的 `prerequisites` 匹配，视为候选流节点对，自动组合成候选业务流，展示给用户确认。

#### 跨系统引用

若业务流涉及其他系统（如用户 App → 商户后台），用户可提供其他系统的 `task-inventory.json` 路径：

```
如果这条业务流涉及其他系统，请提供对应系统的 task-inventory 路径：
/path/to/other-system/.allforai/product-map/task-inventory.json
未提供时，跨系统节点标记为 gap_type: "UNVERIFIED"，不阻断流程。
```

`task_ref` 格式规则：

| 格式 | 含义 |
|------|------|
| `T001` | 当前系统的 T001 |
| `merchant-backend:T015` | merchant-backend 系统的 T015 |

#### 流级缺口类型

| Flag | 含义 |
|------|------|
| `MISSING_TASK` | 流节点引用的 task 在对应系统不存在 |
| `BROKEN_HANDOFF` | 节点间有 handoff，但下游 task 的 prerequisites 对不上 |
| `INDEPENDENT_OPERATION` | task 未被任何流引用，但属于独立操作（如导出、设置、档案管理），无需纳入流 |
| `ORPHAN_TASK` | task 未被任何流引用，且不属于独立操作，可能是建模遗漏 |
| `MISSING_TERMINAL` | 流没有用户侧可感知的终止节点 |

**孤立任务分类规则**：未被任何流引用的任务，按以下规则自动分类：
- **INDEPENDENT_OPERATION**：任务名包含「导出」「设置」「配置」「查看列表」「管理档案」等独立操作关键词，或 `cross_dept` 为 false 且无 `approver_role`
- **ORPHAN_TASK**：不符合 INDEPENDENT_OPERATION 条件的孤立任务，可能是遗漏的流节点

只有 `ORPHAN_TASK` 标记为需关注的潜在问题；`INDEPENDENT_OPERATION` 仅作为信息记录。

#### 自审计子步骤（中型/大型产品强制执行）

业务流初步生成后，自动验证：

1. **Handoff 连续性**：检查每条流中相邻节点的 handoff 是否连贯（前一节点的 outputs.states 是否匹配后一节点的 prerequisites）
2. **终止节点检查**：每条流必须有明确的用户可感知终止节点（如「订单完成」「退款到账」）
3. **高频任务覆盖**：所有 frequency="高" 的任务应至少出现在一条流中（否则标记为 ORPHAN_TASK 候选）
4. **状态供需平衡**（新增，通用版）：
   - 提取所有任务的 `outputs.states` → 生产者清单
   - 提取所有任务的 `prerequisites` → 消费者清单
   - 检测**孤儿状态**：有生产无消费（任何领域都应该避免）
   - 检测**幽灵状态**：有消费无生产（任何领域都零容忍）
   - 展示：「自审计发现 X 个孤儿状态 / X 个幽灵状态」

5. **状态契约检查**（新增，通用版）：
   - 对每个含 `outputs.states` 的任务，检查其 `exceptions` 是否覆盖所有可能错误
   - 对每个含 `prerequisites` 的任务，检查其 `on_failure` 是否定义
   - 检测**契约缺失**：状态转换无异常处理（如"订单支付"无"支付失败"处理）
   - 检测**超时缺失**：长时间操作（>30s）无超时转换定义
   - 展示：「自审计发现 X 个状态转换缺少异常处理 / X 个长时间操作无超时定义」
5. **展示审计结果**：在用户确认前，展示「自审计发现 X 个断裂交接 / X 个缺失终止节点 / X 个高频孤立任务 / X 个孤儿状态 / X 个幽灵状态」

#### 用户确认

展示候选流 + 识别到的缺口 + 自审计结果，用户可：
- 确认/修改候选流
- 补充未被识别的跨系统节点
- 确认孤立任务分类（INDEPENDENT_OPERATION vs ORPHAN_TASK）

确认后写入 `business-flows.json` 和 `business-flows-report.md`。

#### `business-flows.json` Schema

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/business-flows-schema.md

输出：`.allforai/product-map/business-flows.json`、`.allforai/product-map/business-flows-report.md`

#### SVG 生成：business-flows-visual.svg

`business-flows.json` 写入磁盘后，生成 `.allforai/product-map/business-flows-visual.svg`。

**生成方式**：使用 Python 脚本生成 SVG 文件。脚本读取 `business-flows.json`，按以下设计意图生成泳道图：

**设计意图**：
- 按流分区，每条流一个泳道区块
- 泳道按角色分行，节点按 seq 顺序从左到右排列
- 正常节点蓝框白底，缺口节点红色虚线框
- 相邻节点用箭头连接，handoff 信息标注在箭头上方
- 画布宽高自适应节点数量，确保所有内容可见

**颜色规范**：

| 元素 | 颜色 |
|------|------|
| 流标题栏背景 | `#1E293B`，白色文字 |
| 泳道标签背景 | `#F1F5F9`，`#475569` 文字 |
| 正常节点 | border `#3B82F6`，fill `#EFF6FF`，文字 `#1E3A8A` |
| 缺口节点 | border `#EF4444` 虚线，fill `#FEF2F2`，文字 `#991B1B` |
| handoff 箭头 | `#64748B`，marker-end arrow |
| seq 编号圆 | fill `#3B82F6`，白色文字 |

写入 `.allforai/product-map/business-flows-visual.svg`

---

### Step 4：冲突 & 冗余检测

**与 Step 5 互不依赖，可并行执行。**

基于已确认的任务，**仅检测任务级问题**：

**任务级冲突（保留）**：
- 两个任务的 `rules` 或状态流转互相矛盾（业务冲突）
- `main_flow` 缺少必要操作类型（CRUD 缺口：有新增无查看、有创建无撤回等）

**界面级问题（不在此处检测，移至 experience-map）**：
- 同一操作在多个界面重复 → 由 experience-map 的 `REDUNDANT_ENTRY` flag 处理
- 高风险操作没有二次确认 → 由 experience-map 的 `HIGH_RISK_NO_CONFIRM` flag 处理

只标记，不修改，最终决定由用户做出。

**CRUD 缺口建议**：检测到 CRUD 缺口时，除了标记问题，同时给出建议的补充任务描述（任务名 + 所属角色 + 建议的 main_flow），供用户评估是否纳入。用户确认后，纳入的任务追加到 `task-inventory.json` 并更新 decisions.json。

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "conflicts": [
    {
      "id": "C001",
      "type": "CONFLICT",
      "description": "T001 要求金额提交后不可修改，T003 退款编辑允许修改金额",
      "affected_tasks": ["T001", "T003"],
      "severity": "高",
      "confirmed": false
    }
  ],
  "crud_gaps": [
    {
      "id": "CG001",
      "type": "CRUD_INCOMPLETE",
      "description": "T001 main_flow 只有创建和提交，缺少撤回/修改流程",
      "affected_tasks": ["T001"],
      "severity": "中",
      "confirmed": false,
      "suggested_task": {
        "name": "撤回退款申请",
        "owner_role": "R001",
        "main_flow": ["选择待审核退款单", "确认撤回", "释放冻结金额", "通知审核人"]
      }
    }
  ]
}
```

**用户确认**：检测结果有没有误报？哪些 CRUD 缺口需要补充？

**quick 模式冲突处理**：跳过 Step 4（独立冲突检测）和 Step 5（约束识别），但 Step 9 Part 2 仍执行完整冲突扫描（覆盖 CROSS_ROLE_CONFLICT、STATE_DEADLOCK、IDEMPOTENCY_CONFLICT）。quick 模式下 `conflict-report.json` 不生成，冲突结果仅出现在 `validation-report.json` 中。

输出：`.allforai/product-map/conflict-report.json`

---

### Step 5：约束识别

**与 Step 4 互不依赖，可并行执行。**

识别两类约束：

**合规/审计要求**：操作留痕、数据可追溯、保留期限、导出需审批等

**业务约束**：不可逆操作、金额对账一致性、审批分级、SLA 硬限制等

**代码验证**（中型/大型产品推荐）：识别约束后，扫描代码验证哪些约束已有实现（如 bcrypt 密码哈希、GORM 软删除、定时任务自动确认收货等），在约束描述中标注实现状态：
- `"code_status": "implemented"` — 代码已实现
- `"code_status": "partial"` — 部分实现
- `"code_status": "missing"` — 代码未实现（潜在风险）

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "constraints": [
    {
      "id": "CN001",
      "type": "business",
      "description": "退款金额不可超过原订单金额",
      "affected_tasks": ["T001"],
      "enforcement": "hard",
      "code_status": "implemented",
      "confirmed": true
    },
    {
      "id": "CN002",
      "type": "compliance",
      "description": "所有退款操作必须留存操作日志，保留 3 年",
      "affected_tasks": ["T001", "T003"],
      "enforcement": "hard",
      "code_status": "missing",
      "confirmed": true
    }
  ]
}
```

**用户确认**：约束识别完整吗？有没有遗漏的隐性规则？代码实现状态是否准确？

输出：`.allforai/product-map/constraints.json`

---

### Step 6：输出产品地图报告

汇总前步骤的所有已确认数据，生成两个文件。

#### 预置脚本（优先使用）

检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_product_map.py` 是否存在：
- **存在** → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_product_map.py <BASE>`
- **不存在** → 回退到 LLM 生成（向后兼容）

预置脚本聚合 role-profiles + task-inventory + business-flows + 冲突报告 + 约束，生成 product-map.json + report + task-index + flow-index + SVG。

#### `product-map.json` / 报告 / SVG / 索引

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/product-map-output.md

输出：`.allforai/product-map/product-map.json`、`.allforai/product-map/product-map-report.md`、`.allforai/product-map/product-map-visual.svg`

写入 `.allforai/product-map/task-index.json`、`.allforai/product-map/flow-index.json`

---

### Step 7：数据建模

从任务清单、业务流、约束条件推导后端实体模型和 API 契约。

**预置脚本**：`${CLAUDE_PLUGIN_ROOT}/scripts/gen_data_model.py`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_data_model.py <BASE>
```

**推导逻辑**：
- 按 module 分组任务 → 每个 module 对应一个实体（Entity）
- 任务名关键词提取字段（价格→price:decimal，图片→images:file[]，状态→status:enum）
- 业务流节点顺序推导状态机（transitions）和实体关系（1:N）
- 约束条件映射到字段约束（"金额不能为负" → amount: min:0）
- CRUD 任务推导 REST API 契约（R→GET, C→POST, U→PUT, D→DELETE, 状态操作→PATCH）

**输出**：
- `.allforai/product-map/entity-model.json` — 实体模型（字段、类型、约束、状态机、关系）
- `.allforai/product-map/api-contracts.json` — API 契约（method, path, request/response schema）
- `.allforai/product-map/data-model-report.md` — 人类可读报告

**用户确认**：展示实体列表、字段数、API 数量，请用户审阅。

---

### Step 8：视图对象

从实体模型和 API 契约生成前端视图对象（View Object），每个 VO 对应一个界面视图。

**预置脚本**：`${CLAUDE_PLUGIN_ROOT}/scripts/gen_view_objects.py`

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_view_objects.py <BASE>
```

**推导逻辑**：
- 每个任务的 CRUD × 实体 → 一个 VO
  - R + 列表任务 → ListItemVO（interaction_type: MG2-L 或 MG1）
  - R + 详情任务 → DetailVO（interaction_type: MG2-D）
  - C 任务 → CreateFormVO（interaction_type: MG2-C）
  - U 任务 → EditFormVO（interaction_type: MG2-E）
  - 状态操作 → StateActionVO（interaction_type: MG3）
- 每个 VO 包含 Action Binding：按钮/链接与后端接口或本地操作的完整绑定
  - type: navigate（页面跳转）/ api_call（调用接口）/ local_storage（本地存储）
  - 前置条件、二次确认、输入表单、成功/失败行为

**输出**：
- `.allforai/product-map/view-objects.json` — 视图对象（字段、Action Binding、interaction_type）

**用户确认**：展示 VO 列表及类型分布，请用户审阅。如需审核数据模型全貌，可在 `/review` 统一审核站点的数据模型 tab 中查看。

---

### Step 9：校验

Step 6 完成后必须执行，所有模式均不可跳过。分三部分顺序执行，完成后统一展示，一次用户确认。

#### 预置脚本（优先使用）

检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_validation_report.py` 是否存在：
- **存在** → `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_validation_report.py <BASE>`
- **不存在** → 回退到 LLM 生成（向后兼容）

预置脚本执行 Part 1（完整性扫描）和 Part 2（冲突重扫），输出 validation-report.json + .md。Part 3（竞品差异）需要 WebSearch，由 LLM 补充执行。

#### Part 1：完整性扫描

遍历 `task-inventory.json` 所有任务，按字段层级分级检查：

**ERROR 级（required 字段缺失）**：

| 检查项 | Flag |
|--------|------|
| `main_flow` 为空或缺失 | `MISSING_MAIN_FLOW` |
| `owner_role` 缺失 | `MISSING_OWNER` |
| `frequency` 或 `risk_level` 缺失 | `MISSING_PRIORITY` |

**WARNING 级（recommended 字段缺失，仅高频+高风险任务）**：

| 检查项 | Flag |
|--------|------|
| `exceptions` 为空或缺失 | `MISSING_EXCEPTIONS` |
| `acceptance_criteria` 少于 3 条 | `THIN_AC` |
| `rules` 为空 | `MISSING_RULES` |

**INFO 级（recommended 字段缺失，中低频任务）**：

| 检查项 | Flag |
|--------|------|
| `exceptions` 为空或缺失 | `INFO_MISSING_EXCEPTIONS` |
| `acceptance_criteria` 少于 3 条 | `INFO_THIN_AC` |
| `value` 字段缺失 | `INFO_MISSING_VALUE` |

**展示规则**：ERROR 级全部列出；WARNING 级列出具体任务；INFO 级仅展示统计数字（如「另有 X 个中低频任务缺少 exceptions，属于 INFO 级」）。

#### Part 2：冲突重扫

基于完整地图重扫，比 Step 4 覆盖更广：

| 冲突类型 | Flag | 说明 |
|----------|------|------|
| 跨角色规则矛盾 | `CROSS_ROLE_CONFLICT` | A 角色的规则和 B 角色的规则互相冲突 |
| 状态流转死锁 | `STATE_DEADLOCK` | 任务 A 的输出状态被任务 B 的规则拒绝 |
| 幂等规则不一致 | `IDEMPOTENCY_CONFLICT` | 两个任务对同一对象的幂等规则不一致 |

#### Part 3：竞品差异（`competitors` 非空时执行）

Web 搜索加载各竞品功能概况，与完整任务清单做 diff，生成三列。

**对比维度**：根据 `competitor-profile.json` 中的 `comparison_scope` 确定对比焦点：
- `platform_features`：对比平台级功能模块（如支付、物流、CRM），以我方任务清单的功能模块为基准
- `user_experience`：对比用户交互体验（如搜索、推荐、下单流程）
- `business_model`：对比商业模式（如佣金结构、会员体系、广告模式）
- `comprehensive`：全方位对比

Web 搜索策略：优先访问竞品官方功能页、官方帮助文档目录，其次参考第三方对比评测。
对比粒度：以任务清单中的 name 为基准单位。
搜索失败处理：若某竞品数据无法获取，记录 `"data_source": "unavailable"`，不中断 Part 3，其余竞品继续分析。

| 列 | 含义 | 用户决策 |
|----|------|----------|
| `we_have_they_dont` | 我们有竞品没有 | 确认是否作为差异化保留 |
| `they_have_we_dont` | 竞品有我们没有 | 评估是否补齐 |
| `both_have_different_approach` | 都有但做法不同 | 确认设计分歧方向 |

Web 搜索完成后，将竞品功能数据补全到 `competitor-profile.json`，`analysis_status` 改为 `"completed"`。

#### 用户确认

三部分结果合并展示，用户确认：
- 哪些完整性问题是真实问题（vs 误报）
- 哪些冲突需要处理
- 哪些竞品差距需要跟进

确认后将结果写入 `validation-report.json` 和 `validation-report.md`。

**回写**：Step 9 完成后，将校验结果回写到 `product-map.json` 的 `summary` 字段（`validation_issues`、`competitor_gaps`），确保汇总文件始终反映最新状态。

#### `validation-report.json` Schema

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schemas/validation-report-schema.md

输出：`.allforai/product-map/validation-report.json`、`.allforai/product-map/validation-report.md`、`.allforai/product-map/competitor-profile.json`（补全）

---

## 输出文件结构

```
.allforai/product-map/
├── role-profiles.json          # Step 1: 角色画像
├── task-inventory.json         # Step 2: 任务清单（全量，区分 required/recommended 字段）
├── task-inventory-basic.json   # Step 2: 基本功能（认证/支付/管理/支持等基础设施）
├── task-inventory-core.json    # Step 2: 核心功能（产品差异化价值功能）
├── business-flows.json         # Step 3: 业务流（含 INDEPENDENT_OPERATION 分类）
├── business-flows-report.md    # Step 3: 业务流摘要（人类可读）
├── business-flows-visual.svg   # Step 3: 业务流泳道图（Python 脚本生成）
├── conflict-report.json        # Step 4: 任务级冲突检测结果（含 CRUD 缺口建议）
├── constraints.json            # Step 5: 业务约束清单（含 code_status）
├── product-map.json            # Step 6: 汇总文件（供其他技能加载）
├── product-map-report.md       # Step 6: 可读报告
├── product-map-visual.svg      # Step 6: 角色-任务树（Python 脚本生成）
├── task-index.json             # Step 6: 任务索引（轻量，供下游两阶段加载）
├── flow-index.json             # Step 6: 业务流索引（轻量，供下游两阶段加载）
├── entity-model.json           # Step 7: 实体模型（字段、类型、约束、状态机、关系）
├── api-contracts.json          # Step 7: API 契约（method, path, request/response schema）
├── data-model-report.md        # Step 7: 数据建模报告（人类可读）
├── view-objects.json           # Step 8: 视图对象（字段、Action Binding、interaction_type）
├── product-map-decisions.json  # 用户决策日志（增量复用）
├── competitor-profile.json     # Step 0 写草稿（含 comparison_scope），Step 9 补全
├── validation-report.json      # Step 9：三合一校验结果（分 ERROR/WARNING/INFO 级）
├── validation-report.md        # Step 9：校验摘要（人类可读）
└── refresh-diff.md             # refresh 模式：新旧版本差异摘要
```

### decisions.json 通用格式

所有 `*-decisions.json` 文件使用统一格式，记录每个 Step 的用户确认结果：

```json
[
  {
    "step": "Step 1",
    "item_id": "R001",
    "item_name": "描述",
    "decision": "confirmed | modified | deferred | auto_audited",
    "reason": "用户备注（可选）",
    "decided_at": "2026-02-25T10:30:00Z"
  }
]
```

- `confirmed`：用户确认无修改
- `modified`：用户修改后确认（修改内容已写入对应输出文件）
- `deferred`：用户暂不决定，下次运行时重新提问
- `auto_audited`：自审计子步骤自动发现并补充（如代码路由审计发现的遗漏任务），已纳入输出但标记来源

**加载逻辑**：每个 Step 开始前检查 decisions.json，已 `confirmed` 或 `auto_audited` 的条目跳过确认直接沿用，`deferred` 的条目重新提问。

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **`product-map-decisions.json`**：加载时用 `python -m json.tool` 验证 JSON 合法性。解析失败 → 检查 `.bak` → 提示恢复或重新运行 `/product-map refresh`。
- **`product-concept.json`**（概念指导模式）：加载时验证 JSON 合法性 + `version` 字段有效。解析失败 → 退出概念指导模式，回退到标准模式并告知用户。

### 零结果处理
- **Step 2 提取 0 任务**：若非访谈模式（`analysis_mode != "interview"`）→ ⚠ 警告「代码路由/菜单/权限点均未识别到任何任务，可能是非标准框架」+ 建议切换为访谈模式（`analysis_mode: "interview"`）。
- **scope 模式匹配 0 任务**：明确告知「关键词 "{关键词}" 未匹配任何任务，请检查拼写或换关键词」，列出 task-inventory 中现有模块名供参考。

### 规模自适应
- 已有完整实现（见「规模适配」章节）。阈值：small ≤30 / medium 31–80 / large >80 任务。
- 各 Step 的交互策略已在「规模适配」章节详细定义，此处不重复。

### WebSearch 故障
- **Step 9 Part 3 竞品搜索**：工具不可用 → 告知用户「⚠ WebSearch 暂不可用，竞品差异分析无法执行」→ Part 3 标注 `analysis_status: "tool_unavailable"` 并跳过，Part 1 + Part 2 正常执行。
- **某竞品数据无法获取**：已有处理（`data_source: "unavailable"`），不中断其余竞品分析。

### 上游过期检测
- **`product-concept.json`**（概念指导模式）：加载时比较 `generated_at` 与 `product-map-decisions.json` 最新 `decided_at`。上游更新 → ⚠ 警告「产品概念文档在 product-map 上次运行后被更新，建议重新运行 /product-map refresh 以同步最新概念」。仅警告不阻断。

---

## 10 条铁律

### 1. 产品语言输出

输出全程使用业务语言，不出现接口地址、组件名、代码路径、前后端区分等工程术语。工程细节止于分析过程，不进入产品地图。

### 2. 角色为主线，任务必须完整

从"谁来用"出发，自顶向下展开。每个任务必须归属至少一个角色，且 required 字段必须完整。未被任何业务流引用的任务按 INDEPENDENT_OPERATION（独立操作）或 ORPHAN_TASK（疑似遗漏）分类处理，由用户决定是否纳入流。

### 3. 频次决定主次，任务分类驱动优先级

每个任务按 `frequency`（高/中/低）和 `risk_level`（高/中/低）分类。高频任务优先保证完整性（required + recommended 全填），高风险任务优先保证约束和审计覆盖。频次和风险由代码中的操作分布和业务规则客观推导，PM 可调整但需说明理由。

### 4. 只标不改，用户是权威

检测到 `CONFLICT` / `CRUD_INCOMPLETE`，只标记报告，不执行任何修改，最终决定由用户做出。PM 补充的业务视角无条件纳入；代码里有但 PM 说不需要的任务，标记 `user_removed`，不强行保留。

### 5. 产品地图独立可运行，但 experience-map 是必须的下一步

产品地图独立可运行，提供完整的功能语义：谁用、做什么、怎么做、有何异常、如何验收。`experience-map` 梳理界面、按钮和异常状态，是下游多个技能的必须输入：`feature-gap`、`use-case`、`feature-prune`、`ui-design`、`design-audit` 均依赖 experience-map 数据。当下游技能检测到 experience-map 不存在时，会自动触发 experience-map 运行。

### 6. Step 9 校验不可跳过

Step 9 是地图质量保障，在所有模式（包括 `quick`）下必须执行。校验发现的问题按 ERROR/WARNING/INFO 分级，由用户决定处理优先级；竞品差异只供参考，用户有权忽略。

### 7. Step 3 业务流建模不可跳过

Step 3 是链路完整性的基础，在所有模式（包括 `quick`）下必须执行。若当前系统没有任何跨角色或跨系统的业务链路，可以生成空流列表，但步骤本身必须执行以确认这一判断。

### 8. 每步确认，增量复用

每个 Step 完成后展示摘要，等待用户确认后才进入下一步，不跳步不合并。用户确认结果写入 `product-map-decisions.json`，下次运行自动复用，不重复询问已确认项。`refresh` 命令才清空决策缓存重跑。

**概念指导模式例外**：当 `product-concept.json` 存在时，确认环节缩减为「仅 gap 处确认」。无 gap 的步骤自动通过并记录 `"decision": "concept_guided"`。详见「概念指导模式」章节。

### 9. 规模适配，量体裁衣

根据产品规模自动调整交互策略。小型产品（≤30 任务）使用标准逐项确认；中型/大型产品（>30 任务）使用摘要确认 + 自审计，避免要求用户逐一审阅上百个任务。大文件必须使用脚本生成，不可直接用 Write 工具输出超长 JSON。

### 10. 生成即审计，自查先于人查

中型/大型产品在 Step 2 和 Step 3 完成后，必须执行自审计子步骤（代码路由扫描 / handoff 连续性验证），在请求用户确认前先自行检查遗漏。自审计发现的问题自动修复并标记为 `auto_audited`，减少用户审阅负担。
