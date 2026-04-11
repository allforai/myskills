# Phase 2.5: Contract Extraction Protocol

> Executed after Phase 2 Discovery completes. Extracts acceptance contracts from source code to serve as the oracle for Phase 3 reverse verification.
> Does not modify Phase 2 artifacts, does not generate standard .allforai/ outputs — only outputs `acceptance-contracts.json`.

---

## Core Principle

**Extract intent, not implementation.**

When the tech stack changes, the interaction intent stays the same; component code will be entirely different. Contracts describe "what it does," not "which API it uses to do it."

Implicit cross-module rules (constraints scattered across multiple files with no explicit assertions) must be consolidated into a single contract here — they cannot be left for individual generation units to infer independently.

---

## Step 2.5.1: Backend Behavior Contract Extraction

**Source files:** routes / controllers / service layer (refer to extraction-plan.task_sources)

**Extract per endpoint:**

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

**Extraction notes:**
- `cross_module_rules`: Specifically collect implicit constraints scattered across multiple files. Search all middleware, decorators, and guard side effects in the call chain
- `side_effects`: Only record write operations (database writes, message sends, notifications, log writes); read operations are not side effects
- `errors`: Extract from throw/return error branches in the service layer; do not miss guard clauses

**Do NOT extract:**
- Specific ORM query statements (implementation)
- Framework-specific decorator names (implementation)
- Function names, variable names (implementation)

---

## Step 2.5.2: UI Interaction Intent Contract Extraction

**Source files:** components / screens / state management (refer to extraction-plan.screen_sources)

**Extract per screen:**

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

**Extraction notes:**
- `states`: Business states, not React/Flutter widget states. Ask: "What phase is the user in?"
- `user_actions[].precondition`: Extract from disabled/guard/conditional render logic in the code
- `transitions`: Extract trigger conditions from state machines, conditional navigation, and router.push calls
- `intent`: One sentence describing what the user wants to accomplish on this screen

**For web applications (no mobile gestures):**
- `user_actions` focuses on click / submit / input change
- Cross-app flows (OAuth, payment redirects) mark `"cross_app": true`

**Do NOT extract:**
- Specific CSS class names (implementation)
- Component library APIs (implementation)
- Pixel-level layout (implementation)

---

## Step 2.5.3: Output acceptance-contracts.json

Write to `.allforai/code-replicate/acceptance-contracts.json`:

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

**Pre-write quality checks:**
1. Every backend_contract has at least one error condition (except pure query endpoints)
2. Every ui_contract has at least two states (loading + one business state)
3. Contracts with non-empty cross_module_rules: confirm rules come from real cross-file constraints, not conjecture
4. Total contract count ≥ number of UI modules in source-summary.modules (at least one UI contract per UI module)

---

## Reverse Extraction (used by Phase 3)

After Phase 3 generates target code, apply the same rules to extract contracts B from the target code:

- Backend contracts B: extracted from target routes/controllers, same format as source contracts A
- UI contracts B: extracted from target screens/components, same format as source contracts A

**Diff(A, B) structure:**

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

Empty diff = contract satisfied = pass. Non-empty diff = precise gap = fix target.
