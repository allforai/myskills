---
name: demo-execute
description: >
  Use when the user asks to "populate demo data", "fill demo environment",
  "demo-execute", "demo populate", or mentions data population,
  demo data generation, database seeding for demos.
  Requires demo-plan.json + style-profile.json + upload-mapping.json.
  Requires a running application for data population.
version: "1.0.0"
---

# Demo Execute — Data Generation and Population

> Turn the design plan into real data inside the application.

## Positioning

```
demo-forge internal stages:
  demo-design            →  media-forge + demo-execute (this skill)  →  demo-verify
  Plan what data to generate   Acquire assets + populate data              Verify each item
  Pure design, no execution    Consume the design plan                     Route issues back
```

**This skill's responsibility**: consume demo-plan + style-profile + upload-mapping, generate concrete data records and populate the running application.

---

## Prerequisites

| Condition | Source | Description |
|-----------|--------|-------------|
| `demo-plan.json` | demo-design | Demo data plan (entities, chains, constraints, enums, time distribution) |
| `style-profile.json` | demo-design | Industry style + text templates |
| `upload-mapping.json` | media-forge | Local asset → server URL/ID mapping |
| Application running | User | API accessible |

All four required. Missing any → terminate and tell user to complete the prerequisite.

---

## Workflow

### E1: Data Generation (deterministic)

Read `demo-plan.json` + `style-profile.json` + `upload-mapping.json`, generate records per scenario chain.

**Field generation strategy**:

| Field type | Generation method |
|-----------|-------------------|
| Text fields | Random select from style-profile templates, no adjacent repeats |
| Numeric fields | Values within constraint range + include boundary values |
| Time fields | Weighted sampling (recent-dense distribution + work hours + monthly +-15% fluctuation) |
| Status fields | Allocate by enum coverage requirement, ensure each value has records (including terminal/exception states) |
| Media fields | Read server_url / server_id directly from upload-mapping.json |
| Foreign key fields | Auto-link by chain dependency (parent → child generation order, child references parent's temp ID) |
| Derived fields | Omit — API handles derived fields automatically via business logic |

**Behavior distribution**:

```
10% heavy users → produce ~50% of data
30% regular users → produce ~35% of data
60% light users → produce ~15% of data
```

**Output**: `forge-data-draft.json` (all records use temporary IDs like TEMP-001, TEMP-002).

---

### E2: Pre-flight Self-Check

Verify data quality item-by-item. Issues fall into two categories:

```
□ Entity completeness — no zero-record entities (every entity has at least one record)
□ Enum coverage   — every status field has all values represented (including REJECTED/CANCELED/EXPIRED/FAILED)
□ Foreign key integrity — every foreign key ID has a corresponding record in the dataset
□ Derived fields omitted — API handles derived fields; verify they are NOT in draft data
□ Time logic   — created_at < updated_at, parent entity time earlier than child
□ Media linkage   — all media fields reference upload-mapping entries (no external URLs)
□ Behavior distribution   — heavy users produce approximately 50% of data
□ Text dedup   — no adjacent records with identical text
```

**Handling**:
- Structural issues (missing FK target, zero-record entity): **auto-fix**
- Other issues: mark as `PREFLIGHT_ISSUE`, report to user

`--dry-run` mode stops after E2, does not enter E3.

---

### E3: Data Population

**All data injection goes through API endpoints — no exceptions.** The injection process itself IS integration testing: every API call verifies authentication, permissions, validation, and business logic. Injection failure = BIZ_BUG.

**Population order follows scenario chains** (not alphabetical by entity), ensuring foreign key correctness:

```
1. Config/dictionary entities: API in dependency order (base data first)
2. User accounts: API creation (all scenario chains depend on users)
3. Business entities: by scenario priority (high → medium → low frequency)
   - Within each scenario, follow chain order: parent → child → related entity
   - ALL entities go through API, no exceptions
```

**API_MISSING_BLOCKER handling**:
- Entity marked `API_MISSING_BLOCKER` in `api-gaps.json` → **stop and create the missing API first**
- Missing API is a development task: generate B-FIX task for dev-forge, do not proceed with that entity until API exists
- Never fall back to DB direct write — that hides integration bugs

**Injection = Integration Testing**:
- 灌入过程即集成测试 — 每次 API 调用验证认证、权限、校验、业务逻辑
- 灌入失败 = BIZ_BUG — API 返回非预期结果说明业务逻辑有缺陷，必须修复
- API handles derived fields automatically (aggregates, counts, balances all triggered by business logic)
- No manual derived field correction needed — if aggregates are wrong after API population, that is a BIZ_BUG

**Failure handling**:
- **Independent entity failure**: log as `BIZ_BUG`, continue populating others
- **Parent entity failure**: skip all children in that chain (avoid dangling foreign keys), mark entire chain `CHAIN_FAILED`
- **End of population**: summarize failed chain count and reasons, prompt user to investigate

**Output**:
- `forge-data.json` — created data inventory (temp IDs replaced with real server IDs)
- `forge-log.json` — population log (operation status per record)

---

## forge-data-draft.json vs forge-data.json

| File | Stage | ID type | Purpose |
|------|-------|---------|---------|
| `forge-data-draft.json` | After E1 | Temporary (TEMP-001) | Data blueprint, reusable after clean |
| `forge-data.json` | After E3 | Real server IDs | Basis for clean and verify |

Draft is preserved — after clean, can re-populate without regenerating data.

---

## Clean Mode

Clean mode reads `forge-data.json` and deletes all populated data in reverse order.

**Cleanup order** (reverse of population, to respect foreign key constraints):

```
1. Child entities → parent entities (reverse of forge-data.json population order)
2. User accounts (last — other entities may reference user_id)
3. Base data (config tables, dictionaries)
```

**Cleanup method**:
- Use DELETE API endpoints where available
- For entities without DELETE API: database DELETE by `id` and `table` recorded in `forge-data.json` (cleanup-only exception, not data injection)
- If cascade delete configured, only delete top-level parents; otherwise delete layer by layer

**Cleanup scope**:
- Clear `forge-data.json`, `forge-log.json`
- **Keep** `demo-plan.json`, `style-profile.json`, `assets/`, `upload-mapping.json` (design + assets preserved for reuse)
- **Keep** `forge-data-draft.json` (can re-populate directly)

---

## Reentry Mode

When `verify-issues.json` contains `route_to="execute"` issues, enter reentry mode — fix only problems, do not re-populate everything:

| Issue type | Handling |
|-----------|----------|
| Foreign key broken | Check forge-data.json, supplement missing parent records or fix FK references |
| CHAIN_FAILED | Retry full chain population |
| Derived inconsistency | BIZ_BUG — API should handle derived fields; route to dev_task for fix |

---

## Output Files

| File | Path | Description |
|------|------|-------------|
| `forge-data-draft.json` | `.allforai/demo-forge/` | E1 generated dataset (temporary IDs) |
| `forge-data.json` | `.allforai/demo-forge/` | E3 populated data inventory (real IDs) |
| `forge-log.json` | `.allforai/demo-forge/` | Population log (operation status per record) |

---

## Iron Rules

1. **全部走 API，无例外** — 所有数据灌入通过 API 端点，不直写数据库。灌入过程即集成测试 — 每次 API 调用验证认证、权限、校验、业务逻辑。灌入失败 = BIZ_BUG
2. **API_MISSING_BLOCKER — 缺失 API 必须先补建** — 实体无对应 API 时标记为 `API_MISSING_BLOCKER`，生成 dev-forge 修复任务，不降级为数据库直写
3. **Chain-order population, parent before child** — any child entity population requires its parent to already exist
4. **Failures are never silent, chain failures explicitly marked** — independent failures logged as BIZ_BUG and continue, parent failure marks entire chain CHAIN_FAILED
5. **Verify usability immediately after population** — user accounts verified with auth API right after creation (don't wait for demo-verify to discover wrong password); data relationships queried to confirm chain integrity. Population verification failure → fix and retry, never silently skip
