# Step 4: 数据灌入 + Clean 模式

> 本文档是 demo-forge 最关键的执行步骤 — 通过 API 将规划好的数据灌入运行中的应用，并支持 clean 模式逆序清理。

---

## 1. 前提条件

Step 4 是执行阶段，开始前必须满足以下条件：

### 应用就绪

- 应用必须处于**运行中**状态（用户提供 URL，如 `http://localhost:3000` 或 `http://localhost:8080`）
- 用户提供管理员账号和密码（灌入通常需要管理员权限）

### 前序步骤已完成

| 文件 | 来源 Step | 用途 |
|------|-----------|------|
| `.allforai/seed-forge/project-analysis.json` | Step 0 | 提供 auth endpoint、create API、upload API 映射 |
| `.allforai/seed-forge/forge-plan.json` | Step 2 | 提供 creation_order、每个实体的 count、fields 规则 |
| `.allforai/seed-forge/assets/` | Step 3 | 提供已下载的图片文件，供上传使用 |
| `.allforai/seed-forge/assets-manifest.json` | Step 3 | 图片本地路径 + 来源信息 |

### 前置检查清单

```
1. forge-plan.json 存在且可解析？      → 不存在则报错: "请先运行 /demo-forge plan"
2. forge-plan.json 中 creation_order 非空？ → 空则报错: "数据规划为空，无数据可灌入"
3. 用户是否提供了应用 URL？              → 未提供则询问
4. 用户是否提供了登录凭据？              → 未提供则询问
5. assets/ 目录存在且有图片？            → 不存在则跳过图片上传环节
```

---

## 2. 认证流程

灌入前必须先登录获取 token，所有后续请求都需要携带认证信息。

### 2.1 查找认证端点

从 `project-analysis.json` 中找到 auth 相关的 API 端点：

```
常见认证端点模式:
  POST /api/auth/login
  POST /api/login
  POST /api/auth/signin
  POST /api/v1/auth/token
  POST /api/sessions
```

如果 Step 0 已标记 `API_GAP: 无认证端点`，则无法自动登录 — 询问用户是否有认证方式（如 API Key、固定 token、Basic Auth 等）。

### 2.2 调用登录 API

```
POST {base_url}{auth_endpoint}
Content-Type: application/json

{
  "username": "{user_provided_username}",
  "password": "{user_provided_password}"
}
```

注意：字段名可能不是 `username`/`password`，而是 `email`/`password`、`account`/`passwd` 等。从 Step 0 分析的 auth API 参数结构中确定实际字段名。

### 2.3 提取 Token

登录成功后，token 可能出现在以下位置（按优先级检查）：

| 位置 | 提取方式 | 示例 |
|------|----------|------|
| Response body — `token` 字段 | `response.data.token` 或 `response.token` | `{"token": "eyJhbG..."}` |
| Response body — `access_token` 字段 | `response.data.access_token` | `{"access_token": "eyJhbG..."}` |
| Response body — 嵌套结构 | `response.data.auth.token` | `{"data": {"auth": {"token": "..."}}}` |
| Response header — `Set-Cookie` | 提取 cookie 值 | `Set-Cookie: session=abc123; Path=/` |
| Response header — `Authorization` | 直接使用 | `Authorization: Bearer eyJhbG...` |

### 2.4 在后续请求中使用 Token

根据 token 来源设置请求头：

```
如果是 JWT/Bearer token:
  Authorization: Bearer {token}

如果是 Cookie:
  Cookie: {cookie_name}={cookie_value}

如果是 API Key:
  X-API-Key: {key}
  或 Authorization: ApiKey {key}
```

### 2.5 认证失败处理

```
认证失败 → 立即停止灌入流程，向用户报告:
  - HTTP status code
  - Response body（错误消息）
  - 可能的原因（账号错误、接口不匹配、服务未启动）
  - 不尝试重试或猜测其他凭据
```

**铁律：认证失败不继续。** 没有有效 token，后续所有创建请求都会 401/403，继续执行毫无意义。

---

## 3. 灌入流程

### 3.1 总体逻辑

按 `forge-plan.json` 中的 `creation_order` 数组，依次处理每个实体：

```
加载 forge-plan.json
初始化 id_map = {}
初始化 forge_log = []
初始化 forge_data = { created: [] }

For each entity in creation_order:
  entity_config = forge-plan.entities[entity]
  id_map[entity] = []

  For item_index in range(1, entity_config.count + 1):

    // ── Step 1: 图片上传（如需要）──
    uploaded_refs = {}
    For each field in entity_config.fields:
      If field.type == "image" or field has image_query:
        local_path = .allforai/seed-forge/assets/{entity}/{NNN}.jpg
        If local_path exists:
          uploaded = POST {base_url}{upload_endpoint}
            Content-Type: multipart/form-data
            file: @{local_path}
          If uploaded.success:
            uploaded_refs[field_name] = uploaded.url or uploaded.file_id
          Else:
            Log upload failure
            uploaded_refs[field_name] = null  // 跳过图片，继续创建

    // ── Step 2: 构建请求体 ──
    request_body = {}
    For each field in entity_config.fields:
      If field has "ref" (外键引用):
        // 从 id_map 中随机选取一个已创建的父实体 ID
        parent_entity = field.ref.split(".")[0]
        parent_ids = id_map[parent_entity]
        If parent_ids is empty:
          Log error: "依赖实体 {parent_entity} 无已创建 ID"
          Skip this item
        request_body[field_name] = random_choice(parent_ids)
      Elif field_name in uploaded_refs:
        request_body[field_name] = uploaded_refs[field_name]
      Else:
        request_body[field_name] = generate_value(field.rules)

    // ── Step 3: 调用创建 API ──
    response = POST {base_url}{entity_config.create_api}
      Authorization: Bearer {token}
      Content-Type: application/json
      Body: request_body

    // ── Step 4: 处理结果 ──
    If response.status in [200, 201]:
      created_id = extract_id(response.body)
      id_map[entity].append(created_id)
      forge_data.created.append({
        entity: entity,
        id: created_id,
        api: entity_config.create_api,
        delete_api: "DELETE {entity_base_path}/{created_id}",
        created_at: now(),
        order: global_order_counter++
      })
      forge_log.append({
        entity: entity,
        item_index: item_index,
        status: "success",
        api: entity_config.create_api,
        request_body_summary: summarize(request_body),
        response_status: response.status,
        response_id: created_id,
        error: null,
        timestamp: now()
      })
    Else:
      // 创建失败 — 记录但不中断
      detect_and_record_api_gap(entity, response)
      forge_log.append({
        entity: entity,
        item_index: item_index,
        status: "failed",
        api: entity_config.create_api,
        request_body_summary: summarize(request_body),
        response_status: response.status,
        response_id: null,
        error: response.body,
        timestamp: now()
      })
      // ★ 继续处理下一条，不要停止

保存 forge_log → .allforai/seed-forge/forge-log.json
保存 forge_data → .allforai/seed-forge/forge-data.json
合并更新 api-gaps.json
```

### 3.2 字段值生成规则

在构建 request_body 时，根据 `forge-plan.json` 中每个字段的 rules 生成值：

| 字段类型 | 规则 | 生成方式 |
|----------|------|----------|
| 名称 (name/title) | `style: "行业产品名"` + `examples` | 参考 examples 风格，生成同类名称 |
| 价格 (price/amount) | `range: [min, max]` + `distribution` | 在范围内生成，按分布（normal/uniform） |
| 枚举 (status/role/type) | `values: ["a", "b", "c"]` | 按权重随机选取（如 `["user","user","user","admin"]` 则 user 概率 75%） |
| 邮箱 (email) | `style: "{pinyin}@example.com"` | 根据风格模板生成 |
| 电话 (phone) | `locale: "zh-CN"` | 按地区格式生成 |
| 日期 (date/time) | `range: ["2024-01-01", "2026-02-24"]` | 在范围内随机 |
| 文本 (description/content) | `style: "行业描述"` + `length` | 生成符合行业风格的描述文本 |
| 外键 (category_id/user_id) | `ref: "Category.id"` | 从 id_map 中随机选取 |
| 图片 (image/avatar/cover) | `image_query` | 使用已上传的 URL/ID |
| 布尔 (is_active/published) | `values: [true, false]` | 按权重随机 |

### 3.3 图片上传细节

```
上传请求:
  POST {base_url}{upload_endpoint}
  Authorization: Bearer {token}
  Content-Type: multipart/form-data

  file: @.allforai/seed-forge/assets/{entity}/{NNN}.jpg

上传端点来源:
  - project-analysis.json 中标记的 upload API
  - 常见模式: POST /api/upload, POST /api/files, POST /api/media

上传成功后提取:
  - response.url → 图片访问 URL（如 /uploads/xxx.jpg）
  - response.file_id 或 response.id → 文件 ID
  - response.data.url → 嵌套结构中的 URL

图片编号匹配:
  assets/{entity}/001.jpg → 第 1 条数据
  assets/{entity}/002.jpg → 第 2 条数据
  ...
  如果图片数量 < 数据数量 → 循环使用（001 → 002 → ... → 001 → ...）
```

### 3.4 错误处理策略

```
原则: 单条失败不中断整体灌入。

遇到错误时:
  1. 记录完整错误信息到 forge-log.json
  2. 检测是否属于 API 缺口（见第 5 节）
  3. 跳过该条数据，继续处理下一条
  4. 不重试（避免重复创建）

例外 — 以下情况停止灌入:
  - 认证 token 失效（连续收到 401）→ 停止，报告 token 过期
  - 基础 URL 不可达（连接超时）→ 停止，报告应用可能已关闭
  - 创建 API 端点全部 404（实体级别）→ 跳过该实体，继续下一个实体
```

---

## 4. ID 映射

### 4.1 id_map 结构

灌入过程中维护一个内存中的 id_map，记录每个实体已成功创建的所有 ID：

```json
{
  "Category": [1, 2, 3, 4, 5],
  "User": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
  "Product": [100, 101, 102, 103, 104, 105],
  "Order": [1001, 1002, 1003]
}
```

注意：ID 的类型取决于后端返回，可能是数字、字符串、UUID：

```json
{
  "Category": ["cat-001", "cat-002", "cat-003"],
  "User": ["550e8400-e29b-41d4-a716-446655440000", "..."],
  "Product": [1, 2, 3, 4, 5]
}
```

### 4.2 外键引用解析

当创建一个依赖其他实体的数据时，从 id_map 中解析外键引用：

```
forge-plan.json 中的字段定义:
  "category_id": { "ref": "Category.id" }

解析流程:
  1. 解析 ref 字符串 → parent_entity = "Category", parent_field = "id"
  2. 查找 id_map["Category"]
  3. 如果为空 → 报错（依赖实体尚未创建，creation_order 可能有误）
  4. 如果非空 → 随机选取一个 ID

示例:
  创建 Order 时:
    - user_id → 从 id_map["User"] 中随机选取 → 14
    - product_id → 从 id_map["Product"] 中随机选取 → 103
    - 最终请求体: { "user_id": 14, "product_id": 103, "quantity": 2, ... }
```

### 4.3 分布策略

随机选取外键 ID 时，默认均匀分布。但某些场景可能需要偏斜分布（如部分用户有更多订单）：

```
默认: random_choice(id_map["User"])    → 均匀分布
可选: weighted_choice(id_map["User"])  → 前 20% 的用户占 80% 的订单

根据 forge-plan.json 中 field.distribution 决定:
  "uniform"  → 均匀随机（默认）
  "skewed"   → 头部偏斜，前 20% ID 被选中概率更高
  "sequential" → 顺序循环分配
```

---

## 5. API 缺口实时检测

灌入过程中，每次 API 调用的结果都可能揭示新的 API 缺口。这些缺口与 Step 0 静态分析的缺口合并，形成完整的 API 缺口报告。

### 5.1 缺口检测规则

| HTTP Status | Gap Type | Description | 触发条件 |
|-------------|----------|-------------|----------|
| 404 | `API_GAP: 端点不存在` | Endpoint from analysis doesn't actually exist | 创建 API 或上传 API 返回 404 |
| 400 + field error | `API_GAP: 参数不匹配` | Request body doesn't match what API expects | 返回 400 且 body 包含 field/validation error |
| 413 | `API_GAP: 上传大小限制` | File too large for upload endpoint | 图片上传返回 413 Payload Too Large |
| 401 / 403 | `API_GAP: 权限不足` | Token doesn't have permission for this operation | 已认证但特定端点返回 401/403 |
| 500 | `API_GAP: 服务端错误` | Server error during creation | 返回 500 Internal Server Error |
| Missing fields in response | `API_GAP: 响应结构不符` | Response doesn't return expected ID | 创建成功 (200/201) 但 response body 中无 id 字段 |

### 5.2 缺口记录格式

每条检测到的缺口记录为：

```json
{
  "gap_id": "GAP-RT-001",
  "source": "runtime",
  "entity": "Product",
  "gap_type": "API_GAP: 参数不匹配",
  "api": "POST /api/products",
  "http_status": 400,
  "detail": "Response: {\"error\": \"category_id must be an integer, got string\"}",
  "request_body_sample": { "name": "日式陶瓷杯", "category_id": "cat-001", "price": 89.9 },
  "detected_at": "2026-02-24T15:30:15Z",
  "impact": "Product 灌入失败，category_id 类型不匹配（分析时认为是 string，实际要求 integer）"
}
```

### 5.3 合并 Step 0 + Step 4 缺口

灌入完成后，将 Step 4 实时检测的缺口与 Step 0 静态分析的缺口合并写入 `api-gaps.json`：

```json
{
  "_meta": {
    "generated_at": "2026-02-24T15:45:00Z",
    "static_gaps": 3,
    "runtime_gaps": 2,
    "total_gaps": 5
  },
  "gaps": [
    {
      "gap_id": "GAP-SA-001",
      "source": "static_analysis",
      "entity": "Banner",
      "gap_type": "API_GAP: 无创建接口",
      "detail": "Banner 模型存在但未发现 POST /api/banners 端点",
      "detected_at": "2026-02-24T14:00:00Z"
    },
    {
      "gap_id": "GAP-SA-002",
      "source": "static_analysis",
      "entity": "Product",
      "gap_type": "API_GAP: 无上传接口",
      "detail": "Product 模型有 image 字段但未发现文件上传端点",
      "detected_at": "2026-02-24T14:00:00Z"
    },
    {
      "gap_id": "GAP-RT-001",
      "source": "runtime",
      "entity": "Product",
      "gap_type": "API_GAP: 参数不匹配",
      "api": "POST /api/products",
      "http_status": 400,
      "detail": "category_id must be integer, got string",
      "detected_at": "2026-02-24T15:30:15Z"
    }
  ]
}
```

合并规则：
- `source: "static_analysis"` — 来自 Step 0 的分析
- `source: "runtime"` — 来自 Step 4 的灌入实测
- gap_id 前缀区分：`GAP-SA-xxx` (static analysis) vs `GAP-RT-xxx` (runtime)
- 如果 Step 0 标记了 "无创建接口"，但 Step 4 实际调用成功 → 移除该 static gap（Step 0 误报）
- 如果 Step 0 未发现缺口，但 Step 4 灌入时发现了 → 追加为 runtime gap

---

## 6. Clean 模式

当用户运行 `/demo-forge clean` 时，**直接连数据库批量删除**，比逐条调 DELETE API 快得多。

### 6.1 为什么清理走数据库而不走 API

| | 灌入（走 API） | 清理（走数据库） |
|---|---|---|
| 原因 | 保证业务逻辑一致性（触发校验、hook、关联） | 速度快，一条 SQL 删几百条 |
| 风险 | 无 | 绕过业务逻辑，但清理只是删除，风险可控 |
| 依赖 | 需要应用运行 | 需要数据库连接信息 |

### 6.2 用户输入

用户需提供数据库连接信息，通过 AskUserQuestion 收集：

- **数据库类型**：MySQL / PostgreSQL / SQLite / MongoDB
- **连接方式**（二选一）：
  - 连接字符串（如 `postgresql://user:pass@localhost:5432/mydb`）
  - 或从项目配置文件读取（如 `.env` 中的 `DATABASE_URL`）

优先从项目配置文件自动检测：
- `.env` → `DATABASE_URL`, `DB_HOST`, `DB_NAME`
- `prisma/schema.prisma` → `datasource.url`
- `ormconfig.json` / `ormconfig.ts` → connection config
- `settings.py` → `DATABASES`
- Go 项目 → `config.yaml` 或环境变量

### 6.3 两种清理方式

#### 方式 A：精确删除（默认）

根据 `forge-data.json` 记录的 ID，按表执行 SQL：

```sql
-- 逆序删除：先删子表，再删父表
DELETE FROM orders WHERE id IN (201, 202, 203, ...);
DELETE FROM products WHERE id IN (101, 102, 103, ...);
DELETE FROM users WHERE id IN (11, 12, 13, ...);
DELETE FROM categories WHERE id IN (1, 2, 3, ...);
```

**优点**：只删除 demo-forge 灌入的数据，不影响其他数据。
**适用**：数据库中有其他数据需要保留。

#### 方式 B：整表清空

用户确认后执行 TRUNCATE（需要**二次确认**，因为会删除所有数据）：

```sql
-- 需要用户二次确认：这会清空整张表！
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE users CASCADE;
TRUNCATE TABLE categories CASCADE;
```

**优点**：最快，重置自增 ID。
**适用**：纯演示环境，表里只有 demo-forge 的数据。
**⚠️ 必须二次确认**：提示用户"整表清空会删除所有数据，不仅是 demo-forge 灌入的。确认？"

### 6.4 执行流程

```
/demo-forge clean
      │
      ▼
  1. 加载 .allforai/seed-forge/forge-data.json
      │
      ├── 文件不存在 → 报错: "未找到 forge-data.json，无数据可清理"
      │
      └── 文件存在 → 解析 created 数组
            │
            ▼
  2. 获取数据库连接
      │   优先从项目配置自动检测
      │   检测不到 → 询问用户
      │
      ▼
  3. 连接数据库（通过 Bash 执行 SQL 命令）
      │   MySQL:      mysql -h host -u user -ppass dbname -e "SQL"
      │   PostgreSQL: psql "连接串" -c "SQL"
      │   SQLite:     sqlite3 db.sqlite "SQL"
      │   MongoDB:    mongosh "连接串" --eval "js"
      │
      ▼
  4. 询问清理方式
      │   → 精确删除（默认，推荐）
      │   → 整表清空（需二次确认）
      │
      ▼
  5. 按逆序执行删除
      │   灌入顺序: Category → User → Product → Order
      │   清理顺序: Order → Product → User → Category
      │
      │   精确删除: DELETE FROM {table} WHERE id IN (...)
      │   整表清空: TRUNCATE TABLE {table} CASCADE
      │
      ▼
  6. 更新 forge-data.json（精确删除模式：移除已删除的记录）
      │
      ▼
  7. 输出清理报告（见第 8 节）
```

### 6.5 MongoDB 清理

MongoDB 使用对应语法：

```javascript
// 精确删除
db.orders.deleteMany({ _id: { $in: [ObjectId("..."), ...] } });
// 整表清空
db.orders.drop();
```

### 6.6 关于资源文件

**已下载的图片素材不会被 clean 删除。**

Clean 模式只清理数据库中的记录，不删除本地文件。图片素材可以复用，下次 `/demo-forge fill` 时不需要重新下载。

如果用户需要删除已下载的图片：

```bash
rm -rf .allforai/seed-forge/assets/
```

### 6.7 断点续清

精确删除模式下，`forge-data.json` 会在每批 SQL 执行后更新 — 已成功删除的记录会被移除。下次运行 `/demo-forge clean` 时，只会处理剩余未删除的记录。

---

## 7. 输出格式

### 7.1 forge-log.json

灌入日志，记录每条数据的创建尝试和结果：

```json
{
  "_meta": {
    "started_at": "2026-02-24T15:30:00Z",
    "completed_at": "2026-02-24T15:45:00Z",
    "base_url": "http://localhost:3000",
    "total_attempted": 135,
    "total_success": 128,
    "total_failed": 7
  },
  "log": [
    {
      "entity": "Category",
      "item_index": 1,
      "status": "success",
      "api": "POST /api/categories",
      "request_body_summary": { "name": "家居生活", "sort_order": 1 },
      "response_status": 201,
      "response_id": 1,
      "error": null,
      "timestamp": "2026-02-24T15:30:01Z"
    },
    {
      "entity": "Product",
      "item_index": 3,
      "status": "failed",
      "api": "POST /api/products",
      "request_body_summary": { "name": "日式陶瓷杯", "category_id": "cat-003", "price": 89.9 },
      "response_status": 400,
      "response_id": null,
      "error": { "message": "category_id must be an integer" },
      "timestamp": "2026-02-24T15:32:15Z"
    },
    {
      "entity": "User",
      "item_index": 5,
      "status": "success",
      "api": "POST /api/users",
      "request_body_summary": { "name": "李晓红", "email": "lixiaohong@example.com", "role": "user" },
      "response_status": 201,
      "response_id": 14,
      "error": null,
      "timestamp": "2026-02-24T15:31:05Z"
    }
  ]
}
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| `entity` | string | 实体名称（如 "Product", "User"） |
| `item_index` | number | 该实体的第几条数据（从 1 开始） |
| `status` | string | `"success"` / `"failed"` / `"skipped"` |
| `api` | string | 调用的 API 端点（如 "POST /api/products"） |
| `request_body_summary` | object | 请求体摘要（隐去敏感字段如 password） |
| `response_status` | number | HTTP 响应状态码 |
| `response_id` | any | 成功时返回的实体 ID（number/string/null） |
| `error` | any | 失败时的错误信息（response body 或 null） |
| `timestamp` | string | ISO 8601 时间戳 |

### 7.2 forge-data.json

已创建数据清单，供 clean 模式使用：

```json
{
  "_meta": {
    "forged_at": "2026-02-24T15:45:00Z",
    "base_url": "http://localhost:3000",
    "total_created": 128
  },
  "created": [
    {
      "entity": "Category",
      "id": 1,
      "api": "POST /api/categories",
      "delete_api": "DELETE /api/categories/1",
      "created_at": "2026-02-24T15:30:01Z",
      "order": 1
    },
    {
      "entity": "Category",
      "id": 2,
      "api": "POST /api/categories",
      "delete_api": "DELETE /api/categories/2",
      "created_at": "2026-02-24T15:30:02Z",
      "order": 2
    },
    {
      "entity": "User",
      "id": 10,
      "api": "POST /api/users",
      "delete_api": "DELETE /api/users/10",
      "created_at": "2026-02-24T15:30:05Z",
      "order": 3
    },
    {
      "entity": "Product",
      "id": 100,
      "api": "POST /api/products",
      "delete_api": "DELETE /api/products/100",
      "depends_on": [1],
      "created_at": "2026-02-24T15:31:00Z",
      "order": 4
    },
    {
      "entity": "Order",
      "id": 1001,
      "api": "POST /api/orders",
      "delete_api": "DELETE /api/orders/1001",
      "depends_on": [10, 100],
      "created_at": "2026-02-24T15:35:00Z",
      "order": 5
    }
  ]
}
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| `entity` | string | 实体名称 |
| `id` | any | 创建后返回的 ID |
| `api` | string | 创建时使用的 API |
| `delete_api` | string | 清理时要调用的 DELETE API（含 ID） |
| `depends_on` | array | 该记录依赖的父实体 ID（可选） |
| `created_at` | string | 创建时间 |
| `order` | number | 创建顺序编号（clean 时逆序使用） |

### 7.3 api-gaps.json（更新版）

合并 Step 0 静态分析 + Step 4 运行时检测的完整缺口报告：

```json
{
  "_meta": {
    "generated_at": "2026-02-24T15:45:00Z",
    "static_gaps": 3,
    "runtime_gaps": 2,
    "total_gaps": 5,
    "resolved_gaps": 1
  },
  "gaps": [
    {
      "gap_id": "GAP-SA-001",
      "source": "static_analysis",
      "entity": "Banner",
      "gap_type": "API_GAP: 无创建接口",
      "detail": "Banner 模型存在但未发现 POST /api/banners 端点",
      "detected_at": "2026-02-24T14:00:00Z",
      "status": "open"
    },
    {
      "gap_id": "GAP-RT-001",
      "source": "runtime",
      "entity": "Product",
      "gap_type": "API_GAP: 参数不匹配",
      "api": "POST /api/products",
      "http_status": 400,
      "detail": "category_id must be integer, got string",
      "request_body_sample": { "name": "日式陶瓷杯", "category_id": "cat-003" },
      "detected_at": "2026-02-24T15:30:15Z",
      "status": "open"
    },
    {
      "gap_id": "GAP-RT-002",
      "source": "runtime",
      "entity": "Product",
      "gap_type": "API_GAP: 上传大小限制",
      "api": "POST /api/upload",
      "http_status": 413,
      "detail": "图片文件超过服务端上传大小限制 (2MB)",
      "detected_at": "2026-02-24T15:32:00Z",
      "status": "open"
    }
  ],
  "resolved": [
    {
      "gap_id": "GAP-SA-003",
      "source": "static_analysis",
      "entity": "User",
      "gap_type": "API_GAP: 无创建接口",
      "detail": "Step 0 未发现 POST /api/users，但 Step 4 实际调用成功",
      "resolved_at": "2026-02-24T15:30:05Z",
      "resolution": "static_analysis_false_positive"
    }
  ]
}
```

---

## 8. 报告输出

灌入完成后（或 clean 完成后），**必须在对话中直接输出完整的报告摘要**。不能只说 "灌入已完成" 或 "数据已创建"。

### 8.1 灌入报告模板（full / fill 模式）

参考 `commands/demo-forge.md` 中定义的报告模板，必须包含以下内容：

```
## 演示数据灌入报告

> 执行时间: {时间}
> 执行模式: {full/fill}
> 应用地址: {URL}
> 行业画像: {行业关键词}

### 灌入总览

| 实体 | 计划数 | 成功 | 失败 | 跳过 |
|------|--------|------|------|------|
| Category | 5 | 5 | 0 | 0 |
| User | 15 | 15 | 0 | 0 |
| Product | 50 | 48 | 2 | 0 |
| Order | 100 | 95 | 3 | 2 |
| **合计** | **170** | **163** | **5** | **2** |

### 图片素材

| 分类 | 已下载 | 上传成功 | 上传失败 |
|------|--------|----------|----------|
| avatars | 15 | 15 | 0 |
| products | 50 | 48 | 2 |
| banners | 5 | 5 | 0 |
| **合计** | **70** | **68** | **2** |

### API 缺口

- Product: `API_GAP: 参数不匹配` — POST /api/products 返回 400 "category_id must be integer"
- Upload: `API_GAP: 上传大小限制` — POST /api/upload 返回 413，2 张图片超过 2MB 限制
- Banner: `API_GAP: 无创建接口` — 未发现 POST /api/banners（静态分析）

### 灌入失败详情

- Product #3 "日式陶瓷杯": POST /api/products → 400 "category_id must be integer"
- Product #27 "北欧简约台灯": POST /api/products → 400 "category_id must be integer"
- Order #45: POST /api/orders → 500 Internal Server Error
- Order #67: POST /api/orders → 500 Internal Server Error
- Order #89: POST /api/orders → 500 Internal Server Error

### 下一步
1. 修复 API 缺口（如需要）
2. 重新灌入失败的数据: `/demo-forge fill`
3. 检查灌入的数据是否符合预期
4. 不需要时清理: `/demo-forge clean`
5. 配合功能审计交叉验证: `/feature-audit`

> 灌入日志: `.allforai/seed-forge/forge-log.json`
> 数据清单: `.allforai/seed-forge/forge-data.json`
> API 缺口: `.allforai/seed-forge/api-gaps.json`
```

### 8.2 清理报告模板（clean 模式）

```
## 演示数据清理报告

> 执行时间: {时间}
> 执行模式: clean
> 应用地址: {URL}

### 清理结果

| 实体 | 已删除 | 已不存在 | 失败 |
|------|--------|----------|------|
| Order | 95 | 3 | 2 |
| Product | 48 | 0 | 0 |
| User | 15 | 0 | 0 |
| Category | 5 | 0 | 0 |
| **合计** | **163** | **3** | **2** |

### 删除失败详情

- Order #1045: DELETE /api/orders/1045 → 403 "cannot delete completed order"
- Order #1067: DELETE /api/orders/1067 → 403 "cannot delete completed order"

### 注意
- 已下载的图片素材未被删除（位于 `.allforai/seed-forge/assets/`）
- 如需删除素材: `rm -rf .allforai/seed-forge/assets/`

### 下一步
1. 修复失败项后重新清理: `/demo-forge clean`
2. 重新灌入: `/demo-forge` 或 `/demo-forge fill`
```

### 8.3 报告输出的强制要求

**关键：报告摘要必须包含具体的数据列表和失败详情。**

- 必须逐实体列出灌入统计（不能只给总数）
- 必须逐条列出灌入失败的详情（实体、数据标识、失败原因、API 响应）
- 必须逐条列出 API 缺口（不能只说 "发现了 N 个缺口"）
- 用户看完报告就能知道：哪些数据灌成功了、哪些失败了、API 哪里有缺口
