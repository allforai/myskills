## Patrol 深度测试引擎（Flutter 端）

> 当 Phase 0 检测到 Flutter 客户端时，Phase 3 使用 Patrol 替代 Playwright 做深度测试。
> 两个引擎独立执行，结果汇入同一个 `reports/convergence-deep.json` 格式。

### 架构：双引擎并行

```
Phase 3: 深度测试
├── Web/H5 客户端 → Playwright 引擎（上文所述）
└── Flutter 客户端 → Patrol 引擎（本节）
    ├── 测试代码生成 → .dart 文件
    ├── 执行 → patrol test
    └── 结果收集 → 统一 JSON 格式
```

### Flutter 5 层检测模型

Playwright 的 5 层 404 分类适配到 Flutter 原生语境：

| 层级 | Playwright (Web) | Patrol (Flutter) |
|------|-----------------|-----------------|
| **L1a: 导航** | 菜单/面包屑点击 → 检查 URL | BottomNav/Drawer/AppBar 点击 → 检查当前路由 |
| **L1b: 页面交互** | 页面按钮/链接 → 检查跳转 | Widget 按钮/ListTile → 检查 Navigator 栈 |
| **L2: 页内交互** | 表格操作/表单提交 | ListView 项操作/表单提交/Dialog |
| **L3: API 层** | 拦截 XHR/Fetch → 检查 4xx/5xx | 拦截 Dio/http 响应 → 检查错误状态 |
| **L4: 资源层** | JS/CSS/图片 404 | 图片加载失败(`errorBuilder`)、字体缺失、资源文件 |
| **L5: 边界情况** | 无效 URL、SPA 刷新 | 无效 deep link 路由、权限拒绝、网络断开 |

### Flutter 错误检测信号

与 Web 端检测 HTTP 404 不同，Patrol 端检测以下信号：

| 信号 | 代码检测方式 | 对应问题类型 |
|------|-------------|------------|
| `ErrorWidget` 出现 | `expect(find.byType(ErrorWidget), findsNothing)` | 死链 / 代码错误 |
| 显示 `null`/`undefined` 文本 | `expect(find.text('null'), findsNothing)` | Ghost Feature / 字段不一致 |
| Navigator 栈异常 | 路由跳转后 `find.byType(TargetPage)` 失败 | 死链 |
| `DioException` | 捕获 Dio interceptor 中的错误状态码 | API 死链 |
| 加载卡住 | `CircularProgressIndicator` 超时仍存在 | API 超时 / 接口不存在 |
| 权限弹窗未处理 | Patrol 的 `$.native.grantPermissionWhenInUse()` 检测 | 权限盲点 |

### Patrol 测试生成策略

对每个 Flutter 模块生成 Patrol 测试代码，保存到 `.allforai/deadhunt/patrol/` 目录：

```dart
// 自动生成: .allforai/deadhunt/patrol/order_module_test.dart
import 'package:patrol/patrol.dart';

void main() {
  patrolTest('订单模块 - L1a 导航可达', ($) async {
    // 从首页通过 BottomNav 导航到订单页
    await $(BottomNavigationBar).tap();
    await $(#orderTab).tap();

    // 验证路由正确到达
    expect($.tester.widget<OrderPage>(find.byType(OrderPage)), isNotNull);
  });

  patrolTest('订单模块 - L2 列表操作', ($) async {
    // 点击订单详情
    await $(ListTile).first.tap();

    // 验证详情页加载，无错误 Widget
    expect(find.byType(ErrorWidget), findsNothing);
    expect(find.text('订单详情'), findsOneWidget);
  });

  patrolTest('订单模块 - L3 API 响应', ($) async {
    // 进入订单列表，检查数据加载
    await $(#orderTab).tap();
    await $.pumpAndSettle();

    // 验证无空数据/错误状态
    expect(find.text('加载失败'), findsNothing);
    expect(find.text('null'), findsNothing);
    expect(find.byType(ErrorWidget), findsNothing);
  });
}
```

### Widget 查找策略

Playwright 通过 CSS selector 定位元素，Patrol 需要适配 Widget tree：

| 优先级 | 查找方式 | 示例 | 适用场景 |
|--------|---------|------|---------|
| 1 | Key | `$(Key('order_list'))` | Widget 有显式 Key |
| 2 | Type | `$(OrderListPage)` | Widget 类型唯一 |
| 3 | Text | `$(find.text('订单管理'))` | 文本内容唯一 |
| 4 | Semantics | `$(find.bySemanticsLabel('订单'))` | 有 Semantics 标签 |
| 5 | 组合 | `$(ListView).$(ListTile).first` | 需要层级定位 |

> **选择顺序**：优先用 Key（最稳定），其次 Type，最后 Text。避免依赖 Text（多语言会变）。

### 执行与收敛

```
执行流程：
  1. 生成 Patrol 测试文件 → .allforai/deadhunt/patrol/*.dart
  2. 执行 patrol test --target .allforai/deadhunt/patrol/
  3. 收集结果 → 解析 test report
  4. 转换为统一 JSON 格式 → 合并到 convergence-deep.json

收敛循环：
  与 Playwright 相同结构（2 cycle × 最多 3-4 轮）
  Round 1: 基础扫描（生成并执行所有模块的 Patrol 测试）
  Round 2-4: 模式学习 → 交叉验证 → 扩散搜索（根据失败结果调整测试）
```

### Patrol 环境要求

| 要求 | 说明 |
|------|------|
| Flutter SDK | 项目已有 |
| Patrol CLI | `dart pub global activate patrol_cli` |
| 模拟器/真机 | Android emulator 或 iOS Simulator |
| 项目依赖 | `pubspec.yaml` 中已有 `patrol` |

### Patrol 限制与应对

| 限制 | 应对策略 |
|------|---------|
| 需要模拟器/真机 | 文档说明环境要求；支持 CI 中 Android emulator |
| 执行速度较慢 | 静态分析优先过滤，只测有嫌疑的模块 |
| 无法像 Playwright 拦截网络 | 通过 Dio interceptor 或日志收集 API 响应状态 |
| Widget key 不一定存在 | 支持多种查找策略：Key → Type → Text → Semantics |
| 无法并行多实例 | 模块间串行执行（不同于 Playwright 的并行 context） |

### 结果格式

Patrol 结果转换为与 Playwright 相同的 JSON 格式：

```json
{
  "engine": "patrol",
  "client": "flutter-app",
  "module": "order",
  "findings": [
    {
      "layer": "1a",
      "type": "navigation",
      "description": "从 BottomNav 点击订单 Tab 后未到达 OrderPage",
      "signal": "find.byType(OrderPage) failed",
      "severity": "critical",
      "intent": "FIX"
    },
    {
      "layer": "3",
      "type": "api",
      "description": "订单列表 API 返回错误",
      "signal": "DioException: 404",
      "severity": "critical",
      "intent": "FIX"
    }
  ]
}
```

此格式与 Playwright 引擎的 findings 格式一致，Phase 4 报告生成无需区分引擎来源。
