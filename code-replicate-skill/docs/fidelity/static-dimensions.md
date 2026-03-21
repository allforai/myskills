# 静态代码维度 (F1-F8)

> 代码级对比：产物 vs 目标代码。LLM 根据产物是否存在自动选择适用维度。

## 评分通用规则

- 每个维度的"总数"来自 .allforai/ 产物（确定性来源）
- "匹配数"由 LLM 通过 fidelity-index 定位目标文件后逐项查证
- 每个 gap 必须记录 `evidence`：产物条目 ID + 目标文件搜索结果
- **总数为 0 的维度**自动标记为 N/A，不计入评分
- **基类覆盖**的功能算作匹配 — evidence 中标注 `via: 基类名`

---

## F1 — API 表面还原

**适用条件**：task-inventory.json 存在且包含 API 相关 task

对比 task-inventory 的 inputs/outputs 与目标代码中实际实现的 API 端点：
- 每个 task 是否有对应的端点/handler/controller？
- 输入参数（字段名、类型、必填性）是否一致？
- 输出响应（字段名、类型、状态码）是否一致？
- **路由模型一致性**：配置式路由 vs 代码式路由的优先级映射
- **全栈 task 双向验证**：`layer: fullstack` 的 task 必须在后端（有 API 端点）**和**前端（有 API 调用）两端都存在且参数一致。只有一端实现 → 算 gap（后端有但前端没调用 = 用户不可达）
- 如果 `platform_adaptation.skip_source_features` 存在，排除相关 task
- 评分 = 匹配 task 数 / 有效 task 数 × 100

## F2 — 数据模型还原

**适用条件**：source-summary.data_entities 非空

对比 data_entities 与目标代码中实际定义的实体/模型：
- 每个源码实体是否有对应的目标实体？
- 字段名称和类型是否匹配？
- 关系（1:N, N:M）是否保留？
- 评分 = 匹配字段数 / 总字段数 × 100

## F3 — 业务流还原

**适用条件**：business-flows.json 存在

对比 business-flows 与目标代码中实际的调用链：
- 每个 flow 的节点顺序是否在目标代码中可追踪？
- 跨模块调用（handoff）是否实现？
- 事务边界是否保留？
- 评分 = 可追踪 flow 数 / 总 flow 数 × 100

## F4 — 角色权限还原

**适用条件**：role-profiles.json 存在

对比 role-profiles 与目标代码中实际的认证/授权实现：
- 每个角色是否在目标代码的权限系统中定义？
- 权限边界是否与源码一致？
- 评分 = 已实现角色数 / 总角色数 × 100

## F5 — 异常处理还原

**适用条件**：use-case-tree.json 存在且包含 exception/boundary 类型 UC

对比 use-case-tree 中 type=exception/boundary 的用例与目标代码的错误处理：
- 每个异常用例是否有对应的错误处理？
- 错误消息/状态码是否与 acceptance_criteria 一致？
- 评分 = 已处理异常数 / 总异常用例数 × 100

## F6 — 抽象复用还原

**适用条件**：source-summary.abstractions 非空

对比 abstractions 与目标代码中的共享工具/基类：
- 每个高复用抽象是否有目标等价物？
- 消费模块是否确实使用了共享工具而非内联重复代码？
- 评分 = 已复用抽象数 / 总高复用抽象数 × 100

## F7 — 约束执行还原

**适用条件**：constraints.json 存在（通常 exact 保真度才有）

对比 constraints 中 enforcement=hard 的约束与目标代码：
- 每个硬约束是否有代码执行？
- 评分 = 已实现约束数 / 总 hard 约束数 × 100

## F8 — 基础设施还原（flexible 组件）

**适用条件**：infrastructure-profile.json 存在且含 `cannot_substitute: false` 的组件

仅评估**可替代**（`cannot_substitute: false`）的基础设施组件：
- 缓存框架、日志系统、ORM、DI 框架等设计选型类组件
- 是否有功能等价的目标实现？（不要求 API 一致，只要求能力覆盖）
- 评分 = 已还原的 flexible 组件数 / 总 flexible 组件数 × 100
