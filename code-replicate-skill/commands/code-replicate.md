---
description: "代码复刻：逆向工程已有代码库 → 生成 allforai 产物 → 交还 dev-forge 流水线。模式: interface / functional / architecture / exact"
argument-hint: "[mode: interface|functional|architecture|exact] [path]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion", "Agent", "WebSearch"]
---

# Code Replicate — 代码复刻

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 执行方式

用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/skills/code-replicate.md`，按其完整工作流执行。

从 `$ARGUMENTS` 解析 `mode` 和 `path` 参数（如已提供），预填到 Step 0 Preflight。

## 快速参考

```
/code-replicate                          # 交互式选择信度等级
/code-replicate interface ./src          # 仅复刻 API 合约
/code-replicate functional ./src         # 复刻业务行为
/code-replicate architecture ./src       # 复刻模块结构
/code-replicate exact ./src              # 百分百复刻（含 bug）
```

## 信度等级速查

| 等级 | 适用场景 |
|------|---------|
| `interface` | 后端重写，前端不动；API 兼容迁移 |
| `functional` | 技术栈迁移，保留业务逻辑（**推荐默认**） |
| `architecture` | 大规模重构，保持架构决策 |
| `exact` | 行为零容忍回归；监管合规（⚠️ 耗时最长） |

## 后续步骤

复刻分析完成后，继续 dev-forge 流水线：

```
/design-to-spec   ← 生成目标技术栈实现规格
/task-execute     ← 逐任务生成代码
```
