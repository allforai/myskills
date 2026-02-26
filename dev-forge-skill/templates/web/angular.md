# Angular + Angular Material 模板

> Web 前端参考模板。支持 admin / web-customer 两种子项目类型。仅 CSR 渲染。

---

## 目录结构（通用骨架）

```
apps/{sub-project-name}/
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.spec.json
├── angular.json
├── .env.example
│
├── public/
│   ├── favicon.ico
│   └── images/
│
├── src/
│   ├── main.ts                          # 入口文件
│   ├── index.html
│   ├── styles.scss                      # 全局样式 (Angular Material 主题)
│   │
│   ├── app/
│   │   ├── app.module.ts                # 根模块
│   │   ├── app-routing.module.ts        # 根路由 (lazy-load 子模块)
│   │   ├── app.component.ts
│   │   │
│   │   ├── core/                        # 核心模块 (单例)
│   │   │   ├── core.module.ts
│   │   │   ├── guards/
│   │   │   │   └── auth.guard.ts        # 路由守卫
│   │   │   ├── interceptors/
│   │   │   │   ├── auth.interceptor.ts  # 添加 Bearer token
│   │   │   │   └── error.interceptor.ts # 全局错误处理
│   │   │   ├── services/
│   │   │   │   ├── api.service.ts       # HTTP 客户端
│   │   │   │   ├── auth.service.ts      # 认证服务
│   │   │   │   └── toast.service.ts     # 通知服务
│   │   │   └── models/
│   │   │       └── index.ts             # 接口/类型定义 (引用 shared-types)
│   │   │
│   │   ├── shared/                      # 共享模块
│   │   │   ├── shared.module.ts         # 导出 Material 模块 + 通用组件
│   │   │   ├── components/
│   │   │   │   ├── data-table/          # 数据表格 (mat-table 封装)
│   │   │   │   ├── form-field/          # 表单字段组件
│   │   │   │   ├── confirm-dialog/      # 确认对话框
│   │   │   │   ├── page-header/         # 页面标题 + 操作按钮
│   │   │   │   └── loading-spinner/
│   │   │   ├── pipes/
│   │   │   │   ├── relative-time.pipe.ts
│   │   │   │   └── currency-format.pipe.ts
│   │   │   └── directives/
│   │   │       └── role.directive.ts    # *appRole="'admin'"
│   │   │
│   │   ├── layout/                      # 布局模块
│   │   │   ├── layout.module.ts
│   │   │   ├── layout.component.ts      # 包含 sidenav + toolbar + content
│   │   │   ├── sidebar/
│   │   │   │   └── sidebar.component.ts # mat-sidenav 菜单
│   │   │   ├── header/
│   │   │   │   └── header.component.ts  # mat-toolbar
│   │   │   └── breadcrumb/
│   │   │       └── breadcrumb.component.ts
│   │   │
│   │   ├── auth/                        # 认证模块 (lazy-loaded)
│   │   │   ├── auth.module.ts
│   │   │   ├── auth-routing.module.ts
│   │   │   ├── login/
│   │   │   │   └── login.component.ts
│   │   │   └── register/
│   │   │       └── register.component.ts
│   │   │
│   │   └── features/                    # ★ 业务功能模块 (每模块 lazy-loaded)
│   │       └── {module}/
│   │           ├── {module}.module.ts
│   │           ├── {module}-routing.module.ts
│   │           ├── services/
│   │           │   └── {module}.service.ts   # 模块专属 API 调用
│   │           ├── components/
│   │           │   ├── {entity}-list/
│   │           │   │   └── {entity}-list.component.ts
│   │           │   ├── {entity}-detail/
│   │           │   │   └── {entity}-detail.component.ts
│   │           │   ├── {entity}-form/
│   │           │   │   └── {entity}-form.component.ts
│   │           │   └── {entity}-card/
│   │           │       └── {entity}-card.component.ts
│   │           └── models/
│   │               └── {entity}.model.ts
│   │
│   ├── environments/
│   │   ├── environment.ts               # 开发环境
│   │   └── environment.prod.ts          # 生产环境
│   │
│   └── assets/
│       ├── icons/
│       └── images/
│
└── tests/
    └── e2e/
```

---

## 子项目类型差异

### admin（管理后台）

**特有文件/配置**:
- mat-sidenav 导航（sidebar.component.ts）+ 面包屑
- mat-table 数据表格 — 支持排序 (matSort)、筛选、分页 (mat-paginator)
- Reactive Forms 表单生成 — 支持动态字段
- Dashboard 图表组件（ngx-charts 或 chart.js）
- 路由守卫（auth.guard.ts）— 按角色过滤菜单和路由

**页面生成规则**:
```
screen-map 每个 screen → 1 个 feature module:
  列表页: /{module}/             — mat-table + MatSort + MatPaginator
  详情页: /{module}/:id          — 只读展示 (mat-card)
  创建页: /{module}/new          — Reactive Form
  编辑页: /{module}/:id/edit     — 预填 Reactive Form
```

**权限管理**:
```typescript
// core/guards/auth.guard.ts
@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot): boolean {
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/login']);
      return false;
    }
    const requiredRoles = route.data['roles'] as string[];
    if (requiredRoles && !requiredRoles.includes(this.authService.currentUser.role)) {
      return false;
    }
    return true;
  }
}

// app-routing.module.ts — lazy-load + 守卫
{ path: 'orders', loadChildren: () => import('./features/orders/orders.module').then(m => m.OrdersModule),
  canActivate: [AuthGuard], data: { roles: ['admin', 'manager'] } },
```

### web-customer（消费者端）

**特有文件/配置**:
- `<title>` 和 `<meta>` 动态设置（Angular `Title` / `Meta` service）
- 页面级 SEO（受限于 CSR，需配合预渲染工具或 SSR 方案）
- 图片懒加载（`loading="lazy"`）
- 性能优化（OnPush 变更检测 + trackBy）

**页面生成规则**:
```
screen-map screen → Angular 页面 (CSR):
  首页:      /                     — 静态内容 + 推荐列表
  列表页:    /{module}             — 带搜索/筛选的列表 (virtual scroll)
  详情页:    /{module}/:slug       — 详情展示 (mat-card)
  功能页:    /{module}             — 需登录的功能
```

**Meta 配置**:
```typescript
// features/{module}/components/{entity}-detail/{entity}-detail.component.ts
export class EntityDetailComponent implements OnInit {
  constructor(private title: Title, private meta: Meta) {}

  ngOnInit() {
    this.title.setTitle(this.entity.name);
    this.meta.updateTag({ name: 'description', content: this.entity.description });
    this.meta.updateTag({ property: 'og:title', content: this.entity.name });
    this.meta.updateTag({ property: 'og:image', content: this.entity.coverImage });
  }
}
```

---

## 数据模型 → 组件映射

### 列表组件 (mat-table)

```
entity.fields → mat-table 列定义

映射规则:
  string → 文本列 (matColumnDef)
  number/decimal → 右对齐数字列
  enum/status → mat-chip 状态标签列
  datetime → relative-time pipe
  image_url → <img> 缩略图列
  foreign_key → 关联实体名称列 (异步 pipe)
```

### 表单组件 (Reactive Forms)

```
entity.fields → FormGroup controls

映射规则:
  string(短) → mat-input (matInput)
  string(长)/text → mat-input (textarea, matInput)
  number → mat-input (type="number")
  decimal/money → mat-input + currency-format pipe
  boolean → mat-slide-toggle
  enum → mat-select + mat-option
  date → mat-datepicker
  datetime → mat-datepicker + 时间输入
  image_url → 自定义 ImageUpload 组件
  foreign_key → mat-autocomplete (异步搜索)

验证规则 (来自 constraints):
  required → Validators.required
  max_length → Validators.maxLength(n)
  min/max → Validators.min(n) / Validators.max(n)
  pattern → Validators.pattern(regex)
```

---

## API 客户端

```typescript
// core/services/api.service.ts
import { HttpClient } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = environment.apiUrl || 'http://localhost:4000';

  constructor(private http: HttpClient) {}

  get<T>(path: string) {
    return this.http.get<T>(`${this.baseUrl}${path}`);
  }

  post<T>(path: string, body: unknown) {
    return this.http.post<T>(`${this.baseUrl}${path}`, body);
  }

  put<T>(path: string, body: unknown) {
    return this.http.put<T>(`${this.baseUrl}${path}`, body);
  }

  delete<T>(path: string) {
    return this.http.delete<T>(`${this.baseUrl}${path}`);
  }
}

// core/interceptors/auth.interceptor.ts
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = this.authService.getToken();
    if (token) {
      req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
    }
    return next.handle(req);
  }
}
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
    "ng": "ng",
    "dev": "ng serve --port {port}",
    "build": "ng build --configuration production",
    "test": "ng test",
    "test:e2e": "playwright test",
    "lint": "ng lint"
  },
  "dependencies": {
    "@angular/animations": "^18.0.0",
    "@angular/cdk": "^18.0.0",
    "@angular/common": "^18.0.0",
    "@angular/compiler": "^18.0.0",
    "@angular/core": "^18.0.0",
    "@angular/forms": "^18.0.0",
    "@angular/material": "^18.0.0",
    "@angular/platform-browser": "^18.0.0",
    "@angular/platform-browser-dynamic": "^18.0.0",
    "@angular/router": "^18.0.0",
    "rxjs": "~7.8.0",
    "zone.js": "~0.14.0"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^18.0.0",
    "@angular/cli": "^18.0.0",
    "@angular/compiler-cli": "^18.0.0",
    "typescript": "~5.4.0",
    "karma": "~6.4.0",
    "karma-jasmine": "~5.1.0"
  }
}
```

### angular.json (关键片段)

```json
{
  "projects": {
    "{sub-project-name}": {
      "architect": {
        "build": {
          "options": {
            "outputPath": "dist/{sub-project-name}",
            "styles": ["src/styles.scss"],
            "fileReplacements": []
          },
          "configurations": {
            "production": {
              "budgets": [
                { "type": "initial", "maximumWarning": "500kb", "maximumError": "1mb" }
              ],
              "fileReplacements": [{
                "replace": "src/environments/environment.ts",
                "with": "src/environments/environment.prod.ts"
              }]
            }
          }
        },
        "serve": {
          "options": { "port": "{port}" }
        }
      }
    }
  }
}
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | kebab-case + type 后缀 | `order-list.component.ts` |
| 组件类名 | PascalCase + Component | `OrderListComponent` |
| 服务类名 | PascalCase + Service | `OrderService` |
| 模块类名 | PascalCase + Module | `OrdersModule` |
| pipe 类名 | PascalCase + Pipe | `RelativeTimePipe` |
| 路由路径 | kebab-case | `order-items/` |
| 选择器 | kebab-case + app- 前缀 | `app-order-list` |

---

## Batch 结构（前端）

### admin

```
B1 Foundation: 接口/类型定义、CoreModule (ApiService, AuthService, interceptors)、LayoutModule 骨架、路由配置 (lazy-load)
B2 —:          (无独立 API，跳过)
B3 UI:         SharedModule (mat-table 封装, form-field)、各 feature module 页面组件
B4 Integration: 连接真实 API（替换 environment.apiUrl）、AuthGuard 路由守卫、RxJS 状态管理
B5 Testing:     Jasmine/Karma 组件测试 + Playwright E2E (桌面视口)
```

### web-customer

```
B1 Foundation: 接口/类型定义、CoreModule、Title/Meta SEO 服务、路由配置
B2 —:          (无独立 API，跳过)
B3 UI:         页面组件 (带 Title/Meta 设置)、列表/详情/功能页
B4 Integration: 连接真实 API、Analytics 集成、图片懒加载优化
B5 Testing:     Playwright E2E (桌面+移动视口) + Lighthouse 性能检测
```
