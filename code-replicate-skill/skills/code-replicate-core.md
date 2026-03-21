---
name: code-replicate-core
description: >
  Internal shared protocol for code replication. Do NOT invoke directly —
  loaded by cr-backend.md, cr-frontend.md, cr-fullstack.md, or cr-module.md.
---

# Code Replicate Core Protocol v2.1

## Overview

Code Replicate 是逆向工程桥梁：读取已有代码库，生成标准 `.allforai/` 产物（product-map、experience-map、use-case），
使 dev-forge 流水线（`/design-to-spec` → `/task-execute`）可直接消费。

本技能的唯一职责是从源码提取**业务意图**（做什么），不复制**实现决策**（怎么做）。
源码中的同步/异步模型、错误处理约定、通信协议等属于实现决策，由目标生态的架构惯例替换。

---

## 4 阶段流程

### Phase 1: Preflight

1. 检测 replicate-config.json（断点续跑 — 见下文）
2. 解析 CLI 参数：mode, path/url, --type, --scope, --module, --from-phase
3. 源码获取：
   - 本地路径 → 直接使用
   - Git URL → `git clone --depth 1`（HTTPS / SSH / GitHub 短语法 `user/repo`）
   - 支持 `#branch` 后缀指定分支：`https://github.com/user/repo#develop`
4. 收集缺失参数（AskUserQuestion，最多 1 次合并多题）：
   - 保真度（interface / functional / architecture / exact）
     > 详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity-guide.md
   - 项目类型（backend / frontend / fullstack / module）
   - scope（full / modules / feature）
   - 目标技术栈（同栈 or 跨栈 + 目标名称）
   - 业务方向（replicate / slim / extend）
   - 源 App 运行信息（供 Phase 2c-visual + `/cr-visual` 使用）：
     · 启动命令（前端 + 后端，后端必须运行前端才能展示数据）
     · URL
     · 登录凭证（如有 2FA/验证码，需要提供绕过方式或测试模式命令）
     · 测试数据准备命令（seed 脚本或 demo 账号，空库截图无意义）
     · 平台类型
   > **闭环输入审计**（见 product-design-skill/docs/skill-commons.md §八）：
   > 用户回答后检查**意图闭环**（代码做了什么 vs 用户想要什么一致吗？）
   > 和**边界闭环**（代码处理了正常路径，用户期望的异常处理呢？）。
   > MUST 级缺失以选择题形式追问。
5. 写 replicate-config.json → `.allforai/code-replicate/`（含 `source_app` 字段）
6. 创建 fragments 目录结构：`.allforai/code-replicate/fragments/{roles,screens,tasks,flows,usecases,constraints}/`

---

### Phase 2: Discovery + Confirm

**Step 2a-pre** — LLM 生成 `discovery-profile.json`（项目专属发现规则）

LLM 读取以下信息（context 极小，~2-5KB）：
1. 项目根目录文件列表（`ls -la`，1 层）
2. 关键清单文件内容（package.json / .sln / go.mod / Cargo.toml 等，只读顶层）
3. 前 2 层目录树（`find . -maxdepth 2 -type d`）

基于以上信息，LLM 生成 `discovery-profile.json` 写入 `.allforai/code-replicate/`：

```json
{
  "source_roots": ["packages", "src"],
  "skip_dirs": ["node_modules", ".git", "dist", "build", "__pycache__"],
  "code_extensions": [".ts", ".tsx", ".cs"],
  "entry_patterns": ["main", "index", "app", "program", "startup"],
  "module_boundaries": ["package.json", ".csproj"],
  "module_paths": [
    {"path": "src/ERP.Modules.Sales", "atomic": true},
    {"path": "src/ERP.Modules.Inventory", "atomic": true},
    {"path": "packages/api/src/modules/user", "atomic": true},
    {"path": "packages/api/src/modules/product", "atomic": true}
  ],
  "mega_threshold": 50
}
```

**生成规则**：
- `module_paths` 是**最高优先级** — LLM 直接列出所有业务模块的相对路径
- `module_boundaries` 标记项目清单文件 — 含此文件的目录是原子模块，不可按大小拆分
- `source_roots` / `skip_dirs` / `code_extensions` 只在 `module_paths` 为空时作为 fallback
- LLM **必须**基于对项目结构的理解生成，不可套用模板

**Step 2a** — 运行 `cr_discover.py --profile discovery-profile.json` → source-summary.json 骨架
- 优先使用 profile 中的 `module_paths`（LLM 直接指定的模块列表）
- 无 profile 时 fallback 到内置启发式（SOURCE_ROOTS + 文件数阈值）
- 输出包含 modules 列表（每个含 path, language, key_files, file_count）

**Step 2b** — LLM 逐模块摘要（读 key_files → responsibility / interfaces / entities）
- 每个模块读取 cr_discover.py 标记的 key_files（入口、路由、模型、配置）
- 输出：模块 responsibility 单句描述 + 暴露 interfaces 列表 + 核心 entities
- 大模块（>50 文件）优先分析 key_files，再根据目录结构判断是否需要深入扫描子目录
- **非代码配置文件也可能含业务逻辑**：路由配置（nginx.conf, routes.yaml）、API 定义（OpenAPI spec）、权限矩阵（rbac.yaml）等。LLM 应在 discovery-profile 或 extraction-plan 中将这些文件标注为 task/role/flow 来源。引用项目根目录文件时使用 `"module": null`
> 分析原则详见 ${CLAUDE_PLUGIN_ROOT}/docs/analysis-principles.md

**Step 2b-arch** — LLM 项目特征识别 → `replicate-config.json` 追加 `project_archetype`

LLM 基于 source-summary（模块结构、技术栈、key_files）判断项目的**核心价值类型**：

```
LLM 自问：这个项目的核心价值是什么？
  - "用户通过界面完成业务操作"  → 标准产物模型（task-inventory + flows）
  - "算法的正确性是产品生命线"  → 需要形式化规格 + 多角色测试向量
  - "对外暴露的 API/ABI 契约"  → 需要签名精确复制 + 内存模型 + 集成验证
  - 以上的混合                  → LLM 标注哪些模块属于哪种类型
```

写入 `replicate-config.json` 的 `project_archetype` 字段（LLM 自由描述，不限定枚举）。

**该字段影响后续所有阶段**：
- Phase 3 extraction-plan：LLM 根据 archetype 决定生成什么格式的产物
- Phase 3.5.5 test-vectors：LLM 根据 archetype 选择向量模型（单步/多步/多角色）
- cr-fidelity：LLM 根据 archetype 决定加载哪些验证维度文档

**不限定 archetype 分类** — LLM 可能写 "CRDT 实时协作引擎"、"跨平台 FFI 支付 SDK"、"标准全栈电商" 等任意描述。下游由 LLM 读 archetype 描述后自行决定行为。

**Step 2b-infra** — LLM 基础设施盘点 → `infrastructure-profile.json`

LLM 读源码（不是读依赖清单的名称），理解项目**实际使用了什么基础设施**，写入 `.allforai/code-replicate/infrastructure-profile.json`。

**盘点方式**：LLM 读每个模块的 key_files + 项目根目录的配置文件，**从代码行为中推断**基础设施用途。不靠包名/库名匹配 — 自研基础设施没有已知包名。

**LLM 核心问题**：对每个模块的代码，问"这段代码在业务逻辑之下依赖了什么技术基础设施？"

LLM 自行判断什么构成"基础设施" — 可能是通信协议、加密算法、存储机制、状态管理、二进制依赖、代码生成、路径构建规则，也可能是项目特有的其他类别。不限定维度，LLM 根据实际代码决定。

**产出 schema**（LLM 自由填充，不限定维度名称）：

```json
{
  "generated_at": "ISO8601",
  "components": [
    {
      "name": "LLM 自命名（如 WebSocket Tunnel Layer）",
      "category": "LLM 自分类（如 communication / encryption / storage / protocol / native_sdk / code_generation / state / cache / queue / search / scheduling / ...）",
      "files": ["具体文件路径"],
      "what_it_does": "LLM 用 2-3 句话描述这个组件做了什么",
      "how_it_works": "LLM 描述实现机制（如：自定义二进制帧协议，4字节头+payload+CRC32校验）",
      "is_standard": false,
      "standard_equivalent": "最接近的标准技术（如：类似 gRPC 但自研协议）或 null",
      "cannot_substitute": true,
      "migration_risk": "critical / high / medium / low",
      "migration_risk_reason": "为什么这个风险等级"
    }
  ]
}
```

**关键字段**：
- `is_standard: false` — 自研组件，目标栈不可能有现成等价物
- `cannot_substitute: true` — 不能用"接近的"标准技术替代（如自研加密算法不能随便换成 AES）
- `category` — LLM 自由分类，不限定枚举。可能出现项目特有的类别
- `protocol_spec` — **对自定义协议/加密/序列化组件必填**。LLM 读源码中的协议实现代码，输出结构化规格：

```json
"protocol_spec": {
  "frame_format": "LLM 描述帧结构（字段偏移、长度、编码方式）",
  "state_machine": "LLM 描述状态转换（如有）",
  "test_vectors": [
    {"input": "...", "expected_output": "...", "description": "LLM 从源码测试/常量中提取的验证用例"}
  ]
}
```

`protocol_spec` 是**可验证的结构化规格**，不是文本描述。LLM 根据源码实际的协议实现生成，格式由 LLM 自行决定（帧协议用 field offset 格式，状态机用 state transition 格式，加密用 input/output 对格式）。`test_vectors` 从源码的单元测试或常量中提取，供目标代码验证行为一致性

**Step 2b-assets** — 素材盘点 → `asset-inventory.json`（仅 frontend/fullstack）

LLM 扫描源码的静态资源目录（`public/`, `assets/`, `static/`, `resources/` 等），盘点所有与代码有引用关系的素材。

LLM 对每个素材分类迁移方式：
- `copy` — 文件直接复制到目标项目（图片、字体、音视频、Lottie JSON）
- `transform` — 需要格式转换或重新映射（主题变量、图标组件化、i18n key 格式）
- `replace` — 源框架专属，目标框架需用等价替代（React SVG 组件 → Vue SFC 组件）

产出 `.allforai/code-replicate/asset-inventory.json`：

```json
{
  "generated_at": "ISO8601",
  "assets": [
    {
      "category": "LLM 自分类（icons / images / fonts / animations / theme / i18n / audio_video / ...）",
      "source_path": "素材所在目录或文件",
      "file_count": 0,
      "migration": "copy | transform | replace",
      "migration_detail": "LLM 描述具体迁移方式",
      "code_refs": "哪些代码文件引用了这些素材（import/require/url()）"
    }
  ],
  "theme_system": {
    "mechanism": "LLM 描述主题系统实现方式（CSS Variables / Tailwind / Design Token / ...）",
    "source_files": ["主题定义文件路径"],
    "variables_count": 0,
    "migration_note": "LLM 描述如何映射到目标框架的主题系统"
  }
}
```

**Phase 3 消费**：
- `copy` 类素材 → Phase 3 直接复制到目标项目对应目录，更新引用路径
- `transform` 类素材 → Phase 3 LLM 读源主题文件 → 生成目标框架的主题配置
- `replace` 类素材 → Phase 3 LLM 按 stack-mapping 转换格式

**cr-fidelity 消费**：asset-inventory 存在时启用 U 维度中的素材覆盖检查

**Step 2b-seed** — 基础数据盘点 → `seed-data-inventory.json`（仅 backend/fullstack）

LLM 读源码的 seed 脚本（prisma/seed.ts, db/seeds/, fixtures/ 等）和数据库迁移文件，提取系统运行所需的**基础数据清单**。

基础数据 = 没有它系统能启动但业务不能用的数据（不是用户生成的业务数据）。

LLM 读 seed 脚本 → 提取每条基础数据的内容和用途：

```json
{
  "generated_at": "ISO8601",
  "seed_sources": ["LLM 找到的 seed 脚本/fixture 文件路径"],
  "data": [
    {
      "category": "LLM 自分类",
      "table": "对应的数据库表/集合",
      "records": "LLM 从 seed 脚本中提取的具体数据（JSON 数组）",
      "purpose": "LLM 描述这组数据的业务用途",
      "required": true
    }
  ]
}
```

**Phase 3 消费**：dev-forge 读 seed-data-inventory → 为目标栈生成等价的 seed 脚本（如 Prisma seed.ts → GORM seed.go），数据内容来自产物而非源码 seed 脚本。

**cr-fidelity 消费**：验证目标项目的 seed 脚本是否覆盖了所有 `required: true` 的基础数据。

**Step 2c** — LLM 全局补充（cross_cutting + 隐含依赖 + 架构风格 + **abstractions**）
- 识别跨模块关注点：认证、日志、错误处理、国际化
- 补充隐含依赖：消息队列、缓存、外部 API
- 标记架构风格：monolith / microservice / modular-monolith / serverless
- **提取源码复用模式**：LLM 读 key_files 时观察到的代码复用方式，写入 source-summary.json 的 `abstractions` 字段。LLM 自行判断什么构成"复用模式"——可能是基类继承、mixin 组合、高阶函数、装饰器、依赖注入、代码生成宏等，完全由源码决定

**Step 2c-visual** — 源 App 截图采集（仅 frontend/fullstack 且源 App 可运行时执行）

如果源 App 能启动（replicate-config.source_app 有 start_command），在 Phase 2 阶段就完成截图采集 — **不等到流程末尾**，因为源项目环境可能在后续步骤中被清理。

> 注意：此时 experience-map 尚未生成（Phase 3 才有）。截图导航基于**源码的路由配置**（GoRouter / React Router / nginx.conf 等），不依赖 experience-map。

```
0. 环境准备（全部必须成功才能开始截图）
   a. 启动后端（如果 source_app 有 backend_start_command）→ 等待后端可达
      没有后端 → 前端截图全是错误页面 → 不启动截图流程
   b. 执行数据准备（如果 source_app 有 seed_command）→ 等待完成
      空数据库 → 所有列表页都是"暂无数据" → 截图无意义
   c. 启动前端（source_app.start_command）→ 等待前端可达

1. 登录
   a. 导航到登录页
   b. 用 source_app.login 凭证登录
   c. 如果登录需要 2FA/验证码 → 用 source_app.login.bypass_command 执行绕过
      （如：关闭验证码的 env 变量、测试模式 API、直接注入 token）
   d. 登录失败 → 停止截图流程，标记原因

2. 提取路由列表
   a. 从 source-summary.modules 的 key_files 中找到路由配置文件
   b. LLM 读路由配置 → 提取所有可导航路由
   c. 参数化路由（/users/:id）→ LLM 从页面或 API 获取一个真实 ID 填入
      （如：登录后访问用户列表 → 取第一条的 ID → /users/123）
   d. 非 URL 直达的页面（模态框、嵌套导航）→ LLM 记录导航步骤：
      [{action: "click", selector: "...", then_screenshot: "modal_name.png"}]

3. 逐路由截图
   - URL 直达路由：Playwright browser_navigate → browser_take_screenshot
   - 参数化路由：用 Step 2c 获取的真实 ID 导航
   - 非 URL 页面：按导航步骤执行（click → wait → screenshot）
   - 移动端：Maestro navigate → screenshot（如果可用）
   - 桌面：用户手动截图

4. 保存
   - 截图 → .allforai/code-replicate/visual/source/{route_or_name}.png
   - 路由映射 → visual/route-map.json：
     [{route: "/appointments", file: "appointments.png", type: "url_direct"},
      {route: null, name: "新建预约弹窗", file: "create_appointment_modal.png", type: "navigation_steps",
       steps: [{action: "click", selector: "#btn-new"}]}]

5. 清理
   - 停止前端、后端
```

**前置条件全部是硬性的**：后端不可用、数据库为空、登录失败 → 不截图，不降级。截图要么正确要么不截。

**Step 2d** — 展示发现 + 一次性确认（AskUserQuestion，**最后一次**）
- 展示：模块清单、技术栈、粒度推荐、跨栈映射决策点
- **展示 infrastructure-profile 中 `migration_risk = critical | high` 的组件** — 用户需要确认这些组件的迁移策略
- **特别关注通信+加密的交叉点**：通信协议内嵌的加密层（如 WebSocket Tunnel 内的自研加密）容易被拆分看待而遗漏整体语义
- 收集：模块范围调整、映射决策、粒度确认、**基础设施迁移决策**
  > 栈映射参考详见 ${CLAUDE_PLUGIN_ROOT}/docs/stack-mappings.md

**Step 2e** — 写入 replicate-config.json 更新 + stack-mapping.json（仅跨栈）
- 跨栈时 stack-mapping.json 记录：源概念 → 目标概念映射
- **每条映射必须标注 `compatibility`**：
  - `flexible` — 设计选型可替代（如状态管理框架、UI 组件库、DI 框架）
  - `exact` — 协议层不可替代（如加密算法、通信协议、序列化格式）— 与现有服务端通信的组件**默认 exact**
  - LLM 根据 infrastructure-profile 的 `cannot_substitute` 字段判断。与服务端通信的组件（API client、WebSocket、gRPC）必须标 exact
- 跨栈时额外生成 `abstraction_mapping`：LLM 将 Step 2c 发现的源码复用模式映射到目标栈的等价复用机制
- **跨栈时额外生成 `infrastructure_mapping`**：LLM 将 infrastructure-profile 中每个组件映射到目标栈的等价实现。`cannot_substitute: true` 的组件必须标注精确迁移方案（不可用"类似的"替代），`is_standard: false` 的自研组件需要标注"目标栈需要重新实现"
- **跨平台时额外生成 `platform_adaptation`**：当源平台和目标平台的交互模型不同（mobile↔desktop, web↔native）时，LLM 生成 UX 转换规则、注意力阈值覆盖、不适用功能列表。dev-forge 和 cr-fidelity 读此字段调整行为
- 同栈时不生成 stack-mapping.json（但 source-summary.abstractions 和 infrastructure-profile 仍然生成，供 dev-forge 直接使用）

> **=== Phase 2 结束后不再问任何配置问题 ===**

---

### Phase 3: Generate（静默执行）

**Step 3-pre** — LLM 生成 `extraction-plan.json`（项目专属提取规则）

LLM 读取 source-summary.json（已有模块清单、技术栈、key_files），针对**当前项目**生成提取计划，写入 `.allforai/code-replicate/extraction-plan.json`：

```json
{
  "role_sources": [
    {"module": "M003", "file": "internal/middleware/auth.go", "how": "RoleType enum 定义了 4 种角色"},
    {"module": "M003", "file": "config/permissions.yaml", "how": "RBAC 权限矩阵"}
  ],
  "task_sources": [
    {"module": "M001", "file": "cmd/api/handlers/*.go", "how": "每个导出 handler 函数 = 一个 task"},
    {"module": "M005", "file": "internal/cron/jobs.go", "how": "每个 cron job = 一个 task"}
  ],
  "flow_sources": [
    {"module": "M002", "file": "internal/service/order_service.go", "how": "CreateOrder 方法调用链 = 一个完整 flow"}
  ],
  "screen_sources": [
    {"module": "M010", "file": "src/app/*/page.tsx", "how": "每个 page.tsx = 一个 screen，同目录下 layout.tsx 提供布局信息"}
  ],
  "usecase_sources": [
    {"module": "M001", "file": "cmd/api/handlers/*.go", "how": "handler 中的 if/switch 分支 = boundary/exception use case"}
  ],
  "constraint_sources": [
    {"module": "M004", "file": "internal/model/*.go", "how": "struct tag 中的 validate 标签 = 输入约束"}
  ],
  "cross_cutting": [
    {"concern": "认证", "files": ["internal/middleware/auth.go"], "applies_to": ["M001", "M002"]},
    {"concern": "日志", "files": ["internal/logger/logger.go"], "applies_to": "all"}
  ],
  "abstraction_sources": [
    {"file": "lib/core/base_bloc.dart", "how": "15个 feature Bloc 都继承此基类，提供统一的 loading/error state 处理"},
    {"file": "lib/shared/widgets/custom_button.dart", "how": "全 app 复用的按钮组件，封装了 loading 状态和 haptic feedback"},
    {"file": "lib/core/network/api_service.dart", "how": "统一 HTTP 封装：token 注入、错误拦截、重试逻辑，所有 feature service 依赖此类"}
  ],
  "asset_sources": [
    {"path": "LLM 根据 asset-inventory 指向的素材目录", "migration": "copy | transform | replace"}
  ],
  "infrastructure_sources": [
    {"file": "LLM 根据 infrastructure-profile 指向的文件", "how": "LLM 描述该文件中基础设施的实现方式"}
  ],
  "dependency_map": [
    {"from": "M001", "to": "M003", "via": "require('app.service.user_service')", "type": "direct_call"},
    {"from": "M001", "to": "M002", "via": "access_by_lua_file middleware/auth.lua", "type": "middleware"},
    {"from": "M003", "to": "M004", "via": "require('app.dao.user_dao')", "type": "direct_call"},
    {"from": "M002", "to": null, "via": "ngx.shared.rate_limit_counter", "type": "shared_state"}
  ]
}
```

**生成原则**：
- LLM **必须**读 source-summary.json 中每个模块的 key_files 才能生成
- 每个 source 条目的 `how` 字段描述**该项目**的具体提取方式，不套用框架模板
- 如果 source-summary 模块数多（>20），可以按类聚合（`"file": "internal/service/*.go"`）
- extraction-plan 决定 Phase 3 每个 Step 读哪些文件、用什么逻辑提取，替代 specialist skill 中的硬编码映射表
- `abstraction_sources` 指向 source-summary.abstractions 中发现的复用模式的**具体实现文件**，Phase 3 生成片段时 LLM 应读这些文件理解复用契约，确保目标代码不丢失复用结构
- `dependency_map` — LLM 读 key_files 中的 import/require/include 语句后填充的**模块间依赖关系**。替代 cr_discover.py 的机械式 import 解析。LLM 可理解任何语言的依赖语法（Go import, JS require, Lua require, Python import, C# using, Rust use, nginx include/lua_file 引用等）。Phase 4 外循环 OL-D3 横切覆盖度检查读此字段而非 source-summary.modules[].dependencies

---

按顺序，每步：LLM 按 extraction-plan 读指定文件 → 生成 JSON 片段 → **4D 自检** → 脚本合并 → 标准产物。

**archetype 适配**：LLM 读 `replicate-config.project_archetype`，对以下 Step 调整生成策略：
- task-inventory：标准应用 → 用户任务（owner_role + frequency + main_flow）；算法引擎 → 算法规格（formal_properties + state_transitions）；SDK/Library → 函数签名（parameters + return_type + memory_ownership）
- test-vectors：标准应用 → 单输入单输出；算法 → 多角色并发序列；SDK → 函数调用 + ABI 验证
- experience-map：有 UI → 生成；纯算法/SDK → 跳过
LLM 根据 archetype 描述自行决定具体策略，不受上述示例限制。

### 4D 片段自检（每个 Step 生成后立即执行）

每生成一个模块的片段，LLM 用四维追问验证片段质量：

| 维度 | 追问 | 不通过则 |
|------|------|---------|
| **D1 结论** | 提取的 task/role/flow 是否完整覆盖该模块源码中的业务逻辑？有没有遗漏的入口？ | 补充遗漏项 |
| **D2 证据** | 每个 acceptance_criteria 能追溯到源码哪个文件哪段逻辑？protection_level 的判断依据是什么？ | 补充 `_evidence` 内部注释 |
| **D3 约束** | 遗漏了什么前置条件？异常路径覆盖了吗？跨模块依赖标注了吗？ | 补充 prerequisites/exceptions |
| **D4 决策** | category 判为 core 而非 basic 的理由？audience_type 判断是否合理？ | 修正判断或补充理由 |

4D 自检是**内嵌在每个 Step 中的思维过程**，不产出额外文件。如果自检发现问题，LLM 直接修正当前片段后再交给 merge 脚本。

**Step 3.1** — role-profiles → `cr_merge_roles.py` → `product-map/role-profiles.json`
- LLM 按 extraction-plan.role_sources 读指定文件提取角色
- **LLM 片段必须输出 `audience_type`**（consumer / professional）— 基于角色在源码中的实际行为判断，不依赖名称关键词
- 可选：`operation_profile`（frequency/density/screen_granularity）

**Step 3.1.5** — experience-map stub（仅 frontend/fullstack）→ `cr_merge_screens.py` → `experience-map/experience-map.json`
- LLM 按 extraction-plan.screen_sources 读指定页面文件提取屏幕信息
- **LLM 片段必须输出每个 component 的 `render_as`**（12 值枚举）— 基于组件在页面中的实际用途判断
- **LLM 片段应输出 `layout_type`**（语义化布局名，如 auth_card、priority_queue，不用通用名如 "form"）

**Step 3.1.8** — 素材迁移（仅 frontend/fullstack 且 asset-inventory.json 存在时执行）

LLM 按 extraction-plan.asset_sources 处理每类素材：
- `copy` → 复制文件到目标项目对应目录 + 更新代码中的引用路径（源框架路径 → 目标框架路径）
- `transform` → LLM 读源主题/i18n 文件 → 生成目标框架等价配置（如 Ant Design token → Element Plus CSS Variables）
- `replace` → LLM 按 stack-mapping 转换格式（如 React SVG 组件 → Vue SFC 组件）

**路径映射**由 LLM 根据目标框架惯例决定：
- Next.js `public/` → Vite `public/`（直接映射）
- Next.js `app/*/icon.svg` (import) → Vue `src/assets/icons/` (import)
- 具体映射写入 `asset-migration-map.json` 供 cr-fidelity U7 验证

**Step 3.2** — task-inventory（两轮）→ `cr_merge_tasks.py` → `product-map/task-inventory.json`
- LLM 按 extraction-plan.task_sources 读指定文件提取任务
- 第一轮：骨架（id, title, module, type, role_id, category, protection_level）
- 第二轮：深层字段（acceptance_criteria, api_endpoint, prerequisites — 仅 functional+）
- **LLM 片段必须输出 `protection_level`**（core / defensible / nice_to_have）— 基于源码中该功能的业务重要性判断
- **LLM 片段必须输出结构化 `inputs`/`outputs`** — `inputs: {fields: [], defaults: {}}`，`outputs: {states: [], messages: [], records: [], notifications: []}`

**Step 3.3** — business-flows（functional+）→ `cr_merge_flows.py` → `product-map/business-flows.json`
- LLM 按 extraction-plan.flow_sources 读指定文件追踪完整业务流程
- 每个 flow 引用 task_id 列表（来自 Step 3.2 产物）

**Step 3.4** — use-case-tree + report（functional+）→ `cr_merge_usecases.py` + `cr_gen_usecase_report.py`
- 输出为**扁平 `use_cases` 数组**（v2.5.0+），每条包含显式 role_id、task_id、functional_area_name
- `then` 字段必须是**数组**（不是字符串）
- type 枚举已扩展至 13 种（含 journey_guidance, state_transition 等）
- report 由 gen 脚本从 JSON 自动生成，LLM 不直接写 Markdown

**Step 3.5** — constraints（exact only）→ `cr_merge_constraints.py` → `product-map/constraints.json`
- 标记源码中的硬约束：并发限制、数据一致性要求、外部 API 限流
- 标记已知 bug 和技术债（exact 保真度特有）

**Step 3.5.5** — 测试向量提取 → `test-vectors.json`

LLM 读 infrastructure-profile 中 `cannot_substitute: true` 或 `compatibility: exact` 的组件的源码实现，提取可验证的测试向量。

**向量模型由 LLM 根据 project_archetype 决定**（以下为常见模型，不限定）：

**模型 A — 单步（标准应用/加密/编解码）**：
```json
{"input": "...", "expected_output": "...", "description": "..."}
```

**模型 B — 多步序列（状态机/协议/SDK 调用链）**：
```json
{
  "initial_state": "...",
  "steps": [
    {"input": "...", "expected_state": "...", "expected_output": "..."},
    {"input": "...", "expected_state": "...", "expected_output": "..."}
  ]
}
```

**模型 C — 多角色并发（CRDT/协作/分布式）**：
```json
{
  "initial_state": "...",
  "operations": [
    {"actor": "A", "op": "...", "clock": "..."},
    {"actor": "B", "op": "...", "clock": "..."}
  ],
  "expected_merged_state": "...",
  "property": "LLM 描述该场景验证的形式化属性（如交换律、幂等性）"
}
```

**模型 D — ABI 签名（SDK/Library）**：
```json
{
  "function": "pm_process",
  "signature": {"params": ["pm_context_t*", "const pm_request_t*"], "return": "int"},
  "memory_ownership": {"param_0": "borrowed", "param_1": "borrowed", "return": "value"},
  "call_convention": "cdecl"
}
```

LLM 可以在同一个 test-vectors.json 中混合使用多种模型。

**向量来源**（优先级）：源码单元测试 > 标准测试向量（NIST/RFC） > 源码常量 > LLM 构造

**提取来源**（优先级）：
1. 源码的单元测试中已有的测试数据
2. 源码中的常量/fixture 数据
3. LLM 读懂算法后手动构造的测试向量

**用途**：dev-forge 生成目标代码后，用这些 test vectors 验证目标实现的行为与源码一致。cr-fidelity F8 基础设施还原可直接跑这些 vectors。

**Step 3.6** — 索引 + 汇总 → `cr_gen_indexes.py` + `cr_gen_product_map.py`
- task-index.json：轻量索引供下游按需加载
- flow-index.json：业务流索引
- product-map.json：全局汇总（统计 + 元信息 + **experience_priority**）
- `experience_priority` 从角色 audience_type 和任务分布自动推断 — dev-forge 全链路依赖此字段

**生成顺序有依赖**：role-profiles → task-inventory → business-flows → use-case-tree → constraints。
后续产物引用前序产物的 ID。

**每次 LLM 调用的上下文**：
- source-summary.json（~4-8 KB，常驻全局视角）
- 当前模块源码（~10-30 KB）
- 目标 schema 定义（~2-4 KB，按需加载）
- replicate-config 摘要（~1 KB）

---

### Phase 4: Verify & Handoff

**Step 4a** — `cr_validate.py` 结构校验 + **内循环修复**
- 检查项：必填字段完整、ID 引用有效、role_id/flow_id 存在、schema 合规
- 不通过 → 进入内循环修复：

```
内循环（CG-1 收敛控制）:
  1. 错误清单交 LLM 修正对应片段
  2. 重新 merge + validate
  3. 分类失败：
     - SCHEMA_ERROR  — 字段缺失/格式错误 → 修片段
     - REF_ERROR     — ID 引用断裂 → 修引用
     - LOGIC_GAP     — 业务逻辑不完整 → 补充片段
  4. 收敛条件：
     - 最多 3 轮修复
     - 每轮错误数必须 ≤ 上一轮（单调递减）
     - 违反单调递减 → 停止修复，剩余标记为 KNOWN_GAP
     - 第 3 轮仍有错误 → 记录为 KNOWN_GAP，继续 Step 4b
```

**Step 4b** — **6V 多维审计**（LLM 执行，不依赖外部工具）

LLM 从六个视角审查已合并产物，输出问题清单写入 `replicate-report.md`：

| 视角 | 审查内容 | 检查方式 |
|------|---------|---------|
| **user** | 每个角色的核心任务是否都被提取了？有没有角色有 0 个 task？ | 比对 role-profiles × task-inventory |
| **business** | 核心业务流是否有 flow 覆盖？orphan_tasks 中有没有核心任务？ | 检查 business-flows 覆盖 + orphan 列表 |
| **tech** | 技术约束（API 限制、并发、事务）是否进入 constraints 或 task.rules？ | 检查 constraint_sources 覆盖 |
| **data** | 数据实体是否完整？字段、关系、索引是否被记录？ | 比对 source-summary.data_entities × task.inputs/outputs |
| **ux** | （仅 frontend/fullstack）screen 的 states 是否覆盖 empty/loading/error/success？ | 检查 experience-map screens |
| **risk** | 安全/合规/隐私约束是否标注？支付/医疗/金融等高风险操作有 protection_level=core？ | 检查 constraints + task.protection_level |

6V 发现的问题分为两类：
- **可修复**：遗漏的 task、缺失的 flow 引用 → 回到 Step 4a 内循环补充
- **需标注**：无法从源码提取的信息（如合规要求需要人工确认）→ 写入 report 的 warnings

**Step 4b.5** — **注意力管理评估**（仅当 `experience_priority.mode` = consumer 或 mixed）

LLM 对 experience-map 中的 consumer 屏幕执行注意力负载检查：

| 检查项 | 阈值 | 问题标记 |
|--------|------|---------|
| 单屏操作步骤数 | >7 步 | `ATTENTION_OVERLOAD` |
| 跨屏记忆需求 | 需要用户记住前一屏信息才能完成当前操作 | `MEMORY_BURDEN` |
| 上下文切换 | 同一 flow 中页面跳转 >3 次 | `CONTEXT_SWITCH` |
| 反馈缺失 | 操作后无 loading/success 状态 | `FEEDBACK_GAP` |

注意力问题写入对应 screen 的 `_attention_flags` 字段，同时汇总到 report。这些 flag 在 dev-forge 的 design-to-spec 阶段会被消费，驱动 UI 简化决策。

**Step 4c** — XV 交叉验证（可选，需 `OPENROUTER_API_KEY`）
- 用不同模型审查产物一致性 → 问题写入产物 flags 字段
- 无 API key 时静默跳过

**Step 4d** — **外循环：意图保真验证**

> "走了这么多步，还在正确的路上吗？"

LLM 回到 source-summary.json 原点，验证提取结果是否覆盖业务意图：

```
OL-D1 模块覆盖度:
  - 读 source-summary.modules（全部模块清单）
  - 每个模块是否产出了至少 1 个 task？
  - file_count > 20 但 task_count = 0 的模块 → 标记为「提取遗漏」

OL-D2 抽象保全度:
  - 读 source-summary.abstractions
  - 每个 consumer_count > 3 的抽象是否进入了 stack-mapping.abstraction_mapping？
  - 未映射的高复用抽象 → 标记为「复用断裂」

OL-D3 横切覆盖度:
  - 读 extraction-plan.dependency_map（LLM 生成的模块间依赖，替代 cr_discover 的机械解析）
  - 读 extraction-plan.cross_cutting
  - 每个 dependency_map 中 type=middleware 的依赖是否在 flow 或 task.prerequisites 中出现？
  - 每个 cross_cutting 关注点是否有对应 task 或 flow 覆盖？
  - 未覆盖的横切点 → 标记为「横切遗漏」

OL-D4 角色完整性:
  - 读 role-profiles.json
  - 每个角色是否有 ≥1 个 use-case（happy_path）？
  - 无 use-case 的角色 → 标记为「角色空壳」

收敛控制（CG-3）:
  - 外循环发现的缺口总数 ≤ Phase 3 产物总条目数的 20%
  - 超过 20% → 停止补充，在 report 中标记"提取覆盖不足，建议提高保真度或扩大分析范围"
  - 外循环最多执行 1 轮（不递归）

追加项处理:
  汇总 OL-D1~D4 的缺口 → 回到 Phase 3 对应 Step 补充片段 → 重新 merge + validate
```

**Step 4e** — `cr_gen_report.py` → replicate-report.md
- 包含：源码概况、保真度、模块覆盖率、跳过项、校验结果、6V 审计结果、注意力评估、XV 发现、外循环意图覆盖度

**Step 4f** — Handoff
- 输出产物清单（路径 + 文件大小）
- 推荐下一步：`/project-setup` → `/design-to-spec` → `/task-execute`
- 跨栈复刻额外提示：检查 stack-mapping.json 中的手动决策点
- KNOWN_GAP 列表（内循环未修复 + 外循环超 20% 的遗漏项）

---

## 铁律

1. **Preflight + Discovery 收完所有参数** — Phase 2 结束后不再问任何配置问题
2. **source-summary 常驻上下文** — 所有 Phase 3 LLM 调用都包含它作为全局视角
3. **每次 LLM 调用单一目标** — 一次只生成一种产物的一个模块片段
4. **脚本合并产物** — LLM 不负责跨模块合并或 ID 分配
5. **标准产物路径** — task-inventory / business-flows / role-profiles → `product-map/`，use-case-tree → `use-case/`，CR 过程文件 → `code-replicate/`
6. **片段文件不是最终产物** — fragments/ 下的临时 JSON 仅供 merge 脚本消费，不交给 dev-forge
7. **业务意图优先** — 提取"做什么"，不复制"怎么做"；实现决策由目标生态填充
8. **下游必填字段** — `experience_priority`（product-map）、`protection_level`（task）、`audience_type`（role）、`render_as`（component）必须生成，dev-forge 全链路依赖
9. **结构化字段** — `inputs`/`outputs`/`audit` 必须使用对象格式（非简单数组），`then`（use-case）必须是数组
10. **LLM 直出优先** — `audience_type`、`protection_level`、`render_as` 等语义字段必须由 LLM 在片段中直接输出（基于源码语义理解），脚本仅做 fallback 兜底。禁止依赖名称关键词模式匹配作为主要判断逻辑
11. **extraction-plan 驱动** — Phase 3 的每个 Step 必须按 extraction-plan.json 中指定的文件和提取方式工作，不套用框架模板。extraction-plan 本身由 LLM 基于 source-summary 生成，确保适配任何技术栈和项目结构
12. **抽象复用传递** — 源码的复用模式（source-summary.abstractions）必须传递到目标代码。跨栈时通过 stack-mapping.abstraction_mapping 映射到目标栈等价机制；同栈时 dev-forge 直接读 abstractions。禁止将源码中 N 个模块共享的基类/mixin/DI 展开为 N 份重复代码
13. **4D 片段自检** — Phase 3 每个 Step 生成片段后必须执行 4D 追问（结论/证据/约束/决策），发现问题当场修正，不等到 Phase 4
14. **6V 多维审计** — Phase 4 必须从 user/business/tech/data/ux/risk 六个视角审查产物，防止单维盲区
15. **内循环收敛** — Phase 4a 修复循环遵循 CG-1：最多 3 轮、单调递减、违反则停止。防止无限修复循环
16. **外循环意图保真** — Phase 4d 回到 source-summary 原点验证提取覆盖度，遵循 CG-3：追加缺口 ≤ 总条目 20%、最多 1 轮。防止提取产物偏离源码业务意图
17. **跨平台适配** — 当源平台和目标平台交互模型不同（mobile↔desktop）时，必须生成 `platform_adaptation`。产物中的 UX 模式（布局、手势、导航、注意力阈值）不可原样传递到不同平台的目标代码。cr-fidelity 评估时使用适配后的阈值和排除列表
18. **配置即代码** — 非代码配置文件（nginx.conf, routes.yaml, OpenAPI spec, rbac.yaml, upstream.conf 等）可能包含路由定义、权限规则、基础设施配置等业务逻辑。extraction-plan 必须将这些文件纳入 task/role/flow 来源，使用 `"module": null` 引用根目录文件。source-summary.infrastructure 必须记录上游服务、共享内存、负载均衡等基础设施依赖
19. **基础设施先于业务** — Phase 2b-infra 必须在业务提取（Phase 3）之前完成。LLM 通过读代码行为（不是包名匹配）盘点所有基础设施组件，特别是自研组件、非标准协议、自定义加密、二进制 SDK。`cannot_substitute: true` 的组件禁止近似替代。通信协议和加密如果是耦合实现（如加密隧道），必须作为一个整体组件盘点，不可拆分
20. **协议必须结构化** — 自定义协议/加密/序列化组件必须输出 `protocol_spec`（帧格式 + 状态机 + 测试向量），不可只用文本描述。测试向量从源码测试或常量中提取，使目标代码可以精确验证行为一致性
21. **运行时验证** — cr-fidelity 不能只做代码对比（静态），必须包含运行时验证：构建（R1）、冒烟启动（R2）、测试向量执行（R3）、协议兼容性测试（R4）。综合分 = 静态分 × 0.5 + 运行时分 × 0.5。构建失败 = 一切白费
22. **项目特征驱动** — LLM 在 Phase 2b-arch 识别 project_archetype（自由描述，不限枚举），后续所有阶段（产物格式、测试向量模型、验证维度）均由 archetype 驱动。标准 CRUD 应用用 task-inventory + 单步向量；算法引擎用形式化规格 + 多角色并发向量；SDK/Library 用 ABI 签名 + 内存模型。混合项目可按模块分别标注
23. **素材即代码** — 前端/全栈项目的静态资源（图标、图片、字体、动画、主题变量、i18n 文案）是代码的组成部分，缺失则运行时碎图/缺字体/key 显示。Phase 2b-assets 必须盘点所有与代码有引用关系的素材，Phase 3.1.8 按 copy/transform/replace 三种方式迁移。cr-fidelity U7 验证素材完整性

---

## 保真度控制

保真度不决定生成哪些 CR 文件，而是决定标准产物中哪些字段被填充、填到多深。

| 级别 | 分析深度 | 产物输出 |
|------|---------|---------|
| interface | 只看入口层签名 | task-inventory(精简) + role-profiles（含 audience_type）+ product-map（含 experience_priority） |
| functional | 读函数体，追踪逻辑 | 上 + business-flows（含 systems/handoff）+ use-case-tree（扁平数组）+ task 结构化字段补全 |
| architecture | 额外分析模块依赖 | 上 + task 增加 module/prerequisites/cross_dept + innovation_use_case |
| exact | 额外标记 bug/约束 | 上 + constraints.json + task.flags |

> 完整说明详见 ${CLAUDE_PLUGIN_ROOT}/docs/fidelity-guide.md

---

## 断点续跑

replicate-config.json 的 `progress` 字段追踪：`current_phase`, `current_step`, `completed_steps`, `fragments`。

- 检测到 config 且 `progress.current_phase > 1` → 跳到对应阶段
- `--from-phase N` → 强制重跑（清除该阶段及之后的 progress）
- 已生成的标准产物重跑时先删除再重新合并
- fragments/ 目录在对应阶段重跑时清空

断点续跑流程：
1. Phase 1 检测到 replicate-config.json 存在
2. 读取 `progress.current_phase` 和 `progress.current_step`
3. 跳过已完成步骤，从中断点继续
4. 用户可用 `--from-phase 3` 强制从 Phase 3 重新开始

> Schema 详见 ${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md

---

## 错误处理

| 场景 | 处理 |
|------|------|
| Git clone 失败 | Phase 1 报错退出 |
| 源码为空 | Phase 2a 报错退出 |
| LLM 返回无效 JSON | 重试一次，仍失败 → 跳过模块，标记 report |
| cr_validate.py 失败 | 错误清单给 LLM 修正，最多 2 轮 |
| 模块源码过大（>100KB） | 只读 key_files，标记 partial_analysis |
| 脚本不存在 | LLM 直接生成完整产物（降级模式） |

---

## 产物路径

**标准产物**（dev-forge 可消费）：
- `.allforai/product-map/`: product-map.json, task-inventory.json, role-profiles.json, business-flows.json, constraints.json, task-index.json, flow-index.json
- `.allforai/experience-map/`: experience-map.json（frontend/fullstack stub）
- `.allforai/use-case/`: use-case-tree.json, use-case-report.md

**CR 专属过程文件**：
- `.allforai/code-replicate/`: replicate-config.json, source-summary.json, discovery-profile.json, extraction-plan.json, stack-mapping.json, replicate-report.md
- `.allforai/code-replicate/fragments/`: 中间片段（合并后可删除）

---

## 脚本调用参考

所有脚本位于 `${CLAUDE_PLUGIN_ROOT}/scripts/`：

```bash
# Phase 2: Discovery (with optional LLM-generated profile)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_discover.py <source_path> <output_path> [--profile <profile_path>]

# Phase 3: Merge scripts
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_roles.py <base_path> <fragments_dir>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_screens.py <base_path> <fragments_dir>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_tasks.py <base_path> <fragments_dir>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_flows.py <base_path> <fragments_dir>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_usecases.py <base_path> <fragments_dir>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_merge_constraints.py <base_path> <fragments_dir>

# Phase 3: Generation scripts
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_gen_usecase_report.py <base_path>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_gen_indexes.py <base_path>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_gen_product_map.py <base_path>

# Phase 4: Validation & Report
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_validate.py <base_path>
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cr_gen_report.py <base_path>
```

**merge 脚本约定**：
- 读 `<fragments_dir>/*.json` → 合并去重 → 分配连续 ID → 写入 `<base_path>` 对应标准路径
- fragments 文件名格式：`{module_name}.json`（每模块一个片段文件）
- 合并时自动处理：ID 重编号、跨片段引用修正、重复条目去重

**gen 脚本约定**：
- 读已合并产物 → 生成派生文件（report / index / summary）
- 不修改已合并的标准产物

**LLM 片段生成格式**：
- 每次 LLM 调用输出一个模块的 JSON 片段
- 片段使用临时 ID（如 `TMP-001`），merge 脚本统一重编号
- 跨模块引用使用 `$ref:module_name:tmp_id` 占位符，merge 脚本解析替换
- **片段必须包含语义字段**（不可省略让脚本猜测）：
  - role 片段：`audience_type`（consumer / professional）
  - task 片段：`protection_level`（core / defensible / nice_to_have）、结构化 `inputs`/`outputs`
  - screen 片段：每个 component 的 `render_as`（12 值枚举）、`layout_type`（语义名称）
