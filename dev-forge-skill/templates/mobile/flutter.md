# Flutter + Dart 模板

> 移动端参考模板。project-scaffold 读取此文件，按规则生成 Flutter 脚手架。支持 mobile-native 子项目类型。

---

## 目录结构

```
apps/{sub-project-name}/
├── pubspec.yaml
├── analysis_options.yaml
├── .env.example
│
├── android/                             # Android 原生配置
│   ├── app/
│   │   └── build.gradle
│   └── build.gradle
│
├── ios/                                 # iOS 原生配置
│   └── Runner/
│       ├── Info.plist
│       └── Assets.xcassets/
│
├── lib/
│   ├── main.dart                        # 入口文件 (ProviderScope + App)
│   ├── app.dart                         # MaterialApp / CupertinoApp 配置
│   │
│   ├── config/                          # 全局配置
│   │   ├── routes.dart                  # GoRouter 路由定义
│   │   ├── theme.dart                   # Material/Cupertino 主题
│   │   ├── constants.dart               # 常量
│   │   └── env.dart                     # 环境变量
│   │
│   ├── core/                            # 核心层 (跨 feature 共享)
│   │   ├── api/
│   │   │   ├── api_client.dart          # HTTP 客户端 (Dio)
│   │   │   ├── api_error.dart           # 错误类型
│   │   │   └── interceptors/
│   │   │       ├── auth_interceptor.dart
│   │   │       └── error_interceptor.dart
│   │   ├── auth/
│   │   │   ├── auth_provider.dart       # 认证状态 Provider
│   │   │   └── auth_service.dart        # Token 存储 (flutter_secure_storage)
│   │   ├── storage/
│   │   │   └── local_storage.dart       # 本地存储 (shared_preferences)
│   │   └── widgets/                     # 通用 Widget
│   │       ├── app_scaffold.dart        # 通用页面骨架 (SafeArea + AppBar)
│   │       ├── loading_indicator.dart
│   │       ├── error_view.dart
│   │       └── empty_view.dart
│   │
│   ├── shared/                          # 共享 UI 组件
│   │   ├── widgets/
│   │   │   ├── app_button.dart
│   │   │   ├── app_text_field.dart
│   │   │   ├── app_card.dart
│   │   │   ├── app_badge.dart
│   │   │   ├── app_avatar.dart
│   │   │   ├── app_bottom_sheet.dart
│   │   │   ├── swipeable_row.dart
│   │   │   └── pull_to_refresh.dart
│   │   └── extensions/
│   │       ├── context_ext.dart         # BuildContext 扩展
│   │       └── string_ext.dart
│   │
│   ├── models/                          # 数据模型 (引用 shared-types → Dart class)
│   │   ├── user.dart
│   │   └── {entity}.dart               # ★ freezed 或手写 data class
│   │
│   ├── features/                        # ★ 业务功能模块 (按 screen-map 生成)
│   │   └── {module}/
│   │       ├── providers/
│   │       │   └── {module}_provider.dart   # Riverpod Provider (API 调用 + 状态)
│   │       ├── screens/
│   │       │   ├── {entity}_list_screen.dart
│   │       │   ├── {entity}_detail_screen.dart
│   │       │   ├── {entity}_create_screen.dart
│   │       │   └── {entity}_edit_screen.dart
│   │       └── widgets/
│   │           ├── {entity}_card.dart
│   │           ├── {entity}_form.dart
│   │           └── {entity}_list_tile.dart
│   │
│   └── navigation/                      # 导航相关
│       ├── bottom_nav_bar.dart          # 底部 Tab 导航
│       └── app_router.dart              # GoRouter 实例
│
├── test/                                # 单元测试 + Widget 测试
│   ├── features/
│   └── core/
│
├── integration_test/                    # 集成测试
│   └── app_test.dart
│
└── assets/
    ├── fonts/
    ├── images/
    └── icons/
```

---

## Screen 映射规则

### 从 screen-map 到 Screen Widget

```
screen-map screen → Flutter Screen Widget

映射规则:
  screen (列表类) → ListView.builder / CustomScrollView + {entity}_card 组件
  screen (详情类) → SingleChildScrollView + {entity}_detail 组件
  screen (表单类) → Form + TextFormField 组件 (键盘自适应)
  screen (仪表盘) → SingleChildScrollView + 统计 Card + 图表

Tab 分配:
  screen-map 中频率最高的 3-5 个 screen → 底部 BottomNavigationBar / NavigationBar
  其余 screen → GoRouter push 导航 (从 Tab 页面进入)
```

### 导航配置

```
GoRouter 路由:
  /login            → 未登录时显示
  /                 → 底部 Tab (ShellRoute)
  /tab1             → Tab 1 页面
  /tab2             → Tab 2 页面
  /{module}/:id     → 从 Tab 页面 push 的详情页
  /{module}/new     → 创建页
  /{module}/:id/edit → 编辑页

路由守卫:
  GoRouter redirect 中检查 auth 状态:
    已登录 → 正常导航
    未登录 → 重定向到 /login
```

---

## 数据模型 → 组件映射

### 列表组件 (ListView)

```
entity.fields → Card / ListTile 展示字段

映射规则:
  image_url → 左侧/顶部缩略图 (CachedNetworkImage)
  title (string) → 主标题 (Text, fontWeight: FontWeight.bold)
  description (text) → 副标题 (Text, maxLines: 2, overflow: ellipsis)
  enum/status → 右上角状态标签 (AppBadge)
  datetime → 底部时间 (相对时间 via timeago)
  decimal/money → 右侧金额 (高亮色)
```

### 表单组件

```
entity.fields → Form fields

映射规则:
  string(短) → TextFormField
  string(长)/text → TextFormField (maxLines: 5)
  number → TextFormField (keyboardType: TextInputType.number)
  decimal/money → TextFormField (keyboardType: TextInputType.numberWithOptions(decimal: true)) + 货币前缀
  boolean → SwitchListTile
  enum → DropdownButtonFormField / BottomSheet 选择器
  date → showDatePicker → DatePicker
  datetime → showDatePicker + showTimePicker
  image_url → ImagePicker (image_picker package)
  foreign_key → Autocomplete / BottomSheet + ListView 搜索选择

验证规则 (来自 constraints):
  required → validator: (v) => v.isEmpty ? '必填' : null
  max_length → maxLength: n + LengthLimitingTextInputFormatter
  min/max → 自定义 validator 范围检查
  pattern → RegExp 验证
```

---

## 平台适配

```
Material / Cupertino 自适应:

策略: 使用 Material 3 为主，关键组件提供平台适配:
  - 导航: NavigationBar (Material) / CupertinoTabBar (iOS)
  - 对话框: AlertDialog (Material) / CupertinoAlertDialog (iOS)
  - 开关: Switch.adaptive
  - 指示器: CircularProgressIndicator.adaptive
  - 滚动: 自动适配平台滚动物理效果 (BouncingScrollPhysics / ClampingScrollPhysics)

判断方式:
  Platform.isIOS → Cupertino 风格
  其他 → Material 风格
```

---

## API 客户端

```dart
// lib/core/api/api_client.dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  static const _baseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://localhost:4000',
  );

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'auth_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) {
        if (error.response?.statusCode == 401) {
          // 清除 token，重定向到登录
        }
        handler.next(error);
      },
    ));
  }

  Future<T> get<T>(String path) async {
    final res = await _dio.get(path);
    return res.data as T;
  }

  Future<T> post<T>(String path, dynamic body) async {
    final res = await _dio.post(path, data: body);
    return res.data as T;
  }

  Future<T> put<T>(String path, dynamic body) async {
    final res = await _dio.put(path, data: body);
    return res.data as T;
  }

  Future<void> delete(String path) async {
    await _dio.delete(path);
  }
}
```

---

## 离线策略

```
优先级: 网络请求 → 本地缓存 → 离线提示

core/storage/local_storage.dart:
  - 使用 shared_preferences 缓存列表/详情数据
  - 离线时: 读取缓存 + 队列写操作 (drift / sqflite)
  - 恢复时: 同步队列中的写操作

connectivity_plus:
  - 监听网络连接状态变化
  - 离线 Banner 提示 (MaterialBanner)
  - 恢复网络后自动同步
```

---

## 配置文件模板

### pubspec.yaml

```yaml
name: {sub_project_name}
description: {project-description}
version: 0.1.0+1
publish_to: none

environment:
  sdk: '>=3.2.0 <4.0.0'
  flutter: '>=3.19.0'

dependencies:
  flutter:
    sdk: flutter
  # 路由
  go_router: ^14.2.0
  # 状态管理
  flutter_riverpod: ^2.5.0
  riverpod_annotation: ^2.3.0
  # 网络
  dio: ^5.7.0
  # 存储
  flutter_secure_storage: ^9.2.0
  shared_preferences: ^2.3.0
  # UI
  cached_network_image: ^3.4.0
  shimmer: ^3.0.0
  # 工具
  intl: ^0.19.0
  timeago: ^3.7.0
  connectivity_plus: ^6.0.0
  image_picker: ^1.1.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0
  build_runner: ^2.4.0
  riverpod_generator: ^2.4.0
  integration_test:
    sdk: flutter
  patrol: ^3.10.0

flutter:
  uses-material-design: true
  assets:
    - assets/images/
    - assets/icons/
  fonts:
    - family: AppFont
      fonts:
        - asset: assets/fonts/AppFont-Regular.ttf
        - asset: assets/fonts/AppFont-Bold.ttf
          weight: 700
```

### analysis_options.yaml (关键片段)

```yaml
include: package:flutter_lints/flutter.yaml

linter:
  rules:
    prefer_const_constructors: true
    prefer_const_declarations: true
    avoid_print: true
    require_trailing_commas: true
```

---

## 命名约定

| 元素 | 约定 | 示例 |
|------|------|------|
| 文件名 | snake_case | `order_list_screen.dart` |
| 类名 | PascalCase | `OrderListScreen` |
| Widget 名 | PascalCase | `OrderCard` |
| Provider 名 | camelCase + Provider | `orderListProvider` |
| 变量/函数 | camelCase | `fetchOrders()` |
| 常量 | camelCase + k 前缀 | `kDefaultPadding` |
| 路由路径 | kebab-case | `/order-items` |
| 包名 | snake_case | `order_module` |

---

## Batch 结构（mobile-native）

```
B1 Foundation: 数据模型 (Dart class)、GoRouter 导航配置、主题/常量、API 客户端 (Dio)、Riverpod 基础 Provider
B2 —:          (无独立 API，跳过)
B3 UI:         Screen Widget (ListView/ScrollView/Form)、底部 Tab 页面、业务 Widget (Card/Form/Detail)
B4 Integration: API 集成 (切换 mock → 真实后端)、离线同步 (connectivity_plus)、推送集成 (firebase_messaging)、深度链接
B5 Testing:     Widget 测试 (flutter_test) + 集成测试 (Patrol / integration_test)
```

---

## 推送通知

```dart
// lib/core/push/push_service.dart
import 'package:firebase_messaging/firebase_messaging.dart';

class PushService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;

  Future<void> initialize() async {
    final settings = await _messaging.requestPermission();
    if (settings.authorizationStatus != AuthorizationStatus.authorized) return;

    final token = await _messaging.getToken();
    if (token != null) {
      // 注册 token 到后端
      await apiClient.post('/api/devices', {
        'push_token': token,
        'platform': Platform.isIOS ? 'ios' : 'android',
      });
    }

    // 前台消息处理
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      // 显示本地通知
    });
  }
}
```

---

## 设备权限声明

```
按 product-map 任务需求声明权限:

任务涉及"拍照/上传图片" → image_picker + camera permission (Info.plist / AndroidManifest)
任务涉及"定位/地图" → geolocator + location permission
任务涉及"扫码" → mobile_scanner + camera permission
任务涉及"文件下载" → path_provider + storage permission
任务涉及"推送通知" → firebase_messaging + notification permission
任务涉及"生物识别" → local_auth + FaceID/TouchID/Fingerprint permission
```
