# Flask + SQLAlchemy + PostgreSQL 模板

> 后端参考模板。project-scaffold 读取此文件，按规则生成 Flask 后端脚手架。

---

## 目录结构

```
apps/{sub-project-name}/
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .flaskenv
├── Dockerfile
│
├── app/
│   ├── __init__.py                            # create_app() 工厂函数
│   ├── extensions.py                          # db / migrate / ma / jwt 实例
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                        # 基础/开发/生产配置
│   │   └── database.py                        # SQLAlchemy URI 构建
│   │
│   ├── common/
│   │   ├── __init__.py
│   │   ├── response.py                        # 统一响应封装 (success / error)
│   │   ├── exceptions.py                      # 自定义异常 + 错误处理器
│   │   ├── pagination.py                      # 分页工具函数
│   │   ├── decorators.py                      # role_required / validate_json
│   │   └── error_codes.py                     # 错误码常量
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py                          # Blueprint: login / register / me
│   │   ├── services.py
│   │   └── schemas.py                         # LoginSchema / RegisterSchema
│   │
│   ├── users/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── services.py
│   │   ├── models.py                          # User model
│   │   └── schemas.py                         # UserSchema
│   │
│   └── modules/                               # ★ 业务模块（按 product-map 模块生成）
│       └── {module_name}/
│           ├── __init__.py
│           ├── routes.py                      # Blueprint 路由
│           ├── services.py                    # 业务逻辑层
│           ├── models.py                      # SQLAlchemy model
│           └── schemas.py                     # Marshmallow schema
│
├── migrations/                                # Alembic 迁移目录
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── conftest.py                            # pytest fixtures
│   ├── test_auth.py
│   └── modules/
│       └── test_{module_name}.py
│
└── docker-compose.yml
```

---

## 数据模型生成规则

### Model 映射

```
product-map entity → SQLAlchemy model

映射规则:
  entity.name (snake_case) → PascalCase class + snake_case 复数表名
  entity.fields → db.Column()
  entity.relations → db.relationship() + db.ForeignKey()
  entity.states → Python Enum

示例:
  product-map entity: {
    name: "order",
    fields: ["id", "user_id", "total_amount", "status", "note"],
    states: ["pending", "confirmed", "shipped", "completed", "cancelled"]
  }
  →
  import enum
  from app.extensions import db

  class OrderStatus(enum.Enum):
      PENDING = "pending"
      CONFIRMED = "confirmed"
      SHIPPED = "shipped"
      COMPLETED = "completed"
      CANCELLED = "cancelled"

  class Order(db.Model):
      __tablename__ = "orders"

      id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
      user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
      total_amount = db.Column(db.Numeric(10, 2), nullable=False)
      status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
      note = db.Column(db.Text, nullable=True)
      created_at = db.Column(db.DateTime, server_default=db.func.now())
      updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

      user = db.relationship("User", backref=db.backref("orders", lazy="dynamic"))
```

### 字段类型映射

| product-map 字段类型 | SQLAlchemy 列类型 |
|---------------------|------------------|
| string / text | `db.Column(db.String(255))` |
| long_text | `db.Column(db.Text)` |
| number / integer | `db.Column(db.Integer)` |
| decimal / money | `db.Column(db.Numeric(10, 2))` |
| boolean | `db.Column(db.Boolean, default=False)` |
| date | `db.Column(db.Date)` |
| datetime | `db.Column(db.DateTime)` |
| json | `db.Column(db.JSON, nullable=True)` |
| enum | `db.Column(db.Enum(XxxStatus))` |
| image_url | `db.Column(db.String(500), nullable=True)` |
| foreign_key | `db.Column(db.String(36), db.ForeignKey("xxx.id"))` |

---

## 路由生成规则

### CRUD 端点

```
product-map task (CRUD 类型) → Flask Blueprint 路由

命名规则:
  task 对应 entity → 复数小写 snake_case 作为 Blueprint 名 + kebab-case URL 前缀
  entity: "order" → Blueprint("orders") → 路由: /api/orders

标准 CRUD:
  GET    /api/{resource}          → list_items (分页 + 筛选)
  GET    /api/{resource}/<id>     → get_item
  POST   /api/{resource}          → create_item
  PUT    /api/{resource}/<id>     → update_item
  DELETE /api/{resource}/<id>     → delete_item
```

### 非 CRUD 端点

```
task 包含状态变更 / 审批 / 特殊操作 → 自定义路由

示例:
  task: "审批订单" → PATCH /api/orders/<id>/approve
  task: "批量导出" → POST  /api/orders/export
  task: "统计报表" → GET   /api/orders/stats
```

### 角色守卫

```
task.owner_role → @role_required() 装饰器

示例:
  task.owner_role = "admin"    → @role_required("admin")
  task.owner_role = "merchant" → @role_required("merchant")
```

---

## 配置文件模板

### requirements.txt

```
Flask==3.0.*
Flask-SQLAlchemy==3.1.*
Flask-Migrate==4.0.*
Flask-Marshmallow==1.2.*
marshmallow-sqlalchemy==1.0.*
Flask-JWT-Extended==4.6.*
Flask-CORS==4.0.*
psycopg2-binary==2.9.*
python-dotenv==1.0.*
gunicorn==21.2.*
pytest==8.0.*
pytest-flask==1.3.*
```

### pyproject.toml（核心段）

```toml
[project]
name = "{sub-project-name}"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | snake_case | `order_item.py` |
| 类名 | PascalCase | `OrderItem` |
| 变量/函数 | snake_case | `total_amount` |
| 数据库表名 | snake_case 复数 | `order_items` |
| 数据库列名 | snake_case | `total_amount` |
| API 路由 | kebab-case 复数 | `/api/order-items` |
| Blueprint 名 | snake_case 复数 | `order_items` |
| Schema 文件 | snake_case | `schemas.py` (内含 `OrderItemSchema`) |
| 模块目录 | snake_case | `modules/order_items/` |

---

## Batch 结构（backend 特有）

```
B1 Foundation: Model 文件、Enum 定义、Alembic 迁移脚本、config/ + common/ + extensions 搭建
B2 API:        Blueprint 路由 + Service 层 + Marshmallow Schema + 装饰器注册
B3 —:          (后端无 UI 层，跳过)
B4 Integration: Swagger/Flasgger 文档、健康检查端点、错误处理器统一、CORS 配置
B5 Testing:     单元测试 (model + service) + API 集成测试 (pytest-flask client)
```
