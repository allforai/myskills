# 并行执行编排 & 任务 Batch 结构

## 并行执行编排

> Step 1-4 由 Agent 并行执行，编排器负责分类、调度和聚合。
> 本段描述 Agent 调度逻辑，Step 1-4 的具体内容见 design-to-spec.md「工作流」段落。

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

后端 Agent 完成后，**并行执行以下 N 个任务**。
并行任务全部完成后才继续到 Step 5。

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
1. 加载 skills/design-to-spec.md（仅参考规则和模板，不重复全局步骤）
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
- 产品设计产物: .allforai/product-map/, .allforai/experience-map/ 等
- 后端 design.md: .allforai/project-forge/sub-projects/{backend-name}/design.md（仅前端 Agent 引用）
- 后端 design.json: .allforai/project-forge/sub-projects/{backend-name}/design.json（仅前端 Agent 引用）
{自动模式标记: __orchestrator_auto: true（若自动模式激活）}

类型契约注入（仅前端 Agent）:
  编排器在启动 Phase B 前，自动从后端产物提取类型契约，注入每个前端 Agent prompt:
  1. 从 design.json 提取 data_models（所有 Entity 的字段名、类型、关联关系）
  2. 从 design.json 提取 api_endpoints 的 request_schema / response_schema
  3. 若后端子项目已生成公共类型定义文件 → 提取类型定义原文
  4. 将以上内容作为「## 后端类型契约（只读参考）」章节注入前端 Agent prompt
  这确保前端 Agent 对数据结构字段命名、ID vs 名称、枚举值与后端完全一致，
  而非各自推断导致 mismatch。

重要:
- 仅处理本子项目，不读写其他子项目的产出目录
- 按端差异化规则生成（参考 design-to-spec.md 的「各端差异化 Spec 生成」表格）
- 遵循两阶段加载（先 index 再 full data）
- 前端 Agent: 接口调用必须引用后端 design.md 中已定义的接口 ID
- 前端 Agent: 数据结构字段命名必须与注入的后端类型契约完全一致（不可自行推断字段名）
- 预置脚本优先: 检查 scripts/ 是否有可用脚本
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
    - requirements.md 存在且非空
    - design.md 存在且非空
    - tasks.md 存在且非空
  三件全且非空 → 该子项目已完成（LLM 可进一步验证内容质量，但不阻断 resume）

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

> **注意**：以下 B0-B5 结构为默认参考模板。LLM 会根据实际项目的任务依赖图动态调整层数和执行顺序，不强制所有项目遵循固定 6 层结构。GraphQL-first、组件库、微服务等项目形态可能产生不同的 Batch 划分。

```
## Batch 0: Monorepo Setup（全局，最先执行）
- [ ] 0.1 配置 monorepo workspace + 根配置文件
- [ ] 0.2 创建 packages/shared-types（从 product-map entities 生成）
- [ ] 0.3 创建开发桩服务（来自 seed-forge plan 数据）

## Batch 1: Foundation（各子项目并行）
- [ ] 1.1 [api-backend] 数据模型、迁移、配置
- [ ] 1.2 [merchant-admin] 布局骨架、路由配置
- [ ] 1.3 [customer-web] SSR 配置、SEO 基础
...

## Batch 2: API / Service（后端）
- [ ] 2.1 [api-backend] Controller + Service + DTO + 中间件
...

## Batch 3: UI / Page（前端并行，连开发桩）
- [ ] 3.1 [merchant-admin] 页面组件（连开发桩）
- [ ] 3.2 [customer-web] 页面组件
...

## Batch 4: Integration（等 B2 完成）
- [ ] 4.1 生成公共 API 客户端包（从后端接口定义）
- [ ] 4.2 [merchant-admin] 切换开发桩 → 真实后端
- [ ] 4.3 [customer-web] 切换开发桩 → 真实后端
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
B2: 端点级任务（⚠️ 必须按端点组拆分，禁止按 controller 合并）
    拆分规则：
    - 同一实体标准 CRUD → 可合为 1 个任务（GET list + detail + POST + PUT + DELETE）
    - 独立业务逻辑端点 → 独立任务（如审核 approve/reject、统计 stats、充值 topup）
    - 状态变更端点 → 独立任务（如 ship、confirm、cancel）
    - 聚合/分析端点 → 独立任务
    示例：
    ✓ B2.1  Auth CRUD（register + login + refresh）
    ✓ B2.2  Auth 密码重置（forgot-password + reset-password）← 独立业务逻辑
    ✓ B2.10 商户审批（POST /merchants/:id/approval）← 状态变更
    ✓ B2.11 商户暂停（POST /merchants/:id/suspend）← 状态变更
    ✓ B2.12 邀请码 CRUD（POST + GET + DELETE /invite-codes）← 关联功能
    ✗ B2.10 Admin 商户管理 controller（审批+暂停+邀请码+列表）← 太粗，禁止
B3: —（无 UI 层，跳过）
B4: 接口文档生成、健康检查/探针、错误响应统一、客户端 SDK 导出
B5: 单元测试 (entity+service) + API 集成测试（LLM 根据项目已有测试框架推理工具选择）
```

**admin**:
```
B1: 类型定义、API 客户端封装、根 layout + 侧边栏骨架、路由配置
B2: —（无独立 API，跳过）
B3: DataTable、Form 组件、页面组件、图表组件
B4: 连接真实后端（替换开发桩连接配置）、路由守卫、状态管理
B5: 组件测试 + E2E 测试（LLM 根据项目已有测试框架推理工具选择，桌面视口）
```

**web-customer**:
```
B1: 类型定义、API 客户端、SEO meta 组件、SSR/SSG 基础配置
B2: —（无独立 API，跳过）
B3: 页面组件 (带 SSR metadata)、列表/详情/功能页
B4: 连接真实后端、结构化数据 (JSON-LD)、Analytics 集成
B5: E2E 测试（LLM 根据项目已有测试框架推理工具选择，桌面+移动视口）+ Lighthouse 性能检测
```

**web-mobile**:
```
B1: 类型定义、PWA 配置、Service Worker、移动布局骨架
B2: —（无独立 API，跳过）
B3: 移动组件 (下拉刷新/无限滚动/手势)、页面、离线状态页
B4: 连接真实后端、离线缓存同步、推送集成
B5: E2E 移动视口测试（LLM 根据项目已有测试框架推理工具选择）+ Lighthouse 移动性能检测
```

**mobile-native (React Native)**:
```
B1: 类型定义、导航栈配置、本地存储 schema、权限声明、API 客户端（LLM 扫描项目依赖检测实际使用的导航/存储/网络库）
B2: —（无独立 API，跳过）
B3: Screen 组件 (FlatList/ScrollView/Form)、Tab 页面 (Bottom Tabs)、业务组件
B4: 后端集成（切换开发桩 → 真实后端）、离线同步、推送集成（LLM 检测项目已配置的推送服务）、深度链接
B5: E2E / 平台原生测试（LLM 根据技术栈选择工具）
```

**mobile-native (Flutter)**:
```
B1: 数据模型 (Dart class)、导航配置、主题/常量、API 客户端、状态管理基础（LLM 扫描 pubspec.yaml 检测实际使用的导航/网络/状态管理库）
B2: —（无独立 API，跳过）
B3: Screen Widget (ListView/SingleChildScrollView/Form)、底部 Tab (NavigationBar)、业务 Widget (Card/ListTile/Detail)
B4: 后端集成（切换开发桩 → 真实后端）、离线同步、推送集成（LLM 检测项目已配置的推送服务）、深度链接
B5: Widget 测试 + 集成测试（LLM 根据项目已有测试框架推理工具选择）
```

**mobile-native (Android Kotlin/Java)**:
```
B1: 数据模型 (data class)、导航配置、常量/主题、API 客户端、DI 基础（LLM 扫描 build.gradle 检测实际使用的导航/网络/DI 库）
B2: —（无独立 API，跳过）
B3: Screen (Compose Screen / Fragment)、BottomNavigation、业务组件 (LazyColumn/Card/Detail)
B4: 后端集成（切换开发桩 → 真实后端）、推送集成（LLM 检测项目已配置的推送服务）、深度链接
B5: E2E / UI 测试 + JUnit 单元测试（LLM 根据技术栈选择工具）
```

**mobile-native (iOS Swift/SwiftUI)**:
```
B1: 数据模型 (Codable struct)、导航配置、常量/主题、API 客户端（LLM 扫描 Swift Package / Podfile 检测实际使用的导航/网络库）
B2: —（无独立 API，跳过）
B3: Screen View (List/Form/NavigationLink)、TabView、业务组件
B4: 后端集成（切换开发桩 → 真实后端）、推送集成（LLM 检测项目已配置的推送服务）、深度链接
B5: UI 测试 + 单元测试（LLM 根据技术栈选择工具）
```
