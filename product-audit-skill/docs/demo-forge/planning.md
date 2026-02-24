# Step 2: 数据规划 (Data Planning)

> 基于 project-analysis.json（数据模型 + API 映射）和 industry-profile.json（行业画像），为每个实体生成完整的数据计划：条数、字段值风格、依赖顺序、图片需求。

---

## 1. 数据计划生成 (Plan Generation)

对 `project-analysis.json` 中识别出的每个 entity，逐一生成数据计划条目：

### 处理流程

```
for each entity in project-analysis.json:
    1. 确定 count        → 参考 industry-profile.json 的 data_volume 建议
    2. 绑定 create_api   → 从 project-analysis.json 的 API 映射中获取 POST 端点
    3. 解析 depends_on   → 分析外键字段，确定前置依赖实体
    4. 设计 fields       → 结合 industry-profile.json 的风格，为每个字段指定生成策略
```

### 每个实体的计划结构

| 字段 | 说明 | 来源 |
|------|------|------|
| `model` | 实体名称 | project-analysis.json |
| `count` | 计划生成条数 | industry-profile.json 建议 + 用户可覆盖 |
| `create_api` | POST 端点路径 | project-analysis.json 的 API 映射 |
| `upload_api` | 文件上传端点（如有） | project-analysis.json 的 API 映射 |
| `depends_on` | 前置依赖实体列表 | 外键分析 |
| `fields` | 每个字段的生成规则 | industry-profile.json 风格 + 字段类型推断 |

### 依赖解析规则

外键字段的识别方式（按技术栈）：

| 技术栈 | 外键标识 | 示例 |
|--------|----------|------|
| GORM | `gorm:"foreignKey:..."` 或 `XxxID uint` | `CategoryID uint` → depends_on Category |
| Ent | `edge.To()` / `edge.From()` | `edge.From("category")` → depends_on Category |
| TypeORM | `@ManyToOne()` / `@JoinColumn()` | `@ManyToOne(() => Category)` → depends_on Category |
| Prisma | `@relation` 字段 | `category Category @relation(...)` → depends_on Category |
| Django | `ForeignKey()` / `ManyToManyField()` | `category = ForeignKey(Category)` → depends_on Category |
| SQLAlchemy | `ForeignKey()` / `relationship()` | `Column(ForeignKey('category.id'))` → depends_on Category |
| Mongoose | `{ type: Schema.Types.ObjectId, ref: 'X' }` | `ref: 'Category'` → depends_on Category |

---

## 2. 依赖排序 (Dependency Sorting)

实体之间存在外键引用关系，必须先创建被引用的实体。使用 **拓扑排序 (Topological Sort)** 确定创建顺序。

### 算法逻辑

```
1. 构建有向图：节点 = 实体，边 = depends_on 关系
   - Product depends_on Category → 边: Category → Product
   - Order depends_on User → 边: User → Order
   - Order depends_on Product → 边: Product → Order

2. 计算每个节点的入度 (in-degree)
   - Category: 0（无人依赖）
   - User: 0（无人依赖）
   - Product: 1（依赖 Category）
   - Order: 2（依赖 User + Product）

3. 将入度为 0 的节点加入队列

4. BFS 逐层弹出：
   Layer 0: [Category, User]        ← 无依赖，可并行
   Layer 1: [Product]               ← Category 创建完毕后
   Layer 2: [Order]                 ← User + Product 创建完毕后

5. 输出 creation_order: ["Category", "User", "Product", "Order"]
```

### 可视化示例

```
电商项目依赖图:

  Category ─────┐
                 ├──→ Product ──┐
  User ─────────┤              ├──→ Order ──→ OrderItem
                 │              │
  Brand ────────┘              │
                                │
  Coupon ──────────────────────┘

拓扑排序结果:
  Layer 0: Category, User, Brand, Coupon     ← 无依赖，并行创建
  Layer 1: Product                           ← 依赖 Category + Brand
  Layer 2: Order                             ← 依赖 User + Product + Coupon
  Layer 3: OrderItem                         ← 依赖 Order + Product

creation_order: ["Category", "User", "Brand", "Coupon", "Product", "Order", "OrderItem"]
```

### 循环依赖处理

如果检测到循环依赖（A depends_on B, B depends_on A），处理策略：

1. **报告给用户** — 说明哪些实体形成了循环
2. **建议方案** — 先创建其中一个实体（不填外键字段），再创建另一个，最后通过 PUT 补上外键
3. **需要用户确认** — 由用户决定先创建哪个

### 并行标记

同一 Layer 内的实体互不依赖，可以并行创建。`forge-plan.json` 中使用 `parallel_group` 标记：

```json
{
  "creation_order": ["Category", "User", "Brand", "Coupon", "Product", "Order"],
  "parallel_groups": [
    { "layer": 0, "entities": ["Category", "User", "Brand", "Coupon"] },
    { "layer": 1, "entities": ["Product"] },
    { "layer": 2, "entities": ["Order"] }
  ]
}
```

---

## 3. 字段值生成规则 (Field Value Generation Rules)

根据字段类型和行业画像，为每个字段设计生成策略。以下是完整的字段类型映射表：

| 字段类型 | 生成策略 | 示例 |
|----------|----------|------|
| String (name) | 从 industry-profile.json 提取行业风格名称，组合品类 + 修饰词 + 材质/特征 | "日式手工陶瓷杯"、"北欧简约台灯" |
| String (description) | 生成 2-3 句行业相关描述，包含材质/功能/卖点关键词 | "精选高岭土，1300度高温烧制，釉面细腻温润。手工拉坯成型，每件都是独一无二的艺术品。" |
| Number (price) | 从 industry-profile.json 获取价格区间，使用正态分布集中在中位数附近 | 29.9, 89, 159, 499（电商）; 9.9, 29, 99（月订阅） |
| Number (quantity/stock) | 合理库存范围，避免极端值 | 10-9999，大部分集中在 50-500 |
| Image/File field | 构建图片搜索关键词（行业 + 品类 + 风格），指定需要的图片数量 | query: "product ceramic photography", count: 50 |
| Foreign key | 引用已创建的父实体 ID，均匀或按权重分配 | `category_id` → 随机选取已创建的 Category.id |
| Enum/Status | 按权重分布选取枚举值，模拟真实数据分布 | `["active"x8, "inactive"x2]` → 80% active, 20% inactive |
| DateTime | 生成最近数周内的日期，均匀分布，避免全部同一天 | "2024-01-01" 到 "2024-01-15"，各天均匀分布 |
| Email | 基于 name 字段生成拼音/英文名 + 固定域名 | "zhangming@example.com"、"lixiaohong@example.com" |
| Phone | 根据行业画像的 locale 生成对应格式号码 | 中国: "138xxxx1234"；美国: "+1 (555) xxx-xxxx" |
| Boolean | 按权重分布，模拟真实业务比例 | `true x7, false x3` → 70% true, 30% false |
| URL | 使用占位 URL 或按模式生成 | "https://example.com/products/001" |

### 各字段类型详细规则

#### String (name) — 名称字段

```
输入:
  - industry_profile.name_style: "日式陶瓷咖啡杯套装"
  - industry_profile.name_components: ["风格", "材质", "品类", "规格"]
  - industry_profile.examples: ["日式手工陶瓷杯", "北欧简约玻璃花瓶"]

生成策略:
  1. 从行业画像提取名称组件词库
  2. 按 "{风格} + {材质/特征} + {品类} + {规格}" 模式组合
  3. 确保每个名称唯一（不重复）
  4. 长度控制在 5-20 个字符

输出示例 (电商-家居):
  "日式手工陶瓷杯"
  "北欧简约实木置物架"
  "复古黄铜床头灯"
  "ins风棉麻桌布"
```

#### Number (price) — 价格字段

```
输入:
  - industry_profile.price_range: [19.9, 999]
  - industry_profile.price_distribution: "normal"

生成策略:
  1. 使用正态分布，均值 = (min + max) / 2，标准差 = (max - min) / 4
  2. 截断到 [min, max] 范围内
  3. 保留一位小数，尾数偏好 .9 / .0（模拟真实定价）
  4. 不同品类可有不同价格区间

输出示例:
  29.9, 59.0, 89.9, 129.0, 159.9, 269.0, 499.0
```

#### Foreign key — 外键字段

```
生成策略:
  1. 从已创建的父实体 ID 池中选取
  2. 默认均匀分布（每个父实体被引用相近次数）
  3. 支持权重分布（某些分类下的产品更多）
  4. 确保每个父实体至少被引用一次（避免空分类）

示例:
  已创建 Category: [id=1 "家居", id=2 "厨具", id=3 "文具"]
  Product.category_id 分配:
    id=1 → 20 个产品
    id=2 → 18 个产品
    id=3 → 12 个产品
```

#### Enum/Status — 枚举字段

```
生成策略:
  1. 识别枚举值列表（从代码或 API schema 中提取）
  2. 按业务合理性分配权重
  3. 常见分布模式:
     - 状态字段: active(80%), inactive(15%), banned(5%)
     - 角色字段: user(80%), admin(10%), moderator(10%)
     - 订单状态: completed(40%), pending(30%), shipped(20%), cancelled(10%)

示例:
  status: ["active", "active", "active", "active", "active", "active", "active", "active", "inactive", "inactive"]
  → 实际效果: 80% active, 20% inactive
```

#### DateTime — 日期时间字段

```
生成策略:
  1. 时间范围: 最近 2-4 周（看起来像活跃使用中）
  2. 均匀分布在范围内，避免集中在同一天
  3. 时间部分: 工作时间（9:00-18:00）为主，少量晚间
  4. 按实体逻辑排序: 创建时间 < 更新时间 < 完成时间
  5. 关联实体时间一致: Order.created_at > User.created_at

示例:
  created_at 分布: "2024-01-01T09:23:00Z" ... "2024-01-15T16:45:00Z"
  updated_at: 每条 created_at + random(1h ~ 72h)
```

---

## 4. 图片需求汇总 (Image Requirements Aggregation)

从所有实体的字段计划中提取图片需求，汇总为统一的图片采集清单。

### 汇总流程

```
1. 遍历 forge-plan.json 中所有实体
2. 识别 Image/File 类型字段
3. 按实体/用途分组
4. 计算总数 + 明细
5. 为每组生成搜索关键词
```

### 汇总表示例

```
图片需求汇总:

| 实体 | 字段 | 用途 | 数量 | 搜索关键词 |
|------|------|------|------|------------|
| User | avatar | 用户头像 | 15 | "portrait professional headshot" |
| Product | image | 商品主图 | 50 | "product {category} photography white background" |
| Product | gallery | 商品详情图 | 150 | "product {category} detail lifestyle" |
| Category | icon | 分类图标 | 10 | "{category_name} icon flat design" |
| Banner | image | 首页轮播图 | 5 | "ecommerce banner promotion {industry}" |
| Article | cover | 文章封面 | 30 | "blog cover {topic} photography" |

总计: 260 张
```

### 关键词构建规则

图片搜索关键词的构建考虑以下因素：

| 因素 | 示例 | 说明 |
|------|------|------|
| 行业 | "ecommerce", "education" | 来自 industry-profile.json |
| 品类 | "ceramic", "furniture" | 来自实体的 category 字段 |
| 风格 | "photography", "flat design" | 来自 industry-profile.json 的 image_style |
| 用途 | "product", "portrait", "banner" | 来自字段语义 |
| 背景 | "white background", "lifestyle" | 商品图常用白底，场景图用 lifestyle |

```
关键词组合模板:
  商品图: "product {category} photography {background}"
  头像: "portrait professional {style}"
  Banner: "{industry} banner {occasion}"
  分类图: "{category} icon {style}"
```

---

## 5. 数据量建议 (Data Volume Recommendations)

根据实体类型和行业特征，给出默认数据量建议。用户可覆盖所有数字。

### 默认数据量

| 实体类型 | 典型实体 | 建议条数 | 理由 |
|----------|----------|----------|------|
| **核心业务实体** | Product, Course, Project | 30 - 80 | 演示需要足够的浏览感，列表页至少 2-3 页 |
| **支撑分类实体** | Category, Tag, Brand | 5 - 15 | 太少显得空，太多分散注意力 |
| **用户实体** | User, Member, Customer | 10 - 30 | 需要看起来有多个活跃用户 |
| **交易记录** | Order, Payment, Booking | 100 - 300 | 交易记录多才像活跃系统 |
| **内容实体** | Post, Article, Comment | 50 - 200 | 社区/博客类需要充足内容 |
| **配置实体** | Setting, Config, Role | 3 - 10 | 配置项少量即可 |
| **关联实体** | OrderItem, CartItem | 随主实体 x2~x5 | 每个 Order 平均 2-5 个 Item |

### 按行业调整

| 行业 | 核心实体量 | 用户量 | 交易量 | 内容量 |
|------|------------|--------|--------|--------|
| 电商 | Product: 50+ | User: 20+ | Order: 200+ | Review: 100+ |
| SaaS | Project: 10+ | Member: 15+ | — | Task: 100+ |
| 教育 | Course: 30+ | Student: 25+ | Enrollment: 150+ | Lesson: 100+ |
| 餐饮 | Dish: 40+ | Customer: 15+ | Order: 300+ | — |
| 内容平台 | — | Author: 10+ | — | Post: 100+, Comment: 200+ |
| 医疗 | — | Patient: 20+ | Appointment: 100+ | Record: 50+ |

### 用户覆盖机制

用户可在确认环节调整任何实体的数量：

```
Claude: "以下是数据量建议：
  - Product: 50
  - Category: 10
  - User: 20
  - Order: 200
  请确认或调整。"

用户: "Product 改成 30，Order 改成 100，其他 OK。"

Claude: "已更新。Product: 30, Order: 100。继续？"
```

---

## 6. 用户确认点 (User Confirmation)

Step 2 完成后，以结构化方式向用户展示完整数据计划，等待确认。

### 展示内容

**Part 1: 实体清单 + 数据量**

```
数据计划:
┌────────────┬──────┬──────────────────────┬────────────────────┐
│ 实体        │ 条数 │ 创建 API              │ 依赖               │
├────────────┼──────┼──────────────────────┼────────────────────┤
│ Category   │ 10   │ POST /api/categories │ 无                 │
│ Brand      │ 8    │ POST /api/brands     │ 无                 │
│ User       │ 20   │ POST /api/users      │ 无                 │
│ Product    │ 50   │ POST /api/products   │ Category, Brand    │
│ Order      │ 200  │ POST /api/orders     │ User, Product      │
│ OrderItem  │ 600  │ POST /api/order-items │ Order, Product    │
└────────────┴──────┴──────────────────────┴────────────────────┘
创建顺序: Category → Brand → User → Product → Order → OrderItem
```

**Part 2: 字段值示例**

```
Product 字段示例:
  name:        "日式手工陶瓷杯" / "北欧简约实木置物架" / "复古黄铜床头灯"
  description: "精选高岭土，1300度高温烧制，釉面细腻温润。"
  price:       29.9 / 89.0 / 159.9 / 499.0
  status:      active(80%) / inactive(20%)
  category_id: → 引用已创建的 Category
  image:       → 搜索 "product ceramic photography"

User 字段示例:
  name:   "张明" / "李晓红" / "王建国"
  email:  "zhangming@example.com"
  phone:  "13812345678"
  avatar: → 搜索 "portrait professional headshot"
  role:   user(80%) / admin(10%) / moderator(10%)
```

**Part 3: 图片需求**

```
图片需求:
  用户头像:     20 张 (portrait professional headshot)
  商品主图:     50 张 (product {category} photography)
  分类图标:     10 张 ({category} icon)
  ──────────────────
  总计:         80 张
```

### 确认问题

向用户确认以下内容：

1. **数据量** — 每个实体的条数合适吗？需要增减吗？
2. **字段风格** — 名称、描述、价格范围满意吗？
3. **创建顺序** — 依赖关系正确吗？顺序对吗？
4. **图片需求** — 图片数量和搜索关键词合适吗？

```
Claude: "以上是完整数据计划，请确认或指出需要调整的地方：
  1. 数据量是否合适？
  2. 字段值风格是否满意？
  3. 创建顺序是否正确？
  4. 图片搜索关键词是否合适？"

用户确认后 → confirmed_by_user = true → 输出 forge-plan.json
```

---

## 7. 输出格式 (Output Schema)

Step 2 的输出为 `.allforai/seed-forge/forge-plan.json`，完整 JSON Schema 如下：

```json
{
  "meta": {
    "generated_at": "2026-02-24T10:30:00Z",
    "project": "my-ecommerce-app",
    "step": 2,
    "industry": "电商-家居",
    "based_on": {
      "project_analysis": ".allforai/seed-forge/project-analysis.json",
      "industry_profile": ".allforai/seed-forge/industry-profile.json"
    }
  },
  "entities": [
    {
      "model": "Category",
      "count": 10,
      "create_api": "POST /api/categories",
      "upload_api": null,
      "depends_on": [],
      "fields": {
        "name": {
          "type": "string",
          "style": "分类名称",
          "examples": ["家居日用", "厨房用品", "办公文具", "数码配件"],
          "unique": true
        },
        "description": {
          "type": "string",
          "style": "分类简介，1句话",
          "examples": ["精选家居日用好物，提升生活品质"]
        },
        "icon": {
          "type": "image",
          "image_query": "{category_name} icon flat design",
          "count": 10
        },
        "sort_order": {
          "type": "number",
          "range": [1, 10],
          "distribution": "sequential"
        }
      }
    },
    {
      "model": "Brand",
      "count": 8,
      "create_api": "POST /api/brands",
      "upload_api": null,
      "depends_on": [],
      "fields": {
        "name": {
          "type": "string",
          "style": "品牌名，中文或日式",
          "examples": ["无印良品", "网易严选", "小米有品", "造作"],
          "unique": true
        },
        "logo": {
          "type": "image",
          "image_query": "brand logo minimalist",
          "count": 8
        },
        "description": {
          "type": "string",
          "style": "品牌简介，1-2句",
          "examples": ["专注高品质家居生活用品，简约而不简单。"]
        }
      }
    },
    {
      "model": "User",
      "count": 20,
      "create_api": "POST /api/users",
      "upload_api": "POST /api/upload/avatar",
      "depends_on": [],
      "fields": {
        "name": {
          "type": "string",
          "style": "中文姓名",
          "examples": ["张明", "李晓红", "王建国", "赵雨涵"]
        },
        "email": {
          "type": "email",
          "pattern": "{name_pinyin}@example.com",
          "examples": ["zhangming@example.com", "lixiaohong@example.com"]
        },
        "phone": {
          "type": "phone",
          "locale": "zh-CN",
          "pattern": "1{3-9}xxxxxxxxx",
          "examples": ["13812345678", "15698765432"]
        },
        "avatar": {
          "type": "image",
          "image_query": "portrait professional headshot",
          "count": 20
        },
        "role": {
          "type": "enum",
          "values": ["admin", "user", "moderator"],
          "weights": [0.1, 0.8, 0.1]
        },
        "status": {
          "type": "enum",
          "values": ["active", "inactive"],
          "weights": [0.85, 0.15]
        },
        "created_at": {
          "type": "datetime",
          "range": ["2024-01-01T00:00:00Z", "2024-01-15T23:59:59Z"],
          "distribution": "uniform"
        }
      }
    },
    {
      "model": "Product",
      "count": 50,
      "create_api": "POST /api/products",
      "upload_api": "POST /api/upload/product-image",
      "depends_on": ["Category", "Brand"],
      "fields": {
        "name": {
          "type": "string",
          "style": "行业产品名: {风格}+{材质}+{品类}",
          "examples": ["日式手工陶瓷杯", "北欧简约实木置物架", "复古黄铜床头灯"],
          "unique": true
        },
        "description": {
          "type": "string",
          "style": "2-3句产品描述，包含材质/工艺/卖点",
          "examples": ["精选高岭土，1300度高温烧制，釉面细腻温润。手工拉坯成型，每件都是独一无二的艺术品。容量约300ml，适合咖啡、茶饮。"]
        },
        "price": {
          "type": "number",
          "range": [19.9, 999],
          "distribution": "normal",
          "decimal_places": 1,
          "tail_preference": [".9", ".0"]
        },
        "original_price": {
          "type": "number",
          "range": [29.9, 1299],
          "distribution": "derived",
          "derive_rule": "price * random(1.2, 1.8)"
        },
        "stock": {
          "type": "number",
          "range": [10, 9999],
          "distribution": "normal",
          "center": 200
        },
        "image": {
          "type": "image",
          "image_query": "product {category_name} photography white background",
          "count": 50
        },
        "gallery": {
          "type": "image_array",
          "image_query": "product {category_name} detail lifestyle",
          "count_per_item": 3,
          "total": 150
        },
        "category_id": {
          "type": "foreign_key",
          "ref": "Category.id",
          "distribution": "balanced",
          "min_per_parent": 2
        },
        "brand_id": {
          "type": "foreign_key",
          "ref": "Brand.id",
          "distribution": "balanced",
          "min_per_parent": 3
        },
        "status": {
          "type": "enum",
          "values": ["active", "inactive", "draft"],
          "weights": [0.7, 0.1, 0.2]
        },
        "is_featured": {
          "type": "boolean",
          "weights": { "true": 0.3, "false": 0.7 }
        },
        "created_at": {
          "type": "datetime",
          "range": ["2024-01-01T00:00:00Z", "2024-01-15T23:59:59Z"],
          "distribution": "uniform"
        }
      }
    },
    {
      "model": "Order",
      "count": 200,
      "create_api": "POST /api/orders",
      "upload_api": null,
      "depends_on": ["User", "Product"],
      "fields": {
        "order_no": {
          "type": "string",
          "pattern": "ORD{YYYYMMDD}{SEQ:6}",
          "examples": ["ORD20240108000001", "ORD20240112000042"],
          "unique": true
        },
        "user_id": {
          "type": "foreign_key",
          "ref": "User.id",
          "distribution": "weighted",
          "note": "部分用户多单，模拟活跃用户"
        },
        "total_amount": {
          "type": "number",
          "range": [19.9, 2999],
          "distribution": "derived",
          "derive_rule": "sum(order_items.price * quantity)"
        },
        "status": {
          "type": "enum",
          "values": ["pending", "paid", "shipped", "completed", "cancelled"],
          "weights": [0.1, 0.15, 0.2, 0.45, 0.1]
        },
        "payment_method": {
          "type": "enum",
          "values": ["wechat", "alipay", "card"],
          "weights": [0.5, 0.35, 0.15]
        },
        "shipping_address": {
          "type": "string",
          "style": "中国地址格式",
          "examples": ["北京市朝阳区建国路88号", "上海市浦东新区陆家嘴环路1000号"]
        },
        "created_at": {
          "type": "datetime",
          "range": ["2024-01-01T00:00:00Z", "2024-01-15T23:59:59Z"],
          "distribution": "uniform",
          "constraint": "> User.created_at"
        },
        "paid_at": {
          "type": "datetime",
          "distribution": "derived",
          "derive_rule": "created_at + random(1min, 30min)",
          "nullable_if": "status == 'pending' || status == 'cancelled'"
        }
      }
    },
    {
      "model": "OrderItem",
      "count": 600,
      "create_api": "POST /api/order-items",
      "upload_api": null,
      "depends_on": ["Order", "Product"],
      "fields": {
        "order_id": {
          "type": "foreign_key",
          "ref": "Order.id",
          "distribution": "grouped",
          "items_per_parent": { "min": 1, "max": 5, "avg": 3 }
        },
        "product_id": {
          "type": "foreign_key",
          "ref": "Product.id",
          "distribution": "weighted",
          "note": "热门商品被下单更多"
        },
        "quantity": {
          "type": "number",
          "range": [1, 5],
          "distribution": "normal",
          "center": 1
        },
        "unit_price": {
          "type": "number",
          "distribution": "derived",
          "derive_rule": "snapshot of Product.price at order time"
        }
      }
    }
  ],
  "creation_order": ["Category", "Brand", "User", "Product", "Order", "OrderItem"],
  "parallel_groups": [
    { "layer": 0, "entities": ["Category", "Brand", "User"] },
    { "layer": 1, "entities": ["Product"] },
    { "layer": 2, "entities": ["Order"] },
    { "layer": 3, "entities": ["OrderItem"] }
  ],
  "image_requirements": {
    "total": 238,
    "breakdown": {
      "category_icons": {
        "count": 10,
        "query_template": "{category_name} icon flat design",
        "sources": [
          { "type": "competitor", "priority": 1 },
          { "type": "unsplash", "query": "{category_name} icon flat design", "priority": 2 }
        ]
      },
      "brand_logos": {
        "count": 8,
        "query_template": "brand logo minimalist",
        "sources": [
          { "type": "competitor", "priority": 1 },
          { "type": "unsplash", "query": "brand logo minimalist", "priority": 2 }
        ]
      },
      "user_avatars": {
        "count": 20,
        "query_template": "portrait professional headshot",
        "sources": [
          { "type": "unsplash", "query": "portrait professional headshot", "priority": 1 }
        ]
      },
      "product_images": {
        "count": 50,
        "query_template": "product {category_name} photography white background",
        "sources": [
          { "type": "competitor", "priority": 1 },
          { "type": "unsplash", "query": "product {category_name} photography white background", "priority": 2 }
        ]
      },
      "product_gallery": {
        "count": 150,
        "query_template": "product {category_name} detail lifestyle",
        "sources": [
          { "type": "competitor", "priority": 1 },
          { "type": "unsplash", "query": "product {category_name} detail lifestyle", "priority": 2 }
        ]
      }
    }
  },
  "confirmed_by_user": false
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `meta.based_on` | object | 本计划的输入来源文件路径 |
| `entities[].model` | string | 实体名称，与 project-analysis.json 中的 model 名对应 |
| `entities[].count` | number | 计划生成条数，用户可覆盖 |
| `entities[].create_api` | string | HTTP method + path，来自 project-analysis.json |
| `entities[].upload_api` | string\|null | 图片/文件上传端点，无则 null |
| `entities[].depends_on` | string[] | 前置依赖实体列表（外键引用） |
| `entities[].fields` | object | 每个字段的生成规则 |
| `entities[].fields.*.type` | string | 字段类型: string / number / image / foreign_key / enum / datetime / email / phone / boolean / url |
| `entities[].fields.*.style` | string | 值的风格描述（用于 LLM 生成） |
| `entities[].fields.*.examples` | string[] | 示例值（展示给用户确认 + 指导生成） |
| `entities[].fields.*.distribution` | string | 分布方式: uniform / normal / weighted / balanced / derived / sequential |
| `entities[].fields.*.weights` | object\|number[] | 枚举/布尔字段的权重分配 |
| `creation_order` | string[] | 拓扑排序后的创建顺序 |
| `parallel_groups` | array | 可并行创建的实体分组 |
| `image_requirements` | object | 图片需求汇总，传递给 Step 3 |
| `image_requirements.breakdown.*.sources` | array | 图片来源优先级列表。`type`: `"competitor"` / `"unsplash"` / `"pexels"`，`priority`: 数字越小优先级越高。竞品优先，免费图库兜底 |
| `confirmed_by_user` | boolean | 用户确认前 false，确认后 true |

---

## 执行流程总结

```
1. 读取 project-analysis.json（实体 + API 映射 + 外键关系）
2. 读取 industry-profile.json（行业风格 + 数据量建议）
3. 为每个实体生成数据计划（count, fields, depends_on）
4. 拓扑排序 → creation_order + parallel_groups
5. 汇总图片需求 → image_requirements
6. 向用户展示完整计划（实体表 + 字段示例 + 图片清单 + 创建顺序）
7. 等待用户确认 → confirmed_by_user = true
8. 输出 .allforai/seed-forge/forge-plan.json
9. 传递给 Step 3 (Asset Collection)
```
