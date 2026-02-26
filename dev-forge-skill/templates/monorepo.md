# Monorepo 根配置模板

> 本模板定义 monorepo 根目录的标准结构。project-scaffold 据此生成 workspace 配置。

---

## 目录结构

```
{project-name}/
├── package.json                    # workspace 根配置
├── {workspace-config}              # pnpm-workspace.yaml / turbo.json / nx.json
├── tsconfig.base.json              # 共享 TS 配置（JS/TS 项目）
├── .eslintrc.js                    # 共享 lint 配置
├── .prettierrc                     # 共享格式化配置
├── .gitignore
├── .env.example                    # 环境变量示例
│
├── apps/                           # ★ 子项目层
│   ├── {backend-app}/              # 后端服务
│   ├── {admin-app}/                # 管理后台
│   ├── {customer-app}/             # 消费者端
│   ├── {mobile-app}/               # 移动端
│   └── mock-server/                # Mock 后端
│
├── packages/                       # ★ 共享包
│   ├── shared-types/               # 跨端共享类型定义
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── src/
│   │       ├── index.ts
│   │       ├── entities.ts         # product-map entity → TS interface
│   │       ├── api-types.ts        # API 请求/响应类型
│   │       └── enums.ts            # 状态枚举
│   ├── api-client/                 # 生成的 API 客户端（B4 阶段生成）
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── src/
│   │       ├── index.ts
│   │       ├── client.ts           # HTTP 客户端封装
│   │       └── endpoints/          # 按模块分的端点调用
│   └── ui-kit/                     # 共享 UI 组件（可选）
│       ├── package.json
│       └── src/
│
├── e2e/                            # ★ 跨端 E2E 测试
│   ├── playwright.config.ts
│   ├── scenarios/                  # e2e-verify 生成的场景
│   └── fixtures/
│
└── .allforai/                      # 产品设计 + 锻造产物（不进 apps/）
```

---

## Workspace 配置（按工具）

### pnpm workspace

**pnpm-workspace.yaml**:
```yaml
packages:
  - "apps/*"
  - "packages/*"
  - "e2e"
```

**根 package.json**:
```json
{
  "name": "{project-name}",
  "private": true,
  "scripts": {
    "dev": "pnpm -r --parallel run dev",
    "build": "pnpm -r run build",
    "lint": "pnpm -r run lint",
    "test": "pnpm -r run test",
    "mock": "pnpm --filter mock-server run start",
    "e2e": "pnpm --filter e2e run test"
  },
  "devDependencies": {
    "typescript": "^5.3.0"
  },
  "engines": {
    "node": ">=18.0.0",
    "pnpm": ">=8.0.0"
  }
}
```

### Turborepo

**turbo.json**:
```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": [".env"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "build/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {},
    "test": {
      "dependsOn": ["build"]
    }
  }
}
```

### Nx

**nx.json**:
```json
{
  "$schema": "https://raw.githubusercontent.com/nrwl/nx/master/packages/nx/schemas/nx-schema.json",
  "targetDefaults": {
    "build": {
      "dependsOn": ["^build"],
      "cache": true
    },
    "lint": { "cache": true },
    "test": { "cache": true }
  },
  "defaultBase": "main"
}
```

### 手动管理（混合语言）

JS/TS 部分使用 pnpm workspace，非 JS 后端在 `apps/` 下独立管理：

```
apps/
├── api-backend/          # Go / Java / Python — 独立 Makefile / build.gradle / setup.py
├── merchant-admin/       # JS/TS — pnpm workspace 管理
└── customer-web/         # JS/TS — pnpm workspace 管理
```

**pnpm-workspace.yaml**（仅包含 JS 子项目）:
```yaml
packages:
  - "apps/merchant-admin"
  - "apps/customer-web"
  - "apps/mock-server"
  - "packages/*"
  - "e2e"
```

---

## 共享类型生成规则

### entities.ts（来自 product-map）

```
product-map entity → TypeScript interface

命名规则:
  entity.name (snake_case) → PascalCase interface
  entity.fields → interface fields
  entity.states → enum

示例:
  product-map: { name: "order", fields: ["id", "user_id", "total", "status"] }
  →
  export interface Order {
    id: string;
    userId: string;
    total: number;
    status: OrderStatus;
  }
  export enum OrderStatus {
    PENDING = "pending",
    CONFIRMED = "confirmed",
    ...
  }
```

### api-types.ts（来自 design.md API 端点）

```
每个 API 端点 → Request + Response 类型

示例:
  POST /api/orders → CreateOrderRequest + CreateOrderResponse
  GET /api/orders → ListOrdersParams + ListOrdersResponse
  GET /api/orders/:id → GetOrderResponse
  PUT /api/orders/:id → UpdateOrderRequest + UpdateOrderResponse
  DELETE /api/orders/:id → DeleteOrderResponse
```

---

## tsconfig.base.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "paths": {
      "@shared/types": ["./packages/shared-types/src"],
      "@shared/api-client": ["./packages/api-client/src"],
      "@shared/ui-kit": ["./packages/ui-kit/src"]
    }
  }
}
```

---

## .env.example

```bash
# === 通用 ===
NODE_ENV=development

# === 后端 ===
DATABASE_URL=postgresql://user:password@localhost:5432/{project-name}
JWT_SECRET=change-me-in-production
API_PORT={backend-port}

# === Mock Server ===
MOCK_PORT=4000

# === 前端 ===
NEXT_PUBLIC_API_URL=http://localhost:${API_PORT}
# 开发阶段连 mock-server:
# NEXT_PUBLIC_API_URL=http://localhost:${MOCK_PORT}
```

---

## 生成规则

1. **project-scaffold 读取 project-manifest.json** → 提取 monorepo_tool + 子项目列表
2. **创建根配置** → 按 monorepo_tool 选择对应配置模板
3. **创建 packages/shared-types/** → 从 product-map entities 生成类型
4. **创建 apps/{sub-project}/** → 每个子项目按其 stack template 生成
5. **创建 apps/mock-server/** → 按 mock-server.md 模板生成
6. **创建 e2e/** → Playwright 基础配置
7. **写入 .env.example** → 汇总所有子项目的端口和环境变量
