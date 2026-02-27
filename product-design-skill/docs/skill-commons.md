# 技能通用增强协议

> 本文档定义三项增强协议的**通用框架**。各 skill 仅需引用本文件并补充自身定制内容。

---

## 一、动态趋势补充（WebSearch）

执行任何技能时，除经典理论外，建议补充近 12–24 个月的实践文章与案例：

- **来源优先级**：官方规范/权威研究 > 一线产品团队实践 > 社区文章
- **决策留痕**：对关键结论记录 `ADOPT|REJECT|DEFER` 与理由，避免"只收集不决策"
- **来源写入**：`.allforai/product-design/trend-sources.json`（跨阶段共用）

各技能提供自身领域的搜索关键词示例（见各 skill 文件）。

---

## 二、信息保真增强（4D + 6V）

执行任何阶段时，建议同步参考：`docs/information-fidelity.md`。

- 关键产出除结论字段外，建议补充：`source_refs`、`constraints`、`decision_rationale`。
- 高频/高风险对象至少覆盖 4/6 视角（`user/business/tech/ux/data/risk`）。
- 作为下游锚点的产出，优先保证"可追溯 + 可解释"，避免只保留名称导致语义丢失。

各技能根据自身产出类型，定义具体的保真重点（见各 skill 文件）。

---

## 三、跨模型交叉验证 XV（自动闭环）

预置脚本通过 `OPENROUTER_API_KEY` 环境变量检测可用性，直连 OpenRouter API（Python `urllib.request`），不依赖 MCP 工具：

- **自动检测**：检查 `OPENROUTER_API_KEY` 环境变量是否存在
- **直连 API**：脚本使用 `urllib.request` 直连 `https://openrouter.ai/api/v1/chat/completions`，task→model 路由硬编码于 `_common.py`（与 `defaults.ts` 保持一致）
- **自动采纳**：高严重度发现自动修正数据（追加缺口/用例、调整优先级、标记弱项），不问用户
- **结果写入**：写入产出的 `cross_model_review` 字段
- **API Key 缺失**：静默跳过（向后兼容）
- **API Key 存在但调用失败**：抛异常终止（不静默吞错）
- **429 限流**：sleep 3s → 重试 1 次 → 失败则抛异常

各技能定义自身的验证点、task_type、发送内容和写入字段（见各 skill 文件）。
