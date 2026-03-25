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
| Application running | User | API accessible, database connectable |

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

**Population order follows scenario chain** (not entity alphabetical order), ensuring FK dependencies:

```
1. DB population: config tables, dictionaries, API_GAP entities (no business logic)
2. API population: user accounts (all chains depend on users)
3. Mixed population: by scenario priority (high-freq -> mid-freq -> low-freq)
   - Per scenario, chain order: parent -> child -> associated entities
   - Per entity, use method from demo-plan Step 1-C-2 annotation (api or db)
```

**DB population notes**:
- Direct write bypasses business logic (triggers, callbacks), derived fields need E4 manual correction
- ORM `created_at` / `updated_at` auto-fill does not work, must specify explicitly
- DB-populated records are also written to `forge-data.json`, clean mode DELETEs them directly

**Failure handling**:
- **Independent entity failure**: log and continue with other entities
- **Parent entity failure**: skip all children in that chain (avoid FK dangling), mark entire chain as `CHAIN_FAILED`
- **Population complete**: summarize failed chain count and reasons

**Output**:
- `forge-data.json` — created data inventory (temp IDs replaced with real server IDs)
- `forge-log.json` — population log (operation status per record)

---

### E4: Derived Data Correction (post-DB population)

DB direct write bypasses business logic. Manual correction needed:

| Correction Type | Operation |
|----------------|-----------|
| Aggregate fields | `SELECT SUM(amount) FROM details WHERE parent_id=?` -> `UPDATE parent SET total=?` |
| Count fields | `SELECT COUNT(*) FROM children WHERE parent_id=?` -> `UPDATE parent SET count=?` |
| Balance/inventory | Forward-calculate final value from all journal records |
| Search index | Trigger reindex if full-text search exists |

**Output**: Update `forge-log.json` with E4 correction records.

---

## forge-data-draft.json vs forge-data.json

| File | Stage | ID Type | Purpose |
|------|-------|---------|---------|
| `forge-data-draft.json` | After E1 | Temp placeholder (TEMP-001) | Data blueprint, reusable after clean |
| `forge-data.json` | After E3 | Real server IDs | Basis for clean and verify |

Draft is preserved. After clean, can re-populate without regenerating data.

---

## Clean Mode

Read `forge-data.json`, delete all populated data in reverse population order.

**Cleanup order** (reverse of population, respecting FK constraints):

```
1. Child entities -> parent entities (reverse of forge-data.json population order)
2. User accounts (deleted last, other entities may reference user_id)
3. DB-populated base data (config tables, dictionaries)
```

**Cleanup method**:
- Unified DB DELETE (not API, faster and supports batch)
- DELETE by `id` and `table` from `forge-data.json`
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
| Derived inconsistency | Re-run E4 derived data correction |

---

## Output Files

| File | Path | Description |
|------|------|-------------|
| `forge-data-draft.json` | `.allforai/demo-forge/` | E1 generated dataset (temp IDs) |
| `forge-data.json` | `.allforai/demo-forge/` | E3 populated data inventory (real IDs) |
| `forge-log.json` | `.allforai/demo-forge/` | Population log (status + E4 corrections) |

---

## Iron Rules

1. **Prefer API, use DB when needed** — API population triggers full business logic, DB direct write only for unsupported scenarios
2. **Derived fields must be mathematically calculated, not LLM-estimated** — SUM/COUNT/balance all from deterministic queries
3. **Chain order: parent before child** — any child entity must have its parent already existing before population
4. **Failures are never silent** — independent failures logged and continue, parent failure marks entire chain CHAIN_FAILED
5. **Post-population immediate validation** — verify user login right after account creation (do not wait for demo-verify); confirm chain integrity after association creation. Validation failure -> fix and retry, never silently skip
