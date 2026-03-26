# Step 4.5: 控件数据完整性审计

> 本文档由 cr-visual orchestrator 派遣的 **data-integrity agent** 加载。
> 职责：检查每个 screen 中数据绑定控件是否有真实数据，空控件强制溯源。
> **本 agent 只关注数据完整性**，不做结构对比和联动验证。

## 核心原则

Step 4 检查的是"控件在不在"，本步骤检查的是"控件里有没有数据"。两步缺一不可。

## 扫描协议

对每个 screen 的目标截图，LLM 逐一扫描以下控件类型，对照源截图判断数据完整性：

**1. 数据容器类**：DataGrid / Table / List / Tree / TreeView
- 源截图有 N 行数据 → 目标必须有 ≥1 行真实数据（不要求行数完全一致）
- 表头/列字段是否与源一致？
- Tree 展开后是否有子节点？

**2. 选择器类**：ComboBox / Select / Dropdown / RadioGroup / Checkbox Group
- 源截图有可选项 → 目标不能为 0 个选项
- 如有可能，自动化点击/展开选择器 → 截图验证选项列表非空

**3. 显示绑定类**：TextInput / Label / Badge / Counter / Chip / Tag
- 源截图显示了绑定值（如 "John Doe"、"¥128.00"）→ 目标不能是空白、"undefined"、"null"、"NaN"
- placeholder 不算绑定值

**4. 可视化类**：Chart / Graph / Dashboard Widget / ProgressBar / Sparkline
- 源截图有数据渲染 → 目标不能是空坐标轴/空饼图/进度条为 0
- **Canvas/WebGL 图表不能只靠 LLM 看截图**（LLM 看不出"少了两个数据点"）：
  - 降级验证：用 `pixelmatch` 对比源/目标的 Canvas 区域截图，差异率 > 5% → 标记 `CANVAS_DRIFT`，交人类复核
  - 数据源校验（更强）：拦截驱动图表的 API 请求（Playwright `page.on('response')` 捕获），对比源/目标的 API payload — 数据一致 = 渲染一致的最强基石

**4.5. 多媒体真实性**：img / video / audio / background-image
- **图片**：不是灰色方块、不是 "Image Not Found"、不是默认占位符水印 → LLM 必须审查图片内容本身
  - 如果 capture agent 标记了 BROKEN_MEDIA（资源 404/500）→ 该 screen 直接 mismatch
- **视频/音频**：如果 capture agent 标记了 DEAD_MEDIA（paused/readyState 异常）→ 标记 gap
  - penalty: BROKEN_MEDIA = -20, DEAD_MEDIA = -15

**5. 分页/滚动加载类**：Pagination / InfiniteScroll / "加载更多" 按钮
- 源截图有分页控件 → 目标也必须有（不能只显示第一页数据而没有翻页能力）
- 源截图显示"共 X 页"或"共 N 条" → 目标的总数是否合理（不是 0 也不是 undefined）
- 无限滚动的列表 → 目标是否有"加载更多"的触发机制（按钮/滚动检测）

## 深度验证（超越"有没有"，检查"对不对"）

> 以下检查在基础"非空"扫描之后执行，仅对非空控件进行。

**5. 数据归属验证**（role-view-matrix.json 存在时执行）

如果当前截图是以某角色登录后拍摄的，验证该角色看到的数据是否仅属于其权限范围：

```
对每个数据容器（Table/List）：
  1. 识别数据中的归属标识（owner_id、user_id、department、role 等字段）
  2. 对照 role-view-matrix → 该角色是否应该看到这些数据？
  3. 发现跨权限数据（如普通用户看到了管理员的记录）→ 标记 PERMISSION_LEAK
  4. penalty: -20（比空数据更严重 — 这是安全问题）
```

**6. 数据排列对比**（Table/List/Tree 类控件）

不只检查"有数据"，还检查数据的排列是否与源截图语义一致：

```
对每个 Table/List：
  1. 对比源截图和目标截图的首行数据 — 是否是同类内容？
     （源截图首行是最新订单 → 目标首行也应该是最新的，不是最旧的）
  2. 对比排序方向 — 源是时间倒序，目标不应该是正序
  3. 对比分组/分类 — 源按状态分组，目标也应该分组
  4. 发现排列不一致 → 标记 ORDER_MISMATCH
  5. penalty: -5（功能性问题，不是空数据那么严重）
```

## 溯源协议

对每个空控件，强制溯源：

```
1. 标记为 data_integrity_gap，记录控件类型 + screen + 控件位置描述
2. 读目标代码 → 找该控件的数据来源：
   a. API 接口？→ 检查接口 URL 是否正确、是否被调用、响应是否为空、字段映射是否正确
   b. 静态数据/枚举？→ 检查是否缺少初始化数据或枚举定义
   c. 计算/派生值？→ 检查计算逻辑是否有 null/undefined 路径
   d. 状态管理？→ 检查 store/state 是否正确初始化和订阅
3. 记录溯源结果：{ control_type, location, data_source, root_cause }
```

## 评分

```
每个 data_integrity_gap 的扣分：
  - 空数据容器（Table/List/Tree 零行）      → -15 分
  - 空选择器（ComboBox/Select 零选项）       → -10 分
  - 空绑定值（Label/Badge 显示空白/undefined）→ -5 分
  - 空可视化（Chart 无数据渲染）             → -15 分
  - 权限穿透（PERMISSION_LEAK）              → -20 分（安全问题，最高优先修复）
  - 排列不一致（ORDER_MISMATCH）             → -5 分
  - 媒体资源缺失（BROKEN_MEDIA）             → -20 分（资源 404/500，非视觉差异是资源断裂）
  - 流媒体不工作（DEAD_MEDIA）               → -15 分（video/audio 卡死/暂停/解码错误）
  - Canvas 图表偏差（CANVAS_DRIFT）           → -10 分（pixelmatch 差异率 > 5%，需人工复核）
```

## 禁止项

- ❌ **不得用硬编码假数据修复**（如在前端写死 `["选项1", "选项2"]` 或 `[{name: "测试"}]`）
- ❌ **不得用 mock server 替代真实 API**
- ❌ **不得仅在截图前临时注入数据**（如 `localStorage.setItem` 塞假数据）
- ✅ **必须修复真实数据链路**：前端组件 → API 调用 → 后端逻辑 → 数据库查询
- ✅ **修复后重新截图验证**该控件确实有真实数据显示

## 输出

对每个 screen 返回：
```json
{
  "screen": "screen name",
  "data_integrity_score": 85,
  "data_integrity_gaps": [
    {
      "control_type": "DataGrid",
      "location": "页面中部-订单列表区域",
      "expected": "源截图有 8 行订单数据",
      "actual": "目标截图表头存在但 0 行数据",
      "data_source": "API: GET /api/orders",
      "root_cause": "前端调用了 /api/order（少了 s），404 后静默失败",
      "penalty": -15
    }
  ]
}
```
