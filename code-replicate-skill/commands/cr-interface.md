---
description: "接口复刻：仅复刻 API 合约（路由/参数/响应/状态码），不分析业务逻辑。后端重写时保持前端代码不变的首选。"
argument-hint: "<path-or-url> [--type backend|frontend|fullstack] [--scope full|modules|feature]"
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "AskUserQuestion"]
---

# CR Interface — 接口复刻

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 执行方式

固定 `fidelity = interface`，从 `$ARGUMENTS` 解析源码地址和 `--type`（若有）。

### 项目类型分发

根据 `--type` 参数决定加载哪个技能文件，用 Read 加载后按其完整工作流执行：

1. **`--type backend`** → 加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/cr-backend.md`
2. **`--type frontend`** → 加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/cr-frontend.md`
3. **`--type fullstack`** → 加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/cr-fullstack.md`
4. **未指定 `--type`** → 默认加载并执行 `${CLAUDE_PLUGIN_ROOT}/skills/cr-backend.md`（Phase 2 自动检测，若发现前端项目则切换）

Preflight 时：
- 信度等级已锁定为 `interface`，不询问
- 仅询问缺失的参数（源码地址、目标技术栈）

## 适用场景

- 后端重写，前端代码一行不动
- 从单体架构提取微服务，保持对外 API 不变
- REST → GraphQL 迁移（保留语义，改传输协议）
- 快速生成 API 规格文档（供 dev-forge 消费）
- 前端组件库迁移（仅复刻 Props 接口）

## 产出

```
.allforai/
├── product-map/task-inventory.json   ← 每个 API/组件 = 一个任务
└── code-replicate/
    ├── api-contracts.json            ← 完整 API/Props 合约清单
    └── replicate-report.md
```

## 后续步骤

```
/design-to-spec   ← 基于 API 合约生成目标技术栈实现规格
```
