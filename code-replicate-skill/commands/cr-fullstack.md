---
description: "全栈复刻：前后端联合逆向分析 + 交叉验证（API 绑定、Schema 对齐、认证传播、错误映射）。适合 monorepo 或前后端分离项目的完整迁移。"
argument-hint: "[mode] <path-or-url> [--backend-path <dir>] [--frontend-path <dir>]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion", "Agent", "WebSearch"]
---

# CR Fullstack — 全栈复刻

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 执行方式

固定 `project_type = fullstack`，从 `$ARGUMENTS` 解析 `mode`、`path`（或 git URL）、`--backend-path`、`--frontend-path` 参数（如已提供），然后加载并执行：

`${CLAUDE_PLUGIN_ROOT}/skills/cr-fullstack.md`

### 参数缺失引导

当 `$ARGUMENTS` 为空或缺少必要参数时，用 AskUserQuestion 逐步引导：

1. **源码地址**（若缺失）：「要复刻的全栈项目在哪里？」选项：当前目录 `.` / 输入本地路径 / 输入 Git URL
2. **信度等级**（若缺失）：「需要什么级别的复刻？」选项：functional（业务逻辑，推荐）/ architecture（含架构 + 交叉验证）/ exact（百分百复刻含 bug）
3. **前后端路径**（若无法自动检测）：「请确认前后端代码目录」— 列出项目根目录下的子目录供选择，分别指定 backend-path 和 frontend-path

收集完毕后，按正常流程继续。

Preflight 时：
- 项目类型已锁定为 `fullstack`，不询问
- 自动检测前后端路径（或从引导/参数获取）
- 仅询问缺失的参数（目标技术栈）

## 快速参考

```
/cr-fullstack ./project                                        # 自动检测前后端路径
/cr-fullstack functional ./project                             # 复刻业务行为
/cr-fullstack functional ./project --backend-path server --frontend-path client
/cr-fullstack functional https://github.com/org/repo.git       # 远程 monorepo
/cr-fullstack architecture ./project                           # 复刻架构（含交叉验证）
```

## 适用场景

- Monorepo 项目完整迁移（前后端一起）
- 前后端分离项目的全栈复刻
- 需要 API 绑定验证和 Schema 对齐的迁移
- 认证流程需要完整追踪的项目
- Next.js / Nuxt.js 等全栈框架项目

## 交叉验证产出

除后端/前端各自产物外，额外生成：

```
.allforai/code-replicate/
├── backend/                           ← 后端产物命名空间
├── frontend/                          ← 前端产物命名空间
├── api-bindings.json                  ← 前端调用 ↔ 后端端点
├── schema-alignment.json              ← 数据模型一致性
├── constraint-reconciliation.json     ← 业务规则覆盖
├── auth-propagation.json              ← 认证流程追踪
├── error-mapping.json                 ← 错误处理对齐
├── infrastructure.json                ← 基础设施行为
└── fullstack-report.md                ← 统一报告
```

## 后续步骤

复刻分析完成后，继续 dev-forge 流水线：

```
/design-to-spec   ← 生成目标技术栈实现规格
/task-execute     ← 逐任务生成代码
```
