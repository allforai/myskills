# Phase 0: 项目画像 (Project Profile)

> 本阶段为所有后续分析的基础。输出 `tuner-profile.json`，经用户确认后方可进入后续 Phase。

---

## 1. 技术栈识别

扫描项目根目录及常见子目录，通过配置文件模式识别语言、框架和构建工具。

### 检测规则表

| 语言 | 配置文件 | 框架推断逻辑 |
|------|----------|-------------|
| **Java** | `pom.xml`, `build.gradle`, `build.gradle.kts` | 含 `spring-boot-starter` → Spring Boot；含 `javax.servlet` / `jakarta.servlet` → Java EE / Jakarta EE；含 `quarkus` → Quarkus；含 `micronaut` → Micronaut |
| | `application.yml`, `application.properties` | 存在即加强 Spring Boot 判定；检查 `server.port`、`spring.datasource` 等 key 确认 |
| **Go** | `go.mod` | 检查 module path 和 dependencies：含 `gin-gonic/gin` → Gin；含 `labstack/echo` → Echo；含 `gofiber/fiber` → Fiber；含 `go-kratos/kratos` → Kratos；含 `go-zero` → go-zero |
| | `main.go` | 存在即确认 Go 项目入口 |
| **Node.js** | `package.json` | 检查 `dependencies` / `devDependencies`：含 `express` → Express；含 `@nestjs/core` → NestJS；含 `koa` → Koa；含 `fastify` → Fastify；含 `next` → Next.js (SSR) |
| | `tsconfig.json` | 存在即标记 TypeScript；检查 `strict` 配置判断严格程度 |
| **Python** | `requirements.txt`, `pyproject.toml`, `setup.py` | 含 `django` → Django；含 `flask` → Flask；含 `fastapi` → FastAPI；含 `tornado` → Tornado |
| | `manage.py` | 存在即确认 Django 项目 |
| **.NET** | `*.csproj`, `*.sln` | 检查 csproj 中的 `<PackageReference>`：含 `Microsoft.AspNetCore` → ASP.NET Core；含 `Abp` → ABP Framework |
| | `appsettings.json` | 存在即加强 .NET 判定 |
| **Rust** | `Cargo.toml` | 检查 `[dependencies]`：含 `actix-web` → Actix Web；含 `axum` → Axum；含 `rocket` → Rocket；含 `warp` → Warp |
| **PHP** | `composer.json` | 检查 `require`：含 `laravel/framework` → Laravel；含 `symfony/` → Symfony；含 `hyperf/` → Hyperf |
| **Ruby** | `Gemfile` | 含 `rails` → Ruby on Rails；含 `sinatra` → Sinatra；含 `hanami` → Hanami |

### 执行步骤

1. 在项目根目录执行 Glob 扫描，查找上表中列出的所有配置文件
2. 按优先级匹配：先确定语言，再确定框架，最后确定构建工具
3. 如同时存在多语言配置文件（如 `pom.xml` + `package.json`），标记为多语言项目，以主后端语言为主
4. 将结果写入 `tech_stack` 字段：`language`、`framework`、`build`（构建工具，如 Maven / Gradle / npm / go build）

---

## 2. 架构类型推断

根据目录结构和 import/依赖模式推断项目采用的架构类型。

### 四种架构类型

| 类型 | 标识符 | 核心特征 |
|------|--------|---------|
| 三层架构 | `three-tier` | 3 组不同职责的目录，依赖方向单向：Entry → Business → Data |
| 两层架构 | `two-tier` | 2 组目录，入口层 + 数据层，无独立业务层 |
| DDD | `ddd` | Domain 层零外部依赖，Infrastructure 实现 Domain 接口，Application 编排 |
| 混合/不明 | `mixed` | 无法明确归类，标记后交由用户确认 |

### 检测步骤

**Step 1: 扫描目录结构**

列出项目 src（或等效源码根目录）下的一级和二级目录。记录目录名称及其包含的文件类型。

**Step 2: 分析 import 模式**

对每个目录，采样其中的文件（每目录最多 10 个文件），提取 import / require / use 语句，构建目录间的依赖图。

**Step 3: 确定依赖方向**

将目录间的依赖关系整理为有向图：
- A → B 表示 A 目录中的文件 import 了 B 目录中的内容
- 检查是否存在环形依赖（A → B → A）
- 检查依赖是否单向

**Step 4: 分类判定**

按以下优先级逐条匹配：

1. **DDD 检测**：
   - 存在 `domain` / `model` 目录，其中的文件不 import 任何外部框架或基础设施代码
   - 存在 `infrastructure` / `infra` / `adapter` 目录，其中的文件实现了 domain 层定义的接口
   - 存在 `application` / `app` / `usecase` 目录，编排 domain 对象
   - 三个条件全部满足 → `ddd`

2. **三层架构检测**：
   - 识别出 3 组目录分别承担入口（接收请求、路由分发）、业务（核心逻辑、事务管理）、数据（数据库操作、外部数据源）职责
   - 依赖方向为单向：Entry → Business → Data（允许 Entry 在纯 CRUD 场景直接调 Data）
   - 满足 → `three-tier`

3. **两层架构检测**：
   - 识别出 2 组目录：入口层（接收请求）+ 数据层（数据操作），中间无独立业务层
   - 入口层直接调用数据层的代码比例 > 80%
   - 满足 → `two-tier`

4. **混合/不明**：
   - 以上均不满足，或特征混杂（如部分模块三层、部分模块两层）
   - 标记为 `mixed`，**必须**交由用户确认实际架构意图

### 特殊情况处理

- **单模块小项目**（文件数 < 20）：可能所有代码在一个目录下，按文件内的类/函数职责做逻辑分层，不强求物理分层
- **Monorepo**：每个子项目独立识别架构，允许不同子项目有不同架构
- **微服务项目**：识别到多个独立的 `main` 入口时，询问用户分析范围（单服务 or 全部）

---

## 3. 层级映射

将项目中的实际目录映射到四种逻辑角色。

### 四种逻辑角色

| 逻辑角色 | 标识符 | 职责 | 典型内容 |
|----------|--------|------|---------|
| 入口层 | `entry` | 接收外部请求，参数格式校验，路由分发，响应封装 | Controller, Handler, Router, Resolver (GraphQL), gRPC Service impl |
| 业务层 | `business` | 核心业务逻辑，事务管理，业务规则校验，领域编排 | Service, UseCase, Manager, DomainService, Facade |
| 数据层 | `data` | 数据持久化，外部数据源交互，查询构建，缓存操作 | Repository, DAO, Mapper, Gateway, Client (外部 API) |
| 工具层 | `utility` | 跨层公共工具，配置，常量，异常定义，中间件 | Utils, Config, Constants, Middleware, Interceptor, Filter |

### 核心原则

**名称不重要，职责和依赖方向才重要。**

不同项目命名千差万别：有的叫 `controller`，有的叫 `handler`，有的叫 `api`，有的叫 `web`，有的叫 `rest`——但只要该目录的代码职责是"接收外部请求并分发"，就映射为 `entry`。

判定方法：
1. 检查目录中文件的 import 来源（依赖了谁）
2. 检查目录中文件的被 import 情况（谁依赖了它）
3. 检查代码内容的实际职责（做了什么）
4. 综合以上三点确定逻辑角色

### 映射输出

以 key-value 形式输出，key 为项目中的实际路径（相对于项目根目录），value 为逻辑角色标识符：

```json
{
  "src/controller": "entry",
  "src/service": "business",
  "src/repository": "data",
  "src/common": "utility"
}
```

> 完整的跨语言目录名称 → 逻辑角色对照表见 `./layer-mapping.md`。该表作为初始猜测的参考，最终映射仍需依据实际依赖分析结果。

---

## 4. 模块识别

识别项目中的业务模块（功能域）。一个模块对应一组完成特定业务功能的代码集合。

### 四种识别策略

按优先级依次尝试：

**策略 1: 按子目录划分（feature-based 项目结构）**

项目按功能域组织目录，每个模块拥有自己的子目录。

```
src/
├── user/           → 模块: user
│   ├── controller/
│   ├── service/
│   └── repository/
├── order/          → 模块: order
│   ├── controller/
│   ├── service/
│   └── repository/
└── product/        → 模块: product
```

检测方法：查找 src 下是否有多个子目录，每个子目录内部都包含入口/业务/数据层的文件。

**策略 2: 按命名前缀划分（flat 项目结构）**

所有 Controller 在一个目录，所有 Service 在一个目录，通过文件名前缀区分模块。

```
src/
├── controller/
│   ├── UserController.java     → 模块: user
│   ├── OrderController.java    → 模块: order
│   └── ProductController.java  → 模块: product
├── service/
│   ├── UserService.java
│   ├── OrderService.java
│   └── ProductService.java
└── repository/
```

检测方法：提取入口层文件的名称前缀（去掉 Controller / Handler / Router 等后缀），将相同前缀的文件归为一个模块。

**策略 3: 按 package / namespace 划分**

适用于 Java、.NET 等有包/命名空间概念的语言。

```
com.example.app.user.controller
com.example.app.user.service
com.example.app.order.controller
com.example.app.order.service
```

检测方法：提取包名中的倒数第二级（去掉最后的层级标识如 controller / service），将相同包前缀的文件归为一个模块。

**策略 4: 按数据库表分组**

当以上策略都不适用时（如代码组织混乱），以实体类/数据库表为锚点反推模块。

检测方法：
1. 先执行数据模型识别（第 6 节），获得实体列表
2. 以每个实体为中心，找到引用该实体的所有文件
3. 将引用同一组相关实体的文件归为一个模块
4. 通过实体间的关联关系（外键、引用）判断哪些实体属于同一模块

### 输出

模块列表为字符串数组：

```json
["user", "order", "product", "payment", "notification"]
```

---

## 5. 规模评估

评估项目规模，用于预估后续分析的工作量和合理设定阈值。

### 采集指标

| 指标 | 采集方法 | 用途 |
|------|---------|------|
| 文件数 (files) | 统计所有源代码文件（排除 node_modules、vendor、build 产物、测试文件） | 判断项目规模等级 |
| 代码行数 (lines) | 统计所有源代码文件的总行数（排除空行和纯注释行） | 估算分析时间 |
| 模块数 (modules) | 第 4 节识别结果的数量 | 决定是否需要分模块分批分析 |
| 实体数 (entities) | 第 6 节识别结果的数量 | 评估数据模型复杂度 |

### 执行方法

1. 使用 Glob 匹配源码文件，排除以下目录：
   - `node_modules/`, `vendor/`, `target/`, `build/`, `dist/`, `bin/`, `obj/`
   - `.git/`, `.idea/`, `.vscode/`, `.allforai/code-tuner/`
   - `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`
2. 使用 Bash 的 `wc -l` 统计代码行数（或对大型项目采样估算）
3. 记录文件类型分布（如 `.java` 占 80%、`.xml` 占 15%、其他占 5%）

### 规模等级参考

| 等级 | 文件数 | 代码行数 | 分析策略 |
|------|--------|---------|---------|
| 小型 | < 50 | < 5,000 | 全量扫描，每个文件都读取 |
| 中型 | 50-200 | 5,000-50,000 | 全量扫描，关键文件精读 |
| 大型 | 200-500 | 50,000-200,000 | 分模块分析，每模块采样核心文件 |
| 超大型 | > 500 | > 200,000 | 分模块分批分析，提醒用户指定分析范围 |

---

## 6. 数据模型识别

扫描项目中的实体定义、数据传输对象（DTO/VO/PO），建立数据模型全景。实体类和数据库表结构是服务端最重要的信息。

### 各语言实体检测模式

| 语言 | 检测模式 | 说明 |
|------|---------|------|
| **Java** | `@Entity`, `@Table`, `@Document` 注解 | JPA / Hibernate 实体；`@Document` 用于 MongoDB |
| | `@Data` + `@TableName` | MyBatis-Plus 实体 |
| | 继承 `BaseEntity` / `AbstractEntity` | 框架基类继承 |
| **Go** | struct 带 `gorm:"..."` tag | GORM 实体 |
| | struct 带 `db:"..."` tag | sqlx 实体 |
| | `ent.Schema` 接口实现 | Ent ORM 实体 |
| **Python** | 继承 `models.Model` | Django Model |
| | 继承 `Base`（`declarative_base()` 产生） | SQLAlchemy 实体 |
| | 继承 `BaseModel` + `class Config` 含 `orm_mode` | Pydantic ORM Model |
| | `@dataclass` + `__tablename__` | SQLAlchemy 2.0 声明式 |
| **Node.js** | `@Entity()` 装饰器 | TypeORM 实体 |
| | `sequelize.define()` 或继承 `Model` | Sequelize 实体 |
| | `schema.prisma` 中的 `model` 定义 | Prisma 实体 |
| | `mongoose.Schema` | Mongoose (MongoDB) 实体 |
| **.NET** | 继承 `DbContext` 中的 `DbSet<T>` 引用的类型 T | Entity Framework Core 实体 |
| | `[Table("...")]` attribute | EF 或 Dapper 实体 |
| | 实现 `IEntity` / `IEntity<TKey>` 接口 | ABP Framework 实体 |
| **Rust** | `#[derive(Queryable, Insertable)]` | Diesel 实体 |
| | `Cargo.toml` 含 `sea-orm` + `#[derive(DeriveEntityModel)]` | SeaORM 实体 |
| **PHP** | `@ORM\Entity`, `@ORM\Table` 注解或 PHP 8 Attribute `#[ORM\Entity]` | Doctrine 实体 |
| | 继承 `Illuminate\Database\Eloquent\Model` | Laravel Eloquent 实体 |
| **Ruby** | 继承 `ApplicationRecord` 或 `ActiveRecord::Base` | Rails ActiveRecord 实体 |

### 扫描内容

对每个识别到的实体，提取以下信息：

**基本信息：**
- 实体名称（类名 / struct 名）
- 对应的数据库表名（从注解/tag/配置中提取，如 `@Table(name = "t_user")` → `t_user`）
- 字段数量
- 文件路径

**关系信息：**
- `@OneToMany`, `@ManyToOne`, `@ManyToMany`, `@OneToOne`（Java/JPA）
- `foreignKey`, `references`（GORM tag）
- `ForeignKey`, `belongsTo`, `hasMany`（各 ORM 的关系定义）
- 提取关系的方向和类型：`{ from: "User", to: "Order", type: "one-to-many" }`

**DTO/VO/PO 模式检测：**

扫描是否存在数据传输对象模式：
- 文件名或类名含 `DTO`, `VO`, `PO`, `Request`, `Response`, `Command`, `Query`, `Form`
- 与实体同名但带后缀的类（如 `User` → `UserDTO`, `UserVO`, `UserCreateRequest`）
- 统计 DTO/VO 总数，过多可能意味着过度设计

**公共基础字段：**

检查实体是否包含通用基础字段，记录项目使用的基础字段集：
- `id` — 主键
- `createTime` / `created_at` / `createdAt` / `gmt_create` — 创建时间
- `updateTime` / `updated_at` / `updatedAt` / `gmt_modified` — 更新时间
- `isDeleted` / `deleted` / `deleted_at` / `is_deleted` — 逻辑删除标记
- `createBy` / `created_by` — 创建人
- `updateBy` / `updated_by` — 更新人
- `version` — 乐观锁版本号
- `tenantId` / `tenant_id` — 多租户标识

检查是否有统一的基类（如 `BaseEntity`）包含这些字段。如有基类，只需记录基类字段一次，各实体记录自有字段。

---

## 7. 输出格式

Phase 0 的完整输出为 `tuner-profile.json`，保存在项目的 `.allforai/code-tuner/` 目录下。

### 完整 Schema

```json
{
  "tech_stack": {
    "language": "java",
    "framework": "spring-boot",
    "build": "maven",
    "language_version": "17",
    "framework_version": "3.2.0"
  },
  "architecture": "three-tier",
  "lifecycle": "pre-launch",
  "layer_mapping": {
    "src/main/java/com/example/controller": "entry",
    "src/main/java/com/example/service": "business",
    "src/main/java/com/example/service/impl": "business",
    "src/main/java/com/example/repository": "data",
    "src/main/java/com/example/mapper": "data",
    "src/main/java/com/example/config": "utility",
    "src/main/java/com/example/common": "utility",
    "src/main/java/com/example/entity": "data",
    "src/main/java/com/example/dto": "utility"
  },
  "modules": [
    "user",
    "order",
    "product",
    "payment"
  ],
  "data_model": {
    "entities": [
      {
        "name": "User",
        "table": "t_user",
        "fields": 12,
        "path": "src/main/java/com/example/entity/User.java"
      },
      {
        "name": "Order",
        "table": "t_order",
        "fields": 15,
        "path": "src/main/java/com/example/entity/Order.java"
      }
    ],
    "dto_vo_count": 18,
    "common_base_fields": [
      "id",
      "createTime",
      "updateTime",
      "isDeleted"
    ],
    "base_entity_class": "BaseEntity",
    "relationships": [
      {
        "from": "User",
        "to": "Order",
        "type": "one-to-many"
      },
      {
        "from": "Order",
        "to": "Product",
        "type": "many-to-many"
      }
    ]
  },
  "scale": {
    "files": 156,
    "lines": 23400,
    "modules": 4,
    "entities": 12
  }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tech_stack.language` | string | Y | 主语言标识（小写）：java, go, python, nodejs, dotnet, rust, php, ruby |
| `tech_stack.framework` | string | Y | 框架标识（小写连字符）：spring-boot, gin, nestjs, django, fastapi 等 |
| `tech_stack.build` | string | Y | 构建工具：maven, gradle, npm, yarn, pnpm, go-build, cargo, composer, bundler, dotnet |
| `tech_stack.language_version` | string | N | 语言版本（从配置文件中提取，如有） |
| `tech_stack.framework_version` | string | N | 框架版本（从配置文件中提取，如有） |
| `architecture` | string | Y | 架构类型：`three-tier`, `two-tier`, `ddd`, `mixed` |
| `lifecycle` | string | Y | 生命周期模式：`pre-launch`, `maintenance`（来自用户输入） |
| `layer_mapping` | object | Y | 实际目录路径 → 逻辑角色。key 为相对路径，value 为 `entry` / `business` / `data` / `utility` |
| `modules` | string[] | Y | 业务模块列表 |
| `data_model.entities` | array | Y | 实体列表，每项含 `name`、`table`、`fields`（字段数）、`path` |
| `data_model.dto_vo_count` | number | Y | DTO/VO/Request/Response 等传输对象总数 |
| `data_model.common_base_fields` | string[] | Y | 项目中实体共有的基础字段名列表 |
| `data_model.base_entity_class` | string | N | 如有统一基类，记录基类名 |
| `data_model.relationships` | array | Y | 实体间关系列表，每项含 `from`、`to`、`type`（one-to-one / one-to-many / many-to-many） |
| `scale.files` | number | Y | 源代码文件总数（排除第三方和构建产物） |
| `scale.lines` | number | Y | 代码总行数 |
| `scale.modules` | number | Y | 模块数量 |
| `scale.entities` | number | Y | 实体数量 |

---

## 8. 用户确认清单

Phase 0 完成后，**必须**将以下内容展示给用户并逐项确认。架构类型判断错误会导致后续所有分析结果偏差，因此确认步骤不可跳过。

### 确认展示格式

按以下格式输出确认信息：

```
## 项目画像确认

### 1. 技术栈
- 语言: Java 17
- 框架: Spring Boot 3.2.0
- 构建: Maven

### 2. 架构类型
检测结果: **三层架构 (three-tier)**
判定依据:
- 发现 3 组目录: controller / service / repository
- 依赖方向: controller → service → repository（单向）
- 无反向依赖

### 3. 层级映射

| 实际目录 | 逻辑角色 | 判定依据 |
|----------|---------|---------|
| src/.../controller | Entry (入口层) | 含 @RestController，接收 HTTP 请求 |
| src/.../service | Business (业务层) | 含 @Service，被 controller 调用，调用 repository |
| src/.../service/impl | Business (业务层) | Service 接口的实现类 |
| src/.../repository | Data (数据层) | 含 @Repository，执行数据库操作 |
| src/.../entity | Data (数据层) | 实体定义，含 @Entity 注解 |
| src/.../mapper | Data (数据层) | MyBatis Mapper 接口 |
| src/.../config | Utility (工具层) | 配置类，被多层引用 |
| src/.../common | Utility (工具层) | 公共工具、常量、异常定义 |
| src/.../dto | Utility (工具层) | 数据传输对象，跨层使用 |

### 4. 模块列表
识别到 4 个业务模块:
- user (用户)
- order (订单)
- product (商品)
- payment (支付)

### 5. 数据模型概况
- 实体数: 12
- 关系数: 8
- DTO/VO 数: 18
- 公共基础字段: id, createTime, updateTime, isDeleted (来自 BaseEntity)

---

以上信息是否正确？如有偏差请指出，我将调整后重新确认。
```

### 确认规则

1. **架构类型** — 必须确认。如用户指出判断有误，按用户意图重新分类
2. **层级映射** — 必须确认。如某个目录角色判断错误（如把 Facade 当成了 Entry），按用户反馈修正
3. **模块列表** — 必须确认。用户可能需要增删模块、合并过细的拆分、拆分过粗的合并
4. **数据模型概况** — 展示实体数和关系数供用户确认。如缺少实体或关系，按用户补充修正

确认通过后，将最终版本写入 `.allforai/code-tuner/tuner-profile.json`，进入后续 Phase。

如用户对任何项提出修正：
1. 根据反馈调整对应字段
2. 重新展示修改后的确认信息
3. 再次请求确认
4. 循环直到用户确认通过

---

## 执行检查清单

Phase 0 执行时，按以下清单逐项完成：

- [ ] 扫描配置文件，识别语言、框架、构建工具
- [ ] 分析目录结构和 import 模式，推断架构类型
- [ ] 将实际目录映射到逻辑角色（Entry / Business / Data / Utility）
- [ ] 识别业务模块列表
- [ ] 统计项目规模（文件数、代码行数、模块数、实体数）
- [ ] 扫描实体定义、关系、DTO/VO、公共基础字段
- [ ] 组装 `tuner-profile.json`
- [ ] 展示确认清单，等待用户确认
- [ ] 用户确认通过后，写入 `.allforai/code-tuner/tuner-profile.json`
