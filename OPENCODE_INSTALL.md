# OpenCode Native 安装说明

## 当前状态

仓库现在提供独立的 `opencode-native/` 层：

- 不改动原始 `*-skill/` Claude 插件目录
- OpenCode 通过 `opencode-native/*/skills` 和
  `opencode-native/*/commands` 加载
- 原始插件目录仍是 workflow、docs、scripts 的 source of truth

## 推荐安装

远程安装：

```bash
curl -fsSL https://raw.githubusercontent.com/allforai/myskills/main/install-remote.sh | bash
```

本地开发安装：

```bash
cd /path/to/myskills
./install-opencode.sh
```

安装后，OpenCode 会注册以下 native 插件：

- `product-design`
- `dev-forge`
- `demo-forge`
- `code-tuner`
- `ui-forge`
- `code-replicate`

## 项目内配置

在目标项目中创建 `.opencode/config.json`：

```json
{
  "$schema": "https://opencode.ai/config.schema.json",
  "skills": {
    "inherit": true
  },
  "mcp": {
    "inherit": true
  }
}
```

或直接复制模板：

```bash
cp ~/.opencode/skills/myskills/.opencode.template your-project/.opencode/config.json
```

## Native 层规则

- `AskUserQuestion` 视为行为指引；只有真正阻塞时才问用户
- `${CLAUDE_PLUGIN_ROOT}` 通过 wrapper 相对路径适配
- `allowed-tools`、`$ARGUMENTS` 视为说明性元数据
- MCP / Playwright / 外部服务流程按降级规则运行，不强行宣称完全等价

## 相关文档

- `opencode-native/README.md`
- `opencode-native/SKILL.md`
- `opencode-native/inventory.md`
- `opencode-native/plugin-matrix.md`
- `opencode-native/runtime-gaps.md`
- `opencode-native/compatibility-guide.md`
