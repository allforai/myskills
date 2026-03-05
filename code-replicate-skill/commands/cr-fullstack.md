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

Preflight 时：
- 项目类型已锁定为 `fullstack`，不询问
- 自动检测前后端路径（或从 `--backend-path` / `--frontend-path` 获取）
- 仅询问缺失的参数（信度等级、源码地址、目标技术栈）

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
