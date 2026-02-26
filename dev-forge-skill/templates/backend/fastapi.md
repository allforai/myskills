# FastAPI + SQLAlchemy + PostgreSQL 模板

> 后端参考模板。project-scaffold 读取此文件，按规则生成 FastAPI 后端脚手架。

---

## 目录结构

```
apps/{sub-project-name}/
├── requirements.txt
├── pyproject.toml
├── .env.example
├── Dockerfile
│
├── app/
│   ├── __init__.py
│   ├── main.py                                # FastAPI() 实例 + lifespan
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                          # Pydantic BaseSettings 配置
│   │   ├── database.py                        # async engine + sessionmaker
│   │   ├── security.py                        # JWT 创建/验证、密码 hash
│   │   └── deps.py                            # Depends: get_db / get_current_user
│   │
│   ├── common/
│   │   ├── __init__.py
│   │   ├── response.py                        # 统一响应模型 (ApiResponse)
│   │   ├── pagination.py                      # PaginationParams / PaginatedResponse
│   │   ├── exceptions.py                      # 自定义 HTTPException 处理器
│   │   └── error_codes.py                     # 错误码常量
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py                          # login / register / me
│   │   ├── service.py
│   │   └── schemas.py                         # LoginRequest / TokenResponse
│   │
│   ├── users/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py                          # SQLAlchemy User model
│   │   └── schemas.py                         # Pydantic UserCreate / UserResponse
│   │
│   └── modules/                               # ★ 业务模块（按 product-map 模块生成）
│       └── {module_name}/
│           ├── __init__.py
│           ├── router.py                      # APIRouter 路由
│           ├── service.py                     # 业务逻辑层（async）
│           ├── models.py                      # SQLAlchemy model
│           └── schemas.py                     # Pydantic request/response schema
│
├── alembic/                                   # Alembic 迁移目录
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── conftest.py                            # pytest-asyncio fixtures
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
product-map entity → SQLAlchemy 2.0 model (async)

映射规则:
  entity.name (snake_case) → PascalCase class + snake_case 复数表名
  entity.fields → mapped_column()
  entity.relations → relationship() + ForeignKey
  entity.states → Python Enum

示例:
  product-map entity: {
    name: "order",
    fields: ["id", "user_id", "total_amount", "status", "note"],
    states: ["pending", "confirmed", "shipped", "completed", "cancelled"]
  }
  →
  import enum
  import uuid
  from sqlalchemy import String, Numeric, Text, ForeignKey, Enum as SAEnum
  from sqlalchemy.orm import Mapped, mapped_column, relationship
  from app.core.database import Base, TimestampMixin

  class OrderStatus(str, enum.Enum):
      PENDING = "pending"
      CONFIRMED = "confirmed"
      SHIPPED = "shipped"
      COMPLETED = "completed"
      CANCELLED = "cancelled"

  class Order(Base, TimestampMixin):
      __tablename__ = "orders"

      id: Mapped[str] = mapped_column(
          String(36), primary_key=True, default=lambda: str(uuid.uuid4())
      )
      user_id: Mapped[str] = mapped_column(
          ForeignKey("users.id"), nullable=False, index=True
      )
      total_amount: Mapped[float] = mapped_column(
          Numeric(10, 2), nullable=False
      )
      status: Mapped[OrderStatus] = mapped_column(
          SAEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING
      )
      note: Mapped[str | None] = mapped_column(Text, nullable=True)

      user: Mapped["User"] = relationship(back_populates="orders")

  # Pydantic schema (schemas.py)
  class OrderCreate(BaseModel):
      user_id: str
      total_amount: Decimal
      note: str | None = None

  class OrderResponse(BaseModel):
      id: str
      user_id: str
      total_amount: Decimal
      status: OrderStatus
      note: str | None
      created_at: datetime
      updated_at: datetime
      model_config = ConfigDict(from_attributes=True)
```

### 字段类型映射

| product-map 字段类型 | SQLAlchemy 2.0 列类型 |
|---------------------|----------------------|
| string / text | `mapped_column(String(255))` — `Mapped[str]` |
| long_text | `mapped_column(Text)` — `Mapped[str]` |
| number / integer | `mapped_column(Integer)` — `Mapped[int]` |
| decimal / money | `mapped_column(Numeric(10, 2))` — `Mapped[Decimal]` |
| boolean | `mapped_column(Boolean, default=False)` — `Mapped[bool]` |
| date | `mapped_column(Date)` — `Mapped[date]` |
| datetime | `mapped_column(DateTime)` — `Mapped[datetime]` |
| json | `mapped_column(JSONB, nullable=True)` — `Mapped[dict \| None]` |
| enum | `mapped_column(SAEnum(XxxStatus))` — `Mapped[XxxStatus]` |
| image_url | `mapped_column(String(500), nullable=True)` — `Mapped[str \| None]` |
| foreign_key | `mapped_column(ForeignKey("xxx.id"))` + `relationship()` |

---

## 路由生成规则

### CRUD 端点

```
product-map task (CRUD 类型) → FastAPI APIRouter 路由

命名规则:
  task 对应 entity → 复数小写 kebab-case 作为路由前缀
  entity: "order" → APIRouter(prefix="/api/orders", tags=["orders"])

标准 CRUD:
  GET    /api/{resource}          → list_items (分页 + 筛选)
  GET    /api/{resource}/{id}     → get_item
  POST   /api/{resource}          → create_item  (status_code=201)
  PUT    /api/{resource}/{id}     → update_item
  DELETE /api/{resource}/{id}     → delete_item  (status_code=204)
```

### 非 CRUD 端点

```
task 包含状态变更 / 审批 / 特殊操作 → 自定义路由

示例:
  task: "审批订单" → PATCH /api/orders/{id}/approve
  task: "批量导出" → POST  /api/orders/export
  task: "统计报表" → GET   /api/orders/stats
```

### 角色守卫

```
task.owner_role → Depends() 依赖注入

示例:
  task.owner_role = "admin"    → Depends(require_role("admin"))
  task.owner_role = "merchant" → Depends(require_role("merchant"))
```

---

## 配置文件模板

### requirements.txt

```
fastapi==0.109.*
uvicorn[standard]==0.27.*
sqlalchemy[asyncio]==2.0.*
asyncpg==0.29.*
alembic==1.13.*
pydantic==2.6.*
pydantic-settings==2.1.*
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*
python-multipart==0.0.6
python-dotenv==1.0.*
httpx==0.27.*
pytest==8.0.*
pytest-asyncio==0.23.*
```

### pyproject.toml（核心段）

```toml
[project]
name = "{sub-project-name}"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### app/core/config.py

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "{sub-project-name}"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/dbname"
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | snake_case | `order_item.py` |
| 类名 | PascalCase | `OrderItem` |
| 变量/函数 | snake_case | `total_amount` |
| 数据库表名 | snake_case 复数 | `order_items` |
| 数据库列名 | snake_case（SQLAlchemy 自动） | `total_amount` |
| API 路由 | kebab-case 复数 | `/api/order-items` |
| Router tag | 复数小写 | `tags=["order-items"]` |
| Pydantic schema | PascalCase + 动作 | `OrderItemCreate` / `OrderItemResponse` |
| 模块目录 | snake_case | `modules/order_items/` |

---

## Batch 结构（backend 特有）

```
B1 Foundation: Model 文件、Enum 定义、Alembic 迁移脚本、core/ + common/ 搭建
B2 API:        APIRouter 路由 + Service 层 + Pydantic Schema + Depends 注入注册
B3 —:          (后端无 UI 层，跳过)
B4 Integration: 自动 OpenAPI 文档(/docs)、健康检查端点、异常处理器统一、CORS 中间件
B5 Testing:     单元测试 (service + model) + API 集成测试 (httpx.AsyncClient + pytest-asyncio)
```
