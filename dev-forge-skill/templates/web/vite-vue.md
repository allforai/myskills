# Vite + Vue 3 + Tailwind (SPA) 模板

> Web 前端参考模板。支持 admin / web-customer 两种子项目类型。仅 CSR 渲染，轻量级 Nuxt 替代方案。

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
│   ├── main.ts                          # Vue 入口 (createApp + 插件注册)
│   ├── App.vue                          # 根组件
│   ├── style.css                        # Tailwind 入口 + 自定义 CSS
│   │
│   ├── router/                          # Vue Router
│   │   ├── index.ts                     # createRouter 定义
│   │   └── guards.ts                    # 路由守卫 (beforeEach)
│   │
│   ├── views/                           # 页面组件
│   │   ├── auth/
│   │   │   ├── LoginView.vue
│   │   │   └── RegisterView.vue
│   │   ├── HomeView.vue
│   │   ├── NotFoundView.vue
│   │   └── {module}/                    # ★ 业务页面（按 experience-map 生成）
│   │       ├── {Entity}ListView.vue     # 列表页
│   │       ├── {Entity}DetailView.vue   # 详情页
│   │       ├── {Entity}CreateView.vue   # 创建页
│   │       └── {Entity}EditView.vue     # 编辑页
│   │
│   ├── components/
│   │   ├── ui/                          # 基础 UI 组件
│   │   │   ├── UButton.vue
│   │   │   ├── UInput.vue
│   │   │   ├── UDataTable.vue
│   │   │   ├── UForm.vue
│   │   │   ├── UModal.vue
│   │   │   ├── UToast.vue
│   │   │   └── UPagination.vue
│   │   ├── layout/                      # 布局组件
│   │   │   ├── AppSidebar.vue
│   │   │   ├── AppHeader.vue
│   │   │   ├── AppBreadcrumb.vue
│   │   │   └── AppFooter.vue
│   │   └── features/                    # ★ 业务组件（按模块生成）
│   │       └── {module}/
│   │           ├── {Entity}List.vue
│   │           ├── {Entity}Form.vue
│   │           ├── {Entity}Detail.vue
│   │           └── {Entity}Card.vue
│   │
│   ├── composables/                     # 组合式函数
│   │   ├── useAuth.ts
│   │   ├── useApi.ts                    # API 调用 composable
│   │   ├── usePagination.ts
│   │   └── useToast.ts
│   │
│   ├── lib/                             # 工具库
│   │   ├── api-client.ts               # HTTP 客户端
│   │   ├── auth.ts                      # Token 存储 (localStorage)
│   │   ├── utils.ts
│   │   └── constants.ts
│   │
│   ├── stores/                          # Pinia 状态管理
│   │   ├── auth.ts
│   │   └── app.ts
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
- 侧边栏导航（AppSidebar.vue）+ 面包屑（AppBreadcrumb.vue）
- 数据表格组件（UDataTable.vue）支持排序/筛选/分页
- 表单组件 — 基于 vee-validate + zod 验证
- 图表组件（UChart.vue）— 接入 Dashboard
- 路由守卫 — beforeEach 按角色过滤菜单项和路由

**页面生成规则**:
```
experience-map 每个 screen → 1 组页面:
  列表页: /views/{module}/{Entity}ListView.vue      — UDataTable 组件
  详情页: /views/{module}/{Entity}DetailView.vue    — 只读展示
  创建页: /views/{module}/{Entity}CreateView.vue    — 表单
  编辑页: /views/{module}/{Entity}EditView.vue      — 预填表单
```

**权限管理**:
```typescript
// router/guards.ts
export function setupGuards(router: Router) {
  router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();

    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      return next({ name: 'login', query: { redirect: to.fullPath } });
    }

    const requiredRoles = to.meta.roles as string[] | undefined;
    if (requiredRoles && !requiredRoles.includes(authStore.user.role)) {
      return next({ name: 'forbidden' });
    }

    next();
  });
}

// router/index.ts — 路由配置
{
  path: '/orders',
  component: () => import('@/views/orders/OrderListView.vue'),
  meta: { requiresAuth: true, roles: ['admin', 'manager'] },
}
```

```vue
<!-- components/layout/AppSidebar.vue — 菜单级权限 -->
<script setup lang="ts">
const authStore = useAuthStore();
const visibleMenuItems = computed(() =>
  allMenuItems.filter(item => item.roles.includes(authStore.user.role))
);
</script>
```

### web-customer（消费者端）

**特有文件/配置**:
- `@unhead/vue` 设置 `<title>` / `<meta>`
- 图片懒加载（`loading="lazy"`）
- 性能优化（defineAsyncComponent 路由级代码分割）
- 响应式布局（移动端友好）

**页面生成规则**:
```
experience-map screen → SPA 页面 (CSR):
  首页:      /views/HomeView.vue                — 静态内容 + 推荐列表
  列表页:    /views/{module}/{Entity}ListView.vue — 带搜索/筛选
  详情页:    /views/{module}/{Entity}DetailView.vue — 详情展示
  功能页:    /views/{module}/{Entity}View.vue    — 需登录的功能
```

**Meta 配置**:
```vue
<!-- views/{module}/{Entity}DetailView.vue -->
<script setup lang="ts">
import { useHead } from '@unhead/vue';

const { data } = useApi(`/api/{module}/${route.params.id}`);

useHead({
  title: () => data.value?.title,
  meta: [
    { name: 'description', content: () => data.value?.description },
  ],
});
</script>
```

---

## 数据模型 → 组件映射

### 列表组件

```
entity.fields → UDataTable columns

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
entity.fields → Form fields (vee-validate + zod)

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
    "build": "vue-tsc -b && vite build",
    "preview": "vite preview --port {port}",
    "lint": "eslint .",
    "test": "vitest",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0",
    "pinia": "^2.2.0",
    "@unhead/vue": "^1.11.0",
    "vee-validate": "^4.13.0",
    "@vee-validate/zod": "^4.13.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0",
    "vite": "^5.4.0",
    "vue-tsc": "^2.1.0",
    "vitest": "^2.0.0"
  }
}
```

### vite.config.ts

```typescript
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
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
| 页面文件 | PascalCase + View | `OrderListView.vue` |
| 组件文件 | PascalCase | `UDataTable.vue` |
| composables | camelCase + use | `useAuth.ts` |
| stores | kebab-case | `auth.ts` |
| 路由路径 | kebab-case | `/order-items` |
| CSS 类名 | Tailwind utility | `class="flex items-center"` |
| 类型文件 | kebab-case | `api-types.ts` |

---

## Batch 结构（前端）

### admin

```
B1 Foundation: 类型定义、API 客户端封装、Vue Router 配置 + 守卫、MainLayout 骨架、Pinia stores
B2 —:          (无独立 API，跳过)
B3 UI:         UDataTable 组件、UForm 组件 (vee-validate + zod)、页面组件、图表组件
B4 Integration: 连接真实 API（替换 VITE_API_URL）、路由守卫 (beforeEach)、Pinia 状态管理
B5 Testing:     组件测试 (Vitest + Vue Test Utils) + Playwright E2E (桌面视口)
```

### web-customer

```
B1 Foundation: 类型定义、API 客户端封装、Vue Router 配置 (lazy routes)、@unhead/vue meta
B2 —:          (无独立 API，跳过)
B3 UI:         页面组件 (带 useHead meta)、列表/详情/功能页
B4 Integration: 连接真实 API、Analytics 集成、响应式布局优化
B5 Testing:     Playwright E2E (桌面+移动视口) + Lighthouse 性能检测
```
