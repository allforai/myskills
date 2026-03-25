# Three-Platform Plugin Acceptance Test Matrix

> Date: 2026-03-26
> Status: Approved
> Purpose: PR merge gate — all 3 projects must pass on all 3 platforms before merging feat/multi-platform-native-skills

## Test Projects

### Project 1: FreshEats Delivery App (鲜食达外卖)

**Type:** Mobile + Backend (Flutter + Go Gin)
**Validates:** product-design → dev-forge → demo-forge

**Scenario:**
- 3 roles: customer, merchant, rider
- 20+ tasks across ordering, delivery tracking, merchant management
- 3 core business flows: place order, dispatch rider, merchant settlement
- UI design with per-role HTML previews
- Demo data with media (food photos, store logos)

**Execution chain:**
```
/product-design full
  → .allforai/product-concept/product-concept.json
  → .allforai/product-map/ (role-profiles, task-inventory, task-index, business-flows)
  → .allforai/experience-map/ (journey-emotion-map, experience-map, interaction-gate)
  → .allforai/use-case/ (use-case-tree.json + use-case-report.md)
  → .allforai/feature-gap/ (gap-report.json + gap-report.md)
  → .allforai/ui-design/ (ui-design-spec.md + preview/*.html)
  → .allforai/design-audit/ (audit-report.json + audit-report.md)

/project-forge full
  → .allforai/project-forge/ (forge-decisions, project-manifest, build-log)
  → Sub-projects: go-api (Go Gin) + flutter-app (Flutter)
  → Per sub-project: requirements.md + design.md + tasks.md

/demo-forge
  → .allforai/demo-forge/ (demo-plan, forge-data, assets/, verify-report)
  → Multi-round iteration until 95% pass rate
```

---

### Project 2: TeamPulse Team Management SaaS

**Type:** Web backend + frontend (Go Gin + React)
**Validates:** dev-forge → code-tuner → ui-forge

**Scenario:**
- Team/member/project CRUD with role-based access
- Sprint board, task assignment, workload heatmap
- Go Gin three-tier architecture (handler → service → repository)
- 4 modules: auth, team, project, analytics

**Execution chain:**
```
/project-forge full (from manual requirements, no product-design)
  → .allforai/project-forge/ (forge-decisions, project-manifest)
  → Sub-projects: go-api + react-web
  → Generate code skeleton + implement tasks

/code-tuner full
  → .allforai/code-tuner/ (tuner-profile, phase1-4 JSONs, tuner-report.md, tuner-tasks.json)
  → Verify: architecture compliance score, duplication rate, abstraction quality

/ui-forge
  → Fidelity check against ui-design-spec
  → Restore or polish as needed
```

---

### Project 3: Open Source Project Replication

**Type:** Reverse-engineering an existing Go API
**Validates:** code-replicate → dev-forge

**Scenario:**
- Target: a small open-source Go REST API (e.g., a task management API with 5-10 endpoints)
- Reverse-engineer into .allforai/ artifacts
- Use artifacts to generate a Flutter frontend

**Execution chain:**
```
/code-replicate (point at existing Go API source)
  → .allforai/product-map/ (reverse-engineered role-profiles, task-inventory)
  → .allforai/use-case/ (reverse-engineered use-case-tree)
  → .allforai/experience-map/ (reverse-engineered)

/project-forge full (using replicated artifacts, generate Flutter frontend)
  → .allforai/project-forge/
  → Flutter app code generated from reverse-engineered specs
```

---

## Test Matrix

```
                        product  dev    demo   code   code      ui
                        design   forge  forge  tuner  replicate forge
FreshEats Delivery       X        X      X      -      -         -
TeamPulse SaaS           -        X      -      X      -         X
Open Source Replication   -        X      -      -      X         -
```

## Acceptance Criteria (per project, per platform)

| Check | Standard | Tolerance |
|-------|----------|-----------|
| `.allforai/` directory structure | Identical across 3 platforms | Exact match |
| JSON output schema (field names, types) | Identical | Exact match |
| Phase execution order | Same phases in same order | Exact match |
| Output file count | Same number of files | Exact match |
| Quality scores (code-tuner) | Same scoring weights applied | +/- 5% (LLM randomness) |
| Degradation behavior | Same fallback paths | Exact match |
| Report content | Semantically equivalent | Language may differ (CN vs EN) |

## Execution Order

```
Phase 1: Claude — run all 3 projects (establish baseline)
Phase 2: Codex  — run all 3 projects (compare to baseline)
Phase 3: OpenCode — run all 3 projects (compare to baseline)
Phase 4: Diff report — aggregate differences across platforms
```

## Diff Report Format

For each project, produce:
```
## [Project Name] — Platform Comparison

### .allforai/ structure diff
(tree diff of directory listings)

### JSON schema diff
(field-by-field comparison of key output files)

### Behavioral diff
(any phases skipped, extra questions asked, different degradation paths)

### Verdict: PASS / FAIL
```

## Pass Criteria for PR Merge

**All 3 projects must PASS on all 3 platforms.** Specifically:
1. Claude baseline established (all 3 projects produce valid .allforai/ output)
2. Codex produces structurally identical output for all 3 projects
3. OpenCode produces structurally identical output for all 3 projects
4. No platform skips phases that others execute
5. No platform produces extra/missing output files
