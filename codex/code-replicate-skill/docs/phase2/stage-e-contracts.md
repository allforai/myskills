# Phase 2.5: 合约提取协议

> Phase 2 Discovery 结束后执行。从源码提取验收合约，作为 Phase 3 逆向检查的 oracle。
> 不改变 Phase 2 产物，不生成 .allforai/ 标准产物，只输出 `acceptance-contracts.json`。

---

## 核心原则

**提取意图，不提取实现。**

换了技术栈，交互意图不变；组件代码完全不同。合约描述"做什么"，不描述"用什么 API 做"。

跨模块的隐性规则（散落在多个文件中、没有显式断言的约束）必须在这里整合为一条合约，不能留给各自的生成单元各自推断。

---

## Step 2.5.0: 入口可达性扫描（前置过滤）

**目标：** 在提取合约前，建立可达性地图，排除死代码和死功能，避免把"从未运行"的代码提取为合约。

**执行步骤：**

1. 从 `source-summary.json` 取所有入口点（路由注册、事件监听、CLI 命令、main loop、定时任务）
2. 从入口点出发追踪调用链，标记每个 handler / screen 的可达性：

| 可达性标记 | 含义 | 后续处理 |
|-----------|------|---------|
| `reachable` | 从入口可追踪到 | 正常提取合约，`confidence: "high"` |
| `suspect_dead` | 无入口指向、被 feature flag 关闭、或被注释包围 | 跳过提取，列入 `dead_code_candidates.json` |
| `unknown` | 动态 dispatch / 字符串拼接路由 / 跨进程调用 | 提取合约，标 `confidence: "low"` |

3. 按项目类型识别可达性：
   - **Web 后端**：从路由文件追踪 handler
   - **React/Next.js**：从 `<Route>` / `router.push` / `Link` 追踪 Page
   - **Flutter**：从 `Navigator.push` / `GoRouter` 追踪 Screen
   - **游戏引擎**：从 SceneManager / 状态机跳转追踪 Scene
4. 输出 `dead_code_candidates.json` 到 `.allforai/code-replicate/`
5. 在 Step 2.5.3 写完合约后，向用户展示候选死代码列表，等待确认

**`dead_code_candidates.json` 格式：**

```json
{
  "candidates": [
    {
      "type": "screen",
      "name": "LegacyReportScreen",
      "file": "src/screens/LegacyReportScreen.tsx",
      "reason": "no_navigation_path",
      "last_commit": "2021-03-14"
    },
    {
      "type": "endpoint",
      "name": "POST /api/v1/export/csv",
      "file": "routes/export.php",
      "reason": "feature_flag_disabled",
      "flag": "ENABLE_CSV_EXPORT=false"
    }
  ]
}
```

用户可选择：**忽略**（不复刻）或**强制纳入**（`confidence: "forced"`）。

**当 `source_runnable: false` 时：** 可达性扫描是截图缺失时的唯一过滤机制。所有 UI 合约额外标记 `"evidence": "code_only"`，提示 Phase 3 遇到 known_gap 时优先怀疑合约本身（可能是死代码漏网），而非直接修复生成代码。

---

## Step 2.5.1: 后端行为合约提取

**来源文件：** routes / controllers / service 层（参考 extraction-plan.task_sources）

**每个接口提取：**

```json
{
  "contract_id": "BC-001",
  "module_id": "M001",
  "endpoint": "POST /api/orders",
  "inputs": {
    "fields": ["user_id", "items[]", "coupon_code"],
    "required": ["user_id", "items[]"],
    "constraints": ["items[] must not be empty", "coupon_code must be valid if provided"]
  },
  "outputs": {
    "success": { "status": 201, "body": ["order_id", "estimated_delivery"] },
    "errors": [
      { "condition": "items empty", "status": 422 },
      { "condition": "coupon expired", "status": 400 },
      { "condition": "insufficient stock", "status": 409 }
    ]
  },
  "side_effects": ["inventory.decrement", "notification.send_confirmation", "audit_log.write"],
  "cross_module_rules": [
    "User must not be banned (checked in auth middleware before handler)",
    "Order total recalculated server-side; client-provided total is ignored"
  ]
}
```

**提取要点：**
- `cross_module_rules`：专门收集散落在多个文件中的隐性约束。搜索调用链上所有中间件、装饰器、guard 的副作用
- `side_effects`：只记录写操作（写库、发消息、推通知、写日志）；读操作不是 side_effect
- `errors`：从 service 层的 throw/return error 分支提取，不要漏 guard clause

**不提取：**
- 具体 ORM 查询语句（实现）
- 框架特定的装饰器名称（实现）
- 函数名、变量名（实现）

---

## Step 2.5.2: UI 交互意图合约提取

**来源文件：** components / screens / state management（参考 extraction-plan.screen_sources）

**每个屏幕提取：**

```json
{
  "contract_id": "UI-001",
  "module_id": "M002",
  "screen": "BattleScreen",
  "states": ["loading", "in_battle", "paused", "victory", "defeat"],
  "user_actions": [
    {
      "action": "tap_attack",
      "precondition": "state == in_battle AND attack_cooldown == 0",
      "outcome": "trigger combat_handler, update hp display"
    },
    {
      "action": "open_inventory",
      "precondition": "state != in_battle",
      "outcome": "navigate to InventoryScreen"
    },
    {
      "action": "pause",
      "precondition": "state == in_battle",
      "outcome": "state → paused, show pause menu"
    }
  ],
  "transitions": [
    { "from": "loading", "trigger": "battle data loaded", "to": "in_battle" },
    { "from": "in_battle", "trigger": "enemy hp <= 0", "to": "victory" },
    { "from": "in_battle", "trigger": "player hp <= 0", "to": "defeat" }
  ],
  "intent": "玩家在此屏幕执行回合制战斗操作，战斗结束时过渡到结算界面"
}
```

**提取要点：**
- `states`：业务状态，不是 React/Flutter 的 widget state。问："用户处于哪个阶段？"
- `user_actions[].precondition`：从代码中的 disabled/guard/conditional render 提取
- `transitions`：从状态机、条件导航、router.push 调用提取触发条件
- `intent`：一句话，说用户在这个屏幕想完成什么

**对于 Web 应用（无移动端手势）：**
- `user_actions` 聚焦 click / submit / input change
- 跨 App flow（OAuth、支付跳转）标记 `"cross_app": true`

**对于非标框架（游戏引擎、桌面 GUI、自定义状态机）：**
- `states` 和 `user_actions` 的**来源文件**由 LLM 根据项目实际架构自主识别——可能是 Scene 管理器、Animator 状态机、事件总线、自定义 GameStateManager，而非传统 components/screens
- 提取**目标**（意图）不变：用户处于哪个阶段、能做什么操作、触发什么转换
- 逆向提取（Phase 3）同理：从目标栈的等价结构中提取，不强求与源码来源文件类型相同

**不提取：**
- 具体 CSS 类名（实现）
- 组件库 API（实现）
- 像素级布局（实现）

---

## Step 2.5.3: 输出 acceptance-contracts.json

写入 `.allforai/code-replicate/acceptance-contracts.json`：

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO 8601 timestamp>",
  "source_path": "<source project path>",
  "total_backend_contracts": 12,
  "total_ui_contracts": 8,
  "backend_contracts": [],
  "ui_contracts": []
}
```

**写入前质量检查：**
1. 每个 backend_contract 有至少一个 error condition（纯查询接口除外）
2. 每个 ui_contract 有至少两个 states（loading + 一个业务状态）
3. cross_module_rules 不为空的合约：确认规则来自真实的跨文件约束，不是臆测
4. 总合约数 ≥ source-summary.modules 中 UI 模块数量（每个 UI 模块至少一个 UI 合约）

---

## 逆向提取（Phase 3 使用）

Phase 3 生成目标代码后，用同一套规则从目标代码中提取合约 B：

- 后端合约 B：从目标路由/控制器提取，与源码合约 A 格式相同
- UI 合约 B：从目标屏幕/组件提取，与源码合约 A 格式相同

**Diff(A, B) 结构：**

```json
{
  "contract_id": "BC-005",
  "missing_error_conditions": [
    { "condition": "user_banned", "status": 403 }
  ],
  "missing_side_effects": ["audit_log.write"],
  "extra_error_conditions": [],
  "intent_mismatch": null
}
```

空 diff = 合约满足 = 通过。非空 diff = 精确差距 = 修复目标。
