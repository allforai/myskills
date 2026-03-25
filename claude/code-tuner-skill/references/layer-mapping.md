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
