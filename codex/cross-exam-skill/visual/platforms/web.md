# Web 运行适配

这是取证适配，视觉规则仍按 visual-acceptance.md 逐类与用户确认；本文只定义 Web 目标怎么普查、怎么把七个维度施加到真实浏览器、怎么留证据。先检测包管理器与启动命令（package.json scripts、Vite/Next/CRA 配置、Docker compose），从工程已有命令确定如何起本地服务；不猜端口，以启动日志或配置为准。

普查页面与实际入口：路由表（React Router / Next app 或 pages 目录 / Vue Router / SvelteKit routes）、导航与 Tab、Modal / Drawer / Toast / Popover、受权限与登录态影响的分支、响应式断点下出现或消失的入口。组件不都等于页面，标明顶级页面、组件、弹层及实际可达性；动态注册（运行时拉取的菜单、按角色下发的路由）未知需 could_not。

七个维度对 Web 的取值，全部在 environment 类由用户确认为具体值：
- device：视口宽高加设备像素比，如 `1440x900@2`、`390x844@3`；不写"桌面"或"所有手机"。取值下限见下文"布局阈值"。
- os：浏览器引擎与主版本，如 `Chromium 131`、`WebKit 18`；同一引擎不同版本按用户确认是否分列。
- appearance：`prefers-color-scheme` 的 light / dark，另加站点自身主题开关的值（如果有）。
- dynamic_type：浏览器缩放或根字号，如 `zoom 100%`、`zoom 150%`、`font-size 20px`；站点不响应缩放时取单一值 `zoom 100%`，依据（例如 CSS 未使用 rem/em）记在 environment 类的确认里。
- locale：浏览器语言加站点语言开关的值。
- orientation：`landscape` / `portrait`；桌面视口取单一值 `landscape`，依据记在 environment 类的确认里。
- state：加载、空、错误、权限拒绝、离线、键盘弹出（移动）等，按页面归入。

维度没有"不适用"：每个维度都是非空的具体值列表，某维度对该产品无意义就取一个值并记依据。整条用例的 applicability: not_applicable 只留给组合本身不可能存在的情况（如某页面在某设备上根本不可达），须有 reason 与 basis。

施加与核对：优先本机可见窗口工具或页面自动化工具（Playwright MCP、Chrome DevTools MCP、playwright-cli），用它们的 resize / emulate / 颜色方案 / locale 接口设置维度，然后在页面里核对真正生效（`window.innerWidth`、`matchMedia('(prefers-color-scheme: dark)')`、`document.documentElement.lang`、计算后的根字号），核对结果写进 capture。无法施加的维度记无法自证，不凭截图元数据补。motion 用录屏或按时间戳抓帧，静态截图不证明动画。截图模式见下一节：全页与视口不是两种存法，是两种不同的画面。

## 布局阈值：device 轴从代码来，不从用户的屏幕来

普查时从代码读出 `layout_thresholds`，每条带出处：CSS `@media (min-width|max-width)` 与 `@container` 的宽度；Tailwind / UnoCSS / MUI / Ant 等框架的 `screens` / `breakpoints` 配置；主内容列的 `max-width`（列被截住居中之后，比它宽的窗口都是另一副样子，所以 max-width 本身是一个阈值）；JS 里对 `window.innerWidth` / `matchMedia` 的条件分支；侧栏折叠、栅格列数变化的宽度。`width_range`：桌面 Web 与 Electron / Tauri 的最小值取 `minWidth`（没有声明就取代码里最小的阈值之下一档），最大值不小于 1920（外接显示器），用户有更宽的显示器就取那个；移动 Web 的最小值取最窄的目标设备。

device 轴每个阈值两侧各一个值、并触到 `width_range` 两端，`matrix.py` 拒绝不满足的清单。用户说"我用 1512x982"，那只是其中一个值。可拉伸的桌面窗口另加 `resize-` 开头的状态（如 `resize-shrink-to-min`、`resize-grow-to-max`），录屏取证：拉动过程中的布局抖动和拉完后的重排是静态图看不到的。

## 截图模式与滚动：无头全页截图不是用户看到的画面

Playwright / Puppeteer 的无头浏览器默认带 `--hide-scrollbars`，滚动条宽度为 0（`window.innerWidth === document.documentElement.clientWidth`）；全页截图把整个文档一次铺开。这张图上有三类东西系统性地不存在，不是"没拍到"，是这种画面里根本没有：

- **滚动条本身**：有无、样式、gutter 占位；有头浏览器里 0–17px 的 gutter 会改变断点命中与横向布局，无头图永远命中"无 gutter"那一档。
- **滚动才出现的状态**：sticky / fixed 元素在全页图里只在顶部出现一次；吸顶、回到顶部按钮、滚动加载、scroll-snap、"折叠线以下的内容可达"在无头全页图里没有对应画面。
- **横向溢出的用户可见形态**：body 横向滚动被整页画布吞掉，图上看不出页面会左右晃。

因此每条 Web capture 必记四个字段，缺一条该 capture 不能支撑任何滚动类断言：
- `capture_mode`：`viewport`（真实视口一屏）或 `full_page`（整页铺开）。
- `headless`：true / false。
- `scrollbars`：`native`（有 gutter，页面读回 `innerWidth - clientWidth > 0`）、`hidden`（无头默认）、`overlay`（macOS 等系统的悬浮滚动条，gutter 为 0 但滚动时可见，这是真实用户条件，记系统设置为依据）。
- `scroll_profile`：在页面里读回的 `{scroll_width, client_width, scroll_height, client_height, gutter_px, overflow_x, overflow_y, nested_scrollers: [选择器]}`（`documentElement` 的四个尺寸、`innerWidth - clientWidth`、html/body 计算后的 overflow、`scrollHeight > clientHeight` 且 overflow 为 auto/scroll 的容器）。它是文本证据：`scroll_width > client_width` 本身就能落"页面横向溢出"的 gap，与截图模式无关。

滚动类断言只认 `capture_mode: viewport` 且 `scrollbars: native` 的图，且在声明的滚动位置各一张：普查时把会滚动的页面（目标视口下 `scroll_height > client_height`）在 inventory 标 `scrollable: true`，其 state 轴必须含滚动位置状态，命名以 `scroll-` 开头（`scroll-top`、`scroll-mid`、`scroll-bottom`，或 `scroll-sticky-header` 这类具名状态）；矩阵展开会拒绝标了 scrollable 却没有滚动状态的页面，校验器会拒绝用 full_page 或 hidden 滚动条的图裁滚动状态用例。只有无头全页证据时，滚动状态用例裁 unprovable，`visual_failure_ref` 写"无头全页截图无滚动条/无折叠线"，不从整页图推断。

拿到原生滚动条的办法：Playwright `chromium.launch({ headless: false })`，或无头下 `ignoreDefaultArgs: ['--hide-scrollbars']`；Chrome DevTools MCP 连接可见的 Chrome。用哪种写进 capture 的 `capture_tool`，并以页面读回的 `gutter_px` 为准，不以启动参数为准。

只操作本地/开发实例；写请求造成的副作用限于该实例。测试数据优先用已有合成数据；页面含真实敏感数据时停该项并交用户处理。同一浏览器上下文一次只由一个 prober 操作，独立上下文才可并发。构建标识 = commit 加工作树快照摘要（`git diff HEAD` 输出与全部未跟踪文件内容合并后的 SHA-256），有构建产物时再加 dist 目录摘要；同一提交上两次不同的未提交修改必须得到不同的 build，只写 commit 加 dirty 不够。dev server 热更新期间不采集，采集前后各算一次快照摘要，不一致则该批作废。
