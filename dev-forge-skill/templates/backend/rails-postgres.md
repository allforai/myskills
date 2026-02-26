# Ruby on Rails + PostgreSQL 模板

> 后端参考模板。project-scaffold 读取此文件，按规则生成 Rails API 后端脚手架。

---

## 目录结构

```
apps/{sub-project-name}/
├── Gemfile
├── Gemfile.lock
├── Rakefile
├── .env.example
├── Dockerfile
├── config.ru
│
├── app/
│   ├── controllers/
│   │   ├── application_controller.rb          # 基类: API 模式 + 异常处理
│   │   ├── concerns/
│   │   │   ├── authenticatable.rb             # JWT 认证 concern
│   │   │   └── paginatable.rb                 # 分页 concern
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth_controller.rb         # login / register / me
│   │   │       ├── users_controller.rb
│   │   │       └── {module_name}/             # ★ 业务模块
│   │   │           └── {resource}_controller.rb
│   │   │
│   │   └── health_controller.rb               # 健康检查
│   │
│   ├── models/
│   │   ├── application_record.rb              # 基类
│   │   ├── concerns/
│   │   │   └── has_uuid.rb                    # UUID 主键 concern
│   │   ├── user.rb
│   │   └── {entity_name}.rb                   # ★ 业务实体
│   │
│   ├── serializers/                           # ActiveModel Serializers
│   │   ├── user_serializer.rb
│   │   └── {entity_name}_serializer.rb
│   │
│   ├── services/                              # Service Objects
│   │   ├── auth/
│   │   │   ├── login_service.rb
│   │   │   └── register_service.rb
│   │   └── {module_name}/
│   │       └── {action}_service.rb
│   │
│   └── policies/                              # Pundit 授权 (可选)
│       ├── application_policy.rb
│       └── {entity_name}_policy.rb
│
├── config/
│   ├── application.rb
│   ├── database.yml                           # PostgreSQL 配置
│   ├── routes.rb                              # 路由定义
│   ├── environments/
│   │   ├── development.rb
│   │   ├── production.rb
│   │   └── test.rb
│   └── initializers/
│       ├── cors.rb                            # Rack::Cors 配置
│       └── jwt.rb                             # JWT 配置
│
├── db/
│   ├── migrate/                               # ActiveRecord 迁移
│   │   └── YYYYMMDDHHMMSS_create_{table}.rb
│   ├── schema.rb
│   └── seeds.rb
│
├── lib/
│   └── json_web_token.rb                      # JWT encode/decode 工具
│
└── spec/                                      # RSpec 测试
    ├── rails_helper.rb
    ├── spec_helper.rb
    ├── factories/                             # FactoryBot 工厂
    │   ├── users.rb
    │   └── {entity_name}s.rb
    ├── models/
    │   └── {entity_name}_spec.rb
    └── requests/
        └── api/v1/
            └── {resource}_spec.rb
```

---

## 数据模型生成规则

### Model 映射

```
product-map entity → ActiveRecord Model + Migration

映射规则:
  entity.name (snake_case) → PascalCase class + snake_case 复数表名（Rails 自动）
  entity.fields → migration 列定义 + model 验证
  entity.relations → belongs_to / has_many / has_many :through
  entity.states → enum 声明

示例:
  product-map entity: {
    name: "order",
    fields: ["id", "user_id", "total_amount", "status", "note"],
    states: ["pending", "confirmed", "shipped", "completed", "cancelled"]
  }
  →
  # db/migrate/YYYYMMDDHHMMSS_create_orders.rb
  class CreateOrders < ActiveRecord::Migration[7.1]
    def change
      create_table :orders, id: :uuid do |t|
        t.references :user, null: false, foreign_key: true, type: :uuid
        t.decimal :total_amount, precision: 10, scale: 2, null: false
        t.string :status, null: false, default: "pending"
        t.text :note
        t.timestamps
      end
      add_index :orders, :status
    end
  end

  # app/models/order.rb
  class Order < ApplicationRecord
    belongs_to :user

    enum :status, {
      pending: "pending",
      confirmed: "confirmed",
      shipped: "shipped",
      completed: "completed",
      cancelled: "cancelled"
    }

    validates :total_amount, presence: true, numericality: { greater_than: 0 }
    validates :status, presence: true

    scope :recent, -> { order(created_at: :desc) }
  end

  # app/serializers/order_serializer.rb
  class OrderSerializer < ActiveModel::Serializer
    attributes :id, :user_id, :total_amount, :status, :note, :created_at, :updated_at
    belongs_to :user
  end
```

### 字段类型映射

| product-map 字段类型 | Rails Migration 列类型 |
|---------------------|----------------------|
| string / text | `t.string :name, limit: 255` |
| long_text | `t.text :description` |
| number / integer | `t.integer :count` |
| decimal / money | `t.decimal :amount, precision: 10, scale: 2` |
| boolean | `t.boolean :active, default: false` |
| date | `t.date :birth_date` |
| datetime | `t.datetime :published_at` |
| json | `t.jsonb :metadata, default: {}` |
| enum | `t.string :status` + model `enum` 声明 |
| image_url | `t.string :image_url, limit: 500` |
| foreign_key | `t.references :user, foreign_key: true, type: :uuid` |

---

## 路由生成规则

### CRUD 端点

```
product-map task (CRUD 类型) → Rails resources 路由

命名规则:
  task 对应 entity → 复数小写 snake_case 作为 resources 名
  entity: "order" → resources :orders → /api/v1/orders

标准 CRUD (resources 自动生成):
  GET    /api/v1/{resource}          → index  (分页 + 筛选)
  GET    /api/v1/{resource}/:id      → show
  POST   /api/v1/{resource}          → create
  PUT    /api/v1/{resource}/:id      → update
  DELETE /api/v1/{resource}/:id      → destroy
```

### 非 CRUD 端点

```
task 包含状态变更 / 审批 / 特殊操作 → member / collection 路由

示例:
  task: "审批订单" → member { patch :approve }   → PATCH /api/v1/orders/:id/approve
  task: "批量导出" → collection { post :export }  → POST  /api/v1/orders/export
  task: "统计报表" → collection { get :stats }    → GET   /api/v1/orders/stats
```

### 角色守卫

```
task.owner_role → before_action + Pundit 授权

示例:
  task.owner_role = "admin"    → before_action :require_admin!
  task.owner_role = "merchant" → authorize @order, :approve? (Pundit policy)
```

---

## 配置文件模板

### Gemfile

```ruby
source "https://rubygems.org"

ruby "~> 3.3.0"

gem "rails", "~> 7.1"
gem "pg", "~> 1.5"
gem "puma", "~> 6.4"
gem "bcrypt", "~> 3.1"
gem "jwt", "~> 2.7"
gem "active_model_serializers", "~> 0.10"
gem "rack-cors", "~> 2.0"
gem "kaminari", "~> 1.2"       # 分页
gem "pundit", "~> 2.3"         # 授权
gem "bootsnap", require: false

group :development, :test do
  gem "rspec-rails", "~> 6.1"
  gem "factory_bot_rails", "~> 6.4"
  gem "faker", "~> 3.2"
  gem "dotenv-rails", "~> 3.0"
  gem "rubocop-rails", require: false
end

group :test do
  gem "shoulda-matchers", "~> 6.0"
  gem "database_cleaner-active_record", "~> 2.1"
end
```

### config/database.yml

```yaml
default: &default
  adapter: postgresql
  encoding: unicode
  pool: <%= ENV.fetch("RAILS_MAX_THREADS") { 5 } %>
  host: <%= ENV["DB_HOST"] || "localhost" %>
  port: <%= ENV["DB_PORT"] || 5432 %>
  username: <%= ENV["DB_USER"] %>
  password: <%= ENV["DB_PASS"] %>

development:
  <<: *default
  database: {sub_project_name}_development

test:
  <<: *default
  database: {sub_project_name}_test

production:
  <<: *default
  database: {sub_project_name}_production
```

### config/routes.rb

```ruby
Rails.application.routes.draw do
  get "health", to: "health#show"

  namespace :api do
    namespace :v1 do
      post "auth/login", to: "auth#login"
      post "auth/register", to: "auth#register"
      get  "auth/me", to: "auth#me"

      resources :users, only: [:index, :show, :update, :destroy]
      # resources :{module}, except: [:new, :edit]   ← 按模块追加
    end
  end
end
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | snake_case | `order_item.rb` |
| 类名 | PascalCase | `OrderItem` |
| 变量/方法 | snake_case | `total_amount` |
| 数据库表名 | snake_case 复数（自动） | `order_items` |
| 数据库列名 | snake_case | `total_amount` |
| API 路由 | snake_case 复数 | `/api/v1/order_items` |
| Controller | PascalCase 复数 + Controller | `OrderItemsController` |
| Serializer | PascalCase 单数 + Serializer | `OrderItemSerializer` |
| Factory | snake_case 复数 | `factories/order_items.rb` |
| 常量 | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE` |

---

## Batch 结构（backend 特有）

```
B1 Foundation: Model 文件、enum 声明、ActiveRecord 迁移(rails db:migrate)、config/ + concerns 搭建
B2 API:        Controller + Serializer + Service Object + routes.rb 注册 + 授权策略
B3 —:          (后端无 UI 层，跳过)
B4 Integration: Swagger (rswag) 文档、健康检查端点、统一异常处理(rescue_from)、CORS 配置
B5 Testing:     单元测试 (model + service) + Request spec (RSpec + FactoryBot)
```
