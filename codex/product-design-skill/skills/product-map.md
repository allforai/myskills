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
version: "2.8.0"
---

# Product Map — 产品地图梳理

> 读代码了解现状，用 PM 语言呈现，建立"现状 + 期望"的完整产品地图

## 目标

以代码为输入、以 PM 视角为准绳，梳理产品的完整现状：

1. **谁在用** — 识别用户角色，明确权限边界和 KPI
2. **做了什么** — 按角色提取核心任务，标注频次、风险、跨部门依赖、异常与验收标准
3. **有没有问题** — 检测任务级冲突、规则矛盾、CRUD 缺口
4. **受什么约束** — 识别合规、审计、业务约束
5. **体验重心在哪** — 判断该产品是 `consumer`、`admin` 还是 `mixed`，让下游技能使用不同的设计与实现标准

---

## 定位

```
product-map（现状+方向）      experience-map（必须）            feature-gap（对齐视角）
项目现在有什么？应该有什么？   界面、按钮、异常状态梳理        地图说有的，现在有没有？
代码读现状，PM 定方向          以 task-inventory 为输入     以 product-map 为基准
输出产品地图（PM 语言呈现）    输出体验地图              输出缺口报告
```

**核心定位**：读代码了解现状，用 PM 语言呈现，让 PM 确认并补充业务视角，最终形成"现状 + 期望"的完整产品地图，用于指导项目未来发展方向。

**后续技能依赖**：`feature-gap`、`seed-forge` 均以 `.allforai/product-map/product-map.json` 为输入基准，无需重复分析。界面交互细节由 `experience-map` 技能单独梳理（必须运行，下游多个技能依赖其数据）。

### 用户端优先级判定（新增全局指导思想）

product-map 必须在早期输出一个全局判断，供后续所有技能消费，而不是等到 UI 阶段才临时决定：

```json
"experience_priority": {
  "mode": "consumer | admin | mixed",
  "consumer_surface": true,
  "consumer_core": true,
  "primary_experience": "mobile | web-customer | admin | mixed",
  "reasoning": [
    "核心价值主要通过用户端持续使用获得",
    "后台主要承担配置、审核、运营支撑"
  ]
}
```

判定规则：

- `consumer`：核心价值主要发生在用户端，后台只是支撑
- `admin`：核心价值主要发生在后台或专业操作端
- `mixed`：两端都重要，但用户端仍需单独做成熟度检查

如果存在移动端/C 端主界面，默认必须显式判断，禁止跳过。

---

## 快速开始

```
/product-map              # 完整流程（Step 0-9，无界面梳理）
/product-map quick        # 跳过冲突检测（Step 4）和约束识别（Step 5）
/product-map refresh      # 重新采集，忽略已有缓存
/product-map scope 用户管理  # 只梳理指定功能模块
```

## 增强协议（网络搜索 + 4D+6V + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**搜索关键词**：`"story mapping" + 行业词 + "best practices" + 2025`

**4D+6V 重点**：每个任务补充 `source_refs`、`constraints`、`decision_rationale`；`task-inventory.json` 作为下游锚点，优先保证"可追溯 + 可解释"。

**下游基线定义**：

> 详见 `./docs/skill-commons.md`「上游基线验收」。

product-map 的产出同时是 journey-emotion 和 experience-map 的**验收基线**：

- **→ journey-emotion**：LLM 生成情绪标注后，用 business-flows.json 对照审查——每条业务流的每个节点是否有情绪标注？异常分支（exceptions）是否标注了负面情绪？independent_operations 是否也有对应旅程线？
- **→ experience-map**：LLM 设计界面后，用 task-inventory.json 对照审查——每个任务是否被至少一个界面覆盖？entity-model 中的状态机是否在对应界面的 states 中体现？

product-map 的质量（任务描述的具体程度、业务流节点的完整性、数据模型的字段覆盖）直接决定下游基线验收的精度。

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
| Step 2 生成 | 直接写入文件 | **必须使用脚本生成**（Python/Node），避免 单次输出超限 |
| Step 2 确认 | 展示完整任务表 | 展示角色×任务数摘要 + 审计发现的差异 |
| Step 3 确认 | 展示完整流列表 | 展示流摘要 + 自动检测的缺口 |
| Step 2/3 自审计 | 跳过（人工可覆盖） | **强制执行**自审计子步骤 |
| Step 9 完整性 | 逐项列出 | 仅列出 required 字段的缺失（推荐字段归为 INFO） |

**脚本生成指南**（中型/大型产品必读）：

当任务数 > 30 时，`task-inventory.json` 通常超过 单次输出限制。此时必须：
1. 先生成一个 Python/Node 脚本（如 `gen_tasks.py`）
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

## 用户端导向原则（全流程下游基线）

当 `experience_priority.mode = consumer` 或 `mixed` 时，product-map 不得只把用户端看成”功能入口集合”，而要把它看成”持续体验载体”。此时任务梳理必须额外覆盖：

- 主线任务闭环：用户打开应用后，不需要思考”我该做什么”——首页直接展示个性化的下一步动作，完成后有结果反馈，反馈中包含再下一步引导（不是回到列表页）
- 回访理由：提醒、进度、历史、订阅、推荐、连续状态——至少 2 项形成独立任务（不是附属在 CRUD 任务里的一句话）
- 状态机厚度：核心对象不只是”创建→查看”，而是有完整生命周期（草稿/处理中/完成/失败/恢复/归档），每个状态转换是独立的产品场景
- 关系网络：谁发起、谁反馈、谁确认、谁收到通知——每种关系产生独立的信息流（不只是数据库外键）
- 移动端场景：碎片时间、单手操作、弱网、即时反馈
- 首次体验：新用户首次打开不是直接进空白首页，而是有引导流程（目标设定/偏好收集/个性化准备）——这是独立任务，不是注册的附属步骤

### 多模型 Consumer 体验补全（Step 2 之后、Step 3 之前，OpenRouter 可用时必做）

> **核心思想**：单模型生成任务时容易陷入”功能思维”（我需要什么 API），第二模型从”用户思维”（我打开这个 App 会做什么）独立生成体验要素清单，两份清单合并后才进入业务流生成。这不是验审，是**对抗式共创**。

**触发条件**：experience_priority.mode = consumer 或 mixed **且** OpenRouter MCP 可用

**执行**：

Step 2 的 task-inventory 初稿生成后，**为每类需要留存的核心用户角色**分别向第二模型发送 prompt（多角色则并行发送多次）：

从 role-profiles.json 筛选”需要被留存的用户角色”（通常 1-3 个，如买家/达人/司机），每个角色一次调用：

```
你是一个 {产品类型} 产品的 {角色名}（不是开发者）。
你的身份：{角色一句话描述}
产品定位：{product-concept 一句话描述}
竞品参考：{concept 中的竞品或 LLM 推断的同类产品}

想象你第一次使用这个产品，从注册到成为日活用户的完整旅程。
请列出你期望的体验要素（不是功能列表，是”我作为这个角色会经历什么”）：

1. 首次打开时我会经历什么？
2. 我每天打开它的理由是什么？
3. 完成核心操作后我会看到什么？
4. 什么机制让我明天还想回来？
5. 我会怎么向同行介绍这个产品？

回复 JSON: {“role”: “{角色名}”, “user_journey_expectations”: [{“moment”: “首次打开”, “expectation”: “...”}, ...]}
```

调用（并行，每角色一次）：`OpenRouter MCP ask_model(task: “user_perspective_{role}”, prompt: 上述)`

**合并**：LLM（Claude）将所有角色的 expectations 汇总，逐条对比 task-inventory 初稿：
- 第二模型提到但 task-inventory 未覆盖的体验要素 → 转化为独立产品任务，补入 task-inventory
- 第二模型提到且 task-inventory 已覆盖 → 确认，不重复
- 第二模型的建议明显超出产品范围 → 忽略，记录到 pipeline-decisions.json
- 不同角色的 expectations 冲突 → 记录，由 Claude 判断取舍

> OpenRouter 不可用 → 跳过此步，回退到纯自审模式（输出 `多模型补全 ⊘ OpenRouter 不可用`）
> 角色数 > 3 → 只取前 3 个最核心角色（按 role-profiles 的 user_count 或 frequency 排序）

### 用户端专项自检（Step 2 / Step 3 之后，多模型补全的兜底）

若判定为 `consumer` 或 `mixed`，必须额外自检：

- 用户端任务是否只有”浏览/提交/查看”三板斧，没有持续关系？
- 核心对象是否只有 CRUD，没有生命周期？
- 是否缺少提醒、历史、进度、通知、回访触发点？
- 是否只有概念映射，没有成熟产品闭环？

发现以上问题时，不要等下游修补，直接在 product-map 补厚任务定义与业务流。

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 步骤 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Step 0 竞品提问** | 询问用户竞品信息 | 读 `pipeline_preferences.competitors`：非空 → 直接填充 `competitor-profile.json`，跳过提问；空 → 记录 `competitors: []`，Step 9 Part 3 跳过竞品差异 |
| **Step 0 画像确认** | 向用户确认 | 自动确认，记入 `pipeline-decisions.json`（`decision: "auto_confirmed"`） |
| **Step 1 角色确认** | 向用户确认 | 自动确认 |
| **Step 2 任务确认** | 向用户确认 | 自动确认 |
| **Step 3 业务流确认** | 向用户确认 | 自动确认 |
| **Step 4 冲突确认** | 向用户确认 | 自动确认（冲突记录到 decisions.json） |
| **Step 5 约束确认** | 向用户确认 | 自动确认 |
| **Step 6.5 体验基因** | 向用户确认 | 自动确认（DIFF 数 = 0 → 停下来问用户） |
| **Step 7 数据建模** | 向用户确认 | 自动确认 |
| **Step 8 视图对象** | 向用户确认 | 自动确认 |
| **Step 9 校验** | 向用户确认 | ERROR 级问题（必填字段缺失、引用断裂）→ **停下来问用户**；WARNING/INFO → 记日志自动继续 |

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
Step 6.5: Experience DNA 体验基因
      从产品地图 + 竞品画像 + 机制决策中提取差异化体验契约
      → 生成 experience-dna.json
      → 输出进度「Step 6.5 体验基因 ✓ {N} 差异化契约 (core:{C} defensible:{D})」（不停）
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

## Step 详细定义（按阶段加载）

详细的 Step 定义拆分到以下文件中，执行到对应阶段时加载：

| 文件 | 包含步骤 | 加载时机 |
|------|----------|----------|
| `docs/product-map/extraction-steps.md` | Step 0（项目画像）、Step 1（角色识别）、Step 2（任务提取） | 流程开始时加载 |
| `docs/product-map/modeling-steps.md` | Step 3（业务流）、Step 4（冲突检测）、Step 5（约束识别）、Step 6（报告输出）、Step 6.5（体验基因） | Step 2 完成后加载 |
| `docs/product-map/data-modeling-steps.md` | Step 7（数据建模）、Step 8（视图对象） | Step 6.5 完成后加载 |
| `docs/product-map/validation-steps.md` | Step 9（校验） | Step 8 完成后加载 |

**加载方式**：读取 `./docs/product-map/<filename>` 获取当前阶段的完整步骤定义。每个子文件是自包含的，包含该阶段所有步骤的完整 schema、示例、审计规则和输出规范。

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
├── experience-dna.json         # Step 6.5: 体验基因（差异化契约、过渡仪式、反模式）
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

### 网络搜索不可用
- **Step 9 Part 3 竞品搜索**：工具不可用 → 告知用户「⚠ 网络搜索暂不可用，竞品差异分析无法执行」→ Part 3 标注 `analysis_status: "tool_unavailable"` 并跳过，Part 1 + Part 2 正常执行。
- **某竞品数据无法获取**：已有处理（`data_source: "unavailable"`），不中断其余竞品分析。

### 上游过期检测
- **`product-concept.json`**（概念指导模式）：加载时比较 `generated_at` 与 `product-map-decisions.json` 最新 `decided_at`。上游更新 → ⚠ 警告「产品概念文档在 product-map 上次运行后被更新，建议重新执行 product-map refresh 以同步最新概念」。仅警告不阻断。

### 执行失败保护

- 任何步骤遇到不可恢复错误 → 写入 `.allforai/product-map/product-map-error.json`，包含 `{"error": "...", "step": "...", "timestamp": "..."}`。

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

产品地图独立可运行，提供完整的功能语义：谁用、做什么、怎么做、有何异常、如何验收。`experience-map` 梳理界面、按钮和异常状态，是下游多个技能的必须输入：`feature-gap`、`use-case`、`ui-design`、`design-audit` 均依赖 experience-map 数据。当下游技能检测到 experience-map 不存在时，会自动触发 experience-map 运行。

### 6. Step 9 校验不可跳过

Step 9 是地图质量保障，在所有模式（包括 `quick`）下必须执行。校验发现的问题按 ERROR/WARNING/INFO 分级，由用户决定处理优先级；竞品差异只供参考，用户有权忽略。

### 7. Step 3 业务流建模不可跳过

Step 3 是链路完整性的基础，在所有模式（包括 `quick`）下必须执行。若当前系统没有任何跨角色或跨系统的业务链路，可以生成空流列表，但步骤本身必须执行以确认这一判断。

### 8. 每步确认，增量复用

每个 Step 完成后展示摘要，等待用户确认后才进入下一步，不跳步不合并。用户确认结果写入 `product-map-decisions.json`，下次运行自动复用，不重复询问已确认项。`refresh` 命令才清空决策缓存重跑。

**概念指导模式例外**：当 `product-concept.json` 存在时，确认环节缩减为「仅 gap 处确认」。无 gap 的步骤自动通过并记录 `"decision": "concept_guided"`。详见「概念指导模式」章节。

### 9. 规模适配，量体裁衣

根据产品规模自动调整交互策略。小型产品（≤30 任务）使用标准逐项确认；中型/大型产品（>30 任务）使用摘要确认 + 自审计，避免要求用户逐一审阅上百个任务。大文件必须使用脚本生成，不可直接输出超长 JSON。

### 10. 生成即审计，自查先于人查

中型/大型产品在 Step 2 和 Step 3 完成后，必须执行自审计子步骤（代码路由扫描 / handoff 连续性验证），在请求用户确认前先自行检查遗漏。自审计发现的问题自动修复并标记为 `auto_audited`，减少用户审阅负担。
