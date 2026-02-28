# OpenRouter MCP 配置指南

## 环境变量

API Key 已配置在 `~/.bashrc`：
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

## MCP 服务器位置

```
/home/hello/Documents/myskills/product-design-skill/mcp-openrouter/
```

## 配置文件

### 1. MCP 服务器配置
`product-design-skill/.mcp.json`
```json
{
  "mcpServers": {
    "openrouter": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp-openrouter/dist/index.js"],
      "env": {
        "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}"
      }
    }
  }
}
```

### 2. 路由配置
`mcp-openrouter/src/config/defaults.ts`

定义 task_type → model_family 的映射关系。

### 3. 模型家族定义
`mcp-openrouter/src/data/model-families.json`

定义每个 model_family 的 provider 和 id_prefixes。

## 可用模型家族

| Family | Provider | 适用场景 |
|--------|----------|---------|
| gpt | OpenAI | 信息综合、结构化推理 |
| gemini | Google | 发散思维、多模态 |
| claude | Anthropic | 结构化分析、严谨推理 |
| deepseek | DeepSeek | 推理链、技术分析 |
| llama | Meta | 通用推理、多语言 |
| qwen | Alibaba | 中文理解、双语推理 |

## 创新流程路由（新增）

| Task Type | Model Family | 角色 | Temperature |
|-----------|-------------|------|-------------|
| assumption_challenge | gpt | 挑战者 | 1.0 |
| constraint_classification | gemini | 守护者 | 0.5 |
| innovation_exploration | gpt | 探索者 A | 0.9 |
| innovation_exploration_alt | gemini | 探索者 B | 0.9 |
| disruptive_innovation | gpt | 颠覆者 | 1.2 |
| boundary_enforcement | gemini | 守护者 | 0.3 |
| cross_domain_research | deepseek | 考古学家 | 0.9 |
| synthesis_innovation | qwen | 炼金师 | 0.8 |

## 测试连接

```bash
cd /home/hello/Documents/myskills/product-design-skill/mcp-openrouter
./test-connection.sh
```

## 在 Claude Code 中使用

配置完成后，在 skill 中调用：

```typescript
// 示例：调用 ask_model 工具
const result = await ask_model({
  task: "assumption_challenge",
  prompt: "列出英语教育行业的 10 条共识...",
  model_family: "gpt",
  temperature: 1.0
});
```

## 故障排查

### 1. API Key 无效
```bash
echo $OPENROUTER_API_KEY
```

### 2. 模型不可用（区域限制）
某些模型在中国区不可用，使用以下替代：
- `openai/gpt-*` → `qwen/qwen-*` 或 `deepseek/deepseek-*`
- `google/gemini-*` → 通常可用

### 3. MCP 服务器未编译
```bash
cd mcp-openrouter
npm run build
```

## 用户自定义路由

创建 `.allforai/openrouter-config.yaml`：
```yaml
routing:
  competitive_analysis: "qwen"  # 覆盖默认路由
  market_research: "deepseek"
```
