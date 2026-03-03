---
description: "配置 OpenRouter API Key，启用跨模型交叉验证（XV）。检测当前状态、引导获取 Key、验证连接、持久化到 shell 配置。"
argument-hint: "[check|reset]"
allowed-tools: ["Read", "Bash", "AskUserQuestion"]
---

# Setup OpenRouter — 配置跨模型交叉验证

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 模式路由

- **无参数** → 完整引导：检测 → 获取 Key → 验证 → 持久化
- **`check`** → 仅检测当前状态（Key 是否已配置、MCP 工具是否可用）
- **`reset`** → 清除已有配置，重新引导

## 背景说明

产品设计套件的 8 个技能均支持**跨模型交叉验证（XV）**— 用不同 AI 模型（GPT/Gemini/DeepSeek 等）交叉审视产出，弥补单一模型的知识偏差和推理盲区。

XV 通过 OpenRouter 统一调用多家模型。需要一个 OpenRouter API Key 才能启用。**XV 完全可选 — 没有 Key 时所有技能正常运行，只是跳过交叉验证。**

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

检测两个 XV 通道：

1. **MCP 工具通道**：检查 `mcp__plugin_product-design_openrouter__detect_region` 工具是否可用
   - 可用 → 调用 `mcp__plugin_product-design_openrouter__detect_region`，展示模型路由策略。MCP XV 就绪
   - 不可用 → MCP XV 未就绪（可能需要重启 Claude Code）

2. **脚本通道**：检查 `OPENROUTER_API_KEY` 环境变量
   - 已设置 → 脚本 XV 就绪（预置 Python 脚本直连 OpenRouter API）
   - 未设置 → 脚本 XV 未就绪

**模式分支**：

- 两个通道均就绪：
  - 若模式为 `check` → 输出状态报告后结束
  - 若模式为无参数 → 询问「OpenRouter 已配置完毕，是否需要重新配置？」
    - 否 → 结束
    - 是 → 继续 Step 2
  - 若模式为 `reset` → 继续 Step 2
- 至少一个通道未就绪：
  - 若模式为 `check` → 输出状态报告后结束，附带提示
  - 其他模式 → 继续 Step 2

### Step 2: 引导获取 Key

使用 AskUserQuestion 询问：

**「你是否已有 OpenRouter API Key？」**

选项：
- **已有 Key** — 我已经有 OpenRouter API Key，直接配置
- **需要注册** — 带我去获取一个

#### 选择「需要注册」时：

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

#### 选择「已有 Key」时：

使用 AskUserQuestion 询问「请粘贴你的 OpenRouter API Key」。

### Step 3: 持久化 Key

获取到 Key 后：

1. **检测用户 shell**：读取 `$SHELL` 环境变量判断是 bash 还是 zsh
2. **确定配置文件**：
   - zsh → `~/.zshrc`
   - bash → `~/.bashrc`
3. **检查是否已有旧配置**：用 Grep 检查配置文件中是否已有 `OPENROUTER_API_KEY`
   - 已有 → 告知用户将替换旧值
4. **使用 AskUserQuestion 确认**：展示将要追加的内容和目标文件，请用户确认
5. **写入**：用 Bash 追加 `export OPENROUTER_API_KEY="sk-or-..."` 到对应配置文件
6. **立即生效**：提示用户需要**重启 Claude Code**（或新开终端后重新启动），因为 MCP 服务器在启动时读取环境变量

### Step 4: 验证连接

提示用户：

```
配置已写入 {配置文件路径}。

当前状态：
- 脚本 XV: {可用 — Key 已在环境变量中 / 需重启 — Key 刚写入 shell 配置}
- MCP XV: {需重启 Claude Code 以加载新 Key}

下一步：
1. 退出当前 Claude Code 会话
2. 重新启动 Claude Code
3. 运行 /setup-openrouter check 验证连接

Key 生效后，所有 8 个产品设计技能将自动启用跨模型交叉验证（XV）。
无需修改任何技能配置 — XV 会在每个阶段自动检测工具可用性。
```

## 报告输出要求（强制执行）

### check 模式报告

```
## OpenRouter 状态检测

| 项目 | 状态 |
|------|------|
| MCP 服务器构建 | {已构建 / 未构建} |
| MCP 工具 | {可用 / 不可用（需重启 Claude Code）} |
| API Key | {已配置 / 未配置} |
| 脚本 XV | {已启用 / 未启用} |
| MCP XV | {已启用 / 未启用} |

{注: 预置脚本直连 OpenRouter API，不依赖 MCP。两个通道独立工作。}
{若 MCP 未构建：运行 /setup-openrouter 自动构建}
{若 Key 未配置：运行 /setup-openrouter 进行配置}
{若 MCP 已构建但工具不可用：需重启 Claude Code 加载 MCP 服务器}
```

### 完整配置报告

```
## OpenRouter 配置完成

| 项目 | 结果 |
|------|------|
| API Key | 已写入 {配置文件路径} |
| Key 前缀 | sk-or-...{后4位} |
| 生效方式 | 重启 Claude Code |

下一步：重启 Claude Code 后运行 /setup-openrouter check 验证连接。
```

## 铁律（强制执行）

1. **Key 不落日志** — API Key 不得写入 `.allforai/` 或任何项目目录下的文件。只写入用户 shell 配置文件（`~/.zshrc` 或 `~/.bashrc`）
2. **不自动写入** — 写入 shell 配置文件前必须展示内容并获得用户确认
3. **不阻塞主流程** — 本命令仅配置 XV 增强。未配置 OpenRouter 不影响任何技能的核心功能
