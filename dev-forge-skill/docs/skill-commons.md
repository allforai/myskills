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

## 二、外部能力探测协议

> 统一探测、降级模式。完整注册表和规范见 `product-design-skill/docs/skill-commons.md`「外部能力探测协议」章节。

dev-forge 涉及的外部能力：

| 能力 | 使用技能 | 重要性 | 降级行为 |
|------|---------|--------|---------|
| `playwright` | e2e-verify, product-verify | 条件必需（验证阶段） | 阻塞，提示安装 |
| `openrouter_mcp` | design-to-spec, task-execute, e2e-verify, product-verify | 可选 | 跳过 XV，输出提示 |

**提示格式**：`{step_name} ⊘ {能力名} 不可用，{降级动作}`

---

## 三、工程保真增强（4E + 4V）

执行任何阶段时，建议同步参考：`docs/engineering-fidelity.md`。

- **E2 Provenance**：关键产出标注 `_Source: T001, F001, CN001_`，确保可追溯到 product-map。
- **E3 Guardrails**：高频/高风险任务的 rules / exceptions / audit / sla 映射到 spec，不遗漏业务边界。
- **E4 Context**：保留 value / risk_level / frequency，让下游理解"为什么重要"。
- **4V 覆盖**：高频+高风险任务至少覆盖 api + data + behavior 三个工程视角。

各技能根据自身产出类型，定义具体的保真重点（见各 skill 文件）。

---

## 四、跨模型增强（OpenRouter）

通过 OpenRouter MCP (`mcp__plugin_product-design_ai-gateway__ask_model`) 调用不同模型家族，利用各模型专长增强特定阶段的产出质量。

### 专家模型路由矩阵 (The Expert Matrix)

> 根据任务领域自动选择最强审计模型，利用各模型长处进行 XV 交叉验证。

| 审计领域 | 推荐模型家族 | 擅长领域 | 应用场景示例 |
|-----------|-------------|---------|--------------|
| **架构与 API** | **GPT-4o** | 工业级标准遵循、RESTful 规范、OpenAPI 结构 | `api_design_review`, 契约漂移判定 |
| **数据与算法** | **DeepSeek** | RDBMS 性能优化、复杂 SQL、逻辑严密性、算法一致性 | `data_model_review`, 后端逻辑审计 |
| **UI 与 视觉** | **Gemini / GPT-4o-mini** | 多模态推理、布局感知、CSS 原语映射、Stitch 还原度 | `ui_consistency_review`, 前端组件审计 |
| **安全与合规** | **GPT-4o** | 漏洞模式识别、SAST 结果解读、敏感信息脱敏 | `security_audit`, DevSecOps 风险评估 |
| **测试与边界** | **Gemini** | 创意发散、异常路径设想、复杂 Mock 数据构造 | `test_scenario_gap`, 情感诱导数据设计 |

### 调用规范 (XV 自动路由)

执行 XV 审计时，Agent 应根据任务的 `batch` 类型自动映射模型：
- **B1 (Data/Foundation)** -> DeepSeek
- **B2 (Interface/API)** -> GPT-4o
- **B3 (UI/Component)** -> Gemini
- **B5 (Testing/Security)** -> GPT-4o / Gemini

---

## 五、优雅降级与成本控制
