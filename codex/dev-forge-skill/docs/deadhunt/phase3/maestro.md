## Maestro 参考示例（React Native / Android 端）

> **本文档是参考示例，不是强制路由目标。**
> 展示 Maestro 框架下的测试模式（5 层检测、YAML flow 生成、结果格式等），供 LLM 适配 RN / Android 项目时参考。
> Helper 生成规则见 `helper-rules.md`，引擎选择由 LLM 根据项目决定。

### 架构：多引擎并行

```
Phase 3: 深度测试
├── Web/H5 客户端     → Playwright 引擎
├── Flutter 客户端    → Patrol 引擎
├── React Native 客户端 → Maestro 引擎（本节）
└── Android 原生客户端  → Maestro 引擎（本节）
    ├── 测试流生成 → .yaml 文件
    ├── 执行 → maestro test
    └── 结果收集 → 统一 JSON 格式
```

### 5 层检测模型（适配 RN / Android 原生语境）

| 层级 | Playwright (Web) | Maestro (RN/Android) |
|------|-----------------|----------------------|
| **L1a: 导航** | 菜单/面包屑点击 → 检查 URL | BottomTab/Drawer/Back 点击 → 检查当前 screen |
| **L1b: 页面交互** | 页面按钮/链接 → 检查跳转 | 按钮/ListItem 点击 → 检查 screen 切换 |
| **L2: 页内交互** | 表格操作/表单提交 | FlatList 项操作/表单提交/Modal |
| **L3: API 层** | 拦截 XHR/Fetch → 检查 4xx/5xx | 监听网络响应 → 检查错误状态 |
| **L4: 资源层** | JS/CSS/图片 404 | 图片加载失败、字体缺失、本地资源 |
| **L5: 边界情况** | 无效 URL、SPA 刷新 | 无效 deep link、权限拒绝、网络断开 |

### 错误检测信号

| 信号 | 检测方式 | 对应问题类型 |
|------|---------|------------|
| 红色报错界面 (RN Red Box) | `assertNotVisible: "Error"` + 截图比对 | 代码错误 / 死链 |
| 空列表 / null 文本 | `assertNotVisible: "null"` | Ghost Feature / 字段不一致 |
| 加载卡住 | `assertNotVisible: "Loading"` (超时后) | API 超时 / 接口不存在 |
| 权限弹窗未处理 | `allowPermission: true` 后检测正常流程 | 权限盲点 |
| Navigation 跳转失败 | 目标 screen 的唯一元素不可见 | 死链 |
| Network 错误提示 | `assertVisible: "网络错误"` 未出现 | API 连通性 |

### Maestro 测试流生成策略

对每个 RN / Android 模块生成 Maestro flow 文件，保存到 `.allforai/deadhunt/maestro/` 目录：

```yaml
# 自动生成: .allforai/deadhunt/maestro/order_module_flow.yaml
appId: com.example.app
---
# L1a: 导航可达
- launchApp
- tapOn: "订单"           # BottomTab
- assertVisible: "我的订单"

# L2: 列表操作
- tapOn:
    index: 0
    text: ".*"             # 点击第一条订单
- assertVisible: "订单详情"
- assertNotVisible: "null"
- assertNotVisible: "Error"

# L3: 数据加载
- assertVisible: "订单编号"
- assertNotVisible: "加载失败"
```

### 元素定位策略

| 优先级 | 定位方式 | 示例 | 适用场景 |
|--------|---------|------|---------|
| 1 | testID / accessibilityLabel | `tapOn: {id: "order_list"}` | 有显式 testID |
| 2 | 文本内容 | `tapOn: "订单管理"` | 文本唯一且稳定 |
| 3 | 元素类型 + 文本 | `tapOn: {text: "提交", type: "RCTButton"}` | 同文本多元素 |
| 4 | 位置索引 | `tapOn: {index: 0}` | 列表第一项 |

> **选择顺序**：优先用 testID（最稳定），其次文本，最后位置索引。避免过度依赖文本（多语言会变）。

### 降级策略

Maestro 不可用时：

| 平台 | 降级 | 说明 |
|------|------|------|
| React Native | Detox | JS 驱动，需 Detox 配置 |
| Android 原生 | Espresso（`./gradlew connectedAndroidTest`） | 需要编写 Espresso 测试代码 |
| 均不可用 | `DEFERRED_NATIVE` | 仅测 API 层，标记移动端待补 |

### 执行与收敛

```
执行流程：
  1. 生成 Maestro flow 文件 → .allforai/deadhunt/maestro/*.yaml
  2. 执行 maestro test .allforai/deadhunt/maestro/
  3. 收集结果 → 解析 maestro report
  4. 转换为统一 JSON 格式 → 合并到 convergence-deep.json

收敛循环：
  与 Playwright/Patrol 相同结构（2 cycle × 最多 3-4 轮）
  Round 1: 基础扫描（生成并执行所有模块的 flow）
  Round 2-4: 模式学习 → 交叉验证 → 扩散搜索（根据失败结果调整 flow）
```

### 环境要求

| 要求 | 说明 |
|------|------|
| Maestro CLI | `curl -Ls https://get.maestro.mobile.dev \| bash` |
| Android 模拟器 / 真机 | `adb devices` 列出设备 |
| iOS 模拟器（RN） | macOS + Xcode + `xcrun simctl list` |
| App 已安装 | `maestro test` 前需先构建安装 |

### 结果格式

```json
{
  "engine": "maestro",
  "client": "react-native-app",
  "module": "order",
  "findings": [
    {
      "layer": "1a",
      "type": "navigation",
      "description": "点击 BottomTab「订单」后未显示订单列表",
      "signal": "assertVisible: '我的订单' failed",
      "severity": "critical",
      "intent": "FIX"
    },
    {
      "layer": "3",
      "type": "api",
      "description": "订单列表显示「加载失败」",
      "signal": "assertNotVisible: '加载失败' failed",
      "severity": "critical",
      "intent": "FIX"
    }
  ]
}
```

此格式与 Playwright / Patrol 引擎的 findings 格式一致，Phase 4 报告生成无需区分引擎来源。
