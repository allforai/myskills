---
name: setup
description: >
  Detect and configure optional external capabilities for the Pi meta-skill adapter
  (agent CLIs, API keys, browser automation). User-invoked only via /skill:setup
  or /skill:meta-skill setup; never invoke it yourself.
---

# Setup — Pi External Capability Management

用户显式调用 `/skill:setup [check|reset|update|impact]` 才运行。相对路径从本 skill 目录解析；包根目录是上两级。

## Modes

- 无参数: 完整检测与补救引导
- `check`: 只报告状态
- `reset`: 清除假定，从头评估
- `update`: 刷新安装说明
- `impact [from_ref]`: 分析 meta-skill 变更，建议当前项目哪些节点应重跑

## Capability Model

所有外部能力都可选。缺了就降级，不要把 setup 当成 bootstrap 失败。

### MCP-backed tools

| Capability | Pi check | Purpose |
|------------|----------|---------|
| browser automation | 当前会话是否已有 Playwright/浏览器工具 | UI verification |

### Agent CLI

交叉验证不需要专门的服务：Pi 直接换一个模型跑，或交给本机装着的另一家 agent CLI；都没有就用新上下文的子代理。

| Capability | Pi check | Purpose |
|------------|----------|---------|
| 生图 | `command -v codex` | 唯一图片生成源（`codex exec`），见 game-art `image-generation-contract` |
| 生视频 | `command -v grok` + `grok --no-auto-update models` 显示已登录 | 唯一视频生成源；需订阅含视频且未被零数据保留关闭 |

### API-key-backed services

| Capability | Env var |
|------------|---------|
| OpenRouter | `OPENROUTER_API_KEY` |
| Google AI（Lyria 配乐生成） | `GOOGLE_API_KEY` |

### Built-in fallback

| Capability | Fallback |
|------------|----------|
| search | 当前 Pi 已加载的 web search 工具；没有就跳过增强搜索 |
| question flow | 纯文本提问 |

不要自动安装扩展、MCP 服务器或另一套 harness。

## Step 1: Status Dashboard

至少报告：浏览器自动化、Codex 与 Grok CLI、两个 API key。
附降级说明：无浏览器则跳过动态 UI 验证；无 Codex 则生图请求阻塞（`blocked_by_missing_image_cli`），无 Grok 则生视频请求阻塞（`blocked_by_missing_video_cli`），二者都没有替代源。

`check` 模式在仪表板后停止。

## Step 2: Remediation

- 缺 env：请用户提供，不要编造 key
- 缺浏览器：说明前提和降级路径，不要代装

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
