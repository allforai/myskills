---
description: "产品设计全流程编排：concept → map → screen → [use-case ∥ gap ∥ ui-design] → audit。模式: full / resume"
argument-hint: "[mode: full|resume] [skip: concept]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "WebSearch", "Agent"]
---

# Product Design Full — 产品设计全流程编排

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 设计思想入口（建议先读）

执行全流程前，建议先阅读：

- `${CLAUDE_PLUGIN_ROOT}/docs/product-design-principles.md`

该文档汇总前段/中段/尾段的经典理论支持（如第一性原理、JTBD、Kano、Nielsen、ISO 9241-11、WCAG）及参考文献。

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 从头执行全流程（已有产物作为参考但会重新生成）
- **`full skip: concept`** → 从头执行，但跳过 Phase 1 概念发现
- **`resume`** → 检测已有产物，从第一个未完成阶段开始

## 编排流程

每个生成阶段遵循统一模式：**LLM 生成 → 4D/6V/闭环 verify loop（以上一级产物为基准验证）→ 自动修正 → 继续下一阶段**。

**唯一的强制人工审核门：Phase 5 wireframe-review**。其他阶段仅靠 verify loop 自动验证，不强制弹出人工审核。

**所有阶段均可审核**：用户随时可通过 `/review` 命令启动 Review Hub，审核任意阶段产物（概念/地图/数据模型/线框/UI 等），收集反馈并迭代修改。非强制 ≠ 不可用。

```
Phase 0: 产物探测
  ↓
Phase 1: concept — LLM 生成 → verify loop（以用户需求为基准）
  ↓
Phase 2: product-map — LLM 生成 → verify loop（以 concept 为基准）
  ↓
Phase 3: journey-emotion — LLM 生成 → verify loop（以 product-map 为基准）
  ↓
Phase 4: experience-map — LLM 生成 → verify loop（以 journey-emotion + product-map 为基准）→ interaction-gate（experience-map Step 3.6 已内置模式扫描+行为规范）
  ↓
Phase 5: wireframe — Playwright verify loop → ★ 人工审核 ★（唯一强制门）→ 结构锁定
  ↓
Phase 6: 并行执行 — use-case / feature-gap / ui-design（各含 verify loop，以 experience-map 为基准）→ 聚合 checkpoint
  ↓
Phase 7: ui-verify — Playwright verify loop（自动，以 ui-design 为基准）
  ↓
Phase 8: design-audit（终审）
```

### 统一 verify loop 执行模板

所有阶段的 verify loop 执行同一模式。**核心原则：以上一级产物为基准验证当前产物**。

```
loop (max 3 rounds):
  1. python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_review.py <BASE> --phase <PHASE> [--xv]
     → stdout JSON: 产出上下文 + 4D/6V/闭环审查问题 [+ XV 跨模型意见]
  2. LLM 读取输出，以上一级产物为基准审查：
     - 4D: 结论正确(D1)？有证据(D2)？约束识别(D3)？决策有依据(D4)？
     - 6V: user/business/tech/ux/data/risk 六视角是否合理
     - 闭环: 配置/监控/异常/生命周期/映射/导航 是否完整
     - XV（如有）: 第二模型意见是否成立
  3. 发现问题 → 自动修改源文件 → 回到 1
     没有问题 → 退出 loop，直接进入下一阶段
```

**验证基准链**：
| Phase | 当前产物 | 验证基准（上一级） |
|-------|---------|--------------|
| 1 concept | product-concept.json | 用户需求描述 |
| 2 product-map | task-inventory + business-flows | product-concept.json |
| 3 journey-emotion | journey-emotion-map.json | business-flows.json |
| 4 experience-map | experience-map.json | journey-emotion + task-inventory + entity-model |
| 6 use-case | use-case-tree.json | task-inventory + experience-map |
| 6 feature-gap | gap-tasks.json | task-inventory + experience-map + business-flows |
| 6 ui-design | ui-design-spec.md | experience-map（含 _pattern*、_behavioral* 字段） |

各阶段对应的 `--phase` 值：concept / map / journey / experience / use-case / feature-gap / ui-design / wireframe / ui

---

## Phase 0：产物探测

扫描以下目录，判断每个阶段的完成状态：

| Phase | 阶段 | 完成标志 |
|-------|------|----------|
| 1 | concept | `.allforai/product-concept/` 存在 |
| 1.5 | concept-baseline | `.allforai/product-concept/concept-baseline.json` 存在（推拉协议的推侧） |
| 2 | product-map | `.allforai/product-map/task-inventory.json` 存在且 task 数 > 0 |
| 3 | journey-emotion | `.allforai/experience-map/journey-emotion-map.json` 存在 |
| 4 | experience-map | `.allforai/experience-map/experience-map.json` 存在且 screen 数 > 0 |
| 4 | interaction-gate | `.allforai/experience-map/interaction-gate.json` 存在 |
| 5 | wireframe-review | `.allforai/wireframe-review/review-feedback.json` 存在且 submitted_at 非空（唯一人工门） |
| 6 | use-case | `.allforai/use-case/use-case-tree.json` 存在 |
| 6 | feature-gap | `.allforai/feature-gap/gap-tasks.json` 存在 |
| 6 | ui-design | `.allforai/ui-design/ui-design-spec.md` 存在 |
| 7 | ui-verify | Playwright verify loop 完成（自动，无人工门） |
| 8 | design-audit | `.allforai/design-audit/audit-report.json` 存在 |

**full 模式**：从 Phase 1（或 Phase 2 如果 skip concept）开始。
**resume 模式**：从第一个未完成阶段开始。

> **并行组**: Phase 6 的 use-case / feature-gap / ui-design 并行执行。
> resume 模式下，仅当该组全部完成才视为"Phase 6 已完成"，否则补跑缺失的。

向用户展示探测结果。

### 外部能力快检

> 统一协议见 `${CLAUDE_PLUGIN_ROOT}/docs/skill-commons.md`「外部能力探测协议」。

产物探测后，检测本流水线涉及的外部能力并输出状态：

| 能力 | 探测方式 | 重要性 |
|------|---------|--------|
| OpenRouter (MCP) | `mcp__plugin_product-design_ai-gateway__ask_model` 可用性 | 可选 |
| OpenRouter (Script) | `OPENROUTER_API_KEY` 环境变量 | 可选 |
| Stitch UI | `mcp__plugin_product-design_stitch__create_project` 可用性 | 可选 |
| Playwright | `mcp__playwright__browser_navigate` 或 `mcp__plugin_playwright_playwright__browser_navigate` 可用性 | 可选 |
| WebSearch | 内置，始终可用 | 核心 |

**输出格式**（每行一个能力）：

```
外部能力:
  OpenRouter (MCP)    ✓ 就绪          XV 交叉验证（MCP 通道）
  OpenRouter (Script) ✓ 就绪          XV 交叉验证（脚本通道）
  Stitch UI           ✗ 未就绪        UI 视觉稿（可选，/setup check 查看详情）
  Playwright          ✓ 就绪          线框自动验证（Phase 4.7）
  WebSearch           ✓ 内置          搜索驱动设计
```

此通知仅为信息性输出，不阻塞任何流程。未就绪的可选能力自动跳过，提示格式统一为 `{step} ⊘ {能力} 不可用，{降级动作}`。

未配置 API Key 的服务提示运行 `/setup` 配置（Key 存储在 shell 环境变量）。

确认执行计划后开始。

---

## Phase 1：concept（可选）

**跳过条件**：用户指定 `skip: concept`，或 resume 模式下已完成。

**执行**：
1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/product-concept.md`
2. 按 product-concept 技能的完整工作流执行

**检查点**：concept 产出目录存在。

---

## 自动模式检测

Phase 1（product-concept）执行完毕后，检测自动模式条件：

1. 读取 `.allforai/product-concept/product-concept.json`
2. 检查 `pipeline_preferences` 字段是否存在
3. **存在** → 启用自动模式：
   - 后续 Phase 2-7 每个技能调用时携带上下文标记 `__orchestrator_auto: true`
   - 检查点策略切换为三级评估（见下方）
   - 向用户展示：「检测到流水线偏好，启用全自动模式 — ERROR 级问题才停，WARNING 记日志继续」
4. **不存在** → 交互模式（当前行为不变）

### 检查点三级评估（自动模式）

自动模式下，后续 Phase 的每个检查点行为变更：

| 级别 | 条件 | 行为 |
|------|------|------|
| **ERROR** | 必填字段缺失、引用断裂、task 数 = 0、必须文件不存在 | **停下来问用户**，展示错误详情，等待用户决策 |
| **WARNING** | 推荐字段缺失、覆盖率低于预期、轻微不一致 | 记入 `.allforai/pipeline-decisions.json`（`decision: "auto_continued"`），展示日志行后自动继续 |
| **PASS** | 检查全部通过 | 自动继续，展示一行摘要 |

### `pipeline-decisions.json`（自动模式决策日志）

自动模式下所有自动确认和自动跳过的决策记录在此文件，用户事后可审查：

```json
[
  {
    "phase": "Phase 2",
    "skill": "product-map",
    "step": "Step 1",
    "decision": "auto_confirmed",
    "severity": "PASS",
    "summary": "角色列表 3 个，无差异",
    "decided_at": "ISO timestamp"
  },
  {
    "phase": "Phase 4",
    "skill": "experience-map",
    "step": "Step 2",
    "decision": "auto_continued",
    "severity": "WARNING",
    "summary": "2 个 SILENT_FAILURE 检出，已记录",
    "details": ["S008 批量导出无 on_failure", "S012 删除操作无确认弹窗"],
    "decided_at": "ISO timestamp"
  }
]
```

---

## Phase 1 — Step 2：concept-verify

按统一 verify loop 执行（`--phase concept`）。

**本阶段闭环重点**：
- pain↔reliever 双向映射：每个痛点有缓解方案吗？每个方案对应哪个痛点？
- gain↔creator 双向映射：每个收益有创造机制吗？
- mechanism→JTBD 映射：每个产品机制服务于哪个用户任务？有孤立机制吗？
- revenue→value 映射：每个收费项有对应的价值交付吗？

---

verify loop 通过后直接进入 Phase 1 — Step 3。用户可随时通过 `/review` 命令手动启动 Review Hub 查看任意阶段产物。

---

## Phase 1 — Step 3：生成概念蒸馏基线

> 推拉协议的「推」侧。详见 `skill-commons.md` §三.A。

verify loop 通过后，编排器自动从概念产物中提取紧凑基线：

1. 读取 `.allforai/product-concept/product-concept.json` + `role-value-map.json` + `product-mechanisms.json`
2. LLM 按 `skill-commons.md` §三.A 的固定 schema 提取字段，生成 `.allforai/product-concept/concept-baseline.json`
3. 控制文件大小在 2KB 以内

**检查点**：`concept-baseline.json` 存在且包含 `mission`、`roles`、`governance_styles` 字段。

**自动模式**：直接生成，PASS 后继续。文件过大（>3KB）→ WARNING，记日志继续。

生成完成后直接进入 Phase 2，不弹出人工审核。

---

## Phase 1-2：pipeline-decisions 写入

concept 和 product-map 完成后，追加记录到 `.allforai/pipeline-decisions.json`：

```json
{"phase": "Phase 1 — concept", "decision": "auto_confirmed", "detail": "concept generated", "decided_at": "..."}
{"phase": "Phase 2 — product-map", "decision": "auto_confirmed", "detail": "tasks=N, roles=M, flows=K", "decided_at": "..."}
```

按 `phase` 字段去重 — 重跑时替换已有条目，不产生重复。

---

## Phase 2：product-map

**执行**：
1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/product-map.md`
2. 按 product-map 技能的完整工作流执行
3. 完成后追加 pipeline-decisions 记录（自动模式下）

**检查点**：
- `task-inventory.json` 存在
- task 数量 > 0
- `task-inventory-basic.json` 和 `task-inventory-core.json` 存在
- 每个 task 有 `category` 字段（basic 或 core）

检查点失败 → 向用户报告，询问是否继续（product-map 是后续所有阶段的基础，强烈建议修复）。

**自动模式检查点**：task 数 = 0 → ERROR（停）；category 字段缺失 → WARNING（记日志继续）；task 数 > 0 且分类完整 → PASS。

---

## Phase 2 — Step 2：map-verify

按统一 verify loop 执行（`--phase map`）。

**本阶段闭环重点**：
- 四类闭环审计：每个功能任务的配置/监控/异常/生命周期闭环是否完整
- mechanism→task 映射：concept 里的每个产品机制是否都有对应任务
- task→flow 映射：高频任务是否至少出现在一条业务流中

---

verify loop 通过后直接进入 Phase 3，不弹出人工审核。

---

## Phase 3：journey-emotion

**Step 1: 生成**
1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/journey-emotion.md`
2. 按 journey-emotion 技能的完整工作流执行

**Step 2: verify loop**（`--phase journey`）

**本阶段闭环重点**：
- 低谷→恢复闭环：每个情感低谷有对应的设计干预和恢复节点吗？
- 旅程始→终闭环：每条旅程线有明确起终点吗？终点情感正面吗？（Peak-End Rule）
- 失败→继续闭环：高 risk 节点失败后能否回到正常流程？

---

## Phase 4：experience-map

**Step 1: 生成**

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/experience-map.md`，按 skill 工作流执行。LLM 主导屏幕设计。

**Step 1.5: verify loop**（`--phase experience`）

**本阶段闭环重点**：
- 导航闭环：每个屏幕可达且可退，无死胡同
- 状态机闭环：每个状态有出口转换，无状态死锁
- 错误→恢复闭环：每个可能失败的操作有恢复路径回到正常流程
- task→screen 映射闭环：所有 core task 都有对应屏幕

---

## Phase 4 — Step 2：interaction-gate

**执行**：
1. 用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/interaction-gate.md`，按其工作流执行
2. LLM 分析 experience-map + task-inventory，识别交互风险点并生成门禁报告

**检查点**：
- `gate-report.json` 存在

---

## Phase 5 — Step 1：wireframe-verify（Playwright verify loop）

> 统一验收方法论的 Playwright 变体：Playwright 采集视觉上下文 → LLM 用 4D+6V+闭环审查 → 改源 → loop 到干净。

### 前置条件

- experience-map 已完成（screen 数 > 0）
- Playwright MCP 可用（激活工具或 deferred tools 中）
- Playwright 不可用 → 跳过，记录 `playwright_skipped`，进入 wireframe-review

### 执行

```
loop:
  1. 确保 Review Hub 运行
  2. Playwright 导航到 http://localhost:18900/wireframe
  3. 逐屏点击 → snapshot → LLM 判断：
     - 交互类型 vs 渲染布局是否匹配？（业务语义与布局 slots 是否对应）
     - data_fields 的字段名是否出现在渲染中？
     - actions 的按钮是否存在？
     - 产品语言（中文/英文）与 UI 文本是否一致？
     - Flow 面板的上下游指向对不对？
  4. 发现问题 → 直接修改 experience-map.json → 回到 1
     没有问题 → 退出 loop，进入 wireframe-review 人工审核
```

**关键**：LLM 审查的是**业务合理性**，不只是"字段存在"。交互类型描述的业务场景必须与实际渲染的布局语义一致。

---

## Phase 5 — Step 2：wireframe-review（人工审核 — 结构锁定门）

experience-map + interaction-gate 完成后，**在视觉设计之前**进行低保真结构审核。

**目的**：验证 IA 结构、屏幕流转和功能完整性。此阶段发现的问题可能导致 product-map 或 experience-map 变更，因此必须在投入视觉设计前完成。

**执行**：

1. **复用 Review Hub（或重启）**：
   ```
   检查 http://localhost:18900/ 是否可达：
     可达 → 提示用户刷新 /wireframe tab
     不可达 → 重新启动: python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_hub_server.py <BASE> --port 18900
   ```
   - 输出：`审核站点已运行: http://localhost:18900/wireframe → 请在线框 tab 中审核`
   - 补充提示：`数据模型也可查看: http://localhost:18900/data-model`
   - 界面按角色或情感旅程线分组
   - 用户点击线框添加 pin 评论，选择反馈类别（Flow/Structure → experience-map、Feature/Task → product-map、Concept → concept）
   - 审核完毕点击 "Submit Feedback"

2. **读取反馈并路由**：
   - 读取 `.allforai/wireframe-review/review-feedback.json`
   - K = 0 → 全部通过，结构锁定，进入 Stitch 决策点
   - K > 0 → 按类别汇总修复建议：
     - product-map 类 → 提示重跑 product-map + experience-map
     - experience-map 类 → 提示重跑 experience-map
     - concept 类 → 提示回到 product-concept
   - 修复后用户在 Hub 重新审核

3. **迭代循环**（最多 3 轮）

4. **3 轮后仍有未通过** → 记录 `wireframe_review_incomplete`，继续

**不可跳过**：wireframe-review 是必须环节，自动模式下也必须执行。

**resume 模式**：
- `review-feedback.json` 存在且所有 status="approved" → 跳过
- `review-feedback.json` 存在但有 status="revision" → 从迭代步骤继续
- 不存在 → 正常启动

---

## Phase 5 — Step 3：Stitch 可用性决策点

wireframe-review 通过后、进入 Phase 6 并行执行前，检查 Stitch 可用性：

```
检查 mcp__plugin_product-design_stitch__create_project 是否可用:
  可用 → 继续（Stitch 将在 Phase 6 ui-design 中使用）
  不可用 → AskUserQuestion（3 选 1）:
    A) 上传设计稿 — 用户手动上传 mockup 到 .allforai/ui-design/mockups/
    B) 跳过视觉验收 — 继续，但 forge-report 标注「Visual quality NOT verified」
    C) 配置 Stitch — 中断，运行 /setup 配置后重新执行

    用户选 B:
      记录 pipeline-decisions: { decision: "stitch_skipped", reason: "user acknowledged" }
      design-audit 将标记 stitch_skipped: true
    用户选 C:
      终止当前流程，提示运行 /setup
```

---

## Phase 6 生成策略

**LLM 主导生成**：

产品设计阶段的所有内容生成任务（用例推导、缺口分析、UI 设计）均由 LLM 主导。LLM 理解业务领域语境，根据上游产物自主设计。验证由上一阶段的 verify loop 完成。

---

## Phase 6：并行执行

> use-case、feature-gap、ui-design 之间无数据依赖（均仅依赖 product-map + experience-map），使用 Agent tool 并行执行。

### 执行方式

Phase 5 通过后，用**单条消息发出 3 个 Agent tool 调用**并行执行。
Agent tool 的屏障同步机制保证 3 个 Agent 全部完成后才继续到聚合 checkpoint。

每个 Agent 的 prompt 模板：

~~~
你是产品设计流水线的并行执行器。

任务: 执行 {skill-name} 技能的完整工作流 + 统一 verify loop。

执行步骤:
1. 用 Read 工具加载 ${CLAUDE_PLUGIN_ROOT}/skills/{skill-name}.md
2. 按该技能的完整工作流执行（不跳步骤、不简化）
3. 产出写入 .allforai/{skill-name}/ 目录
4. 按统一 verify loop 执行（--phase {verify-phase}），loop 到干净
5. pipeline-decisions 写入分片文件 .allforai/pipeline-decisions-{skill-name}.json

重要:
- 禁止直接写入 pipeline-decisions.json 主文件
- LLM 主导生成，按 skill.md 工作流执行
- 不要读写其他并行 Agent 的产出目录
- 每个 skill 的 .md 文件指明了生成方式和输出 schema 约束，严格遵循
~~~

3 个 Agent 调用的具体参数：

| Agent | skill-name | 生成方式 | 产出目录 | 分片文件 |
|-------|-----------|---------|---------|---------|
| Agent 1 | use-case | LLM 主导 | `.allforai/use-case/` | `pipeline-decisions-use-case.json` |
| Agent 2 | feature-gap | LLM 主导 | `.allforai/feature-gap/` | `pipeline-decisions-feature-gap.json` |
| Agent 3 | ui-design | LLM 主导 | `.allforai/ui-design/` | `pipeline-decisions-ui-design.json` |

### 聚合 checkpoint

3 个 Agent 全部返回后，编排器执行聚合 checkpoint。分三步：检测 → 解决 → 验证通过。

---

**Step 0: 检测（脚本）**

执行 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_aggregate_checkpoint.py <BASE> --mode auto`

脚本自动完成：
- 合并分片 `pipeline-decisions-*.json` → 主文件（去重，删分片）
- 检测 4 类跨 skill 冲突，输出 `aggregate-checkpoint.json`
- exit 0 = 无冲突（PASS/WARNING），跳到 Step 2
- exit 1 = 有 CONFLICT 或 ERROR，进入 Step 1 解决

---

**Step 1: 概念驱动冲突解决（LLM）**

脚本检测到 CONFLICT/ERROR 后，编排器读取 `aggregate-checkpoint.json` 的 `findings` 数组，**逐条回溯产品概念解决**。

**1.1 加载概念上下文**

用 Read 加载 `.allforai/product-concept/product-concept.json`，提取：
- `mission` — 产品定位
- `roles[].jobs / pain_relievers / gain_creators` — 角色价值
- `strategy.errc.reduce` 中 `kano=must-have` 的条目 — 不可削减功能
- `strategy.errc.create` — 差异化功能

**1.2 逐条解决冲突**

对 findings 中每个 `severity=CONFLICT` 或 `severity=ERROR` 的条目，回溯产品概念解决。

**1.3 追加 pipeline-decisions 记录**

```json
{"phase": "Aggregation — conflict resolution", "decision": "auto_resolved", "detail": "N conflicts resolved via concept: ...", "decided_at": "..."}
```

---

**Step 2: 验证通过（脚本重跑）**

再次执行 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_aggregate_checkpoint.py <BASE> --mode auto`

- exit 0 → 所有检查通过，进入 Phase 7
- exit 1 → 仍有冲突 → 回到 Step 1 再次解决（最多 3 轮）
- 3 轮后仍 exit 1 → 向用户展示剩余冲突，等待人工决策

---

**聚合 checkpoint 严重级定义**：

| 级别 | 含义 | 行为 |
|------|------|------|
| ERROR | 安全护栏违规 | Step 1 无条件修复 |
| CONFLICT | 跨 skill 矛盾 | Step 1 概念驱动修复 |
| WARNING | 覆盖率不足等 | 记日志，不阻塞 |
| PASS | 检查通过 | 继续 |

### 错误处理

~~~
3 个 Agent 返回后:
  检查每个 Agent 的返回结果:
    全部成功 → 执行聚合 checkpoint → 进入 Phase 7
    部分失败 →
      成功的 Agent: 正常收集产出
      失败的 Agent: 记录错误信息
      向用户报告:
        "Phase 6 并行执行结果:
         ✓ use-case: 完成
         ✓ feature-gap: 完成
         ✓ ui-design: 完成"
      询问用户:
        1. 重试失败的 skill（仅重跑失败的 Agent）
        2. 跳过继续到 Phase 7（ui-review → design-audit）
        3. 中止流程
    全部失败 →
      向用户报告所有错误
      询问: 全部重试 / 中止
~~~

### resume 模式下的并行处理

~~~
resume 模式检测 Phase 6 完成状态:
  3 个产出全部存在（use-case, feature-gap, ui-design） → 跳过 Phase 6，进入 Phase 7
  部分存在 → 仅启动缺失产出对应的 Agent（已有产出不重跑）
  全部不存在 → 正常启动 3 个并行 Agent
~~~

---

## Phase 7 — Step 1：ui-verify（Playwright verify loop）

> 统一验收方法论的 Playwright 变体：Playwright 采集视觉上下文 → LLM 用 4D+6V+闭环审查 → 改源 → loop 到干净。

**前置条件**：Playwright MCP 可用。不可用 → 跳过，记录 `playwright_skipped`。

**本阶段闭环重点**：
- 操作→反馈闭环：每个按钮/操作在 UI 中有对应的视觉反馈吗？
- 破坏→确认闭环：不可逆操作有确认对话框吗？
- 表单→状态闭环：输入字段有空/合法/错误等完整状态吗？
- 视觉一致性：相同类型屏幕使用相同组件模式？

---

## Phase 7 — Step 2：ui-review（可选人工审核）

Playwright verify loop 通过后，**自动进入 Phase 8**（design-audit），不强制弹出人工审核。

但用户可随时通过 `/review` 命令启动 Review Hub 审核 UI 设计，收集反馈并迭代修改。

**触发方式**：用户主动运行 `/review`，或在全流程结束后审核。

**审核流程**（用户触发后）：

1. **启动 Review Hub**：
   - 复用已运行的 Hub 或重启：`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_hub_server.py <BASE> --port 18900`
   - 输出：`审核站点已运行: http://localhost:18900/ui → 请在 UI tab 中审核`
   - 用户点击界面添加 pin 评论，提交反馈

2. **读取反馈并迭代**：
   - 读取 `.allforai/ui-review/review-feedback.json`
   - K = 0 → 无修改意见，继续
   - K > 0 → 对 status="revision" 的界面重新生成（局部重跑 ui-design），最多 3 轮

**自动模式**：Phase 7 仅执行 Playwright verify loop，直接进入 Phase 8。用户事后可 `/review` 审核。

---

## Phase 8：design-audit（终审 — 三阶段并行架构）

**执行**：
1. 用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-audit.md`

**Phase A（脚本，串行）**：确定性检查

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_design_audit.py <BASE> [--mode auto]
```

脚本执行逆向追溯、覆盖洪泛、横向一致性、连贯性、信息保真、XV 交叉验证。
输出 `.allforai/design-audit/audit-report.json`（基线报告）。

**Phase B（LLM，并行 3 Agent）**：语义审计

用**单条消息发出 3 个 Agent tool 调用**并行执行。Agent 屏障同步机制保证全部完成后才继续。

每个 Agent 的 prompt 模板：

~~~
你是设计审计流水线的并行审计器。

任务: 执行 {审计维度} 的完整检测流程。

上下文:
- 读取 .allforai/design-audit/audit-report.json（Phase A 基线报告，只读）
- 读取 .allforai/experience-map/experience-map.json
- 读取相关上游产物（见 design-audit.md 对应 Step 的前置条件）

执行:
1. 用 Read 加载 ${CLAUDE_PLUGIN_ROOT}/skills/design-audit.md
2. 按对应 Step 的检测项逐一执行
3. 前置条件不满足 → status="skipped"，仍写分片文件
4. 结果写入: .allforai/design-audit/audit-shard-{shard_name}.json

重要:
- 禁止修改 audit-report.json（Phase A 产出）
- 禁止读写其他 Agent 的分片文件
~~~

| Agent | 审计维度 | 对应 Step | 分片文件 |
|-------|---------|----------|---------|
| Agent 1 | 模式一致性 + 创新保真 | Step 5 + Step 5.5 | `audit-shard-pattern.json` |
| Agent 2 | 行为一致性 | Step 5.6 | `audit-shard-behavioral.json` |
| Agent 3 | 交互类型一致性 | Step 5.7 | `audit-shard-interaction.json` |

**Phase C（合并）**：汇总报告

3 个 Agent 全部返回后，编排器执行：
1. 读取 `audit-report.json`（Phase A 基线）+ 3 个 `audit-shard-*.json` 分片
2. 合并分片 sections 到主报告的 `summary` 和 issues 字段
3. 重新生成 `audit-report.md`（含全部维度）
4. 删除分片文件

**quick 模式**：仅执行 Phase A 脚本，跳过 Phase B/C。

**自动模式检查点**：审计正常执行，所有结果写入报告。CONFLICT 级问题在摘要中高亮标注。自动模式下终审不停，但摘要中列出所有积累的 WARNING 条目总数。

**输出**：终审报告 + 全流程执行摘要

---

## 全流程执行摘要（强制输出）

所有阶段完成后，在对话中输出全流程摘要：

```
## 产品设计全流程执行摘要

> 执行模式: {full/resume}
> 执行时间: {开始时间} — {结束时间}

### 各阶段状态

| Phase | 阶段 | 状态 | 备注 |
|-------|------|------|------|
| 1 | concept | 完成/跳过 | verify loop: X 轮, review: X 轮 |
| 2 | product-map | 完成 | task 数: X, verify loop: X 轮, review: X 轮 |
| 3 | journey-emotion | 完成 | — |
| 4 | experience-map | 完成 | screen 数: X |
| 5 | wireframe-review | 完成 | Playwright verify: X 轮, 人工审核: X 轮 |
| 6 | 并行组 | 完成/部分失败 | use-case/feature-gap/ui-design |
| 7 | ui-verify | 完成 | Playwright verify: X 轮（人工审核: 可选，/review 触发） |
| 8 | design-audit | 完成 | 见终审报告 |

### 终审评分

- 逆向追溯：X ORPHAN
- 覆盖洪泛：覆盖率 XX%
- 横向一致性：X CONFLICT / X WARNING

### 产出文件

> 全部产出位于 `.allforai/` 目录下
> 终审报告: `.allforai/design-audit/audit-report.md`
```

---

## 铁律

1. **每阶段加载对应 skill** — 不跳步骤，不简化流程，完整执行每个技能的工作流
2. **检查点必须验证** — 每个阶段结束后验证产出存在性，失败时向用户报告
3. **用户可在任意阶段中止** — 检查点失败或用户主动中止时，保存已有产出，输出部分摘要
4. **verify loop 不替代终审** — 阶段内的 verify loop 保证内容正确性，完整校验由 Phase 8 design-audit 负责
5. **产品设计内只读不改上游** — 产品设计流水线内，后序阶段发现上游问题时只报告，不自动回退修改上游产物。**开发阶段例外**：开发阶段发现上游漏掉的支撑功能时，按逆向补漏协议（skill-commons §五）回补上游（补漏不开新战线）
6. **并行 Agent 产出隔离** — Phase 6 的 3 个并行 Agent 各自写入独立目录和分片 pipeline-decisions 文件，不读写其他 Agent 的产出。聚合由编排器在全部完成后统一执行
7. **Phase 转换零停顿** — 严禁在 Phase 之间停下来问"继续？""进入下一阶段？"等确认性问题。检查点 PASS 后直接加载下一阶段 skill 并执行，只输出一行状态摘要（如 `Phase 3 ✓ → Phase 4`）。唯一允许停顿的场景是 ERROR 级安全护栏
