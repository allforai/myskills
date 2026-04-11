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
  detect requirements-brief.json → read as input, skip directional questions
  no requirements-brief.json → warn user, offer to run /requirements first,
                               or continue with unconfirmed status
```

Stages A→B→C run automatically in sequence. The user experiences them as the tail end of `/product-concept`, not as a separate command.

A standalone `/requirements` command is also added for re-running independently (e.g., after scope change).

---

## Stage A — Core Path Confirmation (coarse)

**Input:** concept-baseline.json  
**Goal:** Lock the 2-4 main user paths before any expansion.

LLM reads concept-baseline roles + business model, derives 2-4 core paths written as actor + step sequence. Only the happy path is shown — no exceptions, no edge cases.

**Interaction:**
```
核心路径：
1. 买家：搜索商品 → 加购 → 结账 → 收货确认
2. 卖家：上架商品 → 处理订单 → 发货
3. 管理员：处理投诉 → 封禁用户

确认以上路径，或告知遗漏/错误：
```

User reply locks paths. Additions or corrections are incorporated before proceeding to Stage B.

---

## Stage B — Standard Module Batch Sign-off

**Input:** Stage A confirmed paths + project type  
**Goal:** Confirm standard infrastructure in one message; skip lengthy discussion.

**Composition:**
- **Static baseline** (always shown, filtered by project type):

| Module | fullstack | backend | frontend |
|--------|-----------|---------|----------|
| 认证 (Auth) | ✓ | ✓ | — |
| 会话 (Session) | ✓ | ✓ | — |
| 权限 (RBAC) | ✓ | ✓ | — |
| 通知-邮件 | ✓ | ✓ | — |
| 软删除 | ✓ | ✓ | — |
| 国际化 (i18n) | optional | optional | optional |

- **Domain additions:** LLM infers 2-5 domain-specific modules from Stage A paths and product type. Examples: payment+refund for e-commerce, follow-graph for social, audit-log for enterprise admin.

**Interaction:**
```
标准模块 [默认方案] — 有异议请标注，其余视为确认：

基础层
  [认证]    邮箱密码 + Google OAuth
  [会话]    JWT，7天有效期，refresh token
  [权限]    RBAC，admin / user 两级
  [通知]    邮件（注册确认/密码重置）
  [软删除]  用户/订单数据逻辑删除

领域层（推断）
  [支付]    第三方网关，支持退款申请
  [评价]    买家对订单评价，卖家可回复
  [消息]    站内通知，按类型分组
```

User replies with only the items they want to change. Silence = confirmed.

---

## Stage C — Boundary Decisions (fine)

**Input:** Stage A paths + Stage B modules  
**Goal:** Close 3-5 ambiguities that cannot be inferred, using multiple-choice questions.

LLM scans confirmed paths for branch points that affect data model or flow design. Asks one question at a time, always with lettered options.

**Example:**
```
路径"买家结账"有一个需要确认的点：

支付失败后订单保留多久？
  a) 30分钟自动取消
  b) 24小时（用户可重新支付）
  c) 不自动取消，人工处理
```

Maximum 5 questions. Questions that can be reasonably defaulted are skipped (default noted in output).

---

## Output: requirements-brief.json

Written to `.allforai/product-concept/requirements-brief.json`.

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO 8601>",
  "confirmed_at": "<ISO 8601>",

  "core_paths": [
    {
      "id": "CP-001",
      "actor": "买家",
      "path": ["搜索商品", "加购", "结账", "收货确认"],
      "confirmed": true
    }
  ],

  "standard_modules": [
    {
      "id": "SM-auth",
      "name": "认证",
      "default": "邮箱密码 + Google OAuth",
      "confirmed": true,
      "override": null
    },
    {
      "id": "SM-payment",
      "name": "支付",
      "default": "第三方网关，支持退款申请",
      "confirmed": true,
      "override": "需支持微信支付"
    }
  ],

  "boundary_decisions": [
    {
      "id": "BD-001",
      "question": "支付失败后订单保留多久？",
      "answer": "30分钟自动取消",
      "affects_path": "CP-001"
    }
  ],

  "unconfirmed_areas": []
}
```

---

## Product-Map Integration

| requirements-brief field | product-map usage |
|--------------------------|-------------------|
| `core_paths` | Seed business-flows skeleton directly; no re-inference |
| `standard_modules` (confirmed) | Auto-generate corresponding tasks; no discussion |
| `standard_modules` (override) | Generate as customized tasks; flag for attention |
| `boundary_decisions` | Write to constraints.json for the affected flow |
| `unconfirmed_areas` | Flag in conflict-report.json as needs-confirmation |

Product-map skips directional questions when requirements-brief is present. Standard module tasks are generated with a `source: "standard_module"` tag so they are visually distinct in review output.

---

## Files to Change

**New files:**
- `codex/product-design-skill/skills/requirements.md` — Stage A/B/C logic, standard module catalog, output schema
- `opencode/product-design-skill/skills/requirements.md` — English mirror

**Modified files:**
- `codex/product-design-skill/skills/product-concept.md` — append trigger block at end: "after concept-baseline.json, proceed to Requirements Confirmation"
- `opencode/product-design-skill/skills/product-concept.md` — mirror
- `codex/product-design-skill/skills/product-map.md` — add Step 0: detect + read requirements-brief.json
- `opencode/product-design-skill/skills/product-map.md` — mirror
- `codex/product-design-skill/AGENTS.md` — add requirements skill registration + artifact path
- `opencode/product-design-skill/SKILL.md` — add requirements skill registration + artifact path
- `codex/product-design-skill/execution-playbook.md` — add requirements phase to phase table
- `opencode/product-design-skill/execution-playbook.md` — mirror

**Artifact path added to `.allforai/`:**
- `.allforai/product-concept/requirements-brief.json`

---

## Non-Goals

- No re-running Stage A/B/C automatically when scope changes — user runs `/requirements` manually
- No deep requirement decomposition (that's product-map's job)
- No UI wireframes or screen design (that's experience-map's job)
- Standard module catalog does not include infrastructure choices (DB type, cloud provider) — those belong in product-concept pipeline_preferences
