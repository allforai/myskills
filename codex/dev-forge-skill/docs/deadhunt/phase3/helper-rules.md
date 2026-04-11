# UI 测试 Helper 生成规则

> 这些规则适用于任意 UI 测试框架（Patrol、XCUITest、Maestro、Unity Test Framework、Espresso、Detox 等）。
> 引擎由 LLM 根据项目实际使用的测试框架决定，规则本身与引擎无关。

## 前置步骤：识别测试框架

扫描项目，识别每个客户端实际使用的测试框架：

- 查看 `pubspec.yaml` / `package.json` / `build.gradle` / `*.csproj` / `*.xcodeproj` 等依赖声明
- 查看已有测试文件的 import / using 语句
- 查看 CI 配置中的测试命令

识别结果决定 helper 的语言和 API，规则目标不变。

## 核心原则：补充，不替代

**Helper 的作用是补充框架原生能力不足的部分，不是替代框架本身。**

生成 helper 前，先对每条规则评估目标框架的原生支持程度：

- **原生已覆盖**：框架本身已提供可靠的解决方案，helper 对该层为空或仅做薄封装（统一调用风格）
- **原生部分覆盖**：框架有基础支持但存在边界盲点，helper 补充缺失部分
- **原生未覆盖**：框架对该层无内置保护，helper 提供完整实现

评估结果写入 `.allforai/deadhunt/ui-helper-profile.json`，**按 module_id 分组**（与 `bootstrap-profile.json` 的 `modules[].id` 对齐）：

```json
{
  "modules": [
    {
      "module_id": "M002",
      "path": "petmart-app",
      "framework": "Patrol",
      "helper_file": "integration_test/helpers/ui_helper.dart",
      "layers": {
        "element_discovery":  { "native": "partial",   "helper": "supplement" },
        "button_trigger":     { "native": "partial",   "helper": "supplement" },
        "gesture":            { "native": "partial",   "helper": "supplement" },
        "async_wait":         { "native": "partial",   "helper": "supplement" },
        "system_dialog":      { "native": "covered",   "helper": "thin" },
        "keyboard_ime":       { "native": "uncovered", "helper": "full" },
        "scroll_container":   { "native": "uncovered", "helper": "full" },
        "cross_app":          { "native": "partial",   "helper": "supplement" }
      }
    },
    {
      "module_id": "M003",
      "path": "petmart-admin",
      "framework": "Playwright",
      "helper_file": "e2e/helpers/ui_helper.ts",
      "layers": {
        "element_discovery":  { "native": "partial",   "helper": "supplement" },
        "button_trigger":     { "native": "partial",   "helper": "supplement" },
        "gesture":            { "native": "covered",   "helper": "thin" },
        "async_wait":         { "native": "partial",   "helper": "supplement" },
        "system_dialog":      { "native": "covered",   "helper": "thin" },
        "keyboard_ime":       { "native": "covered",   "helper": "thin" },
        "scroll_container":   { "native": "covered",   "helper": "thin" },
        "cross_app":          { "native": "n/a",       "helper": "skip" }
      }
    }
  ]
}
```

每个 module 独立评估、独立生成 helper 文件，路径放在 module 自身目录下。
后端模块（无 UI）跳过评估，不生成 helper。

Helper 只为 `partial` 和 `uncovered` 的层生成实质逻辑；`covered` 的层最多做薄封装保持调用风格统一，不重新实现框架已有的能力。

## Helper 文件生成原则

- 生成测试文件前，先完成框架能力评估，再生成对应的 helper 文件（已存在则跳过）
- 测试代码不直接调用框架原生 API，全部通过 helper 封装后调用
- Helper 由 LLM 扫描项目代码特化生成，以下规则描述**目标**，实现方式由 LLM 决定

---

## 8 条脆弱层规则

**规则 1：控件发现**
- 目标：元素查找必须有明确的失败语义；找不到时抛出可识别的错误，不能静默跳过
- 禁止：以位置索引作为唯一定位手段
- 扫描项目：无障碍标识符（testID / accessibilityIdentifier / Key 等）的覆盖率；覆盖率低时 helper 需包含多级降级逻辑，并在报告中标记 `SELECTOR_UNSTABLE`

**规则 2：按钮触发**
- 目标：触发前必须确认元素在视口内、可见、且处于可交互状态
- 禁止：对不可见或 disabled 元素执行点击并忽略结果
- 扫描项目：项目中 disabled 状态的判断方式（属性名 / 颜色 / opacity / 自定义标识）

**规则 3：触控手势**
- 目标：手势操作前 UI 必须处于稳定状态（动画 / 页面过渡完成）
- 扫描项目：项目中使用的动画时长、过渡类型

**规则 4：异步等待**
- 目标：断言前必须等待数据就绪；超时时报告具体等待目标而非通用失败信息
- 扫描项目：项目中 loading 状态的 UI 表现、数据就绪的可见信号（loading 消失 / 列表出现 / 特定文本出现）

**规则 5：系统弹窗**
- 目标：测试流程不因系统弹窗中断；已知权限弹窗自动处理，未知弹窗 best-effort dismiss
- 扫描项目：平台权限声明文件（`Info.plist` / `AndroidManifest.xml` / 其他平台等效文件）中声明的权限列表

**规则 6：键盘与输入法**
- 目标：输入框聚焦后，后续 tap 目标仍在可操作区域内；输入完成前不触发其他交互
- 扫描项目：表单页面结构，判断键盘弹出后是否存在被遮挡的交互元素；检查项目是否面向非英语用户（日语 / 中文 / 阿拉伯语等需要 IME 的语言）
- 注：仅适用于有软键盘的平台（移动端）；桌面端跳过此规则
- **IME 扩展**：若项目使用 IME（输入法），helper 必须额外处理输入法组合态（composing state）——在输入法未确认（変換中 / 候选词未选定）期间禁止触发其他元素；等待输入确认后再继续

**规则 7：滚动容器**
- 目标：滚动容器内的元素在交互前必须已渲染进视图树
- 扫描项目：项目中使用的虚拟列表 / 懒加载组件类型

**规则 8：跨 App 流程**
- 目标：测试流程能跟踪 App 离开和返回的完整状态；跨 App 跳转后验证返回时的上下文正确性
- 扫描项目：检查项目中是否存在以下场景——第三方登录（LINE / Google / Apple）、外部支付跳转（PayPay / 支付宝 / 微信支付）、深链接返回、Universal Link / App Link
- 注：跨 App 流程属于移动端专有场景；Web 端跳过此规则
- **范围边界**：helper 只处理 App 内的等待和状态验证，跨 App 的实际跳转行为由平台框架负责（XCUITest 的 `XCUIApplication`、Patrol 的 `$.native`）

---

## 截图规则（独立于 8 条脆弱层规则）

- 目标：断言失败时自动截图，截图存入 `.allforai/deadhunt/screenshots/{module}/{step}.png`
- findings JSON 中附加 `screenshot` 字段指向对应文件
- 扫描项目：无需扫描，截图能力由各框架原生 API 提供

---

## 参考示例

以下文件展示了特定框架下的实现模式，供 LLM 参考，不是强制路由目标：

| 文件 | 框架 | 适用场景 |
|------|------|---------|
| `patrol.md` | Patrol | Flutter 跨平台 |
| `maestro.md` | Maestro | React Native / Android 原生 |
| `xcuitest.md` | XCUITest | iOS 原生（Swift/SwiftUI） |

遇到上述框架以外的情况（游戏引擎、桌面 GUI、自定义测试框架等），LLM 参照这些示例的结构自行适配，无需对应的参考文件。
