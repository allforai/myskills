# SwiftUI 运行适配

这是取证适配，视觉规则见 ../swiftui/。先检测 .xcodeproj/.xcworkspace、scheme、bundle id、部署目标和设备支持；从工程已有命令/测试配置确定如何构建。通过 xcodebuild -list、xcrun simctl list devices available 和各子命令 help 做能力探测，不固定型号或 OS。

布局阈值（写进 inventory 的 `layout_thresholds`，单位 pt）从代码读：`horizontalSizeClass` / `verticalSizeClass` 分支（compact ↔ regular 的边界随设备与分屏变化，把每个会切换尺寸类的宽度列出）；`GeometryReader` / `containerRelativeFrame` / `onGeometryChange` 里对宽度的比较；`ViewThatFits` 的候选宽度；`NavigationSplitView` 折叠成栈的宽度；`UIScreen.main.bounds` / `UIDevice.userInterfaceIdiom` 的条件。`width_range`：最小值取 `TARGETED_DEVICE_FAMILY` 里最窄的支持设备（iPhone 320 或 375 pt），iPad 支持多任务（没有 `UIRequiresFullScreen`）时取 Slide Over 320 pt；最大值取最大的支持设备（iPad 13 英寸横屏 1376 pt，macOS 取最大窗口或显示器宽度）。device 轴写模拟器名时在 inventory 顶层 `devices` 表给出每个名字的 pt 宽高与 scale（`xcrun simctl list devicetypes` 加设备规格），矩阵按 portrait 短边、landscape 长边算有效宽度。iPad 分屏是 device 值，不是 state：在 `devices` 表里作为独立条目（如 `"iPad Pro 13 slide-over": {"width": 320, "height": 1376, "scale": 2, "fixed_width": true}`、`split-1/3` 同理），`fixed_width: true` 表示旋转不改宽度，矩阵按声明宽度算。尺寸类阈值不是纯宽度：`horizontalSizeClass` 的 regular 在 iPhone 上只有 Plus / Max 横屏才出现，普通 iPhone 横屏宽度再大也是 compact；所以这类阈值的上侧必须含一个尺寸类真是 regular 的设备（任一全屏 iPad，或 Plus / Max 横屏），并在 basis 里写明——矩阵只查宽度，查不出尺寸类。macOS 可拉伸窗口另加 `resize-` 状态，录屏取证。

打包语言（写进 inventory 的 `locales`）从工程读：`Localizable.xcstrings` / `*.lproj` 目录、`CFBundleLocalizations`、`CFBundleDevelopmentRegion`（默认语言）、`knownRegions`；RTL 看是否有 ar / he / fa 等资源与 `layoutDirection` 分支。`translation_keys` 以 `.xcstrings` 的 `localizations` 逐语言 diff（`stringUnit.state` 为 `translated` 才算有），或 `.lproj/*.strings` 逐文件 diff。施加：launch arguments `-AppleLanguages (ja)` `-AppleLocale ja_JP`，或 `xcrun simctl spawn <udid> defaults write` 改系统语言后重启 App；读回写进 capture：`Locale.current.identifier`、`Bundle.main.preferredLocalizations.first`，`direction` 取 `UIView.userInterfaceLayoutDirection(for:)` / SwiftUI `\.layoutDirection`。

普查 SwiftUI View 与实际入口：App/Scene/WindowGroup、NavigationStack/Link/Destination、TabView、sheet/fullScreenCover/popover、Router/Coordinator、条件与权限分支、iPad SplitView。View 不都等于页面，标明顶级页面、组件、弹层及实际可达性；动态注册未知需 could_not。

使用指定 Simulator UDID 构建、安装、launch，然后 xcrun simctl io <udid> screenshot <evidence.png>。截图能力不代表能操作：检测可用 XCUITest/设备自动化/可见窗口工具及其授权；点击/键盘/手势必须真执行。遵循所在平台的可见窗口工具技能。缺操作工具时逐项无法自证，不凭路由代码补截图。

优先现有 UI tests/launch arguments/合成数据构造状态，不添加产品探针或改源码来制造通过。按已确认矩阵设置外观、content size、locale、orientation，并在运行中核对设置真正生效。用 xcrun simctl help 核查可用命令，无法施加的维度记无法自证。动画保留录屏和有时间戳关键帧；不支持直接读视频的 reviewer 使用帧序列，不能据两张静态图宣称节奏正确。

设备操作按 UDID 串行；取证前记录设备原设置，结束恢复本轮修改。构建产物放系统缓存/临时目录，审计证据写 run/evidence。真机能力缺失不影响模拟器可测项目，但不得声称真机覆盖。只声明支持的平台（iOS/iPadOS/macOS 等）参与矩阵；macOS 使用实际应用窗口截图工具并注明，不能拿 iOS Simulator 代替。
