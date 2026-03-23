# Phase 2.13 Real Screenshots Design

## Problem

Phase 2.13 screenshots are being faked — the LLM uses `page.evaluate()` to directly manipulate DOM/View control states instead of driving UI through real business logic. This produces screenshots that show UI states that can never actually occur through normal application usage.

Root causes:
1. `interaction-recordings.json` designs individual operations, not end-to-end business flows. Many UI states (e.g., "order approved") require multi-step, multi-role flows that individual operations can't reach.
2. No explicit prohibition against DOM manipulation. When the LLM can't reach a state through user interaction, it takes shortcuts.
3. Error/exception states are inherently hard to trigger through normal interaction.

## Solution

Two changes to `stage-c-resources.md`:

1. **Section 2.12.8**: Redesign `interaction-recordings.json` from independent operations to business flow chains
2. **Section 2.13**: Add three-tier execution strategy + iron law prohibiting DOM manipulation

## Change 1: interaction-recordings.json — Business Flow Chains

### Current structure (independent operations)

```json
{
  "recordings": [
    {
      "screen": "订单创建页",
      "type": "functional_action",
      "interaction": "创建订单",
      "steps": [
        {"action": "click", "target": "新建按钮"},
        {"action": "type", "target": "名称输入框", "value": "测试订单"},
        {"action": "click", "target": "提交按钮"}
      ],
      "expected_result": { "screenshot_after": "创建成功提示" }
    },
    {
      "screen": "订单详情页",
      "type": "functional_action",
      "interaction": "审批订单",
      "steps": [
        {"action": "click", "target": "审批按钮"}
      ],
      "expected_result": { "screenshot_after": "状态变为已审批" }
    }
  ]
}
```

Problem: "审批订单" is an independent recording. To reach "审批" state, the LLM needs a submitted order — but there's no connection to the "创建订单" recording. The LLM fakes the state.

### New structure (business flow chains)

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
        {"role": "R001", "action": "screenshot", "name": "order_created", "expected": "订单创建成功，状态为待审批"},

        {"role": "R002", "action": "login"},
        {"role": "R002", "action": "navigate", "target": "/orders"},
        {"role": "R002", "action": "click", "target": "刚创建的订单"},
        {"role": "R002", "action": "click", "target": "审批按钮"},
        {"role": "R002", "action": "wait", "condition": "审批成功提示"},
        {"role": "R002", "action": "screenshot", "name": "order_approved", "expected": "订单状态变为已审批"}
      ]
    },
    {
      "name": "order_validation_errors",
      "description": "订单表单校验错误",
      "steps": [
        {"role": "R001", "action": "login"},
        {"role": "R001", "action": "navigate", "target": "/orders/new"},
        {"role": "R001", "action": "click", "target": "提交按钮"},
        {"role": "R001", "action": "wait", "condition": "校验错误出现"},
        {"role": "R001", "action": "screenshot", "name": "order_validation_error", "expected": "必填字段校验错误提示"}
      ]
    },
    {
      "name": "order_server_error",
      "description": "订单创建时服务端返回 500",
      "steps": [
        {"role": "R001", "action": "login"},
        {"role": "R001", "action": "navigate", "target": "/orders/new"},
        {"role": "R001", "action": "mock_route", "url": "POST /api/orders", "response": {"status": 500, "body": {"error": "Internal Server Error"}}},
        {"role": "R001", "action": "fill", "target": "订单表单", "data": {"name": "测试订单", "amount": 1000}},
        {"role": "R001", "action": "click", "target": "提交按钮"},
        {"role": "R001", "action": "wait", "condition": "错误提示出现"},
        {"role": "R001", "action": "screenshot", "name": "order_server_error", "expected": "服务端错误提示"},
        {"role": "R001", "action": "clear_mock"}
      ]
    }
  ],
  "unreachable": [
    {
      "state": "并发编辑冲突",
      "reason": "需要两个用户同时编辑同一订单并同时提交，Playwright 无法可靠模拟精确并发时序",
      "source_file": "src/services/order_service.go:handleConflict"
    }
  ]
}
```

### Key design decisions

**Flow-based, not operation-based.** Each flow is a complete business scenario. Steps within a flow are sequential — each step's result is the next step's precondition. Screenshots are milestones within the flow.

**Role-aware steps.** Each step has a `role` field. When role changes between consecutive steps, the LLM automatically logs out and re-logs in with the new role's credentials (from `role-view-matrix.json`).

**Step action types:**

| Action | Description |
|--------|-------------|
| `login` | Login with the step's role credentials |
| `navigate` | Go to URL/route |
| `click` | Click a UI element (user-level Playwright click) |
| `fill` | Fill a form field (user-level Playwright fill) |
| `type` | Type text keystroke by keystroke |
| `select` | Select dropdown option |
| `drag` | Drag element |
| `hover` | Hover over element |
| `wait` | Wait for condition (element visible, text appears, navigation) |
| `screenshot` | Take screenshot at this milestone |
| `vm_call` | Call ViewModel/Store method (Tier 2 fallback — see execution strategy) |
| `mock_route` | Mock an API route response (Tier 3 — for error states) |
| `clear_mock` | Remove route mocks |

**`unreachable` array.** States that cannot be reached through any of the three tiers. Each entry documents what state, why it's unreachable, and which source file handles it. This replaces faking — if you can't reach it honestly, document it instead.

**LLM generation guidance.** When generating flows, LLM should:
- Design flows around business entities and their lifecycle (create → read → update → delete)
- Include role switches for approval/review/permission-dependent states
- Use `mock_route` for error states (server errors, timeouts, rate limits)
- Use `vm_call` only when user interaction cannot reach a state (e.g., background job completion, external system callback)
- Mark truly unreachable states in `unreachable` array with clear reasons

**Visual effects.** The current `visual_effect` type (animations, transitions) remains as-is — these are simple single-step recordings that don't need flow chains. They become single-step flows:

```json
{
  "name": "kanban_drag_reorder",
  "description": "看板拖拽排序动画",
  "type": "visual_effect",
  "steps": [
    {"role": "R001", "action": "login"},
    {"role": "R001", "action": "navigate", "target": "/kanban"},
    {"role": "R001", "action": "drag", "source": "任务卡片", "target": "目标列"},
    {"role": "R001", "action": "screenshot", "name": "kanban_after_drag", "expected": "卡片移动到目标列"}
  ]
}
```

## Change 2: Phase 2.13 Execution — Three-Tier Strategy

### Current execution

The current doc describes executing `interaction-recordings.json` entries one by one. No restrictions on how Playwright interacts with the page.

### New execution: Three tiers + iron law

**Iron law: NEVER use `page.evaluate()` to modify DOM or View control state. Only permitted uses of `page.evaluate()` are: (1) calling ViewModel/Store/Bloc methods (`vm_call` action), (2) reading state for assertions. Violation = faked screenshot = worthless.**

**Tier 1 — User Interaction (default):**
- Actions: login, navigate, click, fill, type, select, drag, hover, wait, screenshot
- Executed using Playwright's user-level APIs (`page.click()`, `page.fill()`, `page.type()`, etc.)
- These trigger real event handlers → real ViewModel logic → real UI updates via data binding
- All forward business flows use Tier 1

**Tier 2 — ViewModel Call (fallback for unreachable-via-UI states):**
- Action: `vm_call`
- Used when a state cannot be reached through user interaction alone
- Examples: background job completion, external webhook callback, admin-only server action, timer-triggered state change
- Executed via `page.evaluate()` calling into the app's state management layer
- LLM must specify the exact ViewModel/Store/Bloc method from source code analysis
- Framework-specific — LLM determines the call based on Phase 2 source code understanding:
  - Vue: `window.__vue_app__...store.dispatch('action', payload)`
  - React: access store via `window.__REDUX_STORE__` or component ref
  - Angular: `ng.getComponent(el).method()`
  - Svelte: access store via module-scoped variables
  - Non-web (Flutter/Native): use platform integration test driver to call methods
- After `vm_call`, wait for UI to settle before screenshot

**Tier 3 — Network Mock (for error/exception states):**
- Actions: `mock_route`, `clear_mock`
- Used to simulate server errors, timeouts, rate limits, malformed responses
- Executed via Playwright's `page.route()` API to intercept and mock network responses
- After setting up mock, proceed with normal Tier 1 user interaction (fill form, click submit) — the error state appears naturally because the server "returned" an error
- Always `clear_mock` after capturing the error state screenshot

**Tier selection rule:**
```
Can this state be reached by clicking/typing/navigating?
  → YES → Tier 1
  → NO → Can it be reached by calling a ViewModel method?
    → YES → Tier 2 (vm_call)
    → NO → Is it an error/network state?
      → YES → Tier 3 (mock_route)
      → NO → Mark as UNREACHABLE
```

### Execution flow per flow chain

```
For each flow in interaction-recordings.json:
  current_role = null
  for each step in flow.steps:
    if step.role != current_role:
      logout current session (if any)
      login with step.role credentials (from role-view-matrix)
      current_role = step.role

    execute step.action:
      login    → Playwright login flow with role credentials
      navigate → page.goto(target)
      click    → page.click(target)  [Tier 1]
      fill     → page.fill(target, data)  [Tier 1]
      type     → page.type(target, value)  [Tier 1]
      select   → page.selectOption(target, value)  [Tier 1]
      drag     → page.dragAndDrop(source, target)  [Tier 1]
      hover    → page.hover(target)  [Tier 1]
      wait     → page.waitForSelector/waitForURL/custom condition
      screenshot → page.screenshot() → save to visual/source/interactions/
      vm_call  → page.evaluate(() => store.method(args))  [Tier 2]
      mock_route → page.route(url, handler)  [Tier 3]
      clear_mock → page.unroute(url)  [Tier 3]

    if step failed:
      retry once
      if still failed → record failure reason, continue to next step
      DO NOT fake the state to make it work
```

### Adoption of existing 2.13 mechanisms

Everything else in the current 2.13 stays:
- Multi-role static screenshots (from role-view-matrix)
- Video recording for visual effects
- HTTP + WebSocket communication logging
- before/after screenshots for functional actions
- Capture report (capture-report.json)
- Quality checks (blank page, error page, loading state detection)

The only change is HOW interactions are executed (flow chains instead of independent operations) and the three-tier restriction on what Playwright APIs are allowed.

## Files to modify

| File | Change |
|------|--------|
| `code-replicate-skill/docs/phase2/stage-c-resources.md` | Rewrite 2.12.8 (flow-based recordings) + update 2.13 (three-tier execution + iron law) |

No other files need changes.
