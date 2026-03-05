---
description: "模块复刻：复刻指定模块并处理依赖边界（外部依赖、事件契约、共享层）。适合从大型项目中提取和迁移特定模块。"
argument-hint: "[mode] <path-or-url> --module <module-path> [--module <module-path>]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion", "Agent", "WebSearch"]
---

# CR Module — 模块复刻

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 执行方式

从 `$ARGUMENTS` 解析 `mode`、`path`（或 git URL）和 `--module` 参数。项目类型从 Phase 2 自动检测（后端模块 / 前端模块）。

加载并执行：`${CLAUDE_PLUGIN_ROOT}/skills/cr-module.md`

Preflight 时：
- `--module` 为必填参数（可多个）
- `scope` 自动设为 `modules`
- 项目类型从源码自动检测，不询问
- 仅询问缺失的参数（信度等级、源码地址、目标技术栈）

## 快速参考

```
/cr-module ./src --module src/modules/user                      # 复刻 user 模块
/cr-module functional ./src --module src/modules/user --module src/modules/auth
/cr-module functional ./src --module src/user                   # 简写路径
/cr-module functional https://github.com/org/repo.git --module src/modules/payment
/cr-module architecture ./src --module src/modules/order        # 含架构分析
```

## 适用场景

- 从单体项目提取特定模块迁移
- 微服务拆分（识别模块间隐式依赖）
- 模块级技术栈升级
- 评估模块的独立性和可迁移性

## 依赖边界处理

cr-module 会主动扫描并展示目标模块的外部依赖：

| 依赖类型 | 扫描内容 | 处理方式 |
|---------|---------|---------|
| 代码依赖 | import/require 外部模块 | 纳入 / 标记为外部接口 |
| 事件依赖 | emit/publish/subscribe 模式 | 记录事件契约 |
| 共享层 | 中间件/类型/数据表/配置 | 标记为前置依赖 |

## 产出

```
.allforai/code-replicate/
├── module-boundaries.json    ← 模块独有：依赖边界 + 事件契约 + 共享层
├── source-analysis.json
├── api-contracts.json
├── behavior-specs.json       ← functional+
├── arch-map.json             ← architecture+
├── stack-mapping.json
└── replicate-report.md       ← 含模块边界摘要
```

## 后续步骤

复刻分析完成后，继续 dev-forge 流水线：

```
/design-to-spec   ← 生成目标技术栈实现规格
/task-execute     ← 逐任务生成代码
```
