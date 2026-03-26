---
name: cr-visual
description: >
  Use when user wants to "compare UI visually", "视觉还原", "截图对比",
  "UI 还原度", "看看界面像不像", "visual comparison", "screenshot diff",
  or mentions comparing source and target app screenshots for UI fidelity.
---

# 视觉还原度 — CR Visual v1.1

> 源 App vs 目标 App 逐屏截图/录像 → 对比 → 修复 → 重新对比 → 直到视觉一致

## 定位

cr-visual 是复刻流程的**最后一步** — 在 cr-fidelity + product-verify + testforge 全部通过后执行。

```
cr-fidelity → product-verify → testforge → cr-visual（这里）
```

**前置条件**：测试全绿，App 能稳定运行。截图对比需要 App 正常工作。

**平台差异自动排除**：如果 `stack-mapping.json` 含 `platform_adaptation` → cr-visual 启动时自动加载转换规则。符合 platform_adaptation 的差异（如移动端底部导航 → 桌面端侧边栏）自动标记为 `not_a_gap`，LLM 对比时直接跳过不扣分，不需要用户手动提示。

**多角色对比**：如果 `role-view-matrix.json` 存在 → 逐角色截图并分别对比。

**交互行为对比**：如果 `interaction-recordings.json` 存在 → 源 App 的证据已在 Phase 2.13 采集。cr-visual 对目标 App 执行**同样的业务流程链**：

逐 flow 执行（按 interaction-recordings.json 的 flows 结构）：
1. 按 flow.steps 在目标 App 上执行同样的操作序列（角色切换、填表、点击、等待）
2. 在每个 screenshot 里程碑截图 → 与源 App 的对应截图对比
3. 同时采集目标 App 的 API 日志 → 与源 App 的 api.json 对比

五层验证：
1. **静态页面**：源截图 vs 目标截图 → 布局/组件/数据展示一致吗？
2. **CRUD 全状态**：flow 链自然覆盖 CRUD 生命周期 → 逐里程碑截图对比
3. **动态效果**（type=visual_effect 的 flow）：源录像 vs 目标录像 → 动画/过渡一致吗？
4. **API 日志**：源 api.json vs 目标 api.json → 同样的操作触发了同样的请求吗？
5. **综合**：同一 flow → 每个里程碑截图 + API 都一致 = high

每个交互输出 match_level: high / medium / low / mismatch

---

## 流程

```
Step 1: 获取 screen 列表（从 experience-map）
Step 2: 获取源 App 截图/录像（Phase 2 已采集 or 现场采集）
Step 3: 获取目标 App 截图/录像
Step 4: LLM 逐屏对比（结构级 + 动态效果）
Step 4.5: 控件数据完整性审计（空控件溯源 + 评分修正）
Step 4.6: 控件联动验证（interaction-recordings 有 linkage_verify 时执行）
Step 5: 差异报告 + 评分
Step 6: 修复差异（LLM 修改目标代码）
Step 7: 重新截图/录像 → 重新对比 → 达标退出
```

`full` 模式 = Step 1-7 闭环（最多 3 轮）
`analyze` 模式 = Step 1-5 仅出报告
`fix` 模式 = Step 6-7 基于上次报告修复

---

## Step 1: Screen 列表 + 路由映射

从 `.allforai/experience-map/experience-map.json` 提取所有 screen，建立路由映射：

```
1. 从 experience-map 提取每个 screen 的 name、route（如有）、layout_type
2. 读 .allforai/code-replicate/visual/route-map.json（Phase 2c-visual 生成的路由→截图映射）
3. 建立配对：screen name ↔ route path ↔ 源截图文件名
   - experience-map screen 有 route → 直接匹配 route-map
   - experience-map screen 无 route → LLM 按 screen name 和 route-map 的语义相似度匹配
4. 跳过无法配对的 screen
```

---

## Step 1.5: 源 App 启动信息

cr-visual 需要知道怎么启动和导航源 App。信息来源（优先级）：

1. **replicate-config.json 的 `source_app` 字段**（code-replicate Phase 1 收集）：
   ```json
   "source_app": {
     "start_command": "npm run dev",
     "backend_start_command": "cd server && npm start",
     "seed_command": "npm run db:seed",
     "url": "http://localhost:3000",
     "login": {
       "username": "test@example.com",
       "password": "test123",
       "bypass_command": "设置环境变量/API调用来绕过2FA（如有）"
     },
     "platform": "web | mobile | desktop"
   }
   ```
   Phase 1 Preflight 时 LLM 应向用户询问：
   - 源 App 如何启动？需要先启动后端吗？
   - 有测试数据吗？seed 命令是什么？
   - 需要登录吗？有验证码/2FA 吗？怎么绕过？

2. **用户通过 `--source` 参数直接提供 URL**

3. **用户通过 `--screenshots` 提供已有截图**

如果 replicate-config 没有 `source_app` 且用户未传参 → 询问用户源应用信息（这是继续执行的必需条件）。

---

## Step 2: 源 App 截图

**方式 A（首选）— Phase 2 已采集**：
- 检查 `.allforai/code-replicate/visual/source/` 是否已有截图
- 已有 → 直接复用（Phase 2c-visual 在复刻早期已自动采集，此时源项目环境可能已不在）

**方式 B — 用户提供截图目录**：
- 读取 `--screenshots` 目录中的图片文件
- LLM 将图片文件名与 experience-map screen name 配对

**方式 C — 源 App 仍可运行**：
- 按 Phase 2c-visual 的完整协议执行（启动后端 → seed 数据 → 启动前端 → 登录 → 截图）
- 任何前置条件失败（后端不可用、数据库为空、登录失败）→ 不截图，报具体失败原因

**无截图可用** → 报错退出：「源 App 截图不可用。请提供 --screenshots 目录，或确保源 App 环境完整（后端 + 数据 + 登录凭证）」

---

## Step 3: 目标 App 截图

**截图工具由 LLM 根据目标技术栈自行决定**。LLM 读项目技术栈 → 选择合适的自动化工具 → 用 Bash 执行截图命令。

LLM 读目标项目的技术栈 → 自行搜索并选择适合该技术栈的 UI 自动化工具 → 用 Bash 执行截图命令。不限定工具列表。

**如果 LLM 找不到可用的自动化工具** → 提示用户手动截图到 `visual/target/`。这是最后兜底，不是默认行为。

---

## Step 4: LLM 逐屏对比

对每对截图（source/screen_name.png vs target/screen_name.png），LLM 用 Read 查看两张图片，评估：

**结构级对比（做）**：
- 区域划分是否等价？（头部/内容/底部/侧边栏）
- 关键 UI 元素是否存在？（按钮、输入框、列表、卡片）
- 数据展示区域的位置是否合理？
- 导航入口是否可见？（菜单、Tab、返回按钮）
- 信息层级是否一致？（标题 > 副标题 > 正文的层次感）

**不做**：
- 像素级颜色对比（目标可以换主题色）
- 字体/字号精确匹配（目标可以用不同字体）
- 间距/留白精确匹配（目标可以重新设计间距）
- 动画/过渡效果（截图看不到）

**跨平台调整**：
- 如果 stack-mapping 有 `platform_adaptation.ux_transformations`
- 按转换期望评估：mobile 单列 → desktop 多面板不算 gap
- mobile 底部导航 → desktop 侧边栏不算 gap

**每个 screen 输出**：
```json
{
  "screen": "screen name",
  "structural_match": "high | medium | low | mismatch",
  "structural_score": 100 | 70 | 40 | 0,
  "differences": "LLM 自由描述差异",
  "source_screenshot": "visual/source/xxx.png",
  "target_screenshot": "visual/target/xxx.png"
}
```

> 注意：此阶段仅输出 `structural_match` / `structural_score`，最终的 `match_level` / `score` 在 Step 4.5 之后合并计算。

---

## Step 4.5: 控件数据完整性审计

> Step 4 检查的是"控件在不在"，Step 4.5 检查的是"控件里有没有数据"。两步缺一不可。

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

**对每个空控件，强制溯源**：

```
1. 标记为 data_integrity_gap，记录控件类型 + screen + 控件位置描述
2. 读目标代码 → 找该控件的数据来源：
   a. API 接口？→ 检查接口 URL 是否正确、是否被调用、响应是否为空、字段映射是否正确
   b. 静态数据/枚举？→ 检查是否缺少初始化数据或枚举定义
   c. 计算/派生值？→ 检查计算逻辑是否有 null/undefined 路径
   d. 状态管理？→ 检查 store/state 是否正确初始化和订阅
3. 记录溯源结果：{ control_type, location, data_source, root_cause }
```

**评分修正**：

```
每个 data_integrity_gap 的扣分：
  - 空数据容器（Table/List/Tree 零行）      → -15 分
  - 空选择器（ComboBox/Select 零选项）       → -10 分
  - 空绑定值（Label/Badge 显示空白/undefined）→ -5 分
  - 空可视化（Chart 无数据渲染）             → -15 分

合并计算最终分数：
  final_score = structural_score - sum(data_integrity_penalties)
  final_score = max(0, final_score)  // 不低于 0

match_level 由 final_score 决定：
  ≥ 90 → high | ≥ 60 → medium | ≥ 30 → low | < 30 → mismatch
```

**禁止项**：

- ❌ **不得用硬编码假数据修复**（如在前端写死 `["选项1", "选项2"]` 或 `[{name: "测试"}]`）
- ❌ **不得用 mock server 替代真实 API**
- ❌ **不得仅在截图前临时注入数据**（如 `localStorage.setItem` 塞假数据）
- ✅ **必须修复真实数据链路**：前端组件 → API 调用 → 后端逻辑 → 数据库查询
- ✅ **修复后重新截图验证**该控件确实有真实数据显示

**每个 screen 最终输出**（合并 Step 4 + 4.5）：
```json
{
  "screen": "screen name",
  "match_level": "high | medium | low | mismatch",
  "score": 85,
  "structural_score": 100,
  "data_integrity_score": 85,
  "differences": "结构完整，但订单列表 DataGrid 为空（0行），状态筛选 ComboBox 无选项",
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
  ],
  "source_screenshot": "visual/source/xxx.png",
  "target_screenshot": "visual/target/xxx.png"
}
```

---

## Step 4.6: 控件联动验证

> **前置条件**：`interaction-recordings.json` 存在且含 `linkage_verify` 步骤。无此文件或无联动步骤 → 跳过。

Step 4/4.5 检查的是静态状态（截图里看到什么），Step 4.6 检查的是**动态因果**（操作 A → B 是否正确响应）。

**执行协议**：

对 interaction-recordings 中每个 `linkage_verify` 步骤：

```
1. 在目标 App 上执行 trigger_action（如 select "广东省"）
2. 等待联动响应（短暂 wait，通常 500ms-2s）
3. 逐个验证 expected_effects：

   options_update（级联选择）：
     → 展开下游选择器 → 截图 → 选项列表非空且内容与触发值关联
     → 与源 App 同步骤截图对比

   visibility_toggle（条件显隐）：
     → 检查目标控件的 visible 状态变化
     → 截图验证：控件出现/消失与源 App 一致

   enabled_toggle（条件启禁）：
     → 检查目标控件的 disabled/enabled 状态
     → 截图对比或 DOM 属性检查

   value_update（自动计算）：
     → 读取目标控件的显示值
     → 与源 App 的对应值对比（或根据已知公式验证正确性）
     → 特别关注：NaN、0、空白 = 计算链路断裂

   data_filter（联动筛选）：
     → 切换后截图 → 表格/列表内容是否正确过滤
     → 行数变化是否合理（不是全量也不是零行）

   detail_load（主从联动）：
     → 点击主控件某行 → 截图详情区域
     → 详情内容是否对应被点击行的数据（强断言：字段值匹配）

   reset（联动重置）：
     → 上级变化后 → 下级是否正确清空/恢复默认

4. 每个联动检查点输出：
   - linkage_result: pass / fail / partial
   - 失败时记录：trigger_control、target_control、effect_type、expected、actual
```

**评分影响**：

```
每个联动检查点的结果：
  pass    → 不扣分
  partial → -5 分（联动触发了但结果不完全正确，如选项有但内容不对）
  fail    → -10 分（联动完全无效，下游控件无响应）

联动分独立计算，追加到 screen 的 final_score：
  final_score = structural_score - data_integrity_penalties - linkage_penalties
```

**每个 screen 最终输出增加 linkage 字段**：
```json
{
  "linkage_results": [
    {
      "trigger_control": "省份下拉框",
      "trigger_action": "select 广东省",
      "target_control": "城市下拉框",
      "effect_type": "options_update",
      "result": "fail",
      "expected": "选项更新为广东省城市",
      "actual": "选项列表仍为空",
      "root_cause": "onChange 未调用 fetchCities()，事件绑定丢失",
      "penalty": -10
    }
  ],
  "linkage_score": 90
}
```

---

## Step 5: 报告

写入 `.allforai/code-replicate/visual-report.json` + `visual-report.md`：

```json
{
  "generated_at": "ISO8601",
  "total_screens": 20,
  "compared": 18,
  "skipped": 2,
  "overall_score": 68,
  "structural_avg_score": 82,
  "data_integrity_avg_score": 65,
  "linkage_avg_score": 75,
  "total_data_integrity_gaps": 7,
  "total_linkage_failures": 3,
  "screens": [
    {
      "screen": "...", "match_level": "high", "score": 100,
      "structural_score": 100, "data_integrity_score": 100, "linkage_score": 100,
      "differences": "无明显差异", "data_integrity_gaps": [], "linkage_results": []
    },
    {
      "screen": "...", "match_level": "low", "score": 35,
      "structural_score": 70, "data_integrity_score": 55, "linkage_score": 80,
      "differences": "列表布局从卡片式变成了表格式，缺少筛选栏",
      "data_integrity_gaps": [
        {"control_type": "DataGrid", "location": "...", "root_cause": "...", "penalty": -15}
      ],
      "linkage_results": [
        {"trigger_control": "...", "target_control": "...", "effect_type": "options_update", "result": "fail", "penalty": -10}
      ]
    }
  ]
}
```

`visual-report.md` 包含：
- 每个 screen 的截图路径对（用户可直接查看）
- 结构差异描述
- **数据完整性审计结果**（空控件清单 + 溯源结论）
- **控件联动验证结果**（联动检查点清单 + 失败根因）
- 整体评分（结构分 + 数据完整性分 + 联动分 = 综合分）
- 低分 screen 的修复方案（区分结构修复 / 数据链路修复 / 联动修复）

---

## Step 6+7: 修复闭环 — 调用 ralph-loop

视觉还原追求 **100% 一致**，不是"差不多就行"。使用 ralph-loop 持续修复直到完美。

**启动 ralph-loop**：

```
启动视觉还原修复循环（ralph-loop pattern）

每轮执行:
  1. 读 visual-report.json → 找到 match_level ≠ high 的 screen
  2. 按 score 从低到高排序 → 取最低分的 1 个 screen
  3. 读源截图/录像 + 目标截图/录像 → 识别具体差异
  4. 诊断根因层级：
     LLM 看截图/录像差异 → 判断根因在哪一层：

     UI 层（直接修）:
       - 布局结构 → 改模板/CSS
       - 组件缺失 → 补组件
       - 主题变量 → 修正变量值
       - 素材缺失 → 补图标/图片/字体
       - 动画缺失 → 补 CSS transition / 动画代码

     数据完整性层（Step 4.5 标记的 data_integrity_gap → 按溯源结果修）:
       - API 未调用/URL 错误 → 修前端 API 调用代码
       - API 返回空 → 检查后端查询逻辑/数据库是否有数据 → 修后端或补 seed
       - 字段映射错误 → 修前端数据绑定（如 response.data vs response.result）
       - 枚举/静态选项缺失 → 补枚举定义（禁止硬编码假数据，必须来自配置或 API）
       - Store/State 未初始化 → 修状态管理初始化逻辑
       ⚠️ 禁止用硬编码假数据蒙混：前端写死选项/行数据 = 修复无效，必须走真实数据链路

     联动层（Step 4.6 标记的 linkage fail/partial → 按联动类型修）:
       - 事件绑定丢失 → 补 onChange/onSelect/onClick 绑定到正确的处理函数
       - 联动 API 未调用 → 修事件处理函数，补调用下游数据获取逻辑
       - 联动状态未传递 → 修 setState/dispatch/emit，确保下游控件订阅了正确的数据源
       - computed/watch 缺失 → 补响应式计算链（如 quantity × price → total）
       - 条件显隐逻辑缺失 → 补 v-if/v-show/visible 绑定条件
       - 条件启禁逻辑缺失 → 补 disabled 绑定条件
       - 联动重置缺失 → 上级变化时 reset 下级控件的值和选项
       ⚠️ 修复后必须重新执行 linkage_verify 验证联动恢复正常

     非 UI 层（根因升级 → 修完回来）:
       - 权限按钮未隐藏 → 检查 RBAC 逻辑 → 可能是 role-view-matrix 未还原 → 修权限代码
       - 请求报错 → 检查错误码 → 可能是 error-catalog 不一致 → 修错误定义
       - 图标/字体碎裂 → 检查 asset 引用 → 可能是 asset 迁移遗漏 → 补 asset
       - 基础设施差异 → 检查 infrastructure-profile → 可能是协议/加密层问题

  5. 执行修复：
     UI 层 → 直接 Edit 目标代码
     数据完整性层 → 按 data_integrity_gap.root_cause 修复真实数据链路
     联动层 → 修复事件绑定/状态传递/响应式计算链 → 重跑 linkage_verify 验证
     非 UI 层 → 根因升级：
       a. 标记当前 screen 为 BLOCKED（等待上游修复）
       b. 直接修复上游代码（后端/API/权限/asset/基础设施）
       c. 修复后重新构建前后端
       d. 回到当前 screen 继续视觉修复

  6. 构建验证（确保不破坏编译）
  7. 对修复的 screen 重新截图/录像
  8. 重新对比 → 更新 visual-report.json
  9. 该 screen 达到 high → 下一个 screen
     仍未 high → 继续修该 screen（可能有多层差异）

退出条件:
  - 所有 screen match_level = high → 100% 达成
  - 或达到 30 轮上限
```

**关键要求**：

**必须使用真实数据和真实服务**：
- 截图时目标 App 必须连接**真实后端**（不是 mock server）
- 页面展示的必须是**真实业务数据**（不是 seed 的采样数据）
- 如果源 App 截图时用的是真实数据 → 目标 App 截图时也必须用同样的数据源
- 数据差异导致的界面差异不是视觉 bug — 但**空数据 vs 有数据**的差异是 bug

**每轮只修 1 个 screen**：
- 聚焦一个问题修到完美，不跳来跳去
- 修完一个 screen（high）再修下一个
- 避免"改了 A 破了 B"的来回

**30 轮不是上限而是最低保证**：
- 60 个页面 × 可能每个页面需要 1-3 轮 → 需要足够多的轮次
- 如果 30 轮后还有 screen 未达 high → 继续（ralph-loop 不限轮次）
- 只有当所有 screen 都 high 或用户手动终止时才停

---

## 局限性

- LLM 的视觉对比是**主观的** — 报告附截图路径，用户应复核
- 需要 App 能运行且可导航到各页面（需要测试账号/数据）
- 移动端截图依赖平台对应的 UI 自动化工具或用户手动截图
- 交互行为对比依赖 `interaction-recordings.json` 的 flows 结构 — 无此文件时仅做静态截图对比

---

## 加载核心协议

> 核心协议详见 ./skills/code-replicate-core.md
