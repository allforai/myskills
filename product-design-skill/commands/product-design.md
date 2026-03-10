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

```
Phase 0: 产物探测
  扫描 .allforai/，标记哪些阶段已完成
  full 模式 → 从头开始
  resume 模式 → 从第一个未完成阶段开始
  ↓
Phase 1: concept（可选）
  加载并执行 skills/product-concept.md
  ↓ checkpoint
Phase 1.4: concept-pre-verify（自动执行）
  JSON 结构校验 → 自动修复 → 再校验（无需 Playwright）
  ↓ checkpoint
Phase 1.5: concept-review（概念脑图审核，必须）
  启动脑图审核服务器 → 用户验证产品定位/角色/商业模式/机制
  反馈汇总修改建议，由用户决定是否重跑 concept
  ↓ 全部通过后进入 product-map
Phase 2: product-map
  加载并执行 skills/product-map.md
  ↓ checkpoint
Phase 2.4: map-pre-verify（自动执行）
  JSON 结构校验 → 自动修复 → 再校验（无需 Playwright）
  ↓ checkpoint
Phase 2.5: map-review（产品地图脑图审核，必须）
  启动脑图审核服务器 → 用户验证角色/任务/业务流
  反馈按类别汇总（角色/任务/业务流），由用户决定是否重跑 product-map
  ↓ 全部通过后进入 journey-emotion
Phase 3: journey-emotion
  加载并执行 skills/journey-emotion.md
  ↓ checkpoint
Phase 4: experience-map
  加载并执行 skills/experience-map.md
  ↓ checkpoint + 轻量校验
Phase 4.5: interaction-gate
  加载并执行 skills/interaction-gate.md
  ↓ checkpoint
Phase 4.5: design-pattern（自动执行）
  加载并执行 skills/design-pattern.md
  ↓ checkpoint
Phase 4.6: behavioral-standards（自动执行）
  加载并执行 skills/behavioral-standards.md
  ↓ checkpoint
Phase 4.7: playwright-verify（自动执行）
  Playwright headless 验证线框渲染 → 自动修复 → 再验证（最多 3 轮）
  ↓ checkpoint
Phase 5: wireframe-review（线框交互审核 — 结构锁定门，必须）
  启动线框审核服务器 → 用户验证 IA/流程/功能完整性
  反馈路由到 product-map / experience-map / concept
  ↓ 全部通过后结构锁定，进入视觉设计
Phase 6-8: 并行执行（3 个 Agent 同时启动）
  ┌─ Agent: use-case      → .allforai/use-case/
  ├─ Agent: feature-gap   → .allforai/feature-gap/
  └─ Agent: ui-design     → .allforai/ui-design/
  全部完成 ↓ 聚合 checkpoint + pipeline-decisions 合并 + 轻量校验
Phase 8.5: ui-pre-verify（自动执行）
  Playwright headless 验证 UI 渲染 → 自动修复 → 再验证（最多 3 轮）
  ↓ checkpoint
Phase 9: ui-review（视觉审核迭代，必须）
  启动审核服务器 → 用户浏览标注 → 提交反馈 → 局部重跑 ui-design
  ↓ 循环直到用户确认全部通过
Phase 10: design-audit full（终审）
  加载并执行 skills/design-audit.md full
  ↓ 输出最终审计报告 + 全流程摘要
```

---

## Phase 0：产物探测

扫描以下目录，判断每个阶段的完成状态：

| 阶段 | 完成标志 |
|------|----------|
| concept | `.allforai/product-concept/` 目录存在 |
| concept-review | `.allforai/concept-review/review-feedback.json` 存在且 submitted_at 非空 |
| product-map | `.allforai/product-map/task-inventory.json` 存在且 task 数 > 0 |
| map-review | `.allforai/product-map-review/review-feedback.json` 存在且 submitted_at 非空 |
| journey-emotion | `.allforai/experience-map/journey-emotion-map.json` 存在 |
| experience-map | `.allforai/experience-map/experience-map.json` 存在且 screen 数 > 0 |
| interaction-gate | `.allforai/experience-map/interaction-gate.json` 存在 |
| data-model | `.allforai/product-map/entity-model.json` 存在 |
| view-objects | `.allforai/product-map/view-objects.json` 存在 |
| design-pattern | `.allforai/design-pattern/pattern-catalog.json` 存在 |
| behavioral-standards | `.allforai/behavioral-standards/behavioral-standards.json` 存在 |
| playwright-verify | `.allforai/wireframe-verify/verification-report.json` 存在且 `overall` = "PASS" |
| use-case | `.allforai/use-case/use-case-tree.json` 存在 |
| feature-gap | `.allforai/feature-gap/gap-tasks.json` 存在 |
| feature-prune | `.allforai/feature-prune/prune-decisions.json` 存在（可选，手动执行） |
| wireframe-review | `.allforai/wireframe-review/review-feedback.json` 存在且 submitted_at 非空 |
| ui-design | `.allforai/ui-design/ui-design-spec.md` 存在 |
| design-audit | `.allforai/design-audit/audit-report.json` 存在 |

**full 模式**：从 Phase 1（或 Phase 2 如果 skip concept）开始，逐阶段执行。
**resume 模式**：从第一个未完成阶段开始。

> **design-pattern**: 自动执行阶段，`pattern-catalog.json` 存在或 Phase 4.5 明确跳过，视为已完成。

> **behavioral-standards**: 自动执行阶段，`behavioral-standards.json` 存在或 Phase 4.6 明确跳过，视为已完成。

> **并行组**: use-case / feature-gap / ui-design 为并行执行组。feature-prune 为可选手动阶段。
> resume 模式下，仅当该组全部完成才视为"Phase 6-8 已完成"，否则补跑缺失的 skill。

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

自动模式下，Phase 2-7 的每个检查点行为变更：

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

## Phase 1.4：concept-pre-verify（概念自动校验）

> 自动执行，无需 Playwright。直接校验 JSON 结构完整性。

**执行**：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_review.py <BASE> --phase concept
```

脚本自动检查：
- mission 非空
- 每个角色有 jobs / pain_relievers / gain_creators
- business_model.metrics ≥3 个且字段完整
- mechanisms ≥5 个
- pipeline_preferences 已设置 ui_style 和 scope_strategy

**结果处理**：
- 0 ERROR → PASS，进入 Phase 1.5
- 有 ERROR → Claude Code 自动修复 product-concept.json → 重跑脚本（最多 3 轮）
- WARNING → 记日志继续

**输出**：`.allforai/concept-verify/verification-report.json`

---

## Phase 1.5：concept-review（概念脑图审核）

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

## Phase 1-2 pipeline-decisions 写入

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

## Phase 2.4：map-pre-verify（地图自动校验）

> 自动执行，无需 Playwright。直接校验 JSON 结构完整性。

**执行**：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_review.py <BASE> --phase map
```

脚本自动检查：
- 每个角色至少有 1 个 core task
- 频次标签（高/中/低）和风险标签是否完整
- 业务流步骤 ≥2（不能太短）
- 所有 core task 是否被至少一个业务流覆盖

**结果处理**：
- 0 ERROR → PASS，进入 Phase 2.5
- 有 ERROR → Claude Code 自动修复 → 重跑（最多 3 轮）
- WARNING → 记日志继续

**输出**：`.allforai/map-verify/verification-report.json`

---

## Phase 2.5：map-review（产品地图脑图审核）

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

**执行**：
1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/journey-emotion.md`
2. 按 journey-emotion 技能的完整工作流执行

**检查点**：
- `experience-map/journey-emotion-map.json` 存在

---

## Phase 4：experience-map

**预置脚本优先**：

```
检查 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_experience_map.py 是否存在：
  存在 → python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_experience_map.py <BASE> --mode auto --shard experience-map
  不存在 → 用 Read 工具加载 skills/experience-map.md，按 skill 工作流执行
```

**执行**（脚本不存在时的回退路径）：
1. 用 Read 工具加载 `${CLAUDE_PLUGIN_ROOT}/skills/experience-map.md`
2. 按 experience-map 技能的完整工作流执行

**检查点**：
- `experience-map.json` 存在
- screen 数量 > 0

**轻量校验**：
- 每个 screen 的 `tasks` 中的 task_id 在 `task-inventory.json` 中存在
- 发现问题 → 列出不一致项，询问用户是否继续

**自动模式检查点**：screen 数 = 0 → ERROR（停）；tasks 引用断裂 → ERROR（停）；其余不一致 → WARNING 记日志继续。

---

## Phase 4.5：interaction-gate

**执行**：
1. 检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_interaction_gate.py` 是否存在
2. 存在 → 执行预置脚本：`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_interaction_gate.py <BASE> --mode auto`
3. 不存在 → 用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/interaction-gate.md`，按其工作流执行

**检查点**：
- `gate-report.json` 存在

---

## Phase 4.5：设计模式分析

> 自动执行，无需用户干预

### 执行方式

1. 检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_design_pattern.py` 是否存在
2. 存在 → 执行预置脚本：`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_design_pattern.py <BASE> --mode auto`
3. 不存在 → 用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/design-pattern.md`，按其工作流执行

执行条件：
- 自动模式下，experience-map 完成后立即执行
- 若所有 8 类模式均未达阈值，技能/脚本自动输出跳过提示，无需用户操作

### 质量门禁（pattern-catalog.json 存在时）

| 条件 | 标准 |
|------|------|
| pattern-catalog.json | 存在（或明确跳过）|
| tasks_tagged | 所有 _pattern 匹配任务已标注 |
| screens_tagged | 所有 _pattern 匹配界面已标注 |

PASS → 进入 Phase 5-7 并行组

### resume 模式
- `pattern-catalog.json` 存在 → 跳过 Phase 4.5
- 文件不存在且 experience-map 已完成 → 补跑 Phase 4.5

---

## Phase 4.6：行为规范分析

> 自动执行，无需用户干预

### 执行方式

1. 检查 `${CLAUDE_PLUGIN_ROOT}/scripts/gen_behavioral_standards.py` 是否存在
2. 存在 → 执行预置脚本：`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_behavioral_standards.py <BASE> --mode auto`
3. 不存在 → 用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/behavioral-standards.md`，按其工作流执行

执行条件：
- experience-map 完成后执行（不依赖 design-pattern）
- 若所有行为模式一致，脚本自动输出跳过提示

### 质量门禁

| 条件 | 标准 |
|------|------|
| behavioral-standards.json | 存在（或明确跳过）|

PASS → 进入 Phase 5-7 并行组

### resume 模式
- `behavioral-standards.json` 存在 → 跳过 Phase 4.6
- 文件不存在且 experience-map 已完成 → 补跑 Phase 4.6

---

## Phase 4.7：playwright-verify（线框自动验证）

> 自动执行，无需用户干预。Playwright headless 验证 → 自动修复 → 再验证循环。

### 前置条件

- experience-map 已完成（screen 数 > 0）
- Playwright MCP 可用（`mcp__playwright__browser_navigate` 在激活工具或 deferred tools 中）
- Playwright 不可用 → 跳过本阶段，记录 `playwright_skipped`，继续进入 Phase 5

### 执行方式

**Step 1: 准备**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_wireframes.py <BASE>
```

脚本自动完成：
- 从 experience-map.json 收集所有屏幕元数据
- 启动 Review Hub（headless，--no-open）
- 输出 `.allforai/wireframe-verify/screens-to-verify.json`

**Step 2: Playwright 逐屏验证（Claude Code 执行）**

读取 `screens-to-verify.json`，对每个屏幕执行：

1. 导航到 Review Hub wireframe 页面
2. 点击屏幕 → 捕获 accessibility snapshot
3. 对比 snapshot 与屏幕元数据，判断：

| 检查项 | 判断方式 | 严重级 |
|--------|---------|--------|
| 交互类型 vs 布局匹配 | snapshot 中的 layout slots 是否与 expected_layout 一致 | ERROR |
| 数据字段渲染 | snapshot 中是否包含 data_fields 中的字段名 | ERROR |
| 操作按钮存在 | snapshot 中是否包含 actions 中的按钮 | WARNING |
| 文本语言一致性 | 中文产品不应出现英文 UI 文本（Dashboard/Settings 等） | WARNING |
| 屏幕流转 | Flow 面板中 ← → 指向正确的上下游屏幕 | WARNING |
| 状态定义 | State 面板中列出了状态机定义 | WARNING |

4. 输出每个屏幕的验证结果：
```json
{
  "screen_id": "S009",
  "name": "学习核心单词",
  "severity": "ERROR",
  "issue": "CT3 渲染为 Profile card (avatar-header)，但业务是单词卡片学习，应为 CT4",
  "fix_suggestion": "interaction_type: CT3 → CT4"
}
```

5. 写入 `.allforai/wireframe-verify/verification-input.json`

**Step 3: 自动修复（Claude Code 执行）**

如果有 ERROR 级问题：
1. 读取 verification-input.json 中的 ERROR 条目
2. 根据 fix_suggestion 直接修改 experience-map.json
3. 重启 Review Hub
4. 回到 Step 2 重新验证修复的屏幕

**Step 4: 生成报告**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_wireframes.py <BASE> --report
```

### 循环控制

- 最多 3 轮（Step 2-3 循环）
- 每轮只验证上一轮 ERROR 的屏幕（增量验证，不重复验证已通过的）
- 3 轮后仍有 ERROR → WARNING 降级，记日志继续

### 质量门禁

| 条件 | 标准 |
|------|------|
| verification-report.json | 存在 |
| overall | PASS（无 ERROR）或 3 轮后降级 |

PASS → 进入 Phase 5（wireframe-review）

### resume 模式

- `verification-report.json` 存在且 `overall` = "PASS" → 跳过
- 报告存在但 `overall` = "FAIL" → 重新执行 Step 2-4
- 不存在 → 正常执行

---

## Phase 5：wireframe-review（线框交互审核）

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
   - K = 0 → 全部通过，结构锁定，进入 Phase 5.5（Stitch 决策）
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

## Phase 5.5：Stitch 可用性决策点

wireframe-review 通过后、进入 Phase 6-8 并行执行前，检查 Stitch 可用性：

```
检查 mcp__plugin_product-design_stitch__create_project 是否可用:
  可用 → 继续（Stitch 将在 Phase 8 ui-design 的 Step 5.5 中使用）
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

## Phase 6-8 预置脚本优先（自动模式）

自动模式下，Phase 6-8 优先使用预置脚本（位于 `${CLAUDE_PLUGIN_ROOT}/scripts/`）：

```
检查 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_xxx.py 是否存在：
  存在 → python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_xxx.py <BASE> --mode auto
  不存在 → 回退到 LLM 临场生成脚本（向后兼容）
```

预置脚本的优势：
- **零语法错误**：不存在 `gaps[:30)` 等括号混用
- **字段名统一**：experience-map 用 `tasks`，flow 用 `nodes`（不再误读 `task_refs` / `steps`）
- **pipeline-decisions 去重**：按 phase 名替换，重跑不产生重复条目

---

## Phase 6-8：并行执行

> Phase 6 (use-case)、Phase 7 (feature-gap)、Phase 8 (ui-design)
> 之间无数据依赖（均仅依赖 product-map + experience-map），使用 Agent tool 并行执行。

### 执行方式

Phase 5/5.5 checkpoint 通过后，用**单条消息发出 3 个 Agent tool 调用**并行执行。
Agent tool 的屏障同步机制保证 3 个 Agent 全部完成后才继续到聚合 checkpoint。

每个 Agent 的 prompt 模板：

~~~
你是产品设计流水线的并行执行器。

任务: 执行 {skill-name} 技能的完整工作流。

执行步骤:
1. 用 Read 工具加载 ${CLAUDE_PLUGIN_ROOT}/skills/{skill-name}.md
2. 按该技能的完整工作流执行（不跳步骤、不简化）
3. 产出写入 .allforai/{skill-name}/ 目录
4. pipeline-decisions 写入分片文件 .allforai/pipeline-decisions-{skill-name}.json（不写 pipeline-decisions.json 主文件）

上下文:
- 产品地图: .allforai/product-map/
- 体验地图: .allforai/experience-map/
- 产品概念: .allforai/product-concept/（可选）
{自动模式标记: __orchestrator_auto: true（若自动模式激活）}

重要:
- pipeline-decisions 必须写入分片文件 .allforai/pipeline-decisions-{skill-name}.json
- 禁止直接写入 pipeline-decisions.json 主文件，该文件由编排器聚合写入
- 预置脚本调用时传 --shard {skill-name}（如 --shard feature-gap），脚本自动写入分片文件
- 不要读写其他并行 Agent 的产出目录
- 预置脚本优先: 检查 ${CLAUDE_PLUGIN_ROOT}/scripts/gen_{script}.py 是否存在，存在则优先使用
~~~

3 个 Agent 调用的具体参数：

| Agent | skill-name | 预置脚本 | --shard 值 | 产出目录 | 分片文件 |
|-------|-----------|---------|-----------|---------|---------|
| Agent 1 | use-case | `gen_use_cases.py` | `use-case` | `.allforai/use-case/` | `pipeline-decisions-use-case.json` |
| Agent 2 | feature-gap | `gen_feature_gap.py` | `feature-gap` | `.allforai/feature-gap/` | `pipeline-decisions-feature-gap.json` |
| Agent 3 | ui-design | `gen_ui_design.py` | `ui-design` | `.allforai/ui-design/` | `pipeline-decisions-ui-design.json` |

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

- exit 0 → 所有检查通过，进入 Phase 9
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
    全部成功 → 执行聚合 checkpoint → 进入 Phase 8
    部分失败 →
      成功的 Agent: 正常收集产出
      失败的 Agent: 记录错误信息
      向用户报告:
        "Phase 6-8 并行执行结果:
         ✓ use-case: 完成
         ✓ feature-gap: 完成
         ✓ ui-design: 完成"
      询问用户:
        1. 重试失败的 skill（仅重跑失败的 Agent）
        2. 跳过继续到 Phase 9（ui-review → design-audit）
        3. 中止流程
    全部失败 →
      向用户报告所有错误
      询问: 全部重试 / 中止
~~~

### resume 模式下的并行处理

~~~
resume 模式检测 Phase 6-8 完成状态:
  3 个产出全部存在（use-case, feature-gap, ui-design） → 跳过 Phase 6-8，进入 Phase 9
  部分存在 → 仅启动缺失产出对应的 Agent（已有产出不重跑）
  全部不存在 → 正常启动 3 个并行 Agent
  注: feature-prune 产出不影响自动流程判断
~~~

---

## Phase 8.5：ui-pre-verify（UI 自动验证）

> 自动执行，需要 Playwright。验证 UI 渲染质量。

**前置条件**：Playwright MCP 可用。不可用 → 跳过，记录 `playwright_skipped`。

**执行**：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_review.py <BASE> --phase ui
```

脚本准备 items 列表 + 启动 Review Hub。Claude Code 使用 Playwright：

1. 导航到 /ui，逐屏 snapshot
2. 检查：HTML 渲染正常、样式一致、中文标签、组件复用
3. 输出 `ui-verify/verification-input.json`
4. 有 ERROR → 自动修复 → 重新验证（最多 3 轮）

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_review.py <BASE> --phase ui --report
```

**输出**：`.allforai/ui-verify/verification-report.json`

---

## Phase 9：ui-review（视觉审核迭代）

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
   - K = 0 → 全部通过，进入 Phase 10
   - K > 0 → 对 status="revision" 的界面重新生成设计（局部重跑 ui-design）

3. **迭代循环**（最多 3 轮）：
   - 重新生成后，提示用户在 Hub 重新审核修改后的界面
   - 循环直到全部通过或达到 3 轮上限

4. **3 轮后仍有未通过**：
   - 记录剩余问题到 pipeline-decisions.json
   - 向用户报告，继续进入 Phase 10（design-audit 会标记 `ui_review_incomplete`）

**不可跳过**：ui-review 是必须环节，自动模式下也必须执行。

**resume 模式**：
- `review-feedback.json` 存在且所有界面 status="approved" → 跳过 Phase 9
- `review-feedback.json` 存在但有 status="revision" → 从迭代步骤继续
- `review-feedback.json` 不存在 → 正常启动审核

---

## Phase 10：design-audit full（终审）

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

| 阶段 | 状态 | 检查点 | 备注 |
|------|------|--------|------|
| concept | 完成/跳过 | — | {备注} |
| concept-review | 完成 | 审核轮次: X | 通过: X / 修改: X |
| product-map | 完成 | task 数: X | — |
| map-review | 完成 | 审核轮次: X | 通过: X / 修改: X |
| journey-emotion | 完成 | — | — |
| experience-map | 完成 | screen 数: X | 校验: X 项通过 |
| interaction-gate | 完成 | — | — |
| wireframe-review | 完成/跳过 | 审核轮次: X | 结构锁定 / 修改: X |
| **Phase 6-8 并行** | | | |
| ├ use-case | 完成/失败 | use-case 数: X | 校验: X task 有用例 |
| ├ feature-gap | 完成/失败 | gap 数: X | — |
| ├ feature-prune | 完成/未执行 | CORE/DEFER/CUT: X/X/X | 可选，手动执行 |
| └ ui-design | 完成/失败 | — | 校验: CORE 覆盖 XX% |
| 聚合校验 | PASS/FAIL | gap×prune 矛盾: X | UI CORE 覆盖: XX% |
| ui-review | 完成/跳过 | 审核轮次: X | 通过: X / 修改: X |
| design-audit | 完成 | 见终审报告 | — |

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
4. **轻量校验不替代终审** — 阶段间的轻量校验仅做快速检查，完整校验由 Phase 9 design-audit 负责
5. **只读不改上游** — 后序阶段发现上游问题时只报告，不自动回退修改上游产物
6. **并行 Agent 产出隔离** — Phase 6-8 的 3 个并行 Agent 各自写入独立目录和分片 pipeline-decisions 文件，不读写其他 Agent 的产出。聚合由编排器在全部完成后统一执行
7. **Phase 转换零停顿** — 严禁在 Phase 之间停下来问"继续？""进入下一阶段？"等确认性问题。检查点 PASS 后直接加载下一阶段 skill 并执行，只输出一行状态摘要（如 `Phase 3 ✓ → Phase 4`）。唯一允许停顿的场景是 ERROR 级安全护栏
