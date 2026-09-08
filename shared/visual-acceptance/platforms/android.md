# Android 运行适配

这是取证适配，视觉规则仍按 visual-acceptance.md 逐类与用户确认。先检测 Gradle 模块、`applicationId`、`minSdk` / `targetSdk`、支持的 ABI 与屏幕声明（`<supports-screens>`、`resizeableActivity`、`android:configChanges`），从工程已有命令（`./gradlew :app:installDebug`、既有 UI test）确定如何构建安装；用 `adb devices`、`emulator -list-avds`、`avdmanager list device` 做能力探测，不固定机型或 API 级别。

普查页面与实际入口：Activity / Fragment / Compose `NavHost` 路由、BottomNavigation / Drawer / Tab、Dialog / BottomSheet / Snackbar、深链与权限分支、多窗口与折叠态下出现或消失的入口。Composable 不都等于页面，标明顶级页面、组件、弹层及实际可达性；动态注册未知需 could_not。

布局阈值（写进 inventory 的 `layout_thresholds`，单位 dp）从代码读：资源限定符目录 `layout-sw600dp` / `values-w840dp` / `layout-land` 等的宽度；`WindowSizeClass`（compact < 600、medium 600–840、expanded ≥ 840）的使用点；Compose `BoxWithConstraints` / `LocalConfiguration.screenWidthDp` 的比较；`ConstraintLayout` 的 `layout_constraintWidth_max`；折叠屏 `WindowLayoutInfo` / posture 分支。`width_range`：最小值取 `<supports-screens>` 或最窄目标机型（常见 320–360 dp），最大值取最大平板或桌面模式（Chromebook / DeX 1280 dp 以上；platform android 隐含 `form_factor: mobile`，不受 `matrix.py` 桌面下限 1920 的约束）；`resizeableActivity=true` 时分屏与自由窗口的宽度也是 device 值，在 inventory 顶层 `devices` 表里作独立条目（如 `"pixel-8-split-1/2": {"width": 412, "height": 445, "scale": 2.625, "fixed_width": true}`），`fixed_width: true` 表示旋转不改宽度。device 轴写 AVD / 机型名时同样在 `devices` 表给出 dp 宽高与 density；`WindowSizeClass` 的 medium 段（600–840）要有一个真正落在段内的宽度，不能只靠两侧跨过去。

打包语言（写进 inventory 的 `locales`）从工程读：`res/values-xx/strings.xml` 目录、`resConfigs` / `localeFilters`、`locales_config.xml`（Android 13+ 应用内语言）、`android:supportsRtl`；`translation_keys` 以 `values/strings.xml` 为点名册逐语言 diff（`translatable="false"` 的 key 排除）。其它轴的支持值（普查官 `axis_support`）：appearance 看 `values-night/`、`Theme.*.DayNight`、`AppCompatDelegate.setDefaultNightMode` / Compose `isSystemInDarkTheme()`；`dark_variant_gaps` 列 `values/colors.xml` 有而 `values-night/` 没有的 color、无 `-night` 变体的 drawable、源码字面量颜色。dynamic_type 看 `sp` 与 `fontScale` 用法（用 `dp` 写字号的界面不响应字号，单值带出处）。orientation 看 `android:screenOrientation` 与 `configChanges`。

七个维度对 Android 的取值，全部在 environment 类由用户确认为具体值：
- device：dp 宽高加密度，如 `411x914@2.625`、`800x1280@2`；施加：`adb shell wm size WxH`（px）与 `adb shell wm density D`，读回 `adb shell wm size` / `wm density` 与页面内 `resources.displayMetrics` / `LocalConfiguration.screenWidthDp`。
- os：Android 版本与 API 级别（`adb shell getprop ro.build.version.release` / `sdk`），厂商皮肤（One UI、MIUI）按用户确认是否分列。
- appearance：`adb shell cmd uimode night yes|no`，应用内主题开关另算一个值；读回 `Configuration.uiMode & UI_MODE_NIGHT_MASK` 写进 `readback.appearance`。
- dynamic_type：`adb shell settings put system font_scale 1.0|1.3|2.0`，读回 `Configuration.fontScale` 写进 `readback.dynamic_type`；显示大小 `wm density` 另算一档。
- width：`Resources.configuration.screenWidthDp` 或 `WindowMetricsCalculator` 的宽度换算成 dp，写 `readback.width`，须等于用例设备在该方向下的有效宽度。
- locale：`adb shell setprop persist.sys.locale` 或系统设置切换，Android 13+ 另可 `adb shell cmd locale set-app-locales <package> --locales ja`；读回 `Configuration.locales[0]` 写进 `readback.locale`，`readback.direction` 取 `Configuration.layoutDirection` / `View.layoutDirection`（`supportsRtl=false` 时 RTL 语言永远读回 ltr，那是一条 gap）。
- orientation：`adb shell settings put system accelerometer_rotation 0` 加 `user_rotation 0|1`，读回 `Configuration.orientation` 写进 `readback.orientation`。
- state：加载、空、错误、权限拒绝、离线、键盘弹出、进程被杀后恢复（`adb shell am kill` 再回前台），按页面归入。

施加后必须在应用里读回真正生效的值写进 capture，不凭 adb 命令返回码补。截图 `adb exec-out screencap -p > <evidence.png>`；动画用 `adb shell screenrecord` 录屏加带时间戳抓帧。截图能力不代表能操作：点击/输入/手势用既有 UI test（Espresso / Compose test）、`adb shell input` 或可见窗口工具真执行，缺操作工具时逐项无法自证。

只操作模拟器或开发机上的调试构建；写请求造成的副作用限于该实例。设备操作按序列号串行，取证前记录原设置（`wm size reset`、`wm density reset`、font_scale、night mode）并在结束恢复。构建标识同 Web：commit 加工作树快照摘要，有 APK 时再加 APK 摘要；热重载 / Apply Changes 期间不采集。真机能力缺失不影响模拟器可测项，但不得声称真机覆盖。
