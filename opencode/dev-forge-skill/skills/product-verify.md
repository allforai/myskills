---
name: product-verify
description: >
  Use when the user wants to "verify product implementation", "acceptance test",
  "validate code against product map", "check if features are implemented",
  "static code coverage check", "dynamic browser testing", "Maestro mobile testing",
  "find unimplemented tasks",
  "find extra code not in product map", "产品验收", "静态验收", "动态验收",
  "代码是否实现了产品地图", "验证功能实现", "找漏实现的功能", "代码覆盖检查",
  "Maestro 移动端测试", "XCUITest iOS 测试",
  or wants to prove code implements the product map features and flows.
  Requires product-map to have been run first. Optionally uses experience-map and use-case.
version: "1.7.0"
---

# Product Verify — 产品验收

> 产品地图说应该有的，代码里真的实现了吗？行为符合预期吗？

## 目标

以 `product-map`（以及可选的 `experience-map`、`use-case`）为基准，回答两个问题：

1. **静态：代码有没有？** — 每个任务是否有对应的 API 路由？每个界面是否有对应的组件？每条约束是否有对应的校验逻辑？
2. **动态：行为对不对？** — 用 Playwright（Web）/ XCUITest（iOS 原生）/ Patrol（Flutter）/ Maestro（RN 原生）运行实际应用，用例脚本跑得通吗？

当 `product-map.json` 中的 `experience_priority.mode = consumer` 或 `mixed` 时，还要额外回答第三个问题：

3. **像成熟用户产品吗？** — 用户端是否只有功能壳子和概念映射，还是已经具备主线、反馈、状态系统、持续关系与移动端产品感

发现差异，生成三类任务清单：
- **IMPLEMENT** — 产品地图有但代码没有（漏实现）
- **REMOVE_EXTRA** — 代码有但产品地图没有（多余代码，自动建议 keep/remove）
- **FIX_FAILING** — 代码有但行为不符合预期（测试失败）

---

## 定位

```
product-map（现状+方向）   feature-gap（功能查漏）    product-verify（验收）
产品应该长什么样           地图说有的，现在有没有      代码实现了地图里的任务吗
基础层                    产品层比对                 代码层比对 + 运行时验证
不看代码                  不看代码                   扫描代码 + 跑浏览器 / 移动模拟器
```

**与 feature-gap 的区别**：feature-gap 检查**产品地图自身**是否完整（CRUD 齐不齐、旅程通不通）；product-verify 检查**代码**是否实现了产品地图中的任务（路由有没有、组件在不在、行为对不对）。一个审产品设计，一个审代码实现。

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。

若 `product-map.json` 含 `experience_priority`，product-verify 必须继承该字段，切换不同的验收标准。

---

## 快速开始

```
/product-verify           # 静态验收（默认，无需应用运行）
/product-verify static    # 同上，显式指定
/product-verify dynamic   # 动态验收（需要应用正在运行）
/product-verify full      # 静态 + 动态完整验收
/product-verify refresh   # 清除决策缓存，重新完整验收
/product-verify scope --tasks T001,T002 --sub-projects api-backend
                          # 增量验收（仅检查指定任务/子项目范围）
```

---

## 增强协议（网络搜索 + 4E+4V + OpenRouter）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**网络搜索关键词**：
- `"automated acceptance testing {framework} {year}"`
- `"Playwright testing best practices {year}"`
- `"Lighthouse CI performance budget {year}"`

**4D+6V 验收基准**：
- **4D 覆盖度矩阵**: S1-S4 结果按 Data/Interface/Logic/UX 四维度聚合，每维度覆盖率 ≥ 85% 为 PASS
- **6V 失败诊断**: D4 对动态失败进行 Contract/Conformance/Correctness/Consistency/Capability/Context 六维诊断
- **闭环判定**: 静态 4D + 动态 4D 取 min，任一维度 < 80% 自动生成补充任务

**OpenRouter 专家矩阵覆盖**：
- S1 covered（API/后端）→ DeepSeek 审计实现深度
- S2 covered（UI/前端）→ Gemini 审计组件保真度
- S3 covered（安全/规则）→ GPT 审计护栏完整性

---

## 产品验收原则

> 以下原则在各步骤中强制执行。

| 原则 | 对应步骤 | 具体规则 |
|------|---------|---------|
| **概念意图验证** | S1 语义审计 | 不只检查"代码有没有"，还检查"代码是否还原了产品概念的意图"。LLM 读 product-concept.json 中的创新点描述，对比代码实际做了什么。实现了 30% 的意图（如只有文字没有对比照片）→ partial，不是 genuine |
| **集成任务分级** | S1/S4 | 区分"纯代码任务"和"需要外部配置的集成任务"（OAuth SDK、支付网关、推送服务、文件存储）。集成任务如果只有 coming soon / mock → 标记为 `integration_pending`（独立分类，不算 genuine 也不算 missing） |
| **Mock 回退检测** | S1 语义审计 | 检测 catch 块中返回硬编码假数据的模式。provider/service 的 error fallback 如果返回 mock 列表而非 throw → 标记为 `mock_masked`（Warning：功能看似正常但数据是假的） |
| 语义覆盖优于字符串匹配 | S1 语义审计 | LLM 读代码理解逻辑，不再依赖路由关键词匹配。4D 维度判定取代二元 covered/missing |
| 先有条件再验证 | D1 动态 | 验收条件必须来自 use-case-tree.json 的 Given/When/Then，不自行编造验收标准 |
| 可用性启发式检查 | D3.5 认知走查 | 每个页面检查：错误状态有提示、加载有反馈、操作可撤销、导航一致、权限拒绝有说明 |
| 静态先行 | 整体时机 | 静态语义扫描不需要启动应用，优先执行，尽早发现覆盖缺口 |
| 4D 覆盖度闭环 | 静态汇总 + D5 | 按 Data/Interface/Logic/UX 四维度聚合覆盖率，任一维度 < 85%（静态）/ 80%（动态）自动生成补充任务 |
| XV 降低单模型盲区 | S5 XV | S1-S4 由 Claude 完成，S5 用专家模型矩阵二次审计，分歧项标记 REVIEW_NEEDED |
| 6V 诊断取代规则分类 | D4 6V 诊断 | 动态失败不再按错误特征硬编码分类，LLM 从 6 个工程视角深度诊断根因 |

---

## 模式说明

| 模式 | 说明 | 是否需要应用运行 |
|------|------|----------------|
| `static` | 代码扫描，检查 API/组件/约束覆盖 | 否 |
| `dynamic` | Playwright 浏览器测试 | 是 |
| `full` | 静态 + 动态 | dynamic 阶段需要 |
| `refresh` | 清除 verify-decisions.json 缓存，重新完整运行 | 视模式而定 |
| `scope` | 增量验收：仅 S1+S3 范围过滤，S2/S4/Dynamic 跳过 | 否 |

---

## 工作流

```
前置检查：
  概念蒸馏基线（推拉协议 — 见 product-design-skill/docs/skill-commons.md §三.A）：
    .allforai/product-concept/concept-baseline.json → 自动加载，不存在则 WARNING
    → 验证时以产品定位和治理风格为基准判断功能正确性
  两阶段数据加载：
  Phase 1 — 加载索引（< 5KB）：
    检查 task-index.json → 获取任务 id/task_name/frequency/owner_role/risk_level + 模块分组
    检查 experience-map.json → 获取界面 id/name/task_refs/action_count（S2 用）
    任一索引不存在 → 对应数据回退到 Phase 2 全量加载（向后兼容）
  Phase 2 — 按需加载完整数据：
    加载 .allforai/product-map/product-map.json
    若 product-map.json 也不存在 → 提示用户先执行 product-map 工作流，终止
    若存在 `experience_priority.mode = consumer|mixed` → 启用用户端成熟度验收附加规则
  其他可选数据：
    experience-map.json 必须（不存在则自动运行 experience-map 生成，然后启用 S2）
    use-case-tree.json 可选（dynamic 优先使用，否则自动推导）
    verify-decisions.json 存在则加载历史决策，已决策项自动跳过
  ↓
前置: 创新保护感知
  加载 task-inventory.json 检查 innovation_tasks 字段：
    存在 → 提取所有 protection_level=core 的任务 ID 列表
      在 S1-S5 静态验证和 D2-D3 动态验证中，core 创新任务视为 frequency=high，确保不被优先级降级
      S5 成本控制中，core 创新任务始终包含在审查集中，不受 covered 数量阈值限制
    不存在 → 跳过，按标准优先级处理
  ↓
前置: 上游过期检测
  加载输入文件时，比较关键上游文件的修改时间与本技能上次输出的生成时间：
  - product-map.json 在 verify-report.md 生成后被更新
    → ⚠ 警告「product-map.json 在 verify-report.md 生成后被更新，数据可能过期，建议重新运行 product-map」
  - requirements.md 在 verify-report.md 生成后被更新
    → ⚠ 警告「requirements.md 在 verify-report.md 生成后被更新，数据可能过期，建议重新运行 design-to-spec」
  - 仅警告不阻断，用户可选择继续或先刷新上游
  ↓

[Static 阶段]（static / full 模式）
  **并行执行**：S0-S4 读取不同产物、零依赖，并行分派 5 个子任务：
    ┌── Agent(S0): 双向追溯矩阵（读 task-inventory + tasks.md + 代码路由）
    ├── Agent(S1): 语义化 Task 覆盖检查（读 task-inventory + 代码）
    ├── Agent(S2): UI 组件保真度检查（读 experience-map + 前端代码）
    ├── Agent(S3): 护栏逻辑覆盖审计（读 constraints + task.rules + 代码）
    └── Agent(S4): Extra 代码 AI 研判（读代码路由 + task-inventory）
  全部完成 → 聚合结果 → S5 XV 交叉验证
  ↓
  S0: 双向追溯矩阵 (Bidirectional Traceability Matrix)
      > S1 用 LLM 语义判断"代码有没有实现功能"，S0 用结构化匹配建立"任务↔端点"的形式化映射。
      > 两者互补：S0 捕获结构性遗漏（快、确定性高），S1 捕获语义性缺陷（深、理解力强）。

      **输入**：
      - `task-inventory.json`（产品任务列表，每个任务有 task_name / main_flow / api_hint 等）
      - `tasks.md`（B2 端点任务列表，每个任务有端点路径 + _Acceptance_ 条件）
      - 代码中实际注册的路由/端点（从 router 文件、controller 装饰器、路由配置等提取）

      **正向追溯（Forward: 产品任务 → 代码端点）**：
      1. 遍历 task-inventory.json 的每个 CORE 任务
      2. 查找 tasks.md 中是否有对应的 B2 任务（通过 _Source_ 字段或语义匹配）
      3. 查找代码中是否有对应的路由注册
      4. 产出矩阵行：`| T001 | 创建订单 | B2.15 POST /orders | router.go:42 | ✓ TRACED |`
      5. 无 B2 任务 → `FORWARD_ORPHAN`（spec 遗漏）
      6. 有 B2 但无代码路由 → `FORWARD_UNIMPLEMENTED`（实现遗漏）

      **逆向追溯（Reverse: 代码端点 → 产品任务）**：
      1. 遍历代码中所有注册的路由/端点
      2. 查找 tasks.md 中是否有对应的 B2 任务
      3. 查找 task-inventory.json 中是否有对应的产品任务
      4. 产出矩阵行：`| GET /admin/stats | B2.42 | T089 | ✓ TRACED |`
      5. 无 B2 任务且无产品任务 → `REVERSE_ORPHAN`（幽灵端点，可能是遗留代码或未记录功能）
      6. 有 B2 但无产品任务 → `REVERSE_SPEC_ORPHAN`（实现超出规格，需确认是否合理）

      **验收条件追溯（Acceptance Trace，有 _Acceptance_ 时执行）**：
      1. 对有 `_Acceptance_` 字段的 B2 任务，检查每条验收条件中的端点是否在代码路由中存在
      2. 验收条件的端点不存在 → `ACCEPTANCE_UNIMPLEMENTED`（验收标准无法执行）

      **严重级定义**：
      | 标记 | 严重级 | 含义 |
      |------|--------|------|
      | `FORWARD_ORPHAN` | CRITICAL | 产品任务无对应 spec 任务（spec 生成遗漏） |
      | `FORWARD_UNIMPLEMENTED` | CRITICAL | spec 有但代码没实现 |
      | `ACCEPTANCE_UNIMPLEMENTED` | CRITICAL | 验收条件引用的端点未实现 |
      | `REVERSE_ORPHAN` | WARNING | 代码端点无对应产品任务（可能是基础设施端点，需人工确认） |
      | `REVERSE_SPEC_ORPHAN` | INFO | 实现超出规格（记录，不阻塞） |

      **输出**：
      - `traceability-matrix.json`：完整的双向映射矩阵
      - 汇总：`「S0 追溯矩阵 ✓ 正向: {N} traced / {M} orphan / {K} unimpl, 逆向: {P} traced / {Q} orphan」`

      **与 S1 的关系**：
      - S0 FORWARD_UNIMPLEMENTED + S1 missing → 高置信缺失（两条证据链）
      - S0 FORWARD_UNIMPLEMENTED + S1 genuine → S0 可能匹配错误，以 S1 语义判断为准
      - S0 TRACED + S1 stub → 路由存在但实现为空壳，以 S1 判断为准
  ↓
  S1: 语义化 Task 覆盖检查 (LLM-driven)
      LLM Agent 分析代码库，不再仅匹配路由字符串，而是理解代码逻辑是否真正闭环了 `task-inventory.json` 定义的功能。
      **4D 审计基准**：
      - **Data**: 任务涉及的实体/表是否有对应 ORM/Schema 定义？
      - **Interface**: 任务的 CRUD 操作是否有完整的路由 handler（非空桩）？
      - **Logic**: handler 内是否包含 `task.rules` 对应的业务判断逻辑？
      - **UX**: 前端是否有对应页面/组件消费该 API？
      **空壳检测（Hollow Shell Detection）**：

      > **必须由 LLM 语义判断，禁止退化为模式匹配。**
      > 不要 grep `() {}` 或 `TODO` 来判断空壳——聪明的空壳不会写 TODO，
      > 它会有看似合理的代码结构但不产生真实业务效果。

      UI 文件存在 ≠ 功能实现。LLM 读每个文件的代码，以"如果用户真的使用这个功能，会得到什么结果？"为判断标准：

      - **用户点了按钮会发生什么？** LLM 追踪事件回调的调用链——如果最终没有到达 API 调用或状态变更，就是空壳
      - **页面展示的数据从哪来？** LLM 判断数据是来自 API/Provider/Store 还是硬编码在组件内。展示层组件必须消费外部数据源
      - **这个组件的 tasks.md 验收条件满足了吗？** LLM 读对应任务的 Acceptance 条件，逐条判断代码是否满足
      - **tasks.md 指定的文件是否都创建了？** 对比 Files 列表与实际文件系统，缺失 → 降级

      判定不是靠匹配代码模式，而是 LLM 理解代码意图后回答：
      **"如果一个真实用户使用这个功能，能得到有价值的结果吗？"**
      能 → genuine。不能但有部分逻辑 → partial。完全不能 → stub/hollow。

      **覆盖判定**（取代字符串匹配）：
      - `genuine` — 4D 中至少 3 维有实质代码，且无关键交互空壳
      - `partial` — 1-2 维有实质代码，或有空壳交互（标注缺失维度 + 空壳清单）
      - `stub` — 仅有路由声明 / TODO / mock 返回 / 关键交互全部为空壳
      - `missing` — 无任何匹配代码
      → 输出进度: 「S1 语义审计 ✓ genuine:{N} partial:{K} stub:{J} missing:{M} hollow:{H}」
  ↓
  S1.5: 功能深度验收 (LLM-driven, concept-baseline 存在时执行)

      > S1 检查"代码存在吗"和"是不是空壳"，但不检查"实现深度够不够"。
      > 一个 methodology_engine.py 有 200 行代码、不是 placeholder、也不是 TODO——
      > 但如果概念说"阶段驱动讨论"，而代码只做"关键词匹配选方法论名字"，这就是**深度不足**。
      > S1.5 解决的是：代码实现的行为是否达到了产品概念描述的意图。

      **输入**：
      - `concept-baseline.json` 的 `core_mechanisms`（核心机制描述）
      - `product-concept.json` 的 `innovation_concepts`（创新概念 + 行为描述）
      - `product-concept.json` 的 `product_mechanisms`（方法论引擎、搜索引擎、AI 工具等详细行为定义）
      - 对应的源代码文件

      **LLM 审计方式**：
      对每个核心机制和创新概念，LLM 做两件事：
      1. **提取概念意图**：从概念文件中提取该机制"应该做什么"的行为描述（不是功能名，是具体行为）
      2. **比对代码行为**：读对应源代码，判断代码实现的行为是否匹配概念意图

      **判定标准**：
      - `FULL` — 代码行为完整覆盖概念描述的意图
      - `SHALLOW` — 代码有相关逻辑但深度不足（如概念说"阶段驱动"但代码只做"选名字"）
      - `STUB` — 代码只有接口/壳子，核心逻辑缺失或 mock
      - `MISSING` — 完全没有对应代码

      **SHALLOW 的典型模式**（LLM 判断，不硬编码）：
      - 概念说"自动搜索并引用"→ 代码有搜索函数但返回硬编码结果
      - 概念说"按阶段引导讨论"→ 代码能选方法论但没有阶段推进逻辑
      - 概念说"生成结构化输出（导图/表格）"→ 代码有 Tab 切换但渲染器是 placeholder
      - 概念说"跨域类比"→ 代码调了 LLM 但 prompt 里没有跨域搜索指令

      **修复方向**：
      - SHALLOW/STUB 项 → 生成 `DEEPEN` 类型的修复任务（不是新建功能，是加深已有实现）
      - DEEPEN 任务比 IMPLEMENT 任务优先级低但比 FIX 高

      **无 concept-baseline 时**：跳过 S1.5，输出 `S1.5 ⊘ 无概念基线`

      → 输出进度: 「S1.5 深度验收 ✓ full:{N} shallow:{K} stub:{J} missing:{M}」
  ↓
  S2: UI 组件保真度检查 (LLM-driven)
      Agent 扫描前端代码，以 `experience-map.json` 为真值验证组件实现保真度。
      **6V 保真度维度**：
      - **V1 Contract**: 组件 props 是否匹配 `screen.actions` 定义的交互？
      - **V2 Conformance**: 组件是否使用了 `ui-design-spec.md` 指定的 Design Token？
      - **V3 Correctness**: `screen.states`（empty/loading/error/permission_denied）四态是否全部实现？
      - **V4 Consistency**: 同类页面（列表/详情/表单）是否使用相同组件套路？
      - **V5 Capability**: 是否实现了 `implementation_contract.required_behaviors`？
      - **V6 Context**: `emotion_context` 标注的焦虑/沮丧触点是否有对应 UI 反馈？
      **保真度评分**：通过 V 数 / 6 = 保真度分（≥ 0.8 为 PASS）
      **用户端附加规则（consumer/mixed）**：
      - 首页不能只是入口拼盘，必须能识别主线任务或状态总览
      - 核心界面不能只可点击，还要能看出下一步引导
      - 历史/提醒/通知/进度/最近活动等持续关系入口若设计基线要求存在，则必须验收
      - 若整体观感仍像后台页面压缩版或概念 demo，S2 至少记为 `warn`
      → 输出进度: 「S2 UI 保真 ✓ pass:{N} warn:{M} fail:{K}（平均保真度 {score}）」
  ↓
  S2.5: 产品打磨审查 (LLM-driven, consumer_apps 存在时执行)

      > S1 检查"有没有"，S1.5 检查"深度够不够"，S2 检查"保真度高不高"——
      > 但这些都是工程师视角。S2.5 切换到**用户/设计师/PM 视角**，
      > 审查的是"用起来感觉怎么样"。

      LLM Agent 读 consumer_apps 中每个子项目的**用户可见代码**
      （screen/widget/page + theme + i18n 文本 + 路由），然后回答以下问题：

      **P1 首次体验**：
      如果我是第一次打开这个 App——
      - 我能在 3 秒内知道这个产品是干什么的吗？（首屏信息密度）
      - 有没有引导我完成第一个核心操作？（新手引导/空态引导）
      - 第一次操作完成后，有没有正向反馈让我觉得"值了"？（完成仪式/结果展示）

      **P2 文案语气**：
      读所有用户可见文本（i18n 文件 + 硬编码字符串）——
      - 语气是否一致？（全部正式 or 全部轻松，不是混搭）
      - 有没有 CRUD 味道的文案？（"创建成功""删除确认""请输入"→ 后台语气）
      - 有没有让用户产生情感连接的文案？（"一群 AI 大佬帮你想" vs "开始会议"）

      **P3 视觉节奏**：
      读 theme 文件 + 各页面的布局代码——
      - 间距是否成体系？（用 theme 定义的 spacing 还是随手写 16/20/24）
      - 颜色是否收敛？（用 theme 定义的色板还是随手写 hex 值）
      - 字号层级是否清晰？（标题/正文/辅助文字是否用 TextTheme 还是随手写 fontSize）

      **P4 流程连贯**：
      追踪核心用户流（从 router 配置 + 页面跳转代码推导）——
      - A 页面到 B 页面的跳转有没有转场？（不是瞬间切换）
      - 返回时上下文是否保持？（列表滚动位置、表单草稿、筛选条件）
      - 操作完成后用户知道下一步做什么吗？（不是回到空白页）

      **P5 性能隐患**：
      读数据加载代码——
      - 列表有没有分页/虚拟滚动？（300 条数据一次加载 = 卡顿）
      - 图片有没有懒加载或尺寸限制？（全尺寸原图 = 慢）
      - 有没有不必要的全量请求？（每次进页面 reload 全部数据）
      - 有没有缓存策略？（离线或弱网时的体验）

      **判定**：
      每个 P 维度标为 `good` / `needs_polish` / `poor`
      - `poor` 项 → 生成 `POLISH` 类型任务
      - `needs_polish` → 记录建议，不阻塞
      - 全部 `good` → PASS

      **无 consumer_apps 时**（纯后台产品）：跳过 S2.5

      → 输出进度: 「S2.5 打磨审查 ✓ P1:{r} P2:{r} P3:{r} P4:{r} P5:{r}」
  ↓
  S3: 护栏逻辑覆盖审计 (LLM-driven)
      Agent 深度 Grep + Read 代码，理解业务校验逻辑是否完整覆盖三级护栏。
      **三级护栏基准**：
      - **L1 constraints.json**: 全局业务约束（金额上限/不可逆状态/跨实体规则）
      - **L2 task.rules**: 任务级业务规则（幂等窗口/阈值触发/校验逻辑）
      - **L3 task.exceptions**: 异常处理逻辑（超时/冲突/权限不足/并发）
      **审计方式**：Agent 逐条读取约束，Read 对应代码文件，判断逻辑是否语义等价（而非关键词匹配）。
      → 输出进度: 「S3 护栏审计 ✓ L1:{a}/{b} L2:{c}/{d} L3:{e}/{f}」
  ↓
  S4: Extra 代码 AI 研判
      Agent 自动研判地图外的端点，语义区分”基础设施”与”幽灵功能”。
      **研判逻辑**：Agent 读取端点 handler 代码，理解其用途，分类为：
      - `infra` — 健康检查/认证回调/文档/静态资源/框架内置（自动 ignore）
      - `dev_support` — 调试端点/seed 数据/mock 路由（自动 ignore + 标注”生产前移除”）
      - `ghost` — 无法归类到任何产品功能（建议 mark_remove）
      - `undocumented` — 有实质业务逻辑但不在产品地图中（建议 add_to_map）
      → 输出进度: 「S4 Extra ✓ infra:{N} dev:{M} ghost:{J} undocumented:{K}」
  ↓
  S5: Cross-Model 交叉验证 (XV)
      **目的**：S1-S4 由 Claude 单模型完成，存在盲区。通过专家模型矩阵二次审计。
      **模型路由**（遵循 `docs/skill-commons.md` 专家矩阵）：
      - S1 covered 项（API/后端）→ DeepSeek 审计代码实现深度
      - S2 covered 项（UI/前端）→ Gemini 审计组件保真度
      - S3 covered 项（安全/规则）→ GPT 审计护栏完整性
      **审查范围**（成本控制）：
        covered 总数 ≤ 20 → 全量审查
        21-50 → 仅 frequency=高 + risk_level=高
        > 50 → 仅 frequency=高（上限 30 项）
        protection_level=core 的创新任务始终纳入，不受阈值限制
      **审查方式**：
        Read 匹配文件（handler ±15 行，上限 50 行）
        构造审查 prompt（角色 + 任务描述 + 代码片段 + 4D 判断标准）
        调用 OpenRouter 专家模型
        比对结果：Claude 与专家模型一致 → 确认 | 分歧 → 标记 REVIEW_NEEDED
      OpenRouter 不可用 → 跳过 S5，输出: 「S5 XV ⊘ OpenRouter 不可用，跳过」
      → 输出进度: 「S5 XV ✓ {N} 项审查, {M} 项分歧(REVIEW_NEEDED)」
  ↓
  S6: 旅程级验证（Journey-Level Verification）
      逐用例验证端到端可达性，汇总 S1-S5 结果计算旅程完整度。
      use-case-tree.json 不存在 → 跳过 S6
      → 输出进度: 「S6 旅程级 ✓ passed:{N} partial:{M} failed:{K}」
  ↓
  S7: 种子数据↔测试场景覆盖矩阵 (Seed-Test Coverage Matrix)
      **目的**：验证 seed-forge 生成的数据是否足以支撑 product-verify 和 testforge 的所有测试场景。
      **前提**：`.allforai/seed-forge/seed-plan.json` 存在；否则跳过。
      **审计逻辑**：
      1. 从 use-case-tree.json / D1 测试序列提取所有需要的前置数据状态
      2. 从 seed-plan.json 提取已规划生成的实体 + 状态分布
      3. 逐场景比对：
         - 场景需要"已撤销记录" → seed-plan 是否规划了 REVOKED 状态记录？
         - 场景需要"两个角色各自操作" → seed-plan 是否有两个角色的账号？
         - 场景需要"筛选结果 ≥2 条" → seed-plan 的数据量是否满足？
      **覆盖矩阵**：
      | 测试场景 | 需要的数据状态 | seed-plan 覆盖 | 缺口 |
      |---------|-------------|--------------|------|
      | UC-001 创建工单 | 可用条目 ≥1 | ✅ | — |
      | UC-005 撤销审批 | REVOKED 记录 ≥1 | ❌ | SEED_GAP |
      **闭环**：缺口项自动生成 SEED_SUPPLEMENT 任务，指示 seed-forge 补充缺失数据。
      → 输出进度: 「S7 Seed 覆盖 ✓ covered:{N}/{M} gaps:{K}」
  ↓
  静态汇总 + 4D/6V 覆盖度闭环:
    **覆盖度矩阵**（自动生成）：
    | 检查项 | genuine | partial | stub | missing | XV 分歧 |
    |--------|---------|---------|------|---------|---------|
    | S0 双向追溯 | traced:{N} | — | — | fwd_orphan:{M} fwd_unimpl:{K} | rev_orphan:{Q} |
    | S1 Task 语义覆盖 | {N} | {K} | {J} | {M} | {D} |
    | S2 UI 保真度 | {N} | — | — | {M} | {D} |
    | S3 护栏覆盖 | {N} | — | — | {M} | {D} |

    **4D 维度覆盖热力图**：
    | 维度 | 覆盖率 | 薄弱任务 |
    |------|--------|---------|
    | Data | {N}% | {列出 Data 维度缺失的任务} |
    | Interface | {N}% | {列出 Interface 维度缺失的任务} |
    | Logic | {N}% | {列出 Logic 维度缺失的任务} |
    | UX | {N}% | {列出 UX 维度缺失的任务} |

    **闭环判定**：
    - 4D 每维度覆盖率均 ≥ 85% 且 XV 分歧率 ≤ 5% → STATIC_PASS
    - 任一维度 < 85% 或分歧率 > 5% → 生成补充 IMPLEMENT 任务，标注缺失维度
    → 自动采纳全部分类（不停）

[Dynamic 阶段]（dynamic / full 模式）
  D0: 应用可达性预检
      自动检测 URL（Grep 代码配置 PORT/listen/.env）
      HTTP 请求验证可达性
      可达 → 继续（不停）
      不可达 → 记录为 ENV_ISSUE，跳过 dynamic 阶段（不停）
  ↓
  D1: LLM 驱动测试序列生成
      **use-case-tree.json 存在时**：
      - 提取正常流 + E2E 用例，按角色分组
      - Agent 审查用例覆盖度：是否覆盖了 experience-map 中所有 frequency=高 的 screen？
      - 覆盖不足 → Agent 自动补充遗漏路径的测试序列
      **use-case-tree.json 不存在时**：
      - Agent 从 task-inventory.json 自动推导（frequency=高/中 的任务）
      - 按角色生成最简测试序列（登录 → 执行核心任务 → 验证结果）
      → 自动推导/补充测试序列（不停，汇总到 D4 批量确认）
  ↓
  D2∥D3: 并行执行正常流 + E2E 流用例（独立 Playwright browser context）
      ┌── Agent(D2): 正常流用例（独立 context，隔离 cookie/session）
      └── Agent(D3): E2E 流用例（独立 context，隔离数据）
      全部完成 → 聚合结果
      → 输出进度: 「D2 正常流 ✓ pass:{N} fail:{M} | D3 E2E流 ✓ pass:{N} fail:{M}」
  ↓
  D3.5: LLM Cognitive Walkthrough（可发现性测试）
      模拟真实用户视角，验证功能可发现性（详见下方 D3.5 章节）
  ↓
  D3.6: UI 活性验证 (UI Liveness Guarantee)
      **目的**：experience-map 中每个 screen 的每个 action 都必须有数据让它"活"起来，否则验收时看到的是空壳。
      **基准**：experience-map.json 的 screens + actions + states
      **验证规则**（逐 screen 逐 action Playwright 检查）：
      | UI 元素类型 | 最低数据保障 | 检查方法 |
      |------------|------------|---------|
      | 列表页 | ≥ 2 条记录 | `browser_evaluate` 计数列表行/卡片 |
      | 详情页 | ≥ 1 条完整字段记录 | 检查无 null/undefined/空值 |
      | 操作按钮 | ≥ 1 条可操作的目标数据 | 按钮非 disabled 且有目标记录 |
      | 搜索/筛选 | ≥ 2 条可区分记录 | 搜索后结果变化 |
      | 状态标签/徽章 | 每种状态至少 1 条 | 对照 task.outputs.states 逐状态验证 |
      | Dashboard/图表 | ≥ 1 个月跨度数据 | 图表渲染非空 |
      | 空态页面 | 专门验证 empty state | 新角色/空数据账号登录后 empty 页正确展示 |
      **用户端附加活性（consumer/mixed）**：
      - 首页主线卡片/主 CTA 必须有真实数据或明确状态驱动
      - 历史/通知/进度/最近活动等持续关系模块不能全部空壳占位
      - 完成动作后，结果页或列表回流必须可见
      **逆向验证链**：
      experience-map.screen → 反推最低数据需求 → 对比 seed-plan.json → 缺口即 SEED_GAP
      **输出**：
      | screen | actions 总数 | 有数据支撑的 action | 活性率 |
      |--------|------------|-------------------|-------|
      | 工单列表 | 5 | 5 | 100% |
      | 撤销审批 | 3 | 1 | 33% ← 需补 REVOKED 数据 |
      活性率 < 80% 的 screen → 生成 SEED_SUPPLEMENT + IMPLEMENT 任务
      → 输出进度: 「D3.6 UI 活性 ✓ alive:{N}/{M} screens（平均活性 {rate}%）」
  ↓
  D3.7: 数据流闭环追踪 (Data Flow Tracing)
      **目的**：跟踪一条业务实体从创建→更新→流转→消费→终态的全生命周期，验证数据在每个节点的正确性。
      **基准**：business-flows.json 的每条 flow = 一条数据流路径
      **验证流程**：
      1. 选取 frequency=高 的 flow（≤5 条）
      2. 对每条 flow，用 Playwright + API 调用追踪数据全生命周期：
         - 创建节点：API 创建实体 → 验证响应 + 数据库状态
         - 流转节点：触发状态变更 → 验证前后端状态同步
         - 消费节点：在下游页面验证数据正确展示
         - 终态节点：实体到达终态后各关联实体是否正确更新
      3. 每个节点验证：输入数据 = 上游输出数据（字段名/类型/精度一致）
      **断裂检测**：
      - 某节点数据丢失或字段值变异 → DATA_FLOW_BREAK
      - 终态记录的关联数据不完整 → DATA_INTEGRITY_ISSUE
      → 输出进度: 「D3.7 数据流 ✓ flows:{N} breaks:{M}」
  ↓
  D3.8: 状态机完备性验证 (State Machine Completeness)
      **目的**：task.outputs.states 定义了 N 种状态，验证每种状态是否可达、有数据记录、UI 正确展示。
      **基准**：task-inventory.json 中每个任务的 `outputs.states` + seed-plan.json
      **验证矩阵**：
      | 实体 | 定义状态 | 有数据 | UI 可见 | 可达路径 |
      |------|---------|--------|---------|---------|
      | Record | PENDING | ✅ | ✅ | 创建后默认 |
      | Record | CONFIRMED | ✅ | ✅ | 审核通过 |
      | Record | REVOKED | ❌ | — | 撤销审批通过 |
      | Record | CANCELED | ✅ | ✅ | 用户取消 |
      **死胡同检测**：
      - 某状态有入口无出口（不可逆但未标注为终态） → STATE_DEAD_END
      - 某状态无数据覆盖 → STATE_NO_DATA（SEED_SUPPLEMENT）
      - 某状态有数据但 UI 未正确渲染状态标签 → STATE_UI_MISMATCH
      → 输出进度: 「D3.8 状态机 ✓ {N}/{M} 状态有数据, 死胡同:{K}」
  ↓
  D3.9: 约束运行时穿透测试 (Constraint Penetration Test)
      **目的**：S3 验证约束逻辑"代码有"，但运行时真的拦截了吗？用边界数据主动触发约束。
      **前提**：seed-plan.json 中有边界数据（1-D 约束规则设计的产出）；否则跳过。
      **测试策略**：
      1. 从 constraints.json + task.rules 提取可运行时验证的约束（≤10 条，选 risk_level=高）
      2. 对每条约束构造违规操作：
         - 金额上限约束 → 尝试提交超限金额
         - 不可逆状态约束 → 尝试回退已终结的记录
         - 幂等约束 → 短时间内重复提交
         - 权限约束 → 用低权限角色尝试高权限操作
      3. 验证系统响应：
         - 拦截成功 → CONSTRAINT_ENFORCED（预期的错误提示/拒绝）
         - 未拦截 → CONSTRAINT_BYPASS（严重：约束未生效）
         - 拦截但提示不友好 → CONSTRAINT_UX_ISSUE（有拦截但 UI 反馈差）
      → 输出进度: 「D3.9 约束穿透 ✓ enforced:{N} bypass:{M} ux_issue:{K}」
  ↓
  D4: LLM 6V 失败诊断与分类
      Agent 对 D2/D3 中所有失败用例进行 6V 视角深度诊断：
      **6V 诊断维度**：
      1. **Contract (V1)**: 失败是否源于前后端字段名/类型不一致（契约漂移）？
         → 分类: CONTRACT_SYNC（需同步 design.json）
      2. **Conformance (V2)**: 是否是环境不可达、超时或数据库连接问题？
         → 分类: ENV_ISSUE
      3. **Correctness (V3)**: 代码逻辑是否未按 `design.json` 规格实现？
         → 分类: FIX_FAILING
      4. **Consistency (V4)**: 是否与其他同类页面的行为不一致？
         → 分类: FIX_FAILING（标注参照页面）
      5. **Capability (V5)**: 是否是 SLA 性能不达标（超时/响应慢）导致的失败？
         → 分类: FIX_FAILING（标注 SLA 基准）
      6. **Context (V6)**: 失败点是否位于 `journey-emotion.json` 标注的高情感触点？
         → 影响升级: 根据上下文判定是否提升优先级（不一律 P0）

      **Agent 诊断流程**：
      - Read 失败截图 + 错误日志 + 对应代码文件
      - 比对 design.json 中的预期行为
      - 输出: { “verdict”: “V1-V6 中的主因”, “classification”, “reason”, “fix_hint” }

      **批量确认展示格式**：
      ## 动态验收结果 (6V 诊断)

      通过: {N}/{M} 用例

      失败项（LLM 6V 诊断）:
      | 用例 | 失败步骤 | 主因维度 | 诊断结论 | 分类 | 修复线索 |
      |------|---------|---------|---------|------|---------|
      | UC001 | Step 3 | V3 Correctness | handler 未处理空待处理列表 | FIX_FAILING | pending.controller:42 |
      | UC005 | Step 1 | V2 Conformance | 连接拒绝 | ENV_ISSUE | 检查 port 3001 |
      | UC008 | Step 2 | V1 Contract | 字段名 userName vs user_name | CONTRACT_SYNC | 同步 design.json |

      → 自动采纳全部建议分类（不停）
  ↓
  D5: 动态 4D 覆盖度闭环
      **交叉比对 D2/D3 通过用例与 S1 语义覆盖**：
      - S1 genuine + D2/D3 pass → 真正覆盖（最高置信）
      - S1 genuine + D2/D3 fail → 静态有但运行时不通（FIX_FAILING 优先级提升）
      - S1 missing + D 未覆盖 → 确认缺失
      **4D 动态维度覆盖**：
      | 维度 | 静态覆盖 | 动态验证 | 最终判定 |
      |------|---------|---------|---------|
      | Data | S1+S3 | D2/D3 数据操作成功率 | min(静态, 动态) |
      | Interface | S1 | D2/D3 API 调用成功率 | min(静态, 动态) |
      | Logic | S3 | D2/D3 业务流程通过率 | min(静态, 动态) |
      | UX | S2 | D3.5 可发现性分数 | min(静态, 动态) |

      **闭环判定**：
      - 4D 每维度最终判定均 ≥ 80% → VERIFY_PASS
      - 任一维度 < 80% → 生成针对性 IMPLEMENT/FIX 任务，标注缺失维度和修复线索

      若 `experience_priority.mode = consumer` 或 `mixed`，**仅对 consumer_apps 中的子项目**还需额外满足：
      - 用户端主线可发现
      - 关键状态可感知
      - 完成后知道下一步
      - 至少存在一条持续关系链路（历史/提醒/通知/进度/订阅/推荐中的相关项）

      否则即使基础 4D 达标，也应标记为 `VERIFY_WARN` 并生成补充任务。
      > consumer_apps 由 design-to-spec 初始化推导并记录在 forge-decisions.json 中。admin/merchant 子项目不受此附加约束。

生成输出文件：
  static-report.json / dynamic-report.json / verify-tasks.json / verify-report.md
```

---

### S1：Task → API 覆盖检查

**数据加载**：两阶段加载——先检查 `.allforai/product-map/task-index.json`（索引，< 5KB），存在则加载索引获取任务 id/task_name/frequency/owner_role，再按需从 `task-inventory.json` 加载完整任务数据。索引不存在时回退到全量加载 `task-inventory.json`。

**扫描策略**：
1. **框架检测**：Grep package.json / Gemfile / requirements.txt / composer.json 识别后端框架（Express / Rails / Django / Laravel / NestJS 等）
2. **路由扫描**：Glob 路由文件（routes/**, **/router.**, **/controllers/**），提取所有已定义端点
3. **映射比对**：对每个 task，检查是否存在路径或方法关键词匹配的路由

**覆盖状态**：
- `covered` — 找到匹配路由
- `missing_api` — 未找到任何匹配路由（→ IMPLEMENT 候选）
- `partial` — 找到路由但缺少角色鉴权中间件

**输出**：写入 `static-report.json` 的 `task_coverage` 字段。

---

### S2：Screen → 组件覆盖检查

**前提**：`.allforai/experience-map/experience-map.json` 存在；否则自动加载并执行 `../product-design-skill/skills/experience-map.md` 的完整工作流生成体验地图，完成后继续 S2。

**扫描策略**：
1. Glob 前端页面/视图文件（pages/**, views/**, src/pages/**, app/**/page.**, 等）
2. 对每个 screen，匹配路由路径或组件名关键词

**覆盖状态**：
- `covered` — 找到对应页面组件
- `missing_screen` — 未找到（→ IMPLEMENT 候选）

**输出**：写入 `static-report.json` 的 `screen_coverage` 字段。

---

### S3：约束 → 代码覆盖检查

**数据来源**：
- `product-map.json` 中的 `constraints` — 全局业务约束
- `task-inventory.json` 中每个任务的 `rules` — 任务级业务规则（幂等、阈值、校验）
- `task-inventory.json` 中每个任务的 `exceptions` — 异常处理逻辑（超时、冲突、权限）
- `task-inventory.json` 中每个任务的 `audit` — 审计中间件（操作记录、字段变更）

**扫描策略**：对每条约束/规则/异常/审计要求，Grep 代码库中的：
- 校验器（validator, validate, schema）
- 中间件（middleware, guard, interceptor, policy）
- 审计逻辑（audit, log, track, record）
- 条件判断中的约束关键词

**覆盖状态**：
- `covered` — 找到对应校验逻辑
- `missing_constraint` — 未找到（→ IMPLEMENT 候选，高风险约束优先）

**输出**：写入 `static-report.json` 的 `constraint_coverage` 字段。

---

### S3.5：Implementation Contract 验证

**前提**：`.allforai/experience-map/experience-map.json` 中 screens 含 `implementation_contract` 字段。字段不存在 → 跳过 S3.5。

**扫描策略**：
1. 遍历 experience-map 中每个 screen 的 `implementation_contract`
2. 对每个 screen，Grep 前端代码找到对应组件
3. 检查组件是否匹配 `pattern`：
   - `bottom-sheet` → 查找 BottomSheet / Drawer / ActionSheet 组件
   - `modal-picker` → 查找 Modal / Dialog / Picker 组件
   - `multi-step-form` → 查找 Stepper / Steps / multi-step 模式
   - `full-page` → 查找独立页面路由
   - `standard-page` → 不检查（默认模式）
   - 其他值 → ⚠ WARNING「未知 pattern: {value}，跳过验证」（product-design 可能新增了 pattern 但 S3.5 未同步）
4. 检查 `forbidden` 列表中的模式是否出现
5. 检查 `required_behaviors` 是否有对应实现

**覆盖状态**：
- `compliant` — 组件匹配 pattern，无 forbidden 违规
- `violation` — 使用了 forbidden 模式，或缺少 required_behaviors（→ FIX_CONTRACT 任务）
- `unchecked` — 组件未找到（由 S2 处理）

**输出**：写入 `static-report.json` 的 `contract_compliance` 字段。violation 项生成 `FIX_CONTRACT` 类型任务到 `verify-tasks.json`。

---

### S4：Extra 代码扫描

**策略**：反向扫描——提取代码中所有路由端点，与 task-inventory 中的任务做反向比对，找出**代码有但产品地图没有**的端点。

**排除项**（自动标注「基础设施/开发支持，不计入 EXTRA」）：
- 健康检查端点（/health, /ping, /ready, /metrics, /status）
- 认证/OAuth 回调端点（/auth/callback, /oauth/*, /login, /logout）
- API 文档端点（/api-docs, /swagger, /openapi, /redoc）
- 静态资源路由（/public/*, /static/*, /assets/*, /favicon.ico）
- 框架内置路由（Next.js `_next/*`, Rails `/rails/*`, Django `/admin/`, Vite `/@vite/*`）
- WebSocket 升级端点（/ws, /socket.io）

**EXTRA 自动建议规则**：
基础设施端点已在排除列表中自动跳过。剩余 EXTRA 端点默认建议 `ignore`，用户在静态汇总确认时可改为 `add_to_map` 或 `mark_remove`。

**输出**：EXTRA 项在静态汇总中批量展示（含自动建议），用户一次确认或逐条调整：
- `add_to_map` — 补录到产品地图（记录 INFO）
- `mark_remove` — 标记为 REMOVE_EXTRA 任务
- `ignore` — 合理遗留，忽略

---

### S5：Cross-Model 交叉验证

**目的**：S1 和 S3 的 covered 判定基于 Glob+Grep 模式匹配，存在假阳性风险——路由文件存在但 handler 内容为 `TODO`、空函数、或仅返回 mock 数据。通过 OpenRouter 调用第二模型（DeepSeek）读取实际代码片段，独立判断是否真正实现。

**触发条件**：OpenRouter MCP 可用时自动执行。不可用时跳过并在汇总中标注。

**审查范围**（成本控制）：

| covered 总数 | 审查策略 |
|-------------|---------|
| ≤ 20 项 | 全量审查所有 covered 项 |
| 21-50 项 | 仅审查 frequency=高 + risk_level=高 的 covered 项 |
| > 50 项 | 仅审查 frequency=高 的 covered 项（上限 30 项） |

例外：`protection_level=core` 的创新任务始终纳入审查，不受数量阈值限制。

**执行流程**：

```
对每个待审查的 covered 项:
  1. Read 匹配文件（matched_routes / matched_code 中的文件路径）
     提取路由 handler / 校验逻辑的关键代码段（匹配行 ±15 行，上限 50 行）
  2. 构造审查 prompt:
     角色: 你是一位严格的代码审查员
     任务描述: "{task_name}: {task 简述}"
     代码片段: （上一步提取的代码）
     判断标准:
       genuine — handler 包含实际业务逻辑（数据库操作/服务调用/条件判断）
       stub — handler 为空函数、仅返回固定值、包含 TODO/FIXME、或仅 console.log
       partial — handler 有部分逻辑但明显不完整（如只处理了 happy path，缺少错误处理）
     输出: { "verdict": "genuine|stub|partial", "reason": "一句话理由" }
  3. 调用 OpenRouter:
     mcp__ai-gateway__ask_model(
       task: "technical_validation",
       model_family: "deepseek",
       prompt: 上述 prompt
     )
  4. 比对结果:
     Claude covered + 第二模型 genuine → 确认 covered（无分歧）
     Claude covered + 第二模型 stub → 标记 REVIEW_NEEDED（假阳性嫌疑）
     Claude covered + 第二模型 partial → 标记 REVIEW_NEEDED（实现不完整）
```

**分歧处理**：REVIEW_NEEDED 项在静态汇总中单独展示，用户可选：
- `downgrade` — 将 covered 降级为 missing（加入 IMPLEMENT 候选）
- `keep` — 维持 covered（代码足够）
- `partial` — 标记为 partial（生成补全任务）

**输出**：写入 `static-report.json` 的 `cross_model_review` 字段。

---

### S6: 旅程级验证（Journey-Level Verification）

逐用例验证端到端可达性，发现"任务都在但流程断裂"的问题。

**前置**：use-case-tree.json（必须）+ static-report.json（S1-S5 产出）

**如果 use-case-tree.json 不存在 → 跳过 S6**，输出提示："S6 ⊘ use-case-tree.json 不存在，跳过旅程级验证"

**验证逻辑**：

1. **加载用例树**：从 use-case-tree.json 提取所有用例，每个用例包含有序步骤序列

2. **逐用例验证**：对每个用例的每个步骤：
   - 查找步骤关联的 task_ref
   - 从 S1 结果检查：该任务的 API/路由是否已覆盖？
   - 从 S2 结果检查：该任务的界面/组件是否已覆盖？
   - 从 S3 结果检查：该任务的约束是否已实现？
   - 步骤状态：全部通过 → ✅ | 部分缺失 → ⚠️ | 完全缺失 → ❌

3. **旅程完整度计算**：
   ```
   journey_completeness = 通过步骤数 / 总步骤数
   ```
   - ≥ 90% → PASS
   - 70%-89% → PARTIAL（可上线但有缺口）
   - < 70% → FAIL（旅程断裂，不可上线）

4. **断裂点识别**：
   - 连续 2+ 步骤缺失 → 标记为 CRITICAL_BREAK（用户流程中断）
   - 单步缺失但前后完整 → 标记为 GAP（可绕过）
   - 最后一步缺失 → 标记为 INCOMPLETE_ENDING（用户无法完成）

5. **按用例优先级排序**：
   - 根据需求优先级和业务上下文判定每个用例的通过要求
   - 核心业务旅程 → 必须 PASS；辅助功能 → 允许 PARTIAL

**输出追加到 static-report.json**：

```json
{
  "journey_verification": {
    "total_journeys": 12,
    "passed": 8,
    "partial": 3,
    "failed": 1,
    "journeys": [
      {
        "use_case_id": "UC-003",
        "use_case_name": "用户提交流程",
        "priority": "P0",
        "steps": [
          { "step": 1, "task_ref": "T-001", "label": "浏览条目", "api": "✅", "ui": "✅", "constraint": "✅", "status": "PASS" },
          { "step": 2, "task_ref": "T-002", "label": "创建工单", "api": "✅", "ui": "✅", "constraint": "✅", "status": "PASS" },
          { "step": 3, "task_ref": "T-003", "label": "审批确认", "api": "✅", "ui": "❌", "constraint": "N/A", "status": "PARTIAL" },
          { "step": 4, "task_ref": "T-004", "label": "查看结果", "api": "✅", "ui": "✅", "constraint": "✅", "status": "PASS" }
        ],
        "completeness": 0.875,
        "verdict": "PARTIAL",
        "breaks": [
          { "type": "GAP", "step": 3, "missing": ["ui"], "impact": "用户无法看到审批页面" }
        ]
      }
    ]
  }
}
```

**verify-report.md 追加**：

```markdown
## 旅程级验证

| 用例 | 优先级 | 完整度 | 结论 | 断裂点 |
|------|--------|--------|------|--------|
| 用户提交流程 | P0 | 87.5% | ⚠️ PARTIAL | Step 3 缺 UI |
| 用户注册流程 | P0 | 100% | ✅ PASS | — |
| 内容管理 | P1 | 60% | ❌ FAIL | Step 2-3 连续缺失 |

### 关键发现
- P0 旅程通过率：{N}/{M}
- 关键断裂：{列出 CRITICAL_BREAK}
- 建议：{优先修复 P0 FAIL 旅程}
```

**生成 IMPLEMENT 任务时的增强**：
- 传统方式：`IMPLEMENT T-003`（孤立任务）
- 旅程感知：`IMPLEMENT T-003 — 阻断「用户提交流程」Step 3/4，P0 优先级`
- 断裂点任务自动提升优先级为 P0

---

### D0：应用可达性预检

**目的**：在启动 Playwright 测试前确认应用可访问，避免浪费时间。

**检测策略**（优先自动检测，仅不可达时交互）：
1. 自动检测：Grep 代码中的 `PORT`、`listen`、`localhost`、`.env` 等配置，推测应用 URL
2. 使用 Bash `curl -s -o /dev/null -w "%{http_code}" <URL>` 验证 HTTP 可达性
3. 可达 → 继续（不停）
4. 不可达 → 记录为 ENV_ISSUE，跳过 dynamic 阶段（不停）

**输出**：确认的 `app_url` 写入 `dynamic-report.json` 的 `app_url` 字段。

---

### 动态验证工具路由

根据子项目类型自动选择动态验证工具：

| 子项目类型 | 验证工具 | 说明 |
|-----------|---------|------|
| `admin` / `web-customer` / `web-mobile` | **Playwright** | MCP browser_* 工具执行用例 |
| `mobile-native` (iOS Swift/SwiftUI) | **XCUITest** | `xcodebuild test` 执行原生 UI 测试 |
| `mobile-native` (Android Kotlin/Java) | **Maestro** | CLI `maestro test` 执行验证流 |
| `mobile-native` (Flutter) | **Patrol** | `patrol test` 执行 Flutter 原生 UI 测试 |
| `mobile-native` (Expo / RN) | **Maestro** | CLI `maestro test` 执行验证流 |
| `backend` | **curl / HTTP** | API 路由 + 响应校验 |

**工具探测**：
- Playwright: 检测 `mcp__playwright__browser_navigate` 或 `mcp__playwright__browser_navigate` 工具可用性
- Patrol: 检测 `which patrol` CLI 可用性（Bash）或项目 `pubspec.yaml` 含 `patrol` 依赖
- Maestro: 检测 `which maestro` CLI 可用性（Bash）
- XCUITest: 检测 `which xcodebuild` CLI 可用性（Bash）

**移动端工具选择逻辑**：
```
mobile-native 子项目:
  tech_stack = Swift / SwiftUI   → XCUITest
  tech_stack = Kotlin / Java     → Maestro（降级 → Espresso）
  tech_stack = Flutter           → Patrol（降级 → flutter test integration_test/）
  tech_stack = RN / Expo         → Maestro（降级 → Detox）
```

**Maestro 降级**：
- Patrol CLI 不可用（Flutter）→ 降级为 `flutter test integration_test/`
- Maestro CLI 不可用 → Android 降级为 Espresso，RN 降级为 Detox
- 均不可用 → 标记为 `DEFERRED_NATIVE`（仅测 API 层）
- 输出提示：「安装 Maestro（`curl -Ls https://get.maestro.mobile.dev | bash`）以启用移动端动态验证」

**XCUITest 降级**：
- `xcodebuild` 不可用（非 macOS / 无 Xcode）→ 标记为 `DEFERRED_NATIVE`（仅测 API 层）
- 输出提示：「XCUITest 需要 macOS + Xcode，当前环境不支持」

**Maestro 用例执行**：
1. 从 use-case 提取移动端用例步骤
2. 生成 Maestro flow YAML（tapOn / assertVisible / takeScreenshot）
3. 执行 `maestro test` 并收集 JUnit 结果
4. 截图存储到 `.allforai/product-verify/screenshots/maestro/`
5. 结果合并到统一的 verify-tasks.json（与 Playwright 结果同格式）

**XCUITest 用例执行**：
1. 从 use-case 提取 iOS 端用例步骤
2. 生成 XCUITest Swift 测试文件：
   ```swift
   import XCTest

   final class ProductVerify_{scenario_id}Tests: XCTestCase {
       let app = XCUIApplication()

       override func setUpWithError() throws {
           continueAfterFailure = false
           app.launch()
       }

       func test_{step_name}() throws {
           // 导航到目标页面
           app.buttons["{element_label}"].tap()
           // 断言预期结果
           XCTAssertTrue(app.staticTexts["{expected_text}"].waitForExistence(timeout: 5))
           // 截图
           let screenshot = app.screenshot()
           let attachment = XCTAttachment(screenshot: screenshot)
           attachment.name = "{scenario_id}_{step}"
           attachment.lifetime = .keepAlways
           add(attachment)
       }
   }
   ```
3. 执行测试：
   ```bash
   xcodebuild test \
     -project {project_path} \
     -scheme {scheme_name} \
     -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' \
     -resultBundlePath .allforai/product-verify/xcuitest-results \
     | xcpretty --report junit --output .allforai/product-verify/xcuitest-junit.xml
   ```
4. 截图存储到 `.allforai/product-verify/screenshots/xcuitest/`
5. 结果解析 JUnit XML → 统一格式，合并到 verify-tasks.json（与 Playwright/Maestro 结果同格式）

---

### D1：加载/推导测试序列

**use-case-tree.json 存在时**：
- 提取所有 `type: "normal"` 的正常流用例
- 提取所有 `type: "e2e"` 的 E2E 用例
- 过滤掉 `priority: "低"` 的用例（可选，询问用户）

**use-case-tree.json 不存在时（自动推导）**：
- 从 task-inventory.json 提取 frequency=高 和 frequency=中 的任务
- 按角色分组，为每个角色生成最简测试序列（登录 → 执行核心任务 → 验证结果）
- 自动推导测试序列（不停，汇总到 D4 批量确认）

---

### D2/D3：Playwright 执行

> **工具条件**：以下 D2-D3 步骤中的 Playwright 操作适用于 Web 端子项目。Mobile-native 子项目使用 Maestro 等效操作（见「动态验证工具路由」）。

**执行方式**：使用 MCP Playwright 工具交互式测试，主要工具：
- `browser_navigate` — 导航到目标页面
- `browser_snapshot` — 获取页面可访问性快照（用于定位元素）
- `browser_click` / `browser_type` / `browser_fill_form` — 模拟用户操作
- `browser_take_screenshot` — 失败时截图保存到 `.allforai/product-verify/screenshots/`
- `browser_wait_for` — 等待页面加载或元素出现

**执行原则**：
- 每个用例独立运行，不相互依赖
- 每步操作前先 `browser_snapshot` 获取当前页面状态，再根据快照中的元素 ref 执行操作
- 失败时记录：失败步骤、错误信息、截图路径
- 超时阈值：单步 10 秒，单用例 60 秒（可配置）

---

### D3.5：LLM Cognitive Walkthrough（可发现性测试）

**前提**：dynamic 或 full 模式 + Playwright 可用 + 应用已可达（D0 通过）。任一不满足 → 跳过。

**目的**：验证用户能否**发现**功能，而非功能是否存在。E2E 测试知道组件 ID 直接点击；认知走查模拟真实用户只看界面内容。

**执行流程**：

1. 从 role-profiles.json 提取角色列表
2. 从 experience-map.json 提取每个角色的核心操作线（取 frequency=高 的前 3 条）
3. 对每条操作线构造认知走查任务:
   - persona: "{角色名}，首次使用本系统"
   - goal: 操作线的 name（如 "完成首次提交"）
   - 期望步数: 操作线 continuity.total_steps
   - 禁止提供: 路由名、组件 ID、导航提示
4. 对每个任务:
   a. browser_navigate 到首页
   b. browser_snapshot 获取页面快照
   c. 基于快照内容（纯文本，不看 HTML 结构），决定下一步点击
   d. 记录每次点击的 ref 和原因
   e. 重复 b-d 直到目标完成或达到 max_clicks（期望步数 x 3）
   f. 记录: 完成/放弃、实际点击数、卡住点
5. 输出 cognitive-walkthrough.json

**卡住判定**：连续 2 次快照相同（点击无效果）或 3 次回退（找不到入口）。

**输出**：`.allforai/product-verify/cognitive-walkthrough.json`

`discoverability_score` = `expected_clicks / actual_clicks`（上限 1.0）。
`overall_discoverability` = 所有走查分数的算术平均。

**D4 汇总集成**：D3.5 结果在 D4 汇总中展示为独立段落，不影响 FIX_FAILING 分类。discoverability_score < 0.5 的走查标记为 WARNING。

**结果分类**（每个用例）：
- `pass` — 所有步骤成功
- `fail` — 某步骤失败（记录原因）
- `skip` — 前置条件不满足（如需要种子数据未准备）
- `error` — Playwright 自身错误（环境问题）

---

### D4：自动分类 + 批量确认

**自动分类规则**（基于错误特征建议分类，用户仍是最终决策者）：

| 错误特征 | 自动建议 | 理由 |
|---------|---------|------|
| HTTP 5xx 响应 | FIX_FAILING | 服务端错误 = 代码缺陷 |
| 404 on expected route | FIX_FAILING | 路由未实现 |
| 元素未找到 / 断言失败 | FIX_FAILING | 页面实现不完整 |
| Connection refused / timeout | ENV_ISSUE | 服务未启动或网络问题 |
| Database error in response | ENV_ISSUE | 数据库未初始化 |
| Auth redirect (unexpected) | FIX_FAILING | 权限配置错误 |
| CORS error | ENV_ISSUE | 开发环境跨域配置 |

**批量确认展示格式**：

```
## 动态验收结果

通过: {N}/{M} 用例

失败项（自动建议分类）:
| 用例 | 失败步骤 | 错误 | 建议分类 | 理由 |
|------|---------|------|---------|------|
| UC001 创建工单 | Step 3 | 500 Internal Error | FIX_FAILING | HTTP 5xx |
| UC005 导出报表 | Step 1 | Connection refused | ENV_ISSUE | 连接拒绝 |
| UC008 批量删除 | Step 2 | Element not found | FIX_FAILING | 元素缺失 |

→ 自动采纳全部建议分类（不停）
```

---

## Scope 模式（增量验收）

供 `task-execute` 每 Round 结束后调用，仅验证本 Round 涉及的任务和子项目。

**调用方式**：`/product-verify scope --tasks T001,T002,T003 --sub-projects api-backend`

**参数**：
- `--tasks` — 逗号分隔的 task_id 列表（来自 build-log.json 当前 Round 的任务）
- `--sub-projects` — 逗号分隔的子项目名（来自 build-log.json 当前 Round 涉及的子项目）

**执行范围**：

| 步骤 | Scope 模式行为 | 理由 |
|------|--------------|------|
| S1: Task → API 覆盖 | 仅检查 `--tasks` 中的任务 | 增量：只验证本 Round 新实现的 |
| S2: Screen → 组件覆盖 | **跳过** | 界面覆盖需全量比对才有意义 |
| S3: 约束 → 代码覆盖 | 仅检查 `--tasks` 关联的约束 | 增量：只验证本 Round 涉及的约束 |
| S4: Extra 代码扫描 | **跳过** | 反向扫描需全量，增量无意义 |
| S5: 交叉验证 | 仅审查 `--tasks` 中 covered 的项 | 增量：只交叉验证本 Round 的结果 |
| S6: 旅程级验证 | 如 use-case-tree.json 存在，仅验证包含本 Round 任务的用例 | 增量：不全量验证，只检查涉及当前 Round 任务的旅程 |
| Dynamic (D0-D4) | **跳过** | 动态测试留给 full 模式 |

**输出**：结果追加到 `static-report.json`（不覆盖之前的全量结果），同时返回给调用方（task-execute）用于写入 build-log.json 的 `verification` 字段。

---

## 输出文件结构

```
.allforai/product-verify/
├── traceability-matrix.json # S0: 双向追溯矩阵（task↔endpoint 形式化映射）
├── static-report.json       # S1-S6: 静态覆盖状态（含 journey_verification）
├── dynamic-report.json      # D2-D3: 动态测试结果
├── verify-tasks.json        # 待处理任务清单（IMPLEMENT / REMOVE_EXTRA / FIX_FAILING）
├── verify-report.md         # 可读版报告（含 innovation_coverage + 旅程级验证）
└── verify-decisions.json    # 用户决策日志（S4 EXTRA 归属 + D4 失败分类）
```

### static-report.json

```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "task_coverage": [
    {
      "task_id": "T001",
      "task_name": "{任务名}",
      "frequency": "高 | 中 | 低",
      "owner_role": "{角色名}",
      "status": "covered | missing_api | partial",
      "matched_routes": ["/api/tickets POST"],
      "notes": "缺少角色鉴权中间件"
    }
  ],
  "screen_coverage": [
    {
      "screen_id": "S001",
      "screen_name": "{界面名}",
      "status": "covered | missing_screen",
      "matched_components": ["src/pages/tickets/index.tsx"],
      "notes": ""
    }
  ],
  "constraint_coverage": [
    {
      "task_id": "T001",
      "constraint": "{约束描述}",
      "status": "covered | missing_constraint",
      "matched_code": ["src/middleware/auth.ts:42"],
      "risk_level": "高 | 中 | 低"
    }
  ],
  "extra_endpoints": [
    {
      "route": "/api/legacy/export GET",
      "file": "src/routes/legacy.ts:15",
      "decision": "add_to_map | mark_remove | ignore | pending"
    }
  ],
  "cross_model_review": {
    "enabled": true,
    "model": "deepseek",
    "reviewed_count": 12,
    "results": [
      {
        "source_step": "S1",
        "item_id": "T005",
        "item_name": "创建撤销",
        "claude_verdict": "covered",
        "deepseek_verdict": "stub",
        "deepseek_reason": "handler 仅包含 // TODO: implement revoke logic",
        "matched_file": "src/routes/revoke.ts:23",
        "resolution": "downgrade | keep | partial | pending"
      }
    ],
    "summary": {
      "agree": 10,
      "disagree": 2
    }
  },
  "innovation_coverage": {
    "core_tasks_total": 0,
    "core_tasks_verified": 0,
    "coverage_rate": "100%"
  }
}
```

### dynamic-report.json

```json
{
  "generated_at": "2024-01-15T11:00:00Z",
  "app_url": "http://localhost:{port}",
  "test_sequences": [
    {
      "case_id": "UC001",
      "case_name": "{用例名}",
      "source": "use-case-tree | auto-derived",
      "role": "{角色名}",
      "task_id": "T001",
      "result": "pass | fail | skip | error",
      "steps": [
        {
          "step": 1,
          "action": "{操作描述}",
          "status": "pass | fail",
          "error": null,
          "screenshot": ".allforai/product-verify/screenshots/UC001-step1.png"
        }
      ],
      "duration_ms": 3200,
      "failure_classification": "FIX_FAILING | ENV_ISSUE | DEFERRED | null"
    }
  ],
  "summary": {
    "total": 20,
    "pass": 15,
    "fail": 3,
    "skip": 1,
    "error": 1
  }
}
```

### verify-tasks.json

> 以下示例以虚构业务为背景，仅用于说明输出格式。

```json
[
  {
    "id": "VT-001",
    "type": "IMPLEMENT | REMOVE_EXTRA | FIX_FAILING",
    "task_id": "T001",
    "task_name": "{任务名}",
    "frequency": "高 | 中 | 低",
    "priority": "P0 | P1 | P2",
    "source_step": "S1 | S2 | S3 | S4 | D4",
    "description": "「创建工单」任务无对应 API 路由",
    "affected_roles": ["运营专员"],
    "suggested_action": "实现 POST /api/tickets 端点"
  }
]
```

旅程感知优先级提升：如 S6 发现某任务是旅程断裂点（CRITICAL_BREAK 或 INCOMPLETE_ENDING），该 IMPLEMENT 任务优先级自动提升为 P0，并附加断裂影响描述。

### verify-decisions.json

```json
[
  {
    "step": "S4",
    "item_id": "/api/legacy/export",
    "item_name": "旧版导出端点",
    "decision": "add_to_map | mark_remove | ignore",
    "reason": "用户备注（可选）",
    "decided_at": "2024-01-15T10:30:00Z"
  },
  {
    "step": "D4",
    "item_id": "UC003",
    "item_name": "运营创建撤销工单用例失败",
    "decision": "FIX_FAILING | ENV_ISSUE | DEFERRED",
    "reason": "数据库连接超时，非代码问题",
    "decided_at": "2024-01-15T11:15:00Z"
  }
]
```

**加载逻辑**：每个 Step 开始前检查 verify-decisions.json，已有决策的条目跳过确认直接沿用。`refresh` 模式下将文件重命名为 `.bak` 后重跑。

---

## 7 条铁律

1. **上游产物是不可逾越的真值** — 静态验收以 product-map.json + experience-map.json + design.json 为真值基准，不引入额外需求来源；有争议的功能先补充到产品地图，再重跑验收
2. **只报告不修改代码** — 发现缺口只标记到 verify-tasks.json，不自动生成、修改或删除任何实现代码
3. **4D 覆盖度闭环驱动** — 按 Data/Interface/Logic/UX 四维度聚合覆盖率，低于阈值自动生成针对性补充任务（标注缺失维度），直到闭环通过
4. **设计反向驱动验收** — experience-map 的 screen/action 反推最低数据需求，验证种子数据覆盖度和 UI 活性，设计产物既是正向生成的输入也是逆向验收的基准
5. **用户端主价值面从严验收** — 若 `experience_priority = consumer|mixed`，验收不能停留在“功能存在 + 测试能跑通”，还要验证是否达到成熟用户产品的基本体验门槛
5. **EXTRA 自动建议归属** — EXTRA 代码由 Agent 语义研判自动分类（infra/dev/ghost/undocumented），写入决策日志
6. **6V 诊断取代规则分类** — 动态失败由 LLM 从 6 个工程视角深度诊断根因，输出分类 + 修复线索，自动采纳写入决策日志
7. **全链路数据闭环** — 不只验证"代码有没有"，还验证数据流是否贯通、状态机是否完备、约束是否运行时生效
