# Go + Gin + GORM + PostgreSQL 模板

> 后端参考模板。project-scaffold 读取此文件，按规则生成 Go Gin 后端脚手架。

---

## 目录结构

```
apps/{sub-project-name}/
├── go.mod
├── go.sum
├── .env.example
├── Dockerfile
├── Makefile
│
├── cmd/
│   └── server/
│       └── main.go                            # 应用入口
│
├── internal/
│   ├── config/
│   │   └── config.go                          # Viper 配置加载
│   │
│   ├── middleware/
│   │   ├── auth.go                            # JWT 认证中间件
│   │   ├── cors.go                            # CORS 中间件
│   │   ├── logger.go                          # 请求日志中间件
│   │   └── recovery.go                        # Panic 恢复
│   │
│   ├── common/
│   │   ├── response.go                        # 统一响应封装 (Success / Error)
│   │   ├── pagination.go                      # 分页请求/响应结构
│   │   ├── errors.go                          # 自定义错误码
│   │   └── jwt.go                             # JWT 工具函数
│   │
│   ├── auth/
│   │   ├── handler.go                         # Login / Register / Me
│   │   ├── service.go
│   │   └── dto.go                             # LoginRequest / RegisterRequest
│   │
│   ├── users/
│   │   ├── handler.go
│   │   ├── service.go
│   │   ├── model.go                           # User struct + GORM tags
│   │   ├── repository.go
│   │   └── dto.go
│   │
│   ├── modules/                               # ★ 业务模块（按 product-map 模块生成）
│   │   └── {module_name}/
│   │       ├── handler.go                     # Gin handler 函数
│   │       ├── service.go                     # 业务逻辑层
│   │       ├── model.go                       # GORM model struct
│   │       ├── repository.go                  # 数据访问层
│   │       └── dto.go                         # 请求/响应 DTO
│   │
│   └── routes/
│       └── router.go                          # 路由注册总入口
│
├── pkg/                                       # 可复用公共包
│   ├── database/
│   │   └── postgres.go                        # GORM 连接初始化
│   └── validator/
│       └── validator.go                       # 自定义验证器
│
├── migrations/                                # SQL 迁移文件 (golang-migrate)
│   ├── 000001_init.up.sql
│   └── 000001_init.down.sql
│
└── tests/
    ├── setup_test.go                          # 测试初始化
    └── modules/
        └── {module_name}_test.go
```

---

## 数据模型生成规则

### Model 映射

```
product-map entity → GORM model struct

映射规则:
  entity.name (snake_case) → PascalCase struct + snake_case 复数表名 (TableName())
  entity.fields → struct 字段 + gorm tag
  entity.relations → 关联 struct + gorm 外键
  entity.states → string 常量组 或 自定义类型

示例:
  product-map entity: {
    name: "order",
    fields: ["id", "user_id", "total_amount", "status", "note"],
    states: ["pending", "confirmed", "shipped", "completed", "cancelled"]
  }
  →
  package order

  import (
      "time"
      "github.com/google/uuid"
      "gorm.io/gorm"
  )

  type OrderStatus string

  const (
      OrderStatusPending   OrderStatus = "pending"
      OrderStatusConfirmed OrderStatus = "confirmed"
      OrderStatusShipped   OrderStatus = "shipped"
      OrderStatusCompleted OrderStatus = "completed"
      OrderStatusCancelled OrderStatus = "cancelled"
  )

  type Order struct {
      ID          string      `gorm:"type:uuid;primaryKey;default:gen_random_uuid()" json:"id"`
      UserID      string      `gorm:"type:uuid;not null;index" json:"user_id"`
      User        User        `gorm:"foreignKey:UserID" json:"-"`
      TotalAmount float64     `gorm:"type:decimal(10,2);not null" json:"total_amount"`
      Status      OrderStatus `gorm:"type:varchar(20);not null;default:'pending'" json:"status"`
      Note        *string     `gorm:"type:text" json:"note,omitempty"`
      CreatedAt   time.Time   `gorm:"autoCreateTime" json:"created_at"`
      UpdatedAt   time.Time   `gorm:"autoUpdateTime" json:"updated_at"`
  }

  func (Order) TableName() string {
      return "orders"
  }
```

### 字段类型映射

| product-map 字段类型 | GORM 类型 / Go 类型 |
|---------------------|---------------------|
| string / text | `gorm:"type:varchar(255)"` — `string` |
| long_text | `gorm:"type:text"` — `string` |
| number / integer | `gorm:"type:int"` — `int` |
| decimal / money | `gorm:"type:decimal(10,2)"` — `float64` |
| boolean | `gorm:"type:boolean;default:false"` — `bool` |
| date | `gorm:"type:date"` — `time.Time` |
| datetime | `gorm:"type:timestamp"` — `time.Time` |
| json | `gorm:"type:jsonb"` — `datatypes.JSON` |
| enum | `gorm:"type:varchar(20)"` — 自定义 `type XxxStatus string` |
| image_url | `gorm:"type:varchar(500)"` — `*string` |
| foreign_key | `gorm:"type:uuid;index"` + 关联 struct |

---

## 路由生成规则

### CRUD 端点

```
product-map task (CRUD 类型) → Gin RouterGroup 路由

命名规则:
  task 对应 entity → 复数小写 kebab-case 作为路由组前缀
  entity: "order" → routerGroup: /api/orders

标准 CRUD:
  GET    /api/{resource}          → List   (分页 + 筛选)
  GET    /api/{resource}/:id      → GetByID
  POST   /api/{resource}          → Create
  PUT    /api/{resource}/:id      → Update
  DELETE /api/{resource}/:id      → Delete
```

### 非 CRUD 端点

```
task 包含状态变更 / 审批 / 特殊操作 → 自定义路由

示例:
  task: "审批订单" → PATCH /api/orders/:id/approve
  task: "批量导出" → POST  /api/orders/export
  task: "统计报表" → GET   /api/orders/stats
```

### 角色守卫

```
task.owner_role → 中间件函数

示例:
  task.owner_role = "admin"    → middleware.RequireRole("admin")
  task.owner_role = "merchant" → middleware.RequireRole("merchant")
```

---

## 配置文件模板

### go.mod

```
module github.com/{org}/{sub-project-name}

go 1.22

require (
    github.com/gin-gonic/gin v1.9.1
    gorm.io/gorm v1.25.5
    gorm.io/driver/postgres v1.5.4
    github.com/golang-jwt/jwt/v5 v5.2.0
    github.com/spf13/viper v1.18.2
    github.com/google/uuid v1.6.0
    github.com/swaggo/gin-swagger v1.6.0
    github.com/swaggo/swag v1.16.3
    github.com/stretchr/testify v1.8.4
    github.com/golang-migrate/migrate/v4 v4.17.0
)
```

### Makefile

```makefile
.PHONY: dev build test migrate

dev:
	go run cmd/server/main.go

build:
	go build -o bin/server cmd/server/main.go

test:
	go test ./... -v -cover

migrate-up:
	migrate -path migrations -database "$(DATABASE_URL)" up

migrate-down:
	migrate -path migrations -database "$(DATABASE_URL)" down 1

swag:
	swag init -g cmd/server/main.go -o docs
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | snake_case.go | `order_item.go` |
| struct 名 | PascalCase | `OrderItem` |
| 字段名 (exported) | PascalCase | `TotalAmount` |
| JSON tag | snake_case | `json:"total_amount"` |
| 数据库表名 | snake_case 复数 | `order_items` |
| 数据库列名 | snake_case（gorm 自动） | `total_amount` |
| API 路由 | kebab-case 复数 | `/api/order-items` |
| 包名 | 全小写单词 | `orderitem` |
| 常量 | PascalCase 前缀 | `OrderStatusPending` |
| 接口名 | PascalCase + er | `OrderRepository` |

---

## Batch 结构（backend 特有）

```
B1 Foundation: Model struct、常量/类型定义、SQL 迁移脚本、config/ + common/ + pkg/database 搭建
B2 API:        Handler + Service + Repository + DTO + 路由注册 + 中间件挂载
B3 —:          (后端无 UI 层，跳过)
B4 Integration: Swagger 文档(swaggo)、健康检查端点、错误码统一、Makefile 完善
B5 Testing:     单元测试 (service + repository mock) + API 集成测试 (httptest)
```
