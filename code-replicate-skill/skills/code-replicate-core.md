---
name: code-replicate-core
description: >
  Internal shared protocol for code replication. Do NOT invoke directly —
  loaded by cr-backend.md, cr-frontend.md, cr-fullstack.md, or cr-module.md.
---

# Code Replicate Core Protocol v2.1

## Overview

Code Replicate 是逆向工程桥梁：读取已有代码库，生成标准 `.allforai/` 产物（product-map、experience-map、use-case），
使 dev-forge 流水线（`/design-to-spec` → `/task-execute`）可直接消费。

本技能的唯一职责是从源码提取**业务意图**（做什么），不复制**实现决策**（怎么做）。
源码中的同步/异步模型、错误处理约定、通信协议等属于实现决策，由目标生态的架构惯例替换。

---

## 4 阶段流程

### Phase 1: Preflight

1. 检测 replicate-config.json（断点续跑 — 见下文）
2. 解析 CLI 参数：mode, path/url, --type, --scope, --module, --from-phase
3. 源码获取：
   - 本地路径 → 直接使用
   - Git URL → `git clone --depth 1`（HTTPS / SSH / GitHub 短语法 `user/repo`）
   - 支持 `#branch` 后缀指定分支：`https://github.com/user/repo#develop`
4. 收集缺失参数（AskUserQuestion，最多 1 次合并多题）：
   - 保真度（interface / functional / architecture / exact）
     > 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity-guide.md
   - 项目类型（backend / frontend / fullstack / module）
   - scope（full / modules / feature）
   - 目标技术栈（同栈 or 跨栈 + 目标名称）
   - 业务方向（replicate / slim / extend）
   - 源 App 运行信息（供 Phase 2c-visual + `/cr-visual` 使用）：
     · 启动命令（前端 + 后端，后端必须运行前端才能展示数据）
     · URL
     · 登录凭证（如有 2FA/验证码，需要提供绕过方式或测试模式命令）
     · 测试数据准备命令（seed 脚本或 demo 账号，空库截图无意义）
     · 平台类型
   > **闭环输入审计**（见 product-design-skill/docs/skill-commons.md §八）：
   > 用户回答后检查**意图闭环**（代码做了什么 vs 用户想要什么一致吗？）
   > 和**边界闭环**（代码处理了正常路径，用户期望的异常处理呢？）。
   > MUST 级缺失以选择题形式追问。
5. 写 replicate-config.json → `.allforai/code-replicate/`（含 `source_app` 字段）
6. 创建 fragments 目录结构：`.allforai/code-replicate/fragments/{roles,screens,tasks,flows,usecases,constraints}/`

---

### Phase 2: Discovery + Confirm

Phase 2 分 4 个阶段，共 15 步。每个阶段的详细协议按需加载。

#### Stage A — 结构发现（项目长什么样）

| Step | 产出 | 做什么 |
|------|------|--------|
| 2.1 | discovery-profile.json | LLM 读根目录 → 生成模块发现规则 |
| 2.2 | source-summary.json 骨架 | cr_discover.py 扫描文件 |
| 2.3 | source-summary.json 完整 | LLM 逐模块读 key_files → 摘要 |
| 2.4 | project_archetype | LLM 识别项目核心价值类型 |

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/phase2/stage-a-structure.md

#### Stage B — 运行基础发现（项目靠什么跑）

| Step | 产出 | 做什么 |
|------|------|--------|
| 2.5 | infrastructure-profile.json | 自研基础设施盘点 |
| 2.6 | env-inventory.json | 环境变量清单 |
| 2.7 | third-party-services.json | 第三方服务清单 |
| 2.8 | cron-inventory.json | 定时任务清单 |
| 2.9 | error-catalog.json | 错误码体系 |

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/phase2/stage-b-runtime.md

#### Stage C — 资源发现（项目带什么素材/数据）

| Step | 产出 | 做什么 |
|------|------|--------|
| 2.10 | asset-inventory.json | 前端素材盘点 |
| 2.11 | seed-data-inventory.json | 后端基础数据 |
| 2.12 | abstractions + cross_cutting | 复用模式 + 横切关注 |
| 2.13 | visual/source/ + route-map.json | 源 App 截图存档 |

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/phase2/stage-c-resources.md

#### Stage D — 确认 + 映射

| Step | 产出 | 做什么 |
|------|------|--------|
| 2.14 | 用户确认 | 展示发现 → 最后一次交互 |
| 2.15 | stack-mapping.json | 跨栈映射 |

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/phase2/stage-d-confirm.md

> **=== Phase 2 结束后不再问任何配置问题 ===**

---

### Phase 3: Generate（静默执行）

**Step 3-pre** — LLM 生成 `extraction-plan.json`（项目专属提取规则）

LLM 读取 source-summary.json（已有模块清单、技术栈、key_files），针对**当前项目**生成提取计划，写入 `.allforai/code-replicate/extraction-plan.json`：

```json
{
  "role_sources": [
    {"module": "M003", "file": "internal/middleware/auth.go", "how": "RoleType enum 定义了 4 种角色"},
    {"module": "M003", "file": "config/permissions.yaml", "how": "RBAC 权限矩阵"}
  ],
  "task_sources": [
    {"module": "M001", "file": "cmd/api/handlers/*.go", "how": "每个导出 handler 函数 = 一个 task"},
    {"module": "M005", "file": "internal/cron/jobs.go", "how": "每个 cron job = 一个 task"}
  ],
  "flow_sources": [
    {"module": "M002", "file": "internal/service/order_service.go", "how": "CreateOrder 方法调用链 = 一个完整 flow"}
  ],
  "screen_sources": [
    {"module": "M010", "file": "src/app/*/page.tsx", "how": "每个 page.tsx = 一个 screen，同目录下 layout.tsx 提供布局信息"}
  ],
  "usecase_sources": [
    {"module": "M001", "file": "cmd/api/handlers/*.go", "how": "handler 中的 if/switch 分支 = boundary/exception use case"}
  ],
  "constraint_sources": [
    {"module": "M004", "file": "internal/model/*.go", "how": "struct tag 中的 validate 标签 = 输入约束"}
  ],
  "cross_cutting": [
    {"concern": "认证", "files": ["internal/middleware/auth.go"], "applies_to": ["M001", "M002"]},
    {"concern": "日志", "files": ["internal/logger/logger.go"], "applies_to": "all"}
  ],
  "abstraction_sources": [
    {"file": "lib/core/base_bloc.dart", "how": "15个 feature Bloc 都继承此基类，提供统一的 loading/error state 处理"},
    {"file": "lib/shared/widgets/custom_button.dart", "how": "全 app 复用的按钮组件，封装了 loading 状态和 haptic feedback"},
    {"file": "lib/core/network/api_service.dart", "how": "统一 HTTP 封装：token 注入、错误拦截、重试逻辑，所有 feature service 依赖此类"}
  ],
  "asset_sources": [
    {"path": "LLM 根据 asset-inventory 指向的素材目录", "migration": "copy | transform | replace"}
  ],
  "infrastructure_sources": [
    {"file": "LLM 根据 infrastructure-profile 指向的文件", "how": "LLM 描述该文件中基础设施的实现方式"}
  ],
  "dependency_map": [
    {"from": "M001", "to": "M003", "via": "require('app.service.user_service')", "type": "direct_call"},
    {"from": "M001", "to": "M002", "via": "access_by_lua_file middleware/auth.lua", "type": "middleware"},
    {"from": "M003", "to": "M004", "via": "require('app.dao.user_dao')", "type": "direct_call"},
    {"from": "M002", "to": null, "via": "ngx.shared.rate_limit_counter", "type": "shared_state"}
  ]
}
```

**生成原则**：
- LLM **必须**读 source-summary.json 中每个模块的 key_files 才能生成
- 每个 source 条目的 `how` 字段描述**该项目**的具体提取方式，不套用框架模板
- `dependency_map` — LLM 读 key_files 中的 import/require/include 语句后填充的模块间依赖关系
- **`artifacts` — LLM 决定本项目需要生成哪些产物**（见下）

### extraction-plan.artifacts — LLM 自由决定产物列表

extraction-plan 新增 `artifacts` 字段：LLM 根据 project_archetype 决定**生成什么产物、用什么 schema、存到哪个路径**。

**不再硬编码 Step 3.1-3.6**。LLM 自行规划产物列表：

```json
"artifacts": [
  {
    "name": "LLM 自命名（如 task-inventory / system-spec / dag-spec / command-tree）",
    "path": "输出路径（如 product-map/task-inventory.json）",
    "schema": "LLM 描述 schema（自由格式）或引用标准 schema（如 '标准 task-inventory'）",
    "sources": [{"module": "...", "file": "...", "how": "..."}],
    "merge_script": "对应的 merge 脚本路径（如有）或 null（LLM 直接输出完整产物）"
  }
]
```

**标准 Web 应用**的 artifacts 列表（LLM 自然生成，不是硬编码）：
- role-profiles → `cr_merge_roles.py`
- experience-map → `cr_merge_screens.py`（有 UI 时）
- task-inventory → `cr_merge_tasks.py`
- business-flows → `cr_merge_flows.py`
- use-case-tree → `cr_merge_usecases.py`
- constraints → `cr_merge_constraints.py`（exact 时）
- test-vectors → null（LLM 直接输出）
- indexes + product-map → gen 脚本

**非标准项目**的 artifacts 列表（LLM 自由决定）：
- 游戏服务端 → system-spec（ECS 系统定义）+ config-schema（数值表结构）+ protocol-spec
- 数据管道 → dag-spec（DAG 定义）+ transform-catalog（转换逻辑）+ schema-registry
- CLI 工具 → command-tree（命令树）+ plugin-interface（插件接口）
- 微服务合并 → service-boundary-map（服务边界→函数边界映射）

**有 merge 脚本的产物**（标准 .allforai/ 产物）走脚本合并流程。
**无 merge 脚本的产物**（项目特有产物）由 LLM 直接输出完整 JSON，存到 `.allforai/code-replicate/` 目录。

dev-forge 和 cr-fidelity 根据**实际存在的产物文件**自适应消费（已有机制）。

---

按 extraction-plan.artifacts 列表顺序，逐产物执行：LLM 读 sources → 生成片段 → **4D 自检** → 合并（有脚本用脚本，无脚本 LLM 直接输出）。

### 4D 片段自检（每个 Step 生成后立即执行）

每生成一个模块的片段，LLM 用四维追问验证片段质量：

| 维度 | 追问 | 不通过则 |
|------|------|---------|
| **D1 结论** | 提取的 task/role/flow 是否完整覆盖该模块源码中的业务逻辑？有没有遗漏的入口？ | 补充遗漏项 |
| **D2 证据** | 每个 acceptance_criteria 能追溯到源码哪个文件哪段逻辑？protection_level 的判断依据是什么？ | 补充 `_evidence` 内部注释 |
| **D3 约束** | 遗漏了什么前置条件？异常路径覆盖了吗？跨模块依赖标注了吗？ | 补充 prerequisites/exceptions |
| **D4 决策** | category 判为 core 而非 basic 的理由？audience_type 判断是否合理？ | 修正判断或补充理由 |

4D 自检是**内嵌在每个 Step 中的思维过程**，不产出额外文件。如果自检发现问题，LLM 直接修正当前片段后再交给 merge 脚本。

### 标准产物 Step 参考（LLM 选择标准 .allforai/ 产物时使用）

> 以下 Step 3.1-3.6 仅在 extraction-plan.artifacts 包含对应标准产物时执行。
> 非标准项目（游戏/数据管道/CLI 等）的 artifacts 列表不含这些 Step → 跳过。

**Step 3.1** — role-profiles → `cr_merge_roles.py` → `product-map/role-profiles.json`
- LLM 按 extraction-plan.role_sources 读指定文件提取角色
- **LLM 片段必须输出 `audience_type`**（consumer / professional）— 基于角色在源码中的实际行为判断，不依赖名称关键词
- 可选：`operation_profile`（frequency/density/screen_granularity）

**Step 3.1.5** — experience-map stub（仅 frontend/fullstack）→ `cr_merge_screens.py` → `experience-map/experience-map.json`
- LLM 按 extraction-plan.screen_sources 读指定页面文件提取屏幕信息
- **LLM 片段必须输出每个 component 的 `render_as`**（12 值枚举）— 基于组件在页面中的实际用途判断
- **LLM 片段应输出 `layout_type`**（语义化布局名，如 auth_card、priority_queue，不用通用名如 "form"）

**Step 3.1.8** — 素材迁移（仅 frontend/fullstack 且 asset-inventory.json 存在时执行）

LLM 按 extraction-plan.asset_sources 处理每类素材：
- `copy` → 复制文件到目标项目对应目录 + 更新代码中的引用路径（源框架路径 → 目标框架路径）
- `transform` → LLM 读源主题/i18n 文件 → 生成目标框架等价配置（如 Ant Design token → Element Plus CSS Variables）
- `replace` → LLM 按 stack-mapping 转换格式（如 React SVG 组件 → Vue SFC 组件）

**路径映射**由 LLM 根据目标框架惯例决定：
- Next.js `public/` → Vite `public/`（直接映射）
- Next.js `app/*/icon.svg` (import) → Vue `src/assets/icons/` (import)
- 具体映射写入 `asset-migration-map.json` 供 cr-fidelity U7 验证

**Step 3.2** — task-inventory（两轮）→ `cr_merge_tasks.py` → `product-map/task-inventory.json`
- LLM 按 extraction-plan.task_sources 读指定文件提取任务
- 第一轮：骨架（id, title, module, type, role_id, category, protection_level）
- 第二轮：深层字段（acceptance_criteria, api_endpoint, prerequisites — 仅 functional+）
- **LLM 片段必须输出 `protection_level`**（core / defensible / nice_to_have）— 基于源码中该功能的业务重要性判断
- **LLM 片段必须输出结构化 `inputs`/`outputs`** — `inputs: {fields: [], defaults: {}}`，`outputs: {states: [], messages: [], records: [], notifications: []}`

**Step 3.3** — business-flows（functional+）→ `cr_merge_flows.py` → `product-map/business-flows.json`
- LLM 按 extraction-plan.flow_sources 读指定文件追踪完整业务流程
- 每个 flow 引用 task_id 列表（来自 Step 3.2 产物）

**Step 3.4** — use-case-tree + report（functional+）→ `cr_merge_usecases.py` + `cr_gen_usecase_report.py`
- 输出为**扁平 `use_cases` 数组**（v2.5.0+），每条包含显式 role_id、task_id、functional_area_name
- `then` 字段必须是**数组**（不是字符串）
- type 枚举已扩展至 13 种（含 journey_guidance, state_transition 等）
- report 由 gen 脚本从 JSON 自动生成，LLM 不直接写 Markdown

**Step 3.5** — constraints（exact only）→ `cr_merge_constraints.py` → `product-map/constraints.json`
- 标记源码中的硬约束：并发限制、数据一致性要求、外部 API 限流
- 标记已知 bug 和技术债（exact 保真度特有）

**Step 3.5.5** — 测试向量提取 → `test-vectors.json`

LLM 读 infrastructure-profile 中 `cannot_substitute: true` 或 `compatibility: exact` 的组件的源码实现，提取可验证的测试向量。

**向量模型由 LLM 根据 project_archetype 决定**（以下为常见模型，不限定）：

**模型 A — 单步（标准应用/加密/编解码）**：
```json
{"input": "...", "expected_output": "...", "description": "..."}
```

**模型 B — 多步序列（状态机/协议/SDK 调用链）**：
```json
{
  "initial_state": "...",
  "steps": [
    {"input": "...", "expected_state": "...", "expected_output": "..."},
    {"input": "...", "expected_state": "...", "expected_output": "..."}
  ]
}
```

**模型 C — 多角色并发（CRDT/协作/分布式）**：
```json
{
  "initial_state": "...",
  "operations": [
    {"actor": "A", "op": "...", "clock": "..."},
    {"actor": "B", "op": "...", "clock": "..."}
  ],
  "expected_merged_state": "...",
  "property": "LLM 描述该场景验证的形式化属性（如交换律、幂等性）"
}
```

**模型 D — ABI 签名（SDK/Library）**：
```json
{
  "function": "pm_process",
  "signature": {"params": ["pm_context_t*", "const pm_request_t*"], "return": "int"},
  "memory_ownership": {"param_0": "borrowed", "param_1": "borrowed", "return": "value"},
  "call_convention": "cdecl"
}
```

LLM 可以在同一个 test-vectors.json 中混合使用多种模型。

**向量来源**（优先级）：源码单元测试 > 标准测试向量（NIST/RFC） > 源码常量 > LLM 构造

**提取来源**（优先级）：
1. 源码的单元测试中已有的测试数据
2. 源码中的常量/fixture 数据
3. LLM 读懂算法后手动构造的测试向量

**用途**：dev-forge 生成目标代码后，用这些 test vectors 验证目标实现的行为与源码一致。cr-fidelity F8 基础设施还原可直接跑这些 vectors。

**Step 3.6** — 索引 + 汇总 → `cr_gen_indexes.py` + `cr_gen_product_map.py`
- task-index.json：轻量索引供下游按需加载
- flow-index.json：业务流索引
- product-map.json：全局汇总（统计 + 元信息 + **experience_priority**）
- `experience_priority` 从角色 audience_type 和任务分布自动推断 — dev-forge 全链路依赖此字段

**生成顺序有依赖**：role-profiles → task-inventory → business-flows → use-case-tree → constraints。
后续产物引用前序产物的 ID。

**每次 LLM 调用的上下文**：
- source-summary.json（~4-8 KB，常驻全局视角）
- 当前模块源码（~10-30 KB）
- 目标 schema 定义（~2-4 KB，按需加载）
- replicate-config 摘要（~1 KB）

---

### Phase 4: Verify & Handoff

**Step 4a** — `cr_validate.py` 结构校验 + **内循环修复**
- 检查项：必填字段完整、ID 引用有效、role_id/flow_id 存在、schema 合规
- 不通过 → 进入内循环修复：

```
内循环（CG-1 收敛控制）:
  1. 错误清单交 LLM 修正对应片段
  2. 重新 merge + validate
  3. 分类失败：
     - SCHEMA_ERROR  — 字段缺失/格式错误 → 修片段
     - REF_ERROR     — ID 引用断裂 → 修引用
     - LOGIC_GAP     — 业务逻辑不完整 → 补充片段
  4. 收敛条件：
     - 最多 3 轮修复
     - 每轮错误数必须 ≤ 上一轮（单调递减）
     - 违反单调递减 → 停止修复，剩余标记为 KNOWN_GAP
     - 第 3 轮仍有错误 → 记录为 KNOWN_GAP，继续 Step 4b
```

**Step 4b** — **6V 多维审计**（LLM 执行，不依赖外部工具）

LLM 从六个视角审查已合并产物，输出问题清单写入 `replicate-report.md`：

| 视角 | 审查内容 | 检查方式 |
|------|---------|---------|
| **user** | 每个角色的核心任务是否都被提取了？有没有角色有 0 个 task？ | 比对 role-profiles × task-inventory |
| **business** | 核心业务流是否有 flow 覆盖？orphan_tasks 中有没有核心任务？ | 检查 business-flows 覆盖 + orphan 列表 |
| **tech** | 技术约束（API 限制、并发、事务）是否进入 constraints 或 task.rules？ | 检查 constraint_sources 覆盖 |
| **data** | 数据实体是否完整？字段、关系、索引是否被记录？ | 比对 source-summary.data_entities × task.inputs/outputs |
| **ux** | （仅 frontend/fullstack）screen 的 states 是否覆盖 empty/loading/error/success？ | 检查 experience-map screens |
| **risk** | 安全/合规/隐私约束是否标注？支付/医疗/金融等高风险操作有 protection_level=core？ | 检查 constraints + task.protection_level |

6V 发现的问题分为两类：
- **可修复**：遗漏的 task、缺失的 flow 引用 → 回到 Step 4a 内循环补充
- **需标注**：无法从源码提取的信息（如合规要求需要人工确认）→ 写入 report 的 warnings

**Step 4b.5** — **注意力管理评估**（仅当 `experience_priority.mode` = consumer 或 mixed）

LLM 对 experience-map 中的 consumer 屏幕执行注意力负载检查：

| 检查项 | 阈值 | 问题标记 |
|--------|------|---------|
| 单屏操作步骤数 | >7 步 | `ATTENTION_OVERLOAD` |
| 跨屏记忆需求 | 需要用户记住前一屏信息才能完成当前操作 | `MEMORY_BURDEN` |
| 上下文切换 | 同一 flow 中页面跳转 >3 次 | `CONTEXT_SWITCH` |
| 反馈缺失 | 操作后无 loading/success 状态 | `FEEDBACK_GAP` |

注意力问题写入对应 screen 的 `_attention_flags` 字段，同时汇总到 report。这些 flag 在 dev-forge 的 design-to-spec 阶段会被消费，驱动 UI 简化决策。

**Step 4c** — XV 交叉验证（可选，需 `OPENROUTER_API_KEY`）
- 用不同模型审查产物一致性 → 问题写入产物 flags 字段
- 无 API key 时静默跳过

**Step 4d** — **外循环：意图保真验证**

> "走了这么多步，还在正确的路上吗？"

LLM 回到 source-summary.json 原点，验证提取结果是否覆盖业务意图：

```
OL-D1 模块覆盖度:
  - 读 source-summary.modules（全部模块清单）
  - 每个模块是否产出了至少 1 个 task？
  - file_count > 20 但 task_count = 0 的模块 → 标记为「提取遗漏」

OL-D2 抽象保全度:
  - 读 source-summary.abstractions
  - 每个 consumer_count > 3 的抽象是否进入了 stack-mapping.abstraction_mapping？
  - 未映射的高复用抽象 → 标记为「复用断裂」

OL-D3 横切覆盖度:
  - 读 extraction-plan.dependency_map（LLM 生成的模块间依赖，替代 cr_discover 的机械解析）
  - 读 extraction-plan.cross_cutting
  - 每个 dependency_map 中 type=middleware 的依赖是否在 flow 或 task.prerequisites 中出现？
  - 每个 cross_cutting 关注点是否有对应 task 或 flow 覆盖？
  - 未覆盖的横切点 → 标记为「横切遗漏」

OL-D4 角色完整性:
  - 读 role-profiles.json
  - 每个角色是否有 ≥1 个 use-case（happy_path）？
  - 无 use-case 的角色 → 标记为「角色空壳」

收敛控制（CG-3）:
  - 外循环发现的缺口总数 ≤ Phase 3 产物总条目数的 20%
  - 超过 20% → 停止补充，在 report 中标记"提取覆盖不足，建议提高保真度或扩大分析范围"
  - 外循环最多执行 1 轮（不递归）

追加项处理:
  汇总 OL-D1~D4 的缺口 → 回到 Phase 3 对应 Step 补充片段 → 重新 merge + validate
```

**Step 4e** — `cr_gen_report.py` → replicate-report.md
- 包含：源码概况、保真度、模块覆盖率、跳过项、校验结果、6V 审计结果、注意力评估、XV 发现、外循环意图覆盖度

**Step 4f** — Handoff
- 输出产物清单（路径 + 文件大小）
- 推荐下一步：`/project-setup` → `/design-to-spec` → `/task-execute`
- 跨栈复刻额外提示：检查 stack-mapping.json 中的手动决策点
- KNOWN_GAP 列表（内循环未修复 + 外循环超 20% 的遗漏项）

---

## 铁律

1. **Preflight + Discovery 收完所有参数** — Phase 2 结束后不再问任何配置问题
2. **source-summary 常驻上下文** — 所有 Phase 3 LLM 调用都包含它作为全局视角
3. **每次 LLM 调用单一目标** — 一次只生成一种产物的一个模块片段
4. **脚本合并产物** — LLM 不负责跨模块合并或 ID 分配
5. **标准产物路径** — task-inventory / business-flows / role-profiles → `product-map/`，use-case-tree → `use-case/`，CR 过程文件 → `code-replicate/`
6. **片段文件不是最终产物** — fragments/ 下的临时 JSON 仅供 merge 脚本消费，不交给 dev-forge
7. **业务意图优先** — 提取"做什么"，不复制"怎么做"；实现决策由目标生态填充
8. **下游必填字段** — `experience_priority`（product-map）、`protection_level`（task）、`audience_type`（role）、`render_as`（component）必须生成，dev-forge 全链路依赖
9. **结构化字段** — `inputs`/`outputs`/`audit` 必须使用对象格式（非简单数组），`then`（use-case）必须是数组
10. **LLM 直出优先** — `audience_type`、`protection_level`、`render_as` 等语义字段必须由 LLM 在片段中直接输出（基于源码语义理解），脚本仅做 fallback 兜底。禁止依赖名称关键词模式匹配作为主要判断逻辑
11. **extraction-plan 驱动** — Phase 3 的每个 Step 必须按 extraction-plan.json 中指定的文件和提取方式工作，不套用框架模板。extraction-plan 本身由 LLM 基于 source-summary 生成，确保适配任何技术栈和项目结构
12. **抽象复用传递** — 源码的复用模式（source-summary.abstractions）必须传递到目标代码。跨栈时通过 stack-mapping.abstraction_mapping 映射到目标栈等价机制；同栈时 dev-forge 直接读 abstractions。禁止将源码中 N 个模块共享的基类/mixin/DI 展开为 N 份重复代码
13. **4D 片段自检** — Phase 3 每个 Step 生成片段后必须执行 4D 追问（结论/证据/约束/决策），发现问题当场修正，不等到 Phase 4
14. **6V 多维审计** — Phase 4 必须从 user/business/tech/data/ux/risk 六个视角审查产物，防止单维盲区
15. **内循环收敛** — Phase 4a 修复循环遵循 CG-1：最多 3 轮、单调递减、违反则停止。防止无限修复循环
16. **外循环意图保真** — Phase 4d 回到 source-summary 原点验证提取覆盖度，遵循 CG-3：追加缺口 ≤ 总条目 20%、最多 1 轮。防止提取产物偏离源码业务意图
17. **跨平台适配** — 当源平台和目标平台交互模型不同（mobile↔desktop）时，必须生成 `platform_adaptation`。产物中的 UX 模式（布局、手势、导航、注意力阈值）不可原样传递到不同平台的目标代码。cr-fidelity 评估时使用适配后的阈值和排除列表
18. **配置即代码** — 非代码配置文件（nginx.conf, routes.yaml, OpenAPI spec, rbac.yaml, upstream.conf 等）可能包含路由定义、权限规则、基础设施配置等业务逻辑。extraction-plan 必须将这些文件纳入 task/role/flow 来源，使用 `"module": null` 引用根目录文件。source-summary.infrastructure 必须记录上游服务、共享内存、负载均衡等基础设施依赖
19. **基础设施先于业务** — Phase 2b-infra 必须在业务提取（Phase 3）之前完成。LLM 通过读代码行为（不是包名匹配）盘点所有基础设施组件，特别是自研组件、非标准协议、自定义加密、二进制 SDK。`cannot_substitute: true` 的组件禁止近似替代。通信协议和加密如果是耦合实现（如加密隧道），必须作为一个整体组件盘点，不可拆分
20. **协议必须结构化** — 自定义协议/加密/序列化组件必须输出 `protocol_spec`（帧格式 + 状态机 + 测试向量），不可只用文本描述。测试向量从源码测试或常量中提取，使目标代码可以精确验证行为一致性
21. **运行时验证** — cr-fidelity 不能只做代码对比（静态），必须包含运行时验证：构建（R1）、冒烟启动（R2）、测试向量执行（R3）、协议兼容性测试（R4）。综合分 = 静态分 × 0.5 + 运行时分 × 0.5。构建失败 = 一切白费
22. **项目特征驱动 + 产物自由化** — LLM 在 Phase 2.4 识别 project_archetype，在 Phase 3-pre 的 extraction-plan.artifacts 中自由决定输出什么产物、用什么 schema。标准 Web 应用自然选择 task-inventory + flows；游戏选择 system-spec + config-schema；数据管道选择 dag-spec + transform-catalog。不硬编码产物列表 — LLM 根据 archetype 自行决定
23. **素材即代码** — 前端/全栈项目的静态资源（图标、图片、字体、动画、主题变量、i18n 文案）是代码的组成部分，缺失则运行时碎图/缺字体/key 显示。Phase 2b-assets 必须盘点所有与代码有引用关系的素材，Phase 3.1.8 按 copy/transform/replace 三种方式迁移。cr-fidelity U7 验证素材完整性

---

## 保真度控制

保真度不决定生成哪些 CR 文件，而是决定标准产物中哪些字段被填充、填到多深。

| 级别 | 分析深度 | 产物输出 |
|------|---------|---------|
| interface | 只看入口层签名 | task-inventory(精简) + role-profiles（含 audience_type）+ product-map（含 experience_priority） |
| functional | 读函数体，追踪逻辑 | 上 + business-flows（含 systems/handoff）+ use-case-tree（扁平数组）+ task 结构化字段补全 |
| architecture | 额外分析模块依赖 | 上 + task 增加 module/prerequisites/cross_dept + innovation_use_case |
| exact | 额外标记 bug/约束 | 上 + constraints.json + task.flags |

> 完整说明详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity-guide.md

---

## 断点续跑

replicate-config.json 的 `progress` 字段追踪每一步的完成状态：

```json
"progress": {
  "current_phase": 2,
  "current_step": "2.8",
  "completed_steps": ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7"],
  "completed_artifacts": ["discovery-profile.json", "source-summary.json", "infrastructure-profile.json", "env-inventory.json", "third-party-services.json"]
}
```

**每完成一个 Step**，LLM 立即更新 `progress`（写 replicate-config.json）。崩溃后重启 → 从 `current_step` 继续。

- Phase 2 的 15 步精确到 `"2.1"` ~ `"2.15"`
- Phase 3 的每个 artifact 精确到 `"3.task-inventory"` / `"3.system-spec"` 等
- `--from-step 2.5` → 从 Step 2.5 重新开始（清除 2.5 及之后的 progress + 产物）
- `--from-phase 3` → 从 Phase 3 重新开始（保留 Phase 2 全部产物）

## 增量复刻

源码修改后，不需要重跑整个 pipeline：

```
/code-replicate --incremental
```

**增量检测**：
1. 比对源码当前 git hash vs `replicate-config.progress.source_hash`
2. `git diff` 找出修改的文件列表
3. 映射修改文件 → 受影响的模块（source-summary.modules）
4. 仅对受影响模块重新执行：
   - Stage B: 如果修改了基础设施代码 → 重跑 2.5-2.9
   - Stage C: 如果修改了素材/seed → 重跑 2.10-2.11
   - Phase 3: 仅重新生成受影响模块的片段 → 重新 merge
   - Phase 4: 重新 validate

不受影响的模块和产物保持不变。

## 跳过模块

source_path 中的某些模块不需要复刻（已经是目标栈、或不在迁移范围内）：

```
/code-replicate --skip payment-service,legacy-tool
```

或在 discovery-profile.json 中标注：

```json
"module_paths": [
  {"path": "payment-service", "skip": true, "reason": "已经是 Go，不需要复刻"},
  {"path": "user-service", "atomic": true}
]
```

skip 的模块：
- Phase 2: 不分析（不出现在 source-summary.modules 中）
- Phase 3: 不生成任何产物
- Phase 4: 不验证
- 但在 dependency_map 中仍然作为**外部依赖**记录（其他模块可能调用它）

## 并行化

Phase 2 Stage B 的 5 步（2.5-2.9）互相独立 → 可以用 Agent tool 并行执行：

```
Stage B 并行:
  Agent 1: 2.5 infrastructure-profile
  Agent 2: 2.6 env-inventory + 2.7 third-party-services（共享 .env 文件读取）
  Agent 3: 2.8 cron-inventory + 2.9 error-catalog
```

Phase 3 的模块片段生成也可以并行（不同模块互不依赖）。

LLM 自行决定是否并行 — 小项目串行更简单，大项目并行更快。

## 进度可见

每完成一个 Step，LLM 输出一行进度：

```
Phase 2 ▸ Stage A [████████████████████] 4/4 ✓
Phase 2 ▸ Stage B [████████████░░░░░░░░] 3/5 ⟳ 2.8 cron-inventory...
```

进度信息同时写入 `replicate-config.progress`（断点续跑用）和对话输出（用户可见）。

## 数据库 Schema 迁移

Phase 2 Stage C 的 seed-data-inventory 记录了**数据内容**，但没有记录**表结构**。

LLM 在 Step 2.11 同时提取 Schema 信息 → 写入 `seed-data-inventory.json` 的扩展字段：

```json
"schema": [
  {
    "table": "表名",
    "columns": [{"name": "...", "type": "...", "nullable": true, "default": "..."}],
    "indexes": [{"name": "...", "columns": ["..."], "unique": true}],
    "foreign_keys": [{"column": "...", "references": "其他表.字段"}]
  }
]
```

**来源**：Prisma schema / Django models.py / SQLAlchemy models / 迁移文件 / CREATE TABLE SQL。

dev-forge 读此 schema → 为目标栈生成等价的数据库迁移（如 GORM AutoMigrate / Prisma schema / SQL 迁移脚本）。

---

## 错误处理

| 场景 | 处理 |
|------|------|
| Git clone 失败 | Phase 1 报错退出 |
| 源码为空 | Phase 2a 报错退出 |
| LLM 返回无效 JSON | 重试一次，仍失败 → 跳过模块，标记 report |
| cr_validate.py 失败 | 错误清单给 LLM 修正，最多 2 轮 |
| 模块源码过大（>100KB） | 只读 key_files，标记 partial_analysis |
| 脚本不存在 | LLM 直接生成完整产物（降级模式） |

---

## 产物路径

**标准产物**（dev-forge 可消费）：
- `.allforai/product-map/`: product-map.json, task-inventory.json, role-profiles.json, business-flows.json, constraints.json, task-index.json, flow-index.json
- `.allforai/experience-map/`: experience-map.json（frontend/fullstack stub）
- `.allforai/use-case/`: use-case-tree.json, use-case-report.md

**CR 专属过程文件**：
- `.allforai/code-replicate/`: replicate-config.json, source-summary.json, discovery-profile.json, extraction-plan.json, stack-mapping.json, replicate-report.md
- `.allforai/code-replicate/fragments/`: 中间片段（合并后可删除）

---

## 脚本调用参考

所有脚本位于 `${CLAUDE_PLUGIN_ROOT}/scripts/`：

```bash
# Phase 2: Discovery (with optional LLM-generated profile)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_discover.py <source_path> <output_path> [--profile <profile_path>]

# Phase 3: Merge scripts
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_roles.py <base_path> <fragments_dir>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_screens.py <base_path> <fragments_dir>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_tasks.py <base_path> <fragments_dir>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_flows.py <base_path> <fragments_dir>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_usecases.py <base_path> <fragments_dir>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_constraints.py <base_path> <fragments_dir>

# Phase 3: Generation scripts
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_gen_usecase_report.py <base_path>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_gen_indexes.py <base_path>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_gen_product_map.py <base_path>

# Phase 4: Validation & Report
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_validate.py <base_path>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_gen_report.py <base_path>
```

**merge 脚本约定**：
- 读 `<fragments_dir>/*.json` → 合并去重 → 分配连续 ID → 写入 `<base_path>` 对应标准路径
- fragments 文件名格式：`{module_name}.json`（每模块一个片段文件）
- 合并时自动处理：ID 重编号、跨片段引用修正、重复条目去重

**gen 脚本约定**：
- 读已合并产物 → 生成派生文件（report / index / summary）
- 不修改已合并的标准产物

**LLM 片段生成格式**：
- 每次 LLM 调用输出一个模块的 JSON 片段
- 片段使用临时 ID（如 `TMP-001`），merge 脚本统一重编号
- 跨模块引用使用 `$ref:module_name:tmp_id` 占位符，merge 脚本解析替换
- **片段必须包含语义字段**（不可省略让脚本猜测）：
  - role 片段：`audience_type`（consumer / professional）
  - task 片段：`protection_level`（core / defensible / nice_to_have）、结构化 `inputs`/`outputs`
  - screen 片段：每个 component 的 `render_as`（12 值枚举）、`layout_type`（语义名称）
