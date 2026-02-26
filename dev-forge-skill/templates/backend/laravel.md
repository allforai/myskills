# Laravel + Eloquent + PostgreSQL 模板

> 后端参考模板。project-scaffold 读取此文件，按规则生成 Laravel 后端脚手架。

---

## 目录结构

```
apps/{sub-project-name}/
├── composer.json
├── artisan
├── .env.example
├── Dockerfile
│
├── app/
│   ├── Http/
│   │   ├── Controllers/
│   │   │   ├── Controller.php                 # 基类
│   │   │   ├── Auth/
│   │   │   │   └── AuthController.php         # login / register / me
│   │   │   └── Api/
│   │   │       ├── UserController.php
│   │   │       └── {Module}/                  # ★ 业务模块
│   │   │           └── {Entity}Controller.php
│   │   │
│   │   ├── Middleware/
│   │   │   ├── Authenticate.php
│   │   │   └── CheckRole.php                  # 角色检查中间件
│   │   │
│   │   ├── Requests/                          # Form Requests（验证）
│   │   │   ├── Auth/
│   │   │   │   ├── LoginRequest.php
│   │   │   │   └── RegisterRequest.php
│   │   │   └── {Module}/
│   │   │       ├── Store{Entity}Request.php
│   │   │       └── Update{Entity}Request.php
│   │   │
│   │   └── Resources/                         # API Resources（序列化）
│   │       ├── UserResource.php
│   │       └── {Module}/
│   │           ├── {Entity}Resource.php
│   │           └── {Entity}Collection.php
│   │
│   ├── Models/
│   │   ├── User.php
│   │   └── {Entity}.php                       # ★ Eloquent 模型
│   │
│   ├── Services/                              # 业务逻辑层
│   │   ├── AuthService.php
│   │   └── {Module}/
│   │       └── {Entity}Service.php
│   │
│   ├── Enums/                                 # PHP 8.1+ Enum
│   │   └── {Entity}Status.php
│   │
│   ├── Exceptions/
│   │   └── Handler.php                        # 统一异常处理
│   │
│   └── Providers/
│       ├── AppServiceProvider.php
│       ├── AuthServiceProvider.php
│       └── RouteServiceProvider.php
│
├── config/
│   ├── app.php
│   ├── auth.php                               # Sanctum / JWT 配置
│   ├── database.php
│   └── cors.php
│
├── database/
│   ├── migrations/
│   │   └── YYYY_MM_DD_HHMMSS_create_{table}_table.php
│   ├── factories/
│   │   ├── UserFactory.php
│   │   └── {Entity}Factory.php
│   └── seeders/
│       └── DatabaseSeeder.php
│
├── routes/
│   ├── api.php                                # API 路由定义
│   └── web.php
│
├── tests/
│   ├── TestCase.php
│   ├── Feature/
│   │   ├── Auth/
│   │   │   └── AuthTest.php
│   │   └── Api/
│   │       └── {Entity}Test.php
│   └── Unit/
│       └── Services/
│           └── {Entity}ServiceTest.php
│
└── docker-compose.yml
```

---

## 数据模型生成规则

### Model 映射

```
product-map entity → Eloquent Model + Migration

映射规则:
  entity.name (snake_case) → PascalCase class + snake_case 复数表名（Laravel 自动）
  entity.fields → migration 列定义 + model $fillable / $casts
  entity.relations → belongsTo / hasMany / belongsToMany
  entity.states → PHP Enum

示例:
  product-map entity: {
    name: "order",
    fields: ["id", "user_id", "total_amount", "status", "note"],
    states: ["pending", "confirmed", "shipped", "completed", "cancelled"]
  }
  →
  // app/Enums/OrderStatus.php
  enum OrderStatus: string
  {
      case Pending = 'pending';
      case Confirmed = 'confirmed';
      case Shipped = 'shipped';
      case Completed = 'completed';
      case Cancelled = 'cancelled';
  }

  // database/migrations/YYYY_MM_DD_create_orders_table.php
  Schema::create('orders', function (Blueprint $table) {
      $table->uuid('id')->primary();
      $table->foreignUuid('user_id')->constrained()->cascadeOnDelete();
      $table->decimal('total_amount', 10, 2);
      $table->string('status', 20)->default('pending');
      $table->text('note')->nullable();
      $table->timestamps();
      $table->index('status');
  });

  // app/Models/Order.php
  class Order extends Model
  {
      use HasUuids;

      protected $fillable = [
          'user_id', 'total_amount', 'status', 'note',
      ];

      protected $casts = [
          'total_amount' => 'decimal:2',
          'status' => OrderStatus::class,
      ];

      public function user(): BelongsTo
      {
          return $this->belongsTo(User::class);
      }
  }

  // app/Http/Resources/Order/OrderResource.php
  class OrderResource extends JsonResource
  {
      public function toArray(Request $request): array
      {
          return [
              'id' => $this->id,
              'user_id' => $this->user_id,
              'total_amount' => $this->total_amount,
              'status' => $this->status,
              'note' => $this->note,
              'created_at' => $this->created_at,
              'updated_at' => $this->updated_at,
          ];
      }
  }
```

### 字段类型映射

| product-map 字段类型 | Laravel Migration 列类型 |
|---------------------|------------------------|
| string / text | `$table->string('name', 255)` |
| long_text | `$table->text('description')` |
| number / integer | `$table->integer('count')` |
| decimal / money | `$table->decimal('amount', 10, 2)` |
| boolean | `$table->boolean('active')->default(false)` |
| date | `$table->date('birth_date')` |
| datetime | `$table->timestamp('published_at')` |
| json | `$table->jsonb('metadata')->nullable()` |
| enum | `$table->string('status', 20)` + PHP Enum cast |
| image_url | `$table->string('image_url', 500)->nullable()` |
| foreign_key | `$table->foreignUuid('user_id')->constrained()` |

---

## 路由生成规则

### CRUD 端点

```
product-map task (CRUD 类型) → Laravel apiResource 路由

命名规则:
  task 对应 entity → 复数小写 kebab-case 作为路由前缀
  entity: "order" → Route::apiResource('orders', OrderController::class)

标准 CRUD (apiResource 自动生成):
  GET    /api/{resource}          → index  (分页 + 筛选)
  GET    /api/{resource}/{id}     → show
  POST   /api/{resource}          → store
  PUT    /api/{resource}/{id}     → update
  DELETE /api/{resource}/{id}     → destroy
```

### 非 CRUD 端点

```
task 包含状态变更 / 审批 / 特殊操作 → 自定义路由

示例:
  task: "审批订单" → Route::patch('orders/{order}/approve', [OrderController::class, 'approve'])
  task: "批量导出" → Route::post('orders/export', [OrderController::class, 'export'])
  task: "统计报表" → Route::get('orders/stats', [OrderController::class, 'stats'])
```

### 角色守卫

```
task.owner_role → middleware 绑定

示例:
  task.owner_role = "admin"    → ->middleware('role:admin')
  task.owner_role = "merchant" → ->middleware('role:merchant')
```

---

## 配置文件模板

### composer.json（核心依赖）

```json
{
    "name": "{vendor}/{sub-project-name}",
    "type": "project",
    "require": {
        "php": "^8.2",
        "laravel/framework": "^11.0",
        "laravel/sanctum": "^4.0",
        "spatie/laravel-query-builder": "^5.8",
        "spatie/laravel-data": "^4.0"
    },
    "require-dev": {
        "fakerphp/faker": "^1.23",
        "laravel/pint": "^1.13",
        "phpunit/phpunit": "^10.5",
        "laravel/telescope": "^5.0",
        "barryvdh/laravel-ide-helper": "^3.0"
    },
    "scripts": {
        "dev": "php artisan serve",
        "test": "php artisan test",
        "lint": "pint"
    }
}
```

### .env.example

```
APP_NAME={sub-project-name}
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://localhost:8000

DB_CONNECTION=pgsql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE={sub_project_name}
DB_USERNAME=postgres
DB_PASSWORD=

JWT_SECRET=change-me
JWT_TTL=60
```

### routes/api.php

```php
use Illuminate\Support\Facades\Route;

Route::post('auth/login', [AuthController::class, 'login']);
Route::post('auth/register', [AuthController::class, 'register']);

Route::middleware('auth:sanctum')->group(function () {
    Route::get('auth/me', [AuthController::class, 'me']);
    Route::apiResource('users', UserController::class);
    // Route::apiResource('{resource}', {Entity}Controller::class);  ← 按模块追加
});
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | PascalCase | `OrderItem.php` |
| 类名 | PascalCase | `OrderItem` |
| 变量/属性 | camelCase / snake_case(Eloquent) | `$totalAmount` / `total_amount` |
| 数据库表名 | snake_case 复数（自动） | `order_items` |
| 数据库列名 | snake_case | `total_amount` |
| API 路由 | kebab-case 复数 | `/api/order-items` |
| Controller | PascalCase 单数 + Controller | `OrderItemController` |
| Resource | PascalCase 单数 + Resource | `OrderItemResource` |
| FormRequest | Store/Update + PascalCase + Request | `StoreOrderItemRequest` |
| Factory | PascalCase + Factory | `OrderItemFactory` |
| Enum | PascalCase + Status/Type | `OrderItemStatus` |

---

## Batch 结构（backend 特有）

```
B1 Foundation: Model 文件、Enum 定义、Artisan 迁移(php artisan migrate)、config/ + Providers 搭建
B2 API:        Controller + FormRequest + Resource + Service + routes/api.php 注册 + Middleware
B3 —:          (后端无 UI 层，跳过)
B4 Integration: Swagger(L5-Swagger) 文档、健康检查端点、Handler 统一异常、CORS 配置
B5 Testing:     单元测试 (Service + Model) + Feature 测试 (PHPUnit + Factory)
```
