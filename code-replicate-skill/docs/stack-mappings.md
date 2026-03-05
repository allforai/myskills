# 跨栈映射参考 (Stack Mappings Reference)

> 本文档列举常见跨栈映射场景，分三类：直接等价（自动映射）、多方案可选（用户决策）、架构性差异（需解释）。

---

## 路由层

| 源 | 目标 | 类型 | 映射 |
|----|------|------|------|
| Express `router.get('/path', handler)` | Go Gin | 直接等价 | `r.GET("/path", handler)` |
| Express `router.post()` | Go Gin | 直接等价 | `r.POST()` |
| Express `router.use()` 中间件 | Go Gin | 直接等价 | `r.Use()` 中间件 |
| FastAPI `@app.get("/path")` | Go Gin | 直接等价 | `r.GET("/path", handler)` |
| Django URLconf | NestJS `@Controller` | 多方案 | 结构差异较大，见下 |
| Laravel Route::get() | NestJS `@Get()` | 直接等价 | 装饰器路由 |
| Spring `@RequestMapping` | NestJS `@Controller` | 直接等价 | 均为装饰器路由 |

---

## 异步任务 / 队列

| 源 | 目标 | 类型 | 选项 |
|----|------|------|------|
| Python Celery | Go | **多方案可选** | A: goroutine + channel（无依赖，轻量）<br>B: [asynq](https://github.com/hibiken/asynq)（Redis 后端，生产可用）<br>C: [machinery](https://github.com/RichardKnop/machinery)（多后端，功能丰富） |
| Python Celery | Node.js | **多方案可选** | A: [BullMQ](https://bullmq.io/)（推荐，Redis 后端）<br>B: [Bee-Queue](https://github.com/bee-queue/bee-queue)（轻量）<br>C: pg-boss（PostgreSQL 后端） |
| Node.js Bull | Go | **多方案可选** | A: asynq（同为 Redis 后端，最接近）<br>B: goroutine pool |
| Java Spring @Async | Node.js | 直接等价 | async/await + Promise |
| Laravel Queue | Node.js BullMQ | 直接等价 | 均为 Redis 队列 |

---

## 认证 / 会话

| 源 | 目标 | 类型 | 选项 |
|----|------|------|------|
| PHP Session | 现代后端 | **多方案可选** | A: JWT（无状态，推荐分布式）<br>B: Redis Session（有状态，行为最接近）<br>C: Cookie-based Session（单机）|
| Express session-cookie | Go | **多方案可选** | A: JWT（推荐）<br>B: Redis + gorilla/sessions |
| Django Session | Go | **多方案可选** | A: JWT<br>B: Redis Session |
| JWT (any) | JWT (any) | 直接等价 | 只需换签名库 |
| Passport.js OAuth | Go oauth2 | 直接等价 | golang.org/x/oauth2 |

---

## ORM / 数据访问

| 源 | 目标 | 类型 | 选项 |
|----|------|------|------|
| Sequelize (Node.js) | GORM (Go) | 直接等价 | 模型定义方式不同，语义等价 |
| TypeORM | GORM | 直接等价 | 均支持 Active Record + Data Mapper |
| SQLAlchemy | GORM | 直接等价 | 语法不同，功能对齐 |
| Django ORM | TypeORM | 直接等价 | 迁移系统均有 |
| Eloquent (Laravel) | Prisma | 直接等价 | 均为 Active Record 风格 |
| Hibernate (Java) | TypeORM | 直接等价 | 均为 JPA 风格注解 |
| **ORM 关联（一对多）** | 任意目标 | **多方案可选** | A: ORM 关联（代码清晰）<br>B: 手写 JOIN（性能可控）<br>C: DataLoader（N+1 问题场景）|

---

## 实时通信

| 源 | 目标 | 类型 | 选项 |
|----|------|------|------|
| Socket.io | Go WebSocket | **多方案可选** | A: gorilla/websocket（标准库风格）<br>B: [centrifugo](https://github.com/centrifugal/centrifugo)（生产级，有重连/房间）|
| Socket.io | Go SSE | **架构性差异** | SSE 单向，需重新评估是否满足需求 |
| WebSocket (any) | SSE | **架构性差异** | 双向 → 单向，需确认客户端是否依赖双向 |
| SSE | WebSocket | **架构性差异** | 单向 → 双向，客户端需修改 |

---

## 文件存储

| 源 | 目标 | 类型 | 选项 |
|----|------|------|------|
| 本地文件系统 | 云存储 | **多方案可选** | A: AWS S3<br>B: Cloudflare R2（兼容 S3 API）<br>C: 阿里云 OSS |
| AWS S3 | 阿里云 OSS | 直接等价 | SDK 不同，API 语义相同 |
| GridFS (MongoDB) | 对象存储 | **架构性差异** | 块存储 vs 对象存储，需评估文件大小和访问模式 |
| multer (Node.js) | Go multipart | 直接等价 | 均为标准 multipart 处理 |

---

## 缓存

| 源 | 目标 | 类型 | 映射 |
|----|------|------|------|
| Redis (any SDK) | Redis (Go) | 直接等价 | go-redis/redis |
| Memcached | Redis | 直接等价（语义） | 键值语义相同，无 TTL 语义差异 |
| 内存缓存 (node-cache 等) | Go sync.Map | 直接等价 | 单进程缓存 |
| 内存缓存 | Redis | **架构性差异** | 单进程 → 分布式，需考虑缓存失效策略 |

---

## 架构性差异详解

### Django → NestJS

Django 是"大而全"的单体框架（ORM + 模板 + Admin + 路由集成），NestJS 是模块化的 Node.js 框架。

**主要映射关系**：
- Django App → NestJS Module
- Django View → NestJS Controller
- Django Model → TypeORM Entity
- Django Serializer → NestJS DTO + class-validator
- Django Admin → 需要独立实现（推荐 AdminJS 或自建）
- Django Signals → NestJS Events (EventEmitter2)
- Django Middleware → NestJS Middleware / Interceptor / Guard

**用户决策点**：Django Admin 功能如何在 NestJS 中替代？

---

### PHP Laravel → Go Gin

PHP 是解释型语言，Go 是编译型语言，并发模型完全不同。

**主要映射关系**：
- Laravel Route → Gin Router
- Laravel Controller → Gin Handler Function
- Eloquent Model → GORM Model
- Laravel Middleware → Gin Middleware
- Laravel Service Provider → Go package init / wire
- Laravel Artisan Command → cobra CLI
- Laravel Queue → asynq（Redis）
- Laravel Scheduler → cron / robfig/cron

**架构性差异**：
- PHP 每请求独立进程 → Go goroutine（需处理共享状态）
- Laravel Facade（全局单例）→ Go 依赖注入（需显式传递）
- PHP 动态类型 → Go 静态类型（需定义所有 struct）

---

### 单体应用 → 微服务

**架构性差异**（必须用户确认）：

| 问题 | 选项 |
|------|------|
| 服务间通信 | REST / gRPC / Message Queue |
| 分布式事务 | Saga Pattern / 两阶段提交 |
| 服务发现 | Consul / Kubernetes / 硬编码 |
| 配置管理 | 环境变量 / Vault / Consul KV |
| 日志聚合 | ELK / Loki / CloudWatch |

---

## 使用说明

Phase 5 跨栈映射时，从本文档查询对应映射类型：
- **直接等价** → 自动映射，写入 `stack-mapping.json` 的 `auto_mapped` 数组
- **多方案可选** → 触发 `AskUserQuestion`，用户选择后写入 `user_decisions` 数组
- **架构性差异** → 详细解释后 `AskUserQuestion` 确认，写入 `arch_decisions` 数组

---

## 框架内置能力速查表

> Phase 5 步骤 5a-0 使用。根据 `target_stack` 查询此表，识别源码中手写实现可被目标框架内置能力替代的部分。

### 参数校验 (Validation)

| 框架 | 内置能力 | 说明 |
|------|---------|------|
| NestJS | class-validator + ValidationPipe | 装饰器声明式校验，自动 400 响应 |
| Go Gin | binding tags (`binding:"required"`) | struct tag 校验，ShouldBind 自动触发 |
| Django | Forms / Serializer validation | ModelForm 自动校验，DRF Serializer |
| Laravel | FormRequest + Validator | 声明式规则，自动 422 响应 |
| Spring Boot | @Valid + Hibernate Validator | JSR-380 注解校验 |
| FastAPI | Pydantic models | 类型+约束自动校验 |
| Express | — | 无内置，需 joi / zod / express-validator |

### 认证授权 (Auth)

| 框架 | 内置能力 | 说明 |
|------|---------|------|
| NestJS | Guards + Passport + CASL | @UseGuards 装饰器，角色/权限控制 |
| Go Gin | — | 无内置，需 casbin / jwt-go 中间件 |
| Django | django.contrib.auth + DRF permissions | 内置用户模型、权限系统、认证后端 |
| Laravel | Gates + Policies + Spatie Permission | 声明式授权，内置 Auth scaffolding |
| Spring Boot | Spring Security | 过滤器链、角色、方法级安全注解 |
| FastAPI | Depends + OAuth2PasswordBearer | 依赖注入式认证 |

### 分页 (Pagination)

| 框架 | 内置能力 | 说明 |
|------|---------|------|
| NestJS | @nestjs/common 无内置 / nestjs-paginate | 社区包，需配合 TypeORM/Prisma |
| Go Gin | — | 无内置，需手写或用 gorm scopes |
| Django | Paginator + DRF PageNumberPagination | 内置完整分页（偏移/游标） |
| Laravel | ->paginate() | Eloquent 内置，自动生成分页元数据 |
| Spring Boot | Pageable + Page<T> | Spring Data 内置分页参数绑定 |
| FastAPI | — | 无内置，需 fastapi-pagination |

### 缓存 (Cache)

| 框架 | 内置能力 | 说明 |
|------|---------|------|
| NestJS | @nestjs/cache-manager + CacheInterceptor | 装饰器 @CacheKey/@CacheTTL |
| Go Gin | — | 无内置，需 go-cache / redis |
| Django | django.core.cache | 多后端（memcached/redis/file/db） |
| Laravel | Cache facade + cache() helper | 多驱动，支持 tags |
| Spring Boot | @Cacheable / @CacheEvict | 注解式缓存，多后端 |

### 日志 (Logging)

| 框架 | 内置能力 | 说明 |
|------|---------|------|
| NestJS | @nestjs/common Logger | 内置 Logger 类，支持 scope 注入 |
| Go Gin | gin.Logger() 中间件 | 内置请求日志中间件 |
| Django | django.utils.log + logging config | 内置 logging 配置集成 |
| Laravel | Log facade (Monolog) | 多 channel（stack/daily/slack） |
| Spring Boot | spring-boot-starter-logging | Logback 默认集成 |

### 错误处理 (Error Handling)

| 框架 | 内置能力 | 说明 |
|------|---------|------|
| NestJS | ExceptionFilter + HttpException | @Catch 装饰器，全局/控制器级过滤 |
| Go Gin | gin.Recovery() + CustomRecovery | panic 恢复中间件 |
| Django | Middleware exception handling | 内置 handler400/403/404/500 |
| Laravel | App\Exceptions\Handler | 集中异常处理，render/report |
| Spring Boot | @ControllerAdvice + @ExceptionHandler | 全局异常处理注解 |
| Express | error middleware (err, req, res, next) | 约定式错误中间件 |

### 文件上传 (File Upload)

| 框架 | 内置能力 | 说明 |
|------|---------|------|
| NestJS | @UseInterceptors(FileInterceptor) + Multer | 装饰器集成 Multer |
| Go Gin | c.FormFile() / c.MultipartForm() | 内置 multipart 解析 |
| Django | request.FILES + FileField | 内置文件处理 |
| Laravel | $request->file() + Storage facade | 内置文件存储抽象 |
| Spring Boot | @RequestParam MultipartFile | 内置 multipart 解析 |

### 定时任务 (Scheduling)

| 框架 | 内置能力 | 说明 |
|------|---------|------|
| NestJS | @nestjs/schedule + @Cron() | 装饰器声明式 cron |
| Go Gin | — | 无内置，需 robfig/cron |
| Django | — | 无内置，需 django-celery-beat / APScheduler |
| Laravel | Console\Kernel schedule() | 内置任务调度器 |
| Spring Boot | @Scheduled | 注解式定时任务 |

### CORS

| 框架 | 内置能力 | 说明 |
|------|---------|------|
| NestJS | app.enableCors() | 一行配置 |
| Go Gin | — | 需 gin-contrib/cors |
| Django | — | 需 django-cors-headers |
| Laravel | config/cors.php | 内置 CORS 配置 |
| Spring Boot | @CrossOrigin / WebMvcConfigurer | 注解或全局配置 |
| Express | — | 需 cors 包 |

### 序列化 (Serialization)

| 框架 | 内置能力 | 说明 |
|------|---------|------|
| NestJS | class-transformer + @Exclude/@Expose | 装饰器控制序列化字段 |
| Go Gin | struct json tags | `json:"name,omitempty"` |
| Django | DRF Serializers | 声明式序列化 + 嵌套支持 |
| Laravel | API Resources + JsonResource | 声明式 API 资源转换 |
| Spring Boot | Jackson @JsonIgnore/@JsonProperty | 注解控制 JSON 序列化 |

### 使用方式

5a-0 步骤中：
1. 根据 `target_stack` 找到对应框架行，收集所有「有内置能力」的分类
2. 扫描源码产物，识别源码中手写实现了这些分类功能的部分
3. 匹配项标记为 `framework_builtin: true`，推荐使用内置方案
4. 标注「—」的分类表示该框架无内置能力，源码手写实现需保留或选择第三方库
