# Step 3: 素材采集 — Asset Collection

> demo-forge 的第三步：根据 forge-plan.json 中的图片需求，优先从竞品网站爬取真实产品图片，不足时用免费图库补充。
>
> 前置步骤: [数据规划 (Step 2)](./data-plan.md) 输出的 `forge-plan.json` + `industry-profile.json`（含竞品 URL）
> 输出文件: `.allforai/seed-forge/assets-manifest.json` + `.allforai/seed-forge/assets/` 目录

---

## 1. 图片来源优先级 — Image Source Priority

**竞品优先，免费图库兜底。**

| 优先级 | 来源 | 方式 | 适用场景 |
|--------|------|------|----------|
| 1 | **竞品网站** | WebFetch 分类页/列表页 → 提取产品图片 URL → 下载 | 产品图、分类图、Banner — 最真实 |
| 2 | **Unsplash** | WebFetch search page → extract direct image URLs | 竞品不足时补充，头像类优先用这个 |
| 3 | **Pexels** | WebFetch search page → extract direct image URLs | Unsplash 不够时补充 |
| 4 | **Placeholder** | Generate simple colored placeholder | 所有来源都失败时的兜底方案 |

### 规则

- **竞品优先** — 从用户确认的竞品网站爬取真实产品图片（仅用于内部演示）
- **不访问登录页面** — 只爬取公开可访问的页面
- **不复制竞品文案** — 图片可以用，文字内容（产品名、描述）自己生成
- **不用 Google Images** — 搜索引擎返回的图片版权不明
- **Placeholder 仅作兜底** — 所有来源都失败时才用纯色占位图

---

## 2. 竞品爬取流程 — Competitor Scraping Workflow（主要来源）

### 2.1 读取竞品列表

从 `industry-profile.json` 的 `competitors` 字段读取竞品网站和分类页：

```python
# 伪代码
competitors = industry_profile["competitors"]
# [
#   { "name": "XX商城", "url": "https://example.com", "category_pages": [...] },
#   { "name": "YY平台", "url": "https://competitor.cn", "category_pages": [...] }
# ]
```

### 2.2 逐竞品逐页爬取

对每个竞品网站的每个分类页/列表页：

```
对每个竞品网站:
  对每个分类页 URL:
    1. WebFetch 获取页面 HTML/Markdown
    2. 从页面中提取产品图片 URL:
       - <img src="..."> 标签中的 src 属性
       - CSS background-image: url(...) 中的 URL
       - <source srcset="..."> 中的 URL
       - data-src / data-lazy-src 等懒加载属性
    3. 过滤图片 URL:
       - 跳过 icon / logo / 广告图（URL 含 icon/logo/ad/banner-ad 关键词）
       - 跳过尺寸过小的图（URL 参数含 width < 200 或 thumbnail）
       - 跳过 SVG 和 GIF 格式（通常是图标/动画）
       - 保留: 产品图、分类图、Banner 图
    4. 按用途分类:
       - 产品图: 在产品列表/网格区域的图片
       - 分类图: 在分类导航区域的图片
       - Banner: 在轮播/横幅区域的大图
    5. 下载到对应目录:
       .allforai/seed-forge/assets/products/{NNN}.jpg
       .allforai/seed-forge/assets/categories/{NNN}.jpg
       .allforai/seed-forge/assets/banners/{NNN}.jpg
    6. 记录到 assets-manifest.json
```

### 2.3 图片 URL 提取规则

从 WebFetch 返回的页面内容中提取图片 URL 的优先级：

```
1. 主图优先:
   - <img> 标签且位于产品卡片/网格容器内
   - class/id 含 product/item/goods 的元素内的图片

2. 高分辨率优先:
   - srcset 中选择最大尺寸
   - data-original / data-src 通常是高清原图

3. URL 清理:
   - 移除 URL 中的缩略图参数（如 _thumb、_small、?w=100）
   - 保留原图路径或使用中等尺寸参数
   - 确保 URL 是完整的绝对路径（补全 protocol + domain）
```

### 2.4 爬取限制与安全

| 限制 | 说明 |
|------|------|
| **只爬公开页面** | 不访问需要登录、Cookie 验证的页面 |
| **自然间隔** | 依赖 WebFetch 调用之间的自然间隔（1-2 秒），不做精确速率控制 |
| **失败跳过** | 遇到 403/404/超时，记录日志，跳过该 URL，继续下一个 |
| **每竞品上限** | 每个竞品网站最多爬取 5 个分类页，避免过度访问 |
| **总图片上限** | 竞品爬取的总图片数不超过 forge-plan.json 中的需求量 |

### 2.5 竞品爬取结果汇总

爬取完成后，统计结果：

```
竞品爬取结果:
  XX商城: 产品图 35 张, 分类图 8 张, Banner 3 张
  YY平台: 产品图 28 张, 分类图 6 张, Banner 2 张
  ─────────────────────
  合计:   产品图 63 张, 分类图 14 张, Banner 5 张

需求量:  产品图 50 张, 分类图 10 张, Banner 5 张, 头像 20 张
缺口:    头像 20 张 → 转入 Unsplash 搜索
```

---

## 3. 免费图库补充 — Free Library Supplement

竞品图片不足的部分，从 Unsplash/Pexels 补充。头像类图片默认使用免费图库（竞品网站通常没有合适的头像素材）。

### 3.1 需要补充的场景

- 竞品爬取数量不够（如需要 50 张产品图但只爬到 30 张）
- 竞品不适合的类型（头像、场景图、抽象 Banner）
- 竞品列表为空（用户未提供且自动发现失败）

### 3.2 关键词收集

从 `forge-plan.json` 的 entities 中提取所有 `image_query` 字段：

```python
# 伪代码
keywords = []
for entity in forge_plan["entities"]:
    for field_name, field_spec in entity["fields"].items():
        if "image_query" in field_spec:
            keywords.append({
                "query": field_spec["image_query"],
                "entity": entity["model"],
                "field": field_name,
                "count": field_spec.get("count", entity["count"])
            })
```

### 3.3 关键词去重与分组

相似关键词合并，避免重复搜索浪费时间：

```
原始关键词:
  - "portrait professional" (User.avatar, 15张)
  - "portrait business" (Admin.avatar, 5张)
  - "product electronics photography" (Product.image, 30张)

合并后:
  Group 1: "portrait professional" → 需要 20 张 (15+5)
  Group 2: "product electronics photography" → 需要 30 张（减去竞品已爬到的数量）
```

### 3.4 逐组搜索

For each keyword group:

```
1. WebFetch `https://unsplash.com/s/photos/{query}`
   → 从返回的 HTML/Markdown 中提取图片 URL
   → URL 格式通常为: https://images.unsplash.com/photo-xxxxx

2. 如果 Unsplash 结果不足（< 需要数量的 80%）:
   → WebFetch `https://www.pexels.com/search/{query}/`
   → 提取 Pexels 图片 URL

3. 如果两个来源加起来仍不足:
   → 尝试替换关键词（去掉修饰词、换同义词）
   → 仍然不够则标记需要 placeholder 补充

4. 从结果中选取所需数量的图片
   → 优先选择构图清晰、主体明确的图片
   → 避免重复（同一张图不用于不同实体）
```

---

## 4. 下载流程 — Download Workflow

### 4.1 逐图下载

For each selected image (无论来源):

```bash
# 1. 创建目录
mkdir -p .allforai/seed-forge/assets/{entity}/

# 2. 下载图片（带 URL 参数控制尺寸）
curl -L -o .allforai/seed-forge/assets/{entity}/{NNN}.jpg "{url}"

# 3. 验证文件完整性
#    - 文件存在
#    - 文件大小 > 1KB（排除空文件/错误页面）
#    - 是有效的图片格式（可选：用 file 命令检查 MIME type）
```

### 4.2 文件命名规则

```
{entity}/{NNN}.jpg

entity  — 小写实体名复数形式: avatars, products, categories, banners
NNN     — 三位数零填充序号: 001, 002, ..., 999
扩展名  — 统一 .jpg（即使原始是 .png 或 .webp，curl 下载后以实际格式存储）
```

### 4.3 下载后校验

```bash
# 检查文件是否存在且有内容
if [ -f ".allforai/seed-forge/assets/products/001.jpg" ] && [ $(stat -c%s ".allforai/seed-forge/assets/products/001.jpg") -gt 1024 ]; then
    echo "OK"
else
    echo "FAILED - retry or skip"
fi
```

### 4.4 写入 manifest

每下载成功一张图片，立即更新 `assets-manifest.json`（增量写入，防止中断丢失进度）。

---

## 5. 目录结构 — Directory Structure

```
.allforai/seed-forge/
└── assets/
    ├── avatars/           # User avatars — 用户头像（通常来自 Unsplash）
    │   ├── 001.jpg
    │   ├── 002.jpg
    │   └── ...
    ├── products/          # Product images — 商品/产品图片（优先来自竞品）
    │   ├── 001.jpg
    │   ├── 002.jpg
    │   └── ...
    ├── categories/        # Category icons/banners — 分类图标或横幅（优先来自竞品）
    │   ├── 001.jpg
    │   └── ...
    ├── banners/           # Site banners — 站点横幅广告图（优先来自竞品）
    │   ├── 001.jpg
    │   └── ...
    └── misc/              # Other images — 其他未分类图片
        └── ...
```

### 目录命名规则

- 目录名 = 实体名的小写复数形式（`User` → `avatars`, `Product` → `products`）
- 如果实体字段名更直观则用字段名（User 的 avatar 字段 → `avatars/`）
- `misc/` 用于不属于任何特定实体的通用图片

---

## 6. 图片尺寸 — Image Dimensions

下载合理尺寸的图片，**不要下载原始高分辨率大图**（浪费带宽和磁盘，演示不需要 4K）。

### 竞品图片尺寸

竞品网站的图片 URL 通常已带尺寸参数，保持原样下载即可。如果原图过大（> 2MB），可尝试：
- 替换 URL 中的尺寸参数为中等尺寸
- 或下载后用工具压缩

### Unsplash / Pexels 尺寸控制

| 用途 | 目标尺寸 | Unsplash URL 参数 | Pexels 处理 |
|------|----------|-------------------|-------------|
| **Avatars** 头像 | ~400px square | `?w=400&h=400&fit=crop` | `?auto=compress&cs=tinysrgb&w=400` |
| **Product images** 商品图 | ~800px wide | `?w=800` | `?auto=compress&cs=tinysrgb&w=800` |
| **Banners** 横幅 | ~1200px wide | `?w=1200` | `?auto=compress&cs=tinysrgb&w=1200` |
| **Thumbnails** 缩略图 | ~300px | `?w=300` | `?auto=compress&cs=tinysrgb&w=300` |
| **Category icons** 分类图 | ~600px | `?w=600` | `?auto=compress&cs=tinysrgb&w=600` |

### Unsplash URL 参数速查

```
基础 URL: https://images.unsplash.com/photo-xxxxxxx

尺寸控制:
  ?w=800           宽度 800px（高度自动等比）
  ?h=600           高度 600px
  ?w=400&h=400     指定宽高
  &fit=crop        裁切填充（用于头像等正方形场景）
  &fit=contain     保持比例缩放

质量控制:
  &q=80            JPEG 质量 80%（默认 75，演示够用）
  &fm=jpg          输出格式 JPEG
```

### Pexels URL 参数速查

```
基础 URL: https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg

尺寸控制:
  ?auto=compress&cs=tinysrgb&w=800    宽度 800px 压缩
  ?auto=compress&cs=tinysrgb&h=600    高度 600px
  &dpr=1                               设备像素比 1x（避免 2x 大图）
```

---

## 7. 来源记录 — Source Attribution

### 所有来源都记录

无论图片来自竞品还是免费图库，**始终记录来源信息**：

```json
{
  "source": "competitor",
  "source_url": "https://example.com/products/phone-case",
  "competitor_domain": "example.com",
  "downloaded_at": "2026-02-24T10:30:00Z"
}
```

```json
{
  "source": "unsplash",
  "source_url": "https://unsplash.com/photos/abc123",
  "photographer": "John Doe",
  "license": "Unsplash License",
  "downloaded_at": "2026-02-24T10:30:00Z"
}
```

记录来源的好处：
- 追溯每张图片来自哪个竞品/图库
- 竞品图片标记 `competitor_domain` 便于后续管理
- 免费图库图片保留摄影师信息

---

## 8. 错误处理 — Error Handling

### 8.1 竞品爬取失败

```
WebFetch 返回 403/404/超时:
  → 记录失败日志（URL + 错误码）
  → 跳过该 URL，继续下一个分类页
  → 该竞品所有页面都失败 → 跳过该竞品，继续下一个

竞品页面无法提取图片 URL:
  → 页面结构不支持（SPA 动态渲染、需要 JS 执行）
  → 记录为 "extraction_failed"
  → 继续下一个页面

竞品爬取总量不足:
  → 自动切到 Unsplash/Pexels 补充缺口
```

### 8.2 下载失败

```
下载失败（网络超时、404、403）
  → 重试一次（间隔 2 秒）
  → 仍然失败 → 跳过该图片，在 manifest 中标记 status: "failed"
  → 记录失败原因到 manifest 的 error 字段
  → 继续处理下一张图片（不中断整个流程）
```

### 8.3 搜索无结果（免费图库）

```
Unsplash 搜索返回 0 结果
  → 尝试 Pexels 搜索同一关键词
  → Pexels 也无结果 → 尝试简化关键词（去掉修饰词）
    例: "product electronics photography white background"
      → "electronics product"
      → "electronics"
  → 简化后仍无结果 → 使用 placeholder 图片
  → 在 manifest 中标记 source: "placeholder"
```

### 8.4 Rate Limiting

```
收到 429 Too Many Requests 或类似速率限制响应
  → 等待 5 秒后重试
  → 连续 3 次被限流 → 切换到另一个来源
  → 所有来源都被限流 → 暂停 30 秒后继续
  → 在 manifest 中记录 rate_limited: true 的图片
```

### 8.5 文件校验失败

```
下载的文件 < 1KB
  → 可能下载了错误页面 HTML 而非图片
  → 删除该文件，标记为失败
  → 重试一次（可能换一个 URL）
```

### 8.6 磁盘空间

```
下载前粗略估算总大小:
  - 每张图片约 100-500KB（压缩后）
  - 100 张图片 ≈ 10-50MB
  - 一般不会成为问题

如果磁盘空间不足 → 提示用户清理空间或减少图片数量
```

---

## 9. 输出格式 — Output Format

### assets-manifest.json 完整 Schema

```json
{
  "$schema": "assets-manifest",
  "version": "2.0",
  "generated_at": "2026-02-24T10:30:00Z",
  "summary": {
    "total_required": 100,
    "total_downloaded": 95,
    "total_failed": 3,
    "total_placeholder": 2,
    "by_source": {
      "competitor": 60,
      "unsplash": 28,
      "pexels": 7,
      "placeholder": 2
    },
    "by_entity": {
      "avatars": { "required": 20, "downloaded": 20, "failed": 0, "placeholder": 0 },
      "products": { "required": 50, "downloaded": 48, "failed": 1, "placeholder": 1 },
      "categories": { "required": 10, "downloaded": 9, "failed": 1, "placeholder": 1 },
      "banners": { "required": 5, "downloaded": 5, "failed": 0, "placeholder": 0 }
    }
  },
  "assets": [
    {
      "id": "product-001",
      "entity": "products",
      "local_path": ".allforai/seed-forge/assets/products/001.jpg",
      "source": "competitor",
      "source_url": "https://example.com/products/wireless-earbuds",
      "competitor_domain": "example.com",
      "download_url": "https://example.com/images/products/earbuds-main.jpg",
      "license": "N/A (internal demo use only)",
      "photographer": null,
      "dimensions": {
        "width": 800,
        "height": 800
      },
      "file_size_bytes": 156200,
      "search_query": null,
      "status": "downloaded",
      "downloaded_at": "2026-02-24T10:30:05Z",
      "error": null
    },
    {
      "id": "avatar-001",
      "entity": "avatars",
      "local_path": ".allforai/seed-forge/assets/avatars/001.jpg",
      "source": "unsplash",
      "source_url": "https://unsplash.com/photos/abc123",
      "competitor_domain": null,
      "download_url": "https://images.unsplash.com/photo-abc123?w=400&h=400&fit=crop",
      "license": "Unsplash License",
      "photographer": "Jane Smith",
      "dimensions": {
        "width": 400,
        "height": 400
      },
      "file_size_bytes": 45320,
      "search_query": "portrait professional",
      "status": "downloaded",
      "downloaded_at": "2026-02-24T10:30:15Z",
      "error": null
    },
    {
      "id": "product-048",
      "entity": "products",
      "local_path": ".allforai/seed-forge/assets/products/048.jpg",
      "source": "placeholder",
      "source_url": null,
      "competitor_domain": null,
      "download_url": null,
      "license": "N/A",
      "photographer": null,
      "dimensions": {
        "width": 800,
        "height": 600
      },
      "file_size_bytes": 2048,
      "search_query": "product gadget photography",
      "status": "placeholder",
      "downloaded_at": "2026-02-24T10:35:00Z",
      "error": "All sources exhausted: competitor pages had no matching images, Unsplash/Pexels returned no results"
    },
    {
      "id": "category-010",
      "entity": "categories",
      "local_path": null,
      "source": "competitor",
      "source_url": "https://competitor.cn/categories/home",
      "competitor_domain": "competitor.cn",
      "download_url": "https://competitor.cn/images/cat-home.jpg",
      "license": "N/A (internal demo use only)",
      "photographer": null,
      "dimensions": null,
      "file_size_bytes": 0,
      "search_query": null,
      "status": "failed",
      "downloaded_at": null,
      "error": "Download failed after 2 attempts: HTTP 403 Forbidden"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | Yes | 唯一标识: `{entity}-{NNN}` |
| `entity` | string | Yes | 所属实体目录名 |
| `local_path` | string\|null | No | 本地文件路径（失败时为 null） |
| `source` | string | Yes | 来源: `"competitor"` / `"unsplash"` / `"pexels"` / `"placeholder"` |
| `source_url` | string\|null | No | 原始图片所在页面 URL |
| `competitor_domain` | string\|null | No | 竞品域名（仅 source=competitor 时有值） |
| `download_url` | string\|null | No | 实际下载使用的图片 URL |
| `license` | string | Yes | 许可证名称。竞品图片为 `"N/A (internal demo use only)"` |
| `photographer` | string\|null | No | 摄影师名（仅免费图库来源时有值） |
| `dimensions` | object\|null | No | `{ width, height }` in pixels |
| `file_size_bytes` | number | Yes | 文件大小（字节），失败时为 0 |
| `search_query` | string\|null | No | 搜索关键词（仅免费图库来源时有值） |
| `status` | string | Yes | `"downloaded"` / `"failed"` / `"placeholder"` |
| `downloaded_at` | string\|null | No | ISO 8601 下载时间 |
| `error` | string\|null | No | 错误信息（成功时为 null） |

---

## 10. 完整执行流程 — Full Execution Flow

```
读取 forge-plan.json (image_requirements)
读取 industry-profile.json (competitors)
        │
        ▼
┌───────────────────────────┐
│  Phase 1: 竞品爬取         │
│  对每个竞品 → 每个分类页    │
│  WebFetch → 提取图片 URL   │
│  过滤 → 分类 → 下载         │
└────────────┬──────────────┘
             ▼
    统计竞品爬取结果
    计算缺口（需求量 - 已爬到的量）
             │
             ▼
┌───────────────────────────┐
│  Phase 2: 免费图库补充      │
│  仅补充缺口部分             │
│  Unsplash → Pexels → 占位图 │
└────────────┬──────────────┘
             ▼
    所有图片下载到 .allforai/seed-forge/assets/
    写入 assets-manifest.json
             │
             ▼
        传递给 Step 4
```

---

## 11. 与其他步骤的衔接

### 输入依赖（来自 Step 1 + Step 2）

```
industry-profile.json
  → competitors[].url              — 竞品网站 URL
  → competitors[].category_pages   — 分类页 URL 列表

forge-plan.json
  → entities[].fields[].image_query    — 免费图库搜索关键词
  → entities[].fields[].count          — 需要数量
  → image_requirements.total           — 总图片数量
  → image_requirements.breakdown       — 按实体分类的数量和来源优先级
```

### 输出供给（给 Step 4）

```
assets-manifest.json
  → assets[].local_path    — Step 4 灌入时上传这个文件
  → assets[].entity        — Step 4 知道这张图属于哪个实体
  → assets[].id            — Step 4 用来匹配具体的数据记录
  → assets[].status        — Step 4 跳过 failed 的图片

assets/ 目录
  → 实际图片文件，Step 4 通过上传 API 灌入系统
```

### 失败时的影响

- 图片下载失败不阻塞 Step 4 — 灌入时跳过无图片的记录，或使用默认图片
- `assets-manifest.json` 中有完整的成功/失败记录，Step 4 据此决策
- 如果大面积失败（>50% 图片），提示用户检查网络或手动提供图片
- 竞品全部爬取失败时，自动降级为纯免费图库模式（等同于旧版行为）
