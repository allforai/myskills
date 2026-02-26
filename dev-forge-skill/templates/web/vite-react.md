# Vite + React + Tailwind (SPA) 模板

> Web 前端参考模板。支持 admin / web-customer 两种子项目类型。仅 CSR 渲染，轻量级 Next.js 替代方案。

---

## 目录结构（通用骨架）

```
apps/{sub-project-name}/
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── index.html                          # Vite 入口 HTML
├── .env.example
│
├── public/
│   ├── favicon.ico
│   └── images/
│
├── src/
│   ├── main.tsx                         # React 入口
│   ├── App.tsx                          # 根组件 (Router + Providers)
│   ├── index.css                        # Tailwind 入口 + 自定义 CSS
│   │
│   ├── routes/                          # 路由配置
│   │   ├── index.tsx                    # createBrowserRouter 定义
│   │   ├── layouts/
│   │   │   ├── RootLayout.tsx           # 根 layout
│   │   │   ├── AuthLayout.tsx           # 认证布局 (居中卡片)
│   │   │   └── MainLayout.tsx           # 主布局 (侧边栏+内容区)
│   │   └── guards/
│   │       └── AuthGuard.tsx            # 路由守卫 (检查 token)
│   │
│   ├── pages/                           # 页面组件
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── HomePage.tsx
│   │   ├── NotFoundPage.tsx
│   │   └── {module}/                    # ★ 业务页面（按 screen-map 生成）
│   │       ├── {Entity}ListPage.tsx     # 列表页
│   │       ├── {Entity}DetailPage.tsx   # 详情页
│   │       ├── {Entity}CreatePage.tsx   # 创建页
│   │       └── {Entity}EditPage.tsx     # 编辑页
│   │
│   ├── components/
│   │   ├── ui/                          # 基础 UI 组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── Form.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── Pagination.tsx
│   │   ├── layout/                      # 布局组件
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Breadcrumb.tsx
│   │   │   └── Footer.tsx
│   │   └── features/                    # ★ 业务组件（按模块生成）
│   │       └── {module}/
│   │           ├── {Entity}List.tsx
│   │           ├── {Entity}Form.tsx
│   │           ├── {Entity}Detail.tsx
│   │           └── {Entity}Card.tsx
│   │
│   ├── hooks/                           # 自定义 hooks
│   │   ├── useAuth.ts
│   │   ├── useApi.ts                    # API 调用 hook (React Query 封装)
│   │   ├── usePagination.ts
│   │   └── useToast.ts
│   │
│   ├── lib/                             # 工具库
│   │   ├── api-client.ts               # HTTP 客户端
│   │   ├── auth.ts                      # Token 存储 (localStorage)
│   │   ├── utils.ts
│   │   └── constants.ts
│   │
│   ├── stores/                          # 状态管理 (Zustand)
│   │   └── auth-store.ts
│   │
│   └── types/                           # 类型定义（引用 shared-types）
│       └── index.ts
│
└── tests/
    ├── components/
    └── e2e/
```

---

## 子项目类型差异

### admin（管理后台）

**特有文件/配置**:
- 侧边栏导航（Sidebar.tsx）+ 面包屑（Breadcrumb.tsx）
- 数据表格组件（DataTable.tsx）— 基于 @tanstack/react-table，支持排序/筛选/分页
- 表单组件 — 基于 react-hook-form + zod 验证
- 图表组件（Chart.tsx）— 接入 Dashboard (recharts)
- AuthGuard — 按角色过滤菜单项和路由

**页面生成规则**:
```
screen-map 每个 screen → 1 组页面:
  列表页: /pages/{module}/{Entity}ListPage.tsx      — DataTable 组件
  详情页: /pages/{module}/{Entity}DetailPage.tsx    — 只读展示
  创建页: /pages/{module}/{Entity}CreatePage.tsx    — 表单
  编辑页: /pages/{module}/{Entity}EditPage.tsx      — 预填表单
```

**权限管理**:
```tsx
// routes/guards/AuthGuard.tsx
export function AuthGuard({ children, roles }: { children: ReactNode; roles?: string[] }) {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/403" replace />;
  }
  return <>{children}</>;
}

// routes/index.tsx — 路由配置
{
  path: '/',
  element: <AuthGuard><MainLayout /></AuthGuard>,
  children: [
    { path: 'orders', element: <OrderListPage /> },
    { path: 'orders/:id', element: <OrderDetailPage /> },
  ],
}
```

### web-customer（消费者端）

**特有文件/配置**:
- react-helmet-async 设置 `<title>` / `<meta>`
- 图片懒加载（`loading="lazy"`）
- 性能优化（React.lazy + Suspense 路由级代码分割）
- 响应式布局（移动端友好）

**页面生成规则**:
```
screen-map screen → SPA 页面 (CSR):
  首页:      /pages/HomePage.tsx             — 静态内容 + 推荐列表
  列表页:    /pages/{module}/{Entity}ListPage.tsx — 带搜索/筛选
  详情页:    /pages/{module}/{Entity}DetailPage.tsx — 详情展示
  功能页:    /pages/{module}/{Entity}Page.tsx — 需登录的功能
```

**Meta 配置**:
```tsx
// pages/{module}/{Entity}DetailPage.tsx
import { Helmet } from 'react-helmet-async';

export function EntityDetailPage() {
  const { data } = useApi(`/api/{module}/${id}`);
  return (
    <>
      <Helmet>
        <title>{data.title}</title>
        <meta name="description" content={data.description} />
      </Helmet>
      {/* ... */}
    </>
  );
}
```

---

## 数据模型 → 组件映射

### 列表组件

```
entity.fields → DataTable columns (@tanstack/react-table)

映射规则:
  string → 文本列
  number/decimal → 右对齐数字列
  enum/status → 状态标签列 (Badge 组件)
  datetime → 相对时间列 ("3 小时前")
  image_url → 缩略图列
  foreign_key → 关联实体名称列
```

### 表单组件

```
entity.fields → Form fields (react-hook-form + zod)

映射规则:
  string(短) → Input 组件
  string(长)/text → Textarea 组件
  number → Input (type="number") 组件
  decimal/money → 金额输入组件 (带货币符号)
  boolean → Switch/Checkbox 组件
  enum → Select/RadioGroup 组件
  date → DatePicker 组件
  datetime → DateTimePicker 组件
  image_url → ImageUpload 组件
  foreign_key → SearchableSelect/Combobox 组件

验证规则 (来自 constraints → zod schema):
  required → z.string().min(1)
  max_length → z.string().max(n)
  min/max → z.number().min(n).max(n)
  pattern → z.string().regex(regex)
```

---

## API 客户端

```typescript
// src/lib/api-client.ts
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:4000';

class ApiClient {
  private token: string | null = null;

  setToken(token: string) { this.token = token; localStorage.setItem('token', token); }
  clearToken() { this.token = null; localStorage.removeItem('token'); }

  constructor() {
    this.token = localStorage.getItem('token');
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ message: res.statusText }));
      throw new ApiError(res.status, error.message || res.statusText);
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  }

  get<T>(path: string) { return this.request<T>('GET', path); }
  post<T>(path: string, body: unknown) { return this.request<T>('POST', path, body); }
  put<T>(path: string, body: unknown) { return this.request<T>('PUT', path, body); }
  delete<T>(path: string) { return this.request<T>('DELETE', path); }
}

export const api = new ApiClient();
```

---

## 配置文件模板

### package.json

```json
{
  "name": "{sub-project-name}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --port {port}",
    "build": "tsc -b && vite build",
    "preview": "vite preview --port {port}",
    "lint": "eslint .",
    "test": "vitest",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "react-hook-form": "^7.53.0",
    "@hookform/resolvers": "^3.9.0",
    "zod": "^3.23.0",
    "@tanstack/react-query": "^5.56.0",
    "@tanstack/react-table": "^8.20.0",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0",
    "vite": "^5.4.0",
    "vitest": "^2.0.0"
  }
}
```

### vite.config.ts

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:4000',
        changeOrigin: true,
      },
    },
  },
});
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 页面文件 | PascalCase + Page | `OrderListPage.tsx` |
| 组件文件 | PascalCase | `DataTable.tsx` |
| 组件名 | PascalCase | `DataTable` |
| hooks | camelCase + use- | `useAuth` |
| 路由路径 | kebab-case | `/order-items` |
| CSS 类名 | Tailwind utility | `className="flex items-center"` |
| 类型文件 | kebab-case | `api-types.ts` |
| stores | kebab-case + -store | `auth-store.ts` |

---

## Batch 结构（前端）

### admin

```
B1 Foundation: 类型定义、API 客户端封装、React Router 配置、MainLayout 骨架、Zustand stores
B2 —:          (无独立 API，跳过)
B3 UI:         DataTable 组件 (@tanstack/react-table)、Form 组件 (react-hook-form)、页面组件、图表组件
B4 Integration: 连接真实 API（替换 VITE_API_URL）、AuthGuard 路由守卫、React Query 缓存
B5 Testing:     组件测试 (Vitest + React Testing Library) + Playwright E2E (桌面视口)
```

### web-customer

```
B1 Foundation: 类型定义、API 客户端封装、React Router 配置 (lazy routes)、react-helmet-async
B2 —:          (无独立 API，跳过)
B3 UI:         页面组件 (带 Helmet meta)、列表/详情/功能页
B4 Integration: 连接真实 API、Analytics 集成、响应式布局优化
B5 Testing:     Playwright E2E (桌面+移动视口) + Lighthouse 性能检测
```
