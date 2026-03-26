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
