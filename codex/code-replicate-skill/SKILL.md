---
name: code-replicate
description: >
  Code Replication Bridge: reverse-engineer existing codebases (any tech stack) into
  .allforai/ artifacts compatible with the dev-forge pipeline. 4 fidelity levels:
  interface (API contracts), functional (business behavior), architecture (patterns),
  exact (including bugs). Supports cross-stack migration.
---

# Code Replicate v2.1 — 代码复刻插件

> 逆向工程桥梁层：已有代码 → 标准 `.allforai/` 产物 → dev-forge 流水线

## 定位

Code Replicate 将已有代码库逆向解构为标准 `.allforai/` 产物，直接接入 dev-forge 流水线。不生成代码，只生成产物。行业和技术栈无关。

## 4 阶段工作流

| Phase | 名称 | 说明 | 交互 |
|-------|------|------|------|
| 1 | Preflight | 参数收集 + Git clone | 用户交互点 1 |
| 2 | Discovery + Confirm | 源码扫描 + 模块摘要 + **基础设施盘点** + 抽象提取 + 用户确认 | 用户交互点 2（最后一次） |
| 3 | Generate | LLM 按 extraction-plan 分模块生成片段 → 脚本合并 → 标准产物 | 静默 |
| 4 | Verify & Handoff | schema 校验 + XV 验证 + 报告 | 静默 |

> 完整协议见 `./skills/code-replicate-core.md`

## 保真度

| 等级 | 分析深度 | 标准产物输出 |
|------|---------|-------------|
| `interface` | 只看入口层签名 | task-inventory（精简）+ role-profiles（含 audience_type）+ product-map（含 experience_priority） |
| `functional` | 读函数体，追踪逻辑 | 上 + business-flows（含 systems/handoff）+ use-case-tree（扁平数组）+ task 结构化字段 |
| `architecture` | 额外分析模块依赖 | 上 + task 增加 module/prerequisites/cross_dept |
| `exact` | 额外标记 bug/约束 | 上 + constraints.json + task.flags |

> 详见 `./docs/fidelity-guide.md`

## 子技能

| 技能文件 | 用途 |
|---------|------|
| `skills/code-replicate-core.md` | 4 阶段协议 + 铁律 + 脚本调用参考 |
| `skills/cr-backend.md` | 后端分析视角：入口层 / 服务层 / 数据层 / 横切层 |
| `skills/cr-frontend.md` | 前端分析视角：页面 / 组件 / 状态 / 交互 |
| `skills/cr-fullstack.md` | 全栈：双栈分析 + 交叉验证 + 基础设施扫描 |
| `skills/cr-module.md` | 模块：依赖边界扫描 + 外部接口记录 |
| `skills/cr-fidelity.md` | 还原度验证：源码 vs 目标代码多维对比 + 闭环修复 |
| `skills/cr-visual.md` | 视觉还原度：源 App vs 目标 App 截图结构级对比 |

## 输出目录

```
.allforai/
├── product-map/          ← product-map, task-inventory, role-profiles,
│                           business-flows, constraints, indexes
├── experience-map/       ← experience-map.json（frontend/fullstack stub）
├── use-case/             ← use-case-tree, use-case-report
└── code-replicate/       ← replicate-config, source-summary,
                            discovery-profile, infrastructure-profile,
                            asset-inventory, extraction-plan,
                            stack-mapping, replicate-report,
                            fidelity-report
```

## 工作流衔接

```
code-replicate → design-to-spec → task-execute
    ↓
cr-fidelity（代码级还原度 — 复刻专属）
    ↓
product-verify（功能验收 — 与创建路径共用）
    ↓
testforge（测试质量 — 与创建路径共用）
    ↓
cr-visual（视觉还原度 — 测试全绿后，App 稳定运行时执行）
```

cr-fidelity 验证代码还原，product-verify 和 testforge 与创建路径共用。
cr-visual 最后执行 — 需要 App 稳定运行才能截图对比。

## 文档

- `./docs/fidelity-guide.md` — 保真度等级详解
- `./docs/analysis-principles.md` — 通用分析指导原则
- `./docs/stack-mappings.md` — 跨栈映射参考
- `./docs/schema-reference.md` — CR 专属 schema 定义
