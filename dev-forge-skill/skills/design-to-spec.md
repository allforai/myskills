---
name: design-to-spec
description: >
  Use when the user wants to "convert design to spec", "generate requirements from product map",
  "create tasks from design", "design to specification", "设计转规格", "生成需求文档",
  "生成任务列表", "从产品设计产物生成开发规格", "产物转换",
  or needs to transform product-design artifacts into per-sub-project requirements, design docs, and atomic task lists.
  Requires project-manifest.json (from project-setup) and product-map artifacts.
version: "1.1.0"
---

# Design to Spec — 设计转规格

> 从产品设计产物自动生成按子项目划分的 requirements + design + tasks

## 目标

以 `project-manifest.json` 和 product-design 产物为输入，为每个子项目生成三份开发规格文档：

1. **requirements.md** — 用户故事 + 验收条件 + 非功能需求
2. **design.md** — API 端点 / 页面路由 / 数据模型 / 组件架构 / 时序图
3. **tasks.md** — 原子任务列表，按开发层分 Batch（B0-B5）

---

## 定位

```
project-setup（架构层）   design-to-spec（规格层）   project-scaffold（实现层）
拆子项目/选技术栈         生成 spec 文档/任务列表      生成代码骨架
manifest.json            requirements + design + tasks  实际文件和目录
```

**前提**：
- 必须先运行 `project-setup`，生成 `.allforai/project-forge/project-manifest.json`
- 必须先运行 `product-map`，生成 `.allforai/product-map/` 产物

---

## 快速开始

```
/design-to-spec           # 全量生成（全部子项目）
/design-to-spec full      # 同上
/design-to-spec sp-001    # 仅指定子项目
```

---

## 增强协议（WebSearch + 4E+4V）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：
- `"{framework} API design patterns {year}"`
- `"{ORM} database schema design best practices"`
- `"REST API naming conventions {year}"`
- `"clean architecture {language} example {year}"`

**4E+4V 重点**（design-to-spec 是产品→工程的核心桥梁）：
- **E2 Provenance**: requirements.md 每个需求项标注 `_Source: T001, F001, CN001_`
- **E3 Guardrails**: task.rules → Business Rules 节；task.exceptions → Error Scenarios 节；task.audit → Audit Requirements 节；task.sla → SLA 标注；task.approver_role → Approval 节
- **E4 Context**: task.value → Value 注释；task.risk_level → Risk 标签；task.frequency → Priority
- **4V**: 高频+高风险任务的 design.md 至少覆盖 api + data + behavior 三个视角

---

## 规格生成理论支持

> 详见 `docs/dev-forge-principles.md` — 中段：规格与实现

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|---------|---------|
| **Clean Architecture** (Martin, 2017) | Step 3 Tasks 分 Batch | 依赖规则：B1→B2→B3→B4 遵循内→外依赖方向 |
| **SOLID Principles** (Martin, 2003) | Step 3 原子任务设计 | 单一职责：每任务 1-3 文件、单一目的 |
| **Hexagonal Architecture** (Cockburn, 2005) | Step 2 Design 生成 | 端口与适配器：API 客户端是端口，mock/真实后端是适配器 |
| **REST Maturity Model** (Richardson, 2008) | Step 2 API 端点设计 | Level 2：资源 + HTTP 动词 + 状态码 |
| **Database Normalization** (Codd, 1970) | Step 2 表结构设计 | 从 product-map entities 推导，遵循 3NF |
| **User Story Mapping** (Patton, 2014) | Step 1 Requirements | 按角色+流程组织用户故事 |
| **API-First Design** | Step 2 生成顺序 | 先后端 API 端点定义，再前端引用 |
| **C4 Model** (Brown, 2018) | Step 2 Design 结构 | design.md 按 C4 层级组织（系统→容器→组件→代码） |

---

## 核心映射逻辑

| 产品设计产物 | 目标 spec | 映射规则 | 4E |
|---|---|---|---|
| role-profiles.json | requirements.md | "As a {role}" 用户故事 | E1 |
| task-inventory.json | requirements.md | 每任务 = 1 需求项，frequency → priority | E1 |
| acceptance_criteria | requirements.md | 直接映射为验收条件 | E1 |
| use-case-tree.json | requirements.md | Given/When/Then 丰富验收条件 | E1 |
| constraints.json | requirements.md | 非功能需求（安全/性能/业务规则） | E3 |
| screen-map.json | design.md | 每 screen = 1 页面/组件规格 | E1 |
| screen.states | design.md | empty/loading/error/permission_denied → 界面四态设计 | E3 |
| screen.actions | design.md | 每 action → 1 API 端点（后端）/ 1 交互规格（前端） | E1 |
| action.on_failure | design.md | 操作失败 → UI 反馈设计（toast/banner/inline error） | E3 |
| action.exception_flows | design.md | 任务异常 → UI 响应映射（1-to-1，from screen-map Step 2） | E3 |
| action.validation_rules | design.md | 前端验证规则 → 表单 Schema 设计 | E3 |
| action.requires_confirm | design.md | 高风险操作 → 确认弹窗组件设计 | E3 |
| screen-conflict.json | requirements.md | 异常缺口（SILENT_FAILURE 等）→ 补充 Error Scenarios | E3 |
| business-flows.json | design.md | flow → 时序图（Mermaid） | E1 |
| ui-design-spec.md | design.md | 设计 token、组件库引用 | E1 |
| prune-decisions.json | tasks.md | 仅 CORE 任务进入实施范围 | E4 |
| task.rules | requirements.md | 每需求项的「Business Rules」节 | E3 |
| task.exceptions | requirements.md | 每需求项的「Error Scenarios」节 | E3 |
| task.sla | requirements.md | 每需求项的 SLA 标注 | E3 |
| task.prerequisites | requirements.md | 每需求项的「Prerequisites」节 | E3 |
| task.config_items | requirements.md + design.md | 配置依赖节 + 配置端点/表设计 | E3 |
| task.outputs | design.md | states → 状态机设计；notifications → 事件/通知设计 | E1 |
| task.audit | requirements.md + design.md | 审计需求节 + 审计日志表/中间件设计 | E3 |
| task.approver_role | requirements.md + design.md | 审批流需求 + 审批 API 端点 + 状态流转 | E3 |
| task.cross_dept_roles | design.md | 跨部门交接 → webhook/集成点设计 | E1 |
| task.value | requirements.md | 业务价值注释（E4 Context） | E4 |
| task.risk_level | requirements.md + tasks.md | 风险标签 → review 优先级 | E4 |
| constraints.code_status | requirements.md | hard 约束 → 验证中间件需求 | E3 |

---

## 各端差异化 Spec 生成

### backend

| 维度 | 内容 |
|------|------|
| requirements 侧重 | API 合约、并发、幂等、事务一致性 |
| design 侧重 | 端点设计、数据模型（Entity + 关系）、中间件链 |
| 非功能需求 | 吞吐量、事务一致性、错误码规范 |
| 从 screen-map 取 | 不取（无 UI） |
| 从 ui-design 取 | 不取 |

### admin

| 维度 | 内容 |
|------|------|
| requirements 侧重 | CRUD 完整性、批量操作、权限矩阵 |
| design 侧重 | 页面布局、组件树、表单验证规则 |
| 非功能需求 | 角色权限矩阵、审计日志 |
| 从 screen-map 取 | actions → CRUD 页面规格；states → 四态设计；on_failure + exception_flows → 错误反馈；validation_rules → 表单 Schema；requires_confirm → 确认弹窗 |
| 从 ui-design 取 | 全量设计 token |

### web-customer

| 维度 | 内容 |
|------|------|
| requirements 侧重 | SEO、加载速度、可访问性 |
| design 侧重 | SSR/SSG 策略、meta 标签、结构化数据 |
| 非功能需求 | Lighthouse 分数、Core Web Vitals |
| 从 screen-map 取 | actions → 页面组件规格；states → 四态设计（empty 状态需 SEO 友好）；on_failure + exception_flows → 用户友好错误页；validation_rules → 表单 Schema |
| 从 ui-design 取 | 全量设计 token + 性能约束 |

### web-mobile

| 维度 | 内容 |
|------|------|
| requirements 侧重 | 触屏可用性、离线场景 |
| design 侧重 | 移动优先布局、PWA 配置 |
| 非功能需求 | 弱网容忍、Service Worker |
| 从 screen-map 取 | actions → 触屏交互规格；states → 四态设计（loading 需骨架屏、error 需离线提示）；on_failure → 弱网重试 UI；validation_rules → 移动端表单验证 |
| 从 ui-design 取 | 移动适配的设计 token |

### mobile-native (React Native / Flutter)

| 维度 | 内容 |
|------|------|
| requirements 侧重 | 离线同步、推送、设备权限 |
| design 侧重 | 导航栈（RN: React Navigation / Flutter: GoRouter）、原生组件、存储策略 |
| 非功能需求 | 电池/流量优化、后台任务 |
| 从 screen-map 取 | actions → Screen 组件规格（RN: Screen 组件 / Flutter: Screen Widget）；states → 四态设计（离线态额外处理）；on_failure + exception_flows → 原生错误提示；validation_rules → 表单验证 |
| 从 ui-design 取 | 原生端设计 token（如有） |
| 测试工具 | RN: Detox / Maestro / Flutter: Patrol / integration_test |

---

## 工作流

```
前置: 两阶段加载
  Phase 1 — 加载索引（< 5KB）:
    project-manifest.json → 子项目列表
    task-index.json → 任务 id/name/frequency/module
    screen-index.json → 界面 id/name/action_count（可选）
    flow-index.json → 业务流 id/name（可选）
  Phase 2 — 按需加载 full 数据（仅加载当前子项目需要的模块）
  若 project-manifest.json 不存在 → 提示先运行 /project-setup，终止
  若 product-map.json 不存在 → 提示先运行 /product-map，终止
  加载 prune-decisions.json → 过滤: 仅 CORE 和 DEFER 任务进入范围
  ↓
Step 0: 模块映射验证
  检查 manifest 中所有子项目的 assigned_modules
  合并后与 task-index 的全量模块对照
  未覆盖的模块 → AskUserQuestion 解决:
    分配给某个子项目 / 标记暂缓 / 移除
  → 确认后更新 project-manifest.json
  ↓
Step 1: Requirements 生成（逐子项目）
  对每个子项目:
    a. 过滤该子项目的 assigned_modules → 获取模块内的任务列表
    b. 加载对应 full 数据（task-inventory + constraints + use-cases）
    c. 按子项目类型（backend/admin/web-customer/web-mobile/mobile-native）
       应用差异化 requirements 模板
    d. 生成 requirements.md（4E 增强模板）:
       每个需求项包含：
       - 优先级 + 角色（frequency → P0/P1/P2 + owner_role）
       - Value 注释（← E4 Context，from task.value）
       - 用户故事（As a {role}, I want... So that...）
       - 验收条件（Given/When/Then，来自 use-case-tree）
       - Business Rules（← E3 Guardrails，from task.rules）
       - Error Scenarios（← E3 Guardrails，from task.exceptions）
       - SLA（← E3 Guardrails，from task.sla）
       - Prerequisites（← E3 Guardrails，from task.prerequisites）
       - Approval（← E3 Guardrails，from task.approver_role）
       - Audit（← E3 Guardrails，from task.audit）
       - Config（← E3 Guardrails，from task.config_items）
       - 非功能需求（来自 constraints + 子项目类型特有需求）
       - _Source: T001, F001, CN001_（← E2 Provenance）
       注: 字段不存在或为空时省略对应节，不生成空占位
    → 写入 .allforai/project-forge/sub-projects/{name}/requirements.md
    → 展示摘要 → 用户确认
  ↓
Step 2: Design 生成（逐子项目，API-first 策略）
  **原则: 先表结构、后 API、再展开**
  对每个子项目，基于 tech-profile 映射:
    所有端共通（最先生成）:
      entities → 数据模型 / 表结构设计（ER 图 Mermaid）
      entity.fields → 字段类型 + 约束 + 索引
      entity.relations → 外键 + 关联关系
    backend（数据模型之后）:
      tasks → API 端点设计（RESTful 路由、请求/响应 DTO）
      constraints → 中间件链设计
      flows → 后端时序图
    前端类 (admin/web-customer/web-mobile):
      screens → 页面路由 + 组件架构
      screen.states → 界面四态设计（empty/loading/error/permission_denied）
      actions → 交互规格（引用已定义的 API 端点）
      action.on_failure + exception_flows → 操作异常 UI 反馈设计
      action.validation_rules → 表单验证 Schema
      action.requires_confirm → 确认弹窗组件规格
      flows → 前端状态流转图
      ui-design-spec → 设计 token 引用
    mobile-native:
      screens → 导航栈 + Screen 组件规格
      screen.states → 界面四态设计（同上）
      actions → 原生交互规格（引用已定义的 API 端点）
      action.on_failure + exception_flows → 原生异常 UI 反馈设计
      action.validation_rules → 表单验证规则
    按需生成的 4E 增强章节（字段存在时才生成）:
      task.rules（聚合）→ 验证规则设计（验证中间件/Schema 设计）
      task.outputs.states + task.exceptions → 状态机设计（Mermaid stateDiagram）
      task.audit（聚合）→ 审计日志设计（audit_logs 表结构 + 中间件）
      task.outputs.notifications → 通知/事件设计（事件触发规则）
      task.approver_role → 审批流 API（审批端点 + 状态流转）
      task.config_items → 配置管理设计（配置端点/表）
      task.cross_dept_roles → 集成点设计（webhook/回调端点）
    → 写入 .allforai/project-forge/sub-projects/{name}/design.md
    → 展示摘要 → 用户确认
  **生成顺序**: 后端 design.md 先于前端，确保前端 design 可直接引用 API 端点定义
  ↓
Step 3: Tasks 生成（逐子项目）
  按开发层分 Batch，每任务遵循原子标准:
    - 1-3 文件，15-30 分钟，单一目的
    - 指明具体文件路径（基于技术栈 template 约定）
    - 标注 _Requirements_ 和 _Leverage_ 引用
    - 标注 _Guardrails_（← E3，溯源 task.rules/exceptions/audit ID）
    - 标注 _Risk_（← E4，from task.risk_level，HIGH 任务优先 review）
  按需在 tasks.md 末尾生成专用任务批次（从聚合字段推导）：
    - 审计日志任务（从 task.audit 聚合 → audit_logs 表+中间件+测试）
    - 审批流任务（从 task.approver_role 聚合 → 审批 API+状态机+测试）
    - 配置管理任务（从 config_items 聚合 → 配置表+端点+测试）
  → Batch 结构因子项目类型而异（见下文）
  → 写入 .allforai/project-forge/sub-projects/{name}/tasks.md
  → 展示摘要 → 用户确认
  ↓
Step 4: 跨子项目依赖分析
  识别跨项目依赖:
    后端 API 端点 → 前端 API 客户端
    共享类型 → packages/shared-types
    后端 B2 完成 → 前端 B4 才能开始（切换 mock → 真实后端）
  生成跨项目任务排序 → execution_order
  → 更新 project-manifest.json
  → 展示依赖图 → 用户确认
```

---

## 任务 Batch 结构

### 全局 Batch（monorepo 视角）

```
## Batch 0: Monorepo Setup（全局，最先执行）
- [ ] 0.1 配置 monorepo workspace + 根配置文件
- [ ] 0.2 创建 packages/shared-types（从 product-map entities 生成）
- [ ] 0.3 创建 mock-server（来自 seed-forge plan 数据）

## Batch 1: Foundation（各子项目并行）
- [ ] 1.1 [api-backend] 数据模型、迁移、配置
- [ ] 1.2 [merchant-admin] 布局骨架、路由配置
- [ ] 1.3 [customer-web] SSR 配置、SEO 基础
...

## Batch 2: API / Service（后端）
- [ ] 2.1 [api-backend] Controller + Service + DTO + 中间件
...

## Batch 3: UI / Page（前端并行，连 mock-server）
- [ ] 3.1 [merchant-admin] 页面组件（连 mock-server）
- [ ] 3.2 [customer-web] 页面组件
...

## Batch 4: Integration（等 B2 完成）
- [ ] 4.1 生成 packages/api-client（从后端 Swagger/OpenAPI）
- [ ] 4.2 [merchant-admin] 切换 mock → 真实后端 API
- [ ] 4.3 [customer-web] 切换 mock → 真实后端 API
...

## Batch 5: Testing
- [ ] 5.1 [api-backend] 单元测试 + API 集成测试
- [ ] 5.2 [merchant-admin] 组件测试 + E2E
...
```

### 各端 Batch 内容差异

**backend**:
```
B1: 类型定义、Entity 文件、数据库迁移、config + common 搭建
B2: Controller + Service + DTO + 中间件注册
B3: —（无 UI 层，跳过）
B4: Swagger 文档、健康检查、错误码统一、API 客户端导出
B5: 单元测试 (entity+service) + API 集成测试 (supertest/pytest)
```

**admin**:
```
B1: 类型定义、API 客户端封装、根 layout + 侧边栏骨架、路由配置
B2: —（无独立 API，跳过）
B3: DataTable、Form 组件、页面组件、图表组件
B4: 连接真实 API（替换 mock-server base URL）、路由守卫、状态管理
B5: 组件测试 (Jest + RTL) + Playwright E2E (桌面视口)
```

**web-customer**:
```
B1: 类型定义、API 客户端、SEO meta 组件、SSR/SSG 基础配置
B2: —（无独立 API，跳过）
B3: 页面组件 (带 SSR metadata)、列表/详情/功能页
B4: 连接真实 API、结构化数据 (JSON-LD)、Analytics 集成
B5: Playwright E2E (桌面+移动视口) + Lighthouse 性能检测
```

**web-mobile**:
```
B1: 类型定义、PWA 配置、Service Worker、移动布局骨架
B2: —（无独立 API，跳过）
B3: 移动组件 (下拉刷新/无限滚动/手势)、页面、离线状态页
B4: 连接真实 API、离线缓存同步、推送集成
B5: Playwright 移动视口测试 + Lighthouse 移动性能检测
```

**mobile-native (React Native)**:
```
B1: 类型定义、导航栈配置 (React Navigation)、本地存储 schema (AsyncStorage)、权限声明、API 客户端 (Axios)
B2: —（无独立 API，跳过）
B3: Screen 组件 (FlatList/ScrollView/Form)、Tab 页面 (Bottom Tabs)、业务组件
B4: API 集成 (切换 mock → 真实后端)、离线同步、推送 (Expo Notifications)、深度链接
B5: Detox / Maestro 测试
```

**mobile-native (Flutter)**:
```
B1: 数据模型 (Dart class)、GoRouter 导航配置、主题/常量、API 客户端 (Dio)、Riverpod 基础 Provider
B2: —（无独立 API，跳过）
B3: Screen Widget (ListView/SingleChildScrollView/Form)、底部 Tab (NavigationBar)、业务 Widget (Card/ListTile/Detail)
B4: API 集成 (切换 mock → 真实后端)、离线同步 (connectivity_plus)、推送 (firebase_messaging)、深度链接
B5: Widget 测试 (flutter_test) + 集成测试 (Patrol / integration_test)
```

---

## 原子任务格式

每个任务遵循以下格式：

```markdown
- [ ] {batch}.{seq} [{sub-project}] {任务标题}
  - Files: `{file-path-1}`, `{file-path-2}`
  - 具体实现要点（2-4 条）
  - _Requirements: REQ-{id}_
  - _Leverage: {existing-file-or-package}_
  - _Guardrails: T001.rules[1,2], CN001_    ← 护栏溯源（from task.rules/exceptions/audit）
  - _Risk: HIGH | MEDIUM | LOW_              ← 风险标签（from task.risk_level）
```

**原子性标准**：
- 1-3 文件：每任务最多涉及 3 个相关文件
- 15-30 分钟：单人可在此时间内完成
- 单一目的：一个可测试的结果
- 具体路径：基于技术栈 template 的命名约定
- 引用明确：标注依赖的 requirements 和可复用的代码
- 护栏溯源：标注该任务需遵守的业务规则/异常/审计 ID
- 风险标签：HIGH 标签任务优先 code review

---

## 输出文件

```
.allforai/project-forge/sub-projects/
  {sub-project-name}/
  ├── requirements.md        # Step 1 输出
  ├── design.md              # Step 2 输出
  └── tasks.md               # Step 3 输出
```

---

## 5 条铁律

### 1. CORE 优先，DEFER 标记

仅 CORE 任务进入 tasks.md 的主体。DEFER 任务在末尾单独列出（标记 `[DEFERRED]`），不进入执行计划。CUT 任务完全排除。

### 2. 两阶段加载

先读 index 文件（< 5KB）确定范围，再按需加载 full 数据。大型产品可节省 90%+ token。

### 3. 按端差异化

不同子项目类型的 spec 内容截然不同。后端无 UI 层，前端无 API 层。不生成不属于该端的内容。

### 4. 任务必须原子

每任务 1-3 文件、15-30 分钟、单一目的。不出现"实现 XX 系统"这样的宽泛任务。

### 5. 跨项目依赖显式声明

后端 B2 → 前端 B4 的依赖、共享类型的依赖，都在 Step 4 中显式声明并写入 execution_order。
