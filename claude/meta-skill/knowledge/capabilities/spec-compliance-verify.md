# Spec Compliance Verify Capability

> Mechanically verify that implementation matches design-to-spec artifacts.
> design-to-spec produces api-spec.json + db-schema.md + protocol-spec.md;
> this capability checks if code implements EXACTLY what was specified —
> no missing endpoints, no schema drift, no undocumented additions.

## Goal

After implementation, do a precise diff between spec artifacts and actual code.
This is NOT semantic judgment — it's mechanical: spec says 20 endpoints,
code has 20 endpoints, each with matching request/response schemas.

## Prerequisites

1. design-to-spec artifacts exist (api-spec.json, db-schema.md, optionally protocol-spec.md)
2. Implementation is complete

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `spec-compliance-report.json` | Per-endpoint / per-table / per-message verification |

**spec-compliance-report.json field schema:**
```json
{
  "api_compliance": {
    "spec_endpoint_count": "<number>",
    "implemented_count": "<number>",
    "missing": [
      { "endpoint": "<string — route + method>", "reason": "<string>" }
    ],
    "extra": [
      { "endpoint": "<string — implemented but not in spec>", "risk": "<string>" }
    ],
    "schema_drift": [
      {
        "endpoint": "<string>",
        "field": "<string — field name>",
        "spec_type": "<string>",
        "actual_type": "<string>",
        "file": "<string — file:line>"
      }
    ]
  },
  "db_compliance": {
    "spec_table_count": "<number>",
    "implemented_count": "<number>",
    "missing_tables": ["<string>"],
    "missing_columns": [
      { "table": "<string>", "column": "<string>", "spec_type": "<string>" }
    ],
    "extra_tables": ["<string — not in spec, may be intentional>"],
    "index_compliance": {
      "spec_index_count": "<number>",
      "implemented_count": "<number>",
      "missing": ["<string — index description>"]
    }
  },
  "protocol_compliance": {
    "spec_message_count": "<number>",
    "implemented_count": "<number>",
    "missing": ["<string — message type>"],
    "direction_mismatch": [
      { "message": "<string>", "spec_direction": "<string>", "actual_direction": "<string>" }
    ]
  },
  "summary": {
    "total_spec_items": "<number>",
    "compliant": "<number>",
    "missing": "<number>",
    "drifted": "<number>",
    "extra": "<number>"
  }
}
```

### Check Dimensions

**1. API Endpoint Compliance**

For each endpoint in api-spec.json:
- Route exists in code (router/route registration)
- HTTP method matches
- Request schema: all specified fields accepted, types match
- Response schema: all specified fields returned, types match
- Auth requirement matches (public / auth / role-restricted)

Also check reverse: any implemented endpoint NOT in api-spec.json → flag as "extra"
(may be intentional like health checks, or may be scope creep).

**2. DB Schema Compliance**

For each table/collection in db-schema.md:
- Table exists in migrations or ORM models
- All columns exist with correct types
- Constraints match (NOT NULL, UNIQUE, FK references)
- Indexes specified in spec are created

Also check: tables in code but not in spec → flag as "extra".

**3. Protocol Compliance (when protocol-spec.md exists)**

For each message type in protocol-spec.md:
- Message handler exists in server code
- Message sender exists in client code (or vice versa per direction)
- Payload fields match spec

### Required Quality

- 100% of spec items checked (no silent skips)
- Missing items have clear "expected X at Y, not found" descriptions
- Schema drift has field-level precision (not just "endpoint differs")
- Extra items distinguished from missing (extra = scope concern, missing = implementation gap)

## Methodology Guidance (not steps)

- **Spec-first traversal**: Iterate over spec items, check code for each. NOT code-first.
- **Mechanical matching**: Route strings, field names, type names — exact match, not semantic
- **Migration-aware**: For DB, check both ORM model definitions AND migration files
- **Extra detection matters**: Undocumented endpoints are security risks (unprotected surface area)

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Upstream-Baseline-Validation: spec is the upstream baseline

## Composition Hints

### Single Node (default)
One spec-compliance-verify node runs after implementation, before or alongside product-verify.

### Skip Entirely
When design-to-spec was skipped (goals don't include create/rebuild).
When translating (source code IS the spec).

### Merge with Product Verify
For simple projects: add spec compliance as a static check dimension within product-verify.
