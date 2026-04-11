# Phase 2.5: 合约提取协议

> Phase 2 Discovery 结束后执行。从源码提取验收合约，作为 Phase 3 逆向检查的 oracle。
> 不改变 Phase 2 产物，不生成 .allforai/ 标准产物，只输出 `acceptance-contracts.json`。

---

## 核心原则

**提取意图，不提取实现。**

换了技术栈，交互意图不变；组件代码完全不同。合约描述"做什么"，不描述"用什么 API 做"。

跨模块的隐性规则（散落在多个文件中、没有显式断言的约束）必须在这里整合为一条合约，不能留给各自的生成单元各自推断。

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
