# Nuxt 3 + Tailwind 模板

> Web 前端参考模板。支持 admin / web-customer / web-mobile 三种子项目类型。

---

## 目录结构（通用骨架）

```
apps/{sub-project-name}/
├── package.json
├── tsconfig.json
├── nuxt.config.ts
├── tailwind.config.ts
├── .env.example
│
├── public/
│   ├── favicon.ico
│   └── images/
│
├── server/                             # Nitro 服务端 (API routes / middleware)
│   ├── api/                            # 服务端 API 路由（BFF 代理，可选）
│   │   └── [...].ts
│   ├── middleware/
│   │   └── auth.ts                     # 服务端认证中间件
│   └── utils/
│       └── api-proxy.ts
│
├── pages/                              # 文件路由
│   ├── index.vue                       # 首页
│   ├── login.vue                       # 登录页
│   └── {module}/                       # ★ 业务模块（按 screen-map 生成）
│       ├── index.vue                   # 列表页
│       ├── [id].vue                    # 详情页
│       ├── new.vue                     # 创建页
│       └── [id]/edit.vue              # 编辑页
│
├── layouts/
│   ├── default.vue                     # 默认布局（导航 + 内容区）
│   ├── auth.vue                        # 认证布局（居中卡片）
│   └── blank.vue                       # 空白布局
│
├── components/
│   ├── ui/                             # 基础 UI 组件
│   │   ├── UButton.vue
│   │   ├── UInput.vue
│   │   ├── UDataTable.vue
│   │   ├── UForm.vue
│   │   ├── UModal.vue
│   │   ├── UToast.vue
│   │   └── UPagination.vue
│   ├── layout/                         # 布局组件
│   │   ├── LayoutSidebar.vue
│   │   ├── LayoutHeader.vue
│   │   ├── LayoutBreadcrumb.vue
│   │   └── LayoutFooter.vue
│   └── features/                       # ★ 业务组件（按模块生成）
│       └── {module}/
│           ├── {Entity}List.vue
│           ├── {Entity}Form.vue
│           ├── {Entity}Detail.vue
│           └── {Entity}Card.vue
│
├── composables/                        # 组合式函数
│   ├── useAuth.ts
│   ├── useApiClient.ts                 # 对 useFetch 的封装
│   ├── usePagination.ts
│   └── useToast.ts
│
├── stores/                             # Pinia 状态管理
│   ├── auth.ts
│   └── app.ts
│
├── types/                              # 类型定义（引用 shared-types）
│   └── index.ts
│
├── utils/                              # 工具函数
│   ├── constants.ts
│   └── format.ts
│
├── assets/
│   └── css/
│       └── main.css                    # Tailwind 入口 + 自定义 CSS
│
├── middleware/                          # 客户端路由中间件
│   └── auth.ts                         # 认证路由守卫
│
└── tests/
    ├── components/
    └── e2e/
```

---

## 子项目类型差异

### admin（管理后台）

**特有文件/配置**:
- 侧边栏导航（LayoutSidebar.vue）+ 面包屑（LayoutBreadcrumb.vue）
- 数据表格组件（UDataTable.vue）支持排序/筛选/分页
- 表单生成器组件（UFormBuilder.vue）支持动态字段
- 图表组件（UChart.vue）— 接入 Dashboard
- 路由中间件 — 按角色过滤菜单项

**页面生成规则**:
```
screen-map 每个 screen → 1 组页面:
  列表页: /pages/{module}/index.vue      — UDataTable 组件
  详情页: /pages/{module}/[id].vue       — 只读展示
  创建页: /pages/{module}/new.vue        — 表单
  编辑页: /pages/{module}/[id]/edit.vue  — 预填表单
```

**权限管理**:
```vue
<!-- middleware/auth.ts — 路由级权限 -->
<script setup>
export default defineNuxtRouteMiddleware((to) => {
  const { loggedIn, user } = useAuth();
  if (!loggedIn.value && to.path !== '/login') {
    return navigateTo('/login');
  }
});
</script>

<!-- components/layout/LayoutSidebar.vue — 菜单级权限 -->
<script setup>
const { user } = useAuth();
const visibleMenuItems = computed(() =>
  allMenuItems.filter(item => item.roles.includes(user.value.role))
);
</script>
```

**渲染模式**: CSR 为主（`ssr: false`）或按需 SSR。

### web-customer（消费者端）

**特有文件/配置**:
- SEO meta 组件（`useHead()` / `useSeoMeta()` in each page）
- SSR / SSG 策略配置（`routeRules` in `nuxt.config.ts`）
- 结构化数据（JSON-LD via `useHead()`）
- 图片优化（`<NuxtImg>` + `<NuxtPicture>` via `@nuxt/image`）
- 性能预算（`nuxt.config.ts` 中 `nitro.prerender` + `routeRules`）

**页面生成规则**:
```
screen-map screen → SSR/SSG 页面:
  首页:      /pages/index.vue              — SSG (routeRules: prerender)
  列表页:    /pages/{module}/index.vue     — SSR (带搜索/筛选)
  详情页:    /pages/{module}/[slug].vue    — ISR (routeRules: swr)
  功能页:    /pages/{module}/index.vue     — CSR (需登录的功能)
```

**SEO 配置**:
```vue
<!-- pages/{module}/[slug].vue -->
<script setup>
const route = useRoute();
const { data } = await useAsyncData(`${route.params.slug}`, () =>
  $fetch(`/api/{module}/${route.params.slug}`)
);
useSeoMeta({
  title: data.value.title,
  description: data.value.description,
  ogImage: data.value.coverImage,
});
useHead({
  script: [{ type: 'application/ld+json', innerHTML: JSON.stringify(jsonLd) }],
});
</script>
```

**渲染模式**: SSR + ISR（`routeRules` 按路由配置）。

### web-mobile（移动网页 / PWA）

**特有文件/配置**:
- PWA 模块（`@vite-pwa/nuxt`）— manifest + Service Worker
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
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@vite-pwa/nuxt'],
  pwa: {
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
  },
});
```

**渲染模式**: SSR + PWA 离线缓存。

---

## 数据模型 → 组件映射

### 列表组件

```
entity.fields → UDataTable columns / 卡片字段

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
  string(短) → UInput 组件
  string(长)/text → UInput (type="textarea") 组件
  number → UInput (type="number") 组件
  decimal/money → 金额输入组件 (带货币符号)
  boolean → Toggle/Checkbox 组件
  enum → USelect/RadioGroup 组件
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
// composables/useApiClient.ts
export const useApiClient = () => {
  const config = useRuntimeConfig();
  const BASE_URL = config.public.apiUrl || 'http://localhost:4000';
  const authStore = useAuthStore();

  const request = async <T>(method: string, path: string, body?: unknown): Promise<T> => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (authStore.token) headers['Authorization'] = `Bearer ${authStore.token}`;

    const data = await $fetch<T>(`${BASE_URL}${path}`, {
      method: method as any,
      headers,
      body: body ? body : undefined,
    });

    return data;
  };

  return {
    get: <T>(path: string) => request<T>('GET', path),
    post: <T>(path: string, body: unknown) => request<T>('POST', path, body),
    put: <T>(path: string, body: unknown) => request<T>('PUT', path, body),
    del: <T>(path: string) => request<T>('DELETE', path),
  };
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
    "dev": "nuxt dev --port {port}",
    "build": "nuxt build",
    "generate": "nuxt generate",
    "preview": "nuxt preview --port {port}",
    "lint": "eslint .",
    "test": "vitest",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "nuxt": "^3.13.0",
    "vue": "^3.5.0",
    "@pinia/nuxt": "^0.5.0",
    "pinia": "^2.2.0"
  },
  "devDependencies": {
    "@nuxt/image": "^1.8.0",
    "@nuxtjs/tailwindcss": "^6.12.0",
    "@vite-pwa/nuxt": "^0.10.0",
    "typescript": "^5.3.0",
    "vitest": "^2.0.0"
  }
}
```

### nuxt.config.ts

```typescript
export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@nuxt/image',
  ],
  runtimeConfig: {
    public: {
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:4000',
    },
  },
  // web-customer: SSR + ISR 路由规则
  // routeRules: {
  //   '/': { prerender: true },
  //   '/{module}/**': { swr: 3600 },
  // },
  // admin: 关闭 SSR
  // ssr: false,
});
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 页面文件 | kebab-case | `order-items/index.vue` |
| 组件文件 | PascalCase | `UDataTable.vue` |
| composables | camelCase + use | `useAuth.ts` |
| stores | kebab-case | `auth.ts` |
| 路由目录 | kebab-case | `order-items/` |
| CSS 类名 | Tailwind utility | `class="flex items-center"` |
| 类型文件 | kebab-case | `api-types.ts` |

---

## Batch 结构（前端）

### admin

```
B1 Foundation: 类型定义、API 客户端封装（composable）、default layout + 侧边栏骨架、Pinia store
B2 —:          (无独立 API，跳过)
B3 UI:         UDataTable 组件、UForm 组件、页面组件、图表组件
B4 Integration: 连接真实 API（替换 mock-server base URL）、路由守卫中间件、Pinia 状态管理
B5 Testing:     组件测试 (Vitest + Vue Test Utils) + Playwright E2E (桌面视口)
```

### web-customer

```
B1 Foundation: 类型定义、API 客户端封装、SEO meta composable、routeRules SSR/ISR 配置
B2 —:          (无独立 API，跳过)
B3 UI:         页面组件 (带 useSeoMeta)、列表/详情/功能页
B4 Integration: 连接真实 API、结构化数据 (JSON-LD)、Analytics 集成
B5 Testing:     Playwright E2E (桌面+移动视口) + Lighthouse 性能检测
```

### web-mobile

```
B1 Foundation: 类型定义、PWA 配置 (@vite-pwa/nuxt)、Service Worker、移动布局骨架
B2 —:          (无独立 API，跳过)
B3 UI:         移动组件 (下拉刷新/无限滚动/手势)、页面组件、离线状态页
B4 Integration: 连接真实 API、离线缓存同步、推送集成
B5 Testing:     Playwright 移动视口测试 + Lighthouse 移动性能检测
```
