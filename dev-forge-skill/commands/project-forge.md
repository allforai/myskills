---
description: "项目锻造全流程：setup → spec → scaffold → build → verify。模式: full / existing / resume"
argument-hint: "[mode: full|resume] [existing]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "Agent"]
---

# Project Forge — 项目锻造全流程编排

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

> **跨插件调用约定**：本命令是「导航员」。
> - Phase 2-6, 9 在本插件内执行，通过 `${CLAUDE_PLUGIN_ROOT}/skills/` 路径加载技能。
> - Phase 4（demo-forge）为独立插件 `demo-forge-skill/`，提示用户运行 `/demo-forge design`。
> - Phase 7（任务执行）调用 `task-execute` skill，自动编排 superpowers 技能。
> - Phase 8（验证闭环）产品验收 + E2E 验证 → 修复任务 → 回归。
> - 各阶段产物通过 `.allforai/` 目录作为层间合约。

### ⚠️ 阶段→技能速查（必看）

> **Phase 7 是 task-execute（写代码），不是 product-verify（验收）。**
> product-verify 属于 Phase 8。不要混淆！

| Phase | 技能文件 | 做什么 | 完成标志 |
|-------|---------|--------|---------|
| 1 | _(内嵌本文)_ | 技术风险调研 | `forge-decisions.json` 有 `technical_spikes` |
| 2 | `skills/project-setup.md` | 拆子项目 + 选技术栈 | `project-manifest.json` 存在 |
| 3 | `skills/design-to-spec.md` | 产品设计 → 规格文档 | 每子项目有 `requirements.md` + `design.md` + `tasks.md` |
| 4 | _(外部: demo-forge 插件)_ | 演示数据方案 | `demo-plan.json` 存在 |
| **5** | **`skills/shared-utilities.md`** | **共享工具分析 + 任务注入** | **`shared-utilities-plan.json` 存在** |
| 6 | `skills/project-scaffold.md` | 脚手架生成 | `scaffold-manifest.json` 存在 + mock 可启动 |
| **7** | **`skills/task-execute.md`** | **按 tasks.md 逐任务写业务代码** | **`build-log.json` 存在且 CORE 任务 completed** |
| 8 | `skills/product-verify.md` + `skills/e2e-verify.md` | 验证闭环 + 修复回归 | `verify-tasks.json` 无 IMPLEMENT/FIX_FAILING |
| 9 | `skills/e2e-verify.md` | 跨端验证（条件执行） | E2E 通过率 ≥ 80% |
| 10 | _(内嵌本文)_ | 最终报告 | `forge-report.md` |

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 新项目，从头执行全流程
- **`full existing`** → 已有项目，gap 模式（扫描代码 → 仅补缺）
- **`resume`** → 检测已有产物，从第一个未完成阶段继续

## 十阶段架构

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
│  Phase 3: 设计转规格 (design-to-spec)                       │
│    读产品设计产物 → 按子项目生成 spec                        │
│    输出: requirements.md + design.md + tasks.md              │
│  ↓ 质量门禁: 每子项目 3 份 spec 完整                        │
│  Phase 4: 演示数据方案                                       │
│    提示用户运行 /demo-forge design                           │
│    输出: demo-plan.json                                      │
│  ↓ 质量门禁: demo-plan.json 存在                            │
│  Phase 5: 共享工具分析 (shared-utilities)                   │
│    扫描现有代码 → 跨任务模式分析 → 三方库调研 → 注入 B1     │
│    输出: shared-utilities-plan.json                          │
│  ↓ 质量门禁: shared-utilities-plan.json 存在                │
│  Phase 6: 脚手架生成 (project-scaffold)                     │
│    按模板 + mock-server                                      │
│    输出: 项目骨架 + mock-server/                             │
│  ↓ 质量门禁: 脚手架存在 + mock 可启动                       │
│  Phase 7: 任务执行 (task-execute)                             │
│    自动编排: 策略推断 → 委托执行 → 进度追踪 → 增量验证      │
│    Round 0→1→2→3→4                                          │
│  ↓ 质量门禁: CORE 任务完成，lint 通过                       │
│  Phase 8: 验证闭环                                           │
│    抽象门禁 + product-verify + e2e-verify → 修复 → 回归     │
│  ↓ 质量门禁: 修复项 = 0 或记录为已知问题继续                │
│  Phase 9: 跨端验证 (e2e-verify) — 条件执行                   │
│    仅当 Phase 8 被跳过时执行                                  │
│    业务流 → 跨端场景 → Playwright                            │
│  ↓                                                          │
│  Phase 10: 最终报告                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 0：产物检测 + 初始化 + Preflight 偏好收集

### 产物探测

扫描以下目录，判断进度：

| 阶段 | 完成标志 |
|------|----------|
| product-design | `.allforai/product-map/task-inventory.json` 存在且 task 数 > 0 |
| technical-spike | `forge-decisions.json` 存在且 `technical_spikes` 数组长度 > 0 |
| project-setup | `.allforai/project-forge/project-manifest.json` 存在 |
| design-to-spec | `.allforai/project-forge/sub-projects/*/tasks.md` 存在 |
| demo-forge design | `.allforai/demo-forge/demo-plan.json` 存在 |
| shared-utilities | `.allforai/project-forge/shared-utilities-plan.json` 存在 |
| project-scaffold | `.allforai/project-forge/sub-projects/*/scaffold-manifest.json` 存在 |
| task-execution | `.allforai/project-forge/build-log.json` 存在 |
| e2e-verify | `.allforai/project-forge/e2e-report.json` 存在 |

### 前置检查

**product-design 产物必须存在**：
- 检查 `.allforai/product-map/product-map.json`
- 不存在 → 输出「请先完成产品设计流程（/product-design full），再运行项目锻造」，终止

### 模式处理

**full 模式**：从 Phase 2 开始，逐阶段执行。
**full existing**：Phase 2 的 project-setup 以 existing 模式运行（扫描代码）。
**resume 模式**：从第一个未完成阶段开始。

### 初始化决策追踪

创建/更新 `.allforai/project-forge/forge-decisions.json`：

```json
{
  "forge_run": {
    "mode": "full | existing | resume",
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
    "phase_4": "pending | completed | skipped",
    "phase_5": "pending | completed | skipped",
    "phase_6": "pending | completed | skipped",
    "phase_7": "pending | in_progress | completed",
    "phase_8": "pending | in_progress | completed | skipped",
    "phase_9": "pending | completed | skipped",
    "phase_10": "pending | completed"
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
| 有 mobile 标记 或 screen-map 中有 mobile 界面 | `mobile-native` |

读取 `${CLAUDE_PLUGIN_ROOT}/templates/stacks.json`，按端类型过滤可选技术栈。

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

自动采纳推荐配置，写入 forge-decisions.json，继续（不停）

**Step 2d: 写入 forge-decisions.json**

将确认后的配置写入 `forge-decisions.json` 的 `preflight` 字段（结构见「初始化决策追踪」中的 JSON schema）。

---

输出探测结果 + 执行计划（含 preflight 结果摘要），自动开始（不停）。

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

### Step 2: WebSearch 调研

对每个检测到的 spike 类别，执行 2-3 轮 WebSearch：

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

若 OpenRouter MCP 可用（`mcp__plugin_product-design_openrouter__ask_model` 工具存在），对每个 spike 向不同模型发送验证请求：

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

自动采纳全部推荐方案，写入 forge-decisions.json，继续（不停）

用户也可对某项选择「TBD（待定）」→ 该 spike 的 `status` 标记为 `tbd`，不阻塞流程，但 design-to-spec 会在对应章节标注 `[PENDING: 技术方案待定]`。

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

自动确认，写入 forge-decisions.json，继续（不停）

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

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/project-setup.md`，按其工作流执行。

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

## Phase 3：设计转规格

### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md`，按其工作流执行。

design-to-spec 内部使用 Agent tool 并行加速：后端子项目先完成 spec，然后多个前端子项目并行生成 spec。详见 design-to-spec.md 的「并行执行编排」段落。

### 质量门禁

| 条件 | 标准 |
|------|------|
| 每子项目 3 份 spec | requirements.md + design.md + tasks.md 全部存在 |
| 任务覆盖 | 所有 CORE 任务都出现在 tasks.md 中 |
| 原子性 | tasks.md 中无宽泛任务（如"实现 XX 系统"） |

**PASS** → 进入 Phase 4
**FAIL** → 记录问题到 forge-decisions.json，带问题继续（不停）

---

## Phase 4：演示数据方案

### 执行方式

提示用户运行 `/demo-forge design` 完成演示数据方案设计。

> 注: demo-forge 已独立为 `demo-forge-skill/` 插件。本阶段仅做 plan 设计，完整灌入（media + execute + verify）在 Phase 8 代码稳定后运行 `/demo-forge`。

### 质量门禁

| 条件 | 标准 |
|------|------|
| demo-plan.json | 存在于 `.allforai/demo-forge/`（或用户选择跳过） |

---

## Phase 5：共享工具分析

### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/shared-utilities.md`，按其工作流执行。

- new 模式 → 跳过 Step 1（无已有代码），从 Step 2 开始
- existing 模式 → 全量执行 Step 1-5

### 质量门禁

| 条件 | 标准 |
|------|------|
| shared-utilities-plan.json | 存在 |
| B1 任务注入 | 所有 SU-xxx 有对应 B1 任务（`_SharedUtility: SU-xxx_` 标注） |
| Leverage 更新 | affects_tasks 中的任务已有 SU-xxx 引用 |

**PASS** → 进入 Phase 6（project-scaffold）
**用户跳过** → 记录到 forge-decisions.json（`phase_5: "skipped"`），继续

---

## Phase 6：脚手架生成

### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffold.md`，按其工作流执行。

### New vs Existing 差异

- **new**：全量脚手架
- **existing**：仅补缺文件，绝不覆盖已有

### 质量门禁

| 条件 | 标准 |
|------|------|
| 脚手架文件 | scaffold-manifest.json 存在且文件数 > 0 |
| mock-server | apps/mock-server/server.js 存在 |
| 依赖安装 | 自动执行 pnpm install，检查退出码 = 0 |
| mock 启动 | 自动启动 mock-server，curl health check 返回 2xx |

**PASS** → 进入 Phase 7（⚠️ Phase 7 = task-execute，加载 `${CLAUDE_PLUGIN_ROOT}/skills/task-execute.md`）
**FAIL** → 记录问题到 forge-decisions.json，带问题继续（不停）

---

## Phase 7：任务执行

### 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/task-execute.md`，按其工作流执行。

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

**PASS** → 进入 Phase 8
**FAIL** → 记录 failed/skipped 任务到 forge-decisions.json，带问题继续（不停）

---

## Phase 8：验证闭环

### 前置产物检查（防跳过 Phase 7）

> ⚠️ **硬性前置条件**：`.allforai/project-forge/build-log.json` 必须存在且至少有一个 Round 状态为 `completed`。
> 若 build-log.json 不存在 → **说明 Phase 7 (task-execute) 未执行，必须先回退执行 Phase 7。**
> 禁止绕过此检查直接进入验证。

### 执行方式

Phase 7 完成后，运行完整验证并闭环修复：

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

Step 1: 完整产品验收
  用 Read 加载 ${CLAUDE_PLUGIN_ROOT}/skills/product-verify.md
  执行 /product-verify full（静态 + 动态）
  输出: verify-tasks.json（IMPLEMENT / REMOVE_EXTRA / FIX_FAILING）

Step 2: 跨端验证
  用 Read 加载 ${CLAUDE_PLUGIN_ROOT}/skills/e2e-verify.md
  执行 /e2e-verify full
  输出: e2e-report.json（FIX_REQUIRED 项）

Step 3: 判断是否需要修复
  汇总 verify-tasks.json 中 IMPLEMENT + FIX_FAILING 项
  汇总 e2e-report.json 中 FIX_REQUIRED 项
  无修复项 → PASS，进入 Phase 9
  有修复项 → Step 4

Step 4: 生成修复任务
  将验证发现转为原子任务，格式与 tasks.md 一致:
    - IMPLEMENT → 新增实现任务
    - FIX_FAILING → 修复任务（含失败截图/日志引用）
    - FIX_REQUIRED → 跨端修复任务
  追加到对应子项目 tasks.md 的 Fix Round（B-FIX）
  → 输出: 「修复任务 ✓ IMPLEMENT:{N} FIX_FAILING:{M} FIX_REQUIRED:{K}」
  → 直接执行（不停，来源是已经用户批量确认过的验证结果，无需二次确认）

Step 5: 执行修复
  调用 /task-execute 执行 Fix Round
  build-log.json 追加 fix round 记录

Step 6: 回归验证
  重跑 Step 1-2（仅 scope 模式，覆盖修复涉及的 task_ids）
  仍有失败 → 记录为已知问题，继续（不停）
  全部通过 → PASS
```

### 质量门禁

| 条件 | 标准 |
|------|------|
| verify-tasks.json | IMPLEMENT + FIX_FAILING = 0（或记录为已知问题） |
| e2e-report.json | FIX_REQUIRED = 0（或记录为已知问题） |

**PASS** → 进入 Phase 9
**FAIL** → 记录已知问题到 forge-decisions.json，继续（不停）

---

## Phase 9：跨端验证（条件执行）

### 条件判断

检查 Phase 8 状态：
- Phase 8 **completed**（验证闭环已通过） → **跳过 Phase 9**，直接进入 Phase 10
- Phase 8 **skipped**（用户跳过验证闭环） → 执行 Phase 9
- Phase 8 中有 **DEFERRED** 项 → 自动跳过 Phase 9（不停）

### 执行方式（仅 Phase 8 被跳过时）

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/e2e-verify.md`，按其工作流执行。

### 前置

所有子项目应用必须正在运行。提示用户启动：
```
Phase 9 需要所有子项目应用正在运行。请确认以下服务已启动：

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

## Phase 10：最终报告

### 汇总所有阶段

读取全部阶段产出，生成最终报告：

**输出文件**：
- `.allforai/project-forge/forge-report.json` — 全量报告（机器版）
- `.allforai/project-forge/forge-report.md` — 人类版摘要

### forge-report.md 结构

```markdown
# 项目锻造报告

## 执行摘要

- 执行模式: {full/existing/resume}
- 子项目数: {N}
- 总任务数: {N} (CORE: {N}, DEFER: {N})

## 各阶段状态

| 阶段 | 状态 | 质量门禁 | 关键产出 |
|------|------|----------|----------|
| Phase 1: 技术调研 | 完成/跳过 | PASS/SKIP | {N} 项 spike 决策 |
| Phase 2: 项目引导 | 完成 | PASS | project-manifest.json |
| Phase 3: 设计转规格 | 完成 | PASS | {N} 子项目 × 3 份 spec |
| Phase 4: 演示方案 | 完成/跳过 | PASS/SKIP | demo-plan.json |
| Phase 5: 共享工具分析 | 完成/跳过 | PASS/SKIP | 复用 {M} 现有 + 新建 {K} 共享工具 |
| Phase 6: 脚手架生成 | 完成 | PASS | {N} 文件 + mock-server |
| Phase 7: 任务执行 | 完成 | PASS | {N}/{M} 任务完成 |
| Phase 8: 验证闭环 | 完成 | PASS | 修复 {N} 项，回归通过 |
| Phase 9: 跨端验证 | 完成/跳过 | PASS/SKIP | {N}/{M} 场景通过（Phase 8 已覆盖则跳过） |

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

## 下一步行动

1. [ ] 处理 DEFER 任务
2. [ ] 修复 E2E 失败项
3. [ ] 运行 /demo-forge 灌入演示数据
4. [ ] 运行 /product-verify full 完整验收
5. [ ] 运行 /deadhunt full 链路验证
6. [ ] 运行 /code-tuner full 架构分析

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
| Phase 3 | 全量 spec 生成 | 仅为缺失模块生成 spec |
| Phase 5 | 跳过 Step 1，从 Step 2 开始 | 全量执行 Step 1（扫描已有工具库存）|
| Phase 6 | 全量脚手架 | 仅补缺文件，绝不覆盖已有 |
| Phase 7 | 全量任务执行 | 仅执行缺口任务 |
| Phase 9 | 全量 E2E | 全量 E2E（无差异） |

---

## 铁律

### 1. 质量门禁不跳过

每阶段完成后必须通过质量门禁。失败时记录问题到 forge-decisions.json，自动带问题继续（不停）。

### 2. 用户可在任意阶段中止

保存已有产出，输出部分摘要。resume 模式可从中断处继续。

### 3. 编排命令是导航员

不直接实现功能，而是加载对应 skill 或提示用户执行对应命令。

### 4. .allforai/ 是层间合约

各阶段通过 `.allforai/project-forge/` 下的文件交换数据，不通过对话上下文传递大量数据。

### 5. 决策全程追踪

所有用户决策记录到 forge-decisions.json，可追溯、可审计。
