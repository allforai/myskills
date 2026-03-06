---
description: "检测和配置所有外部能力：Playwright（UI 自动化）+ OpenRouter（跨模型 XV）+ Brave Search（媒体搜索）+ Google AI（生图/生视频）+ Stitch UI（视觉稿）。一站式状态仪表板 + 引导配置。"
argument-hint: "[check|reset]"
allowed-tools: ["Read", "Write", "Grep", "Bash", "AskUserQuestion"]
---

# Setup — 外部能力管理

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数** → 完整引导：检测 → 获取 Key → 验证 → 持久化
- **`check`** → 仅检测当前状态（全部外部能力的可用性仪表板）
- **`reset`** → 清除已有配置，重新引导

## 外部能力总览

插件套件依赖以下外部能力，分为三类：

### MCP 工具（需安装插件）

| 能力 | 探测方式 | 使用插件 | 用途 |
|------|---------|---------|------|
| Playwright | `mcp__plugin_playwright_playwright__browser_navigate` 可用性 | demo-forge, dev-forge, deadhunt | UI 自动化：验证、E2E 测试、死链扫描 |
| Stitch UI | `mcp__plugin_product-design_stitch__create_project` 可用性 | product-design | 高保真 UI 视觉稿生成（Google Stitch） |

### API Key 服务（需配置密钥）

| 能力 | Key 格式 | 使用插件 | 用途 | 备注 |
|------|---------|---------|------|------|
| OpenRouter | `sk-or-...` | product-design, dev-forge, demo-forge | XV 交叉验证 + GPT-5/Gemini 生图 | Key 写入 ai-gateway env |
| Google AI | `AIza...` | demo-forge | Imagen 4 生图 + Veo 3.1 生视频 + TTS | Key 写入 ai-gateway env |
| fal.ai | fal key | demo-forge | FLUX 2 Pro 生图 + Kling 生视频 | Key 写入 ai-gateway env |
| Brave Search | `BSA...` | demo-forge | 媒体搜索（网页/图片/视频） | Key 写入 ai-gateway env |

### 内置工具（始终可用）

| 能力 | 使用插件 | 用途 |
|------|---------|------|
| WebSearch | product-design, demo-forge | 搜索驱动设计、媒体搜索降级 |

**所有外部能力均为可选 — 未配置时技能正常运行，跳过对应增强功能或走降级链。**

## 执行流程

### Step 0: MCP 服务器构建检测

在检测 Key 之前，先确保 MCP 服务器已构建（所有模式均执行此步）：

1. **检查 dist/index.js 是否存在**：
   ```bash
   ls ${CLAUDE_PLUGIN_ROOT}/mcp-ai-gateway/dist/index.js
   ```

2. **不存在或文件 < 100 bytes** → 需要构建：
   - 检查 node_modules 是否存在：`ls ${CLAUDE_PLUGIN_ROOT}/mcp-ai-gateway/node_modules/`
   - 不存在 → 运行 `cd ${CLAUDE_PLUGIN_ROOT}/mcp-ai-gateway && npm install`
   - 运行 `cd ${CLAUDE_PLUGIN_ROOT}/mcp-ai-gateway && npm run build`
   - 验证 `dist/index.js` 已生成
   - 成功 → 报告「MCP 服务器构建成功」
   - 失败 → 报告错误，提示「MCP 构建失败，XV 的 MCP 工具不可用，但预置脚本 XV 不受影响」，继续执行

3. **已存在** → 报告「MCP 服务器已构建」，继续

### Step 1: 检测当前状态

检测所有外部能力的就绪状态：

#### 1a. Playwright MCP（已内置于 .mcp.json）

1. **检查 MCP 工具**：检查 `mcp__plugin_product-design_playwright__browser_navigate` 或 `mcp__plugin_playwright_playwright__browser_navigate` 工具是否可用（内置版或独立插件版均可）
   - 可用 → Playwright 就绪
   - 不可用 → Playwright 未就绪（可能需要重启 Claude Code 加载 .mcp.json 中的内置配置）

#### 1b. OpenRouter

1. **MCP 工具通道**：检查 `mcp__plugin_product-design_ai-gateway__ask_model` 工具是否可用
   - 可用 → MCP XV 就绪
   - 不可用 → MCP XV 未就绪（可能需要重启 Claude Code）

2. **脚本通道**：检查 `OPENROUTER_API_KEY` 环境变量
   - 已设置 → 脚本 XV 就绪
   - 未设置 → 脚本 XV 未就绪

#### 1c. Brave Search

1. **MCP 工具通道**：检查 `mcp__plugin_product-design_ai-gateway__brave_web_search` 工具是否可用
   - 可用 → Brave MCP 就绪（ai-gateway 已加载且 BRAVE_API_KEY 已配置）
   - 不可用 → Brave MCP 未就绪

2. **环境变量**：检查 `BRAVE_API_KEY` 环境变量
   - 已设置 → Brave Key 就绪（脚本可用）
   - 未设置 → Brave 未就绪

#### 1d. Google AI

1. **MCP 工具通道**：检查 `mcp__plugin_product-design_ai-gateway__generate_image` 工具是否可用
   - 可用 → Google AI MCP 就绪（ai-gateway 已加载且 GOOGLE_API_KEY 已配置）
   - 不可用 → Google AI MCP 未就绪

2. **环境变量**：检查 `GOOGLE_API_KEY` 环境变量
   - 已设置 → Google AI Key 就绪（脚本可用）
   - 未设置 → Google AI 未就绪

#### 1e. fal.ai (FLUX + Kling)

1. **MCP 工具通道**：检查 `mcp__plugin_product-design_ai-gateway__flux_generate_image` 工具是否可用
   - 可用 → fal.ai MCP 就绪
   - 不可用 → fal.ai MCP 未就绪

2. **环境变量**：检查 `FAL_KEY` 环境变量
   - 已设置 → fal.ai Key 就绪
   - 未设置 → fal.ai 未就绪

#### 1f. Stitch UI

1. **检查 MCP 工具**：检查 `mcp__plugin_product-design_stitch__create_project` 工具是否可用
   - 可用 → Stitch 就绪
   - 不可用 → Stitch 未就绪（需运行 `npx -y @_davideast/stitch-mcp init` 完成 Google OAuth 认证）

#### 状态仪表板输出

展示所有外部能力的状态汇总：

```
## 外部能力状态

| 能力 | 类型 | 状态 | 使用插件 | 用途 |
|------|------|------|---------|------|
| Playwright | MCP 工具 | {就绪/未就绪} | demo-forge, dev-forge, deadhunt | UI 自动化 |
| Stitch UI | MCP 工具 | {就绪/未就绪} | product-design | UI 视觉稿 |
| OpenRouter (MCP) | AI Gateway | {就绪/未就绪} | product-design, dev-forge | XV 交叉验证 |
| Google AI (MCP) | AI Gateway | {就绪/未就绪} | demo-forge | AI 生图/生视频/TTS |
| Brave Search (MCP) | AI Gateway | {就绪/未就绪} | demo-forge | 媒体搜索（网页/图片/视频） |
| OpenRouter Image | AI Gateway | 就绪（随 OpenRouter） | demo-forge | GPT-5/Gemini 生图（无额外 Key） |
| fal.ai (MCP) | AI Gateway | {就绪/未就绪} | demo-forge | FLUX 2 Pro 生图 + Kling 生视频 |
| OpenRouter (Script) | Key | {就绪/未就绪} | product-design 预置脚本 | XV 交叉验证 |
| Google AI (Key) | Key | {就绪/未就绪} | demo-forge 预置脚本 | AI 生图/生视频/TTS |
| Brave Search (Key) | Key | {就绪/未就绪} | demo-forge 预置脚本 | 媒体搜索 |
| WebSearch | 内置 | 就绪 | product-design, demo-forge | 搜索 |
| MCP 服务器 | 构建产物 | {已构建/未构建} | — | AI Gateway（OpenRouter + Google AI + Brave） |

降级链:
  Brave 不可用 → WebSearch → AI 生成
  OpenRouter MCP 不可用 → OpenRouter Script → 跳过 XV
  生图: Google Imagen 4 → OpenAI GPT Image → FLUX 2 Pro → 跳过
  生视频: Google Veo 3.1 → Kling → 跳过
  Playwright 不可用 → 无降级（提示安装）
  Stitch 不可用 → 跳过视觉稿，使用文字规格
```

**模式分支**：

- `check` 模式 → 输出状态仪表板后结束（附带未就绪项的安装/配置提示）
- `reset` 模式 → 继续 Step 1.5（全部 MCP）→ Step 2（全部 Key）
- 无参数模式：
  - 全部就绪 → 询问「所有外部服务已配置完毕，是否需要重新配置？」
  - 有未就绪项 → 继续 Step 1.5（仅未就绪的 MCP）→ Step 2（仅未就绪的 Key）

### Step 1.5: MCP 工具安装引导

对每个未就绪的 MCP 工具，按顺序引导安装。**已就绪的跳过。**

#### 1.5a. Playwright（若未就绪）

Playwright MCP 已内置于 product-design 插件的 `.mcp.json`（`@playwright/mcp@latest`），正常情况下随插件自动加载。

**若检测到未就绪**，说明 MCP 服务器可能未成功启动。提示：

```
Playwright MCP 已内置于插件配置，但当前未就绪。
可能原因：首次加载需要下载 @playwright/mcp 包。
建议：重启 Claude Code 后重新检测。
```

使用 AskUserQuestion 询问：

**「Playwright 未就绪（已内置于插件 .mcp.json）。如何处理？」**

选项：
- **重启后重试** — 我稍后重启 Claude Code，Playwright 会自动加载
- **独立安装** — 使用 `claude plugin add playwright` 安装官方独立插件
- **跳过** — 暂不处理（Playwright 无降级链，依赖它的功能将不可用）

#### 1.5b. Stitch UI（若未就绪）

使用 AskUserQuestion 询问：

**「Stitch UI 未就绪，用于生成高保真 UI 视觉稿（product-design ui-design 阶段）。是否安装？」**

选项：
- **安装** — 立即初始化 Stitch（需完成 Google OAuth 认证）
- **跳过** — 暂不安装（ui-design 将只生成文字规格，跳过视觉稿）
- **查看详情** — 展示安装步骤

##### 选择「安装」时：

执行初始化命令：

```bash
npx -y @_davideast/stitch-mcp init
```

> **注意**：此命令会打开浏览器进行 Google OAuth 认证。认证完成后，OAuth 凭证存储在 `~/.stitch-mcp/`。

认证成功后提示：

```
Stitch UI 认证完成。
MCP 服务器配置已在插件 .mcp.json 中就绪。
需重启 Claude Code 后生效。
```

##### 选择「查看详情」时：

展示完整安装步骤后回到选择。

```
Stitch UI（Google Stitch）安装步骤：

1. 初始化并完成 Google OAuth 认证:
   npx -y @_davideast/stitch-mcp init
   （会打开浏览器，用 Google 账号授权）

2. 认证完成后 OAuth 凭证自动存储在 ~/.stitch-mcp/

3. 重启 Claude Code

前提：
- 需要 Google 账号
- MCP 服务器配置已在插件 .mcp.json 中预置（无需额外配置）

用途：
- product-design ui-design Step 5.5: 生成高保真 UI 视觉稿
- 产出 HTML + 截图，供 dev-forge 参考实现
```

### Step 2: 引导获取 Key

按顺序引导每个未配置的服务。**已配置的服务跳过（除非 reset 模式）。**

#### 2a. OpenRouter

使用 AskUserQuestion 询问：

**「你是否已有 OpenRouter API Key？」**

选项：
- **已有 Key** — 我已经有 OpenRouter API Key，直接配置
- **需要注册** — 带我去获取一个
- **跳过** — 暂不配置 OpenRouter

##### 选择「需要注册」时：

展示注册步骤：

```
OpenRouter 注册步骤：

1. 访问 https://openrouter.ai
2. 点击右上角 Sign Up，使用 Google/GitHub 登录
3. 进入 https://openrouter.ai/keys 创建 API Key
4. 复制 Key（以 sk-or- 开头）

提示：
- OpenRouter 按用量计费，交叉验证每次调用成本约 $0.01-0.05
- 建议先充值 $5 试用，足够运行数十次完整产品设计流程
```

然后使用 AskUserQuestion 询问「请粘贴你的 OpenRouter API Key」（提供"其他"输入框让用户粘贴）。

##### 选择「已有 Key」时：

使用 AskUserQuestion 询问「请粘贴你的 OpenRouter API Key」。

##### 选择「跳过」时：

记录跳过，继续下一个服务。

#### 2b. Brave Search

使用 AskUserQuestion 询问：

**「你是否已有 Brave Search API Key？」**

选项：
- **已有 Key** — 我已经有 Brave Search API Key，直接配置
- **需要注册** — 带我去获取一个
- **跳过** — 暂不配置 Brave Search

##### 选择「需要注册」时：

展示注册步骤：

```
Brave Search API 注册步骤：

1. 访问 https://brave.com/search/api/
2. 点击 Get Started，创建账号
3. 创建 API Key
4. 复制 Key

提示：
- Brave Search 有免费额度（2000 queries/month）
- 足够运行多轮 demo-forge 媒体搜索
```

然后使用 AskUserQuestion 询问「请粘贴你的 Brave Search API Key」（提供"其他"输入框让用户粘贴）。

##### 选择「已有 Key」时：

使用 AskUserQuestion 询问「请粘贴你的 Brave Search API Key」。

##### 选择「跳过」时：

记录跳过，继续下一个服务。

#### 2c. Google AI

使用 AskUserQuestion 询问：

**「你是否已有 Google AI API Key？」**

选项：
- **已有 Key** — 我已经有 Google AI API Key，直接配置
- **需要注册** — 带我去获取一个
- **跳过** — 暂不配置 Google AI

##### 选择「需要注册」时：

展示注册步骤：

```
Google AI API Key 获取步骤：

1. 访问 https://console.cloud.google.com/
2. 创建或选择项目
3. 启用 Vertex AI API:
   在终端运行: gcloud services enable aiplatform.googleapis.com
   或在控制台搜索 "Vertex AI API" 并启用
4. 访问 https://console.cloud.google.com/apis/credentials
5. 点击 "Create Credentials" -> "API Key"
6. 复制 Key（以 AIza 开头）

提示：
- 需要 Google Cloud 账号（有免费额度）
- 一个 Key 覆盖: Imagen 4（生图）+ Veo 3.1（生视频）+ Cloud TTS（语音）
- 建议限制 Key 仅允许 Vertex AI API 调用
```

然后使用 AskUserQuestion 询问「请粘贴你的 Google AI API Key」（提供"其他"输入框让用户粘贴）。

##### 选择「已有 Key」时：

使用 AskUserQuestion 询问「请粘贴你的 Google AI API Key」。

##### 选择「跳过」时：

记录跳过，继续下一个服务。

#### 2d. fal.ai (FLUX 2 Pro + Kling)

使用 AskUserQuestion 询问：

**「你是否已有 fal.ai API Key？」**

选项：
- **已有 Key** — 我已经有 fal.ai Key，直接配置
- **需要注册** — 带我去获取一个
- **跳过** — 暂不配置 fal.ai

##### 选择「需要注册」时：

展示注册步骤：

```
fal.ai API Key 获取步骤：

1. 访问 https://fal.ai/dashboard
2. 注册账号（GitHub 登录）
3. 进入 Keys 页面创建 API Key
4. 复制 Key

提示：
- FLUX 2 Pro: $0.055/张（质量 Elo 最高）
- Kling 视频: ~$0.03/秒（性价比最高的视频生成）
- 按量计费，无月费
```

然后使用 AskUserQuestion 询问「请粘贴你的 fal.ai Key」（提供"其他"输入框让用户粘贴）。

##### 选择「已有 Key」时：

使用 AskUserQuestion 询问「请粘贴你的 fal.ai Key」。

##### 选择「跳过」时：

记录跳过。

### Step 3: 持久化 Key

对 Step 2 中获取到的每个 Key 执行持久化（跳过的服务不处理）。

**存储位置**：插件 `.mcp.json` 的 `env` 块（不污染 shell 环境变量）。

**原理**：
- MCP 工具路径：Claude Code 启动 MCP 服务器时自动注入 `.mcp.json` 中的 `env` 变量
- Python 脚本路径：`_common.py` 的 `_resolve_api_key()` 先查环境变量，再 fallback 解析 `.mcp.json` 的 `env` 块
- 两条路径都能读到 Key，无需在 `~/.zshrc` 或 `~/.bashrc` 中 export

**操作流程**：

1. **读取当前 `.mcp.json`**：
   ```
   Read ${CLAUDE_PLUGIN_ROOT}/.mcp.json
   ```

2. **合并 Key 到 env 块**：

   | Key | 写入位置 |
   |-----|---------|
   | `OPENROUTER_API_KEY` | `mcpServers.ai-gateway.env.OPENROUTER_API_KEY` |
   | `GOOGLE_API_KEY` | `mcpServers.ai-gateway.env.GOOGLE_API_KEY` |
   | `FAL_KEY` | `mcpServers.ai-gateway.env.FAL_KEY` |
   | `BRAVE_API_KEY` | `mcpServers.ai-gateway.env.BRAVE_API_KEY` |

   所有 Key 统一存储在 ai-gateway 服务器的 env 块中。将模板引用替换为实际值。

3. **使用 AskUserQuestion 确认**：展示将要写入的内容，请用户确认：

```
将写入以下 Key 到 ${CLAUDE_PLUGIN_ROOT}/.mcp.json：

  mcpServers.ai-gateway.env.OPENROUTER_API_KEY = "sk-or-...{后4位}"
  mcpServers.ai-gateway.env.GOOGLE_API_KEY = "AIza...{后4位}"
  mcpServers.ai-gateway.env.FAL_KEY = "...{后4位}"
  mcpServers.ai-gateway.env.BRAVE_API_KEY = "BSA...{后4位}"

Key 仅存储在插件配置中，不写入 shell 环境变量。
确认写入？
```

4. **写入**：用 Write 工具更新 `.mcp.json`
5. **生效方式**：
   - AI Gateway MCP 工具（OpenRouter + Google AI + Brave）：需**重启 Claude Code**（MCP 服务器启动时读取 env）
   - Python 脚本 XV：**立即生效**（每次执行时读取 `.mcp.json`）

### Step 4: 验证与报告

输出最终状态报告：

```
## 外部服务配置完成

| 服务 | Key | 存储位置 | 用途 |
|------|-----|---------|------|
| OpenRouter | sk-or-...{后4位} | .mcp.json → ai-gateway.env | XV + GPT-5/Gemini 生图 |
| Google AI | AIza...{后4位} | .mcp.json → ai-gateway.env | Imagen 4 + Veo 3.1 + TTS |
| fal.ai | ...{后4位} | .mcp.json → ai-gateway.env | FLUX 2 Pro + Kling 生视频 |
| Brave Search | BSA...{后4位} | .mcp.json → ai-gateway.env | 媒体搜索 |

下一步：重启 Claude Code 后运行 /setup check 验证连接。
```

对于跳过的服务，状态列显示「已跳过（可选）」。
对于之前已配置的服务，状态列显示「已配置（未修改）」。

## 报告输出要求（强制执行）

### check 模式报告

```
## 外部能力状态

MCP 工具:
  Playwright       {就绪/未就绪}   demo-forge, dev-forge, deadhunt — UI 自动化
  Stitch UI        {就绪/未就绪}   product-design — UI 视觉稿（Google Stitch）

AI Gateway（统一 MCP 服务器）:
  OpenRouter       {就绪/未就绪}   product-design, dev-forge — XV + GPT-5/Gemini 生图
  Google AI        {就绪/未就绪}   demo-forge — Imagen 4 + Veo 3.1 + TTS
  fal.ai           {就绪/未就绪}   demo-forge — FLUX 2 Pro + Kling 生视频
  Brave Search     {就绪/未就绪}   demo-forge — 媒体搜索（网页/图片/视频）

API Key（脚本回退）:
  OpenRouter Key   {就绪/未就绪}   product-design 预置脚本 — XV 交叉验证
  Google AI Key    {就绪/未就绪}   demo-forge 预置脚本 — AI 生图/生视频/TTS
  Brave Key        {就绪/未就绪}   demo-forge 预置脚本 — 媒体搜索

内置:
  WebSearch        就绪            product-design, demo-forge — 搜索

{若有未就绪的 MCP 工具或 Key：运行 /setup 进行安装和配置}
{若 MCP 已安装但工具不可用：需重启 Claude Code 加载 MCP 服务器}
{注: 所有外部能力均为可选，未配置不影响核心功能}
```

### 完整配置报告

```
## 外部服务配置完成

| 服务 | Key | 状态 | 用途 |
|------|-----|------|------|
| OpenRouter | sk-or-...{后4位} | {已写入 ai-gateway.env / 已跳过 / 已配置} | XV + GPT-5/Gemini 生图 |
| Google AI | AIza...{后4位} | {已写入 ai-gateway.env / 已跳过 / 已配置} | Imagen 4 + Veo 3.1 + TTS |
| fal.ai | ...{后4位} | {已写入 ai-gateway.env / 已跳过 / 已配置} | FLUX 2 Pro + Kling 生视频 |
| Brave Search | BSA...{后4位} | {已写入 ai-gateway.env / 已跳过 / 已配置} | 媒体搜索 |

MCP 工具（Step 1.5 已引导安装）:
  Playwright     {已安装/已跳过/之前已就绪}  demo-forge, dev-forge, deadhunt — UI 自动化
  Stitch UI      {已安装/已跳过/之前已就绪}  product-design — UI 视觉稿

下一步：重启 Claude Code 后运行 /setup check 验证连接。
```

## 铁律（强制执行）

1. **Key 不落项目目录** — API Key 不得写入 `.allforai/` 或任何用户项目目录下的文件。只写入插件自身的 `.mcp.json`（插件安装目录，非项目目录）
2. **不自动写入** — 写入配置文件前必须展示内容并获得用户确认
3. **不阻塞主流程** — 本命令仅配置增强功能。未配置任何服务不影响技能的核心功能
4. **不污染 shell** — 不向 `~/.zshrc`、`~/.bashrc` 等 shell 配置文件写入 export 语句。Key 统一存储在插件 `.mcp.json` 中
