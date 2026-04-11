# Product Requirements Confirmation Design

## Goal

Insert a progressive requirements confirmation phase between `/product-concept` and `/product-map`. Users confirm core user paths, sign off standard modules in bulk, and answer 3-5 boundary questions — producing `requirements-brief.json` that gives product-map a confirmed foundation so it doesn't start from scratch.

## Problem

Currently product-concept outputs vision-level artifacts (mission, roles, competitive strategy) and product-map immediately expands into full task-inventory + business-flows. There is no checkpoint where the user confirms "what we are actually building." Product-map can go in the wrong direction, requiring expensive rework.

## Workflow Position

```
/product-concept
  [existing steps: mission / roles / business model / competitive position]
  Step N+1: generate concept-baseline.json  (existing)
  Step N+2: auto-enter Requirements Confirmation (Stage A → B → C)  [NEW]
  → write requirements-brief.json
  → product-concept complete

/product-map
  detect requirements-brief.json
    confirmed_status = "fully_confirmed"    → skip directional questions
    confirmed_status = "partially_confirmed" → skip confirmed sections only;
                                               ask about pending areas
    confirmed_status = "pending"            → warn user; offer /requirements first,
                                               or continue with unconfirmed status
    confirmed_status = "stale" / schema mismatch → warn + fall back to
                                               standard flow (no silent skip)
  no requirements-brief.json → warn user, offer /requirements first,
                                or continue with unconfirmed status
```

Stages A→B→C run automatically in sequence. The user experiences them as the tail end of `/product-concept`, not as a separate command.

A standalone `/requirements` command is also added for re-running independently (e.g., after scope change).

---

## Stage A — Core Path Confirmation (coarse)

**Input:** concept-baseline.json (fallback: ask user to describe main roles and flows if file absent)
**Goal:** Lock the main user paths (typically 2-4; complex products may have more) before any expansion.

LLM reads concept-baseline roles + business model, derives the main core paths. Each path includes actor, trigger, main steps, and success outcome — no exceptions or edge cases.

**Path format:**

| Field | Description |
|-------|-------------|
| `actor` | Role performing the path |
| `trigger` | What initiates the path |
| `steps` | Main action sequence (happy path only) |
| `success_outcome` | What state the system is in when done |

**Interaction:**
```
核心路径：
1. 买家
   触发：选定商品后发起购买
   步骤：搜索商品 → 加购 → 结账 → 支付
   成功结果：形成待履约订单，库存锁定，等待卖家发货

2. 卖家
   触发：有新订单待处理
   步骤：查看订单 → 备货 → 填写快递信息 → 发货确认
   成功结果：订单进入物流阶段，买家收到通知

3. 管理员
   触发：收到用户投诉
   步骤：查看投诉 → 审核证据 → 处置（警告/封禁）
   成功结果：投诉关闭，处置记录留存

确认以上路径，或告知遗漏/错误：
```

**Confirmation rule:** Only an explicit user reply (confirm / continue / 无修改, or corrections) advances to Stage B. No reply → status remains `pending`; do not proceed automatically.

---

## Stage B — Standard Module Batch Sign-off

**Input:** Stage A confirmed paths + project type (read from `concept-baseline.pipeline_preferences.project_type`; default: `fullstack`)
**Goal:** Confirm standard infrastructure in one message; skip lengthy discussion.

### Module Catalog Structure

Modules are grouped in three tiers. Each module has an `inclusion_rule` that governs when it appears.

**Tier 1 — foundation_defaults** (shown by default, user can turn off):

| Module | inclusion_rule | fullstack | backend | frontend |
|--------|---------------|-----------|---------|----------|
| 认证 (Auth) | always | 邮箱+OAuth | 邮箱+OAuth | Firebase Auth / Auth0 |
| 会话 (Session) | always | ✓ | ✓ | — |
| 权限 (RBAC) | always | ✓ | ✓ | — |
| 通知-邮件 | always | ✓ | ✓ | — |
| 软删除 | has_user_data OR has_order_data | ✓ | ✓ | — |

Note: Auth module defaults to Firebase Auth / Auth0 when `project_type = frontend`.

**Tier 2 — domain_defaults** (LLM infers from Stage A paths; shown with `[推断]` label):

Examples by domain signal in Stage A paths:
- e-commerce paths → 支付+退款, 物流追踪, 商品评价
- social paths → 关注关系, 消息通知, 内容审核
- enterprise admin paths → 操作审计日志, 多租户, SSO
- SaaS paths → 订阅计费, 用量统计, Webhook

If no domain signals are inferred, Tier 2 is omitted; show message: "领域层（推断）：未识别到明显领域特征，跳过。"

**Tier 3 — optional_candidates** (not shown by default; listed at bottom as "可选项"):

Examples: 实时聊天, 文件存储, 全文搜索, 多语言 (i18n), 离线支持 (PWA)

### Interaction

```
标准模块 — 明确回复"确认"或指出修改项后继续：

基础层（默认启用）
  [认证]    邮箱密码 + Google OAuth
  [会话]    JWT，7天有效期，refresh token
  [权限]    RBAC，admin / user 两级
  [通知]    邮件（注册确认/密码重置）
  [软删除]  用户/订单数据逻辑删除保留

领域层（推断自核心路径）
  [支付]    第三方网关，支持退款申请  [推断]
  [评价]    买家对订单评价，卖家可回复  [推断]
  [消息]    站内通知，按类型分组  [推断]

可选项（如需请告知）
  实时聊天 / 文件存储 / 全文搜索 / i18n / PWA离线

回复"确认"继续，或说明要改的项：
```

**Confirmation rules:**
- Explicit "确认 / confirm / continue / 无修改" → writes `status: "confirmed"` for all modules; `decision_source: "user_confirmed"`.
- Correction-only reply (e.g., "支付改为微信支付，其余确认") → unchanged modules implicitly confirmed; corrected module gets `decision_source: "user_override"`.
- User explicitly removes a module (e.g., "去掉软删除") → `status: "excluded"`, `decision_source: "user_excluded"`.
- No reply or session interruption → `status: "pending"`.

---

## Stage C — Boundary Decisions (fine)

**Input:** Stage A paths + Stage B modules
**Goal:** Close ambiguities that cannot be inferred, using multiple-choice questions.

**Zero-question exit:** If no question passes the selection filter, Stage C is skipped and requirements-brief.json is written immediately with `boundary_decisions: []`.

### Question Selection Rule

Only ask questions where the answer affects at least one of:
- Data entity design (new entity, field, or relationship)
- Permission model (who can do what)
- Key state transitions in a core path
- External integration choice (which third-party, or none)
- Billing / compliance constraint

Questions that can be reasonably defaulted are skipped; the chosen default is recorded in `boundary_decisions` with `decision_source: "default"`.

Maximum 5 questions total.

### Interaction

Questions are asked one at a time. After each answer, confirm receipt briefly before presenting the next question:

```
路径"买家结账"有一个需要确认的点：

支付失败后订单保留多久？
  a) 30分钟自动取消
  b) 24小时（用户可重新支付）
  c) 不自动取消，人工处理
```

If the user answers outside the listed options (e.g., "2小时"), record the answer verbatim as `decision_source: "user_custom"`.

After all questions are answered (or defaulted), Stage C is complete and requirements-brief.json is written.

---

## Output: requirements-brief.json

Written to `.allforai/product-concept/requirements-brief.json`.

```json
{
  "schema_version": "1.1",
  "generated_at": "<ISO 8601>",
  "confirmed_at": "<ISO 8601 or null>",
  "confirmed_status": "fully_confirmed | partially_confirmed | pending",
  "source_command": "/product-concept | /requirements",
  "based_on_concept_baseline_version": "<mtime of concept-baseline.json>",

  "core_paths": [
    {
      "id": "CP-001",
      "actor": "买家",
      "trigger": "选定商品后发起购买",
      "steps": ["搜索商品", "加购", "结账", "支付"],
      "success_outcome": "形成待履约订单，库存锁定，等待卖家发货",
      "status": "confirmed | pending",
      "notes": null
    }
  ],

  "standard_modules": [
    {
      "id": "SM-auth",
      "name": "认证",
      "tier": "foundation_default",
      "default": "邮箱密码 + Google OAuth",
      "status": "confirmed | pending | excluded",
      "decision_source": "default | user_confirmed | user_override | user_excluded | inferred",
      "override": null
    },
    {
      "id": "SM-payment",
      "name": "支付",
      "tier": "domain_default",
      "default": "第三方网关，支持退款申请",
      "status": "confirmed",
      "decision_source": "user_override",
      "override": "需支持微信支付"
    }
  ],

  "boundary_decisions": [
    {
      "id": "BD-001",
      "question": "支付失败后订单保留多久？",
      "options": ["30分钟自动取消", "24小时（用户可重新支付）", "不自动取消，人工处理"],
      "selected_option": "30分钟自动取消",
      "decision_source": "user_selected | user_custom | default",
      "rationale": null,
      "impact_scope": ["CP-001", "SM-payment"]
    }
  ],

  "unconfirmed_areas": []
}
```

**`confirmed_status` logic:**
- `fully_confirmed`: all core_paths `status: confirmed`, all standard_modules `status: confirmed | excluded`, all boundary_decisions have `decision_source` set
- `partially_confirmed`: Stage A confirmed but Stage B or C not completed; `unconfirmed_areas` lists affected item IDs
- `pending`: Stage A not yet completed (session interrupted before any confirmation)

**`unconfirmed_areas` population rule:** After each stage completes, append IDs of any items that remain `status: "pending"`. If all items in a stage are confirmed, nothing is appended for that stage.

---

## Product-Map Integration

| requirements-brief state | product-map behavior |
|--------------------------|----------------------|
| `fully_confirmed` | Skip all directional questions; seed flows + tasks from brief |
| `partially_confirmed` | Skip confirmed sections; ask about pending areas before expanding |
| `pending` | Warn user; offer `/requirements` first, or continue as unconfirmed |
| `stale` (schema_version mismatch OR concept-baseline.json mtime newer than `based_on_concept_baseline_version`) | Warn user; fall back to standard flow; set `requirements_stale: true` in product-map.json |
| File absent | Warn user; offer `/requirements`; or continue as unconfirmed |

**Field usage:**

| Field | product-map usage |
|-------|-------------------|
| `core_paths` | Seed business-flows skeleton; `success_outcome` anchors flow end state |
| `standard_modules` (confirmed) | Auto-generate tasks with `source: "standard_module"` tag |
| `standard_modules` (user_override) | Generate as customized tasks; flag for attention |
| `standard_modules` (pending) | Ask user before generating |
| `standard_modules` (excluded) | Skip generation entirely |
| `boundary_decisions` | Write to constraints.json for the affected flow |
| `unconfirmed_areas` | Flag in conflict-report.json |

---

## Files to Change

**New files:**
- `codex/product-design-skill/skills/requirements.md` — Stage A/B/C logic, module catalog (3 tiers + inclusion_rules), output schema, confirmation rules
- `opencode/product-design-skill/skills/requirements.md` — English mirror

**Modified files:**
- `codex/product-design-skill/skills/product-concept.md` — append trigger block at end: after concept-baseline.json, auto-enter Requirements Confirmation
- `opencode/product-design-skill/skills/product-concept.md` — mirror
- `codex/product-design-skill/skills/product-map.md` — add Step 0: detect + read requirements-brief.json with confirmed_status branch (5 states)
- `opencode/product-design-skill/skills/product-map.md` — mirror
- `codex/product-design-skill/AGENTS.md` — add requirements skill registration (row 1.6) + artifact path + resume marker
- `opencode/product-design-skill/SKILL.md` — add requirements skill registration + artifact path
- `codex/product-design-skill/execution-playbook.md` — add Phase 1.6 requirements to phase table
- `opencode/product-design-skill/execution-playbook.md` — mirror

**Artifact path added to `.allforai/`:**
- `.allforai/product-concept/requirements-brief.json`

**Test / validation items:**
- Sample `requirements-brief.json` with `fully_confirmed` status (e-commerce golden case)
- Sample `requirements-brief.json` with `partially_confirmed` status (Stage B interrupted)
- Sample with `schema_version: "1.0"` (stale detection test)
- Golden path transcript: `/product-concept` → Stage A/B/C interaction → `requirements-brief.json` → `/product-map` Step 0 reads and branches correctly

---

## Non-Goals

- No re-running Stage A/B/C automatically when scope changes — user runs `/requirements` manually
- No deep requirement decomposition (that's product-map's job)
- No UI wireframes or screen design (that's experience-map's job)
- Standard module catalog does not include infrastructure choices (DB type, cloud provider) — those belong in product-concept pipeline_preferences
