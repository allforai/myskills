---
description: "测试驱动的质量锻造：审计测试缺口 → 补测试 → 修 bug → 直到全绿。覆盖测试金字塔全层级（unit / component / integration / platform-ui / e2e-chain）。模式: full / analyze / fix"
argument-hint: "[mode: full|analyze|fix] [--sub-project <name>] [--module <name>]"
allowed-tools: ["Read", "Write", "Edit", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "Agent"]
---

# TestForge — 测试驱动的质量锻造

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 定位

```
product-verify  "代码实现了功能吗？"       → 只报告不改代码
testforge       "测试代码够好吗？够全吗？" → 审计 + 生成测试 + E2E 链 + 修 bug + 全绿
```

testforge 审查的是**项目自身的测试代码**，用 FVL 三维验证发现缺口。覆盖**测试金字塔全层级**：

```
     ╱ E2E Chains ╲        ← 跨子项目业务链（Path B）
    ╱  Platform UI  ╲       ← 同一场景 × N 个平台的 UI 自动化（Path C）
   ╱   Integration   ╲      ← 多模块协作测试（Path D）
  ╱     Component     ╲     ← UI 组件渲染 + 交互 + Flutter widget test（Path A）
 ╱        Unit         ╲    ← 函数、store、service、validation（Path A）
```

不只补测试，还主动推导"没人想到但该有"的场景，发现业务 bug 直接修复，循环至全绿。

## 模式路由

根据用户参数决定执行模式：

- **无参数 或 `full`** → 完整锻造：Phase 0 → 1 → 2 → 3 → 4 → 5 → 6
- **`analyze`** → 仅审计：Phase 0 → 1 → 2 → 3 → Step 4.0(静态接缝预检) → 6（不补测试不修代码，但 Step 4.0 纯静态分析纳入审计）
- **`fix`** → 仅锻造：Phase 0 → 4 → 6（用已有 `testforge-analysis.json`，若分析文件时间早于最新 git commit 则警告并建议重新 analyze；若文件不存在则报错：「未找到 testforge-analysis.json，请先运行 `/testforge analyze`」）

`--sub-project <name>` 限制只处理指定子项目。
`--module <name>` 限制只处理指定模块（Phase 1 仅审计该模块相关源文件，Phase 4 仅锻造该模块的缺口）。

---

## 上游消费链（Front-load Decisions）

Phase 0 的决策项可从上游产物自动获取，**已从上游获取的决策直接采用（展示一行摘要），仅缺失或冲突项才询问用户**：

```
优先级 1: .allforai/testforge/testforge-decisions.json（自身 resume 缓存）
    ↓ 不存在或过期
优先级 2: .allforai/project-forge/project-manifest.json（project-setup 产出）
    ↓ 不存在
优先级 3: 自动检测（扫描 package.json / go.mod / pubspec.yaml + 测试配置文件）
    ↓ 无法推断
优先级 4: AskUserQuestion 询问用户
```

**字段映射表**：

| Phase 0 决策项 | project-manifest.json | 自动检测方式 |
|---------------|----------------------|-------------|
| sub-projects | `sub_projects[]` | 扫描根目录下含 `package.json` / `go.mod` / `pubspec.yaml` 的子目录 |
| tech-stack | `sub_projects[].tech_stack` | 读取配置文件推断 |
| test-framework | — | vitest.config → Vitest, jest.config → Jest, go test → Go testing, flutter_test → flutter_test, pytest → pytest |
| test-patterns | — | 扫描已有测试文件的命名模式和目录结构 |
| e2e-framework | — | playwright.config.* → Playwright, cypress.config.* → Cypress, maestro/ → Maestro |
| business-flows | `.allforai/product-map/business-flows.json` | 不存在则 E2E 链推导降级 |
| page-routes | — | 扫描 pages/ / views/ / routes 目录提取前端路由表 |
| api-endpoints | — | 扫描后端路由注册文件（router.go / routes.ts 等）提取 API 路由表 |

---

## Phase 0：项目画像 + 测试基础设施探测

### Step 0.1: 消费上游决策

按上游消费链优先级获取子项目列表、技术栈、测试框架。

### Step 0.2: 测试基础设施探测

对每个子项目，扫描以下维度：

| 维度 | 探测方式 | 产出 |
|------|---------|------|
| 单元测试框架 | Glob `**/vitest.config.*` `**/jest.config.*` + `go.mod` + `pubspec.yaml` | unit_framework |
| 测试配置 | Read 配置文件 → 提取 environment, setupFiles, include patterns | config_summary |
| Setup 文件 | Read setupFiles 路径 → 提取 mock 列表和 plugin 注册 | setup_summary |
| Test Helpers | Glob `**/__tests__/{render,helpers,utils,factories}.*` `**/test/helpers/**` | helpers_list |
| Factories | Glob `**/__tests__/factories/**` `**/test/factories/**` | factory_list |
| 现有单元测试 | Glob `**/*.test.{ts,tsx}` `**/*_test.go` `**/*_test.dart` | existing_unit_tests[] |
| 测试脚本 | Read package.json → scripts.test / scripts.test:coverage | test_commands |
| E2E 框架 | Glob `**/playwright.config.*` `**/cypress.config.*` `**/maestro/**` | e2e_framework |
| 现有 E2E 测试 | Glob `**/e2e/**/*.spec.{ts,js}` `**/*.e2e.{ts,js}` | existing_e2e_tests[] |
| 前端路由表 | Glob `**/pages/**/*.{vue,tsx,jsx}` `**/views/**/*.{vue,tsx,jsx}` + 读路由配置文件 | page_routes[] |
| API 路由表 | Grep 后端路由注册模式（`router.GET/POST/PUT/DELETE` / `app.use` 等） | api_endpoints[] |
| 子项目端口 | 读 .env / project-manifest / 配置文件中的 port 定义 | ports_map |
| E2E 工具可用性 | 检测 Playwright MCP 工具 / `which maestro` / `which xcodebuild` | e2e_tools_available |
| 跨平台目标 | 见下方「跨平台探测」 | target_platforms[] |
| 平台测试环境 | 见下方「跨平台探测」 | available_platforms[] |

**跨平台探测**（Flutter / React Native / .NET MAUI / KMP 等跨平台框架）：

跨平台框架一份代码编译到多个平台。testforge 的原则是**能测几个平台就测几个平台**。

Step 1: 识别目标平台

| 框架 | 探测方式 | 可能的目标平台 |
|------|---------|--------------|
| Flutter | `pubspec.yaml` 存在 + Glob `android/` `ios/` `web/` `macos/` `linux/` `windows/` | 存在的目录 = 目标平台 |
| React Native | `react-native` in package.json + Glob `android/` `ios/` + 检查 `react-native-web` 依赖 | android, ios, web(如有) |
| .NET MAUI | `*.csproj` 含 `<TargetFrameworks>` | 解析 TargetFrameworks |
| KMP | `build.gradle.kts` 含 `kotlin("multiplatform")` | 解析 targets |

Step 2: 检测平台测试环境可用性

| 平台 | 可用条件 | 不可用时降级 |
|------|---------|------------|
| **主机**（unit/widget） | 始终可用 | — |
| **Web** | Playwright 可用（MCP 或 CLI） | 生成脚本 PLAN_ONLY |
| **Android** | `which adb` + 设备/模拟器在线（`adb devices`） | 跳过 Android 集成测试 |
| **iOS** | macOS + `which xcodebuild` + 模拟器可用 | 跳过 iOS 集成测试 |
| **macOS** | macOS + 项目有 macos/ 目标 | 跳过 macOS 测试 |
| **Linux** | Linux + 项目有 linux/ 目标 | 跳过 Linux 测试 |
| **Windows** | Windows + 项目有 windows/ 目标 | 跳过 Windows 测试 |

输出示例：
```
跨平台目标: [android, ios, web, macos]
可用测试环境: [主机 ✓, web ✓, android ✗(无模拟器), ios ✗(非macOS), macos ✗(非macOS)]
→ 可执行: 主机测试(unit/widget) + Web E2E
→ 仅生成脚本: Android/iOS/macOS 集成测试
```

### Step 0.3: 基线测试运行

**在审计之前，必须先跑一遍现有测试建立基线。** 不跑基线 → Phase 4 分不清"新测试暴露的 bug"还是"原来就坏的测试"。

对每个子项目，使用探测到的测试命令运行全量测试：

```
逐子项目运行（可并行，各子项目互不影响）：
  - 前端：npm run test / npx vitest run
  - 后端：go test ./... / pytest
  - 跨平台：flutter test
  - E2E：npx playwright test / maestro test（仅已有脚本，不生成新的）
        ⚠ E2E 基线需要应用运行；先检查端口可达性，不可达则跳过，标记 E2E_BASELINE_SKIPPED

记录：
  baseline_tests: {总测试数}
  baseline_pass: {通过数}
  baseline_fail: {失败数}
  baseline_skip: {跳过数}
  pre_existing_failures: [{文件, 测试名, 错误信息}]

处理：
  全部通过 → 基线清洁，继续
  有失败 → 记录为 PRE_EXISTING_FAILURE，Phase 4 的 CG-1 排除这些测试
  环境问题导致无法运行（如 Redis 不可用）→ 记录 ENV_ISSUE，该子项目基线标记为 PARTIAL
```

### Step 0.4: 输出画像摘要

```
## 测试画像

| 子项目 | 类型 | 单元框架 | E2E 框架 | 测试数 | 通过 | 失败 | Helpers | Factories |
|--------|------|---------|---------|-------|------|------|---------|-----------|
| ... | frontend/backend/cross-platform | ... | ... | ... | ... | ... | ... | ... |
```

写入 `.allforai/testforge/test-profile.json`。

### Step 0.5: 加载上游文档（按需）

检查并加载以下上游产物（存在则加载，不存在则标注缺失，不阻断）：

| 产物 | 路径 | 用途（Phase） |
|------|------|-------------|
| design.md | `.allforai/project-forge/sub-projects/*/design.md` | Phase 1 Layer 1 |
| design.json | `.allforai/project-forge/sub-projects/*/design.json` | Phase 1 Layer 1（API 端点提取） |
| tasks.md | `.allforai/project-forge/sub-projects/*/tasks.md` | Phase 1 Layer 2 |
| business-flows.json | `.allforai/product-map/business-flows.json` | Phase 1 Layer 3, Phase 3 Layer B, **Phase 4 E2E 链推导** |
| constraints.json | `.allforai/product-map/product-map.json` 中 constraints | Phase 1 Layer 3, Phase 5 |
| concept-baseline.json | `.allforai/product-concept/concept-baseline.json` | Phase 5 |
| role-profiles.json | `.allforai/product-map/role-profiles.json` | Phase 2 H2, Phase 3 Layer C, Phase 5 |
| use-case-tree.json | `.allforai/product-map/use-case-tree.json` | Phase 1 Layer 3, **Phase 4 E2E 负向场景** |
| e2e-scenarios.json | `.allforai/project-forge/e2e-scenarios.json` | Phase 4 E2E 链（已有规划则复用） |

**无上游文档时的降级**：
- 无 design.md/design.json → Phase 1 跳过 Layer 1，仅做 Layer 0（代码级审计）
- 无 tasks.md → Phase 1 跳过 Layer 2
- 无 product-map → Phase 1 跳过 Layer 3，Phase 3 跳过 Layer B/C，Phase 5 跳过
- 无 business-flows + 无 e2e-scenarios → Phase 4 跳过 E2E 链锻造，仅做单元/组件测试
- 全部缺失 → 仅做 Layer 0 代码级审计 + Phase 3 Layer A 代码级负空间 + Phase 4 单元测试锻造

写入 `testforge-decisions.json`。

---

## Phase 1：纵向审计 — tests ↔ 上游基准

> "每个该测的点，有测试守护吗？"

**跨子项目并行**：各子项目的审计互相独立，使用 Agent tool 并行执行。

### 验证基准链（从浅到深）

**Layer 0: tests ↔ 源代码**（始终执行）

对每个子项目的每个可测试源文件：

1. **覆盖映射**：将已有测试文件与源文件配对（按项目实际的测试目录结构匹配）
2. **标记状态**：
   - `COVERED` — 有对应测试文件且测试函数 ≥ 1
   - `PARTIAL` — 有测试文件但覆盖不足（分支覆盖 < 50%）
   - `UNCOVERED` — 无对应测试文件
   - `TRIVIAL` — 文件太简单不需要测试（纯类型定义、常量、re-export）
3. **分支分析**：对 COVERED 和 PARTIAL 文件，LLM 读源码提取：
   - if/switch/ternary 分支 → 测试覆盖了哪些分支？
   - error return / catch / throw → 错误路径有测试吗？
   - 边界条件（空值、零值、极值）→ 有边界测试吗？
4. **测试类型标注**：对每个缺口标注应在金字塔哪层测试：

```
test_type 分类逻辑（通用规则，不特化任何框架）：
├── unit        — 纯函数、工具函数、验证逻辑、状态管理、服务层、数据模型
├── component   — UI 组件渲染 + 用户交互 + 事件触发（含 Flutter widget test，主机运行无需设备）
├── integration — 多模块协作（API client + 状态管理 + 组件联动）
├── e2e_chain   — 跨 ≥2 个子项目的业务流（需要浏览器自动化或 API 串联）
└── platform_ui — 跨平台 UI 自动化测试（同一场景在每个可用平台各跑一遍）
                  Flutter/RN widget test 不属于此类（它们在主机运行，归入 component）
                  此类仅限需要真实平台环境的 UI 自动化：浏览器、模拟器、真机
```

**Layer 1: tests ↔ design.md**（有 design.md 时执行）

LLM 读 design.md / design.json，提取：
- API 端点定义 → 每个端点的正常响应 + 错误码有测试吗？
- 状态机定义 → 每个状态转换有测试覆盖吗？
- 数据模型关联 → 级联操作（删除父记录时子记录？）有测试吗？

**Layer 2: tests ↔ tasks.md**（有 tasks.md 时执行）

LLM 读 tasks.md，对每个 task 提取：
- `exceptions` → 每个异常路径有对应测试？
- `rules` → 每个业务规则有测试验证？
- `_Acceptance_` → 验收条件有对应断言？

**Layer 3: tests ↔ product-map**（有 product-map 时执行）

LLM 读 product-map，提取：
- `business-flows` 的关键节点 → 有测试守护该节点的逻辑？
- `constraints` 中 `enforcement: "hard"` → 有测试穿透验证约束生效？
- `use-case-tree` 的验收用例 → 有对应集成测试？
- **跨子项目业务流** → 有 E2E 链测试覆盖完整流程吗？（无 → 标为 `e2e_chain` 缺口）

### 4D 维度聚合

将所有 Layer 的缺口按 4D 维度归类：

| 维度 | 审计问题 | 基准来源 |
|------|---------|---------|
| **Data** | 数据操作（CRUD、关联、级联）有测试吗？ | design.md entities + tasks.md |
| **Interface** | API 正常/异常响应有测试吗？参数校验有测试吗？ | design.md endpoints + tasks.md rules |
| **Logic** | 业务规则、状态流转、权限判断有测试吗？ | tasks.md rules/exceptions + constraints |
| **UX** | 组件渲染、交互、错误提示、loading 状态有测试吗？ | experience-map screens/actions |

### 输出

写入 `.allforai/testforge/testforge-analysis.json`：

```json
{
  "analyzed_at": "ISO8601",
  "sub_projects": [{
    "name": "...",
    "source_files": 120,
    "test_files": 52,
    "file_coverage": { "COVERED": 45, "PARTIAL": 12, "UNCOVERED": 55, "TRIVIAL": 8 },
    "gaps": [
      {
        "id": "TG-001",
        "dimension": "Logic",
        "layer": 0,
        "source_file": "src/services/order.ts",
        "upstream_ref": null,
        "description": "订单服务 — 无测试覆盖",
        "severity": "CRITICAL",
        "test_type": "unit"
      },
      {
        "id": "TG-050",
        "dimension": "Logic",
        "layer": 3,
        "source_file": null,
        "upstream_ref": "business-flows.json#F003",
        "description": "交易闭环业务流 — 无跨端 E2E 链测试",
        "severity": "HIGH",
        "test_type": "e2e_chain"
      }
    ],
    "coverage_by_4d": {
      "Data": { "covered": 45, "gaps": 12, "rate": "78.9%" },
      "Interface": { "covered": 38, "gaps": 8, "rate": "82.6%" },
      "Logic": { "covered": 30, "gaps": 18, "rate": "62.5%" },
      "UX": { "covered": 25, "gaps": 15, "rate": "62.5%" }
    }
  }]
}
```

→ 输出进度：「Phase 1 纵向审计 ✓ L0:{a} L1:{b} L2:{c} L3:{d} 缺口（unit:{u} component:{c} integration:{i} platform_ui:{p} e2e:{e}）」

---

## Phase 2：横向审计 — 兄弟测试交叉验证

> "各子项目的测试之间一致吗？"

### 五类横向闭环

**H1: Mock 数据一致性**

后端测试 mock 的响应结构 ↔ 前端测试 mock 的请求/响应结构。
两边 mock 同一个 API，字段名和数据类型要一致。
不一致 = `MOCK_DRIFT`（测试绿了但上线会炸）。

扫描方式：
- Grep 前端测试文件中的 mock 返回值（`vi.fn()`, `mockResolvedValue`, `msw handlers` 等）
- Grep 后端测试文件中 mock 的响应结构
- 比对同一 API 端点的 mock 数据结构

**H2: 实体 CRUD 覆盖对称性**

跨角色看同一实体：后端对某实体有哪些 CRUD 测试？各前端有哪些？
哪些操作没有任何端测到？= `CROSS_PROJECT_GAP`

**H3: 业务规则测试归属**

一条约束可能涉及后端 + 前端（如"订单超时自动取消"）。
后端有定时任务/事件测试吗？前端有状态变更展示测试吗？
只测了一端 = `RULE_PARTIAL`

**H4: 错误处理对称性**

后端返回 4xx/5xx 错误 → 前端有没有测到这些错误码的 UI 处理？
后端测了错误返回但前端没测错误处理 = `ERROR_ASYMMETRY`

**H5: 跨站业务链完整性**（有 business-flows 或 ≥2 个前端子项目时执行）

从 API 路由表和页面路由表出发，按业务域分组（每组 = 同一实体的完整生命周期操作），检查：
- 实体从"创建"到"终态"的全链路，是否有跨站 E2E 测试覆盖？
- 只覆盖了部分站点 = `CHAIN_PARTIAL`
- 完全无 E2E 覆盖 = `CHAIN_MISSING`

### 输出

追加到 `testforge-analysis.json` 的 `horizontal_gaps` 字段：

```json
{
  "horizontal_gaps": [
    {
      "id": "HG-001",
      "type": "MOCK_DRIFT|CROSS_PROJECT_GAP|RULE_PARTIAL|ERROR_ASYMMETRY|CHAIN_PARTIAL|CHAIN_MISSING",
      "entity": "...",
      "description": "...",
      "affected_sub_projects": ["..."],
      "severity": "HIGH"
    }
  ]
}
```

→ 输出进度：「Phase 2 横向审计 ✓ MOCK_DRIFT:{a} CROSS_GAP:{b} RULE_PARTIAL:{c} ERROR_ASYM:{d} CHAIN:{e}」

---

## Phase 3：负空间推导

> "没人想到但该有的测试场景"

### 四层推导

**Layer A: 代码级负空间**（始终执行）

LLM 读每个未充分测试的源文件，主动推导：
- **并发竞态**：两个用户同时操作同一资源会怎样？
- **数据边界**：金额为 0/负数/超大值？字符串为空/超长/特殊字符？
- **状态不一致**：操作到一半失败，数据状态会不会脏？
- **权限越界**：低权限用户直接调高权限 API 会怎样？
- **外部依赖失败**：第三方 API 超时/返回异常格式？

**Layer B: 业务级负空间**（有 business-flows 时执行）

LLM 读业务流，推导每个节点的"如果不…会怎样"：
- **流程中断**：用户在中间步骤放弃，前序步骤的数据怎么处理？
- **逆向操作**：创建后能取消吗？取消后能恢复吗？
- **时序依赖**：A 操作必须在 B 之前，顺序反了呢？
- **资源耗尽**：库存为 0、余额不足、配额用完？

**Layer C: 跨端负空间**（有 role-profiles 时执行）

LLM 读角色定义，推导跨角色操作的边界：
- A 正在编辑，B 同时删除了这条数据？
- A 提交审批，B 在 A 提交瞬间修改了审批规则？
- 管理员禁用了用户，该用户的已登录会话怎样？

**Layer D: E2E 链负空间**（有 business-flows 且 ≥2 个子项目时执行）

LLM 读业务流和已有 E2E 链，推导跨站异常场景：
- **链路断裂**：子项目 A 操作成功但子项目 B 的对应页面未更新？
- **角色越权**：跳过审批步骤直接访问后续页面？
- **数据穿透延迟**：一端修改数据后，另一端需要刷新才能看到还是实时？
- **多端并发**：两个不同角色在不同子项目中同时操作同一实体？

### 标记与收敛

- 所有推导出的场景标记 `[DERIVED]`，与文档明确要求的场景区分
- 每个源文件推导的负空间场景 ≤ 5 个（取最高风险的）
- 总负空间场景 ≤ Phase 1 缺口数的 50%（CG-2 防膨胀）
- 推导出的场景必须能对应到具体代码路径或页面路径（不是纯假设）
- E2E 负空间场景标注 `test_type: "e2e_chain"`

### 输出

追加到 `testforge-analysis.json` 的 `negative_space` 字段：

```json
{
  "negative_space": [
    {
      "id": "NS-001",
      "layer": "A|B|C|D",
      "source_file": "src/services/order.ts",
      "trigger": "...",
      "scenario": "...",
      "risk": "high",
      "test_type": "unit|component|integration|e2e_chain|platform_ui",
      "derived": true
    }
  ]
}
```

→ 输出进度：「Phase 3 负空间 ✓ Layer A:{a} Layer B:{b} Layer C:{c} Layer D:{d}」

---

## Phase 4：锻造循环（Forge-Fix Loop）

> "补测试 → 跑测试 → 修 bug → 重跑 → 收敛"

### Step 4.0: 静态接缝预检（deadhunt + fieldcheck）

> **在写任何测试之前，先用静态分析秒级扫除接缝问题。**
> 实战数据：单元测试发现 0 个 bug，E2E 发现 51 个 bug，其中 35 个（69%）是 fieldcheck/deadhunt 能秒级检出的接缝问题。
> 前置静态检查可以避免大量无效的 E2E 修复轮次。

并行执行 2 个 Agent：
  Agent 1: 用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/commands/deadhunt.md`
           执行 /deadhunt static（死链 + CRUD 缺口 + 幽灵功能 + 接缝检查）
  Agent 2: 用 Read 加载 `${CLAUDE_PLUGIN_ROOT}/commands/fieldcheck.md`
           执行 /fieldcheck full（UI↔API↔Entity↔DB 字段一致性 + 接缝检查 SC-1~SC-5）

汇总结果：
  severity=critical 的问题 → 直接修复（不消耗 CG-1 轮次）
  severity=warning → 记录到报告，不阻塞
  修复后 → 运行构建验证（npm run build / go build）确保修复未破坏编译

---

### Step 4.1: 基础设施补全 + ENV_ISSUE 子项目处理（仅 full/fix 模式）

**ENV_ISSUE 子项目**（Phase 0 基线标记为 ENV_ISSUE 的子项目）：
- 仍然生成测试代码（代码审查有价值）
- 标记所有生成的测试为 `PLAN_ONLY`（不执行，不计入 CG-1）
- 报告中单独列出：「{sub-project}: 已生成 {N} 个测试，待环境就绪后执行」

检查测试基础设施是否充足：
- setup 文件缺失 → 参考同项目或最成熟子项目生成
- factories 不覆盖当前批次的实体 → 补
- render helpers 缺失 → 补
- E2E 配置缺失 → 根据探测到的 E2E 框架生成配置
- 平台测试 mock helpers 缺失 → 补
- 原则：复用已有风格，不另起炉灶

### Step 4.2: 批次规划 + 分路

将 Phase 1-3 的所有缺口按 `test_type` 分为 4 条锻造路径，每条路径内按优先级排序：

```
severity CRITICAL > HIGH > MEDIUM
dimension Logic > Interface > Data > UX（业务规则最先）
负空间 [DERIVED] 排在同 severity 的文档缺口之后
```

```
路径 A: Unit + Component（单元/组件测试）
  **仅对有业务逻辑的代码生成单元测试**：
  ✓ 补测试：状态机、业务规则、权限判断、金额计算、cron job、验证逻辑、数据转换
  ✗ 不补测试：纯 CRUD wrapper、API client 透传函数、纯 re-export、常量定义
  理由：纯透传代码的 bug 在接缝层（fieldcheck 已检出），单元测试 mock 掉了接缝反而测不出问题

  每批 5-8 个缺口（同模块、同层优先分组）
  依赖关系：service 层先于 page/component 层
  --module 过滤：仅保留属于指定模块的缺口

路径 D: Integration（集成测试）
  每批 3-5 个缺口
  依赖关系：单元测试通过后再做集成

路径 C: Platform UI（跨平台 UI 测试）
  对跨平台框架（Flutter/RN/MAUI 等），按可用平台逐个执行 UI 自动化测试：
  - 每个可用平台独立一批，使用对应工具
  - 同一套业务场景在每个平台各跑一遍
  依赖关系：unit/component（Path A）+ integration（Path D）先通过，再跑平台 UI
  非跨平台项目 → 此路径为空，自动跳过

路径 B: E2E Chain（跨站业务链测试）
  每批 1-2 条链（每条链是完整业务流）
  依赖关系：Path A/D/C 完成后再锻造链
```

**执行顺序**：Step 4.0(静态接缝预检) → Step 4.1(基础设施) → Step 4.2(批次规划) → Step 4.3 路径 A(仅逻辑层) → D → C → B(E2E 链) → Step 4.4(构建验证)

**跨子项目并行**：同一路径内，不同子项目互相独立，使用 Agent tool 并行执行。例如 Path A 中 website 和 admin 的单元测试可同时锻造。Path B 除外（E2E 链天然跨子项目，按链串行）。

### Step 4.3: 逐批锻造（内循环）

#### 路径 A/D: 单元 / 组件 / 集成测试

对每批：

```
1. 生成测试代码
   对每个缺口：
     a. Read 源代码 + 上游文档（design/tasks）
     b. Read 已有测试（避免重复）
     c. Read 已有 helpers/factories（复用）
     d. 生成测试代码（遵循项目现有风格和命名模式）
     e. 跑单个测试文件验证语法通过

2. 跑全量测试
   根据子项目类型选择运行命令：
   - 检测 package.json scripts.test → npm run test
   - 检测 go.mod → go test ./...
   - 检测 pubspec.yaml → flutter test（unit + widget，主机运行）
   - 检测 pytest / setup.py → pytest

3. 分类失败
   TEST_BUG  — 测试写错了（mock 不对、断言错误）→ 修测试
   BIZ_BUG   — 业务代码有 bug → 修业务代码
   ENV_ISSUE — 环境问题（DB/Redis 不可用等）→ 记录跳过

4. 修复 → 重跑

5. 收敛条件（CG-1）：
   - max 3 轮修复
   - 每轮失败数必须 ≤ 上一轮（单调递减）
   - 违反单调递减（失败数增加）→ 回滚该轮修改，标记剩余为 KNOWN_FAILURE
   - 第 3 轮仍失败 → 记录为 KNOWN_FAILURE，继续下一批
```

#### 路径 C: 跨平台 UI 自动化测试

> 同一套业务场景，在每个可用平台各跑一遍 UI 自动化测试。

**前置条件**：Path A（unit/component）和 Path D（integration）中该子项目的测试已通过。

**执行协议**：

```
1. 从 Phase 0 读取 target_platforms[] 和 available_platforms[]

2. 推导 UI 测试场景
   来源（按优先级）：
   a. 已有平台测试脚本（Glob integration_test/ / e2e/ / maestro/）
   b. business-flows 中属于该子项目的用户操作流
   c. Phase 1 中 test_type=platform_ui 的缺口
   d. 从页面路由表推导关键页面的 UI 测试（导航、表单、列表）

3. 逐平台执行（可用平台并行）

   | 平台 | 工具 | 执行方式 | 场景格式 |
   |------|------|---------|---------|
   | Web | Playwright | browser_navigate/click/snapshot 或 `npx playwright test` | .spec.ts |
   | Android | Maestro | `maestro test` | .yaml |
   | iOS | Maestro 或 XCUITest | `maestro test` 或 `xcodebuild test` | .yaml / .swift |
   | macOS | Playwright(Flutter Web 模式) 或 原生 | `flutter test integration_test/ -d macos` | _test.dart |
   | Linux | Playwright(Flutter Web 模式) 或 原生 | `flutter test integration_test/ -d linux` | _test.dart |

4. 跨平台差异记录
   同一场景在 A 平台通过但 B 平台失败 → 标记为 PLATFORM_SPECIFIC_BUG
   场景示例：Web 上按钮可点击但 Android 上被键盘遮挡

5. 不可用平台处理
   - 生成测试脚本但标记为 PLAN_ONLY
   - 报告中列出「已生成脚本，待 {platform} 环境就绪后执行」

6. 收敛（CG-1 同样适用，按平台独立计数）
```

#### 路径 B: E2E 链锻造

> 从业务流推导完整的跨站测试链，生成可执行的测试脚本。

**数据来源（按优先级）**：
1. `e2e-scenarios.json`（已有场景规划）→ 复用步骤定义，生成测试脚本
2. `business-flows.json`（业务流定义）→ 推导链路步骤，生成测试脚本
3. Phase 2 H5 `CHAIN_MISSING` 缺口 → 从 API 路由表 + 页面路由表反推链路
4. 以上全无 → 跳过 E2E 链锻造

**链路推导规则（通用，不特化任何业务域）**：

```
1. 识别链路候选
   读 business-flows，对每个 flow：
     - 提取涉及的角色（role-profiles 映射）和子项目
     - 跨 ≥2 个子项目的 flow → 标记为 E2E 链候选
     - 单子项目 flow → 跳过（已由单元/集成测试覆盖）
     - **等价子项目展开**：同一角色有多个 app（如 R001 同时分配 website 和 mobile），
       则该角色的每个 app 都必须独立参与 E2E 链测试。
       例如买家操作在 website 上测一遍，还要在 mobile 上测一遍（如环境可用）。
       不得仅测一端就声称该角色已覆盖。

2. 分解链路步骤
   对每条候选链，按 flow 的步骤序列：
     a. 确定每步操作的子项目和角色
     b. 从 page_routes[] 匹配该操作对应的页面 URL
     c. 从 api_endpoints[] 匹配该操作触发的 API
     d. 推导验证点：
        - UI 验证：元素可见/文本匹配/状态变化
        - API 验证：响应状态码/响应体字段
        - 数据验证：操作结果在其他子项目可见

3. 生成测试脚本
   根据探测到的 E2E 框架生成对应格式：
     - Playwright → .spec.ts 文件（test.describe + test.step）
     - Cypress → .cy.ts 文件
     - Maestro → .yaml 流程文件
     - 无 E2E 框架 → 生成 Playwright 配置 + 脚本（推荐默认）

4. 链路设计原则（通用）
   - 每条链完全自给自足：测试内自行创建数据，不依赖其他链或 seed 数据
   - 数据隔离：使用时间戳/随机后缀确保唯一性
   - 每步包含 Given-When-Then：前置条件 → 操作 → 验证
   - 失败时截图/日志以便调试
```

**E2E 测试工具路由**：

根据子项目类型和目标平台自动选择测试工具：

**原生项目**（单平台）：

| 子项目类型 | 测试工具 | 执行方式 |
|-----------|---------|---------|
| Web 前端（管理台/用户端） | **Playwright** | MCP browser_* 工具 或 CLI |
| 原生 iOS（Swift/SwiftUI） | **XCUITest** | `xcodebuild test` |
| 原生 Android（Kotlin/Java） | **Maestro** | CLI `maestro test` |
| 后端 | **curl / HTTP** | Bash API 调用验证 |

**跨平台项目**（同一代码库多平台）：

| 框架 | 平台 | 测试工具 | 执行方式 |
|------|------|---------|---------|
| Flutter | Web | **Playwright** | `flutter run -d chrome` + Playwright 测试 |
| Flutter | Android | **Maestro** 或 `flutter test integration_test/ -d emulator` | Maestro yaml 或 Dart integration test |
| Flutter | iOS | **Maestro** 或 `flutter test integration_test/ -d simulator` | Maestro yaml 或 Dart integration test |
| Flutter | macOS/Linux | `flutter test integration_test/ -d {platform}` | Dart integration test |
| RN | Web | **Playwright**（需 react-native-web） | Playwright .spec.ts |
| RN | Android | **Maestro** | `maestro test` |
| RN | iOS | **Maestro** | `maestro test` |

降级策略：
- Playwright MCP headed 模式失败（无 X Server）→ 加 `--headless` 参数重试，**不得降级为 curl**
- Playwright MCP 不可用 → 降级为 Playwright CLI（`npx playwright test --headed=false`）
- Maestro 不可用 → Flutter 降级为 `flutter test integration_test/`，RN 降级为 Detox
- 模拟器/真机不可用 → 跳过该平台 UI 测试，生成脚本标记 `PLAN_ONLY`
- 全部不可用 → 仅生成脚本 + 主机测试（unit/widget）

**铁律：UI 类测试（E2E 链的 Web 步骤、Platform UI）严禁降级为 curl/HTTP API 调用。**
必须使用浏览器自动化工具（Playwright/Cypress/Maestro）执行。
API 验证仅用于后端步骤（无 UI 的纯 API 端点验证）。
如果浏览器自动化环境不可用，必须先解决环境问题（安装 xvfb、配置 headless），不得跳过。

**E2E 链执行**：

```
（Step B.0 静态预检已前置到 Step 4.0，在所有 Path 之前执行）

Step B.1: 应用可达性检查
  逐子项目检查端口: curl -s -o /dev/null -w "%{http_code}" http://localhost:{port}
  全部可达 → 继续执行
  部分不可达 → AskUserQuestion 提示：
    「以下子项目未运行: {列表}。
     (1) 帮我启动（读取 package.json scripts.dev / go run 等）
     (2) 仅生成脚本，跳过执行
     (3) 我手动启动，稍后重试」
    用户选 1 → 尝试启动，成功则继续，失败则降级为 PLAN_ONLY
    用户选 2 → PLAN_ONLY
    用户选 3 → 等待用户确认后重新检查端口
  全部不可达 → 同上提示

Step B.2: 场景推导
  正向场景：从 business-flows 提取跨 ≥2 子项目的 flow → E2E 链
  负向场景：从 use-case-tree.json 提取 exception/boundary 用例中涉及跨子项目的 → 负向 E2E 链
  use-case-tree 不存在 → 跳过负向场景

Step B.3: 并行执行
  按数据隔离性分组，使用 Agent tool 并行执行：
  - 数据无交叉的链 → 分到不同 Agent
  - 共享数据的链 → 同一 Agent 内串行
  - 负向链单独分组（避免污染正向链数据）

  逐链、逐步执行：
  - Web 步骤：browser_navigate → browser_snapshot → browser_fill/click → browser_snapshot
  - API 步骤：Bash curl → 验证响应
  - 平台 UI 步骤：按工具路由执行
  - 跨子项目切换：navigate 到不同子项目 URL

Step B.4: 6V 诊断与失败分类
  对每个失败步骤，LLM 从 6 个工程视角深度诊断根因：

  | 维度 | 诊断问题 | 分类 |
  |------|---------|------|
  | V1 Contract | 前后端字段名/类型/路径不一致？ | CONTRACT_SYNC |
  | V2 Conformance | 环境不可达、超时、连接问题？ | ENV_ISSUE |
  | V3 Correctness | 代码逻辑未按规格实现？ | FIX_REQUIRED |
  | V4 Consistency | 跨子项目数据状态不一致？ | FIX_REQUIRED |
  | V5 Capability | 性能/SLA 不达标导致超时？ | FIX_REQUIRED |
  | V6 Context | 失败点是否位于关键用户触点？ | 影响优先级判定 |

  诊断流程：
  1. Read 失败截图 + 错误日志
  2. Read 对应子项目的代码文件
  3. 加载 design.json 对应节点的规格定义（如有）
  4. 输出: { primary_cause, classification, diagnosis, evidence, fix_hint }

Step B.5: 跨端数据流追踪
  对每条跨端链，在执行时同步追踪：
  - 写入端：子项目 A 创建/修改实体 → 记录 API 返回数据
  - 消费端：子项目 B 读取/展示该实体 → 验证一致性
  - 断裂检测：
    - 实体在消费端查不到 → DATA_FLOW_BREAK
    - 字段值不一致 → DATA_INCONSISTENCY
    - 关联数据缺失 → RELATION_BREAK

Step B.6: 跨端状态机验证
  提取跨端状态转换（如 A 端 PENDING → B 端 APPROVED → A 端 CONFIRMED），验证：
  - A 端操作后，B 端是否收到状态变更？
  - B 端操作后，A 端状态是否同步？
  - 终态在各端展示是否一致？
  - 死胡同检测：A 端发起操作 → B 端无对应入口 = CROSS_PROJECT_DEAD_END

Step B.7: 4D 跨端覆盖度闭环
  汇总所有 E2E 链结果，按 4D 维度聚合：
  - Data: 跨端数据读写一致？
  - Interface: 跨端 API 契约匹配？
  - Logic: 跨端状态流转完整？
  - UX: 跨端展示连贯？
  每维度 ≥ 85% → E2E_PASS
  任一维度 < 85% → 生成针对性修复任务
```

**KNOWN_FAILURE 传播处理**：
- Path A/D/C 留下的 KNOWN_FAILURE 和 PLATFORM_SPECIFIC_BUG，检查是否参与 E2E 链
- 涉及 KNOWN_FAILURE 模块的链 → 标记为 `AT_RISK`，仍然执行但预期可能失败
- 涉及 PLATFORM_SPECIFIC_BUG 的链 → 在对应平台标记 `AT_RISK`（其他平台正常执行）
- AT_RISK 链失败且根因指向 KNOWN_FAILURE 或 PLATFORM_SPECIFIC_BUG → 不计入 CG-1 轮次，直接标记 KNOWN_FAILURE_PROPAGATED
- AT_RISK 链通过 → 说明 E2E 层面该模块可工作，移除 AT_RISK 标记

**E2E 链收敛（CG-1 同样适用）**：
- 每条链 max 3 轮修复（修脚本 + 修业务代码）
- FIX_REQUIRED / CONTRACT_SYNC → 直接修复后重跑
- ENV_ISSUE → 记录跳过
- KNOWN_FAILURE_PROPAGATED → 记录跳过（根因在上游路径）
- 第 3 轮仍失败 → KNOWN_FAILURE

### 修业务代码的边界

- 只修测试发现的明确 bug（函数返回错误值、缺少校验、状态未更新）
- 不做重构、不改架构、不加新功能
- E2E 链发现的 UI/API bug 同样直接修复
- 每次修改记录到 `testforge-fixes.json`：

```json
{
  "fixes": [
    {
      "id": "FIX-001",
      "type": "BIZ_BUG|UI_BUG|API_BUG|TEST_BUG|SCRIPT_BUG",
      "file": "...",
      "line": 142,
      "description": "...",
      "test_ref": "TG-001",
      "source": "Phase 1 Layer 2 / Phase 3 NS-001"
    }
  ]
}
```

### Step 4.4: 构建验证

每批完成后：
- 前端子项目：运行构建命令验证（CLAUDE.md 若有要求则遵循）
- 后端：编译检查
- E2E 脚本：语法检查 + 如果应用运行则执行
- 确保测试代码和修复代码不破坏构建

→ 输出进度：每批「Batch B{N} [{test_type}] ✓ tests:{a} fixes:{b} known_failure:{c}」

---

## Phase 5：外循环校验

> "走了这么多步，还在正确的路上吗？"

锻造循环完成后，回到起点验证意图保真。

**OL-D1 意图保真**：
- 读 `concept-baseline.json` 的 `mission` + `roles[].jobs`
- 每个核心角色的核心任务，现在有测试守护吗？（包括 E2E 链）
- 有缺口 → 追加到缺口清单

**OL-D2 约束执行**：
- 读 `constraints.json` 的 `enforcement: "hard"`
- 每条硬约束有测试穿透验证吗？（不只是代码存在，而是测试验证了约束生效）
- 有缺口 → 追加

**OL-D3 角色完整性**：
- 读 `role-profiles.json`
- 每个角色的 CRUD 生命周期有测试覆盖吗？
- 每个角色的核心业务流有 E2E 链覆盖吗？

**收敛控制（CG-3）**：
- 外循环追加缺口 ≤ Phase 1-3 总缺口数的 20%
- 超过 → 停止追加，记录为"需要重新规划"
- 外循环最多执行 1 轮（不递归）

**追加项锻造**：汇总 OL-D1/D2/D3 的追加缺口，按 test_type 分路，遵循 A → D → C → B 顺序再跑一轮 Phase 4（仅追加项，CG-1 同样适用）。

**无上游文档时**：Phase 5 整体跳过，输出「Phase 5 ⊘ 无上游概念产物，跳过外循环」

→ 输出进度：「Phase 5 外循环 ✓ 追加缺口:{N} 修复:{M}」

---

## Phase 6：报告输出

### 保存报告文件

- `.allforai/testforge/testforge-analysis.json` — 审计分析数据
- `.allforai/testforge/testforge-fixes.json` — 修复记录
- `.allforai/testforge/testforge-report.md` — 人类可读报告
- `.allforai/testforge/e2e-chains.json` — E2E 链定义（如有生成）

### 报告输出要求（强制执行）

**不要只说"锻造完成"或"报告已保存"。你必须在对话中直接展示以下内容：**

**模式条件化**：标注 `[full/fix]` 的章节在 analyze 模式下省略（analyze 模式只输出审计结果，不输出锻造/修复/E2E 相关章节）。未标注的章节所有模式都输出。

```
## TestForge 质量锻造报告

> 执行时间: {时间}
> 执行模式: {full/analyze/fix}
> 覆盖范围: {N} 个子项目, {M} 个模块

### 审计总览

| 指标 | 数值 |
|------|------|
| 审计缺口总数 | {N}（unit:{u} component:{c} integration:{i} platform_ui:{p} e2e_chain:{e}） |
| 负空间推导场景数 | {N} |
| 基线测试 | 总数:{N} 通过:{pass} 失败:{fail} PRE_EXISTING_FAILURE:{N} |
| 4D 覆盖率 | D:{d}% I:{i}% L:{l}% U:{u}% |

### 锻造总览 [full/fix]

| 指标 | 数值 |
|------|------|
| 补全测试数 | {N} |
| 发现业务 bug 数 | {N} |
| 修复业务 bug 数 | {N} |
| 负空间中发现真实 bug | {M} |
| 锻造轮次 | {N} |
| 最终测试通过率 | {N}% |

### 测试金字塔覆盖 [full/fix]

| 层级 | 锻造前 | 锻造后 | 变化 |
|------|--------|--------|------|
| Unit | {N} tests | {N} tests | +{delta} |
| Component | {N} tests | {N} tests | +{delta} |
| Integration | {N} tests | {N} tests | +{delta} |
| E2E Chain | {N} chains | {N} chains | +{delta} |
| Platform UI | {N} tests × {P} platforms | {N} tests × {P} platforms | +{delta} |

### 覆盖率变化（4D） [full/fix]

| 维度 | 锻造前 | 锻造后 | 变化 |
|------|--------|--------|------|
| Data | {before}% | {after}% | +{delta}% |
| Interface | {before}% | {after}% | +{delta}% |
| Logic | {before}% | {after}% | +{delta}% |
| UX | {before}% | {after}% | +{delta}% |

### E2E 链清单 [full/fix]

| # | 链路名称 | 类型 | 步数 | 涉及子项目 | 状态 |
|---|---------|------|------|-----------|------|
| 1 | {从 business-flow 推导的链名} | 正向/负向 | {N} | {sub-projects} | ✅ PASS / ❌ FAIL / 📋 PLAN_ONLY |
...

### E2E 失败诊断（6V） [full/fix]

| 链路 | 失败步骤 | 主因维度 | 诊断结论 | 分类 | 修复线索 |
|------|---------|---------|---------|------|---------|
| ... | Step N | V1-V6 | ... | FIX_REQUIRED/CONTRACT_SYNC/ENV_ISSUE | ... |
...

### 跨平台 UI 覆盖 [full/fix, 仅跨平台项目]

| 子项目 | 框架 | 目标平台 | 可用平台 | 场景数 | 通过/失败 | PLATFORM_SPECIFIC_BUG |
|--------|------|---------|---------|--------|----------|----------------------|
| ... | Flutter/RN | android,ios,web | web ✓ android ✗ ios ✗ | {N} | {pass}/{fail} | {N} |

### 静态接缝预检修复（Step 4.0 deadhunt + fieldcheck） [full/fix]

| 工具 | 扫描结果 | Critical 修复 | Warning 记录 |
|------|---------|--------------|-------------|
| deadhunt | {dead_links} 死链, {crud_gaps} CRUD 缺口 | 修复 {N} 项 | {M} 项 |
| fieldcheck | {field_issues} 字段不一致 | 修复 {N} 项 | {M} 项 |

### 跨端数据流 & 状态机 [full/fix]

| 检查项 | 状态 |
|--------|------|
| 数据流完整性 | flows:{N} breaks:{M} |
| 状态机完备性 | transitions:{N} failures:{M} |
| 4D 跨端覆盖 | D:{d}% I:{i}% L:{l}% U:{u}% → {E2E_PASS/FAIL} |

### 修复的业务 Bug 清单 [full/fix]

| # | 子项目 | 文件 | Bug 描述 | 发现来源 | 测试引用 |
|---|--------|------|---------|---------|---------|
| 1 | ... | ... | ... | ... | ... |
...

### 横向审计发现

| 类型 | 数量 | 示例 |
|------|------|------|
| MOCK_DRIFT | {N} | ... |
| ERROR_ASYMMETRY | {N} | ... |
| CHAIN_MISSING | {N} | ... |
...

### 外循环校验结果 [full]

| 检查项 | 状态 |
|--------|------|
| 意图保真（mission 覆盖） | ✓ / 缺 {N} 项 |
| 硬约束穿透 | ✓ / 缺 {N} 项 |
| 角色 CRUD 完整性 | ✓ / 缺 {N} 项 |
| 角色 E2E 链完整性 | ✓ / 缺 {N} 项 |

### KNOWN_FAILURE（未解决） [full/fix]

(仍失败的测试，附原因和建议)

### 下一步建议（条件化输出，仅列出实际需要的项）

(若有 KNOWN_FAILURE) 1. 处理 KNOWN_FAILURE 项
(若 Path B 未执行，如 analyze 模式) 2. 运行 /testforge fix 执行锻造（含 E2E 链）
(若有 deadhunt/fieldcheck 修复) 3. 运行 /deadhunt incremental 回归验证
(若无 CI 覆盖率门禁) 4. 考虑配置 CI 覆盖率门禁
(若有 PRE_EXISTING_FAILURE) 5. 修复基线中已存在的 {N} 个失败测试
```

**关键：摘要必须包含具体的 bug 清单和修复详情，不能只给统计数字。用户看完报告就能知道修了什么、还剩什么。**

---

## 决策日志

每次用户通过 AskUserQuestion 确认决策时，追加记录到 `testforge-decisions.json`：

```json
{
  "decisions": [
    {
      "step": "Phase 0",
      "item_id": "scope",
      "decision": "confirmed",
      "value": "all sub-projects",
      "decided_at": "ISO8601"
    }
  ]
}
```

**输出路径**：`.allforai/testforge/testforge-decisions.json`

**resume 模式**：已有 decisions.json 时，已确认步骤自动跳过（展示一行摘要），从第一个无决策记录的步骤继续。

---

## 测试代码规范（跨技术栈通用原则）

生成测试代码时遵循以下原则（不特化任何框架）：

1. **行为驱动命名** — describe/group 按功能分组，不按方法名
2. **Given-When-Then 结构** — 每个测试：准备数据 → 执行操作 → 验证结果
3. **表驱动优先**（多参数场景）— 同一逻辑的多个输入用 table-driven / parameterized
4. **Mock 最小化** — 只 mock 外部依赖（HTTP、DB），不 mock 被测模块的内部方法
5. **一个测试一个断言意图** — 可以有多个 expect/assert，但必须验证同一个行为
6. **错误路径必测** — 每个 catch/error return/throw 至少一个测试
7. **E2E 链数据自给自足** — 每条链在测试内创建所需数据，不依赖外部 seed 或其他链

---

## 铁律

### 1. 测试质量优于数量
不生成 snapshot-only / `expect(true).toBe(true)` 占位测试。每个测试验证一个有意义的行为。

### 2. 遵循项目现有风格
已有 render helper → 用它。已有 factories → 复用并扩展。已有 setup 的 mock 模式 → 保持一致。已有 E2E 目录结构 → 遵循。

### 3. 修 bug 不改架构
只修测试发现的明确 bug，不做重构、不改架构、不加新功能。

### 4. 构建必须通过
运行项目配置的构建命令验证。

### 5. CG-1 收敛
每批 max 3 轮修复，单调递减，第 3 轮仍失败记录为 KNOWN_FAILURE。

### 6. CG-2 负空间边界
负空间总场景 ≤ Phase 1 缺口数的 50%，超过则截断取最高风险项。

### 7. CG-3 外循环边界
外循环追加缺口 ≤ 总缺口数 20%，超过则停止。

### 8. Phase 转换零停顿
Phase 之间不问"继续？"，质量门禁 PASS 或 FAIL（带问题继续）后直接进入下一阶段。

### 9. 负空间标记 [DERIVED]
推导场景与文档场景严格区分，报告中明确标注来源。

### 10. 不破坏已有测试
新测试不得导致已有测试失败。每批完成后全量运行验证。

### 11. 降级不阻断
无上游文档时降级执行（仅代码级审计 + 单元测试锻造），不阻断整个流程。

### 12. 金字塔分层
缺口放到正确的测试层级：纯逻辑用 unit，UI 交互用 component，跨子项目用 e2e_chain。不在 unit 层写 E2E 逻辑，不在 E2E 层测纯函数。

### 13. E2E 链通用性
E2E 链的步骤定义基于上游 business-flows 动态推导，不硬编码任何特定业务域或页面路径。链路结构来自数据，不来自 skill 自身。
