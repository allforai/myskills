---
description: "产品设计全流程编排：concept → map → journey → experience → feature-gap → audit。模式: full / resume"
argument-hint: "[mode: full|resume] [skip: concept]"
---

# Product Design Full — 产品设计全流程编排

（根据用户请求的模式/参数执行）

## 插件根目录

所有文档路径基于技能根目录（相对路径）

## 设计思想入口（建议先读）

执行全流程前，建议先阅读：

- `./docs/product-design-principles.md`

该文档汇总前段/中段/尾段的经典理论支持（如第一性原理、JTBD、Kano、Nielsen、ISO 9241-11、WCAG）及参考文献。

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 从头执行全流程（已有产物作为参考但会重新生成）
- **`full skip: concept`** → 从头执行，但跳过 Phase 1 概念发现
- **`resume`** → 检测已有产物，从第一个未完成阶段开始

## 编排流程

每个生成阶段遵循统一模式：**LLM 生成 → 4D/6V/闭环 verify loop（以上一级产物为基准验证）→ 自动修正 → 继续下一阶段**。

新增全局原则：如果 `product-map` 判定当前产品为 `consumer` 或 `mixed`，则后续 Phase 2-6 的 verify loop 必须按“用户端成熟度”收紧，而不能只验证结构存在和功能覆盖。

**无强制人工审核门**。所有阶段仅靠 verify loop 自动验证。用户随时可通过 `/review` 命令启动 Review Hub，审核任意阶段产物（概念/地图/数据模型/线框/UI 等），收集反馈并迭代修改。

> **设计决策**：线框审核在 AI pipeline 中价值有限——低保真渲染无法有效审核 UX，结构正确性已被 Playwright verify loop 覆盖，代码自动生成后直接看运行产品反馈质量更高。因此降级为可选。

```
Phase 0: 产物探测
  ↓
Phase 1: concept — LLM 生成 → verify loop（以用户需求为基准）
  ↓
Phase 2: product-map — LLM 生成 → verify loop（以 concept 为基准）
  ↓
Phase 3: journey-emotion — LLM 生成 → verify loop（以 product-map 为基准）
  ↓
Phase 4: experience-map — LLM 生成 → verify loop（以 journey-emotion + product-map 为基准）→ interaction-gate
  ↓
Phase 5: feature-gap — LLM 生成 → verify loop（以 experience-map + product-map 为基准）
  ↓
Phase 6: design-audit（终审）
```

### 统一 verify loop 执行模板

所有阶段的 verify loop 执行同一模式。**核心原则：以上一级产物为基准验证当前产物**。

```
loop (max 3 rounds):
  1. python3 ../../shared/scripts/product-design/verify_review.py <BASE> --phase <PHASE> [--xv]
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
| 5 feature-gap | gap-tasks.json | task-inventory + experience-map + business-flows |
各阶段对应的 `--phase` 值：concept / map / journey / experience / feature-gap

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
| 5 | feature-gap | `.allforai/feature-gap/gap-tasks.json` 存在 |
| 6 | design-audit | `.allforai/design-audit/audit-report.json` 存在 |

**full 模式**：从 Phase 1（或 Phase 2 如果 skip concept）开始。
**resume 模式**：从第一个未完成阶段开始。

> Phase 5 feature-gap 单独执行（不再并行）。
> resume 模式下，feature-gap 已完成则跳过。

向用户展示探测结果。

### 用户端体验重心探测（新增）

在 Phase 2（product-map）完成后，后续阶段默认读取 `product-map.json` 中的 `experience_priority`：

- `consumer` → 用户端/移动端作为主价值面，后续设计和规格按成熟产品标准推进
- `admin` → 维持后台/专业端优先标准
- `mixed` → 两端都做，但用户端仍必须经过成熟度检查

这不是单独新增一个 Phase，而是让 Phase 3-6 自动切换评价标准。

### 产品规模前置检测

> 在 Phase 1 开始前，评估产品规模。超大型产品应拆成多个独立产品分批设计。

**检测方式**：从用户输入（PRD/口述/已有代码）中快速估算：
- 角色数
- 预估模块数（粗略）
- 是否包含多个独立业务域（如 ERP + 供应链 + 金融）

**规模分级与处理**：

| 规模 | 角色数 | 预估模块数 | 处理方式 |
|------|--------|-----------|---------|
| 标准 | ≤ 4 | ≤ 15 | 正常执行全流程 |
| 大型 | 5-8 | 16-30 | 提醒用户"项目较大"，正常执行（skill 内部自动分批） |
| **超大** | **> 8** | **> 30** | **建议拆分**：用 向用户询问用户是否拆成 2-3 个独立产品分批设计 |

**超大型产品拆分建议**：
```
检测到产品规模较大（{N} 个角色，预估 {M} 个模块）。
建议拆分为独立产品分批设计和开发：

方案 A: 按业务域拆分
  产品 1: {核心业务域} ({modules})
  产品 2: {支撑业务域} ({modules})
  产品 3: {管理/运营域} ({modules})

方案 B: 按交付优先级拆分
  Phase 1: {MVP 核心} ({modules})
  Phase 2: {扩展功能} ({modules})
  Phase 3: {运营工具} ({modules})

每个产品独立走 product-design → dev-forge 全流程。
先完成最核心的产品，再依次扩展。
```

用户选择拆分 → 记录拆分决策到 `.allforai/product-concept/scope-decisions.json`，然后只对第一个子产品执行 Phase 1。
用户选择不拆 → 记录决策，正常执行（skill 内部自动分批处理大规模）。

### 外部能力快检

> 统一协议见 `./docs/skill-commons.md`「外部能力探测协议」。

产物探测后，检测本流水线涉及的外部能力并输出状态：

| 能力 | 探测方式 | 重要性 |
|------|---------|--------|
| OpenRouter (MCP) | `mcp__openrouter__ask_model` 可用性 | 可选 |
| OpenRouter (Script) | `OPENROUTER_API_KEY` 环境变量 | 可选 |
| Stitch UI | `mcp__stitch__create_project` 可用性 | 可选 |
| Playwright | `mcp__playwright__browser_navigate` 或 `mcp__playwright__browser_navigate` 可用性 | 可选 |
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
1. 用 Read 工具加载 `./skills/product-concept.md`
2. 按 product-concept 技能的完整工作流执行

**检查点**：concept 产出目录存在。

---

## 自动模式检测

Phase 1（product-concept）执行完毕后，检测自动模式条件：

1. 读取 `.allforai/product-concept/product-concept.json`
2. 检查 `pipeline_preferences` 字段是否存在
3. **存在** → 启用自动模式：
   - 后续 Phase 2-6 每个技能调用时携带上下文标记 `__orchestrator_auto: true`
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
1. 用 Read 工具加载 `./skills/product-map.md`
2. 按 product-map 技能的完整工作流执行
3. 完成后追加 pipeline-decisions 记录（自动模式下）

**检查点**：
- `task-inventory.json` 存在
- task 数量 > 0
- `task-inventory-basic.json` 和 `task-inventory-core.json` 存在
- 每个 task 有 `category` 字段（basic 或 core）
- `product-map.json` 存在且包含 `experience_priority` 字段（若产品有用户端/移动端主界面）

检查点失败 → 向用户报告，询问是否继续（product-map 是后续所有阶段的基础，强烈建议修复）。

**自动模式检查点**：task 数 = 0 → ERROR（停）；category 字段缺失 → WARNING（记日志继续）；`experience_priority` 缺失且产品含用户端 → ERROR（停，此字段影响全部下游 14 个技能的 consumer 增强分支）；task 数 > 0 且分类完整 → PASS。

---

## Phase 2 — Step 2：map-verify

按统一 verify loop 执行（`--phase map`）。

**本阶段闭环重点**：
- 四类闭环审计：每个功能任务的配置/监控/异常/生命周期闭环是否完整
- mechanism→task 映射：concept 里的每个产品机制是否都有对应任务
- task→flow 映射：高频任务是否至少出现在一条业务流中

**用户端成熟度审计（当 `experience_priority.mode = consumer` 或 `mixed` 时追加）**：

自审清单（LLM 逐条回答 是/否）：
- 用户端任务是否只有"浏览/提交/查看"，没有首次引导、持续关系、进度追踪、智能推荐、激励机制中的任何一项？
- 核心对象（如"训练""订单""课程"）是否只有 CRUD，没有生命周期流转（草稿→进行中→完成→复盘→归档）？
- 是否缺少通知/提醒/历史/回访触发点？
- 业务流是否只有 happy path，没有"中断恢复""失败重试""等待反馈"等体验节点？

> 注：如果 product-map Step 2 已执行"多模型 Consumer 体验补全"，此处自审通常能通过（因为第二模型已在生成阶段补厚了任务）。自审仍为必做，作为兜底确认。

发现以上问题 → 判定为 verify loop 失败，LLM 在 task-inventory 和 business-flows 中补厚后重验。

---

verify loop 通过后直接进入 Phase 3，不弹出人工审核。

---

## Phase 3：journey-emotion

**Step 1: 生成**
1. 用 Read 工具加载 `./skills/journey-emotion.md`
2. 按 journey-emotion 技能的完整工作流执行

**Step 2: verify loop**（`--phase journey`）

**本阶段闭环重点**：
- 低谷→恢复闭环：每个情感低谷有对应的设计干预和恢复节点吗？
- 旅程始→终闭环：每条旅程线有明确起终点吗？终点情感正面吗？（Peak-End Rule）
- 失败→继续闭环：高 risk 节点失败后能否回到正常流程？

---

## Phase 4：experience-map

**Step 1: 生成**

用 Read 加载 `./skills/experience-map.md`，按 skill 工作流执行。LLM 主导屏幕设计。

**Step 1.5: verify loop**（`--phase experience`）

**本阶段闭环重点**：
- 导航闭环：每个屏幕可达且可退，无死胡同
- 状态机闭环：每个状态有出口转换，无状态死锁
- 错误→恢复闭环：每个可能失败的操作有恢复路径回到正常流程
- task→screen 映射闭环：所有 core task 都有对应屏幕

---

## Phase 4 — Step 2：interaction-gate

**执行**：
1. 用 Read 加载 `./skills/interaction-gate.md`，按其工作流执行
2. LLM 分析 experience-map + task-inventory，识别交互风险点并生成门禁报告

**检查点**：
- `gate-report.json` 存在

---

## Phase 5：feature-gap（缺口分析）

**执行**：
1. 用 Read 工具加载 `./skills/feature-gap.md`
2. 按 feature-gap 技能的完整工作流执行
3. 产出写入 `.allforai/feature-gap/` 目录

**检查点**：`gap-tasks.json` 存在。

**verify loop**（`--phase feature-gap`）：

**本阶段闭环重点**：
- 状态机可逆性：每个拒绝/失败状态有重试路径吗？
- 异常覆盖：高频任务的异常场景有处理吗？
- task↔screen 覆盖：所有 core task 在 experience-map 中有屏幕？

---

## Phase 6：design-audit（终审）

> **已移除的阶段**：wireframe 生成/验证、use-case（task-inventory 已含用例）、ui-design（开发阶段按需生成）。
> 精简原则：只保留发现真实产品缺口的阶段，去掉格式转换和低价值验证。

**执行**：
1. 用 Read 加载 `./skills/design-audit.md`

**Phase A（脚本，串行）**：确定性检查

```bash
python3 ../../shared/scripts/product-design/gen_design_audit.py <BASE> [--mode auto]
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
1. 用 Read 加载 ./skills/design-audit.md
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

2 个 Agent 全部返回后，编排器执行：
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
| 1 | concept | 完成/跳过 | verify loop: X 轮 |
| 2 | product-map | 完成 | task 数: X, verify loop: X 轮 |
| 3 | journey-emotion | 完成 | — |
| 4 | experience-map | 完成 | screen 数: X |
| 5 | feature-gap | 完成 | gap 数: X |
| 6 | design-audit | 完成 | 见终审报告 |

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
4. **verify loop 不替代终审** — 阶段内的 verify loop 保证内容正确性，完整校验由 Phase 6 design-audit 负责
5. **产品设计内只读不改上游** — 产品设计流水线内，后序阶段发现上游问题时只报告，不自动回退修改上游产物。**开发阶段例外**：开发阶段发现上游漏掉的支撑功能时，按逆向补漏协议（skill-commons §五）回补上游（补漏不开新战线）
6. **Phase 转换零停顿** — 严禁在 Phase 之间停下来问"继续？""进入下一阶段？""要先审阅吗？"等确认性问题。检查点 PASS 后直接加载下一阶段 skill 并执行，只输出一行状态摘要（如 `Phase 3 ✓ → Phase 4`）。唯一允许停顿的场景是 ERROR 级安全护栏。产物审阅是可选的（用户随时可通过 `/review` 主动发起），编排器绝不主动询问是否审阅
