# Quality Checks Capability

> Post-implementation quality validation: dead link detection, CRUD gap hunting,
> ghost feature removal, and cross-layer field name consistency.

## Purpose

Catch quality issues that slip through individual node verification:
- Dead links / broken references in code and artifacts
- CRUD operations that exist in API but have no UI (or vice versa)
- Ghost features (code that's unreachable from any user flow)
- Field name drift between UI labels, API params, DB columns

## Protocol

### Deadhunt
1. **Dead links**: Scan routes/navigation for links pointing to non-existent pages
2. **CRUD gaps**: Cross-reference UI operations × API endpoints × DB operations
3. **Ghost features**: Code reachability analysis — functions not called from any route
4. **Seam checks**: Integration points between modules — caller/callee signature match

### Fieldcheck
1. **UI → API**: Form field names match API request parameter names
2. **API → Entity**: API parameter names match ORM/model field names
3. **Entity → DB**: Model field names match database column names
4. **End-to-end**: Trace a field from UI label through API to DB column — consistent?

### Understand-then-Scan Pattern
For both deadhunt and fieldcheck:
1. LLM reads project structure once → builds understanding
2. Derives detection rules from understanding (not hardcoded grep patterns)
3. Batch scans all files using derived rules
4. Reports findings with file:line references

Output: `.allforai/quality-checks/deadhunt-report.json` + `fieldcheck-report.json`

**deadhunt-report.json field schema:**
```json
{
  "dead_routes": [
    {
      "route": "<string>",
      "file": "<string — file:line>",
      "reason": "<string>"
    }
  ],
  "field_mismatches": [
    {
      "field": "<string>",
      "expected": "<string>",
      "actual": "<string>",
      "file": "<string — file:line>"
    }
  ],
  "fix_tasks": [
    {
      "id": "<string>",
      "type": "<enum: dead_route | field_mismatch | broken_reference>",
      "description": "<string>",
      "file": "<string — file:line reference>",
      "suggested_fix": "<string>"
    }
  ]
}
```
`fix_tasks[].file` MUST include line number (file:line format). Every finding generates a fix_task.

## Rules (Must Preserve)

1. **Understand-then-scan**: LLM reads code to understand patterns FIRST, then scans. No blind grep.
2. **No false positives on intentional gaps**: Dead code marked with `// deprecated` or `// TODO` is flagged differently from truly orphaned code.
3. **Cross-layer tracing**: Field consistency checked across ALL layers, not just adjacent ones.
4. **Actionable output**: Every finding has file:line reference and suggested fix.

## Knowledge References

### Phase-Specific:
- design-audit-dimensions.md §Reference-Integrity: cross-artifact reference validation
- cross-phase-protocols.md §Upstream-Baseline-Validation: staleness and fidelity checks

## Contract-Parity Check (added 2026-04-14)

Extends deadhunt + fieldcheck with a third scan: **when the same symbol name
is consumed by 2+ sites, do all consumers agree on its shape / semantics?**

Classes of symbol to scan:
- **Env vars** — `ProcessInfo.environment[...]`, `os.Getenv(...)`,
  `process.env.*`, `viper.Get*(...)` — any env name referenced in >1 file
  with different derived usage shapes
- **HTTP request fields** — JSON keys in request bodies, query params, path
  params. If the server handler names field `tier` but the admin UI sends
  `subscription_tier`, that's contract drift, even if both compile
- **Query params declared by the server but never read** — `c.Query("tags")`
  that is parsed into a variable then discarded silently (the value never
  reaches the repo / service). Users who pass `?tags=unknown` get the
  wrong result set. Fails silently unless explicitly tested.
- **Response payload keys** — server returns `free_conv` but iOS decoder
  expects `free_conversation`; decoder gracefully returns nil, UI shows
  blank state, no stacktrace
- **Enum values that N-1 consumers know about** — server produces
  `semanticType=placement_quiz` but iOS MessageBubble switch doesn't handle
  it, falls through to default rendering

Detection method:
1. Grep all call sites of the symbol.
2. Extract the expected shape from each surrounding context — what suffix
   is appended, what field is parsed from it, what default is used when
   missing.
3. If any two shapes conflict → `contract_drift_finding`. Include severity
   based on: (a) how many users hit the production path that uses the
   mismatched consumer, (b) whether the mismatch produces a visible error
   or a silent wrong result.

Output goes into `fieldcheck-report.json` under a new key:

```json
{
  "contract_drift_findings": [
    {
      "id": "CD-001",
      "symbol": "UITEST_API_BASE_URL",
      "kind": "env_var_dual_contract",
      "consumers": [
        {"file": "FlyDictUITests/APIHelper.swift", "line": 12, "shape": "bare host; test prepends /api/v1"},
        {"file": "FlyDictApp.swift", "line": 32, "shape": "full URL including /api/v1"}
      ],
      "severity": "P1",
      "user_impact": "Manual launch shows 404 login screen; XCUITest passes.",
      "recommended_fix": "APIClient auto-appends /api/v1 when absent, OR unify test + app conventions on same format"
    },
    {
      "id": "CD-002",
      "symbol": "tier",
      "kind": "request_body_field_drift",
      "consumers": [
        {"file": "flydict-api/internal/controller/admin/user_mgmt_controller.go", "line": 163, "shape": "json:\"tier\" binding:\"required\""},
        {"file": "flydict-admin/src/lib/api/endpoints/users.ts", "line": 22, "shape": "body payload names field subscription_tier"}
      ],
      "severity": "P0",
      "user_impact": "Admin UI PATCH returns 400; subscription adjustments silently fail until one side updates."
    },
    {
      "id": "CD-003",
      "symbol": "/scenarios?tags=",
      "kind": "query_param_accepted_but_unused",
      "consumers": [
        {"file": "scenario_controller.go", "line": 60, "shape": "c.Query(\"tags\") read but passed nowhere"}
      ],
      "severity": "P1",
      "user_impact": "Unknown tag values return full result set instead of 0 rows; users filter by typo see everything."
    }
  ]
}
```

Iron-rule note (from 2026-04-14 FlyDict retrospective):
Items listed in `business-model.rejected_options[]` and
`product-concept.errc_highlights.eliminate[]` are **intentional removals**.
Do NOT flag their absence as contract drift. Only flag where two live
consumers exist with different expectations — not where one consumer was
deliberately retired.

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `deadhunt-report.json` | `fix_tasks[]` | translate (fix loop) | required | 修复循环需要知道哪些死链和字段不一致要修 |
| `fieldcheck-report.json` | `field_mismatches[]` | translate (fix loop) | required | 字段不一致修复需要具体的字段映射信息 |

## Composition Hints

### Single Node (default)
Run after all implementation and verification nodes complete. One node covers both deadhunt + fieldcheck.

### Split Deadhunt vs Fieldcheck
For very large projects: separate nodes for independent parallel execution.

### Skip Fieldcheck
For backend-only projects with no UI layer: fieldcheck (UI→API) is not applicable. Still run deadhunt.
