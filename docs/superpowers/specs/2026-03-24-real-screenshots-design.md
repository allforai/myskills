# Phase 2.13 Real Screenshots Design

## Problem

Phase 2.13 screenshots are being faked — the LLM uses `page.evaluate()` to directly manipulate DOM/View control states instead of driving UI through real business logic. This produces screenshots that show UI states that can never actually occur through normal application usage.

Root causes:
1. `interaction-recordings.json` designs individual operations, not end-to-end business flows. Many UI states (e.g., "order approved") require multi-step, multi-role flows that individual operations can't reach.
2. No explicit prohibition against DOM manipulation. When the LLM can't reach a state through user interaction, it takes shortcuts.
3. Error/exception states are inherently hard to trigger through normal interaction.

## Solution

Changes to `stage-c-resources.md` and related files:

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
        {"role": "R001", "action": "screenshot", "name": "order_created", "expected_result": {
          "screenshot_after": "订单创建成功，状态为待审批",
          "ui_changes": ["订单列表新增一条记录", "成功提示出现"],
          "navigation": "/orders",
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
    },
    {
      "name": "order_validation_errors",
      "description": "订单表单校验错误",
      "steps": [
        {"role": "R001", "action": "login"},
        {"role": "R001", "action": "navigate", "target": "/orders/new"},
        {"role": "R001", "action": "click", "target": "提交按钮"},
        {"role": "R001", "action": "wait", "condition": "校验错误出现"},
        {"role": "R001", "action": "screenshot", "name": "order_validation_error", "expected_result": {
          "screenshot_after": "必填字段校验错误提示",
          "ui_changes": ["名称字段显示红色边框", "金额字段显示'必填'提示"],
          "feedback": "请填写必填字段"
        }}
      ],
      "source_files": ["src/components/OrderForm.tsx"]
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
        {"role": "R001", "action": "screenshot", "name": "order_server_error", "expected_result": {
          "screenshot_after": "服务端错误提示",
          "ui_changes": ["错误提示 toast 出现"],
          "feedback": "服务器错误，请稍后重试"
        }},
        {"role": "R001", "action": "clear_mock"}
      ],
      "source_files": ["src/components/OrderForm.tsx"]
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

**Role-aware steps.** Each step has a `role` field. When role changes between consecutive steps, the LLM automatically switches sessions: clear cookies/localStorage → navigate to login page → login with new role's credentials (from `role-view-matrix.json`). This works even for apps without an explicit logout endpoint.

**Structured `expected_result` preserved.** The `screenshot` action carries the same structured `expected_result` object as the old format (`screenshot_after`, `ui_changes`, `navigation`, `feedback`, `sound`). This maintains compatibility with cr-visual and Phase 3 sound migration.

**`source_files` per flow.** Each flow links to the source code files that implement the business logic being tested, preserving traceability for Phase 3 migration.

**Step action types:**

| Action | Fields | Description |
|--------|--------|-------------|
| `login` | role | Login with the step's role credentials |
| `navigate` | target (URL/route) | Go to URL/route |
| `click` | target (natural-language description, LLM resolves to Playwright selector at execution time) | Click a UI element |
| `fill` | target, data | Fill form fields |
| `type` | target, value | Type text keystroke by keystroke |
| `select` | target, value | Select dropdown option |
| `drag` | source, target | Drag element |
| `hover` | target | Hover over element |
| `wait` | condition | Wait for condition (element visible, text appears, navigation) |
| `screenshot` | name, expected_result | Take screenshot at this milestone |
| `vm_call` | method (JS expression to evaluate), args (optional object), wait_after (optional condition) | Call ViewModel/Store method (Tier 2 fallback) |
| `mock_route` | url (method + path), response (status, body) | Mock an API route response (Tier 3) |
| `clear_mock` | (none) | Remove all route mocks |

**`target` fields are natural-language descriptions** (e.g., "提交按钮", "订单表单"), not CSS selectors. The LLM resolves them to Playwright selectors at execution time using source code analysis and runtime DOM inspection.

**Flow `type` field.** Optional, defaults to `functional_action`. Set to `visual_effect` for animation/transition flows — these trigger video recording instead of before/after screenshots.

**`unreachable` array.** States that cannot be reached through any of the three tiers. Each entry documents what state, why it's unreachable, and which source file handles it. This replaces faking — if you can't reach it honestly, document it instead.

**LLM generation guidance — exhaustive extraction.** When generating flows, LLM must:
- **Exhaust all UI-change-triggering event handlers in source code** (same principle as existing 2.12.8: every event handler that causes UI change = at least one screenshot). Do not hand-pick, exhaust.
- Design flows around business entities and their lifecycle (create → read → update → delete)
- Include role switches for approval/review/permission-dependent states
- Use `mock_route` for server error states (500, timeout, rate limit). Client-side validation errors are Tier 1 — just interact incorrectly (e.g., submit empty form)
- Use `vm_call` only when user interaction cannot reach a state (e.g., background job completion, external system callback)
- Mark truly unreachable states in `unreachable` array with clear reasons

**Delete safety.** Within CRUD flows, use freshly created test data for Delete operations (self-produced, self-consumed). If data cannot be safely deleted → only screenshot the confirmation dialog, mark step as `DELETE_SKIPPED_SAFETY`.

**Flow ordering and parallelism.** Flows are independent unless explicitly noted. Cross-flow data dependencies should be avoided — each flow creates its own test data. For large projects (100+ screenshots), flows targeting different modules can run in parallel via separate Agent instances. Steps within a single flow are always sequential.

**Failure strategy:**
- **Step failure**: retry once. If still failed, record reason. If the failed step is a non-screenshot step (click, fill, navigate), skip to the next `screenshot` step in the flow (attempt to salvage partial results). If a `screenshot` step itself fails, mark it failed and continue.
- **Flow failure**: if login fails or environment is broken (app not running, seed data missing), abort the entire flow, record reason, move to next flow.
- **Environment failure**: if 3+ flows fail due to the same environment issue, abort all remaining flows.

## Change 2: Phase 2.13 Execution — Three-Tier Strategy

### Current execution

The current doc describes executing `interaction-recordings.json` entries one by one. No restrictions on how Playwright interacts with the page.

### New execution: Three tiers + iron law

**Iron law 27: NEVER use `page.evaluate()` to modify DOM or View control state. Only permitted uses of `page.evaluate()` are: (1) calling ViewModel/Store/Bloc methods via `vm_call` action, (2) reading state for assertions. Violation = faked screenshot = worthless.**

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
- LLM must determine the exact call expression from Phase 2 source code analysis — not from known framework patterns
- Requires the source app to be running in development mode (production builds may strip debug accessors)
- After `vm_call`, wait for UI to settle (use `wait_after` field) before screenshot

**Tier 3 — Network Mock (for error/exception states):**
- Actions: `mock_route`, `clear_mock`
- Used to simulate server errors, timeouts, rate limits, malformed responses
- Executed via Playwright's `page.route()` API to intercept and mock network responses
- After setting up mock, proceed with normal Tier 1 user interaction (fill form, click submit) — the error state appears naturally because the server "returned" an error
- `clear_mock` removes all active mocks. Place after the error screenshot to prevent mock leaking into subsequent steps

**Tier selection rule:**
```
Can this state be reached by clicking/typing/navigating?
  → YES → Tier 1 (including client-side validation errors — just interact incorrectly)
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
      clear cookies + localStorage
      navigate to login page
      login with step.role credentials (from role-view-matrix)
      current_role = step.role

    execute step.action:
      login      → clear session + login flow with role credentials
      navigate   → page.goto(target)
      click      → page.click(resolved_selector)  [Tier 1]
      fill       → page.fill(resolved_selector, data)  [Tier 1]
      type       → page.type(resolved_selector, value)  [Tier 1]
      select     → page.selectOption(resolved_selector, value)  [Tier 1]
      drag       → page.dragAndDrop(resolved_source, resolved_target)  [Tier 1]
      hover      → page.hover(resolved_selector)  [Tier 1]
      wait       → page.waitForSelector/waitForURL/custom condition
      screenshot → page.screenshot() → save to visual/source/interactions/
      vm_call    → page.evaluate(() => expr(args)) + wait_after  [Tier 2]
      mock_route → page.route(url, handler)  [Tier 3]
      clear_mock → page.unroute('**')  [Tier 3]

    if step failed:
      retry once
      if still failed:
        record failure reason
        if non-screenshot step → skip to next screenshot milestone
        if screenshot step → mark failed, continue
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
- Capture closure verification (6 checks)

The only change is HOW interactions are executed (flow chains instead of independent operations) and the three-tier restriction on what Playwright APIs are allowed.

## Files to modify

| File | Change |
|------|--------|
| `code-replicate-skill/docs/phase2/stage-c-resources.md` | Rewrite 2.12.8 (flow-based recordings) + update 2.13 (three-tier execution + iron law) |
| `code-replicate-skill/skills/code-replicate-core.md` | Update 2.12.8 description in Stage C table + add iron law 27 |
| `code-replicate-skill/skills/cr-visual.md` | Update references from `recordings[]` to `flows[]` structure |
