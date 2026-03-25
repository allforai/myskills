---
name: demo-design
description: >
  Use when the user asks to "design demo data", "plan demo environment",
  "demo-design", "demo plan", or mentions demo data planning, demo environment design.
  Requires product-map to have been run first.
version: "1.0.0"
---

# Demo Design — Demo Data Scheme Design

> From the product map, plan all data needed to make the product look like it has real users.

## Goal

Using `product-map` as the blueprint, design demo data with business logic, character relationships, and time distribution:

1. **Who uses it** — create realistic user accounts per role
2. **What they did** — generate business data by task frequency (high-freq tasks get more data)
3. **How it connects** — generate complete data chains per scenario, not isolated random records
4. **Follows rules** — set data states per business constraints (irreversible operations, approval chains, amount limits)
5. **Has time depth** — data distributed over months, recent-dense-far-sparse, following work-hour rhythms
6. **Has behavior patterns** — user activity follows power-law distribution, operator attribution is coherent
7. **Looks real** — images are all real-sourced, zero placeholders; text is diverse, not copy-pasted

---

## Position

```
demo-forge internal stages:
  demo-design (this skill)  ->  media-forge + demo-execute  ->  demo-verify
  Plan what data to generate     Acquire media + populate data     Open product and verify item by item
  Pure design, no execution      Consumes design scheme            Produces issue list routed back for fixes
```

**Prerequisite**: product-map must have been run first, generating `.allforai/product-map/product-map.json` and `business-flows.json`.

---

## Enhancement Protocol (web search + OpenRouter)

**Web search keywords**:
- `"{ORM} seed data strategies {year}"`
- `"realistic test data generation {language}"`

**OpenRouter text diversity enhancement** (when available):
- **Chinese market** -> Qwen: generate 15-20 natural Chinese variants per field type
- **International market** -> Gemini: generate diverse English/multilingual variants
- Merge generated variants into `style-profile.json` `text_templates`
- OpenRouter unavailable -> use Claude-generated templates (sufficient quality, slightly less diversity)

---

## Data Design Principles

| Principle | Step | Rule |
|-----------|------|------|
| Cover boundary values | Step 1 | Each field must include boundary data: null, extremes, special chars. Boundaries must respect constraints.json |
| Equivalence partitioning | Step 1 | Partition by role/status (VIP/free/banned), at least 1 representative record per class |
| No duplicate data | Step 2 | Multiple records of the same entity must differ in attributes. No copy-paste-change-ID |
| JSON is the contract format | Step 1 | demo-plan.json output = demo-execute input, structure must be consistent |

---

## Workflow

```
Pre: Load .allforai/product-map/product-map.json + business-flows.json
     Missing -> prompt user to run product-map first, abort
     |
Pre: Upstream staleness detection
     Compare upstream file modification times against last output generation time
     Stale -> warn but do not block
     |
Step 0: Data model mapping
     Code entities <-> product-map tasks/roles correspondence
     -> Output: model-mapping.json, api-gaps.json
     |
Step 1: Demo data scheme design (core)
     1-A Role -> user account design
     1-B Task frequency -> data volume design
     1-C Scenario + business flow -> data chain design
     1-C-2 Population method annotation (api vs db per entity)
     1-D Constraints -> data rule design
     1-E Enum full coverage check
     1-F Time distribution design
     1-G User behavior pattern design
     1-H Data history depth design
     1-M Media field annotation (for media-forge)
     -> Output: demo-plan.json
     |
Step 2: Industry style and text template design
     Name style, regional format, text templates
     -> Output: style-profile.json
     |
Step 2.5: Text diversity enhancement (if OpenRouter available)
     Select model by target market language
     Generate 15-20 natural variants per field type
     Merge into style-profile.json text_templates
```

---

### Step 0: Data Model Mapping

Extract data models (Entity, Model, Schema) from code, map to product-map tasks and roles:

```
product-map task "{task_name}"  ->  code entity {Entity}
product-map role "{role_name}"  ->  code entity User (role={role_key})
product-map scenario "{scenario}" -> entity relations {A} -> {B} -> {C}
```

Detect API gaps: entity without create endpoint, task without API. Mark as `API_GAP`.

Output: `.allforai/demo-forge/model-mapping.json`, `.allforai/demo-forge/api-gaps.json`

---

### Step 1: Demo Data Scheme Design

This is the core step. product-map directly provides all decision inputs.

#### 1-A User Account Design (by role)

Create test accounts for each role in `role-profiles.json`:
- High-frequency roles -> N accounts (split by sub-roles)
- Mid-frequency roles -> fewer accounts
- Admin roles -> 1 account

Each account has realistic info: name, avatar, join date, department.

**Login credentials**: All test accounts use a unified password (e.g., `DemoForge2024!`). If the product has SSO/OAuth only, check for password fallback; otherwise mark `AUTH_GAP`.

#### 1-B Data Volume Design (by frequency)

**Data loading**: If `task-index.json` exists, read frequency from the index (no need to load full task-inventory.json). Otherwise fall back to task-inventory.json.

Allocate by Pareto ratio:

| Task Frequency | Volume Strategy | Example |
|---------------|-----------------|---------|
| High | Large, 70%+ of total | 80 core business records |
| Medium | Moderate, 20% of total | 15 secondary records |
| Low | Minimal, ensure existence | 2 config/policy records |

#### 1-C Data Chain Design (by scenario + business flow)

Generate complete chains, not isolated data. Read `business-flows.json` for cross-role/cross-system flows first, then supplement with standalone tasks from `task-inventory.json`.

#### 1-C-2 Population Method Annotation (per entity)

| Method | When to Use |
|--------|-------------|
| `api` | Entities needing business logic triggers (create records, notifications, status transitions, audit logs) |
| `db` | No business logic side effects (config tables, dictionaries, historical archives, API_GAP entities) |

Prefer `api`; use `db` when: entity is in `api-gaps.json`, need terminal-state data bypassing normal flow, or large batch without bulk API.

#### 1-D Constraint Rules Design

Read from three sources: `constraints.json` (global), `task.rules` (task-level), `task.exceptions` (exception scenarios). Convert each constraint into data generation rules.

#### 1-E Enum Full Coverage Check (mandatory)

Traverse all task `main_flow` and `outputs.states`, extract all status enum values. Every value must have at least one corresponding record. Focus on terminal and exception states (REJECTED / CANCELED / EXPIRED / FAILED / CLOSED).

#### 1-F Time Distribution Design

Default lookback: 90 days, covering 3+ calendar months.

| Rule | Description |
|------|-------------|
| Recent-dense | Last 7 days = 30% of total, last 30 days = 60% |
| Work hours | 80% between 9:00-18:00, only 5% between 22:00-7:00 |
| Weekday priority | Weekday density 3-5x weekend |
| Old=terminal, new=active | 30d+ records 90%+ terminal state, 7d records 50%+ active state |

#### 1-G User Behavior Pattern Design

| Tier | Share | Behavior |
|------|-------|----------|
| Heavy users | 10% of accounts | Produce 50% of data, multi-scenario |
| Normal users | 30% of accounts | Produce 35% of data, 1-2 scenarios |
| Light users | 60% of accounts | Produce 15% of data, single scenario or account-only |

#### 1-H Data History Depth Design

| Data Type | History Depth | Notes |
|-----------|--------------|-------|
| User accounts | 180 days spread | Show continuous growth |
| Core business | 90 days | Monthly fluctuation +-15% |
| Config/dict | System launch date | Earliest records |
| Logs/journal | Follow parent entity | Timestamps consistent |

#### 1-M Media Field Annotation

For each entity field needing media content, generate an acquisition manifest for media-forge:

```json
{
  "entity": "Product",
  "field": "cover_image",
  "media_type": "image",
  "purpose": "Product cover",
  "dimensions": "800x800",
  "aspect_ratio": "1:1",
  "count": 80,
  "search_keywords": ["home goods", "kitchen appliances"],
  "style_notes": "White background product photo, e-commerce style",
  "upload_endpoint": "POST /api/upload/image",
  "ref_field": "cover_image_id"
}
```

---

### Step 2: Industry Style and Text Templates

Based on industry keywords (from product-map or inferred), set:

- Name styles (matching target market culture)
- Amount ranges and currency format
- Regional formats (phone, address, email domain)
- Text content templates per field type (20+ unique variants per category)

**Diversity requirement**: At least 10 variants per field type. Adjacent records must not have identical text.

Output: `.allforai/demo-forge/style-profile.json`

---

### Step 2.5: Text Diversity Enhancement (when OpenRouter available)

- Chinese market -> Qwen model
- International market -> Gemini model
- Input: Step 2 industry keywords + field type list
- Output: 15-20 natural variants per field type
- Merge into style-profile.json `text_templates`
- OpenRouter unavailable -> skip, use Claude-generated templates

---

## Re-entry Mode

When `verify-issues.json` contains `route_to="design"` issues, enter re-entry mode. Core principle: incremental modification of `demo-plan.json`, not full redo.

| Issue Type | Modification |
|-----------|-------------|
| Insufficient entity records | Increase volume in 1-B |
| Uncovered enum values | Add missing enum records in 1-E |
| Incomplete data chain | Add missing child/related entities in 1-C |
| Role with empty main view | Check 1-A accounts and 1-G behavior allocation |
| Dashboard dimension is zero | Add records for that dimension |
| Missing media field annotation | Add to 1-M |

---

## Output Files

| File | Step | Description |
|------|------|-------------|
| `model-mapping.json` | Step 0 | Code entity <-> product-map task/role mapping |
| `api-gaps.json` | Step 0 | API gap report |
| `demo-plan.json` | Step 1 | Full demo data scheme |
| `style-profile.json` | Step 2 + 2.5 | Industry style + text templates + diversity variants |

---

## Iron Rules

### 1. Frequency determines volume, scenario determines associations

High-frequency tasks get more data, low-frequency tasks get less. Associations follow scenario chain design, not random assembly.

### 2. Constraints are hard rules

Business constraints from `constraints.json` must be reflected in data. Amount limits, approval chains, irreversible states — designed data must not violate them.

### 3. Prefer API, use DB when needed

Entities needing business logic (creation, state transitions, notifications) go through API. Config tables, dictionaries, archives, and API_GAP entities go through DB direct write. Each entity is annotated in Step 1-C-2.

---

## Common Omission Patterns

| Omission | Symptom | Prevention |
|----------|---------|------------|
| Missing terminal states | All records "in progress" | 1-E enum coverage check |
| Missing exception states | No failed/rejected/banned data | Allocate records for "bad paths" |
| Empty log tables | No audit logs, messages, journal | Step 0 explicitly list log entities |
| Orphan accounts | Accounts with zero business data | Every demo account must have chain data |
| Missing junction tables | Many-to-many tables empty | Step 0 scan association tables |
| Empty config tables | System params/templates missing | List config entities separately, fill all |
| Time logic errors | Child before parent, future dates in history | Use relative offsets (NOW-7d) |
| Derived field mismatch | Aggregates != detail sum | DB population -> manual recalculation |
| Flat time distribution | All records on same day | 1-F time distribution, 90-day lookback |
| Uniform user behavior | Equal data per user | 1-G power-law: 10% heavy users produce 50% data |
