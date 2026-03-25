# Cross-Stack Mapping Reference

> Equivalence tables for Phase 2d stack mapping. Three categories: direct equivalence (auto-map), multi-option (user decision), architectural difference (needs explanation).

---

## Routing Layer

| Source | Target | Type | Mapping |
|--------|--------|------|---------|
| Express `router.get()` | Go Gin `r.GET()` | Direct | Route handler syntax |
| Express `router.use()` | Go Gin `r.Use()` | Direct | Middleware registration |
| FastAPI `@app.get()` | Go Gin `r.GET()` | Direct | Decorator → function call |
| Django URLconf | NestJS `@Controller` | Multi-option | URL patterns → decorator routes |
| Laravel `Route::get()` | NestJS `@Get()` | Direct | Both decorator-based |
| Spring `@RequestMapping` | NestJS `@Controller` | Direct | Both annotation/decorator routing |

---

## Async Tasks / Queues

| Source | Target | Type | Options |
|--------|--------|------|---------|
| Python Celery | Go | **Multi-option** | A: goroutine + channel (lightweight, no deps) / B: asynq (Redis, production-ready) / C: machinery (multi-backend) |
| Python Celery | Node.js | **Multi-option** | A: BullMQ (recommended, Redis) / B: Bee-Queue (lightweight) / C: pg-boss (PostgreSQL) |
| Node.js Bull | Go | **Multi-option** | A: asynq (same Redis backend) / B: goroutine pool |
| Java Spring @Async | Node.js | Direct | async/await + Promise |
| Laravel Queue | Node.js BullMQ | Direct | Both Redis-backed queues |

---

## Authentication / Sessions

| Source | Target | Type | Options |
|--------|--------|------|---------|
| PHP Session | Modern backend | **Multi-option** | A: JWT (stateless, recommended for distributed) / B: Redis Session (stateful, closest behavior) / C: Cookie Session (single machine) |
| Express session-cookie | Go | **Multi-option** | A: JWT (recommended) / B: Redis + gorilla/sessions |
| Django Session | Go | **Multi-option** | A: JWT / B: Redis Session |
| JWT (any) | JWT (any) | Direct | Only swap signing library |
| Passport.js OAuth | Go oauth2 | Direct | golang.org/x/oauth2 |

---

## ORM / Data Access

| Source | Target | Type | Mapping |
|--------|--------|------|---------|
| Sequelize (Node.js) | GORM (Go) | Direct | Model definition differs, semantics equivalent |
| TypeORM | GORM | Direct | Both support Active Record + Data Mapper |
| SQLAlchemy | GORM | Direct | Syntax differs, features align |
| Django ORM | TypeORM | Direct | Both have migration systems |
| Eloquent (Laravel) | Prisma | Direct | Both Active Record style |
| Hibernate (Java) | TypeORM | Direct | Both JPA-style annotations |
| ORM associations (1:N) | Any target | **Multi-option** | A: ORM associations (clean code) / B: Hand-written JOIN (performance control) / C: DataLoader (N+1 scenarios) |

---

## Real-Time Communication

| Source | Target | Type | Notes |
|--------|--------|------|-------|
| Socket.io | Go WebSocket | **Multi-option** | A: gorilla/websocket (stdlib style) / B: centrifugo (production-grade, rooms + reconnect) |
| Socket.io | SSE | **Arch difference** | SSE is unidirectional — verify client does not require bidirectional |
| WebSocket (any) | SSE | **Arch difference** | Bidirectional to unidirectional — confirm client compatibility |
| SSE | WebSocket | **Arch difference** | Unidirectional to bidirectional — client modifications required |

---

## File Storage

| Source | Target | Type | Options |
|--------|--------|------|---------|
| Local filesystem | Cloud storage | **Multi-option** | A: AWS S3 / B: Cloudflare R2 (S3-compatible) / C: Alibaba OSS |
| AWS S3 | Alibaba OSS | Direct | Different SDK, same API semantics |
| GridFS (MongoDB) | Object storage | **Arch difference** | Chunk storage vs object storage — evaluate file size and access patterns |
| multer (Node.js) | Go multipart | Direct | Both standard multipart handling |

---

## Caching

| Source | Target | Type | Mapping |
|--------|--------|------|---------|
| Redis (any SDK) | Redis (Go) | Direct | go-redis/redis |
| Memcached | Redis | Direct | Key-value semantics equivalent |
| In-memory cache (node-cache) | Go sync.Map | Direct | Single-process cache |
| In-memory cache | Redis | **Arch difference** | Single-process to distributed — consider cache invalidation strategy |

---

## Framework Built-In Capabilities

> Used in Phase 2d to identify source hand-written code replaceable by target framework built-ins.

### Validation

| Framework | Built-in | Notes |
|-----------|----------|-------|
| NestJS | class-validator + ValidationPipe | Decorator-based, auto 400 response |
| Go Gin | binding tags (`binding:"required"`) | Struct tag validation via ShouldBind |
| Django | Forms / DRF Serializer | Auto validation on ModelForm / Serializer |
| Laravel | FormRequest + Validator | Declarative rules, auto 422 response |
| Spring Boot | @Valid + Hibernate Validator | JSR-380 annotation validation |
| FastAPI | Pydantic models | Type + constraint auto-validation |
| Express | — | No built-in; use joi / zod / express-validator |

### Auth

| Framework | Built-in | Notes |
|-----------|----------|-------|
| NestJS | Guards + Passport + CASL | @UseGuards decorator, role/permission control |
| Go Gin | — | No built-in; use casbin / jwt-go middleware |
| Django | django.contrib.auth + DRF permissions | Built-in user model, permission system |
| Laravel | Gates + Policies + Spatie Permission | Declarative auth, built-in scaffolding |
| Spring Boot | Spring Security | Filter chain, roles, method-level annotations |
| FastAPI | Depends + OAuth2PasswordBearer | DI-based authentication |

### Pagination

| Framework | Built-in | Notes |
|-----------|----------|-------|
| NestJS | — | Community package (nestjs-paginate) |
| Go Gin | — | No built-in; hand-write or use gorm scopes |
| Django | Paginator + DRF PageNumberPagination | Built-in offset + cursor pagination |
| Laravel | ->paginate() | Eloquent built-in, auto pagination metadata |
| Spring Boot | Pageable + Page<T> | Spring Data built-in parameter binding |
| FastAPI | — | No built-in; use fastapi-pagination |

### Error Handling

| Framework | Built-in | Notes |
|-----------|----------|-------|
| NestJS | ExceptionFilter + HttpException | @Catch decorator, global/controller scope |
| Go Gin | gin.Recovery() + CustomRecovery | Panic recovery middleware |
| Django | Middleware exception handling | Built-in handler400/403/404/500 |
| Laravel | App\Exceptions\Handler | Centralized exception handling |
| Spring Boot | @ControllerAdvice + @ExceptionHandler | Global exception annotations |
| Express | error middleware (err, req, res, next) | Convention-based error middleware |

### Other Capabilities

| Category | NestJS | Go Gin | Django | Laravel | Spring Boot |
|----------|--------|--------|--------|---------|-------------|
| Cache | @nestjs/cache-manager | — (go-cache/redis) | django.core.cache | Cache facade | @Cacheable |
| Logging | Built-in Logger | gin.Logger() | django.utils.log | Log facade (Monolog) | Logback |
| File Upload | FileInterceptor (Multer) | c.FormFile() | request.FILES | $request->file() | @RequestParam MultipartFile |
| Scheduling | @nestjs/schedule @Cron() | — (robfig/cron) | — (celery-beat) | Console\Kernel schedule() | @Scheduled |
| CORS | app.enableCors() | — (gin-contrib/cors) | — (django-cors-headers) | config/cors.php | @CrossOrigin |
| Serialization | class-transformer | struct json tags | DRF Serializers | API Resources | Jackson annotations |

---

## Usage in Phase 2d

1. **Direct equivalence** — auto-map, write to `stack-mapping.json` `auto_mapped` array
2. **Multi-option** — present options to the user naturally, write choice to `user_decisions`
3. **Architectural difference** — explain implications, confirm with user, write to `user_decisions` with `semantic_drift_risk`
4. **Framework built-ins** — scan source for hand-written implementations of categories where target has built-in support; mark as `framework_builtin: true`
