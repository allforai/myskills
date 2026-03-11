## Phase 0: 项目分析

> 先理解项目，再做验证。这是最关键的一步。

### 0.1 识别技术栈

执行以下命令来判断项目类型：

```bash
# 检查 package.json 确定前端框架
cat package.json | jq '.dependencies, .devDependencies' 2>/dev/null

# 检查是否为 monorepo
ls -la packages/ apps/ 2>/dev/null

# 检查路由配置文件位置
find . -maxdepth 5 -type f \( \
  -name "router.*" -o -name "routes.*" -o \
  -name "*.routes.*" -o -name "routing.module.*" \
  -o -name "next.config.*" -o -name "nuxt.config.*" \
  -o -name "app.config.*" \
\) 2>/dev/null | head -30

# 检查 API 路由
find . -maxdepth 5 -type f -path "*/api/*" -name "*.ts" -o -name "*.js" 2>/dev/null | head -30

# 检查菜单/导航配置
grep -rl "menu\|sidebar\|navigation\|nav" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.vue" --include="*.json" -l 2>/dev/null | head -20
```

### 0.2 识别模块类型

将项目中的模块分为以下几类，以确定各自的 CRUD 完整性要求：

| 模块类型 | 描述 | CRUD 要求 | 示例 |
|---------|------|----------|------|
| **标准业务模块** | 核心业务实体 | 完整 CRUD (创建/读取列表/读取详情/更新/删除) | 用户管理、商品管理、订单管理 |
| **配置模块** | 系统配置 | CR(U) — 通常不需要独立删除 | 系统设置、参数配置 |
| **只读模块** | 日志/审计/报表 | R 只读（列表 + 详情/导出） | 操作日志、审计日志、统计报表 |
| **关联模块** | 依附于父模块 | 在父模块内操作，不需要独立入口 | 订单项、评论回复 |
| **工作流模块** | 有状态流转 | CRUD + 状态操作（审批/驳回等） | 审批流、工单 |
| **认证模块** | 登录/注册 | 专用流程，不套用 CRUD | 登录、注册、找回密码 |
| **跨端协作模块** | CRUD 分布在多个客户端 | 按当前端的职责判定，见 0.3 节 | 用户反馈(App创建+后台管理)、UGC内容 |

### 0.3 多端架构感知 (Multi-Client Architecture)

> **核心概念**：一个业务模块的完整 CRUD 可能分布在多个客户端上，每个客户端只承担一部分职责。验证时必须以"当前客户端应承担的职责"为基准，而不是盲目要求完整 CRUD。

#### 架构类型

首先识别项目属于哪种多端架构：

| 架构类型 | 描述 | 示例 |
|---------|------|------|
| **单前端 + 单后端** | 最简单，直接验证完整 CRUD | 一个 Admin 后台 |
| **多前端 + 单后端** | 多个前端共享一个 API 后端，按角色分工 | Admin + 商户 + 客户 H5 + 客户 App |
| **多前端 + 多后端(BFF)** | 每个前端有自己的 BFF 层 | Admin→admin-api, App→app-api, 共享 core-api |
| **微前端** | 多个子应用组合成一个大应用 | qiankun/Module Federation 架构 |

#### 多前端角色模型

在多前端架构中，每个前端有两个维度的定位：

1. **角色 (role)** — 决定能做什么操作（Admin/商户/客户）
2. **平台 (platform)** — 决定怎么做和做的范围（Web/H5/App/小程序）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           共享后端 API                                   │
└──┬──────────┬───────────┬──────────┬──────────┬──────────┬─────────────┘
   │          │           │          │          │          │
┌──▼──┐  ┌───▼───┐  ┌────▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼────┐
│Admin│  │商户后台│  │客户 Web│ │客户 H5│ │客户App│ │客户小程序│
│后台 │  │       │  │(Vue)  │ │(Vue) │ │(Flut)│ │(原生)  │
└─────┘  └───────┘  └───────┘ └──────┘ └──────┘ └───────┘
角色:超管  角色:商户   角色:客户  角色:客户  角色:客户  角色:客户
平台:web  平台:web   平台:web  平台:h5  平台:app 平台:miniprogram
                    ╰──────── 同角色 peer group ──────────╯
                    核心功能应一致，差异来自平台能力
```

**同角色的多个端构成一个 "peer group"（对等组）**，它们之间：
- **核心业务功能应该一致**（都能下单、都能查看订单、都能评价）
- **平台专属功能允许差异**（App 有推送/扫码/AR，小程序有微信支付/分享，Web 有批量操作）
- **一个端有但对等端没有的核心功能 = 大概率缺失**

#### 平台能力边界

不同平台有不同的技术能力，某些功能只在特定平台有意义：

| 平台能力 | Web (PC) | H5 (移动浏览器) | App (Flutter/RN/原生) | 小程序 |
|---------|----------|----------------|---------------------|--------|
| 文件上传/下载 | ✅ 完整 | ⚠️ 受限 | ✅ 完整 | ⚠️ 受限 |
| 批量操作 | ✅ 适合 | ❌ 屏幕小 | ❌ 屏幕小 | ❌ 屏幕小 |
| 推送通知 | ❌ | ❌ | ✅ | ✅ (订阅消息) |
| 扫码 | ❌ | ⚠️ 需调用摄像头 | ✅ | ✅ |
| 生物识别 | ❌ | ❌ | ✅ | ✅ |
| 支付 | ✅ 网页支付 | ✅ 移动支付 | ✅ 原生支付 | ✅ 微信支付 |
| AR/VR | ❌ | ❌ | ✅ | ❌ |
| 定位 | ⚠️ 精度低 | ✅ | ✅ | ✅ |
| 社交分享 | ⚠️ 链接分享 | ✅ 微信分享 | ✅ 系统分享 | ✅ 微信原生分享 |
| 离线使用 | ❌ | ❌ | ✅ | ⚠️ 有限 |
| 富文本编辑 | ✅ | ⚠️ 体验差 | ⚠️ 体验差 | ❌ |
| 复杂表格/报表 | ✅ | ❌ 不适合 | ❌ 不适合 | ❌ 不适合 |
| 键盘快捷键 | ✅ | ❌ | ❌ | ❌ |

当某个客户端缺少某功能时，需要区分：
- **平台不支持** → 正常，不报问题（如 Web 端没有扫码功能）
- **平台支持但没做** → 如果对等端有，大概率是缺失

每种角色对同一模块的 CRUD 期望不同：

| 模块 | Admin 后台 | 商户后台 | 客户 Web | 客户 H5 | 客户 App | 客户小程序 |
|------|-----------|---------|---------|---------|---------|----------|
| 商品 | CRUD+审核 | CRU(自己的) | R | R | R+AR | R |
| 订单 | RUD+退款 | R+发货 | CR+取消 | CR+取消 | CR+取消 | CR+取消 |
| 评价 | RD(审核) | R+回复 | CR | CR | CR | CR |
| 个人中心 | — | RU(自己) | RU | RU | RU+生物识别 | RU |
| 消息通知 | CRUD | R | R | R | R+推送 | R+订阅消息 |

#### 角色默认期望模板

当无法精确判断时，按角色类型给出默认期望：

```json
{
  "role_defaults": {
    "super_admin": {
      "description": "超级管理员后台，全局管理所有数据",
      "default_crud": {
        "standard":  { "C": true,  "R": true,  "U": true,  "D": true  },
        "config":    { "C": true,  "R": true,  "U": true,  "D": false },
        "readonly":  { "C": false, "R": true,  "U": false, "D": false },
        "workflow":  { "C": false, "R": true,  "U": true,  "D": true, "extra": ["审批","驳回"] }
      },
      "notes": "Admin 通常有最完整的 CRUD，但某些用户产生的数据(评价/反馈)通常不需要新增入口"
    },
    "merchant": {
      "description": "商户/租户后台，管理自己名下的数据",
      "default_crud": {
        "standard":  { "C": true,  "R": true,  "U": true,  "D": "maybe" },
        "config":    { "C": false, "R": true,  "U": true,  "D": false },
        "readonly":  { "C": false, "R": true,  "U": false, "D": false }
      },
      "notes": "商户通常能创建和编辑自己的数据，但删除权可能受限；看不到其他商户的数据",
      "scope_filter": "数据隔离：只能操作自己的数据"
    },
    "customer_web": {
      "description": "C 端用户 Web/H5 前端",
      "default_crud": {
        "standard":  { "C": "maybe", "R": true,  "U": "maybe", "D": false },
        "config":    { "C": false,   "R": false, "U": false,   "D": false },
        "readonly":  { "C": false,   "R": true,  "U": false,   "D": false }
      },
      "notes": "用户端以浏览和下单为主，创建操作限于订单/评价/反馈等用户行为数据"
    },
    "customer_app": {
      "description": "C 端用户移动 App (Flutter/RN/原生)",
      "default_crud": {
        "standard":  { "C": "maybe", "R": true,  "U": "maybe", "D": false },
        "config":    { "C": false,   "R": false, "U": false,   "D": false },
        "readonly":  { "C": false,   "R": true,  "U": false,   "D": false }
      },
      "notes": "与 customer_web 类似，但可能有推送、扫码等 App 专有功能"
    }
  }
}
```

> **`"maybe"` 表示需要根据具体模块判断**，不能一刀切。例如用户端的"订单"模块需要 Create（下单），但"商品"模块不需要 Create。

#### 检测方法

**Step 1: 识别所有前端项目**

```bash
# 检查 monorepo 中的多个前端
ls -d packages/*/  apps/*/ 2>/dev/null

# 通过目录名和 package.json 中的 name 字段识别角色
for dir in apps/*/  packages/*/; do
  if [ -f "$dir/package.json" ]; then
    name=$(cat "$dir/package.json" | jq -r '.name // empty')
    echo "$dir -> $name"
  fi
done

# 常见命名模式:
#   admin / dashboard / management   → super_admin
#   merchant / seller / vendor / shop → merchant
#   client / customer / h5 / mobile / web / wap / m → customer_web
#   app / flutter / rn              → customer_app

# 检查是否有 Flutter 项目
find . .. -maxdepth 4 -name "pubspec.yaml" 2>/dev/null

# 检查是否有小程序项目
find . .. -maxdepth 4 -name "project.config.json" 2>/dev/null

# 检查是否有 React Native 项目
find . .. -maxdepth 4 -name "react-native.config.js" 2>/dev/null

# 关键信号：多个前端指向同一个 API
grep -r "baseURL\|BASE_URL\|API_URL\|apiPrefix" \
  --include="*.ts" --include="*.js" --include="*.dart" --include="*.env*" \
  . 2>/dev/null | head -30
```

**Step 2: 识别 API 前缀分段**

很多项目通过 API 路径前缀区分不同角色的接口：

```bash
# 常见 API 前缀分段模式
# /admin/xxx    → Admin 后台专用接口
# /merchant/xxx → 商户后台专用接口
# /api/xxx      → C 端通用接口
# /app/xxx      → App 端专用接口
# /open/xxx     → 开放接口(无需登录)

# 从后端代码中提取 API 分组
grep -rn "@Controller\|@RequestMapping\|@RestController\|router\.\|app\.\(use\|get\|post\)" \
  --include="*.ts" --include="*.java" --include="*.py" --include="*.go" \
  server/ backend/ api/ 2>/dev/null | \
  grep -oP "['\"]/(admin|merchant|seller|vendor|api|app|open|client|h5|web)/[^'\"]*['\"]" | \
  sort -u

# 从 Swagger/OpenAPI 提取 tags 或 paths 分组
cat swagger.json 2>/dev/null | jq '[.paths | keys[] | split("/")[1]] | unique'
```

**Step 3: 从每个前端代码中提取实际调用的 API**

```bash
# 对每个前端分别扫描
for client_dir in apps/admin apps/merchant apps/customer-h5 ../flutter-app; do
  echo "=== $client_dir ==="

  # 提取所有 API 调用路径
  grep -rn "api/\|/admin/\|/merchant/\|/app/" \
    --include="*.ts" --include="*.tsx" --include="*.js" --include="*.dart" \
    "$client_dir" 2>/dev/null | \
    grep -oP "['\"]/?[a-z]+/[^'\"]+['\"]" | sort -u

  # 提取 HTTP 方法
  grep -rn "\.get(\|\.post(\|\.put(\|\.patch(\|\.delete(" \
    --include="*.ts" --include="*.tsx" --include="*.dart" \
    "$client_dir" 2>/dev/null | \
    grep -v "node_modules\|test" | wc -l
done
```

**Step 4: 构建跨端分工矩阵**

将所有前端的 API 调用汇总，按资源和操作生成矩阵：

```
资源        Admin后台    商户后台     客户H5     客户App
─────────────────────────────────────────────────────
orders      CRUD+退款   R+发货      CR+取消    CR+取消
products    CRUD+审核   CRU         R          R
reviews     RD(审核)    R           CR         CR
users       CRUD        R           RU(自己)   RU(自己)
merchants   CRUD        RU(自己)    —          —
coupons     CRUD        CR          R+领取     R+领取
settings    CRUD        —           —          —
```

#### 职责分工判断规则

当无法确定分工时（比如没有其他客户端的代码），按以下优先级推断：

1. **API 前缀分段**是最可靠的信号：
   - `/admin/orders` 只被 admin 前端调用 → Admin 专属
   - `/api/orders` 被所有 C 端调用 → C 端共用
   - `/merchant/orders` 只被商户端调用 → 商户专属

2. **角色默认期望**作为兜底：
   - Admin 后台默认期望完整 CRUD（用户行为数据除外）
   - 商户后台默认期望 CRU 自己的数据
   - C 端默认期望 R + 特定的 C（下单/评价/反馈）

3. **特殊操作的归属规则**：
   - **审核/审批**：通常只在 Admin 或上级角色端
   - **发货/配送**：通常在商户端
   - **下单/支付**：通常在 C 端
   - **退款**：可能在 Admin（强制退款）和 C 端（申请退款）都有
   - **导出**：通常在 Admin 和商户端，C 端少见
   - **软删除 vs 硬删除**：C 端可能有"取消"(软删除)，Admin 有"删除"(硬删除)

4. **同功能多端的情况**：
   - 客户 H5 和客户 App 通常功能高度一致
   - 如果 H5 有某功能但 App 没有（或反之），大概率是缺失而非分工

5. **不确定的一律标记为 `needs_confirmation`**，让用户确认

### 0.4 输出项目概况文件

分析完成后，生成 `validation-profile.json`：

```json
{
  "project": {
    "name": "XX电商平台",
    "architecture": "multi_frontend_single_backend",
    "api_style": "rest",
    "api_base": "https://api.example.com",
    "api_doc": "https://api.example.com/swagger",
    "is_monorepo": true
  },
  "clients": [
    {
      "id": "admin",
      "name": "Admin 管理后台",
      "role": "super_admin",
      "platform": "web",
      "peer_group": null,
      "framework": "react",
      "ui_library": "antd",
      "router": "react-router",
      "path": "apps/admin",
      "api_prefix": "/admin",
      "run_url": "http://localhost:3000",
      "validate": true,
      "validate_method": "playwright",
      "auth": {
        "method": "form",
        "login_url": "/login",
        "credentials": { "username": "superadmin", "password": "xxx" }
      }
    },
    {
      "id": "merchant",
      "name": "商户后台",
      "role": "merchant",
      "platform": "web",
      "peer_group": null,
      "framework": "vue",
      "ui_library": "element-plus",
      "router": "vue-router",
      "path": "apps/merchant",
      "api_prefix": "/merchant",
      "run_url": "http://localhost:3001",
      "validate": true,
      "validate_method": "playwright",
      "auth": {
        "method": "form",
        "login_url": "/login",
        "credentials": { "username": "test_merchant", "password": "xxx" }
      }
    },
    {
      "id": "customer_web",
      "name": "客户 PC 网站",
      "role": "customer",
      "platform": "web",
      "peer_group": "customer",
      "framework": "vue",
      "ui_library": "element-plus",
      "router": "vue-router",
      "path": "apps/web",
      "api_prefix": "/api",
      "run_url": "http://localhost:3002",
      "validate": true,
      "validate_method": "playwright",
      "auth": {
        "method": "form",
        "login_url": "/login",
        "credentials": { "username": "test_customer", "password": "xxx" }
      },
      "platform_capabilities": ["batch_ops", "rich_editor", "keyboard_shortcuts", "file_download"],
      "platform_limitations": ["no_push", "no_scan", "no_biometric"]
    },
    {
      "id": "customer_h5",
      "name": "客户 H5 (移动端)",
      "role": "customer",
      "platform": "h5",
      "peer_group": "customer",
      "framework": "vue",
      "ui_library": "vant",
      "router": "vue-router",
      "path": "apps/h5",
      "api_prefix": "/api",
      "run_url": "http://localhost:3003",
      "validate": true,
      "validate_method": "playwright",
      "auth": {
        "method": "form",
        "login_url": "/login",
        "credentials": { "username": "test_customer", "password": "xxx" }
      },
      "platform_capabilities": ["wechat_share", "mobile_pay", "geolocation"],
      "platform_limitations": ["no_push", "no_scan", "no_batch_ops", "no_rich_editor"]
    },
    {
      "id": "customer_app",
      "name": "客户 App (Flutter)",
      "role": "customer",
      "platform": "app",
      "peer_group": "customer",
      "framework": "flutter",
      "path": "../flutter-app",
      "api_prefix": "/app",
      "validate": true,
      "validate_method": "patrol",
      "platform_capabilities": ["push", "scan", "biometric", "ar", "offline", "native_pay", "camera"],
      "platform_limitations": ["no_batch_ops", "no_rich_editor"],
      "notes": "Flutter 端使用 Patrol 做深度测试，flutter_test 做单元测试"
    },
    {
      "id": "customer_mp",
      "name": "客户微信小程序",
      "role": "customer",
      "platform": "miniprogram",
      "peer_group": "customer",
      "framework": "taro",
      "path": "apps/miniprogram",
      "api_prefix": "/api",
      "validate": true,
      "validate_method": "miniprogram_automator",
      "platform_capabilities": ["wechat_pay", "subscribe_msg", "scan", "share", "geolocation"],
      "platform_limitations": ["no_push", "no_batch_ops", "no_rich_editor", "no_ar", "limited_file"]
    }
  ],
  "modules": [
    {
      "name": "商品",
      "api_resource": "products",
      "type": "standard",
      "crud_by_client": {
        "admin": {
          "route": "/products",
          "menu_path": "商品管理 > 商品列表",
          "crud": { "C": true, "R": true, "U": true, "D": true },
          "extra_actions": ["审核上架", "批量导入", "导出"],
          "notes": ""
        },
        "merchant": {
          "route": "/products",
          "menu_path": "我的商品",
          "crud": { "C": true, "R": true, "U": true, "D": false },
          "extra_actions": ["上下架"],
          "notes": "商户只能管理自己的商品，不能硬删除，只能下架"
        },
        "customer_web": {
          "route": "/products",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["收藏", "加购物车", "对比"],
          "notes": "PC 端可做商品对比（平台专属：大屏适合对比）"
        },
        "customer_h5": {
          "route": "/products",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["收藏", "加购物车", "分享到微信"],
          "notes": "H5 有微信分享（平台专属）"
        },
        "customer_app": {
          "route": "/products",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["收藏", "加购物车", "AR 预览", "扫码搜索"],
          "notes": "App 有 AR 预览和扫码（平台专属）"
        },
        "customer_mp": {
          "route": "/products",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["收藏", "加购物车", "分享"],
          "notes": "小程序有原生微信分享"
        }
      }
    },
    {
      "name": "订单",
      "api_resource": "orders",
      "type": "workflow",
      "crud_by_client": {
        "admin": {
          "route": "/orders",
          "menu_path": "订单管理 > 订单列表",
          "crud": { "C": false, "R": true, "U": true, "D": true },
          "extra_actions": ["强制退款", "备注", "导出"],
          "notes": "Admin 不创建订单，只管理和处理异常"
        },
        "merchant": {
          "route": "/orders",
          "menu_path": "订单管理",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["发货", "确认收款"],
          "notes": "商户只能查看和发货自己的订单"
        },
        "customer_h5": {
          "route": "/orders",
          "crud": { "C": true, "R": true, "U": false, "D": false },
          "extra_actions": ["取消订单", "申请退款", "确认收货", "评价"],
          "notes": "用户下单和管理自己的订单"
        },
        "customer_app": {
          "route": "/orders",
          "crud": { "C": true, "R": true, "U": false, "D": false },
          "extra_actions": ["取消订单", "申请退款", "确认收货", "评价"],
          "notes": "同 H5"
        }
      }
    },
    {
      "name": "用户评价",
      "api_resource": "reviews",
      "type": "standard",
      "crud_by_client": {
        "admin": {
          "route": "/reviews",
          "menu_path": "运营管理 > 评价管理",
          "crud": { "C": false, "R": true, "U": false, "D": true },
          "extra_actions": ["审核", "置顶"],
          "notes": "Admin 不创建评价，只审核和删除"
        },
        "merchant": {
          "route": "/reviews",
          "menu_path": "评价管理",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["回复"],
          "notes": "商户只能查看和回复自己商品的评价"
        },
        "customer_h5": {
          "route": null,
          "crud": { "C": true, "R": true, "U": true, "D": true },
          "extra_actions": [],
          "notes": "用户在订单详情中评价，评价列表在商品详情中"
        },
        "customer_app": {
          "route": null,
          "crud": { "C": true, "R": true, "U": true, "D": true },
          "extra_actions": [],
          "notes": "同 H5"
        }
      }
    },
    {
      "name": "操作日志",
      "api_resource": "audit_logs",
      "type": "readonly",
      "crud_by_client": {
        "admin": {
          "route": "/system/logs",
          "menu_path": "系统管理 > 操作日志",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "extra_actions": ["导出"],
          "notes": "全局日志，只读"
        },
        "merchant": {
          "route": "/logs",
          "menu_path": "操作记录",
          "crud": { "C": false, "R": true, "U": false, "D": false },
          "notes": "只能看自己的操作记录"
        },
        "customer_h5": null,
        "customer_app": null
      }
    }
  ],
  "validation_scope": {
    "mode": "single|batch|all",
    "target_clients": ["admin"],
    "notes": "可以一次验证一个端，也可以批量验证多个端"
  }
}
```

**重要**：生成后需要请用户确认和补充，特别是：
- 每个前端的测试账号信息
- 每个模块在每个端的 CRUD 分工是否正确（**这是误判的最大来源**）
- 哪些前端需要验证，哪些跳过（如 Flutter 需要单独的测试方案）
- 模块分类是否正确

#### 批量验证模式

当需要验证多个前端时，skill 支持三种模式：

```
# 模式 1: 单端验证（默认）
请验证 admin 后台。项目路径 /path/to/project。

# 模式 2: 批量验证指定端
请验证 admin 后台和商户后台。项目路径 /path/to/project。

# 模式 3: 全端验证
请验证所有可验证的前端。项目路径 /path/to/project。
```

批量模式下，每个前端独立执行完整的验证流程，最终生成一份汇总报告，包含：
- 每个端的独立结果
- 跨端一致性检查（如 H5 有的功能 App 是否也有）
- 全局覆盖率（所有端合计是否覆盖了模块的完整 CRUD）
