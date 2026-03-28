---
name: demo-execute
description: >
  Use when the user asks to "populate demo data", "fill demo environment",
  "demo-execute", "demo populate", or mentions data population, demo data generation, database seeding.
  Requires demo-plan.json + style-profile.json + upload-mapping.json.
  Requires a running application for data population.
version: "1.0.0"
---

# Demo Execute — Data Generation and Population

> Turn the design scheme into real data in the application.

## Position

```
demo-forge internal stages:
  demo-design            ->  media-forge + demo-execute (this skill)  ->  demo-verify
  Plan what data to generate    Acquire media + populate data               Open product and verify
  Pure design, no execution     Consumes design scheme                      Produces issue list routed back
```

**This skill's job**: consume demo-plan + style-profile + upload-mapping, generate concrete data records, and populate the running application.

---

## Prerequisites

| Condition | Source | Description |
|-----------|--------|-------------|
| `demo-plan.json` | demo-design | Demo data scheme (entities, chains, constraints, enums, time distribution) |
| `style-profile.json` | demo-design | Industry style + text templates |
| `upload-mapping.json` | media-forge | Local asset -> server URL/ID mapping |
| Application running | User | API accessible |

All four required. If any missing, abort and prompt to complete the prerequisite.

---

## Workflow

### E1: Data Generation (deterministic)

Read `demo-plan.json` + `style-profile.json` + `upload-mapping.json`, generate records per scenario chain.

**Field generation strategy**:

| Field Type | Generation Method |
|-----------|------------------|
| Text fields | Random selection from style-profile templates, no adjacent duplicates |
| Numeric fields | Values within constraint range + boundary values |
| Time fields | Weighted sampling (recent-dense distribution + work hours + monthly +-15% fluctuation) |
| Status fields | Allocated by enum coverage requirements, every value has records (including terminal/exception) |
| Media fields | Read server_url / server_id from upload-mapping.json |
| Foreign key fields | Auto-linked by chain dependencies (parent -> child order, child references parent temp ID) |
| Derived fields | Mathematical calculation (sum = detail total, count = actual record count) |

**Behavior distribution**:

```
10% heavy users -> produce ~50% of data
30% normal users -> produce ~35% of data
60% light users -> produce ~15% of data
```

**Output**: `forge-data-draft.json` (all records use temp IDs like TEMP-001, TEMP-002).

---

### E2: Pre-population Self-check

Item-by-item quality confirmation. Issues fall into two categories:

```
[ ] Entity completeness — no zero-record entities
[ ] Enum coverage — every status field value has records (including REJECTED/CANCELED/EXPIRED/FAILED)
[ ] Foreign key integrity — every FK ID has a corresponding record in the dataset
[ ] Derived consistency — aggregate fields = sum of details, count fields = actual record count
[ ] Time logic — created_at < updated_at, parent time before child time
[ ] Media association — all media fields reference upload-mapping entries (no external URLs)
[ ] Behavior distribution — heavy users produce ~50% of data
[ ] Text dedup — no adjacent records with identical text
```

**Handling**:
- Math issues (derived inconsistency, count errors): **auto-fix**
- Other issues: mark as `PREFLIGHT_ISSUE`, report to user

`--dry-run` mode stops after E2, does not proceed to E3.

---

### E3: Data Population

**全部走 API，无例外。** 灌入过程即集成测试 — 每次 API 调用验证认证、权限、校验、业务逻辑。灌入失败 = BIZ_BUG。

**Population order follows scenario chain** (not entity alphabetical order), ensuring FK dependencies:

```
1. API population: config tables, dictionaries (POST/PUT endpoints)
2. API population: user accounts (all chains depend on users)
3. API population: by scenario priority (high-freq -> mid-freq -> low-freq)
   - Per scenario, chain order: parent -> child -> associated entities
   - ALL entities go through API endpoints in dependency order
```

**API_MISSING_BLOCKER handling**:
- Entity has no create API endpoint -> flag as `API_MISSING_BLOCKER`
- **Do NOT fall back to DB direct write.** Missing API must be created first.
- Generate a dev task for dev-forge to build the missing endpoint, then retry after endpoint is available.

**Failure handling**:
- **Independent entity failure**: log and continue with other entities. Failure = BIZ_BUG, record for dev-forge.
- **Parent entity failure**: skip all children in that chain (avoid FK dangling), mark entire chain as `CHAIN_FAILED`
- **Population complete**: summarize failed chain count and reasons

**Output**:
- `forge-data.json` — created data inventory (temp IDs replaced with real server IDs)
- `forge-log.json` — population log (operation status per record)

---

## forge-data-draft.json vs forge-data.json

| File | Stage | ID Type | Purpose |
|------|-------|---------|---------|
| `forge-data-draft.json` | After E1 | Temp placeholder (TEMP-001) | Data blueprint, reusable after clean |
| `forge-data.json` | After E3 | Real server IDs | Basis for clean and verify |

Draft is preserved. After clean, can re-populate without regenerating data.

> **No E4 stage.** API handles all derived fields (aggregates, counts, balances, indexes) automatically through business logic. No post-population correction needed.

---

## Clean Mode

Read `forge-data.json`, delete all populated data in reverse population order.

**Cleanup order** (reverse of population, respecting FK constraints):

```
1. Child entities -> parent entities (reverse of forge-data.json population order)
2. User accounts (deleted last, other entities may reference user_id)
3. Base data (config tables, dictionaries — deleted last)
```

**Cleanup method**:
- Use API DELETE endpoints where available (respects business logic and cascade rules)
- DELETE by `id` from `forge-data.json`
- If cascade delete configured, only delete top-level parents; otherwise strict reverse-order layer-by-layer

**Cleanup scope**:
- Clear `forge-data.json`, `forge-log.json`
- **Preserve** `demo-plan.json`, `style-profile.json`, `assets/`, `upload-mapping.json` (design + assets kept for reuse)
- **Preserve** `forge-data-draft.json` (can re-populate directly)

---

## Re-entry Mode

When `verify-issues.json` contains `route_to="execute"` issues, enter re-entry mode — fix issues only, no full re-population:

| Issue Type | Handling |
|-----------|---------|
| FK breakage | Check forge-data.json, supplement missing parent records or fix FK references |
| CHAIN_FAILED | Retry full population for that chain |
| API_MISSING_BLOCKER | Check if dev-forge has built the missing endpoint, retry |

---

## Output Files

| File | Path | Description |
|------|------|-------------|
| `forge-data-draft.json` | `.allforai/demo-forge/` | E1 generated dataset (temp IDs) |
| `forge-data.json` | `.allforai/demo-forge/` | E3 populated data inventory (real IDs) |
| `forge-log.json` | `.allforai/demo-forge/` | Population log (status per record) |

---

## Iron Rules

1. **全部走 API，无例外** — 所有数据灌入通过 API 端点，不直写数据库。灌入过程即集成测试 — 每次 API 调用验证认证、权限、校验、业务逻辑。灌入失败 = BIZ_BUG。
2. **API_MISSING_BLOCKER** — 缺少 API 端点不降级为 DB 直写，标记为 `API_MISSING_BLOCKER`，生成 dev task 先补 API 再灌数据
3. **Chain order: parent before child** — any child entity must have its parent already existing before population
4. **Failures are never silent** — independent failures logged and continue, parent failure marks entire chain CHAIN_FAILED
5. **Post-population immediate validation** — verify user login right after account creation (do not wait for demo-verify); confirm chain integrity after association creation. Validation failure -> fix and retry, never silently skip
6. **No E4 derived correction** — API handles derived fields automatically. If aggregates are wrong after API population, that is a BIZ_BUG, not a demo-forge concern
