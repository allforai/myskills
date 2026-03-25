---
name: design-to-spec
description: >
  Use when the user wants to "convert design to spec", "generate requirements from product map",
  "create tasks from design", "design to specification", "设计转规格", "生成需求文档",
  "生成任务列表", "从产品设计产物生成开发规格", "产物转换",
  or needs to transform product-design artifacts into per-sub-project requirements, design docs, and atomic task lists.
  Also handles shared-utilities analysis (cross-task pattern resonance, third-party library selection, B1 task injection).
  Requires project-manifest.json (from project-setup) and product-map artifacts.
version: "4.1.0"
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

如果上游判定项目为 `consumer` 或 `mixed`，design-to-spec 还必须把“用户端成熟度要求”翻译成可执行规格与任务，而不是只输出页面实现任务。

---

## 定位

```
project-setup（架构层）   design-to-spec（规格层）   task-execute（实现层）
拆子项目/选技术栈         生成 spec 文档/任务列表      逐任务执行代码
manifest.json            req + design + events + tasks  项目代码 + build-log
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

## 增强协议（网络搜索 + 4E+4V + OpenRouter + 闭环输入审计）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**闭环输入审计**（见 `product-design-skill/docs/skill-commons.md` §八）：Architect 生成 design.md 后，审查每个任务是否有**验收闭环**（"完成"标准是什么？谁验收？）。缺失验收条件 → Auditor V11 标记。

**网络搜索关键词**：
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
- **`interface_design_review`** (GPT) — 后端 design.md 生成后，发送接口定义给 GPT 审查
- **`data_model_review`** (DeepSeek) — 数据模型设计生成后，发送给 DeepSeek 检查
- 审查结果合并到 design.md 的 `## Review Notes` 附录（仅有问题时生成）
- OpenRouter 不可用 → 跳过审查，不阻塞生成

---

## 锻造-验证-闭环 (FVL) 概览

> 详细的 FVL 阶段定义（阶段 1-4、V1-V12、负空间推导、XV 交叉审查）见 `./docs/design-to-spec/auditor-validate.md`。

本技能采用基于 LLM 的生成与审计闭环。上游产物是不可逾越的硬约束。
- **阶段 1**: Agent 生成初稿（4D 工程维度覆盖）
- **阶段 1.5**: 负空间推导（异常补全 + B 类缺失功能回补）
- **阶段 2**: 4D/6V+V9+V10+V11+V12 审计
- **阶段 3**: XV 交叉审查（专家模型）
- **阶段 4**: 自动修正（最多 3 轮）

---

## 规格生成原则 (FVL 强制执行)

| 原则 | 具体规则 |
|------|---------|
| 分层依赖方向 | B1(数据模型) → B2(业务逻辑/接口) → B3(UI/展示层) → B4(集成) 严格内→外。展示层不直接访问数据层，必须经过业务逻辑层 |
| 单一职责任务 | 每个原子任务 1-3 文件、15-30 分钟、单一可测结果。禁止出现"实现 XX 系统"这种宽泛任务 |
| 隔离外部调用 | 外部 API/SDK 调用封装为独立 service/adapter 文件，业务层通过接口调用，不直接 import SDK |
| 接口设计遵循目标协议惯例 | REST: 资源复数 + HTTP 动词 + `{ code, message, details }` 错误格式；GraphQL: schema-first + Query/Mutation 分离；gRPC: proto-first + status code；其他协议按其社区最佳实践 |
| 数据模型遵循存储引擎最佳实践 | RDBMS: 范式化设计（反范式需标注理由）；Document DB: 嵌套 vs 引用按访问模式决策；KV: key 结构按查询模式设计。design.md 中标注建模决策依据 |
| 用户故事按角色组织 | requirements.md 按角色分组（"As a {role}"），每组内按 frequency 排序（高频在前） |
| 后端优先生成顺序 | **先生成后端 design.md（数据模型→接口定义），再生成前端 design.md（引用已定义的接口）**。前端 design 中的接口调用必须引用后端 design 中的定义 |
| 设计分层展开 | design.md 从数据模型开始，逐层展开到接口 → 页面 → 组件。每层引用上一层定义 |
| 输入验证在边界层 | 所有外部输入在接入层统一验证（whitelist 模式）。防注入（参数化查询/转义/沙箱）。认证在接入层声明，不在业务代码中手动检查 |
| 统一错误处理 | 全局错误拦截（中间件/拦截器/错误边界），返回统一格式。业务错误用自定义错误类型（含错误码），日志分级 ERROR/WARN/INFO，敏感信息不进日志 |
| 测试与实现对称 | 每个 B2 业务逻辑/接口任务必须对应 B5 测试任务。测试间无共享可变状态，每条测试独立可运行 |
| 性能基线内建 | 集合查询强制分页/游标（默认批次 ≤ 50 条），高频查询路径建索引，避免 N+1 问题。大数据量操作走异步任务 |
| 写操作幂等 | 创建类操作支持幂等键（协议级 header 或业务唯一约束），更新类操作使用乐观锁（version 字段或条件更新），并发冲突返回对应协议的冲突状态 |
| 前端 CRUD 套路一致 | 同类型子项目的列表/新建/编辑/删除/详情必须使用相同组件套路和数据流模式。详见「前端 CRUD 实现套路」章节 |
| 多语言全覆盖 | 所有用户可见文本必须通过 i18n 函数获取（禁止硬编码），新增文本必须同步所有语言文件。design.md 中标注 i18n 方案，tasks.md 中每个涉及 UI 文本的任务标注 `_i18n: sync all locales_` |
| 用户端优先级继承 | 若 `experience_priority.mode = consumer` 或 `mixed`，前端 requirements/design/tasks 必须包含主线闭环、状态系统、反馈机制、回访理由，不得只拆“页面 + 接口 + 表单” |

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
| 用户端增强 | requirements/design/tasks 必须显式覆盖首页主线、空错成系统、提醒/历史/进度/回访触发点、移动端弱网和低注意力场景 |

### mobile-native (React Native / Flutter)

| 维度 | 内容 |
|------|------|
| requirements 侧重 | 离线同步、推送、设备权限 |
| design 侧重 | 导航栈（RN: React Navigation / Flutter: GoRouter）、原生组件、存储策略 |
| 非功能需求 | 电池/流量优化、后台任务 |
| 从 experience-map 取 | actions → Screen 组件规格（RN: Screen 组件 / Flutter: Screen Widget）；states → 四态设计（离线态额外处理）；on_failure + exception_flows → 原生错误提示；validation_rules → 表单验证 |
| 从 ui-design 取 | 原生端设计 token（如有） |
| 测试工具 | iOS: XCUITest / Android: Maestro (Espresso) / RN: Detox / Maestro / Flutter: Patrol / integration_test |
| 用户端增强 | **仅 consumer_apps**：requirements/design/tasks 必须覆盖持续关系（进度、提醒、历史、通知）、状态反馈和产品节奏，禁止只生成”功能入口型壳子”。merchant/admin 类 mobile-native 子项目不适用此行 |

---

## 前端页面交互套路

> 详见以下文档:
> - 图片字段: `./docs/field-specs/image-field.md`
> - 视频字段: `./docs/field-specs/video-field.md`
> - 页面交互类型分类（37 种）: `product-design-skill/docs/interaction-types.md`
> - 技术栈套路（如存在）: `./docs/tech-stack-patterns/{stack}.md`（不存在时由 LLM 基于技术栈常识推导）
> - 行为原语实现映射: `./docs/primitive-impl-map.md`

**套路检测（existing 模式专用）**：existing 模式下，Step 3 生成 design.md 之前，先扫描已有代码提取实际套路（Request 层、列表/表单/状态操作/删除确认/编辑回填/i18n/枚举管理模式）。

**多语言实现规范**：

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

**design.md 中的输出格式**：

生成 frontend 子项目的 design.md 时，在页面规格之前插入「页面交互套路」章节。每个页面规格中标注交互类型。一个页面可以组合多个类型（如「任务详情」= 主从详情 + 状态机操作）。

若 `experience_priority.mode = consumer` 或 `mixed` **且当前子项目属于 consumer_apps**，还必须插入「用户端成熟度要求」章节，至少列出：

- 主线任务闭环
- 状态系统（loading / empty / error / success / progress）
- 回访触发点（history / reminder / subscription / recommendation / notification 中至少相关项）
- 移动端低注意力交互原则

---

## 工作流 — 并行执行编排（角色分离架构）

> **核心原则**：一个 Agent 同时戴 7 顶帽子 → 后期步骤质量衰减 + 自己审自己效果差。
> 按「角色」拆分，不按「文件」拆分。每个角色做一件事，审查者 ≠ 作者。

**四种角色**：
| 角色 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **Architect** | 理解产品 → 设计架构 | product-map + entity-model + experience-dna | requirements.md + design.md |
| **Decomposer** | 读设计 → 拆功能任务 | design.md + requirements.md | tasks.md（B0-B5 平铺功能任务） |
| **Auditor** | 读全部产出 → 找遗漏 | requirements + design + tasks + product-map | validation findings → 修正 specs |
| **Enricher** | 补充元数据 | design + tasks + product-map | event-schema + task-context |

### 用户端子项目识别（design-to-spec 初始化时执行）

当 `experience_priority.mode = consumer` 或 `mixed` 时，从 `project-manifest.json` 的子项目列表中推导子项目的**体验等级**：

| 体验等级 | 判定规则 | consumer 检查 | 多模型共创 | 典型示例 |
|---------|---------|-------------|-----------|---------|
| **consumer** | type=web-customer/web-mobile，或 mobile-native 面向终端消费者 | 全部适用 | 发用户视角 prompt | 买家 App、C 端 Web |
| **creator** | mobile-native/web 面向创作者/达人/服务提供者，但用户体验标准接近 consumer（高频使用、需要留存） | 适用（但"连续激励""进度可视"按创作者视角解读） | 发创作者视角 prompt | 达人 App、司机 App、自由职业者 App |
| **tool** | 面向商家/运营的专业工具，低频或桌面为主 | 不适用 | 不发 | 商家后台、运营工具 |
| **admin** | type=admin/backend | 不适用 | 不发 | 管理后台、纯后端 |

`consumer_apps` = 体验等级为 consumer 或 creator 的子项目列表。

**判定方式**：LLM 读取 project-manifest.json 的子项目描述 + role-profiles.json 中面向的角色特征，推断体验等级。关键判据：**该端用户是否需要被留存？** 需要留存→consumer/creator，不需要→tool/admin。

将推导结果写入 forge-decisions.json 的 `consumer_apps` 字段（含体验等级标注），供下游角色使用。

### 用户端专项检查点（仅对 consumer_apps 中的子项目生效）

当 `experience_priority.mode = consumer` 或 `mixed` 时，**仅对 consumer_apps 中的子项目**：

- Architect 不得只生成”页面清单”，必须在 design.md 中写出该子项目在用户端主线中的角色与持续关系
- Decomposer 拆功能任务时，必须把 design.md 中的产品化设计（状态系统、反馈机制、提醒、历史、通知、推荐）也拆为对应的功能实现任务，不得只拆 CRUD 端点而忽略这些
- Auditor 必须检查前端任务是否只有功能实现，没有用户端成熟度任务；发现则判为缺口

> 非 consumer_apps 的前端子项目（如 admin、merchant 工具端）不受此检查约束，按各自端类型的标准验收。

**角色步骤加载指令**：

- **Architect Agent**: Read `./docs/design-to-spec/architect-steps.md`
- **Decomposer Agent**: Read `./docs/design-to-spec/decomposer-steps.md`
- **Auditor-Validate Agent**: Read `./docs/design-to-spec/auditor-validate.md`（V1-V12 验证 + 闭环 + XV）
- **Auditor-Enrich Agent**: Read `./docs/design-to-spec/auditor-enrich.md`（质量子任务补充，在 Validate 之后执行）
- **Enricher Agent**: Read `./docs/design-to-spec/enricher-steps.md`

**子项目分类**:
  后端组: type = "backend"（可能 1 个或多个微服务）
  前端组: 其余所有子项目（admin/web-customer/web-mobile/mobile-native）
  > 多后端子项目时，每个后端独立走 Phase A 流程（可并行）。

**项目规模自适应**（所有角色统一规则，防止任何 Agent 超载）：

  > **核心原则**：不管项目多大，每个 Agent 单次处理的模块数 ≤ 5，产出/输入 ≤ 1500 行。
  > 超过此限的项目自动拆成模块组并行处理。
  > **判定**：从 project-manifest.json 的 assigned_modules 数量判断。

  | 规模 | 模块数 | 所有角色策略 |
  |------|--------|------------|
  | 小 | ≤ 5 | 单 Agent 全量处理 |
  | 中 | 6-10 | 单 Agent 全量处理（产出通常 ≤ 1500 行） |
  | 大 | 11-20 | 按模块组分批（每批 3-5 模块），所有角色均并行分批 |
  | **超大** | **> 20** | **同"大"规则，但模块分组数更多；数据模型也需分批（>30 实体时）** |

  **模块分组规则**（大/超大项目）：
  1. 从 project-manifest.json 读取 assigned_modules 列表
  2. 按业务相关性分组（如 auth+users 一组、courses+classroom 一组、payment+subscription 一组）
  3. 每组 3-5 个模块

  **各角色分批方式**：
  | 角色 | 小/中型 | 大/超大型 |
  |------|--------|----------|
  | **Architect** | 单 Agent 全量 | 数据模型单 Agent（共享）→ API 设计**按模块组并行多 Agent** |
  | **Decomposer** | 单 Agent 全量 | 按模块组并行（每组只读 `## Module:` 对应段落） |
  | **Auditor-Validate** | 单 Agent 全量 | 按模块组并行验证 |
  | **Auditor-Enrich** | 单 Agent | DIFF ≤ 30: 单 Agent; DIFF > 30: 按子项目分批（DNA/HARDEN/POLISH），再一个全局 Agent 补充 i18n/a11y/测试 |
  | **Enricher** | 单 Agent | 单 Agent（event-schema + task-context 不按模块拆） |

  **Architect 超大型分批**：
  - **数据模型（实体 ≤ 30）**：单 Architect Agent 一次性生成（共享基础）
  - **数据模型（实体 > 30）**：按领域拆分（如 用户域/商品域/订单域/物流域），每域 1 个 Agent
  - **API 设计**：每模块组 1 个 Architect Agent 并行（读共享数据模型 + 生成该组端点）
  - 每个 Architect Agent 输出独立的 `## Module:` 段落，最终合并到 design.md

  **Architect 分批输出格式**（大/超大型项目强制）：
  design.md 中每个模块用 `## Module: {module_name}` 明确分隔，
  让下游 Agent 能按模块名定位段落，不需要读全文。

**Phase A — 后端**:

  Stage 1: Agent(backend-architect): Step 0 → Step 1 → Step 2 → Step 2.5 → Step 3a → Step 3b（按模块分批）→ Step 3.5
    → 产出 requirements.md + design.md（大型项目按模块分节）
  ↓ design.md 完成后，启动 Phase B（前端并行），同时后端继续：

  Stage 2（小/中型项目）: 单个 Agent(backend-decomposer): 读全量 design.md → 生成 tasks.md
  Stage 2（大型项目）: 按模块组并行 → 每组 1 个 Agent(decomposer-{group}): 读对应模块段落 → 生成该组 tasks
    → 全部完成后合并为统一 tasks.md

  Stage 3a（小/中型）: 单个 Agent(backend-auditor-validate): V1-V12 全量验证
  Stage 3a（大型）: 按模块组并行 → 每组 1 个 Agent(auditor-validate-{group}): 验证该组 tasks
    → 全部完成后汇总 findings

  Stage 3b: Agent(backend-auditor-enrich): 质量子任务补充
    → DIFF ≤ 30: 单 Agent 全量补充
    → DIFF > 30: 按子项目分批补充 DNA/HARDEN/POLISH，再全局 Agent 补 i18n/a11y/测试
    → 补充 HARDEN/DNA/POLISH/i18n/测试子任务 → 重检补充结果

  ∥ 与 Stage 2 并行: Agent(backend-enricher-a): Step 3.8 + Step 3.9（event-schema）
  → Stage 3b 完成后: Agent(backend-enricher-b): Step 4.5（task-context）

**Phase B — 前端并行（每个子项目内部同样适用大型项目自适应）**:
  ┌── 子项目 1:
  │     Agent(architect):   Step 1 → Step 3a → Step 3b → 产出 requirements + design
  │     Agent(decomposer):  Step 4 → 产出 tasks.md（大型前端同样按模块分批）
  │     Agent(auditor-validate): V1-V12 验证
  │     Agent(auditor-enrich): 质量子任务补充
  │     Agent(enricher):    Step 3.8 + Step 4.5
  ├── 子项目 2: 同上
  └── 子项目 N: 同上
  全部完成 ↓

**角色隔离规则**：
- Auditor Agent **禁止**和 Architect/Decomposer 是同一个调用（必须是独立的子任务）
- Auditor 只读产出文件做审查，不参与生成过程
- Enricher 和 Architect/Decomposer 无依赖，可以并行

**结构性 consumer 缺口回退**（Phase B 全部完成后检查）：
若 pipeline-decisions.json 中存在 `CONSUMER_MATURITY_GAP_STRUCTURAL` 标记，说明 consumer_apps 缺少整类 screen（如无引导流/无进度页/无通知中心），这不是 design.md 能修补的问题。编排器应：
1. 输出缺失项清单
2. 检查 task-inventory.json 中是否已有对应的产品任务（如缺少引导流 screen，但 task-inventory 有"首次引导"任务）
   - **task-inventory 已有** → 只需回退到 experience-map（`/product-design resume` 从 experience-map 恢复），重新为已有任务设计 screen
   - **task-inventory 也缺失** → 需要回退到 product-map（`/product-design resume` 从 product-map 恢复），先补厚任务定义再重跑 experience-map
3. 回退补充后重新执行 design-to-spec 的对应 consumer 子项目

---

## 并行执行编排 & 任务 Batch 结构

> 详见 `./docs/execution-batches.md`
> 包含：子项目分类（后端/前端组）、Phase A/B Agent 编排、Agent prompt 模板、错误处理、resume 模式、Batch 0-5 结构、各端 Batch 内容差异。

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
  ├── event-schema.md        # Step 3.8 输出（人类可读）
  ├── event-schema.json      # Step 3.8 输出（机器可读）
  ├── tasks.md               # Step 4 输出（人类可读）
  ├── tasks.json             # Step 4 输出（机器可读）
  └── task-context.json      # Step 4.5 输出（任务上下文预计算）

.allforai/project-forge/
  ├── negative-space-supplement.json # 阶段 1.5 负空间推导发现的缺失支撑功能（B 类）
  ├── shared-utilities-plan.json     # Step 7 主产物
  ├── tasks-supplement.json          # Step 7 B1 任务 + 阶段 1.5 SN 任务 + _Leverage_ 补丁
  └── existing-utilities-index.json  # Step 7 已有工具清单（existing 模式）
```

---

## JSON 对应件（机器可读格式）

每个 Markdown 规格文件同时生成 JSON 对应件，供下游技能（task-execute、product-verify）直接解析，避免正则匹配 Markdown 的脆弱性。

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
      "fields": []
    }
  ]
}
```

---

## Step 5: 跨子项目依赖分析

识别跨项目依赖:
  后端接口定义 → 前端客户端
  共享类型定义 → 公共类型包
  后端 B2 完成 → 前端 B4 才能开始（切换开发桩 → 真实后端）
生成跨项目任务排序 → execution_order
→ 写入 `.allforai/project-forge/cross-project-dependencies.json`（依赖图 + execution_order）
→ **不修改** project-manifest.json（上游产物只读）
→ 输出进度: 「跨项目依赖图 ✓ ({N} 条依赖)」（不停，汇总到 Step 6）

---

## Step 6: 阶段末汇总确认

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
dev-bypass: {N} tasks [DEV_ONLY]（仅 dev_mode.enabled = true 时显示）

→ 输出汇总进度「Phase 2 ✓ {N} 子项目 × 5 文档 (Phase A 串行 + Phase B 并行), CORE {M} 任务」（不停）

### 规模自适应

根据子项目任务数自动调整 Step 6 展示策略：
- **小规模**（≤30 tasks/子项目）：逐条展示完整任务列表
- **中规模**（31-80 tasks/子项目）：按 Batch 分组摘要，仅展示 HIGH-risk 任务详情
- **大规模**（>80 tasks/子项目）：统计概览（任务分布、风险分布、覆盖率）+ 仅列 HIGH-risk 项

---

## Step 6.5: 跨子项目 API 契约闭环审计（Cross-Project Contract Audit）

> **问题根因**：各子项目 spec 独立生成，前端 tasks.md 中的 API 调用和 server tasks.md 中的端点可能不一致。
> 此步骤在所有子项目 spec 生成完毕后、进入 Phase 4 之前，用 4D/6V/闭环框架交叉验证跨子项目 API 契约。
> 历史教训：曾有 admin/merchant 前端调用了 ~49 个 server 未实现的端点，直到 Phase 5 deadhunt 才发现。

**输入**：所有子项目的 tasks.md + design.md（已在 Step 1-6 生成完毕）

**审计维度**（7 类闭环 + 4D + 6V 交叉验证）：

=== 闭环审计 ===

| 闭环类型 | 审计方法 | 不通过标记 |
|---------|---------|----------|
| **调用闭环** | 前端 tasks.md 每个 API 调用路径 → server tasks.md 有对应端点？ | `CONTRACT_CALL_MISSING` |
| **消费闭环** | server tasks.md 每个端点 → 至少被一个前端 tasks.md 引用？ | `CONTRACT_ORPHAN_ENDPOINT`（WARNING） |
| **角色 CRUD 闭环** | 每个实体 × 每个角色（consumer/merchant/admin）→ 该角色需要的 CRUD 操作是否完整？ | `CONTRACT_CRUD_GAP` |
| **数据流闭环** | 前端展示的聚合/统计数据 → server 有写入路径？（V10 跨项目投影） | `CONTRACT_PROVENANCE_GAP` |
| **字段闭环** | server API 返回的字段名 → 前端 tasks.md 引用的字段名一致？ | `CONTRACT_FIELD_MISMATCH` |
| **权限闭环** | 端点在 server design.md 的权限组 → 前端调用时在正确的 auth 上下文？ | `CONTRACT_AUTH_MISMATCH` |
| **路径闭环** | 前端引用的 URL 路径前缀（/consumer/, /merchant/, /admin/）→ 与 server 路由分组一致？ | `CONTRACT_PREFIX_MISMATCH` |

=== 4D 审计 ===

| 维度 | 审计问题 |
|------|---------|
| D1 结论正确 | "admin 可以管理产品" → tasks.md 里真的有 admin 的 list + detail + approve 端点？ |
| D2 有证据 | 每个声称的能力 → 在 tasks.md 中有具体 task（不是笼统描述）？ |
| D3 约束识别 | 角色权限边界 → 端点是否在正确的权限组（consumer 端点不能出现在 admin 组）？ |
| D4 决策有据 | admin 只有 approve 没有 browse → 有意设计（记录 rationale）还是遗漏？ |

=== 6V 审计 ===

| 视角 | 审计问题 |
|------|---------|
| User | 用户能端到端完成任务吗？（如：admin 审核产品 → 需要先浏览产品列表 → 需要 list 端点） |
| Tech | 所有 API 调用路径能解析到 server 路由吗？HTTP method + path 完全匹配？ |
| UX | 每个列表页有对应的详情页吗？每个详情页的数据字段 server 都返回了吗？ |
| Data | 前端表单字段 → API request body → server model 字段 → DB column 全链路可达？ |
| Business | 业务流中每个步骤的 API 调用在 server 都有实现？ |
| Risk | 高频/高风险操作（支付/删除/权限变更）在 server 有对应的审计/确认机制？ |

**执行方式**：

1. 提取 server tasks.md 中所有 B2 端点（HTTP method + path + 权限组）→ 构建 `server_endpoints[]`
2. 提取每个前端 tasks.md 中所有 API 调用（B3/B4 任务描述中的端点引用）→ 构建 `frontend_calls[sub_project][]`
3. 提取 server design.md 中每个实体的字段定义 → 构建 `entity_fields[]`
4. 逐条交叉验证（7 闭环 + 4D + 6V）
5. 汇总结果

**结果处理**：

| 严重度 | 处理 |
|--------|------|
| CRITICAL（调用闭环/CRUD 缺口/数据流断裂） | 自动补全：在 server tasks.md 追加缺失的 B2 端点任务，在前端 tasks.md 修正错误路径 |
| WARNING（孤儿端点/字段命名不一致） | 记录到 forge-decisions.json，不阻塞 |
| INFO（权限建议/路径前缀建议） | 记录，不处理 |

**自动补全规则**：
- 缺失的 server 端点 → 按已有 B2 任务格式追加到 server/tasks.md 的对应 Batch
- 前端引用了错误路径 → 修正 tasks.md 中的路径描述
- CRUD 缺口 → 只补必要操作（admin 对产品需要 list + detail，不需要 create/delete）
- 补全的任务标注 `[CONTRACT-FIX]`，便于追溯

**输出**：
- `.allforai/project-forge/contract-audit.json`（审计结果，含每条 finding）
- 修改过的 tasks.md 文件（已补全缺失端点）
- 修改过的 design.md 文件（已补全缺失接口定义）

→ 输出进度: 「Step 6.5 契约审计 ✓ 调用闭环: {N}/{M} 匹配, CRUD 闭环: {K} 缺口已补, 字段闭环: {L} 不一致」

---

## Step 7: 共享层分析（Shared Utilities Analysis）

> 在所有子项目 spec 生成完毕后执行。扫描已有代码 + 跨任务模式共振分析 + 三方库选型 → 生成共享层 B1 任务注入。
> 原 shared-utilities 独立技能合并于此，输出格式不变，task-execute 加载时合并 `tasks-supplement.json`。

### 7a. 已有代码扫描 + 模式共振分析

**已有代码扫描**（existing 模式执行，new 模式跳过）：

扫描项目代码，提取工具库存。**扫描目标**（按优先级）：

| 优先级 | 目标位置 | 识别内容 |
|--------|---------|---------|
| 1 | `utils/` `helpers/` `common/` `shared/` `pkg/` | 工具函数 |
| 2 | `services/` | 外部服务封装（email、sms、storage…） |
| 3 | `middleware/` `interceptors/` `guards/` | 横切关注点 |
| 4 | `package.json` / `go.mod` / `requirements.txt` | 已有三方依赖 |

每个已有工具记录为 EU-xxx（Existing Utility）：

```json
{
  "id": "EU-001",
  "type": "email-service | validator | http-client | pagination | logger | ...",
  "location": "src/utils/email.ts",
  "coverage": "发送模板邮件、HTML 邮件",
  "quality": "good | needs-refactor | partial",
  "usable_as_is": true
}
```

质量评估标准：
- `good`：有完整类型定义、有错误处理、无明显技术债
- `needs-refactor`：功能可用但缺少类型/错误处理，或与项目规范不符
- `partial`：仅覆盖部分场景，需要补充

→ 写入 `.allforai/project-forge/existing-utilities-index.json`

**模式共振分析**（Pattern Resonance Analysis）：

Agent 分析所有子项目 `tasks.md`，识别跨任务的逻辑共振：

1. **跨任务语义聚类**：对具有相似逻辑复杂度和技术挑战的任务进行聚类
2. **抽象可行性评估**：评估抽象后的"认知成本降低"与"耦合风险"
3. **共振识别指标**：
   - **逻辑重叠度**：逻辑链条的重合程度
   - **领域稳定性**：该业务逻辑在 `product-map` 中的变化频率（越稳定越值得抽象）
   - **技术通用性**：是否属于目标技术栈中常见的共性问题

**三方库选型**（网络搜索）：

对识别出的 NEW 共享工具类型，通过网络搜索调研推荐库。搜索词模板（基于 preflight 已选技术栈动态拼接）：

```
"{framework} {utility_type} best library {year}"
```

推荐方向参考（网络搜索确认后使用）：

| 类型 | Node.js/TS | Python | Go |
|------|-----------|--------|-----|
| 校验 | class-validator / zod | pydantic | go-playground/validator |
| HTTP client | axios / got | httpx | resty |
| 日期 | dayjs / date-fns | python-dateutil | carbon |
| 日志 | pino / winston | loguru | zap |
| 邮件 | nodemailer | fastapi-mail | gomail |
| 文件上传 | multer | python-multipart | standard lib |
| 分页 | 3行自实现 | 3行自实现 | 3行自实现 |
| 缓存 | ioredis / node-cache | redis-py | go-redis |

每个 NEW 类型给出 1-2 个推荐选项（含推荐理由）。

**用户确认**：

- 当 `__orchestrator_auto: true` 时，**自动采纳推荐选项（选项 A）**，不停顿。仅当检测到 ERROR 级冲突时才停顿。
- 非 auto-mode：展示完整分析结果，一次性收集用户决策（ONE-SHOT）。
- 已有代码（EU-xxx）无需确认，直接采用。

### 7b. 共享层任务注入

用户确认后（或 auto-mode 自动采纳后），自动执行以下操作：

**生成共享工具 B1 任务**：

为每个 SU-xxx 生成原子任务，写入 `.allforai/project-forge/tasks-supplement.json`（**不修改**原始 tasks.md，上游产物只读）：

```json
{
  "created_at": "ISO8601",
  "source": "shared-utilities",
  "b1_tasks": [
    {
      "id": "1.x",
      "sub_project": "api-backend",
      "title": "创建 {utility_type} 共享工具",
      "files": ["src/utils/{name}.ts", "src/utils/index.ts"],
      "details": "封装 {library}，导出统一接口和类型定义",
      "shared_utility_ref": "SU-001",
      "risk": "MEDIUM"
    }
  ],
  "leverage_patches": [
    {
      "task_id": "2.3",
      "append_leverage": ["SU-001 (class-validator)", "SU-003 (ExceptionFilter)"]
    }
  ],
  "refactor_tasks": [
    {
      "id": "1.x",
      "sub_project": "api-backend",
      "title": "重构 {utility_type}（EU-{id}）以符合项目规范",
      "files": ["{existing_location}"],
      "details": "补充类型定义和错误处理",
      "shared_utility_ref": "EU-001",
      "risk": "LOW"
    }
  ]
}
```

**task-execute 加载时合并**：task-execute 启动时检查 `tasks-supplement.json` 是否存在，若存在则：
- 将 `b1_tasks` 追加到后端子项目 tasks 的 Batch 1 末尾
- 将 `leverage_patches` 中的引用合并到对应任务的 `_Leverage_` 字段
- 将 `refactor_tasks` 追加到 Batch 1（EU-xxx 复用已有，quality=needs-refactor 时）

**_Leverage_ 补丁**（写入 supplement，不修改原文件）：

扫描所有子项目 tasks.md，找到 `affects_tasks` 中匹配的任务 ID，将 SU-xxx 引用记录到 `tasks-supplement.json` 的 `leverage_patches` 数组。

**写入 `shared-utilities-plan.json`**：

```json
{
  "created_at": "ISO8601",
  "mode": "new | existing",
  "existing_utilities": [
    {
      "id": "EU-001",
      "type": "email-service",
      "location": "src/utils/email.ts",
      "quality": "good",
      "action": "reuse | refactor"
    }
  ],
  "shared_utilities": [
    {
      "id": "SU-001",
      "type": "validator",
      "library": "class-validator",
      "decision": "use-third-party | self-implement",
      "b1_task_id": "1.5",
      "affects_tasks": ["2.3", "2.7", "3.1"]
    }
  ],
  "tasks_updated": 24,
  "b1_tasks_added": 4
}
```

→ 输出进度: 「Step 7 ✓ {N} 共享工具（复用 {M} 现有 + 新建 {K}），{P} 个任务更新了 _Leverage_」

### Step 7 输出文件

```
.allforai/project-forge/
├── shared-utilities-plan.json          # 主产物，Step 7 完成标志
├── tasks-supplement.json               # B1 任务 + _Leverage_ 补丁（task-execute 加载时合并）
└── existing-utilities-index.json       # existing 模式下的已有工具清单
```

各子项目 tasks.md **不被修改**。B1 任务和 _Leverage_ 补丁写入 `tasks-supplement.json`，由 task-execute 在加载时动态合并。
