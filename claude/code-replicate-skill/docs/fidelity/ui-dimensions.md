# UI 还原维度 (U1-U6)

> 前端/客户端特有：experience-map 产物 vs 目标代码的 UI 实现。
> 仅当 experience-map.json 存在时加载。

## 评分通用规则

- "总数"来自 experience-map.json 中的 screens/components/states
- "匹配数"由 LLM 在目标代码中查找对应的 Page/View/Screen/Widget 文件
- 如果 `platform_adaptation` 存在，按 `ux_transformations` 调整期望（如 single_task → multi_panel 不算 gap）

---

## U1 — 屏幕覆盖

对比 experience-map 中所有 screens 与目标代码中的页面/视图文件：
- 每个源码 screen 是否有对应的目标页面文件？
- LLM 通过 screen.name + screen.tasks 在目标代码中定位等价页面
- 评分 = 已实现 screen 数 / 总 screen 数 × 100

## U2 — 路由/导航图

对比 experience-map 的 flow_context（prev/next）+ business-flows 的导航节点与目标代码的路由定义：
- 目标代码的 Router/Navigator/NavigationStack 是否定义了所有源码路由路径？
- 导航方向是否一致（A→B 在源码存在 → 目标也存在）？
- 路由参数传递是否保留？
- 深链接/外部入口是否保留？
- 评分 = 已实现路由数 / 总路由数 × 100

## U3 — 组件覆盖

对比 experience-map screens 中的 components[] 与目标代码的 UI 组件：
- **框架标准组件**（在 stack-mapping.auto_mapped 中有映射的，如 Ant Design Button → Element Plus el-button）→ 视为已覆盖，不逐个验证实现
- **自定义组件**（项目自建的共享组件，在 source-summary.abstractions 中记录的）→ 逐个验证：目标代码有等价实现吗？Props/Events API 是否等价？
- 共享组件（出现在多个 screen 中）是否被抽取为独立组件（而非每个页面内联实现）？
- 评分 = (框架映射组件数 + 已实现自定义组件数) / 总组件数 × 100

## U4 — 布局结构

对比 experience-map screens 的 layout_type + layout_description 与目标代码的布局：
- 目标页面的布局结构是否与源码等价？
- **不要求视觉一致**（颜色/字体/间距可以不同），要求**结构一致**（区域划分、层级关系、信息密度）
- 如果 `platform_adaptation.ux_transformations` 存在（如 single_task → multi_panel），按转换后的期望评估
- 评分 = 布局结构匹配的 screen 数 / 总 screen 数 × 100

## U5 — 状态渲染

对比 experience-map screens 的 states{} 与目标代码中的状态处理：
- 每个 screen 是否处理了所有定义的状态（empty/loading/error/success + 业务状态）？
- LLM 在目标代码中搜索条件渲染逻辑（if loading → skeleton, if error → retry button 等）
- 基类/共享组件提供的状态处理算作覆盖
- 评分 = 已处理状态数 / 总定义状态数 × 100

## U6 — 交互模式 + 控件联动

对比 experience-map screens 的 actions[] + interaction_pattern 与目标代码的事件处理：
- 每个 action（按钮点击、表单提交、手势操作）是否有对应的事件处理？
- 跨平台时：如果 `platform_adaptation.ux_transformations` 将 touch gesture 映射为 keyboard shortcut，按映射后的期望评估

**控件联动链验证**（interaction-recordings.json 存在时执行）：

对 interaction-recordings 中每个 `linkage_verify` 步骤，在源码和目标代码中分别追踪联动链：

```
源码联动链：triggerControl.onChange → API call / setState → targetControl.data 更新
目标联动链：是否有等价的触发→响应→更新链路？

检查项：
1. 触发端：事件处理函数是否存在且绑定到正确的控件？
2. 传递层：联动是通过 API 调用、状态管理、还是 computed/watch 传递的？目标代码用了等价机制吗？
3. 响应端：下游控件是否订阅/监听了正确的数据源？
4. 联动类型保真：源码是级联选择 → 目标也是级联（不是硬编码全量选项然后前端过滤）
```

- 联动链完整 = 覆盖
- 触发端存在但传递层断裂 = `LINKAGE_BROKEN`
- 触发端存在但响应端缺失 = `LINKAGE_PARTIAL`
- 整条链缺失 = gap

评分 = (已实现交互数 + 已保留联动链数) / (总定义交互数 + 总联动链数) × 100

## U7 — 素材还原

**适用条件**：asset-inventory.json 存在

对比 asset-inventory 与目标代码中的静态资源：

- **copy 类**：源文件是否已复制到目标项目？引用路径是否更新？
- **transform 类**：主题变量是否映射到目标框架？i18n 文案是否保留完整？
- **replace 类**：SVG 组件/图标库是否转换为目标框架格式？
- **代码引用完整性**：asset-inventory.code_refs 中的每个引用，在目标代码中是否有等价引用且路径正确？（缺失引用 → 运行时碎图/缺字体/key 显示）
- **主题一致性**：如果 asset-inventory.theme_system 存在，目标项目的主题变量数量是否覆盖源项目？（变量丢失 → 部分 UI 用框架默认样式）
- 评分 = 已还原素材类目数 / 总素材类目数 × 100
