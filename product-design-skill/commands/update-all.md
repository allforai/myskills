---
name: update-all
description: >
  Use when the user says "update-all", "update skills", "update plugins",
  "更新插件", "更新技能", "升级全部", "update everything".
  Updates all installed Claude Code plugins, MCP servers, and OpenCode skills.
argument-hint: "[--dry-run]"
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
---

# Update All — 全量更新已安装的插件、MCP 服务和技能

用户请求: $ARGUMENTS

## 执行流程

按以下顺序执行，每步输出结果：

### Step 1: 收集当前状态

```bash
# 1a. 读取已安装插件列表
cat ~/.claude/plugins/installed_plugins.json

# 1b. 读取 MCP 服务配置
cat ~/.claude/settings.json

# 1c. 读取 marketplace 列表
cat ~/.claude/plugins/known_marketplaces.json
```

解析出三组数据：
- **Marketplace 插件**: 从 `installed_plugins.json` 提取所有 `name@marketplace` 及当前版本
- **MCP 服务器**: 从 `settings.json` 的 `mcpServers` 提取名称和路径
- **OpenCode 技能**: 检查 `~/.config/opencode/skills.json` 是否存在

### Step 2: 输出当前状态仪表板

以表格形式输出：

```
╔══════════════════════════════════════════════════════════════╗
║  Installed Components                                       ║
╚══════════════════════════════════════════════════════════════╝

Marketplace Plugins:
  ✓ product-design@myskills              v4.5.1
  ✓ dev-forge@myskills                   v2.9.0
  ✓ superpowers@claude-plugins-official   v4.3.1
  ...

MCP Servers:
  ✓ ai-gateway    node .../dist/index.js

OpenCode:
  ✓ skills.json exists
```

如果用户传了 `--dry-run`，到此停止，不执行更新。

### Step 3: 更新 Marketplace 插件

对每个已安装的插件执行：

```bash
claude plugin update <plugin-name>@<marketplace>
```

**执行策略**：
- 按 marketplace 分组，先更新 `myskills`（本地仓库），再更新 `claude-plugins-official`（远程）
- 对 myskills 插件：先在插件根目录执行 `git pull --ff-only`（如果是 git 仓库）
- 每个插件更新后输出结果（成功/失败/已是最新）
- 失败不中断，继续下一个

### Step 4: 重建 MCP 服务器

对 `settings.json` 中的每个 MCP 服务器：

1. 检查其路径是否存在
2. 如果是 Node.js 项目（有 package.json）：
   ```bash
   cd <server-dir> && npm install && npm run build
   ```
3. 如果是 Python 项目（有 requirements.txt）：
   ```bash
   cd <server-dir> && pip install -r requirements.txt
   ```
4. 输出重建结果

### Step 5: 更新 OpenCode 技能（如果存在）

检查 myskills 仓库根目录是否有 `install-opencode.sh`：

```bash
# 检测插件根目录
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
REPO_ROOT="$(dirname "$PLUGIN_ROOT")"

if [ -f "$REPO_ROOT/install-opencode.sh" ]; then
  bash "$REPO_ROOT/install-opencode.sh"
fi
```

### Step 6: 输出更新汇总

```
╔══════════════════════════════════════════════════════════════╗
║  Update Summary                                             ║
╚══════════════════════════════════════════════════════════════╝

Plugins:
  ✓ product-design@myskills     4.5.0 → 4.5.1
  ✓ superpowers@official         4.3.1 (already latest)
  ✗ ralph-loop@official          update failed: ...
  ...

MCP Servers:
  ✓ ai-gateway                   rebuilt OK

OpenCode:
  ✓ skills.json updated

⚠ 需要重启 Claude Code 以应用更新。
```

## 注意事项

- 更新过程中如果遇到错误，**不要中断**，继续处理其他组件
- `claude plugin update` 更新后需要**重启 Claude Code** 才生效，提醒用户
- MCP 服务器重建后需要重启才能重新加载
- 如果 git pull 有冲突，跳过并提示用户手动解决
- 不修改 `settings.json` 中的 MCP 配置（只重建，不改路径）
