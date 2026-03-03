---
description: "接口复刻：仅复刻 API 合约（路由/参数/响应/状态码），不分析业务逻辑。后端重写时保持前端代码不变的首选。"
argument-hint: "[path]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion"]
---

# CR Interface — 接口复刻

用户请求: $ARGUMENTS

## 执行方式

固定 `fidelity = interface`，从 `$ARGUMENTS` 解析源码路径（若有），然后加载并执行：

`${CLAUDE_PLUGIN_ROOT}/skills/code-replicate.md`

Preflight 时：
- 信度等级已锁定为 `interface`，不询问
- 仅询问缺失的参数（源码路径、目标技术栈）

## 适用场景

- 后端重写，前端代码一行不动
- 从单体架构提取微服务，保持对外 API 不变
- REST → GraphQL 迁移（保留语义，改传输协议）
- 快速生成 API 规格文档（供 dev-forge 消费）

## 产出

```
.allforai/
├── product-map/task-inventory.json   ← 每个 API = 一个任务
└── code-replicate/
    ├── api-contracts.json            ← 完整 API 合约清单
    └── replicate-report.md
```

## 后续步骤

```
/design-to-spec   ← 基于 API 合约生成目标技术栈实现规格
```
