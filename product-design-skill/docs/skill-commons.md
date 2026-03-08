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
| `playwright` | 检查 `mcp__playwright__browser_navigate` 或 `mcp__plugin_playwright_playwright__browser_navigate` 工具可用性（任一可用即就绪） | demo-forge, dev-forge, deadhunt | 无降级 — 提示用户安装 |
| `openrouter_mcp` | 检查 `mcp__plugin_product-design_ai-gateway__ask_model` 工具可用性 | product-design, dev-forge | 跳过 MCP XV，脚本 XV 仍可用 |
| `openrouter_script` | `_resolve_api_key("OPENROUTER_API_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | product-design (预置脚本) | 静默跳过 XV |
| `brave_search_mcp` | 检查 `mcp__plugin_product-design_ai-gateway__brave_web_search` 工具可用性 | demo-forge | 跳过 Brave MCP，脚本仍可用 |
| `brave_search_script` | `_resolve_api_key("BRAVE_API_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | demo-forge (预置脚本) | Brave → WebSearch → AI 生成 |
| `google_ai_mcp` | 检查 `mcp__plugin_product-design_ai-gateway__generate_image` 工具可用性 | demo-forge | 跳过 MCP 生图，脚本仍可用 |
| `google_ai_script` | `_resolve_api_key("GOOGLE_API_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | demo-forge (预置脚本) | Imagen 4 → GPT-5 Image → FLUX 2 Pro → 跳过 |
| `fal_ai_mcp` | 检查 `mcp__plugin_product-design_ai-gateway__flux_generate_image` 工具可用性 | demo-forge | 跳过 fal.ai MCP 生图/生视频 |
| `fal_ai_script` | `_resolve_api_key("FAL_KEY")`：环境变量 → `.mcp.json` env/\_\_keys | demo-forge (预置脚本) | FLUX 2 Pro（生图）+ Kling（生视频） |
| `stitch_ui` | 检查 `mcp__plugin_product-design_stitch__create_project` 工具 | product-design | 跳过视觉稿，使用文字规格 |
| `websearch` | 内置工具，始终可用 | product-design, demo-forge | 无需降级 |

### 统一探测模式

每个技能在执行前，对其依赖的外部能力执行探测。模式统一为三级：

```
探测 → 可用：正常使用
     → 不可用 + 有降级链：走降级链，输出一行提示
     → 不可用 + 无降级链 + 重要性=必需：触发交互式安装引导
     → 不可用 + 无降级链 + 重要性=可选：跳过，输出一行提示
```

**提示格式统一**：

```
{step_name} ⊘ {能力名} 不可用，{降级动作}
```

示例：
- `M2 搜索采集 ⊘ Brave Search 不可用，降级到 WebSearch`
- `XV 交叉验证 ⊘ OpenRouter 不可用，跳过交叉验证`
- `V1 登录验证 ⊘ Playwright 不可用` → 触发安装引导

### 交互式安装引导

当「重要性=必需」的能力未就绪时，用 AskUserQuestion 提供一键安装选项。**不静默安装，始终先问。**

#### 安装注册表

| 能力 ID | 安装命令 | 安装后追加步骤 | 需重启 Claude Code |
|---------|---------|--------------|-------------------|
| `playwright` | `claude mcp add -s user playwright -- npx -y @playwright/mcp@latest` | 无追加步骤（浏览器按需自动下载） | 是 |
| `openrouter_mcp` | `cd {PLUGIN_ROOT}/mcp-ai-gateway && npm install && npm run build` | 需配置 `OPENROUTER_API_KEY`（运行 `/setup`） | 是 |
| `brave_search_mcp` | ai-gateway 已内置，仅需配置 `BRAVE_API_KEY`（运行 `/setup`） | Key 写入 `.mcp.json` ai-gateway env | 是 |
| `google_ai_mcp` | ai-gateway 已内置，仅需配置 `GOOGLE_API_KEY`（运行 `/setup`） | Key 写入 `.mcp.json` ai-gateway env | 是 |
| `stitch_ui` | `claude mcp add -s user stitch -- npx -y @_davideast/stitch-mcp proxy` | 首次需 OAuth: `python3 {PLUGIN_ROOT}/scripts/stitch_oauth.py` | 是 |

#### 引导流程（编排命令的 Phase 0 使用）

当 Phase 0 外部能力快检发现「重要性=必需」的能力未就绪时：

```
1. AskUserQuestion:
   「{能力名} 未就绪，后续 {phase_name} 需要此工具。是否立即安装？」
   选项:
     1. 是，帮我安装
     2. 跳过，我稍后自行安装
     3. 查看安装详情

2. 选择「是，帮我安装」→ 执行安装命令（Bash）→ 安装后追加步骤 → 报告结果
   - 成功 → 提示「安装成功。需重启 Claude Code 生效。现在重启还是继续当前流程？」
   - 失败 → 展示错误信息 + 手动安装命令，继续流程（降级或跳过该阶段）

3. 选择「跳过」→ 记录跳过，按降级策略处理
   - 有降级链 → 走降级链
   - 无降级链 → 跳过依赖此能力的阶段，在最终报告中标注

4. 选择「查看安装详情」→ 展示完整安装步骤 + 前置要求 → 回到步骤 1
```

#### 单技能内的探测（非编排命令）

单独运行技能时（如直接 `/demo-verify`），不做完整引导，只输出一行提示 + 安装命令：

```
⊘ Playwright 不可用。安装: claude mcp add -s user playwright -- npx -y @playwright/mcp@latest（安装后需重启 Claude Code）
```

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

运行 `/setup check` 可一次性查看所有外部能力状态。

---

## 三、信息保真增强（4D + 6V）

执行任何阶段时，建议同步参考：`docs/information-fidelity.md`。

- 关键产出除结论字段外，建议补充：`source_refs`、`constraints`、`decision_rationale`。
- 高频/高风险对象至少覆盖 4/6 视角（`user/business/tech/ux/data/risk`）。
- 作为下游锚点的产出，优先保证"可追溯 + 可解释"，避免只保留名称导致语义丢失。

各技能根据自身产出类型，定义具体的保真重点（见各 skill 文件）。

---

## 四、跨模型交叉验证 XV（自动闭环）

预置脚本通过 `_resolve_api_key("OPENROUTER_API_KEY")` 检测可用性，直连 OpenRouter API（Python `urllib.request`），不依赖 MCP 工具：

- **自动检测**：`_resolve_api_key()` 从环境变量读取（用户在 `~/.zshrc` 或 `~/.bashrc` 中 export）
- **直连 API**：脚本使用 `urllib.request` 直连 `https://openrouter.ai/api/v1/chat/completions`，task→model 路由硬编码于 `_common.py`（与 `defaults.ts` 保持一致）
- **自动采纳**：高严重度发现自动修正数据（追加缺口/用例、调整优先级、标记弱项），不问用户
- **结果写入**：写入产出的 `cross_model_review` 字段
- **API Key 缺失**：静默跳过（向后兼容）
- **API Key 存在但调用失败**：抛异常终止（不静默吞错）
- **429 限流**：sleep 3s → 重试 1 次 → 失败则抛异常

各技能定义自身的验证点、task_type、发送内容和写入字段（见各 skill 文件）。
