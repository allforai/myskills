---
name: task-execute
description: >
  Use when the user wants to "execute tasks from tasks.md", "run implementation round",
  "start coding from task list", "execute batch tasks", "resume implementation",
  "任务执行", "执行开发任务", "按任务列表写代码", "继续实现", "断点续作",
  or needs to systematically execute atomic tasks from tasks.md with progress tracking,
  automatic execution strategy selection, and per-round incremental verification.
  Requires tasks.md (from design-to-spec) and project-manifest.json (from project-setup).
version: "1.3.0"
---

# Task Execute — 任务执行与追踪

> 加载 tasks.md → 逐 Round 执行 → 进度追踪 → 增量验证

## 目标

以 `tasks.md` 和 `project-manifest.json` 为输入，系统化执行原子任务：

1. **自动编排** — 按 Round 结构分组任务，自动推断执行策略
2. **委托执行** — 将实际代码编写委托给 superpowers skill
3. **进度追踪** — 实时更新 build-log.json，支持断点续作
4. **增量验证** — 每 Round 完成后自动触发 lint/test + 增量 product-verify

---

## 定位

```
design-to-spec（规格层）   task-execute（执行层）   testforge（验证层）
生成 tasks.md 任务列表     逐 Round 执行 + 追踪     全金字塔测试锻造
文档                      代码                     测试
```

**前提**：
- 必须有各子项目的 `tasks.md`（来自 design-to-spec）
- 必须有 `project-manifest.json`（来自 project-setup）
- 推荐有 `requirements.md`（增量验证用）

---

## 理论基础

本技能的工作流基于以下工程原则：

- **拓扑排序（Topological Sort）** — Batch 依赖解析：分析任务间依赖构建 DAG，动态生成执行顺序（不固定 B0-B5 六层结构）
- **增量构建验证（Incremental Build Verification）** — 每个 Round 仅验证变更文件，不全量重测，减少反馈延迟
- **文件级冲突检测（File-level Conflict Detection）** — 跨任务文件交集分析决定串行/并行策略，类似版本控制的合并冲突预判
- **Round-based 迭代开发** — 将大规模任务拆分为可管理的迭代批次，每批有明确的验证门禁
- **命令-执行分离（Command Pattern）** — 编排器（strategy）与执行器（agent）职责分离，编排器不直接修改代码

---

## 快速开始

```
/task-execute              # 从 Round 0 开始（或从 build-log 断点续作）
/task-execute round 2      # 仅执行指定 Round
/task-execute resume       # 从 build-log.json 断点续作（同无参数）
```

---

## 增强协议（WebSearch + 4E+4V）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：
- `"{framework} implementation patterns {year}"`
- `"{language} project structure conventions {year}"`

**4E+4V 重点**：
- **E3 Guardrails**: 执行任务时参照 `_Guardrails: T001.rules[1,2]_` 标注，确保业务规则落地
- **E4 Context**: `_Risk: HIGH_` 任务优先 review，执行后额外验证
- **创新任务优先级**：读取 `task-inventory.json` 的 `innovation_tasks` 字段，`protection_level=core` 的任务 → Round 1 优先执行
- **验证增强**：创新任务必须动态验收（不能只静态扫描），验证创新机制是否真正生效

### 增量 XV 验证 (Incremental Cross-Verification)

> 每个任务的执行不仅要通过编译/测试，还要通过**领域专家模型**审计与安全扫描。**`task-context.json` 承载的上游中间产物被视为「硬约束锚点」。**

1.  **任务级审计 (Task-Level XV)**：
    *   **基准**：`task-context.json` (Traceability/Provenance)。
    *   **硬约束检查**：审计模型检查代码是否 100% 落地了 `task.rules` 及其在 `product-design` 阶段被验证通过的业务逻辑。
    *   **模型路由**：遵循 `docs/skill-commons.md` 的**专家模型矩阵**（如 B2 调 GPT-4o，B1 调 DeepSeek）。
    *   **动作**：执行 Agent 编写代码后，指定领域模型家族检查代码是否偏离了原始需求和约束。
    *   **成本控制**：仅对 `_Risk: HIGH_` 或 `protection_level: core` 的任务触发完整 XV；其余任务仅做 Phase 2 本地审计。
    *   **Prompt 模板**：向专家模型发送 `{task-context.json 片段} + {实现代码} + {本地审计结果}`，要求输出 `PASS | FAIL | WARN` + 具体行号 + 修复建议。
    *   **分歧处理**：若 XV 与本地审计矛盾（如本地 PASS 但 XV FAIL），以 XV 结论为准，生成 `B-FIX` 修复任务。
    *   **降级**：OpenRouter 不可用时跳过 XV，输出标注 `XV_SKIPPED`，本地审计结果直接生效。
    *   **结果归档**：XV 审计结果写入 `task-context.json` 的 `xv_audit` 字段，含模型名、结论、耗时。
2.  **安全左移审计 (Forge DevSecOps XV)**：
    *   **动作**：强制扫描硬编码密钥、SQL 注入点、不安全的反序列化以及敏感信息泄漏。
    *   **工具集成**：模拟/调用 SAST 工具（如 gitleaks, semgrep）结果，并由 LLM 进行二次安全风险评估。
3.  **契约漂移监测 (Contract Drift Detection)**：
    *   **动作**：对于 B2 (后端 API) 任务，在 XV 审计时同步对比实际代码与 `design.json` 的差异。
    *   **逻辑**：若实现偏离了原定契约（如字段名微调、性能优化导致的结构变更），审计 Agent 必须判定为 `DRIFT`。
    *   **同步动作**：若 `DRIFT` 被确认为“合理演进”，则触发 **契约自动同步逻辑**（见下文）。
4.  **批次级审计 (Round-Level XV)**：
    *   **基准**：`design.json` 合约。
    *   **动作**：在 Batch 完成后，验证所有新增接口/组件是否符合设计文档中的 4D 规格。
5.  **修复轮次 (Fix Round)**：
    *   审计或安全扫描失败项自动生成 `B-FIX` 任务并立即尝试修复，直到通过 XV 审计。

### 契约漂移自动同步 (Contract Drift Auto-Sync)

> 当后端实现偏离设计时，自动确保两端“协商一致”。

1.  **演进识别**：XV 审计员发现代码与 `design.json` 不符时，提示用户：「检测到契约漂移，该变更属于：A.实现错误（需修复） B.架构演进（需同步下游） C.需要两端协商」。
2.  **契约更新**：若用户选择 B 或协商达成一致：
    *   Agent 自动更新全局 `design.json` 与 `.allforai/` 下的相关模型。
    *   自动触发 `design-to-spec` 增量更新受影响子项目的 `requirements.md` 与 `design.md`。
3.  **下游级联 (Cascading Tasks)**：
    *   自动为所有依赖该接口的前端子项目生成 `[B-CONTRACT-SYNC]` 任务并注入 `tasks.md`。
    *   任务标记为 `HIGH` 优先级，确保下游 Agent 在下一轮 Round 优先处理契约变更。

---

## build-log.json

进度追踪的核心数据结构：

```json
{
  "version": "1.0.0",
  "started_at": "ISO8601",
  "updated_at": "ISO8601",
  "innovation_tasks_summary": {
    "total": 3,
    "core": 2,
    "defensible": 1,
    "experimental": 0,
    "completed": 0,
    "core_completed": 0
  },
  "rounds": [
    {
      "round": 0,
      "name": "Monorepo Setup",
      "status": "pending | in_progress | completed | failed",
      "execution_strategy": "subagent-driven-development | dispatching-parallel-agents",
      "strategy_reason": "仅 3 个任务，串行更简单",
      "started_at": null,
      "completed_at": null,
      "tasks": [
        {
          "id": "0.1",
          "sub_project": "global",
          "title": "配置 monorepo workspace + 根配置文件",
          "status": "pending | in_progress | completed | failed | skipped",
          "started_at": null,
          "completed_at": null,
          "files_modified": [],
          "error": null
        }
      ],
      "quality_checks": {
        "lint": { "status": "pending | pass | fail | skipped", "output": null },
        "test": { "status": "pending | pass | fail | skipped", "output": null }
      },
      "abstraction_check": {
        "status": "skipped | clean | issues_found",
        "issues": [],
        "tasks_generated": []
      },
      "verification": {
        "status": "pending | pass | fail | skipped",
        "scope": { "task_ids": [], "sub_projects": [] },
        "issues": []
      }
    }
  ],
  "summary": {
    "total_tasks": 0,
    "completed": 0,
    "failed": 0,
    "skipped": 0,
    "current_round": 0
  }
}
```

**写入位置**：
- `.allforai/project-forge/build-log.json` — 全局索引（Round 状态 + 统计摘要，不含任务详情）
- `.allforai/project-forge/sub-projects/{name}/build-log-{name}.json` — 各子项目的任务详情

> **分文件策略**：全局 build-log.json 仅保存 Round 级状态和统计摘要（< 5KB），
> 每个子项目的任务详情（status、files_modified、error）写入独立文件。
> 这避免了单文件过大（历史上单文件 > 100KB 导致读写超时）。
> task-execute 加载时合并全局索引 + 当前 Round 涉及的子项目文件。

---

## 工作流

```
前置: 概念蒸馏基线 + 加载
  概念蒸馏基线（推拉协议 — 见 product-design-skill/docs/skill-commons.md §三.A）:
    .allforai/product-concept/concept-baseline.json → 自动加载，不存在则 WARNING
    → 提供产品定位、角色粒度、治理风格作为编码时的业务判断背景
  各子项目 tasks.md → 解析全部任务（id / sub_project / files / batch）
  project-manifest.json → 子项目列表 + 类型
  build-log.json（若存在 → resume 模式）
  task-context.json（如有）— 任务上下文预计算，含旅程位置、情绪上下文、约束溯源、消费者清单、验证建议

  ### 两阶段加载

  **Phase 1 — 索引加载**：
  若 `task-index.json`（来自 product-map）或 `tasks.json`（来自 design-to-spec）存在：
  - 读取索引获取任务 ID、batch 分配、子项目归属
  - 仅加载当前 Round 涉及的 batch 对应的 tasks.md 完整内容

  **Phase 2 — 按需加载**：
  - 当前 Round 的任务：加载完整 tasks.md 中对应 batch 的任务详情
  - 其他 Round 的任务：仅保留索引级信息（ID + 标题 + batch）

  **回退**：索引不存在 → 全量加载所有 tasks.md（向后兼容）
  ↓
前置: 上游过期检测
  加载输入文件时，比较关键上游文件的修改时间与本技能上次输出的生成时间：
  - tasks.md 在 build-log.json 生成后被更新
    → ⚠ 警告「tasks.md 在 build-log.json 生成后被更新，数据可能过期，建议重新运行 design-to-spec」
  - design.md 在 build-log.json 生成后被更新
    → ⚠ 警告「design.md 在 build-log.json 生成后被更新，数据可能过期，建议重新运行 design-to-spec」
  - 仅警告不阻断，用户可选择继续或先刷新上游
  ↓
Step 0: 初始化
  build-log.json 不存在 → 初始化:
    **Step 0.1: 按子项目分组加载**
    读取各子项目的 tasks.md，按子项目维度组织：
    - 每个子项目的任务独立追踪
    - build-log.json 中 tasks 数组的每个任务必须标注 `sub_project` 字段

    **Step 0.2: 按 Round 结构分组**
    分析 tasks.md 中任务的文件依赖和逻辑顺序，动态生成 Round 结构：
    - 无依赖的全局任务 → Round 0
    - Foundation 层任务 → Round 1（并行）
    - 业务任务按依赖拓扑排序 → Round 2+（自动检测可并行组）
    - 测试任务 → 最后 Round
    不固定 B0-B5 六层结构，按实际依赖图决定层数和并行度

    **Step 0.3: Round 自动分片（强制，质量优先）**

    > **核心原则：宁可多跑几轮，不可一次塞太多任务。质量优先于速度。**
    > Agent 注意力是有限的。任务越多，每个任务分到的注意力越少，代码越浅薄。
    > 控制每个子 Round 只有 1-3 个任务，让 Agent 集中全部注意力做深做透。

    对每个 Round 检查任务数量：
    - 任务数 ≤ 3 → 保持不变
    - 任务数 > 3 → 按以下规则自动拆分为子 Round（每个子 Round 1-3 个任务）：

    **拆分策略**：
    1. **按子项目拆分**（优先）：不同子项目的任务天然无文件交叉，拆分为独立子 Round
    2. **按模块拆分**（同子项目内任务仍超 3 个）：按业务模块分组，每组 1-3 个任务
    3. **按依赖链拆分**（模块内仍超 3 个）：按任务依赖图的拓扑层级拆分

    **不要担心 Round 数量多** — 多跑 10 个子 Round 花的时间，远少于后面修 30 个空壳回调的时间。

    **子 Round 命名**：`{parent_round}.{sub_index}`（如 2.1, 2.2, 2.3）
    **子 Round 间顺序**：同子项目内串行，不同子项目间并行

    写入 build-log.json（全部 pending）

  build-log.json 已存在 → resume:
    读取 summary.current_round
    增量检测: 重新解析各子项目 tasks.md，对比 build-log.json 已有 Round:
      发现新批次（如 B-FIX）不在 build-log.json 中
        → 追加为新 Round（round = max_round + 1）
        → 写入 build-log.json（新 Round 全部 pending）
      无新批次 → 跳过
    从第一个非 completed Round 继续
  确定起始 Round → 展示执行计划
  ↓
Step 0.5: 环境配置自动生成（首次执行或 .env 缺失时）

  **所有子项目的 .env 必须在写代码之前就绑好。** 不能等到 E2E 测试阶段才发现 .env 缺失。
  代码跑不起来的第一个原因往往是 .env 没配。

  **执行方式：LLM 分析项目 → 推导所需环境变量 → 从可用来源填充**

  Step 0.5.1: 项目环境检测（LLM 分析，不硬编码）

    对每个子项目，LLM 读取以下文件理解项目需要什么：
    - `.env.example` / `.env.sample` — 最权威的变量清单
    - `config.py` / `config.ts` / `nuxt.config.ts` / `app.config.dart` — 代码中读取了哪些环境变量
    - `docker-compose.yml` — 依赖了哪些服务（DB/Redis/MQ）
    - `package.json` / `requirements.txt` / `pubspec.yaml` — 依赖了哪些 SDK（推断需要哪些 API Key）
    - `forge-decisions.json` 的 `technical_spikes` — 已决策的三方服务

    LLM 从代码中提取所需环境变量清单，分类为：
    | 类型 | 示例 | 填充来源 |
    |------|------|---------|
    | 数据库连接 | DATABASE_URL | 本地服务检测（docker ps / pg_isready / mysql --ping / mongosh --eval） |
    | 认证服务 | 认证 URL/Key（因项目而异） | 本地服务检测（BaaS CLI status）+ forge-decisions |
    | API Key（LLM/搜索/支付等） | OPENROUTER_API_KEY, SERPER_API_KEY | shell 环境变量（$VARNAME）+ forge-decisions |
    | 内部服务地址 | API_BASE_URL, BACKEND_URL | 从 project-manifest 的 port 推导 |
    | 功能开关 | DEV_LLM_MOCK, DEBUG | 开发模式合理默认值 |
    | 其他 | 项目特有的变量 | 标注 TODO，留给用户手动填 |

  Step 0.5.2: 环境变量来源自动探测

    按优先级从高到低尝试填充每个变量：
    1. shell 环境变量（`echo $VARNAME`）— 用户已配置的全局变量
    2. 本地服务状态探测（LLM 根据项目依赖决定执行哪些）：
       - `docker ps` → 正在运行的 DB/Redis/MQ 端口
       - 数据库探测：`pg_isready`(PostgreSQL) / `mysql --ping`(MySQL) / `mongosh --eval`(MongoDB)
       - 缓存探测：`redis-cli ping`(Redis) / `memcached` 端口检测
       - BaaS CLI：若项目依赖 BaaS（如 Supabase/Firebase/Appwrite），执行对应 CLI status 命令获取连接信息
    3. forge-decisions.json → technical_spikes 中已确认的 vendor/sdk
    4. project-manifest.json → 各子项目的 port 配置
    5. 同项目其他子项目的 .env（如后端 .env 有 DB_URL，前端也可能需要 API_URL）
    6. `.env.example` 中的默认值（非敏感项）
    7. 无法推导 → 标注 `# TODO: 请手动填入`

  Step 0.5.3: 生成 .env 并验证

    - 有 `.env.example` → 基于它生成 `.env`（保留注释结构，填入推导值）
    - 无 `.env.example` → 基于 LLM 分析结果从零生成
    - 生成后立即验证：尝试启动子项目（`uvicorn` / `pnpm dev` / `flutter run`），
      如果启动失败且错误信息含 "missing" / "required" / "undefined" 环境变量名
      → 识别缺失变量 → 尝试从其他来源补充 → 重新生成
    - 验证通过 → 记录到 build-log.json（`env_configured: true`）

  ↓
Step 1: 执行策略推断（每 Round 开始时）
  解析当前 Round 全部任务的 Files 字段
  构建 file → [task_id] 映射
  判断:
    有文件交叉 OR 任务数 <= 2
      → subagent-driven-development（串行，防冲突）
    无交叉且分属不同子项目
      → dispatching-parallel-agents（并行，快）
  记录 round.execution_strategy + strategy_reason
  展示: "Round {N}: {任务数} 个任务，策略: {策略}（{reason}）"
  ↓
Step 1.5: B3 前端 UI 上下文准备（Round 2 的 B3 任务执行前）
  仅在当前 Round 包含 B3（前端 UI）任务时执行：

  1. 读取 `<BASE>/ui-design/component-spec.json`（如存在）
  2. B3 共享组件任务上下文追加：
     - 「使用 CSS 变量 / theme token，不硬编码颜色值。
       参考 ui-design-spec.md 的主题变体章节，确保 light/dark 切换。」
     - 「实现 component-spec.json 中标注的所有 variants（size/state）。」
     - 「注入 a11y 属性：按 component-spec.json 的 a11y.requirements 实现。」
  3. 读取 `<BASE>/ui-design/stitch-index.json`（如存在）
  4. 对关联了 Stitch HTML 的任务，注入：
     - 读取 `stitch/{screen_id}-{name}.html`
     - 「基于 Stitch 视觉稿结构，使用项目组件库和 design token 实现。
       保留布局结构，用框架原生方式重写。
       交互原语按 primitive-impl-map 实现：[primitives 列表]」
  5. 无 component-spec.json 或 stitch-index.json → 跳过，正常执行
  ↓
Step 1.7: CC6 API 契约绑定（Frontend → Server Contract Binding）
  仅在当前 Round 包含前端/移动端子项目任务时执行。

  **问题根因**：前端 agent 按 tasks.md 实现 API 调用时，会根据业务逻辑自行推断端点路径，
  但 server 可能未实现该端点（CRUD 只做了 3/5、admin 能审批但不能浏览等），导致 404。
  Server-first 执行顺序是必要条件但不充分 — 前端 agent 必须知道 server 实际注册了哪些路由。

  **执行方式**：
  1. 读取 server 路由注册文件（如 `server/internal/router/router.go`），提取已注册路由列表
  2. 将路由列表作为上下文注入每个前端/移动端任务的 agent prompt：

  ```
  ───── API 契约（来自 server router.go）─────
  以下是 server 已注册的全部路由。你的 API 调用**只能使用这些路由**。
  如果业务需要但路由不存在，你必须：
  1. 先在 server 端补充端点（router + handler + service）
  2. 然后再在前端写 API 调用
  禁止调用不存在的端点、禁止写 TODO 占位的 API 调用。

  {已注册路由列表，按 group 分组}
  ──────────────────────────────────────────
  ```

  3. 路由列表格式：按权限分组（public / consumer / merchant / admin），每行一条 `METHOD /path`
  4. 每个前端 Round 开始时重新读取 router.go（因为前序 Round 可能已新增路由）

  **补端点规则**：
  - 前端 agent 发现需要但不存在的端点时，直接在 server 端补充完整链路（router → handler → service → repository）
  - 补充的端点遵循 server 已有的代码模式
  - 补充后将新路由追加到路由列表上下文中（后续任务可用）
  - 记录到 build-log.json 的 `round.server_supplements[]`：
    ```json
    { "task_id": "B3.15", "method": "GET", "path": "/admin/products/:id", "reason": "admin 产品详情页需要" }
    ```

  **跳过条件**：当前 Round 仅包含 server 子项目任务 → 跳过
  ↓
Step 1.8: 上下文注入（Context Injection）
  当 `task-context.json` 存在时，为当前 Round 的每个任务注入上下文摘要。

  **注入格式**（附加在每个任务描述前）：

  ```
  ───── 任务上下文 ─────
  📍 旅程：「{use_case_name}」第 {step_index}/{total_steps} 步
     ⬅ 前序：{prev_task}  ➡ 后续：{next_task}
  😰 用户情绪：{emotion}（强度 {emotion_intensity}/5）— {design_implication}
  🔒 约束溯源：
     • {rule_text} ← {constraint_ref.id}({constraint_ref.name}): {constraint_ref.reason}
  📡 消费者：{consumers列表，含sub_project + screen_id}
  ⚡ 权重：{frequency_weight} 频率 + {risk_level} 风险
  🧪 验证建议：{verification_hint}
  🔗 业务流：「{flow_name}」第 {position_in_flow} 节点
     上游：{upstream_tasks}  下游：{downstream_tasks}
  ──────────────────────
  ```

  **注入规则**：
  1. `task-context.json` 不存在 → 跳过，行为与旧版一致（向后兼容）
  2. 某任务在 contexts 中无匹配 → 该任务不注入，正常执行
  3. 字段为 `null` 的行不显示（如无旅程位置则省略 📍 行）
  4. 注入内容作为任务 prompt 的**前缀**，不替换任务描述本身
  5. 并行执行时，每个 Agent 只注入自己负责的任务上下文

  **对执行行为的影响**：
  - emotion_context.emotion = "anxious" 或 "frustrated" → 实现时增加用户反馈（loading 状态、进度条、确认对话框）
  - frequency_weight = "critical" → 代码中添加性能注释 `// PERF: high-traffic path`
  - consumers 非空 → API 返回结构添加注释 `// CONTRACT: consumed by {sub_projects}`
  - verification_hint 含 "integration_test" → 自动在 Step 3 质量检查中标记需要集成测试

  **负空间补全（阶段转换思维）**：
  > 见 product-design-skill/docs/skill-commons.md §4.4 + dev-forge/docs/skill-commons.md §四
  编码时，每个任务的实现必须超越 design.md 中已列出的异常，主动补全：
  - 每个 API 调用 → 超时处理 + 重试策略 + 降级方案
  - 每个写操作 → 并发控制（乐观锁/幂等键）
  - 每个外部依赖 → 断路器/降级/回退
  - 每个用户输入 → 边界校验 + 注入防护
  - 每个状态流转 → 非法转换拦截
  design.md 中标注 `[DERIVED]` 的异常场景是 design-to-spec 阶段已推导的，务必实现；
  未标注的盲区由编码 Agent 在实现时自行补全。
  ↓
Step 2: 逐任务执行
  subagent-driven-development 模式:
    按 id 顺序逐个执行
    每任务:
      task.status = in_progress, started_at = now
      调用 /subagent-driven-development 执行该任务
      成功 → task.status = completed, files_modified 从 git diff 提取
      失败 → task.status = failed, error 记录
      更新 build-log.json（实时写入，不等 Round 结束）
  任务上下文注入：如 Step 1.8 已准备上下文摘要，将其作为每个任务 prompt 的前缀传递给执行 Agent。Agent 应根据上下文调整实现策略（防御式编码、性能优化、契约注释等），但不改变任务的功能范围。

  dispatching-parallel-agents 模式:
    按 sub_project 分组，每组内按 id 顺序
    调用 /dispatching-parallel-agents 并行执行各组
    收集结果 → 逐任务更新 build-log.json

  **异常场景补缺检测（每个 B2 任务执行后）**：
  > 执行 agent 在实现每个 B2 端点时，必须主动检测并补全以下异常场景：

  | 检测维度 | 补缺内容 | 示例 |
  |---------|---------|------|
  | **输入边界** | 空值、极值、非法格式、注入攻击 | 价格为负数、名称超长、SQL 注入 |
  | **权限变更** | 操作中途权限被撤销 | 商户被暂停后仍有未处理请求 |
  | **并发竞态** | 同一资源被多个请求同时操作 | 库存并发扣减、订单重复支付 |
  | **状态非法转换** | 不合法的状态流转请求 | 已取消订单再次发货 |
  | **外部服务失败** | 第三方 API 超时/错误 | 支付网关超时、短信发送失败 |
  | **资源不存在** | 引用的关联资源已删除/不存在 | 下单时商品已下架 |
  | **业务规则违反** | 违反 constraints.json 中的硬约束 | 超出每日限额、超出退款期限 |

  执行 agent 发现 design.md 中未覆盖的异常场景时：
  1. 在实现代码中直接补全异常处理（不等待，立即实现）
  2. 记录到 build-log.json 的 `round.exception_supplements[]`：
     ```json
     { "task_id": "B2.15", "type": "concurrent_race", "description": "库存扣减添加乐观锁", "files": ["service/order_service.go"] }
     ```
  3. 不生成额外任务（异常处理随端点一起实现）

  空壳追踪（Hollow Shell Tracking）:
    执行 agent 遇到需要第三方集成（OAuth SDK、支付 SDK、文件上传服务、
    WebSocket 实际发送、推送 SDK 等）但无法在当前任务内完成时：
    **严禁静默留空壳（onPressed: () {}）。** 必须：
    1. 在回调内写 TODO 注释说明缺什么：`// TODO: integrate Apple OAuth SDK`
    2. 记录到 build-log.json 的 `round.hollow_shells[]`：
       ```json
       { "task_id": "B3.05", "file": "login_screen.dart", "line": 42,
         "element": "Apple Sign-In button", "reason": "requires Apple Developer account setup",
         "integration_type": "oauth" }
       ```
    3. 在 Round 质量检查时汇总空壳数量，输出警告：
       「⚠ 本 Round 留下 {N} 个空壳交互，需后续集成任务补完」
    Phase 5 product-verify 和 fieldcheck SC-15 会检测这些空壳并生成修复任务。

  失败处理:
    单任务失败 → 记录 error，继续同 Round 其他无依赖任务
    后续任务依赖失败任务的产出文件 → status = skipped
  ↓
Step 3: Round 质量检查（三路并行）
  Round 全部任务完成（或部分 failed/skipped）后，使用 Agent tool 并行执行三项检查：
    ┌── Agent(lint): 运行 lint → quality_checks.lint 更新
    │     lint 失败 → agent 自动修复 → 重跑
    ├── Agent(test): 运行 test → quality_checks.test 更新
    │     test 失败 → 记录失败测试，不阻塞
    └── Agent(security): **运行安全扫描 (DevSecOps SAST)**
          - 扫描硬编码密钥 (Secret Scan)
          - 运行静态代码安全分析 (Semgrep/SonarQube 模拟)
          - 检查敏感数据泄漏 (PII Leak)
          - 结果记录到 build-log.json round.security_check
          - 严重问题 (HIGH/CRITICAL) → 自动生成 B-FIX 修复任务
    全部完成 → 聚合结果

  abstraction_check（仅 B2 / B3 Round 触发，B0/B1/B4/B5 跳过）:
    检查 shared-utilities-plan.json 是否存在（不存在则跳过整个 check）
    扫描本 Round 的 files_modified:

    检测 1: SU-xxx 已有 B1 实现，但本 Round 某任务又自行实现了相似逻辑
      → 严重度 HIGH → 生成 B-REFACTOR 任务，追加到该子项目 tasks.md

    检测 2: 本 Round ≥3 个任务各自实现了结构签名相似（>70%）的 helper
      （使用 code-tuner 结构签名算法：操作序列 Levenshtein distance）
      → 严重度 MEDIUM → 生成 B-SHARED 任务

    检测 3: 任务声明了 _Leverage: SU-xxx_ 但对应 import 未出现在实际代码中
      → 严重度 LOW → 记录到 verification.issues，不生成任务

    结果写入 build-log.json round.abstraction_check:
      { "status": "skipped|clean|issues_found", "issues": [...], "tasks_generated": [...] }

    issues_found → 展示「⚠ 抽象检查：{N} 个问题，已生成 {M} 个补充任务」
    不阻塞，自动继续 Step 4
  ↓
Step 4: Round 增量验证（存在性 + 正确性）
  quality_checks 完成后:
    收集本 Round 涉及的 task_id + sub_project
    写入 verification.scope

    **创新任务验证增强**（若 `innovation_mode=active`）:
      - 检测本 Round 是否有创新任务完成
      - `protection_level=core` 的创新任务 → 必须动态验收（S2 界面覆盖 + Dynamic Playwright）
      - 验证创新机制是否真正生效（如"场景流"的无限滚动 + 自动播放）

    === 第一层：存在性验证（"有没有"） ===

    调用 product-verify scope 模式:
      S1: Task → API 覆盖检查（仅 scope.task_ids）
      S3: 约束 → 代码覆盖检查（仅 scope.task_ids 关联的约束）
      S2: Screen → 组件覆盖检查（**core 创新任务必须**）
      Dynamic: Playwright 动态验证（**core 创新任务必须**）
      S4: 跳过

    === 第二层：正确性验证（"对不对"）— LLM 语义驱动 ===

    > 存在性验证只能回答"代码存在吗"，无法回答"代码层之间是否一致"。
    > 正确性验证由 LLM 读取多层实际代码，用语义理解判断是否对齐。
    > R0 跳过（仅脚手架）。R1+ 每 Round 必须执行。

    **核心原则：LLM 语义判断优先，不依赖固定规则**
    > 以下 CC1-CC4 是 LLM 的「审查视角」指引，不是机械式规则清单。
    > LLM 应当像一个资深全栈工程师一样，读懂代码意图后判断层间是否语义对齐。
    > 不同项目类型（电商/SaaS/社交/工具）的"对不对"标准不同，LLM 需结合业务上下文判断。
    > 举例给出的场景（如 snake_case vs camelCase）是帮助 LLM 理解判断方向，不是穷举所有情况。

    **触发条件**：当前 Round ≥ 1 且涉及 ≥ 2 个子项目
    **跳过条件**：Round 0（脚手架）或仅涉及 1 个子项目（无跨层可比对）

    **CC1: API 契约一致性**（server Round 有新 handler 时触发）
      LLM Agent 读取 server handler/DTO 文件和各前端 API module 文件，以全栈工程师视角判断：
      前后端连接时，接口契约是否会断裂？

      审查视角（举例，非穷举 — LLM 根据项目实际情况灵活扩展）：
      - 路由路径是否匹配？请求/响应结构是否对齐？字段命名转换是否有保障？

      严重度由 LLM 结合项目上下文判断：
      - CRITICAL — 连接必崩，无自动转换 | WARNING — 可能不匹配但有 fallback | OK — 一致
      → 输出: 「CC1 契约 ✓ ok:{N} warn:{M} critical:{K}」

    **CC2: 枚举/状态值一致性**（任何 Round 有状态相关代码时触发）
      LLM Agent 读取 server model 状态定义、设计文档状态值、前端状态映射代码，综合判断：
      server 返回的每个状态值，前端都能正确渲染和过滤吗？各前端之间是否统一？

      严重度由 LLM 结合渲染/过滤影响判断
      → 输出: 「CC2 状态值 ✓ 实体:{N} 一致:{M} 不一致:{K}」

    **CC3: 数据模型完整性**（server Round 有新 model 时触发）
      LLM Agent 读取设计文档实体定义、server model struct、前端类型定义，综合判断：
      设计要求的字段是否完整落地？server 与前端的字段映射是否正确？特殊类型（如 i18n JSONB）处理是否一致？

      严重度由 LLM 结合业务关键性判断
      → 输出: 「CC3 模型 ✓ 实体:{N} 完整:{M} 缺字段:{K}」

    **CC4: 业务规则落地验证**（B2+ Round 有 service 层代码时触发）
      LLM Agent 读取 requirements.md 中的明确业务规则和对应 service 层代码，用语义理解（不是字符串匹配）判断：
      规则是否被代码逻辑实现？（如"5次失败锁定" → 代码中有计数 + 锁定吗？还是只做了密码比对？）

      严重度由 LLM 结合安全/资金影响判断
         - INFO — 规则已实现但方式与设计不同（如用 Redis 而非数据库计数器）
      → 输出: 「CC4 规则 ✓ 规则:{N} 已落地:{M} 未落地:{K}」

    **CC5: Spec 实现完整性验证**（B2 Round 完成时触发）
      > **核心问题**：任务标记为 completed ≠ 任务 spec 中所有子端点都实现了。
      > 历史案例：B2.110 spec 写了 `GET list + POST messages + PATCH assign` 三个子端点，
      > 但实际只实现了 `GET list + PATCH status`，漏了 `POST messages`。任务仍被标记 completed。

      LLM Agent 读取本 Round 每个 completed B2 任务的 tasks.md 描述和对应的 router/handler 代码，逐条核对：
      - tasks.md 中描述的每个子端点（如 `GET list`, `POST :id/messages`, `PATCH :id/assign`）
      - 是否在 router.go 中有对应路由注册？
      - 是否在 handler 中有对应方法（非空壳）？

      审查方式：
      1. 从 tasks.md 提取任务描述中的端点列表（括号内的 HTTP 方法 + 路径模式）
      2. 在 router.go 中搜索对应路由
      3. 缺失 → `SPEC_NOT_IMPLEMENTED`

      严重度：
      - CRITICAL — 任务描述中的端点在 router 中完全不存在
      - WARNING — 路由存在但 handler 是空壳（仅返回 501/TODO）
      → 输出: 「CC5 实现完整性 ✓ 任务:{N} 子端点:{M} 已实现:{K} 缺失:{L}」

    === 正确性验证执行方式 ===

    CC1-CC5 使用 Agent tool 并行执行（5 个 Agent），与存在性验证的 product-verify scope 串行。

    每个 Agent 的 prompt 模板：
    ```
    你是正确性审计器。任务：执行 {CC维度} 验证。

    本 Round 涉及的子项目: {sub_projects}
    本 Round 修改的文件: {files_modified}

    执行步骤:
    1. 读取设计文档: {design_files}
    2. 读取实际代码: {code_files}（仅读本 Round 修改的文件及其直接关联文件）
    3. 像资深全栈工程师一样理解代码意图，判断层间是否语义对齐

    核心原则：
    - 你的判断基于语义理解，不是字符串匹配或固定规则
    - CC1-CC4 描述的是「审查视角」，告诉你从哪些角度看，不是穷举检查清单
    - 不同项目类型有不同的"对不对"标准，你需要结合业务上下文自主判断
    - 关注的是"连接时会不会断裂"，而不是"格式是不是完全一样"

    举例（帮助理解判断方向，不是唯一规则）：
    `refresh_token`(snake_case) 和 `refreshToken`(camelCase) 语义相同，
    但如果 server 用 `json:"refresh_token"` 而前端发送 `{ refreshToken: ... }`，
    且项目中没有自动命名转换中间件，这是 CRITICAL — 因为 JSON 序列化时会断裂。

    输出格式:
    {
      "dimension": "CC1|CC2|CC3|CC4",
      "findings": [
        {
          "id": "CC1-001",
          "severity": "CRITICAL|WARNING|INFO",
          "title": "简述",
          "design_says": "设计/规格说什么",
          "code_does": "代码实际做什么",
          "affected_files": ["server/...", "admin/..."],
          "fix_suggestion": "修复建议"
        }
      ],
      "summary": { "ok": N, "warning": M, "critical": K }
    }
    ```

    === 正确性验证结果处理 ===

    5 个 Agent 返回后，聚合结果：
    - CRITICAL 数 = 0 → correctness_check.status = "pass"
    - CRITICAL 数 > 0 → correctness_check.status = "fix_required"
      → 自动生成 B-CC-FIX 修复任务，注入当前 Round 或追加为下一 Round
      → **CRITICAL 修复后重跑正确性验证**（最多 2 轮），确认修复有效
      → 2 轮后仍有 CRITICAL → 记录为已知问题，展示给用户，继续（不停）
    - 仅 WARNING → correctness_check.status = "pass_with_warnings"
      → 记录到 build-log.json，不阻塞

    结果写入 build-log.json round.correctness_check:
    {
      "status": "skipped|pass|pass_with_warnings|fix_required",
      "cc1_api_contract": { "ok": N, "warning": M, "critical": K },
      "cc2_status_values": { "ok": N, "warning": M, "critical": K },
      "cc3_data_model": { "ok": N, "warning": M, "critical": K },
      "cc4_business_rules": { "ok": N, "warning": M, "critical": K },
      "cc5_spec_completeness": { "tasks": N, "sub_endpoints": M, "implemented": K, "missing": L },
      "findings": [...],
      "fix_tasks_generated": [...]
    }

    → 输出汇总: 「验证 ✓ 存在性: S1={N} S3={M} | 正确性: CC1={a} CC2={b} CC3={c} CC4={d} CC5={e} | CRITICAL:{total}」

    === 存在性 + 正确性统一结果 ===

    结果写入 verification.issues（合并存在性和正确性发现）
    verification.status = pass | fail（任一层有 CRITICAL 即 fail）
    展示验证结果（仅报告，不阻塞下一 Round — 但 CRITICAL 会触发自动修复）

    **上下文感知验证**：如 task-context.json 存在，验证时额外检查：
    - verification_hint = "integration_test" 的任务 → 检查是否生成了集成测试文件
    - consumers 非空的 API 任务 → 检查 API 返回结构是否包含契约注释
    - 不通过 → 生成 FIX 任务而非阻断

    **创新任务验证失败处理**：
      - core 创新任务验证失败 → ⚠ 警告「核心创新体验不完整，建议优先修复」
      - 记录到 build-log.json 的 verification.issues
  Round 结束:
    round.status = completed
    summary 更新: completed 计数, current_round++

  Round 结束后接缝冒烟（R1+ 含前后端代码的 Round 必须执行）:
    当本 Round 同时包含后端 + 前端任务（或后端 Round 完成后紧接前端 Round 开始前）：
    1. 启动后端 dev server（如果未运行）
    2. 对前端生成的 API 调用路径，用 curl 验证后端能响应（200，非 404/405）
    3. 对比前端代码中读取的字段名与后端 API 实际返回的字段名
    4. 有不匹配 → 立即修复（不等到 testforge Phase 才发现）
    目的: 在代码生成阶段就捕获接缝问题，不留到测试阶段

  前后端字段自动比对（多子项目项目必须执行）:
    当后端 + 前端代码都已生成时，LLM 自动执行：
    1. 从后端代码提取 API 响应字段名（读 DTO/serializer/response model）
    2. 从前端代码提取 API 消费字段名（读 model.fromJson / column key / template 绑定）
    3. 同一端点的字段名逐一对比
    4. 不一致 → 修前端（以后端为准，后端是 source of truth）
    此步骤替代手动跑 fieldcheck — 在代码生成阶段就对齐，不留到验证阶段

  → 进入下一 Round 的 Step 1
```

---

## Resume 语义

```
/task-execute resume 行为:

读取 build-log.json
增量检测（修复轮次发现）:
  重新解析各子项目 tasks.md
  对比 build-log.json 中已有 Round 的任务 id 集合
  tasks.md 中存在 build-log 未收录的批次（如 Phase 4.5 追加的 B-FIX）
    → 追加为新 Round（round = max_round + 1, status = pending）
    → 更新 build-log.json + summary.total_tasks
  无新批次 → 跳过

找到 summary.current_round
检查该 Round:
  round.status = in_progress
    → 从第一个非 completed 任务继续
  round.status = failed
    → 重试 failed 任务（跳过已 completed 的）
  round.status = completed
    → 推进到下一 Round

任务级判定:
  status = completed + files_modified 非空 → 跳过（已完成）
  status = failed → 重新执行
  status = skipped → 检查依赖任务是否已修复，是则重新执行
  status = in_progress → 视为中断，重新执行
  status = pending → 正常执行
```

---

## 执行策略推断规则

| 条件 | 策略 | 理由 |
|------|------|------|
| Round 内任务的 Files 有交叉（同一文件出现在多个任务中） | subagent-driven-development | 文件冲突风险，必须串行 |
| Round 内任务分属不同子项目且文件无交叉 | dispatching-parallel-agents | 天然隔离，可并行 |
| Round 内只有 1-2 个任务 | subagent-driven-development | 并行无意义 |

**检测方式**：解析 Round 内所有任务的 `Files:` 行，构建 `file → [task_id]` 映射。任一文件对应多个 task_id → 有交叉。

---

## 输出文件

```
.allforai/project-forge/
├── build-log.json                  # 进度追踪（全局）
└── sub-projects/{name}/
    ├── tasks.md                    # 输入（来自 design-to-spec）
    └── requirements.md             # 增量验证参考
```

---

## 5 条铁律

### 1. 执行委托，不自己写代码

task-execute 是编排层，实际代码编写委托给 superpowers skill（subagent-driven-development 或 dispatching-parallel-agents）。不直接生成业务代码。

### 2. build-log 实时更新

每个任务状态变更立即写入 build-log.json，不等 Round 结束。中断后可精确 resume。

### 3. 策略自动推断，不问用户

根据文件交叉检测自动选择串行/并行策略。用户无需理解策略差异。

### 4. 验证仅报告，不阻塞

Round 增量验证发现问题时展示给用户，但不阻塞下一 Round 执行。问题汇总到 build-log.json 供后续处理。

### 5. 失败隔离

单任务失败不终止 Round。仅跳过依赖该任务产出文件的后续任务，其余继续执行。

### 6. 禁止空壳代码

生成的 UI 组件中，**事件回调不允许为空**。如果一个按钮/输入框的 onPressed/onChanged 在当前任务范围内无法完整实现（如依赖未完成的上游任务），必须：
- 实现一个显式的 TODO 占位（如 `onPressed: () => showSnackBar("功能开发中")`），不是静默的空函数
- 在 build-log.json 中标记该任务为 `partial`（不是 `completed`），注明哪些回调待补
- 后续 Round 的任务列表自动包含"补全 {文件} 的 {回调}"任务

原因：空回调是"文件存在但功能不可用"的头号原因。65% 的产品还原度缺失来自于 UI 骨架有但回调为空。

### 7. 前端任务必须探测后端（Cross-Stack Awareness）

前端子项目的执行 agent 在写代码前，**必须先读取后端子项目的以下信息**：

```
1. 路由表：Grep 后端 router 文件，提取所有已注册端点（path + method）
2. 模型字段：Read 与当前任务相关的 model/entity 文件，提取实体字段列表
3. 响应格式：Read 对应 handler 的返回结构（或 DTO），确认字段名和嵌套层级
```

**用途**：
- 后端端点已存在 → 前端必须调用，不得留 TODO 或空回调
- 后端模型有字段 → 前端表单必须展示（除非产品明确说不需要）
- 后端响应格式 → 前端 service 层的解析代码必须匹配

**实战数据**：eshop 项目中 80%（12/15）的前端空壳是"后端已有端点但前端没接通"。
根因是前端 agent 不知道后端有什么 → 遇到不确定时就留 `() {}`。
加了这条铁律后，前端 agent 有了后端路由表作为输入，不再需要猜测。

**执行协议**：
- Round 0（项目初始化）完成后，自动提取后端路由表 → 写入 `.allforai/project-forge/api-routes.json`
- 后续 Round 的前端任务 agent prompt 中自动注入该路由表
- 每个 B2 Round 结束后更新路由表（后端可能新增了端点）

**与 fieldcheck 的关系**：
- 铁律 7 是"写代码时就知道后端有什么"→ 预防
- fieldcheck SC-1~SC-15 是"写完代码后检查有没有接错"→ 检测
- 两层互补，预防优于检测
