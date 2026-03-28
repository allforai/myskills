---
name: demo-design
description: >
  Use when the user asks to "design demo data", "plan demo environment",
  "demo-design", "demo plan", or mentions demo data planning,
  demo environment design. Requires product-map to have been run first.
version: "1.0.0"
---

# Demo Design — Data Plan Design

> From the product map, plan all data needed to make the product look like real users are actively using it.

## Goal

Using `product-map` as the blueprint, design demo data with business logic, user relationships, and time distribution:

1. **Who uses it** — create realistic user accounts per role
2. **What they did** — generate business data by task frequency (high-frequency tasks get more, low-frequency less)
3. **How it connects** — generate complete data chains by scenario, not isolated random records
4. **Follows rules** — respect business constraints (irreversible operations, approval chains, amount limits)
5. **Has time depth** — data distributed across months, recent-dense-remote-sparse, follows work hours
6. **Has behavior feel** — user activity follows power-law distribution, operator attribution is consistent, journeys have sequence
7. **Looks real** — images are real acquisitions, zero placeholders; text is diverse, not copy-paste

---

## Positioning

```
demo-forge internal stages:
  demo-design (this skill)  →  media-forge + demo-execute  →  demo-verify
  Plan what data to generate     Acquire assets + populate       Open product, verify each item
  Pure design, no execution      Consume the design plan         Produce issue list, route back
```

**Prerequisite**: product-map must have been run first, producing `.allforai/product-map/product-map.json` and `business-flows.json`.

---

## Enhancement Protocol (网络搜索 + OpenRouter)

**网络搜索 keywords**:
- `"{ORM} seed data strategies {year}"`
- `"realistic test data generation {language}"`
- `"faker.js alternatives {year}"`

**OpenRouter text diversity enhancement**:
- **`text_diversity_zh`** (Qwen) — for Chinese target market, after Step 2 text templates:
  - Input: industry keywords + field type list (names/descriptions/reviews/notifications)
  - Generate: 15-20 natural Chinese variants per field type
  - Purpose: Claude's Chinese tends to be formal; Qwen produces more natural Chinese
- **`text_diversity_intl`** (Gemini) — for international/English target market:
  - Input: same as above
  - Generate: diverse English/multilingual variants
- Generated text variants merge into `style-profile.json` `text_templates` field
- OpenRouter unavailable → use Claude's own templates (quality sufficient, diversity slightly less)

---

## Demo Data Generation Principles

| Principle | Step | Rule |
|-----------|------|------|
| Cover boundary values | Step 1 | Each field must include boundary data: null, extremes, special characters. Numbers include 0, negatives, max. Boundaries must respect constraints.json |
| Equivalence partitioning | Step 1 | Partition by role/status (VIP user / free user / banned user), at least 1 representative record per class |
| No duplicate data | Step 2 | Multiple records of same entity must differ in attributes, no copy-paste with only ID changes |
| JSON is the contract format | Step 1 | demo-plan.json output = demo-execute input, structure must match |

---

## Workflow

```
Prerequisites: Load .allforai/product-map/product-map.json + business-flows.json
    If files missing → tell user to run product-map first, terminate
    ↓
Prerequisites: Upstream staleness detection
    Compare upstream file modification times vs this skill's last output:
    - task-inventory.json updated after demo-plan.json
      → warn "task-inventory.json updated after demo-plan.json, data may be stale"
    - product-map.json updated after demo-plan.json
      → warn "product-map.json updated after demo-plan.json, data may be stale"
    - Warning only, do not block. User chooses to continue or refresh upstream.
    ↓
Execution mode: Steps 0-2 generate-and-continue, plan summary at end (no stop)
    ↓
Step 0: Data model mapping
    Code entities ↔ product-map tasks/roles correspondence
    → Progress: "Step 0 Model mapping done: {N} entities, {M} API gaps" (continue)
    ↓
Step 1: Demo data plan design (core)
    1-A Role → user account design
    1-B Task frequency → data volume design
    1-C Scenario + business flow → data chain design
    1-D Constraints → data rule design
    1-E Enum full coverage check
    1-F Time distribution design
    1-G User behavior pattern design
    1-H Data history depth design
    1-M Media field annotation (acquisition list for media-forge)

    Innovation data chains (if innovation_mode=active):
    - For each protection_level=core innovation concept, design dedicated data chains
    → Progress: "Step 1 Plan done: {N} accounts, {M} entities, {K} chains, {J} media fields" (continue)
    ↓
Step 2: Industry style + text template setup
    Name styles, regional formats, text templates
    → Progress: "Step 2 Style done: {industry} style, {N} text templates" (continue)
    ↓
Step 2.5: Text diversity enhancement (when OpenRouter available)
    Select model by target market language:
      Chinese → Qwen (text_diversity_zh)
      International → Gemini (text_diversity_intl)
    Input: Step 2 industry keywords + field type list
    Output: 15-20 natural variants per field type
    Merge into style-profile.json text_templates
    → Progress: "Step 2.5 Text enhancement done: {N} field types, {M} variants"
    OpenRouter unavailable → skip, use Claude templates
    ↓
Plan summary:
    ## Demo Plan Summary

    | Item | Details |
    |------|---------|
    | Entity mapping | {N} entities mapped, {M} API gaps |
    | User accounts | {N} ({breakdown by role}) |
    | Data volume | High {N}, Medium {M}, Low {K} records |
    | Scenario chains | {N} complete chains |
    | Enum coverage | {N}/{M} state values covered |
    | Time span | {N} days |
    | Media fields | {N} fields, {M} assets to acquire |
    | Industry style | {industry} |
    | Text templates | {N} types, {M} variants |

    → Auto-confirm demo plan, design phase complete
```

---

### Step 0: Data Model Mapping

Extract data models (Entity, Model, Schema) from code, map to `product-map` tasks and roles:

```
product-map task "{task_name}"  →  code entity {Entity}
product-map role "{role_name}"  →  code entity User(role={role_key})
product-map scenario "{scenario}"  →  entity chain {EntityA} → {EntityB} → {EntityC}
```

Detect API gaps: entity without create endpoint, task without corresponding API, mark as `API_MISSING_BLOCKER` — missing API must be created before population.

Output: `.allforai/demo-forge/model-mapping.json`, `.allforai/demo-forge/api-gaps.json`

---

### Step 1: Demo Data Plan Design

The core step. product-map provides all decision basis.

#### 1-A User Account Design (by role)

Create test accounts per role from `role-profiles.json`:

```
{high-frequency role} (R001)  →  N accounts (split by sub-role)
{medium-frequency role} (R002)  →  fewer accounts
{admin role} (R003)  →  1 account
```

Each account has realistic info: name, avatar, join date, department.

**Login credentials**:
- All test accounts use unified password (e.g., `DemoForge2024!`) for quick role switching during demos
- Password written to `demo-plan.json` `credentials` field
- If product has SSO/OAuth, confirm password login fallback support, otherwise mark `AUTH_GAP`

#### 1-B Data Volume Design (by frequency)

**Data loading**: if `task-index.json` exists, read frequency from index directly (no need for full task-inventory.json). Otherwise fall back to reading `task-inventory.json`.

Pareto distribution:

| Frequency | Strategy | Example |
|-----------|----------|---------|
| High | Large volume, 70%+ of total | Core business records 80 |
| Medium | Moderate, ~20% of total | Secondary business 15 |
| Low | Minimal, ensure existence only | Config/policy 2 |

#### 1-C Data Chain Design (by scenario + business flow)

No isolated data. Generate complete chains by scenario. Read `business-flows.json` for cross-role/cross-system flows first, then supplement with independent tasks from `task-inventory.json`.

```
Scenario "{name}" (cross_dept: {deptA}+{deptB}):
  {User entity} x N
    └── {Main business entity} x M (completed status)
          └── {Sub business entity} x K (submitted)
                └── {Approval/routing entity} x J (processed)
                      └── {Notification/log entity} x J (sent)
```

Each scenario's data has continuous timestamps, logical state flow, complete foreign keys.

#### 1-C-2 Population Method Annotation (per entity)

All entities use API population — no exceptions. Annotate the API endpoint for each entity alongside chain design:

| Annotation | Description |
|------------|-------------|
| `api` | Entity has create/update API endpoint — annotate endpoint path |
| `API_MISSING_BLOCKER` | Entity has no create API — must be built before population (generate dev-forge task) |

**No DB fallback**: entities marked `API_MISSING_BLOCKER` block population until the API is created. This ensures every data injection validates the full business logic stack (authentication, permissions, validation, derived fields).

#### 1-D Constraint Rule Design (by business constraints + task rules)

Read three data sources, convert constraints to data generation rules:

1. **`constraints.json`** — global business constraints (amount limits, irreversible states, cross-entity rules)
2. **`task.rules`** — task-level business rules (idempotency windows, threshold triggers, validation logic) → generate data that touches rule boundaries
3. **`task.exceptions`** — task-level exception scenarios (timeout, conflict, permission denied) → generate boundary data that triggers exceptions

#### 1-E Enum Full Coverage Check (mandatory)

Traverse all tasks' `main_flow` and `outputs.states` from `task-inventory.json`, extract all state enum values, confirm each has corresponding records:

```
✗ Wrong: All records status = COMPLETED
✓ Correct: Each defined state value has at least 1 record
```

**Focus on terminal and exception states** (most easily missed):
- `REJECTED / CANCELED / EXPIRED / FAILED / CLOSED` — allocate records specifically
- High-risk task `exceptions` states must exist in data

#### 1-F Time Distribution Design

Demo data timestamps must show realistic usage traces, not all on same day.

**Time span**: default 90 days lookback, covering at least 3 calendar months.

**Distribution rules**:

| Rule | Description |
|------|-------------|
| Recent-dense | Last 7 days = 30% of total, last 30 days = 60%, rest spread earlier |
| Work hours | 80% of operations between 9:00-18:00, only 5% between 22:00-7:00 |
| Weekday bias | Weekday density 3-5x weekend (more extreme for B2B) |
| Old terminal, new active | 30+ day records 90%+ terminal state, 7-day records 50%+ active state |

#### 1-G User Behavior Pattern Design

Real system user activity follows power-law distribution.

| Tier | Share | Behavior |
|------|-------|----------|
| Heavy users | 10% of accounts | Produce 50% of business data, across multiple scenarios |
| Regular users | 30% of accounts | Produce 35% of data, 1-2 scenarios |
| Light users | 60% of accounts | Produce 15% of data, 1 scenario or account-only |

#### 1-H Data History Depth Design

Provide meaningful historical data for reports, dashboards, trend charts.

| Data type | History depth | Notes |
|-----------|--------------|-------|
| User accounts | Spread across 180 days | Show continuous growth, not batch registration |
| Core business entities | 90 days | Monthly fluctuation, not constant |
| Config/dictionary | System launch date | `created_at` earlier than all business data |
| Logs/transactions | Follow parent entity | Time consistent with parent |

**Monthly fluctuation**: each month's volume varies +-15% randomly.

#### 1-M Media Field Annotation

Traverse all entity field definitions, generate acquisition list for each media field:

```json
{
  "entity": "Product",
  "field": "cover_image",
  "media_type": "image",
  "purpose": "product cover",
  "dimensions": "800x800",
  "aspect_ratio": "1:1",
  "count": 80,
  "search_keywords": ["home goods", "kitchen appliances"],
  "style_notes": "white background product photo, e-commerce style",
  "upload_endpoint": "POST /api/upload/image",
  "ref_field": "cover_image_id"
}
```

**Media type acquisition strategy**:

| media_type | Typical scenario | Strategy |
|-----------|-----------------|----------|
| image | Avatars, covers, detail images, banners | Brave Search → 网络搜索 fallback → AI gen (Imagen 4 / GPT-5 Image / FLUX 2 Pro) |
| video | Product videos, tutorials, promos | Brave Video Search → 网络搜索 → AI gen (Veo 3.1 / Kling) / Playwright recording |
| document | PDF attachments, contract scans | Template fill generation |
| audio | Voice messages, audio courses | Google Cloud TTS |

Output: `.allforai/demo-forge/demo-plan.json`

---

### Step 2: Industry Style and Text Template Setup

Based on industry keywords (from user or inferred from product-map), research industry data style via 网络搜索:

**Base style**: name conventions, amount ranges, currency format, category naming.

**Regional format** (determined by product target market):
- Phone number format (matching target market rules)
- Address format (matching target market structure)
- Email domains (use common personal/enterprise domains, not test@test.com)

**Text content templates** (by entity field type):

| Field type | Template strategy | Requirement |
|-----------|-------------------|-------------|
| Names/titles | Industry vocab + attribute combos, 20+ unique templates | Match target market naming conventions |
| Descriptions/notes | 3-5 sentence realistic descriptions, varying length | Mix reasons/scenarios, avoid identical text |
| Approval/decision comments | Positive/neutral/rejection, 3-5 each | Cover approve, reject, request-more-info |
| User feedback/reviews | Positive/neutral/negative at 7:2:1 ratio | Not all max rating, realistic distribution |
| System notifications | Template-fill with variables | Use product's actual notification format |

Output: `.allforai/demo-forge/style-profile.json`

---

## Reentry Mode

When `verify-issues.json` contains `route_to="design"` issues, the orchestrator calls back this skill in reentry mode.

**Core principle**: incrementally modify `demo-plan.json`, do not redo from scratch.

**Common reentry scenarios**:

| Issue type | Modification |
|-----------|-------------|
| Entity record count insufficient | Increase data volume allocation in 1-B |
| Enum value uncovered, filter returns empty | Add missing enum value records in 1-E |
| Data chain incomplete, detail page relations empty | Add missing sub-entity/related entity in 1-C |
| Role's main view has no data | Check 1-A account design and 1-G behavior allocation |
| Dashboard dimension is zero | Add data records for that dimension |
| Media field not annotated | Add missing media field in 1-M |

---

## Output Files

| File | Step | Description |
|------|------|-------------|
| `.allforai/demo-forge/model-mapping.json` | Step 0 | Code entity ↔ product-map task/role mapping |
| `.allforai/demo-forge/api-gaps.json` | Step 0 | API gap report (API_MISSING_BLOCKER — must be resolved before population) |
| `.allforai/demo-forge/demo-plan.json` | Step 1 | Demo data plan (accounts/volume/chains/constraints/enums/time/behavior/media) |
| `.allforai/demo-forge/style-profile.json` | Step 2 + 2.5 | Industry style + text templates + diversity variants |

---

## Iron Rules

### 1. Frequency determines quantity, scenario determines relationships

High-frequency task data should be abundant, low-frequency sparse. Relationships follow scenario chain design, not random assembly.

### 2. Constraints are hard rules

Business constraints from `constraints.json` must be reflected in data. Amount limits, approval chains, irreversible states -- the data plan must not violate them.

### 3. 全部走 API，无例外

所有数据灌入通过 API 端点，不直写数据库。灌入过程即集成测试 — 每次 API 调用验证认证、权限、校验、业务逻辑。缺失 API 的实体标记为 `API_MISSING_BLOCKER`，生成 dev-forge 修复任务，不降级为数据库直写。

---

## Common Omission Patterns

| Omission | Symptom | Prevention |
|----------|---------|------------|
| Terminal states missing | All records "in progress" | 1-E enum check, verify each state |
| Exception states missing | No failed, rejected, banned data | Allocate "bad path" records |
| Log tables empty | Operation logs, messages, transactions empty | Step 0 mapping lists log entities |
| Orphan accounts | Accounts with no business data | Demo accounts must have chain data |
| Junction tables missing | Many-to-many tables empty | Step 0 scans junction tables |
| Config tables empty | System params, templates empty | Config entities listed and fully populated |
| Time logic errors | Child earlier than parent, future dates in history | Use relative time offsets (NOW-7d) |
| Derived field mismatch | Aggregates != detail sums | BIZ_BUG — API should handle derived fields; route to dev_task |
| Unnatural time distribution | All records on same day | 1-F time distribution, 90 day lookback |
| Uniform user behavior | Every user produces equal data | 1-G power-law, 10% heavy users produce 50% data |
