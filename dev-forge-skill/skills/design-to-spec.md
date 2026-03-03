---
name: design-to-spec
description: >
  Use when the user wants to "convert design to spec", "generate requirements from product map",
  "create tasks from design", "design to specification", "设计转规格", "生成需求文档",
  "生成任务列表", "从产品设计产物生成开发规格", "产物转换",
  or needs to transform product-design artifacts into per-sub-project requirements, design docs, and atomic task lists.
  Requires project-manifest.json (from project-setup) and product-map artifacts.
version: "1.3.0"
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

## 增强协议（WebSearch + 4E+4V + OpenRouter）

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

**OpenRouter 交叉审查**（design.md 是全链路咽喉，此处质量提升下游全受益）：
- **`api_design_review`** (GPT) — 后端 design.md 生成后，发送 API 端点列表给 GPT 审查：
  - RESTful 命名规范（资源复数、HTTP 动词语义）
  - 请求/响应 DTO 字段与数据模型的一致性
  - 缺失的常见端点（分页、批量操作、健康检查）
  - 错误码格式统一性
  - 输出: `{ "issues": [{ "endpoint", "type", "suggestion" }], "missing": [...] }`
- **`data_model_review`** (DeepSeek) — ER 设计（Mermaid）生成后，发送给 DeepSeek 检查：
  - 3NF 违反点（传递依赖、冗余字段）
  - 缺失索引（外键字段、高频查询字段）
  - 外键关系漏洞（孤立实体、循环依赖）
  - 命名一致性（表名/字段名风格统一）
  - 输出: `{ "violations": [{ "table", "field", "type", "fix" }] }`
- 审查结果合并到 design.md 的 `## Review Notes` 附录（仅有问题时生成）
- OpenRouter 不可用 → 跳过审查，不阻塞生成

---

## 规格生成原则

> 以下原则在各步骤中强制执行，生成的 spec 必须符合这些规则。

| 原则 | 对应步骤 | 具体规则 |
|------|---------|---------|
| 分层依赖方向 | Step 4 | B1(数据模型) → B2(Service/API) → B3(UI页面) → B4(集成) 严格内→外。Controller 不直接调用 Repository，必须经过 Service |
| 单一职责任务 | Step 4 | 每个原子任务 1-3 文件、15-30 分钟、单一可测结果。禁止出现"实现 XX 系统"这种宽泛任务 |
| Service 隔离外部调用 | Step 3 | 外部 API/SDK 调用封装为独立 service 文件（如 `ai_client.py`、`speech_service.py`），业务层通过 service 接口调用，不直接 import SDK |
| RESTful 端点设计 | Step 3 | 资源名用复数名词（`/users`），用 HTTP 动词表达操作（GET/POST/PUT/DELETE），统一错误码格式 `{ code, message, details }` |
| 数据模型 3NF | Step 3 | 表结构遵循第三范式（消除传递依赖），冗余字段需在 design.md 中标注理由 |
| 用户故事按角色组织 | Step 1 | requirements.md 按角色分组（"As a {role}"），每组内按 frequency 排序（高频在前） |
| API-First 生成顺序 | Step 3 | **先生成后端 design.md（表结构→API 端点），再生成前端 design.md（引用已定义的 API）**。前端 design 中 API 调用必须引用后端 design 中的端点 ID |
| 设计分层展开 | Step 3 | design.md 从表结构开始，逐层展开到 API → 页面 → 组件。每层引用上一层定义 |
| 输入验证在边界层 | Step 3 | 所有用户输入在 Controller/Handler 层统一验证（whitelist 模式）。SQL 参数化查询，HTML 输出转义。认证中间件在路由注册时声明，不在业务代码中手动检查 |
| 统一错误处理 | Step 3 | 全局错误中间件捕获未处理异常，返回统一格式 `{ code, message, details }`。业务错误用自定义 Error 类（含 error_code），日志分级 ERROR/WARN/INFO，敏感信息不进日志 |
| 测试与实现对称 | Step 4 | 每个 B2 Service/API 任务必须对应 B5 测试任务。测试命名 `test_{行为}_{条件}_{预期}`，测试间无共享可变状态，每条测试独立可运行 |
| 性能基线内建 | Step 3 | 列表 API 强制分页（默认 page_size ≤ 50），有外键关联的字段加数据库索引，禁止 N+1 查询（ORM eager loading 或 JOIN）。大数据量操作走异步任务 |
| 写操作幂等 | Step 3 | 创建类 API 支持幂等键（`Idempotency-Key` header 或业务唯一约束），更新类 API 使用乐观锁（version 字段或 updated_at 条件更新），并发冲突返回 409 Conflict |
| 前端 CRUD 套路一致 | Step 3 | 同类型子项目（如多个 admin 端）的列表/新建/编辑/删除/详情必须使用相同组件套路和数据流模式。详见「前端 CRUD 实现套路」章节 |
| 多语言全覆盖 | Step 3, 4 | 所有用户可见文本必须通过 i18n 函数获取（禁止硬编码），新增文本必须同步所有语言文件。design.md 中标注 i18n 方案，tasks.md 中每个涉及 UI 文本的任务标注 `_i18n: sync all locales_` |

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
| forge-decisions.technical_spikes | design.md | spike.affected_tasks 匹配当前子项目任务 → 生成「Third-Party Integrations」章节 | E4 |
| forge-decisions.coding_principles | design.md | universal + project_specific → 生成「Coding Principles」约束章节 | E4 |
| spike.implementation_principles | design.md | 每个匹配 spike 的实现原则 → 写入对应集成章节 | E4 |

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
| design 侧重 | 页面布局、组件树、表单验证规则、CRUD 套路（见「前端 CRUD 实现套路」） |
| 非功能需求 | 角色权限矩阵、审计日志 |
| 从 screen-map 取 | actions → CRUD 页面规格；states → 四态设计；on_failure + exception_flows → 错误反馈；validation_rules → 表单 Schema；requires_confirm → 确认弹窗 |
| 从 ui-design 取 | 全量设计 token |
| CRUD 套路 | design.md 必须包含「CRUD 实现套路」章节，指定列表/表单/删除/详情的组件选型和数据流（详见下方独立章节） |

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

## 前端页面交互套路

> 前端子项目的 design.md 必须为每个页面标注交互类型，并遵循对应的数据流模式。
> 不同交互类型的页面使用不同的组件组合和数据流套路，**同类型页面必须使用相同套路**。
> **existing 模式下**：先扫描已有代码提取实际套路，以已有套路为准。以下为默认套路。

### 套路检测（existing 模式专用）

existing 模式下，Step 3 生成 design.md 之前，先执行套路检测：

1. **Request 层**：扫描 `src/utils/request*` 或 `src/requestConfig*`，识别 HTTP 客户端
2. **列表组件**：扫描 pages 目录，识别列表组件（ProTable / Table / DataGrid）
3. **表单组件**：扫描 `*Create*` / `*Edit*` / `*Form*`，识别表单模式
4. **状态操作**：扫描 `approve` / `reject` / `suspend` / `ship` 等操作模式
5. **删除确认**：扫描 `Modal.confirm` / `Popconfirm` 调用模式
6. **编辑回填**：扫描 `setFieldsValue` / `initialValues` 使用模式
7. **i18n**：扫描 `useIntl` / `useTranslations` / `t()` 调用模式
8. **枚举管理**：扫描 `constants/enum*` / `valueEnum` 定义模式

检测结果写入 design.md 的「页面交互套路」章节。

### 行为原语实现映射

> Step 2 识别出项目使用的行为原语后，查此表确定各技术栈的具体实现选项。
> 优先选用技术栈自带能力（零额外依赖），其次选生态标准库。

| 原语 | UmiJS + AntD Pro | Next.js | Flutter | React Native |
|------|-----------------|---------|---------|--------------|
| `VirtualList` | ProTable 内置虚拟化（默认启用） | `react-virtual` / `@tanstack/react-virtual` | `ListView.builder`（原生懒渲染） | `FlatList`（原生懒渲染） |
| `InfiniteScroll` | `ProList` + `onLoadMore` 回调 | `useInfiniteQuery`（TanStack Query）+ `IntersectionObserver` | `ListView.builder` + `onEndReached` | `FlatList` + `onEndReached` |
| `PullToRefresh` | `ProTable` + `headerTitle` 刷新按钮（桌面无下拉） | `useSWR` mutate / `queryClient.invalidateQueries` | `RefreshIndicator` widget | `RefreshControl`（FlatList prop） |
| `SwipeAction` | 无原生支持（桌面操作列按钮替代） | 无（桌面），移动端用 `react-swipeable` | `Dismissible` / `flutter_slidable` | `react-native-swipeable` |
| `HorizontalSwipe` | N/A（桌面不适用） | `react-swipeable` / `framer-motion` | `PageView` + `GestureDetector` | `PanGestureHandler`（react-native-gesture-handler） |
| `VerticalSwipe` | N/A（桌面不适用） | `framer-motion` 手势 | `PageView`（scrollDirection: vertical） | `FlatList`（vertical pagingEnabled） |
| `DragAndDrop` | `@dnd-kit/core` + `@dnd-kit/sortable` | `@dnd-kit/core` | `ReorderableListView` / `flutter_reorderable_list` | `react-native-draggable-flatlist` |
| `CanvasDrag` | `konva` / `react-flow` | `konva` / `react-flow` | `CustomPaint` + `GestureDetector` | `react-native-canvas` |
| `StateMachine` | 自定义 `useStateMachine` hook（枚举 + 合法转换 Map） | `XState` / Zustand slice | Riverpod `StateNotifier` | Zustand slice |
| `AppendOnlyStream` | Socket.io-client + `useRef` 消息数组 + `requestAnimationFrame` 滚动到底 | Socket.io-client / `EventSource`（SSE） | `StreamBuilder` + WebSocket（`web_socket_channel`） | Socket.io-client + `FlatList` inverted |
| `RealtimeSync` | Socket.io-client + 乐观更新（本地先改，收到服务端确认再 reconcile） | Socket.io-client / Pusher + `useSyncExternalStore` | `web_socket_channel` + Riverpod | Socket.io-client + Zustand |
| `FormWithValidation` | `ProForm` + `rules` 数组（antd 内置校验） | `react-hook-form` + `zod` resolver | `Form` + `TextFormField` + `validator` | `react-hook-form` |
| `MultiStepWizard` | `Steps` 组件 + 分步 `ProForm`（`StepsForm`） | 自定义 step state + 条件渲染 | `Stepper` package / 自定义 `PageView` | `react-native-paper` Steps / 自定义 |
| `TreeNavigation` | `Tree` 组件（AntD）+ 受控展开态 | `react-arborist` / 自定义递归组件 | `TreeView`（flutter_treeview） | `react-native-tree-select` |
| `MediaPlayer` | `react-player` / HTML5 `<video>` | `react-player` / Next.js `<video>` | `video_player` package + `Chewie` | `react-native-video` |
| `ImageLightbox` | `Image.PreviewGroup`（AntD 内置） | `yet-another-react-lightbox` | `photo_view` package | `react-native-image-viewing` |
| `Timeline` | `Steps`（竖向）/ `Timeline`（AntD） | 自定义竖向列表 | `timeline_tile` package | 自定义 `FlatList` |
| `BatchSelection` | `ProTable` + `rowSelection` + `toolBarRender` 批量操作栏 | 自定义 checkbox state + toolbar | `ListView` + `Checkbox` + `FloatingActionButton` | `FlatList` + `Checkbox` + bottom toolbar |

---

### 页面交互类型分类

> **类型定义与推断规则**：见 `product-design-skill/docs/interaction-types.md`（单一事实来源）。
> screen-map Step 1 已为每个 screen 标注 `interaction_type` 字段，design-to-spec 直接读取使用。

37 种交互类型（MG/CT/EC/WK/RT/SB/SY/TU）完整定义见 `product-design-skill/docs/interaction-types.md`。screen-map Step 1 已为每个 screen 标注 `interaction_type` 字段，design-to-spec 直接读取使用。

---

### 按技术栈的各类型套路

#### UmiJS + Ant Design Pro（admin / merchant 类）

##### 公共基础层

**请求层**（所有类型共用）：

| 层次 | 规范 |
|------|------|
| HTTP 客户端 | `@umijs/max` 的 `request` 函数，全局配置在 `requestConfig.ts` |
| Token 管理 | requestConfig.ts 统一处理 Authorization header、token 刷新（mutex）、401 重定向 |
| Service 文件 | 每个域一个文件（`src/services/products.ts`），函数按操作命名 |
| 类型定义 | `src/services/typings.d.ts`，响应统一 `API.Response<T>` / `API.PageResponse<T>` |

**枚举管理**（所有类型共用）：

```
定义: constants/enums.ts — 枚举值（数字或字符串常量）
标签: constants/enumLabels.ts — 多语言标签 + 颜色/Tag 映射
使用: 列表列 valueEnum + 表单 Select options + 详情页 Tag 共用同一套枚举
```

**字段→组件映射**（所有含表单的类型共用，抽象映射见 `docs/interaction-types.md`）：

| 字段类型 | UmiJS + AntD Pro 组件 | 备注 |
|---------|------|------|
| 文本 | `Input` / `ProFormText` | |
| 多行文本 | `Input.TextArea` / `ProFormTextArea` | rows ≥ 3 |
| 枚举/状态 | `Select` / `ProFormSelect` | 选项来自 `constants/enums.ts`，禁止用 Input |
| 数字 | `InputNumber` / `ProFormDigit` | 设置 min/max/precision |
| 布尔 | `Switch` / `ProFormSwitch` | |
| 日期 | `DatePicker` / `ProFormDatePicker` | |
| 图片 | `Upload`（listType="picture-card"） | 限制数量和格式 |
| 关联实体 | `Select`（动态从 API 获取 options） | 如「分类选择」 |

---

##### MG1 只读列表

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

```
组件: ProTable<API.Entity> + useRef<ActionType>()
数据源: request prop → service 函数 → { data, total, success }
筛选: 列定义 valueType: 'select' + valueEnum，或 dateRange 搜索
操作列: 仅「查看详情」Link 跳转，无编辑/删除按钮
分页: params.current → page，defaultPageSize: 10/20
搜索: search={{ labelWidth: 'auto' }}
特征: 无 ModalForm、无 Modal.confirm、无 mutation API 调用
```

Service 层仅需 `getXList()` 函数，无 create/update/delete。

---

##### MG2 CRUD 实体集群

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

**列表页**：
```
组件: ProTable + ActionRef
操作列: 编辑 + 删除（+ 可选的状态切换）
工具栏: 新建按钮（toolBarRender）
```

**新建/编辑表单**：

| 场景 | 组件 | 数据流 |
|------|------|--------|
| 简单实体（≤8 字段） | `ModalForm` + `ProForm*` 字段 | `onFinish` 返回 boolean → 成功关闭 → `actionRef.current?.reload()` |
| 复杂实体（>8 字段 / 含嵌套） | 独立页面 `Form` | `useEffect` fetch → `form.setFieldsValue()` 回填 → 提交 → `history.push()` |

**编辑回填（强制）**：
- ModalForm：打开前 `form.setFieldsValue(record)` 或传 `initialValues`
- 独立页面：`useEffect` 中 fetch → `form.setFieldsValue(res.data)`
- 图片/文件：URL 转 `UploadFile[]`（`{ uid, name, status: 'done', url }`）

**删除操作**：
```
确认: Modal.confirm({ title, content: 实体名, okType: 'danger' }) 或 Popconfirm
执行: onOk → deleteX(id) → message.success → actionRef.current?.reload()
```

Service 层完整：`getXList()` / `getX(id)` / `createX()` / `updateX()` / `deleteX()`

---

##### MG3 状态机驱动

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

**列表页**：
```
组件: ProTable + 状态筛选（valueEnum 按状态着色）
操作列: 根据当前状态动态显示可用操作按钮（条件渲染）
  如: 待发货 → 显示「发货」；已发货 → 显示「查看物流」
无: 编辑按钮、删除按钮
```

**状态操作**：
```
简单操作（无额外输入）:
  Modal.confirm({ title: '确认发货？', onOk: () => shipOrder(id) })
  → message.success → actionRef.current?.reload()

带输入的操作（如拒绝需填理由）:
  ModalForm({ title: '拒绝退款' })
    → ProFormTextArea name="reason" rules=[{ required: true }]
    → onFinish: rejectRefund(id, { reason }) → reload
```

**状态流转图**（design.md 必须包含 Mermaid stateDiagram）：
```
design.md 中为每个状态机实体生成:
  stateDiagram-v2
    [*] --> pending
    pending --> approved : approve()
    pending --> rejected : reject(reason)
    approved --> suspended : suspend(reason)
    suspended --> approved : restore()
```

Service 层：`getXList()` / `getX(id)` / `approveX(id)` / `rejectX(id, reason)` / `shipX(id, data)` 等操作函数，无 `updateX()` 通用编辑。

---

##### MG4 审批流

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

**列表页**：
```
组件: ProTable，status 列默认筛选为「待审批」
操作列: 「审核」Link 跳转到详情页
可选: 批量审批（rowSelection + 工具栏批量操作按钮）
```

**审核详情页**：
```
布局:
  Card(实体完整信息 — Descriptions / 只读展示，不可编辑)
  Card(审核操作面板)
    → 审核检查项（可选 Checkbox 清单）
    → 批准按钮 (Filled, type="primary")
    → 驳回按钮 (Outlined, danger)
    → 驳回时弹出 ModalForm 填写驳回原因

数据流:
  批准: Modal.confirm → approveX(id) → message.success → history.push(列表)
  驳回: ModalForm → rejectX(id, { reason, comment }) → history.push(列表)
```

Service 层：`getXList()` / `getXDetail(id)` / `approveX(id)` / `rejectX(id, reason)`，可选 `batchApproveX(ids[])`。

---

##### MG5 主从详情

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

```
路由: /entities/:id
取数: useParams() → useEffect fetchEntity() → setState

布局:
  PageContainer
    Card(头部 — Avatar/名称/关键指标 Statistic)
    Card(基本信息 — Descriptions column={2})
    Card(关联数据 — Tabs)
      TabPane("订单") → ProTable + 独立 ActionRef（request 内带 entityId 筛选）
      TabPane("积分") → ProTable + 独立 ActionRef
      TabPane("日志") → ProTable（只读）

内嵌操作:
  主实体操作: 按钮 → ModalForm → fetchEntity() 刷新主信息
  子实体操作: 子表操作列 → Modal.confirm → 子表 actionRef.current?.reload()
```

Service 层：`getX(id)` + `getXOrders(id, params)` + `getXPoints(id, params)` 等子实体查询。

---

##### MG6 树形管理

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

```
取数: useEffect fetchTree() → setState（一次加载全树，或懒加载子节点）

布局:
  左侧: Tree 组件展示层级
  右侧/弹窗: 选中节点的编辑表单

新建: 选中父节点 → 打开 ModalForm（带 parentId）→ createX({ ...values, parentId })
编辑: 选中节点 → form.setFieldsValue(node.data) → updateX(id, values)
删除: Popconfirm → deleteX(id)
排序: 拖拽或 sort 字段编辑

刷新: 所有操作后 fetchTree()（重建整棵树）
```

Service 层：`getXTree()` / `createX({ parentId })` / `updateX(id)` / `deleteX(id)` / 可选 `reorderX(id, sort)`。

---

##### MG7 仪表盘

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

```
取数: useEffect → 调用 getDashboard() / getStatistics() → setState
布局:
  Row + Col 网格:
    Statistic 卡片（关键指标：总订单数、待处理、销售额）
    图表（可选: @ant-design/charts — Line/Bar/Pie）
    待办事项列表（Link 跳转到对应管理页）

刷新: 无自动刷新（或可选定时轮询）
```

Service 层：`getDashboard()` / `getStatistics(params)` 聚合查询。

---

##### MG8 配置页

> 类型特征见 `docs/interaction-types.md`。以下为 UmiJS + AntD Pro 实现规范。

```
取数: useEffect → getSettings() → form.setFieldsValue(res.data)

布局:
  PageContainer
    Card(表单)
      Form + Form.Item（字段按业务分组，可用 Divider 分隔）
      提交按钮（固定在底部或浮动）

提交: form.validateFields() → updateSettings(values) → message.success
特征: 无列表、无删除、无新建。只有「加载 → 编辑 → 保存」。
```

Service 层：`getSettings()` / `updateSettings(values)`，仅两个函数。

---

#### Next.js（web-customer 类）

> C 端页面交互类型较少，主要是消费者浏览+操作场景。

| 交互类型 | 套路 |
|---------|------|
| 商品列表/搜索 | Server Component 首屏 SSR + TanStack Query 客户端分页/筛选 |
| 商品详情 | SSR + 客户端交互（加购/收藏/关注） |
| 表单提交（下单/评价/工单） | React Hook Form / 原生 form → `useMutation` → 成功跳转 |
| 用户中心列表（订单/收藏/积分） | TanStack Query `useInfiniteQuery` 无限滚动或分页 |
| 状态操作（取消订单/申请退款） | 确认弹窗 → `useMutation` → `queryClient.invalidateQueries` |
| 个人设置（地址/资料） | `useQuery` 加载 → 表单回填 → `useMutation` 保存 |
| i18n | `useTranslations` hook（next-intl），翻译文件 `src/messages/{locale}.json` |
| 状态管理 | Zustand store（全局状态）+ TanStack Query（服务端缓存） |

#### Flutter（mobile-native 类）

| 交互类型 | 套路 |
|---------|------|
| 列表浏览 | ListView.builder + Riverpod `AsyncNotifierProvider`（分页加载） |
| 详情查看 | `FutureProvider` / `AsyncNotifier` → 单实体 fetch |
| 表单提交 | Form + TextFormField + `controller.text = oldValue` 回填 |
| 枚举选择 | `DropdownButtonFormField` |
| 状态操作 | `showDialog` 确认 → API → `ref.invalidate()` |
| 删除 | `showDialog` 确认 → API → `ref.invalidate()` / `context.pop()` |
| 配置页 | `AsyncNotifier` 加载 → Form 回填 → 保存 |
| i18n | flutter_localizations + `.arb` 文件 |

---

### 多语言实现规范

> 通用规范见 `docs/interaction-types.md`。以下为各技术栈的实现差异。

| 技术栈 | i18n 方案 | 翻译文件位置 | hook/函数 |
|--------|----------|-------------|-----------|
| UmiJS (admin/merchant) | `@umijs/max` 内置 | `src/locales/` | `useIntl()` + `intl.formatMessage()` |
| Next.js (website) | `next-intl` | `src/messages/` | `useTranslations()` |
| Flutter (mobile) | `flutter_localizations` | `lib/l10n/*.arb` | `AppLocalizations.of(context)` |

**通用规则**（所有技术栈）：
- 所有用户可见文本通过 i18n 函数获取，禁止硬编码
- 新增文本必须同步所有语言文件（ja/en/zh-CN）
- Key 按 `{模块}.{页面}.{元素}` 分层命名
- tasks.md 中每个涉及 UI 文本的任务附加 `_i18n: sync all locales_` 标注

---

### design.md 中的输出格式

生成前端子项目的 design.md 时，在页面规格之前插入「页面交互套路」章节。每个页面规格中标注交互类型：

~~~markdown
## 页面交互套路

> 本项目各页面按交互类型分类，同类型页面必须遵循相同的组件选型和数据流。

### 请求层
{从套路检测结果或默认套路填写}

### 页面类型分布
| 类型 | 页面数 | 代表页面 |
|------|--------|---------|
| MG1 只读列表 | {N} | 审计日志、积分历史 |
| MG2 CRUD 集群 | {N} | 商品管理、分类管理 |
| MG3 状态机驱动 | {N} | 订单管理 |
| MG4 审批流 | {N} | 商品审核 |
| MG5 主从详情 | {N} | 用户详情 |
| MG6 树形管理 | {N} | 分类管理 |
| MG7 仪表盘 | {N} | 首页 |
| MG8 配置页 | {N} | 店铺设置 |
| CT/EC/WK/RT/SB/SY | {N} | Feed流、商品详情、IM等 |

### 各类型标准数据流
{按类型列出组件选型 + 数据流 + Service 函数签名}

### 字段→组件映射
{字段类型对照表}

### 枚举管理
{定义位置 + 使用方式}

### 多语言
{i18n 方案 + 语言文件位置 + 同步要求}
~~~

每个具体页面规格标注类型：
~~~markdown
#### 商品列表页 [类型: MG2-完整CRUD]
#### 审计日志页 [类型: MG1-只读列表]
#### 订单详情页 [类型: MG5-主从详情 + MG3-状态机驱动]
~~~

一个页面可以组合多个类型（如「订单详情」= 主从详情 + 状态机操作）。

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
  加载 forge-decisions.json → 读取 technical_spikes + coding_principles（存在时）
  ↓
前置: 上游过期检测
  加载输入文件时，比较关键上游文件的修改时间与本技能上次输出的生成时间：
  - project-manifest.json 在 requirements.md / design.md / tasks.md 生成后被更新
    → ⚠ 警告「project-manifest.json 在 requirements.md/design.md/tasks.md 生成后被更新，数据可能过期，建议重新运行 project-setup」
  - product-map.json 在 requirements.md / design.md / tasks.md 生成后被更新
    → ⚠ 警告「product-map.json 在 requirements.md/design.md/tasks.md 生成后被更新，数据可能过期，建议重新运行 product-map」
  - 仅警告不阻断，用户可选择继续或先刷新上游
  ↓
Step 0: 模块映射验证
  检查 manifest 中所有子项目的 assigned_modules
  合并后与 task-index 的全量模块对照
  未覆盖的模块：
    → 自动分配到最匹配的子项目（按模块类型推断），记录决策（不停）
  → 写入 `.allforai/project-forge/module-assignment-supplement.json`（追加分配条目）
  → **不修改** project-manifest.json（上游产物只读）
  → task-execute / project-scaffold 加载时自动合并 manifest + supplement
  ↓
并行执行编排（详见「## 并行执行编排」段落）:
  子项目分类:
    后端组: type = "backend"（通常 1 个）
    前端组: 其余所有子项目（admin/web-customer/web-mobile/mobile-native）
  Phase A — 后端 Agent（1 个 Agent 调用）:
    Agent(backend): Step 1 → Step 2 → Step 3 → Step 3.5 → Step 4
    ↓ 完成后
  Phase B — 前端并行 Agent（单条消息发出 N 个 Agent 调用）:
    ┌── Agent(前端1): Step 1 → Step 2 → Step 3 → Step 4
    ├── Agent(前端2): Step 1 → Step 2 → Step 3 → Step 4
    └── Agent(前端N): Step 1 → Step 2 → Step 3 → Step 4
    全部完成 ↓
  以下 Step 1-4 描述每个 Agent 内部执行的步骤内容:
  ↓
Step 1: Requirements 生成
  每个 Agent 对其负责的子项目:
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
    → 输出进度: 「{name}/requirements.md ✓ ({N} 需求项)」（不停，汇总到 Step 6）
  ↓
Step 2: 行为原语识别 → 共享组件规划
  （仅前端子项目执行；后端子项目跳过此步直接进入 Step 3）
  ↓
Step 3: Design 生成（API-first 策略）
  **原则: 先表结构、后 API、再展开**
  每个 Agent 对其子项目，基于 tech-profile 映射:
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
    按需生成的 Coding Principles 章节（forge-decisions.json 存在 coding_principles 时）:
      ## Coding Principles
      ### 通用原则
        coding_principles.universal → 逐条列出
      ### 项目特定原则
        coding_principles.project_specific → 逐条列出（含 spike/constraint 溯源标记）
      此章节写在 design.md 开头（数据模型之前），作为全文件的架构约束前言
    按需生成的 Technical Spike 集成章节（forge-decisions.json 存在 technical_spikes 时）:
      过滤 technical_spikes 中 affected_tasks 与当前子项目任务有交集的 spike
      每个匹配的 spike → 生成 Third-Party Integrations 子章节:
        - Vendor + SDK（from spike.decision.vendor / spike.decision.sdk）
        - Integration approach（from spike.decision.approach）
        - Implementation principles（from spike.implementation_principles → 逐条列出）
        - Affected endpoints / components（根据子项目类型推导）
        - spike.status = "tbd" → 标注 [PENDING: 技术方案待定，后续确认后补充]
    → 写入 .allforai/project-forge/sub-projects/{name}/design.md
    → 输出进度: 「{name}/design.md ✓ ({N} API端点, {M} 页面)」（不停，汇总到 Step 6）
  **生成顺序**: 后端 Agent (Phase A) 先于前端 Agent (Phase B)，确保前端 design 可直接引用 API 端点定义
  ↓
Step 3.5: Design 交叉审查（由后端 Agent 在 Phase A 内执行，OpenRouter 可用时）
  后端 design.md 生成后，触发两项交叉审查:
  审查 A — API 设计审查 (GPT):
    提取 design.md 中所有 API 端点（路径+方法+请求/响应 DTO）
    调用: mcp__plugin_product-design_openrouter__ask_model(task: "structured_output", model_family: "gpt")
    审查: RESTful 规范、DTO 一致性、缺失端点、错误码统一
    输出: issues[] + missing[]
  审查 B — 数据模型审查 (DeepSeek):
    提取 design.md 中 ER 设计（Mermaid + 字段定义）
    调用: mcp__plugin_product-design_openrouter__ask_model(task: "technical_validation", model_family: "deepseek")
    审查: 3NF 违反、缺失索引、外键漏洞、命名一致性
    输出: violations[]
  结果处理:
    有问题 → 在 design.md 末尾追加 ## Review Notes 附录（按问题严重度排列）
    无问题 → 不追加
    → 输出进度: 「Step 3.5 交叉审查 ✓ API {N} issues, Model {M} violations」
  OpenRouter 不可用 → 跳过，输出: 「Step 3.5 ⊘ OpenRouter 不可用，跳过交叉审查」
  ↓
Step 4: Tasks 生成
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
  → 输出进度: 「{name}/tasks.md ✓ ({N} 任务, B0-B5)」（不停，汇总到 Step 6）
  ↓
Step 5: 跨子项目依赖分析
  识别跨项目依赖:
    后端 API 端点 → 前端 API 客户端
    共享类型 → packages/shared-types
    后端 B2 完成 → 前端 B4 才能开始（切换 mock → 真实后端）
  生成跨项目任务排序 → execution_order
  → 写入 `.allforai/project-forge/cross-project-dependencies.json`（依赖图 + execution_order）
  → **不修改** project-manifest.json（上游产物只读）
  → 输出进度: 「跨项目依赖图 ✓ ({N} 条依赖)」（不停，汇总到 Step 6）
  ↓
Step 6: 阶段末汇总确认
  展示全部生成结果摘要:

  Phase A (后端):
  | 子项目 | requirements | design | tasks | Step 3.5 审查 |
  |--------|-------------|--------|-------|--------------|
  | {backend} | {N} 需求项 | {N} API端点 | {N} 任务 | API {N} issues, Model {M} violations |

  Phase B (前端并行):
  | 子项目 | requirements | design | tasks | 状态 |
  |--------|-------------|--------|-------|------|
  | {admin} | {N} 需求项 | {N} 页面 | {N} 任务 | 完成/失败 |
  | {web} | {N} 需求项 | {N} 页面 | {N} 任务 | 完成/失败 |
  | {mobile} | {N} 需求项 | {N} 页面 | {N} 任务 | 完成/失败 |

  跨项目依赖: {N} 条
  执行顺序: B0 → B1(并行) → B2 → B3(并行) → B4 → B5
  总任务数: CORE {N} + DEFER {M}

  → 输出汇总进度「Phase 2 ✓ {N} 子项目 × 3 文档 (Phase A 串行 + Phase B 并行), CORE {M} 任务」（不停）
```

### 规模自适应

根据子项目任务数自动调整 Step 6 展示策略：
- **小规模**（≤30 tasks/子项目）：逐条展示完整任务列表
- **中规模**（31-80 tasks/子项目）：按 Batch 分组摘要，仅展示 HIGH-risk 任务详情
- **大规模**（>80 tasks/子项目）：统计概览（任务分布、风险分布、覆盖率）+ 仅列 HIGH-risk 项

---

## 并行执行编排

> Step 1-4 由 Agent 并行执行，编排器负责分类、调度和聚合。
> 本段描述 Agent 调度逻辑，Step 1-4 的具体内容见上方「工作流」段落。

### 子项目分类

编排器读取 `project-manifest.json`，将子项目分为两组：

| 组 | 条件 | 典型子项目 |
|----|------|-----------|
| 后端组 | `type = "backend"` | api-backend |
| 前端组 | 其余所有类型 | admin, web-customer, web-mobile, mobile-native |

### Phase A — 后端 Agent

启动 1 个 Agent 处理后端子项目，完整执行 Step 1 → Step 3 → Step 3.5 → Step 4（跳过 Step 2 原语识别）。

Agent 产出：
```
.allforai/project-forge/sub-projects/{backend-name}/
├── requirements.md    # Step 1
├── design.md          # Step 3 + Step 3.5 审查结果
└── tasks.md           # Step 4
```

### Phase B — 前端并行 Agent

后端 Agent 完成后，用**单条消息发出 N 个 Agent tool 调用**并行执行。
Agent tool 的屏障同步机制保证所有前端 Agent 完成后才继续到 Step 5。

每个前端 Agent 完整执行 Step 1 → Step 2 → Step 3 → Step 4（不执行 Step 3.5）。

每个 Agent 产出：
```
.allforai/project-forge/sub-projects/{frontend-name}/
├── requirements.md    # Step 1
├── design.md          # Step 2 (原语识别) + Step 3
└── tasks.md           # Step 4
```

### Agent prompt 模板

~~~
你是 design-to-spec 的并行执行器。

任务: 为子项目 {sub-project-name} 生成完整的 spec 文档。

执行步骤:
1. 用 Read 工具加载 ${CLAUDE_PLUGIN_ROOT}/skills/design-to-spec.md（仅参考规则和模板，不重复全局步骤）
2. 按 Step 1 (requirements) → Step 2 (原语识别, 仅前端) → Step 3 (design) [→ Step 3.5 仅后端] → Step 4 (tasks) 执行
3. 产出写入 .allforai/project-forge/sub-projects/{sub-project-name}/

子项目信息:
- name: {name}
- type: {type}
- tech_stack: {tech_stack}
- assigned_modules: {modules}

上下文:
- project-manifest.json: .allforai/project-forge/project-manifest.json
- forge-decisions.json: .allforai/project-forge/forge-decisions.json（technical_spikes + coding_principles）
- 产品设计产物: .allforai/product-map/, .allforai/screen-map/ 等
- 后端 design.md: .allforai/project-forge/sub-projects/{backend-name}/design.md（仅前端 Agent 引用）
{自动模式标记: __orchestrator_auto: true（若自动模式激活）}

重要:
- 仅处理本子项目，不读写其他子项目的产出目录
- 按端差异化规则生成（参考 design-to-spec.md 的「各端差异化 Spec 生成」表格）
- 遵循两阶段加载（先 index 再 full data）
- 前端 Agent: API 调用必须引用后端 design.md 中已定义的端点 ID
- 预置脚本优先: 检查 ${CLAUDE_PLUGIN_ROOT}/scripts/ 是否有可用脚本
~~~

Agent 调用参数：

| Agent | Phase | 子项目类型 | 执行步骤 | 产出目录 |
|-------|-------|-----------|---------|---------|
| 后端 Agent | A | backend | Step 1→3→3.5→4 | `.allforai/project-forge/sub-projects/{backend}/` |
| 前端 Agent 1 | B | admin | Step 1→2→3→4 | `.allforai/project-forge/sub-projects/{admin}/` |
| 前端 Agent 2 | B | web-customer | Step 1→2→3→4 | `.allforai/project-forge/sub-projects/{web}/` |
| 前端 Agent N | B | mobile-native | Step 1→2→3→4 | `.allforai/project-forge/sub-projects/{mobile}/` |

### 错误处理

~~~
Phase A (后端 Agent):
  成功 → 进入 Phase B
  失败 →
    向用户报告错误原因
    询问: 重试 / 中止
    注: 后端失败不可跳过（前端依赖后端 design.md）

Phase B (前端 Agent 并行):
  全部成功 → 进入 Step 5
  部分失败 →
    成功的 Agent: 正常收集产出
    失败的 Agent: 记录错误信息
    向用户报告:
      "前端并行执行结果:
       ✓ admin: 完成 (requirements: N, design: N API, tasks: N)
       ✗ web-customer: 失败 — {错误原因}
       ✓ mobile: 完成 (requirements: N, design: N 页面, tasks: N)"
    询问:
      1. 重试失败的子项目（仅重跑失败的 Agent）
      2. 跳过继续到 Step 5（依赖分析标注缺失子项目）
      3. 中止流程
  全部失败 →
    向用户报告所有错误
    询问: 全部重试 / 中止

自动模式:
  后端 Agent 失败 → ERROR（停）
  前端 Agent 部分失败 → WARNING（记日志继续到 Step 5）
  前端 Agent 全部失败 → ERROR（停）
~~~

### resume 模式下的并行处理

~~~
resume 模式检测 Step 1-4 完成状态:
  检测方式: 检查 .allforai/project-forge/sub-projects/{name}/ 下三件套
    - requirements.md 存在
    - design.md 存在
    - tasks.md 存在
  三件全 → 该子项目已完成

  判定:
    后端 + 所有前端三件套全存在 → 跳过 Step 1-4，进入 Step 5
    后端三件套存在，部分前端缺失 → 跳过 Phase A，Phase B 仅启动缺失子项目的 Agent
    后端三件套缺失 → 从 Phase A 重新开始（全量执行）
~~~

### 单子项目退化

仅有 1 个后端子项目、无前端子项目时，Phase B 不启动任何 Agent，自动退化为纯串行执行。

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
  - _Leverage: {existing-file-or-package}_   ← 引用现有文件或三方包；Phase 5 完成后会自动追加 SU-xxx 引用，无需预填
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
  ├── requirements.md        # Step 1 输出（人类可读）
  ├── requirements.json      # Step 1 输出（机器可读）
  ├── design.md              # Step 2+3 输出（人类可读）
  ├── design.json            # Step 2+3 输出（机器可读）
  ├── tasks.md               # Step 4 输出（人类可读）
  └── tasks.json             # Step 4 输出（机器可读）
```

---

## JSON 对应件（机器可读格式）

每个 Markdown 规格文件同时生成 JSON 对应件，供下游技能（task-execute、product-verify、shared-utilities）直接解析，避免正则匹配 Markdown 的脆弱性。

### requirements.json

```json
{
  "sub_project": "backend",
  "generated_at": "ISO8601",
  "requirements": [
    {
      "id": "R-001",
      "title": "用户注册",
      "source_refs": ["T-001", "F-001"],
      "priority": "high",
      "acceptance_criteria": ["..."],
      "constraints": ["CN-001"]
    }
  ]
}
```

### design.json

```json
{
  "sub_project": "backend",
  "generated_at": "ISO8601",
  "api_endpoints": [
    {
      "method": "POST",
      "path": "/api/v1/users",
      "requirement_ref": "R-001",
      "request_schema": {},
      "response_schema": {},
      "error_codes": []
    }
  ],
  "data_models": [
    {
      "name": "User",
      "table": "users",
      "fields": [],
      "requirement_ref": "R-001",
      "indexes": [],
      "relations": []
    }
  ],
  "architecture_layers": {}
}
```

### tasks.json

```json
{
  "sub_project": "backend",
  "generated_at": "ISO8601",
  "tasks": [
    {
      "id": "BE-T001",
      "title": "实现用户注册 API",
      "batch": "B2",
      "files": ["internal/handler/user.go", "internal/service/user.go"],
      "requirements_ref": ["R-001"],
      "leverage": ["SU-001"],
      "guardrails": ["输入校验", "密码加密"],
      "risk": "low",
      "estimated_lines": 120
    }
  ],
  "batch_summary": {
    "B0": { "count": 2, "description": "Monorepo 初始化" },
    "B1": { "count": 5, "description": "共享工具库" },
    "B2": { "count": 15, "description": "数据模型 + API" }
  }
}
```

**生成规则**：
- JSON 和 Markdown 同步生成，JSON 为完整数据，Markdown 为人类摘要
- 下游技能优先读取 JSON（存在时），回退到解析 Markdown（向后兼容）
- JSON 文件路径：与 Markdown 同目录，仅扩展名不同（`requirements.md` → `requirements.json`）

---

## 6 条铁律

### 1. CORE 优先，DEFER 标记

仅 CORE 任务进入 tasks.md 的主体。DEFER 任务在末尾单独列出（标记 `[DEFERRED]`），不进入执行计划。CUT 任务完全排除。

### 2. 两阶段加载

先读 index 文件（< 5KB）确定范围，再按需加载 full 数据。大型产品可节省 90%+ token。

### 3. 按端差异化

不同子项目类型的 spec 内容截然不同。后端无 UI 层，前端无 API 层。不生成不属于该端的内容。

### 4. 任务必须原子

每任务 1-3 文件、15-30 分钟、单一目的。不出现"实现 XX 系统"这样的宽泛任务。

### 5. 跨项目依赖显式声明

后端 B2 → 前端 B4 的依赖、共享类型的依赖，都在 Step 5 中显式声明并写入 execution_order。

### 6. 并行 Agent 产出隔离

Phase A/B 的并行 Agent 各自写入独立子项目目录（`.allforai/project-forge/sub-projects/{name}/`），不读写其他 Agent 的产出。唯一跨 Agent 引用：前端 Agent 只读后端 design.md（API 端点定义），不修改。
