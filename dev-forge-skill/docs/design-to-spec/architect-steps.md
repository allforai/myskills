# Architect Steps — design-to-spec

> This file is loaded by the Architect Agent. It covers Step 0 through Step 3.5.
> Architect's job: understand product → generate requirements.md + design.md.
> Architect does NOT generate tasks — that's the Decomposer's job.

---

## 前置: 概念蒸馏基线 + 两阶段加载

```
概念蒸馏基线（推拉协议 — 见 product-design-skill/docs/skill-commons.md §三.A）:
  .allforai/product-concept/concept-baseline.json → 自动加载，不存在则 WARNING
  → 提供产品定位、角色粒度、治理风格、ERRC 要点作为全局背景知识
  → 指导 requirements/design/tasks 生成时的业务判断
跨级原始数据拉取（推拉协议 §三.B）:
  product-mechanisms.json:
    - governance_styles[].downstream_implications → 决定是否生成审核模块/队列
    - governance_styles[].system_boundary         → 决定哪些功能只写集成接口
  role-value-map.json:
    - roles[].operation_profile                   → 决定路由策略、缓存策略、批量操作设计
Phase 1 — 加载索引（< 5KB）:
  project-manifest.json → 子项目列表
  task-index.json → 任务 id/name/frequency/module
  experience-map.json → 界面 id/name/action_count（可选）
  flow-index.json → 业务流 id/name（可选）
Phase 2 — 按需加载 full 数据（仅加载当前子项目需要的模块）
若 project-manifest.json 不存在 → 提示先运行 /project-setup，终止
若 product-map.json 不存在 → 提示先运行 /product-map，终止
加载 prune-decisions.json → 过滤: 仅 CORE 和 DEFER 任务进入范围
加载 forge-decisions.json → 读取 technical_spikes + coding_principles（存在时）
Load: forge-decisions.json → dev_mode（如有：bypass 类型、策略、隔离方式）
```

## 前置: 上游过期检测

加载输入文件时，比较关键上游文件的修改时间与本技能上次输出的生成时间：
- project-manifest.json 在 requirements.md / design.md / tasks.md 生成后被更新
  → ⚠ 警告「project-manifest.json 在 requirements.md/design.md/tasks.md 生成后被更新，数据可能过期，建议重新运行 project-setup」
- product-map.json 在 requirements.md / design.md / tasks.md 生成后被更新
  → ⚠ 警告「product-map.json 在 requirements.md/design.md/tasks.md 生成后被更新，数据可能过期，建议重新运行 product-map」
- 仅警告不阻断，用户可选择继续或先刷新上游

---

## Step 0: 模块映射验证

检查 manifest 中所有子项目的 assigned_modules
合并后与 task-index 的全量模块对照
未覆盖的模块：
  → 自动分配到最匹配的子项目（按模块类型推断），记录决策（不停）
→ 写入 `.allforai/project-forge/module-assignment-supplement.json`（追加分配条目）
→ **不修改** project-manifest.json（上游产物只读）
→ task-execute 加载时自动合并 manifest + supplement

---

## Step 1: Requirements 生成

每个 Agent 对其负责的子项目:
  a. 过滤该子项目的 assigned_modules → 获取模块内的任务列表
  b. 加载对应 full 数据（task-inventory + constraints + use-cases）
  b2. 读取 product-concept.json 的 `pipeline_preferences.infrastructure`（如存在），
      将基础设施需求（暗色模式/i18n/a11y 等）纳入需求和任务生成
  c. 按子项目类型（backend/admin/web-customer/web-mobile/mobile-native）
     应用差异化 requirements 模板
  d. 生成 requirements.md（4E 增强模板）:
     每个需求项包含：
     - 优先级 + 角色（基于上游产物全局上下文判定优先级 + owner_role）
     - Value 注释（← E4 Context，from task.value）
     - 用户故事（As a {role}, I want... So that...）
     - 验收条件（Given/When/Then，来自 use-case-tree）
     - Business Rules（← E3 Guardrails，from task.rules）
     - Error Scenarios（← E3 Guardrails，from task.exceptions）
     - SLA（← E3 Guardrails，from task.sla）
     - Prerequisites（← E3 Guardrails，from task.prerequisites）
     - Approval（← E3 Guardrails，from task.approver_role）
     - Audit（← E3 Guardrails，from task.audit）
     - Config（← E3 Guardrails，from task.config_items）
     - 非功能需求（来自 constraints + 子项目类型特有需求）
     - _Source: T001, F001, CN001_（← E2 Provenance）
     注: 字段不存在或为空时省略对应节，不生成空占位
  → 写入 .allforai/project-forge/sub-projects/{name}/requirements.md
  → 输出进度: 「{name}/requirements.md ✓ ({N} 需求项)」（不停，汇总到 Step 6）

---

## Step 2: 行为原语识别 → 共享组件规划

（仅前端子项目执行；后端子项目跳过此步直接进入 Step 3）

---

## Step 2.5: 组件规格导入（component-spec.json 存在时执行）

**触发条件**：`<BASE>/ui-design/component-spec.json` 存在
**跳过**：文件不存在 → 直接进入 Step 3（向后兼容）

**ui-design 产出消费方式**：
- `tokens.json` — 直接消费，生成 CSS 变量 / Tailwind theme / Flutter theme
- `component-spec.json` — 直接消费，task-execute 阶段实现共享组件
- `ui-design-spec.json` — 直接消费，屏幕布局、数据绑定、交互模式的确定性规格
- `screenshots/` — 视觉约束参考，读取 `<BASE>/ui-design/screenshots/` 目录下的截图，
  dev-forge 生成页面后可用 Playwright 截图与设计截图做视觉对比验证还原度（辅助验证，不阻断）

**Layer 1（通用，始终执行）**：
1. 读取 `component-spec.json` 的 `shared_components`
2. 对每个共享组件：
   a. 从 `primitive-impl-map.md` 查找当前技术栈的 primitives 实现
   b. 写入 design.md 的 `## 共享组件` 章节：
      - 组件名、出现屏幕、Props 接口
      - 交互原语 + 技术栈实现方案
      - 变体矩阵（size/state）
      - a11y 要求（role、aria 属性、键盘导航）
3. 对 `screen_components` 中的每个屏幕：
   将 used_shared + page_specific 写入对应页面规格
4. 生成键盘导航矩阵写入 design.md

**Layer 2（Stitch 增强，`stitch-index.json` 存在且有 success 屏幕时）**：
5. 读取 `stitch-index.json`
6. 对每个 `status=success` 的屏幕：
   a. 读取 `stitch/*.html`，提取精确 DOM 结构
   b. 提取内联样式 → design token 映射
   c. 补充 design.md 的组件结构（增强 Layer 1 的推断）
7. 记录 pipeline-decision

---

## Step 3a: 加载产品设计数据模型（可选增强）

检查 .allforai/product-map/ 下是否存在产品设计阶段的数据模型:
  - entity-model.json → ER 设计起点（实体、字段、关系、状态机）
  - api-contracts.json → API 设计起点（端点、请求/响应结构）
  - view-objects.json → 前端组件规格起点（VO 字段、Action Binding）
  - experience-dna.json → 体验差异化契约（DIFF-xxx 视觉规格，每个差异点的 widget_type/behavior/placement）

**存在** → 作为 design 生成的基础输入:
  - entities 从 entity-model.json 加载（而非从零推导）
  - endpoints 从 api-contracts.json 加载（而非从零推导）
  - 前端 screens 从 view-objects.json 提取字段定义和交互类型
  - 前端 screens 从 experience-dna.json 匹配 affected_screens/placement 含当前 screen 的 DIFF 项，注入页面规格的「体验差异化」子章节
  - 每个节点保留 source_entity, source_api, source_vo 字段溯源到 product-design 原始 ID
  - 输出进度: 「Step 3a ✓ 加载产品设计数据模型: {N} entities, {M} endpoints, {K} VOs」

**不存在** → 回退到 Step 3b 的从零推导（向后兼容）
  - 输出进度: 「Step 3a ⊘ 无产品设计数据模型，从零推导」

---

## Step 3b: Design 生成 + 技术丰富（API-first 策略）

**当 Step 3a 有数据时**: 在产品设计基础上补充技术细节:
  - 后端: + 索引策略 + 中间件链 + 错误响应结构 + 分页约束 + 幂等性设计
  - 前端: + 组件架构 + 状态管理 + 路由守卫 + 表单验证 Schema
  - 保持 source_* 字段溯源
**当 Step 3a 无数据时**: 完整的从零推导（当前 Step 3 行为不变）

**原则: 先表结构、后 API（按模块分批）、再展开**

> **大项目防退化规则**：后端模块数 > 10 时，API 设计必须按模块分批生成。
> 先完成所有数据模型（实体通常 < 30 个，一次性可控），
> 再逐模块生成 API 端点（每批 1 个模块，写入 design.md 后再做下一个模块）。
> 这样每批的注意力集中在 5-15 个端点，不会因为总量 100+ 而后期退化。

每个 Agent 对其子项目，基于 tech-profile 映射:
  所有端共通（最先生成，一次性完成）:
    entities → 数据模型 / 表结构设计（ER 图 Mermaid）
    entity.fields → 字段类型 + 约束 + 索引
    entity.relations → 外键 + 关联关系
  backend（数据模型之后，**按模块分批**）:
    对每个 assigned_module（从 project-manifest.json 读取）:
      该模块的 tasks → 接口设计（按目标协议生成）
      → 写入 design.md 对应模块章节
      → 完成一个模块再做下一个（不要一次性设计全部端点）
    约束冲突校验（每个接口生成后立即检查）:
      对每个接口定义，读取对应 task 的 rules + exceptions 字段:
      - 若 rules 含「本地处理」「离线」「不存库」「客户端缓存」等关键词
        → 该任务不应生成服务端接口，标记 `[LOCAL_ONLY]` 并跳过
      - 若 rules 含分页/筛选约束（「每页」「分页」「筛选」「排序」「搜索」）
        → 集合查询接口必须包含对应的分页/筛选参数
      - 若 exceptions 含特定错误场景 → 接口的错误响应必须覆盖
    集合查询参数强制提取:
      集合查询类接口生成时，强制读取对应 task 的:
      - main_flow → 提取筛选/搜索/排序操作描述
      - rules → 提取分页规则（默认批次大小、最大批次）、筛选字段、排序字段
      - 生成完整的查询参数文档（分页、排序、筛选）
      - 缺失时使用默认值: 每批 ≤ 20 条, 上限 50 条
    constraints → 中间件/拦截器链设计
    flows → 后端时序图
  前端类 (admin/web-customer/web-mobile):
    多后端服务连接推导:
      读取 manifest 中后端子项目/服务拓扑:
      - 单后端服务 → 生成单一 API 客户端实例
      - 多后端服务（不同地址/端口/协议）→ 自动推导多客户端架构:
        每个后端服务 → 1 个独立客户端实例（按服务职责命名）
        在 design.md 的「请求层」章节写明各实例的连接配置 + 负责的端点/接口范围
        tasks.md B1 中生成对应的客户端初始化任务
    screens → 页面路由 + 组件架构
    diff_contracts（Architect 只标注，不拆任务）→ 从 experience-dna.json 语义匹配当前 screen 的 DIFF 项，
      在 design.md 中做两件事（仅此两件，不生成 tasks）：
        1. 每个页面规格末尾追加「关联 DIFF」标注行：`_DIFF: DIFF-001 StageProgressIndicator, DIFF-002 TypingIndicator_`
        2. 在 design.md 末尾生成独立的「## Experience DNA 组件规格」章节，列出每个 DIFF 的完整 visual_contract（供 Decomposer 读取）

      > **Architect 禁止生成 B3.DNA 任务**——任务拆分是 Decomposer 的职责（Step 4）。
      > Architect 的 design.md 是信息源，Decomposer 读它来拆任务。

    **Decomposer 只做功能分解**：
    > Decomposer 只管拆 B0-B5 平铺的功能任务（happy path + `[DERIVED]` 异常）。
    > **不做**注意力分离拆分（HARDEN/DNA/POLISH/i18n 等）。
    > 那些是 Auditor 的工作——见 Step 4.3 的「注意力分离补充」。
    >
    > 原因：让 Decomposer 既拆功能又拆质量维度 = 7 个关注点 → 注意力分散。
    > Decomposer 做好一件事（功能分解），Auditor 做好一件事（质量补充）。

    screen.states → 界面四态设计（empty/loading/error/permission_denied）
    actions → 交互规格（引用已定义的后端接口）
    action.on_failure + exception_flows → 操作异常 UI 反馈设计
    action.validation_rules → 表单验证 Schema
    action.requires_confirm → 确认弹窗组件规格
    flows → 前端状态流转图
    ui-design-spec → 设计 token 引用
  mobile-native:
    screens → 导航栈 + Screen 组件规格
    screen.states → 界面四态设计（同上）
    actions → 原生交互规格（引用已定义的后端接口）
    action.on_failure + exception_flows → 原生异常 UI 反馈设计
    action.validation_rules → 表单验证规则
  按需生成的 4E 增强章节（字段存在时才生成）:
    task.rules（聚合）→ 按规则语义选择最适合的工程实现方式
    task.outputs.states + task.exceptions → 状态机设计（Mermaid stateDiagram）
    task.audit（聚合）→ 按审计需求选择最适合的工程实现方式
    task.outputs.notifications → 通知/事件设计（事件触发规则）
    task.approver_role → 审批流 API（审批端点 + 状态流转）
    task.config_items → 配置管理设计（配置端点/表）
    task.cross_dept_roles → 集成点设计（webhook/回调端点）
  按需生成的 Coding Principles 章节（forge-decisions.json 存在 coding_principles 时）:
    ## Coding Principles
    ### 通用原则
      coding_principles.universal → 逐条列出
    ### 项目特定原则
      coding_principles.project_specific → 逐条列出（含 spike/constraint 溯源标记）
    此章节写在 design.md 开头（数据模型之前），作为全文件的架构约束前言
  按需生成的 Technical Spike 集成章节（forge-decisions.json 存在 technical_spikes 时）:
    过滤 technical_spikes 中 affected_tasks 与当前子项目任务有交集的 spike
    每个匹配的 spike → 生成 Third-Party Integrations 子章节:
      - Vendor + SDK（from spike.decision.vendor / spike.decision.sdk）
      - Integration approach（from spike.decision.approach）
      - Implementation principles（from spike.implementation_principles → 逐条列出）
      - Affected endpoints / components（根据子项目类型推导）
      - spike.status = "tbd" → 标注 [PENDING: 技术方案待定，后续确认后补充]
  → 写入 .allforai/project-forge/sub-projects/{name}/design.md
  → 同时写入 .allforai/project-forge/sub-projects/{name}/design.json
  design.json 为 design.md 的结构化版本，供 Review Hub 规格 tab 渲染:
  ```json
  {
    "sub_project": "{name}",
    "type": "backend|frontend|mobile",
    "data_models": [
      {
        "table": "orders",
        "source_entity": "E001",
        "fields": [
          {"name": "id", "type": "uuid", "constraints": ["PK", "NOT NULL"], "required": true},
          {"name": "status", "type": "enum", "constraints": ["NOT NULL"], "required": true, "values": ["pending", "paid", "shipped"]}
        ],
        "indexes": [{"name": "idx_status", "columns": ["status"], "type": "btree"}],
        "state_machine": {
          "field": "status",
          "transitions": [
            {"from": "pending", "to": "paid", "trigger": "payment_confirmed"},
            {"from": "paid", "to": "shipped", "trigger": "ship_order"}
          ]
        }
      }
    ],
    "endpoints": [
      {
        "source_api": "API001",
        "method": "GET",
        "path": "/orders",
        "description": "列表查询",
        "params": [{"name": "page", "type": "integer"}, {"name": "status", "type": "string"}],
        "response": {"type": "paginated_list", "item_ref": "orders"},
        "errors": [{"code": 400, "message": "Invalid parameters"}]
      }
    ],
    "pages": [
      {
        "route": "/records",
        "name": "记录列表",
        "source_vo": "VO001",
        "components": ["DataTable", "SearchBar", "Pagination"],
        "states": {"empty": "暂无记录", "loading": "加载中...", "error": "加载失败"},
        "diff_contracts": ["DIFF-001"]
      }
    ],
    "middleware": [
      {"name": "auth", "description": "JWT 认证"},
      {"name": "audit", "description": "操作审计"}
    ],
    "tasks": [
      {"id": "B1", "name": "项目初始化", "status": "pending"},
      {"id": "B2", "name": "数据模型实现", "status": "pending"}
    ]
  }
  ```
  每个节点的 `source_*` 字段溯源到 product-design 的原始 ID（entity-model/api-contracts/view-objects 中的 ID）。
  无 source 数据时（Step 3a 加载失败），`source_*` 字段省略。
  → 输出进度: 「{name}/design.md + design.json ✓ ({N} 接口, {M} 页面)」（不停，汇总到 Step 6）
**生成顺序**: 后端 Step 3b 完成（API 定义就绪）后启动前端 Agent (Phase B)，与后端 Step 3.5-4.5 并行执行

---

## Step 3.5: Design 交叉审查（由后端 Agent 在 Phase A 内执行，OpenRouter 可用时）

后端 design.md 生成后，触发两项交叉审查:
审查 A — 接口设计审查 (GPT):
  提取 design.md 中所有接口定义（签名+请求/响应结构）
  调用: mcp__plugin_product-design_ai-gateway__ask_model(task: "structured_output", model_family: "gpt")
  审查: 协议惯例、数据结构一致性、缺失接口、错误响应统一
  输出: issues[] + missing[]
审查 B — 数据模型审查 (DeepSeek):
  提取 design.md 中 ER 设计（Mermaid + 字段定义）
  调用: mcp__plugin_product-design_ai-gateway__ask_model(task: "technical_validation", model_family: "deepseek")
  审查: 建模合理性、查询性能、关联完整性、命名一致性
  输出: violations[]
结果处理:
  有问题 → 在 design.md 末尾追加 ## Review Notes 附录（按问题严重度排列）
  无问题 → 不追加
  → 输出进度: 「Step 3.5 交叉审查 ✓ 接口 {N} issues, 数据模型 {M} violations」
OpenRouter 不可用 → 跳过，输出: 「Step 3.5 ⊘ OpenRouter 不可用，跳过交叉审查」
