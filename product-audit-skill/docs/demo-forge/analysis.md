# Step 0: 项目分析

> demo-forge 的第一步：静态扫描项目代码，提取数据模型和 API 端点，建立映射关系，检测 API 缺口。
> 本步骤不需要应用运行，纯代码分析。

---

## 1. 数据模型提取 / Data Model Extraction

对项目代码进行静态扫描，识别所有数据模型定义。不同技术栈的扫描策略不同。

### 1.1 Per-Framework Scanning Table

#### Go + GORM

| 项目 | 值 |
|------|-----|
| **Glob** | `**/*.go` |
| **Grep** | `gorm:"` 或 `gorm.Model` |
| **扫描目标** | struct with `gorm:` tags |
| **提取内容** | field name, Go type, gorm tag (column/type/index), json tag, relation tags (`foreignKey`, `references`, `many2many`) |
| **关系识别** | `[]ChildModel` = hasMany, `ParentModel` (non-slice) = belongsTo, `gorm:"many2many:"` = many2many |

```go
// 匹配示例
type Product struct {
    gorm.Model
    Name       string    `json:"name" gorm:"type:varchar(100);not null"`
    Price      float64   `json:"price" gorm:"type:decimal(10,2)"`
    CategoryID uint      `json:"category_id"`
    Category   Category  `json:"category" gorm:"foreignKey:CategoryID"`
    Images     []Image   `json:"images" gorm:"foreignKey:ProductID"`
}
```

Grep pattern 细化：
- 主 grep: `gorm:"` — 找到所有含 gorm tag 的文件
- 辅助 grep: `gorm.Model` — 找到嵌入 gorm.Model 的 struct (确认是模型而非普通 struct)
- 排除: `_test.go`, `vendor/`, `mock`

#### Go + Ent

| 项目 | 值 |
|------|-----|
| **Glob** | `ent/schema/*.go` |
| **Grep** | `func (` + `) Fields()` 或 `ent.Schema` |
| **扫描目标** | ent schema 文件中的 `Fields()` 和 `Edges()` 方法 |
| **提取内容** | `field.String("name")` → name:string, `edge.To("posts", Post.Type)` → hasMany:Post |
| **关系识别** | `edge.To()` = hasMany/hasOne, `edge.From()` = belongsTo, `edge.To().Unique()` = hasOne |

```go
// 匹配示例
func (User) Fields() []ent.Field {
    return []ent.Field{
        field.String("name").NotEmpty(),
        field.String("email").Unique(),
        field.Enum("role").Values("admin", "user").Default("user"),
    }
}

func (User) Edges() []ent.Edge {
    return []ent.Edge{
        edge.To("posts", Post.Type),           // hasMany
        edge.From("company", Company.Type).     // belongsTo
            Ref("employees").Unique(),
    }
}
```

#### NestJS + TypeORM

| 项目 | 值 |
|------|-----|
| **Glob** | `**/*.entity.ts` |
| **Grep** | `@Entity()` |
| **扫描目标** | TypeORM Entity class |
| **提取内容** | `@Column()` → field + type, `@ManyToOne()` → relation, `@PrimaryGeneratedColumn()` → PK |
| **关系识别** | `@OneToMany()`, `@ManyToOne()`, `@ManyToMany()`, `@OneToOne()` — 直接映射 |

```typescript
// 匹配示例
@Entity()
export class Product {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'varchar', length: 100 })
  name: string;

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  price: number;

  @Column({ nullable: true })
  imageUrl: string;

  @ManyToOne(() => Category, (cat) => cat.products)
  category: Category;

  @OneToMany(() => OrderItem, (item) => item.product)
  orderItems: OrderItem[];
}
```

#### NestJS + Prisma

| 项目 | 值 |
|------|-----|
| **Glob** | `**/schema.prisma` 或 `**/prisma/schema.prisma` |
| **Grep** | `^model ` |
| **扫描目标** | Prisma model definitions |
| **提取内容** | field name, Prisma type, `@relation`, `@id`, `@unique`, `?` (optional) |
| **关系识别** | `Category Category @relation(...)` = belongsTo, `Post[]` = hasMany |

```prisma
// 匹配示例
model Product {
  id         Int       @id @default(autoincrement())
  name       String    @db.VarChar(100)
  price      Decimal   @db.Decimal(10, 2)
  imageUrl   String?
  categoryId Int
  category   Category  @relation(fields: [categoryId], references: [id])
  orderItems OrderItem[]
  createdAt  DateTime  @default(now())
}
```

#### Django (models.Model)

| 项目 | 值 |
|------|-----|
| **Glob** | `**/models.py` 或 `**/models/*.py` |
| **Grep** | `models.Model` |
| **扫描目标** | Django Model class |
| **提取内容** | `CharField`, `IntegerField`, `DecimalField` → field+type, `ForeignKey` → relation, `ImageField`/`FileField` → 标记为需要上传 |
| **关系识别** | `ForeignKey()` = belongsTo, `ManyToManyField()` = many2many, 反向关系通过 `related_name` |

```python
# 匹配示例
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'
```

#### FastAPI + SQLAlchemy

| 项目 | 值 |
|------|-----|
| **Glob** | `**/models.py` 或 `**/models/*.py` |
| **Grep** | `declarative_base` 或 `DeclarativeBase` 或 `Base` (结合 `Column`) |
| **扫描目标** | SQLAlchemy model class inheriting from Base |
| **提取内容** | `Column(String)` → field+type, `relationship()` → relation, `ForeignKey()` → FK |
| **关系识别** | `relationship()` + `ForeignKey()` 组合判断方向 |

```python
# 匹配示例
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(500), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"))

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
```

#### Express + Mongoose

| 项目 | 值 |
|------|-----|
| **Glob** | `**/*.model.js`, `**/*.model.ts`, `**/models/*.js`, `**/models/*.ts` |
| **Grep** | `mongoose.Schema` 或 `new Schema` |
| **扫描目标** | Mongoose Schema definition |
| **提取内容** | `name: { type: String }` → field+type, `ref: 'Category'` → relation |
| **关系识别** | `ref: 'ModelName'` = belongsTo (FK reference), `[{ type: ..., ref: }]` = hasMany embedded refs |

```javascript
// 匹配示例
const productSchema = new Schema({
  name: { type: String, required: true, maxlength: 100 },
  price: { type: Number, required: true },
  imageUrl: { type: String },
  category: { type: Schema.Types.ObjectId, ref: 'Category', required: true },
  tags: [{ type: String }],
}, { timestamps: true });
```

### 1.2 Scanning Summary / 扫描策略汇总

| Framework | Glob Pattern | Grep Pattern | Fields | Types | Relations | JSON/API Names |
|-----------|-------------|-------------|--------|-------|-----------|----------------|
| Go+GORM | `**/*.go` | `gorm:"` or `gorm.Model` | struct field name | Go type + gorm type tag | gorm FK/many2many tags | `json:"xxx"` tag |
| Go+Ent | `ent/schema/*.go` | `ent.Schema` | `field.Xxx("name")` | field builder type | `edge.To/From` | field name (snake_case) |
| NestJS+TypeORM | `**/*.entity.ts` | `@Entity()` | `@Column()` prop | TS type + Column options | `@ManyToOne` etc. | property name (camelCase) |
| NestJS+Prisma | `**/schema.prisma` | `^model ` | field lines | Prisma type | `@relation` + `[]` suffix | field name |
| Django | `**/models.py` | `models.Model` | `field = models.XxxField` | Django field class | `ForeignKey`, `ManyToManyField` | field name (snake_case) |
| FastAPI+SQLAlchemy | `**/models.py` | `declarative_base` or `Base` | `Column(Xxx)` | SA type class | `relationship()` + `ForeignKey()` | column name |
| Express+Mongoose | `**/*.model.{js,ts}` | `mongoose.Schema` or `new Schema` | schema keys | `type: Xxx` | `ref: 'Model'` | key name (camelCase) |

### 1.3 Model Extraction Output Example / 模型提取输出示例

提取后统一为标准格式，无论原始框架是什么：

```json
{
  "models": [
    {
      "name": "Product",
      "source_file": "internal/model/product.go",
      "framework": "gorm",
      "table_name": "products",
      "fields": [
        {
          "name": "ID",
          "json_name": "id",
          "type": "uint",
          "db_type": "bigint",
          "primary_key": true,
          "auto_increment": true,
          "nullable": false,
          "relation": null
        },
        {
          "name": "Name",
          "json_name": "name",
          "type": "string",
          "db_type": "varchar(100)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null
        },
        {
          "name": "Price",
          "json_name": "price",
          "type": "float64",
          "db_type": "decimal(10,2)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null
        },
        {
          "name": "ImageURL",
          "json_name": "image_url",
          "type": "string",
          "db_type": "varchar(500)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": true,
          "relation": null,
          "hints": ["image_field"]
        },
        {
          "name": "CategoryID",
          "json_name": "category_id",
          "type": "uint",
          "db_type": "bigint",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": {
            "type": "belongs_to",
            "model": "Category",
            "foreign_key": "CategoryID",
            "references": "ID"
          }
        }
      ],
      "relations_summary": [
        { "type": "belongs_to", "target": "Category", "via": "CategoryID" },
        { "type": "has_many", "target": "OrderItem", "via": "ProductID" }
      ]
    },
    {
      "name": "Category",
      "source_file": "internal/model/category.go",
      "framework": "gorm",
      "table_name": "categories",
      "fields": [
        {
          "name": "ID",
          "json_name": "id",
          "type": "uint",
          "db_type": "bigint",
          "primary_key": true,
          "auto_increment": true,
          "nullable": false,
          "relation": null
        },
        {
          "name": "Name",
          "json_name": "name",
          "type": "string",
          "db_type": "varchar(50)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null
        },
        {
          "name": "IconURL",
          "json_name": "icon_url",
          "type": "string",
          "db_type": "varchar(500)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": true,
          "relation": null,
          "hints": ["image_field"]
        }
      ],
      "relations_summary": [
        { "type": "has_many", "target": "Product", "via": "CategoryID" }
      ]
    }
  ]
}
```

**Field hints 说明**：
- `image_field` — 字段名含 `image`, `img`, `avatar`, `photo`, `icon`, `logo`, `banner`, `thumbnail`, `cover` 之一，或类型为 `ImageField`
- `file_field` — 字段名含 `file`, `attachment`, `document`，或类型为 `FileField`
- 这些 hints 后续用于判断是否需要上传 API

---

## 2. API 端点提取 / API Endpoint Extraction

扫描 Controller / Handler / Router / View 代码，提取所有 CRUD 端点。

### 2.1 Per-Framework Scanning Table

#### Go + Gin

| 项目 | 值 |
|------|-----|
| **Glob** | `**/*.go` |
| **Grep (routes)** | `\.POST\(` / `\.PUT\(` / `\.GET\(` / `\.DELETE\(` / `\.PATCH\(` |
| **Grep (groups)** | `\.Group\(` — 获取路由前缀 |
| **路由 → Handler** | `router.POST("/products", handler.CreateProduct)` → handler 函数名 |
| **Handler → Param** | 在 handler 函数内找 `c.ShouldBindJSON(&xxx)` 或 `c.Bind(&xxx)` → 参数 struct |
| **文件上传** | `c.FormFile(` 或 `c.MultipartForm()` → 标记为 upload endpoint |

#### Go + Echo

| 项目 | 值 |
|------|-----|
| **Glob** | `**/*.go` |
| **Grep (routes)** | `\.POST\(` / `\.PUT\(` / `\.GET\(` / `\.DELETE\(` (同 Gin 但 context 是 `echo.Context`) |
| **Grep (groups)** | `\.Group\(` |
| **Handler → Param** | `c.Bind(&xxx)` → 参数 struct |
| **文件上传** | `c.FormFile(` |

#### NestJS (TypeORM or Prisma)

| 项目 | 值 |
|------|-----|
| **Glob** | `**/*.controller.ts` |
| **Grep (routes)** | `@Post\(` / `@Put\(` / `@Get\(` / `@Delete\(` / `@Patch\(` |
| **Controller prefix** | `@Controller('products')` → base path `/products` |
| **Handler → Param** | `@Body() dto: CreateProductDto` → DTO class name |
| **DTO 定义** | Glob `**/*.dto.ts` → 找到 DTO class 的字段定义 |
| **文件上传** | `@UseInterceptors(FileInterceptor` 或 `@UploadedFile()` |

#### Express + Mongoose

| 项目 | 值 |
|------|-----|
| **Glob** | `**/*.route.js`, `**/*.router.js`, `**/routes/*.js` (同理 `.ts`) |
| **Grep (routes)** | `router\.post\(` / `router\.put\(` / `router\.get\(` / `router\.delete\(` |
| **也检查** | `app\.post\(` — 部分项目直接在 app 上挂路由 |
| **Handler → Param** | handler 函数内 `req.body.xxx` 或 `req.body` 解构 → 提取字段列表 |
| **文件上传** | `multer` / `upload.single(` / `upload.array(` |

#### Django REST Framework

| 项目 | 值 |
|------|-----|
| **Glob** | `**/views.py`, `**/viewsets.py`, `**/views/*.py` |
| **Grep (ViewSet)** | `ViewSet` 或 `ModelViewSet` — 自带 CRUD |
| **Grep (api_view)** | `@api_view\(` — 函数式视图 |
| **Grep (urls)** | `**/urls.py` → `router.register` 或 `path()` 映射 |
| **ViewSet → Serializer** | `serializer_class = ProductSerializer` → 找 Serializer 定义 |
| **Serializer 定义** | Glob `**/serializers.py` → `class ProductSerializer` → `fields` |
| **文件上传** | `FileUploadParser` / `MultiPartParser` |

#### FastAPI + SQLAlchemy

| 项目 | 值 |
|------|-----|
| **Glob** | `**/*.py` |
| **Grep (routes)** | `@app\.post\(` / `@router\.post\(` / `@app\.put\(` / `@router\.put\(` 等 |
| **Handler → Param** | 函数参数类型标注 `def create_product(product: ProductCreate)` → Pydantic model |
| **Pydantic 定义** | Glob `**/schemas.py` 或 `**/schema/*.py` → `class ProductCreate(BaseModel)` |
| **文件上传** | `UploadFile` 参数类型 |

### 2.2 Scanning Summary / 扫描策略汇总

| Framework | Route Grep | Param Discovery | Upload Detection |
|-----------|-----------|-----------------|------------------|
| Go+Gin | `\.POST\(`, `\.Group\(` | `ShouldBindJSON(&xxx)` → struct | `c.FormFile(` |
| Go+Echo | `\.POST\(`, `\.Group\(` | `c.Bind(&xxx)` → struct | `c.FormFile(` |
| NestJS | `@Post\(`, `@Controller\(` | `@Body() dto: XxxDto` → DTO class | `@UploadedFile()` |
| Express | `router\.post\(`, `app\.post\(` | `req.body` 解构 | `multer`, `upload.single(` |
| Django REST | `ViewSet`, `@api_view`, urls.py | `serializer_class` → Serializer | `FileUploadParser` |
| FastAPI | `@app\.post\(`, `@router\.post\(` | 函数参数 type hint → Pydantic | `UploadFile` |

### 2.3 API Endpoint Output Example / API 端点提取输出示例

```json
{
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/v1/products",
      "full_pattern": "/api/v1/products",
      "handler": "CreateProduct",
      "source_file": "internal/handler/product.go",
      "source_line": 42,
      "param_struct": "CreateProductRequest",
      "param_fields": [
        { "name": "name", "type": "string", "required": true },
        { "name": "price", "type": "float64", "required": true },
        { "name": "category_id", "type": "uint", "required": true },
        { "name": "description", "type": "string", "required": false }
      ],
      "is_upload": false,
      "auth_required": true,
      "tags": ["create", "product"]
    },
    {
      "method": "POST",
      "path": "/api/v1/upload/image",
      "full_pattern": "/api/v1/upload/image",
      "handler": "UploadImage",
      "source_file": "internal/handler/upload.go",
      "source_line": 15,
      "param_struct": null,
      "param_fields": [
        { "name": "file", "type": "multipart/file", "required": true },
        { "name": "type", "type": "string", "required": false }
      ],
      "is_upload": true,
      "auth_required": true,
      "tags": ["upload", "image"]
    },
    {
      "method": "POST",
      "path": "/api/v1/auth/login",
      "full_pattern": "/api/v1/auth/login",
      "handler": "Login",
      "source_file": "internal/handler/auth.go",
      "source_line": 28,
      "param_struct": "LoginRequest",
      "param_fields": [
        { "name": "username", "type": "string", "required": true },
        { "name": "password", "type": "string", "required": true }
      ],
      "is_upload": false,
      "auth_required": false,
      "tags": ["auth", "login"]
    },
    {
      "method": "DELETE",
      "path": "/api/v1/products/:id",
      "full_pattern": "/api/v1/products/:id",
      "handler": "DeleteProduct",
      "source_file": "internal/handler/product.go",
      "source_line": 98,
      "param_struct": null,
      "param_fields": [
        { "name": "id", "type": "uint", "required": true, "in": "path" }
      ],
      "is_upload": false,
      "auth_required": true,
      "tags": ["delete", "product"]
    },
    {
      "method": "GET",
      "path": "/api/v1/products",
      "full_pattern": "/api/v1/products",
      "handler": "ListProducts",
      "source_file": "internal/handler/product.go",
      "source_line": 12,
      "param_struct": null,
      "param_fields": [
        { "name": "page", "type": "int", "required": false, "in": "query" },
        { "name": "size", "type": "int", "required": false, "in": "query" }
      ],
      "is_upload": false,
      "auth_required": true,
      "tags": ["list", "product"]
    }
  ],
  "auth_endpoints": [
    {
      "method": "POST",
      "path": "/api/v1/auth/login",
      "token_location": "response.data.token"
    }
  ],
  "upload_endpoints": [
    {
      "method": "POST",
      "path": "/api/v1/upload/image",
      "file_param": "file",
      "response_url_field": "data.url"
    }
  ]
}
```

---

## 3. 模型-API 映射 / Model-API Mapping

将提取的数据模型与 API 端点建立对应关系。三种匹配策略按优先级组合使用。

### 3.1 Name Similarity / 名称相似度匹配

最基础的匹配方式：模型名与路由路径之间的映射。

**规则**：
- `User` model → 匹配 `/api/users`, `/api/v1/users`, `/users`
- 转换规则: `PascalCase → snake_case → plural` — `OrderItem` → `order_items` → `/api/order_items` 或 `/api/order-items`
- 也检查 kebab-case: `OrderItem` → `order-items`

**实现**：
```
model_name_lower = to_snake_case(model.name)        # "order_item"
model_name_plural = pluralize(model_name_lower)      # "order_items"
model_name_kebab = model_name_lower.replace("_","-") # "order-item"

for endpoint in endpoints:
    path_segments = endpoint.path.split("/")
    if model_name_plural in path_segments or model_name_kebab + "s" in path_segments:
        match(model, endpoint)
```

### 3.2 Parameter Matching / 参数字段匹配

当名称匹配有歧义时，通过参数字段进一步确认。

**规则**：
- API 的 `param_fields` 与 model 的 `fields` 比较
- 计算字段名重叠率 (Jaccard similarity)
- 重叠率 > 0.5 认为匹配

**示例**：
```
Model "Product" fields:   [name, price, description, category_id, image_url]
API POST /products params: [name, price, description, category_id]
重叠: 4/5 = 0.8 → 强匹配

API POST /orders params:  [user_id, product_id, quantity]
重叠: 0/5 = 0.0 → 不匹配
```

### 3.3 Route Pattern Matching / RESTful 路由约定匹配

利用 RESTful 约定推断完整 CRUD 集合。

**RESTful 约定**：
```
GET    /api/{model_plural}         → List
POST   /api/{model_plural}         → Create
GET    /api/{model_plural}/:id     → Get
PUT    /api/{model_plural}/:id     → Update
PATCH  /api/{model_plural}/:id     → Partial Update
DELETE /api/{model_plural}/:id     → Delete
```

**非标路由检测**：
- `POST /api/{model_plural}/batch` → Bulk Create
- `POST /api/{model_plural}/import` → Import
- `GET  /api/{model_plural}/export` → Export
- `POST /api/upload` → 通用上传 (需关联到具体 model)

### 3.4 Mapping Output Example / 映射输出示例

```json
{
  "model_api_mapping": [
    {
      "model": "Product",
      "match_confidence": "high",
      "match_method": ["name_similarity", "param_matching"],
      "apis": {
        "create": { "method": "POST", "path": "/api/v1/products" },
        "list":   { "method": "GET",  "path": "/api/v1/products" },
        "get":    { "method": "GET",  "path": "/api/v1/products/:id" },
        "update": { "method": "PUT",  "path": "/api/v1/products/:id" },
        "delete": { "method": "DELETE", "path": "/api/v1/products/:id" }
      },
      "has_upload": false,
      "upload_via": "/api/v1/upload/image"
    },
    {
      "model": "Category",
      "match_confidence": "medium",
      "match_method": ["name_similarity"],
      "apis": {
        "create": null,
        "list":   { "method": "GET", "path": "/api/v1/categories" },
        "get":    null,
        "update": null,
        "delete": null
      },
      "has_upload": false,
      "upload_via": null
    }
  ]
}
```

---

## 4. API 缺口检测 / API Gap Detection (核心增值点)

对每个数据模型逐一检查 CRUD 完整性，标记缺口。这些缺口直接影响 demo-forge 后续步骤能否执行，也是给用户的高价值反馈。

### 4.1 检测规则

#### Rule 1: 无创建接口 (No Create Endpoint)

```
IF model has no POST endpoint mapped:
    gap_type = "NO_CREATE_API"
    severity = "critical"
    message = "API_GAP: 无创建接口, model={name}"
    impact = "demo-forge 无法为该模型灌入数据"
```

这是最严重的缺口。没有创建接口意味着 demo-forge 完全无法为这个模型创建演示数据。

#### Rule 2: 无上传接口 (No Upload Endpoint)

```
IF model has fields with hints ["image_field", "file_field"]:
    IF no upload endpoint found globally:
        gap_type = "NO_UPLOAD_API"
        severity = "high"
        message = "API_GAP: 无上传接口, model={name}, fields={image_fields}"
        impact = "图片/文件字段只能填 URL 字符串，无法上传真实文件"
    ELIF upload endpoint exists but model has no image URL field:
        gap_type = "UPLOAD_FIELD_MISMATCH"
        severity = "medium"
        message = "API_GAP: 模型有图片字段但无法关联上传结果"
```

检查所有含图片/文件字段的模型是否有对应的上传途径。

#### Rule 3: 无批量创建 (No Bulk Create)

```
IF model.count_plan > 20:
    IF no bulk create endpoint (POST /xxx/batch or POST /xxx/import):
        gap_type = "NO_BULK_CREATE"
        severity = "low"
        message = "API_GAP: 无批量创建接口, model={name}, 将逐条创建"
        impact = "灌入效率低，需逐条 POST，数量大时耗时"
```

不阻塞灌入，但会影响效率。标记供用户参考。

#### Rule 4: 无认证接口 (No Auth Endpoint)

```
IF no endpoint with tags ["auth", "login"] found:
    IF any endpoint has auth_required = true:
        gap_type = "NO_AUTH_API"
        severity = "critical"
        message = "API_GAP: 无认证接口, 但存在需认证的端点"
        impact = "demo-forge 无法自动获取 token，需用户手动提供"
```

没有认证接口意味着无法自动登录，需要用户手动提供 token。

#### Rule 5: 无删除接口 (No Delete Endpoint)

```
IF model has create endpoint but no DELETE endpoint:
    gap_type = "NO_DELETE_API"
    severity = "medium"
    message = "API_GAP: 无删除接口, model={name}, 灌入后无法通过 API 清理"
    impact = "demo-forge clean 命令无法清理该模型的数据"
```

灌入后无法通过 `demo-forge clean` 清理，需要用户手动清理数据库。

### 4.2 Severity 级别

| Severity | 含义 | 对 demo-forge 的影响 |
|----------|------|---------------------|
| `critical` | 阻塞灌入 | 该模型完全无法灌入，或所有需认证的 API 无法调用 |
| `high` | 功能缺失 | 灌入可进行但不完整（如缺图片） |
| `medium` | 体验降级 | 灌入可进行但有限制（如无法清理） |
| `low` | 效率问题 | 灌入可进行但效率低（如逐条创建） |

### 4.3 Gap Detection Output Example / 缺口检测输出示例

```json
{
  "gaps": [
    {
      "gap_type": "NO_CREATE_API",
      "severity": "critical",
      "model": "Category",
      "message": "API_GAP: 无创建接口, model=Category",
      "impact": "demo-forge 无法为 Category 灌入数据，依赖 Category 的 Product 也无法正确关联",
      "suggestion": "需要实现 POST /api/v1/categories 接口"
    },
    {
      "gap_type": "NO_UPLOAD_API",
      "severity": "high",
      "model": "Product",
      "fields": ["image_url"],
      "message": "API_GAP: 无上传接口, model=Product, fields=[image_url]",
      "impact": "Product 的 image_url 字段只能填占位 URL，无法上传真实图片",
      "suggestion": "需要实现 POST /api/v1/upload/image 接口，返回上传后的 URL"
    },
    {
      "gap_type": "NO_DELETE_API",
      "severity": "medium",
      "model": "Product",
      "message": "API_GAP: 无删除接口, model=Product",
      "impact": "灌入后 demo-forge clean 无法清理 Product 数据",
      "suggestion": "需要实现 DELETE /api/v1/products/:id 接口"
    },
    {
      "gap_type": "NO_BULK_CREATE",
      "severity": "low",
      "model": "Product",
      "message": "API_GAP: 无批量创建接口, model=Product, 将逐条创建",
      "impact": "50 个 Product 需要发送 50 次 POST 请求",
      "suggestion": "可选实现 POST /api/v1/products/batch 接口"
    }
  ],
  "summary": {
    "total_models": 5,
    "models_with_gaps": 3,
    "critical_gaps": 1,
    "high_gaps": 1,
    "medium_gaps": 1,
    "low_gaps": 1
  }
}
```

---

## 5. 用户确认点 / User Confirmation Points

Step 0 完成分析后，需要向用户展示结果并获取确认。

### 5.1 展示内容

**模型识别结果**：
```
扫描完成，发现以下数据模型：

  Model          Fields  Relations  Source
  ─────          ──────  ─────────  ──────
  User           8       2          internal/model/user.go
  Category       4       1          internal/model/category.go
  Product        10      3          internal/model/product.go
  Order          7       2          internal/model/order.go
  OrderItem      5       2          internal/model/order_item.go

  共 5 个模型，34 个字段，10 个关系
```

**API 映射结果**：
```
API 映射结果：

  Model       Create  Read  Update  Delete  Upload
  ─────       ──────  ────  ──────  ──────  ──────
  User        POST    GET   PUT     DELETE  -
  Category    -       GET   -       -       -
  Product     POST    GET   PUT     -       via /upload
  Order       POST    GET   -       -       -
  OrderItem   -       -     -       -       -
```

**API 缺口警告**：
```
发现 API 缺口：

  [CRITICAL] Category 无创建接口 — 无法灌入分类数据
  [HIGH]     Product 无专属上传接口 — 需要通用上传接口
  [MEDIUM]   Product 无删除接口 — 灌入后无法通过 API 清理
  [MEDIUM]   Order 无删除接口 — 灌入后无法通过 API 清理
  [LOW]      Product 无批量创建 — 将逐条创建 (50 条)
```

### 5.2 向用户提问

需要用户确认的问题（按顺序提问）：

1. **模型识别是否正确？**
   - "以上 5 个模型是否都需要灌入演示数据？有没有遗漏的模型？"
   - 用户可能说 "OrderItem 不需要单独灌入，创建 Order 时会自动创建"

2. **API 映射是否正确？**
   - "API 映射对吗？特别是，创建 Product 是用 POST /api/v1/products 吗？"
   - 用户可能纠正 "创建分类用的是 POST /api/v1/admin/categories，你没扫到因为在另一个 module 里"

3. **API 缺口是否确实存在？**
   - "以上 API 缺口是否属实？有些可能是我没扫到的接口"
   - 用户可能说 "上传接口在 /api/v1/oss/upload，不是 /api/v1/upload/image"

4. **认证方式确认**
   - "登录接口是 POST /api/v1/auth/login 吗？用户名密码还是其他方式？"
   - "管理员账号是什么？（后续灌入数据需要）"

### 5.3 用户反馈处理

用户反馈后更新 `project-analysis.json`：
- 增删模型
- 修正 API 映射
- 标记已确认的缺口 vs 误报的缺口
- 补充遗漏的 API 端点（用户手动提供）

---

## 6. 输出格式 / Output Schemas

Step 0 产出两个文件，存放在项目根目录的 `.allforai/seed-forge/` 下。

### 6.1 project-analysis.json

完整 schema 与示例：

```json
{
  "$schema": "demo-forge/project-analysis",
  "version": "1.0",
  "generated_at": "2026-02-24T10:30:00Z",
  "project": {
    "name": "my-ecommerce",
    "root": "/home/user/projects/my-ecommerce",
    "framework": {
      "language": "go",
      "web_framework": "gin",
      "orm": "gorm",
      "detected_by": ["go.mod: github.com/gin-gonic/gin", "go.mod: gorm.io/gorm"]
    }
  },
  "models": [
    {
      "name": "User",
      "source_file": "internal/model/user.go",
      "source_line": 12,
      "framework": "gorm",
      "table_name": "users",
      "fields": [
        {
          "name": "ID",
          "json_name": "id",
          "type": "uint",
          "db_type": "bigint",
          "primary_key": true,
          "auto_increment": true,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "Username",
          "json_name": "username",
          "type": "string",
          "db_type": "varchar(50)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "Email",
          "json_name": "email",
          "type": "string",
          "db_type": "varchar(100)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "Avatar",
          "json_name": "avatar",
          "type": "string",
          "db_type": "varchar(500)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": true,
          "relation": null,
          "hints": ["image_field"]
        },
        {
          "name": "Role",
          "json_name": "role",
          "type": "string",
          "db_type": "varchar(20)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        }
      ],
      "relations_summary": [
        { "type": "has_many", "target": "Order", "via": "UserID" }
      ]
    },
    {
      "name": "Category",
      "source_file": "internal/model/category.go",
      "source_line": 8,
      "framework": "gorm",
      "table_name": "categories",
      "fields": [
        {
          "name": "ID",
          "json_name": "id",
          "type": "uint",
          "db_type": "bigint",
          "primary_key": true,
          "auto_increment": true,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "Name",
          "json_name": "name",
          "type": "string",
          "db_type": "varchar(50)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "IconURL",
          "json_name": "icon_url",
          "type": "string",
          "db_type": "varchar(500)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": true,
          "relation": null,
          "hints": ["image_field"]
        },
        {
          "name": "SortOrder",
          "json_name": "sort_order",
          "type": "int",
          "db_type": "int",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        }
      ],
      "relations_summary": [
        { "type": "has_many", "target": "Product", "via": "CategoryID" }
      ]
    },
    {
      "name": "Product",
      "source_file": "internal/model/product.go",
      "source_line": 10,
      "framework": "gorm",
      "table_name": "products",
      "fields": [
        {
          "name": "ID",
          "json_name": "id",
          "type": "uint",
          "db_type": "bigint",
          "primary_key": true,
          "auto_increment": true,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "Name",
          "json_name": "name",
          "type": "string",
          "db_type": "varchar(100)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "Description",
          "json_name": "description",
          "type": "string",
          "db_type": "text",
          "primary_key": false,
          "auto_increment": false,
          "nullable": true,
          "relation": null,
          "hints": []
        },
        {
          "name": "Price",
          "json_name": "price",
          "type": "float64",
          "db_type": "decimal(10,2)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "ImageURL",
          "json_name": "image_url",
          "type": "string",
          "db_type": "varchar(500)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": true,
          "relation": null,
          "hints": ["image_field"]
        },
        {
          "name": "Stock",
          "json_name": "stock",
          "type": "int",
          "db_type": "int",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "CategoryID",
          "json_name": "category_id",
          "type": "uint",
          "db_type": "bigint",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": {
            "type": "belongs_to",
            "model": "Category",
            "foreign_key": "CategoryID",
            "references": "ID"
          },
          "hints": []
        },
        {
          "name": "Status",
          "json_name": "status",
          "type": "string",
          "db_type": "varchar(20)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        }
      ],
      "relations_summary": [
        { "type": "belongs_to", "target": "Category", "via": "CategoryID" },
        { "type": "has_many", "target": "OrderItem", "via": "ProductID" }
      ]
    },
    {
      "name": "Order",
      "source_file": "internal/model/order.go",
      "source_line": 10,
      "framework": "gorm",
      "table_name": "orders",
      "fields": [
        {
          "name": "ID",
          "json_name": "id",
          "type": "uint",
          "db_type": "bigint",
          "primary_key": true,
          "auto_increment": true,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "OrderNo",
          "json_name": "order_no",
          "type": "string",
          "db_type": "varchar(32)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "UserID",
          "json_name": "user_id",
          "type": "uint",
          "db_type": "bigint",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": {
            "type": "belongs_to",
            "model": "User",
            "foreign_key": "UserID",
            "references": "ID"
          },
          "hints": []
        },
        {
          "name": "TotalAmount",
          "json_name": "total_amount",
          "type": "float64",
          "db_type": "decimal(10,2)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        },
        {
          "name": "Status",
          "json_name": "status",
          "type": "string",
          "db_type": "varchar(20)",
          "primary_key": false,
          "auto_increment": false,
          "nullable": false,
          "relation": null,
          "hints": []
        }
      ],
      "relations_summary": [
        { "type": "belongs_to", "target": "User", "via": "UserID" },
        { "type": "has_many", "target": "OrderItem", "via": "OrderID" }
      ]
    }
  ],
  "endpoints": [
    {
      "method": "POST",
      "path": "/api/v1/auth/login",
      "handler": "Login",
      "source_file": "internal/handler/auth.go",
      "source_line": 28,
      "param_struct": "LoginRequest",
      "param_fields": [
        { "name": "username", "type": "string", "required": true },
        { "name": "password", "type": "string", "required": true }
      ],
      "is_upload": false,
      "auth_required": false,
      "tags": ["auth", "login"]
    },
    {
      "method": "POST",
      "path": "/api/v1/users",
      "handler": "CreateUser",
      "source_file": "internal/handler/user.go",
      "source_line": 35,
      "param_struct": "CreateUserRequest",
      "param_fields": [
        { "name": "username", "type": "string", "required": true },
        { "name": "email", "type": "string", "required": true },
        { "name": "password", "type": "string", "required": true },
        { "name": "role", "type": "string", "required": false }
      ],
      "is_upload": false,
      "auth_required": true,
      "tags": ["create", "user"]
    },
    {
      "method": "GET",
      "path": "/api/v1/users",
      "handler": "ListUsers",
      "source_file": "internal/handler/user.go",
      "source_line": 12,
      "param_struct": null,
      "param_fields": [],
      "is_upload": false,
      "auth_required": true,
      "tags": ["list", "user"]
    },
    {
      "method": "DELETE",
      "path": "/api/v1/users/:id",
      "handler": "DeleteUser",
      "source_file": "internal/handler/user.go",
      "source_line": 88,
      "param_struct": null,
      "param_fields": [
        { "name": "id", "type": "uint", "required": true, "in": "path" }
      ],
      "is_upload": false,
      "auth_required": true,
      "tags": ["delete", "user"]
    },
    {
      "method": "GET",
      "path": "/api/v1/categories",
      "handler": "ListCategories",
      "source_file": "internal/handler/category.go",
      "source_line": 10,
      "param_struct": null,
      "param_fields": [],
      "is_upload": false,
      "auth_required": true,
      "tags": ["list", "category"]
    },
    {
      "method": "POST",
      "path": "/api/v1/products",
      "handler": "CreateProduct",
      "source_file": "internal/handler/product.go",
      "source_line": 42,
      "param_struct": "CreateProductRequest",
      "param_fields": [
        { "name": "name", "type": "string", "required": true },
        { "name": "price", "type": "float64", "required": true },
        { "name": "description", "type": "string", "required": false },
        { "name": "category_id", "type": "uint", "required": true },
        { "name": "image_url", "type": "string", "required": false },
        { "name": "stock", "type": "int", "required": true }
      ],
      "is_upload": false,
      "auth_required": true,
      "tags": ["create", "product"]
    },
    {
      "method": "GET",
      "path": "/api/v1/products",
      "handler": "ListProducts",
      "source_file": "internal/handler/product.go",
      "source_line": 12,
      "param_struct": null,
      "param_fields": [
        { "name": "page", "type": "int", "required": false, "in": "query" },
        { "name": "size", "type": "int", "required": false, "in": "query" },
        { "name": "category_id", "type": "uint", "required": false, "in": "query" }
      ],
      "is_upload": false,
      "auth_required": true,
      "tags": ["list", "product"]
    },
    {
      "method": "PUT",
      "path": "/api/v1/products/:id",
      "handler": "UpdateProduct",
      "source_file": "internal/handler/product.go",
      "source_line": 70,
      "param_struct": "UpdateProductRequest",
      "param_fields": [
        { "name": "name", "type": "string", "required": false },
        { "name": "price", "type": "float64", "required": false },
        { "name": "description", "type": "string", "required": false },
        { "name": "image_url", "type": "string", "required": false },
        { "name": "stock", "type": "int", "required": false }
      ],
      "is_upload": false,
      "auth_required": true,
      "tags": ["update", "product"]
    },
    {
      "method": "POST",
      "path": "/api/v1/orders",
      "handler": "CreateOrder",
      "source_file": "internal/handler/order.go",
      "source_line": 30,
      "param_struct": "CreateOrderRequest",
      "param_fields": [
        { "name": "items", "type": "array", "required": true,
          "item_fields": [
            { "name": "product_id", "type": "uint", "required": true },
            { "name": "quantity", "type": "int", "required": true }
          ]
        }
      ],
      "is_upload": false,
      "auth_required": true,
      "tags": ["create", "order"]
    },
    {
      "method": "GET",
      "path": "/api/v1/orders",
      "handler": "ListOrders",
      "source_file": "internal/handler/order.go",
      "source_line": 12,
      "param_struct": null,
      "param_fields": [],
      "is_upload": false,
      "auth_required": true,
      "tags": ["list", "order"]
    },
    {
      "method": "POST",
      "path": "/api/v1/upload/image",
      "handler": "UploadImage",
      "source_file": "internal/handler/upload.go",
      "source_line": 15,
      "param_struct": null,
      "param_fields": [
        { "name": "file", "type": "multipart/file", "required": true }
      ],
      "is_upload": true,
      "auth_required": true,
      "tags": ["upload", "image"]
    }
  ],
  "model_api_mapping": [
    {
      "model": "User",
      "match_confidence": "high",
      "match_method": ["name_similarity", "param_matching"],
      "apis": {
        "create": { "method": "POST", "path": "/api/v1/users" },
        "list":   { "method": "GET",  "path": "/api/v1/users" },
        "get":    null,
        "update": null,
        "delete": { "method": "DELETE", "path": "/api/v1/users/:id" }
      },
      "has_upload": false,
      "upload_via": "/api/v1/upload/image",
      "image_fields": ["avatar"]
    },
    {
      "model": "Category",
      "match_confidence": "medium",
      "match_method": ["name_similarity"],
      "apis": {
        "create": null,
        "list":   { "method": "GET", "path": "/api/v1/categories" },
        "get":    null,
        "update": null,
        "delete": null
      },
      "has_upload": false,
      "upload_via": null,
      "image_fields": ["icon_url"]
    },
    {
      "model": "Product",
      "match_confidence": "high",
      "match_method": ["name_similarity", "param_matching"],
      "apis": {
        "create": { "method": "POST", "path": "/api/v1/products" },
        "list":   { "method": "GET",  "path": "/api/v1/products" },
        "get":    null,
        "update": { "method": "PUT",  "path": "/api/v1/products/:id" },
        "delete": null
      },
      "has_upload": false,
      "upload_via": "/api/v1/upload/image",
      "image_fields": ["image_url"]
    },
    {
      "model": "Order",
      "match_confidence": "high",
      "match_method": ["name_similarity", "param_matching"],
      "apis": {
        "create": { "method": "POST", "path": "/api/v1/orders" },
        "list":   { "method": "GET",  "path": "/api/v1/orders" },
        "get":    null,
        "update": null,
        "delete": null
      },
      "has_upload": false,
      "upload_via": null,
      "image_fields": []
    }
  ],
  "auth": {
    "login_endpoint": {
      "method": "POST",
      "path": "/api/v1/auth/login"
    },
    "token_type": "bearer",
    "token_location": "response.data.token",
    "header_format": "Authorization: Bearer {token}"
  },
  "upload": {
    "endpoints": [
      {
        "method": "POST",
        "path": "/api/v1/upload/image",
        "file_param": "file",
        "response_url_field": "data.url",
        "accepted_types": ["image/jpeg", "image/png", "image/webp"]
      }
    ]
  },
  "user_confirmed": false,
  "user_corrections": []
}
```

### 6.2 api-gaps.json

完整 schema 与示例：

```json
{
  "$schema": "demo-forge/api-gaps",
  "version": "1.0",
  "generated_at": "2026-02-24T10:30:00Z",
  "source": "static_analysis",
  "gaps": [
    {
      "id": "GAP-001",
      "gap_type": "NO_CREATE_API",
      "severity": "critical",
      "model": "Category",
      "fields": null,
      "message": "API_GAP: 无创建接口, model=Category",
      "impact": "demo-forge 无法为 Category 灌入数据。Product 依赖 Category (category_id FK)，Category 缺失将导致 Product 灌入时 category_id 无法填入有效值",
      "suggestion": "需要实现 POST /api/v1/categories 接口，接收 name, icon_url, sort_order 字段",
      "detected_at": "step0",
      "confirmed": null
    },
    {
      "id": "GAP-002",
      "gap_type": "NO_UPLOAD_API",
      "severity": "high",
      "model": "Category",
      "fields": ["icon_url"],
      "message": "API_GAP: Category 有图片字段 icon_url 但无创建接口，上传也无从谈起",
      "impact": "Category 的 icon_url 无法填入真实图片 URL",
      "suggestion": "先解决 GAP-001 (创建接口)，然后通过通用上传接口 /api/v1/upload/image 上传 icon 图片",
      "detected_at": "step0",
      "confirmed": null
    },
    {
      "id": "GAP-003",
      "gap_type": "NO_DELETE_API",
      "severity": "medium",
      "model": "Product",
      "fields": null,
      "message": "API_GAP: 无删除接口, model=Product",
      "impact": "demo-forge clean 无法通过 API 清理 Product 数据，需要用户手动操作数据库",
      "suggestion": "实现 DELETE /api/v1/products/:id 接口",
      "detected_at": "step0",
      "confirmed": null
    },
    {
      "id": "GAP-004",
      "gap_type": "NO_DELETE_API",
      "severity": "medium",
      "model": "Order",
      "fields": null,
      "message": "API_GAP: 无删除接口, model=Order",
      "impact": "demo-forge clean 无法通过 API 清理 Order 数据",
      "suggestion": "实现 DELETE /api/v1/orders/:id 接口",
      "detected_at": "step0",
      "confirmed": null
    },
    {
      "id": "GAP-005",
      "gap_type": "NO_BULK_CREATE",
      "severity": "low",
      "model": "Product",
      "fields": null,
      "message": "API_GAP: 无批量创建接口, model=Product, 将逐条创建",
      "impact": "计划灌入 50 个 Product，需要发送 50 次 POST 请求，耗时约 25-50 秒",
      "suggestion": "可选实现 POST /api/v1/products/batch 接口接受数组",
      "detected_at": "step0",
      "confirmed": null
    }
  ],
  "summary": {
    "total_models_scanned": 4,
    "models_with_gaps": 3,
    "gap_counts": {
      "critical": 1,
      "high": 1,
      "medium": 2,
      "low": 1
    },
    "blocking_models": ["Category"],
    "clean_impossible_models": ["Product", "Order"]
  },
  "user_confirmed": false,
  "user_corrections": []
}
```

### 6.3 File 落盘位置

```
{project_root}/
└── .allforai/seed-forge/
    ├── project-analysis.json    ← 本步骤产出
    └── api-gaps.json            ← 本步骤产出
```

两个文件在用户确认后更新 `user_confirmed: true` 并写入 `user_corrections` 数组记录用户的修正内容。后续 Step 1/2/3/4 读取这两个文件作为输入。
