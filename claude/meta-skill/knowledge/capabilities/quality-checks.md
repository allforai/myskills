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

## Rules (Must Preserve)

1. **Understand-then-scan**: LLM reads code to understand patterns FIRST, then scans. No blind grep.
2. **No false positives on intentional gaps**: Dead code marked with `// deprecated` or `// TODO` is flagged differently from truly orphaned code.
3. **Cross-layer tracing**: Field consistency checked across ALL layers, not just adjacent ones.
4. **Actionable output**: Every finding has file:line reference and suggested fix.

## Composition Hints

### Single Node (default)
Run after all implementation and verification nodes complete. One node covers both deadhunt + fieldcheck.

### Split Deadhunt vs Fieldcheck
For very large projects: separate nodes for independent parallel execution.

### Skip Fieldcheck
For backend-only projects with no UI layer: fieldcheck (UI→API) is not applicable. Still run deadhunt.
