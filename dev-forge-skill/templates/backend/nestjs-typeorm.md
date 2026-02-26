# NestJS + TypeORM + PostgreSQL 模板

> 后端参考模板。project-scaffold 读取此文件，按规则生成 NestJS 后端脚手架。

---

## 目录结构

```
apps/{sub-project-name}/
├── package.json
├── tsconfig.json
├── tsconfig.build.json
├── nest-cli.json
├── .env.example
├── .eslintrc.js
│
├── src/
│   ├── main.ts                         # 应用入口
│   ├── app.module.ts                   # 根模块
│   ├── app.controller.ts              # 健康检查
│   │
│   ├── config/
│   │   ├── database.config.ts          # TypeORM 配置
│   │   ├── auth.config.ts              # JWT / Auth 配置
│   │   └── app.config.ts               # 应用通用配置
│   │
│   ├── common/
│   │   ├── decorators/
│   │   │   ├── roles.decorator.ts      # @Roles() 装饰器
│   │   │   └── current-user.decorator.ts
│   │   ├── guards/
│   │   │   ├── jwt-auth.guard.ts       # JWT 守卫
│   │   │   └── roles.guard.ts          # 角色守卫
│   │   ├── interceptors/
│   │   │   ├── transform.interceptor.ts # 统一响应格式
│   │   │   └── logging.interceptor.ts
│   │   ├── filters/
│   │   │   └── http-exception.filter.ts # 统一异常处理
│   │   ├── pipes/
│   │   │   └── validation.pipe.ts       # 全局验证管道
│   │   └── dto/
│   │       ├── pagination.dto.ts        # 分页请求/响应 DTO
│   │       └── api-response.dto.ts      # 统一响应 DTO
│   │
│   ├── auth/
│   │   ├── auth.module.ts
│   │   ├── auth.controller.ts          # login / register / me
│   │   ├── auth.service.ts
│   │   ├── strategies/
│   │   │   └── jwt.strategy.ts
│   │   └── dto/
│   │       ├── login.dto.ts
│   │       └── register.dto.ts
│   │
│   ├── users/
│   │   ├── users.module.ts
│   │   ├── users.controller.ts
│   │   ├── users.service.ts
│   │   ├── entities/
│   │   │   └── user.entity.ts
│   │   └── dto/
│   │       ├── create-user.dto.ts
│   │       └── update-user.dto.ts
│   │
│   └── modules/                        # ★ 业务模块（按 product-map 模块生成）
│       └── {module-name}/
│           ├── {module-name}.module.ts
│           ├── {module-name}.controller.ts
│           ├── {module-name}.service.ts
│           ├── entities/
│           │   └── {entity-name}.entity.ts
│           └── dto/
│               ├── create-{entity-name}.dto.ts
│               ├── update-{entity-name}.dto.ts
│               └── query-{entity-name}.dto.ts
│
├── test/
│   ├── jest-e2e.json
│   └── app.e2e-spec.ts
│
└── migrations/                          # TypeORM 迁移
```

---

## 数据模型生成规则

### Entity 映射

```
product-map entity → TypeORM entity

映射规则:
  entity.name (snake_case) → PascalCase class + snake_case 表名
  entity.fields → @Column 装饰器
  entity.relations → @ManyToOne / @OneToMany / @ManyToMany
  entity.states → enum

示例:
  product-map entity: {
    name: "order",
    fields: ["id", "user_id", "total_amount", "status", "note"],
    states: ["pending", "confirmed", "shipped", "completed", "cancelled"]
  }
  →
  @Entity('orders')
  export class Order {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @ManyToOne(() => User, { nullable: false })
    @JoinColumn({ name: 'user_id' })
    user: User;

    @Column({ name: 'user_id' })
    userId: string;

    @Column({ type: 'decimal', precision: 10, scale: 2 })
    totalAmount: number;

    @Column({ type: 'enum', enum: OrderStatus, default: OrderStatus.PENDING })
    status: OrderStatus;

    @Column({ type: 'text', nullable: true })
    note: string;

    @CreateDateColumn({ name: 'created_at' })
    createdAt: Date;

    @UpdateDateColumn({ name: 'updated_at' })
    updatedAt: Date;
  }

  export enum OrderStatus {
    PENDING = 'pending',
    CONFIRMED = 'confirmed',
    SHIPPED = 'shipped',
    COMPLETED = 'completed',
    CANCELLED = 'cancelled',
  }
```

### 字段类型映射

| product-map 字段类型 | TypeORM 列类型 |
|---------------------|----------------|
| string / text | `@Column({ type: 'varchar', length: 255 })` |
| long_text | `@Column({ type: 'text' })` |
| number / integer | `@Column({ type: 'int' })` |
| decimal / money | `@Column({ type: 'decimal', precision: 10, scale: 2 })` |
| boolean | `@Column({ type: 'boolean', default: false })` |
| date | `@Column({ type: 'date' })` |
| datetime | `@Column({ type: 'timestamp' })` |
| json | `@Column({ type: 'jsonb', nullable: true })` |
| enum | `@Column({ type: 'enum', enum: XxxStatus })` |
| image_url | `@Column({ type: 'varchar', length: 500, nullable: true })` |
| foreign_key | `@ManyToOne() + @JoinColumn() + @Column()` |

---

## 路由生成规则

### CRUD 端点

```
product-map task (CRUD 类型) → NestJS controller 路由

命名规则:
  task 对应 entity → 复数小写 kebab-case 作为路由前缀
  entity: "order" → 路由: /api/orders

标准 CRUD:
  GET    /api/{resource}          → findAll (分页 + 筛选)
  GET    /api/{resource}/:id      → findOne
  POST   /api/{resource}          → create
  PUT    /api/{resource}/:id      → update
  DELETE /api/{resource}/:id      → remove
```

### 非 CRUD 端点

```
task 包含状态变更 / 审批 / 特殊操作 → 自定义路由

示例:
  task: "审批订单" → PATCH /api/orders/:id/approve
  task: "批量导出" → POST /api/orders/export
  task: "统计报表" → GET  /api/orders/stats
```

### 角色守卫

```
task.owner_role → @Roles() 装饰器

示例:
  task.owner_role = "admin" → @Roles('admin')
  task.owner_role = "merchant" → @Roles('merchant')
```

---

## 配置文件模板

### package.json

```json
{
  "name": "{sub-project-name}",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "build": "nest build",
    "dev": "nest start --watch",
    "start": "nest start",
    "start:prod": "node dist/main",
    "lint": "eslint \"{src,test}/**/*.ts\"",
    "test": "jest",
    "test:e2e": "jest --config ./test/jest-e2e.json",
    "migration:generate": "typeorm migration:generate -d src/config/database.config.ts",
    "migration:run": "typeorm migration:run -d src/config/database.config.ts"
  },
  "dependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/platform-express": "^10.0.0",
    "@nestjs/typeorm": "^10.0.0",
    "@nestjs/passport": "^10.0.0",
    "@nestjs/jwt": "^10.0.0",
    "@nestjs/swagger": "^7.0.0",
    "typeorm": "^0.3.0",
    "pg": "^8.11.0",
    "passport": "^0.7.0",
    "passport-jwt": "^4.0.0",
    "bcrypt": "^5.1.0",
    "class-validator": "^0.14.0",
    "class-transformer": "^0.5.0"
  },
  "devDependencies": {
    "@nestjs/cli": "^10.0.0",
    "@nestjs/testing": "^10.0.0",
    "@types/jest": "^29.5.0",
    "@types/node": "^20.0.0",
    "jest": "^29.5.0",
    "ts-jest": "^29.1.0",
    "typescript": "^5.3.0"
  }
}
```

### nest-cli.json

```json
{
  "$schema": "https://json.schemastore.org/nest-cli",
  "collection": "@nestjs/schematics",
  "sourceRoot": "src",
  "compilerOptions": {
    "deleteOutDir": true
  }
}
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | kebab-case | `order-item.entity.ts` |
| 类名 | PascalCase | `OrderItem` |
| 变量/属性 | camelCase | `totalAmount` |
| 数据库表名 | snake_case 复数 | `order_items` |
| 数据库列名 | snake_case | `total_amount` |
| API 路由 | kebab-case 复数 | `/api/order-items` |
| DTO 文件 | kebab-case + 动作 | `create-order-item.dto.ts` |
| 模块目录 | kebab-case | `modules/order-items/` |

---

## Batch 结构（backend 特有）

```
B1 Foundation: 类型定义、Entity 文件、数据库迁移、config/ + common/ 搭建
B2 API:        Controller + Service + DTO + 中间件注册
B3 —:          (后端无 UI 层，跳过)
B4 Integration: Swagger 文档生成、健康检查端点、错误码统一、API 客户端导出
B5 Testing:     单元测试 (entity + service) + API 集成测试 (supertest)
```
