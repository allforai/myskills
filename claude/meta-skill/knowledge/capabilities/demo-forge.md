# Demo Forge Capability

> Create demo-ready data sets via API-driven population + visual verification.
> Internal execution is LLM-driven — data design adapts to project entities and flows.

## Goal

Make the product look like real users are really using it. Design data from product map,
populate via API calls, verify visually. This is also the strongest integration test —
it exposes runtime issues that compile-verify cannot catch.

## Prerequisites

1. Product-map artifacts exist
2. Application code is complete (core features functional)
3. Application is running (needs live instance)

## What LLM Must Accomplish (not how)

### Required Outcomes

- Demo data set designed from product map entities and flows
- Data populated via API calls (not direct DB inserts — validates the API)
- Visual verification: populated data visible on all screens
- >= 95% verification pass rate (max 3 rounds of fix + re-verify)

### Data Design Principles (LLM applies based on project)

| Principle | What | Why |
|-----------|------|-----|
| One account per role | Meaningful usernames, per-role experience | Demonstrates role-based access |
| >= 3 per entity list | Lists don't feel empty | Realistic appearance |
| Full lifecycle chains | Not just "created" — also "in progress", "completed", "archived" | Shows real usage patterns |
| Enum coverage | >= 2 options per status/type field | Demonstrates all states |
| Time distribution | Spread across past 30 days | Shows temporal patterns |
| Realistic behavior | Action sequences that make sense (don't just random-fill) | Believable demo |
| Media fields populated | Images/audio/video where needed (not placeholder URLs) | Professional appearance |
| Constraint compliance | Unique keys, foreign keys, business rules all respected | Validates data integrity |

### Required Outputs

| Output | What |
|--------|------|
| `demo-plan.json` | Data design: entities, volumes, chains, media needs |
| `forge-data.json` | Record of all created entities with IDs |
| `verify-report.json` | Visual verification results |

## Methodology Guidance (not steps)

- **Maximum realism**: Use REAL services whenever possible. If the user provided API keys,
  use the real AI/storage/payment service — NOT mocks or stubs. Dev-mode adapters should
  check for real credentials and use them when available. The ONLY acceptable stubs are
  for external services that genuinely cannot be called (e.g., no API key provided, service
  requires production environment). Every stub is a gap in integration testing.
- **API-driven insertion**: Every data insert is an API call = integration test
- **Dependency order**: Create parent entities before children
- **Zero external links**: All media uploaded to app server
- **Zero placeholder data**: No "[Dev]" prefixed strings, no "https://dev.example.com" URLs.
  If the real service can produce the data, use it. If not, clearly mark as TODO.
- **Verify visually**: Navigate screens with Playwright, verify data appears correctly
- **Fix and re-verify**: On verification failure, diagnose cause, fix data or code, re-verify
- **Demo is testing**: Demo-forge is the strongest integration test. When it discovers
  bugs (wrong API response, missing field, broken adapter, auth failure), the orchestrator
  should pause demo, fix the code, restart services, and resume demo — not skip the issue.
  Demo-forge failures that require code changes should trigger the orchestrator to:
  1. Record the failure in transition_log
  2. Fix the code (directly or via diagnosis protocol)
  3. Rebuild + restart services
  4. Re-run the failed demo step
- **E2E verification is mandatory**: Smoke-test MUST include Playwright-based full E2E
  testing, not just curl API calls. If the project has a frontend (admin/mobile/web),
  the smoke-test node-spec must instruct the subagent to:
  1. Open the frontend in Playwright
  2. Login with seeded credentials
  3. Navigate core flows (list → detail → create → verify)
  4. Take screenshots as evidence
  5. Report any UI rendering issues, broken links, or missing data
  API-only testing misses: broken frontend routing, missing components, CSS issues,
  auth token flow in browser, client-side validation, CORS problems.

## Specialization Guidance

| Project Type | Demo Forge Differences |
|-------------|----------------------|
| Consumer app | User journey data (onboarding → engagement → retention progression) |
| Admin/SaaS | Multi-tenant data, role hierarchies, workflow states |
| Game | Player save data at different progression stages, economy snapshots |
| SDK | Example project using the SDK (dogfooding) — not traditional demo data |
| Marketplace | Both supplier and buyer data, transaction history |

## Knowledge References

### Phase-Specific:
- consumer-maturity-patterns.md: demo data should showcase consumer maturity patterns
- governance-styles.md §Operation-Profiles: demo data volume calibrated to operation profiles

## Composition Hints

### Single Node (default)
For most projects: one demo-forge node runs design + populate + verify.

### Split into Multiple Nodes
For iterative refinement: split design vs execute.
