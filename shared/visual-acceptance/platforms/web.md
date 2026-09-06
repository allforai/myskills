# Web 运行适配

这是取证适配，视觉规则仍按 visual-acceptance.md 逐类与用户确认；本文只定义 Web 目标怎么普查、怎么把七个维度施加到真实浏览器、怎么留证据。先检测包管理器与启动命令（package.json scripts、Vite/Next/CRA 配置、Docker compose），从工程已有命令确定如何起本地服务；不猜端口，以启动日志或配置为准。

普查页面与实际入口：路由表（React Router / Next app 或 pages 目录 / Vue Router / SvelteKit routes）、导航与 Tab、Modal / Drawer / Toast / Popover、受权限与登录态影响的分支、响应式断点下出现或消失的入口。组件不都等于页面，标明顶级页面、组件、弹层及实际可达性；动态注册（运行时拉取的菜单、按角色下发的路由）未知需 could_not。

七个维度对 Web 的取值，全部在 environment 类由用户确认为具体值：
- device：视口宽高加设备像素比，如 `1440x900@2`、`390x844@3`；不写"桌面"或"所有手机"。
- os：浏览器引擎与主版本，如 `Chromium 131`、`WebKit 18`；同一引擎不同版本按用户确认是否分列。
- appearance：`prefers-color-scheme` 的 light / dark，另加站点自身主题开关的值（如果有）。
- dynamic_type：浏览器缩放或根字号，如 `zoom 100%`、`zoom 150%`、`font-size 20px`；站点不响应缩放时取单一值 `zoom 100%`，依据（例如 CSS 未使用 rem/em）记在 environment 类的确认里。
- locale：浏览器语言加站点语言开关的值。
- orientation：`landscape` / `portrait`；桌面视口取单一值 `landscape`，依据记在 environment 类的确认里。
- state：加载、空、错误、权限拒绝、离线、键盘弹出（移动）等，按页面归入。

维度没有"不适用"：每个维度都是非空的具体值列表，某维度对该产品无意义就取一个值并记依据。整条用例的 applicability: not_applicable 只留给组合本身不可能存在的情况（如某页面在某设备上根本不可达），须有 reason 与 basis。

施加与核对：优先本机可见窗口工具或页面自动化工具（Playwright MCP、Chrome DevTools MCP、playwright-cli），用它们的 resize / emulate / 颜色方案 / locale 接口设置维度，然后在页面里核对真正生效（`window.innerWidth`、`matchMedia('(prefers-color-scheme: dark)')`、`document.documentElement.lang`、计算后的根字号），核对结果写进 capture。无法施加的维度记无法自证，不凭截图元数据补。截图取全页或视口，按用例记录；motion 用录屏或按时间戳抓帧，静态截图不证明动画。

只操作本地/开发实例；写请求造成的副作用限于该实例。测试数据优先用已有合成数据；页面含真实敏感数据时停该项并交用户处理。同一浏览器上下文一次只由一个 prober 操作，独立上下文才可并发。构建标识 = commit 加工作树快照摘要（`git diff HEAD` 输出与全部未跟踪文件内容合并后的 SHA-256），有构建产物时再加 dist 目录摘要；同一提交上两次不同的未提交修改必须得到不同的 build，只写 commit 加 dirty 不够。dev server 热更新期间不采集，采集前后各算一次快照摘要，不一致则该批作废。
