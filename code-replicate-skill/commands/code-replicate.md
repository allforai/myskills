---
description: "代码复刻：逆向工程已有代码库 → 生成 allforai 产物 → 交还 dev-forge 流水线。模式: interface / functional / architecture / exact"
argument-hint: "[mode] <path-or-url> [--type backend|frontend|fullstack|module] [--scope full|modules|feature]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion", "Agent", "WebSearch"]
---

# Code Replicate — 代码复刻

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 执行方式

从 `$ARGUMENTS` 解析参数：
- `mode`（interface/functional/architecture/exact）→ 预填信度等级
- `path` 或 git URL → 预填源码地址
- `--type backend|frontend` → 指定项目类型

### 参数缺失引导

当 `$ARGUMENTS` 为空或缺少必要参数时，用 AskUserQuestion 逐步引导：

1. **源码地址**（若缺失）：「要复刻的源码在哪里？」选项：当前目录 `.` / 输入本地路径 / 输入 Git URL
2. **信度等级**（若缺失）：「需要什么级别的复刻？」选项：interface（仅 API 合约）/ functional（业务逻辑，推荐）/ architecture（含架构分析）/ exact（百分百复刻含 bug）
3. **项目类型**（若缺失且无法自动检测）：「这是什么类型的项目？」选项：backend / frontend / fullstack / 自动检测（推荐）

收集完毕后，按正常流程继续。

### 项目类型分发

根据 `--type` 参数决定加载哪个技能文件，用 Read 加载后按其完整工作流执行：

1. **`--type backend`** → 加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/cr-backend.md`
2. **`--type frontend`** → 加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/cr-frontend.md`
3. **`--type fullstack`** → 加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/cr-fullstack.md`
4. **`--type module`** → 加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/cr-module.md`（需 `--module` 参数）
5. **未指定 `--type`** → 默认加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/cr-backend.md`（Phase 2 技术栈识别时，若发现项目为前端项目，自动切换到 cr-frontend）

## 快速参考

```
/code-replicate                                      # 交互式（默认后端）
/code-replicate functional ./src                     # 后端复刻业务行为
/code-replicate functional ./src --type frontend     # 前端复刻业务行为
/code-replicate functional ./src --scope "用户注册和登录"  # 只复刻某个功能
/code-replicate functional ./src --scope "src/user,src/auth" # 只复刻指定模块
/code-replicate exact ./src                          # 百分百复刻（含 bug）
/code-replicate functional https://github.com/org/repo.git  # 远程仓库
/code-replicate functional https://github.com/org/repo#v2.0  # 指定 tag/分支
/code-replicate functional git@github.com:org/repo.git       # SSH 地址
/code-replicate functional ./project --type fullstack         # 全栈复刻（前后端交叉验证）
/code-replicate functional ./src --type module --module src/modules/user  # 模块复刻
```

## 信度等级速查

| 等级 | 适用场景 |
|------|---------|
| `interface` | 后端重写，前端不动；API 兼容迁移 |
| `functional` | 技术栈迁移，保留业务逻辑（**推荐默认**） |
| `architecture` | 大规模重构，保持架构决策 |
| `exact` | 行为零容忍回归；监管合规（⚠️ 耗时最长） |

## 专用命令

| 命令 | 说明 |
|------|------|
| `/cr-backend` | 固定后端模式 |
| `/cr-frontend` | 固定前端模式 |
| `/cr-fullstack` | 全栈复刻（前后端交叉验证） |
| `/cr-module` | 模块复刻（依赖边界处理） |
| `/cr-interface` | 固定 interface 信度 |
| `/cr-exact` | 固定 exact 信度 |
| `/cr-status` | 查看分析进度 |

## 后续步骤

复刻分析完成后，继续 dev-forge 流水线：

```
/design-to-spec   ← 生成目标技术栈实现规格
/task-execute     ← 逐任务生成代码
```
