# AI Gateway MCP 配置指南

## 环境变量

API Key 配置在插件 `.mcp.json` 的 `env` 块中（通过 `/setup` 命令管理）：

| 变量 | 用途 | 必需 |
|------|------|------|
| `OPENROUTER_API_KEY` | 跨模型 XV + GPT-5 Image 生图 | 是（核心） |
| `GOOGLE_API_KEY` | Imagen 4 生图 + Veo 3.1 生视频 + TTS | 可选 |
| `FAL_KEY` | FLUX 2 Pro 生图 + Kling 生视频 | 可选 |
| `BRAVE_API_KEY` | Brave Search 搜索 | 可选 |

## MCP 服务器位置

```
product-design-skill/mcp-ai-gateway/
```

## 配置文件

### 1. MCP 服务器配置
`product-design-skill/.mcp.json`
```json
{
  "mcpServers": {
    "ai-gateway": {
      "command": "node",
      "args": ["./mcp-ai-gateway/dist/index.js"],
      "env": {
        "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
        "GOOGLE_API_KEY": "${GOOGLE_API_KEY}",
        "BRAVE_API_KEY": "${BRAVE_API_KEY}",
        "FAL_KEY": "${FAL_KEY}"
      }
    }
  }
}
```

### 2. 路由配置
`mcp-ai-gateway/src/config/defaults.ts`

定义 task_type -> model_family 的映射关系。

### 3. 模型选择
模型选择由 LLM 驱动（`region-detector.ts`），从 OpenRouter `/models` API 获取候选列表，使用 gpt-4.1-mini 判断各家族最佳旗舰模型，结果缓存 24 小时。

## 注册的工具

| 工具 | 条件 | 用途 |
|------|------|------|
| `ask_model` | 始终 | 跨模型查询 |
| `refresh_models` | 始终 | 刷新模型缓存 + 查看路由状态 |
| `openrouter_generate_image` | 始终 | GPT-5 Image / Gemini Flash Image 生图 |
| `generate_image` | GOOGLE_API_KEY | Imagen 4 生图 |
| `generate_video` | GOOGLE_API_KEY | Veo 3.1 生视频 |
| `generate_tts` | GOOGLE_API_KEY | Cloud TTS 语音合成 |
| `flux_generate_image` | FAL_KEY | FLUX 2 Pro/Dev/Schnell 生图 |
| `kling_generate_video` | FAL_KEY | Kling 2.1 Master 生视频 |
| `brave_web_search` | BRAVE_API_KEY | 网页搜索 |
| `brave_image_search` | BRAVE_API_KEY | 图片搜索 |
| `brave_video_search` | BRAVE_API_KEY | 视频搜索 |

## 可用模型家族

| Family | Provider | 适用场景 |
|--------|----------|---------|
| gpt | OpenAI | 信息综合、结构化推理 |
| gemini | Google | 发散思维、多模态 |
| claude | Anthropic | 结构化分析、严谨推理 |
| deepseek | DeepSeek | 推理链、技术分析 |
| llama | Meta | 通用推理、多语言 |
| qwen | Alibaba | 中文理解、双语推理 |

## 降级链

```
生图: Imagen 4 -> GPT-5 Image -> FLUX 2 Pro -> 跳过
生视频: Veo 3.1 -> Kling -> 跳过
搜索: Brave Search -> WebSearch -> AI 生成
```

## 测试连接

```bash
cd product-design-skill/mcp-ai-gateway
npm run build
# 重启 Claude Code 后工具自动可用
```

## 故障排查

### 1. API Key 无效
运行 `/setup check` 查看所有外部能力状态。

### 2. 模型不可用（区域限制）
`refresh_models` 工具会自动检测区域并路由到可用模型。中国区自动降级到 qwen/deepseek。

### 3. MCP 服务器未编译
```bash
cd product-design-skill/mcp-ai-gateway
npm install && npm run build
```

## 用户自定义路由

创建 `.allforai/openrouter-config.yaml`：
```yaml
routing:
  competitive_analysis: "qwen"  # 覆盖默认路由
  market_research: "deepseek"
```
