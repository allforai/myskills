# experience-map.json — Code-Replicate Extensions

> 以下字段是 code-replicate 对标准 experience-map schema 的扩展。product-design 不生成这些字段。字段均为可选——depth=stub 的 screen 不包含。
> 本文档在生成 experience-map 片段、cr-fidelity U6 评分时按需加载。

## components[].interaction_triggers（可选，depth=deep 时填充）

记录用户触发方式和预期响应。用于 cr-fidelity U6 评分和 Completeness Sweep 维度 B 验证。

```json
{
  "component": "MessageBubble",
  "interaction_triggers": [
    {"trigger": "tap", "target": "图片消息", "response": "全屏预览"},
    {"trigger": "long_press", "target": "任意消息", "response": "操作菜单（转发/收藏/删除）"},
    {"trigger": "double_tap", "target": "文本消息", "response": "文本选择模式"}
  ]
}
```

**字段说明**：
- `trigger` — 用户交互事件类型（tap/click/long_press/drag/drop/paste/keydown/hover 等），或特殊类型（见下）
- `target` — 触发该交互的具体目标（消息类型/按钮/区域）
- `response` — 预期的 UI 响应（页面跳转/弹窗/状态变化/动画）

### trigger 类型总览

| trigger 值 | 用途 | 额外字段 |
|-----------|------|---------|
| tap/click/long_press/... | 离散事件 | 无（或 `conditional_responses` 用于 1:N 结果） |
| `gesture_sequence` | 多步手势组合 | `sequence` |
| `continuous_gesture` | 连续手势+实时反馈 | `gesture`, `realtime_feedback`, `release_behavior` |
| `continuous_binding` | 连续数据驱动渲染 | `data_source` |

**上下文依赖的交互结果**（任何 trigger 类型均可搭配）：

当同一交互根据运行时数据产生不同结果时，用 `conditional_responses` 替代单一 `response`：

```json
{
  "trigger": "tap",
  "target": "扫描结果",
  "conditional_responses": [
    {"condition": "LLM 描述条件（如 扫描内容匹配用户 ID 格式）", "response": "LLM 描述结果（如 跳转添加好友确认页）"},
    {"condition": "LLM 描述条件（如 扫描内容匹配支付链接格式）", "response": "LLM 描述结果（如 跳转支付页）"},
    {"condition": "LLM 描述条件（如 扫描内容为 URL）", "response": "LLM 描述结果（如 内置浏览器打开）"}
  ]
}
```

LLM 从源码的 if/switch 分支中提取条件和结果。如果只记录单一 response，复刻时只实现一种分支，其余全部丢失。

### 手势组合（trigger = gesture_sequence）

单一 trigger 无法表达复合交互。`sequence` 记录手势链的每一步：

```json
{
  "trigger": "gesture_sequence",
  "sequence": ["long_press:录音按钮", "swipe_up:不松手"],
  "target": "录音按钮",
  "response": "录音锁定模式（免持录音，松手后继续录制）"
}
```

### 连续手势（trigger = continuous_gesture）

用户手指移动过程中 UI 实时跟随，松手后可能有物理惯性动画：

```json
{
  "trigger": "continuous_gesture",
  "gesture": "LLM 描述手势类型（如 垂直拖拽/水平拖拽/双指缩放）",
  "target": "LLM 描述被操作的 UI 元素",
  "realtime_feedback": "LLM 描述拖拽过程中的实时视觉反馈",
  "release_behavior": "LLM 描述松手后的行为（如 弹簧动画展开/弹回、惯性滚动、吸附到最近位置）"
}
```

### 连续数据绑定（trigger = continuous_binding）

UI 每帧跟随一个连续变化的数据值更新。不是用户直接触发，而是数据流驱动：

```json
{
  "trigger": "continuous_binding",
  "data_source": "LLM 描述驱动数据（如 playbackPosition stream / downloadProgress / sensorData）",
  "target": "LLM 描述被驱动的 UI 元素",
  "response": "LLM 描述视觉效果（如 进度条位置实时更新 / 文本逐行高亮跟随 / 波形亮度渐变）"
}
```

LLM 在 deep 分析时，搜索源码中的 stream 订阅 / AnimationController / ValueListenable / Observable 等持续数据绑定模式来发现此类交互。

---

## components[].state_variants（可选，depth=deep 时填充）

记录组件的完整状态空间，超越默认的 loading/error/empty。

```json
{
  "component": "VoiceMessage",
  "state_variants": [
    {"state": "recording", "visual": "红色脉冲动画 + 时长计数"},
    {"state": "recorded_preview", "visual": "波形图 + 播放/删除按钮"},
    {"state": "sending", "visual": "上传进度条"},
    {"state": "sent", "visual": "静态波形 + 时长标签"},
    {"state": "playing", "visual": "播放进度动画 + 暂停按钮"},
    {"state": "expired", "visual": "灰色 + '已过期' 标签"}
  ]
}
```

**字段说明**：
- `state` — 状态名称
- `visual` — 该状态的视觉表现描述
- `trigger_source`（可选）— `local`（用户操作触发，默认）或 `remote_push`（服务端推送触发）
- `event`（可选）— 当 trigger_source = remote_push 时，记录触发事件

**远程事件驱动状态**：

许多应用的 UI 状态由服务端推送驱动，而非用户本地操作（如实时协作状态、推送通知、数据同步进度等）。LLM 在 deep 分析时应同时追踪源码中的 WebSocket/EventBus/Push 监听器和 UI 状态绑定。如果只追踪 local 触发的状态，所有 push-driven UI 都会遗漏。

```json
{
  "component": "SyncStatusBar",
  "state_variants": [
    {"state": "syncing", "visual": "旋转图标 + '同步中...'", "trigger_source": "remote_push", "event": "sync.started"},
    {"state": "synced", "visual": "对勾 + '已同步'", "trigger_source": "remote_push", "event": "sync.completed"},
    {"state": "offline", "visual": "警告图标 + '离线模式'", "trigger_source": "remote_push", "event": "network.lost"}
  ]
}
```

---

## components[].render_rules（可选，depth=deep 时填充）

记录条件渲染规则——同一组件根据数据条件呈现不同布局/外观。消失测试：如果条件渲染变成统一渲染，用户会注意到视觉差异。

```json
{
  "component": "ItemGrid",
  "render_rules": [
    {"condition": "items.length = 1", "layout": "单项全宽"},
    {"condition": "items.length = 2", "layout": "双列等宽"},
    {"condition": "items.length >= 3", "layout": "网格布局，每行最多3列"}
  ]
}
```

**字段说明**：
- `condition` — 渲染分支条件（自然语言描述，LLM 从源码 if/switch 中提取）
- `layout` — 该条件下的布局/渲染方式

---

## global_components[]（顶层字段，与 operation_lines 平级）

记录不属于任何单一 screen 的全局持久组件。这些组件跨页面存在，在 per-screen 的 components 中无法表达。

LLM 在 deep 分析时应主动搜索以下模式来发现 global_components：
- 在 app 根层级（MaterialApp/Scaffold 之上）注册的 overlay/persistent widget
- 跨页面共享的 state（如全局播放状态、通话状态、网络状态）
- 在路由切换时不销毁的组件

```json
{
  "global_components": [
    {
      "id": "GC001",
      "name": "LLM 命名",
      "type": "persistent_overlay | status_bar | background_service",
      "visible_on": "LLM 描述可见条件",
      "multiplicity": {
        "type": "static | dynamic",
        "max_instances": "LLM 从源码中提取（static 时为 1，dynamic 时为具体数字或 unbounded）",
        "lifecycle": "LLM 描述实例创建/销毁方式（仅 dynamic 时需要）"
      },
      "interaction_triggers": ["...同 per-screen components schema..."],
      "state_variants": ["...同 per-screen components schema..."]
    }
  ]
}
```

**multiplicity 说明**：
- `static`（默认）— 固定单实例（如网络状态指示器、迷你播放器）
- `dynamic` — 用户运行时创建/销毁，多实例并存（如浮窗、画中画）。`max_instances` 记录上限，`lifecycle` 描述创建/销毁触发条件

**字段说明**：
- `type` — `persistent_overlay`（浮动覆盖层，如播放器、通话浮窗）/ `status_bar`（状态栏，如网络/同步状态）/ `background_service`（后台服务 UI，如下载进度通知）
- `visible_on` — 在哪些页面/条件下可见（自然语言）
- `interaction_triggers` 和 `state_variants` — 与 per-screen components 相同的 schema

---

## 向后兼容性

所有扩展字段均为可选。不填充时，现有 experience-map 消费者（dev-forge、cr-fidelity U1-U5）不受影响。cr-fidelity U6 和 Completeness Sweep 维度 B 读取这些字段时，字段不存在视为"未做 deep 分析"，不扣分。`global_components` 不存在时视为无全局组件。
