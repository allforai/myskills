# 技能通用增强协议

> 本文档定义三项增强协议的**通用框架**。各 skill 仅需引用本文件并补充自身定制内容。

---

## 一、动态趋势补充（WebSearch）

执行任何技能时，除经典理论外，建议补充近 12–24 个月的实践文章与案例：

- **来源优先级**：P1 官方文档/规范 > P2 知名作者（Martin, Fowler, Cockburn）> P3 技术媒体（InfoQ, ThoughtWorks Radar）> P4 社区帖
- **决策留痕**：对关键结论记录 `ADOPT|REJECT|DEFER` 与理由，避免"只收集不决策"
- **来源写入**：`.allforai/project-forge/trend-sources.json`（跨阶段共用）

各技能提供自身领域的搜索关键词示例（见各 skill 文件）。

---

## 二、工程保真增强（4E + 4V）

执行任何阶段时，建议同步参考：`docs/engineering-fidelity.md`。

- **E2 Provenance**：关键产出标注 `_Source: T001, F001, CN001_`，确保可追溯到 product-map。
- **E3 Guardrails**：高频/高风险任务的 rules / exceptions / audit / sla 映射到 spec，不遗漏业务边界。
- **E4 Context**：保留 value / risk_level / frequency，让下游理解"为什么重要"。
- **4V 覆盖**：高频+高风险任务至少覆盖 api + data + behavior 三个工程视角。

各技能根据自身产出类型，定义具体的保真重点（见各 skill 文件）。

---

## 三、跨模型增强（OpenRouter）

通过 OpenRouter MCP (`mcp__openrouter__ask_model`) 调用不同模型家族，利用各模型专长增强特定阶段的产出质量。

### 模型路由表

> 根据任务类型自动选择最佳模型。各 skill 引用此表，按 `task_type` 调用。

| task_type | 模型家族 | 选择理由 | task 参数 | temperature | 典型应用阶段 |
|-----------|---------|---------|----------|-------------|------------|
| `api_design_review` | GPT | 结构化推理、规范遵循 | `structured_output` | 0.2 | design-to-spec Step 2 |
| `data_model_review` | DeepSeek | 技术分析深度、性价比 | `technical_validation` | 0.2 | design-to-spec Step 2 |
| `tech_spike_research` | GPT / Gemini | 竞争分析、发散思维 | `competitive_analysis` | 0.3 | project-forge Phase 0.5 |
| `code_impl_review` | DeepSeek | 代码级技术判断、性价比 | `technical_validation` | 0.2 | product-verify S5 |
| `text_diversity_zh` | Qwen | 中文语感、双语推理 | `chinese_market_analysis` | 0.8 | seed-forge Step 2 |
| `text_diversity_intl` | Gemini | 多语言创意、发散 | `research_synthesis` | 0.8 | seed-forge Step 2 |
| `dependency_check` | GPT | 结构化输出、生态熟悉度 | `structured_output` | 0.1 | project-scaffold Step 3 |
| `test_scenario_gap` | Gemini | 发散思维、边界想象力 | `research_synthesis` | 0.5 | e2e-verify Step 1 |

### 调用规范

```
mcp__openrouter__ask_model(
  task: "{task 参数}",
  model_family: "{模型家族}",
  prompt: "{按下方模板构造}",
  temperature: {温度值}
)
```

### Prompt 模板结构

所有跨模型调用的 prompt 遵循统一结构，确保输出可解析：

```
## 角色
你是一位 {角色描述}。

## 上下文
- 项目技术栈: {tech_stack}
- 当前阶段: {phase_name}

## 输入
{具体内容（代码片段/API 列表/数据模型等）}

## 任务
{具体审查/生成指令}

## 输出格式
以 JSON 格式返回:
{期望的 JSON schema}
```

### 优雅降级

```
OpenRouter MCP 可用?
  → 是: 按模型路由表调用，结果合并到主产出
  → 否: 跳过交叉验证步骤，仅使用 Claude 主引擎结果
       输出: 「{step_name} ⊘ OpenRouter 不可用，跳过交叉验证」
```

**铁律**：OpenRouter 结果是**辅助增强**，不替代 Claude 主引擎。分歧项交用户决策，不自动覆盖。

### 成本控制

| 原则 | 规则 |
|------|------|
| 按需调用 | 仅在路由表定义的阶段调用，不随意扩散 |
| 高频高风险优先 | 审查类调用优先覆盖 frequency=高 + risk_level=高 的项 |
| 批量合并 | 同阶段多个审查项合并为 1 次调用（≤ 3000 字），减少调用次数 |
| 上限封顶 | 单阶段 OpenRouter 调用不超过 5 次 |

各技能在「增强协议」节中标注具体使用的 task_type 和触发条件（见各 skill 文件）。
