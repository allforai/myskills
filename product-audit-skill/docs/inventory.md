# Step 1: 功能清单构建 (Feature Inventory)

> 两条平行线 + 对齐匹配：从需求文档提取"计划功能"，从代码提取"已实现功能"，然后匹配对齐。

---

## 1. 计划功能提取 (Planned Feature Extraction)

从需求来源（PRD、README、OpenAPI spec 等）中提取计划功能列表。

### 提取字段

| 字段 | 说明 | 必填 |
|------|------|------|
| `id` | 自动生成，格式 `PF-001`, `PF-002`, ... | Yes |
| `name` | 功能名称 | Yes |
| `source` | 来源文件:行号，如 `docs/prd.md:42` | **Yes (铁律 #1: 必须有来源定位)** |
| `description` | 简要描述，一句话说清楚这个功能做什么 | Yes |
| `category` | 功能分类（如能检测到）：用户管理、订单、支付、权限... | Optional |

### 提取规则

**粒度控制：**
- 每个独立的 user-facing capability = 一个功能条目
- 子功能（如"用户管理"下的"用户登录"）单独列条目，但标注 parent
- 不要拆得太细 -- 一个功能应该对应一个完整的 user story
- 判断标准：用户能否独立使用这个功能？能 = 独立条目；不能 = 合并到父功能

**按来源类型的提取策略：**

#### 从 PRD 提取
- 扫描编号列表（1. 2. 3. ...）
- 扫描功能标题（## 功能一：xxx）
- 扫描 user story 格式（"作为...我想要...以便..."）
- 扫描表格中的功能列

#### 从 README Features 提取
- Features / 功能特性 section 下的每个 bullet point = 一个功能
- 注意区分"功能描述"和"技术特性"（如"使用 React" 不是功能）

#### 从 OpenAPI / Swagger 提取
- 每个 resource group (tag) = 一个功能模块
- 每个 endpoint = 一个子功能
- 用 `summary` 字段作为功能名称

```
示例：
PF-001 | 用户注册     | docs/prd.md:15  | 新用户通过邮箱注册账号 | 用户管理
PF-002 | 用户登录     | docs/prd.md:23  | 已注册用户通过邮箱密码登录 | 用户管理
PF-003 | 订单创建     | docs/prd.md:45  | 用户选择商品后创建订单 | 订单
PF-004 | 微信支付     | docs/prd.md:67  | 用户通过微信完成订单支付 | 支付
```

---

## 2. 已实现功能提取 (Implemented Feature Extraction)

从代码中通过 4 个维度扫描，提取已实现的功能列表。

### 提取字段

| 字段 | 说明 |
|------|------|
| `id` | 自动生成，格式 `IF-001`, `IF-002`, ... |
| `name` | 功能名称（从路由/组件/测试名推导） |
| `evidence` | 实现证据：`{ route, component, api_endpoint, test_file }` |
| `completeness` | 实现完整度评估：`full` / `partial` / `skeleton` |

### 2a. 路由分析 (Route Analysis)

扫描路由定义文件，每个带页面组件的路由 = 一个已实现功能条目。

**扫描目标：**
- React: `react-router` 配置，`<Route path="..." component={...} />`
- Vue: `vue-router` 配置，`{ path: '...', component: ... }`
- Next.js: `app/` 或 `pages/` 目录结构
- Express/Koa: `router.get()`, `router.post()` 等

**提取内容：**
- Route path（如 `/users`, `/orders/:id`）
- 关联的页面组件文件
- Route guards / middleware（如 `requireAuth`, `adminOnly`）
- 嵌套关系（parent route → child route）

```
示例：
/login          → LoginPage.tsx        → 无 guard
/dashboard      → DashboardPage.tsx    → requireAuth
/admin/users    → AdminUsersPage.tsx   → requireAuth, adminOnly
```

### 2b. 页面组件分析 (Page Component Analysis)

扫描页面级组件，分析每个页面的实际功能。

**识别方式：**
- 被路由引用的组件 = 页面组件
- `pages/` 或 `views/` 目录下的组件 = 页面组件
- 含有 form / table / detail view 的组件 → 推断功能类型

**功能类型推断：**
- 含 `<form>` + submit → 数据创建/编辑功能
- 含 `<table>` / list rendering → 数据列表/查询功能
- 含详情展示 → 数据查看功能
- 含 delete 操作 → 数据删除功能

### 2c. API 端点分析 (API Endpoint Analysis)

扫描后端路由/控制器，列出所有端点。

**提取内容：**
- HTTP method + path（如 `POST /api/users`）
- 对应的 controller / handler 文件
- 请求参数和响应结构（如果容易获取）
- 认证要求

```
示例：
POST   /api/auth/register   → AuthController.register
POST   /api/auth/login      → AuthController.login
GET    /api/orders           → OrderController.list
POST   /api/orders           → OrderController.create
POST   /api/payments/wechat  → PaymentController.wechatPay
```

### 2d. 测试套件分析 (Test Suite Analysis)

扫描测试文件，提取测试覆盖的功能。

**扫描目标：**
- `describe()` block → 功能模块
- `it()` / `test()` block → 具体功能点
- E2E 测试文件 → 完整用户流程

**提取内容：**
- 测试文件路径
- describe 描述文本
- 测试用例数量
- 对应的被测模块

```
示例：
tests/auth.test.ts
  describe("用户注册") → 3 test cases
  describe("用户登录") → 5 test cases
tests/order.test.ts
  describe("订单创建") → 4 test cases
```

### 完整度评估标准

| 完整度 | 判断依据 |
|--------|----------|
| `full` | 有路由 + 有页面组件 + 有 API + 有测试 |
| `partial` | 缺少一两个维度（最常见：有实现没测试） |
| `skeleton` | 只有路由或空组件，实际逻辑未实现 |

---

## 3. 匹配对齐 (Alignment Matching)

将计划功能和已实现功能进行匹配，建立对应关系。

### 匹配信号

用以下 3 种信号进行匹配，按可靠度从高到低：

#### Signal 1: 名称相似度 (Name Similarity)
- 对计划功能名和已实现功能名做 fuzzy matching
- 中文直接比较；英文做 token-level 比较
- 示例："用户注册" ↔ "UserRegistration" → match

#### Signal 2: 路由关联 (Route Association)
- PRD 中提到 "/users" → 匹配到路由 `/users` 的已实现功能
- PRD 中提到"用户列表页" → 匹配到 `/users` 或 `UserListPage`
- 示例：PRD 写"订单详情页" + 路由有 `/orders/:id` → match

#### Signal 3: 关键词重叠 (Keyword Overlap)
- 提取领域关键词：订单(order)、支付(payment)、用户(user)、权限(permission)...
- 计划功能描述和已实现功能证据中的关键词交集
- 示例：计划有"微信支付"，代码有 `wechatPay` controller → match

### 置信度分级

| 置信度 | 条件 | 处理方式 |
|--------|------|----------|
| `high` | >= 2 个信号匹配 | 自动匹配，无需确认 |
| `medium` | 恰好 1 个信号匹配 | 自动匹配，但标记 `review_suggested` |
| `low` | 仅 fuzzy name match，相似度不高 | 标记 `needs_confirmation`，等用户确认 |
| `none` | 无匹配信号 | 未匹配（MISSING 或 UNPLANNED） |

### 未匹配处理

- **计划中有、实现中没有** → `unmatched_planned`（可能是 MISSING，也可能是故意推迟）
- **实现中有、计划中没有** → `unmatched_implemented`（可能是 UNPLANNED，也可能是文档遗漏）

---

## 4. 用户确认点 (User Confirmation)

匹配完成后，以表格形式展示清单，向用户确认：

### 确认问题

**Q1: 功能清单是否准确？有遗漏或误判吗？**
> 展示完整的计划功能列表和已实现功能列表，让用户检查是否有遗漏或错误归类。

**Q2: 以下低置信度匹配是否正确？**
> 展示所有 `medium` 和 `low` 置信度的匹配，让用户逐条确认或修正。

**Q3: 有哪些功能是故意推迟实现的？**
> 对于 `unmatched_planned` 中的条目，询问用户哪些是有意推迟的。
> 用户确认后，这些条目在 Step 2 中标记为 `DEFERRED` 而非 `MISSING`。

### 确认表格示例

```
匹配结果：
┌────────┬──────────┬──────────┬────────────┬─────────┐
│ 计划ID │ 计划功能  │ 实现ID    │ 实现功能    │ 置信度   │
├────────┼──────────┼──────────┼────────────┼─────────┤
│ PF-001 │ 用户注册  │ IF-001   │ Registration│ high    │
│ PF-002 │ 用户登录  │ IF-002   │ Login      │ high    │
│ PF-003 │ 订单创建  │ IF-005   │ CreateOrder│ medium  │ ← review
│ PF-004 │ 微信支付  │ -        │ -          │ none    │ ← MISSING?
│ -      │ -        │ IF-008   │ AdminPanel │ none    │ ← UNPLANNED?
└────────┴──────────┴──────────┴────────────┴─────────┘

请确认：
1. PF-003 ↔ IF-005 匹配是否正确？
2. PF-004 (微信支付) 是尚未实现还是故意推迟？
3. IF-008 (AdminPanel) 是否在计划中但文档未提及？
```

---

## 5. 输出格式 (Output Schema)

Step 1 的最终输出为 `feature-inventory.json`：

```json
{
  "meta": {
    "generated_at": "2026-02-24T10:00:00Z",
    "project": "project-name",
    "step": 1
  },
  "planned_features": [
    {
      "id": "PF-001",
      "name": "用户注册",
      "source": "docs/prd.md:42",
      "description": "新用户通过邮箱注册账号",
      "category": "用户管理"
    }
  ],
  "implemented_features": [
    {
      "id": "IF-001",
      "name": "User Registration",
      "evidence": {
        "route": "/register → RegisterPage.tsx",
        "component": "src/pages/RegisterPage.tsx",
        "api": "POST /api/auth/register → AuthController",
        "test": "tests/auth.test.ts:describe('注册')"
      },
      "completeness": "full"
    }
  ],
  "matches": [
    {
      "planned_id": "PF-001",
      "implemented_id": "IF-001",
      "confidence": "high",
      "signals": ["name_similarity", "route_association"],
      "review_needed": false
    }
  ],
  "unmatched_planned": ["PF-005", "PF-009"],
  "unmatched_implemented": ["IF-008"],
  "confirmed_by_user": false
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `planned_features[].id` | string | `PF-` 前缀 + 三位数字 |
| `planned_features[].source` | string | **铁律 #1: 必须有 file:line** |
| `implemented_features[].evidence` | object | 4 个维度的实现证据，缺失的字段填 `null` |
| `implemented_features[].completeness` | enum | `full` / `partial` / `skeleton` |
| `matches[].confidence` | enum | `high` / `medium` / `low` |
| `matches[].signals` | string[] | 匹配命中的信号列表 |
| `confirmed_by_user` | boolean | 用户确认前为 `false`，确认后为 `true` |

---

## 执行流程总结

```
1. 扫描需求文档 → planned_features[]
2. 扫描代码（4 维度）→ implemented_features[]
3. 匹配对齐 → matches[] + unmatched lists
4. 展示表格 → 等待用户确认
5. 用户确认后 → confirmed_by_user = true → 输出 feature-inventory.json
6. 传递给 Step 2 (Gap Analysis)
```

---

> **铁律速查** — 详见 `${CLAUDE_PLUGIN_ROOT}/skills/feature-audit.md` 的「5 条铁律」章节。
> 本步骤强相关：**来源绑定**（每条匹配必须引用 file:line）、**保守分类**（低置信度匹配标 needs_confirmation）、**用户权威**（匹配结果必须经用户确认）。
