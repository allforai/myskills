# 工程保真方法论（4E + 4V）

> 传递到下游的不仅是"做什么"，还有"为什么做"、"什么不能做"、"做了怎么验"。

## 核心思想

product-design 的 4D+6V 是产品视角，dev-forge 需要翻译为工程可执行形式。4E 保证每条 spec 携带完整语境，4V 保证每个高频/高风险任务覆盖工程所需的全部视角。

---

## 一、4E 工程信息卡

| 产品 4D | 工程 4E | 含义 | 落地位置 |
|---------|--------|------|---------|
| D1 结论 | **E1 Spec** | 做什么：API 合约、Schema、页面规格 | design.md |
| D2 依据 | **E2 Provenance** | 来自哪：task_id、flow_id、constraint_id | 各文档 `_Source:_` 标注 |
| D3 约束 | **E3 Guardrails** | 边界在哪：rules、SLA、exceptions、audit | requirements.md + design.md |
| D4 决策 | **E4 Context** | 为什么重要：value、frequency、risk_level | requirements.md 优先级标签 |

### 最小字段集

- **E1 Spec**：API 端点 / 表结构 / 页面路由（已有，不新增）
- **E2 Provenance**：`_Source: T001, F001, CN001_` — 每个需求项、设计章节、任务行标注来源 ID
- **E3 Guardrails**：`Business Rules` / `Error Scenarios` / `SLA` / `Prerequisites` / `Approval` / `Audit` / `Config` — 从 task.rules / exceptions / sla / prerequisites / approver_role / audit / config_items 映射
- **E4 Context**：`Value` 注释 + `Risk` 标签 + `Priority` 标注 — 从 task.value / risk_level / frequency 映射

---

## 二、4V 工程视角

产品 6V（user / business / tech / ux / data / risk）在工程层精简为 4V：

| 产品 6V | 工程 4V | 工程含义 |
|---------|--------|---------|
| tech | **api** | 接口合约（端点、DTO、状态码、幂等） |
| data | **data** | 数据模型（Schema、约束、索引、迁移） |
| user + ux | **behavior** | 行为视角（状态流转、异常处理、通知触发） |
| risk + business | **ops** | 运维视角（鉴权、审计、SLA、配置项） |

### 覆盖规则

- 高频 + 高风险任务：design.md 至少覆盖 api + data + behavior 三个视角
- 中频任务：至少覆盖 api + data
- 低频任务：至少覆盖 api

---

## 三、product-map → spec 字段映射表

| # | 产品设计字段 | 目标 spec 文件 | 目标章节 | 4E 分类 |
|---|------------|--------------|---------|--------|
| 1 | role-profiles | requirements.md | "As a {role}" 用户故事 | E1 |
| 2 | task.task_name | requirements.md | 需求项标题 | E1 |
| 3 | task.frequency | requirements.md | Priority 标注（高→P0, 中→P1, 低→P2） | E4 |
| 4 | task.main_flow | requirements.md | 验收条件 Given/When/Then | E1 |
| 5 | task.acceptance_criteria | requirements.md | 验收条件 | E1 |
| 6 | task.rules | requirements.md | Business Rules 节 | E3 |
| 7 | task.exceptions | requirements.md | Error Scenarios 节 | E3 |
| 8 | task.sla | requirements.md | SLA 标注 | E3 |
| 9 | task.prerequisites | requirements.md | Prerequisites 节 | E3 |
| 10 | task.config_items | requirements.md + design.md | Config 节 + 配置端点/表设计 | E3 |
| 11 | task.outputs.states | design.md | 状态机设计（Mermaid stateDiagram） | E1 |
| 12 | task.outputs.notifications | design.md | 事件/通知设计 | E1 |
| 13 | task.audit | requirements.md + design.md | Audit 节 + 审计日志表/中间件 | E3 |
| 14 | task.approver_role | requirements.md + design.md | Approval 节 + 审批 API/状态流转 | E3 |
| 15 | task.cross_dept_roles | design.md | webhook/集成点设计 | E1 |
| 16 | task.value | requirements.md | Value 注释 | E4 |
| 17 | task.risk_level | requirements.md + tasks.md | Risk 标签 → review 优先级 | E4 |
| 18 | constraints.code_status | requirements.md | hard 约束 → 验证中间件需求 | E3 |
| 19 | use-case-tree | requirements.md | Given/When/Then 丰富验收条件 | E1 |
| 20 | constraints | requirements.md | 非功能需求（安全/性能/业务规则） | E3 |
| 21 | experience-map | design.md | 页面/组件规格 | E1 |
| 22 | screen.states | design.md | empty/loading/error/permission_denied → 界面四态设计 | E3 |
| 23 | screen.actions | design.md | API 端点 / 交互规格 | E1 |
| 24 | action.on_failure | design.md | 操作失败 → UI 反馈设计 | E3 |
| 25 | action.exception_flows | design.md | 任务异常 → UI 响应映射 | E3 |
| 26 | action.validation_rules | design.md | 前端验证规则 → 表单 Schema | E3 |
| 27 | action.requires_confirm | design.md | 高风险操作 → 确认弹窗设计 | E3 |
| 28 | screen-conflict.json | requirements.md | 异常缺口 → 补充 Error Scenarios | E3 |
| 29 | business-flows | design.md | 时序图（Mermaid） | E1 |
| 30 | ui-design-spec | design.md | 设计 token、组件库引用 | E1 |
| 31 | prune-decisions | tasks.md | CORE 任务进入实施范围 | E4 |

---

## 四、门禁指标

| 指标 | 阈值 | 含义 |
|------|------|------|
| **Provenance 完整率** | >= 95% | spec 需求项可追溯到 product-map（task_id / flow_id / constraint_id） |
| **Guardrails 覆盖率** | >= 90% | 高频+高风险任务的 rules / exceptions / audit 被映射到 spec |
| **4V 视角覆盖** | 高频+高风险 >= 3V | 高频+高风险任务的 design.md 覆盖 api + data + behavior |
