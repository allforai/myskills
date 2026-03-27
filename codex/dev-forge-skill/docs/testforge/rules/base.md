# 铁律 — 基础组（所有 Agent 必须遵守）

### 1. 测试质量优于数量
不生成 snapshot-only / `expect(true).toBe(true)` 占位测试。每个测试验证一个有意义的行为。

### 2. 遵循项目现有风格
已有 render helper → 用它。已有 factories → 复用并扩展。已有 setup 的 mock 模式 → 保持一致。已有 E2E 目录结构 → 遵循。

### 3. 修 bug 不改架构
只修测试发现的明确 bug，不做重构、不改架构、不加新功能。

### 4. 构建必须通过
运行项目配置的构建命令验证。

### 10. 不破坏已有测试
新测试不得导致已有测试失败。每批完成后全量运行验证。

### 12. 金字塔分层
缺口放到正确的测试层级：纯逻辑用 unit，UI 交互用 component，跨子项目用 e2e_chain。不在 unit 层写 E2E 逻辑，不在 E2E 层测纯函数。

### 29. 禁止 Mock API 响应 — 真实后端或不测（No Mock, Real Backend or No Test）

**所有前端测试（unit / component / integration / E2E）必须连接真实后端。没有真实后端 = 标记 NOT_TESTED，不生成 mock 测试。**

Mock 测试是假绿 — LLM 按 TypeScript 类型定义编造 mock 数据，但真实 API 的字段名、类型、是否可空全部可能不一致。Mock 测试只证明"前端代码在想象数据下不崩溃"，发现不了任何真实 bug。

**执行规则**：

| 情况 | 处理 |
|------|------|
| 后端可启动（本地 dev） | 前端测试必须连真实后端 |
| 后端不可启动 | 前端测试标记 `NOT_TESTED`，不生成 mock 测试 |
| 后端 unit test（service 层） | 允许 mock repository 接口（内部实现细节，不是接缝） |
| 后端 unit test（controller 层） | 允许 mock service 接口 |

**禁止的做法**：
- ❌ `mockResolvedValue({id: "1", name: "test"})` — 手写 mock 数据
- ❌ `vi.mock("@/lib/api")` — mock 整个 API 模块
- ❌ `msw` / `nock` / `axios-mock-adapter` 拦截 HTTP — 让请求真的发出去
- ❌ 前端 store 预注入初始状态 — 让 store 从真实 API 加载

**前端测试的正确做法**：
1. Phase 0 确保后端可启动（dev server / docker-compose）
2. Seed 测试数据（seed 脚本或 migration）
3. 前端测试直接连真实后端 API
4. 断言验证真实 API 返回的数据在 UI 上正确显示

**为什么这条铁律存在**：
实践中反复出现的模式 — 数百个 mock 测试全绿，但 E2E 连真实后端一跑，多个页面 JS 崩溃（数值方法对 undefined 调用、数组方法对 object 调用、日期解析失败、字段名不匹配）。所有 bug 都在前后端接缝层，mock 测试一个都发现不了，因为 mock 数据本身就是按前端类型定义"理想化"编造的。没有真实后端的前端测试不如不测。

### 24. 断言源分离（Assertion-Source Separation）
测试断言的"期望值"必须来自上游文档（design/tasks/product-map），不来自实现代码。无上游文档时允许从代码推导，但标注 `_assertion_source: "code"`。

### 28. 反惰性断言 — 验证对错而非有无（Anti-Lazy Assertion）

LLM 生成测试时天然倾向"存在性断言"（最容易生成），但存在性断言几乎不能发现 bug。

**断言深度分级**：

```
Level 0 — 存在性（禁止用于业务逻辑）:
  ❌ expect(element).toBeVisible()
  ❌ expect(result).toBeDefined()
  ❌ expect(response).toBeTruthy()
  仅允许用于：纯 UI 渲染冒烟测试（组件不崩溃）

Level 1 — 量化性（仅允许辅助断言，不能是唯一断言）:
  ⚠️ expect(items.length).toBeGreaterThan(0)
  ⚠️ expect(response.status).toBe(200)
  可以作为前置检查，但后面必须跟 Level 2+ 断言

Level 2 — 结构性（最低合格线）:
  ✅ expect(items[0]).toHaveProperty('name')
  ✅ expect(response.body).toHaveProperty('orderId')
  验证了数据结构，但没验证值的正确性

Level 3 — 值正确性（目标水平）:
  ✅ expect(items[0].name).toBe('预期用户名')
  ✅ expect(order.status).toBe('approved')
  ✅ expect(total).toBe(quantity * price)
  期望值来自上游文档（Rule 24）或已知业务规则
```

**强制自检协议**：

每生成一个测试后，LLM 必须对每个 expect/assert 语句标注深度等级，并执行：

```
1. 标注：给每个断言标注 Level 0/1/2/3
2. 检查：
   - 业务逻辑测试（unit/integration）：Level 3 断言占比 ≥ 60%，否则重写
   - E2E/platform_ui 测试：Level 3 断言占比 ≥ 40%，Level 2+ 占比 ≥ 80%
   - 组件渲染测试（component）：Level 2+ 占比 ≥ 50%
3. 拒绝：
   - 一个测试全是 Level 0/1 断言 → 直接拒绝，重新生成
   - 关键业务路径（CRUD、支付、审批）的测试没有 Level 3 → 拒绝
4. 标记：通过的测试标注 assertion_depth_score（0-3 的加权平均）
```

**常见惰性模式 → 正确写法**：

| 惰性写法（拒绝） | 正确写法（接受） | 区别 |
|---|---|---|
| `expect(page).not.toContain('Error')` | `expect(page).toContain(createdOrder.id)` | 验证"没错" vs 验证"对了" |
| `expect(rows.length).toBeGreaterThan(0)` | `expect(rows[0].name).toBe(expectedName)` | 验证"有" vs 验证"对" |
| `expect(response.status).toBe(200)` | `expect(response.body.total).toBe(128.50)` | 验证"成功" vs 验证"结果对" |
| `expect(component).toMatchSnapshot()` | `expect(screen.getByText('John')).toBeVisible()` | 验证"长这样" vs 验证"内容对" |
| `expect(select.options.length).toBe(3)` | `expect(select.options).toContain('广东省')` | 验证"有3个" vs 验证"包含对的" |
