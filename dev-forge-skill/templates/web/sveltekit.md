# SvelteKit + Tailwind 模板

> Web 前端参考模板。支持 admin / web-customer / web-mobile 三种子项目类型。

---

## 目录结构（通用骨架）

```
apps/{sub-project-name}/
├── package.json
├── tsconfig.json
├── svelte.config.js
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── .env.example
│
├── static/
│   ├── favicon.ico
│   └── images/
│
├── src/
│   ├── app.html                         # HTML 模板
│   ├── app.css                          # Tailwind 入口 + 自定义 CSS
│   ├── hooks.server.ts                  # 服务端钩子 (认证/日志)
│   │
│   ├── routes/                          # 文件路由
│   │   ├── +layout.svelte               # 根 layout
│   │   ├── +layout.server.ts            # 根 layout 数据加载
│   │   ├── +page.svelte                 # 首页
│   │   ├── +error.svelte                # 全局错误页
│   │   ├── (auth)/                      # 认证相关页面组
│   │   │   ├── login/+page.svelte
│   │   │   ├── login/+page.server.ts
│   │   │   └── +layout.svelte
│   │   └── (main)/                      # 主功能区（需要登录）
│   │       ├── +layout.svelte           # 带侧边栏/导航的布局
│   │       ├── +layout.server.ts        # 认证检查
│   │       └── {module}/               # ★ 业务模块（按 screen-map 生成）
│   │           ├── +page.svelte         # 列表页
│   │           ├── +page.server.ts      # 列表数据加载
│   │           ├── [id]/+page.svelte    # 详情页
│   │           ├── [id]/+page.server.ts
│   │           ├── new/+page.svelte     # 创建页
│   │           ├── new/+page.server.ts  # form action 处理
│   │           └── [id]/edit/+page.svelte
│   │
│   ├── lib/                             # $lib 别名目录
│   │   ├── components/
│   │   │   ├── ui/                      # 基础 UI 组件
│   │   │   │   ├── Button.svelte
│   │   │   │   ├── Input.svelte
│   │   │   │   ├── DataTable.svelte
│   │   │   │   ├── Form.svelte
│   │   │   │   ├── Modal.svelte
│   │   │   │   ├── Toast.svelte
│   │   │   │   └── Pagination.svelte
│   │   │   ├── layout/                  # 布局组件
│   │   │   │   ├── Sidebar.svelte
│   │   │   │   ├── Header.svelte
│   │   │   │   ├── Breadcrumb.svelte
│   │   │   │   └── Footer.svelte
│   │   │   └── features/               # ★ 业务组件（按模块生成）
│   │   │       └── {module}/
│   │   │           ├── {entity}-list.svelte
│   │   │           ├── {entity}-form.svelte
│   │   │           ├── {entity}-detail.svelte
│   │   │           └── {entity}-card.svelte
│   │   │
│   │   ├── stores/                      # Svelte stores
│   │   │   ├── auth.ts
│   │   │   └── toast.ts
│   │   │
│   │   ├── api/                         # API 客户端
│   │   │   └── client.ts
│   │   │
│   │   ├── utils/                       # 工具函数
│   │   │   ├── constants.ts
│   │   │   └── format.ts
│   │   │
│   │   └── types/                       # 类型定义（引用 shared-types）
│   │       └── index.ts
│   │
│   └── params/                          # 路由参数匹配器
│       └── id.ts
│
└── tests/
    ├── components/
    └── e2e/
```

---

## 子项目类型差异

### admin（管理后台）

**特有文件/配置**:
- 侧边栏导航（Sidebar.svelte）+ 面包屑（Breadcrumb.svelte）
- 数据表格组件（DataTable.svelte）支持排序/筛选/分页
- 表单组件 — 利用 SvelteKit form actions 处理提交
- 图表组件（Chart.svelte）— 接入 Dashboard
- hooks.server.ts — 按角色过滤路由访问

**页面生成规则**:
```
screen-map 每个 screen → 1 组页面:
  列表页: /routes/(main)/{module}/+page.svelte          — DataTable 组件
  详情页: /routes/(main)/{module}/[id]/+page.svelte     — 只读展示
  创建页: /routes/(main)/{module}/new/+page.svelte      — 表单 (form action)
  编辑页: /routes/(main)/{module}/[id]/edit/+page.svelte — 预填表单
```

**权限管理**:
```typescript
// src/hooks.server.ts — 路由级权限
export const handle: Handle = async ({ event, resolve }) => {
  const token = event.cookies.get('token');
  if (!token && !event.url.pathname.startsWith('/login')) {
    throw redirect(302, '/login');
  }
  if (token) {
    event.locals.user = verifyToken(token);
  }
  return resolve(event);
};

// routes/(main)/+layout.server.ts — 菜单级权限
export const load: LayoutServerLoad = async ({ locals }) => {
  return {
    user: locals.user,
    menuItems: allMenuItems.filter(item =>
      item.roles.includes(locals.user.role)
    ),
  };
};
```

### web-customer（消费者端）

**特有文件/配置**:
- SEO meta（`<svelte:head>` in each +page.svelte）
- SSR / SSG 策略（`+page.server.ts` load 函数 + `prerender` 导出）
- 结构化数据（JSON-LD via `<svelte:head>`）
- 图片优化（`<enhanced:img>` via `@sveltejs/enhanced-img`）
- 性能预算（adapter 配置 + prerender 选项）

**页面生成规则**:
```
screen-map screen → SSR/SSG 页面:
  首页:      /routes/+page.svelte              — SSG (export const prerender = true)
  列表页:    /routes/{module}/+page.svelte     — SSR (带搜索/筛选)
  详情页:    /routes/{module}/[slug]/+page.svelte — SSG + entries()
  功能页:    /routes/{module}/+page.svelte     — CSR (export const ssr = false)
```

**SEO 配置**:
```svelte
<!-- routes/{module}/[slug]/+page.svelte -->
<script lang="ts">
  export let data;
</script>

<svelte:head>
  <title>{data.entity.title}</title>
  <meta name="description" content={data.entity.description} />
  <meta property="og:title" content={data.entity.title} />
  <meta property="og:image" content={data.entity.coverImage} />
  {@html `<script type="application/ld+json">${JSON.stringify(data.jsonLd)}</script>`}
</svelte:head>
```

### web-mobile（移动网页 / PWA）

**特有文件/配置**:
- PWA 配置（`@vite-pwa/sveltekit`）— manifest + Service Worker
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
```typescript
// vite.config.ts
import { SvelteKitPWA } from '@vite-pwa/sveltekit';

export default defineConfig({
  plugins: [
    sveltekit(),
    SvelteKitPWA({
      manifest: {
        name: '{project-name}',
        short_name: '{short-name}',
        start_url: '/',
        display: 'standalone',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
      workbox: { navigateFallback: '/' },
    }),
  ],
});
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
entity.fields → Form fields (利用 SvelteKit form actions)

映射规则:
  string(短) → Input 组件
  string(长)/text → Textarea 组件
  number → Input (type="number") 组件
  decimal/money → 金额输入组件 (带货币符号)
  boolean → Toggle/Checkbox 组件
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
// src/lib/api/client.ts
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:4000';

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

**服务端 API 调用（+page.server.ts）**:
```typescript
// routes/(main)/{module}/+page.server.ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals, fetch }) => {
  const res = await fetch(`${BASE_URL}/api/{module}`, {
    headers: { Authorization: `Bearer ${locals.token}` },
  });
  return { items: await res.json() };
};
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
    "dev": "vite dev --port {port}",
    "build": "vite build",
    "preview": "vite preview --port {port}",
    "lint": "eslint .",
    "test": "vitest",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "@sveltejs/kit": "^2.7.0",
    "svelte": "^4.2.0"
  },
  "devDependencies": {
    "@sveltejs/adapter-auto": "^3.3.0",
    "@sveltejs/vite-plugin-svelte": "^4.0.0",
    "@vite-pwa/sveltekit": "^0.6.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0",
    "vite": "^5.4.0",
    "vitest": "^2.0.0"
  }
}
```

### svelte.config.js

```javascript
import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(),
    alias: {
      $components: 'src/lib/components',
      $stores: 'src/lib/stores',
      $api: 'src/lib/api',
    },
  },
};

export default config;
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 路由文件 | +page/+layout 约定 | `+page.svelte` |
| 组件文件 | PascalCase | `DataTable.svelte` |
| stores | kebab-case | `auth.ts` |
| 路由目录 | kebab-case | `order-items/` |
| 服务端文件 | +page.server.ts | `+page.server.ts` |
| CSS 类名 | Tailwind utility | `class="flex items-center"` |
| 类型文件 | kebab-case | `api-types.ts` |

---

## Batch 结构（前端）

### admin

```
B1 Foundation: 类型定义、API 客户端、hooks.server.ts 认证、根 layout + 侧边栏骨架、stores
B2 —:          (无独立 API，跳过)
B3 UI:         DataTable 组件、Form 组件 (form actions)、页面组件、图表组件
B4 Integration: 连接真实 API（替换 VITE_API_URL）、路由守卫、store 状态管理
B5 Testing:     组件测试 (Vitest + @testing-library/svelte) + Playwright E2E (桌面视口)
```

### web-customer

```
B1 Foundation: 类型定义、API 客户端、SEO meta 模式、prerender/SSR 配置
B2 —:          (无独立 API，跳过)
B3 UI:         页面组件 (带 <svelte:head> SEO)、列表/详情/功能页
B4 Integration: 连接真实 API、结构化数据 (JSON-LD)、Analytics 集成
B5 Testing:     Playwright E2E (桌面+移动视口) + Lighthouse 性能检测
```

### web-mobile

```
B1 Foundation: 类型定义、PWA 配置 (@vite-pwa/sveltekit)、Service Worker、移动布局骨架
B2 —:          (无独立 API，跳过)
B3 UI:         移动组件 (下拉刷新/无限滚动/手势)、页面组件、离线状态页
B4 Integration: 连接真实 API、离线缓存同步、推送集成
B5 Testing:     Playwright 移动视口测试 + Lighthouse 移动性能检测
```
