# Phase 2 Stage C — 资源发现

> 项目带什么素材？需要什么基础数据？有哪些复用模式？UI 长什么样？

---

## 2.10 asset-inventory.json — 前端素材（仅 frontend/fullstack）

LLM 扫描静态资源目录，盘点所有与代码有引用关系的素材。

每个素材分类迁移方式：
- `copy` — 直接复制（图片、字体、音视频、Lottie JSON）
- `transform` — 格式转换（主题变量、i18n key 格式）
- `replace` — 框架格式替换（React SVG 组件 → Vue SFC）

含 `theme_system` 子结构（主题实现方式、变量数量、迁移方式）。

**音效触发映射**：如果项目有音效文件，LLM 额外提取 `sound_triggers`：
```json
"sound_triggers": [
  {"sound_file": "音效文件路径", "trigger": "LLM 描述什么操作触发", "source_code_ref": "调用音效的源码位置"}
]
```
Phase 3 迁移音效文件时同步迁移触发代码。cr-visual 交互验证时通过 `expected_result.sound` 检查目标 App 是否在同样操作时触发音效。

## 2.11 seed-data-inventory.json — 后端基础数据（仅 backend/fullstack）

LLM 读 seed 脚本 / fixture 文件 / 数据库迁移 → 提取系统运行所需的基础数据。

基础数据 = 没有它系统能启动但业务不能用（字典、角色、配置、初始分类）。

每组数据记录：category, table, records（具体数据内容）, purpose, required。

## 2.12 abstractions + cross_cutting — 复用模式 + 横切关注

LLM 读 key_files → 提取：
- **abstractions**：代码复用模式（基类、mixin、DI、装饰器等，LLM 自由分类）
- **cross_cutting**：跨模块关注点（认证、日志、错误处理），含 `phase` 字段（如有阶段式中间件）
- **架构风格**：monolith / microservice / modular-monolith / serverless

## 2.12.5 角色-界面差异矩阵 → `role-view-matrix.json`（仅 frontend/fullstack）

LLM 读源码中的权限控制逻辑（路由守卫、v-if/v-show 权限判断、按钮级 RBAC、数据范围过滤），提取**不同角色在同一页面看到的差异**：

```json
{
  "generated_at": "ISO8601",
  "roles_with_credentials": [
    {"role_id": "R001", "login": {"username": "admin@demo.com", "password": "admin123"}},
    {"role_id": "R002", "login": {"username": "ops@demo.com", "password": "ops123"}}
  ],
  "differences": [
    {
      "screen": "用户管理页",
      "route": "/admin/users",
      "by_role": {
        "R001": {"visible": true, "actions": ["查看", "编辑", "删除", "导出"], "data_scope": "全部"},
        "R002": {"visible": true, "actions": ["查看", "编辑"], "data_scope": "本部门"},
        "R003": {"visible": false}
      }
    }
  ]
}
```

**Phase 1 补充**：`source_app.login` 扩展为**多角色凭证列表**（不是单一账号）。LLM 在 Phase 1 向用户收集每个角色的测试账号。

**用途**：
- Phase 2.13 截图/录像：按每个角色分别登录截图（不只用管理员截一遍）
- cr-visual：按角色对比（管理员视角 vs 管理员视角，运营视角 vs 运营视角）
- cr-fidelity F4：验证权限控制的精确还原

## 2.12.8 业务流程链 → `interaction-recordings.json`（仅 frontend/fullstack）

LLM 读源码中的**所有用户交互行为**，按**业务流程**组织为端到端的流程链，而非独立操作。

**核心原则：每张截图必须是真实业务操作的自然结果，不允许伪造 UI 状态。**

```json
{
  "generated_at": "ISO8601",
  "flows": [
    {
      "name": "order_lifecycle",
      "description": "订单从创建到审批的完整生命周期",
      "steps": [
        {"role": "R001", "action": "login"},
        {"role": "R001", "action": "navigate", "target": "/orders/new"},
        {"role": "R001", "action": "fill", "target": "订单表单", "data": {"name": "测试订单", "amount": 1000}},
        {"role": "R001", "action": "click", "target": "提交按钮"},
        {"role": "R001", "action": "wait", "condition": "成功提示出现"},
        {"role": "R001", "action": "screenshot", "name": "order_created", "expected_result": {
          "screenshot_after": "订单创建成功，状态为待审批",
          "ui_changes": ["订单列表新增一条记录", "成功提示出现"],
          "feedback": "创建成功"
        }},

        {"role": "R002", "action": "login"},
        {"role": "R002", "action": "navigate", "target": "/orders"},
        {"role": "R002", "action": "click", "target": "刚创建的订单"},
        {"role": "R002", "action": "click", "target": "审批按钮"},
        {"role": "R002", "action": "wait", "condition": "审批成功提示"},
        {"role": "R002", "action": "screenshot", "name": "order_approved", "expected_result": {
          "screenshot_after": "订单状态变为已审批",
          "ui_changes": ["状态标签从'待审批'变为'已审批'", "审批按钮消失"],
          "feedback": "审批成功"
        }}
      ],
      "source_files": ["src/handlers/order_handler.go", "src/services/order_service.go"]
    }
  ],
  "unreachable": [
    {
      "state": "并发编辑冲突",
      "reason": "需要两个用户同时编辑同一订单并同时提交，无法可靠模拟精确并发时序",
      "source_file": "src/services/order_service.go:handleConflict"
    }
  ]
}
```

**流程链 vs 独立操作**：每个 flow 是完整的业务场景，步骤串联 — 前一步的结果是后一步的前置条件。screenshot 是流程中的里程碑，不是独立采集动作。

**角色感知**：每个 step 带 `role` 字段。角色切换时自动清除 session → 重新登录（凭证来自 `role-view-matrix.json`）。

**Step action 类型**：

| Action | 字段 | 说明 |
|--------|------|------|
| `login` | role | 用该角色凭证登录 |
| `navigate` | target（URL/路由） | 导航到页面 |
| `click` | target（自然语言描述，执行时 LLM 解析为 Playwright selector） | 点击 UI 元素 |
| `fill` | target, data | 填写表单 |
| `type` | target, value | 逐键输入 |
| `select` | target, value | 选择下拉选项 |
| `drag` | source, target | 拖拽 |
| `hover` | target | 悬浮 |
| `wait` | condition | 等待条件（元素可见、文本出现、导航完成） |
| `screenshot` | name, expected_result | 在此里程碑截图 |
| `vm_call` | method（JS 表达式）, args（可选）, wait_after（可选条件） | 调用 ViewModel/Store 方法（Tier 2 fallback） |
| `mock_route` | url（method + path）, response（status, body） | Mock API 响应（Tier 3） |
| `clear_mock` | （无） | 清除所有 route mock |
| `linkage_verify` | trigger_control, expected_effects[] | 联动检查点：验证触发控件操作后的下游控件变化 |

**`linkage_verify` 详细说明**：

控件联动是指"操作控件 A → 控件 B 自动变化"的关系。LLM 必须从源码中提取所有联动关系，并在 flow steps 中插入 `linkage_verify` 检查点。

```json
{
  "action": "linkage_verify",
  "trigger_control": "省份下拉框",
  "trigger_action": "select 广东省",
  "expected_effects": [
    {
      "target_control": "城市下拉框",
      "effect_type": "options_update",
      "expected": "选项列表更新为广东省的城市（深圳、广州、东莞...）",
      "verify": "options.length >= 1 且选项内容与省份关联"
    },
    {
      "target_control": "区县下拉框",
      "effect_type": "reset",
      "expected": "选项清空，等待选择城市",
      "verify": "options.length == 0 或显示 placeholder"
    }
  ]
}
```

**联动类型参考**（LLM 从源码中穷举提取）：

| 联动类型 | effect_type | 示例 |
|---------|-------------|------|
| 级联选择 | `options_update` | 选省 → 市下拉更新 |
| 条件显隐 | `visibility_toggle` | 勾选复选框 → 新控件出现/消失 |
| 条件启禁 | `enabled_toggle` | 表单填完 → 按钮从 disabled 变 enabled |
| 自动计算 | `value_update` | 数量 × 单价 → 总价 Label 更新 |
| 联动筛选 | `data_filter` | 切换 Tab → 表格数据过滤 |
| 主从联动 | `detail_load` | 点击列表行 → 详情面板加载该行数据 |
| 联动重置 | `reset` | 上级选择变化 → 下级清空 |

**插入规则**：每个会触发联动的 `select`/`click`/`fill`/`type` 步骤之后，必须紧跟一个 `linkage_verify`（在下一个用户操作之前）。LLM 从源码中找到事件处理函数里的 `setState`/`emit`/`dispatch`/`watch`/`computed` 等联动触发点来判断。

**`expected_result` 保留结构化格式**：`screenshot_after`、`ui_changes`、`navigation`、`feedback`、`sound` — 与 cr-visual 和 Phase 3 音效迁移兼容。

**`source_files` 追溯**：每个 flow 关联源码文件，保留 Phase 3 迁移可追溯性。

**flow `type` 字段**：可选，默认 `functional_action`。设为 `visual_effect` 时触发录像而非截图。

**`unreachable` 数组**：三个层级都无法到达的状态。记录原因和源码位置 — 替代伪造。

**LLM 生成指导 — 穷举提取**：

**原则：源码中每一个会引起 UI 变化的事件处理函数 = 至少一张截图。不手工挑选，穷举。**

LLM 读每个页面/组件的源码 → 找出所有绑定了事件处理的 UI 元素 → 按业务实体的生命周期组织为流程链（create → read → update → delete）。

- 跨角色审批/审核/权限操作 → 在同一 flow 中切换角色
- 服务端错误 → `mock_route`（Tier 3）。客户端校验错误 → 直接用 Tier 1 提交不完整表单
- 后台任务完成、外部回调等 UI 交互无法到达的状态 → `vm_call`（Tier 2）
- 真正不可达 → 放入 `unreachable` 数组

**控件联动穷举提取**：

LLM 必须额外扫描每个页面/组件的源码，提取所有控件联动关系：

```
扫描模式（不限框架，按语义理解）：
1. onChange/onSelect/onCheck 等事件处理函数内部：
   - 是否调用了 setState/ref.value= 修改其他控件的数据源？
   - 是否 dispatch 了影响其他控件的 action？
   - 是否触发了 API 调用，其响应用于填充其他控件？
2. watch/computed/useEffect 等响应式依赖：
   - 变量 A 变化 → 自动计算变量 B（如 quantity * price → total）
   - 状态 A 变化 → 控件 B 的 visible/disabled/options 变化
3. 表单验证联动：
   - 字段 A 填写 → 提交按钮 enabled/disabled 变化
   - 字段 A 的值 → 影响字段 B 的验证规则

每发现一个联动关系 → 确保对应 flow 中有 linkage_verify 检查点。
无对应 flow → 创建专门的联动验证 flow（type: "linkage_test"）。
```

**删除安全**：CRUD 流程中用刚创建的测试数据做 Delete（自产自销）。无法安全删除 → 只截确认弹窗，标记 `DELETE_SKIPPED_SAFETY`。

**流程独立 + 并行优化**：流程间无数据依赖（每个 flow 创建自己的测试数据）。大项目（100+ 截图）不同模块的 flow 可用 Agent 并行执行。同一 flow 内步骤始终串行。

## 2.13 源 App 截图 + 录像（仅 frontend/fullstack 且源 App 可运行）

在 Phase 2 阶段采集源 App 截图和动态录像 — 不等到流程末尾（源项目环境可能被清理）。

前置条件（全部硬性，不降级）：
- 后端运行（backend_start_command）
- 数据就绪（seed_command）
- 登录成功（login + bypass_command）

### 静态截图

**多角色截图**：如果 `role-view-matrix.json` 存在且 `roles_with_credentials` 有多个角色：
- 逐角色登录 → 截该角色可见的所有页面
- 保存到 `visual/source/{role_id}/{route}.png`
- route-map.json 按角色分组

**单角色截图**（无角色矩阵时）：用最高权限账号截全量页面。

截图基于**源码路由配置**（此时 experience-map 尚未生成），支持：
- URL 直达路由
- 参数化路由（LLM 从运行中的 App 获取真实 ID）
- 非 URL 页面（记录导航步骤）

### 交互行为采集

如果 `interaction-recordings.json` 存在 → 按流程链逐步执行并采集：

**铁律（iron law 27）：禁止用 `page.evaluate()` 修改 DOM 或 View 控件状态。`page.evaluate()` 仅允许用于：(1) `vm_call` 调用 ViewModel/Store/Bloc 方法，(2) 读取状态用于断言。违反 = 伪造截图 = 无价值。**

**三级执行策略**：

| 优先级 | 策略 | 适用场景 | Playwright API |
|--------|------|---------|----------------|
| Tier 1 | 用户交互 | 正向业务流程 | page.click / page.fill / page.type 等 |
| Tier 2 | ViewModel 调用 | UI 交互无法到达的状态 | page.evaluate() 调用 Store/Bloc 方法 |
| Tier 3 | 网络 Mock | 异常/错误状态 | page.route() 拦截 + Mock 响应 |

**Tier 选择规则**：
```
用户交互能到达？→ YES → Tier 1（包括客户端校验错误 — 提交不完整表单即可）
  → NO → ViewModel 调用能到达？→ YES → Tier 2（vm_call）
    → NO → 是网络/错误状态？→ YES → Tier 3（mock_route）
      → NO → 标记 UNREACHABLE
```

**Tier 2 说明**：LLM 必须从 Phase 2 源码分析中确定具体的调用表达式，不依赖已知框架模式。源 App 须在开发模式运行（生产构建可能移除调试入口）。`vm_call` 后须等待 UI 更新完成再截图。

**执行流程**：
```
对每个 flow:
  current_role = null
  for each step in flow.steps:
    if step.role != current_role:
      清除 cookies + localStorage
      导航到登录页
      用 step.role 凭证登录（来自 role-view-matrix）
      current_role = step.role

    执行 step.action:
      login      → 清除 session + 登录
      navigate   → page.goto(target)
      click      → page.click(resolved_selector)  [Tier 1]
      fill       → page.fill(resolved_selector, data)  [Tier 1]
      type       → page.type(resolved_selector, value)  [Tier 1]
      select     → page.selectOption(resolved_selector, value)  [Tier 1]
      drag       → page.dragAndDrop(resolved_source, resolved_target)  [Tier 1]
      hover      → page.hover(resolved_selector)  [Tier 1]
      wait       → page.waitForSelector / waitForURL / 自定义条件
      screenshot → page.screenshot() → 保存到 visual/source/interactions/
      vm_call    → page.evaluate(() => expr(args)) + wait_after  [Tier 2]
      mock_route → page.route(url, handler)  [Tier 3]
      clear_mock → page.unroute('**')  [Tier 3]

    step 失败时:
      重试 1 次
      仍失败:
        记录失败原因
        非 screenshot 步骤 → 跳到下一个 screenshot 里程碑
        screenshot 步骤 → 标记失败，继续
      绝对不伪造状态

  flow 失败（登录失败/环境不可用）→ 中止该 flow，记录原因，继续下一个 flow
  3+ flow 因同一环境问题失败 → 中止所有剩余 flow
```

**四种证据**（每个 screenshot 里程碑采集）：
- **截图** → 证明操作后 UI 状态正确
- **操作录像**（visual_effect flow）→ 证明操作过程流畅
- **结果 JSON** → 结构化记录实际 UI 行为（跳转/提示/元素变化）
- **API 日志** → 该操作触发的所有网络请求和响应（供接口级对比）

### 通信日志采集（HTTP + WebSocket）

每个 functional_action 执行期间，LLM 同时抓取**所有通信**（HTTP + WebSocket）：

```
对每个 functional_action:
  1. 启动 HTTP 拦截（LLM 用适合当前平台的网络拦截方式）
  2. 启动 WebSocket 拦截（捕获发送和接收的消息帧）
  3. 执行操作步骤（click/submit/drag）
  4. 等待操作完成
  5. 停止拦截 → 保存：
     interactions/{screen}_{interaction}_api.json:
     {
       "http": [
         {"method": "POST", "url": "/api/orders", "request_body": {...}, "status": 201, "response_body": {...}}
       ],
       "websocket": [
         {"direction": "received", "data": {"event": "inventory:updated", "payload": {...}}}
       ]
     }
```

**HTTP + WebSocket 都记录** — 有些操作触发 HTTP 请求同时收到 WebSocket 推送（如下单后库存实时更新）。只记录 HTTP 会遗漏推送消息。

**只记录业务通信**（过滤掉静态资源、analytics、CDN、WebSocket 心跳）。LLM 判断哪些是业务消息。

### 保存

```
visual/source/
  ├── {role_id}/               (静态截图按角色分组)
  │   ├── dashboard.png
  │   └── users.png
  ├── recordings/              (动态录像)
  │   ├── kanban_drag-reorder.mp4
  │   └── page_transition.mp4
  ├── interactions/            (交互行为证据)
  │   ├── users_create_before.png
  │   ├── users_create_after.png
  │   ├── users_create_result.json
  │   ├── users_create_api.json     ← API 日志
  │   ├── orders_delete_before.png
  │   ├── orders_delete_after.png
  │   ├── orders_delete_result.json
  │   └── orders_delete_api.json    ← API 日志
  └── route-map.json
```

### 采集闭环验证

截图和录像采集完成后，LLM 自检覆盖度 — 漏了的重试，直到全覆盖：

```
检查 1: 角色覆盖
  role-view-matrix 中的每个角色都成功登录并截图了吗？
  → 某角色登录失败 → 重试登录（不同方式）→ 仍失败 → 标记原因，不跳过

检查 2: 页面覆盖
  路由列表中每个页面都有对应截图吗？
  → 缺失 → 重新导航截图
  → 导航失败（404/权限不足）→ 记录原因

检查 3: 交互覆盖
  interaction-recordings 中每个 action 都执行了吗？
  → 缺失 → 重试操作
  → 操作失败（按钮不可用/页面变了）→ 记录原因

检查 4: API 日志覆盖
  每个 functional_action 都有 api.json 吗？
  → 缺失 → 重新采集

检查 5: 截图质量
  LLM 查看每张截图 → 是否为空白页/错误页/纯 loading 状态？
  → 质量差 → 等待页面加载完成 → 重新截图

检查 6: 录像质量
  LLM 查看每段录像 → 是否黑屏/卡住/未完成操作？
  → 质量差 → 重新录制

汇总: 输出 visual/source/capture-report.json
  {
    "total_screens": 60,
    "captured": 58,
    "failed": 2,
    "failed_reasons": [...],
    "total_interactions": 7,
    "recorded": 7,
    "quality_issues": 0
  }
```

**不降级** — 能采集的必须采集成功。采集失败的记录原因但不假装成功。
