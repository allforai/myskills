# SwiftUI 基线采集与确认

Adapted from wholiver/swiftui-design-skill; see UPSTREAM.md and LICENSE.

先读现有品牌、设计稿、Asset Catalog、Theme、公共组件，再打开运行中的代表页面。记录观察与冲突，不能把现状多数派直接认定为标准。

逐类向用户展示运行截图和候选规则，逐类确认：direction、color、typography、layout、spacing、icons、components、navigation、feedback、states、motion、environment。每类保存 rules、reference_images、confirmed_at、confirmation（用户原意）。无适用规则也需用户确认原因。

- 色彩：区分 accent、background、surface、textPrimary/Secondary、divider 和 success/warning/error；确认浅深色映射与文字可读性。
- 字体：确认标题、段落、元数据层级、字重、换行和动态字号行为。
- 布局：确认密度、边距、间距尺度、圆角、阴影；相同角色使用同一尺度，允许记录有理由的例外。
- 图标：确认 SF Symbols 或已有图标体系的大小、字重、基线和语义。
- 组件：确认按钮、列表、卡片、表单及各状态的共同外观。
- 交互：确认导航返回、Tab、Sheet 的展示/关闭、危险操作、表单验证和反馈。
- 环境：列出支持的具体设备/OS、外观、字号、语言、方向和状态值；不能用“所有设备”等不可枚举描述。

上游的暖色、衬线标题、禁止某类渐变、每屏一个特色细节是风格偏好，只能提出候选。现有品牌与用户选择优先。不自动搜索下载素材、不生成或改写产品代码。
