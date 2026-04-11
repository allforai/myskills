# Product Requirements Confirmation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/requirements` phase that auto-triggers at the end of `/product-concept`, walks users through progressive requirements confirmation (Stage A: core paths → Stage B: standard module sign-off → Stage C: boundary decisions), and outputs `requirements-brief.json` consumed by `/product-map`.

**Architecture:** New `requirements.md` skill file contains all Stage A/B/C logic, a 3-tier standard module catalog with `inclusion_rule` per entry, explicit confirmation rules (no silence = confirmed), and the `requirements-brief.json` v1.1 schema. `product-concept.md` gets a trigger block at EOF. `product-map.md` gets a Step 0 that branches on `confirmed_status`. Registration files (AGENTS.md, SKILL.md, execution-playbook.md) are updated in both codex and opencode directories.

**Tech Stack:** Markdown skill files, JSON schema samples, no runnable code.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `codex/product-design-skill/skills/requirements.md` | Stage A/B/C logic, module catalog, schema, confirmation rules |
| Create | `opencode/product-design-skill/skills/requirements.md` | English mirror |
| Modify | `codex/product-design-skill/skills/product-concept.md` (EOF) | Append auto-trigger block |
| Modify | `opencode/product-design-skill/skills/product-concept.md` (EOF) | English mirror |
| Modify | `codex/product-design-skill/skills/product-map.md` (before Step 1) | Prepend Step 0: requirements detection |
| Modify | `opencode/product-design-skill/skills/product-map.md` (before Step 1) | English mirror |
| Modify | `codex/product-design-skill/AGENTS.md` | Add row to sub-skills table; update pipeline phases |
| Modify | `opencode/product-design-skill/SKILL.md` | Add skill section; update pipeline description |
| Modify | `codex/product-design-skill/execution-playbook.md` | Insert Phase 1.x in pipeline |
| Modify | `opencode/product-design-skill/execution-playbook.md` | Mirror |
| Create | `codex/product-design-skill/docs/samples/requirements-brief-full.json` | fully_confirmed sample |
| Create | `codex/product-design-skill/docs/samples/requirements-brief-partial.json` | partially_confirmed sample |
| Create | `codex/product-design-skill/docs/samples/requirements-brief-stale.json` | stale/schema-mismatch sample |
| Create | `codex/product-design-skill/docs/samples/requirements-golden-path.md` | Golden path transcript |

---

## Task 1: Create codex/requirements.md skill file

**Files:**
- Create: `codex/product-design-skill/skills/requirements.md`

- [ ] **Step 1: Create the file with frontmatter and Stage A**

```markdown
---
name: requirements
description: >
  Use when the user asks to confirm requirements, "需求确认", "核对需求",
  or when product-concept finishes and auto-triggers requirements confirmation.
  Runs Stage A (core path confirmation) → Stage B (standard module sign-off)
  → Stage C (boundary decisions). Outputs requirements-brief.json.
  Auto-triggered at end of product-concept. Also runnable standalone as /requirements.
---

# Requirements Confirmation — 需求确认

> 在 product-map 展开前，从粗到细确认核心路径、标准模块、关键边界。
> 输出 `requirements-brief.json`，作为 product-map 的确认基础。

---

## 触发条件

- **自动触发**：product-concept 生成 `concept-baseline.json` 后立即进入本阶段
- **手动触发**：用户运行 `/requirements`（需求范围变更后重新确认）

---

## Stage A — 核心路径确认

**输入：** `.allforai/product-concept/concept-baseline.json`  
**目标：** 在任何展开前，锁定 2-4 条主干用户路径。

读取 concept-baseline 中的 roles + business_model，推导 2-4 条核心路径。每条路径包含：

| 字段 | 说明 |
|------|------|
| `actor` | 执行该路径的角色 |
| `trigger` | 触发条件（什么事件启动这条路径） |
| `steps` | 主干步骤序列（只含 happy path，不含异常） |
| `success_outcome` | 路径完成时系统所处的状态 |

**示例展示格式：**

```
核心路径：

1. 买家
   触发：选定商品后发起购买
   步骤：搜索商品 → 加购 → 结账 → 支付
   成功结果：形成待履约订单，库存锁定，等待卖家发货

2. 卖家
   触发：有新订单待处理
   步骤：查看订单 → 备货 → 填写快递信息 → 发货确认
   成功结果：订单进入物流阶段，买家收到发货通知

3. 管理员
   触发：收到用户投诉
   步骤：查看投诉 → 审核证据 → 处置（警告/封禁）
   成功结果：投诉关闭，处置记录留存

确认以上路径，或告知遗漏/错误：
```

**确认规则：**
- 用户明确回复（"确认" / "continue" / "无修改" / 指出修改点）→ 锁定路径，进入 Stage B
- 无回复 / 会话中断 → `status: "pending"`，不自动推进

---

## Stage B — 标准模块批量 Sign-off

**输入：** Stage A 确认的路径 + 项目类型（fullstack / backend / frontend）  
**目标：** 一条消息确认标准基础设施，不做逐项讨论。

### 模块目录（三层结构）

**Tier 1 — foundation_defaults**（默认启用，用户可关闭）

| 模块 ID | 模块名 | 默认方案 | inclusion_rule | fullstack | backend | frontend |
|---------|--------|---------|----------------|-----------|---------|----------|
| SM-auth | 认证 | 邮箱密码 + Google OAuth | always | ✓ | ✓ | ✓ |
| SM-session | 会话 | JWT，7天有效期，refresh token | always | ✓ | ✓ | — |
| SM-rbac | 权限 | RBAC，admin / user 两级 | always | ✓ | ✓ | — |
| SM-email | 通知-邮件 | 注册确认 / 密码重置 | always | ✓ | ✓ | — |
| SM-softdelete | 软删除 | 用户/订单数据逻辑删除保留 | has_user_data OR has_order_data | ✓ | ✓ | — |

**Tier 2 — domain_defaults**（LLM 从 Stage A 路径推断，展示时加 `[推断]` 标签）

| 领域信号（来自 Stage A 路径） | 推断模块 |
|------------------------------|---------|
| 电商路径（购买/订单/支付） | 支付+退款, 物流追踪, 商品评价 |
| 社交路径（关注/内容/互动） | 关注关系, 消息通知, 内容审核 |
| 企业管理路径（审批/权限/报表） | 操作审计日志, 多租户, SSO |
| SaaS 路径（订阅/用量/账单） | 订阅计费, 用量统计, Webhook |

**Tier 3 — optional_candidates**（不默认展示，列在"可选项"区）

实时聊天 / 文件存储 / 全文搜索 / 多语言(i18n) / 离线支持(PWA)

### 展示格式

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
  [站内通知] 按类型分组，支持已读/未读  [推断]

可选项（如需请告知）
  实时聊天 / 文件存储 / 全文搜索 / i18n / PWA 离线

回复"确认"继续，或说明要修改的项：
```

**确认规则：**
- "确认" / "confirm" / "continue" / "无修改" → 所有展示模块写 `status: "confirmed"`
- 指出修改 → 修改项写 `decision_source: "user_override"`，其余写 `status: "confirmed"`
- 无回复 / 中断 → 所有模块写 `status: "pending"`

---

## Stage C — 关键边界决策

**输入：** Stage A 路径 + Stage B 模块  
**目标：** 用选择题关闭 3-5 个无法推断的歧义点。

### 提问选择规则

只提问满足以下至少一项的歧义：
1. **影响数据实体**：需要新增实体、字段或关系
2. **影响权限模型**：谁能做 / 谁不能做
3. **影响关键状态转换**：核心路径中的分支状态
4. **影响外部集成选择**：选哪家第三方，或是否集成
5. **影响计费/合规约束**：付费规则、数据保留要求

可合理设默认值的歧义：跳过提问，在输出中记录 `decision_source: "default"`。

**提问格式（每次一个问题，必须给选项）：**

```
路径"买家结账"有一个需要确认的点：

支付失败后订单保留多久？
  a) 30分钟自动取消
  b) 24小时（用户可重新支付）
  c) 不自动取消，人工处理
```

最多 5 个问题。全部回答后 Stage C 完成。

---

## 输出：requirements-brief.json

写入 `.allforai/product-concept/requirements-brief.json`：

```json
{
  "schema_version": "1.1",
  "generated_at": "<ISO 8601>",
  "confirmed_at": "<ISO 8601 or null>",
  "confirmed_status": "fully_confirmed | partially_confirmed | pending",
  "source_command": "/product-concept | /requirements",
  "based_on_concept_baseline_version": "<hash or timestamp>",

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
      "decision_source": "default | user_confirmed | user_override | inferred",
      "override": null
    }
  ],

  "boundary_decisions": [
    {
      "id": "BD-001",
      "question": "支付失败后订单保留多久？",
      "options": ["30分钟自动取消", "24小时（用户可重新支付）", "不自动取消，人工处理"],
      "selected_option": "30分钟自动取消",
      "decision_source": "user_selected | default",
      "rationale": null,
      "impact_scope": ["CP-001", "SM-payment"],
      "affects_path": "CP-001"
    }
  ],

  "unconfirmed_areas": []
}
```

**`confirmed_status` 判断逻辑：**
- `fully_confirmed`：所有 core_paths + standard_modules + boundary_decisions 均为 confirmed
- `partially_confirmed`：至少一项为 pending，但 Stage A/B/C 已完成
- `pending`：Stage A/B/C 未完成（会话中断）

---

## product-map 消费规则

| confirmed_status | product-map 行为 |
|-----------------|----------------|
| `fully_confirmed` | 跳过方向性问题；用 core_paths 生成 business-flows 骨架；standard_modules 直接生成 tasks |
| `partially_confirmed` | 跳过已确认部分；对 pending 项继续提问再展开 |
| `stale`（schema 版本不匹配） | 警告用户；回退到常规流程 |
| 文件不存在 | 提示用户先运行 /requirements；或以 unconfirmed 状态继续 |

standard_modules 生成的 tasks 带 `"source": "standard_module"` 标签，在 review 中与业务 tasks 视觉区分。
```

- [ ] **Step 2: Verify file was created**

```bash
wc -l codex/product-design-skill/skills/requirements.md
```
Expected: output showing 200+ lines.

- [ ] **Step 3: Validate JSON schema in the file is valid**

```bash
# Extract the JSON block and validate it
python3 -c "
import json
schema = {
  'schema_version': '1.1',
  'generated_at': '2026-04-11T10:00:00Z',
  'confirmed_at': None,
  'confirmed_status': 'fully_confirmed',
  'source_command': '/product-concept',
  'based_on_concept_baseline_version': 'abc123',
  'core_paths': [{'id':'CP-001','actor':'买家','trigger':'发起购买','steps':['结账','支付'],'success_outcome':'形成订单','status':'confirmed','notes':None}],
  'standard_modules': [{'id':'SM-auth','name':'认证','tier':'foundation_default','default':'邮箱密码','status':'confirmed','decision_source':'default','override':None}],
  'boundary_decisions': [],
  'unconfirmed_areas': []
}
print(json.dumps(schema, ensure_ascii=False, indent=2))
print('Schema valid')
"
```
Expected: prints valid JSON + "Schema valid".

- [ ] **Step 4: Commit**

```bash
git add codex/product-design-skill/skills/requirements.md
git commit -m "feat(product-design): add requirements.md skill — Stage A/B/C + module catalog + schema v1.1"
```

---

## Task 2: Create opencode/requirements.md (English mirror)

**Files:**
- Create: `opencode/product-design-skill/skills/requirements.md`

- [ ] **Step 1: Create the English mirror**

```markdown
---
name: requirements
description: >
  Use when the user asks to confirm requirements, or when product-concept finishes
  and auto-triggers requirements confirmation.
  Runs Stage A (core path confirmation) → Stage B (standard module sign-off)
  → Stage C (boundary decisions). Outputs requirements-brief.json.
  Auto-triggered at end of product-concept. Also runnable standalone as /requirements.
---

# Requirements Confirmation

> Progressive requirements confirmation before product-map expands.
> Outputs `requirements-brief.json` as a confirmed foundation for product-map.

---

## Trigger Conditions

- **Auto-trigger**: runs immediately after product-concept generates `concept-baseline.json`
- **Manual trigger**: user runs `/requirements` (e.g., after scope change)

---

## Stage A — Core Path Confirmation

**Input:** `.allforai/product-concept/concept-baseline.json`  
**Goal:** Lock 2-4 main user paths before any expansion.

Read concept-baseline roles + business_model, derive 2-4 core paths. Each path includes:

| Field | Description |
|-------|-------------|
| `actor` | Role performing the path |
| `trigger` | What initiates the path |
| `steps` | Main action sequence (happy path only, no exceptions) |
| `success_outcome` | System state when path completes |

**Display format:**

```
Core paths:

1. Buyer
   Trigger: initiates purchase after selecting product
   Steps: search product → add to cart → checkout → pay
   Success outcome: order created, inventory locked, awaiting seller shipment

2. Seller
   Trigger: new order awaiting processing
   Steps: view order → prepare → fill shipping info → confirm shipment
   Success outcome: order enters logistics phase, buyer notified

3. Admin
   Trigger: receives user complaint
   Steps: view complaint → review evidence → take action (warn/ban)
   Success outcome: complaint closed, action recorded

Confirm the above paths, or indicate any missing or incorrect ones:
```

**Confirmation rule:**
- Explicit reply ("confirm" / "continue" / "no changes" / corrections) → lock paths, proceed to Stage B
- No reply / session interruption → `status: "pending"`, do not auto-advance

---

## Stage B — Standard Module Batch Sign-off

**Input:** Stage A confirmed paths + project type (fullstack / backend / frontend)  
**Goal:** Confirm standard infrastructure in one message; no per-item discussion.

### Module Catalog (3 tiers)

**Tier 1 — foundation_defaults** (enabled by default, user can disable):

| Module ID | Name | Default | inclusion_rule | fullstack | backend | frontend |
|-----------|------|---------|----------------|-----------|---------|----------|
| SM-auth | Auth | Email/password + Google OAuth | always | ✓ | ✓ | ✓ |
| SM-session | Session | JWT, 7-day expiry, refresh token | always | ✓ | ✓ | — |
| SM-rbac | Permissions | RBAC, admin / user two levels | always | ✓ | ✓ | — |
| SM-email | Email notifications | Registration confirm / password reset | always | ✓ | ✓ | — |
| SM-softdelete | Soft delete | Logical deletion for user/order data | has_user_data OR has_order_data | ✓ | ✓ | — |

**Tier 2 — domain_defaults** (LLM infers from Stage A paths; shown with `[inferred]` label):

| Domain signal (from Stage A paths) | Inferred modules |
|------------------------------------|-----------------|
| E-commerce paths (purchase/order/payment) | Payment+refund, order tracking, product reviews |
| Social paths (follow/content/interaction) | Follow graph, message notifications, content moderation |
| Enterprise admin paths (approval/roles/reports) | Audit log, multi-tenant, SSO |
| SaaS paths (subscription/usage/billing) | Subscription billing, usage metrics, Webhook |

**Tier 3 — optional_candidates** (not shown by default; listed as "optional"):

Real-time chat / File storage / Full-text search / i18n / PWA offline

### Display format

```
Standard modules — reply "confirm" or specify changes:

Foundation layer (enabled by default)
  [Auth]        Email/password + Google OAuth
  [Session]     JWT, 7-day expiry, refresh token
  [Permissions] RBAC, admin / user two levels
  [Email]       Registration confirm / password reset
  [Soft delete] Logical deletion for user/order data

Domain layer (inferred from core paths)
  [Payment]     Third-party gateway, supports refunds  [inferred]
  [Reviews]     Buyer reviews on orders, seller can reply  [inferred]
  [Inbox]       In-app notifications, grouped by type  [inferred]

Optional (request if needed)
  Real-time chat / File storage / Full-text search / i18n / PWA offline

Reply "confirm" to continue, or specify any changes:
```

**Confirmation rule:**
- "confirm" / "continue" / "no changes" → all shown modules written as `status: "confirmed"`
- Specific changes → changed items written as `decision_source: "user_override"`, rest as `status: "confirmed"`
- No reply / interruption → all modules written as `status: "pending"`

---

## Stage C — Boundary Decisions

**Input:** Stage A paths + Stage B modules  
**Goal:** Close 3-5 ambiguities using multiple-choice questions.

### Question Selection Rule

Only ask questions where the answer affects at least one of:
1. **Data entity design**: requires new entity, field, or relationship
2. **Permission model**: who can / cannot do something
3. **Key state transitions**: branch states in a core path
4. **External integration choice**: which third-party, or whether to integrate
5. **Billing / compliance constraint**: pricing rules, data retention requirements

Ambiguities with reasonable defaults: skip question, record `decision_source: "default"` in output.

**Question format (one at a time, always with options):**

```
One point to confirm for path "Buyer checkout":

How long should a failed-payment order be retained?
  a) Auto-cancel after 30 minutes
  b) 24 hours (user can retry payment)
  c) No auto-cancel, manual handling
```

Maximum 5 questions. Stage C completes after all answered.

---

## Output: requirements-brief.json

Written to `.allforai/product-concept/requirements-brief.json`:

```json
{
  "schema_version": "1.1",
  "generated_at": "<ISO 8601>",
  "confirmed_at": "<ISO 8601 or null>",
  "confirmed_status": "fully_confirmed | partially_confirmed | pending",
  "source_command": "/product-concept | /requirements",
  "based_on_concept_baseline_version": "<hash or timestamp>",

  "core_paths": [
    {
      "id": "CP-001",
      "actor": "Buyer",
      "trigger": "initiates purchase after selecting product",
      "steps": ["search product", "add to cart", "checkout", "pay"],
      "success_outcome": "order created, inventory locked, awaiting seller shipment",
      "status": "confirmed | pending",
      "notes": null
    }
  ],

  "standard_modules": [
    {
      "id": "SM-auth",
      "name": "Auth",
      "tier": "foundation_default",
      "default": "Email/password + Google OAuth",
      "status": "confirmed | pending | excluded",
      "decision_source": "default | user_confirmed | user_override | inferred",
      "override": null
    }
  ],

  "boundary_decisions": [
    {
      "id": "BD-001",
      "question": "How long should a failed-payment order be retained?",
      "options": ["Auto-cancel after 30 minutes", "24 hours (user can retry)", "No auto-cancel, manual"],
      "selected_option": "Auto-cancel after 30 minutes",
      "decision_source": "user_selected | default",
      "rationale": null,
      "impact_scope": ["CP-001", "SM-payment"],
      "affects_path": "CP-001"
    }
  ],

  "unconfirmed_areas": []
}
```

**`confirmed_status` logic:**
- `fully_confirmed`: all core_paths + standard_modules + boundary_decisions have `status: confirmed`
- `partially_confirmed`: at least one item is `pending`, but Stage A/B/C completed
- `pending`: Stage A/B/C not completed (session interrupted)

---

## Product-Map Consumption Rules

| confirmed_status | product-map behavior |
|-----------------|---------------------|
| `fully_confirmed` | Skip directional questions; seed business-flows from core_paths; auto-generate standard_module tasks |
| `partially_confirmed` | Skip confirmed sections; ask about pending items before expanding |
| `stale` (schema version mismatch) | Warn user; fall back to standard flow |
| File absent | Prompt user to run /requirements first; or continue as unconfirmed |

Standard module tasks are tagged `"source": "standard_module"` so they are visually distinct from business tasks in review output.
```

- [ ] **Step 2: Verify file created**

```bash
wc -l opencode/product-design-skill/skills/requirements.md
```
Expected: 200+ lines.

- [ ] **Step 3: Commit**

```bash
git add opencode/product-design-skill/skills/requirements.md
git commit -m "feat(product-design): add opencode requirements.md skill (English mirror)"
```

---

## Task 3: Add trigger block to product-concept.md (both)

**Files:**
- Modify: `codex/product-design-skill/skills/product-concept.md` (append at EOF, after line 891)
- Modify: `opencode/product-design-skill/skills/product-concept.md` (append at EOF)

- [ ] **Step 1: Check current EOF of codex product-concept.md**

```bash
tail -5 codex/product-design-skill/skills/product-concept.md
```
Expected: lines ending with the "Innovation Boost" rule text.

- [ ] **Step 2: Append trigger block to codex product-concept.md**

Append this content at the very end of `codex/product-design-skill/skills/product-concept.md`:

```markdown

---

## 需求确认（自动触发 — concept-baseline.json 生成后立即执行）

> 详见 `./skills/requirements.md`

`concept-baseline.json` 生成后，自动进入需求确认阶段（Stage A → B → C）：

1. **Stage A**：展示推导出的核心路径，等待用户明确确认
2. **Stage B**：展示标准模块清单（基础层 + 领域层推断），等待用户明确确认
3. **Stage C**：逐一提问 3-5 个无法推断的关键边界，用选择题

三个 Stage 顺序执行。全部完成后写入 `.allforai/product-concept/requirements-brief.json`。

**不得在用户明确回复前自动推进任何 Stage。** 无回复 / 会话中断 → 对应 Stage 写 `status: "pending"`。
```

- [ ] **Step 3: Append trigger block to opencode product-concept.md**

Check EOF first:
```bash
tail -5 opencode/product-design-skill/skills/product-concept.md
```

Append this content at the very end:

```markdown

---

## Requirements Confirmation (Auto-triggered — runs after concept-baseline.json)

> See `./skills/requirements.md`

After `concept-baseline.json` is generated, automatically enter Requirements Confirmation (Stage A → B → C):

1. **Stage A**: Present derived core paths; wait for explicit user confirmation
2. **Stage B**: Present standard module list (foundation layer + inferred domain layer); wait for explicit user confirmation
3. **Stage C**: Ask 3-5 multiple-choice questions for key boundary decisions

Stages run in sequence. After all complete, write `.allforai/product-concept/requirements-brief.json`.

**Do not auto-advance any Stage without an explicit user reply.** No reply / session interruption → write `status: "pending"` for that Stage.
```

- [ ] **Step 4: Verify both files end with the trigger block**

```bash
tail -10 codex/product-design-skill/skills/product-concept.md
tail -10 opencode/product-design-skill/skills/product-concept.md
```
Expected: both show the trigger block content.

- [ ] **Step 5: Commit**

```bash
git add codex/product-design-skill/skills/product-concept.md \
        opencode/product-design-skill/skills/product-concept.md
git commit -m "feat(product-design): trigger requirements confirmation after concept-baseline"
```

---

## Task 4: Add Step 0 to product-map.md (both)

**Files:**
- Modify: `codex/product-design-skill/skills/product-map.md` (before first Step heading)
- Modify: `opencode/product-design-skill/skills/product-map.md` (mirror)

- [ ] **Step 1: Find the first Step heading in codex product-map.md**

```bash
grep -n "^## Step\|^### Step 1\b\|^## 步骤\|^## 操作步骤\|^---" codex/product-design-skill/skills/product-map.md | head -20
```
Note the line number of the first step/phase heading — that's the insertion point.

- [ ] **Step 2: Insert Step 0 in codex product-map.md**

Find the line that starts the first step (e.g., `## Step 1` or `## 步骤一`). Insert the following block immediately before it:

```markdown
## Step 0：读取需求确认基础

检测 `.allforai/product-concept/requirements-brief.json`：

| confirmed_status | product-map 行为 |
|-----------------|----------------|
| `fully_confirmed` | 跳过方向性问题；用 `core_paths` 生成 business-flows 骨架；`standard_modules` 直接生成 tasks（带 `source: "standard_module"` 标签） |
| `partially_confirmed` | 跳过已确认部分；对 `status: "pending"` 的项继续提问后再展开 |
| `stale`（schema 版本不匹配） | 警告用户，回退到常规流程（当作文件不存在处理） |
| 文件不存在 | 提示：建议先运行 `/requirements`；用户可选择继续（以 unconfirmed 状态运行，不跳过任何问题） |

**stale 判定**：`requirements-brief.json` 中 `schema_version` != `"1.1"` 视为 stale。

```

- [ ] **Step 3: Find the first Step heading in opencode product-map.md**

```bash
grep -n "^## Step\|^### Step 1\b\|^---" opencode/product-design-skill/skills/product-map.md | head -20
```

- [ ] **Step 4: Insert Step 0 in opencode product-map.md**

Insert the following block immediately before the first step heading:

```markdown
## Step 0: Read Requirements Brief

Check `.allforai/product-concept/requirements-brief.json`:

| confirmed_status | product-map behavior |
|-----------------|---------------------|
| `fully_confirmed` | Skip directional questions; seed business-flows from `core_paths`; auto-generate tasks from `standard_modules` (tagged `source: "standard_module"`) |
| `partially_confirmed` | Skip confirmed sections; ask about `status: "pending"` items before expanding |
| `stale` (schema version mismatch) | Warn user; fall back to standard flow (treat as absent) |
| File absent | Prompt: recommend running `/requirements` first; user may choose to continue as unconfirmed (no questions skipped) |

**Stale detection**: `schema_version` in requirements-brief.json != `"1.1"` → treat as stale.

```

- [ ] **Step 5: Verify Step 0 appears before Step 1 in both files**

```bash
grep -n "^## Step" codex/product-design-skill/skills/product-map.md | head -5
grep -n "^## Step" opencode/product-design-skill/skills/product-map.md | head -5
```
Expected: `Step 0` appears at a lower line number than `Step 1` in both files.

- [ ] **Step 6: Commit**

```bash
git add codex/product-design-skill/skills/product-map.md \
        opencode/product-design-skill/skills/product-map.md
git commit -m "feat(product-design): add Step 0 to product-map — read requirements-brief with confirmed_status branching"
```

---

## Task 5: Register in AGENTS.md and SKILL.md

**Files:**
- Modify: `codex/product-design-skill/AGENTS.md`
- Modify: `opencode/product-design-skill/SKILL.md`

- [ ] **Step 1: Add requirements row to AGENTS.md sub-skills table**

In `codex/product-design-skill/AGENTS.md`, find the Sub-Skills table (around line 7-16). The current rows are:

```
| 1 | product-concept | ./skills/product-concept.md | ... |
| 2 | product-map | ./skills/product-map.md | ... |
```

Change to:

```
| 1 | product-concept | ./skills/product-concept.md | Discover product vision from scratch (search + choice-driven) or reverse-engineer from existing code |
| 1.5 | requirements | ./skills/requirements.md | Progressive requirements confirmation: Stage A (core paths) → Stage B (standard modules) → Stage C (boundary decisions). Auto-triggered after product-concept; also runnable as /requirements |
| 2 | product-map | ./skills/product-map.md | Map roles, tasks, business flows, constraints, data model, view objects (9 steps) |
```

- [ ] **Step 2: Update pipeline phases in AGENTS.md**

Find the Full Pipeline section (around lines 22-32). Change:

```
Phase 1: product-concept (optional)
Phase 1.5: concept-baseline generation (auto)
Phase 2: product-map
```

To:

```
Phase 1: product-concept (optional)
Phase 1.5: concept-baseline generation (auto)
Phase 1.6: requirements confirmation (auto-triggered after Phase 1.5)
Phase 2: product-map
```

Also update the Resume mode completion marker table — add:

```
| 1.6 requirements | `.allforai/product-concept/requirements-brief.json` exists AND `confirmed_status` != `"pending"` |
```

- [ ] **Step 3: Add requirements skill section to SKILL.md**

In `opencode/product-design-skill/SKILL.md`, find the section for `product-concept` (around line 31) and the section for `product-map` (around line 67). Insert a new section between them:

```markdown
### 1.5. requirements — Requirements Confirmation

> See `./skills/requirements.md`

Auto-triggered after `/product-concept` generates concept-baseline.json. Walks user through 3 stages of progressive requirements confirmation, then outputs `requirements-brief.json` for product-map.

```
/requirements          # Re-run after scope change
```

**Stages:**
- Stage A: Confirm 2-4 core user paths (actor + trigger + steps + success outcome)
- Stage B: Batch sign-off standard modules (foundation defaults + inferred domain modules)
- Stage C: 3-5 multiple-choice boundary questions (only for entity/permission/state/integration/billing decisions)

**Output:** `.allforai/product-concept/requirements-brief.json` with `confirmed_status: fully_confirmed | partially_confirmed | pending`
```

Also update the pipeline description in the frontmatter (line 7):

Change:
```
Pipeline: concept → map → journey-emotion → experience-map → feature-gap → audit.
```
To:
```
Pipeline: concept → requirements → map → journey-emotion → experience-map → feature-gap → audit.
```

- [ ] **Step 4: Verify changes**

```bash
grep -n "requirements" codex/product-design-skill/AGENTS.md
grep -n "requirements" opencode/product-design-skill/SKILL.md
```
Expected: multiple hits in both files covering the new rows and sections.

- [ ] **Step 5: Commit**

```bash
git add codex/product-design-skill/AGENTS.md \
        opencode/product-design-skill/SKILL.md
git commit -m "feat(product-design): register requirements skill in AGENTS.md and SKILL.md"
```

---

## Task 6: Update execution-playbook.md (both)

**Files:**
- Modify: `codex/product-design-skill/execution-playbook.md`
- Modify: `opencode/product-design-skill/execution-playbook.md`

- [ ] **Step 1: Check current pipeline diagram in codex execution-playbook.md**

```bash
head -25 codex/product-design-skill/execution-playbook.md
```

- [ ] **Step 2: Update pipeline diagram in codex execution-playbook.md**

Find the pipeline block (lines 7-23). Change:

```
Phase 1:  product-concept (optional)
Phase 1.5: concept-baseline generation (auto)
Phase 2:  product-map
```

To:

```
Phase 1:   product-concept (optional)
Phase 1.5: concept-baseline generation (auto)
Phase 1.6: requirements confirmation (auto — Stage A→B→C, outputs requirements-brief.json)
Phase 2:   product-map (reads requirements-brief.json in Step 0)
```

Also update the description line at the top (line 3):

Change:
```
> Full pipeline orchestration: concept -> map -> journey -> experience-map -> gate -> use-case -> feature-gap -> ui-design -> design-audit
```
To:
```
> Full pipeline orchestration: concept -> requirements -> map -> journey -> experience-map -> gate -> use-case -> feature-gap -> ui-design -> design-audit
```

- [ ] **Step 3: Add Phase 1.6 detail section in codex execution-playbook.md**

After the `### Phase 1.5: concept-baseline generation` section (or after Phase 1 section if 1.5 is inline), add:

```markdown
### Phase 1.6: requirements confirmation

Skill: `./skills/requirements.md`

Auto-triggered after concept-baseline.json is written. No user action needed to start it.

Skip conditions:
- `.allforai/product-concept/requirements-brief.json` exists AND `confirmed_status` is `fully_confirmed` or `partially_confirmed` → skip (already confirmed)
- User explicitly passes `skip: requirements` → skip with warning

Stage sequence:
- Stage A: present core paths → wait for explicit confirmation
- Stage B: present standard modules → wait for explicit confirmation  
- Stage C: ask up to 5 multiple-choice boundary questions

Output: `.allforai/product-concept/requirements-brief.json`
```

- [ ] **Step 4: Mirror both changes to opencode execution-playbook.md**

```bash
head -25 opencode/product-design-skill/execution-playbook.md
```

Apply the same two changes (pipeline diagram + Phase 1.6 detail section) to `opencode/product-design-skill/execution-playbook.md`.

- [ ] **Step 5: Verify both files have Phase 1.6**

```bash
grep -n "1\.6\|requirements" codex/product-design-skill/execution-playbook.md
grep -n "1\.6\|requirements" opencode/product-design-skill/execution-playbook.md
```
Expected: hits in both files.

- [ ] **Step 6: Commit**

```bash
git add codex/product-design-skill/execution-playbook.md \
        opencode/product-design-skill/execution-playbook.md
git commit -m "feat(product-design): add Phase 1.6 requirements to execution-playbook"
```

---

## Task 7: Create validation samples

**Files:**
- Create: `codex/product-design-skill/docs/samples/requirements-brief-full.json`
- Create: `codex/product-design-skill/docs/samples/requirements-brief-partial.json`
- Create: `codex/product-design-skill/docs/samples/requirements-brief-stale.json`
- Create: `codex/product-design-skill/docs/samples/requirements-golden-path.md`

- [ ] **Step 1: Create fully_confirmed sample**

Create `codex/product-design-skill/docs/samples/requirements-brief-full.json`:

```json
{
  "schema_version": "1.1",
  "generated_at": "2026-04-11T10:00:00Z",
  "confirmed_at": "2026-04-11T10:05:00Z",
  "confirmed_status": "fully_confirmed",
  "source_command": "/product-concept",
  "based_on_concept_baseline_version": "2026-04-11T09:58:00Z",
  "core_paths": [
    {
      "id": "CP-001",
      "actor": "买家",
      "trigger": "选定商品后发起购买",
      "steps": ["搜索商品", "加购", "结账", "支付"],
      "success_outcome": "形成待履约订单，库存锁定，等待卖家发货",
      "status": "confirmed",
      "notes": null
    },
    {
      "id": "CP-002",
      "actor": "卖家",
      "trigger": "有新订单待处理",
      "steps": ["查看订单", "备货", "填写快递信息", "发货确认"],
      "success_outcome": "订单进入物流阶段，买家收到发货通知",
      "status": "confirmed",
      "notes": null
    }
  ],
  "standard_modules": [
    {
      "id": "SM-auth",
      "name": "认证",
      "tier": "foundation_default",
      "default": "邮箱密码 + Google OAuth",
      "status": "confirmed",
      "decision_source": "user_confirmed",
      "override": null
    },
    {
      "id": "SM-session",
      "name": "会话",
      "tier": "foundation_default",
      "default": "JWT，7天有效期，refresh token",
      "status": "confirmed",
      "decision_source": "user_confirmed",
      "override": null
    },
    {
      "id": "SM-rbac",
      "name": "权限",
      "tier": "foundation_default",
      "default": "RBAC，admin / user 两级",
      "status": "confirmed",
      "decision_source": "user_confirmed",
      "override": null
    },
    {
      "id": "SM-email",
      "name": "通知-邮件",
      "tier": "foundation_default",
      "default": "注册确认 / 密码重置",
      "status": "confirmed",
      "decision_source": "user_confirmed",
      "override": null
    },
    {
      "id": "SM-softdelete",
      "name": "软删除",
      "tier": "foundation_default",
      "default": "用户/订单数据逻辑删除保留",
      "status": "confirmed",
      "decision_source": "user_confirmed",
      "override": null
    },
    {
      "id": "SM-payment",
      "name": "支付",
      "tier": "domain_default",
      "default": "第三方网关，支持退款申请",
      "status": "confirmed",
      "decision_source": "user_override",
      "override": "需支持微信支付和支付宝"
    },
    {
      "id": "SM-review",
      "name": "评价",
      "tier": "domain_default",
      "default": "买家对订单评价，卖家可回复",
      "status": "confirmed",
      "decision_source": "inferred",
      "override": null
    }
  ],
  "boundary_decisions": [
    {
      "id": "BD-001",
      "question": "支付失败后订单保留多久？",
      "options": ["30分钟自动取消", "24小时（用户可重新支付）", "不自动取消，人工处理"],
      "selected_option": "30分钟自动取消",
      "decision_source": "user_selected",
      "rationale": null,
      "impact_scope": ["CP-001", "SM-payment"],
      "affects_path": "CP-001"
    },
    {
      "id": "BD-002",
      "question": "卖家是否需要通过资质审核才能开店？",
      "options": ["是，需上传营业执照", "否，注册即可开店", "可选，认证卖家有更高曝光"],
      "selected_option": "可选，认证卖家有更高曝光",
      "decision_source": "user_selected",
      "rationale": null,
      "impact_scope": ["CP-002", "SM-rbac"],
      "affects_path": "CP-002"
    }
  ],
  "unconfirmed_areas": []
}
```

- [ ] **Step 2: Validate fully_confirmed sample is valid JSON**

```bash
python3 -c "import json; json.load(open('codex/product-design-skill/docs/samples/requirements-brief-full.json')); print('valid')"
```
Expected: `valid`

- [ ] **Step 3: Create partially_confirmed sample**

Create `codex/product-design-skill/docs/samples/requirements-brief-partial.json`:

```json
{
  "schema_version": "1.1",
  "generated_at": "2026-04-11T10:00:00Z",
  "confirmed_at": null,
  "confirmed_status": "partially_confirmed",
  "source_command": "/product-concept",
  "based_on_concept_baseline_version": "2026-04-11T09:58:00Z",
  "core_paths": [
    {
      "id": "CP-001",
      "actor": "买家",
      "trigger": "选定商品后发起购买",
      "steps": ["搜索商品", "加购", "结账", "支付"],
      "success_outcome": "形成待履约订单，库存锁定，等待卖家发货",
      "status": "confirmed",
      "notes": null
    }
  ],
  "standard_modules": [
    {
      "id": "SM-auth",
      "name": "认证",
      "tier": "foundation_default",
      "default": "邮箱密码 + Google OAuth",
      "status": "confirmed",
      "decision_source": "user_confirmed",
      "override": null
    },
    {
      "id": "SM-payment",
      "name": "支付",
      "tier": "domain_default",
      "default": "第三方网关，支持退款申请",
      "status": "pending",
      "decision_source": "default",
      "override": null
    }
  ],
  "boundary_decisions": [],
  "unconfirmed_areas": ["SM-payment confirmation pending", "Stage C not yet started"]
}
```

- [ ] **Step 4: Create stale sample**

Create `codex/product-design-skill/docs/samples/requirements-brief-stale.json`:

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-01-15T08:00:00Z",
  "confirmed_at": "2026-01-15T08:10:00Z",
  "confirmed_status": "fully_confirmed",
  "source_command": "/product-concept",
  "core_paths": [
    {
      "id": "CP-001",
      "actor": "User",
      "path": ["login", "view dashboard"],
      "confirmed": true
    }
  ],
  "standard_modules": [],
  "boundary_decisions": [],
  "unconfirmed_areas": []
}
```

Note: `schema_version: "1.0"` and old field structure triggers stale detection in product-map Step 0.

- [ ] **Step 5: Validate both new JSON files**

```bash
python3 -c "
import json
for f in ['codex/product-design-skill/docs/samples/requirements-brief-partial.json',
          'codex/product-design-skill/docs/samples/requirements-brief-stale.json']:
    json.load(open(f))
    print(f, 'valid')
"
```
Expected: both print `valid`.

- [ ] **Step 6: Create golden path transcript**

Create `codex/product-design-skill/docs/samples/requirements-golden-path.md`:

```markdown
# Requirements Confirmation — Golden Path Transcript

Demonstrates the full Stage A → B → C → product-map flow for an e-commerce product.

---

## Context

User just completed `/product-concept` for a marketplace product. `concept-baseline.json` was written to `.allforai/product-concept/`.

---

## Stage A — Core Path Confirmation

**LLM output:**

```
核心路径：

1. 买家
   触发：选定商品后发起购买
   步骤：搜索商品 → 加购 → 结账 → 支付
   成功结果：形成待履约订单，库存锁定，等待卖家发货

2. 卖家
   触发：有新订单待处理
   步骤：查看订单 → 备货 → 填写快递信息 → 发货确认
   成功结果：订单进入物流阶段，买家收到发货通知

3. 管理员
   触发：收到用户投诉
   步骤：查看投诉 → 审核证据 → 处置（警告/封禁）
   成功结果：投诉关闭，处置记录留存

确认以上路径，或告知遗漏/错误：
```

**User reply:** `确认，但买家还有一个退款申请路径`

**LLM adds CP-004, then proceeds to Stage B.**

---

## Stage B — Standard Module Sign-off

**LLM output:**

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
  [站内通知] 按类型分组，支持已读/未读  [推断]

可选项（如需请告知）
  实时聊天 / 文件存储 / 全文搜索 / i18n / PWA 离线

回复"确认"继续，或说明要修改的项：
```

**User reply:** `支付改成支持微信支付和支付宝，其余确认`

**LLM writes SM-payment with `decision_source: "user_override"`, all others `user_confirmed`. Proceeds to Stage C.**

---

## Stage C — Boundary Decisions

**LLM question 1:**

```
路径"买家退款申请"有一个需要确认的点：

买家申请退款后，退款处理方式是？
  a) 卖家处理（卖家同意/拒绝）
  b) 平台客服处理（买家卖家都可申诉）
  c) 自动退款（无需审批，直接退回）
```

**User reply:** `b`

**LLM question 2:**

```
关于权限模型需要确认：

管理员是否分级（超级管理员 vs 普通运营）？
  a) 是，超级管理员可封号，普通运营只能处理投诉
  b) 否，所有管理员权限相同
  c) 暂不分级，后续扩展
```

**User reply:** `a`

**No more questions (remaining ambiguities have reasonable defaults). Stage C complete.**

---

## Output

`requirements-brief.json` written with `confirmed_status: "fully_confirmed"`.

---

## product-map Step 0

**LLM detects requirements-brief.json, reads `confirmed_status: "fully_confirmed"`:**

```
需求已确认（fully_confirmed）。

将基于以下内容展开产品地图：
- 4 条核心路径（买家购买/退款、卖家发货、管理员处理投诉）
- 7 个已确认标准模块（认证/会话/权限/通知/软删除/支付/评价）
- 2 个边界决策（退款平台介入、管理员分级）

直接进入 Step 1...
```

Product-map proceeds without asking directional questions, seeding business-flows from core_paths and auto-generating standard module tasks.
```

- [ ] **Step 7: Commit all samples**

```bash
git add codex/product-design-skill/docs/samples/requirements-brief-full.json \
        codex/product-design-skill/docs/samples/requirements-brief-partial.json \
        codex/product-design-skill/docs/samples/requirements-brief-stale.json \
        codex/product-design-skill/docs/samples/requirements-golden-path.md
git commit -m "feat(product-design): add requirements validation samples and golden path transcript"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|-----------------|------|
| Stage A: core paths with trigger + success_outcome | Task 1/2 (requirements.md) |
| Stage B: 3-tier catalog with inclusion_rule | Task 1/2 (requirements.md) |
| Stage B: explicit confirmation rule (no silence=confirmed) | Task 1/2 (requirements.md) |
| Stage C: question selection rule (5 categories) | Task 1/2 (requirements.md) |
| Stage C: max 5 questions, multiple choice | Task 1/2 (requirements.md) |
| requirements-brief.json v1.1 schema | Task 1/2 (requirements.md) |
| confirmed_status: fully/partially/pending | Task 1/2 (requirements.md) |
| Auto-trigger from product-concept | Task 3 |
| product-map Step 0 with 4-way branch | Task 4 |
| stale detection (schema_version != "1.1") | Task 4 |
| AGENTS.md sub-skills table + pipeline | Task 5 |
| SKILL.md section + pipeline description | Task 5 |
| execution-playbook.md Phase 1.6 | Task 6 |
| fully_confirmed sample JSON | Task 7 |
| partially_confirmed sample JSON | Task 7 |
| stale sample JSON | Task 7 |
| Golden path transcript | Task 7 |

All spec requirements covered. No placeholders found.
