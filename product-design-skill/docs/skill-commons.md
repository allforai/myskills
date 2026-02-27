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

## 三、跨模型交叉验证 XV（可选增强）

当 `mcp__openrouter__ask_model` 工具可用时，在指定 Step 完成后自动发起交叉验证：

- **自动检测**：检查工具是否可用
- **自动发起**：按各技能定义的 `task_type` 和目标模型发起验证
- **结果写入**：写入产出的 `cross_model_review` 字段
- **失败处理**：工具不可用或调用失败时，自动跳过，不阻塞流程，不生成 `cross_model_review` 字段

各技能定义自身的验证点、task_type、发送内容和写入字段（见各 skill 文件）。
