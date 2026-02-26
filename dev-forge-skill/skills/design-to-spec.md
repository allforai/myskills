---
name: design-to-spec
description: >
  Use when the user wants to "convert design to spec", "generate requirements from product map",
  "create tasks from design", "design to specification", "设计转规格", "生成需求文档",
  "生成任务列表", "从产品设计产物生成开发规格", "产物转换",
  or needs to transform product-design artifacts into per-sub-project requirements, design docs, and atomic task lists.
  Requires project-manifest.json (from project-setup) and product-map artifacts.
version: "1.0.0"
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

## 动态趋势补充（WebSearch）

除经典理论外，执行设计转规格时通过 WebSearch 补充最新 API / 架构实践：

**搜索关键词模板**：
- `"{framework} API design patterns {year}"`
- `"{ORM} database schema design best practices"`
- `"REST API naming conventions {year}"`
- `"clean architecture {language} example {year}"`
- `"hexagonal architecture ports adapters {framework}"`

**来源优先级**：P1 官方文档 > P2 知名作者（Martin, Fowler, Cockburn）> P3 技术媒体 > P4 社区帖

**采纳决策**：记录到 `.allforai/project-forge/trend-sources.json`，标注 ADOPT / REJECT / DEFER + 理由。

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

| 产品设计产物 | 目标 spec | 映射规则 |
|---|---|---|
| role-profiles.json | requirements.md | "As a {role}" 用户故事 |
| task-inventory.json | requirements.md | 每任务 = 1 需求项，frequency → priority |
| acceptance_criteria | requirements.md | 直接映射为验收条件 |
| use-case-tree.json | requirements.md | Given/When/Then 丰富验收条件 |
| constraints.json | requirements.md | 非功能需求（安全/性能/业务规则） |
| screen-map.json | design.md | 每 screen = 1 页面/组件规格 |
| screen.actions | design.md | 每 action → 1 API 端点（后端）/ 1 交互规格（前端） |
| business-flows.json | design.md | flow → 时序图（Mermaid） |
| ui-design-spec.md | design.md | 设计 token、组件库引用 |
| prune-decisions.json | tasks.md | 仅 CORE 任务进入实施范围 |

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
| 从 screen-map 取 | actions → CRUD 页面规格 |
| 从 ui-design 取 | 全量设计 token |

### web-customer

| 维度 | 内容 |
|------|------|
| requirements 侧重 | SEO、加载速度、可访问性 |
| design 侧重 | SSR/SSG 策略、meta 标签、结构化数据 |
| 非功能需求 | Lighthouse 分数、Core Web Vitals |
| 从 screen-map 取 | actions → 页面组件规格 |
| 从 ui-design 取 | 全量设计 token + 性能约束 |

### web-mobile

| 维度 | 内容 |
|------|------|
| requirements 侧重 | 触屏可用性、离线场景 |
| design 侧重 | 移动优先布局、PWA 配置 |
| 非功能需求 | 弱网容忍、Service Worker |
| 从 screen-map 取 | actions → 触屏交互规格 |
| 从 ui-design 取 | 移动适配的设计 token |

### mobile-native (React Native / Flutter)

| 维度 | 内容 |
|------|------|
| requirements 侧重 | 离线同步、推送、设备权限 |
| design 侧重 | 导航栈（RN: React Navigation / Flutter: GoRouter）、原生组件、存储策略 |
| 非功能需求 | 电池/流量优化、后台任务 |
| 从 screen-map 取 | actions → Screen 组件规格（RN: Screen 组件 / Flutter: Screen Widget） |
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
    d. 生成 requirements.md:
       - 用户故事（As a {role}, I want... So that...）
       - 验收条件（Given/When/Then，来自 use-case-tree）
       - 非功能需求（来自 constraints + 子项目类型特有需求）
       - 优先级（frequency: 高→P0, 中→P1, 低→P2）
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
      actions → 交互规格（引用已定义的 API 端点）
      flows → 前端状态流转图
      ui-design-spec → 设计 token 引用
    mobile-native:
      screens → 导航栈 + Screen 组件规格
      actions → 原生交互规格（引用已定义的 API 端点）
    → 写入 .allforai/project-forge/sub-projects/{name}/design.md
    → 展示摘要 → 用户确认
  **生成顺序**: 后端 design.md 先于前端，确保前端 design 可直接引用 API 端点定义
  ↓
Step 3: Tasks 生成（逐子项目）
  按开发层分 Batch，每任务遵循原子标准:
    - 1-3 文件，15-30 分钟，单一目的
    - 指明具体文件路径（基于技术栈 template 约定）
    - 标注 _Requirements_ 和 _Leverage_ 引用
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
```

**原子性标准**：
- 1-3 文件：每任务最多涉及 3 个相关文件
- 15-30 分钟：单人可在此时间内完成
- 单一目的：一个可测试的结果
- 具体路径：基于技术栈 template 的命名约定
- 引用明确：标注依赖的 requirements 和可复用的代码

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
