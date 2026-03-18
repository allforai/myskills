---
name: code-replicate
description: >
  Code Replication Bridge: reverse-engineer existing codebases (any tech stack) into
  .allforai/ artifacts compatible with the dev-forge pipeline. 4 fidelity levels:
  interface (API contracts), functional (business behavior), architecture (patterns),
  exact (including bugs). Supports cross-stack migration.
---

# Code Replicate — 代码复刻插件

> 逆向工程桥梁层：已有代码 → `.allforai/` 产物 → dev-forge 流水线 → 目标技术栈代码

## 定位

Code Replicate 是**逆向产品设计桥梁** — 将已有代码库转化为标准 `.allforai/` 产物，直接接入 dev-forge 流水线。不是代码生成工具，而是让已有项目复用整个 dev-forge 基础设施的桥接层。

## 4 阶段工作流

| Phase | 名称 | 说明 |
|-------|------|------|
| 1 | 扫描 | 技术栈识别 + 目录结构 + 入口文件定位 |
| 2 | 提取 | 按信度等级提取行为/合约/架构（类型专用技能执行） |
| 3 | 映射 | 源码行为 → allforai 产物格式转换 + 歧义决策 + XV 验证 |
| 4 | 输出 | 生成 `.allforai/` 目录产物 + replicate-report.md |

> 完整协议见 `${CLAUDE_PLUGIN_ROOT}/skills/code-replicate-core.md`

## 信度等级

| 等级 | 复刻什么 | 适用场景 | 关键产物 |
|------|---------|---------|---------|
| `interface` | API 合约 | 后端重写，前端不动 | task-inventory + api-contracts |
| `functional` | 业务行为 | 技术栈迁移（推荐） | + business-flows + use-case-tree |
| `architecture` | 模块结构 | 大规模重构 | + arch-map |
| `exact` | 百分百复刻 | 行为零容忍回归 | + bug-registry + constraints |

## 子技能

| 技能文件 | 用途 |
|---------|------|
| `skills/code-replicate-core.md` | 4 阶段协议 + 4D/6V/XV 增强 + 铁律（所有类型共享） |
| `skills/cr-backend.md` | 后端：API 合约、Service 逻辑、ORM 映射、微服务契约 |
| `skills/cr-frontend.md` | 前端：组件树、路由、状态管理、移动端导航 |
| `skills/cr-fullstack.md` | 全栈：双栈分析 + 交叉验证（API 绑定、Schema 对齐） |
| `skills/cr-module.md` | 模块：依赖边界扫描、外部依赖、事件契约 |

## 输出目录

```
.allforai/
├── product-map/          ← task-inventory, business-flows, constraints
├── use-case/             ← use-case-tree (functional+)
└── code-replicate/       ← replicate-config, source-analysis, api-contracts,
                            behavior-specs, arch-map, stack-mapping,
                            replicate-report.md
```

## 工作流衔接

```
/code-replicate  →  /project-setup  →  /design-to-spec  →  /task-execute
```

## 文档

- `${CLAUDE_PLUGIN_ROOT}/docs/fidelity-guide.md` — 信度等级详解
- `${CLAUDE_PLUGIN_ROOT}/docs/stack-mappings.md` — 跨栈映射参考
