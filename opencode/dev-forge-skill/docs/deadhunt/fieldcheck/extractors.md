## 字段提取参考 — 各层提取策略

> 本文档定义了 4 层字段模型中每一层的字段提取方法。
> 每一层均提供：搜索命令、提取模式、输出 JSON 格式。
> Agent 应按 L4 → L3 → L2 → L1 的顺序逐层提取，最后进行跨层比对。

```
┌─────────────────────────────────────────────────────────┐
│  L1  UI 显示层    表格列 / 表单字段 / 模板绑定           │
│  L2  API 接口层   请求参数 / 响应字段 / DTO              │
│  L3  实体层       ORM Entity / Model / Struct            │
│  L4  数据库层     DDL / Migration / Schema 定义          │
└─────────────────────────────────────────────────────────┘
```

---

### L4: 数据库层提取

> 数据库层是字段的"事实来源"。所有字段名以数据库实际列名为准。
> 支持 9 种 ORM / Schema 定义方式 + SQL Migration 兜底。

#### Prisma

```bash
# 定位 schema 文件
find . -name "schema.prisma" -not -path "*/node_modules/*" 2>/dev/null

# 提取 model 块（含 @map 列名映射）
grep -n "^model\s\|^\s*\w.*@map\|^\s*\w.*@id\|^\s*\w.*@default\|^\s*@@map" \
  --include="*.prisma" -r prisma/ 2>/dev/null
```

提取规则：

| Prisma 语法 | 提取逻辑 |
|---|---|
| `model User {` | 表名 = `User` 的复数小写形式，或取 `@@map("xxx")` |
| `userName String` | 列名 = `userName`（Prisma 默认驼峰映射到蛇形） |
| `userName String @map("user_name")` | 列名 = `user_name`（`@map` 优先） |
| `@@map("t_user")` | 表名 = `t_user` |
| `isDeleted Boolean @default(false)` | 列名 = `isDeleted`，标记为系统字段 |
| `posts Post[]` | 跳过 — 关系字段，非数据库列 |

#### TypeORM

```bash
# 定位 Entity 文件
grep -rln "@Entity" --include="*.ts" server/src/ src/ 2>/dev/null

# 提取 @Column 及 @PrimaryGeneratedColumn
grep -n "@Column\|@PrimaryGeneratedColumn\|@Entity\|@CreateDateColumn\|@UpdateDateColumn\|@DeleteDateColumn" \
  --include="*.ts" -r server/src/ src/ 2>/dev/null
```

提取规则：

| TypeORM 语法 | 提取逻辑 |
|---|---|
| `@Entity("users")` | 表名 = `users` |
| `@Entity({ name: "t_user" })` | 表名 = `t_user` |
| `@Column()` | 列名 = 属性名 |
| `@Column({ name: "user_name" })` | 列名 = `user_name` |
| `@PrimaryGeneratedColumn()` | 列名 = 属性名，标记为主键 |
| `@CreateDateColumn()` | 列名 = 属性名，标记为系统字段 |
| `@Column({ select: false })` | 列存在但默认不查询，需标注 |

#### JPA / Hibernate (Java)

```bash
# 定位 Entity 类
grep -rln "@Entity" --include="*.java" src/ 2>/dev/null

# 提取表名和列定义
grep -n "@Table\|@Column\|@Id\|@Transient\|@JoinColumn\|@GeneratedValue" \
  --include="*.java" -r src/ 2>/dev/null
```

提取规则：

| JPA 语法 | 提取逻辑 |
|---|---|
| `@Table(name = "t_user")` | 表名 = `t_user` |
| `@Column(name = "user_name")` | 列名 = `user_name` |
| `@Column` 无 `name` | 列名 = 属性名（按 JPA 命名策略转换） |
| `@Id` + `@GeneratedValue` | 列名 = 属性名，标记为主键 |
| `@Transient` | **跳过** — 非持久化字段 |
| `@JoinColumn(name = "dept_id")` | 列名 = `dept_id`（外键列） |
| `@Enumerated(EnumType.STRING)` | 列存在，类型为 `varchar` |

#### GORM (Go)

```bash
# 定位含 gorm tag 的 struct
grep -rln 'gorm:"' --include="*.go" internal/ pkg/ models/ 2>/dev/null

# 提取字段定义
grep -n 'gorm:"\|type\s\+struct\s*{' --include="*.go" -r internal/ pkg/ models/ 2>/dev/null
```

提取规则：

| GORM 语法 | 提取逻辑 |
|---|---|
| `type User struct {` | 表名 = `users`（复数蛇形），或取 `TableName()` 方法 |
| `` UserName string `gorm:"column:user_name"` `` | 列名 = `user_name` |
| `` gorm:"primaryKey" `` | 标记为主键 |
| `` gorm:"-" `` | **跳过** — 非数据库字段 |
| `` gorm:"-:all" `` | **跳过** — 完全忽略 |
| `gorm.Model` (嵌入) | 展开为 `id`, `created_at`, `updated_at`, `deleted_at`，全部标记为系统字段 |

#### Django ORM (Python)

```bash
# 定位 models.py
find . -name "models.py" -not -path "*/migrations/*" -not -path "*/.venv/*" 2>/dev/null

# 提取字段定义
grep -n "models\.\w*Field\|class\s\+\w*(models.Model)\|db_column\|db_table" \
  --include="*.py" -r */models.py 2>/dev/null
```

提取规则：

| Django 语法 | 提取逻辑 |
|---|---|
| `class User(models.Model):` | 表名 = `{app_label}_user`，或取 `Meta.db_table` |
| `user_name = models.CharField(...)` | 列名 = `user_name` |
| `user_name = models.CharField(db_column="uname")` | 列名 = `uname` |
| `dept = models.ForeignKey(...)` | 列名 = `dept_id`（Django 自动追加 `_id`） |
| `dept = models.ForeignKey(db_column="department_id")` | 列名 = `department_id` |
| `models.OneToOneField(...)` | 同 ForeignKey，追加 `_id` |
| `models.ManyToManyField(...)` | **跳过** — 生成中间表，非当前表列 |

#### MyBatis (XML Mapper)

```bash
# 定位 mapper XML
find . -name "*Mapper.xml" -o -name "*mapper.xml" 2>/dev/null

# 提取 resultMap 映射
grep -n "<resultMap\|<result\s\|<id\s\|<association\|<collection" \
  --include="*.xml" -r src/main/resources/ mapper/ 2>/dev/null
```

提取规则：

| MyBatis 语法 | 提取逻辑 |
|---|---|
| `<resultMap type="User">` | 实体 = `User` |
| `<id column="id" property="id"/>` | 列名 = `id`，属性名 = `id`，标记主键 |
| `<result column="user_name" property="userName"/>` | 列名 = `user_name`，属性名 = `userName` |
| `<association property="dept">` | 嵌套实体，递归提取 |
| `SELECT` 语句中直接列出的列 | 兜底方案，当无 `resultMap` 时从 SQL 提取 |

#### Sequelize

```bash
# 定位 Model 定义
grep -rln "Model.init\|sequelize.define\|DataTypes\." --include="*.ts" --include="*.js" \
  server/ src/ 2>/dev/null

# 提取字段
grep -n "DataTypes\.\|type:\s*DataTypes\|field:\s*['\"]" --include="*.ts" --include="*.js" \
  -r server/ src/ 2>/dev/null
```

提取规则：

| Sequelize 语法 | 提取逻辑 |
|---|---|
| `User.init({ ... }, { tableName: 'users' })` | 表名 = `users` |
| `userName: { type: DataTypes.STRING }` | 列名 = `userName`（默认驼峰），开启 `underscored` 时为 `user_name` |
| `userName: { type: DataTypes.STRING, field: 'user_name' }` | 列名 = `user_name`（`field` 优先） |
| `{ underscored: true }` 选项 | 全局驼峰→蛇形转换 |
| `{ timestamps: true }` | 自动追加 `createdAt`, `updatedAt`，标记为系统字段 |
| `{ paranoid: true }` | 自动追加 `deletedAt`，标记为系统字段 |

#### Drizzle

```bash
# 定位 schema 文件
grep -rln "pgTable\|mysqlTable\|sqliteTable" --include="*.ts" src/ drizzle/ db/ 2>/dev/null

# 提取表和列定义
grep -n "pgTable\|mysqlTable\|sqliteTable\|varchar\|integer\|boolean\|text\|timestamp\|serial" \
  --include="*.ts" -r src/ drizzle/ db/ 2>/dev/null
```

提取规则：

| Drizzle 语法 | 提取逻辑 |
|---|---|
| `export const users = pgTable('users', { ... })` | 表名 = `users` |
| `userName: varchar('user_name', { length: 50 })` | 列名 = `user_name`（第一个参数为数据库列名） |
| `id: serial('id').primaryKey()` | 列名 = `id`，标记为主键 |
| `.notNull()` | nullable = `false` |
| `.default(...)` | 记录默认值 |

#### SQL Migration 兜底

> 当以上 ORM 均未检测到时，回退到直接解析 SQL migration 文件。

```bash
# 定位 migration 文件
find . -path "*/migrations/*" -name "*.sql" \
  -o -path "*/migrate/*" -name "*.sql" \
  -o -name "*.up.sql" \
  2>/dev/null | sort

# 提取 CREATE TABLE / ALTER TABLE
grep -n "CREATE TABLE\|ALTER TABLE\|ADD COLUMN\|DROP COLUMN" \
  --include="*.sql" -r migrations/ db/ 2>/dev/null
```

提取规则：

| SQL 语法 | 提取逻辑 |
|---|---|
| `CREATE TABLE users (` | 表名 = `users` |
| `user_name VARCHAR(50) NOT NULL` | 列名 = `user_name`，类型 = `varchar`，nullable = `false` |
| `ALTER TABLE users ADD COLUMN email VARCHAR(100)` | 追加列 `email` 到 `users` 表 |
| `ALTER TABLE users DROP COLUMN old_field` | 从结果中移除 `old_field` |
| `PRIMARY KEY (id)` | 标记 `id` 为主键 |

> **提取优先级**：ORM schema 定义 > SQL migration（因为 migration 可能包含已回滚的变更）。
> 当两者都存在时，以 ORM 为准，migration 用于交叉验证。

#### L4 输出格式

```json
{
  "layer": "L4",
  "source": "prisma/schema.prisma",
  "orm": "prisma",
  "tables": [
    {
      "name": "users",
      "raw_name": "User",
      "file": "prisma/schema.prisma",
      "line": 12,
      "columns": [
        { "name": "id", "type": "int", "nullable": false, "primary_key": true, "system_field": true },
        { "name": "user_name", "type": "varchar", "nullable": false, "primary_key": false, "system_field": false },
        { "name": "email", "type": "varchar", "nullable": false, "primary_key": false, "system_field": false },
        { "name": "dept_id", "type": "int", "nullable": true, "primary_key": false, "system_field": false },
        { "name": "created_at", "type": "timestamp", "nullable": false, "primary_key": false, "system_field": true },
        { "name": "updated_at", "type": "timestamp", "nullable": false, "primary_key": false, "system_field": true }
      ]
    }
  ]
}
```

---

### L3: 实体层提取

> 实体层是 ORM 映射后的代码表示。字段名可能与数据库列名不同（驼峰 vs 蛇形）。
> L3 的核心价值：记录 **属性名 → 列名** 的映射关系，供跨层比对使用。

#### Java Entity

```bash
# 定位 Entity 类（同 L4 JPA，但此处关注属性名而非列名）
grep -rln "@Entity" --include="*.java" src/ 2>/dev/null

# 提取类的所有字段声明
grep -n "private\s\+\w\+\s\+\w\+\s*;" --include="*.java" -r src/main/java/**/entity/ 2>/dev/null
```

提取规则：

| 代码模式 | 提取逻辑 |
|---|---|
| `private String userName;` | 属性名 = `userName` |
| `@Column(name = "user_name")` + `private String userName;` | 属性名 = `userName`，列映射 = `user_name` |
| 无 `@Column` 注解 | 列映射 = 按 JPA 命名策略推断（`ImplicitNamingStrategy`） |
| `@Transient private String fullName;` | **跳过** — 非持久化 |
| `@JsonIgnore private String password;` | 属性存在但标记为"不序列化"，L2 比对时需注意 |

#### Go Struct

```bash
# 提取 struct 字段及 tag
grep -A 1 "type\s\+\w\+\s\+struct" --include="*.go" -r internal/ pkg/ models/ 2>/dev/null

# 提取所有带 json/gorm tag 的字段
grep -n 'json:"\|gorm:"' --include="*.go" -r internal/ pkg/ models/ 2>/dev/null
```

提取规则：

| 代码模式 | 提取逻辑 |
|---|---|
| `` UserName string `json:"user_name" gorm:"column:user_name"` `` | 属性名 = `UserName`，JSON 名 = `user_name`，列名 = `user_name` |
| `` json:"-" `` | **JSON 层跳过**，但 gorm 层可能仍然存在 |
| `` json:"user_name,omitempty" `` | JSON 名 = `user_name`，omitempty 仅影响空值序列化 |
| `` gorm:"-" `` | 非数据库字段，L4 比对时排除 |
| 嵌入 `gorm.Model` | 展开为 `ID`, `CreatedAt`, `UpdatedAt`, `DeletedAt` |

#### TypeScript / Node Entity

```bash
# TypeORM Entity（属性视角）
grep -n "^\s*\w\+\s*[!?]*:" --include="*.ts" -r server/src/**/entities/ 2>/dev/null

# Prisma 生成的 Client 类型（自动生成，只读参考）
find . -path "*/node_modules/.prisma/client/index.d.ts" 2>/dev/null

# Sequelize Model 属性
grep -n "declare\s\+\w\+\s*[!?]*:" --include="*.ts" -r server/src/**/models/ 2>/dev/null
```

提取规则：

| 代码模式 | 提取逻辑 |
|---|---|
| `userName!: string;` | 属性名 = `userName` |
| `@Column({ name: "user_name" })` + `userName!: string;` | 属性名 = `userName`，列映射 = `user_name` |
| Prisma 生成的 `type User = { user_name: string }` | 属性名 = `user_name`（Prisma 客户端保持 schema 中的字段名） |

#### Python Model (Django / SQLAlchemy / Tortoise)

```bash
# Django Model 属性
grep -n "^\s*\w\+\s*=\s*models\.\w*Field" --include="*.py" -r */models.py 2>/dev/null

# SQLAlchemy Model 属性
grep -n "Column(\|mapped_column(" --include="*.py" -r app/models/ 2>/dev/null

# Tortoise ORM
grep -n "fields\.\w*Field" --include="*.py" -r app/models/ 2>/dev/null
```

提取规则：

| 代码模式 | 提取逻辑 |
|---|---|
| `user_name = models.CharField(...)` | 属性名 = `user_name` |
| `user_name = Column(String, name="uname")` | 属性名 = `user_name`，列映射 = `uname` |
| `dept = models.ForeignKey(...)` | 属性名 = `dept`，实际列 = `dept_id` |
| `class Meta: db_table = 't_user'` | 表映射用，非字段 |

#### L3 输出格式

```json
{
  "layer": "L3",
  "source": "server/src/entities/user.entity.ts",
  "entities": [
    {
      "name": "User",
      "table_mapping": "users",
      "file": "server/src/entities/user.entity.ts",
      "line": 5,
      "fields": [
        {
          "name": "id",
          "type": "number",
          "column_mapping": "id",
          "system_field": true,
          "serialization_ignored": false
        },
        {
          "name": "userName",
          "type": "string",
          "column_mapping": "user_name",
          "system_field": false,
          "serialization_ignored": false
        },
        {
          "name": "email",
          "type": "string",
          "column_mapping": "email",
          "system_field": false,
          "serialization_ignored": false
        },
        {
          "name": "password",
          "type": "string",
          "column_mapping": "password",
          "system_field": false,
          "serialization_ignored": true,
          "ignore_annotation": "@JsonIgnore"
        },
        {
          "name": "createdAt",
          "type": "Date",
          "column_mapping": "created_at",
          "system_field": true,
          "serialization_ignored": false
        }
      ]
    }
  ]
}
```

---

### L2: API 接口层提取

> API 层定义了前后端之间传输的字段。DTO/VO 中的字段名可能与 Entity 不同。
> 按置信度从高到低，共 4 种提取策略。Agent 命中第一种即可，无需继续。

#### 策略 1（最高置信度）：OpenAPI / Swagger 文档

```bash
# 定位 OpenAPI 文档
find . -name "swagger.json" -o -name "openapi.json" -o -name "swagger.yaml" \
  -o -name "openapi.yaml" -o -name "api-docs.json" 2>/dev/null

# 如果是运行时生成的 Swagger（NestJS / Spring Boot），查找配置
grep -rn "SwaggerModule\|@EnableSwagger2\|springdoc\|springfox" \
  --include="*.ts" --include="*.java" --include="*.yaml" -r . 2>/dev/null
```

提取规则：
- `paths.{endpoint}.{method}.requestBody.content.application/json.schema` → 请求字段
- `paths.{endpoint}.{method}.responses.200.content.application/json.schema` → 响应字段
- `$ref` 引用递归解析至 `components.schemas` / `definitions`
- `readOnly: true` 的字段只在响应中出现
- `writeOnly: true` 的字段只在请求中出现

#### 策略 2（高置信度）：DTO / VO 类定义

```bash
# Java DTO / VO
find . -name "*DTO.java" -o -name "*Dto.java" -o -name "*VO.java" \
  -o -name "*Vo.java" -o -name "*Request.java" -o -name "*Response.java" 2>/dev/null

# TypeScript DTO（NestJS 风格）
find . -name "*.dto.ts" -o -name "*.vo.ts" -o -name "*.request.ts" \
  -o -name "*.response.ts" 2>/dev/null | grep -v node_modules

# Python Pydantic Schema / DRF Serializer
grep -rln "BaseModel\|Serializer" --include="*.py" -r app/ */schemas/ */serializers/ 2>/dev/null
```

DTO 字段提取规则（Java）：

| 注解 | 提取逻辑 |
|---|---|
| `@JsonProperty("user_name")` | API 字段名 = `user_name`（覆盖属性名） |
| `@ApiModelProperty(hidden = true)` | **跳过** — Swagger 中隐藏 |
| `@ApiModelProperty(value = "用户名")` | 提取为字段描述 |
| `@NotNull` / `@NotBlank` | 标记为必填字段 |
| `@JsonIgnore` | **跳过** — 不参与序列化 |
| `private String userName;`（无注解） | API 字段名 = `userName` |

DTO 字段提取规则（TypeScript / NestJS）：

| 装饰器 | 提取逻辑 |
|---|---|
| `@ApiProperty()` | 标记为 Swagger 可见字段 |
| `@ApiHideProperty()` | **跳过** |
| `@Exclude()` | **跳过** — class-transformer 排除 |
| `@Expose({ name: 'user_name' })` | API 字段名 = `user_name` |
| `@IsString()` / `@IsNotEmpty()` | 标记类型和必填 |
| `@Transform(...)` | 字段存在但值可能变换，需标注 |

DTO 字段提取规则（Python Pydantic）：

| 语法 | 提取逻辑 |
|---|---|
| `user_name: str` | API 字段名 = `user_name` |
| `user_name: str = Field(alias="userName")` | API 字段名 = `userName`（alias 优先） |
| `model_config = ConfigDict(populate_by_name=True)` | 允许用属性名或 alias |
| `@field_serializer` | 字段存在但输出可能变换 |

DTO 字段提取规则（Django REST Framework Serializer）：

| 语法 | 提取逻辑 |
|---|---|
| `user_name = serializers.CharField()` | API 字段名 = `user_name` |
| `user_name = serializers.CharField(source="profile.name")` | API 字段名 = `user_name`，映射到嵌套属性 |
| `class Meta: fields = [...]` | 白名单，只有列出的字段暴露到 API |
| `class Meta: exclude = [...]` | 黑名单，排除的字段不暴露 |
| `read_only_fields = [...]` | 只在响应中出现 |

#### 策略 3（中等置信度）：前端 API 定义文件

```bash
# 前端 TypeScript 接口定义（通常与 API 调用放在一起）
find src/api/ src/services/ -name "*.ts" -o -name "*.js" 2>/dev/null | grep -v node_modules

# 提取 interface / type 定义
grep -n "interface\s\+\w\+\|type\s\+\w\+\s*=" --include="*.ts" \
  -r src/api/ src/services/ src/types/ 2>/dev/null
```

提取规则：

| 代码模式 | 提取逻辑 |
|---|---|
| `interface UserDTO { userName: string; email: string; }` | 字段 = `userName`, `email` |
| `type CreateUserReq = { user_name: string; }` | 字段 = `user_name` |
| `interface UserVO extends BaseVO { ... }` | 递归合并父接口字段 |
| `Partial<User>` | 所有字段变为可选 |
| `Pick<User, 'id' \| 'name'>` | 只取指定字段 |
| `Omit<User, 'password'>` | 排除指定字段 |

#### 策略 4（低置信度兜底）：路由 handler 推断

> 仅当策略 1-3 均无结果时使用。从 controller / route handler 代码推断字段。

```bash
# NestJS controller
grep -n "@Body\|@Query\|@Param\|@Res\|return\s" --include="*.ts" \
  -r server/src/**/controllers/ server/src/**/*.controller.ts 2>/dev/null

# Express handler
grep -n "req\.body\.\|req\.query\.\|req\.params\.\|res\.json\|res\.send" \
  --include="*.ts" --include="*.js" -r server/src/ routes/ 2>/dev/null

# FastAPI (Python)
grep -n "async def\|def\s\+\w\+(.*Request\|.*Body\|.*Query" \
  --include="*.py" -r app/api/ app/routers/ 2>/dev/null

# Gin / Echo (Go)
grep -n 'c\.Bind\|c\.ShouldBind\|c\.JSON\|c\.Query(' --include="*.go" \
  -r internal/handler/ api/ 2>/dev/null

# Spring MVC (Java)
grep -n "@RequestBody\|@RequestParam\|ResponseEntity\|return\s" \
  --include="*.java" -r src/main/java/**/controller/ 2>/dev/null
```

推断规则：

| 代码模式 | 推断逻辑 | 置信度 |
|---|---|---|
| `@Body() dto: CreateUserDto` | 请求字段 = `CreateUserDto` 的属性 | 中 — 需要找到 DTO 定义 |
| `req.body.userName` | 请求包含 `userName` 字段 | 低 — 可能不完整 |
| `const { name, email } = req.body` | 请求包含 `name`, `email` | 低 — 解构可能不完整 |
| `res.json({ id, userName, email })` | 响应包含 `id`, `userName`, `email` | 低 — 可能是部分字段 |
| `c.ShouldBindJSON(&req)` | 请求字段 = `req` 结构体的 json tag | 中 — 需要找到结构体 |

#### Dart 模型类（Dart L2）

> Flutter 客户端的 API 层字段通过 Dart 模型类（`fromJson`/`toJson`）定义。

```bash
# json_serializable 模型
grep -rln "JsonSerializable\|@JsonKey" --include="*.dart" lib/ 2>/dev/null

# freezed 模型
grep -rln "@freezed\|@Freezed" --include="*.dart" lib/ 2>/dev/null

# 手动 fromJson
grep -rln "fromJson\|toJson" --include="*.dart" lib/ 2>/dev/null

# Retrofit 定义
grep -rn "@GET\|@POST\|@PUT\|@DELETE" --include="*.dart" lib/ 2>/dev/null
```

提取规则：

| 序列化方式 | 代码模式 | 提取逻辑 |
|-----------|---------|---------|
| json_serializable | `@JsonKey(name: 'user_name') String userName` | API 字段名 = `user_name`（`@JsonKey` 优先） |
| json_serializable | `String userName` (无 @JsonKey) | API 字段名 = `userName`（属性名即字段名） |
| freezed | `@FreezedUnionValue('userType') String type` | 联合类型值 = `userType` |
| freezed | `required String userName` | API 字段名 = `userName` |
| 手动 fromJson | `userName = json['user_name'] as String` | API 字段名 = `user_name` |
| 手动 fromJson | `email = json['email'] as String?` | API 字段名 = `email`，nullable |
| Retrofit | `@GET('/api/users') Future<List<User>> getUsers()` | 关联 `User` 模型的字段 |

Dart L2 输出格式与通用 L2 格式一致，`strategy` 字段标记为 `"dart_model"`。

#### L2 输出格式

```json
{
  "layer": "L2",
  "source": "openapi.json",
  "strategy": "openapi",
  "endpoints": [
    {
      "path": "/api/users",
      "method": "POST",
      "handler_file": "server/src/modules/user/user.controller.ts",
      "handler_line": 25,
      "request_fields": [
        { "name": "userName", "type": "string", "required": true, "source": "body" },
        { "name": "email", "type": "string", "required": true, "source": "body" },
        { "name": "deptId", "type": "number", "required": false, "source": "body" }
      ],
      "response_fields": [
        { "name": "id", "type": "number", "system_field": true },
        { "name": "userName", "type": "string", "system_field": false },
        { "name": "email", "type": "string", "system_field": false },
        { "name": "createdAt", "type": "string", "system_field": true }
      ]
    },
    {
      "path": "/api/users",
      "method": "GET",
      "handler_file": "server/src/modules/user/user.controller.ts",
      "handler_line": 40,
      "request_fields": [
        { "name": "page", "type": "number", "required": false, "source": "query" },
        { "name": "pageSize", "type": "number", "required": false, "source": "query" },
        { "name": "keyword", "type": "string", "required": false, "source": "query" }
      ],
      "response_fields": [
        { "name": "list", "type": "array", "system_field": false, "items_ref": "UserVO" },
        { "name": "total", "type": "number", "system_field": false },
        { "name": "page", "type": "number", "system_field": false },
        { "name": "pageSize", "type": "number", "system_field": false }
      ]
    }
  ]
}
```

---

### L1: UI 显示层提取

> UI 层是用户可见的字段呈现。提取目标：表格列名、表单字段名、模板中绑定的数据字段。
> 按置信度分两级：高置信度（结构化配置）和中置信度（模板推断）。

#### 高置信度：表格列配置

```bash
# Ant Design / Ant Design Vue — columns 中的 dataIndex
grep -n "dataIndex" --include="*.tsx" --include="*.vue" --include="*.jsx" \
  -r src/pages/ src/views/ 2>/dev/null

# Element Plus / Element UI — prop
grep -n "el-table-column.*prop\|<el-table-column" --include="*.vue" \
  -r src/views/ 2>/dev/null

# 通用 columns 数组（React Table, AG Grid, etc.）
grep -n "columns\s*=\s*\[\|columns:\s*\[" --include="*.tsx" --include="*.ts" --include="*.vue" \
  -r src/pages/ src/views/ 2>/dev/null
```

提取规则：

| 框架 | 代码模式 | 提取字段名 | 提取标签 |
|---|---|---|---|
| Ant Design | `{ title: '用户名', dataIndex: 'userName' }` | `userName` | `用户名` |
| Ant Design | `{ title: '用户名', dataIndex: ['profile', 'name'] }` | `profile.name` | `用户名` |
| Element Plus | `<el-table-column prop="userName" label="用户名"/>` | `userName` | `用户名` |
| React Table | `{ Header: 'Name', accessor: 'userName' }` | `userName` | `Name` |
| AG Grid | `{ headerName: '用户名', field: 'userName' }` | `userName` | `用户名` |
| Naive UI | `{ title: '用户名', key: 'userName' }` | `userName` | `用户名` |

#### 高置信度：表单字段配置

```bash
# Ant Design Form — name 属性
grep -n "Form.Item.*name=\|<a-form-item.*name=" --include="*.tsx" --include="*.vue" --include="*.jsx" \
  -r src/pages/ src/views/ 2>/dev/null

# Element Plus Form — prop 属性
grep -n "el-form-item.*prop=" --include="*.vue" \
  -r src/views/ 2>/dev/null

# React Hook Form — register
grep -n "register(\|useForm\|Controller.*name=" --include="*.tsx" --include="*.jsx" \
  -r src/pages/ src/components/ 2>/dev/null

# Formik — name / Field
grep -n "<Field.*name=\|<FastField.*name=" --include="*.tsx" --include="*.jsx" \
  -r src/pages/ src/components/ 2>/dev/null
```

提取规则：

| 框架 | 代码模式 | 提取字段名 | 提取标签 |
|---|---|---|---|
| Ant Design | `<Form.Item name="userName" label="用户名">` | `userName` | `用户名` |
| Ant Design | `<Form.Item name={['profile', 'name']}>` | `profile.name` | — |
| Element Plus | `<el-form-item prop="userName" label="用户名">` | `userName` | `用户名` |
| React Hook Form | `register("userName")` | `userName` | — |
| React Hook Form | `<Controller name="userName" />` | `userName` | — |
| Formik | `<Field name="userName" />` | `userName` | — |
| VeeValidate | `<Field name="userName" />` | `userName` | — |

#### 中置信度：模板数据绑定

```bash
# Vue 模板绑定
grep -n 'v-model="\|{{ \|:prop="\|:value="' --include="*.vue" \
  -r src/views/ src/pages/ src/components/ 2>/dev/null

# React JSX 数据渲染
grep -n '{data\.\|{record\.\|{item\.\|{row\.\|props\.' --include="*.tsx" --include="*.jsx" \
  -r src/pages/ src/components/ 2>/dev/null

# Angular 模板绑定
grep -n '{{ \|\[value\]="\|\[ngModel\]="' --include="*.html" --include="*.component.ts" \
  -r src/app/ 2>/dev/null
```

提取规则：

| 框架 | 代码模式 | 提取字段名 | 置信度 |
|---|---|---|---|
| Vue | `v-model="form.userName"` | `userName` | 高 — 表单绑定 |
| Vue | `{{ item.userName }}` | `userName` | 中 — 模板插值 |
| Vue | `:label="item.userName"` | `userName` | 中 — 属性绑定 |
| React | `{data.userName}` | `userName` | 中 — JSX 表达式 |
| React | `{record.userName}` | `userName` | 中 — 表格行渲染 |
| Angular | `{{ user.userName }}` | `userName` | 中 — 模板插值 |
| Angular | `[value]="user.userName"` | `userName` | 中 — 属性绑定 |

#### 搜索/过滤字段

```bash
# 搜索表单字段（通常是 GET 请求的 query 参数在 UI 上的体现）
grep -n "搜索\|筛选\|过滤\|search\|filter\|keyword" --include="*.tsx" --include="*.vue" \
  -r src/pages/ src/views/ 2>/dev/null
```

> 搜索字段在 L2 中对应 `source: "query"` 的请求参数。跨层比对时需要匹配。

#### Flutter Widget（Dart L1）

> 当项目包含 Flutter 客户端时，L1 提取需要覆盖 Dart Widget 文件。

```bash
# DataTable 列字段
grep -rn "DataColumn\|DataCell" --include="*.dart" lib/ 2>/dev/null

# Form 字段绑定
grep -rn "TextFormField\|TextField\|DropdownButton\|DropdownButtonFormField" \
  --include="*.dart" lib/ 2>/dev/null

# 文本显示绑定
grep -rn "Text(\|TextSpan(" --include="*.dart" lib/ 2>/dev/null

# ListView / GridView 项
grep -rn "ListTile\|GridTile\|Card(" --include="*.dart" lib/ 2>/dev/null

# JSON 映射字段
grep -rn "json\['" --include="*.dart" lib/ 2>/dev/null
```

提取规则：

| 组件 | 代码模式 | 提取字段名 | 提取标签 |
|------|---------|-----------|---------|
| DataTable | `DataColumn(label: Text('用户名'))` | 从对应 `DataCell` 取字段绑定 | `用户名` |
| TextFormField | `TextFormField(controller: _nameCtrl)` | 追踪 controller → 变量名推断字段 | 取 `decoration.labelText` |
| Text | `Text(model.userName)` | `userName` | — |
| Text | `Text(item['user_name'])` | `user_name` | — |
| ListTile | `ListTile(title: Text(item.name), subtitle: Text(item.email))` | `name`, `email` | — |

#### 前端 API Service 层响应字段

> 前端 API service/client 函数中，对 HTTP 响应的字段访问路径。
> 纳入 L1 字段集合（component type = `api_service`），参与 L1↔L2 比对。
> LLM 驱动提取 — 读 service 函数代码，结合 SC-1 的拦截器解包规则推算字段路径。

#### L1 输出格式

```json
{
  "layer": "L1",
  "pages": [
    {
      "page": "用户管理",
      "file": "src/pages/user/UserList.tsx",
      "components": [
        {
          "type": "table",
          "component": "ProTable",
          "line": 45,
          "fields": [
            { "name": "userName", "context": "column", "label": "用户名", "line": 52 },
            { "name": "email", "context": "column", "label": "邮箱", "line": 53 },
            { "name": "deptName", "context": "column", "label": "部门", "line": 54 },
            { "name": "status", "context": "column", "label": "状态", "line": 55 },
            { "name": "createdAt", "context": "column", "label": "创建时间", "line": 56 }
          ]
        },
        {
          "type": "search",
          "component": "SearchForm",
          "line": 20,
          "fields": [
            { "name": "keyword", "context": "search", "label": "关键词", "line": 22 },
            { "name": "status", "context": "search", "label": "状态", "line": 25 },
            { "name": "deptId", "context": "search", "label": "部门", "line": 28 }
          ]
        }
      ]
    },
    {
      "page": "用户新增/编辑",
      "file": "src/pages/user/UserForm.tsx",
      "components": [
        {
          "type": "form",
          "component": "ProForm",
          "line": 30,
          "fields": [
            { "name": "userName", "context": "form", "label": "用户名", "line": 35 },
            { "name": "email", "context": "form", "label": "邮箱", "line": 40 },
            { "name": "phone", "context": "form", "label": "手机号", "line": 45 },
            { "name": "deptId", "context": "form", "label": "所属部门", "line": 50 },
            { "name": "roleIds", "context": "form", "label": "角色", "line": 55 }
          ]
        }
      ]
    }
  ]
}
```

---

### 通用字段过滤规则

> 系统字段在各层之间几乎必然存在命名差异（如 L4 `created_at` → L3 `createdAt` → L2 响应中存在但请求中不存在 → L1 只在表格中显示）。
> 这些差异是**合理的设计**，不应报告为问题。

#### 系统字段清单

以下字段应在提取时标记为 `system_field: true`，跨层比对时**仅做标注，不报告为缺失**：

| 类别 | 字段名变体 | 说明 |
|---|---|---|
| 主键 | `id`, `_id`, `ID`, `pk` | 主键通常自动生成，前端可能不显示 |
| 创建时间 | `createdAt`, `created_at`, `gmt_create`, `createTime`, `create_time`, `ctime` | 各框架命名习惯不同 |
| 更新时间 | `updatedAt`, `updated_at`, `gmt_modified`, `updateTime`, `update_time`, `mtime` | 同上 |
| 软删除 | `deletedAt`, `deleted_at`, `is_deleted`, `isDeleted`, `del_flag` | 通常不在 UI 层暴露 |
| 创建人 | `createdBy`, `created_by`, `creator`, `create_by` | 审计字段 |
| 更新人 | `updatedBy`, `updated_by`, `modifier`, `update_by` | 审计字段 |
| 乐观锁 | `version`, `revision`, `opt_lock_version` | 并发控制，前端不感知 |
| 多租户 | `tenantId`, `tenant_id`, `org_id` | 由框架自动注入，不在 UI 上出现 |

#### 过滤逻辑

```
对每个提取到的字段 f:
  1. 将 f 标准化（驼峰转蛇形、去前缀 is_/has_、统一小写）
  2. 与系统字段清单匹配
  3. 若匹配：
     - 标记 system_field = true
     - 跨层比对时：
       - L4 有 / L1 无 → 正常（系统字段通常不在 UI 显示）
       - L4 有 / L2 请求无 → 正常（系统字段通常自动填充）
       - L4 有 / L2 响应无 → 轻微提示（某些场景需要返回创建时间等）
  4. 若不匹配：
     - system_field = false
     - 跨层比对时正常报告缺失
```

#### 为什么需要过滤

系统字段在不同层有合理的存在差异：

| 层 | `id` | `created_at` | `password` | `deleted_at` | `tenant_id` |
|---|---|---|---|---|---|
| L4 数据库 | 存在 | 存在 | 存在 | 存在 | 存在 |
| L3 实体 | 存在 | 存在 | 存在（@JsonIgnore） | 存在 | 存在 |
| L2 响应 | 存在 | 通常存在 | **不应存在** | 不存在 | 不存在 |
| L2 请求 | 不存在（自动生成） | 不存在（自动填充） | 存在（注册时） | 不存在 | 不存在（框架注入） |
| L1 显示 | 通常隐藏 | 通常显示 | 不存在 | 不存在 | 不存在 |

如果不做过滤，每个模块都会报出大量 "L4 有 `tenant_id` 但 L1 没有" 这类误报，淹没真正有价值的发现。

> **注意**：`password` 不在系统字段清单中。如果 `password` 出现在 L2 响应中，应该报告为**安全问题**而非正常差异。
