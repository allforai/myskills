# Step 1: 行业画像 — Industry Profile

> 前置步骤: Step 0 已完成 `project-analysis.json`（数据模型 + API 映射）
> 输出文件: `.allforai/seed-forge/industry-profile.json`

---

## 1. 用户输入 — User Input

用户提供一个**行业关键词**，描述目标产品所在的行业。

示例 / Examples:

| 关键词 | 说明 |
|--------|------|
| `跨境电商` | Cross-border e-commerce, product listings with international pricing |
| `在线教育` | Online education, courses / students / enrollment |
| `餐饮外卖` | Food delivery, menus / dishes / orders |
| `SaaS 项目管理` | SaaS project management, workspaces / boards / tasks |
| `社交平台` | Social platform, users / posts / comments / likes |
| `医疗健康` | Healthcare, patients / appointments / records |

技能根据这个关键词执行搜索，提取该行业的**数据风格**，用于后续生成真实感演示数据。

> **为什么需要行业关键词？** 不同行业的产品命名、价格区间、分类层级、图片风格差异巨大。一个"咖啡杯"和一个"Pro 订阅计划"需要完全不同的数据生成策略。

---

## 2. 搜索策略 — Search Strategy

对每个行业关键词，执行 **3 次 WebSearch**，逐步构建行业画像。

### Query 1: 了解典型数据 — Understand Typical Data

```
WebSearch("{行业} 产品 示例数据")
WebSearch("{industry} sample products")
```

**目的**: 了解该行业的产品/实体**长什么样**。

**从结果中提取**:
- 典型实体名称（产品名 / 课程名 / 菜品名 / 项目名）
- 名称的长度、用词习惯、是否带规格参数
- 常见属性字段（颜色、尺码、学时、辣度、成员数...）
- 数据量级感知（一个典型店铺有多少商品？一个教育平台有多少课程？）

**示例结果利用**:

| 行业 | 搜索结果中的信号 | 提取出的风格 |
|------|-----------------|-------------|
| 跨境电商 | "Wireless Bluetooth Earbuds with Charging Case" | 英文标题，带功能描述，20-60 字符 |
| 餐饮外卖 | "香辣小龙虾尾 (中份)" | 中文菜名 + 规格，5-15 字符 |
| SaaS 项目管理 | "Team Collaboration — Pro Plan" | 英文 + 功能词 + 版本层级 |

### Query 2: 了解数据风格 — Data Style (Naming, Pricing, Categorization)

```
WebSearch("{行业} 主流产品 特点")
```

**目的**: 提取命名规律、价格分布、分类层级结构。

**从结果中提取**:
- **命名模式** — 是 `品牌 + 材质 + 品类` 还是 `功能 + 版本` 还是 `菜系 + 做法 + 主料`？
- **价格范围** — 该行业的低/中/高价位分别是多少？货币单位是 CNY / USD？是一次性还是订阅制？
- **分类结构** — 有几级分类？典型分类路径是什么样？
- **行业术语** — 有哪些字段是该行业特有的（如电商的 SKU、教育的"学时"、餐饮的"辣度"）

**示例结果利用**:

| 行业 | 价格信号 | 分类信号 |
|------|---------|---------|
| 跨境电商 | "$9.99 - $299.99", free shipping threshold | Electronics > Audio > Earbuds |
| 在线教育 | "¥49 - ¥999", 部分免费试听 | 编程 > Python > 入门 |
| 餐饮外卖 | "¥15 - ¥128", 套餐比单品贵 | 川菜 > 热菜 > 荤菜 |

### Query 3: 确定图片搜索关键词 — Image Search Keywords

```
WebSearch("{行业} product photography style")
```

**目的**: 确定 Step 3 素材采集时用什么关键词在 Unsplash/Pexels 上搜图。

**从结果中提取**:
- **图片风格** — 白底产品图？场景图？截图？食物特写？人物头像？
- **图片关键词** — 直接可用于 Unsplash 搜索的英文关键词
- **图片比例** — 正方形（电商）、16:9（课程封面）、圆形（头像）
- **图片数量需求** — 每个实体需要几张图（商品多图、课程封面单图）

**示例结果利用**:

| 行业 | 图片风格 | Unsplash 关键词 |
|------|---------|----------------|
| 跨境电商 | white background product photography | `product photography`, `minimal product` |
| 餐饮外卖 | overhead food photography, warm lighting | `food photography`, `dish plating` |
| SaaS | dashboard UI, clean interface | `dashboard ui`, `saas interface` |
| 在线教育 | course cover, instructor portrait | `online learning`, `classroom` |
| 社交平台 | user avatar, social media post | `portrait`, `lifestyle photography` |
| 医疗健康 | medical equipment, clinic interior | `medical`, `healthcare professional` |

---

## 3. 风格提取维度 — Style Extraction Dimensions

搜索完成后，将结果整理为以下维度的**行业风格表**。

这张表是 demo-forge 数据生成的核心参考——每个维度直接对应后续 Step 2 数据规划中的一个配置项。

| 维度 | 电商 E-commerce | SaaS | 餐饮 Food Delivery | 教育 Education | 社交 Social |
|------|-----------------|------|---------------------|----------------|-------------|
| **实体名称风格** Entity naming | "日式陶瓷咖啡杯套装" / "Wireless Bluetooth Earbuds" — 材质+品类+规格 | "团队协作 Pro 版" / "Project Hub Enterprise" — 功能+版本 | "香辣小龙虾套餐" — 口味+主料+规格 | "Python入门到实战" — 技术+级别+目标 | — (用户生成内容，不需要产品名) |
| **价格范围** Price range | CNY: ¥19.9 - ¥999; USD: $9.99 - $299.99 | $9 - $99/月 (subscription); Free tier common | ¥15 - ¥128; 套餐 ¥30 - ¥80 | ¥49 - ¥999; 部分免费 | — (typically free, premium ¥12-30/月) |
| **价格模式** Pricing model | 一次性 one-time | 月付/年付 subscription | 一次性 per-order | 一次性 or 会员制 membership | 免费 + 会员增值 freemium |
| **分类结构** Category hierarchy | 3 级: 家居 > 厨具 > 杯具 | 2 级: 项目管理 > 看板 | 2-3 级: 川菜 > 热菜 > 荤菜 | 2 级: 编程 > Python | 1 级: 话题标签 tags |
| **图片风格** Image style | product photography, white background, studio lighting | dashboard screenshot, UI mockup, feature illustration | food photography, overhead shot, warm lighting | course cover design, instructor photo | avatar (portrait), post image (lifestyle) |
| **Unsplash 关键词** | `product`, `minimal object` | `dashboard`, `laptop workspace` | `food plating`, `restaurant dish` | `online learning`, `study` | `portrait`, `lifestyle` |
| **用户名风格** Username style | 中文姓名 "张明" / "李晓红" | English + company "John@Acme" / "Sarah Miller" | 中文昵称 "美食达人小王" / 手机尾号 "用户****8832" | 学员姓名 "王同学" / "Lily Chen" | 昵称 "星空下的猫" / "pixel_wanderer" |
| **数据量级** Volume reference | 商品 50+, SKU 150+, 分类 20+, 用户 20+, 订单 200+ | 项目 10+, 成员 15+, 任务 100+, 评论 200+ | 菜品 80+, 分类 15+, 订单 100+, 用户 30+ | 课程 20+, 章节 100+, 学员 50+, 评价 80+ | 用户 30+, 帖子 200+, 评论 500+, 点赞 1000+ |
| **特有字段** Industry-specific fields | SKU, 库存, 物流信息, 规格参数 | 到期日, 使用量, 团队人数上限, 权限等级 | 辣度, 份量, 配送时间, 满减条件 | 学时, 难度, 完成率, 证书 | 关注数, 粉丝数, 互动率 |
| **关系复杂度** Relationship complexity | 商品 → 分类, 商品 → SKU, 订单 → 商品 (多对多), 用户 → 订单 | 工作区 → 项目 → 任务 → 子任务, 成员 → 角色 | 店铺 → 分类 → 菜品, 用户 → 订单 → 菜品 (多对多) | 课程 → 章节 → 课时, 学员 → 报名 → 课程 | 用户 → 帖子, 用户 → 关注 (自引用), 帖子 → 评论 → 回复 |

### 如何使用这张表

1. **匹配行业** — 用户输入的行业关键词匹配到最接近的列
2. **交叉数据模型** — 将 Step 0 的 `project-analysis.json` 中的每个 model 对应到表中的维度
3. **生成风格配置** — 输出 `industry-profile.json`，供 Step 2 数据规划使用

---

## 4. 竞品网站收集 — Competitor URL Collection

在行业搜索之后，收集竞品网站 URL，供 Step 3 爬取真实产品图片。

### 4.1 获取竞品 URL

**方式 1: 用户直接提供（优先）**

询问用户：

> **请提供 1-5 个竞品网站 URL（用于爬取产品图片素材）：**

用户可能给出：
- `https://www.example-shop.com`
- `https://competitor.cn`
- 不提供（跳到方式 2）

**方式 2: 自动发现**

如果用户不提供竞品 URL，通过 WebSearch 自动发现：

```
WebSearch("{行业} 知名品牌 官网")
WebSearch("{行业} top brands official website")
```

从搜索结果中提取 1-5 个竞品网站 URL。

### 4.2 竞品分类页收集

对每个竞品网站，用 WebFetch 访问首页，提取分类页/列表页 URL：

```
WebFetch(competitor_url)
  → 从导航栏/菜单提取分类页链接
  → 记录到 category_pages 列表
```

### 4.3 用户确认

向用户展示收集到的竞品列表：

```
竞品网站列表:
  1. XX商城 — https://example.com
     分类页: /electronics, /fashion, /home
  2. YY平台 — https://competitor.cn
     分类页: /products/phones, /products/accessories

请确认以上竞品网站是否正确？是否需要增减？
```

### 4.4 存入 industry-profile.json

竞品 URL 列表存入 `industry-profile.json` 的新增 `competitors` 字段：

```json
{
  "competitors": [
    {
      "name": "XX商城",
      "url": "https://example.com",
      "category_pages": [
        "https://example.com/electronics",
        "https://example.com/fashion"
      ]
    },
    {
      "name": "YY平台",
      "url": "https://competitor.cn",
      "category_pages": [
        "https://competitor.cn/products/phones",
        "https://competitor.cn/products/accessories"
      ]
    }
  ]
}
```

---

## 5. 边界与禁止事项 — Boundaries

这一步有明确的边界。**风格自己提取，文案自己生成，图片从竞品爬取。**

### 允许与禁止 / Allowed vs Prohibited

| 行为 | 是否允许 | 说明 |
|------|----------|------|
| **爬取竞品公开页面的产品图片** | 允许 | 仅用于内部演示，Step 3 执行 |
| **收集竞品网站 URL 和分类页** | 允许 | 本步骤执行，用于 Step 3 爬取 |
| **复制竞品产品名** | 禁止 | 提取命名**模式**（如"材质+品类+规格"），自行生成 |
| **复制竞品文案/描述** | 禁止 | 只参考风格，文字内容自己生成 |
| **访问需要登录的页面** | 禁止 | 只爬取公开可访问的页面 |
| **抓取竞品精确价格数据** | 禁止 | 提取价格**范围**和**模式**（订阅制/一次性） |

### 图片 vs 文字的区别

```
图片: 可以直接从竞品爬取（仅限内部演示用途）
文字: 只提取 "风格"，不复制 "内容"

OK:  从竞品官网下载产品图片用于演示环境
OK:  "电商产品名通常是 '材质 + 品类 + 规格' 格式，8-20 个字"
NOT: "复制淘宝上的 '日式手工陶瓷咖啡杯套装' 这个名字"

OK:  "SaaS 定价通常 $9-99/月，分 Free/Pro/Enterprise 三档"
NOT: "Notion 的 Pro 版是 $10/月"
```

---

## 6. 用户确认点 — User Confirmation

搜索完成并提取风格后，**必须向用户展示行业画像并等待确认**，不能自动进入 Step 2。

### 展示格式

```
====================================
  行业画像 — Industry Profile
  行业: 跨境电商 (Cross-border E-commerce)
====================================

  实体名称风格: 英文标题, "品牌 + 功能 + 规格", 20-60 chars
  价格范围:     $9.99 - $299.99 (one-time)
  分类结构:     3 级 — Electronics > Audio > Earbuds
  图片风格:     product photography, white background
  用户名风格:   English names — "John Smith", "Sarah Lee"
  数据量级:     商品 50+, 用户 20+, 订单 200+

====================================
```

### 确认提问

向用户提问:

> **行业风格对吗？要调整名称风格、价格范围、图片关键词吗？**

用户可能的调整:
- "价格范围改成 ¥50-500" — 更新 `priceRange`
- "名称要用中文" — 更新 `entityNamingStyle`
- "图片搜索加上 lifestyle" — 更新 `imageKeywords`
- "用户量改成 50 个" — 更新 `volumeReference`
- "确认，继续" — 进入 Step 2

---

## 7. 输出格式 — Output Format

输出文件: `.allforai/seed-forge/industry-profile.json`

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "IndustryProfile",
  "description": "行业画像 — 描述目标行业的数据风格，用于指导演示数据生成",
  "type": "object",
  "required": [
    "industry",
    "generatedAt",
    "searchQueries",
    "entityNamingStyle",
    "priceRange",
    "categoryStructure",
    "imageStyle",
    "usernameStyle",
    "volumeReference",
    "industrySpecificFields"
  ],
  "properties": {
    "industry": {
      "type": "object",
      "description": "行业标识",
      "required": ["keyword", "keywordEn", "description"],
      "properties": {
        "keyword":     { "type": "string", "description": "用户输入的行业关键词" },
        "keywordEn":   { "type": "string", "description": "English translation of the keyword" },
        "description": { "type": "string", "description": "一句话描述该行业的数据特征" }
      }
    },
    "generatedAt": {
      "type": "string",
      "format": "date-time",
      "description": "生成时间"
    },
    "searchQueries": {
      "type": "array",
      "description": "实际执行的搜索查询及结果摘要",
      "items": {
        "type": "object",
        "required": ["query", "purpose", "keyFindings"],
        "properties": {
          "query":       { "type": "string", "description": "搜索查询文本" },
          "purpose":     { "type": "string", "description": "该查询的目的" },
          "keyFindings": { "type": "array", "items": { "type": "string" }, "description": "从搜索结果中提取的关键发现" }
        }
      }
    },
    "entityNamingStyle": {
      "type": "object",
      "description": "实体名称风格",
      "required": ["pattern", "language", "lengthRange", "examples"],
      "properties": {
        "pattern":     { "type": "string", "description": "命名模式，如 '材质+品类+规格'" },
        "language":    { "type": "string", "enum": ["zh", "en", "mixed"], "description": "名称语言" },
        "lengthRange": { "type": "object", "properties": { "min": { "type": "integer" }, "max": { "type": "integer" } }, "description": "名称字符数范围" },
        "examples":    { "type": "array", "items": { "type": "string" }, "description": "示例名称 (自行编写，非抄袭)" }
      }
    },
    "priceRange": {
      "type": "object",
      "description": "价格范围和模式",
      "required": ["currency", "min", "max", "model"],
      "properties": {
        "currency": { "type": "string", "description": "货币单位 CNY/USD/EUR" },
        "min":      { "type": "number", "description": "最低价" },
        "max":      { "type": "number", "description": "最高价" },
        "model":    { "type": "string", "enum": ["one-time", "subscription", "freemium", "mixed"], "description": "定价模式" },
        "tiers":    { "type": "array", "items": { "type": "string" }, "description": "价格档位名称，如 ['Free', 'Pro', 'Enterprise']" }
      }
    },
    "categoryStructure": {
      "type": "object",
      "description": "分类层级结构",
      "required": ["depth", "examplePaths"],
      "properties": {
        "depth":        { "type": "integer", "description": "分类层级数" },
        "examplePaths": { "type": "array", "items": { "type": "string" }, "description": "示例分类路径，如 ['家居 > 厨具 > 杯具']" },
        "topCategories":{ "type": "array", "items": { "type": "string" }, "description": "一级分类列表" }
      }
    },
    "imageStyle": {
      "type": "object",
      "description": "图片风格和搜索关键词",
      "required": ["style", "keywords", "aspectRatio"],
      "properties": {
        "style":       { "type": "string", "description": "图片风格描述" },
        "keywords":    { "type": "array", "items": { "type": "string" }, "description": "Unsplash/Pexels 搜索关键词" },
        "aspectRatio": { "type": "string", "description": "推荐图片比例，如 '1:1', '16:9'" },
        "perEntity":   { "type": "integer", "description": "每个实体需要几张图" }
      }
    },
    "usernameStyle": {
      "type": "object",
      "description": "用户名/人名风格",
      "required": ["language", "pattern", "examples"],
      "properties": {
        "language": { "type": "string", "enum": ["zh", "en", "mixed", "nickname"], "description": "姓名语言" },
        "pattern":  { "type": "string", "description": "命名模式描述" },
        "examples": { "type": "array", "items": { "type": "string" }, "description": "示例名称" }
      }
    },
    "volumeReference": {
      "type": "object",
      "description": "各实体建议数据量",
      "additionalProperties": {
        "type": "integer",
        "description": "实体名称 → 建议数量"
      }
    },
    "industrySpecificFields": {
      "type": "array",
      "description": "该行业特有的字段",
      "items": {
        "type": "object",
        "required": ["field", "description", "exampleValues"],
        "properties": {
          "field":         { "type": "string", "description": "字段名" },
          "description":   { "type": "string", "description": "字段说明" },
          "exampleValues": { "type": "array", "items": {}, "description": "示例值" }
        }
      }
    },
    "competitors": {
      "type": "array",
      "description": "竞品网站列表，供 Step 3 爬取产品图片",
      "items": {
        "type": "object",
        "required": ["name", "url"],
        "properties": {
          "name":           { "type": "string", "description": "竞品名称" },
          "url":            { "type": "string", "format": "uri", "description": "竞品官网 URL" },
          "category_pages": { "type": "array", "items": { "type": "string" }, "description": "分类页/列表页 URL" }
        }
      }
    },
    "userConfirmed": {
      "type": "boolean",
      "description": "用户是否已确认该画像",
      "default": false
    },
    "userAdjustments": {
      "type": "array",
      "description": "用户要求的调整记录",
      "items": {
        "type": "object",
        "properties": {
          "field":    { "type": "string", "description": "调整的字段" },
          "before":   { "description": "调整前的值" },
          "after":    { "description": "调整后的值" },
          "reason":   { "type": "string", "description": "调整原因" }
        }
      }
    }
  }
}
```

### 完整示例 — Full Example

以下是 **跨境电商** 行业的完整输出示例:

```json
{
  "industry": {
    "keyword": "跨境电商",
    "keywordEn": "Cross-border E-commerce",
    "description": "面向海外消费者的电商平台，商品以 3C、家居、服饰为主，英文标题，USD 定价"
  },
  "generatedAt": "2026-02-24T14:30:00Z",
  "searchQueries": [
    {
      "query": "跨境电商 产品 示例数据",
      "purpose": "了解该行业典型产品数据的结构和内容",
      "keyFindings": [
        "产品标题为英文，格式: 品牌 + 核心功能 + 规格参数",
        "标题长度通常 40-80 字符",
        "常见品类: Electronics, Home & Garden, Fashion, Beauty"
      ]
    },
    {
      "query": "跨境电商 主流产品 特点",
      "purpose": "提取命名规律、价格分布、分类层级",
      "keyFindings": [
        "定价以 USD 为主，区间 $5.99 - $299.99",
        "3 级分类结构: Department > Category > Subcategory",
        "SKU 编码格式: 品类缩写 + 序号，如 EL-001"
      ]
    },
    {
      "query": "cross-border e-commerce product photography style",
      "purpose": "确定图片搜索关键词和风格",
      "keyFindings": [
        "主图为白底产品图 (white background product photography)",
        "辅图为场景使用图 (lifestyle product shot)",
        "推荐正方形比例 1:1，主图 1 张 + 辅图 3-5 张"
      ]
    }
  ],
  "entityNamingStyle": {
    "pattern": "Brand + Core Feature + Specification",
    "language": "en",
    "lengthRange": { "min": 30, "max": 80 },
    "examples": [
      "Portable Wireless Bluetooth Speaker with LED Light",
      "Stainless Steel Insulated Water Bottle 750ml",
      "Ultra-Thin Laptop Stand Adjustable Aluminum Alloy",
      "Cotton Linen Throw Pillow Cover 18x18 inches"
    ]
  },
  "priceRange": {
    "currency": "USD",
    "min": 5.99,
    "max": 299.99,
    "model": "one-time",
    "tiers": null
  },
  "categoryStructure": {
    "depth": 3,
    "examplePaths": [
      "Electronics > Audio > Bluetooth Speakers",
      "Home & Garden > Kitchen > Drinkware",
      "Fashion > Women > Dresses",
      "Beauty > Skincare > Moisturizers"
    ],
    "topCategories": [
      "Electronics",
      "Home & Garden",
      "Fashion",
      "Beauty & Health",
      "Sports & Outdoors",
      "Toys & Hobbies"
    ]
  },
  "imageStyle": {
    "style": "White background product photography, clean and minimal",
    "keywords": [
      "product photography white background",
      "minimal product shot",
      "lifestyle product photography",
      "ecommerce product"
    ],
    "aspectRatio": "1:1",
    "perEntity": 4
  },
  "usernameStyle": {
    "language": "en",
    "pattern": "Western first name + last name",
    "examples": [
      "John Smith",
      "Sarah Johnson",
      "Michael Chen",
      "Emily Davis"
    ]
  },
  "volumeReference": {
    "products": 50,
    "categories": 20,
    "users": 20,
    "orders": 200,
    "reviews": 150
  },
  "industrySpecificFields": [
    {
      "field": "sku",
      "description": "库存单位编码，每个商品变体唯一",
      "exampleValues": ["EL-BT-001", "HG-KT-042", "FA-WD-018"]
    },
    {
      "field": "stock",
      "description": "库存数量",
      "exampleValues": [100, 500, 0, 25]
    },
    {
      "field": "weight",
      "description": "商品重量 (g)，影响运费计算",
      "exampleValues": [150, 500, 1200]
    },
    {
      "field": "shippingTime",
      "description": "预计配送天数",
      "exampleValues": ["7-15 days", "3-7 days", "15-30 days"]
    },
    {
      "field": "rating",
      "description": "商品评分 1-5",
      "exampleValues": [4.5, 4.8, 3.9, 5.0]
    }
  ],
  "competitors": [
    {
      "name": "AliExpress",
      "url": "https://www.aliexpress.com",
      "category_pages": [
        "https://www.aliexpress.com/category/44/consumer-electronics.html",
        "https://www.aliexpress.com/category/15/home-and-garden.html"
      ]
    }
  ],
  "userConfirmed": false,
  "userAdjustments": []
}
```

---

## 附录: 流程图 — Process Flow

```
用户输入行业关键词
        │
        ▼
┌─────────────────────────┐
│  WebSearch Query 1       │
│  "{行业} 产品 示例数据"   │──→ 提取: 名称风格, 字段特征, 数据量级
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  WebSearch Query 2       │
│  "{行业} 主流产品 特点"   │──→ 提取: 价格范围, 分类结构, 命名模式
└────────────┬────────────┘
             ▼
┌─────────────────────────────────┐
│  WebSearch Query 3               │
│  "{industry} product photography │──→ 提取: 图片风格, 搜索关键词, 比例
│   style"                         │
└────────────┬────────────────────┘
             ▼
┌─────────────────────────────────┐
│  竞品网站收集                     │
│  用户提供 or WebSearch 自动发现   │──→ 竞品 URL + 分类页
│  WebFetch 首页提取分类页链接      │
└────────────┬────────────────────┘
             ▼
┌─────────────────────────┐
│  整合为 industry-profile │
│  生成 JSON（含竞品列表）  │
└────────────┬────────────┘
             ▼
┌─────────────────────────────┐
│  展示给用户确认               │
│  "行业风格对吗？              │
│   竞品网站列表正确吗？        │
│   要调整名称风格、            │
│   价格范围、图片关键词吗？"    │
└────────────┬────────────────┘
             ▼
       用户确认 ──→ userConfirmed: true
             │
             ▼
    保存 .allforai/seed-forge/industry-profile.json
             │
             ▼
      进入 Step 2: 数据规划
```
