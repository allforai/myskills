---
description: "项目锻造全流程：setup → spec → build → verify。模式: full / existing"
---

# Project Forge — 项目锻造全流程编排



> **跨插件调用约定**：本命令是「导航员」。
> - Phase 1-5, 7-8 在本插件内执行，通过 `./skills/` 或 `./commands/` 路径加载。
> - Phase 6（demo-forge）为独立插件 `demo-forge-skill/`，提示用户运行 `/demo-forge design`。
> - Phase 4（任务执行）调用 `task-execute` skill，自动编排 superpowers 技能。
> - Phase 5（验证闭环）产品验收 + testforge E2E 链验证 + deadhunt + fieldcheck → 修复任务 → 回归。
> - 各阶段产物通过 `.allforai/` 目录作为层间合约。

### ⚠️ 阶段→技能速查（必看）

> **Phase 4 是 task-execute（写代码），不是 product-verify（验收）。**
> product-verify 属于 Phase 5。不要混淆！

| Phase | 技能文件 | 做什么 | 完成标志 |
|-------|---------|--------|---------|
| 1 | _(内嵌本文)_ | 技术风险调研 | `forge-decisions.json` 有 `technical_spikes` |
| 2 | `skills/project-setup.md` | 拆子项目 + 选技术栈 | `project-manifest.json` 存在 |
| 3 | `skills/design-to-spec.md` | 产品设计 → 规格文档 + 共享工具分析 | 每子项目有 `requirements.md` + `design.md` + `tasks.md` + `shared-utilities-plan.json` 存在 |
| **4** | **`skills/task-execute.md`** | **按 tasks.md 逐任务写业务代码（R0 含项目初始化）** | **`build-log.json` 存在且 CORE 任务 completed** |
| 5 | `skills/product-verify.md` + `commands/testforge.md` + `commands/deadhunt.md` + `commands/fieldcheck.md` | 4-Agent 并行扫描 + 统一修复回归 | `verify-tasks.json` 无 IMPLEMENT/FIX_FAILING + `validation-report-summary.md` + `field-report.md` 存在 |
| 6 | _(外部: demo-forge 插件)_ | 演示数据方案 | `demo-plan.json` 存在 |
| 7 | `commands/testforge.md` | 跨端验证（条件执行） | E2E 通过率 ≥ 80% |
| 8 | _(内嵌本文)_ | 最终报告 | `forge-report.md` |

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 新项目，从头执行全流程
- **`full existing`** → 已有项目，gap 模式（扫描代码 → 仅补缺）

## 用户端导向继承（新增）

若上游 `product-map.json` 含 `experience_priority.mode = consumer | mixed`，则本编排器在 Phase 3-5 自动切换到用户端优先标准：

- Phase 3 (`design-to-spec`) 不得只生成“页面 + API + 表单”任务
- Phase 4 (`task-execute`) 不得把“页面能开 + API 通”当作完成
- Phase 5（验证闭环）需要优先拦截明显的运行时空壳、接缝断裂和 demo 级假完成；完整的用户端成熟度验收仍由 `product-verify` / `testforge` 承担

这不是新增分叉流水线，而是对同一条主流程施加不同的完成标准。

## 八阶段架构

```
┌─────────────────────────────────────────────────────────────┐
│                  Project Forge (项目锻造)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 0: 产物检测 + 模式路由 + Preflight 偏好收集           │
│  ↓                                                          │
│  Phase 1: 技术风险调研 (technical-spike)                     │
│    自动检测非 CRUD 技术点 → WebSearch 调研 → 方案对比        │
│    输出: forge-decisions.json → technical_spikes              │
│  ↓ 质量门禁: 每项 spike 已确认或标记 TBD                    │
│  Phase 2: 项目引导 (project-setup)                          │
│    交互式: 拆子项目 + 选技术栈 + 分模块                     │
│    输出: project-manifest.json                               │
│  ↓ 质量门禁: ≥1 子项目，每个有技术栈                        │
│  Phase 3: 设计转规格 + 共享层分析 (design-to-spec)           │
│    读产品设计产物 → 按子项目生成 spec → 共享工具分析+注入    │
│    输出: requirements.md + design.md + tasks.md              │
│          + shared-utilities-plan.json + tasks-supplement.json │
│  ↓ 质量门禁: 每子项目 3 份 spec + shared-utilities-plan     │
│  Phase 4: 任务执行 (task-execute)                             │
│    R0 项目初始化 → R1 基础设施 → R2 业务 → R3 集成 → R4 测试│
│    自动编排: 策略推断 → 委托执行 → 进度追踪 → 增量验证      │
│  ↓ 质量门禁: CORE 任务完成，lint 通过                       │
│  Phase 5: 验证闭环 + 完整性（4-Agent 并行扫描）              │
│    抽象门禁 → [product-verify ∥ testforge ∥ deadhunt ∥       │
│    fieldcheck] → 统一修复 → 回归                             │
│  ↓ 质量门禁: 修复项 = 0 或记录为已知问题继续                │
│  Phase 6: 演示数据方案 (demo-forge design)                   │
│    代码稳定后设计演示数据，提示运行 /demo-forge design       │
│    输出: demo-plan.json                                      │
│  ↓ 质量门禁: demo-plan.json 存在（或跳过）                  │
│  Phase 7: 跨端验证 (testforge) — 条件执行                    │
│    仅当 Phase 5 被跳过时执行                                  │
│    业务流 → 跨端场景 → Playwright / Maestro                   │
│  ↓                                                          │
│  Phase 8: 最终报告                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 0：产物检测 + 初始化 + Preflight 偏好收集

### 产物探测

扫描以下目录，判断前置条件和已有产物：

| 阶段 | 完成标志 |
|------|----------|
| product-design | `.allforai/product-map/task-inventory.json` 存在且 task 数 > 0 |
| technical-spike | `forge-decisions.json` 存在且 `technical_spikes` 数组长度 > 0 |
| project-setup | `.allforai/project-forge/project-manifest.json` 存在 |
| design-to-spec | `.allforai/project-forge/sub-projects/*/tasks.md` 存在且 `shared-utilities-plan.json` 存在 |
| task-execution | `.allforai/project-forge/build-log.json` 存在 |
| product-verify | `.allforai/product-verify/verify-report.md` 存在 |
| deadhunt | `.allforai/deadhunt/output/validation-report-summary.md` 存在 |
| fieldcheck | `.allforai/deadhunt/output/field-analysis/field-report.md` 存在 |
| demo-forge design | `.allforai/demo-forge/demo-plan.json` 存在 |
| testforge E2E | `.allforai/testforge/testforge-report.md` 存在且含 E2E chain 结果 |

### 前置检查

**product-design 产物必须存在**：
- 检查 `.allforai/product-map/product-map.json`
- 不存在 → 输出「请先完成产品设计流程（/product-design full），再运行项目锻造」，终止

若 `product-map.json` 中存在 `experience_priority`，Phase 0 需要把它写入 `forge-decisions.json`，作为后续 Phase 的执行偏置来源。

若 `experience_priority.mode = consumer` 或 `mixed` 且 `project-manifest.json` 已存在，Phase 0 还需推导 `consumer_apps` 列表（从 sub_projects 中筛选面向终端用户的子项目：type=web-customer/web-mobile 直接归入；type=mobile-native 按面向角色判断，consumer→归入，merchant/admin→排除），写入 `forge-decisions.json` 的 `consumer_apps` 字段。若 project-manifest 尚未生成（Phase 2 才产出），则 design-to-spec 初始化时推导并回写。

### 规模提醒

产物探测时顺便检查规模（从 task-inventory.json 的 task 数 + project-manifest.json 的 sub_project 数）：
- task 数 > 200 或 sub_project 数 > 6 → 输出「项目规模较大，design-to-spec 将自动启用模块分批处理」
- task 数 > 500 → 输出「超大型项目。如未在 product-design 阶段拆分，建议先拆分再继续」

仅提醒不阻断。

### 模式处理

**full 模式**：从 Phase 1 开始，逐阶段执行。
**full existing**：Phase 2 的 project-setup 以 existing 模式运行（扫描代码）。

### 交互模式检测

读取 `.allforai/product-concept/product-concept.json` 中的 `__orchestrator_auto` 字段：
- `__orchestrator_auto: true` → **自动模式**：推荐方案自动采纳，决策点零停顿
- `__orchestrator_auto: false` 或字段不存在 → **交互模式**：每个决策点展示推荐后等待用户确认或调整

> 注意：「Phase 转换零停顿」铁律仍然有效——Phase 之间不问"继续？"。交互模式只影响 **决策点**（技术选型、Spike 方案选择），不影响阶段流转。

将检测结果写入 `forge-decisions.json` 的 `forge_run.interactive` 字段：`true`（交互）或 `false`（自动）。

### 闭环输入审计

> 见 `product-design-skill/docs/skill-commons.md`「§八 闭环输入审计」。

交互模式下收集用户决策（技术选型、Spike 方案、Preflight 偏好）时，每个确认后执行闭环审计。重点关注**技术闭环**（选了技术栈，运维/监控/部署谁管？）和**凭证闭环**（需要外部服务，Key 从哪来？sandbox 怎么配？）。

### 外部能力快检

> 统一协议见 `product-design-skill/docs/skill-commons.md`「外部能力探测协议」。

检测本流水线涉及的外部能力并输出状态：

| 能力 | 探测方式 | 重要性 | 降级行为 |
|------|---------|--------|---------|
| Playwright | Playwright browser automation 可用性（任一可用即就绪） | Phase 5-8 必需 | 阻塞验证阶段，提示安装 |
| Maestro | `which maestro` CLI 可用性（Bash 检测） | mobile-native 子项目必需 | Playwright 降级（仅测 Web 端点）|
| OpenRouter (MCP) | `cross-model API (e.g., OpenRouter)` 可用性 | 可选 | 跳过 XV 交叉验证 |

**输出格式**：

```
外部能力:
  Playwright        ✓ 就绪     Web E2E 验证 + 产品验收（Phase 5-8）
  Maestro           ✗ 未就绪   Mobile-native E2E 验证（Phase 5-8）
  OpenRouter (MCP)  ✗ 未就绪   XV 交叉验证（可选，跳过）
```

**交互式安装引导**（统一协议见 `product-design-skill/docs/skill-commons.md`）：

- **Playwright 未就绪**：Phase 0 输出提示，不阻塞 Phase 1-4。进入 Phase 5 前输出安装提示并声明推荐选项（「是，帮我安装」/「跳过」/「查看详情」）
- **OpenRouter 未就绪**：提示运行 `/setup` 配置（Key 存储在插件 `.mcp.json`，不污染 shell 环境变量），不阻塞

### 初始化决策追踪

创建/更新 `.allforai/project-forge/forge-decisions.json`：

```json
{
  "forge_run": {
    "mode": "full | existing",
    "started_at": "ISO8601",
    "product_source": ".allforai/product-map/product-map.json"
  },
  "preflight": {
    "inferred_endpoints": ["backend", "admin", "web-customer", "mobile-native"],
    "tech_preferences": {
      "backend": {
        "template_id": "go-gin",
        "architecture": "three-layer",
        "cqrs": false
      },
      "admin": {
        "template_id": "nextjs",
        "state_management": "zustand",
        "server_cache": "tanstack-query"
      },
      "web-customer": {
        "template_id": "nextjs",
        "state_management": "zustand",
        "server_cache": "tanstack-query"
      },
      "mobile-native": {
        "template_id": "flutter"
      }
    },
    "monorepo_tool": "manual",
    "auth_strategy": "jwt",
    "confirmed_at": "ISO8601"
  },
  "technical_spikes": [
    {
      "id": "TS001",
      "category": "ai_llm | speech | payment | push | algorithm | realtime | file_storage | oauth",
      "title": "描述性标题",
      "affected_tasks": ["T002", "T004"],
      "dimensions": ["vendor", "architecture", "cost", "compliance"],
      "options_researched": [
        {
          "label": "方案名 (推荐)",
          "vendor": "azure | google | openai | ...",
          "components": { "stt": "Azure STT", "pronunciation": "Azure Pronunciation Assessment" },
          "pros": ["优势1", "优势2"],
          "cons": ["劣势1"],
          "cost_model": "$1/audio-hour",
          "complexity": "low | medium | high",
          "sdk": "package-name",
          "compatibility": "与已选技术栈兼容度说明"
        }
      ],
      "decision": {
        "selected": "方案名",
        "vendor": "azure",
        "sdk": "package-name",
        "approach": "集成方案一句话描述",
        "notes": "用户补充说明"
      },
      "implementation_principles": [
        "该 spike 的具体编码约束，如：所有 AI 调用统一通过 ai_client service",
        "共用模式说明，如：T002/T004 共用同一套 streaming 逻辑"
      ],
      "status": "confirmed | tbd"
    }
  ],
  "coding_principles": {
    "generated_at": "ISO8601",
    "universal": [
      "相同场景必须使用相同套路（同类功能共用 service/helper，禁止各自实现）",
      "底层工具库不重复（HTTP client / error handler / logger 全项目统一一份）",
      "成熟三方优先（有维护良好的库就用，不自行实现）",
      "每个外部服务调用封装为独立 service，业务层不直接调用 SDK"
    ],
    "project_specific": [
      "基于项目特点推导的原则，如：所有 AI 调用需 content filter 中间件",
      "基于约束推导的原则，如：支付操作必须写审计日志（CN005）"
    ]
  },
  "phase_status": {
    "phase_1": "pending | completed | skipped",
    "phase_2": "pending | completed | skipped",
    "phase_3": "pending | completed | skipped",
    "phase_4": "pending | in_progress | completed",
    "phase_5": "pending | in_progress | static_pass | completed | not_tested",
    "phase_6": "pending | completed | skipped",
    "phase_7": "pending | completed | skipped",
    "phase_8": "pending | completed"
  },
  "decisions": []
}
```

### Preflight 技术偏好收集

> 目标：前置收集所有纯偏好问题，避免后续阶段中断。

**Step 2a: 推断端类型**

读取 `.allforai/product-map/role-profiles.json`：

| 条件 | 推断端类型 |
|------|-----------|
| 始终 | `backend` |
| 有 consumer 类角色 | `web-customer` |
| 有 producer / admin 类角色 | `admin` |
| 有 mobile 标记 或 experience-map 中有 mobile 界面 | `mobile-native` |

按端类型过滤可选技术栈。

**Step 2b: 生成推荐配置**

基于以下规则生成推荐值（优先级：用户偏好 > 智能推断 > 默认值）：

| 配置项 | 推荐规则 |
|--------|---------|
| 后端技术栈 | 用户偏好（如 MEMORY 记录 Go+Gin → `go-gin`）> stacks.json 中 type=backend 第一个 |
| 后端架构 | product-map 聚合根 > 5 或跨域交互多 → DDD；否则 → 三层架构 |
| DDD 时 CQRS | 默认 false |
| 前端技术栈 (admin/consumer) | 后端选 Vue 系 → Nuxt；否则 → Next.js |
| 移动端技术栈 | 用户偏好（如 Flutter）> flutter（默认） |
| Monorepo 工具 | 全 TS → pnpm-workspace；混合语言 → manual；子项目 > 4 → turborepo |
| 状态管理 | React 系 → Zustand；Vue 系 → Pinia；Angular → 跳过 |
| 服务端缓存 | TanStack Query（React / Vue 通用） |
| 认证策略 | 多角色权限 → JWT；简单场景 → Session |

**Step 2c: 展示推荐配置 + 自动确认**

向用户展示推荐配置表：

~~~markdown
## Preflight — 技术偏好

从产品地图分析，你的产品需要 {N} 个端：

| 端 | 推荐技术栈 | 理由 |
|---|---|---|
| 后端 API | {stack} ({arch}) | {reason} |
| 管理后台 | {stack} | {reason} |
| 消费者 Web | {stack} | {reason} |
| 移动端 | {stack} | {reason} |

| 配置项 | 推荐值 |
|---|---|
| Monorepo | {tool} |
| 状态管理 | {lib} |
| 服务端缓存 | {lib} |
| 认证策略 | {strategy} |
~~~

- **自动模式**：自动采纳推荐配置，写入 forge-decisions.json，继续（不停）
- **交互模式**：展示推荐配置表，等待用户确认或调整。用户确认后写入 forge-decisions.json，继续

**Step 2d: 写入 forge-decisions.json**

将确认后的配置写入 `forge-decisions.json` 的 `preflight` 字段（结构见「初始化决策追踪」中的 JSON schema）。

---

输出探测结果 + 执行计划（含 preflight 结果摘要）。
- **自动模式**：自动开始（不停）
- **交互模式**：等待用户确认后开始

---

## Phase 1：技术风险调研（Technical Spike Analysis）

> 目标：自动检测产品中的非 CRUD 技术点，通过 WebSearch 调研现有方案，向用户呈现 2-3 个方案的对比表格，由用户选择。

### 跳过条件

若 task-inventory.json 中无任何命中关键词 → 输出「未检测到非 CRUD 技术点，跳过 Phase 1」，直接进入 Phase 2。

### existing 模式差异

existing 模式下，Step 1 之前先扫描项目已有依赖文件（`package.json` / `go.mod` / `pubspec.yaml` / `requirements.txt`），识别已安装的 SDK：
- 已有 SDK 覆盖的 spike → 跳过调研，直接记录为 confirmed（vendor/sdk 从依赖文件读取）
- 未覆盖的 spike → 正常执行 Step 2-4 调研流程

### Step 1: 自动检测

扫描 task-inventory.json 中每个 task 的 `task_name` + `main_flow[]` + `exceptions[]` + `rules[]` 字段，匹配以下关键词，归类为 spike 项：

| 类别 | 检测关键词（中） | 检测关键词（英） |
|------|----------------|-----------------|
| **ai_llm** | AI、Prompt、生成内容、智能回复、模型、GPT、大模型 | AI, LLM, GPT, generate, model, prompt |
| **speech** | 语音、发音、音素、识别、跟读、朗读、TTS、语音合成 | speech, pronunciation, phoneme, STT, TTS, voice |
| **payment** | 订阅、付费、支付、退款、购买、IAP、扣费 | payment, subscription, refund, purchase, IAP, billing |
| **push** | 推送、通知提醒、FCM、APNs | push notification, FCM, APNs, remind |
| **algorithm** | 记忆曲线、推荐算法、排行榜、A/B测试、个性化 | algorithm, recommendation, ranking, A/B test, spaced repetition |
| **realtime** | 实时、流式、streaming、WebSocket、长连接 | real-time, streaming, WebSocket, SSE, live |
| **file_storage** | 上传、下载、图片、视频、音频、文件、OSS、存储 | upload, download, file, image, video, audio, storage, S3 |
| **oauth** | 第三方登录、微信登录、Apple登录、OAuth、社交登录 | OAuth, social login, WeChat, Apple Sign-In, Google Sign-In |

同时扫描 constraints.json 中 `enforcement: "hard"` 的约束，若涉及支付/审计/合规 → 补充到对应 spike。

**去重合并**：多个 task 命中同一类别 → 合并为单个 spike 项，`affected_tasks` 列表汇总。

### Step 2: WebSearch 调研（并行）

各 spike 类别互不依赖，execute parallel research。dispatch N parallel agents（N = 检测到的 spike 数量），每个 Agent 负责一个 spike 类别的 2-3 轮 WebSearch + 方案提炼。

每个 Agent 的 prompt 模板：

~~~
你是技术调研代理。

任务: 调研 {spike_category} 的技术方案
项目技术栈: {backend_framework} + {mobile_framework}
受影响任务: {affected_tasks_summary}

执行:
1. 用 WebSearch 执行 2-3 轮搜索（搜索词见下方）
2. 从搜索结果提炼 2-3 个可行方案
3. 返回每个方案的：名称、核心能力、与技术栈兼容性、SDK/库、集成复杂度、成本模型、优势（2-3条）、劣势（2-3条）、推荐理由

搜索词: {对应类别的搜索词模板，替换变量后}
~~~

所有 Agent 返回后，编排器汇总各 spike 的方案数据，统一进入 Step 2.5（XV）和 Step 3（对比表）。

**搜索词生成规则**（基于 preflight 已选技术栈动态拼接）：

| 类别 | 搜索词模板 |
|------|-----------|
| ai_llm | `"{backend_framework} streaming LLM response {year}"`、`"LLM API comparison pricing {year}"`、`"AI content moderation API {year}"` |
| speech | `"pronunciation assessment API phoneme level {year}"`、`"speech recognition API comparison {backend_language} {year}"`、`"{vendor_A} vs {vendor_B} speech API"` |
| payment | `"{mobile_framework} in-app purchase {year}"`、`"subscription management service comparison {year}"`、`"RevenueCat vs Adapty vs {alt}"` |
| push | `"{mobile_framework} push notification setup {year}"`、`"FCM APNs unified push service {year}"` |
| algorithm | `"{algorithm_name} implementation {backend_language}"`、`"{algorithm_name} open source library comparison"` |
| realtime | `"WebSocket vs SSE {backend_framework} {year}"`、`"real-time communication {backend_framework} best practice"` |
| file_storage | `"file upload service comparison S3 R2 {year}"`、`"{backend_framework} file upload best practice"` |
| oauth | `"{mobile_framework} OAuth social login {year}"`、`"Apple Google WeChat login integration {year}"` |

其中 `{backend_framework}` / `{backend_language}` / `{mobile_framework}` 从 preflight 决策读取，`{year}` 取当前年份。

### Step 2.5: 跨模型交叉验证（可选）

若 OpenRouter MCP 可用（`cross-model API (e.g., OpenRouter)` 工具存在），对每个 spike 向不同模型发送验证请求：

**Prompt 模板**：
```
项目技术栈: {backend_framework} + {mobile_framework}
技术点: {spike_title}
受影响功能: {affected_tasks_summary}
WebSearch 找到的候选方案: {option_list}

请评估以上方案，补充遗漏选项，指出潜在风险。回答限 300 字。
```

**调用参数**：`task: "competitive_analysis"`, `temperature: 0.3`

将跨模型反馈合并到 Step 3 的对比表中：补充遗漏方案、修正不准确的优劣势判断。

> 若 OpenRouter 不可用 → 跳过此步，仅使用 WebSearch 结果。

### Step 3: 整理方案对比表

对每个 spike，从搜索结果中提炼 2-3 个可行方案，整理为**对比表格**呈现给用户：

~~~markdown
### TS{N}: {spike 标题}

受影响任务: {task_id_list}
影响维度: {vendor / architecture / cost / compliance}

| 维度 | 方案 A: {name} (推荐) | 方案 B: {name} | 方案 C: {name} |
|------|----------------------|----------------|----------------|
| 核心能力 | ... | ... | ... |
| 与 {framework} 兼容 | ✅ / ⚠️ / ❌ | ... | ... |
| SDK / 库 | `{package}` | `{package}` | `{package}` |
| 集成复杂度 | 低 / 中 / 高 | ... | ... |
| 成本模型 | {pricing} | {pricing} | {pricing} |
| 社区 & 文档 | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| 优势 | • ... | • ... | • ... |
| 劣势 | • ... | • ... | • ... |

**推荐理由**: {为什么推荐方案 A，结合已选技术栈和项目特点}
~~~

**表格原则**：
- 推荐方案放第一列，标注「(推荐)」
- 维度行数 ≤ 10，聚焦决策关键因素
- 成本模型尽量给出具体数字（月/次/小时单价）
- 兼容性基于已选技术栈评估（如 FastAPI → 看 Python SDK 质量）
- 优劣势各 2-3 条，简洁明确

### Step 4: 用户选择

所有 spike 的对比表格一次性展示后：

- **自动模式**：自动采纳全部推荐方案，写入 forge-decisions.json，继续（不停）
- **交互模式**：等待用户逐项确认或调整。用户可对某项选择「TBD（待定）」→ 该 spike 的 `status` 标记为 `tbd`，不阻塞流程，但 design-to-spec 会在对应章节标注 `[PENDING: 技术方案待定]`。用户确认后继续。

### Step 4.5: 外部服务凭据收集（spike 决策确认后立即执行）

> **E2E 测试必须完全仿真**——mock 只用于单元测试，E2E 必须打真实 sandbox。
> 凭据在 spike 决策时就收集，不要等到测试阶段才发现"Key 没配"。

对每个 confirmed spike，LLM 判断需要什么凭据，声明所需凭据并假设合理默认值（仅在阻塞时才询问用户）：

```
您选择了以下外部服务，E2E 测试需要真实/sandbox 凭据才能验证功能。
请提供（留空 = 该服务的 E2E 测试标记为 NOT_VERIFIED）：

| 服务 | 需要的凭据 | 用途 | 您的值 |
|------|-----------|------|--------|
| {spike.vendor} | {LLM 推导的凭据字段} | sandbox 测试 | ______ |
| ... | ... | ... | ______ |

提示：
- 这些凭据仅用于 sandbox/测试环境，不用于生产
- 留空不阻塞开发，但 E2E 测试无法验证该服务的功能
- 可以稍后补充（运行 /project-forge credentials 更新）
```

**LLM 根据 spike 决策动态推导需要的凭据**（不硬编码具体服务）：
- IAP 类 → sandbox API Key / 测试账号
- Auth 类 → OAuth Client ID + Secret / 测试用户
- 搜索/LLM API 类 → API Key（通常有免费额度）
- 存储类 → Bucket + Access Key（或使用本地替代）
- 推送类 → FCM Server Key / APNs Certificate

**收集结果写入 forge-decisions.json 的 `service_credentials` 字段**：
```json
{
  "service_credentials": [
    {
      "spike_ref": "TS001",
      "service": "LiteLLM/OpenAI",
      "credentials_provided": true,
      "env_vars": {"OPENAI_API_KEY": "sk-..."},
      "test_mode": "real_sandbox"
    },
    {
      "spike_ref": "TS003",
      "service": "RevenueCat",
      "credentials_provided": false,
      "test_mode": "not_verified",
      "user_note": "稍后补充"
    }
  ]
}
```

**`test_mode` 三种状态**：
- `real_sandbox` — 用户提供了真实 sandbox 凭据 → E2E 完全仿真
- `not_verified` — 用户明确说"暂不提供" → E2E 该服务标记 NOT_VERIFIED（诚实）
- ~~`mock`~~ — **E2E 层禁止 mock**。Mock 只用于 B5 单元/组件测试

**凭据流入 .env**：
Step 0.5（环境配置）时读取 `service_credentials` → 写入各子项目 .env。
`credentials_provided=false` 的服务 → .env 中该变量标注 `# NOT_PROVIDED — E2E will be NOT_VERIFIED`。

### Step 5: 生成编码原则（两层）

基于 spike 决策 + 项目约束，生成两层编码原则：

**第一层：项目级通用原则**（`coding_principles.universal`）

以下原则始终包含（不可删除，可追加）：

| # | 原则 | 落地示例 |
|---|------|---------|
| U1 | 相同场景必须使用相同套路 | T002/T004 都是 AI 对话 → 共用同一个 conversation service |
| U2 | 底层工具库不重复 | HTTP client / error handler / logger / date 全项目统一一份 |
| U3 | 成熟三方优先 | 有维护良好的库就用，不自行实现（如用 tenacity 而不是手写 retry） |
| U4 | 外部服务调用封装为独立 service | 业务层不直接 import SDK，通过 service 层隔离 |

**第二层：项目级特定原则**（`coding_principles.project_specific`）

从 spike 决策 + constraints.json 推导：
- 每个 confirmed spike → 生成 `implementation_principles`（2-4 条具体编码约束）
- constraints 中 hard enforcement → 生成对应的代码层原则

~~~markdown
## 编码原则

### 通用原则
1. 相同场景使用相同套路（同类功能共用 service，禁止各自实现）
2. 底层工具库全项目统一（HTTP client / logger / error handler）
3. 成熟三方优先（有维护良好的库就用，不造轮子）
4. 外部服务封装为 service（业务层不直接调用 SDK）

### 项目特定原则
- [TS001] 所有 AI 调用通过 `services/ai_client.py`，streaming 用 async generator
- [TS002] 语音评估通过 `services/speech_service.py`，失败时 fallback 到文字输入
- [CN005] 支付操作必须经过审计日志中间件
- [CN001] 免费用量限制在 middleware 层统一拦截
~~~

- **自动模式**：自动确认，写入 forge-decisions.json，继续（不停）
- **交互模式**：展示编码原则，等待用户确认或补充。确认后写入 forge-decisions.json，继续

### Step 6: 写入 forge-decisions.json

将所有 spike 决策写入 `technical_spikes` 数组，编码原则写入 `coding_principles` 字段（结构见「初始化决策追踪」中的 JSON schema）。

更新 `phase_status.phase_1` 为 `completed`。

### 质量门禁

| 条件 | 标准 |
|------|------|
| spike 覆盖 | 所有检测到的 spike 已确认或标记 TBD |
| 编码原则 | universal ≥ 4 条，每个 confirmed spike 有 implementation_principles |
| 无遗漏 | 自动确认无补充项 |

**PASS** → 进入 Phase 2
**SKIP**（无 spike 检测到）→ 直接进入 Phase 2

---

## Phase 2：项目引导

### 执行方式

用 Read 加载 `./skills/project-setup.md`，按其工作流执行。

- full 模式 → project-setup new
- existing 模式 → project-setup existing

### 质量门禁

| 条件 | 标准 |
|------|------|
| 子项目数量 | ≥ 1 |
| 每个子项目有技术栈 | template_id 非空 |
| 模块覆盖率 | 100%（所有模块已分配） |

**PASS** → 进入 Phase 3
**FAIL** → 记录问题到 forge-decisions.json，带问题继续（不停）

---

## Phase 3：设计转规格 + 共享层分析

### 执行方式

用 Read 加载 `./skills/design-to-spec.md`，按其工作流执行（Step 1-6 规格生成 + Step 7 共享层分析）。

design-to-spec 内部使用 parallel execution加速：后端子项目先完成 spec，然后多个前端子项目并行生成 spec。详见 design-to-spec.md 的「并行执行编排」段落。

Step 7（共享层分析）在所有子项目 spec 生成完毕后执行：
- new 模式 → 跳过已有代码扫描，从模式共振分析开始
- existing 模式 → 全量执行（已有代码扫描 + 模式共振分析 + 三方库选型）
- auto-mode → Step 7 用户确认自动采纳推荐选项

### 质量门禁

| 条件 | 标准 |
|------|------|
| 每子项目 3 份 spec | requirements.md + design.md + tasks.md 全部存在 |
| 任务覆盖 | 所有 CORE 任务都出现在 tasks.md 中 |
| 原子性 | tasks.md 中无宽泛任务（如"实现 XX 系统"） |
| shared-utilities-plan.json | 存在 |
| B1 任务注入 | 所有 SU-xxx 有对应 B1 任务 |
| Leverage 更新 | affects_tasks 中的任务已有 SU-xxx 引用 |

**PASS** → 进入 Phase 4（task-execute）
**FAIL** → 记录问题到 forge-decisions.json，带问题继续（不停）

---

## Phase 4：任务执行

### 源代码目录预检（full 模式必做）

> **full 模式 = 从零构建。** 如果源代码目录已有旧代码，task-execute 会自动切到增量模式（修补而非重写），导致旧代码残留、新概念无法落地。这是历史上最严重的执行错误之一。

**full 模式下**，Phase 4 开始前检查 project-manifest.json 中每个子项目的 `base_path` 目录：

- 目录不存在 → 正常（从零开始）
- 目录存在且有源代码文件（非空目录、含 `.py`/`.ts`/`.dart`/`.go` 等）→ **旧代码残留，必须处理**

**处理方式**：
- **自动模式**：将旧代码目录重命名为 `{name}.pre-forge-bak`（保留备份），然后从空目录开始
- **交互模式**：展示警告并询问：「子项目 {name} 已有源代码。full 模式将从零构建。(1) 备份旧代码后清空 (2) 在旧代码上增量修改 (3) 中止」
  - 选 1 → 重命名为 `.pre-forge-bak`，从空开始
  - 选 2 → 切换该子项目为 existing 行为（增量）
  - 选 3 → 中止

> **existing 模式下**此检查不触发——existing 就是要在已有代码上工作。

### 执行方式

用 Read 加载 `./skills/task-execute.md`，按其工作流执行。

task-execute 自动完成：
- 加载各子项目 tasks.md + project-manifest.json
- 初始化/恢复 build-log.json
- 按 Round 结构分组，每 Round 自动推断执行策略（串行/并行）
- 逐任务委托 superpowers skill 执行
- 每 Round 结束后自动 lint/test + 增量 product-verify

### 质量门禁

| 条件 | 标准 |
|------|------|
| CORE 任务 | 全部标记 completed（build-log.json） |
| lint | 通过（或最后 Round 质量检查无 fail） |
| test | 通过（或自动跳过并记录） |

**PASS** → 进入 Phase 4.5（接缝门禁）
**FAIL** → 记录 failed/skipped 任务到 forge-decisions.json，带问题继续（不停）

---

## Phase 4.5：接缝门禁 + 功能深度审计（Seam Gate + Depth Audit）— 不可跳过

> **Phase 4（代码生成）和 Phase 5（测试验证）之间必须经过两道门禁。**
> 接缝门禁：前后端连接是否对齐。
> 深度审计：每个 UI 元素是否真的能用（不是空壳）。
>
> **为什么需要深度审计**：代码生成 Agent 在一次性处理大量任务时，倾向于生成"骨架完整但回调为空"的代码。
> 文件存在 ≠ 功能可用。编译通过 ≠ 按钮能点。Widget 渲染 ≠ 数据能加载。
> 深度审计在测试之前发现这些"空壳"，避免测试覆盖了一个不能用的功能还标绿。

Phase 4 写完所有代码后，立即执行 deadhunt static + fieldcheck full：

```
Step 4.5.1: 启动所有子项目的 dev server

Step 4.5.2: 并行执行 2 个 Agent
  Agent 1: /deadhunt static — 死链 + CRUD 缺口 + API 路径匹配
  Agent 2: /fieldcheck full — UI↔API↔Entity 字段名一致性

Step 4.5.3: 修复 critical 问题
  severity=critical → 直接修复代码
  修复后重启受影响的 dev server

Step 4.5.3.5: 认证链路端到端验证
  若项目有认证功能（登录/注册），验证完整认证链路：
  1. 用认证服务 SDK/API 登录测试账号 → 获取 token
  2. 检查 token 格式/算法（LLM 解析 token header 确认签名算法）
  3. 用该 token 调后端受保护 API → 必须返回 200（不是 401/403）
  4. 若后端返回认证错误 → 诊断：token 算法不匹配？secret 配置错误？中间件顺序错误？
  目的: 认证是所有 API 调用的前提，认证链路断 = 全部功能不可用

Step 4.5.4: 接缝冒烟 + UI 性能基线
  对每个前端子项目的核心页面：
  1. 启动浏览器（Playwright headless）
  2. 真实登录（不 bypass）
  3. 访问核心页面 → 验证页面有数据（强断言：具体数据可见，不只是"不是空白"）
  4. **测量页面加载性能**（用户感知的慢 = UI 层面慢，不只是 API 响应快）：
     - 页面完全加载时间（从 navigate 到内容渲染完成）
     - 首屏数据可见时间（从 navigate 到第一条业务数据出现）
     - 方式: Playwright `page.goto()` 的 `waitUntil: 'networkidle'` 计时
       + 等待具体数据元素出现的计时
     - 记录到 `seam-gate-report.json`:
       ```json
       {"page": "/users", "load_ms": 1200, "data_visible_ms": 2800, "status": "pass"}
       ```
     - 阈值: 首屏数据可见 > 5s → WARNING（标记为性能问题）
              首屏数据可见 > 10s → 需排查（SSR hydration 问题？每请求查 DB？N+1？）
  5. 有问题 → 修复 → 重验
```

Step 4.5.5: 功能深度审计（Depth Audit）

  **代码生成 Agent 倾向于产出"骨架完整但回调为空"的代码。深度审计检查每个功能是否真的能用。**

  LLM 读取产品概念中的核心功能列表（从 product-concept.json 的 core_mechanisms + innovation_concepts），
  对每个核心功能在代码中逐项验证：

  1. **回调连通性**：UI 元素（按钮/输入框/手势）的事件回调是否连接到业务逻辑？
     - 扫描前端代码中的 onPressed / onClick / onTap / onSubmit
     - 回调为 null / 空函数 / TODO 注释 → 标记为 `HOLLOW_CALLBACK`
     - 回调连接到 provider/service 但 provider 未实现 → 标记为 `STUB_LOGIC`

  2. **数据绑定完整性**：页面展示的数据是否来自真实 API？
     - 扫描前端代码中的 API 调用和数据绑定
     - 使用硬编码 mock 数据 → 标记为 `MOCK_DATA`
     - API 调用存在但响应未解析/绑定到 UI → 标记为 `UNBOUND_DATA`

  3. **核心功能对照**：
     - 从 product-concept 提取核心功能（如"多媒体输入支持5种格式"）
     - 在代码中逐项验证（如：文字✅ 图片❌空回调 语音❌空回调 文件❌空回调 链接❌不存在）
     - 实现度 < 80% 的核心功能 → 标记为 `INCOMPLETE_CORE`

  修复策略：
  - HOLLOW_CALLBACK → 补全回调实现
  - STUB_LOGIC → 补全 provider/service 逻辑
  - MOCK_DATA → 接入真实 API
  - INCOMPLETE_CORE → 拆分为更细粒度的任务，补全缺失部分

**质量门禁**：
- deadhunt critical = 0
- fieldcheck critical = 0
- 核心页面接缝冒烟全通过
- 核心页面首屏数据可见 < 5s（WARNING 不阻塞，记录到报告）
- 核心功能无 INCOMPLETE_CORE（WARNING 不阻塞，记录到报告）

**PASS** → 进入 Phase 5
**FAIL** → 修复后重跑（最多 3 轮）

---

## Phase 5：验证闭环 + 完整性验证（4-Agent 并行扫描）

### 前置产物检查（防跳过 Phase 5）

> ⚠️ **硬性前置条件**：`.allforai/project-forge/build-log.json` 必须存在且至少有一个 Round 状态为 `completed`。
> 若 build-log.json 不存在 → **说明 Phase 4 (task-execute) 未执行，必须先回退执行 Phase 4。**
> 禁止绕过此检查直接进入验证。

### 执行方式

Phase 4 完成后，运行完整验证并闭环修复：

```
Step 0.5: 抽象完整性检查（Abstraction Gate）

scope 限定在 build-log.json 中所有 files_modified 的并集（不扫全库）。
调用 code-tuner 的 Phase 2（重复检测）+ Phase 3（抽象机会分析）逻辑。

结果分级处理：
- CRITICAL（相同逻辑 5 处以上，或 SU-xxx 已实现但 2+ 任务绕过自行实现）
  → 生成 B-REFACTOR 任务，追加到对应子项目 tasks.md，合并入修复 Round 一起执行
- WARNING（3-4 处重复）
  → 记录到 forge-report.md 的 Tech Debt 章节，不阻塞流程
- 无发现 → 直接进入 Step 1

输出：.allforai/project-forge/abstraction-report.json

Step 1: 并行扫描（4 个 Agent）

product-verify、testforge（E2E chain）、deadhunt、fieldcheck 四项扫描均为只读代码分析，
互不影响，dispatch parallel agents 并行执行：

  Agent 1: 完整产品验收
    用 Read 加载 ./skills/product-verify.md
    执行 /product-verify full（静态 + 动态）
    输出: verify-tasks.json（IMPLEMENT / REMOVE_EXTRA / FIX_FAILING）

  Agent 2: 跨端验证（测试锻造 E2E 链）
    用 Read 加载 ./commands/testforge.md
    执行 /testforge（Phase 4 Path B: E2E chain forge）
    输出: testforge-report.md（E2E chain 结果）

  Agent 3: 死链猎杀
    用 Read 加载 ./commands/deadhunt.md
    执行 /deadhunt static（静态分析）
    若应用已运行 → 执行 /deadhunt full（含深度测试）
    输出: validation-report-summary.md + fix-tasks.json

  Agent 4: 字段一致性检查
    用 Read 加载 ./commands/fieldcheck.md
    执行 /fieldcheck full
    输出: field-report.md + field-issues.json

4 个 Agent 全部返回后，进入 Step 1.5。

Step 1.5: LLM 冒烟测试生成 + 执行（运行时验证）

> **核心原则**：Step 1 的 4-Agent 扫描是静态分析（读代码文件）。
> 但"代码文件正确"不等于"应用能跑起来且功能可用"。
> 静态分析能发现的问题（字段名/路径/覆盖率），运行时问题发现不了。
> 运行时问题必须通过**启动应用 → 实际请求 → 检查结果**来发现。
>
> **不硬编码检查项**——让 LLM 读当前项目的代码和配置，推理出该项目可能存在哪些运行时风险，
> 然后生成对应的冒烟测试。不同项目的风险不同，生成的测试也不同。

前置：启动所有子项目应用。
若无法启动 → 标记 `phase_5 = not_tested`，记录原因，不标记为 pass。

**Step 1.5a: LLM 分析运行时风险**

LLM Agent 读取以下内容（不是全部代码，只读关键文件）：
- project-manifest.json（子项目列表、端口、技术栈）
- 每个子项目的入口文件和配置文件（从 manifest 的技术栈推断文件位置）
- 跨子项目通信的模块（如前端的 API 客户端、后端的中间件配置）
- build-log.json 中的 files_modified 列表

然后以一个要部署这套系统的运维工程师视角，推理：
1. 这些子项目在运行时如何连接？哪些连接点可能断？
2. 哪些配置需要跨子项目一致（地址、端口、密钥、路径前缀）？当前是否一致？
3. 代码中有哪些依赖在编译时不报错但运行时可能失败的？
4. 还有哪些该项目架构下特有的运行时风险？

**Step 1.5b: 生成冒烟测试**

基于 1.5a 的风险分析，LLM 生成一组可执行的冒烟测试脚本。
测试形式不限——可以是 curl 命令、Playwright 脚本、Python 脚本、或 Bash 脚本。
关键是：每个测试**实际发请求或打开页面**，检查**运行时结果**。

LLM 生成的测试不限形式和内容，但必须覆盖以下三个层级（最低深度要求）：

| 层级 | 验证什么 | 不通过说明什么 |
|------|---------|-------------|
| **进程级** | 每个子项目启动后能响应请求且无致命错误 | 编译/构建通过 ≠ 运行时正常 |
| **连接级** | 子项目之间的请求能到达且返回预期格式 | 子项目间的配置不一致 |
| **数据级** | 至少一条核心业务的完整链路走通，验证终点是**用户最终看到的结果**，不是中间层的 API 响应 | 数据在某一层断裂（API 正确但渲染失败、渲染正确但数据为空） |

> **数据级的验证终点**：如果项目有用户界面，"结果正确"指的是用户在界面上能看到正确的数据（不是空的、不是报错的）。如果项目没有用户界面（纯后端/CLI），API 响应或命令输出就是终点。关键原则：**验证链必须延伸到用户实际触达的最后一层**，中间层全部正确但最后一层断裂 = 不通过。

三层级是最低深度定义。LLM 根据项目架构自由补充更多测试——单体项目可能只需进程+数据两级，微服务项目连接级测试会更多。

**Step 1.5c: 执行冒烟测试**

逐个执行生成的测试，收集结果：
- PASS: 运行时验证通过
- FAIL: 运行时发现问题（记录具体错误信息）
- NOT_TESTED: 无法执行（环境不满足、应用未启动、工具不可用等）

> **NOT_TESTED 不等于 PASS，也不等于 SKIP。**
> NOT_TESTED 的项必须在 Phase 7 或后续流程中补测。
> 报告中必须醒目标注 NOT_TESTED 项数量。

结果写入 `.allforai/project-forge/smoke-test-report.json`

**Step 1.5d: 判定 Phase 5 验证层级**

汇总 Step 1（静态）+ Step 1.5（动态）结果：
- 静态全通过 + 动态全通过 → `phase_5 = completed`
- 静态全通过 + 动态有 FAIL → `phase_5 = static_pass`（进入 Step 3 修复动态问题）
- 静态全通过 + 动态全 NOT_TESTED → `phase_5 = not_tested`
- 静态有 FAIL → `phase_5 = in_progress`（进入 Step 3 修复）

Step 2: 汇总判断
  汇总 verify-tasks.json 中 IMPLEMENT + FIX_FAILING 项
  汇总 testforge-report.md 中 FIX_REQUIRED 项
  汇总 deadhunt fix-tasks.json 中 severity=critical 项
  汇总 fieldcheck field-issues.json 中 severity=critical 项
  汇总 smoke-test-report.json 中 FAIL 项
  无修复项 → PASS，Phase 5 质量门禁通过
  有修复项 → Step 3

Step 3: 生成修复任务
  将所有验证发现转为原子任务，格式与 tasks.md 一致:
    - IMPLEMENT → 新增实现任务
    - FIX_FAILING → 修复任务（含失败截图/日志引用）
    - FIX_REQUIRED → 跨端修复任务
    - deadhunt critical → 死链修复任务
    - fieldcheck critical → 字段修复任务
  追加到对应子项目 tasks.md 的 Fix Round（B-FIX）
  → 输出: 「修复任务 ✓ IMPLEMENT:{N} FIX_FAILING:{M} FIX_REQUIRED:{K} DEADHUNT:{D} FIELD:{F}」
  → 直接执行（不停，来源是已经用户批量确认过的验证结果，无需二次确认）

Step 4: 执行修复
  调用 /task-execute 执行 Fix Round
  build-log.json 追加 fix round 记录

Step 5: 回归验证
  重跑 Step 1（仅 scope 模式，覆盖修复涉及的 task_ids）
  仍有失败 → 记录为已知问题，继续（不停）
  全部通过 → PASS
```

### 质量门禁

| 条件 | 标准 |
|------|------|
| verify-tasks.json | IMPLEMENT + FIX_FAILING = 0（或记录为已知问题） |
| testforge E2E chain | FIX_REQUIRED = 0（或记录为已知问题）；NOT_TESTED > 0 时标记 `PASS_WITH_UNTESTED`（不阻塞但报告醒目提示） |
| deadhunt | 无 critical 死链（或已修复） |
| fieldcheck | 无 critical 字段不一致（或已修复） |
| smoke-test | FAIL = 0；NOT_TESTED > 0 时 `phase_5 = not_tested`（不标记为 completed） |

**判定逻辑**：
- 全部 PASS 且 smoke-test 无 FAIL 无 NOT_TESTED → `phase_5 = completed`
- 全部 PASS 但 smoke-test 有 NOT_TESTED → `phase_5 = not_tested`（Phase 7 必须执行）
- 有 FAIL 已修复 → `phase_5 = completed`
- 有 FAIL 记录为已知问题 → `phase_5 = completed`（但 forge-report 醒目标注）

**PASS** → 进入 Phase 6（演示数据方案）
**FAIL** → 记录已知问题到 forge-decisions.json，继续（不停）

---

## Phase 6：演示数据方案

### 执行方式

代码稳定后，提示用户运行 `/demo-forge design` 完成演示数据方案设计。

> 注: demo-forge 已独立为 `demo-forge-skill/` 插件。本阶段仅做 plan 设计，完整灌入（media + execute + verify）在最终报告后运行 `/demo-forge`。

### 质量门禁

| 条件 | 标准 |
|------|------|
| demo-plan.json | 存在于 `.allforai/demo-forge/`（或用户选择跳过） |

**PASS** → 进入 Phase 7
**用户跳过** → 记录到 forge-decisions.json（`phase_6: "skipped"`），继续

---

## Phase 7：跨端验证（条件执行）

### 条件判断

检查 Phase 5 状态：
- Phase 5 **completed**（静态 + 动态验证均通过） → **跳过 Phase 7**，直接进入 Phase 8
- Phase 5 **static_pass**（仅静态验证通过，动态验证未执行） → **必须执行 Phase 7**（静态通过 ≠ 动态通过）
- Phase 5 **not_tested**（验证无法执行，如应用未启动） → **必须执行 Phase 7**（未测试 ≠ 通过）
- Phase 5 **skipped**（用户主动跳过） → 执行 Phase 7

> **铁律：未测试 ≠ 跳过 ≠ 通过。** `not_tested` 和 `static_pass` 都不能触发"已覆盖"的跳过逻辑。只有 `completed`（含动态验证）才能跳过后续验证阶段。

### 执行方式（Phase 5 不是 completed 时）

用 Read 加载 `./commands/testforge.md`，执行 Phase 4 Path B（E2E chain forge）。

**PASS** → 进入 Phase 8（最终报告）

### 前置

所有子项目应用必须正在运行。提示用户启动：
```
跨端验证需要所有子项目应用正在运行。请确认以下服务已启动：

- api-backend: http://localhost:{port}
- merchant-admin: http://localhost:{port}
- customer-web: http://localhost:{port}
```

### 质量门禁

| 条件 | 标准 |
|------|------|
| E2E 通过率 | ≥ 80% 场景通过 |
| FIX_REQUIRED | 已全部分类 |

---

## Phase 8：最终报告

### 汇总所有阶段

读取全部阶段产出，生成最终报告：

**输出文件**：
- `.allforai/project-forge/forge-report.json` — 全量报告（机器版）
- `.allforai/project-forge/forge-report.md` — 人类版摘要

### forge-report.md 结构

```markdown
# 项目锻造报告

## 执行摘要

- 执行模式: {full/existing}
- 子项目数: {N}
- 总任务数: {N} (CORE: {N}, DEFER: {N})

## 各阶段状态

| 阶段 | 状态 | 质量门禁 | 关键产出 |
|------|------|----------|----------|
| Phase 1: 技术调研 | 完成/跳过 | PASS/SKIP | {N} 项 spike 决策 |
| Phase 2: 项目引导 | 完成 | PASS | project-manifest.json |
| Phase 3: 设计转规格+共享层 | 完成 | PASS | {N} 子项目 × 3 份 spec + 复用 {M} 现有 + 新建 {K} 共享工具 + 负空间补全 {J} 项 |
| Phase 4: 任务执行 | 完成 | PASS | {N}/{M} 任务完成 |
| Phase 5: 验证闭环+完整性 | 完成 | PASS | 修复 {N} 项，回归通过；deadhunt: {D} 问题，fieldcheck: {F} 问题 |
| Phase 6: 演示方案 | 完成/跳过 | PASS/SKIP | demo-plan.json |
| Phase 7: 跨端验证 | 完成/跳过 | PASS/SKIP | {N}/{M} 场景通过（Phase 5 已覆盖则跳过） |

## 各子项目状态

| 子项目 | 类型 | 技术栈 | 任务 | 完成率 | E2E |
|--------|------|--------|------|--------|-----|
| api-backend | backend | NestJS | X/Y | 100% | N/A |
| merchant-admin | admin | Next.js | X/Y | 95% | 4/5 |
...

## 待处理项

### DEFER 任务（{N} 个）
{列表}

### E2E 失败项（{N} 个）
{列表}

### 未测试项 NOT_TESTED（{N} 个）
> 这些测试因环境缺失被跳过——不是通过，不是失败，是没有测到。
{列表，含: 测试名称 + 跳过原因 + 需要的环境}

### 负空间补全（{N} 项）— 开发阶段发现的缺失支撑功能
> 产品设计阶段关注主流程（正确），以下功能由开发阶段 FVL 负空间推导补全。
> 详见 `.allforai/project-forge/negative-space-supplement.json`

| ID | 触发功能 | 补全内容 | 严重度 | 任务 |
|----|---------|---------|--------|------|
| NS-001 | 认证模块 | 密码恢复流程 | MUST | SN-001~003 |
{列表}

## 下一步行动

1. [ ] 处理 DEFER 任务
2. [ ] 修复 E2E 失败项
3. [ ] 运行 /demo-forge 灌入演示数据
4. [ ] 运行 /code-tuner full 架构分析

## 产出文件索引

> project-manifest: `.allforai/project-forge/project-manifest.json`
> 各子项目 spec: `.allforai/project-forge/sub-projects/{name}/`
> E2E 报告: `.allforai/project-forge/e2e-report.md`
> 全程决策: `.allforai/project-forge/forge-decisions.json`
```

---

## New vs Existing 模式差异

| Phase | New 模式 | Existing 模式 |
|-------|---------|--------------|
| Phase 1 | 全量调研 | 扫描代码已有依赖，仅调研缺失项 |
| Phase 2 | 从空白引导拆分 | 扫描已有代码，提议拆分，识别缺口 |
| Phase 3 | 全量 spec 生成 + 共享层分析（跳过已有代码扫描） | 仅为缺失模块生成 spec + 共享层全量执行（含已有工具库存扫描） |
| Phase 4 | 全量任务执行 | 仅执行缺口任务 |
| Phase 5 | 全量 4-Agent 并行扫描（含 deadhunt + fieldcheck） | 全量（无差异） |
| Phase 7 | 全量 E2E | 全量 E2E（无差异） |

---

## 铁律

### 1. 质量门禁不跳过

每阶段完成后必须通过质量门禁。失败时记录问题到 forge-decisions.json，自动带问题继续（不停）。

### 2. 用户可在任意阶段中止

保存已有产出，输出部分摘要。如需重新执行，运行 `full` 模式从头开始。

### 3. 编排命令是导航员

不直接实现功能，而是加载对应 skill 或提示用户执行对应命令。

### 4. .allforai/ 是层间合约

各阶段通过 `.allforai/project-forge/` 下的文件交换数据，不通过对话上下文传递大量数据。

### 5. 决策全程追踪

所有用户决策记录到 forge-decisions.json，可追溯、可审计。

### 6. Phase 转换零停顿

**严禁在 Phase 之间停下来问"继续？""进入下一阶段？"等确认性问题。** 质量门禁 PASS 或 FAIL（带问题继续）后，直接加载下一阶段的 skill 并执行，不输出任何需要用户回复的确认提问。唯一允许停顿的场景是铁律第 2 条（用户主动中止）和 ERROR 级安全护栏。Phase 转换时只输出一行状态摘要（如 `Phase 5 ✓ → Phase 6`），然后立即开始下一阶段。

### 7. 未测试 ≠ 跳过 ≠ 通过

三个状态有本质区别，禁止混淆：

| 状态 | 含义 | 后续处理 |
|------|------|---------|
| `completed` / `PASS` | 测试执行了且通过 | 可信赖，后续阶段可跳过 |
| `not_tested` | 测试条件不满足（应用未启动/环境不可用），**未执行** | **必须在后续阶段补测**，不得视为通过 |
| `skipped` | 用户主动决定跳过 | 记录决策原因，后续阶段**必须执行**对应验证 |
| `FAIL` | 测试执行了且失败 | 生成修复任务，修复后回归 |

**违反此铁律的典型场景**：
- 静态扫描通过 → 标记 completed → 后续动态验证跳过 → 运行时 bug 逃逸。**错误**：静态通过应标记 `static_pass`，动态验证必须执行
- 测试工具不可用 → 标记 skipped → 报告显示"全部通过"。**错误**：应标记 `not_tested`，报告醒目提示未测试项数量
- 应用启动失败 → 跳过冒烟测试 → 继续下一阶段。**错误**：应标记 `not_tested`，不应继续声称验证通过
