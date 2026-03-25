## 报告格式参考

> 本文档定义 fieldcheck 的输出文件格式和对话中必须展示的报告摘要模板。

### 输出文件结构

```
.allforai/deadhunt/output/field-analysis/
├── field-profile.json    ← 各层提取到的原始字段清单
├── field-mapping.json    ← 跨层映射关系（匹配结果）
├── field-issues.json     ← 发现的问题列表（含矩阵交叉验证结果）
├── field-matrix.json     ← 全链路存在矩阵（仅 full/backend scope 生成）
└── field-report.md       ← 人类可读的完整报告
```

---

### field-profile.json

各层字段提取的原始结果，合并为一个文件：

```json
{
  "generated_at": "2026-02-17T10:30:00Z",
  "project": "XX电商平台",
  "tech_stack": {
    "frontend": "vue",
    "backend": "java-spring",
    "orm": "jpa",
    "db": "mysql"
  },
  "layers": {
    "L4": {
      "source": "jpa_entity",
      "tables": [
        {
          "name": "users",
          "model_name": "User",
          "file": "server/src/entities/User.java:15",
          "columns": [
            { "name": "id", "type": "int", "primary": true },
            { "name": "user_name", "type": "varchar", "nullable": false },
            { "name": "email", "type": "varchar", "nullable": false, "unique": true },
            { "name": "avatar_url", "type": "varchar", "nullable": true },
            { "name": "created_at", "type": "datetime", "nullable": false }
          ]
        },
        {
          "name": "orders",
          "model_name": "Order",
          "file": "server/src/entities/Order.java:12",
          "columns": [
            { "name": "id", "type": "int", "primary": true },
            { "name": "user_id", "type": "int", "nullable": false },
            { "name": "order_amount", "type": "decimal", "nullable": false },
            { "name": "total_price", "type": "decimal", "nullable": false },
            { "name": "status", "type": "varchar", "nullable": false }
          ]
        }
      ]
    },
    "L3": {
      "source": "java_entity",
      "entities": [
        {
          "name": "User",
          "file": "server/src/entities/User.java:15",
          "table": "users",
          "fields": [
            { "name": "id", "type": "Long", "column": "id", "primary": true },
            { "name": "userName", "type": "String", "column": "user_name" },
            { "name": "email", "type": "String", "column": "email" },
            { "name": "avatarUrl", "type": "String", "column": "avatar_url" },
            { "name": "createdAt", "type": "LocalDateTime", "column": "created_at" }
          ]
        },
        {
          "name": "Order",
          "file": "server/src/entities/Order.java:12",
          "table": "orders",
          "fields": [
            { "name": "id", "type": "Long", "column": "id", "primary": true },
            { "name": "userId", "type": "Long", "column": "user_id" },
            { "name": "orderAmount", "type": "BigDecimal", "column": "order_amount" },
            { "name": "totalPrice", "type": "BigDecimal", "column": "total_price" },
            { "name": "status", "type": "String", "column": "status" }
          ]
        }
      ]
    },
    "L2": {
      "source": "dto_classes",
      "endpoints": [
        {
          "method": "GET",
          "path": "/api/users",
          "file": "server/src/dto/UserResponse.java:8",
          "request": [
            { "name": "keyword", "type": "string", "in": "query" },
            { "name": "page", "type": "number", "in": "query" }
          ],
          "response": [
            { "name": "id", "type": "number" },
            { "name": "userName", "type": "string" },
            { "name": "email", "type": "string" },
            { "name": "displayName", "type": "string" },
            { "name": "createdBy", "type": "string" },
            { "name": "createdAt", "type": "string" }
          ]
        },
        {
          "method": "GET",
          "path": "/api/orders",
          "file": "server/src/dto/OrderResponse.java:6",
          "request": [
            { "name": "status", "type": "string", "in": "query" }
          ],
          "response": [
            { "name": "id", "type": "number" },
            { "name": "orderAmout", "type": "number" },
            { "name": "totalPrice", "type": "number" },
            { "name": "status", "type": "string" }
          ]
        }
      ]
    },
    "L1": {
      "source": "vue_components",
      "pages": [
        {
          "path": "/users/list",
          "component": "UserList",
          "file": "src/views/user/UserList.vue",
          "fields": [
            { "name": "userName", "context": "table-column", "label": "用户名", "line": 45 },
            { "name": "email", "context": "table-column", "label": "邮箱", "line": 46 },
            { "name": "avatar", "context": "template-binding", "label": null, "line": 32 },
            { "name": "nickname", "context": "table-column", "label": "昵称", "line": 48 }
          ]
        },
        {
          "path": "/orders/list",
          "component": "OrderList",
          "file": "src/views/order/OrderList.vue",
          "fields": [
            { "name": "orderAmount", "context": "table-column", "label": "订单金额", "line": 38 },
            { "name": "totalPrice", "context": "table-column", "label": "总价", "line": 52 },
            { "name": "status", "context": "table-column", "label": "状态", "line": 55 }
          ]
        }
      ]
    }
  },
  "stats": {
    "L4_fields": 172,
    "L3_fields": 178,
    "L2_fields": 189,
    "L1_fields": 156,
    "modules_analyzed": 12
  }
}
```

---

### field-mapping.json

跨层匹配结果：

```json
{
  "generated_at": "2026-02-17T10:30:00Z",
  "mappings_by_module": [
    {
      "module": "user",
      "table": "users",
      "entity": "User",
      "field_mappings": [
        {
          "field_key": "userName",
          "L4": { "name": "user_name", "type": "varchar", "file": "prisma/schema.prisma:14" },
          "L3": { "name": "userName", "type": "String", "file": "server/src/entities/User.java:22" },
          "L2": { "name": "userName", "type": "string", "file": "server/src/dto/UserResponse.java:8" },
          "L1": { "name": "userName", "type": null, "file": "src/views/user/UserList.vue:45", "context": "table-column", "label": "用户名" },
          "match_type": "style_equivalent",
          "status": "pass"
        },
        {
          "field_key": "email",
          "L4": { "name": "email", "type": "varchar", "file": "prisma/schema.prisma:16" },
          "L3": { "name": "email", "type": "String", "file": "server/src/entities/User.java:24" },
          "L2": { "name": "email", "type": "string", "file": "server/src/dto/UserResponse.java:10" },
          "L1": { "name": "email", "type": null, "file": "src/views/user/UserList.vue:46", "context": "table-column", "label": "邮箱" },
          "match_type": "exact",
          "status": "pass"
        },
        {
          "field_key": "avatar",
          "L4": { "name": "avatar_url", "type": "varchar", "file": "prisma/schema.prisma:18" },
          "L3": { "name": "avatarUrl", "type": "String", "file": "server/src/entities/User.java:28" },
          "L2": null,
          "L1": { "name": "avatar", "type": null, "file": "src/views/user/UserList.vue:32", "context": "template-binding" },
          "match_type": null,
          "status": "issue",
          "issue": { "type": "GHOST", "severity": "critical", "detail": "L1 uses 'avatar' but L2 response does not include this field" }
        }
      ]
    },
    {
      "module": "order",
      "table": "orders",
      "entity": "Order",
      "field_mappings": [
        {
          "field_key": "orderAmount",
          "L4": { "name": "order_amount", "type": "decimal", "file": "prisma/schema.prisma:34" },
          "L3": { "name": "orderAmount", "type": "BigDecimal", "file": "server/src/entities/Order.java:34" },
          "L2": { "name": "orderAmout", "type": "number", "file": "server/src/dto/OrderDTO.java:23" },
          "L1": { "name": "orderAmount", "type": null, "file": "src/views/order/OrderList.vue:38", "context": "table-column", "label": "订单金额" },
          "match_type": "typo",
          "status": "issue",
          "issue": { "type": "TYPO", "severity": "critical", "detail": "L2 'orderAmout' is a misspelling of L3 'orderAmount' (edit distance = 1)" }
        },
        {
          "field_key": "totalPrice",
          "L4": { "name": "total_price", "type": "decimal", "file": "prisma/schema.prisma:35" },
          "L3": { "name": "totalPrice", "type": "BigDecimal", "file": "server/src/entities/Order.java:36" },
          "L2": { "name": "totalPrice", "type": "number", "file": "server/src/dto/OrderResponse.java:20" },
          "L1": { "name": "totalPrice", "type": null, "file": "src/views/order/OrderList.vue:52", "context": "table-column", "label": "总价" },
          "match_type": "style_equivalent",
          "status": "pass"
        }
      ]
    }
  ],
  "summary": {
    "L1_L2": { "total": 156, "pass": 148, "issues": 8 },
    "L2_L3": { "total": 189, "pass": 185, "issues": 4 },
    "L3_L4": { "total": 178, "pass": 176, "issues": 2 }
  }
}
```

---

### field-issues.json

所有问题的结构化列表：

```json
{
  "generated_at": "2026-02-17T10:30:00Z",
  "issues": [
    {
      "id": "FC-001",
      "type": "GHOST",
      "severity": "critical",
      "module": "user",
      "field": "avatar",
      "layers": "L1↔L2",
      "detail": "前端 UserList.vue:32 使用 `avatar` 字段显示头像，但 GET /api/users 的响应（UserResponse.java）不包含此字段，页面将显示 undefined",
      "source_file": "src/views/user/UserList.vue:32",
      "target_file": "server/src/dto/UserResponse.java",
      "suggestion": "在 UserResponse 中添加 avatar 字段，或修改前端使用 avatarUrl 与 Entity 保持一致"
    },
    {
      "id": "FC-002",
      "type": "TYPO",
      "severity": "critical",
      "module": "order",
      "field": "orderAmout → orderAmount",
      "layers": "L2↔L3",
      "detail": "OrderDTO.java:23 中字段名为 `orderAmout`（缺少字母 n），而 Entity 中为 `orderAmount`，导致序列化时字段值丢失",
      "source_file": "server/src/dto/OrderDTO.java:23",
      "target_file": "server/src/entities/Order.java:34",
      "suggestion": "修正 DTO 中的拼写：orderAmout → orderAmount"
    },
    {
      "id": "FC-003",
      "type": "STALE",
      "severity": "warning",
      "module": "user",
      "field": "createdBy",
      "layers": "L2↔L1",
      "detail": "API 响应中返回 `createdBy` 字段（UserResponse.java:12），但前端所有用户相关页面均未使用此字段，属于冗余传输",
      "source_file": "server/src/dto/UserResponse.java:12",
      "target_file": null,
      "suggestion": "如无需展示，从 UserResponse 中移除以减少传输量；或在用户详情页中展示创建者信息"
    },
    {
      "id": "FC-004",
      "type": "GAP",
      "severity": "critical",
      "module": "product",
      "field": "seoKeywords",
      "layers": "L3↔L2",
      "detail": "Product Entity 有 `seoKeywords` 字段（对应 DB 列 `seo_keywords`），但 ProductResponse、ProductDetailResponse 等所有 DTO 均未暴露此字段，前端无法获取 SEO 关键词数据",
      "source_file": "server/src/entities/Product.java:56",
      "target_file": null,
      "suggestion": "在 ProductDetailResponse 中添加 seoKeywords 字段，使前端编辑页面可以管理 SEO 关键词"
    },
    {
      "id": "FC-005",
      "type": "SEMANTIC",
      "severity": "warning",
      "module": "user",
      "field": "nickname vs displayName",
      "layers": "L1↔L2",
      "detail": "前端 UserProfile.vue:18 使用 `nickname` 字段，API 返回 `displayName` 字段。语义可能相同（都表示用户显示名），但无法自动确认是否指代同一数据",
      "source_file": "src/views/user/UserProfile.vue:18",
      "target_file": "server/src/dto/UserResponse.java:15",
      "suggestion": "确认二者是否指代同一字段。如果是，统一命名为 displayName 或 nickname",
      "needs_confirmation": true
    },
    {
      "id": "FC-006",
      "type": "TYPE",
      "severity": "warning",
      "module": "order",
      "field": "totalPrice",
      "layers": "L2↔L1",
      "detail": "API 返回 totalPrice 类型为 number（后端 BigDecimal），但前端表格列直接渲染未做格式化，可能显示为长浮点数（如 99.90000000001）",
      "source_file": "server/src/dto/OrderResponse.java:20",
      "target_file": "src/views/order/OrderList.vue:52",
      "suggestion": "前端列渲染时添加金额格式化（如 toFixed(2)、currency filter 或 Intl.NumberFormat）"
    },
    {
      "id": "FC-007",
      "note": "与 FC-001 为同一字段问题，经 Step 3.5 矩阵交叉验证升级",
      "type": "GAP",
      "severity": "critical",
      "module": "user",
      "field": "avatar",
      "layers": "L1↔L2",
      "detail": "前端 UserList.vue:32 使用 `avatar` 字段，API 未返回此字段",
      "source_file": "src/views/user/UserList.vue:32",
      "target_file": "server/src/dto/UserResponse.java",
      "suggestion": "在 UserResponse 中添加 avatar 字段",
      "matrix_pattern": "DTO_SKIP",
      "cross_layer_evidence": "字段在 L1/L3/L4 均存在，仅 L2(DTO) 缺失，高置信度为 DTO 遗漏"
    },
    {
      "id": "FC-008",
      "type": "DB_ORPHAN",
      "severity": "warning",
      "module": "user",
      "field": "old_email",
      "layers": "L4",
      "detail": "数据库 users 表有 old_email 列，但所有上层（Entity/API/UI）均未引用",
      "source_file": null,
      "target_file": "users.old_email (DB column)",
      "suggestion": "确认是否为废弃列，如是则执行 migration 删除",
      "matrix_pattern": "DB_ORPHAN",
      "cross_layer_evidence": "字段仅在 L4(DB) 存在，所有上层均未引用，可能是废弃列",
      "needs_confirmation": true
    }
  ],
  "stats": {
    "total": 8,
    "critical": 4,
    "warning": 4,
    "needs_confirmation": 2,
    "matrix_enhanced": 2
  }
}
```

---

### field-matrix.json

全链路字段存在矩阵（仅 `full` 和 `backend` scope 生成）：

```json
{
  "generated_at": "2026-02-17T10:30:00Z",
  "scope": "full",
  "modules": {
    "user": {
      "fields": {
        "userName": { "L1": true, "L2": true, "L3": true, "L4": true, "pattern": "FULL_CHAIN" },
        "email": { "L1": true, "L2": true, "L3": true, "L4": true, "pattern": "FULL_CHAIN" },
        "avatar": { "L1": true, "L2": false, "L3": true, "L4": true, "pattern": "DTO_SKIP" },
        "password": { "L1": false, "L2": false, "L3": true, "L4": true, "pattern": "BACKEND_ONLY" },
        "oldEmail": { "L1": false, "L2": false, "L3": false, "L4": true, "pattern": "DB_ORPHAN" }
      },
      "pattern_summary": { "FULL_CHAIN": 10, "DTO_SKIP": 1, "BACKEND_ONLY": 2, "DB_ORPHAN": 1 }
    },
    "order": {
      "fields": {
        "orderAmount": { "L1": true, "L2": true, "L3": true, "L4": true, "pattern": "FULL_CHAIN" },
        "totalPrice": { "L1": true, "L2": true, "L3": true, "L4": true, "pattern": "FULL_CHAIN" },
        "refundNote": { "L1": true, "L2": true, "L3": false, "L4": true, "pattern": "ORM_SKIP" }
      },
      "pattern_summary": { "FULL_CHAIN": 16, "ORM_SKIP": 1, "UI_MISSING": 2 }
    }
  },
  "global_summary": {
    "total_fields": 87,
    "FULL_CHAIN": 65,
    "DTO_SKIP": 2,
    "ORM_SKIP": 1,
    "UI_MISSING": 8,
    "BACKEND_ONLY": 4,
    "DB_ORPHAN": 3,
    "COMPUTED": 3,
    "DTO_ONLY": 1
  }
}
```

---

### 对话中报告摘要模板（强制输出）

分析完成后，**必须**在对话中直接展示以下格式的完整报告。不能只说"报告已保存"或只给统计数字。

````
## 字段一致性检查报告

> 分析时间: {ISO timestamp}
> 分析范围: {模块数} 个模块, {scope} 模式
> 字段总数: L1={n} / L2={n} / L3={n} / L4={n}
> 技术栈: 前端 {framework} / 后端 {backend} / ORM {orm}

### 总览

| 层级对比 | 字段数 | 一致 | 不一致 | 覆盖率 |
|---------|--------|------|--------|--------|
| L1↔L2 (UI↔API)       | xxx | xxx | xxx | xx.x% |
| L2↔L3 (API↔Entity)   | xxx | xxx | xxx | xx.x% |
| L3↔L4 (Entity↔DB)    | xxx | xxx | xxx | xx.x% |

### 全链路矩阵总览（full/backend scope）

| 模块 | 总字段 | 全链路✅ | DTO_SKIP🔴 | ORM_SKIP🔴 | UI_MISSING🟡 | DB_ORPHAN🟡 | BACKEND_ONLY |
|------|--------|---------|-----------|-----------|-------------|------------|-------------|
| 用户管理 | 15 | 10 | 1 | 0 | 1 | 1 | 2 |
| 订单管理 | 22 | 16 | 0 | 1 | 2 | 0 | 3 |

### 🔴 严重问题 (Critical)

| # | 类型 | 模块 | 字段 | L1 | L2 | L3 | L4 | 位置 | 修复建议 |
|---|------|------|------|----|----|----|----|------|---------|
| FC-001 | GHOST (DTO_SKIP) | 用户管理 | avatar | ✅ | ❌ | ✅ | ✅ | UserList.vue:32 → UserResponse 无此字段 | DTO 添加 avatar 字段 |
| FC-002 | TYPO | 订单管理 | orderAmout | ✅ | ✅ | ✅ | ✅ | OrderDTO.java:23 | 修正为 orderAmount |
| FC-004 | GAP | 商品管理 | seoKeywords | ❌ | ❌ | ✅ | ✅ | Product.java:56 → 所有 DTO 未暴露 | ProductDetailResponse 添加 |

### 🟡 警告 (Warning)

| # | 类型 | 模块 | 字段 | 层级 | 位置 | 建议 |
|---|------|------|------|------|------|------|
| FC-003 | STALE | 用户管理 | createdBy | L2↔L1 | API 返回但前端未使用 | 移除或展示 |
| FC-005 | SEMANTIC | 用户管理 | nickname/displayName | L1↔L2 | 前端和 API 命名不同 | 确认是否同一字段 |
| FC-006 | TYPE | 订单管理 | totalPrice | L2↔L1 | number 未格式化 | 前端添加金额格式化 |

### ❓ 需人工确认

| # | 模块 | 字段 | 原因 |
|---|------|------|------|
| FC-005 | 用户管理 | nickname vs displayName | 语义可能相同但无法自动判定，需确认是否指代同一数据 |

### 字段热力图

| 模块 | 🔴 | 🟡 | 总问题 |
|------|-----|-----|--------|
| 用户管理 | 1 | 2 | 3 |
| 订单管理 | 1 | 1 | 2 |
| 商品管理 | 1 | 0 | 1 |
| 其他模块 | 0 | 0 | 0 |

### 下一步建议

1. 优先修复 🔴 Critical — 幽灵字段(GHOST)导致页面显示 undefined，拼写错误(TYPO)导致数据丢失
2. 对 ❓ 需确认项逐个告诉我是否为同一字段
3. STALE 字段建议在下次迭代中清理，减少 API 响应体积
4. 修复后重新运行 `/deadhunt:fieldcheck` 验证

> 完整报告: `.allforai/deadhunt/output/field-analysis/field-report.md`
> 问题清单: `.allforai/deadhunt/output/field-analysis/field-issues.json`
> 字段映射: `.allforai/deadhunt/output/field-analysis/field-mapping.json`
> 字段矩阵: `.allforai/deadhunt/output/field-analysis/field-matrix.json`
````

**关键：摘要必须包含具体的问题列表和修复建议，不能只给统计数字。用户看完摘要就能知道出了什么问题、在哪里、怎么修。**
