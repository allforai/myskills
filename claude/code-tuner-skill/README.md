# code-tuner

A Claude Code plugin skill that analyzes server-side code for architectural violations, cross-layer duplication, abstraction opportunities, and validation issues. Outputs a comprehensive score (0-100) and actionable refactoring task list. Supports three-tier, two-tier, and DDD architectures across Java, Go, Node.js, Python, .NET, Rust, PHP, and Ruby.

## 30-second start

```bash
# 1) Install (aligned with other plugins)
claude plugin add /path/to/code-tuner-skill

# 2) Run full analysis
/code-tuner full
```

## Common scenarios

| Scenario | Recommended command |
|---|---|
| Full architecture assessment (default) | `/code-tuner full` |
| Check architecture compliance only | `/code-tuner compliance` |
| Hunt duplicated logic across layers | `/code-tuner duplication` |
| Find abstraction/refactor opportunities | `/code-tuner abstraction` |
| Regenerate report from existing outputs | `/code-tuner report` |

## Installation

```bash
claude plugin add /path/to/code-tuner-skill
```

## Usage

```
/code-tuner full
/code-tuner compliance
/code-tuner duplication
/code-tuner abstraction
/code-tuner report
```

Or use natural language:

```
请用 code-tuner 分析我的项目。项目路径是 /path/to/project。项目状态是未上线。
please use code-tuner to analyze my project at /path/to/project. It's pre-launch.
```

Modes:
- **full** — Phase 0 → 1 → 2 → 3 → 4 (default)
- **compliance** — Architecture compliance only
- **duplication** — Duplication detection only
- **abstraction** — Abstraction analysis only
- **report** — Regenerate report from existing phase outputs

Lifecycle is asked interactively if not specified (pre-launch or maintenance).

## Output

All output goes to `.allforai/code-tuner/` in your project root.

```
your-project/
└── .allforai/code-tuner/
    ├── tuner-profile.json        # Phase 0: 项目画像（架构类型、层级映射、模块列表）
    ├── phase1-compliance.json    # Phase 1: 架构违规列表
    ├── phase2-duplicates.json    # Phase 2: 重复检测结果
    ├── phase3-abstractions.json  # Phase 3: 抽象机会
    ├── tuner-report.md           # Phase 4: 综合报告（0-100 评分 + 问题热力图）
    └── tuner-tasks.json          # Phase 4: 重构任务清单（按优先级排序）
```

## License

MIT


---

## 内嵌文档（自动汇总）

> 以下内容已从子文档汇总到 README，便于单文件阅读。

### 来源文件：`references/layer-mapping.md`

# Cross-Language Layer Mapping Reference

将实际目录/包名映射到逻辑角色（Entry / Business / Data / Utility / Entity），用于 Phase 0 快速识别项目分层结构。

核心原则：名称不重要，职责和依赖方向才重要。不同语言和框架使用不同的命名约定，但底层的分层逻辑是一致的。通过识别目录的实际职责而非名称来判断其逻辑角色。

---

## 逻辑角色定义

| 逻辑角色 | 职责 | 依赖方向 |
|---------|------|---------|
| Entry (入口层) | 接收请求、参数解析、格式校验、调用业务层、返回响应 | → Business, → Data (仅简单CRUD) |
| Business (业务层) | 业务逻辑、业务规则验证、事务管理、编排多个数据操作 | → Data |
| Data (数据层) | 数据持久化、查询、ORM映射 | 不依赖其他层 |
| Utility (工具层) | 通用工具方法、配置、常量 | 不依赖业务层 |
| Entity (实体层) | 数据模型定义、实体类 | 被所有层引用 |

### 依赖方向总则

合法依赖方向：Entry → Business → Data，所有层 → Entity，所有层 → Utility。

违规依赖方向：Data → Business，Data → Entry，Business → Entry。检测到此类反向依赖时标记为架构违规。

---

## Java / Spring Boot (三层)

标准的三层架构，Spring Boot 项目中最常见的组织方式。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| controller/ | Entry | @RestController, @Controller |
| api/ | Entry | API endpoint definitions |
| rest/ | Entry | RESTful endpoints |
| service/ | Business | @Service |
| service/impl/ | Business | Service implementations |
| manager/ | Business | 复杂业务编排 |
| repository/ | Data | @Repository, JpaRepository |
| dao/ | Data | Data Access Object |
| mapper/ | Data | MyBatis mapper interfaces |
| entity/ | Entity | @Entity JPA entities |
| model/ | Entity | Domain models |
| domain/ | Entity | Domain objects |
| dto/ | Entity | Data Transfer Objects |
| vo/ | Entity | View Objects |
| po/ | Entity | Persistent Objects |
| util/ | Utility | Utility classes |
| utils/ | Utility | Utility classes |
| common/ | Utility | Common utilities |
| config/ | Utility | @Configuration |
| constant/ | Utility | Constants |
| enums/ | Utility | Enumerations |
| exception/ | Utility | Custom exceptions |
| interceptor/ | Entry | Request interceptors |
| filter/ | Entry | Servlet filters |
| aspect/ | Utility | AOP aspects |

识别要点：查找 `@RestController`、`@Service`、`@Repository` 注解来确认角色。当目录名含糊时，注解是最可靠的判断依据。

---

## Java / DDD

领域驱动设计的分层结构，`domain/` 目录承担混合职责，需要按子目录细分判断。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| interfaces/ | Entry | Controller/REST/RPC endpoints |
| application/ | Business | Application services, orchestration |
| domain/ | Entity + Business | Aggregates, entities, value objects, domain services, repository interfaces |
| domain/model/ | Entity | Domain entities and VOs |
| domain/service/ | Business | Domain services |
| domain/repository/ | Business (interface) | Repository interfaces (NOT impl) |
| infrastructure/ | Data + Utility | Repository impl, external service adapters |
| infrastructure/persistence/ | Data | Repository implementations |
| infrastructure/gateway/ | Utility | External API clients |

识别要点：DDD 项目中 `domain/repository/` 只定义接口，实现在 `infrastructure/persistence/`。分析时注意区分接口定义与实现，接口归 Business，实现归 Data。`domain/` 目录本身是混合角色，必须检查子目录内容才能准确归类。

---

## Go

Go 项目结构差异较大，需根据框架（标准库、gin、go-zero、kratos 等）灵活判断。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| handler/ | Entry | HTTP handlers |
| api/ | Entry | API definitions |
| controller/ | Entry | HTTP controllers |
| router/ | Entry | Route definitions |
| service/ | Business | Business logic |
| logic/ | Business | Business logic (go-zero style) |
| usecase/ | Business | Use cases |
| repository/ | Data | Database operations |
| store/ | Data | Data storage |
| dao/ | Data | Data access |
| model/ | Entity | Data models |
| entity/ | Entity | Entities |
| types/ | Entity | Type definitions |
| schema/ | Entity | DB schema |
| pkg/ | Utility | Shared packages |
| internal/ | varies | Internal packages (check content) |
| cmd/ | Entry | CLI entry points |
| middleware/ | Entry | HTTP middleware |
| config/ | Utility | Configuration |
| util/ | Utility | Utilities |

识别要点：`internal/` 目录是 Go 特有的访问控制机制，其内容可能包含任意层的代码，必须检查子目录结构来判断。`pkg/` 通常是工具层，但大型项目中也可能包含业务代码。`cmd/` 是程序入口，包含 `main()` 函数。go-zero 框架使用 `logic/` 替代 `service/`，使用 `handler/` 替代 `controller/`，使用 `svc/` 作为服务上下文依赖注入。

---

## Node.js / NestJS

NestJS 使用装饰器和文件名后缀约定，按后缀判断角色最为可靠。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| *.controller.ts | Entry | @Controller |
| *.gateway.ts | Entry | WebSocket gateways |
| *.resolver.ts | Entry | GraphQL resolvers |
| *.service.ts | Business | @Injectable services |
| *.repository.ts | Data | Custom repositories |
| *.entity.ts | Entity | TypeORM entities |
| *.dto.ts | Entity | DTOs |
| *.module.ts | Utility | NestJS modules |
| *.guard.ts | Entry | Auth guards |
| *.pipe.ts | Entry | Validation pipes |
| *.interceptor.ts | Entry | Interceptors |
| *.middleware.ts | Entry | Middleware |

识别要点：NestJS 按文件后缀而非目录组织代码。扫描时优先匹配 `*.controller.ts`、`*.service.ts` 等模式。模块目录下通常混合放置所有角色的文件，不能按目录判断。查找 `@Controller()`、`@Injectable()`、`@Entity()` 装饰器作为辅助确认。

---

## Node.js / Express

Express 项目结构松散，没有强制约定，依赖目录命名和中间件注册模式来识别。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| routes/ | Entry | Route definitions |
| controllers/ | Entry | Request handlers |
| middleware/ | Entry | Express middleware |
| services/ | Business | Business logic |
| models/ | Data + Entity | Mongoose/Sequelize models |
| repositories/ | Data | Data access layer |
| schemas/ | Entity | Validation schemas (Joi/Zod) |
| utils/ | Utility | Utilities |
| helpers/ | Utility | Helper functions |
| config/ | Utility | Configuration |

识别要点：Express 项目中 `models/` 通常同时承担 Data 和 Entity 角色（Mongoose model 既定义 schema 又提供查询方法）。小型项目可能没有 `services/` 目录，业务逻辑直接写在 `controllers/` 中——这本身就是一个需要检测的分层问题。

---

## Python / Django

Django 按 app 组织代码，每个 app 内部使用固定的文件名约定。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| views.py | Entry | View functions/classes |
| viewsets.py | Entry | DRF ViewSets |
| urls.py | Entry | URL routing |
| serializers.py | Entry + Entity | DRF serializers (validation + DTO) |
| services.py | Business | Business logic |
| models.py | Data + Entity | Django ORM models |
| managers.py | Data | Custom model managers |
| admin.py | Entry | Admin interface |
| forms.py | Entry | Form validation |
| middleware.py | Entry | Django middleware |
| utils.py | Utility | Utilities |
| tasks.py | Business | Celery tasks |
| signals.py | Business | Django signals |

识别要点：Django 的 `models.py` 同时承担 Data 和 Entity 角色，ORM model 既定义数据结构又提供查询接口。`serializers.py` 是混合角色，既做入口层的参数校验，又定义 DTO。很多 Django 项目没有独立的 `services.py`，业务逻辑散落在 `views.py` 中——标记此模式为分层不清晰。

---

## Python / FastAPI

FastAPI 项目通常参考 tiangolo 推荐的目录结构。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| routers/ | Entry | APIRouter endpoints |
| api/ | Entry | API endpoints |
| schemas/ | Entity | Pydantic models |
| models/ | Data + Entity | SQLAlchemy models |
| crud/ | Data | CRUD operations |
| services/ | Business | Business logic |
| deps/ | Utility | Dependencies |
| core/ | Utility | Core config |
| utils/ | Utility | Utilities |

识别要点：FastAPI 使用 Pydantic 做数据校验，`schemas/` 目录存放 Pydantic model（归 Entity），`models/` 存放 SQLAlchemy model（归 Data + Entity）。区分两者：Pydantic model 用于 API 数据交换，SQLAlchemy model 用于数据库映射。`crud/` 目录是 FastAPI 项目特有的模式，封装基本的增删改查操作，归 Data 层。

---

## .NET / ASP.NET Core

.NET 项目通常使用 PascalCase 目录名，按 Solution/Project 组织。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| Controllers/ | Entry | [ApiController] |
| Services/ | Business | Business services |
| Repositories/ | Data | Data access |
| Models/ | Entity | Entity models |
| DTOs/ | Entity | Data transfer objects |
| ViewModels/ | Entity | View models |
| Data/ | Data | DbContext, migrations |
| Middleware/ | Entry | ASP.NET middleware |
| Filters/ | Entry | Action filters |
| Helpers/ | Utility | Helper classes |
| Extensions/ | Utility | Extension methods |

识别要点：查找 `[ApiController]`、`[HttpGet]` 等 attribute 确认 Entry 层。`Data/` 目录通常包含 EF Core 的 `DbContext` 和 migration 文件。大型 .NET 项目可能使用 Clean Architecture，将各层拆分为独立的 Project（.csproj），此时按 Project 引用关系判断依赖方向。

---

## Rust / Actix-web

Rust Web 项目结构相对统一，主要框架包括 actix-web、axum、rocket。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| handlers/ | Entry | Request handlers |
| routes/ | Entry | Route configuration |
| services/ | Business | Business logic |
| repositories/ | Data | Database operations |
| models/ | Entity | Data models |
| schema/ | Entity | Diesel schema |
| dto/ | Entity | Request/Response types |
| middleware/ | Entry | Actix middleware |
| utils/ | Utility | Utilities |
| config/ | Utility | Configuration |
| errors/ | Utility | Custom error types |

识别要点：Rust 项目中查找 `#[get]`、`#[post]`、`HttpRequest`、`web::Json` 等标记确认 Entry 层。Diesel ORM 使用 `schema.rs`（由 diesel CLI 自动生成）定义表结构。axum 框架使用 `Router` 和 handler 函数，与 actix-web 的目录约定基本一致。

---

## PHP / Laravel

Laravel 有强约定的目录结构，大部分代码位于 `app/` 目录下。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| app/Http/Controllers/ | Entry | Controllers |
| app/Http/Middleware/ | Entry | Middleware |
| app/Http/Requests/ | Entry | Form requests (validation) |
| app/Services/ | Business | Business services |
| app/Repositories/ | Data | Repositories |
| app/Models/ | Data + Entity | Eloquent models |
| app/Helpers/ | Utility | Helper functions |
| routes/ | Entry | Route definitions |
| config/ | Utility | Configuration |

识别要点：Laravel 的 Eloquent model 同时承担 Data 和 Entity 角色。`app/Http/Requests/` 中的 FormRequest 类负责入口层的参数校验。默认项目可能没有 `Services/` 和 `Repositories/` 目录（Laravel 不强制这两层），业务逻辑可能直接写在 Controller 中——标记为需要关注的分层问题。

---

## Ruby / Rails

Rails 遵循约定优于配置原则，目录结构高度统一。

| 实际目录/包名 | 逻辑角色 | 说明 |
|-------------|---------|------|
| app/controllers/ | Entry | Controllers |
| app/services/ | Business | Service objects |
| app/models/ | Data + Entity | ActiveRecord models |
| app/serializers/ | Entity | JSON serializers |
| app/jobs/ | Business | Background jobs |
| app/mailers/ | Business | Email sending |
| lib/ | Utility | Shared libraries |
| config/ | Utility | Configuration |

识别要点：Rails 的 ActiveRecord model 是典型的 Data + Entity 混合角色。`app/services/` 不是 Rails 默认目录，存在时说明项目有意识地进行了分层。没有 `services/` 的 Rails 项目通常将业务逻辑放在 model（fat model 模式）或 controller（fat controller 模式）中——两者都是需要检测的代码质量问题。

---

## 依赖方向分析

分析 import/require/use 语句来判断依赖方向，检测是否存在违规的反向依赖。

### Java

```java
import com.example.controller.*  // → Entry
import com.example.service.*     // → Business
import com.example.repository.*  // → Data
```

检测规则：若 `repository` 包中的类 import 了 `service` 包，标记为 Data → Business 反向依赖违规。若 `service` 包 import 了 `controller` 包，标记为 Business → Entry 反向依赖违规。

### Go

```go
import "project/handler"    // → Entry
import "project/service"    // → Business
import "project/repository" // → Data
```

检测规则：Go 的 import 路径直接反映包依赖。扫描每个 `.go` 文件的 import block，根据路径中包含的关键词判断被依赖的层级。注意 Go 禁止循环 import，编译器会直接报错，因此循环依赖问题较少见，但跨层依赖仍需检测。

### TypeScript/JavaScript

```typescript
import { ... } from '../controllers/'  // → Entry
import { ... } from '../services/'     // → Business
import { ... } from '../repositories/' // → Data
```

检测规则：扫描 `import` 和 `require` 语句，通过相对路径或模块路径中的目录名判断依赖目标。NestJS 项目中还需检查构造函数注入（`@Inject()`）来追踪依赖关系。

### Python

```python
from app.views import ...       # → Entry
from app.services import ...    # → Business
from app.models import ...      # → Data
```

检测规则：扫描 `import` 和 `from ... import` 语句。Django 项目中注意 `models.py` 被所有层引用是正常的（Entity 角色），但 `views.py` 不应被 `models.py` 或 `services.py` 引用。

### C#

```csharp
using Project.Controllers;   // → Entry
using Project.Services;      // → Business
using Project.Repositories;  // → Data
```

检测规则：扫描 `using` 语句和 Project 引用（.csproj 中的 `<ProjectReference>`）。Clean Architecture 项目中，检查 Project 级别的引用方向比文件级别更有效。

### Rust

```rust
use crate::handlers::*;      // → Entry
use crate::services::*;      // → Business
use crate::repositories::*;  // → Data
```

检测规则：扫描 `use crate::` 和 `mod` 语句。Rust 的模块系统严格，通过 `pub` 可见性控制可以部分限制跨层访问，但仍需检测逻辑上的依赖方向违规。

### PHP

```php
use App\Http\Controllers\*;  // → Entry
use App\Services\*;          // → Business
use App\Repositories\*;      // → Data
```

检测规则：扫描 `use` 语句（PHP namespace import）。Laravel 项目中注意 Facade 和 Service Container 的隐式依赖可能绕过 import 检测——此类情况需结合 `app()` 调用和 `@inject` directive 辅助分析。

### Ruby

```ruby
# Ruby 不使用显式 import，依赖 Rails autoload
# 通过类名引用检测依赖
UserController  # → Entry
UserService     # → Business
User            # → Data + Entity
```

检测规则：Ruby/Rails 使用 autoload 机制，没有显式 import 语句。通过分析文件中引用的类名和方法调用来推断依赖关系。查找 Controller 中是否直接调用 Model 的查询方法（跳过 Service 层）作为分层违规的信号。

---

## 通用识别策略

当目录名无法明确判断角色时，按以下优先级进行识别：

1. **检查框架注解/装饰器/attribute**：`@RestController`、`@Service`、`@Repository`（Java），`@Controller()`、`@Injectable()`（NestJS），`[ApiController]`（.NET）等是最可靠的判断依据。
2. **检查基类/接口继承**：继承 `JpaRepository` 的类归 Data 层，继承 `Controller` 的类归 Entry 层。
3. **检查文件内容特征**：包含 HTTP method 处理（GET/POST/PUT/DELETE）的归 Entry 层，包含 SQL/ORM 查询的归 Data 层。
4. **检查依赖注入模式**：Entry 层注入 Business 层，Business 层注入 Data 层——通过构造函数参数或字段注入反推角色。
5. **回退到目录名匹配**：使用本文档中的映射表作为最后手段。

当一个目录承担多个逻辑角色时（如 Django 的 `models.py` = Data + Entity），在分析报告中标注混合角色，并按主要职责归类。


### 来源文件：`references/phase0-profile.md`

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

> 完整的跨语言目录名称 → 逻辑角色对照表见 `${CLAUDE_PLUGIN_ROOT}/references/layer-mapping.md`。该表作为初始猜测的参考，最终映射仍需依据实际依赖分析结果。

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


### 来源文件：`references/phase1-compliance.md`

# Phase 1: Architecture Compliance Check

Phase 1 对服务端代码进行架构合规性检查，覆盖三层架构、两层架构、DDD 架构以及通用规则。所有规则按 ID 编号，检测结果输出为 `phase1-compliance.json`。

---

## 三层架构规则 (T-01 ~ T-06)

适用于 Entry(Controller/Handler) → Business(Service) → Data(Repository/DAO) 分层结构。

### T-01: 依赖方向单向

- **规则**: 强制依赖方向为 Entry → Business → Data，禁止反向依赖。Service 不能 import Controller，Repository 不能 import Service。
- **严重级别**: critical
- **检测方法**: 扫描 Business 层文件的 import/require 语句，匹配是否引用 Entry 层的包或模块；扫描 Data 层文件，匹配是否引用 Business 层的包或模块。
- **违规示例 (Java)**:
```java
// UserService.java — 违规：Service import 了 Controller
package com.example.service;
import com.example.controller.UserController; // T-01 violation

public class UserService {
    private UserController controller; // 反向依赖
}
```
- **违规示例 (Go)**:
```go
// service/user_service.go — 违规：service 包 import 了 handler 包
package service

import "myapp/handler" // T-01 violation

func ProcessUser() {
    handler.GetContext() // 反向依赖入口层
}
```
- **违规示例 (TypeScript)**:
```typescript
// services/user.service.ts — 违规：Service import Controller
import { UserController } from '../controllers/user.controller'; // T-01 violation
```

### T-02: 入口层不得包含业务逻辑

- **规则**: Controller/Handler 只负责参数接收、格式校验、调用 Service、组装响应。禁止在入口层编写业务判断（if/else 业务条件、状态机流转、金额计算等）。
- **严重级别**: warning
- **检测方法**: 在 Entry 层文件中检测业务性质的条件判断——排除格式校验类（null check、length check、type check）之后，剩余的 if/else/switch 中包含业务术语（balance、status、inventory、price、discount、expired 等）视为违规。
- **违规示例 (Java)**:
```java
// OrderController.java — 违规：Controller 中包含库存判断
@PostMapping("/orders")
public Response createOrder(@RequestBody OrderRequest req) {
    Product product = productService.getProduct(req.getProductId());
    if (product.getInventory() < req.getQuantity()) { // T-02 violation: 业务逻辑
        return Response.error("库存不足");
    }
    BigDecimal total = product.getPrice()
        .multiply(BigDecimal.valueOf(req.getQuantity())); // T-02 violation: 金额计算
    return orderService.create(req, total);
}
```
- **违规示例 (Python)**:
```python
# views/order_view.py — 违规：View 中包含折扣计算
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    product = product_service.get(data["product_id"])
    if product.status == "discontinued":  # T-02 violation: 业务状态判断
        return jsonify(error="商品已下架"), 400
    discount = 0.8 if data["is_vip"] else 1.0  # T-02 violation: 折扣逻辑
    total = product.price * data["quantity"] * discount
    return order_service.create(data, total)
```

### T-03: 入口层直接访问数据层

- **规则 (特殊)**: 入口层直接注入 Repository/DAO 时需判断是否合理。简单 CRUD（无业务判断、无组合调用、无事务要求）→ **OK (info)**；包含业务逻辑 → **违规 (warning)**。
- **严重级别**: 视情况 info 或 warning
- **检测方法**: 检测 Entry 层文件是否 import Data 层模块。若检测到，进一步分析该方法体：(1) 是否仅有单次 Repository 调用且无条件分支 → info (simple CRUD); (2) 是否存在多次 Repository 调用、if/else 判断、事务注解 → warning (含业务逻辑)。

**合格的 Simple CRUD 示例**:
```java
// UserController.java — OK：纯粹的单表查询，无业务判断
@GetMapping("/users/{id}")
public UserDTO getUser(@PathVariable Long id) {
    User user = userRepository.findById(id).orElseThrow();
    return UserDTO.from(user); // 单次查询 + 转换，无业务逻辑
}

@GetMapping("/users")
public List<UserDTO> listUsers(Pageable pageable) {
    return userRepository.findAll(pageable)
        .map(UserDTO::from).getContent(); // 单次分页查询
}
```

**违规示例——包含业务逻辑**:
```java
// OrderController.java — 违规：跳过 Service 但包含业务逻辑
@PostMapping("/orders")
public Response createOrder(@RequestBody OrderRequest req) {
    Product product = productRepository.findById(req.getProductId()).orElseThrow();
    if (product.getInventory() < req.getQuantity()) { // 业务判断 → 不是 simple CRUD
        return Response.error("库存不足");
    }
    product.setInventory(product.getInventory() - req.getQuantity()); // 库存扣减
    productRepository.save(product);
    Order order = new Order(req, product.getPrice());
    orderRepository.save(order); // 多表操作 + 事务需求 → 应在 Service 层
    return Response.ok(order);
}
```

**判定标准汇总**:

| 特征 | Simple CRUD (OK) | 含业务逻辑 (违规) |
|------|-------------------|-------------------|
| Repository 调用次数 | 1 次 | 多次 |
| 条件分支 | 无业务判断 | 有 if/else 业务条件 |
| 事务需求 | 无 | 有 @Transactional 或跨表操作 |
| 数据组合 | 无 | 多表数据拼装 |
| 写操作附带校验 | 无 | 有（库存、余额等） |

### T-04: 数据层不得反向依赖业务层

- **规则**: Repository/DAO 不能 import Service 层模块。数据层只与实体和数据库框架交互。
- **严重级别**: critical
- **检测方法**: 扫描 Data 层文件的 import 语句，匹配 Business 层的包名或模块路径。
- **违规示例 (Java)**:
```java
// UserRepository.java — 违规
package com.example.repository;
import com.example.service.NotificationService; // T-04 violation
```
- **违规示例 (Go)**:
```go
// repository/user_repo.go — 违规
package repository
import "myapp/service" // T-04 violation
```

### T-05: 实体类不得在入口层直接暴露

- **规则**: Controller/Handler 的返回值和请求参数不得直接使用 Entity 类，应使用 DTO/VO 进行隔离。防止数据库结构泄漏、序列化问题、过度暴露字段。
- **严重级别**: warning
- **检测方法**: 分析 Entry 层方法的返回类型和参数类型，若直接引用 entity/model/domain 包下的类则标记违规。检查 `@ResponseBody` 方法返回 Entity、`@RequestBody` 参数为 Entity。
- **违规示例 (Java)**:
```java
// UserController.java — 违规：直接返回 Entity
@GetMapping("/users/{id}")
public User getUser(@PathVariable Long id) { // T-05 violation: 返回 User Entity
    return userService.findById(id);
}
```
- **违规示例 (TypeScript)**:
```typescript
// user.controller.ts — 违规：直接返回数据库 model
@Get(':id')
async getUser(@Param('id') id: string): Promise<UserEntity> { // T-05 violation
    return this.userService.findById(id);
}
```

### T-06: 工具类不得依赖任何业务层

- **规则**: util/helper/common 包中的类不得 import Service、Repository、Controller。工具类应保持通用性，无业务耦合。
- **严重级别**: warning
- **检测方法**: 扫描 util/helper/common 目录下文件的 import 语句，匹配 controller/service/repository/handler 等业务层包名。
- **违规示例 (Java)**:
```java
// DateUtils.java — 违规
package com.example.util;
import com.example.service.ConfigService; // T-06 violation: 工具类依赖 Service
```
- **违规示例 (Python)**:
```python
# utils/date_helper.py — 违规
from services.config_service import ConfigService  # T-06 violation
```

---

## 两层架构规则 (W-01 ~ W-03)

适用于只有 Entry(Controller/Handler) → Data(Repository/DAO) 两层的简单项目，无独立 Business 层。

### W-01: 依赖方向 Entry → Data

- **规则**: 强制依赖方向为 Entry → Data，Data 层不得反向引用 Entry 层。
- **严重级别**: critical
- **检测方法**: 与 T-01 相同，但只检测两层间的关系。扫描 Data 层 import 是否包含 Entry 层引用。

### W-02: 业务逻辑应集中在入口层

- **规则**: 两层架构中，业务逻辑应集中在 Entry 层而非散落在 Data 层。Repository/DAO 中不应出现业务条件判断。
- **严重级别**: warning
- **检测方法**: 扫描 Data 层文件，检测是否包含业务性质的 if/else 判断（排除 null check 和数据完整性校验）。

### W-03: 实体暴露控制

- **规则**: 与 T-05 相同。即使是两层架构，也应避免直接暴露 Entity。对于极简项目（< 5 个实体）可降级为 info。
- **严重级别**: info 或 warning（视项目规模）
- **检测方法**: 同 T-05。额外统计项目实体数量以判定严重级别。

---

## DDD 规则 (D-01 ~ D-04)

适用于 Domain-Driven Design 分层：Interfaces → Application → Domain → Infrastructure。

### D-01: Domain 层零外部依赖

- **规则**: Domain 层不得引入任何框架 import（Spring、Hibernate、Express、GORM 等）和基础设施 import（database driver、HTTP client、message queue client）。Domain 层只包含纯业务逻辑和领域模型。
- **严重级别**: critical
- **检测方法**: 扫描 domain 包/目录下所有文件的 import 语句，匹配框架包名清单（`org.springframework`、`javax.persistence`、`gorm.io`、`express`、`sqlalchemy` 等）。允许标准库和领域内部引用。
- **违规示例 (Java)**:
```java
// domain/model/Order.java — 违规
package com.example.domain.model;
import javax.persistence.Entity;    // D-01 violation: 框架依赖
import javax.persistence.Id;        // D-01 violation
import org.springframework.data.annotation.CreatedDate; // D-01 violation
```
- **违规示例 (Go)**:
```go
// domain/order.go — 违规
package domain
import "gorm.io/gorm" // D-01 violation: ORM 框架依赖
```

### D-02: Application 通过接口调用 Infrastructure

- **规则**: Application 层调用 Infrastructure 层时必须通过 Domain 层定义的接口（Repository Interface / Port），不得直接依赖 Infrastructure 实现类。
- **严重级别**: critical
- **检测方法**: 扫描 Application 层 import 语句，若直接引用 `infrastructure` 包下的具体实现类则标记违规。检查注入的依赖类型是否为接口。
- **违规示例 (Java)**:
```java
// application/OrderAppService.java — 违规
import com.example.infrastructure.persistence.OrderRepositoryImpl; // D-02 violation

public class OrderAppService {
    private final OrderRepositoryImpl repo; // 应依赖 OrderRepository 接口
}
```

### D-03: 领域逻辑在 Domain 内

- **规则**: 业务规则和领域逻辑应定义在 Domain 层的 Entity/Value Object/Domain Service 中，不应散落在 Application Service。Application Service 只做编排（调用 Domain 对象 + 基础设施）。
- **严重级别**: warning
- **检测方法**: 在 Application 层文件中检测业务条件判断。若 Application Service 方法中存在大量 if/else 业务逻辑（而非纯粹的流程编排），标记为违规。启发式规则：单个方法超过 3 个业务条件分支。

### D-04: 聚合边界清晰

- **规则**: 一个聚合不得直接访问另一个聚合的内部实体。跨聚合交互应通过 Repository 获取聚合根，或通过 Domain Event。
- **严重级别**: warning
- **检测方法**: 分析 Domain 层内 import 关系。若聚合 A 的代码直接引用聚合 B 的非根实体，标记违规。需先识别聚合根（通常是有 Repository 接口的实体）。

---

## 通用规则 (G-01 ~ G-06)

适用于所有架构模式。

### G-01: 循环依赖检测

- **规则**: 任何两个或多个模块之间不得形成循环依赖。
- **严重级别**: critical
- **检测算法**:
  1. 构建 import 有向图：每个文件/模块为节点，import 关系为有向边。
  2. 使用 DFS 遍历图，维护当前访问路径栈。
  3. 若遍历时遇到已在栈中的节点，则检测到环。
  4. 记录完整的环路径：A → B → C → A。
  5. 对同一个环只报告一次，取字典序最小的节点作为起点。

### G-02: 实体公共字段未抽取基类

- **规则**: 若多个 Entity 类都定义了 `id`、`createTime`/`createdAt`、`updateTime`/`updatedAt` 等公共字段，应抽取 BaseEntity 基类。
- **严重级别**: info
- **检测方法**: 统计 Entity 类中出现 `id`、`createTime`、`updateTime` 字段的频率。若 >= 3 个 Entity 都有相同的公共字段且未继承同一基类，标记建议。

### G-03: 配置硬编码

- **规则**: 业务代码中不得硬编码配置值。URL、IP 地址、密码、端口号、magic number 应通过配置文件或环境变量注入。
- **严重级别**: warning（密码类为 critical）
- **检测方法**: 使用正则匹配以下模式：
  - URL: `https?://[^\s"']+`（排除 test 文件和注释）
  - IP: `\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`
  - 密码相关: 变量名含 `password`/`secret`/`token` 且赋值为字符串字面量
  - Magic number: 业务代码中非 0/1/-1 的数字字面量（需启发式排除数组索引和常见常量）

### G-04: 格式校验应在入口层完成

- **规则**: 格式类校验（null check、长度校验、正则校验、类型校验）应在 Entry 层完成，不应出现在 Business 层。
- **严重级别**: info
- **检测方法**: 在 Service/Business 层文件中检测以下模式：
  - 正则校验: `Pattern.compile`、`matches()`、`re.match`、`RegExp`
  - Null check: 参数 null 判断后直接抛出 `IllegalArgumentException` 或返回错误
  - 长度校验: `.length() >` / `.length <` 结合参数校验类异常
  - 手动类型判断: `instanceof` 用于参数校验

### G-05: 业务规则验证应在业务层

- **规则**: 业务性质的条件判断（余额是否充足、库存是否足够、状态是否允许流转、权限是否满足）应在 Business 层，不应出现在 Controller。
- **严重级别**: warning
- **检测方法**: 在 Entry 层文件中检测含有以下业务术语的条件判断：`balance`、`inventory`/`stock`、`status`、`state`、`permission`、`role`、`expired`、`limit`、`quota`。排除格式类校验关键词。

### G-06: 数据层不做业务验证

- **规则**: Repository/DAO 中不得包含业务逻辑条件判断。数据层只负责 CRUD 操作，业务规则在 Business 层处理。
- **严重级别**: warning
- **检测方法**: 在 Data 层文件中检测 if/else 条件语句。排除以下合法情况：null/empty 防御性编程、数据库异常处理、分页参数处理。剩余的条件分支标记为疑似业务逻辑。

---

## 分层验证原则（宽进严出）

应用 Postel's Law（宽进严出）于服务端分层，确定每一层的校验职责边界。

### 入口层 (Entry Layer) — 格式校验

负责执行格式类校验，确保输入数据格式正确后传递给业务层：

- **Null check**: 必填字段是否为空
- **Length check**: 字符串长度、集合大小
- **Regex check**: 邮箱格式、手机号格式、身份证格式
- **Type check**: 数值范围、日期格式、枚举值

将格式校验放在入口层的原因：Business 层可能被多个入口复用（REST API、gRPC、MQ Consumer），每个入口的格式要求可能不同。在入口层完成格式校验，使 Business 层可专注于业务逻辑。

### 业务层 (Business Layer) — 业务规则校验

负责执行业务规则校验，保证业务操作的合法性：

- **余额校验**: 账户余额是否足以完成扣款
- **库存校验**: 商品库存是否足以完成下单
- **状态流转**: 订单状态 PENDING → PAID 是否合法（不能 CANCELLED → PAID）
- **权限校验**: 用户角色是否有权执行该操作
- **业务唯一性**: 业务层面的去重判断（如一个用户不能重复报名）

将业务规则放在业务层的原因：业务规则跟随业务逻辑，与入口形式无关。无论请求来自 HTTP、gRPC 还是消息队列，业务规则保持一致。

### 数据层 (Data Layer) — 数据完整性

只负责数据存储层面的约束：

- **Unique constraint**: 数据库唯一索引
- **Foreign key**: 外键约束
- **Type constraint**: 字段类型、长度限制
- **Not null constraint**: 数据库层面的非空约束

禁止在数据层执行业务验证。数据层的 Repository/DAO 只进行数据存取，不判断业务条件。

---

## 检测模式（按语言）

各语言的 import/依赖检测 grep 模式：

### Java
```
# import 语句
grep -rn "^import\s" --include="*.java"
# 匹配包名层级：controller/service/repository/domain
pattern: ^import\s+[\w.]+\.(controller|service|repository|dao|domain|infrastructure|application)\.
```

### Go
```
# import 语句
grep -rn "\"[\w/]+\"" --include="*.go"
# 匹配包路径中的层级目录
pattern: "[\w/]+/(handler|controller|service|repository|dao|domain|infrastructure)"
```

### Node.js / TypeScript
```
# import/require 语句
grep -rn "import\s.*from\|require(" --include="*.ts" --include="*.js"
# 匹配路径中的层级目录
pattern: (import|require).*['"]\.\./*(controllers?|services?|repositories?|models?|domain|infrastructure)
```

### Python
```
# import 语句
grep -rn "^from\s\|^import\s" --include="*.py"
# 匹配模块路径中的层级
pattern: ^(from|import)\s+[\w.]*\.(controllers?|services?|repositories?|models?|domain|infrastructure)
```

### .NET (C#)
```
# using 语句
grep -rn "^using\s" --include="*.cs"
# 匹配 namespace 层级
pattern: ^using\s+[\w.]+\.(Controllers?|Services?|Repositories?|Domain|Infrastructure)
```

### Rust
```
# use 语句
grep -rn "^use\s" --include="*.rs"
# 匹配 module 路径
pattern: ^use\s+(crate::)?(handlers?|services?|repositories?|domain|infrastructure)
```

---

## 输出格式

Phase 1 检测结果输出为 `phase1-compliance.json`，schema 定义如下：

```json
{
  "architecture": "three-tier | two-tier | ddd | unknown",
  "detectedLayers": ["entry", "business", "data"],
  "violations": [
    {
      "rule": "T-03",
      "severity": "warning",
      "file": "src/main/java/com/example/controller/UserController.java",
      "line": 45,
      "description": "入口层直接访问数据层且包含业务逻辑：Controller 中注入 Repository 并存在库存判断条件分支",
      "evidence": "import com.example.repository.UserRepository",
      "label": "MUST-FIX",
      "suggestion": {
        "pre-launch": "将业务逻辑提取到 UserService，Controller 仅调用 Service 方法",
        "maintenance": "记录为 TECH-DEBT，下次迭代重构时迁移到 Service 层"
      }
    },
    {
      "rule": "G-03",
      "severity": "critical",
      "file": "src/main/java/com/example/service/PaymentService.java",
      "line": 12,
      "description": "硬编码密码字符串",
      "evidence": "String apiKey = \"sk-live-abc123def456\";",
      "label": "MUST-FIX",
      "suggestion": {
        "pre-launch": "将 apiKey 迁移至环境变量或配置中心，代码中通过 @Value 或 os.environ 读取",
        "maintenance": "立即修复——安全风险，不论项目阶段"
      }
    }
  ],
  "summary": {
    "critical": 2,
    "warning": 5,
    "info": 3
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `architecture` | string | 检测到的架构模式 |
| `detectedLayers` | string[] | 识别到的分层 |
| `violations[].rule` | string | 规则 ID（T-01 ~ T-06, W-01 ~ W-03, D-01 ~ D-04, G-01 ~ G-06） |
| `violations[].severity` | string | `critical` / `warning` / `info` |
| `violations[].file` | string | 违规文件路径 |
| `violations[].line` | number | 违规行号 |
| `violations[].description` | string | 中文违规描述 |
| `violations[].evidence` | string | 触发违规的代码片段或 import 语句 |
| `violations[].label` | string | `MUST-FIX`（critical/warning） / `TECH-DEBT`（info 或维护阶段的 warning） |
| `violations[].suggestion` | object | 分阶段修复建议：`pre-launch`（上线前）和 `maintenance`（维护期） |
| `summary` | object | 各严重级别的违规计数 |

### Label 判定规则

- **MUST-FIX**: 所有 critical 违规；warning 违规在 pre-launch 阶段
- **TECH-DEBT**: info 违规；warning 违规在 maintenance 阶段（已上线项目酌情排期）

### Severity 汇总

- **critical**: 架构方向性错误，导致维护成本急剧上升（T-01, T-04, D-01, D-02, G-01, G-03 密码类）
- **warning**: 职责越界，当前可工作但长期劣化（T-02, T-03 含业务逻辑, T-05, T-06, G-03 非密码类, G-04, G-05, G-06）
- **info**: 改进建议，提升代码质量（T-03 simple CRUD, W-03 极简项目, G-02）


### 来源文件：`references/phase2-duplicates.md`

# Phase 2: 重复代码检测 (Duplication Detection)

对服务端代码进行结构化重复检测，覆盖 Entry（API/入口）、Business（业务）、Data（数据）、Utility（工具）四层。核心思路：不做逐行 diff，而是提取方法的**结构签名**进行相似度比对，阈值 70%。

---

## 2-1. API/入口层重复

### 检测模式

#### 模式 A：相似的导出逻辑

多个 Controller 各自实现 export 方法，内部逻辑均为 query → transform → write Excel → return stream。仅 entity 名称和查询条件不同。

**Java (Spring Boot) 示例：**

```java
// UserController.java
@GetMapping("/users/export")
public void exportUsers(HttpServletResponse response, UserQuery query) {
    List<User> list = userService.list(query);
    List<UserExcelVO> voList = list.stream().map(UserExcelVO::from).collect(toList());
    ExcelUtil.write(response, "users.xlsx", UserExcelVO.class, voList);
}

// OrderController.java
@GetMapping("/orders/export")
public void exportOrders(HttpServletResponse response, OrderQuery query) {
    List<Order> list = orderService.list(query);
    List<OrderExcelVO> voList = list.stream().map(OrderExcelVO::from).collect(toList());
    ExcelUtil.write(response, "orders.xlsx", OrderExcelVO.class, voList);
}
```

结构签名完全一致：`(Query, Response) → [service.list, stream.map, ExcelUtil.write] → (void)`。

**Node.js (NestJS) 示例：**

```typescript
// user.controller.ts
@Get('users/export')
async exportUsers(@Query() query: UserQueryDto, @Res() res: Response) {
  const list = await this.userService.findAll(query);
  const rows = list.map(toUserExcelRow);
  const buffer = await generateExcel(rows, UserColumns);
  res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
  res.send(buffer);
}

// order.controller.ts
@Get('orders/export')
async exportOrders(@Query() query: OrderQueryDto, @Res() res: Response) {
  const list = await this.orderService.findAll(query);
  const rows = list.map(toOrderExcelRow);
  const buffer = await generateExcel(rows, OrderColumns);
  res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
  res.send(buffer);
}
```

#### 模式 B：相似的分页/排序/过滤实现

每个 Controller 各自解析 `page`、`size`、`sort`、`filter` 参数，手动构造分页对象。

```java
// 在多个 Controller 中重复出现
int page = query.getPage() != null ? query.getPage() : 1;
int size = query.getSize() != null ? query.getSize() : 20;
String sort = query.getSort() != null ? query.getSort() : "id";
String direction = query.getDirection() != null ? query.getDirection() : "DESC";
PageRequest pageRequest = PageRequest.of(page - 1, size, Sort.by(Sort.Direction.fromString(direction), sort));
```

#### 模式 C：相似的 CRUD endpoint handler

每个 Controller 的 create / update / delete 方法遵循相同流程：validate input → call service → wrap response。

```java
// 几乎每个 Controller 都有这种结构
@PostMapping
public Result<UserVO> create(@Valid @RequestBody UserCreateDTO dto) {
    return Result.ok(userService.create(dto));
}

@PutMapping("/{id}")
public Result<UserVO> update(@PathVariable Long id, @Valid @RequestBody UserUpdateDTO dto) {
    return Result.ok(userService.update(id, dto));
}

@DeleteMapping("/{id}")
public Result<Void> delete(@PathVariable Long id) {
    userService.delete(id);
    return Result.ok();
}
```

### 合并策略

| 模式 | 合并方式 | 说明 |
|------|---------|------|
| 相似导出 | 创建通用 `ExportController`，接收 module 参数 | `GET /export?module=user&query=...`，内部通过策略模式路由到对应 Service |
| 相似分页 | 提取 `PageableResolver` 工具类或自定义 `@PageableDefault` 注解 | 统一解析逻辑，Controller 直接接收 `Pageable` 对象 |
| 相似 CRUD | 创建 `BaseCrudController<E, CreateDTO, UpdateDTO, VO>`，子类仅声明泛型 | NestJS 中可用 mixin 模式实现 |

---

## 2-2. 业务层重复

### 检测模式

#### 模式 A：相似的 CRUD 流程

多个 Service 的 create/update/getById 方法内部步骤完全一致，仅 entity 类型不同。

```java
// UserService.java
public UserVO create(UserCreateDTO dto) {
    validateCreate(dto);           // 1. validate
    User entity = toEntity(dto);   // 2. transform
    setDefaults(entity);           // 3. set defaults
    userRepo.save(entity);         // 4. save
    return toVO(entity);           // 5. transform to VO
}

// OrderService.java
public OrderVO create(OrderCreateDTO dto) {
    validateCreate(dto);           // 1. validate
    Order entity = toEntity(dto);  // 2. transform
    setDefaults(entity);           // 3. set defaults
    orderRepo.save(entity);        // 4. save
    return toVO(entity);           // 5. transform to VO
}
```

结构签名：`(CreateDTO) → [validate, toEntity, setDefaults, repo.save, toVO] → (VO)`，相似度 100%。

#### 模式 B：复制粘贴仅改 entity 名称

典型表现为方法体结构完全相同，仅将 `User` 替换为 `Order`、`userRepo` 替换为 `orderRepo`。扫描时提取操作序列（去除具体类型名称）即可发现。

#### 模式 C：相似的业务规则

状态机、审批流等结构性相似的业务逻辑。例如订单审批和退款审批都实现了 `submit → review → approve/reject → complete` 的状态流转，内部校验与通知逻辑结构一致。

#### 模式 D：Passthrough Service 检测（T-03 规则）

识别仅做透传的 Service 方法——方法体只调用一个 Repository/DAO 方法并直接返回结果，无任何业务逻辑。

**Passthrough 示例（应标记）：**

```java
// UserService.java — passthrough，无业务逻辑
public User getById(Long id) {
    return userRepository.findById(id).orElseThrow(() -> new NotFoundException("User not found"));
}
```

```typescript
// user.service.ts — passthrough
async findById(id: string): Promise<User> {
  return this.userRepository.findOneOrFail({ where: { id } });
}
```

上述方法仅做 Repository 调用 + 异常包装，无校验、无转换、无副作用。建议移除该 Service 方法，让 Entry 层直接调用 Data 层。

**合法 Service 逻辑示例（不应标记）：**

```java
// UserService.java — 有真实业务逻辑
public UserVO getById(Long id) {
    User user = userRepository.findById(id)
        .orElseThrow(() -> new NotFoundException("User not found"));
    enrichWithDepartment(user);       // 关联查询
    auditService.logAccess(id);       // 副作用：审计日志
    return UserVO.from(user);         // 数据转换
}
```

判定标准：方法内除 repository 调用外，存在**额外操作**（关联查询、副作用、数据转换、权限校验等）则为合法 Service 逻辑。

---

## 2-3. 数据层重复

### 检测模式

#### 模式 A：相似的查询逻辑

多个 Repository/DAO 的查询方法仅在表名和条件字段上不同，查询结构（JOIN、WHERE 组合方式、分页排序）完全一致。

```java
// UserRepository
@Query("SELECT u FROM User u WHERE u.status = :status AND u.name LIKE :keyword ORDER BY u.createdAt DESC")
Page<User> search(@Param("status") Integer status, @Param("keyword") String keyword, Pageable pageable);

// OrderRepository
@Query("SELECT o FROM Order o WHERE o.status = :status AND o.title LIKE :keyword ORDER BY o.createdAt DESC")
Page<Order> search(@Param("status") Integer status, @Param("keyword") String keyword, Pageable pageable);
```

#### 模式 B：重复的分页/排序/过滤逻辑

Data 层各自实现分页参数处理，而非统一委托给框架或共享工具。

#### 模式 C：DTO/VO 字段高度重叠

多个 DTO 或 VO 之间字段重合度超过 70%。

**检测方法（Jaccard 相似度）：**

1. 提取每个 DTO/VO 的所有字段名集合，例如：
   - `UserDTO = {id, name, email, phone, status, createdAt, updatedAt, avatar, role, department}`
   - `UserVO = {id, name, email, phone, status, createdAt, updatedAt, avatar}`
2. 计算 Jaccard 系数：`J = |A ∩ B| / |A ∪ B|`
   - 交集：`{id, name, email, phone, status, createdAt, updatedAt, avatar}` = 8 个
   - 并集：`{id, name, email, phone, status, createdAt, updatedAt, avatar, role, department}` = 10 个
   - `J = 8 / 10 = 0.80` → 超过 70% 阈值 → 标记

> 注意：跨层的 Entity ↔ DTO 重叠属于架构设计意图，见「误判排除」一节。仅对**同层或相邻层的非 Entity 类型**计算。

#### 模式 D：相似的 mapper/converter 方法

多个 converter 类中存在结构一致的字段映射方法，逐字段 set/get 且映射方式无差异。

---

## 2-4. 工具类重复

### 检测模式

#### 模式 A：不同包中的同名工具类

多个模块各自包含功能相同的工具类，例如 `com.app.user.util.DateUtils` 和 `com.app.order.util.DateUtils` 内部方法签名和实现一致。

**检测方法：**
1. 扫描所有以 `Utils`、`Helper`、`Tool`、`Common` 结尾（或在 `util`/`utils`/`common`/`shared`/`helper` 目录下）的类/文件。
2. 提取方法签名列表。
3. 对不同文件中的同名方法做签名比对（参数类型 + 返回类型 + 操作序列）。
4. 签名匹配度 > 70% 即标记。

#### 模式 B：重新实现已有依赖的能力

项目依赖中已包含 Apache Commons Lang、Guava、Lodash 等工具库，但代码中自行实现了相同功能。

检测方式：维护常见工具库的 API 清单，扫描自定义工具方法的签名和功能描述，匹配已有库中的等价方法。

常见案例：
- 自定义 `StringUtils.isEmpty()` vs `org.apache.commons.lang3.StringUtils.isEmpty()`
- 自定义 `CollectionUtils.partition()` vs `com.google.common.collect.Lists.partition()`
- 自定义 `deepClone()` vs `lodash.cloneDeep()`

#### 模式 C：跨模块复制工具类

同一个工具类文件被复制到多个模块，而非抽取为 shared module 引用。通过文件内容 hash 或方法签名集合相似度检测。

---

## 结构签名方法

### 核心算法

结构签名（Structural Signature）是 Phase 2 的核心检测手段，用于避免逐行 diff 带来的噪音（变量命名、空格、注释差异等），聚焦于方法的**行为结构**。

**提取步骤：**

1. **解析入参类型**：提取方法参数的抽象类型（DTO、ID、Query 等），忽略具体类名。
2. **识别操作序列**：按执行顺序提取方法体内的操作类型：
   - `validate` — 参数校验、断言
   - `query` / `db-read` — 数据库读取
   - `db-write` / `save` — 数据库写入
   - `api-call` — 外部 API 调用
   - `transform` / `map` — 数据转换
   - `setDefaults` — 默认值设置
   - `notify` — 消息/事件发送
   - `log` — 日志记录
   - `cache-read` / `cache-write` — 缓存操作
3. **提取返回类型**：抽象为 VO、Entity、void、List、Page 等。
4. **生成签名字符串**：`(抽象入参) → [操作序列] → (抽象返回)`。

**比对方式：**

对两个签名中的操作序列计算编辑距离（Levenshtein distance），归一化后得到相似度。阈值设定为 **70%**——高于 70% 即判定为候选重复对。

### 示例

```
UserService.create:    (CreateDTO) → [validate, transform, setDefaults, db-write, transform] → (VO)
OrderService.create:   (CreateDTO) → [validate, transform, setDefaults, db-write, transform] → (VO)
Similarity: 100% → 候选重复

UserService.update:    (ID, UpdateDTO) → [db-read, validate, merge, db-write, transform] → (VO)
ProductService.update: (ID, UpdateDTO) → [db-read, validate, merge, db-write, transform, notify] → (VO)
Similarity: 5/6 operations match = 83% → 候选重复

UserService.register:  (RegisterDTO) → [validate, transform, db-write, api-call, notify] → (VO)
OrderService.create:   (CreateDTO) → [validate, transform, setDefaults, db-write, transform] → (VO)
Similarity: 2/5 exact position match = 40% → 不标记
```

---

## 误判排除

以下场景**不应**标记为重复：

### 1. 跨层的有意隔离

Entity（Data 层）与 DTO（Entry 层）字段高度重叠属于分层架构的设计意图，不是重复。保持各层独立的数据模型是为了解耦——Data 层 schema 变更不应直接暴露给 API 消费者。

**判定规则：** Entity 与 DTO/VO 之间的字段重叠不计入 DTO overlap 检测。仅对**同层**的多个 DTO 之间或同层多个 VO 之间进行比对。

### 2. 框架强制的样板代码

以下属于框架要求，不构成可消除的重复：
- Spring Boot：`@RestController`、`@Service`、`@Repository` 注解声明
- NestJS：`@Controller()`、`@Injectable()`、`@Module()` 装饰器
- JPA Entity：`@Entity`、`@Table`、`@Column` 注解
- Lombok：`@Data`、`@Builder` 等注解

**判定规则：** 在提取结构签名时，忽略框架注解/装饰器。仅分析方法体内的操作序列。

### 3. 测试代码

测试文件中可能存在大量重复的 setup 逻辑（mock 初始化、测试数据构造），这些重复往往是有意为之，目的是保持测试用例独立可读。

**判定规则：** 对 `*Test.java`、`*Spec.ts`、`*.test.ts`、`*.spec.ts`、`*_test.go` 等测试文件，默认跳过或降低告警级别（severity: `info` 而非 `warning`）。

### 4. 极小方法

单行或两行的简单委托方法（如 getter/setter wrapper）不标记，避免产生过量低价值告警。

**判定规则：** 方法体操作序列长度 < 2 时跳过。

---

## 输出格式

Phase 2 的检测结果输出为 `phase2-duplicates.json`，schema 如下：

```json
{
  "duplicate_pairs": [
    {
      "id": "DUP-001",
      "type": "entry-layer",
      "similarity": 85,
      "file_a": {
        "path": "src/controller/UserController.java",
        "method": "exportUsers",
        "line_start": 45,
        "line_end": 52
      },
      "file_b": {
        "path": "src/controller/OrderController.java",
        "method": "exportOrders",
        "line_start": 38,
        "line_end": 45
      },
      "structural_signature": "(Query, Response) → [service.list, stream.map, ExcelUtil.write] → (void)",
      "suggestion": {
        "pre-launch": "合并为通用 ExportController，接收 module 参数路由到对应 Service",
        "maintenance": "提取 exportTemplate() 方法至 BaseController，原方法标注 @Deprecated 后逐步替换"
      }
    }
  ],
  "passthrough_services": [
    {
      "service_file": "src/service/UserService.java",
      "method": "getById",
      "delegates_to": "userRepository.findById",
      "suggestion": "Remove passthrough, let Entry call Data directly"
    }
  ],
  "dto_overlaps": [
    {
      "dto_a": "src/dto/UserDTO.java",
      "dto_b": "src/dto/UserVO.java",
      "overlap_percentage": 80,
      "shared_fields": ["id", "name", "email", "phone", "status", "createdAt", "updatedAt", "avatar"],
      "suggestion": "提取共享字段为 UserBase，UserDTO extends UserBase 增加 role/department，UserVO extends UserBase"
    }
  ],
  "summary": {
    "total_pairs": 12,
    "by_layer": {
      "entry": 3,
      "business": 5,
      "data": 2,
      "utility": 2
    }
  }
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识，格式 `DUP-NNN` |
| `type` | enum | `entry-layer` / `business-layer` / `data-layer` / `utility` |
| `similarity` | number | 结构相似度百分比（70-100） |
| `file_a` / `file_b` | object | 重复对的两个方法的位置信息 |
| `structural_signature` | string | 匹配的结构签名描述 |
| `suggestion.pre-launch` | string | 上线前模式下的合并建议 |
| `suggestion.maintenance` | string | 维护模式下的渐进式重构建议 |
| `passthrough_services[].delegates_to` | string | 被透传调用的 Repository 方法 |
| `dto_overlaps[].overlap_percentage` | number | Jaccard 相似度百分比 |
| `dto_overlaps[].shared_fields` | array | 重叠的具体字段名列表 |

---

## 模式区分

### Pre-launch 模式（上线前）

项目尚未上线或处于大版本重构期，可承受较大改动范围。

**策略：直接合并/重写。**

- 给出**目标结构**而非增量修改步骤。
- 示例建议：「合并 UserController.export 和 OrderController.export 为 GenericExportController.export(String module, Query query)，通过 Map<String, ExportStrategy> 路由到具体实现。」
- 对 passthrough service 直接建议删除，调用方改为直接引用 Repository。
- 对 DTO overlap 建议提取 base class 或使用组合模式（composition）。

**Pre-launch 输出重点：**
1. 合并后的目标类/方法结构描述。
2. 需要删除的文件或方法列表。
3. 需要修改的调用方列表。

### Maintenance 模式（维护期）

项目已上线运行，需要渐进式重构以控制风险。

**策略：提取共享 → 保留原接口 → 标记废弃 → 逐步替换。**

- 第一步：提取公共逻辑为新方法/类（如 `AbstractCrudService<E, D, V>`）。
- 第二步：原方法内部改为委托调用新方法，保持外部接口不变。
- 第三步：原方法标注 `@Deprecated`（Java）或 `/** @deprecated */`（TypeScript）。
- 第四步：在后续迭代中逐步将调用方切换到新接口，最终删除旧方法。

**Maintenance 输出重点：**
1. 提取出的共享方法/类的建议实现。
2. 原方法的委托改造示例。
3. 废弃标记和替换时间线建议。

---

## 检测优先级

按影响面和修复收益排序检测优先级：

| 优先级 | 类型 | 原因 |
|--------|------|------|
| P0 | Passthrough Service | 违反分层原则（T-03），修复成本最低，收益明确 |
| P1 | 业务层 CRUD 重复 | 影响面最广，通常涉及多个 Service |
| P2 | 入口层重复 | 影响 API 一致性，合并后可减少大量模板代码 |
| P3 | 工具类重复 | 维护风险（修一处漏一处），但影响面相对局部 |
| P4 | DTO/VO 重叠 | 需要权衡改动范围，跨层影响需谨慎 |
| P5 | 数据层查询重复 | 多数可通过泛型 Repository 解决，但需评估 ORM 框架支持度 |


### 来源文件：`references/phase3-abstractions.md`

# Phase 3: 抽象机会分析

> 本阶段在 Phase 2（重复检测）之后执行。依赖 `tuner-profile.json` 中的层级映射和模块列表，以及 `phase2-duplicates.json` 中已识别的重复项。

Phase 3 从五个维度分析抽象机会：垂直抽象（继承/基类）、横向抽象（组合/工具方法）、接口合并（API 参数化）、验证逻辑规范性、过度抽象检测。同时检测"该抽象没抽象"和"不该抽象却抽象了"两个方向。

---

## 3-1. 垂直抽象（继承/基类）

### 检测目标

找出多个类之间存在 >60% 结构重叠的情况，评估是否适合抽取公共基类。

### 检测方法

1. 从 Phase 2 的重复检测结果中提取已识别的相似类对
2. 对同一层级（通常是 Business 层或 Data 层）的类进行结构签名比对：提取每个类的方法列表，比较方法签名模式（参数类型序列 -> 操作序列 -> 返回类型）
3. 计算结构重叠率：`重叠方法数 / max(类A方法数, 类B方法数) * 100`
4. 重叠率 >60% 的类组标记为垂直抽象候选

### 常见模式

以下是服务端项目中最常见的垂直抽象机会：

**BaseService（CRUD 模板方法）**

最高频的模式。多个 Service 类包含结构相同的 `create`、`update`、`delete`、`getById`、`page` 方法，仅实体类型和少量验证逻辑不同。

**BaseController（通用端点模式）**

多个 Controller 包含相同的 CRUD 端点定义、相同的参数解析逻辑、相同的响应包装。

**BaseEntity（公共字段）**

多个实体类包含相同的基础字段：`id`、`createTime`、`updateTime`、`isDeleted`、`createdBy`、`updatedBy`。这通常是最容易也最安全的垂直抽象。

### 具体示例（Java）

```java
// Before: 3 个 Service 具有相同的 create 流程
// UserService.java
public UserVO create(UserDTO dto) {
    validateUser(dto);           // 验证
    User entity = toEntity(dto); // DTO -> Entity
    setDefaults(entity);         // 设置默认值(createTime, createdBy...)
    userRepo.save(entity);       // 持久化
    return toVO(entity);         // Entity -> VO
}

// OrderService.java
public OrderVO create(OrderDTO dto) {
    validateOrder(dto);
    Order entity = toEntity(dto);
    setDefaults(entity);
    orderRepo.save(entity);
    return toVO(entity);
}

// ProductService.java
public ProductVO create(ProductDTO dto) {
    validateProduct(dto);
    Product entity = toEntity(dto);
    setDefaults(entity);
    productRepo.save(entity);
    return toVO(entity);
}
```

```java
// After: 抽取 BaseService<E, D, V>
public abstract class BaseService<E extends BaseEntity, D, V> {

    protected abstract JpaRepository<E, Long> getRepository();

    public V create(D dto) {
        validate(dto);
        E entity = toEntity(dto);
        setDefaults(entity);
        getRepository().save(entity);
        return toVO(entity);
    }

    public V update(Long id, D dto) {
        E entity = getRepository().findById(id)
            .orElseThrow(() -> new NotFoundException(id));
        validate(dto);
        updateEntity(entity, dto);
        getRepository().save(entity);
        return toVO(entity);
    }

    public void delete(Long id) {
        E entity = getRepository().findById(id)
            .orElseThrow(() -> new NotFoundException(id));
        entity.setIsDeleted(true);
        getRepository().save(entity);
    }

    public V getById(Long id) {
        E entity = getRepository().findById(id)
            .orElseThrow(() -> new NotFoundException(id));
        return toVO(entity);
    }

    public PageResult<V> page(PageQuery query) {
        Page<E> page = getRepository().findAll(buildSpec(query), query.toPageable());
        return PageResult.of(page.map(this::toVO));
    }

    // 子类实现差异部分
    protected abstract void validate(D dto);
    protected abstract E toEntity(D dto);
    protected abstract void updateEntity(E entity, D dto);
    protected abstract V toVO(E entity);

    protected void setDefaults(E entity) {
        entity.setCreateTime(LocalDateTime.now());
        entity.setIsDeleted(false);
    }
}
```

```java
// 子类只需实现差异逻辑
public class UserService extends BaseService<User, UserDTO, UserVO> {
    @Override protected JpaRepository<User, Long> getRepository() { return userRepo; }
    @Override protected void validate(UserDTO dto) { /* 用户特有验证 */ }
    @Override protected User toEntity(UserDTO dto) { /* 用户特有转换 */ }
    @Override protected void updateEntity(User entity, UserDTO dto) { /* 用户特有更新 */ }
    @Override protected UserVO toVO(User entity) { /* 用户特有VO映射 */ }
}
```

### Go 语言中的等价模式

Go 没有继承，使用嵌入 struct + 泛型（Go 1.18+）实现类似效果：

```go
// 通过泛型函数 + interface 约束实现
type Entity interface {
    SetCreateTime(t time.Time)
    SetDeleted(d bool)
}

func Create[E Entity, D any, V any](
    repo Repository[E],
    toEntity func(D) E,
    toVO func(E) V,
    validate func(D) error,
) func(D) (V, error) {
    return func(dto D) (V, error) {
        if err := validate(dto); err != nil { return *new(V), err }
        entity := toEntity(dto)
        entity.SetCreateTime(time.Now())
        if err := repo.Save(entity); err != nil { return *new(V), err }
        return toVO(entity), nil
    }
}
```

### 何时不应抽取基类

识别以下情况时，不建议抽取垂直抽象，即使表面结构相似：

- **业务逻辑即将分化**：当前 create 流程相同，但已知不同实体的 create 逻辑将沿不同方向演化（例如订单 create 即将加入库存锁定、支付流程，而用户 create 保持简单）
- **方法签名相似但语义不同**：`validate()` 虽然签名相同，但各类的验证逻辑完全不同且复杂，抽取基类后 abstract 方法过多，基类变成空壳
- **强制继承破坏单一职责**：某些类已有其他继承关系（框架要求），再加一层继承会导致继承链过深
- **团队对泛型/模板不熟悉**：抽取后代码可读性反而下降，维护成本增加

判断规则：如果抽取基类后，子类需要 override 超过 50% 的模板方法，说明差异大于共性，不应抽取。

---

## 3-2. 横向抽象（组合/工具方法）

### 检测目标

找出散落在多个文件中的相似代码片段，评估是否适合抽取为共享 utility 或 service。

### 检测方法

1. 从 Phase 2 的重复检测结果中提取跨文件的代码片段重复
2. 对非完整方法级别的重复（代码块级别），分析其功能共性
3. 统计同一模式出现的文件数，出现在 >= 3 个文件中的模式优先处理
4. 评估参数化可行性：差异部分是否可以通过参数、回调、配置抽离

### 常见模式

**Excel/CSV 导出逻辑**

多个 Controller 或 Service 中包含相似的导出流程：查询数据 -> 构建表头 -> 填充行 -> 设置样式 -> 写入流 -> 返回响应。差异仅在于查询方法、列定义、数据映射。

```
// 散落在 UserController, OrderController, ProductController 中
query data → build header → fill rows → set style → write stream → response
```

建议：抽取 `ExportService.export(query, columnDefs, rowMapper)` 或 `ExcelExportUtil`。

**分页参数解析**

多处手动解析 `pageNum`、`pageSize`、`sortField`、`sortOrder`，做默认值处理和范围校验。

建议：抽取 `PageQuery` 值对象，统一在入口层解析。对于 Spring Boot 项目使用 `Pageable` 参数解析器；对于 Go 项目使用 middleware 统一解析。

**响应包装**

多处手动构建统一响应格式 `{ code, message, data }`，包括成功响应和错误响应。

建议：抽取 `Result<T>` 响应包装类 + 全局异常处理器，Controller 方法直接返回业务数据，包装由框架层自动处理。

**文件上传处理**

多处包含相同的文件校验（大小、类型）、存储路径生成、保存逻辑。

建议：抽取 `FileStorageService`，提供 `upload(file, config)` 方法，config 包含允许的类型、大小限制、存储策略。

**日期/时间格式化**

多处包含相同的日期解析和格式化逻辑，尤其是处理多种输入格式的场景。

建议：抽取 `DateTimeUtil`，或统一使用框架级 serializer/deserializer 配置。

### 抽取原则

- 将差异部分参数化：通过方法参数、泛型、回调函数（Function/Consumer）、配置对象传入差异
- 保持工具方法无状态：不依赖类成员变量，纯输入输出
- 考虑职责归属：通用技术逻辑放 Utility 层，涉及业务概念的放 Business 层的共享 Service
- 命名反映功能而非调用者：用 `ExcelExportUtil` 而非 `UserExportHelper`

---

## 3-3. 接口合并（API 参数化）

### 检测目标

找出多个 API 端点逻辑完全相同、仅实体/资源类型不同的情况，评估是否可合并为参数化接口。

### 检测方法

1. 提取所有 Controller/Handler 的端点方法
2. 比较端点方法的操作序列签名（忽略具体实体类型）
3. 操作序列完全相同且 >= 3 个端点匹配时，标记为合并候选

### 典型模式

```
GET  /user/page    → parsePageParams → buildQuery → repo.page → wrapResponse
GET  /order/page   → parsePageParams → buildQuery → repo.page → wrapResponse
GET  /product/page → parsePageParams → buildQuery → repo.page → wrapResponse

POST /user/export    → queryAll → buildExcel → streamResponse
POST /order/export   → queryAll → buildExcel → streamResponse
POST /product/export → queryAll → buildExcel → streamResponse

GET  /user/{id}    → repo.findById → checkNull → toVO → wrapResponse
GET  /order/{id}   → repo.findById → checkNull → toVO → wrapResponse
GET  /product/{id} → repo.findById → checkNull → toVO → wrapResponse
```

### 合并策略（按语言）

**Java / Spring Boot**

方案 A：泛型 Controller 基类

```java
public abstract class BaseCrudController<E, D, V> {
    protected abstract BaseService<E, D, V> getService();

    @GetMapping("/page")
    public PageResult<V> page(PageQuery query) {
        return getService().page(query);
    }

    @GetMapping("/{id}")
    public V getById(@PathVariable Long id) {
        return getService().getById(id);
    }

    @PostMapping
    public V create(@RequestBody @Valid D dto) {
        return getService().create(dto);
    }
}
```

方案 B：共享 Mixin/Trait（Kotlin interface with default methods）

方案 C：通用 middleware + 路由配置（适合高度动态的场景）

**Go / Gin or Echo**

使用高阶函数生成 handler：

```go
func CrudHandlers[E Entity, D any, V any](svc Service[E, D, V]) {
    return func(r *gin.RouterGroup) {
        r.GET("/page", PageHandler(svc))
        r.GET("/:id", GetByIdHandler(svc))
        r.POST("", CreateHandler(svc))
    }
}
```

**Node.js / NestJS**

使用 Mixin 模式或动态 module：

```typescript
function CrudController<E, D, V>(entityCls: Type<E>): Type<ICrudController<D, V>> {
    class BaseCrud implements ICrudController<D, V> {
        constructor(private service: BaseService<E, D, V>) {}
        @Get('page') page(@Query() q: PageQuery) { return this.service.page(q); }
        @Get(':id') getById(@Param('id') id: string) { return this.service.getById(id); }
    }
    return BaseCrud;
}
```

### 何时不应合并

识别以下情况时，不建议合并 API 端点：

- **鉴权策略不同**：用户列表只有管理员可查，订单列表用户自己可查 — 合并后权限控制变复杂
- **过滤条件不同**：用户列表按角色过滤，订单列表按状态+时间过滤，产品列表按分类+价格过滤 — 查询构建器无法统一
- **响应格式不同**：用户返回脱敏信息，订单返回关联商品，产品返回库存信息 — VO 结构差异大
- **性能特征不同**：某些端点需要缓存，某些需要实时查询，某些需要关联查询 — 统一处理会拖慢简单场景或遗漏优化
- **端点即将分化**：业务需求明确不同端点将沿不同方向演化

判断规则：如果合并后需要在通用逻辑中加入 >= 3 个 `if entity == "xxx"` 的分支判断，说明差异已超过共性，不应合并。

---

## 3-4. 验证逻辑分析

### 分层验证原则（宽进严出 / Postel's Law）

验证逻辑的位置和策略直接影响代码质量和可维护性。遵循 Postel's Law（宽进严出）：

- **宽进（入口层）**：接受各种合理的输入格式，做容错处理。执行简单格式校验：非空、长度、正则匹配、类型转换。目的是拦截明显无效的输入，减轻后续层的负担。格式校验放在入口层的原因是业务层可能被多个入口调用（HTTP API、MQ consumer、定时任务、RPC），每个入口的输入格式可能不同，格式校验不应下沉到业务层重复编写。
- **严出（返回值）**：返回给调用方的数据必须结构完整、格式统一。null 值处理一致（是返回 null 还是空集合还是抛异常），错误响应格式统一（统一 error code + message 结构），日期/金额等格式标准化。

### 反模式：严进宽出

入口层对输入格式要求极其严格（不做容错），但输出给前端的数据格式却不统一（有时返回 null，有时返回空数组，有时字段缺失）。这是最常见的验证反模式。

### 检查项

| 检查项 | 问题描述 | 检测方法 |
|--------|----------|----------|
| 验证逻辑位置是否合理 | 格式校验（regex、length、null check）出现在 Service/Business 层 | 在 Business layer files 中 grep regex patterns、`.length()`/`len()`、`== null`/`== nil` 等格式校验特征 |
| 业务校验位置是否合理 | 业务规则（余额、库存、状态流转）出现在 Controller/Entry 层 | 在 Entry layer files 中 grep balance、inventory、stock、status 等业务概念 |
| 验证逻辑是否重复 | 同一字段在多处重复校验 | 找相同的正则表达式或相同字段名的校验逻辑出现在多个文件中 |
| 是否严进宽出（反模式） | 入口层严格拒绝各种输入，但输出格式却不一致 | 检查返回值中 null vs `[]` vs `{}` 的混用、日期格式不统一、error 结构不统一 |
| 错误响应是否统一 | 验证失败时的响应格式不一致 | 检查异常处理返回值格式：有的返回 `{code, msg}`，有的返回 `{error}`，有的直接返回 string |
| 校验注解/装饰器是否生效 | 声明了 `@Valid` / `@Validated` 等注解但未触发 | 检查 Controller 参数是否有 `@Valid`（Java）、`validate` pipe（NestJS）、binding tag（Go） |

### 检测流程

1. 从 `tuner-profile.json` 获取层级映射，确定每个文件属于哪一层
2. 在 Entry layer 文件中搜索业务概念关键词（balance, inventory, stock, status, permission 等），标记为"业务校验位置不当"
3. 在 Business layer 文件中搜索格式校验特征（regex, length, pattern, email format, phone format 等），标记为"格式校验位置不当"
4. 跨文件搜索相同的正则表达式或相同字段名 + 校验方法的组合，标记为"验证逻辑重复"
5. 分析返回值格式一致性：抽样检查各端点的成功响应和错误响应格式
6. 汇总验证问题，生成建议

### 验证模式（按语言/框架）

不同技术栈有不同的验证最佳实践，检测时需识别并匹配：

**Java / Spring Boot**

- Bean Validation（JSR 380）：`@NotNull`、`@NotBlank`、`@Size`、`@Pattern`、`@Email`、`@Min`、`@Max`
- 分组校验：`@Validated(CreateGroup.class)` 区分新增和更新的校验规则
- 自定义 Validator：实现 `ConstraintValidator` 接口
- 全局异常处理：`@ControllerAdvice` + `@ExceptionHandler(MethodArgumentNotValidException.class)`

检测要点：检查是否使用了 Bean Validation 而非手写 if-else 校验；检查 `@Valid` / `@Validated` 是否遗漏。

**Go**

- struct tags：`validate:"required,min=1,max=100"`（配合 go-playground/validator）
- 自定义 middleware 校验
- 手动校验函数

检测要点：检查是否统一使用 validator 库而非散落的 if 判断；检查 struct tag 是否完整。

**Node.js / TypeScript**

- class-validator decorators：`@IsNotEmpty()`、`@IsEmail()`、`@MinLength()`
- Joi schema validation
- Zod schema validation
- NestJS ValidationPipe（全局或局部）

检测要点：检查是否有统一的 validation pipe；检查 DTO class 是否使用了装饰器。

**Python**

- Pydantic validators（v2: `@field_validator`）
- Django forms / serializers（`serializers.CharField(max_length=100)`）
- marshmallow schemas
- 手动 raise ValueError / ValidationError

检测要点：检查是否使用了框架级验证而非手写 if-raise；检查 Pydantic model 的 field 约束是否完整。

**.NET / C#**

- Data Annotations：`[Required]`、`[StringLength]`、`[RegularExpression]`
- FluentValidation：`RuleFor(x => x.Name).NotEmpty().MaximumLength(100)`
- 自定义 ActionFilter

检测要点：检查是否使用了 Data Annotations 或 FluentValidation；检查 `[ApiController]` 是否启用了自动模型验证。

---

## 3-5. 过度抽象检测（反向检查）

### 检测目标

在检测"缺少抽象"的同时，反向检测"过度抽象"——不必要的复杂性。过度抽象同样是代码质量问题，增加阅读成本、维护成本、调试难度。

### 检查项

| 坏味道 | 检测方法 | 建议 |
|--------|----------|------|
| 只有 1 个实现的接口 | 找所有 interface/trait/protocol 定义，统计其 implements/实现类数量 | 无需接口，直接用具体类。例外：DDD 中 Domain 定义接口、Infrastructure 实现 → 合理（依赖倒置） |
| 只被调用 1 次的工具方法 | 在 Utility 层找所有 public 方法，统计每个方法在整个项目中的调用次数 | 内联回唯一调用处。工具方法的价值在于复用，只用一次则没有抽取意义 |
| 层层转发无增值 | 找 Service 方法，检查方法体是否仅 `return repo.xxx()` 或仅调用一个下层方法无额外逻辑 | 跳过中间层，让上层直接调下层（参考 T-03 规则）。除非该 Service 方法是事务边界或有明确的扩展计划 |
| 过深的继承链 (>3 层) | 分析 `extends`/`implements`/`embed` 链的深度，从具体类向上追溯到根基类 | 优先使用组合替代继承。超过 3 层的继承链通常意味着职责划分有问题 |
| 不必要的 Builder/Factory | 找 Builder pattern 或 Factory pattern 的实现，检查是否只有 1 种构建方式 | 只有 1 种构建方式时直接用构造函数或 static factory method，无需完整 Builder |
| 不必要的 Event/Observer | 找事件发布/订阅机制，检查某事件是否只有 1 个 subscriber | 只有 1 个 subscriber 时直接方法调用即可，事件机制增加了调试追踪难度 |
| 空 abstract method 过多的基类 | 统计基类中 abstract method 占比，超过 70% 则基类几乎无共享逻辑 | 基类变成纯接口定义，无共享实现 → 改用接口；或基类 abstract method 过多说明子类差异大于共性，不应强行抽取 |

### 检测流程

1. **单实现接口检测**

   扫描所有 interface/trait/abstract class 定义。对每个定义，在整个项目中搜索 `implements`/`extends`/嵌入引用。统计实现数量。

   ```
   interface PaymentGateway → 实现: StripeGateway, AlipayGateway → 合理（多实现）
   interface UserService    → 实现: UserServiceImpl              → 可疑（单实现）
   ```

2. **单次调用工具方法检测**

   扫描 Utility 层所有 public 方法。对每个方法名，在整个项目中 grep 调用点（排除定义本身）。调用次数 == 1 时标记。

3. **透传方法检测**

   扫描 Business layer 的所有方法。分析方法体：如果方法体只有 1 行且该行是调用 Data layer 的方法并直接返回结果（可能有简单的参数转发），标记为透传。

   ```java
   // 透传示例
   public User getById(Long id) { return userRepo.findById(id).orElse(null); }
   // 非透传（有业务逻辑）
   public User getById(Long id) {
       User user = userRepo.findById(id).orElseThrow(...);
       checkPermission(user);
       return user;
   }
   ```

4. **继承深度检测**

   从每个具体类出发，沿 extends 链向上遍历，记录深度。框架基类（如 Spring 的 `JpaRepository`、Django 的 `ModelViewSet`）不计入深度，只统计项目内自定义的继承层级。

5. **Builder/Factory 必要性检测**

   找所有 Builder class 和 Factory class。检查 Builder 是否只有一种 build 路径（所有字段都在一个 build 方法中设置）。检查 Factory 是否只创建一种类型的对象。

### 何时接口是合理的（即使只有 1 个实现）

不是所有单实现接口都需要消除。以下情况是合理的：

- **DDD 依赖倒置**：Domain 层定义 Repository 接口，Infrastructure 层提供实现。即使只有一个实现，接口的目的是保持 Domain 层的纯净性和可替换性。这是架构约束，不是过度设计。
- **明确的多实现计划**：当前只有 Redis 缓存实现，但路线图中明确计划添加 Memory 缓存和 Memcached 实现。接口为未来扩展做准备。
- **外部依赖隔离**：封装第三方 SDK（支付、短信、OSS）的接口，即使当前只对接一个供应商，接口便于未来切换供应商。
- **测试需要**：需要 mock 的依赖通过接口注入。但注意现代测试框架（Mockito、gomock、jest）可以 mock 具体类，不一定需要接口。评估具体测试框架能力后再判断。

判断规则：如果移除接口后，代码的可维护性和可测试性没有实质性下降，则接口是不必要的。

---

## 输出格式

分析完成后，将结果写入 `.allforai/code-tuner/phase3-abstractions.json`。Schema 如下：

```json
{
  "vertical_abstractions": [
    {
      "id": "ABS-V-001",
      "candidates": ["UserService", "OrderService", "ProductService"],
      "overlap_percentage": 75,
      "overlapping_methods": ["create", "update", "delete", "getById", "page"],
      "diverging_methods": ["UserService.resetPassword", "OrderService.cancelOrder"],
      "suggested_base": "BaseService<E, D, V>",
      "estimated_reduction_lines": 120,
      "suggestion": {
        "pre-launch": "抽取 BaseService<E, D, V> 基类，将 CRUD 模板方法统一。子类只实现 validate/toEntity/toVO。预计减少 120 行重复代码。",
        "maintenance": "标记为重构机会。当下次修改任一 Service 的 CRUD 逻辑时，同步抽取基类。预计减少 120 行重复代码，消除 3 处重复。"
      }
    }
  ],
  "horizontal_abstractions": [
    {
      "id": "ABS-H-001",
      "pattern": "Excel export logic",
      "occurrences": [
        {"file": "UserController.java", "line": 45, "method": "exportUsers"},
        {"file": "OrderController.java", "line": 67, "method": "exportOrders"},
        {"file": "ProductController.java", "line": 32, "method": "exportProducts"}
      ],
      "similarity_percentage": 85,
      "suggested_extraction": "ExcelExportService.export(queryFn, columnDefs, rowMapper)",
      "estimated_reduction_lines": 90,
      "suggestion": {
        "pre-launch": "抽取 ExcelExportService，参数化查询函数、列定义、行映射。3 处调用改为委托调用。",
        "maintenance": "抽取 ExcelExportService，原调用点改为委托。不改变外部行为，风险低。"
      }
    }
  ],
  "api_consolidations": [
    {
      "id": "ABS-A-001",
      "endpoints": [
        "GET /user/page",
        "GET /order/page",
        "GET /product/page"
      ],
      "operation_signature": "parsePageParams → buildQuery → repo.page → wrapResponse",
      "suggested_approach": "generic BaseCrudController<E, D, V> with /page endpoint",
      "blockers": [],
      "suggestion": {
        "pre-launch": "抽取 BaseCrudController<E, D, V>，统一分页端点。子 Controller 继承并指定泛型参数。",
        "maintenance": "创建 BaseCrudController 后逐步迁移，每次迁移一个 Controller 并回归测试。"
      }
    }
  ],
  "validation_issues": [
    {
      "id": "VAL-001",
      "type": "wrong-layer",
      "subtype": "format-in-business",
      "file": "UserService.java",
      "line": 23,
      "code_snippet": "if (dto.getEmail() == null || !dto.getEmail().matches(\"^[\\\\w@.]+$\")) { throw ... }",
      "description": "格式校验（email 正则匹配）出现在 Business 层。应移至 Entry 层使用 @Email 注解。",
      "suggestion": "在 UserDTO 的 email 字段添加 @NotNull @Email 注解，删除 Service 中的手动校验。"
    },
    {
      "id": "VAL-002",
      "type": "duplicate",
      "file": "OrderController.java",
      "line": 15,
      "related_files": ["OrderService.java:34"],
      "description": "orderId 非空校验在 Controller 和 Service 中重复出现。",
      "suggestion": "只在 Controller 层（入口层）保留 @NotNull 校验，Service 层移除。"
    },
    {
      "id": "VAL-003",
      "type": "strict-in-loose-out",
      "file": "ProductController.java",
      "line": 78,
      "description": "入口层严格拒绝不带分页参数的请求，但分页响应在无数据时有时返回 null 有时返回空 []。",
      "suggestion": "统一分页响应格式：无数据时返回 { list: [], total: 0, page: 1 }，不返回 null。"
    },
    {
      "id": "VAL-004",
      "type": "inconsistent-error",
      "file": "multiple",
      "description": "验证失败时，UserController 返回 {code: 400, msg: '...'}, OrderController 返回 {error: '...'}，格式不统一。",
      "suggestion": "实现全局异常处理器（@ControllerAdvice），统一验证异常响应格式为 {code, message, details}。"
    }
  ],
  "over_abstractions": [
    {
      "id": "OVER-001",
      "type": "single-impl-interface",
      "file": "UserService.java",
      "interface_file": "IUserService.java",
      "description": "IUserService 接口只有 UserServiceImpl 一个实现，且不属于 DDD 依赖倒置场景。",
      "suggestion": "删除 IUserService 接口，直接使用 UserService 具体类。其他类注入 UserService 而非 IUserService。"
    },
    {
      "id": "OVER-002",
      "type": "single-use-util",
      "file": "StringUtils.java",
      "method": "formatOrderNumber",
      "call_count": 1,
      "caller": "OrderService.java:56",
      "description": "StringUtils.formatOrderNumber() 只在 OrderService 中调用 1 次。",
      "suggestion": "将 formatOrderNumber 逻辑内联到 OrderService 中。如果未来有复用需求再抽取。"
    },
    {
      "id": "OVER-003",
      "type": "passthrough",
      "file": "ProductService.java",
      "method": "getById",
      "description": "ProductService.getById(id) 仅 return productRepo.findById(id)，无任何业务逻辑。",
      "suggestion": "让 Controller 直接调用 productRepo.findById(id)，跳过 Service 层透传。（参考 T-03 规则）"
    },
    {
      "id": "OVER-004",
      "type": "deep-inheritance",
      "file": "VipOrderService.java",
      "chain": "VipOrderService → OrderService → BaseService → AbstractEntity",
      "depth": 4,
      "description": "继承链深度为 4 层（不含框架类），超过 3 层阈值。",
      "suggestion": "将 VipOrderService 的差异逻辑改为组合模式（注入策略对象），而非继承 OrderService。"
    },
    {
      "id": "OVER-005",
      "type": "unnecessary-builder",
      "file": "UserBuilder.java",
      "description": "UserBuilder 只有 1 种构建方式，所有字段都在一次调用链中设置。",
      "suggestion": "删除 UserBuilder，使用构造函数或 static factory method：User.of(name, email, role)。"
    }
  ]
}
```

### 字段说明

- `id`：唯一标识符。垂直抽象用 `ABS-V-NNN`，横向抽象用 `ABS-H-NNN`，接口合并用 `ABS-A-NNN`，验证问题用 `VAL-NNN`，过度抽象用 `OVER-NNN`
- `type`：问题分类，用于过滤和统计
- `suggestion`：对象形式，包含 `pre-launch` 和 `maintenance` 两种模式下的不同建议
- `estimated_reduction_lines`：预估可减少的代码行数（仅抽象类问题包含此字段）
- 验证问题的 `type` 取值：`wrong-layer`（校验位置不当）、`duplicate`（重复校验）、`strict-in-loose-out`（严进宽出反模式）、`inconsistent-error`（错误响应不统一）
- 过度抽象的 `type` 取值：`single-impl-interface`（单实现接口）、`single-use-util`（单次调用工具方法）、`passthrough`（透传方法）、`deep-inheritance`（过深继承链）、`unnecessary-builder`（不必要的 Builder）

---

## 模式区分

Phase 3 的每条发现都必须提供两种模式下的差异化建议：

### Pre-launch 模式

- 积极建议实施抽象，提供目标代码结构
- 建议重组目录结构（如创建 `base/` 目录存放基类）
- 建议引入新的设计模式（策略模式替代继承链、模板方法模式统一流程）
- 对过度抽象直接建议删除/简化
- 给出预估减少的代码行数和受影响的文件数
- 提供具体的目标代码骨架（伪代码或模板）

### Maintenance 模式

- 仅标记抽象机会和预期收益（减少 N 行代码 / 消除 N 处重复），不建议大规模重写
- 建议增量式重构：下次修改相关代码时顺便实施
- 对过度抽象评估移除风险：涉及多少调用点、是否有外部依赖该接口
- 验证问题按影响范围排序：全局性问题（错误响应不统一）优先于局部问题（某个字段重复校验）
- 不建议修改已稳定运行的代码，除非有明确的 bug 或性能问题

### 优先级排序

无论哪种模式，发现项按以下优先级排序：

1. 验证问题中的 `wrong-layer`（影响正确性）
2. 验证问题中的 `inconsistent-error`（影响 API 一致性）
3. 过度抽象中的 `passthrough`（简单修复，收益明确）
4. 垂直/横向抽象（减少重复代码量最大的优先）
5. 接口合并（通常改动范围大，优先级较低）
6. 过度抽象中的 `single-impl-interface`（移除风险需评估）
7. 验证问题中的 `duplicate`（不影响正确性，只是冗余）

---

## 与其他 Phase 的关系

- **Phase 2 -> Phase 3**：Phase 2 的重复检测结果是 Phase 3 的输入。Phase 2 识别出的重复对，Phase 3 进一步分析是否适合抽象以及抽象方式。
- **Phase 1 -> Phase 3**：Phase 1 的层级违规结果用于辅助验证逻辑分析（已知哪些文件属于哪一层）。Phase 1 中 T-03（简单 CRUD 跳层）的判断结果与 Phase 3 的透传方法检测互相印证。
- **Phase 3 -> Phase 4**：Phase 3 的所有发现项进入 Phase 4 的评分计算（抽象合理度、验证规范度两个维度）和重构任务清单生成。


### 来源文件：`references/phase4-report.md`

# Phase 4: 综合评分与报告生成

> code-tuner 最终阶段：汇总 Phase 1-3 的所有发现，计算五维评分，生成结构化报告和重构任务清单。

---

## 五维评分体系

采用扣分制（deduction-based scoring），每个维度以 100 分为基准，根据发现的问题逐项扣分，最低为 0 分。五个维度按权重加权汇总为总分。

---

### 架构合规度（25%）

衡量项目是否遵循分层架构规范，包括层间依赖方向、职责分配、禁止的跨层调用等。

**评分公式：**

```
arch_score = max(0, 100 - (critical_count * 15) - (warning_count * 5) - (info_count * 1))
```

**扣分规则：**

| 违规级别 | 每次扣分 | 典型示例 |
|---------|---------|---------|
| Critical | -15 | Controller 直接调用 DAO；Entity 出现在 Controller 参数中 |
| Warning | -5 | Service 调用另一个 Service 的 DAO；工具类放在错误的 module 中 |
| Info | -1 | 建议但非强制的命名规范偏差；可选的注解缺失 |

**计算示例：**

假设检测到 2 个 Critical violation、3 个 Warning violation、5 个 Info violation：

```
arch_score = max(0, 100 - (2 * 15) - (3 * 5) - (5 * 1))
           = max(0, 100 - 30 - 15 - 5)
           = 50
```

---

### 代码重复率（25%）

衡量项目中代码重复和冗余的严重程度，涵盖代码片段重复、passthrough method、DTO 字段重叠。

**评分公式：**

```
dup_score = max(0, 100
  - (high_sim_pairs * 8)       // similarity > 90%
  - (mid_sim_pairs * 4)        // similarity 70%-90%
  - (passthrough_count * 3)    // passthrough service methods
  - (dto_overlap_pairs * 3))   // DTO overlap > 70%
```

**扣分规则：**

| 重复类型 | 每次扣分 | 判定条件 |
|---------|---------|---------|
| 高相似度代码对 | -8 | 两个代码片段 similarity > 90% |
| 中相似度代码对 | -4 | 两个代码片段 similarity 70%-90% |
| Passthrough service method | -3 | Service 方法仅透传调用 DAO，无业务逻辑 |
| DTO 字段重叠对 | -3 | 两个 DTO 类字段重叠率 > 70% |

**计算示例：**

假设检测到 3 对高相似度代码、2 对中相似度代码、4 个 passthrough method、2 对 DTO 重叠：

```
dup_score = max(0, 100 - (3 * 8) - (2 * 4) - (4 * 3) - (2 * 3))
          = max(0, 100 - 24 - 8 - 12 - 6)
          = 50
```

---

### 抽象合理度（20%）

衡量抽象层次是否恰当——既不缺失必要的抽象，也不存在过度抽象。

**评分公式：**

```
abs_score = max(0, 100
  - (missing_vertical * 10)     // 缺失纵向抽象
  - (missing_horizontal * 6)    // 缺失横向抽象
  - (api_consolidation * 4)     // API 可合并
  - (over_abstraction * 5))     // 过度抽象
```

**扣分规则：**

| 问题类型 | 每次扣分 | 判定条件 |
|---------|---------|---------|
| 缺失纵向抽象 | -10 | 3 个及以上相似类可抽取公共基类/接口 |
| 缺失横向抽象 | -6 | 同一代码片段在 3 个及以上位置重复出现 |
| API 合并机会 | -4 | 多个相似 API endpoint 可合并为参数化接口 |
| 过度抽象 | -5 each | 不必要的 interface、util class、中间层 |

**计算示例：**

假设检测到 1 个缺失纵向抽象、2 个缺失横向抽象、1 个 API 合并机会、1 个过度抽象：

```
abs_score = max(0, 100 - (1 * 10) - (2 * 6) - (1 * 4) - (1 * 5))
          = max(0, 100 - 10 - 12 - 4 - 5)
          = 69
```

---

### 验证规范度（15%）

衡量数据验证是否在正确的层执行、是否存在重复验证、错误响应是否一致。

**评分公式：**

```
val_score = max(0, 100
  - (wrong_layer * 8)            // 验证在错误层
  - (dup_validation * 5)         // 重复验证逻辑
  - (strict_in_loose_out * 10)   // strict-in-loose-out 反模式
  - (inconsistent_error * 8))    // 错误响应不一致
```

**扣分规则：**

| 问题类型 | 每次扣分 | 判定条件 |
|---------|---------|---------|
| 验证在错误层 | -8 each | 格式校验在 Service 层；业务校验在 Controller 层 |
| 重复验证逻辑 | -5 each | 同一验证逻辑在多处重复实现 |
| Strict-in-loose-out 反模式 | -10 each | 入参严格但出参宽松，或反之 |
| 错误响应不一致 | -8 | 同类验证失败返回不同格式的错误信息 |

**计算示例：**

假设检测到 2 个验证在错误层、1 个重复验证、0 个 strict-in-loose-out、1 个错误响应不一致：

```
val_score = max(0, 100 - (2 * 8) - (1 * 5) - (0 * 10) - (1 * 8))
          = max(0, 100 - 16 - 5 - 0 - 8)
          = 71
```

---

### 数据模型规范度（15%）

衡量 Entity、DTO、VO 等数据模型的设计规范程度。

**评分公式：**

```
model_score = max(0, 100
  - (missing_base_fields * 10)   // 公共字段未抽取（仅扣一次）
  - (dto_vo_overlap * 5)         // DTO/VO 字段重叠
  - (entity_exposed * 5)         // Entity 暴露在 Entry 层
  - (missing_relation * 3))      // 缺失关联关系
```

**扣分规则：**

| 问题类型 | 每次扣分 | 判定条件 |
|---------|---------|---------|
| 公共字段未抽取到基类 | -10（仅一次） | `createTime`、`updateTime` 等公共字段未提取到 `BaseEntity` |
| DTO/VO 字段重叠 | -5 per pair | 两个 DTO 或 VO 类字段重叠率 > 70% |
| Entity 暴露在 Entry 层 | -5 each | Controller 方法直接接收或返回 Entity |
| 缺失关联关系 | -3 each | 外键字段存在但未建立 JPA/MyBatis 关联映射 |

**注意：** `missing_base_fields` 是布尔性质的扣分——不论有多少个 Entity 缺失公共字段，只扣一次 10 分。

**计算示例：**

假设公共字段未抽取（扣 1 次）、2 对 DTO/VO 重叠、1 个 Entity 暴露、2 个缺失关联：

```
model_score = max(0, 100 - (1 * 10) - (2 * 5) - (1 * 5) - (2 * 3))
            = max(0, 100 - 10 - 10 - 5 - 6)
            = 69
```

---

### 总分计算

将五个维度按权重加权求和：

```
total = arch_score  * 0.25
      + dup_score   * 0.25
      + abs_score   * 0.20
      + val_score   * 0.15
      + model_score * 0.15
```

以上述示例数据计算：

```
total = 50 * 0.25 + 50 * 0.25 + 69 * 0.20 + 71 * 0.15 + 69 * 0.15
      = 12.5 + 12.5 + 13.8 + 10.65 + 10.35
      = 59.8
```

该项目评分为 59.8，等级为 D。

---

## 分数解读

| 分数范围 | 等级 | 含义 |
|---------|------|------|
| 90-100 | A 优秀 | 架构清晰，极少重复，抽象合理 |
| 75-89 | B 良好 | 少量问题，值得优化但不紧急 |
| 60-74 | C 需要关注 | 明显的结构问题，应尽快优化 |
| 40-59 | D 较差 | 大量重复和违规，需要系统性重构 |
| 0-39 | F 严重 | 架构混乱，建议重新规划 |

对于等级的使用建议：

- **A / B 等级**：维持现状，在日常开发中保持规范即可。运行 `code-tuner` 做定期检查。
- **C 等级**：安排专项优化迭代，按 `tuner-tasks.json` 中的任务清单逐步修复。
- **D / F 等级**：停止新功能开发，优先解决结构性问题。建议按 `pre-launch` 模式排序任务，从影响最大的问题开始。

---

## 报告模板 (tuner-report.md)

生成的 `tuner-report.md` 包含以下完整章节：

### 第一节：摘要

展示总分、各维度分数、项目基本信息。

```markdown
# Code Tuner 分析报告

**生成时间：** 2026-02-17 10:30:00
**项目路径：** /path/to/project
**分析模式：** pre-launch

## 摘要

| 指标 | 分数 | 等级 |
|------|------|------|
| **总分** | **59.8** | **D 较差** |
| 架构合规度 | 50 / 100 | |
| 代码重复率 | 50 / 100 | |
| 抽象合理度 | 69 / 100 | |
| 验证规范度 | 71 / 100 | |
| 数据模型规范度 | 69 / 100 | |

**项目概况：**
- 扫描文件数：87
- 扫描代码行数：12,450
- 发现问题总数：23（Critical: 2, Warning: 8, Info: 13）
- 预估可消除重复代码行：320 行
```

### 第二节：问题列表

按严重程度排序（Critical → Warning → Info），每条问题包含完整上下文。

```markdown
## 问题列表

### Critical

#### [T-01] Controller 直接调用 DAO
- **文件：** `src/main/java/com/example/controller/OrderController.java:34`
- **描述：** `OrderController` 直接注入并调用 `OrderMapper`，跳过 Service 层
- **修复建议：**
  - **pre-launch：** 将 DAO 调用移至 `OrderService`，Controller 改为调用 Service 方法
  - **maintenance：** 新建 `OrderService.findById()` 方法封装此调用，Controller 切换到新方法

#### [G-03] 跨模块 Service 直接调用
- **文件：** `src/main/java/com/example/order/service/OrderService.java:78`
- **描述：** `OrderService` 直接调用 `UserMapper`，跨越模块边界直接访问 DAO
- **修复建议：**
  - **pre-launch：** 通过 `UserService` 暴露查询接口，`OrderService` 改为调用 `UserService`
  - **maintenance：** 同 pre-launch，但添加 Facade 层做防腐

### Warning

#### [DUP-001] 高相似度代码片段
- **文件：** `src/.../UserService.java:23-45` ↔ `src/.../OrderService.java:67-89`
- **描述：** 两段分页查询逻辑相似度 93%，仅查询对象不同
- **修复建议：**
  - **pre-launch：** 抽取通用分页查询方法到 `BaseService`
  - **maintenance：** 新建 `PageQueryHelper` 工具类，逐步替换

### Info
...
```

### 第三节：重复热力图

以 Module x Module 矩阵展示模块间的重复代码对数量。

```markdown
## 重复热力图

模块间重复代码对数量：

```
            | user | order | product | payment |
  user      |  -   |   3   |    1    |    0    |
  order     |  3   |   -   |    2    |    1    |
  product   |  1   |   2   |   -     |    0    |
  payment   |  0   |   1   |    0    |    -    |
```

**热点分析：**
- `user` ↔ `order` 模块间重复最多（3 对），建议优先处理
- `order` ↔ `product` 存在 2 对重复，多为分页和查询逻辑
```

### 第四节：各 Phase 详细发现

按分析阶段组织，展示每个 Phase 的完整发现。

```markdown
## 各 Phase 详细发现

### Phase 1: 架构合规检查

扫描规则 16 条，触发 8 条：
- T-01 (Critical): 1 处 — OrderController 直接调用 DAO
- G-03 (Warning): 2 处 — 跨模块 Service 调用
- ...

### Phase 2: 重复与冗余检测

代码片段重复：5 对（高相似 3 对，中相似 2 对）
Passthrough method：4 个
DTO 重叠：2 对
预估可消除行数：320 行

详细列表：
1. `UserService.java:23-45` ↔ `OrderService.java:67-89` — similarity 93%
2. ...

### Phase 3: 抽象与验证分析

缺失抽象：
- 纵向：`UserService`, `OrderService`, `ProductService` 可抽取 `BaseCrudService`
- 横向：分页查询片段在 4 处重复

验证问题：
- `OrderService.java:45` 手机号格式校验应在 Controller 层
- ...
```

### 第五节：趋势对比

如果 `.allforai/code-tuner/` 目录下存在上次报告，展示变化趋势。

```markdown
## 趋势对比

**对比基准：** 2026-02-10 报告

| 指标 | 上次 | 本次 | 变化 |
|------|------|------|------|
| 总分 | 52.3 | 59.8 | +7.5 ↑ |
| 架构合规度 | 40 | 50 | +10 ↑ |
| 代码重复率 | 45 | 50 | +5 ↑ |
| 抽象合理度 | 65 | 69 | +4 ↑ |
| 验证规范度 | 68 | 71 | +3 ↑ |
| 数据模型规范度 | 65 | 69 | +4 ↑ |

**新增问题（2）：**
- [DUP-005] `PaymentService.java:30-52` ↔ `RefundService.java:10-32`
- [T-08] `ReportController` 直接访问 `OrderMapper`

**已修复问题（5）：**
- ~~[T-02] UserController 包含业务逻辑~~ — 已移至 UserService
- ~~[DUP-002] 用户查询逻辑重复~~ — 已抽取到 BaseService
- ...
```

若无上次报告，显示 `> 首次分析，无历史对比数据。` 并跳过此节。

---

## 重构任务清单 (tuner-tasks.json)

生成结构化 JSON 任务清单，供下游工具或开发者直接消费。

### 完整 Schema

```json
{
  "generated_at": "2026-02-17T10:30:00Z",
  "lifecycle": "pre-launch|maintenance",
  "total_score": 67.75,
  "dimension_scores": {
    "architecture": 50,
    "duplication": 50,
    "abstraction": 69,
    "validation": 71,
    "data_model": 69
  },
  "tasks": [
    {
      "id": "TASK-001",
      "phase": "phase1",
      "rule": "T-03",
      "severity": "warning",
      "title": "手机号格式校验应从 OrderService 移到 OrderController",
      "description": "OrderService.java:45 包含手机号正则校验，这是格式验证，应在入口层完成",
      "files": [
        "src/main/java/com/example/order/service/OrderService.java:45",
        "src/main/java/com/example/order/controller/OrderController.java"
      ],
      "effort": "low",
      "estimated_lines_reduced": 5,
      "suggestion": {
        "pre-launch": "直接将校验逻辑移到 OrderController，在 Service 中删除",
        "maintenance": "在 OrderController 中添加校验，Service 中的暂时保留，标记 @Deprecated"
      }
    },
    {
      "id": "TASK-002",
      "phase": "phase2",
      "rule": "DUP-001",
      "severity": "warning",
      "title": "UserService 和 OrderService 分页查询逻辑重复",
      "description": "两处分页查询逻辑相似度 93%，仅查询实体不同，可抽取泛型基类",
      "files": [
        "src/main/java/com/example/user/service/UserService.java:23-45",
        "src/main/java/com/example/order/service/OrderService.java:67-89"
      ],
      "effort": "medium",
      "estimated_lines_reduced": 40,
      "suggestion": {
        "pre-launch": "创建 BaseCrudService<T> 泛型基类，将分页逻辑下沉到基类",
        "maintenance": "新建 PageQueryHelper 工具类封装分页逻辑，逐步替换各 Service 中的实现"
      }
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 任务唯一标识，格式 `TASK-NNN`，按排序后的顺序编号 |
| `phase` | string | 来源阶段：`phase1`、`phase2`、`phase3` |
| `rule` | string | 触发的规则 ID，如 `T-01`、`G-03`、`DUP-001`、`ABS-V01` |
| `severity` | string | `critical` / `warning` / `info` |
| `title` | string | 一句话描述任务内容，使用中文 |
| `description` | string | 详细说明问题位置和原因 |
| `files` | string[] | 涉及的文件路径，含行号 |
| `effort` | string | 预估工作量：`low`（< 30 min）、`medium`（30 min - 2 h）、`high`（> 2 h） |
| `estimated_lines_reduced` | number | 预估可消除的重复/冗余代码行数 |
| `suggestion` | object | 按 lifecycle 分别给出修复建议 |

---

## 任务排序逻辑

根据 `lifecycle` 参数采用不同的排序策略。

### Pre-launch 模式：按质量影响降序

上线前追求最大质量改善，优先修复对代码质量影响最大的问题。

排序优先级（从高到低）：

1. **Critical architecture violations**（结构性问题）
   - 层间违规调用、禁止的依赖方向等
   - 不修复会导致后续开发持续产生问题
2. **High duplication**（高重复度问题）
   - similarity > 90% 的代码对
   - 消除后可大量减少代码行数
3. **Missing abstractions**（缺失抽象）
   - 纵向/横向抽象缺失
   - 修复后可系统性消除重复模式
4. **Validation issues**（验证问题）
   - 验证层错位、重复验证
5. **Data model issues**（数据模型问题）
   - DTO/VO 重叠、Entity 暴露等

### Maintenance 模式：按变更风险升序

维护期追求最小变更风险，优先做低风险的改善。

排序优先级（从低风险到高风险）：

1. **Low-risk utility extraction**（低风险工具抽取）
   - 新建文件，不修改已有代码
   - 例如：创建 `PageQueryHelper` 工具类
2. **Validation placement fix**（验证位置修正）
   - 在文件间移动代码，影响范围可控
   - 例如：将格式校验从 Service 移到 Controller
3. **DTO consolidation**（DTO 合并）
   - 合并高重叠的 DTO/VO 类
   - 需要修改引用方，但类型安全保障了正确性
4. **Service passthrough removal**（Passthrough 方法消除）
   - 删除透传方法，调用方需要调整
   - 中等风险，需要确认所有调用链路
5. **Architecture restructuring**（架构重组）
   - 跨模块调用修正、层级调整
   - 最高风险，涉及多文件多模块改动，排在最后

### 同一优先级内的子排序

在同一优先级内，按以下规则子排序：

- `estimated_lines_reduced` 降序（优先处理收益大的）
- `effort` 升序（同等收益下优先处理工作量小的）
- `files` 数组长度升序（涉及文件少的优先）

---

## 报告输出规范

### 文件输出

1. 将 `tuner-report.md` 保存到 `.allforai/code-tuner/tuner-report.md`
2. 将 `tuner-tasks.json` 保存到 `.allforai/code-tuner/tuner-tasks.json`
3. 如果 `.allforai/code-tuner/` 目录不存在，自动创建
4. 如果已存在上次报告，将旧报告重命名为 `tuner-report-{timestamp}.md` 作为历史归档

### 会话内摘要展示

保存文件后，在会话中直接展示摘要信息。禁止仅输出"报告已保存"而不展示内容。

摘要必须包含以下内容：

1. **总分和等级**：明确显示数字和等级
2. **各维度分数**：列出五个维度的具体分数
3. **关键问题摘要**：至少列出所有 Critical 问题和前 3 个 Warning 问题，包含具体文件路径
4. **重构建议**：根据当前 lifecycle 模式给出排在前三的任务
5. **文件位置**：告知报告和任务清单的保存路径

示例会话输出格式：

```
## Code Tuner 分析完成

**总分：59.8 / 100（D 较差）**

| 维度 | 分数 |
|------|------|
| 架构合规度 | 50 |
| 代码重复率 | 50 |
| 抽象合理度 | 69 |
| 验证规范度 | 71 |
| 数据模型规范度 | 69 |

### 关键问题

- **[Critical] T-01** `OrderController.java:34` — Controller 直接调用 DAO
- **[Critical] G-03** `OrderService.java:78` — 跨模块直接访问 DAO
- **[Warning] DUP-001** `UserService.java:23` ↔ `OrderService.java:67` — 分页逻辑重复（93%）
- **[Warning] T-03** `OrderService.java:45` — 格式校验在 Service 层
- **[Warning] DUP-003** `UserDTO.java` ↔ `UserVO.java` — 字段重叠 85%

### 优先处理任务（pre-launch 模式）

1. TASK-001: 修复 OrderController 直接调用 DAO（effort: medium）
2. TASK-002: 抽取 UserService/OrderService 公共分页逻辑（effort: medium）
3. TASK-003: 将手机号校验从 OrderService 移到 Controller（effort: low）

详细报告：`.allforai/code-tuner/tuner-report.md`
任务清单：`.allforai/code-tuner/tuner-tasks.json`
```

### 趋势对比展示

若 `.allforai/code-tuner/` 中存在上次的 `tuner-report.md`，在保存新报告前先解析旧报告的分数和问题列表，进行对比。

对比逻辑：

1. 提取旧报告中的总分和各维度分数
2. 按 Rule ID + 文件路径匹配问题，找出新增和已修复的问题
3. 在新报告的"趋势对比"章节和会话摘要中都展示变化

若不存在旧报告，在报告中注明"首次分析"并跳过趋势对比章节。
