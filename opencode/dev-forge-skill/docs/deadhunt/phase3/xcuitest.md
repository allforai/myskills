## XCUITest 参考示例（iOS 原生端）

> **本文档是参考示例，不是强制路由目标。**
> 展示 XCUITest 框架下的测试模式（5 层检测、Swift 测试生成、结果格式等），供 LLM 适配 iOS 原生项目时参考。
> Helper 生成规则见 `helper-rules.md`，引擎选择由 LLM 根据项目决定。

### 架构定位

```
Phase 3: 深度测试
├── Web/H5 客户端    → Playwright 引擎
├── Flutter 客户端   → Patrol 引擎
├── RN/Android 客户端 → Maestro 引擎
└── iOS 原生客户端    → XCUITest 引擎（本节）
    ├── 测试代码生成 → .swift 文件
    ├── 执行 → xcodebuild test
    └── 结果收集 → 统一 JSON 格式
```

### 5 层检测模型（适配 iOS 原生语境）

| 层级 | Playwright (Web) | XCUITest (iOS) |
|------|-----------------|----------------|
| **L1a: 导航** | 菜单/面包屑点击 → 检查 URL | TabBar/NavigationBar 点击 → 检查当前 ViewController |
| **L1b: 页面交互** | 页面按钮/链接 → 检查跳转 | UIButton/UITableViewCell 点击 → 检查页面跳转 |
| **L2: 页内交互** | 表格操作/表单提交 | UITableView 操作/UITextField 输入/UIAlertController |
| **L3: API 层** | 拦截 XHR/Fetch → 检查 4xx/5xx | URLSession 网络响应 → 检查错误状态（需 stub 或日志） |
| **L4: 资源层** | JS/CSS/图片 404 | UIImageView 加载失败、本地资源缺失 |
| **L5: 边界情况** | 无效 URL、SPA 刷新 | 无效 Universal Link / Deep Link、权限拒绝、后台恢复 |

### 错误检测信号

| 信号 | XCUITest 检测方式 | 对应问题类型 |
|------|-----------------|------------|
| 崩溃 / 无响应 | `XCTAssertTrue(app.state == .runningForeground)` | 代码错误 |
| 空白页面 | 检查关键元素不存在 | 死链 / 路由错误 |
| 显示 "null" / "(null)" | `XCTAssertFalse(app.staticTexts["null"].exists)` | 字段不一致 |
| 加载卡住 | `XCTAssertFalse(app.activityIndicators.element.exists)` (超时后) | API 超时 |
| 权限弹窗未处理 | `addUIInterruptionMonitor` 自动处理系统弹窗 | 权限盲点 |
| Alert 意外出现 | `XCTAssertFalse(app.alerts.element.exists)` | 未处理的错误弹窗 |

### XCUITest 测试生成策略

对每个 iOS 模块生成 XCUITest 文件，保存到 `.allforai/deadhunt/xcuitest/` 目录：

```swift
// 自动生成: .allforai/deadhunt/xcuitest/OrderModuleTests.swift
import XCTest

class OrderModuleTests: XCTestCase {
    let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = false
        app.launch()
    }

    // L1a: 导航可达
    func testOrderTabNavigation() throws {
        app.tabBars.buttons["订单"].tap()
        XCTAssertTrue(app.navigationBars["我的订单"].exists)
    }

    // L2: 列表操作
    func testOrderDetailNavigation() throws {
        app.tabBars.buttons["订单"].tap()
        app.tables.cells.element(boundBy: 0).tap()
        XCTAssertTrue(app.navigationBars["订单详情"].exists)
        XCTAssertFalse(app.staticTexts["null"].exists)
        XCTAssertFalse(app.staticTexts["(null)"].exists)
    }

    // L3: 数据加载（检查 loading 消失）
    func testOrderDataLoaded() throws {
        app.tabBars.buttons["订单"].tap()
        let loading = app.activityIndicators.element
        let loaded = loading.waitForNonExistence(timeout: 10)
        XCTAssertTrue(loaded, "订单列表加载超时")
        XCTAssertFalse(app.staticTexts["加载失败"].exists)
    }
}
```

### 元素定位策略

| 优先级 | 定位方式 | 示例 | 适用场景 |
|--------|---------|------|---------|
| 1 | accessibilityIdentifier | `app.buttons["submit_button"]` | 有显式 identifier |
| 2 | accessibilityLabel | `app.buttons["提交"]` | 有 a11y label |
| 3 | 元素类型 + 文本 | `app.staticTexts["订单管理"]` | 文本唯一 |
| 4 | 位置索引 | `app.tables.cells.element(boundBy: 0)` | 列表第一项 |

> **选择顺序**：优先用 accessibilityIdentifier（最稳定），其次 Label，最后位置索引。

### 环境要求与限制

| 要求 | 说明 |
|------|------|
| macOS + Xcode | 非 macOS 环境直接标记 `DEFERRED_NATIVE` |
| iOS Simulator | `xcrun simctl list devices` 检查可用模拟器 |
| Scheme 配置 | 项目需有 UI Test target |

| 限制 | 应对策略 |
|------|---------|
| 只能在 macOS 运行 | 非 macOS 标记 `DEFERRED_NATIVE`，输出提示 |
| 执行较慢（需启动模拟器） | 静态分析优先过滤，只测有嫌疑的模块 |
| API 层拦截能力弱 | 通过 UI 上的错误提示间接验证；需 stub 支持时标注 |

### 降级策略

| 条件 | 处理 |
|------|------|
| 非 macOS 环境 | `DEFERRED_NATIVE`：仅测 API 层，输出「XCUITest 需要 macOS + Xcode」 |
| 无 UI Test target | 跳过深度测试，仅做静态分析 + R2 smoke |

### 执行命令

```bash
xcodebuild test \
  -scheme YourAppScheme \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  -testPlan DeadHuntTests \
  -only-testing:DeadHuntUITests
```

### 结果格式

```json
{
  "engine": "xcuitest",
  "client": "ios-native",
  "module": "order",
  "findings": [
    {
      "layer": "1a",
      "type": "navigation",
      "description": "TabBar「订单」点击后未显示「我的订单」导航标题",
      "signal": "app.navigationBars['我的订单'].exists == false",
      "severity": "critical",
      "intent": "FIX"
    }
  ]
}
```

此格式与 Playwright / Patrol / Maestro 引擎的 findings 格式一致，Phase 4 报告生成无需区分引擎来源。
