# Next.js 14 (App Router) + Tailwind 模板

> Web 前端参考模板。支持 admin / web-customer / web-mobile 三种子项目类型。

---

## 目录结构（通用骨架）

```
apps/{sub-project-name}/
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── postcss.config.js
├── .env.local.example
│
├── public/
│   ├── favicon.ico
│   └── images/
│
├── src/
│   ├── app/                            # App Router
│   │   ├── layout.tsx                  # 根 layout
│   │   ├── page.tsx                    # 首页
│   │   ├── loading.tsx                 # 全局 loading
│   │   ├── error.tsx                   # 全局错误边界
│   │   ├── not-found.tsx               # 404 页面
│   │   ├── (auth)/                     # 认证相关页面组
│   │   │   ├── login/page.tsx
│   │   │   └── layout.tsx
│   │   └── (main)/                     # 主功能区（需要登录）
│   │       ├── layout.tsx              # 带侧边栏/导航的布局
│   │       └── {module}/              # ★ 业务模块（按 screen-map 生成）
│   │           ├── page.tsx            # 列表页
│   │           ├── [id]/page.tsx       # 详情页
│   │           ├── new/page.tsx        # 创建页
│   │           └── [id]/edit/page.tsx  # 编辑页
│   │
│   ├── components/
│   │   ├── ui/                         # 基础 UI 组件
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── data-table.tsx
│   │   │   ├── form.tsx
│   │   │   ├── modal.tsx
│   │   │   ├── toast.tsx
│   │   │   └── pagination.tsx
│   │   ├── layout/                     # 布局组件
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   ├── breadcrumb.tsx
│   │   │   └── footer.tsx
│   │   └── features/                   # ★ 业务组件（按模块生成）
│   │       └── {module}/
│   │           ├── {entity}-list.tsx
│   │           ├── {entity}-form.tsx
│   │           ├── {entity}-detail.tsx
│   │           └── {entity}-card.tsx
│   │
│   ├── hooks/                          # 自定义 hooks
│   │   ├── use-auth.ts
│   │   ├── use-api.ts                  # API 调用 hook
│   │   ├── use-pagination.ts
│   │   └── use-toast.ts
│   │
│   ├── lib/                            # 工具库
│   │   ├── api-client.ts               # HTTP 客户端（连 mock-server 或真实后端）
│   │   ├── auth.ts                     # 认证工具
│   │   ├── utils.ts                    # 通用工具
│   │   └── constants.ts
│   │
│   ├── stores/                         # 状态管理（可选）
│   │   └── auth-store.ts
│   │
│   ├── types/                          # 类型定义（引用 shared-types）
│   │   └── index.ts
│   │
│   └── styles/
│       └── globals.css                 # Tailwind 入口 + 自定义 CSS
│
└── tests/
    ├── components/
    └── e2e/
```

---

## 子项目类型差异

### admin（管理后台）

**特有文件/配置**:
- 侧边栏导航（sidebar.tsx）+ 面包屑（breadcrumb.tsx）
- 数据表格组件（data-table.tsx）支持排序/筛选/分页
- 表单生成器组件（form-builder.tsx）支持动态字段
- 图表组件（chart.tsx）— 接入 Dashboard
- 路由守卫 — 按角色过滤菜单项

**页面生成规则**:
```
screen-map 每个 screen → 1 组页面:
  列表页: /app/(main)/{module}/page.tsx       — DataTable 组件
  详情页: /app/(main)/{module}/[id]/page.tsx  — 只读展示
  创建页: /app/(main)/{module}/new/page.tsx   — 表单
  编辑页: /app/(main)/{module}/[id]/edit/page.tsx — 预填表单
```

**权限管理**:
```tsx
// middleware.ts — 路由级权限
export function middleware(request: NextRequest) {
  const token = request.cookies.get('token');
  if (!token && !request.nextUrl.pathname.startsWith('/login')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
}

// components/layout/sidebar.tsx — 菜单级权限
const menuItems = allMenuItems.filter(item =>
  item.roles.includes(currentUser.role)
);
```

### web-customer（消费者端）

**特有文件/配置**:
- SEO meta 组件（`metadata` export in each page）
- SSR / SSG 策略配置（`generateStaticParams` / `revalidate`）
- 结构化数据（JSON-LD）
- 图片优化（`next/image` + `sizes` + `priority`）
- 性能预算（`next.config.js` 中 `experimental.optimizeCss`）

**页面生成规则**:
```
screen-map screen → SSR/SSG 页面:
  首页:      /app/page.tsx              — SSG + revalidate
  列表页:    /app/{module}/page.tsx     — SSR (带搜索/筛选)
  详情页:    /app/{module}/[slug]/page.tsx — SSG + generateStaticParams
  功能页:    /app/{module}/page.tsx     — CSR (需登录的功能)
```

**SEO 配置**:
```tsx
// app/{module}/[slug]/page.tsx
export async function generateMetadata({ params }): Promise<Metadata> {
  const data = await fetchData(params.slug);
  return {
    title: data.title,
    description: data.description,
    openGraph: { images: [data.coverImage] },
  };
}
```

### web-mobile（移动网页 / PWA）

**特有文件/配置**:
- `manifest.json`（PWA 清单）
- `sw.js`（Service Worker — 可用 next-pwa 插件）
- 移动优先布局（底部导航 + 全屏卡片）
- 触屏交互组件（下拉刷新、无限滚动、左滑操作）
- `viewport` meta 配置

**页面生成规则**:
```
screen-map screen → 移动优先页面:
  - 底部 Tab 导航（最多 5 个主入口）
  - 列表使用虚拟滚动或无限加载
  - 详情页全屏展示
  - 表单分步骤（避免长表单）
```

**PWA 配置**:
```json
// public/manifest.json
{
  "name": "{project-name}",
  "short_name": "{short-name}",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#ffffff",
  "background_color": "#ffffff",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

---

## 数据模型 → 组件映射

### 列表组件

```
entity.fields → DataTable columns

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
entity.fields → Form fields

映射规则:
  string(短) → Input 组件
  string(长)/text → Textarea 组件
  number → NumberInput 组件
  decimal/money → 金额输入组件 (带货币符号)
  boolean → Switch/Checkbox 组件
  enum → Select/RadioGroup 组件
  date → DatePicker 组件
  datetime → DateTimePicker 组件
  image_url → ImageUpload 组件
  foreign_key → SearchableSelect/Combobox 组件

验证规则 (来自 constraints):
  required → required 属性
  max_length → maxLength 验证
  min/max → 范围验证
  pattern → regex 验证
```

---

## API 客户端

```typescript
// src/lib/api-client.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

class ApiClient {
  private token: string | null = null;

  setToken(token: string) { this.token = token; }
  clearToken() { this.token = null; }

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
  "scripts": {
    "dev": "next dev --port {port}",
    "build": "next build",
    "start": "next start --port {port}",
    "lint": "next lint",
    "test": "jest",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0"
  }
}
```

### next.config.js

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**' },
    ],
  },
  // web-customer: 启用性能优化
  // experimental: { optimizeCss: true },
};
module.exports = nextConfig;
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | kebab-case | `data-table.tsx` |
| 组件名 | PascalCase | `DataTable` |
| hooks | camelCase + use- | `useAuth` |
| 路由目录 | kebab-case | `order-items/` |
| CSS 类名 | Tailwind utility | `className="flex items-center"` |
| 类型文件 | kebab-case | `api-types.ts` |

---

## Batch 结构（前端）

### admin

```
B1 Foundation: 类型定义、API 客户端封装、根 layout + 侧边栏骨架、路由配置
B2 —:          (无独立 API，跳过)
B3 UI:         DataTable 组件、Form 组件、页面组件、图表组件
B4 Integration: 连接真实 API（替换 mock-server base URL）、路由守卫、状态管理
B5 Testing:     组件测试 (Jest + RTL) + Playwright E2E (桌面视口)
```

### web-customer

```
B1 Foundation: 类型定义、API 客户端封装、SEO meta 组件、SSR/SSG 基础配置
B2 —:          (无独立 API，跳过)
B3 UI:         页面组件 (带 SSR metadata)、列表/详情/功能页
B4 Integration: 连接真实 API、结构化数据 (JSON-LD)、Analytics 集成
B5 Testing:     Playwright E2E (桌面+移动视口) + Lighthouse 性能检测
```

### web-mobile

```
B1 Foundation: 类型定义、PWA 配置、Service Worker、移动布局骨架
B2 —:          (无独立 API，跳过)
B3 UI:         移动组件 (下拉刷新/无限滚动/手势)、页面组件、离线状态页
B4 Integration: 连接真实 API、离线缓存同步、推送集成
B5 Testing:     Playwright 移动视口测试 + Lighthouse 移动性能检测
```
