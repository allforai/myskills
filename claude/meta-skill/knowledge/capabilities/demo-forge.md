# Demo Forge Capability

> Capability reference for demo data generation via API-driven population.
> Bootstrap may create one or multiple nodes from this capability depending on project complexity.

## Purpose

Create demo-ready data sets that showcase the product's capabilities.
Design data schema from product map, populate via API calls, verify visually.

Goal: make the product look like real users are really using it.

## Prerequisites

1. product-map artifacts exist (`.allforai/product-map/`)
2. Application code is complete (core features functional)
3. Application is running (execute + verify need live instance)

## Phases

### Phase 1: Design

From product-map blueprint, plan the full demo data set:
- Account system (one account per role, meaningful usernames)
- Data volume (at least 3 per entity list)
- Business chains (full lifecycle flows, not just creation)
- Enum coverage (at least 2 options per status field)
- Time distribution (spread across past 30 days)
- Behavior patterns (realistic action sequences)
- Media fields (identify which fields need image/video)
- Constraints (unique keys, foreign keys, business rules)

Output: `.allforai/demo-forge/demo-plan.json`, `model-mapping.json`, `api-gaps.json`

### Phase 2: Media

Acquire or generate demo media assets:
- Search existing assets or generate via image/video AI
- Process to required dimensions/formats
- Upload to app server (no external links allowed)

Output: `.allforai/demo-forge/upload-mapping.json`

### Phase 3: Execute

API-driven data population:
- Follow demo-plan entity chains in dependency order
- Validate data integrity on each API call (insertion = integration test)
- Record all created entity IDs for verify phase

Output: `.allforai/demo-forge/forge-data.json`

### Phase 4: Verify

Playwright-based visual verification:
- Navigate all screens with populated data
- Verify 7 layers: lists visible, details correct, relationships shown,
  media renders, status flows completable, search/filter works, role isolation holds
- On failure: diagnose cause, fix data or code, re-verify
- Convergence: iterate until 95% pass rate (max 3 rounds)

Output: `.allforai/demo-forge/verify-report.json`

## Rules

1. **Product-map prerequisite**: product-map must exist before demo-forge.
2. **App must be running**: execute + verify need live app instance.
3. **API-driven insertion**: Validate data integrity during population, not after.
4. **Zero external links**: All media assets uploaded to app server.
5. **95% convergence**: Iterate design->execute->verify until 95% pass (max 3 rounds).
6. **Business chain completeness**: Data must form complete lifecycle flows, not isolated records.

## Composition Hints

### Single Node (default)
For most projects: one demo-forge node runs design + media + execute + verify as a single pipeline.

### Split into Multiple Nodes
For iterative refinement: split design vs execute (demo-forge-design, demo-forge-execute) so data design can be reviewed and revised before population begins.

### Merge with Another Capability
Rarely merged. Demo forge requires a running application and product-map artifacts, making it a distinct pipeline stage. Keep separate.
