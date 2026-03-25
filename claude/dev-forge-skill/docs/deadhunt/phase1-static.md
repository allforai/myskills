## Phase 1: 静态分析

> 不运行应用，仅通过代码分析发现问题。
> **核心原则：双向分析**
>
> **Understand-then-Scan 原则**：不硬编码 grep 模式盲扫。
> LLM 先在 Phase 0 理解项目的路由注册方式、API 定义模式、ORM 约定，
> 再用这个理解去扫描全项目。本文档中的 grep/find 命令均为**参考示例**，
> 执行时根据 Phase 0 理解的实际模式选择对应提取方式。

```
方向 A: 界面 → 数据 (Forward)          方向 B: 数据 → 界面 (Reverse)
"界面上有的，后面能通吗？"              "后端有的，界面上找得到吗？"

 菜单入口 ──→ 路由存在？                 API 端点 ──→ 有前端调用？
 链接跳转 ──→ 目标有效？                 路由定义 ──→ 有菜单/按钮指向？
 按钮操作 ──→ API 存在？                 数据库表 ──→ 有对应管理界面？
 表单提交 ──→ 后端处理？                 后端权限 ──→ 前端有对应控制？

两方向交叉得出四种状态：
┌──────────────┬──────────────────┬─────────────────────┐
│              │ 数据层存在        │ 数据层不存在          │
├──────────────┼──────────────────┼─────────────────────┤
│ 界面有入口    │ ✅ 健康           │ 🔴 死链 (点了就 404)  │
│ 界面无入口    │ 🔴 幽灵功能       │ ✅ 正常 (未实现)      │
│              │ (不可达的功能)     │                     │
└──────────────┴──────────────────┴─────────────────────┘
```

### 1.1 方向 A（界面→数据）: 路由完整性分析

**目标**：找出所有注册的路由，与菜单/导航配置做交叉对比。

**重要**：根据 Phase 0 探测到的技术栈，**仅执行对应框架的提取策略**。以下是各框架的参考模式（不是全部执行）：

```
路由提取策略（按 Phase 0 探测到的框架选择执行）：

配置式路由（React Router / Vue Router / Angular Router）：
  → 扫描路由配置文件中的 path 定义

文件式路由（Nuxt / Next.js / Remix / SvelteKit）：
  → 扫描 pages/ 或 app/ 目录的文件结构推导路由

原生移动端（Flutter GoRouter / RN Navigation）：
  → 扫描路由配置类/文件

后端路由（Express / Gin / Spring / Django）：
  → 扫描路由注册语句
```

输出：`static-analysis/routes.json`
```json
{
  "registered_routes": [
    { "path": "/users", "component": "UserList", "file": "src/pages/users/index.tsx" },
    { "path": "/users/create", "component": "UserCreate", "file": "src/pages/users/create.tsx" },
    { "path": "/users/:id", "component": "UserDetail", "file": "src/pages/users/[id].tsx" }
  ],
  "menu_entries": [
    { "path": "/users", "label": "用户管理", "parent": "系统管理" }
  ],
  "orphan_routes": [
    { "path": "/users/create", "reason": "路由已注册但无菜单入口" }
  ],
  "dead_menu_entries": [
    { "path": "/reports/daily", "reason": "菜单配置了但无对应组件" }
  ]
}
```

### 1.2 方向 A（界面→数据）: 链接目标有效性

```
扫描策略（按技术栈选择文件类型和导航 API）：
  → 提取代码中所有路由跳转目标（navigate/push/replace/href/to/Link/router.go 等）
  → 仅扫描 Phase 0 确认的前端文件类型（.vue/.tsx/.jsx/.svelte/.dart 等）
  → 与注册路由做对比，找出跳转目标不存在的死链
```

输出：`static-analysis/link-targets.json`

### 1.3 方向 A（界面→数据）: CRUD 完整性检查

对每个标准业务模块，检查是否存在：

| 操作 | 常见代码模式 |
|------|-------------|
| Create (新增) | 新增按钮、`/xxx/create` 路由、`<XxxForm>` 组件、`POST /api/xxx` |
| Read List (列表) | 列表页、`/xxx` 路由、`<XxxList>` 或 `<XxxTable>` 组件、`GET /api/xxx` |
| Read Detail (详情) | 详情页、`/xxx/:id` 路由、`<XxxDetail>` 组件、`GET /api/xxx/:id` |
| Update (编辑) | 编辑按钮、`/xxx/:id/edit` 路由或编辑弹窗、`PUT/PATCH /api/xxx/:id` |
| Delete (删除) | 删除按钮/确认框、`DELETE /api/xxx/:id` |

```
扫描策略（按技术栈选择文件类型）：
  对每个模块，在前端源码中搜索 CRUD 相关模式：
  → Create: 新增/添加/create/Add 相关 UI 元素 + POST API 调用
  → Read:   列表/详情页面 + GET API 调用
  → Update: 编辑/修改 UI + PUT/PATCH API 调用
  → Delete: 删除按钮/确认框 + DELETE API 调用
  仅扫描 Phase 0 确认的前端文件类型
```

输出：`static-analysis/crud-coverage.json`

### 1.4 方向 B（数据→界面）: API 端点反向覆盖分析

> **这是发现"幽灵功能"的关键步骤。**
> 后端已经提供了 API，但前端没有任何地方调用它 → 要么是前端漏做了，要么是废弃 API。

```
提取策略（根据 Phase 0 探测到的技术栈选择）：

Step 1: 提取后端所有 API 端点
  来源优先级：
  a. OpenAPI/Swagger 文档（最权威，如有）
  b. 后端路由注册代码（按框架选择提取模式：
     装饰器模式 / 链式注册 / 配置文件 / 文件路由 等）
  c. Controller/Handler 文件中的路由注解

Step 2: 提取前端所有 API 调用
  来源：
  a. API client / service 层文件（集中定义的 HTTP 调用）
  b. 自动生成的 API 代码（OpenAPI codegen 等）
  c. 分散在组件/页面中的直接调用

Step 3: 差集分析
  后端有但前端没调用 = ghost API（幽灵功能）
  前端调用但后端没注册 = dead endpoint（死链）
```

输出：`static-analysis/api-reverse-coverage.json`
```json
{
  "backend_api_count": 87,
  "frontend_call_count": 72,
  "coverage_rate": "82.7%",
  "ghost_apis": [
    {
      "method": "DELETE",
      "path": "/admin/coupons/batch",
      "backend_file": "server/src/modules/coupon/coupon.controller.ts:45",
      "severity": "high",
      "analysis": "后端有批量删除优惠券接口，但前端没有任何地方调用",
      "possible_reason": "前端漏做 | 废弃接口 | 计划中功能",
      "needs_confirmation": true
    },
    {
      "method": "GET",
      "path": "/admin/users/export",
      "backend_file": "server/src/modules/user/user.controller.ts:78",
      "severity": "medium",
      "analysis": "后端有用户导出接口，但前端没有导出按钮",
      "possible_reason": "前端漏做导出功能",
      "needs_confirmation": true
    },
    {
      "method": "PUT",
      "path": "/api/user/avatar",
      "backend_file": "server/src/modules/user/user.controller.ts:92",
      "severity": "high",
      "analysis": "后端有头像更新接口，但所有客户端都没调用",
      "possible_reason": "所有客户端都漏做了头像上传功能",
      "needs_confirmation": true
    }
  ],
  "orphan_frontend_apis": [
    {
      "method": "GET",
      "path": "/admin/dashboard/realtime",
      "frontend_file": "src/api/dashboard.ts:34",
      "severity": "critical",
      "analysis": "前端调用了此接口，但后端没有对应的路由",
      "result": "运行时必然 404"
    }
  ]
}
```

### 1.5 方向 B（数据→界面）: 路由反向可达性分析

> 路由注册了，但界面上没有任何入口（菜单、按钮、链接）能到达。

```
扫描策略（按 Phase 0 确认的技术栈选择文件类型和路由 API）：
1. 从路由配置/文件路由中提取所有已注册路由
2. 从菜单/导航配置中提取所有菜单引用的路由
3. 从代码中提取所有编程式导航目标（navigate/push/replace/go 等）
4. 合并 2+3 = UI 层可到达的路由集合
5. 差集：已注册但 UI 层不可达 = 幽灵路由（orphan route）
```

输出：`static-analysis/unreachable-routes.json`
```json
{
  "unreachable_routes": [
    {
      "path": "/products/import",
      "component": "ProductImport",
      "file": "src/pages/products/import.tsx",
      "severity": "high",
      "analysis": "商品导入页面已开发，路由已注册，但界面上没有任何按钮或链接指向此页面",
      "suggestion": "在商品列表页的工具栏添加'导入'按钮"
    },
    {
      "path": "/system/backup",
      "component": "SystemBackup",
      "file": "src/pages/system/backup.tsx",
      "severity": "medium",
      "analysis": "系统备份页面存在但无导航入口",
      "suggestion": "在系统设置菜单下添加'数据备份'入口"
    }
  ]
}
```

### 1.6 方向 B（数据→界面）: 数据模型反向覆盖

> 如果有数据库 schema，检查是否有数据表/模型完全没有对应的管理界面。

```
扫描策略（按 Phase 0 确认的 ORM/框架选择提取方式）：
1. 从后端 ORM model 定义中提取所有数据实体名称
   （识别方式取决于 ORM：装饰器、schema 文件、struct tag、Model 子类等）
2. 从前端路由/页面列表中提取所有业务模块
3. 差集：后端有实体但前端无管理界面 = 未覆盖模型（uncovered model）
```

输出：`static-analysis/model-coverage.json`
```json
{
  "backend_models": ["User", "Product", "Order", "Coupon", "Review", "AuditLog", "SystemConfig", "Notification", "PaymentRecord"],
  "frontend_modules": ["User", "Product", "Order", "Coupon", "Review", "AuditLog", "SystemConfig"],
  "uncovered_models": [
    {
      "model": "Notification",
      "table": "notifications",
      "type": "standard",
      "severity": "high",
      "analysis": "通知表有数据，但后台没有通知管理界面",
      "needs_confirmation": true,
      "possible_reason": "前端漏做 | 通过其他方式管理 | 计划中"
    },
    {
      "model": "PaymentRecord",
      "table": "payment_records",
      "type": "readonly",
      "severity": "medium",
      "analysis": "支付记录表存在但后台没有查看入口",
      "needs_confirmation": true,
      "possible_reason": "应在订单详情中查看 | 需要独立管理页面"
    }
  ]
}
```

### 1.6b Flutter/Dart 静态分析补充

> 当 Phase 0 检测到 Flutter 客户端时（`pubspec.yaml` 存在），对 `.dart` 文件执行以下补充分析。
> 与 Web 端的分析逻辑相同（双向、6 步），但 grep 模式和路由结构不同。

#### Dart 路由提取

```bash
# GoRouter（最常用）
grep -rn "GoRoute\|path:" --include="*.dart" lib/ 2>/dev/null

# auto_route
grep -rn "@RoutePage\|AutoRoute(" --include="*.dart" lib/ 2>/dev/null

# GetX
grep -rn "GetPage(" --include="*.dart" lib/ 2>/dev/null

# Navigator 原生
grep -rn "pushNamed\|Navigator.push\|MaterialPageRoute" --include="*.dart" lib/ 2>/dev/null
```

提取规则：

| 路由库 | 代码模式 | 提取逻辑 |
|--------|---------|---------|
| GoRouter | `GoRoute(path: '/orders', builder: ...)` | 路径 = `/orders`，递归提取 `routes:` 子路由 |
| GoRouter | `GoRoute(path: '/orders/:id')` | 动态路由，`:id` 为参数 |
| auto_route | `AutoRoute(path: '/orders', page: OrderRoute.page)` | 路径 = `/orders`，页面 = `OrderRoute` |
| GetX | `GetPage(name: '/orders', page: () => OrderPage())` | 路径 = `/orders`，页面 = `OrderPage` |
| Navigator | `Navigator.pushNamed(context, '/orders')` | 导航目标 = `/orders` |
| Navigator | `MaterialPageRoute(builder: (_) => OrderPage())` | 导航目标 = `OrderPage` Widget |

#### Dart API 调用提取

```bash
# Dio（最常用）
grep -rn "dio\.\(get\|post\|put\|patch\|delete\)\|\.get(\|\.post(\|\.put(" \
  --include="*.dart" lib/ 2>/dev/null

# Dio baseUrl
grep -rn "baseUrl\|BaseOptions" --include="*.dart" lib/ 2>/dev/null

# http 包
grep -rn "http\.\(get\|post\|put\|patch\|delete\)\|Uri\.parse" \
  --include="*.dart" lib/ 2>/dev/null

# Retrofit 注解
grep -rn "@GET\|@POST\|@PUT\|@PATCH\|@DELETE" --include="*.dart" lib/ 2>/dev/null

# Chopper
grep -rn "@Get\|@Post\|@Put\|@Patch\|@Delete" --include="*.dart" lib/ 2>/dev/null
```

提取规则：

| HTTP 库 | 代码模式 | 提取逻辑 |
|---------|---------|---------|
| Dio | `dio.get('/api/orders')` | 方法 = GET, 路径 = `/api/orders` |
| Dio | `dio.post('/api/orders', data: body)` | 方法 = POST, 路径 = `/api/orders` |
| Retrofit | `@GET('/api/orders')` | 方法 = GET, 路径 = `/api/orders` |
| Retrofit | `@POST('/api/orders')` | 方法 = POST, 路径 = `/api/orders` |
| http | `http.get(Uri.parse('$baseUrl/api/orders'))` | 方法 = GET, 需拼接 baseUrl |

#### Dart Widget 导航链

```bash
# GoRouter 编程式导航
grep -rn "context\.go\|context\.push\|context\.replace\|GoRouter\.of" \
  --include="*.dart" lib/ 2>/dev/null

# GetX 编程式导航
grep -rn "Get\.to\|Get\.toNamed\|Get\.off\|Get\.offNamed" \
  --include="*.dart" lib/ 2>/dev/null

# auto_route 编程式导航
grep -rn "AutoRouter\.of\|context\.router\.push\|context\.pushRoute" \
  --include="*.dart" lib/ 2>/dev/null

# Navigator 原生
grep -rn "Navigator\.\(push\|pop\|pushReplacement\|pushNamed\)" \
  --include="*.dart" lib/ 2>/dev/null
```

#### Dart 状态管理层扫描

> 追踪数据从 API 到 UI 的流动路径，辅助发现 Ghost Features。

```bash
# Provider / Riverpod
grep -rn "ChangeNotifierProvider\|StateNotifierProvider\|FutureProvider\|StreamProvider\|ref\.watch\|ref\.read" \
  --include="*.dart" lib/ 2>/dev/null

# Bloc / Cubit
grep -rn "BlocProvider\|BlocBuilder\|BlocListener\|emit(\|Cubit<" \
  --include="*.dart" lib/ 2>/dev/null

# GetX
grep -rn "GetxController\|\.obs\|Obx(\|GetBuilder" \
  --include="*.dart" lib/ 2>/dev/null
```

| 状态管理 | 数据流模式 | 分析方式 |
|---------|-----------|---------|
| Riverpod | `Provider` → `ref.watch` → Widget | 追踪 Provider 中的 API 调用，检查 Widget 是否消费 |
| Bloc | `Event` → `Bloc.emit(State)` → `BlocBuilder` | 追踪 Event handler 中的 API 调用，检查 State 字段是否被 UI 使用 |
| GetX | `Controller.method()` → `.obs` → `Obx()` | 追踪 Controller 中的 API 调用，检查 `.obs` 变量是否被 `Obx` 包裹 |

### 1.7 权限配置分析

如果项目有权限系统，分析哪些功能被权限控制：

```
扫描策略（按 Phase 0 确认的技术栈选择文件类型）：
→ 在前端源码中搜索权限相关代码模式：
  permission / authorize / role / access / hasPermission / checkPermission /
  canAccess / guard / middleware 等
→ 仅扫描 Phase 0 确认的前端文件类型
→ 产出：权限控制点列表 + 哪些路由/功能被权限保护
```

### 1.8 接缝检查（Seam Analysis）

> 以下检查发现"两端各自正确但接缝不匹配"的问题。
> 这类问题是 E2E 测试中最高频的根因，但完全可以在静态分析阶段秒级检出。
> 作为 Round 1 基线扫描的最后一步执行，发现的问题纳入收敛循环。
>
> **两层规则**：1.8.1~1.8.4 是内置通用规则；执行完毕后，LLM 额外推导该项目特有的接缝点
> （如微服务 proto 同步、monorepo 共享包版本、消息队列 schema 一致性等），
> 产出为项目派生规则，纳入后续收敛轮次。详见 fieldcheck overview.md 的两层规则架构。

#### 1.8.1 文件路由冲突检测

基于文件系统的路由框架中，动态路由文件和同名目录共存会导致路由冲突。

```
检测逻辑（技术栈无关）：
1. 识别项目使用的文件路由框架（Phase 0 已探测）
   （适用于所有文件式路由框架，不限于特定框架）
2. 扫描路由目录（pages/ / app/ / routes/ 等）
3. 检测模式：同一目录下同时存在
   - 动态路由文件（带参数占位符的文件，如 [param] / :param / $param 等命名模式）
   - 同名目录（该参数名的目录下有子路由文件）
4. 如果动态路由文件没有嵌套路由出口（框架对应的子路由渲染组件），
   则子路由无法渲染 → ROUTE_CONFLICT

产出: { parent_file, child_files[], has_outlet: bool, severity }
```

#### 1.8.2 权限/RBAC 通配符检查

前端权限检查代码常用精确匹配，但后端可能分配通配符权限。精确匹配无法识别通配符 → 管理员看不到菜单。

```
检测逻辑（技术栈无关）：
1. 扫描前端权限检查代码
   - Grep: hasPermission / checkPermission / canAccess / includes(permission) 等
   - 提取权限检查函数体
2. 分析是否处理了通配符模式：
   - 是否有 "*" 或 "admin:*" 等通配符匹配逻辑
   - 是否只做精确字符串匹配
3. 扫描后端角色定义
   - 是否存在 permissions: ["*"] 或类似通配符分配
4. 前端无通配符处理 + 后端有通配符分配 → RBAC_WILDCARD_MISS

产出: { frontend_file, check_function, backend_role, wildcard_pattern, severity }
```

#### 1.8.3 API 端点路径前后端一致性

前端 API client 调用的 URL 路径与后端 router 注册的路径必须完全匹配（含 HTTP method）。

```
检测逻辑（技术栈无关）：
1. 提取前端 API 调用的完整路径（method + path）
   - 来源：API client 文件、service 文件、store 文件
2. 提取后端路由注册的完整路径（method + path）
   - 来源：router 定义文件
3. 逐条比对：
   - 前端调用的路径在后端路由中不存在 → DEAD_ENDPOINT（已有）
   - 前端路径与后端路径相似但不完全匹配（如多/少一级路径段）→ PATH_DRIFT
   - 前端 method 与后端 method 不匹配 → METHOD_MISMATCH

产出: { frontend_file, frontend_path, backend_file, backend_path, diff_type }
```

#### 1.8.4 基础设施配置 ↔ 子项目一致性

后端的跨域（CORS）、内容安全策略（CSP）、代理配置等必须包含所有子项目的端口/域名。新增子项目或平台时容易遗漏。

```
检测逻辑（结构化比对）：
1. 从 Phase 0 提取所有子项目的端口和域名
   - 开发环境：localhost:{port}
   - 生产环境：子项目域名（如有配置）

2. 提取后端基础设施配置：
   - CORS allowed origins（中间件/配置文件）
   - CSP 白名单（如有）
   - 反向代理配置（nginx/caddy 等）

3. 比对：
   - 子项目端口不在 CORS origins → CORS_ORIGIN_MISSING（Critical）
   - 子项目域名不在 CSP → CSP_MISSING（Warning）
   - 子项目没有代理规则 → PROXY_MISSING（Warning）

产出: { sub_project, port, config_type, config_file, status }
```

---

### 1.9 双向分析汇总

所有静态分析完成后（含接缝检查），生成汇总矩阵 `static-analysis/bidirectional-matrix.json`：

```json
{
  "summary": {
    "forward_issues": {
      "dead_menu_entries": 3,
      "dead_link_targets": 5,
      "crud_missing_in_ui": 4
    },
    "reverse_issues": {
      "ghost_apis": 8,
      "unreachable_routes": 3,
      "uncovered_models": 2
    },
    "cross_validated": {
      "ui_has_and_data_has": 72,
      "ui_has_but_data_missing": 5,
      "data_has_but_ui_missing": 13,
      "neither_has": 0
    }
  },
  "health_score": {
    "forward": "93.5%",
    "reverse": "84.7%",
    "overall": "89.1%"
  }
}
```

---

## 多轮收敛机制

> 单次分析容易漏掉问题：grep 模式覆盖不全、双向分析缺乏闭环反馈、问题模块的邻居未被排查。
> 收敛机制通过逐轮递进，让每一轮都比上一轮更精准。

### 收敛循环结构

```
Round 1 (基础扫描):  执行上述 1.1 - 1.9 全部步骤（含接缝检查），建立 baseline
                      记录 findings 数量 = count_r1
        ↓
Round 2 (模式学习):  从 Round 1 结果提取模式 → 用新模式搜同类问题
                      delta_r2 = 新发现数量
        ↓
Round 3 (交叉验证):  方向A结果反查方向B遗漏，方向B结果反查方向A遗漏
                      delta_r3 = 新发现数量
        ↓
Round 4 (扩散搜索):  对问题模块的关联模块做排查
                      delta_r4 = 新发现数量
        ↓
收敛检查: if (delta_r2 + delta_r3 + delta_r4 > 0) && (iteration < 3)
            → 回到 Round 2，用扩大后的 findings 再来一轮
          else → 收敛完成，输出最终结果到 bidirectional-matrix.json
```

**最大周期数：3**（Round 2-4 为一个周期，最多重复 3 个周期。含 Round 1 基础扫描，总计最多 10 轮）。

每轮的新发现都需要标记 `source` 字段，用于追踪和报告：
- Round 1: `source: "baseline"`
- Round 2: `source: "pattern_learning"`
- Round 3: `source: "cross_validation"`
- Round 4: `source: "diffusion"`

---

### 1.10 Round 2: 模式学习

> 从上轮 findings 中提取模式，用新模式搜索同类问题。
> **只搜索上轮没覆盖到的范围，不重复已检查的内容。**

#### 模式提取规则

对上轮每个 finding，按以下规则提取模式并生成新的搜索动作：

| 发现类型 | 提取的模式 | 新搜索动作 |
|---------|-----------|-----------|
| 死链 `/admin/users/detail` | 路径模式: `/admin/*/detail` | grep 所有匹配 `/admin/.*/detail` 的路由，逐一验证目标是否存在 |
| 幽灵 API `DELETE /api/coupons/batch` | 操作模式: `*/batch` 端点 | grep 所有包含 `batch` 的后端端点，检查前端是否调用 |
| 孤儿路由 `src/pages/reports/daily.tsx` | 目录模式: `reports/` 下所有页面 | 遍历 `reports/` 目录下每个组件文件，检查是否有菜单/链接入口 |
| 动态路由拼接 `navigate('/xxx' + id)` | 代码模式: 字符串拼接路由 | grep `navigate\(.*\+\|navigate\(.*\$\{` 以及 `push\(.*\+\|push\(.*\$\{` 找所有动态拼接的路由 |
| CRUD 缺失: 用户管理缺删除 | CRUD 模式: 某类操作缺失 | 对所有标准业务模块检查是否也缺少同类操作（如：都缺删除？都缺导出？） |
| 404 API 路径含 `/v2/` | 版本模式: API 版本前缀 | grep 所有 `/v2/` 的 API 调用，检查后端是否都支持 v2 |

#### 执行步骤

1. **遍历上轮 findings**，对每个 finding 按上表规则提取模式
2. **去重合并模式**（如多个 findings 都指向同一个路径模式，只搜一次）
3. **对每个模式生成 grep/分析命令**：
   ```bash
   # 示例：路径模式 /admin/*/detail
   grep -rn "path.*admin.*detail\|/admin/[^/]*/detail" --include="*.tsx" --include="*.ts" src/

   # 示例：操作模式 */batch
   grep -rn "batch" --include="*.ts" server/src/ | grep -i "@Get\|@Post\|@Put\|@Delete\|router\."

   # 示例：代码模式 — 字符串拼接路由
   grep -rn "navigate(.*+\|navigate(.*\${\|push(.*+\|push(.*\${" --include="*.tsx" --include="*.ts" src/
   ```
4. **执行搜索**，对每个匹配结果做验证（目标路由是否存在、API 是否被调用）
5. **新发现加入 findings**，标记 `source: "pattern_learning"`
6. **记录 delta_r2** = 本轮新发现数量

---

### 1.11 Round 3: 交叉验证

> 方向 A（界面→数据）和方向 B（数据→界面）的结果互相审查，找出对方的盲区。

#### A → B 反查：用界面侧结果追查数据侧遗漏

对方向 A 的每个 finding，检查方向 B 是否有对应条目：

```
方向A发现死链 /admin/reports/daily
  → 反查方向B: 这个路由对应的后端 API 是什么？
  → grep 后端代码中 "reports" 或 "daily" 相关的 controller/handler
  → 如果方向B没检查到这个 API → 补查
  → 可能发现: 后端有 @Get('reports/daily') 但方向B的 grep 没匹配到（写法差异）

方向A发现 CRUD 缺删除入口
  → 反查方向B: 后端有 DELETE 端点吗？
  → grep "DELETE\|@Delete\|delete(" 在对应模块的 controller 中
  → 有 DELETE 端点 → 前端确实遗漏（加强方向A的结论）
  → 没有 DELETE 端点 → 后端也没做（修正判定：不是前端问题）
```

#### B → A 反查：用数据侧结果追查界面侧遗漏

对方向 B 的每个 finding，检查方向 A 是否有对应条目：

```
方向B发现幽灵 API: POST /api/users/import
  → 反查方向A: 有没有导入按钮？
  → grep "导入\|import\|Import" 在用户管理相关组件中
  → 可能发现: 按钮存在但被 v-if="false" 或 display:none 隐藏了（新问题类型）

方向B发现不可达路由: /products/import
  → 反查方向A: 有没有任何入口指向它？
  → 补查所有间接引用: onClick → navigate('/products/import')
  → 不只查菜单配置，也查按钮点击事件和编程式导航
```

#### 执行步骤

1. 取方向 A 所有 findings → 对每个检查方向 B 是否有对应条目
   - 有对应 → 跳过（已覆盖）
   - 无对应 → 生成反向查询并执行
2. 取方向 B 所有 findings → 对每个检查方向 A 是否有对应条目
   - 同上反向操作
3. 新发现标记 `source: "cross_validation"`
4. 如果交叉验证修正了已有 finding 的判定（如：方向A报"前端缺失"但方向B发现后端也没做），更新该 finding 的 `reason` 和 `action`
5. 记录 delta_r3 = 本轮新发现数量

---

### 1.12 Round 4: 扩散搜索

> 问题会扎堆。一个模块有问题，它的邻居大概率也有。
> 从已知问题点向关联模块扩散排查，**只扩散一层，不递归**。

#### 关联关系定义

对每个问题模块，按以下 5 种关系找到关联模块：

1. **同目录兄弟**
   ```bash
   # src/pages/order/list.tsx 有问题 → 排查 src/pages/order/ 下所有文件
   ls src/pages/order/
   ```

2. **同路由前缀**
   ```bash
   # /admin/order/list 有问题 → 排查所有 /admin/order/* 路由
   grep -rn "path.*admin/order" --include="*.ts" --include="*.tsx" src/
   ```

3. **共享 API 前缀**
   ```bash
   # /api/order/ 相关接口有问题 → 排查所有 /api/order/* 端点
   grep -rn "/api/order" --include="*.ts" src/api/ server/src/
   ```

4. **共享组件**
   ```bash
   # OrderTable 组件关联页面有问题 → 谁还 import 了 OrderTable？
   grep -rn "import.*OrderTable\|from.*OrderTable" --include="*.tsx" --include="*.vue" src/
   ```

5. **同批次修改**
   ```bash
   # 找到问题文件最近的 commit，看同一个 commit 还改了什么
   git log --oneline -1 --format=%H -- src/pages/order/
   git show --name-only <commit_hash> | grep "src/"
   ```

#### 执行步骤

1. 收集所有 Round 1-3 的问题模块，去重得到问题模块列表
2. 对每个问题模块，按上述 5 种关联关系找到关联模块
3. 合并所有关联模块，去重
4. **过滤掉已被 Round 1-3 充分检查过的模块**（避免重复劳动）
5. 对剩余关联模块执行：路由完整性(1.1) + CRUD 覆盖(1.3) + API 反向覆盖(1.4) 检查
6. 新发现标记 `source: "diffusion"`
7. 记录 delta_r4 = 本轮新发现数量

---

### 1.13 收敛追踪

每轮执行完毕后，记录收敛数据到 `static-analysis/convergence.json`：

```json
{
  "phase": "static",
  "max_iterations": 3,
  "rounds": [
    { "round": 1, "cycle": 0, "type": "baseline",         "new_findings": 12, "total": 12 },
    { "round": 2, "cycle": 1, "type": "pattern_learning",  "new_findings": 5,  "total": 17 },
    { "round": 3, "cycle": 1, "type": "cross_validation",  "new_findings": 3,  "total": 20 },
    { "round": 4, "cycle": 1, "type": "diffusion",         "new_findings": 2,  "total": 22 },
    { "round": 5, "cycle": 2, "type": "pattern_learning",  "new_findings": 1,  "total": 23 },
    { "round": 6, "cycle": 2, "type": "cross_validation",  "new_findings": 0,  "total": 23 },
    { "round": 7, "cycle": 2, "type": "diffusion",         "new_findings": 0,  "total": 23 }
  ],
  "converged_at_round": 7,
  "baseline_findings": 12,
  "convergence_bonus": 11,
  "bonus_rate": "91.7%"
}
```

`convergence_bonus` 和 `bonus_rate` 是收敛机制的价值证明——让用户看到"多找几轮"到底多找出了多少。

在 `bidirectional-matrix.json` 的汇总中也加入收敛信息：

```json
{
  "summary": { ... },
  "health_score": { ... },
  "convergence": {
    "total_rounds": 7,
    "baseline_findings": 12,
    "final_findings": 23,
    "bonus_rate": "91.7%"
  }
}
```

