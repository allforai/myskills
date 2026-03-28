# Experience Map 自适应深度

> 生成 experience-map 片段时按需加载。
> 本文档由 code-replicate-core.md 按需加载，不要提前阅读。

生成 experience-map 的 screen 片段时，LLM 对每个 screen 自主决定分析深度：

```json
{
  "screen": "chat_main",
  "depth": "deep",
  "depth_reasoning": "核心组件 MessageList 有 switch(message.type) 分出 74 个渲染分支，每个分支有独立交互行为。stub 级别只能记录 'MessageList 存在'，无法区分 74 种不同用户体验。",
  "complexity_signals": ["switch/enum 分支数: 74", "交互事件类型: click/longpress/drag/paste", "状态变体: loading/sending/failed/recalled"]
}
```

## LLM 判断 depth 的信号（非规则，推理参考）

- 该 screen 源文件 import 数量 > 10 → 可能需要 deep
- 存在 switch/if-else 链且分支 > 5 → 建议 deep
- 组件有多种交互事件（不只是 click）→ 建议 deep
- 纯展示型 screen（设置页/关于页）→ stub 足够

## depth = deep 时额外提取

1. **interaction_triggers**：对每个 component，追踪到**组件内部的事件绑定**，记录用户触发方式和预期响应（schema 见 `${CLAUDE_PLUGIN_ROOT}/docs/schemas/experience-map-extensions.md`）。不只是组件级别的"可点击"——要深入到子交互。trigger 类型覆盖：离散事件（tap/long_press）、手势组合（gesture_sequence）、连续手势（continuous_gesture，如拖拽进度条带实时反馈）、连续数据绑定（continuous_binding，如进度条/歌词高亮跟随播放位置）
2. **state_variants**：对每个 component，记录完整状态空间（超越默认 loading/error/empty）。同时追踪**远程事件驱动的状态**（trigger_source=remote_push）——源码中的 WebSocket/EventBus 监听器触发的 UI 状态变化
3. **枚举驱动渲染展开**：当检测到 switch/enum 模式且分支 > 5 时，逐分支提取为独立 component 或 variant 条目
4. **多步操作流**：识别需要多步才能完成的交互，将整条操作流记录在 interaction_triggers 中，每步单独列出
5. **条件渲染规则（render_rules）**：当同一 component 根据数据条件呈现不同布局时，记录各条件分支的渲染方式
6. **全局持久组件（global_components）**：识别不属于任何单一 screen 的跨页面组件，记录到 experience-map 顶层 `global_components[]`

## depth = deep 完成后：交互模式自查

LLM 对每个 depth=deep 的 screen，提取完 interaction_triggers 后执行一轮反向验证：

1. **事件绑定扫描**：回到该 screen 的源文件及其子文件，搜索所有事件绑定关键词（框架无关——LLM 根据源码技术栈自行确定关键词列表，如 Flutter: onTap/onLongPress/onPanUpdate/GestureDetector/Listener/Draggable/Dismissible；React: onClick/onDrag/onKeyDown/onTouchStart；原生: addTarget/addGestureRecognizer/setOnClickListener 等）
2. **逐个比对**：每个扫描到的事件绑定，检查是否已出现在 interaction_triggers 中
3. **补漏**：未出现的 → 判断是否为用户可感知交互（消失测试）→ 是 → 补充到 interaction_triggers

同样扫描远程事件监听：搜索 WebSocket/EventBus/Stream/BroadcastReceiver 等订阅模式，检查是否已出现在 state_variants（trigger_source=remote_push）中。

输出 self_check 摘要（不写文件，作为内部推理过程）：
- 扫描到事件绑定 N 个，已覆盖 M 个，补充 K 个
- 扫描到远程监听 N 个，已覆盖 M 个，补充 K 个

## depth = stub 时

保持现有行为——只记录顶层 component 列表 + 基本 states 字典。
