# React Native + Expo 模板

> 移动端参考模板。project-scaffold 读取此文件，按规则生成 React Native + Expo 脚手架。

---

## 目录结构

```
apps/{sub-project-name}/
├── package.json
├── tsconfig.json
├── app.json                            # Expo 配置
├── babel.config.js
├── metro.config.js
├── .env.example
│
├── app/                                # Expo Router (文件系统路由)
│   ├── _layout.tsx                     # 根 layout (Provider + Navigation)
│   ├── index.tsx                       # 首页 (重定向)
│   ├── (auth)/                         # 认证相关
│   │   ├── _layout.tsx
│   │   ├── login.tsx
│   │   └── register.tsx
│   ├── (tabs)/                         # 底部 Tab 导航
│   │   ├── _layout.tsx                 # TabBar 配置
│   │   ├── index.tsx                   # Tab 1 首页
│   │   ├── {tab2}.tsx                  # Tab 2
│   │   ├── {tab3}.tsx                  # Tab 3
│   │   └── profile.tsx                 # 个人中心
│   └── (stack)/                        # 堆栈导航 (详情/编辑等)
│       ├── _layout.tsx
│       └── {module}/
│           ├── [id].tsx                # 详情页
│           └── edit.tsx                # 编辑页
│
├── components/
│   ├── ui/                             # 基础 UI 组件
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   ├── Avatar.tsx
│   │   ├── Badge.tsx
│   │   ├── BottomSheet.tsx
│   │   ├── SwipeableRow.tsx
│   │   └── PullToRefresh.tsx
│   ├── layout/                         # 布局组件
│   │   ├── Screen.tsx                  # 安全区域 + 状态栏
│   │   ├── Header.tsx
│   │   └── TabBar.tsx
│   └── features/                       # ★ 业务组件
│       └── {module}/
│           ├── {entity}-list.tsx
│           ├── {entity}-card.tsx
│           ├── {entity}-form.tsx
│           └── {entity}-detail.tsx
│
├── hooks/
│   ├── useAuth.ts
│   ├── useApi.ts
│   ├── useRefresh.ts                   # 下拉刷新
│   ├── useInfiniteScroll.ts            # 无限滚动
│   └── useOffline.ts                   # 离线状态检测
│
├── services/
│   ├── api-client.ts                   # HTTP 客户端
│   ├── auth.ts                         # Token 存储 (SecureStore)
│   ├── storage.ts                      # 本地存储 (AsyncStorage)
│   └── push-notifications.ts           # 推送通知注册
│
├── stores/
│   ├── auth-store.ts                   # 认证状态
│   └── offline-store.ts                # 离线数据缓存
│
├── types/                              # 类型定义 (引用 shared-types)
│   └── index.ts
│
├── constants/
│   ├── colors.ts                       # 颜色主题
│   ├── layout.ts                       # 布局常量
│   └── api.ts                          # API 端点常量
│
├── utils/
│   ├── format.ts                       # 格式化工具
│   └── validation.ts                   # 表单验证
│
└── assets/
    ├── fonts/
    ├── images/
    └── icons/
```

---

## Screen 映射规则

### 从 screen-map 到 Screen 组件

```
screen-map screen → React Native Screen

映射规则:
  screen (列表类) → FlatList + {entity}-card 组件
  screen (详情类) → ScrollView + {entity}-detail 组件
  screen (表单类) → KeyboardAvoidingView + {entity}-form 组件
  screen (仪表盘) → ScrollView + 统计卡片 + 图表

Tab 分配:
  screen-map 中频率最高的 3-5 个 screen → 底部 Tab
  其余 screen → Stack 导航 (从 Tab 页面进入)
```

### 导航栈配置

```
Expo Router 文件系统路由:
  (auth)/           → 未登录时显示
  (tabs)/           → 登录后的底部 Tab
  (stack)/{module}/ → 从 Tab 页面 push 的详情/编辑页

路由守卫:
  app/_layout.tsx 中检查 token:
    有 token → 显示 (tabs)
    无 token → 重定向到 (auth)/login
```

---

## 数据模型 → 组件映射

### 列表组件 (FlatList)

```
entity.fields → 卡片展示字段

映射规则:
  image_url → 左侧/顶部缩略图 (Image 组件)
  title (string) → 主标题 (Text, fontSize: 16, fontWeight: 'bold')
  description (text) → 副标题 (Text, fontSize: 14, color: 'gray', numberOfLines: 2)
  enum/status → 右上角状态标签 (Badge 组件)
  datetime → 底部时间 (相对时间)
  decimal/money → 右侧金额 (高亮)
```

### 表单组件

```
entity.fields → 表单字段

映射规则:
  string(短) → TextInput
  string(长)/text → TextInput (multiline)
  number → TextInput (keyboardType: 'numeric')
  decimal/money → TextInput (keyboardType: 'decimal-pad') + 货币前缀
  boolean → Switch
  enum → Picker / BottomSheet 选择器
  date → DateTimePicker (mode: 'date')
  datetime → DateTimePicker (mode: 'datetime')
  image_url → ImagePicker (expo-image-picker)
  foreign_key → SearchableSelect (BottomSheet + FlatList)
```

---

## API 客户端

```typescript
// services/api-client.ts
import * as SecureStore from 'expo-secure-store';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:4000';

class ApiClient {
  private async getToken(): Promise<string | null> {
    return SecureStore.getItemAsync('auth_token');
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const token = await this.getToken();
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ message: res.statusText }));
      throw new ApiError(res.status, error.message);
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

## 离线策略

```
优先级: 网络请求 → 本地缓存 → 离线提示

hooks/useOffline.ts:
  - 监听 NetInfo 连接状态
  - 离线时: 读 AsyncStorage 缓存 + 队列写操作
  - 恢复时: 同步队列中的写操作

stores/offline-store.ts:
  - 缓存最近访问的列表/详情数据
  - 队列化离线创建/更新操作
  - 恢复网络后按 FIFO 顺序同步
```

---

## 配置文件模板

### package.json

```json
{
  "name": "{sub-project-name}",
  "version": "0.1.0",
  "private": true,
  "main": "expo-router/entry",
  "scripts": {
    "dev": "expo start",
    "build:android": "eas build --platform android",
    "build:ios": "eas build --platform ios",
    "lint": "eslint .",
    "test": "jest"
  },
  "dependencies": {
    "expo": "~50.0.0",
    "expo-router": "~3.4.0",
    "expo-secure-store": "~12.8.0",
    "expo-image-picker": "~14.7.0",
    "expo-notifications": "~0.27.0",
    "react": "18.2.0",
    "react-native": "0.73.0",
    "react-native-safe-area-context": "^4.8.0",
    "react-native-screens": "~3.29.0",
    "react-native-gesture-handler": "~2.14.0",
    "react-native-reanimated": "~3.6.0",
    "@react-native-async-storage/async-storage": "^1.21.0",
    "@react-native-community/netinfo": "^11.2.0"
  },
  "devDependencies": {
    "@types/react": "~18.2.0",
    "typescript": "^5.3.0",
    "jest": "^29.5.0",
    "jest-expo": "~50.0.0"
  }
}
```

### app.json

```json
{
  "expo": {
    "name": "{project-display-name}",
    "slug": "{sub-project-name}",
    "version": "0.1.0",
    "scheme": "{sub-project-name}",
    "platforms": ["ios", "android"],
    "orientation": "portrait",
    "icon": "./assets/images/icon.png",
    "splash": {
      "image": "./assets/images/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.{org}.{sub-project-name}"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/images/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "com.{org}.{sub_project_name}"
    },
    "plugins": [
      "expo-router",
      "expo-secure-store"
    ]
  }
}
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| Screen 文件 | kebab-case (Expo Router) | `order-detail.tsx` |
| 组件文件 | PascalCase | `OrderCard.tsx` |
| 组件名 | PascalCase | `OrderCard` |
| hooks | camelCase + use | `useAuth` |
| services | kebab-case | `api-client.ts` |
| stores | kebab-case + -store | `auth-store.ts` |

---

## Batch 结构（mobile-native）

```
B1 Foundation: 类型定义、导航栈配置、本地存储 schema、权限声明、API 客户端
B2 —:          (无独立 API，跳过)
B3 UI:         Screen 组件 (FlatList/ScrollView/Form)、Tab 页面、业务组件
B4 Integration: API 集成 (切换 mock → 真实后端)、离线同步、推送集成、深度链接
B5 Testing:     Detox / Maestro 测试（非 Playwright）
```

---

## 推送通知

```typescript
// services/push-notifications.ts
import * as Notifications from 'expo-notifications';
import { api } from './api-client';

export async function registerForPush() {
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== 'granted') return;

  const token = (await Notifications.getExpoPushTokenAsync()).data;
  // 注册 token 到后端
  await api.post('/api/devices', { push_token: token, platform: Platform.OS });
}
```

---

## 设备 API 权限声明

```
按 product-map 任务需求声明权限:

任务涉及"拍照/上传图片" → expo-image-picker + camera permission
任务涉及"定位/地图" → expo-location + location permission
任务涉及"扫码" → expo-barcode-scanner + camera permission
任务涉及"文件下载" → expo-file-system + storage permission
任务涉及"推送通知" → expo-notifications + notification permission
```
