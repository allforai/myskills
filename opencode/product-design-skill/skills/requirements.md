---
name: requirements
description: >
  Use when the user asks to confirm requirements, "需求确认", "核对需求",
  or when product-concept finishes and auto-triggers requirements confirmation.
  Runs Stage A (core path confirmation) → Stage B (standard module sign-off)
  → Stage C (boundary decisions). Outputs requirements-brief.json.
  Auto-triggered at end of product-concept. Also runnable standalone as /requirements.
---

# Requirements Confirmation

> Before product-map expansion, confirm core paths, standard modules, and key boundaries
> from high-level to detail. Outputs `requirements-brief.json` as the confirmed basis for product-map.

---

## Trigger Conditions

- **Auto-triggered**: immediately after product-concept generates `concept-baseline.json`
- **Manual trigger**: user runs `/requirements` (re-confirm after scope changes)

---

## Stage A — Core Paths Confirmation

**Input:** `.allforai/product-concept/concept-baseline.json`  

**When concept-baseline.json is absent:** Prompt user to run `/product-concept` first, or switch to manual mode — ask the user directly:
1. Who are the core user roles for this product?
2. What is the main usage path for each role (trigger → steps → success outcome)?

Collect 2-4 paths manually, then proceed to Stage B.

**Goal:** Lock the main user paths before any expansion (typically 2-4). When there are more than 4 roles, group them by primary business value and present in batches; the user can confirm all or focus on core roles first.

Read roles + business_model from concept-baseline and derive 2–4 core paths. Each path contains:

| Field | Description |
|-------|-------------|
| `actor` | The role executing this path |
| `trigger` | Trigger condition (what event starts the path) |
| `steps` | Trunk step sequence (happy path only, no exception branches) |
| `success_outcome` | System state when the path completes successfully |

**Example display format:**

```
Core Paths:

1. Buyer
   Trigger: Initiates purchase after selecting a product
   Steps: Search product → Add to cart → Checkout → Pay
   Success outcome: Order created and awaiting fulfillment, inventory reserved, waiting for seller to ship

2. Seller
   Trigger: New order pending processing
   Steps: View order → Prepare goods → Enter shipping info → Confirm shipment
   Success outcome: Order enters logistics phase, buyer receives shipment notification

3. Admin
   Trigger: User complaint received
   Steps: View complaint → Review evidence → Take action (warn / ban)
   Success outcome: Complaint closed, action record retained

Please confirm these paths, or point out any missing or incorrect items:
```

**Confirmation Rule:**
- User replies explicitly ("confirmed" / "continue" / "no changes" / points out changes) → lock paths, proceed to Stage B
- No reply / session interrupted → `status: "pending"`, do not auto-advance

---

## Stage B — Standard Modules Bulk Sign-off

**Input:** Paths confirmed in Stage A + project type (fullstack / backend / frontend)  
**Goal:** Confirm standard infrastructure in one message, no item-by-item discussion.

### Module Catalog (Three-Tier Structure)

**Tier 1 — foundation_defaults** (enabled by default; user may disable)

| Module ID | Module Name | Default Solution | inclusion_rule | fullstack | backend | frontend |
|-----------|-------------|-----------------|----------------|-----------|---------|----------|
| SM-auth | Authentication | Email/password + Google OAuth | always | ✓ | ✓ | ✓ |
| SM-session | Session | JWT, 7-day expiry, refresh token | always | ✓ | ✓ | — |
| SM-rbac | Authorization | RBAC, admin / user two levels | always | ✓ | ✓ | — |
| SM-email | Email Notification | Registration confirmation / password reset | always | ✓ | ✓ | — |
| SM-softdelete | Soft Delete | Logical deletion retention for user/order data | has_user_data OR has_order_data | ✓ | ✓ | — |

**SM-auth frontend specialization:** When project type is `frontend` (no own backend), the default changes to "Third-party auth SDK integration (Firebase Auth / Auth0) + local token storage" — do not show "Email/password + Google OAuth" which implies a self-hosted auth backend.

**inclusion_rule evaluation:** Before displaying the Stage B module list, evaluate each foundation_default module's `inclusion_rule`:
- `always` → always include
- `has_user_data OR has_order_data` → include only when Stage A paths involve user account operations or order operations; otherwise set `status: "excluded"` and omit from the displayed list

**Tier 2 — domain_defaults** (LLM infers from Stage A paths; displayed with `[inferred]` tag)

| Domain Signal (from Stage A paths) | Inferred Modules |
|-------------------------------------|-----------------|
| E-commerce paths (purchase/order/payment) | Payment + Refunds, Shipment Tracking, Product Reviews |
| Social paths (follow/content/interaction) | Follow Graph, Push Notifications, Content Moderation |
| Enterprise management paths (approval/permissions/reporting) | Audit Log, Multi-tenancy, SSO |
| SaaS paths (subscription/usage/billing) | Subscription Billing, Usage Metrics, Webhooks |

**When no domain matches:** If Stage A paths do not match any domain signal above, show a prompt in the Tier 2 area instead of leaving it empty:

```
Domain layer (no known domain pattern detected)
  If you need domain-specific modules (e.g. medical records, shipment tracking, leaderboards), please specify
```

**Tier 3 — optional_candidates** (not shown by default; listed under "Optional" section)

Real-time Chat / File Storage / Full-text Search / Internationalization (i18n) / Offline Support (PWA)

### Display Format

```
Standard Modules — reply "confirmed" or point out changes to proceed:

Foundation Layer (enabled by default)
  [Auth]        Email/password + Google OAuth
  [Session]     JWT, 7-day expiry, refresh token
  [AuthZ]       RBAC, admin / user two levels
  [Notification] Email (registration confirmation / password reset)
  [Soft Delete] Logical deletion retention for user/order data

Domain Layer (inferred from core paths)
  [Payment]     Third-party gateway, supports refund requests  [inferred]
  [Reviews]     Buyer reviews on orders, seller can reply  [inferred]
  [In-app Notifications] Grouped by type, supports read/unread  [inferred]

Optional (let us know if needed)
  Real-time Chat / File Storage / Full-text Search / i18n / PWA Offline

Reply "confirmed" to continue, or describe the items you want to change:
```

**Confirmation Rule:**
- "confirmed" / "confirm" / "continue" / "no changes" → write `status: "confirmed"`, `decision_source: "user_confirmed"` for all displayed modules
- Corrections only (no explicit "confirm") → changed items get `decision_source: "user_override"`; remaining items are treated as implicitly confirmed: `status: "confirmed", decision_source: "user_confirmed"`
- No reply / interrupted → all modules get `status: "pending"`
- User says "don't need X" / "remove X" / "disable X" → write `status: "excluded"`, `decision_source: "user_excluded"` for that module; no tasks generated

---

## Stage C — Key Boundary Decisions

**Input:** Stage A paths + Stage B modules  
**Goal:** Use multiple-choice questions to close 3–5 ambiguities that cannot be inferred.

### Question Selection Rule

Only ask about ambiguities that satisfy at least one of the following:
1. **Affects data entities**: requires adding new entities, fields, or relationships
2. **Affects the permission model**: who can / cannot perform an action
3. **Affects key state transitions**: branching states in core paths
4. **Affects external integration choices**: which third-party to use, or whether to integrate
5. **Affects billing / compliance constraints**: payment rules, data retention requirements

Ambiguities where a sensible default can be set: skip the question, record `decision_source: "default"` in the output.

**Question format (one question at a time, always include options):**

```
The path "Buyer Checkout" has one point that needs confirmation:

How long should an order be retained after a payment failure?
  a) Auto-cancel after 30 minutes
  b) 24 hours (user can retry payment)
  c) Never auto-cancel, handle manually
```

Maximum 5 questions. Stage C completes once all are answered.

**Out-of-option answers:** If the user's answer is not one of the given options (e.g. "1 hour", "depends on order amount"), write the user's verbatim text to `selected_option`, set `decision_source: "user_custom"`, and continue to the next question. Do not re-ask; do not force-map to existing options.

**Question flow:** Display one question at a time, wait for the user's answer before showing the next. After all questions are answered (or confirmed no more questions), proceed to the output phase.

If no ambiguities meet the question selection rules, skip Stage C and output requirements-brief.json directly (`boundary_decisions: []` is a valid value).

---

## Output: requirements-brief.json

Write to `.allforai/product-concept/requirements-brief.json`:

```json
{
  "schema_version": "1.1",
  "generated_at": "<ISO 8601>",
  "confirmed_at": "<ISO 8601 or null>",
  "confirmed_status": "fully_confirmed | partially_confirmed | pending",
  "source_command": "/product-concept | /requirements",
  "based_on_concept_baseline_version": "<mtime ISO 8601 of concept-baseline.json; if unavailable use generated_at>",

  "core_paths": [
    {
      "id": "CP-001",
      "actor": "Buyer",
      "trigger": "Initiates purchase after selecting a product",
      "steps": ["Search product", "Add to cart", "Checkout", "Pay"],
      "success_outcome": "Order created and awaiting fulfillment, inventory reserved, waiting for seller to ship",
      "status": "confirmed | pending",
      "notes": null
    }
  ],

  "standard_modules": [
    {
      "id": "SM-auth",
      "name": "Authentication",
      "tier": "foundation_default",
      "default": "Email/password + Google OAuth",
      "status": "confirmed | pending | excluded",
      "decision_source": "default | user_confirmed | user_override | user_excluded | inferred",
      "override": null
    }
  ],

  "boundary_decisions": [
    {
      "id": "BD-001",
      "question": "How long should an order be retained after a payment failure?",
      "options": ["Auto-cancel after 30 minutes", "24 hours (user can retry payment)", "Never auto-cancel, handle manually"],
      "selected_option": "Auto-cancel after 30 minutes",
      "decision_source": "user_selected | user_custom | default",
      "rationale": null,
      "impact_scope": ["CP-001", "SM-payment"]
    }
  ],

  "unconfirmed_areas": []
}
```

**`confirmed_status` evaluation logic:**
- `fully_confirmed`: all core_paths + standard_modules + boundary_decisions are confirmed
- `partially_confirmed`: at least one item is pending, but Stage A/B/C have been completed
- `pending`: Stage A/B/C not completed (session interrupted)

**`unconfirmed_areas` field rules:**
- Items with `status: "pending"` in Stage A/B/C — add their IDs (e.g. `CP-001`, `SM-payment`) to this array
- If all items are confirmed, write `[]`

---

## product-map Consumption Rules

| confirmed_status | product-map behavior |
|-----------------|----------------------|
| `fully_confirmed` | Skip directional questions; use core_paths to generate business-flows skeleton; standard_modules generate tasks directly |
| `partially_confirmed` | Skip confirmed portions; continue asking for pending items before expanding |
| `stale` (schema version mismatch) | Warn user; fall back to standard flow |
| File not found | Prompt user to run /requirements first; or continue with unconfirmed status |

Tasks generated from standard_modules carry a `"source": "standard_module"` tag, visually distinguished from business tasks in review.
