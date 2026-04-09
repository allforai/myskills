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
