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

## 二、外部能力探测协议

> 统一各技能对外部工具/服务的探测、使用和降级模式。避免各技能各写各的降级逻辑。

### 能力注册表

| 能力 ID | 探测方式 | 使用插件 | 降级策略 |
|---------|---------|---------|---------|
| `playwright` | 检查 `mcp__plugin_playwright_playwright__browser_navigate` 工具可用性 | demo-forge, dev-forge, deadhunt | 无降级 — 提示用户安装 |
| `openrouter_mcp` | 调用 `mcp__plugin_product-design_openrouter__detect_region` | product-design, dev-forge | 跳过 MCP XV，脚本 XV 仍可用 |
| `openrouter_script` | 检查 `OPENROUTER_API_KEY` 环境变量 | product-design (预置脚本) | 静默跳过 XV |
| `brave_search` | 检查 `mcp__brave-search__brave_web_search` 工具 或 `BRAVE_API_KEY` | demo-forge | Brave → WebSearch → AI 生成 |
| `google_ai` | 检查 `GOOGLE_API_KEY` 环境变量 | demo-forge | Google AI → DALL-E → 本地 SD → 报错 |
| `stitch_ui` | 检查 `mcp__plugin_product-design_stitch__create_project` 工具 | product-design (规划中) | 跳过视觉稿，使用文字规格 |
| `websearch` | 内置工具，始终可用 | product-design, demo-forge | 无需降级 |

### 统一探测模式

每个技能在执行前，对其依赖的外部能力执行探测。模式统一为三级：

```
探测 → 可用：正常使用
     → 不可用 + 有降级链：走降级链，输出一行提示
     → 不可用 + 无降级链：提示用户安装/配置，阻塞或跳过（视能力重要性）
```

**提示格式统一**：

```
{step_name} ⊘ {能力名} 不可用，{降级动作}
```

示例：
- `M2 搜索采集 ⊘ Brave Search 不可用，降级到 WebSearch`
- `XV 交叉验证 ⊘ OpenRouter 不可用，跳过交叉验证`
- `V1 登录验证 ⊘ Playwright 不可用，请安装: claude mcp add playwright -- npx @anthropic-ai/mcp-playwright`

### 技能声明规范

各技能在「增强协议」或「前提」节中，用以下格式声明外部能力依赖：

```markdown
**外部能力依赖**：

| 能力 | 重要性 | 降级行为 |
|------|--------|---------|
| playwright | 必需 | 阻塞，提示安装 |
| openrouter_mcp | 可选 | 跳过 XV |
```

### 全局状态检测

运行 `/setup-services check` 可一次性查看所有外部能力状态。

---

## 三、信息保真增强（4D + 6V）

执行任何阶段时，建议同步参考：`docs/information-fidelity.md`。

- 关键产出除结论字段外，建议补充：`source_refs`、`constraints`、`decision_rationale`。
- 高频/高风险对象至少覆盖 4/6 视角（`user/business/tech/ux/data/risk`）。
- 作为下游锚点的产出，优先保证"可追溯 + 可解释"，避免只保留名称导致语义丢失。

各技能根据自身产出类型，定义具体的保真重点（见各 skill 文件）。

---

## 四、跨模型交叉验证 XV（自动闭环）

预置脚本通过 `OPENROUTER_API_KEY` 环境变量检测可用性，直连 OpenRouter API（Python `urllib.request`），不依赖 MCP 工具：

- **自动检测**：检查 `OPENROUTER_API_KEY` 环境变量是否存在
- **直连 API**：脚本使用 `urllib.request` 直连 `https://openrouter.ai/api/v1/chat/completions`，task→model 路由硬编码于 `_common.py`（与 `defaults.ts` 保持一致）
- **自动采纳**：高严重度发现自动修正数据（追加缺口/用例、调整优先级、标记弱项），不问用户
- **结果写入**：写入产出的 `cross_model_review` 字段
- **API Key 缺失**：静默跳过（向后兼容）
- **API Key 存在但调用失败**：抛异常终止（不静默吞错）
- **429 限流**：sleep 3s → 重试 1 次 → 失败则抛异常

各技能定义自身的验证点、task_type、发送内容和写入字段（见各 skill 文件）。
