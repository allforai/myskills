# Spring Boot + JPA + PostgreSQL 模板

> 后端参考模板。project-scaffold 读取此文件，按规则生成 Spring Boot 后端脚手架。

---

## 目录结构

```
apps/{sub-project-name}/
├── pom.xml                                    # Maven 构建文件
├── build.gradle                               # Gradle 构建文件（二选一）
├── .env.example
├── Dockerfile
│
├── src/
│   ├── main/
│   │   ├── java/com/{group}/{artifact}/
│   │   │   ├── Application.java               # @SpringBootApplication 入口
│   │   │   │
│   │   │   ├── config/
│   │   │   │   ├── DatabaseConfig.java         # DataSource 配置
│   │   │   │   ├── SecurityConfig.java         # Spring Security 配置
│   │   │   │   ├── SwaggerConfig.java          # Springdoc OpenAPI 配置
│   │   │   │   └── WebConfig.java              # CORS / 拦截器注册
│   │   │   │
│   │   │   ├── common/
│   │   │   │   ├── dto/
│   │   │   │   │   ├── ApiResponse.java        # 统一响应包装
│   │   │   │   │   └── PageRequest.java        # 分页请求 DTO
│   │   │   │   ├── exception/
│   │   │   │   │   ├── GlobalExceptionHandler.java  # @ControllerAdvice
│   │   │   │   │   ├── BusinessException.java
│   │   │   │   │   └── ErrorCode.java          # 错误码枚举
│   │   │   │   ├── security/
│   │   │   │   │   ├── JwtTokenProvider.java
│   │   │   │   │   ├── JwtAuthenticationFilter.java
│   │   │   │   │   └── CurrentUser.java        # 自定义注解
│   │   │   │   └── util/
│   │   │   │       └── BeanCopyUtils.java
│   │   │   │
│   │   │   ├── auth/
│   │   │   │   ├── AuthController.java         # login / register / me
│   │   │   │   ├── AuthService.java
│   │   │   │   └── dto/
│   │   │   │       ├── LoginRequest.java
│   │   │   │       └── RegisterRequest.java
│   │   │   │
│   │   │   ├── users/
│   │   │   │   ├── UserController.java
│   │   │   │   ├── UserService.java
│   │   │   │   ├── UserRepository.java
│   │   │   │   ├── entity/
│   │   │   │   │   └── User.java
│   │   │   │   └── dto/
│   │   │   │       ├── CreateUserRequest.java
│   │   │   │       └── UpdateUserRequest.java
│   │   │   │
│   │   │   └── modules/                       # ★ 业务模块（按 product-map 模块生成）
│   │   │       └── {module}/
│   │   │           ├── {Module}Controller.java
│   │   │           ├── {Module}Service.java
│   │   │           ├── {Module}Repository.java
│   │   │           ├── entity/
│   │   │           │   └── {Entity}.java
│   │   │           └── dto/
│   │   │               ├── Create{Entity}Request.java
│   │   │               ├── Update{Entity}Request.java
│   │   │               └── {Entity}Response.java
│   │   │
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       └── db/migration/                  # Flyway 迁移
│   │
│   └── test/
│       └── java/com/{group}/{artifact}/
│           ├── ApplicationTests.java
│           └── modules/
│               └── {module}/
│                   ├── {Module}ServiceTest.java
│                   └── {Module}ControllerTest.java
│
└── docker-compose.yml
```

---

## 数据模型生成规则

### Entity 映射

```
product-map entity → JPA entity

映射规则:
  entity.name (snake_case) → PascalCase class + snake_case 表名（@Table）
  entity.fields → 字段 + @Column 注解
  entity.relations → @ManyToOne / @OneToMany / @ManyToMany
  entity.states → enum

示例:
  product-map entity: {
    name: "order",
    fields: ["id", "user_id", "total_amount", "status", "note"],
    states: ["pending", "confirmed", "shipped", "completed", "cancelled"]
  }
  →
  @Entity
  @Table(name = "orders")
  public class Order {

      @Id
      @GeneratedValue(strategy = GenerationType.UUID)
      private String id;

      @ManyToOne(fetch = FetchType.LAZY, optional = false)
      @JoinColumn(name = "user_id")
      private User user;

      @Column(name = "total_amount", precision = 10, scale = 2, nullable = false)
      private BigDecimal totalAmount;

      @Enumerated(EnumType.STRING)
      @Column(name = "status", nullable = false)
      private OrderStatus status = OrderStatus.PENDING;

      @Column(name = "note", columnDefinition = "TEXT")
      private String note;

      @CreationTimestamp
      @Column(name = "created_at", updatable = false)
      private LocalDateTime createdAt;

      @UpdateTimestamp
      @Column(name = "updated_at")
      private LocalDateTime updatedAt;
  }

  public enum OrderStatus {
      PENDING, CONFIRMED, SHIPPED, COMPLETED, CANCELLED
  }
```

### 字段类型映射

| product-map 字段类型 | JPA 列类型 |
|---------------------|-----------|
| string / text | `@Column(length = 255)` — `String` |
| long_text | `@Column(columnDefinition = "TEXT")` — `String` |
| number / integer | `@Column` — `Integer` |
| decimal / money | `@Column(precision = 10, scale = 2)` — `BigDecimal` |
| boolean | `@Column` — `Boolean` |
| date | `@Column` — `LocalDate` |
| datetime | `@Column` — `LocalDateTime` |
| json | `@Column(columnDefinition = "jsonb")` + `@Type(JsonType.class)` — `Map<String,Object>` |
| enum | `@Enumerated(EnumType.STRING) @Column` — `XxxStatus` |
| image_url | `@Column(length = 500)` — `String` |
| foreign_key | `@ManyToOne + @JoinColumn` |

---

## 路由生成规则

### CRUD 端点

```
product-map task (CRUD 类型) → Spring Boot controller 路由

命名规则:
  task 对应 entity → 复数小写 kebab-case 作为路由前缀
  entity: "order" → 路由: /api/orders

标准 CRUD:
  GET    /api/{resource}          → list (分页 + 筛选)
  GET    /api/{resource}/{id}     → getById
  POST   /api/{resource}          → create
  PUT    /api/{resource}/{id}     → update
  DELETE /api/{resource}/{id}     → delete
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
task.owner_role → @PreAuthorize 注解

示例:
  task.owner_role = "admin"    → @PreAuthorize("hasRole('ADMIN')")
  task.owner_role = "merchant" → @PreAuthorize("hasRole('MERCHANT')")
```

---

## 配置文件模板

### pom.xml（核心依赖）

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.0</version>
</parent>

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-security</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springdoc</groupId>
        <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
        <version>2.3.0</version>
    </dependency>
    <dependency>
        <groupId>org.postgresql</groupId>
        <artifactId>postgresql</artifactId>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>org.flywaydb</groupId>
        <artifactId>flyway-core</artifactId>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-api</artifactId>
        <version>0.12.3</version>
    </dependency>
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

### application.yml

```yaml
spring:
  datasource:
    url: jdbc:postgresql://${DB_HOST:localhost}:${DB_PORT:5432}/${DB_NAME}
    username: ${DB_USER}
    password: ${DB_PASS}
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
  flyway:
    enabled: true

server:
  port: ${PORT:8080}
  servlet:
    context-path: /api
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | PascalCase | `OrderItem.java` |
| 类名 | PascalCase | `OrderItem` |
| 变量/属性 | camelCase | `totalAmount` |
| 数据库表名 | snake_case 复数 | `order_items` |
| 数据库列名 | snake_case | `total_amount` |
| API 路由 | kebab-case 复数 | `/api/order-items` |
| DTO 文件 | PascalCase + 动作 | `CreateOrderItemRequest.java` |
| 包目录 | 全小写 | `modules/orderitem/` |
| 常量 | UPPER_SNAKE_CASE | `MAX_PAGE_SIZE` |

---

## Batch 结构（backend 特有）

```
B1 Foundation: Entity 文件、Enum 定义、Flyway 迁移脚本、config/ + common/ 搭建
B2 API:        Controller + Service + Repository + DTO + Security 注册
B3 —:          (后端无 UI 层，跳过)
B4 Integration: Springdoc OpenAPI 文档、健康检查端点(Actuator)、错误码统一、DTO 校验
B5 Testing:     单元测试 (Service + Repository) + API 集成测试 (@SpringBootTest + MockMvc)
```
