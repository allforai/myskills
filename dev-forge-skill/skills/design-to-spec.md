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
2. **design.md** — 接口定义 / 页面路由 / 数据模型 / 组件架构 / 时序图
3. **event-schema.md** — 埋点事件定义 / 漏斗 / 北极星指标
4. **tasks.md** — 原子任务列表，按开发层分 Batch（B0-B5）
5. **task-context.json** — 任务上下文预计算（旅程位置 / 情绪 / 约束溯源 / 消费者 / 验证建议）

---

## 定位

```
project-setup（架构层）   design-to-spec（规格层）   project-scaffold（实现层）
拆子项目/选技术栈         生成 spec 文档/任务列表      生成代码骨架
manifest.json            req + design + events + tasks  实际文件和目录
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
- `"{database} schema design best practices"`
- `"{protocol} interface naming conventions {year}"`（protocol = REST/GraphQL/gRPC/等）
- `"clean architecture {language} example {year}"`

**4E+4V 重点**（design-to-spec 是产品→工程的核心桥梁）：
- **E2 Provenance**: requirements.md 每个需求项标注 `_Source: T001, F001, CN001_`
- **E3 Guardrails**: task.rules → Business Rules 节；task.exceptions → Error Scenarios 节；task.audit → Audit Requirements 节；task.sla → SLA 标注；task.approver_role → Approval 节
- **E4 Context**: task.value → Value 注释；task.risk_level → Risk 标签；task.frequency → Priority
- **4V**: 高频+高风险任务的 design.md 至少覆盖 api + data + behavior 三个视角

**OpenRouter 交叉审查**（design.md 是全链路咽喉，此处质量提升下游全受益）：
- **`interface_design_review`** (GPT) — 后端 design.md 生成后，发送接口定义给 GPT 审查：
  - 接口命名是否遵循目标协议惯例（REST: 资源复数 + HTTP 动词；GraphQL: Query/Mutation 命名；gRPC: Service/RPC 命名）
  - 请求/响应结构与数据模型的字段一致性
  - 缺失的常见接口（列表查询、批量操作、健康检查/探针）
  - 错误响应格式统一性
  - 输出: `{ "issues": [{ "interface", "type", "suggestion" }], "missing": [...] }`
- **`data_model_review`** (DeepSeek) — 数据模型设计生成后，发送给 DeepSeek 检查：
  - 数据建模合理性（RDBMS: 范式与反范式权衡；Document DB: 嵌套 vs 引用；KV: key 设计与访问模式）
  - 查询性能（缺失索引、N+1 风险、热点 key）
  - 关联完整性（孤立实体、循环依赖、级联规则）
  - 命名一致性（实体名/字段名风格统一）
  - 输出: `{ "violations": [{ "entity", "field", "type", "fix" }] }`
- 审查结果合并到 design.md 的 `## Review Notes` 附录（仅有问题时生成）
- OpenRouter 不可用 → 跳过审查，不阻塞生成

---

## 规格生成原则

> 以下原则在各步骤中强制执行，生成的 spec 必须符合这些规则。

| 原则 | 对应步骤 | 具体规则 |
|------|---------|---------|
| 分层依赖方向 | Step 4 | B1(数据模型) → B2(业务逻辑/接口) → B3(UI/展示层) → B4(集成) 严格内→外。展示层不直接访问数据层，必须经过业务逻辑层 |
| 单一职责任务 | Step 4 | 每个原子任务 1-3 文件、15-30 分钟、单一可测结果。禁止出现"实现 XX 系统"这种宽泛任务 |
| 隔离外部调用 | Step 3 | 外部 API/SDK 调用封装为独立 service/adapter 文件，业务层通过接口调用，不直接 import SDK |
| 接口设计遵循目标协议惯例 | Step 3 | REST: 资源复数 + HTTP 动词 + `{ code, message, details }` 错误格式；GraphQL: schema-first + Query/Mutation 分离；gRPC: proto-first + status code；其他协议按其社区最佳实践 |
| 数据模型遵循存储引擎最佳实践 | Step 3 | RDBMS: 范式化设计（反范式需标注理由）；Document DB: 嵌套 vs 引用按访问模式决策；KV: key 结构按查询模式设计。design.md 中标注建模决策依据 |
| 用户故事按角色组织 | Step 1 | requirements.md 按角色分组（"As a {role}"），每组内按 frequency 排序（高频在前） |
| 后端优先生成顺序 | Step 3 | **先生成后端 design.md（数据模型→接口定义），再生成前端 design.md（引用已定义的接口）**。前端 design 中的接口调用必须引用后端 design 中的定义 |
| 设计分层展开 | Step 3 | design.md 从数据模型开始，逐层展开到接口 → 页面 → 组件。每层引用上一层定义 |
| 输入验证在边界层 | Step 3 | 所有外部输入在接入层统一验证（whitelist 模式）。防注入（参数化查询/转义/沙箱）。认证在接入层声明，不在业务代码中手动检查 |
| 统一错误处理 | Step 3 | 全局错误拦截（中间件/拦截器/错误边界），返回统一格式。业务错误用自定义错误类型（含错误码），日志分级 ERROR/WARN/INFO，敏感信息不进日志 |
| 测试与实现对称 | Step 4 | 每个 B2 业务逻辑/接口任务必须对应 B5 测试任务。测试间无共享可变状态，每条测试独立可运行 |
| 性能基线内建 | Step 3 | 集合查询强制分页/游标（默认批次 ≤ 50 条），高频查询路径建索引，避免 N+1 问题。大数据量操作走异步任务 |
| 写操作幂等 | Step 3 | 创建类操作支持幂等键（协议级 header 或业务唯一约束），更新类操作使用乐观锁（version 字段或条件更新），并发冲突返回对应协议的冲突状态 |
| 前端 CRUD 套路一致 | Step 3 | 同类型子项目的列表/新建/编辑/删除/详情必须使用相同组件套路和数据流模式。详见「前端 CRUD 实现套路」章节 |
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
| experience-map.json | design.md | 每 screen = 1 页面/组件规格 | E1 |
| screen.states | design.md | empty/loading/error/permission_denied → 界面四态设计 | E3 |
| screen.actions | design.md | 每 action → 1 接口定义（后端）/ 1 交互规格（前端） | E1 |
| action.on_failure | design.md | 操作失败 → UI 反馈设计 | E3 |
| action.exception_flows | design.md | 任务异常 → UI 响应映射（1-to-1，from experience-map Step 2） | E3 |
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
| task.approver_role | requirements.md + design.md | 审批流需求 + 审批接口 + 状态流转 | E3 |
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
| requirements 侧重 | 接口合约、并发、幂等、事务一致性 |
| design 侧重 | 接口设计、数据模型（Entity + 关系）、中间件/拦截器链 |
| 非功能需求 | 吞吐量、事务一致性、错误响应规范 |
| 从 experience-map 取 | 不取（无 UI） |
| 从 ui-design 取 | 不取 |

### admin

| 维度 | 内容 |
|------|------|
| requirements 侧重 | CRUD 完整性、批量操作、权限矩阵 |
| design 侧重 | 页面布局、组件树、表单验证规则、CRUD 套路（见「前端 CRUD 实现套路」） |
| 非功能需求 | 角色权限矩阵、审计日志 |
| 从 experience-map 取 | actions → CRUD 页面规格；states → 四态设计；on_failure + exception_flows → 错误反馈；validation_rules → 表单 Schema；requires_confirm → 确认弹窗 |
| 从 ui-design 取 | 全量设计 token |
| CRUD 套路 | design.md 必须包含「CRUD 实现套路」章节，指定列表/表单/删除/详情的组件选型和数据流（详见下方独立章节） |

### web-customer

| 维度 | 内容 |
|------|------|
| requirements 侧重 | SEO、加载速度、可访问性 |
| design 侧重 | SSR/SSG 策略、meta 标签、结构化数据 |
| 非功能需求 | Lighthouse 分数、Core Web Vitals |
| 从 experience-map 取 | actions → 页面组件规格；states → 四态设计（empty 状态需 SEO 友好）；on_failure + exception_flows → 用户友好错误页；validation_rules → 表单 Schema |
| 从 ui-design 取 | 全量设计 token + 性能约束 |

### web-mobile

| 维度 | 内容 |
|------|------|
| requirements 侧重 | 触屏可用性、离线场景 |
| design 侧重 | 移动优先布局、PWA 配置 |
| 非功能需求 | 弱网容忍、Service Worker |
| 从 experience-map 取 | actions → 触屏交互规格；states → 四态设计（loading 需骨架屏、error 需离线提示）；on_failure → 弱网重试 UI；validation_rules → 移动端表单验证 |
| 从 ui-design 取 | 移动适配的设计 token |

### mobile-native (React Native / Flutter)

| 维度 | 内容 |
|------|------|
| requirements 侧重 | 离线同步、推送、设备权限 |
| design 侧重 | 导航栈（RN: React Navigation / Flutter: GoRouter）、原生组件、存储策略 |
| 非功能需求 | 电池/流量优化、后台任务 |
| 从 experience-map 取 | actions → Screen 组件规格（RN: Screen 组件 / Flutter: Screen Widget）；states → 四态设计（离线态额外处理）；on_failure + exception_flows → 原生错误提示；validation_rules → 表单验证 |
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

> Step 2 识别出原语后，按需读取详细映射表：`${CLAUDE_PLUGIN_ROOT}/docs/primitive-impl-map.md`
> 包含：22 种原语 × Web（UmiJS/Vue3/Next.js/Nuxt）+ 原生/桌面（iOS/Android/Flutter/RN/Windows）共 9 技术栈实现。

---

### 图片字段处理规范

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/field-specs/image-field.md`
> 包含：上传策略（预签名URL/预上传/Multipart）、编辑回填（10技术栈）、多图管理规则、移动端选图入口、显示尺寸规格（服务端URL参数）。
### 视频字段处理规范

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/field-specs/video-field.md`
> 包含：上传策略（简单POST/分片/预签名URL）、转码状态轮询（10技术栈）、编辑回填（10技术栈）、封面图处理。
### 页面交互类型分类

> **类型定义与推断规则**：见 `product-design-skill/docs/interaction-types.md`（单一事实来源）。
> experience-map Step 1 已为每个 screen 标注 `interaction_type` 字段，design-to-spec 直接读取使用。

37 种交互类型（MG/CT/EC/WK/RT/SB/SY/TU）完整定义见 `product-design-skill/docs/interaction-types.md`。experience-map Step 1 已为每个 screen 标注 `interaction_type` 字段，design-to-spec 直接读取使用。

---

### 按技术栈的各类型套路

#### UmiJS + Ant Design Pro（admin / merchant 类）

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/tech-stack-patterns/umijs.md`
> 包含：公共基础层（请求层/枚举/字段→组件映射）+ MG1~MG8 全类型套路。
#### Next.js（web-customer 类）

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/tech-stack-patterns/nextjs.md`
> 包含：C端页面套路概览 + CT1 Feed流 / EC1商品详情 / EC2购物车 / WK1 IM 详细实现。
#### Flutter（mobile-native 类）

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/tech-stack-patterns/flutter.md`
> 包含：移动端套路概览 + CT1 Feed流 / EC1商品详情 / WK1 IM 详细实现。
### 多语言实现规范

> 通用规范见 `docs/interaction-types.md`。以下为各技术栈的实现差异。

| 技术栈 | i18n 方案 | 翻译文件位置 | hook/函数 |
|--------|----------|-------------|-----------|
| UmiJS (admin/merchant) | `@umijs/max` 内置 | `src/locales/` | `useIntl()` + `intl.formatMessage()` |
| Next.js (website) | `next-intl` | `src/messages/` | `useTranslations()` |
| Flutter (mobile) | `flutter_localizations` | `lib/l10n/*.arb` | `AppLocalizations.of(context)` |

**通用规则**（所有技术栈）：
- 所有用户可见文本通过 i18n 函数获取，禁止硬编码
- 新增文本必须同步所有语言文件
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
    experience-map.json → 界面 id/name/action_count（可选）
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
    Agent(backend): Step 1 → Step 2 → Step 3 → Step 3.5 → Step 3.8 → Step 4 → Step 4.5
    ↓ 完成后
  Phase B — 前端并行 Agent（单条消息发出 N 个 Agent 调用）:
    ┌── Agent(前端1): Step 1 → Step 2 → Step 3 → Step 3.8 → Step 4 → Step 4.5
    ├── Agent(前端2): Step 1 → Step 2 → Step 3 → Step 3.8 → Step 4 → Step 4.5
    └── Agent(前端N): Step 1 → Step 2 → Step 3 → Step 3.8 → Step 4 → Step 4.5
    全部完成 ↓
  以下 Step 1-4.5 描述每个 Agent 内部执行的步骤内容:
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
Step 2.5: 组件规格导入（component-spec.json 存在时执行）
  **触发条件**：`<BASE>/ui-design/component-spec.json` 存在
  **跳过**：文件不存在 → 直接进入 Step 3（向后兼容）

  **Layer 1（通用，始终执行）**：
  1. 读取 `component-spec.json` 的 `shared_components`
  2. 对每个共享组件：
     a. 从 `primitive-impl-map.md` 查找当前技术栈的 primitives 实现
     b. 写入 design.md 的 `## 共享组件` 章节：
        - 组件名、出现屏幕、Props 接口
        - 交互原语 + 技术栈实现方案
        - 变体矩阵（size/state）
        - a11y 要求（role、aria 属性、键盘导航）
  3. 对 `screen_components` 中的每个屏幕：
     将 used_shared + page_specific 写入对应页面规格
  4. 生成键盘导航矩阵写入 design.md

  **Layer 2（Stitch 增强，`stitch-index.json` 存在且有 success 屏幕时）**：
  5. 读取 `stitch-index.json`
  6. 对每个 `status=success` 的屏幕：
     a. 读取 `stitch/*.html`，提取精确 DOM 结构
     b. 提取内联样式 → design token 映射
     c. 补充 design.md 的组件结构（增强 Layer 1 的推断）
  7. 记录 pipeline-decision

  ↓
Step 3: Design 生成（API-first 策略）
  **原则: 先表结构、后 API、再展开**
  每个 Agent 对其子项目，基于 tech-profile 映射:
    所有端共通（最先生成）:
      entities → 数据模型 / 表结构设计（ER 图 Mermaid）
      entity.fields → 字段类型 + 约束 + 索引
      entity.relations → 外键 + 关联关系
    backend（数据模型之后）:
      tasks → 接口设计（按目标协议生成：REST 路由 / GraphQL schema / gRPC proto / 等）
      约束冲突校验（每个接口生成后立即检查）:
        对每个接口定义，读取对应 task 的 rules + exceptions 字段:
        - 若 rules 含「本地处理」「离线」「不存库」「客户端缓存」等关键词
          → 该任务不应生成服务端接口，标记 `[LOCAL_ONLY]` 并跳过
        - 若 rules 含分页/筛选约束（「每页」「分页」「筛选」「排序」「搜索」）
          → 集合查询接口必须包含对应的分页/筛选参数
        - 若 exceptions 含特定错误场景 → 接口的错误响应必须覆盖
      集合查询参数强制提取:
        集合查询类接口生成时，强制读取对应 task 的:
        - main_flow → 提取筛选/搜索/排序操作描述
        - rules → 提取分页规则（默认批次大小、最大批次）、筛选字段、排序字段
        - 生成完整的查询参数文档（分页、排序、筛选）
        - 缺失时使用默认值: 每批 ≤ 20 条, 上限 50 条
      constraints → 中间件/拦截器链设计
      flows → 后端时序图
    前端类 (admin/web-customer/web-mobile):
      多后端服务连接推导:
        读取 manifest 中后端子项目/服务拓扑:
        - 单后端服务 → 生成单一 API 客户端实例
        - 多后端服务（不同地址/端口/协议）→ 自动推导多客户端架构:
          每个后端服务 → 1 个独立客户端实例（按服务职责命名）
          在 design.md 的「请求层」章节写明各实例的连接配置 + 负责的端点/接口范围
          tasks.md B1 中生成对应的客户端初始化任务
      screens → 页面路由 + 组件架构
      screen.states → 界面四态设计（empty/loading/error/permission_denied）
      actions → 交互规格（引用已定义的后端接口）
      action.on_failure + exception_flows → 操作异常 UI 反馈设计
      action.validation_rules → 表单验证 Schema
      action.requires_confirm → 确认弹窗组件规格
      flows → 前端状态流转图
      ui-design-spec → 设计 token 引用
    mobile-native:
      screens → 导航栈 + Screen 组件规格
      screen.states → 界面四态设计（同上）
      actions → 原生交互规格（引用已定义的后端接口）
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
    → 输出进度: 「{name}/design.md ✓ ({N} 接口, {M} 页面)」（不停，汇总到 Step 6）
  **生成顺序**: 后端 Agent (Phase A) 先于前端 Agent (Phase B)，确保前端 design 可直接引用后端接口定义
  ↓
Step 3.5: Design 交叉审查（由后端 Agent 在 Phase A 内执行，OpenRouter 可用时）
  后端 design.md 生成后，触发两项交叉审查:
  审查 A — 接口设计审查 (GPT):
    提取 design.md 中所有接口定义（签名+请求/响应结构）
    调用: mcp__plugin_product-design_ai-gateway__ask_model(task: "structured_output", model_family: "gpt")
    审查: 协议惯例、数据结构一致性、缺失接口、错误响应统一
    输出: issues[] + missing[]
  审查 B — 数据模型审查 (DeepSeek):
    提取 design.md 中 ER 设计（Mermaid + 字段定义）
    调用: mcp__plugin_product-design_ai-gateway__ask_model(task: "technical_validation", model_family: "deepseek")
    审查: 建模合理性、查询性能、关联完整性、命名一致性
    输出: violations[]
  结果处理:
    有问题 → 在 design.md 末尾追加 ## Review Notes 附录（按问题严重度排列）
    无问题 → 不追加
    → 输出进度: 「Step 3.5 交叉审查 ✓ 接口 {N} issues, 数据模型 {M} violations」
  OpenRouter 不可用 → 跳过，输出: 「Step 3.5 ⊘ OpenRouter 不可用，跳过交叉审查」
  ↓
Step 3.8: 埋点规格生成（Event Schema）
  基于 requirements 和 design 产物，自动推导埋点方案。

  **输入**：
  - requirements.json（用户故事 + 验收标准）
  - design.json（API 端点 / 页面路由）
  - task-inventory.json（frequency、risk_level）
  - experience-map.json（screen actions、on_failure）

  **生成规则**：

  1. **关键事件推导**：
     - 每个 P0/P1 需求 → 至少 1 个核心事件
     - 每个页面 → page_view 事件
     - 每个表单提交 → form_submit 事件
     - 每个关键 CTA → click 事件
     - 每个 API 错误响应 → error 事件
     - 每个异常流（on_failure） → failure 事件

  2. **漏斗定义**：
     - 从 business-flows.json 提取核心流程
     - 每个流程 → 1 个漏斗（funnel）
     - 漏斗节点 = 流程中的关键步骤

  3. **事件属性规范**：
     每个事件必须包含：
     - event_name: snake_case 命名
     - event_category: page_view | user_action | form | error | system
     - properties: { key: type } 映射
     - trigger: 触发条件描述
     - requirement_ref: 关联需求 ID
     - screen_ref: 关联界面 ID（前端事件）

  4. **北极星指标关联**：
     - 从 product-concept.json 提取 success_metrics（如有）
     - 每个北极星指标 → 关联事件 + 计算公式

  **输出**：
  ```
  .allforai/project-forge/sub-projects/{name}/event-schema.json
  .allforai/project-forge/sub-projects/{name}/event-schema.md
  ```

  **event-schema.json 结构**：
  ```json
  {
    "sub_project": "admin",
    "generated_at": "ISO8601",
    "events": [
      {
        "event_name": "user_registration_completed",
        "event_category": "user_action",
        "properties": {
          "user_id": "string",
          "registration_method": "string",
          "time_to_complete_ms": "number"
        },
        "trigger": "用户完成注册表单提交且服务端返回成功",
        "requirement_ref": "R-001",
        "screen_ref": "S-003",
        "priority": "P0"
      }
    ],
    "funnels": [
      {
        "funnel_name": "user_onboarding",
        "flow_ref": "F-001",
        "steps": [
          { "step": 1, "event": "landing_page_view", "label": "落地页" },
          { "step": 2, "event": "registration_started", "label": "开始注册" },
          { "step": 3, "event": "registration_completed", "label": "完成注册" },
          { "step": 4, "event": "first_action_completed", "label": "首次操作" }
        ]
      }
    ],
    "metrics": [
      {
        "metric_name": "activation_rate",
        "formula": "count(first_action_completed) / count(registration_completed)",
        "target": "≥ 60%",
        "related_events": ["registration_completed", "first_action_completed"]
      }
    ]
  }
  ```

  **event-schema.md** 内容：
  - 事件清单表（event_name | category | trigger | priority）
  - 漏斗可视化（Mermaid flowchart）
  - 指标定义表（metric | formula | target）

  → 写入 .allforai/project-forge/sub-projects/{name}/event-schema.json + event-schema.md
  → 输出进度: 「{name}/event-schema ✓ ({N} events, {M} funnels, {K} metrics)」（不停，汇总到 Step 6）
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
  B5 中应包含埋点验证任务：验证关键事件是否正确触发、属性是否完整、漏斗是否连通。
  → Batch 结构因子项目类型而异（见下文）
  → 写入 .allforai/project-forge/sub-projects/{name}/tasks.md
  → 输出进度: 「{name}/tasks.md ✓ ({N} 任务, B0-B5)」（不停，汇总到 Step 4.5）

  当 component-spec.json 存在时，B3 任务分批调整：

  **B3 Round 1**（共享组件优先）：
  - 实现 component-spec.json 中的 shared_components
  - 每个共享组件一个任务，含 variants + a11y 实现
  - 任务元数据追加：`component_spec_ref: true`

  **B3 Round 2+**（页面组件）：
  - 页面级组件引用 Round 1 已实现的共享组件
  - 如有 Stitch HTML → 任务追加 `stitch_ref: screen_id` + `stitch_html: 文件路径`

  ↓
Step 4.5: 任务上下文预计算（Task Context）
  为每个任务预计算完整上下文包，供 task-execute 消费，减少"概念→代码"失真。

  **输入**：
  - tasks.json（本步骤 Step 4 产出）
  - requirements.json（Step 1 产出）
  - design.json（Step 3 产出）
  - use-case-tree.json（如有）
  - journey-emotion.json（如有）
  - constraints.json（如有）
  - business-flows.json（如有）
  - cross-project-dependencies.json（Step 5 产出，第二轮补充）

  **生成规则**：

  对 tasks.json 中每个任务，计算以下上下文字段：

  1. **journey_position**（旅程位置）：
     - 从 use-case-tree.json 查找包含该任务 source_ref 的用例
     - 提取：use_case_id, use_case_name, step_index, total_steps, prev_task, next_task
     - 无匹配 → `null`

  2. **emotion_context**（情绪上下文）：
     - 从 journey-emotion.json 查找该任务关联触点的情绪
     - 提取：emotion（期待/满意/焦虑/沮丧）, emotion_intensity(1-5), design_implication
     - 无匹配 → `null`

  3. **constraint_rationale**（约束溯源）：
     - 对 task.guardrails 中每条规则，反查 constraints.json 找到来源约束
     - 输出：{ rule_text: string, constraint_refs: [{ id, name, reason, severity }] }

  4. **consumers**（消费者清单）：
     - 对后端 API 任务：从其他子项目的 design.json 扫描引用该端点的前端页面
     - 输出：[{ sub_project, screen_id, usage_description }]
     - 前端任务 → `[]`

  5. **frequency_weight**（流量权重）：
     - 从 task-inventory.json 提取 frequency 字段
     - 映射：daily+ → "critical", weekly → "high", monthly → "medium", rare → "low"

  6. **risk_level**（风险等级）：
     - 直接从 task-inventory.json 提取

  7. **verification_hint**（验证建议）：
     - frequency_weight=critical + risk_level=high → "integration_test + load_test"
     - frequency_weight=critical → "integration_test"
     - risk_level=high → "unit_test + code_review"
     - 其他 → "unit_test"

  8. **flow_position**（业务流位置）：
     - 从 business-flows.json 查找包含该任务的流程
     - 提取：flow_id, flow_name, position_in_flow, upstream_tasks, downstream_tasks

  **输出**：
  ```
  .allforai/project-forge/sub-projects/{name}/task-context.json
  ```

  ```json
  {
    "sub_project": "backend",
    "generated_at": "ISO8601",
    "contexts": [
      {
        "task_id": "BE-T001",
        "journey_position": {
          "use_case_id": "UC-003",
          "use_case_name": "用户下单流程",
          "step_index": 2,
          "total_steps": 5,
          "prev_task": "BE-T000",
          "next_task": "BE-T002"
        },
        "emotion_context": {
          "emotion": "anxious",
          "emotion_intensity": 4,
          "design_implication": "需要明确的进度反馈和错误恢复"
        },
        "constraint_rationale": [
          {
            "rule_text": "确认后不可变",
            "constraint_refs": [
              { "id": "CN-005", "name": "GDPR 合规", "reason": "审计追踪完整性", "severity": "critical" },
              { "id": "CN-008", "name": "反欺诈", "reason": "防止订单篡改", "severity": "high" }
            ]
          }
        ],
        "consumers": [
          { "sub_project": "web-customer", "screen_id": "S-003", "usage_description": "订单创建表单提交" },
          { "sub_project": "mobile-app", "screen_id": "S-M012", "usage_description": "移动端下单" }
        ],
        "frequency_weight": "critical",
        "risk_level": "high",
        "verification_hint": "integration_test + load_test",
        "flow_position": {
          "flow_id": "F-002",
          "flow_name": "订单处理流程",
          "position_in_flow": 2,
          "upstream_tasks": ["BE-T000"],
          "downstream_tasks": ["BE-T002", "BE-T005"]
        }
      }
    ]
  }
  ```

  → 写入 .allforai/project-forge/sub-projects/{name}/task-context.json
  → 输出进度: 「{name}/task-context.json ✓ ({N} tasks enriched, {M} with journey, {K} with constraints)」（不停，汇总到 Step 6）
  ↓
Step 5: 跨子项目依赖分析
  识别跨项目依赖:
    后端接口定义 → 前端客户端
    共享类型定义 → 公共类型包
    后端 B2 完成 → 前端 B4 才能开始（切换开发桩 → 真实后端）
  生成跨项目任务排序 → execution_order
  → 写入 `.allforai/project-forge/cross-project-dependencies.json`（依赖图 + execution_order）
  → **不修改** project-manifest.json（上游产物只读）
  → 输出进度: 「跨项目依赖图 ✓ ({N} 条依赖)」（不停，汇总到 Step 6）
  ↓
Step 6: 阶段末汇总确认
  展示全部生成结果摘要:

  Phase A (后端):
  | 子项目 | requirements | design | tasks | task-context | event-schema | Step 3.5 审查 |
  |--------|-------------|--------|-------|-------------|--------------|--------------|
  | {backend} | {N} 需求项 | {N} 接口 | {N} 任务 | {N} enriched | {N} events | 接口 {N} issues, 模型 {M} violations |

  Phase B (前端并行):
  | 子项目 | requirements | design | tasks | task-context | event-schema | 状态 |
  |--------|-------------|--------|-------|-------------|--------------|------|
  | {admin} | {N} 需求项 | {N} 页面 | {N} 任务 | {N} enriched | {N} events | 完成/失败 |
  | {web} | {N} 需求项 | {N} 页面 | {N} 任务 | {N} enriched | {N} events | 完成/失败 |
  | {mobile} | {N} 需求项 | {N} 页面 | {N} 任务 | {N} enriched | {N} events | 完成/失败 |

  跨项目依赖: {N} 条
  执行顺序: B0 → B1(并行) → B2 → B3(并行) → B4 → B5
  总任务数: CORE {N} + DEFER {M}

  → 输出汇总进度「Phase 2 ✓ {N} 子项目 × 5 文档 (Phase A 串行 + Phase B 并行), CORE {M} 任务」（不停）
```

### 规模自适应

根据子项目任务数自动调整 Step 6 展示策略：
- **小规模**（≤30 tasks/子项目）：逐条展示完整任务列表
- **中规模**（31-80 tasks/子项目）：按 Batch 分组摘要，仅展示 HIGH-risk 任务详情
- **大规模**（>80 tasks/子项目）：统计概览（任务分布、风险分布、覆盖率）+ 仅列 HIGH-risk 项

---

## 并行执行编排 & 任务 Batch 结构

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/execution-batches.md`
> 包含：子项目分类（后端/前端组）、Phase A/B Agent 编排、Agent prompt 模板、错误处理、resume 模式、Batch 0-5 结构、各端 Batch 内容差异。

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
  ├── event-schema.md        # Step 3.8 输出（人类可读）
  ├── event-schema.json      # Step 3.8 输出（机器可读）
  ├── tasks.md               # Step 4 输出（人类可读）
  ├── tasks.json             # Step 4 输出（机器可读）
  └── task-context.json      # Step 4.5 输出（任务上下文预计算）
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
  "sub_project": "admin",
  "generated_at": "ISO8601",
  "shared_components": [
    {
      "primitive": "VirtualList",
      "used_by_screens": ["S001", "S005", "S012"],
      "suggested_name": "<DataList>",
      "tech_stack_impl": "ProTable 内置虚拟化"
    },
    {
      "primitive": "StateMachine",
      "used_by_screens": ["S003", "S008"],
      "suggested_name": "useStateMachine",
      "tech_stack_impl": "自定义 hook（枚举 + 合法转换 Map）"
    }
  ],
  "api_endpoints": [
    {
      "id": "EP-001",
      "signature": "CreateUser",
      "requirement_ref": "R-001",
      "request_schema": {},
      "response_schema": {},
      "error_responses": [],
      "protocol_detail": {}
    }
  ],
  "data_models": [
    {
      "name": "User",
      "storage": "users",
      "fields": [],
      "requirement_ref": "R-001",
      "indexes": [],
      "relations": []
    }
  ],
  "architecture_layers": {}
}
```

**`shared_components`**（Step 2 产出，仅前端子项目）：
- `primitive`：行为原语名（来自 `interaction-types.md` 行为原语索引）
- `used_by_screens`：使用该原语的界面 ID 列表（`screen_id` from experience-map.json）
- `suggested_name`：建议的组件/hook 封装名称
- `tech_stack_impl`：该技术栈下的具体实现方案（来自行为原语实现映射表）

> 后端子项目 `shared_components` 为空数组 `[]`（跳过 Step 2）。

### tasks.json

```json
{
  "sub_project": "backend",
  "generated_at": "ISO8601",
  "tasks": [
    {
      "id": "BE-T001",
      "title": "实现用户注册接口",
      "batch": "B2",
      "files": ["{按技术栈约定的接口层文件}", "{按技术栈约定的业务逻辑文件}"],
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

后端 B2 → 前端 B4 的依赖、共享类型定义的依赖，都在 Step 5 中显式声明并写入 execution_order。

### 6. 并行 Agent 产出隔离 + 类型契约传递

Phase A/B 的并行 Agent 各自写入独立子项目目录（`.allforai/project-forge/sub-projects/{name}/`），不读写其他 Agent 的产出。跨 Agent 数据流严格单向：编排器从后端产物提取类型契约（data_models + request/response schema + 类型定义），注入前端 Agent prompt，确保数据结构字段命名、ID vs 名称等与后端完全一致。前端 Agent 不自行推断后端已定义的数据结构。
