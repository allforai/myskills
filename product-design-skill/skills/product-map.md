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
version: "2.5.0"
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
product-map（现状+方向）      screen-map（可选增强）        feature-gap（对齐视角）      feature-prune（决策视角）
项目现在有什么？应该有什么？   界面、按钮、异常状态梳理        地图说有的，现在有没有？      地图里有的，该不该留？
代码读现状，PM 定方向          以 task-inventory 为输入     以 product-map 为基准        以 product-map 为锚点
输出产品地图（PM 语言呈现）    输出界面交互地图              输出缺口报告                 输出剪枝报告
```

**核心定位**：读代码了解现状，用 PM 语言呈现，让 PM 确认并补充业务视角，最终形成"现状 + 期望"的完整产品地图，用于指导项目未来发展方向。

**后续技能依赖**：`feature-gap`、`feature-prune`、`seed-forge` 均以 `.allforai/product-map/product-map.json` 为输入基准，无需重复分析。界面交互细节由 `screen-map` 技能（可选）单独梳理。

---

## 快速开始

```
/product-map              # 完整流程（Step 0-7，无界面梳理）
/product-map quick        # 跳过冲突检测（Step 4）和约束识别（Step 5）
/product-map refresh      # 重新采集，忽略已有缓存
/product-map scope 退款管理  # 只梳理指定功能模块
```

## 动态趋势补充（WebSearch）

除经典理论外，执行本技能时建议补充近 12–24 个月的实践文章/案例：

- 搜索关键词示例：`"story mapping" + 行业词 + "best practices" + 2025`
- 来源优先级：官方规范/权威研究 > 一线产品团队实践 > 社区文章
- 决策留痕：记录“是否采纳 + 理由”，避免只收集不决策

建议将来源写入：`.allforai/product-design/trend-sources.json`（跨阶段共用）。

## 中段经理理论支持（可选增强，不破坏现有流程）

为保证「概念 → 功能点 → 交互」阶段具备可审计的产品管理依据，product-map 可叠加以下理论锚点：

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|----------|----------|
| Story Mapping（Jeff Patton） | Step 2/3 | 任务按用户活动流分层：主干活动（backbone）→ 任务切片（slice）→ 版本范围 |
| RACI 职责矩阵 | Step 1/2 | 在角色与任务关系中明确 Responsible / Accountable / Consulted / Informed，减少角色边界冲突 |
| 风险矩阵（Impact × Probability） | Step 2/5 | 将 risk_level 的判定从主观高/中/低，改为可解释的概率×影响分档 |
| DoR（Definition of Ready） | Step 7 | 将 required 字段完整性视为进入下游（screen-map/use-case）的就绪门槛 |

> 建议：默认沿用现有流程；当团队需要更强「产品管理可追溯性」时启用本增强。

**scope 模式**：运行与 full 相同的 Step 序列，但在前置加载后先按关键词过滤 — 匹配 `task-inventory.json` 中 `task_name` 包含该关键词的任务，以及这些任务关联的角色和场景。后续所有 Step 仅处理过滤后的子集。输出文件中标注 `"scope": "{关键词}"`。若 `task-inventory.json` 尚不存在（首次运行），scope 过滤延迟到 Step 2 完成后执行，Step 0–2 按完整范围运行。

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
| Step 7 完整性 | 逐项列出 | 仅列出 required 字段的缺失（推荐字段归为 INFO） |

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
| **Step 7 校验** | 用户确认校验结果 | 跳过竞品差异（concept 已有 competitive_position），**仅在 ERROR 级问题处暂停确认**，WARNING/INFO 自动记录 |

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
Step 7: 校验
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
- **有竞品**：记录名字列表和对比维度，生成 `competitor-profile.json` 草稿（写名字 + `comparison_scope`），Step 7 再做 Web 搜索
- **无竞品**：记录 `competitors: []`，`analysis_status` 设为 `"skipped"`，Step 7 只做完整性 + 冲突校验，跳过竞品差异部分

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

> 草稿此时只写入名字和对比维度，Step 7 执行完后补全竞品功能数据，`analysis_status` 改为 `"completed"`。
> `analysis_status` 取值：`"pending"`（待分析）/ `"skipped"`（无竞品，Step 7 跳过竞品差异）/ `"completed"`（已完成）
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

标记角色面向的用户群体，供 screen-map 选择交互设计标准。

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
| **required** | `id`, `task_name`, `owner_role`, `frequency`, `risk_level`, `main_flow`, `status` | 任务身份和核心属性，缺失将导致下游技能无法正常工作 |
| **recommended** | `value`, `approver_role`, `viewer_roles`, `cross_dept`, `cross_dept_roles`, `sla`, `prerequisites`, `rules`, `config_items`, `inputs`, `outputs`, `exceptions`, `audit`, `acceptance_criteria` | 丰富任务语义，提升地图质量，但非强制 |

**生成策略**：
- **小型产品（≤30 任务）**：尽量填写所有字段，包括 recommended
- **中型/大型产品（>30 任务）**：优先保证所有 required 字段完整；recommended 字段按优先级填写：高频+高风险任务填写全部 recommended 字段，中低频任务至少填写 `rules` 和 `exceptions`

#### 任务 Schema

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "tasks": [
    {
      "id": "T001",
      "task_name": "创建并提交退款单",
      "value": "把退款申请从线下表格改为系统闭环，减少漏审与重复退款",
      "owner_role": "R001",
      "approver_role": "R002",
      "viewer_roles": ["R003"],
      "frequency": "高",
      "risk_level": "高",
      "cross_dept": true,
      "cross_dept_roles": ["财务", "仓储"],
      "sla": "24h 内处理",
      "prerequisites": ["已有订单", "有退款申请权限", "订单状态为已支付"],
      "main_flow": [
        "选择订单",
        "自动带出支付信息",
        "填写退款原因与金额",
        "校验（≤ 可退金额）",
        "提交 → 进入财务待审",
        "通知财务审核"
      ],
      "rules": [
        "同订单同原因 30 分钟内幂等，不重复创建",
        "金额变更需二次确认弹窗",
        "金额 ≥ 5000 触发主管复核流程"
      ],
      "config_items": [
        {"param": "幂等窗口时长", "current": "30分钟", "config_level": "general_config"},
        {"param": "触发复核的金额阈值", "current": "5000", "config_level": "general_config"}
      ],
      "inputs": {
        "fields": ["订单编号", "退款原因", "退款金额"],
        "defaults": { "退款金额": "原支付金额" }
      },
      "outputs": {
        "states": ["财务待审"],
        "messages": ["退款单已提交，财务将在 24h 内处理"],
        "records": ["退款单据"],
        "notifications": ["财务审核通知"]
      },
      "exceptions": [
        "订单已全额退款 → 提示不可重复退款",
        "支付信息缺失 → 提示联系技术支持",
        "权限不足 → 提示申请权限",
        "审批超时 48h → 自动升级到上级"
      ],
      "audit": {
        "recorded_actions": ["创建", "修改", "提交", "审批", "驳回"],
        "fields_logged": ["退款金额变更前后值", "退款原因", "操作人", "时间"]
      },
      "acceptance_criteria": [
        "超额退款不可提交并提示可退金额",
        "30 分钟内重复提交自动去重",
        "金额 ≥ 5000 触发复核流程",
        "操作日志包含变更前后值"
      ],
      "status": "confirmed",
      "flags": []
    }
  ]
}
```

**任务字段说明**：

| 字段 | 层级 | 说明 |
|------|------|------|
| `id` | required | 全局唯一任务标识（如 T001） |
| `task_name` | required | 动词 + 对象 + 结果（可操作动作，不用空词） |
| `owner_role` | required | 主操作角色 |
| `frequency` | required | 高/中/低 |
| `risk_level` | required | 高/中/低 |
| `main_flow` | required | 3–8 步，写到"可操作"粒度 |
| `status` | required | 任务状态：`confirmed` / `user_added` / `user_removed` |
| `value` | recommended | 解决什么问题/提升什么指标（一句话） |
| `approver_role` | recommended | 审批角色（无审批流则省略） |
| `viewer_roles` | recommended | 只读角色列表 |
| `cross_dept` | recommended | 是否跨部门（boolean） |
| `cross_dept_roles` | recommended | 跨部门涉及的角色列表 |
| `sla` | recommended | 服务等级目标时限 |
| `prerequisites` | recommended | 权限/数据状态/依赖配置前置条件 |
| `rules` | recommended | 校验、权限、状态流转、计算口径 |
| `config_items` | recommended | 可配置参数列表（见下方「配置级别」章节） |
| `inputs` | recommended | 输入字段和默认值 |
| `outputs` | recommended | 输出状态、消息、单据、通知 |
| `exceptions` | recommended | 失败提示/修复；撤回/幂等/重复提交；不可逆说明 |
| `audit` | recommended | 哪些操作被记录、记录哪些字段 |
| `acceptance_criteria` | recommended | 3–10 条可验证的验收标准 |
| `flags` | metadata | 问题标记：`CONFLICT` / `CRUD_INCOMPLETE`（空表示无问题） |

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
- Step 7 校验时，检查所有 `general_config` 参数是否被 R007（或同等管理员角色）的「配置系统参数」任务覆盖

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

**用户确认**：任务清单完整吗？审计发现的遗漏是否都应纳入？

输出：`.allforai/product-map/task-inventory.json`

---

### Step 3：业务流建模

Step 2 完成后执行，所有模式均不可跳过。

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
4. **展示审计结果**：在用户确认前，展示「自审计发现 X 个断裂交接 / X 个缺失终止节点 / X 个高频孤立任务」

#### 用户确认

展示候选流 + 识别到的缺口 + 自审计结果，用户可：
- 确认/修改候选流
- 补充未被识别的跨系统节点
- 确认孤立任务分类（INDEPENDENT_OPERATION vs ORPHAN_TASK）

确认后写入 `business-flows.json` 和 `business-flows-report.md`。

#### `business-flows.json` Schema

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "generated_at": "2026-02-25T10:00:00Z",
  "systems": {
    "current": "user-app",
    "linked": [
      {
        "name": "merchant-backend",
        "task_inventory_path": "/path/to/.allforai/product-map/task-inventory.json",
        "loaded": true
      }
    ]
  },
  "flows": [
    {
      "id": "F001",
      "name": "售后全链路",
      "description": "用户发起售后申请到最终处理完成的完整业务链路",
      "systems_involved": ["user-app", "merchant-backend"],
      "nodes": [
        {
          "seq": 1,
          "name": "用户发起售后申请",
          "task_ref": "user-app:T001",
          "role": "买家",
          "handoff": null,
          "gap": false
        },
        {
          "seq": 2,
          "name": "商户收到售后通知",
          "task_ref": "merchant-backend:T015",
          "role": "商户",
          "handoff": {
            "mechanism": "webhook",
            "data": ["售后单 ID", "买家 ID", "金额", "原因"]
          },
          "gap": false
        }
      ],
      "gap_count": 0,
      "confirmed": false
    }
  ],
  "summary": {
    "flow_count": 2,
    "flow_gaps": 1,
    "orphan_tasks": ["T008"],
    "independent_operations": ["T025", "T030"]
  }
}
```

#### `business-flows-report.md` 结构（摘要级）

```
# 业务流报告

2 条业务流 · 1 个流缺口 · 1 个孤立任务 · 2 个独立操作

## 业务流列表
- F001 售后全链路（user-app + merchant-backend）— 1 个缺口
- F002 订单支付链路（user-app）— 0 个缺口

## 流缺口
- F001 节点4：user-app:T002（用户查看处理结果）— MISSING_TASK

## 孤立任务（可能遗漏建模，需确认）
- T008 批量导出订单 — 请确认是否需要加入某条流

## 独立操作（无需纳入流）
- T025 管理收货地址
- T030 修改个人资料

> 完整数据见 .allforai/product-map/business-flows.json
```

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

**界面级问题（不在此处检测，移至 screen-map）**：
- 同一操作在多个界面重复 → 由 screen-map 的 `REDUNDANT_ENTRY` flag 处理
- 高风险操作没有二次确认 → 由 screen-map 的 `HIGH_RISK_NO_CONFIRM` flag 处理

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
        "task_name": "撤回退款申请",
        "owner_role": "R001",
        "main_flow": ["选择待审核退款单", "确认撤回", "释放冻结金额", "通知审核人"]
      }
    }
  ]
}
```

**用户确认**：检测结果有没有误报？哪些 CRUD 缺口需要补充？

**quick 模式冲突处理**：跳过 Step 4（独立冲突检测）和 Step 5（约束识别），但 Step 7 Part 2 仍执行完整冲突扫描（覆盖 CROSS_ROLE_CONFLICT、STATE_DEADLOCK、IDEMPOTENCY_CONFLICT）。quick 模式下 `conflict-report.json` 不生成，冲突结果仅出现在 `validation-report.json` 中。

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

#### `product-map.json` — 结构化汇总（供下游技能加载）

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "generated_at": "2026-02-24T10:00:00Z",
  "version": "2.4.0",
  "scope": "full",
  "scale": "large",
  "summary": {
    "role_count": 3,
    "task_count": 24,
    "flow_count": 2,
    "flow_gaps": 1,
    "orphan_task_count": 1,
    "independent_operation_count": 5,
    "conflict_count": 1,
    "constraint_count": 5,
    "validation_issues": 5,
    "competitor_gaps": 3
  },
  "roles": [...],        // 来自 role-profiles.json
  "tasks": [...],        // 来自 task-inventory.json
  "conflicts": [...],    // 来自 conflict-report.json（quick 模式为空数组）
  "constraints": [...]   // 来自 constraints.json（quick 模式为空数组）
  // flows 独立存储于 business-flows.json，此处不嵌入
}
```

`summary` 字段供下游技能（feature-gap、feature-prune、seed-forge）快速获取产品规模，无需遍历全部数组。

下游技能以此文件为主输入，同时按需加载 `business-flows.json`（业务流数据独立存储）。

#### `product-map-report.md` — 可读摘要（给人看）

报告结构：

```
# 产品地图摘要

角色 X 个 · 任务 X 个 · 高频任务 X 个 · 冲突 X 个 · 约束 X 条

## 角色总览
| 角色 | 职责 | KPI |
|------|------|-----|
| （每角色一行） | | |

## 高频任务（Top 20%）
- T001 任务名（高频 / 高风险 / 跨部门）
- T005 任务名（高频 / 低风险）

## 冲突摘要
- C001 描述（高）

## 业务约束摘要
- CN001 描述（硬约束）

## 下一步建议
- 运行 /screen-map 梳理界面、按钮和异常状态（可选）
- 运行 /use-case 生成用例集（可选）
- 运行 /feature-gap 检测功能缺口
- 运行 /feature-prune 评估功能去留

> 完整数据见 .allforai/product-map/product-map.json
```

输出：`.allforai/product-map/product-map.json`、`.allforai/product-map/product-map-report.md`

#### SVG 生成：product-map-visual.svg

`product-map-report.md` 写入磁盘后，生成 `.allforai/product-map/product-map-visual.svg`。

**生成方式**：使用 Python 脚本生成 SVG 文件。脚本读取 `role-profiles.json` 和 `task-inventory.json`，按以下设计意图生成角色-任务树状图：

**设计意图**：
- 左侧角色框，右侧任务框，折线连接
- 任务按 frequency 颜色区分：高频绿色、中频黄色、低频灰色
- 高风险任务标注红色徽章，跨部门任务标注紫色徽章，有冲突标记橙色三角
- 画布高度自适应任务数量

**颜色规范**：

| 元素 | 颜色 |
|------|------|
| 角色框 | fill `#3B82F6`，白色文字 |
| 任务框·frequency="高" | fill `#22C55E`，白色文字 |
| 任务框·frequency="中" | fill `#F59E0B`，白色文字 |
| 任务框·frequency="低" | fill `#9CA3AF`，白色文字 |
| 风险徽章（risk_level="高"） | fill `#EF4444` |
| 跨部门徽章（cross_dept=true） | fill `#8B5CF6` |
| 冲突标记（flags 不为空） | fill `#F97316` |
| 连线 | stroke `#CBD5E1` |

**图例**：画布顶部横向排列色块 + 说明文字：高频/中频/低频/高风险/跨部门/冲突

写入 `.allforai/product-map/product-map-visual.svg`

#### 索引文件生成

`product-map-visual.svg` 写入后，立即生成两个轻量索引文件，供下游技能两阶段加载使用。

##### `task-index.json`

从 `task-inventory.json` 提取关键字段，按模块分组。模块归组方法：按 `task_name` 中的首个名词短语（如「退款管理」「订单查询」）进行语义聚类，与 `use-case` 的功能区分组逻辑一致。

```json
{
  "generated_at": "2026-02-25T10:00:00Z",
  "source": "task-inventory.json",
  "task_count": 24,
  "modules": [
    {
      "name": "退款管理",
      "tasks": [
        {
          "id": "T001",
          "task_name": "创建并提交退款单",
          "frequency": "高",
          "owner_role": "R001",
          "risk_level": "高"
        }
      ]
    }
  ]
}
```

##### `flow-index.json`

从 `business-flows.json` 提取关键字段。

```json
{
  "generated_at": "2026-02-25T10:00:00Z",
  "source": "business-flows.json",
  "flow_count": 2,
  "flows": [
    {
      "id": "F001",
      "name": "售后全链路",
      "node_count": 4,
      "gap_count": 1,
      "roles": ["买家", "商户"]
    }
  ]
}
```

**生成规则**：
- 索引随 Step 6 输出一起生成，时间戳与 `product-map.json` 的 `generated_at` 一致
- `scope` 模式下索引仍生成完整内容（不按 scope 过滤），确保下游技能自行筛选
- 下游技能加载索引时若发现索引不存在，回退到全量加载，行为与旧版完全一致

写入 `.allforai/product-map/task-index.json`、`.allforai/product-map/flow-index.json`

---

### Step 7：校验

Step 6 完成后必须执行，所有模式均不可跳过。分三部分顺序执行，完成后统一展示，一次用户确认。

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
对比粒度：以任务清单中的 task_name 为基准单位。
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

**回写**：Step 7 完成后，将校验结果回写到 `product-map.json` 的 `summary` 字段（`validation_issues`、`competitor_gaps`），确保汇总文件始终反映最新状态。

#### `validation-report.json` Schema

> 以下示例以虚构业务为背景，仅用于说明输出格式。实际内容由 product-map 分析结果决定，不限行业。

```json
{
  "generated_at": "2026-02-24T12:00:00Z",
  "summary": {
    "error_issues": 0,
    "warning_issues": 3,
    "info_issues": 15,
    "conflict_issues": 2,
    "competitor_gaps": 4
  },
  "completeness": [
    {
      "task_id": "T001",
      "task_name": "创建并提交退款单",
      "level": "WARNING",
      "flags": ["THIN_AC"],
      "detail": "acceptance_criteria 只有 2 条，建议补充到 3 条以上",
      "confirmed": false
    }
  ],
  "conflicts": [
    {
      "id": "V001",
      "type": "CROSS_ROLE_CONFLICT",
      "description": "T001 规定退款金额提交后不可修改，T007（财务审核）允许审核时调整金额",
      "affected_tasks": ["T001", "T007"],
      "severity": "高",
      "confirmed": false
    }
  ],
  "competitor_diff": {
    "comparison_scope": "platform_features",
    "competitors_analyzed": ["Shopify", "有赞"],
    "we_have_they_dont": [
      {
        "feature": "退款单幂等去重",
        "our_task": "T001",
        "note": "差异化优势，建议保留",
        "confirmed": false,
        "decision": null
      }
    ],
    "they_have_we_dont": [
      {
        "feature": "批量退款",
        "competitor": "有赞",
        "note": "高频场景，建议评估是否补齐",
        "confirmed": false,
        "decision": null
      }
    ],
    "both_have_different_approach": [
      {
        "feature": "审批流",
        "our_approach": "固定两级审批",
        "their_approach": "动态多级审批（有赞）",
        "note": "设计分歧，需确认方向",
        "confirmed": false,
        "decision": null
      }
    ]
  }
}
```

**decision 有效值**：
- `we_have_they_dont`: `"keep_as_differentiator"` | `"reconsider"`
- `they_have_we_dont`: `"add_to_backlog"` | `"skip"`
- `both_have_different_approach`: `"keep_current"` | `"adopt_competitor"` | `"custom"`

#### `validation-report.md` 结构（摘要级，人类可读）

```
# 产品地图校验报告

ERROR X 个 · WARNING X 个 · INFO X 个（统计） · 冲突 X 个
竞品差距：竞品有我没有 X 个 / 我有竞品没有 X 个 / 做法不同 X 个

## ERROR 级问题（必须修复）
（无则显示「无 ERROR 级问题」）

## WARNING 级问题（建议修复）
- T001 THIN_AC：acceptance_criteria 只有 2 条
- T005 MISSING_EXCEPTIONS：exceptions 为空

## INFO 统计
- 另有 X 个中低频任务缺少 exceptions
- 另有 X 个中低频任务缺少 value

## 冲突问题
- V001 CROSS_ROLE_CONFLICT（高）：T001 vs T007，退款金额修改规则矛盾

## 竞品差异（对比维度：{comparison_scope}）
### 竞品有我们没有（潜在缺口）
- 批量退款（有赞）— 高频场景，建议评估

### 我们有竞品没有（差异化）
- 退款单幂等去重 — 差异化优势，建议保留

### 做法不同（设计分歧）
- 审批流：我们固定两级 vs 有赞动态多级 — 需确认方向

> 完整数据见 .allforai/product-map/validation-report.json
```

输出：`.allforai/product-map/validation-report.json`、`.allforai/product-map/validation-report.md`、`.allforai/product-map/competitor-profile.json`（补全）

---

## 输出文件结构

```
.allforai/product-map/
├── role-profiles.json          # Step 1: 角色画像
├── task-inventory.json         # Step 2: 任务清单（区分 required/recommended 字段）
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
├── product-map-decisions.json  # 用户决策日志（增量复用）
├── competitor-profile.json     # Step 0 写草稿（含 comparison_scope），Step 7 补全
├── validation-report.json      # Step 7：三合一校验结果（分 ERROR/WARNING/INFO 级）
├── validation-report.md        # Step 7：校验摘要（人类可读）
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
- **Step 7 Part 3 竞品搜索**：工具不可用 → 告知用户「⚠ WebSearch 暂不可用，竞品差异分析无法执行」→ Part 3 标注 `analysis_status: "tool_unavailable"` 并跳过，Part 1 + Part 2 正常执行。
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

### 5. 完整功能地图不依赖界面梳理

产品地图独立可运行，提供完整的功能语义：谁用、做什么、怎么做、有何异常、如何验收。`screen-map` 是可选增强层，梳理界面、按钮和异常状态；`feature-gap Step 2/3` 需要 screen-map 数据，但 `feature-gap Step 1`、`feature-prune`、`seed-forge` 可直接基于产品地图运行。

### 6. Step 7 校验不可跳过

Step 7 是地图质量保障，在所有模式（包括 `quick`）下必须执行。校验发现的问题按 ERROR/WARNING/INFO 分级，由用户决定处理优先级；竞品差异只供参考，用户有权忽略。

### 7. Step 3 业务流建模不可跳过

Step 3 是链路完整性的基础，在所有模式（包括 `quick`）下必须执行。若当前系统没有任何跨角色或跨系统的业务链路，可以生成空流列表，但步骤本身必须执行以确认这一判断。

### 8. 每步确认，增量复用

每个 Step 完成后展示摘要，等待用户确认后才进入下一步，不跳步不合并。用户确认结果写入 `product-map-decisions.json`，下次运行自动复用，不重复询问已确认项。`refresh` 命令才清空决策缓存重跑。

**概念指导模式例外**：当 `product-concept.json` 存在时，确认环节缩减为「仅 gap 处确认」。无 gap 的步骤自动通过并记录 `"decision": "concept_guided"`。详见「概念指导模式」章节。

### 9. 规模适配，量体裁衣

根据产品规模自动调整交互策略。小型产品（≤30 任务）使用标准逐项确认；中型/大型产品（>30 任务）使用摘要确认 + 自审计，避免要求用户逐一审阅上百个任务。大文件必须使用脚本生成，不可直接用 Write 工具输出超长 JSON。

### 10. 生成即审计，自查先于人查

中型/大型产品在 Step 2 和 Step 3 完成后，必须执行自审计子步骤（代码路由扫描 / handoff 连续性验证），在请求用户确认前先自行检查遗漏。自审计发现的问题自动修复并标记为 `auto_audited`，减少用户审阅负担。
