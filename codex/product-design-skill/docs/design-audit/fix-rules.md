# Design Audit — Fix Rules & Defensive Patterns

> Extracted from `skills/design-audit.md`. All fix/remediation rules, defensive patterns, and iron laws.

---

## 增强协议（网络搜索 + 4D+6V + XV）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**搜索关键词**：`"usability heuristic evaluation" + "case study" + 2025`、`"design audit checklist" + 产品类型 + "real project"`、`"WCAG 2.2 compliance" + "UI audit"`

**4D+6V 重点**：`fidelity_score` 作为量化指标；补充 Traceability 完整率（建议 `>= 95%`）和 Viewpoint 覆盖率（建议 `>= 90%`）两项门禁；CONFLICT/ORPHAN 问题附带 `source_refs` 与 `decision_rationale`。

**XV 交叉验证**（Step 3 横向一致性检测后）：

| 验证点 | task_type | 发送内容 | 写入字段 |
|--------|-----------|----------|----------|
| 跨层矛盾验证 | `cross_layer_validation`→gpt | 审计摘要：CONFLICT/ORPHAN/GAP 问题列表 + 典型矛盾案例 | cross_model_review.additional_contradictions |
| 覆盖盲区分析 | `coverage_analysis`→deepseek | 审计摘要：覆盖率统计 + 未覆盖任务列表 + 可用层信息 | cross_model_review.coverage_blindspots |

自动写入：遗漏的跨层矛盾（审计自身未检测到的层间不一致、隐性依赖断裂）、覆盖盲区（系统性遗漏模式、特定角色或模块的覆盖偏低区域）。

---

## 尾段理论支持（可选增强）

为让设计审计从"规则检查"升级为"体验质量治理"，可在现有三维校验上叠加：

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|----------|----------|
| Nielsen 可用性启发式 | Step 3 | 将 cross-check 结果映射为可用性问题类型（可见性、一致性、错误预防等） |
| ISO 9241-11（有效性/效率/满意度） | Step 2/4 | 将覆盖率与冲突结果翻译为可用性质量指标，便于发布评审 |
| WCAG 可访问性原则 | Step 3/4 | 对 UI 相关冲突补充可访问性风险标注（对比度、反馈可感知、可操作性） |
| 一致性与认知负荷原则 | Step 1/3 | 对 ORPHAN/BROKEN_REF/高频埋深给出认知成本解释，支撑优先级排序 |

> 说明：此增强不改变现有输出结构，仅增加审计结论的理论可解释性。

---

## 全自动模式

**激活条件**（同时满足）：
1. `.allforai/product-concept/product-concept.json` 存在且含 `pipeline_preferences` 字段
2. 上下文含 `__orchestrator_auto: true`（由 `/product-design full` 编排器传入）

**未同时满足** → 保持标准交互模式（当前行为不变）。

**行为变化**：

| 阶段 | 标准模式 | 全自动模式 |
|------|----------|-----------|
| **Phase A 脚本执行** | 脚本执行后，向用户确认 trace/coverage/cross 结果 | 脚本执行后自动确认，所有问题记入 `pipeline-decisions.json`（`decision: "auto_confirmed"`） |
| **Phase B Agent 1: 模式+创新** | 向用户确认 | 自动执行（前置条件不满足 → 跳过），问题记入分片 |
| **Phase B Agent 2: 行为** | 向用户确认 | 自动执行（前置条件不满足 → 跳过），问题记入分片 |
| **Phase B Agent 3: 交互类型** | 向用户确认 | 自动执行（前置条件不满足 → 跳过），问题记入分片 |
| **Phase C 合并报告** | 向用户确认 | 自动确认 |

**安全护栏**（自动模式下仍然停下来问用户）：
- ERROR 级验证失败（product-map.json 损坏、必须层缺失）

---

## 生成方式

LLM 对全流程产物执行三维审计（逆向追溯、覆盖洪泛、横向一致性）。终审需要跨阶段语义关联分析（如"concept 中的核心价值主张是否在 UI 中有体现"），脚本只能做字段引用检查。

可选辅助脚本：`../../shared/scripts/product-design/gen_design_audit.py`（用于机械性字段引用检查和覆盖率统计，LLM 必须在其上补充语义一致性分析和改进建议）。

---

## 防御性规范

> 通用模式定义见 `docs/defensive-patterns.md`，以下为本技能的具体应用。

### 加载校验
- **所有上游产物（6 层）**：加载每个层的 JSON 文件时用 `python -m json.tool` 验证合法性。单个文件解析失败 → 该层标记为「不可用（JSON 损坏）」，从 `available_layers[]` 中移除，跳过相关校验项。不因单个文件损坏中断整体审计。
- **`product-map.json`**（必须层）：解析失败 → 告知用户「product-map.json 损坏，请重新执行 product-map」，**终止审计**。

### 零结果处理
- **全部检查通过 0 问题**：明确告知「设计审计通过 — 所有校验项均 PASS（逆向追溯 {N} 项 / 覆盖洪泛 {M} 项 / 横向一致性 {K} 项）」。
- **某维度 0 检查项**（因层缺失全部跳过）：标注「{维度名} 无可执行校验项（可用层不足），已跳过」，不报错。

### 规模自适应
- **阈值**：以任务数为计量对象。small ≤30 / medium 31–80 / large >80。
- **small**（≤30 任务）：完整详细报告 — 所有维度的每条检查结果逐一列出。
- **medium**（31–80 任务）：按严重度分层展示 — HIGH/CONFLICT 详细、MEDIUM/WARNING 摘要、LOW/INFO 仅统计。
- **large**（>80 任务）：统计总览 + 仅展开 HIGH/CONFLICT 级问题，其余按类型折叠为统计数字。

### 网络搜索不可用
- **趋势搜索**（动态趋势补充）：工具不可用或无有用结果 → 跳过趋势补充，不影响审计主流程。

### 上游过期检测
- **逐层时间戳比较**：加载每个上游产物时读取 `generated_at`，与审计运行时间比较。若某层在其前序层更新之后未被刷新 → 警告「{层名} 的 generated_at ({时间}) 早于其上游 {上游层名} 的 generated_at ({时间})，该层数据可能过期」。
- **报告中标注过期层**：在审计报告的摘要部分列出所有检测到的过期层，供用户决定是否先刷新再审计。
- 仅警告不阻断。

### 执行失败保护

- 任何步骤遇到不可恢复错误 → 写入 `.allforai/design-audit/design-audit-error.json`，包含 `{"error": "...", "step": "...", "timestamp": "..."}`。

---

## 5 条铁律

### 1. 只读不改

审计只报告问题，不修改任何上游产物。发现 ORPHAN 或 CONFLICT 后，由用户决定回哪一层修复。

### 2. 已有产物决定校验范围

缺失的层自动跳过对应的校验项，不报错、不要求用户先运行缺失的技能。报告中标注「层缺失，已跳过」即可。

### 3. product-map 是锚点

所有追溯和洪泛以 product-map 的 task-inventory 为根。task-inventory 中的任务是唯一的真值来源。

### 4. 按严重度排序

问题清单始终按以下顺序排列：CONFLICT > ORPHAN > GAP > WARNING > BROKEN_REF。同级别内按 task_id 排序。

### 5. category 一致性校验

校验 `task-inventory.json` 中所有任务是否标注了 `category`（basic/core）。缺失 category 的任务记为 WARNING。

### 6. 幂等

多次运行结果一致。不产生副作用，不缓存决策，不依赖上次运行结果。每次运行都是全新的独立校验。
