# Express -> Gin (Go) Mapping

> Equivalence tables for translating Node.js/Express patterns to Go/Gin.
> Three categories: direct equivalence (auto-map), multi-option (user decision), architectural difference (needs explanation).
> Source reference: `claude/code-replicate-skill/docs/stack-mappings.md`

---

## Routing

| Express | Gin | Type | Notes |
|---------|-----|------|-------|
| `router.get("/path", handler)` | `r.GET("/path", handler)` | Direct | |
| `router.post("/path", handler)` | `r.POST("/path", handler)` | Direct | |
| `router.put("/path", handler)` | `r.PUT("/path", handler)` | Direct | |
| `router.patch("/path", handler)` | `r.PATCH("/path", handler)` | Direct | |
| `router.delete("/path", handler)` | `r.DELETE("/path", handler)` | Direct | |
| `router.all("/path", handler)` | `r.Any("/path", handler)` | Direct | |
| `express.Router()` prefix group | `r.Group("/prefix")` | Direct | |
| Nested routers | Nested `r.Group()` | Direct | |
| `req.params.id` | `c.Param("id")` | Direct | `:id` in route pattern |
| `req.query.page` | `c.Query("page")` | Direct | |
| `req.query` with default | `c.DefaultQuery("page", "1")` | Direct | |
| `req.body` (JSON) | `c.ShouldBindJSON(&body)` | Direct | Returns error; check it |
| `req.body` (form) | `c.ShouldBind(&form)` | Direct | Uses struct tags |
| `req.headers["x-token"]` | `c.GetHeader("X-Token")` | Direct | |
| `res.json(data)` | `c.JSON(http.StatusOK, data)` | Direct | |
| `res.status(404).json(err)` | `c.JSON(http.StatusNotFound, err)` | Direct | |
| `res.send(text)` | `c.String(http.StatusOK, text)` | Direct | |
| `res.sendFile(path)` | `c.File(path)` | Direct | |
| `res.redirect(url)` | `c.Redirect(http.StatusFound, url)` | Direct | |
| `next()` in handler | `c.Next()` | Direct | |
| `next(err)` error pass | `c.AbortWithStatusJSON(500, err)` | Direct | |
| `req.app.locals` | Passed via `c.Set` / `c.Get` | Direct | |

---

## Middleware

| Express | Gin | Type | Notes |
|---------|-----|------|-------|
| `app.use(cors())` | `r.Use(cors.Default())` | Direct | `github.com/gin-contrib/cors` |
| `app.use(morgan("dev"))` | `r.Use(gin.Logger())` | Direct | Built-in |
| `app.use(express.json())` | Built-in via `ShouldBindJSON` | Direct | No separate middleware needed |
| `app.use(express.urlencoded())` | Built-in via `ShouldBind` | Direct | |
| `app.use(helmet())` | `r.Use(secure.New(...))` | Direct | `github.com/unrolled/secure` |
| `app.use(compression())` | `r.Use(gzip.Gzip(gzip.DefaultCompression))` | Direct | `github.com/gin-contrib/gzip` |
| `app.use(express.static(dir))` | `r.Static("/static", "./static")` | Direct | |
| Custom auth middleware | `func AuthMiddleware() gin.HandlerFunc` | Direct | Returns `gin.HandlerFunc` |
| `req.user = decoded` | `c.Set("user", decoded)` | Direct | |
| `req.user` (read) | `c.Get("user")` with type assertion | Direct | |
| `app.use(rateLimit(...))` | `r.Use(limiter.RateLimiter(...))` | Multi-option | A: `golang.org/x/time/rate` / B: `ulule/limiter` |
| Global error handler (4-arg middleware) | `gin.Recovery()` + custom `RecoveryWithWriter` | Direct | |
| `app.use` order matters | Middleware registration order in Gin | Direct | Same semantics |

---

## ORM (Sequelize -> GORM)

| Sequelize | GORM | Type | Notes |
|-----------|------|------|-------|
| `Model.findAll()` | `db.Find(&results)` | Direct | |
| `Model.findAll({ where })` | `db.Where("field = ?", val).Find(&results)` | Direct | |
| `Model.findOne({ where })` | `db.Where("field = ?", val).First(&result)` | Direct | Returns error on not-found |
| `Model.findByPk(id)` | `db.First(&result, id)` | Direct | |
| `Model.count({ where })` | `db.Model(&Model{}).Where(...).Count(&count)` | Direct | |
| `Model.create(data)` | `db.Create(&record)` | Direct | |
| `Model.bulkCreate(records)` | `db.Create(&records)` (slice) | Direct | |
| `Model.update(data, { where })` | `db.Model(&record).Updates(data)` | Direct | |
| `Model.destroy({ where })` | `db.Delete(&record, id)` | Direct | Soft delete if `gorm.Model` used |
| `Model.destroy({ force: true })` | `db.Unscoped().Delete(&record)` | Direct | Hard delete |
| `sequelize.query(sql)` | `db.Raw(sql).Scan(&result)` | Direct | |
| `include` (eager load) | `db.Preload("Association").Find(...)` | Direct | |
| Migrations (sequelize-cli) | GORM `AutoMigrate` (dev) / goose (prod) | Multi-option | A: AutoMigrate (simple) / B: goose (versioned) |
| `belongsTo` / `hasMany` | GORM struct tags (`belongs_to` / `has_many`) | Direct | |
| `hasMany` through join table | `many2many:"join_table"` GORM tag | Direct | |
| Transactions | `db.Transaction(func(tx *gorm.DB) error {...})` | Direct | |
| `Model.scope` | GORM Scopes (`db.Scopes(myScope)`) | Direct | |
| `Op.like` | `db.Where("name LIKE ?", "%val%")` | Direct | |
| `Op.in` | `db.Where("id IN ?", ids)` | Direct | |

---

## Auth (Passport.js -> Go)

| Passport.js / Express | Go | Type | Notes |
|----------------------|-----|------|-------|
| JWT strategy (`passport-jwt`) | `golang-jwt/jwt` | Direct | `github.com/golang-jwt/jwt/v5` |
| JWT sign | `jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(secret)` | Direct | |
| JWT verify | `jwt.ParseWithClaims(tokenStr, &claims, keyFunc)` | Direct | |
| OAuth2 strategy (`passport-oauth2`) | `golang.org/x/oauth2` | Direct | |
| Google OAuth | `golang.org/x/oauth2/google` | Direct | |
| Session strategy | `gorilla/sessions` + Redis | Multi-option | A: JWT (stateless) / B: Redis session (stateful) |
| `req.isAuthenticated()` | Custom middleware + `c.Get("user")` check | Direct | |
| `req.logout()` | Token blacklist or short TTL + refresh | Multi-option | A: token blacklist in Redis / B: short TTL |
| RBAC (`accesscontrol`) | `casbin` | Direct | `github.com/casbin/casbin` |
| `passport.initialize()` | — | Arch diff | No passport equivalent; implement middleware directly |
| `passport.session()` | — | Arch diff | Use gorilla/sessions if session needed |

---

## Async / Concurrency

| Express/Node | Go | Type | Notes |
|-------------|-----|------|-------|
| `async/await` function | goroutine | Direct | Gin handlers run in goroutines per request |
| `await fetch(url)` | `http.Get(url)` / `resty` / `req` | Multi-option | A: stdlib `net/http` / B: `go-resty/resty` |
| `Promise.all([a, b, c])` | `errgroup.Group` | Direct | `golang.org/x/sync/errgroup` |
| `Promise.all` dynamic | `sync.WaitGroup` + channel | Direct | |
| `Promise.race` | `select` on channels | Direct | |
| `setTimeout(fn, delay)` | `time.AfterFunc(delay, fn)` | Direct | |
| `setInterval(fn, period)` | `time.NewTicker(period)` | Direct | |
| `clearInterval` | `ticker.Stop()` | Direct | |
| Bull/BullMQ queue | `asynq` (Redis) | Direct | `github.com/hibiken/asynq` — same Redis backend |
| Bull/BullMQ (PostgreSQL) | `pg-boss` -> `river` | Direct | `github.com/riverqueue/river` |
| Celery (Python) | `machinery` | Multi-option | A: asynq (Redis) / B: machinery (multi-backend) |
| Worker threads | goroutine pool | Direct | |
| `EventEmitter` | channels / `sync.Cond` | Multi-option | A: channels (typed) / B: pub/sub lib (watermill) |
| `process.on("uncaughtException")` | `recover()` in goroutine | Direct | |
| Stream piping | `io.Copy` / `io.Pipe` | Direct | |
| `util.promisify` | — | Arch diff | Go uses synchronous calls in goroutines; no promisify |
