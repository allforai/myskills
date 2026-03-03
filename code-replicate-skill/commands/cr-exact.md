---
description: "精准复刻：百分百复刻源代码行为，含已知 bug、边界用例、非显式行为。适用于行为零容忍回归或监管合规场景。"
argument-hint: "[path]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion"]
---

# CR Exact — 精准复刻

用户请求: $ARGUMENTS

## ⚠️ 注意事项

此模式分析耗时显著更长，且**会复刻已知 bug**（客户端依赖的非预期行为）。

建议：
- 仅对关键业务模块使用（支付、权限、核心业务流程）
- 非关键模块建议使用 `functional` 或 `architecture` 模式
- 分析前确认你真的需要行为百分百一致

## 执行方式

固定 `fidelity = exact`，从 `$ARGUMENTS` 解析源码路径（若有），然后加载并执行：

`${CLAUDE_PLUGIN_ROOT}/skills/code-replicate.md`

Preflight 时：
- 信度等级已锁定为 `exact`，不询问
- **额外询问**：bug 复刻默认策略（replicate / fix / ask 逐一决策）
- 仅询问缺失的参数（源码路径、目标技术栈）

## 适用场景

- 客户端代码不可改，服务端必须行为完全一致
- 监管/合规要求行为可溯源
- 遗留系统现代化，不允许任何行为回归
- 关键业务系统（支付、库存）容忍度为零

## 产出

```
.allforai/
├── product-map/
│   ├── task-inventory.json     ← 所有 API 任务
│   ├── business-flows.json     ← 业务流程
│   └── constraints.json        ← Bug 行为标记为"已知约束"
├── use-case/
│   └── use-case-tree.json
└── code-replicate/
    ├── api-contracts.json
    ├── behavior-specs.json
    ├── arch-map.json
    ├── bug-registry.json        ← Bug 清单（含复刻决策）
    └── replicate-report.md
```
