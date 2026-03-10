---
description: "产品设计全流程编排：concept → map → screen → [use-case ∥ gap ∥ ui-design] → audit。feature-prune 可选手动执行。模式: full / resume"
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

每个生成阶段遵循**统一验收方法论**（详见 `docs/skill-commons.md` §三）：

```
生成 → verify loop（4D+6V+闭环+XV）→ 干净后进入人工审核或下一阶段
```

```
Phase 0: 产物探测
  ↓
Phase 1: concept — 生成 → verify loop → concept-review
  ↓
Phase 2: product-map — 生成 → verify loop → map-review
  ↓
Phase 3: journey-emotion — 生成 → verify loop
  ↓
Phase 4: experience-map — 生成 → verify loop → interaction-gate → design-pattern → behavioral-standards
  ↓
Phase 5: wireframe-review — Playwright verify loop → 人工审核 → 结构锁定
  ↓
Phase 6: 并行执行 — use-case / feature-gap / ui-design（各含 verify loop）→ 聚合 checkpoint
  ↓
Phase 7: ui-review — Playwright verify loop → 人工审核
  ↓
Phase 8: design-audit（终审）
```

### 统一 verify loop 执行模板

所有阶段的 verify loop 执行同一模式，仅 `--phase` 参数不同：

```
loop (max 3 rounds):
  1. python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_review.py <BASE> --phase <PHASE> [--xv]
     → stdout JSON: 产出上下文 + 4D/6V/闭环审查问题 [+ XV 跨模型意见]
  2. Claude Code 读取输出，按统一验收方法论审查：
     - 4D: 结论正确(D1)？有证据(D2)？约束识别(D3)？决策有依据(D4)？
     - 6V: user/business/tech/ux/data/risk 六视角是否合理
     - 闭环: 配置/监控/异常/生命周期/映射/导航 是否完整
     - XV（如有）: 第二模型意见是否成立
  3. 发现问题 → 修改源文件 → 回到 1
     没有问题 → 退出 loop
```

各阶段对应的 `--phase` 值：concept / map / journey / experience / use-case / feature-gap / ui-design / wireframe / ui

---

## Phase 0：产物探测

扫描以下目录，判断每个阶段的完成状态：

| Phase | 阶段 | 完成标志 |
|-------|------|----------|
| 1 | concept | `.allforai/product-concept/` 存在 |
| 1 | concept-review | `.allforai/concept-review/review-feedback.json` 存在且 submitted_at 非空 |
| 2 | product-map | `.allforai/product-map/task-inventory.json` 存在且 task 数 > 0 |
| 2 | map-review | `.allforai/product-map-review/review-feedback.json` 存在且 submitted_at 非空 |
| 3 | journey-emotion | `.allforai/experience-map/journey-emotion-map.json` 存在 |
| 4 | experience-map | `.allforai/experience-map/experience-map.json` 存在且 screen 数 > 0 |
| 4 | interaction-gate | `.allforai/experience-map/interaction-gate.json` 存在 |
| 4 | design-pattern | `.allforai/design-pattern/pattern-catalog.json` 存在（或明确跳过） |
| 4 | behavioral-standards | `.allforai/behavioral-standards/behavioral-standards.json` 存在（或明确跳过） |
| 5 | wireframe-review | `.allforai/wireframe-review/review-feedback.json` 存在且 submitted_at 非空 |
| 6 | use-case | `.allforai/use-case/use-case-tree.json` 存在 |
| 6 | feature-gap | `.allforai/feature-gap/gap-tasks.json` 存在 |
| 6 | feature-prune | `.allforai/feature-prune/prune-decisions.json` 存在（可选） |
| 6 | ui-design | `.allforai/ui-design/ui-design-spec.md` 存在 |
| 7 | ui-review | `.allforai/ui-review/review-feedback.json` 存在且 submitted_at 非空 |
| 8 | design-audit | `.allforai/design-audit/audit-report.json` 存在 |

**full 模式**：从 Phase 1（或 Phase 2 如果 skip concept）开始。
**resume 模式**：从第一个未完成阶段开始。

> **并行组**: Phase 6 的 use-case / feature-gap / ui-design 并行执行。feature-prune 可选。
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

## Phase 1 — Step 3：concept-review（人工审核）

> **Review Hub 生命周期**: 审核站点在 Phase 1.5 首次启动，后续 Phase 2.5/5/9 复用同一进程。
> 站点不会在提交反馈后关闭。如果进程意外终止，后续 Phase 会自动重启。

concept 完成后，**必须**启动概念脑图审核，让用户验证 AI 生成的产品概念。

**目的**：用户在此阶段确认产品定位、目标用户、商业模式、产品机制、创新概念。概念错误 = 全部返工。

**执行**：

1. **启动 Review Hub 审核站点**：
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_hub_server.py <BASE> --port 18900
   ```
   - Hub 在此首次启动，后续 Phase 2.5/5/9 复用同一进程
   - 提交反馈后 Hub 不关闭，保持运行
   - 启动后输出：`审核站点已启动: http://localhost:18900/ → 请在概念 tab 中审核`
   - 脑图展示：产品定位 → 目标用户（角色+痛点+增益）→ 商业模式 → 产品机制 → 创新概念 → 流水线偏好
   - 用户点击节点添加评论，标记 Approved 或 Needs Revision
   - 审核完毕点击 "Submit Feedback"

2. **读取反馈并汇总**：
   - 读取 `.allforai/concept-review/review-feedback.json`
   - K = 0 → 概念确认，进入 Phase 2（product-map）
   - K > 0 → 按节点分组展示修改建议，提示用户重跑 /product-concept

3. **迭代循环**（最多 3 轮）

**不可跳过**：concept-review 是必须环节，自动模式下也必须执行。

**resume 模式**：
- `review-feedback.json` 存在且所有 status="approved" → 跳过
- `review-feedback.json` 存在但有 status="revision" → 从迭代步骤继续
- 不存在 → 正常启动

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

## Phase 2 — Step 3：map-review（人工审核）

product-map 完成后，**必须**启动产品地图脑图审核，让用户验证角色、任务和业务流。

**目的**：用户在此阶段确认角色定义、核心/基本任务分类、频次/风险标签、业务流步骤。地图错误 = 所有下游返工。

**执行**：

1. **复用 Review Hub（或重启）**：
   ```
   检查 http://localhost:18900/ 是否可达：
     可达 → 提示用户刷新 /map tab
     不可达 → 重新启动: python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_hub_server.py <BASE> --port 18900
   ```
   - 输出：`审核站点已运行: http://localhost:18900/map → 请在地图 tab 中审核`
   - 脑图展示：角色列表 → 核心任务/基本任务（频次+风险标签）→ 业务流（步骤+角色流转+GAP 标记）
   - 用户点击节点添加评论，标记 Approved 或 Needs Revision
   - 审核完毕点击 "Submit Feedback"

2. **读取反馈并汇总**：
   - 读取 `.allforai/product-map-review/review-feedback.json`
   - K = 0 → 地图确认，进入 Phase 3（journey-emotion）
   - K > 0 → 按类别汇总修复建议：
     - 角色类问题：角色增删改
     - 任务类问题：任务增删改、频次/风险调整
     - 业务流问题：流程断裂、缺失步骤
   - 提示用户修改后重跑 /product-map

3. **迭代循环**（最多 3 轮）

**不可跳过**：map-review 是必须环节，自动模式下也必须执行。

**resume 模式**：
- `review-feedback.json` 存在且所有 status="approved" → 跳过
- `review-feedback.json` 存在但有 status="revision" → 从迭代步骤继续
- 不存在 → 正常启动

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

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/experience-map.md`，按 skill 工作流执行。LLM 主导屏幕设计，可选用辅助脚本加速基础映射。

**Step 1.5: verify loop**（`--phase experience`）

**本阶段闭环重点**：
- 导航闭环：每个屏幕可达且可退，无死胡同
- 状态机闭环：每个状态有出口转换，无状态死锁
- 错误→恢复闭环：每个可能失败的操作有恢复路径回到正常流程
- task→screen 映射闭环：所有 core task 都有对应屏幕

---

## Phase 4 — Step 2：interaction-gate

**执行**：
1. 检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_interaction_gate.py` 是否存在
2. 存在 → 执行预置脚本：`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_interaction_gate.py <BASE> --mode auto`
3. 不存在 → 用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/interaction-gate.md`，按其工作流执行

**检查点**：
- `gate-report.json` 存在

---

## Phase 4 — Step 3：设计模式分析

> 自动执行，无需用户干预

### 执行方式

1. 用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-pattern.md`，按其工作流执行
2. LLM 分析 task-inventory + experience-map，识别重复设计模式

执行条件：
- 自动模式下，experience-map 完成后立即执行
- 若所有 8 类模式均未达阈值，技能/脚本自动输出跳过提示，无需用户操作

### 质量门禁（pattern-catalog.json 存在时）

| 条件 | 标准 |
|------|------|
| pattern-catalog.json | 存在（或明确跳过）|
| tasks_tagged | 所有 _pattern 匹配任务已标注 |
| screens_tagged | 所有 _pattern 匹配界面已标注 |

PASS → 进入 Phase 6 并行组

### resume 模式
- `pattern-catalog.json` 存在 → 跳过 Phase 4.5
- 文件不存在且 experience-map 已完成 → 补跑 Phase 4.5

---

## Phase 4 — Step 4：行为规范分析

> 自动执行，无需用户干预

### 执行方式

1. 用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/behavioral-standards.md`，按其工作流执行
2. LLM 分析 experience-map 中跨界面的行为一致性

执行条件：
- experience-map 完成后执行（不依赖 design-pattern）
- 若所有行为模式一致，脚本自动输出跳过提示

### 质量门禁

| 条件 | 标准 |
|------|------|
| behavioral-standards.json | 存在（或明确跳过）|

PASS → 进入 Phase 6 并行组

### resume 模式
- `behavioral-standards.json` 存在 → 跳过 Phase 4.6
- 文件不存在且 experience-map 已完成 → 补跑 Phase 4.6

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

## Phase 6 生成策略（自动模式）

**LLM 主导生成，脚本辅助校验**：

产品设计阶段的核心生成任务（业务流分组、实体建模、用例推导、UI 设计）需要理解业务领域语境，由 LLM 主导。脚本仅用于：
- 机械性结构检查（feature-gap 的覆盖扫描）
- 后置 schema 校验
- 文件聚合和统计

每个 skill 的 `.md` 文件中标注了哪些步骤可用辅助脚本加速，LLM 应按 skill 指引决定是否调用。

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
- LLM 主导生成，脚本仅用于辅助（schema 校验、结构扫描）
- 不要读写其他并行 Agent 的产出目录
- 每个 skill 的 .md 文件指明了生成方式和输出 schema 约束，严格遵循
~~~

3 个 Agent 调用的具体参数：

| Agent | skill-name | 生成方式 | 产出目录 | 分片文件 |
|-------|-----------|---------|---------|---------|
| Agent 1 | use-case | LLM 主导（脚本可选辅助） | `.allforai/use-case/` | `pipeline-decisions-use-case.json` |
| Agent 2 | feature-gap | 脚本结构检查 + LLM 语义分析 | `.allforai/feature-gap/` | `pipeline-decisions-feature-gap.json` |
| Agent 3 | ui-design | LLM 主导（设计推理） | `.allforai/ui-design/` | `pipeline-decisions-ui-design.json` |

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

> **条件守卫**: gap×prune 矛盾和 safety 检查仅在 `.allforai/feature-prune/prune-decisions.json` 存在时执行。若 feature-prune 未运行（无该文件），这两类冲突不会出现，Step 1 仅处理其余冲突类型。

**1.1 加载概念上下文**

用 Read 加载 `.allforai/product-concept/product-concept.json`，提取：
- `mission` — 产品定位
- `roles[].jobs / pain_relievers / gain_creators` — 角色价值
- `strategy.errc.reduce` 中 `kano=must-have` 的条目 — 不可削减功能
- `strategy.errc.create` — 差异化功能
- `pipeline_preferences.scope_strategy` — 剪枝策略（aggressive/balanced/conservative）

**1.2 逐条解决冲突**

对 findings 中每个 `severity=CONFLICT` 或 `severity=ERROR` 的条目：

| 冲突类型 | 解决规则 |
|---------|---------|
| **gap×prune 矛盾**（task 有 gap 但标 CUT） | 逐个 task 判断：① basic 类 → CORE ② task_name 匹配 mission/pain_relievers/ERRC must-have → CORE ③ risk 高/中 或营收相关 → CORE ④ 被业务流引用 → DEFER ⑤ 以上均否 + scope=aggressive → DEFER（gap 未解决不能 CUT）⑥ scope=balanced/conservative → DEFER |
| **safety 违规**（高频 CUT + 业务流引用） | 无条件 → CORE（安全护栏不可覆盖） |

**1.3 写回修复**

- 读取 `.allforai/feature-prune/prune-decisions.json`
- 修改冲突 task 的 `decision` 字段，追加 `xv_notes` 记录修改原因（含概念依据）
- 写回文件

**1.4 追加 pipeline-decisions 记录**

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
  注: feature-prune 产出不影响自动流程判断
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

## Phase 7 — Step 2：ui-review（人工审核）

ui-design 生成 HTML 预览 / Stitch 视觉稿后，必须经过用户审核确认再进入终审。

**执行**：

1. **复用 Review Hub（或重启）**：
   ```
   检查 http://localhost:18900/ 是否可达：
     可达 → 提示用户刷新 /ui tab
     不可达 → 重新启动: python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_hub_server.py <BASE> --port 18900
   ```
   - 输出：`审核站点已运行: http://localhost:18900/ui → 请在 UI tab 中审核`
   - 用户点击界面任意位置添加 pin 评论
   - 审核完毕点击 "Submit Feedback" → 生成 `review-feedback.json`

2. **读取反馈并迭代**：
   - 读取 `.allforai/ui-review/review-feedback.json`
   - 统计：N 个界面已审核，M 个通过，K 个需修改
   - K = 0 → 全部通过，进入 Phase 8
   - K > 0 → 对 status="revision" 的界面重新生成设计（局部重跑 ui-design）

3. **迭代循环**（最多 3 轮）：
   - 重新生成后，提示用户在 Hub 重新审核修改后的界面
   - 循环直到全部通过或达到 3 轮上限

4. **3 轮后仍有未通过**：
   - 记录剩余问题到 pipeline-decisions.json
   - 向用户报告，继续进入 Phase 8（design-audit 会标记 `ui_review_incomplete`）

**不可跳过**：ui-review 是必须环节，自动模式下也必须执行。

**resume 模式**：
- `review-feedback.json` 存在且所有界面 status="approved" → 跳过
- `review-feedback.json` 存在但有 status="revision" → 从迭代步骤继续
- `review-feedback.json` 不存在 → 正常启动审核

---

## Phase 8：design-audit（终审）

**执行**：
1. 检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_design_audit.py` 是否存在
2. 存在 → 执行预置脚本；不存在 → 加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-audit.md` 按 full 模式执行完整三合一校验

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
| 7 | ui-review | 完成 | Playwright verify: X 轮, 人工审核: X 轮 |
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
5. **只读不改上游** — 后序阶段发现上游问题时只报告，不自动回退修改上游产物
6. **并行 Agent 产出隔离** — Phase 6 的 3 个并行 Agent 各自写入独立目录和分片 pipeline-decisions 文件，不读写其他 Agent 的产出。聚合由编排器在全部完成后统一执行
7. **Phase 转换零停顿** — 严禁在 Phase 之间停下来问"继续？""进入下一阶段？"等确认性问题。检查点 PASS 后直接加载下一阶段 skill 并执行，只输出一行状态摘要（如 `Phase 3 ✓ → Phase 4`）。唯一允许停顿的场景是 ERROR 级安全护栏
