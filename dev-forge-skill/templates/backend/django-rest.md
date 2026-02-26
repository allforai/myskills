# Django + DRF + PostgreSQL 模板

> 后端参考模板。project-scaffold 读取此文件，按规则生成 Django REST Framework 后端脚手架。

---

## 目录结构

```
apps/{sub-project-name}/
├── manage.py
├── requirements.txt
├── pyproject.toml
├── .env.example
├── Dockerfile
│
├── config/                                    # 项目级配置（Django project）
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                            # 公共设置
│   │   ├── development.py                     # 开发环境
│   │   └── production.py                      # 生产环境
│   ├── urls.py                                # 根 URL 配置
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                                      # Django apps 目录
│   ├── __init__.py
│   │
│   ├── common/
│   │   ├── __init__.py
│   │   ├── permissions.py                     # IsOwner / IsAdmin 自定义权限
│   │   ├── pagination.py                      # StandardPagination 类
│   │   ├── exceptions.py                      # 自定义异常处理器
│   │   ├── mixins.py                          # TimestampMixin 等
│   │   └── response.py                        # 统一响应封装
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── urls.py
│   │   ├── views.py                           # LoginView / RegisterView / MeView
│   │   └── serializers.py                     # LoginSerializer / RegisterSerializer
│   │
│   ├── users/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                          # User model (AbstractUser)
│   │   ├── admin.py
│   │   ├── urls.py
│   │   ├── views.py                           # UserViewSet
│   │   ├── serializers.py
│   │   └── migrations/
│   │
│   └── {module_name}/                         # ★ 业务模块（按 product-map 模块生成）
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py                          # Django Model
│       ├── admin.py                           # ModelAdmin 注册
│       ├── urls.py                            # Router 注册
│       ├── views.py                           # ModelViewSet
│       ├── serializers.py                     # ModelSerializer
│       ├── filters.py                         # django-filter FilterSet
│       ├── permissions.py                     # 模块级权限（可选）
│       └── migrations/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   └── {module_name}/
│       ├── test_models.py
│       ├── test_views.py
│       └── test_serializers.py
│
└── docker-compose.yml
```

---

## 数据模型生成规则

### Model 映射

```
product-map entity → Django Model

映射规则:
  entity.name (snake_case) → PascalCase class + 默认 snake_case 复数表名
  entity.fields → Django Field 类型
  entity.relations → ForeignKey / ManyToManyField
  entity.states → TextChoices

示例:
  product-map entity: {
    name: "order",
    fields: ["id", "user_id", "total_amount", "status", "note"],
    states: ["pending", "confirmed", "shipped", "completed", "cancelled"]
  }
  →
  import uuid
  from django.db import models

  class Order(models.Model):

      class Status(models.TextChoices):
          PENDING = "pending", "Pending"
          CONFIRMED = "confirmed", "Confirmed"
          SHIPPED = "shipped", "Shipped"
          COMPLETED = "completed", "Completed"
          CANCELLED = "cancelled", "Cancelled"

      id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
      user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="orders")
      total_amount = models.DecimalField(max_digits=10, decimal_places=2)
      status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
      note = models.TextField(blank=True, default="")
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      class Meta:
          db_table = "orders"
          ordering = ["-created_at"]
```

### 字段类型映射

| product-map 字段类型 | Django Field 类型 |
|---------------------|------------------|
| string / text | `models.CharField(max_length=255)` |
| long_text | `models.TextField()` |
| number / integer | `models.IntegerField()` |
| decimal / money | `models.DecimalField(max_digits=10, decimal_places=2)` |
| boolean | `models.BooleanField(default=False)` |
| date | `models.DateField()` |
| datetime | `models.DateTimeField()` |
| json | `models.JSONField(default=dict, blank=True)` |
| enum | `models.CharField(choices=XxxStatus.choices)` |
| image_url | `models.URLField(max_length=500, blank=True)` |
| foreign_key | `models.ForeignKey("app.Model", on_delete=models.CASCADE)` |

---

## 路由生成规则

### CRUD 端点

```
product-map task (CRUD 类型) → DRF ModelViewSet + DefaultRouter

命名规则:
  task 对应 entity → 复数小写 kebab-case 作为路由前缀
  entity: "order" → router.register("orders", OrderViewSet) → /api/orders/

标准 CRUD (ModelViewSet 自动生成):
  GET    /api/{resource}/          → list (分页 + 筛选)
  GET    /api/{resource}/{id}/     → retrieve
  POST   /api/{resource}/          → create
  PUT    /api/{resource}/{id}/     → update
  PATCH  /api/{resource}/{id}/     → partial_update
  DELETE /api/{resource}/{id}/     → destroy
```

### 非 CRUD 端点

```
task 包含状态变更 / 审批 / 特殊操作 → @action 装饰器

示例:
  task: "审批订单" → @action(detail=True, methods=["patch"], url_path="approve")
  task: "批量导出" → @action(detail=False, methods=["post"], url_path="export")
  task: "统计报表" → @action(detail=False, methods=["get"], url_path="stats")
```

### 角色守卫

```
task.owner_role → permission_classes

示例:
  task.owner_role = "admin"    → permission_classes = [IsAuthenticated, IsAdmin]
  task.owner_role = "merchant" → permission_classes = [IsAuthenticated, IsMerchant]
```

---

## 配置文件模板

### requirements.txt

```
Django==5.0.*
djangorestframework==3.15.*
djangorestframework-simplejwt==5.3.*
django-filter==24.1
django-cors-headers==4.3.*
psycopg2-binary==2.9.*
python-dotenv==1.0.*
drf-spectacular==0.27.*
gunicorn==21.2.*
pytest==8.0.*
pytest-django==4.8.*
factory-boy==3.3.*
```

### settings/base.py（核心段）

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # Local apps
    "apps.users",
    "apps.auth",
    # "apps.{module_name}",   ← 按模块追加
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASS"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | snake_case | `order_item.py`（通常统一放 `models.py`）|
| 类名 | PascalCase | `OrderItem` |
| 变量/函数 | snake_case | `total_amount` |
| 数据库表名 | snake_case 复数 (Meta.db_table) | `order_items` |
| 数据库列名 | snake_case（Django 自动） | `total_amount` |
| API 路由 | kebab-case 复数 | `/api/order-items/` |
| App 目录 | snake_case | `apps/order_items/` |
| Serializer | PascalCase + Serializer | `OrderItemSerializer` |
| ViewSet | PascalCase + ViewSet | `OrderItemViewSet` |

---

## Batch 结构（backend 特有）

```
B1 Foundation: Model 文件、TextChoices 枚举、Django 迁移(makemigrations)、config/ + common/ 搭建
B2 API:        ViewSet + Serializer + Router 注册 + FilterSet + 权限类
B3 —:          (后端无 UI 层，跳过)
B4 Integration: drf-spectacular OpenAPI 文档、健康检查端点、异常处理器统一、Admin 注册
B5 Testing:     单元测试 (model + serializer) + API 集成测试 (APITestCase / pytest-django)
```
