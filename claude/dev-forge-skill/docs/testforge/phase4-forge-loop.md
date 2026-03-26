# Phase 4：锻造循环（Forge-Fix Loop）

> "补测试 → 跑测试 → 修 bug → 重跑 → 收敛"

## Step 4.0: 静态接缝预检（deadhunt + fieldcheck）— 不可跳过

> **⚠️ 铁律：Step 4.0 是 Phase 4 的第一步，不可跳过、不可推迟、不可"先写测试再补"。**
> **违反此步骤 = 后续所有测试结果不可信。**
>
> 原因：接缝层问题（API URL 不匹配、字段名不一致、分页参数格式不兼容）是测试"假绿"的头号原因。
> 单元测试 mock 掉了接缝所以测不出，E2E 测试用弱断言也测不出，
> 但 deadhunt/fieldcheck 的纯静态分析能在秒级检出这些问题。
> 先修接缝再写测试，否则测试建立在错误的连接上，全是假绿。
>
> **Step 4.0 的产出是后续所有测试的前提。接缝不对，测试全是假绿。**

若 `experience_priority.mode = consumer | mixed`，**Step 4 后续生成/修复测试时** 不能只验证"功能做了"，还必须优先覆盖用户端成熟度节点：

- 首页主线可发现
- 核心状态可感知
- 完成后知道下一步
- 持续关系链路不空壳

> 这不是 Step 4.0 静态接缝预检本身的职责。Step 4.0 只负责发现接缝层假绿；上述节点用于指导 Step 4 后续测试锻造优先级。

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

## Step 4.0.5: Chain 0 冒烟（运行时接缝验证）— 不可跳过

> **⚠️ 铁律：Step 4.0.5 在 Step 4.0（静态）之后、所有测试生成之前执行。**
> 静态分析能发现字段名/路径不匹配，但发现不了：JWT 算法不一致、CORS 配置错误、响应结构层级不一致、SSR hydration 问题。
> 唯一能 100% 发现所有接缝 bug 的方法：**真的跑起来，真的发请求，真的看结果。**
>
> **Step 4.0（静态）+ Step 4.0.5（运行时）= 接缝层 100% 覆盖。两步缺一不可。**

**前置**：启动所有子项目应用（后端 + 前端）。不可达 → 尝试启动 → 仍不可达 → 标记 `NOT_TESTED`（不是 PASS）。

**执行内容**（从 Path B Chain 0 提取，但在所有测试生成之前执行）：

```
1. 应用可达性检查
   逐子项目 curl 端口 → 全部可达才继续

2. 真实登录冒烟（每个有登录页的子项目）
   Web 端：Playwright browser_navigate → 登录页 → 填表单 → 点登录 → 验证跳转 → 验证首页有数据
   Mobile 端：设备可用时执行，不可用标记 NOT_TESTED

3. 登录后接缝验证
   a. CORS：前端调后端 API → 无 CORS 错误
   b. 认证链路：JWT token 前端→后端验证通过 → 返回 200
   c. 首页数据：登录后页面显示真实数据（强断言，不只是"不是空白"）
   d. Console 零 error：browser console 无 error 级日志

4. 失败处理
   任一步失败 → 立即诊断修复（不消耗 CG-1 轮次）
   修复后重跑 → 全通过后才进入 Step 4.1
   Chain 0 不通过 = 后续所有测试结果不可信 = 不允许跳过
```

**与 Path B Chain 0 的关系**：
- Step 4.0.5 是 Chain 0 的**前置执行**（在测试生成之前跑，发现致命接缝问题）
- Path B 是 Chain 0 + 完整业务链（在所有单元/集成测试之后跑）
- Step 4.0.5 通过后，Path B 可以复用 Chain 0 的登录态，不需要重新跑

**为什么不等到 Path B 才跑 Chain 0**：
- Path B 排在 Path A/D/C 之后，可能要几个小时才执行到
- 如果接缝断裂（登录不了、首页白屏），这几个小时写的所有测试都基于错误的假设
- 5 分钟的 Chain 0 冒烟能提前发现 90% 的致命 bug，省下后续几小时的无效工作

---

## Step 4.1: 基础设施补全 + ENV_ISSUE 子项目处理（仅 full/fix 模式）

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

## Step 4.2: 批次规划 + 分路

将 Phase 1-3 的所有缺口按 `test_type` 分为 4 条锻造路径，每条路径内按优先级排序：

```
severity CRITICAL > HIGH > MEDIUM
dimension Logic > Interface > Data > UX（业务规则最先）
负空间 [DERIVED] 排在同 severity 的文档缺口之后
```

**铁律按需加载**（每条路径只加载它需要的规则组，降低注意力负荷）：

| 路径 | 加载的规则文件 |
|------|--------------|
| Path A | `rules/base.md` + `rules/convergence.md` |
| Path D | `rules/base.md` + `rules/convergence.md` |
| Path C | `rules/base.md` + `rules/convergence.md` + `rules/e2e.md` + `rules/data-linkage.md` |
| Path B | `rules/base.md` + `rules/convergence.md` + `rules/e2e.md` |

> 路径文件位于 `${CLAUDE_PLUGIN_ROOT}/docs/testforge/rules/`。每个路径 Agent 启动时只 Read 自己需要的规则文件，不加载全量 iron-rules.md。

```
路径 A: Unit + Component（单元/组件测试）
  **仅对有业务逻辑的代码生成单元测试**（Understand-then-Scan：LLM 读源文件判断是否有逻辑）：
  ✓ 补测试：状态机、业务规则、权限判断、金额计算、cron job、验证逻辑、数据转换
  ✗ 不补测试：纯 CRUD wrapper、API client 透传函数、纯 re-export、常量定义
  判定方式：LLM 读源代码，理解函数做了什么，判断是否包含分支/计算/状态转换。不靠文件名或目录推断。
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

**执行顺序**：Step 4.0(静态接缝预检) → **Step 4.0.5(Chain 0 冒烟 — 跑起来验证)** → Step 4.1(基础设施) → Step 4.2(批次规划) → Step 4.3 路径 A(仅逻辑层) → D → C → B(完整 E2E 链，复用 Chain 0 登录态) → Step 4.4(构建验证)

**跨子项目并行**：同一路径内，不同子项目互相独立，使用 Agent tool 并行执行。例如 Path A 中 website 和 admin 的单元测试可同时锻造。Path B 除外（E2E 链天然跨子项目，按链串行）。

## Step 4.3: 逐批锻造（内循环）

### 断言源分离协议（Assertion-Source Separation）

> **⚠️ 这是防止"用答案设计问题"的核心机制。**
>
> 测试的断言（expect/assert）来源必须与实现代码严格分离：
> - **断言的"期望值"** → 只能来自上游文档（design.md, tasks.md, product-map）
> - **测试的"怎么调"** → 可以读实现代码（知道函数签名、参数类型）
>
> 禁止从实现代码中读取返回值结构后直接写 `expect(result).toEqual(实现返回的东西)`。
> 必须从上游文档中找到"这个函数应该返回什么"再写断言。

**每个测试的生成顺序必须是"断言先行"**：

```
Step 1: 确定断言（从上游文档拉取）
  a. 读缺口的 upstream_ref（指向 design/tasks/product-map 的具体条目）
  b. 从 upstream_ref 提取业务期望：
     - tasks.md 的 _Acceptance_ → 验收条件 = 断言
     - tasks.md 的 rules → 业务规则 = 断言
     - tasks.md 的 exceptions → 异常路径 = 断言
     - design.json 的 API endpoint → 响应码 + 字段 = 断言
     - constraints 的 enforcement: hard → 约束条件 = 断言
  c. 将业务期望转为测试断言伪代码（此时不看实现代码）
     示例：「规则: 订单金额 > 10000 需要审批」
     → expect(orderService.create({amount: 15000})).toRequireApproval()

Step 2: 编写测试代码（从实现代码拉取）
  a. 读源代码 → 理解函数签名、参数类型、依赖注入方式
  b. 读已有测试 → 复用 helpers/factories/命名风格
  c. 用 Step 1 的断言伪代码 + Step 2a 的函数签名 → 生成完整测试

Step 3: 验证断言不是同义反复
  生成后自检：
  - 断言中的期望值是否能追溯到 upstream_ref？（可追溯 → ✓）
  - 如果断言只是 `expect(result).toEqual(函数实际返回值)` 且无 upstream_ref → ⚠️ 同义反复嫌疑
  - 无 upstream_ref 的缺口（Layer 0 代码级缺口）→ 允许从代码推导断言，但必须标注 `_assertion_source: "code"`
```

**无上游文档时的降级**：
- Layer 0 缺口（无 design/tasks）→ 允许从代码逻辑推导断言，标注 `_assertion_source: "code"`
- 报告中统计 `code-derived` vs `upstream-derived` 断言比例 — 比例过高（>80%）→ 建议用户补充上游文档

### 路径 A/D: 单元 / 组件 / 集成测试

对每批：

```
1. 生成测试代码
   对每个缺口：
     a. 断言先行：读 upstream_ref → 提取业务期望 → 写断言伪代码
     b. Read 源代码 → 理解函数签名和依赖
     c. Read 已有测试（避免重复）
     d. Read 已有 helpers/factories（复用）
     e. 合成完整测试代码（断言来自 Step a，调用方式来自 Step b-d）
     f. 跑单个测试文件验证语法通过

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

   ⚠️ TEST_BUG 分类时追问：断言错误是因为"断言来自实现代码"还是"实现不符合业务要求"？
   - 断言来自实现 → 断言本身是同义反复，需要从 upstream_ref 重新推导
   - 实现不符合要求 → 保持断言，修实现

4. 修复 → 重跑

5. 收敛条件（CG-1）：
   - max 3 轮修复
   - 每轮失败数必须 ≤ 上一轮（单调递减）
   - 违反单调递减（失败数增加）→ 回滚该轮修改，标记剩余为 KNOWN_FAILURE
   - 第 3 轮仍失败 → 记录为 KNOWN_FAILURE，继续下一批
```

### 路径 C: 跨平台 UI 自动化测试

> 同一套业务场景，在每个可用平台各跑一遍 UI 自动化测试。

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/testforge/path-c-platform-ui.md（如存在）
> 如不存在，按以下协议执行：

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
   | macOS | 原生桌面 | `flutter test integration_test/ -d macos` | _test.dart |
   | Linux | 原生桌面 | `flutter test integration_test/ -d linux` | _test.dart |
   | Android/iOS 降级 | 桌面原生 + 手机分辨率 | `flutter test integration_test/ -d {当前OS桌面设备}` | _test.dart（标记 DESKTOP_SUBSTITUTE） |

3.5 **测试深度要求（Path C 继承 Path B 的原则）**

   > Path C 和 Path B 的区别只是**测试工具不同**（Playwright vs Flutter integration_test vs Maestro），
   > **测试深度要求相同**。不能因为换了工具就降低标准。

   Platform UI 测试必须满足以下深度（与 Path B E2E Chain 一致）：

   - **真实认证**：测试必须走真实登录流程（输入凭证→提交→验证跳转），不能跳过认证直接进入页面
   - **数据加载验证**：登录后的页面必须验证**真实 API 数据出现在界面上**（强断言），不能只验证空壳 UI 渲染
   - **核心业务流走通**：至少覆盖一条完整业务链（如：登录→看帖子列表→进入帖子→看到楼层回帖→发帖→验证新帖出现）
   - **三层级**：进程（app 不崩溃）+ 连接（API 数据到达）+ 数据（用户看到正确内容）

   如果认证服务（如 Supabase）在测试环境不可用，必须通过后端 API 登录获取 token 后注入，
   **不能跳过登录说"login will likely fail"然后只测空壳**。

3.6 **控件数据完整性验证（DataBinding 维度缺口）**

   > 此步骤专门处理 Phase 1 标记为 `DATABINDING_GAP` 的缺口。
   > 与 Step 3.5 的区别：3.5 验证"页面级数据加载"，3.6 验证"逐控件数据填充"。

   对每个 DATABINDING_GAP 缺口，生成/补充 platform_ui 测试：

   ```
   数据容器（Table/DataGrid/List/Tree）：
     - 导航到目标页面 → 等待 API 响应完成
     - 断言：行数 ≥ 1（强断言：行内容包含预期字段值）
     - 断言：列标题与 design.md 定义一致
     - 空数据状态测试：mock 空响应 → 验证显示空状态提示（不是白屏/报错）

   选择器（ComboBox/Select/Dropdown）：
     - 导航到目标页面 → 点击/展开选择器
     - 断言：选项列表长度 ≥ 1
     - 断言：选项内容来自真实 API（非硬编码）
     - 验证方式：检查选项内容与 API 响应数据一致

   显示绑定（Label/Badge/Counter 绑定变量的）：
     - 导航到目标页面 → 等待数据加载
     - 断言：绑定值 ≠ ""、≠ "undefined"、≠ "null"、≠ "NaN"
     - 强断言：绑定值与 API 响应中的对应字段一致

   可视化（Chart/Graph/ProgressBar）：
     - 导航到目标页面 → 等待渲染完成
     - 断言：图表 canvas/SVG 非空（有数据点/路径）
     - 断言：坐标轴有刻度值（非全零/空）
   ```

   **禁止硬编码假数据修复**：如果测试发现控件为空，修复方式必须是修数据链路（API 调用/后端逻辑/数据库），
   不得在前端代码中硬编码 `["选项1", "选项2"]` 或 `[{name: "测试数据"}]` 来让测试通过。
   硬编码假数据 = BIZ_BUG 而非 TEST_BUG。

3.7 **控件联动测试（Linkage 缺口）**

   > 此步骤专门处理 Phase 1 标记为 `LINKAGE_GAP` 的缺口。
   > 与 Step 3.6 的区别：3.6 验证"控件有数据"，3.7 验证"操作 A 后控件 B 正确响应"。

   对每个 LINKAGE_GAP 缺口，生成 component 或 platform_ui 测试：

   ```
   级联选择（select A → select B 选项更新）：
     - 渲染包含联动控件的组件/页面
     - 选择 A 的某个值 → 等待响应
     - 断言：B 的选项列表更新（options.length >= 1）
     - 断言：B 的选项内容与 A 的值关联（非全量静态选项）
     - 选择 A 的另一个值 → 断言 B 的选项再次变化
     - 选择 A 后：断言下游控件（如 C）被重置

   条件显隐（checkbox/radio → 控件出现/消失）：
     - 初始状态：断言目标控件不可见
     - 勾选/选中触发条件 → 断言目标控件可见
     - 取消勾选 → 断言目标控件再次不可见
     - 双向验证：出现和消失都必须测

   条件启禁（表单状态 → 按钮 disabled/enabled）：
     - 初始空表单：断言提交按钮 disabled
     - 填写必填字段 → 断言按钮 enabled
     - 清空某必填字段 → 断言按钮回到 disabled
     - 检查 DOM 属性（disabled/aria-disabled），不只看视觉样式

   自动计算（input × input → computed label）：
     - 输入值 A=10, B=5 → 断言 C=50（精确值，不只是"非空"）
     - 修改 A=20 → 断言 C=100（验证响应式更新）
     - 边界：A=0 → 断言 C=0（不是 NaN/undefined）
     - 断言公式来源：从上游文档或源码注释中提取计算规则

   联动筛选（tab/filter → 列表变化）：
     - 全部 Tab 下：记录行数 N
     - 切换到筛选 Tab → 断言行数 < N（不是全量）
     - 切换回全部 → 断言行数恢复为 N

   主从联动（list click → detail panel）：
     - 点击第 1 行 → 断言详情面板显示第 1 行的唯一标识字段
     - 点击第 2 行 → 断言详情面板更新为第 2 行数据（不是还停留在第 1 行）
   ```

   **联动测试的失败分类**：
   - 事件绑定丢失（onClick/onChange 未绑定）→ BIZ_BUG
   - 状态传递断裂（dispatch/emit 丢失）→ BIZ_BUG
   - API 联动未实现（onChange 未调 API）→ BIZ_BUG
   - 计算公式错误（结果不对）→ BIZ_BUG
   - 全部归为 BIZ_BUG（不是 TEST_BUG），因为联动是核心交互行为。

4. 跨平台差异记录
   同一场景在 A 平台通过但 B 平台失败 → 标记为 PLATFORM_SPECIFIC_BUG
   场景示例：Web 上按钮可点击但 Android 上被键盘遮挡

5. 不可用平台处理
   - 生成测试脚本但标记为 PLAN_ONLY
   - 报告中列出「已生成脚本，待 {platform} 环境就绪后执行」

6. 收敛（CG-1 同样适用，按平台独立计数）
```

### 路径 B: E2E 链锻造

> 详见 testforge.md 中 路径 B 部分（保留在主文件中或独立拆出）

## Step 4.4: 构建验证

所有路径锻造完成后，运行项目配置的构建命令验证：
- npm run build / go build / flutter build 等
- 构建失败 → 分析原因，修复后重试
- 确保测试代码不引入编译错误

## Step 4.5: 任务清单验收（防遗漏）

> 所有路径完成后，回头检查 Phase 1 的 control_inventory — 有没有遗漏。

```
1. 读 testforge-analysis.json → control_inventory
2. 统计 has_test 状态：
   - has_test = true → 已覆盖
   - has_test = false → 遗漏（Path C agent 没处理到）
3. 遗漏项 > 0 → 为每个遗漏项补生成测试（不消耗 CG-1 轮次）
4. 补生成后重跑测试 → 更新 has_test
5. 输出进度：「Step 4.5 验收 ✓ 控件覆盖 {covered}/{total}，联动覆盖 {covered}/{total}，补测试 {N} 个」
```

**为什么需要这一步**：Path C agent 可能因为注意力不足跳过了某些控件。
任务清单验收是最后的安全网 — 确保 Phase 1 枚举的每个控件和联动都有测试守护。
