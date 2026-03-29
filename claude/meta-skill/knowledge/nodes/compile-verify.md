# Compile Verify Node Template

> Verify that translated code compiles and builds successfully.
> Distinct from per-component compile loops in translate — this is the final gate.

## Purpose

Full build verification after all translation is complete.
Catches cross-component integration issues that per-component loops may miss
(shared type mismatches, import cycles, missing peer dependencies).

## Protocol

1. Run full build command(s)
2. Capture exit code + error output
3. On failure: categorize errors (see Error Taxonomy below), feed back to translate node for targeted fixes
4. On success: mark node complete, pass build artifact paths to test-verify

## Error Taxonomy

| Category | Examples | Action |
|----------|----------|--------|
| Syntax | Missing semicolons, malformed expressions | Return to translate — component-level fix |
| Type mismatch | Interface drift between modules | Return to translate — fix at boundary |
| Missing dependency | Unresolved import, absent package | Check mapping table — add to target stack |
| Configuration | Build config missing, env vars absent | Fix in node-spec build section |
| Integration | Cross-module circular dependency | Return to translate — restructure DAG |

## Rules

1. **Build commands from node-spec**: Not hardcoded. Bootstrap generates them per platform.
2. **Full build, not incremental**: Catches cross-component integration issues that incremental builds hide.
3. **Error categorization before retry**: LLM must classify each error before feeding back — prevents random fix attempts.
4. **Max 3 fix-and-rebuild cycles**: If not green after 3 cycles, surface unresolved errors as UPSTREAM_DEFECT.
5. **No silent partial success**: If build emits warnings that indicate runtime failure (deprecations, missing peer deps), treat as failure.
6. **Artifact path recording**: On success, record output artifact paths (dist/, build/, apk, etc.) for test-verify.

## Connection to Fidelity Verification

This node covers the R1 (Build) layer of the cr-fidelity runtime verification stack:
- R1 pass here = prerequisite cleared for test-verify (R2 Smoke, R3 Test Vectors, R4 Protocol Compat)
- R1 failure blocks all downstream fidelity scoring
- Build failure = composite fidelity score = 0 regardless of static analysis results

## What Bootstrap Specializes

- Exact build commands per platform (frontend: `npm run build`, backend: `go build ./...`, mobile: `flutter build apk`, etc.)
- Expected success output patterns (exit code, output path)
- Known build quirks for this tech stack (e.g., codegen steps, proto compilation)
- Environment variable requirements at build time
