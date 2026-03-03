# 信度等级指南 (Fidelity Level Guide)

## 四个等级概述

信度等级决定逆向分析的**深度和范围**，影响产出的 allforai 产物精度以及对 dev-forge 流水线的利用度。

---

## interface（接口级）

**目标**：只复刻 API 合约 — 路由、参数、响应结构、状态码

**分析内容**：
- HTTP 路由（GET /users/:id、POST /orders 等）
- 请求参数（path / query / body 字段、类型、必填/可选）
- 响应结构（JSON schema、嵌套关系）
- HTTP 状态码（200/201/400/401/403/404/422/500 的触发条件）
- 认证方式（JWT header / API Key / Cookie）

**适用场景**：
- 需要兼容现有客户端，不想改接口契约
- 后端重写，前端代码不动
- 从 REST 迁移到 GraphQL（保留语义，改传输协议）
- 微服务拆分，对外接口不变

**产出的 allforai 产物**：
- `product-map/task-inventory.json` — 每个路由 = 一个任务（仅 CRUD 操作）
- `code-replicate/api-contracts.json` — 完整 API 合约清单

**预期分析时长**：快（通常 10-30 分钟）

---

## functional（功能级）

**目标**：复刻业务行为 — 逻辑路径、数据流、错误处理策略

**分析内容**：包含 interface 全部内容，加上：
- 业务逻辑条件分支（if 库存不足 then 返回 422、if 重复订单 then...）
- 数据流（数据从哪来、经过哪些变换、写到哪里）
- 错误处理策略（重试逻辑、fallback 行为、降级策略）
- 事务边界（哪些操作是原子的）
- 副作用（发邮件、触发队列、写审计日志等）

**适用场景**：
- 技术栈迁移（Python → Go、PHP → Node.js）
- 同技术栈框架升级（Express → Fastify）
- 引入新架构模式（从单体拆微服务，保留业务逻辑）

**产出的 allforai 产物**：
- 包含 interface 全部产物
- `product-map/business-flows.json` — 业务流程
- `use-case/use-case-tree.json` — 用例树
- `code-replicate/behavior-specs.json` — 行为规格

**预期分析时长**：中（30-90 分钟）

---

## architecture（架构级）

**目标**：复刻模块结构、分层、依赖关系

**分析内容**：包含 functional 全部内容，加上：
- 模块依赖图（哪个模块依赖哪个）
- 分层结构（Controller → Service → Repository 等）
- 设计模式（Repository Pattern、Strategy、Observer、Factory 等）
- 职责边界（每个模块/类的边界和契约）
- 横切关注点（日志、认证、缓存、限流如何实现）

**适用场景**：
- 大规模重构，保持架构决策
- 团队技术能力提升（理解架构后再迁移）
- 引入 DDD、Clean Architecture 等新架构（基于现有架构演进）

**产出的 allforai 产物**：
- 包含 functional 全部产物
- `code-replicate/arch-map.json` — 架构地图

**预期分析时长**：较长（1-3 小时）

---

## exact（精准级）

**目标**：百分百复刻 — 包含 bug、边界用例、非显式行为

**分析内容**：包含 architecture 全部内容，加上：
- 已知 bug（如：分页从 0 开始还是 1 开始、特殊字符处理）
- 边界用例（空列表、null 处理、超大数字、并发竞态）
- 非显式行为（未文档化的行为，如缓存失效时序）
- 性能特征（批量查询策略、N+1 查询位置、索引依赖）
- bug 标记（哪些行为是 bug 但客户端已依赖）

**适用场景**：
- 客户端代码不可改，服务端必须行为一致
- 合规要求（监管审计，行为必须可溯源）
- 遗留系统现代化（不允许行为回归）
- 关键业务系统（支付、库存，容忍度为零）

**⚠️ 警告**：
- 此模式会复刻已知 bug。建议在 replicate-report.md 中明确标注哪些行为是 bug，让用户决定是否修复
- 分析耗时显著更长，建议仅用于关键模块

**产出的 allforai 产物**：
- 包含 architecture 全部产物
- `code-replicate/bug-registry.json` — Bug 清单（含"是否复刻"决策字段）
- `product-map/constraints.json` — Bug 行为标记为"已知约束"

**预期分析时长**：长（3 小时以上，取决于代码库规模）

---

## 等级选择决策树

```
需要改 API 接口契约？
├── 否（客户端代码不能动）→ exact（如果行为100%一致是硬性要求）
│                          → interface（如果只保留接口签名即可）
└── 是（可以调整接口）→ 业务逻辑需要一样吗？
                        ├── 否 → interface
                        └── 是 → 架构设计需要一样吗？
                                  ├── 否 → functional
                                  └── 是 → architecture 或 exact
```

---

## 信度等级 × allforai 产物对照

| 产物 | interface | functional | architecture | exact |
|------|-----------|------------|--------------|-------|
| `product-map/task-inventory.json` | ✅ | ✅ | ✅ | ✅ |
| `product-map/business-flows.json` | - | ✅ | ✅ | ✅ |
| `product-map/constraints.json` | - | - | - | ✅ |
| `use-case/use-case-tree.json` | - | ✅ | ✅ | ✅ |
| `code-replicate/api-contracts.json` | ✅ | ✅ | ✅ | ✅ |
| `code-replicate/behavior-specs.json` | - | ✅ | ✅ | ✅ |
| `code-replicate/arch-map.json` | - | - | ✅ | ✅ |
| `code-replicate/bug-registry.json` | - | - | - | ✅ |
