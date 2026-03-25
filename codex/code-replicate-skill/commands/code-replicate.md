---
description: "代码复刻：逆向工程已有代码库 → 生成 allforai 产物 → 交还 dev-forge 流水线。模式: interface / functional / architecture / exact"
argument-hint: "[mode] <path-or-url> [--type backend|frontend|fullstack|module] [--scope full|modules|feature] [--module <path>] [--skip <modules>] [--from-phase N] [--from-step N.N] [--incremental]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion", "Agent", "WebSearch"]
---

# Code Replicate — 代码复刻

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 参数解析

从 `$ARGUMENTS` 解析：

| 参数 | 格式 | 说明 |
|------|------|------|
| `mode` | 位置参数 #1 | interface / functional / architecture / exact |
| `path` | 位置参数 #2 | 本地路径或 Git URL |
| `--type` | backend / frontend / fullstack / module | 项目类型（缺省自动检测） |
| `--scope` | full / modules / feature / 自由文本 | 分析范围 |
| `--module` | 路径 | 模块级复刻时指定模块路径 |
| `--from-phase` | 1-4 | 从指定阶段重跑（保留之前产物） |

### Git URL 支持

支持以下格式，可选 `#branch` 后缀指定分支/tag：

- HTTPS: `https://github.com/org/repo.git`
- SSH: `git@github.com:org/repo.git`
- GitHub 短语法: `org/repo`（自动展开为 `https://github.com/org/repo.git`）
- 分支/Tag: `https://github.com/org/repo#v2.0`

检测到 Git URL 时，clone 到临时目录后继续分析。

## 参数缺失引导

当 `$ARGUMENTS` 为空或缺少必要参数时，用 AskUserQuestion 逐步引导：

1. **源码地址**（若缺失）：「要复刻的源码在哪里？」选项：当前目录 `.` / 输入本地路径 / 输入 Git URL
2. **信度等级**（若缺失）：「需要什么级别的复刻？」选项：interface（仅 API 合约）/ functional（业务逻辑，推荐）/ architecture（含架构分析）/ exact（百分百复刻含 bug）
3. **项目类型**（若缺失且无法自动检测）：「这是什么类型的项目？」选项：backend / frontend / fullstack / 自动检测（推荐）

收集完毕后，按正常流程继续。

## 项目类型自动检测

当 `--type` 未指定时，扫描代码库判断项目类型：

- **backend**: routes/controllers/middleware/models 目录或文件
- **frontend**: components/pages/store/hooks/screens 目录或文件
- **fullstack**: 前后端代码共存（monorepo 或全栈框架）
- **module**: 需显式 `--type module --module <path>` 指定

## 技能分发

根据项目类型加载对应技能文件，用 Read 加载后按其完整工作流执行：

1. **`--type backend`**（或自动检测为后端）→ 加载 `${CLAUDE_PLUGIN_ROOT}/skills/cr-backend.md`
2. **`--type frontend`**（或自动检测为前端）→ 加载 `${CLAUDE_PLUGIN_ROOT}/skills/cr-frontend.md`
3. **`--type fullstack`**（或自动检测为全栈）→ 加载 `${CLAUDE_PLUGIN_ROOT}/skills/cr-fullstack.md`
4. **`--type module`** → 加载 `${CLAUDE_PLUGIN_ROOT}/skills/cr-module.md`（需 `--module` 参数）

所有技能文件内部加载 `${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md` 作为 4 阶段协议基础。

## 快捷命令

| 命令 | 等效 |
|------|------|
| `/cr-backend` | `/code-replicate --type backend` |
| `/cr-frontend` | `/code-replicate --type frontend` |
| `/cr-fullstack` | `/code-replicate --type fullstack` |
| `/cr-module` | `/code-replicate --type module` |
| `/cr-interface` | `/code-replicate interface` |
| `/cr-exact` | `/code-replicate exact` |
| `/cr-status` | 查看当前分析进度 |

## 快速参考

```
/code-replicate                                      # 交互式引导
/code-replicate functional ./src                     # 后端复刻业务行为（自动检测类型）
/code-replicate functional ./src --type frontend     # 前端复刻业务行为
/code-replicate functional ./src --type fullstack    # 全栈复刻（前后端交叉验证）
/code-replicate functional ./src --scope "用户注册和登录"  # 只复刻某个功能
/code-replicate interface ./src                      # 仅复刻 API 合约
/code-replicate exact ./src                          # 百分百复刻（含 bug）
/code-replicate functional https://github.com/org/repo.git      # 远程仓库
/code-replicate functional https://github.com/org/repo#v2.0     # 指定分支/tag
/code-replicate functional git@github.com:org/repo.git           # SSH 地址
/code-replicate functional org/repo                              # GitHub 短语法
/code-replicate functional ./src --type module --module src/user # 模块复刻
/code-replicate --from-phase 3                                   # 从 Phase 3 重跑
```

## 信度等级速查

| 等级 | 适用场景 |
|------|---------|
| `interface` | 后端重写，前端不动；API 兼容迁移 |
| `functional` | 技术栈迁移，保留业务逻辑（**推荐默认**） |
| `architecture` | 大规模重构，保持架构决策 |
| `exact` | 行为零容忍回归；监管合规 |

## 后续步骤

复刻分析完成后，继续 dev-forge 流水线：

```
/code-replicate   →  逆向分析，生成 .allforai/ 产物
    ↓
/project-setup    →  基于产物初始化目标项目
    ↓
/design-to-spec   →  生成目标技术栈实现规格
    ↓
/task-execute     →  逐任务生成代码
```
