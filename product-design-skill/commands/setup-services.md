---
description: "配置外部服务 API Key：OpenRouter（跨模型交叉验证）+ Brave Search（媒体搜索+通用搜索增强）+ Google AI（生图/生视频/TTS）。检测状态、引导获取、验证连接、持久化。"
argument-hint: "[check|reset]"
allowed-tools: ["Read", "Write", "Grep", "Bash", "AskUserQuestion"]
---

> **升级提示**: 此命令是 `/setup-openrouter` 的超集，一站式配置所有外部服务。

# Setup Services — 配置外部服务

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数** → 完整引导：检测 → 获取 Key → 验证 → 持久化
- **`check`** → 仅检测当前状态（三个 Key 是否已配置、MCP 工具是否可用）
- **`reset`** → 清除已有配置，重新引导

## 背景说明

产品设计套件和演示锻造依赖三个外部服务，通过 API Key 启用增强功能：

| 服务 | 环境变量 | Key 格式 | 用途 |
|------|---------|---------|------|
| OpenRouter | `OPENROUTER_API_KEY` | `sk-or-...` | 跨模型交叉验证（XV）— 用 GPT/Gemini/DeepSeek 等交叉审视产出 |
| Brave Search | `BRAVE_API_KEY` | `BSA...` | 媒体搜索（图片/视频）+ 通用搜索增强（竞品分析、行业调研） |
| Google AI | `GOOGLE_API_KEY` | `AIza...` | AI 生图（Imagen 3）+ 生视频（Veo 2）+ TTS（Cloud TTS） |

**三个服务均为可选 — 没有 Key 时所有技能正常运行，只是跳过对应增强功能。**

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

检测三个服务的就绪状态：

#### 1a. OpenRouter

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

#### 1c. Google AI

1. **环境变量**：检查 `GOOGLE_API_KEY` 环境变量
   - 已设置 → Google AI 就绪
   - 未设置 → Google AI 未就绪

#### 状态表输出

展示三个服务的状态汇总表：

```
## 外部服务状态

| 服务 | Key | MCP 工具 | 状态 |
|------|-----|----------|------|
| OpenRouter | {已配置/未配置} | {可用/不可用} | {就绪/未就绪} |
| Brave Search | {已配置/未配置} | {可用/不可用} | {就绪/未就绪} |
| Google AI | {已配置/未配置} | — | {就绪/未就绪} |
```

**模式分支**：

- 三个服务均就绪：
  - 若模式为 `check` → 输出状态报告后结束
  - 若模式为无参数 → 询问「所有外部服务已配置完毕，是否需要重新配置？」
    - 否 → 结束
    - 是 → 继续 Step 2
  - 若模式为 `reset` → 继续 Step 2
- 至少一个服务未就绪：
  - 若模式为 `check` → 输出状态报告后结束，附带提示
  - 其他模式 → 继续 Step 2（仅引导未就绪的服务）

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

对 Step 2 中获取到的每个 Key 执行持久化（跳过的服务不处理）：

1. **检测用户 shell**：读取 `$SHELL` 环境变量判断是 bash 还是 zsh
2. **确定配置文件**：
   - zsh → `~/.zshrc`
   - bash → `~/.bashrc`
3. **检查是否已有旧配置**：用 Grep 检查配置文件中是否已有对应环境变量名
   - 已有 → 告知用户将替换旧值
4. **使用 AskUserQuestion 确认**：展示将要追加的所有内容和目标文件，请用户确认。一次性展示所有待写入的 Key（而非逐个确认），例如：

```
将写入以下内容到 ~/.zshrc：

export OPENROUTER_API_KEY="sk-or-..."
export BRAVE_API_KEY="BSA..."
export GOOGLE_API_KEY="AIza..."

确认写入？
```

5. **写入**：用 Bash 追加对应 `export` 行到配置文件
6. **立即生效**：提示用户需要**重启 Claude Code**（或新开终端后重新启动），因为 MCP 服务器在启动时读取环境变量

### Step 4: 验证与报告

输出最终状态报告：

```
## 外部服务配置完成

| 服务 | Key | 状态 | 用途 |
|------|-----|------|------|
| OpenRouter | sk-or-...{后4位} | 已写入 {path} | 跨模型交叉验证 |
| Brave Search | BSA...{后4位} | 已写入 {path} | 媒体搜索 + 通用搜索 |
| Google AI | AIza...{后4位} | 已写入 {path} | AI 生图/生视频/TTS |

下一步：重启 Claude Code 后运行 /setup-services check 验证连接。
```

对于跳过的服务，状态列显示「已跳过（可选）」。
对于之前已配置的服务，状态列显示「已配置（未修改）」。

## 报告输出要求（强制执行）

### check 模式报告

```
## 外部服务状态检测

| 服务 | Key | MCP 工具 | 状态 | 用途 |
|------|-----|----------|------|------|
| OpenRouter | {已配置/未配置} | {可用/不可用} | {就绪/未就绪} | 跨模型交叉验证 |
| Brave Search | {已配置/未配置} | {可用/不可用} | {就绪/未就绪} | 媒体搜索 + 通用搜索 |
| Google AI | {已配置/未配置} | — | {就绪/未就绪} | AI 生图/生视频/TTS |
| MCP 服务器 | — | — | {已构建/未构建} | OpenRouter MCP 通道 |

{若有未配置的服务：运行 /setup-services 进行配置}
{若 MCP 已构建但工具不可用：需重启 Claude Code 加载 MCP 服务器}
{注: 所有服务均为可选，未配置不影响核心功能}
```

### 完整配置报告

```
## 外部服务配置完成

| 服务 | Key | 状态 | 用途 |
|------|-----|------|------|
| OpenRouter | sk-or-...{后4位} | {已写入 {path} / 已跳过 / 已配置} | 跨模型交叉验证 |
| Brave Search | BSA...{后4位} | {已写入 {path} / 已跳过 / 已配置} | 媒体搜索 + 通用搜索 |
| Google AI | AIza...{后4位} | {已写入 {path} / 已跳过 / 已配置} | AI 生图/生视频/TTS |

下一步：重启 Claude Code 后运行 /setup-services check 验证连接。
```

## 铁律（强制执行）

1. **Key 不落日志** — API Key 不得写入 `.allforai/` 或任何项目目录下的文件。只写入用户 shell 配置文件（`~/.zshrc` 或 `~/.bashrc`）
2. **不自动写入** — 写入 shell 配置文件前必须展示内容并获得用户确认
3. **不阻塞主流程** — 本命令仅配置增强功能。未配置任何服务不影响技能的核心功能
