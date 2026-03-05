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

### API Key 服务（需配置环境变量）

| 能力 | 环境变量 | Key 格式 | 使用插件 | 用途 |
|------|---------|---------|---------|------|
| OpenRouter | `OPENROUTER_API_KEY` | `sk-or-...` | product-design, dev-forge | 跨模型交叉验证（XV） |
| Brave Search | `BRAVE_API_KEY` | `BSA...` | demo-forge | 媒体搜索（图片/视频） |
| Google AI | `GOOGLE_API_KEY` | `AIza...` | demo-forge | AI 生图（Imagen 3）+ 生视频（Veo 2）+ TTS |

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
   ls ${CLAUDE_PLUGIN_ROOT}/mcp-openrouter/dist/index.js
   ```

2. **不存在或文件 < 100 bytes** → 需要构建：
   - 检查 node_modules 是否存在：`ls ${CLAUDE_PLUGIN_ROOT}/mcp-openrouter/node_modules/`
   - 不存在 → 运行 `cd ${CLAUDE_PLUGIN_ROOT}/mcp-openrouter && npm install`
   - 运行 `cd ${CLAUDE_PLUGIN_ROOT}/mcp-openrouter && npm run build`
   - 验证 `dist/index.js` 已生成
   - 成功 → 报告「MCP 服务器构建成功」
   - 失败 → 报告错误，提示「MCP 构建失败，XV 的 MCP 工具不可用，但预置脚本 XV 不受影响」，继续执行

3. **已存在** → 报告「MCP 服务器已构建」，继续

### Step 1: 检测当前状态

检测所有外部能力的就绪状态：

#### 1a. Playwright MCP

1. **检查 MCP 工具**：检查 `mcp__plugin_playwright_playwright__browser_navigate` 工具是否可用
   - 可用 → Playwright 就绪
   - 不可用 → Playwright 未就绪

#### 1b. OpenRouter

1. **MCP 工具通道**：检查 `mcp__plugin_product-design_openrouter__detect_region` 工具是否可用
   - 可用 → 调用 `mcp__plugin_product-design_openrouter__detect_region`，展示模型路由策略。MCP XV 就绪
   - 不可用 → MCP XV 未就绪（可能需要重启 Claude Code）

2. **脚本通道**：检查 `OPENROUTER_API_KEY` 环境变量
   - 已设置 → 脚本 XV 就绪
   - 未设置 → 脚本 XV 未就绪

#### 1b. Brave Search

1. **MCP 工具通道**：检查是否有名称中包含 `brave` 的 MCP 工具可用（如 `brave_web_search`、`brave_image_search`）
   - 可用 → Brave MCP 就绪
   - 不可用 → Brave MCP 未就绪

2. **环境变量**：检查 `BRAVE_API_KEY` 环境变量
   - 已设置 → Brave 就绪
   - 未设置 → Brave 未就绪

#### 1d. Google AI

1. **环境变量**：检查 `GOOGLE_API_KEY` 环境变量
   - 已设置 → Google AI 就绪
   - 未设置 → Google AI 未就绪

#### 1e. Stitch UI

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
| OpenRouter (MCP) | MCP 工具 | {就绪/未就绪} | product-design, dev-forge | XV 交叉验证 |
| OpenRouter (Script) | 环境变量 | {就绪/未就绪} | product-design 预置脚本 | XV 交叉验证 |
| Brave Search | MCP/环境变量 | {就绪/未就绪} | demo-forge | 媒体搜索 |
| Google AI | 环境变量 | {就绪/未就绪} | demo-forge | AI 生图/生视频/TTS |
| Stitch UI | MCP 工具 | {就绪/未就绪} | product-design | UI 视觉稿 |
| WebSearch | 内置 | 就绪 | product-design, demo-forge | 搜索 |
| MCP 服务器 | 构建产物 | {已构建/未构建} | — | OpenRouter MCP 通道 |

降级链:
  Brave 不可用 → WebSearch → AI 生成
  OpenRouter MCP 不可用 → OpenRouter Script → 跳过 XV
  Google AI 不可用 → DALL-E → 本地 SD → 跳过
  Playwright 不可用 → 无降级（提示安装）
```

**模式分支**：

- 所有 API Key 服务均就绪：
  - 若模式为 `check` → 输出状态仪表板后结束
  - 若模式为无参数 → 询问「所有外部服务已配置完毕，是否需要重新配置？」
    - 否 → 结束
    - 是 → 继续 Step 2
  - 若模式为 `reset` → 继续 Step 2
- 至少一个 API Key 服务未就绪：
  - 若模式为 `check` → 输出状态仪表板后结束，附带提示
  - 其他模式 → 继续 Step 2（仅引导未就绪的 API Key 服务）
- MCP 工具类（Playwright/Stitch）未就绪：
  - `check` 模式在状态表后附带安装提示
  - 其他模式 → 继续 Step 1.5（引导安装未就绪的 MCP 工具）

### Step 1.5: MCP 工具安装引导

对每个未就绪的 MCP 工具，按顺序引导安装。**已就绪的跳过。**

#### 1.5a. Playwright（若未就绪）

使用 AskUserQuestion 询问：

**「Playwright 未就绪，用于 UI 自动化验证（demo-forge/dev-forge/deadhunt）。是否安装？」**

选项：
- **安装** — 立即安装 Playwright MCP
- **跳过** — 暂不安装（Playwright 无降级链，依赖它的功能将不可用）
- **查看详情** — 展示安装步骤

##### 选择「安装」时：

执行安装命令：

```bash
claude mcp add playwright -- npx @anthropic-ai/mcp-playwright
```

安装成功后提示：

```
Playwright MCP 已安装。
首次使用前需安装浏览器: npx playwright install chromium
需重启 Claude Code 后生效。
```

##### 选择「查看详情」时：

展示完整安装步骤后回到选择。

```
Playwright MCP 安装步骤：

1. 安装 MCP 服务器:
   claude mcp add playwright -- npx @anthropic-ai/mcp-playwright

2. 安装浏览器（首次）:
   npx playwright install chromium

3. 重启 Claude Code

用途：
- demo-forge verify: Playwright 验证灌入数据
- dev-forge e2e-verify: 端到端测试
- deadhunt deep/full: 动态死链扫描
```

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
- 一个 Key 覆盖: Imagen 3（生图）+ Veo 2（生视频）+ Cloud TTS（语音）
- 建议限制 Key 仅允许 Vertex AI API 调用
```

然后使用 AskUserQuestion 询问「请粘贴你的 Google AI API Key」（提供"其他"输入框让用户粘贴）。

##### 选择「已有 Key」时：

使用 AskUserQuestion 询问「请粘贴你的 Google AI API Key」。

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
   | `OPENROUTER_API_KEY` | `mcpServers.openrouter.env.OPENROUTER_API_KEY` |
   | `BRAVE_API_KEY` | 新增 `mcpServers.brave-search.env.BRAVE_API_KEY`（若 brave-search 服务器不存在则仅记录，提示用户自行配置 Brave MCP） |
   | `GOOGLE_API_KEY` | 新增 `mcpServers.google-ai.env.GOOGLE_API_KEY`（虚拟服务器条目，仅作 Key 存储，无 command） |

   对于 OpenRouter：将 `"${OPENROUTER_API_KEY}"` 模板引用替换为实际值。

   对于无对应 MCP 服务器的 Key（Brave、Google AI）：在 `.mcp.json` 中新增一个 `__keys` 存储区：
   ```json
   "__keys": {
     "BRAVE_API_KEY": "BSA...",
     "GOOGLE_API_KEY": "AIza..."
   }
   ```
   > `__keys` 是约定前缀，不会被 Claude Code 解析为 MCP 服务器。Python 脚本的 `_resolve_api_key()` 会读取此区。

3. **使用 AskUserQuestion 确认**：展示将要写入的内容，请用户确认：

```
将写入以下 Key 到 ${CLAUDE_PLUGIN_ROOT}/.mcp.json：

  mcpServers.openrouter.env.OPENROUTER_API_KEY = "sk-or-...{后4位}"
  __keys.BRAVE_API_KEY = "BSA...{后4位}"
  __keys.GOOGLE_API_KEY = "AIza...{后4位}"

Key 仅存储在插件配置中，不写入 shell 环境变量。
确认写入？
```

4. **写入**：用 Write 工具更新 `.mcp.json`
5. **生效方式**：
   - OpenRouter MCP 工具：需**重启 Claude Code**（MCP 服务器启动时读取 env）
   - Python 脚本 XV：**立即生效**（每次执行时读取 `.mcp.json`）

### Step 4: 验证与报告

输出最终状态报告：

```
## 外部服务配置完成

| 服务 | Key | 存储位置 | 用途 |
|------|-----|---------|------|
| OpenRouter | sk-or-...{后4位} | .mcp.json → openrouter.env | 跨模型交叉验证 |
| Brave Search | BSA...{后4位} | .mcp.json → __keys | 媒体搜索 |
| Google AI | AIza...{后4位} | .mcp.json → __keys | AI 生图/生视频/TTS |

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

API Key 服务:
  OpenRouter (MCP)    {就绪/未就绪}   product-design, dev-forge — XV 交叉验证
  OpenRouter (Script) {就绪/未就绪}   product-design 预置脚本 — XV 交叉验证
  Brave Search        {就绪/未就绪}   demo-forge — 媒体搜索
  Google AI           {就绪/未就绪}   demo-forge — AI 生图/生视频/TTS

内置:
  WebSearch           就绪           product-design, demo-forge — 搜索
  MCP 服务器          {已构建/未构建}  — OpenRouter MCP 通道

{若 Playwright 未就绪：安装: claude mcp add playwright -- npx @anthropic-ai/mcp-playwright}
{若有未配置的 API Key：运行 /setup 进行配置}
{若 MCP 已构建但工具不可用：需重启 Claude Code 加载 MCP 服务器}
{注: 所有外部能力均为可选，未配置不影响核心功能}
```

### 完整配置报告

```
## 外部服务配置完成

| 服务 | Key | 状态 | 用途 |
|------|-----|------|------|
| OpenRouter | sk-or-...{后4位} | {已写入 {path} / 已跳过 / 已配置} | 跨模型交叉验证 |
| Brave Search | BSA...{后4位} | {已写入 {path} / 已跳过 / 已配置} | 媒体搜索 |
| Google AI | AIza...{后4位} | {已写入 {path} / 已跳过 / 已配置} | AI 生图/生视频/TTS |

MCP 工具（需独立安装，不涉及 Key）:
  Playwright  {就绪/未就绪}  {若未就绪: claude mcp add playwright -- npx @anthropic-ai/mcp-playwright}
  Stitch UI   {就绪/未就绪}  {若未就绪: npx -y @_davideast/stitch-mcp init（完成 Google OAuth 认证）}

下一步：重启 Claude Code 后运行 /setup check 验证连接。
```

## 铁律（强制执行）

1. **Key 不落项目目录** — API Key 不得写入 `.allforai/` 或任何用户项目目录下的文件。只写入插件自身的 `.mcp.json`（插件安装目录，非项目目录）
2. **不自动写入** — 写入配置文件前必须展示内容并获得用户确认
3. **不阻塞主流程** — 本命令仅配置增强功能。未配置任何服务不影响技能的核心功能
4. **不污染 shell** — 不向 `~/.zshrc`、`~/.bashrc` 等 shell 配置文件写入 export 语句。Key 统一存储在插件 `.mcp.json` 中
