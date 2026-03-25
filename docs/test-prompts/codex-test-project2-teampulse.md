# Codex Test — Project 2: TeamPulse Team Management SaaS

## Context

You are testing the myskills plugin suite on the Codex platform. Plugins at `/path/to/myskills/codex/`.

Test project directory: `test-teampulse/`

## Task 1: Dev Forge (no product-design — start from manual requirements)

Read `codex/dev-forge-skill/AGENTS.md` and `codex/dev-forge-skill/execution-playbook.md`.

**Project description:**
- TeamPulse — team management SaaS for software teams
- Features: team/member CRUD, project management, sprint board, task assignment, workload heatmap
- Go Gin three-tier (handler → service → repository), PostgreSQL
- React frontend with Ant Design
- 4 modules: auth, team, project, analytics
- RBAC: admin, manager, member roles

**Execute project-forge full:**
1. Generate forge-decisions.json (Go Gin + React, 2 sub-projects)
2. Generate project-manifest.json
3. Generate go-api specs: requirements.md (15 requirements), design.md (35+ endpoints, 7 DB tables), tasks.md (30 tasks)
4. Generate build-log.json (all tasks completed — simulating finished codebase)

**Expected output:**
```
.allforai/project-forge/forge-decisions.json
.allforai/project-forge/project-manifest.json
.allforai/project-forge/build-log.json
go-api/requirements.md
go-api/design.md
go-api/tasks.md
```

---

## Task 2: Code Tuner

Read `codex/code-tuner-skill/AGENTS.md` and `codex/code-tuner-skill/execution-playbook.md`.

Run code-tuner full analysis on the TeamPulse go-api (simulated — use the design.md as reference):

**Context:**
- Go Gin three-tier, 4 modules, PostgreSQL
- Lifecycle: pre-launch (aggressive optimization)
- Simulate realistic findings

**Execute all 5 phases:**
1. Phase 0: Project profile — identify stack, architecture, layers, modules, data model
2. Phase 1: Compliance — check T-01~T-06, G-01~G-06 rules. Find 2 T-03 violations (handler calls repo directly with business logic)
3. Phase 2: Duplication — find 3 similar CRUD patterns, 2 passthrough services
4. Phase 3: Abstraction — suggest BaseCrudService extraction, find 1 over-abstraction
5. Phase 4: Score and report

**Expected output:**
```
.allforai/code-tuner/tuner-profile.json
.allforai/code-tuner/tuner-decisions.json
.allforai/code-tuner/phase1-compliance.json
.allforai/code-tuner/phase2-duplicates.json
.allforai/code-tuner/phase3-abstractions.json
.allforai/code-tuner/tuner-report.md
.allforai/code-tuner/tuner-tasks.json
```

**Scoring target (approximate):**

| Dimension | Weight | Expected Score |
|-----------|--------|---------------|
| Architecture compliance | 25% | ~82 |
| Code duplication | 25% | ~75 |
| Abstraction quality | 20% | ~80 |
| Validation standards | 15% | ~85 |
| Data model quality | 15% | ~90 |
| **Weighted total** | | **~81-82** |

---

## Verification

```bash
find test-teampulse/.allforai/ -type f | wc -l
# Expected: 10+ files

find test-teampulse/.allforai/ -name "*.json" -exec python3 -m json.tool {} > /dev/null \;

# Check tuner scoring
grep -A10 "综合评分\|Weighted\|Total" test-teampulse/.allforai/code-tuner/tuner-report.md
```
