# SwiftUI 运行适配

这是取证适配，视觉规则见 ../swiftui/。先检测 .xcodeproj/.xcworkspace、scheme、bundle id、部署目标和设备支持；从工程已有命令/测试配置确定如何构建。通过 xcodebuild -list、xcrun simctl list devices available 和各子命令 help 做能力探测，不固定型号或 OS。

普查 SwiftUI View 与实际入口：App/Scene/WindowGroup、NavigationStack/Link/Destination、TabView、sheet/fullScreenCover/popover、Router/Coordinator、条件与权限分支、iPad SplitView。View 不都等于页面，标明顶级页面、组件、弹层及实际可达性；动态注册未知需 could_not。

使用指定 Simulator UDID 构建、安装、launch，然后 xcrun simctl io <udid> screenshot <evidence.png>。截图能力不代表能操作：检测可用 XCUITest/设备自动化/可见窗口工具及其授权；点击/键盘/手势必须真执行。遵循所在平台的可见窗口工具技能。缺操作工具时逐项无法自证，不凭路由代码补截图。

优先现有 UI tests/launch arguments/合成数据构造状态，不添加产品探针或改源码来制造通过。按已确认矩阵设置外观、content size、locale、orientation，并在运行中核对设置真正生效。用 xcrun simctl help 核查可用命令，无法施加的维度记无法自证。动画保留录屏和有时间戳关键帧；不支持直接读视频的 reviewer 使用帧序列，不能据两张静态图宣称节奏正确。

设备操作按 UDID 串行；取证前记录设备原设置，结束恢复本轮修改。构建产物放系统缓存/临时目录，审计证据写 run/evidence。真机能力缺失不影响模拟器可测项目，但不得声称真机覆盖。只声明支持的平台（iOS/iPadOS/macOS 等）参与矩阵；macOS 使用实际应用窗口截图工具并注明，不能拿 iOS Simulator 代替。
