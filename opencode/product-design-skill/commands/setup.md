---
description: "检测和配置所有外部能力：Playwright（UI 自动化）+ OpenRouter（跨模型 XV）+ Brave Search（媒体搜索）+ Google AI（生图/生视频）+ Stitch UI（视觉稿）。一站式状态仪表板 + 引导配置 + 一键更新所有插件/MCP/技能。"
---

# Setup — 外部能力管理

（根据用户请求的模式/参数执行）

## 插件根目录

所有文档路径基于技能根目录（相对路径）

## 模式路由

- **无参数** → 完整引导：检测 → 获取 Key → 验证 → 持久化
- **`check`** → 仅检测当前状态（全部外部能力的可用性仪表板）
- **`reset`** → 清除已有配置，重新引导
- **`update`** → 更新所有已安装的插件、MCP 服务器和技能（见 Step 5）

## 外部能力总览

插件套件依赖以下外部能力，分为三类：

### MCP 工具（需安装插件）

| 能力 | 探测方式 | 使用插件 | 用途 |
|------|---------|---------|------|
| Playwright | `mcp__playwright__browser_navigate` 或 `mcp__playwright__browser_navigate` 可用性（任一可用即就绪） | demo-forge, dev-forge, deadhunt | UI 自动化：验证、E2E 测试、死链扫描 |
| Stitch UI | `mcp__stitch__create_project` 可用性 | product-design | 高保真 UI 视觉稿生成（Google Stitch） |

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
   ls ./mcp-ai-gateway/dist/index.js
   ```

2. **不存在或文件 < 100 bytes** → 需要构建：
   - 检查 node_modules 是否存在：`ls ./mcp-ai-gateway/node_modules/`
   - 不存在 → 运行 `cd ./mcp-ai-gateway && npm install`
   - 运行 `cd ./mcp-ai-gateway && npm run build`
   - 验证 `dist/index.js` 已生成
   - 成功 → 报告「MCP 服务器构建成功」
   - 失败 → 报告错误，提示「MCP 构建失败，XV 的 MCP 工具不可用，但预置脚本 XV 不受影响」，继续执行

3. **已存在** → 报告「MCP 服务器已构建」，继续

### Step 1: 检测当前状态

检测所有外部能力的就绪状态：

#### 工具可用性检测方法（重要）

Claude Code 使用**延迟加载（deferred tools）**机制：MCP 工具可能已注册但未激活到当前上下文。检测工具是否可用需要**同时检查两个来源**：

1. **当前激活工具列表** — 已加载到上下文中的工具，可直接调用
2. **`<available-deferred-tools>` 列表** — 会话开始时系统消息中列出的延迟加载工具名称

**判定规则：工具名出现在任一列表中即为「可用」。** 不要因为工具仅在 deferred 列表中就误报为「未安装」。

#### 1a. Playwright MCP

1. **检查 MCP 工具**：在激活工具列表和 `<available-deferred-tools>` 中查找 `mcp__playwright__browser_navigate` 或 `mcp__playwright__browser_navigate`（任一前缀、任一列表匹配即通过）
   - 可用 → **✅ 就绪**
   - 不可用 → **❌ 未安装**（提示安装 Playwright MCP，见 Step 1.5a）

#### 1b. OpenRouter

1. **MCP 工具通道**：在激活工具列表和 `<available-deferred-tools>` 中查找 `mcp__openrouter__ask_model`
   - 可用 → MCP XV 就绪
   - 不可用 → MCP XV 未就绪（可能需要重启 Claude Code）

2. **脚本通道**：检查 `OPENROUTER_API_KEY` 环境变量
   - 已设置 → 脚本 XV 就绪
   - 未设置 → 脚本 XV 未就绪

#### 1c. Brave Search

1. **MCP 工具通道**：在激活工具列表和 `<available-deferred-tools>` 中查找 `mcp__openrouter__brave_web_search`
   - 可用 → Brave MCP 就绪（ai-gateway 已加载且 BRAVE_API_KEY 已配置）
   - 不可用 → Brave MCP 未就绪

2. **脚本通道**：检查 `BRAVE_API_KEY` 环境变量
   - 已设置 → Brave Key 就绪
   - 未设置 → Brave 未就绪

#### 1d. Google AI

1. **MCP 工具通道**：在激活工具列表和 `<available-deferred-tools>` 中查找 `mcp__openrouter__generate_image`
   - 可用 → Google AI MCP 就绪（ai-gateway 已加载且 GOOGLE_API_KEY 已配置）
   - 不可用 → Google AI MCP 未就绪

2. **脚本通道**：检查 `GOOGLE_API_KEY` 环境变量
   - 已设置 → Google AI Key 就绪
   - 未设置 → Google AI 未就绪

#### 1e. fal.ai (FLUX + Kling)

1. **MCP 工具通道**：在激活工具列表和 `<available-deferred-tools>` 中查找 `mcp__openrouter__flux_generate_image`
   - 可用 → fal.ai MCP 就绪
   - 不可用 → fal.ai MCP 未就绪

2. **脚本通道**：检查 `FAL_KEY` 环境变量
   - 已设置 → fal.ai Key 就绪
   - 未设置 → fal.ai 未就绪

#### 1f. Stitch UI

1. **检查 MCP 工具**：在激活工具列表和 `<available-deferred-tools>` 中查找 `mcp__stitch__create_project` 或 `mcp__stitch__create_project`（任一前缀、任一列表匹配即通过）
   - 可用 → **✅ 就绪**
   - 不可用 → 检查 `~/.stitch-mcp/config/application_default_credentials.json` 是否存在
     - 凭证存在 → 检查是否包含 `quota_project_id` 字段：
       - 有 → **⚠️ OAuth 已完成但 MCP 未加载**（可能需要重启 Claude Code）
       - 无 → **⚠️ OAuth 已完成但缺少 quota project**（需运行 Step 1.5b 补充配置）
     - 凭证不存在 → **❌ 未配置**（需先完成 OAuth 和 quota project 配置）

#### 状态仪表板输出

展示所有外部能力的状态汇总：

```
## 外部能力状态

| 能力 | 类型 | 状态 | 使用插件 | 用途 |
|------|------|------|---------|------|
| Playwright | 用户级 MCP | {✅ 就绪 / ❌ 未安装} | demo-forge, dev-forge, deadhunt | UI 自动化 |
| Stitch UI | 用户级 MCP | {✅ 就绪 / ⚠️ 缺 OAuth / ❌ 未安装} | product-design | UI 视觉稿 |
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

执行安装命令：

```bash
claude mcp add -s user playwright -- npx -y @playwright/mcp@latest
```

安装成功后提示：

```
Playwright MCP 已注册到用户级配置。需重启 Claude Code 后生效。
```

#### 1.5b. Stitch UI（若未就绪）

使用 向用户询问：

**「Stitch UI 未就绪，用于生成高保真 UI 视觉稿。是否安装？」**

选项：
- **安装** — 注册 MCP + 引导 OAuth
- **跳过** — 暂不安装（ui-design 将只生成文字规格，跳过视觉稿）

##### 选择「安装」时：

**Step 1: 安装 stitch-mcp**

检查 `stitch-mcp` 是否已全局安装：
```bash
which stitch-mcp
```
- 已安装 → 跳过
- 未安装 → 安装：`npm install -g @_davideast/stitch-mcp`

> **注意**: 不要用 `npx -y @_davideast/stitch-mcp proxy` 启动 Stitch MCP。npx 启动太慢会导致 MCP 握手超时。必须全局安装后用 `stitch-mcp proxy` 直接启动。

**Step 2: 检查 OAuth 凭证**

检查 `~/.stitch-mcp/config/application_default_credentials.json` 是否存在：
- 存在 → 继续 Step 3
- 不存在 → 使用内置 Python 脚本完成 OAuth：

```bash
python3 ../../shared/scripts/product-design/stitch_oauth.py
```

脚本会自动打开浏览器完成 Google OAuth。如果浏览器无法打开（如远程服务器），使用手动模式：

```bash
python3 ../../shared/scripts/product-design/stitch_oauth.py --manual
```

手动模式会打印一个 URL，用户在任意浏览器打开授权后，将验证码粘贴回终端。

OAuth 凭证长期有效（以年计），只需做一次。

**Step 3: 配置 quota project**

读取 `~/.stitch-mcp/config/application_default_credentials.json`，检查是否包含 `quota_project_id` 字段：
- 已有 → 跳过
- 缺失 → 需要配置。使用 ADC 的 refresh_token 调用 Google API 列出用户的 GCP 项目：

```python
# 用 refresh_token 换取 access_token，然后调用 cloudresourcemanager API
GET https://cloudresourcemanager.googleapis.com/v1/projects?pageSize=10
Authorization: Bearer {access_token}
```

展示项目列表，让用户选择一个（优先推荐名称含 "Gemini" 或 "AI" 的项目）。然后将选中的 project ID 写入 ADC 文件的 `quota_project_id` 字段。

如果用户没有任何 GCP 项目，提示：
```
需要一个 Google Cloud 项目作为 Stitch API 的计费项目。
1. 访问 https://console.cloud.google.com/projectcreate
2. 创建一个项目（名称随意）
3. 重新运行 /setup
```

**Step 4: 确认 MCP 已在插件 .mcp.json 中注册**

检查 `./.mcp.json` 是否包含 `stitch` 服务器配置：
- 已有 → 跳过
- 缺失 → 添加到 `.mcp.json`：
```json
"stitch": {
  "command": "stitch-mcp",
  "args": ["proxy"],
  "env": {
    "GOOGLE_CLOUD_PROJECT": "{选中的 project ID}"
  }
}
```

提示重启 Claude Code 后生效。

### Step 2: 引导获取 Key

按顺序引导每个未配置的服务。**已配置的服务跳过（除非 reset 模式）。**

#### 2a. OpenRouter

使用 向用户询问：

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

然后使用 向用户询问「请粘贴你的 OpenRouter API Key」（提供"其他"输入框让用户粘贴）。

##### 选择「已有 Key」时：

使用 向用户询问「请粘贴你的 OpenRouter API Key」。

##### 选择「跳过」时：

记录跳过，继续下一个服务。

#### 2b. Brave Search

使用 向用户询问：

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

然后使用 向用户询问「请粘贴你的 Brave Search API Key」（提供"其他"输入框让用户粘贴）。

##### 选择「已有 Key」时：

使用 向用户询问「请粘贴你的 Brave Search API Key」。

##### 选择「跳过」时：

记录跳过，继续下一个服务。

#### 2c. Google AI

使用 向用户询问：

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

然后使用 向用户询问「请粘贴你的 Google AI API Key」（提供"其他"输入框让用户粘贴）。

##### 选择「已有 Key」时：

使用 向用户询问「请粘贴你的 Google AI API Key」。

##### 选择「跳过」时：

记录跳过，继续下一个服务。

#### 2d. fal.ai (FLUX 2 Pro + Kling)

使用 向用户询问：

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

然后使用 向用户询问「请粘贴你的 fal.ai Key」（提供"其他"输入框让用户粘贴）。

##### 选择「已有 Key」时：

使用 向用户询问「请粘贴你的 fal.ai Key」。

##### 选择「跳过」时：

记录跳过。

### Step 3: 持久化 Key

对 Step 2 中获取到的每个 Key 执行持久化（跳过的服务不处理）。

**存储位置**：用户 shell 配置文件（`~/.zshrc` 或 `~/.bashrc`）的 export 语句。

**原理**：
- MCP 工具路径：`.mcp.json` 的 env 块使用 `${VAR}` 引用，Claude Code 启动 MCP 服务器时从 shell 环境变量注入
- Python 脚本路径：`_common.py` 的 `_resolve_api_key()` 直接读环境变量
- 两条路径统一从环境变量读取，Key 不写入任何 JSON 文件，避免被插件更新/重装覆盖

**操作流程**：

1. **检测 shell 类型**：
   ```bash
   echo $SHELL
   ```
   - `/bin/zsh` → 配置文件 `~/.zshrc`
   - `/bin/bash` → 配置文件 `~/.bashrc`

2. **生成 export 语句**：

   ```bash
   # myskills API Keys
   export OPENROUTER_API_KEY="sk-or-..."
   export GOOGLE_API_KEY="AIza..."
   export FAL_KEY="..."
   export BRAVE_API_KEY="BSA..."
   ```

3. **使用 向用户确认**：展示将要追加的内容，请用户确认：

```
将追加以下 export 到 {~/.zshrc 或 ~/.bashrc}：

  export OPENROUTER_API_KEY="sk-or-...{后4位}"
  export GOOGLE_API_KEY="AIza...{后4位}"
  export FAL_KEY="...{后4位}"
  export BRAVE_API_KEY="BSA...{后4位}"

确认写入？
```

4. **写入**：追加到 shell 配置文件（检查是否已有同名 export，有则替换而非重复追加）
5. **生效方式**：
   - 当前终端：运行 `source ~/.zshrc`（或 `~/.bashrc`）立即生效
   - 新终端：自动生效
   - MCP 服务器：需**重启 Claude Code**（重新加载环境变量）

### Step 4: 验证与报告

输出最终状态报告：

```
## 外部服务配置完成

| 服务 | Key | 存储位置 | 用途 |
|------|-----|---------|------|
| OpenRouter | sk-or-...{后4位} | shell 环境变量 | XV + GPT-5/Gemini 生图 |
| Google AI | AIza...{后4位} | shell 环境变量 | Imagen 4 + Veo 3.1 + TTS |
| fal.ai | ...{后4位} | shell 环境变量 | FLUX 2 Pro + Kling 生视频 |
| Brave Search | BSA...{后4位} | shell 环境变量 | 媒体搜索 |

下一步：运行 source ~/.zshrc 后重启 Claude Code，然后 /setup check 验证连接。
```

对于跳过的服务，状态列显示「已跳过（可选）」。
对于之前已配置的服务，状态列显示「已配置（未修改）」。

## 报告输出要求（强制执行）

### check 模式报告

```
## 外部能力状态

MCP 工具（用户级 claude mcp add -s user）:
  Playwright       {✅ 就绪 / ❌ 未安装}   demo-forge, dev-forge, deadhunt — UI 自动化
  Stitch UI        {✅ 就绪 / ⚠️ MCP 已注册但缺 OAuth / ❌ 未安装}   product-design — UI 视觉稿（Google Stitch）

AI Gateway（统一 MCP 服务器）:
  OpenRouter       {就绪/未就绪}   product-design, dev-forge — XV + GPT-5/Gemini 生图
  Google AI        {就绪/未就绪}   demo-forge — Imagen 4 + Veo 3.1 + TTS
  fal.ai           {就绪/未就绪}   demo-forge — FLUX 2 Pro + Kling 生视频
  Brave Search     {就绪/未就绪}   demo-forge — 媒体搜索（网页/图片/视频）

API Key（环境变量）:
  OpenRouter Key   {就绪/未就绪}   product-design 预置脚本 — XV 交叉验证
  Google AI Key    {就绪/未就绪}   demo-forge 预置脚本 — AI 生图/生视频/TTS
  Brave Key        {就绪/未就绪}   demo-forge 预置脚本 — 媒体搜索
  fal.ai Key       {就绪/未就绪}   demo-forge 预置脚本 — FLUX 2 Pro + Kling

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
| OpenRouter | sk-or-...{后4位} | {已写入 shell / 已跳过 / 已配置} | XV + GPT-5/Gemini 生图 |
| Google AI | AIza...{后4位} | {已写入 shell / 已跳过 / 已配置} | Imagen 4 + Veo 3.1 + TTS |
| fal.ai | ...{后4位} | {已写入 shell / 已跳过 / 已配置} | FLUX 2 Pro + Kling 生视频 |
| Brave Search | BSA...{后4位} | {已写入 shell / 已跳过 / 已配置} | 媒体搜索 |

MCP 工具（Step 1.5 已引导安装）:
  Playwright     {已安装/已跳过/之前已就绪}  demo-forge, dev-forge, deadhunt — UI 自动化
  Stitch UI      {已安装/已跳过/之前已就绪}  product-design — UI 视觉稿

下一步：重启 Claude Code 后运行 /setup check 验证连接。
```

### Step 5: 更新已安装的插件和服务（仅 `update` 模式）

`update` 模式跳过 Step 1-4，直接执行更新流程。

#### 5a. 更新 Claude Code 插件

1. **同步 marketplace git 缓存**（关键步骤）：

   Claude Code 在 `~/.claude/plugins/marketplaces/` 下为每个 marketplace 维护独立的 git clone。`claude plugin update` 依赖此缓存，若缓存过旧则拉不到新版本。

   ```bash
   # 遍历所有 marketplace 缓存目录，逐个 git pull
   for dir in ~/.claude/plugins/marketplaces/*/; do
     if [ -d "$dir/.git" ]; then
       echo "🔄 同步 marketplace 缓存: $(basename $dir)"
       git -C "$dir" pull origin main 2>/dev/null || git -C "$dir" pull 2>/dev/null || echo "⚠️ $(basename $dir) 同步失败，跳过"
     fi
   done
   ```

2. **读取已安装插件列表**：
   ```bash
   cat ~/.claude/plugins/installed_plugins.json
   ```

3. **解析每个插件**，提取 `scope`（marketplace 名）和插件名：
   - 每条记录有 `scope`（如 `myskills`）、`installPath`（安装目录）、`version`（当前版本）
   - 从 `installPath` 的末级目录名提取插件名

4. **逐个更新**：
   ```bash
   claude plugin update <plugin-name>@<scope>
   ```
   例如：`claude plugin update product-design@myskills`

5. **MCP 配置保护**：对每个更新的插件，对比更新前后的 `.mcp.json`：
   - 更新前：读取 `<installPath>/.mcp.json` 保存为 `old_mcp`
   - 更新后：读取新的 `.mcp.json` 保存为 `new_mcp`
   - 如果 `old_mcp` 中存在的 server 条目在 `new_mcp` 中消失 → **警告用户并自动合并缺失条目**
   - 输出：`⚠️ <plugin>: ai-gateway 条目在新版中缺失，已自动恢复`

6. **汇总报告**：列出每个插件的更新前后版本

#### 5b. 重建 MCP 服务器

1. **读取 MCP 配置**：
   ```bash
   cat ~/.claude/settings.json
   ```
   提取 `mcpServers` 中的所有服务器

2. **对每个 node 类型的 MCP 服务器**，检查其 `args` 中的入口文件路径，找到对应的 `package.json` 所在目录

3. **重建**：
   ```bash
   cd <mcp-server-dir> && npm install && npm run build
   ```

4. **报告构建结果**

#### 5c. 更新 OpenCode 技能（若已配置）

1. **检查 OpenCode 技能仓库**：
   ```bash
   ls ~/.opencode/skills/myskills/update-skills.sh
   ```

2. **存在则执行更新脚本**：
   ```bash
   ~/.opencode/skills/myskills/update-skills.sh
   ```

3. **不存在则跳过**（用户未安装 OpenCode 技能）

#### 更新报告

```
## 更新完成

Claude Code 插件:
  product-design    4.5.0 → 4.5.1  ✅
  dev-forge         2.6.0 → 2.7.0  ✅
  deadhunt          2.1.0 → 2.1.0  （无更新）
  ...

MCP 服务器:
  ai-gateway        ✅ 重建成功

OpenCode 技能:
  {已更新 / 未安装，跳过}

⚠️ 插件或 MCP 服务器有更新时，必须重启 Claude Code 才能生效。
   请退出当前会话并重新启动 Claude Code。
```

**重启提示规则**：
- 任何插件版本发生变化 → 必须提示重启
- MCP 服务器重建成功 → 必须提示重启
- 所有插件均无更新且无 MCP 重建 → 不提示重启
- 提示文案必须包含「请退出当前会话并重新启动 Claude Code」，不能只说"需要重启"

## 铁律（强制执行）

1. **Key 不落项目目录** — API Key 不得写入 `.allforai/` 或任何用户项目目录下的文件
2. **Key 不写入 JSON** — API Key 不写入 `.mcp.json` 或任何 JSON 配置文件。`.mcp.json` 仅使用 `${VAR}` 引用环境变量
3. **不自动写入** — 写入 shell 配置前必须展示内容并获得用户确认
4. **不阻塞主流程** — 本命令仅配置增强功能。未配置任何服务不影响技能的核心功能
