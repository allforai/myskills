---
description: 在当前项目打开、关闭或查看 Jev 选模型（on | off | status）
argument-hint: on | off | status
disable-model-invocation: true
allowed-tools: Bash(python3:*)
---

参数是 `$ARGUMENTS`。它必须是 `on`、`off`、`status` 之一；不是的话，不运行任何命令，告诉用户用法：`/jev on | off | status`。

是的话运行：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jev_ctl.py" $ARGUMENTS --cwd "$PWD"
```

把输出原样告诉用户，不加解释。
