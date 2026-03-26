## 铁律

> **注意力管理**：本文件是完整参考。实际执行时，每条路径的 Agent 只加载对应的规则组文件（`rules/*.md`），不加载本文件。
>
> | 规则组文件 | 包含规则 | 适用 Agent |
> |-----------|---------|-----------|
> | `rules/base.md` | 1-4, 10, 12, 24 | 所有 |
> | `rules/convergence.md` | 5-9, 11, 13 | Forge agents |
> | `rules/e2e.md` | 14-23 | Path B/C |
> | `rules/data-linkage.md` | 25-26 | Path C + cr-visual |

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

### 14. E2E 选择器先看后写
写 Web UI E2E 测试前，必须先 `browser_navigate` + `browser_snapshot` 看真实 DOM 结构，基于快照中的实际元素编写选择器。**严禁不看页面凭猜测写 CSS 选择器** — 这是 E2E 测试首轮失败的头号原因。UI 框架（Naive UI/Ant Design/Material 等）的实际 DOM 结构与组件 API 不同，必须实地查看。

### 15. 路由模式必须探测
Flutter Web 默认 hash routing，SPA 框架可能用 hash 或 history。E2E 测试生成前必须探测路由模式（Phase 0 Step 2.5），hash 模式下所有 URL 加 `/#` 前缀。不探测路由模式直接写 URL = 必然 404。

### 16. E2E = 模拟用户，不是测试代码

E2E 的本质不是"测试代码逻辑"，而是"模拟一个真实用户从打开浏览器到完成操作的全过程"。
用户做什么，测试做什么，一步不少，一步不绕。

**这意味着 E2E 严禁做以下任何事（哪怕"只是为了方便"）：**

| 严禁 | 为什么 | 用户会怎样 |
|------|--------|-----------|
| cookie/localStorage inject 跳过登录 | 用户必须点登录按钮 | 登录表单提交不了也测不出来 |
| 直接设置 Pinia/Redux store 状态 | 用户不会手动改 store | SSR hydration 不一致测不出来 |
| 绕过 CORS（后端直调代替浏览器调） | 用户的浏览器会发 preflight | CORS 中间件顺序错误测不出来 |
| 用 mock JWT 替代真实认证 token | 用户用 Supabase/Firebase 真实 JWT | JWT 算法不匹配（ES256 vs HS256）测不出来 |
| 跳过 .env 配置直接注入变量 | 用户首次拉代码必须配 .env | 缺 .env 导致的页面白屏/500 测不出来 |
| 用 API 调用替代 UI 操作 | 用户点按钮不是发 curl | 按钮 click handler 没绑定测不出来 |
| 后端开着 dev auth bypass 跑 E2E | 用户的后端没有 dev bypass | 认证链路（JWT 签名/验证/格式）的 bug 全部逃逸 |

**后端环境要求**：E2E 测试时，后端必须以接近生产的配置运行。E2E 测的是"真实用户使用的系统"，不是"开发者调试用的系统"。具体要求：

- 认证 dev bypass 必须关闭（真实 JWT 验证）
- 产品核心功能依赖的外部服务必须真实调用（不能 mock）。如果产品的核心价值是"AI 多模型回帖"，那 LLM 调用不能 mock；如果核心是"支付"，那支付不能 mock
- 判断标准：**如果这个服务 mock 了，用户能感知到产品和真实版本不一样吗？** 能 → 不能 mock。不能 → 可以 mock
- 纯辅助服务（如日志收集、监控上报、分析埋点）可以 mock 或跳过

**唯一允许的"捷径"**：Chain 0 真实登录验证通过后，保存 storageState 供后续链复用（这不是 bypass，是复用已验证的真实登录态）。

### 17. E2E Chain 0 是一切的前提

Chain 0（真实登录冒烟测试）必须在所有业务链之前执行，且不可跳过。它验证的不只是"能不能登录"，而是整条接缝链：

```
Chain 0 验证清单（全部通过才能继续）：
  ✓ .env 存在且含必要变量（认证 URL/Key + API 地址）
  ✓ 前端页面能渲染（非白屏、非 500、非 "Missing config"）
  ✓ 登录表单能交互（输入框可填、按钮可点、click handler 触发）
  ✓ 认证服务可达（Supabase/Firebase 返回 JWT）
  ✓ 后端 API 可达（无 CORS 拦截，JWT 验证通过，返回 200）
  ✓ 登录后成功跳转（不被 SSR middleware 重定向回 login）
  ✓ 跳转后页面可用（仪表盘/首页正常渲染）
  ✓ browser console 无 error 级日志

任何一项失败 → 停止所有后续 E2E 链 → 诊断修复 → 重跑 Chain 0
```

### 18. .env 必须存在且完整

E2E 启动前检查**每个子项目**（不只前端）的 .env：

检查方式：LLM 读取 `.env.example` + 代码中的 config 文件 → 提取所需变量清单 → 比对 `.env` 实际内容。
- 完整 → 继续
- 缺失或不完整 → 按 task-execute Step 0.5 的逻辑自动推导生成
  （从 shell 环境变量、本地服务状态、forge-decisions、project-manifest 推导）
- 生成后重启受影响的 dev server

.env 缺失是"用户一打开就报错"的头号原因。测试全绿但 .env 没配 = 假绿。

### 19. WebGL 不稳定环境降级
WSL2/CI 等无 GPU 环境下，Flutter Web CanvasKit (WebGL) 渲染不稳定。探测到 `WEBGL_UNSTABLE` 时必须：用 `--web-renderer html` 构建，Playwright 加 `retries: 3` + `workers: 1`，不因 WebGL 崩溃标记为业务 bug。

### 20. Mock 数据必须反映真实格式

测试中的 mock/fixture 数据必须和真实服务返回的数据格式一致。常见陷阱：
- **JWT mock**：手动构造 `{"role": "admin"}` 但真实认证服务（Supabase/Firebase/Auth0）的 JWT 用不同字段名或不同值（如 Supabase 的 `role` 是 `"authenticated"` 不是业务角色）
- **API response mock**：前端 mock 了 `{data: [...]}` 但后端实际返回 `{code: 0, data: {items: [...], total: N}}`
- **时间格式**：mock 用 `"2024-01-01"` 但实际返回 ISO8601 `"2024-01-01T00:00:00Z"`

**验证方式**：Chain 0 真实登录成功后，把真实 JWT decode 一次，和 unit test 中 mock JWT 的结构对比。字段名/值不一致 = 测试结果不可信。

### 21. E2E 断言必须穿透数据流

E2E 断言不是"页面不是空白"，而是"我刚写入的数据在另一个端能看到且正确"。

**三级断言强度**：
- ❌ **弱断言**：`expect(page).not.toContain('No Data')` — 只证明页面有东西，可能是别的数据
- ⚠️ **中断言**：`expect(tableRows).toBeGreaterThan(0)` — 证明有数据，但不知道是不是刚写入的
- ✅ **强断言**：`expect(page).toContain(createdEntity.uniqueField)` — 证明"我写入的那条数据在这里"

**E2E 链的每一步验证都必须用强断言。** 写入操作返回的 ID/唯一字段必须在消费端找到。

实践方法：
1. 写入端操作后，保存返回值（如 `const user = await api.post('/register', data)`）
2. 消费端验证时，用返回值中的唯一字段搜索（如 `expect(page).toContain(user.email)`）
3. 不仅验证存在，还验证关键字段值一致（如状态、金额、时间）

### 22. 接缝层是 bug 密度最高的地方

实践数据：单元测试发现 0 个真实 bug，E2E 发现的 bug 中 70% 是接缝问题：
- 前后端字段名不一致
- CORS 中间件注册顺序（必须在认证中间件外层）
- JWT 签名算法前后端不匹配
- SSR framework 客户端状态 vs 服务端状态不同步
- 表单 submit 事件被 UI 框架组件吞掉

**testforge 的优先级应该是：Chain 0 接缝验证 > 业务链 E2E > 集成测试 > 单元测试。**
先确保用户能打开页面、能登录、能看到数据，再去测边界条件和异常路径。

### 23. E2E 外部服务禁止 mock（除非明确无法调用）

E2E 测试的本质是模拟真实用户使用真实系统。外部服务的 mock 会隐藏接缝 bug（SDK 初始化失败、Key 格式错误、API 版本不兼容、回调地址配错）。

**规则**：

| 情况 | 处理 | 理由 |
|------|------|------|
| 有 API Key 且服务可达 | **必须真实调用** | mock 掉 = 假绿 |
| 有 Key 但服务有 sandbox/测试环境 | **用 sandbox** | 支付、短信、快递等有官方测试环境的，用测试环境而非 mock |
| 无 Key 或服务明确无法调用（如第三方快递实际发货） | **标记 `NOT_VERIFIED`** | 诚实说"没测到"，不能 mock 后说"通过了" |
| 纯辅助服务（日志/监控/埋点/分析） | **可以 mock 或跳过** | 不影响用户感知 |

**判断标准**：如果这个服务 mock 了，用户打开 App 能感知到和真实版本不一样吗？
- 能感知 → **不能 mock**（如 AI 回帖内容、支付结果、搜索结果）
- 不能感知 → 可以 mock（如日志上报、后台统计）

**常见不能 mock 的服务**（用 sandbox/测试环境代替）：
- LLM API（产品核心是 AI，mock 后产品等于空壳）
- 支付（用 sandbox：RevenueCat sandbox / Stripe test mode）
- 认证（用本地实例：Supabase local / Firebase emulator）
- 搜索（用真实 API：Brave Search / Google）

**常见可以 mock 的服务**：
- 日志收集（Sentry / Datadog）
- 分析埋点（Mixpanel / Amplitude）
- 监控上报（Prometheus / Grafana）
- 推送通知（可以 mock 发送端，但接收端需真实）

**违反此铁律的后果**：
mock 了 LLM → E2E 说"AI 回帖功能正常"→ 上线后 Key 无效/模型名错误/provider 不可达 → 用户看到空白。
这正是本项目发生过的事。

### 24. 断言源分离（Assertion-Source Separation）

测试断言的"期望值"必须来自上游文档（design/tasks/product-map），不来自实现代码。

**禁止**：读实现代码 → 看到返回 `{status: "pending"}` → 写 `expect(result.status).toBe("pending")`
**正确**：读 tasks.md acceptance_criteria → 看到"创建后状态为 created" → 写 `expect(result.status).toBe("created")`

如果断言来自实现且实现有 bug，测试会通过 → bug 永远不被发现。这是"用答案设计问题"。

无上游文档时（Layer 0 代码级缺口），允许从代码推导断言，但必须标注 `_assertion_source: "code"`。
报告中统计 code-derived vs upstream-derived 断言比例。

### 25. 控件数据完整性必须有测试守护

数据绑定控件（Table/DataGrid/List/ComboBox/Select/Label/Chart 等）不仅要测"能渲染"，还要测"有数据"。

**测试标准**：
- 数据容器：`expect(rows.length).toBeGreaterThanOrEqual(1)` + 强断言行内容
- 选择器：展开后 `expect(options.length).toBeGreaterThanOrEqual(1)` + 验证选项来自真实 API
- 绑定显示：`expect(text).not.toBe("")` + `expect(text).not.toMatch(/undefined|null|NaN/)`
- 可视化：`expect(dataPoints.length).toBeGreaterThanOrEqual(1)`

**禁止**：
- ❌ 用前端硬编码假数据让测试通过（如写死 `options: ["A", "B"]`）
- ❌ 仅测"组件渲染不报错"而不测"组件显示了真实数据"
- ❌ mock API 返回假数据让控件"看起来有数据"但真实 API 其实没对接

**空控件是真 bug**：源 App 有数据的控件 → 目标 App 同一控件为空 → 这不是"UI 问题"，是数据链路断裂（API 未调用/字段映射错/后端查询空），必须沿数据链路溯源修复。

### 26. 控件联动必须显式测试因果关系

联动测试不是"流程走通就行"— 必须**显式验证因果**：操作 A → B 正确响应。

**测试结构**：
```
1. 设置初始状态（记录 B 的初始值/状态）
2. 执行触发操作（操作 A）
3. 等待响应（联动可能涉及 API 调用）
4. 断言 B 的变化（不只是"B 有值"，而是"B 因为 A 而正确变化"）
5. 反向验证：改回 A → B 恢复/重置
```

**禁止**：
- ❌ 只测最终状态（填完整个表单后截图）— 看不出中间哪步联动断了
- ❌ 只测正向（选了省份 → 有城市）不测反向（换省份 → 城市更新）
- ❌ 用 E2E 流程的"下游步骤没报错"当作"联动正常"— 间接覆盖不够，根因不明确
- ❌ 跳过 disabled/enabled 状态检查 — 这是最常见的联动漏检类型

**联动断裂是高优先级 bug**：联动是用户对"操作→反馈"的核心心智模型，联动断裂 = 用户困惑 = 产品质量硬伤。
