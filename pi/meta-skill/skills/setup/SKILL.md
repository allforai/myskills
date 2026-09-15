---
name: setup
description: >
  Detect and configure optional external capabilities for the Pi meta-skill adapter
  (gateway build, API keys, browser automation). User-invoked only via /skill:setup
  or /skill:meta-skill setup; never invoke it yourself.
---

# Setup — Pi External Capability Management

用户显式调用 `/skill:setup [check|reset|update|impact]` 才运行。相对路径从本 skill 目录解析；包根目录是上两级。

## Modes

- 无参数: 完整检测与补救引导
- `check`: 只报告状态
- `reset`: 清除假定，从头评估
- `update`: 重建本地 gateway 并刷新安装说明
- `impact [from_ref]`: 分析 meta-skill 变更，建议当前项目哪些节点应重跑

## Capability Model

所有外部能力都可选。缺了就降级，不要把 setup 当成 bootstrap 失败。

### MCP-backed tools

| Capability | Pi check | Purpose |
|------------|----------|---------|
| browser automation | 当前会话是否已有 Playwright/浏览器工具 | UI verification |
| Stitch UI | 当前会话是否已有 Stitch 工具 | high-fidelity visual generation |
| ai-gateway | `../../mcp-ai-gateway/dist/index.js` 存在 | search / image / model gateway |

### API-key-backed services

| Capability | Env var |
|------------|---------|
| OpenRouter | `OPENROUTER_API_KEY` |
| Google AI | `GOOGLE_API_KEY` |
| fal.ai | `FAL_KEY` |
| Brave Search | `BRAVE_API_KEY` |

### Built-in fallback

| Capability | Fallback |
|------------|----------|
| search | 当前 Pi 已加载的 web search 工具；没有就跳过增强搜索 |
| question flow | 纯文本提问 |

不要自动安装扩展、MCP 服务器或另一套 harness。

## Step 0: Build Check

1. 检查 `../../mcp-ai-gateway/dist/index.js`
2. 缺失时：`cd ../../mcp-ai-gateway && npm install && npm run build`
3. 报告构建是否就绪。构建失败则说明 MCP 工具不可用，预置脚本仍可用，继续。

## Step 1: Status Dashboard

至少报告：gateway 构建、浏览器自动化、Stitch、四个 API key。
附降级说明：无浏览器则跳过动态 UI 验证；无 Stitch 则用文本视觉规格；无搜索 key 则用已有搜索或用户材料；无图/视频服务则跳过媒体增强。

`check` 模式在仪表板后停止。

## Step 2: Remediation

- 缺 gateway build：执行或说明构建步骤
- 缺 env：请用户提供，不要编造 key
- 缺浏览器 / Stitch：说明前提和降级路径，不要代装

## Step 3: Impact Analysis

`impact` 模式不配置外部服务。从当前项目根运行：

```bash
python3 ../../scripts/orchestrator/analyze_skill_update_impact.py \
  --repo-root <myskills_repo> \
  --project-root . \
  --from-ref <from_ref> \
  --output-root .allforai/setup
```

源码安装时 `<myskills_repo>` 是包根的上两级。没有 `<from_ref>` 时仍运行分析器（可省略该旗标）。不是 git 仓库则改传 `--changed-file`。
产物：`.allforai/setup/skill-update-impact.json` 与 `.md`。
用报告决定是否重跑 `/skill:bootstrap`、某个节点或 QA；setup 本身不自动重跑。
