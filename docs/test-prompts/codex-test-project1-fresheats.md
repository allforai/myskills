# Codex Test — Project 1: FreshEats Delivery App (鲜食达外卖)

## Context

You are testing the myskills plugin suite on the Codex platform. The plugins are at `/path/to/myskills/codex/`. Each plugin has an `AGENTS.md` entry point and an `execution-playbook.md` for phase orchestration.

The test project directory is: `test-fresheats/`

## Task 1: Product Design Full Pipeline

Read `codex/product-design-skill/AGENTS.md` and `codex/product-design-skill/execution-playbook.md` first.

Then execute the full product-design pipeline for a **FreshEats food delivery app**:

**Product description:**
- 鲜食达 — 30-minute fresh food delivery platform
- 3 roles: customer (顾客), merchant (商家), rider (骑手)
- Core flows: place order → dispatch rider → deliver → settle
- Mobile app (Flutter) + backend API (Go Gin)
- Competitors: Meituan, Ele.me

**Execute phases in order:**
1. Phase 1: Product Concept — define problem, roles, value proposition
2. Phase 2: Product Map — 3 roles, 20+ tasks, 3 business flows, task index, flow index
3. Phase 3: Journey Emotion — emotional journey per role per flow
4. Phase 4: Experience Map — screens, operation lines, interaction gate scoring
5. Phase 5: Use Cases + Feature Gap (parallel) — 40+ use cases, gap analysis
6. Phase 6: Feature Prune — classify CORE/DEFER/CUT
7. Phase 7: UI Design — design spec with tokens and component guidelines
8. Phase 8: Design Audit — multi-dimensional audit with scoring

**All output goes to:** `test-fresheats/.allforai/`

**Expected output files:**
```
.allforai/
├── product-concept/product-concept.json
├── product-map/role-profiles.json
├── product-map/task-inventory.json
├── product-map/task-index.json
├── product-map/business-flows.json
├── product-map/flow-index.json
├── experience-map/journey-emotion-map.json
├── experience-map/experience-map.json
├── experience-map/interaction-gate.json
├── use-case/use-case-tree.json
├── use-case/use-case-report.md
├── feature-gap/gap-report.json
├── feature-gap/gap-report.md
├── feature-prune/prune-decisions.json
├── feature-prune/prune-report.md
├── ui-design/ui-design-spec.md
├── design-audit/audit-report.json
└── design-audit/audit-report.md
```

**Quality criteria:**
- All JSON files must be valid (parseable)
- role-profiles: 3 roles
- task-inventory: 20+ tasks
- business-flows: 3+ flows
- use-case-tree: 40+ use cases
- audit score: documented with 5-dimension breakdown

---

## Task 2: Dev Forge Full Pipeline

Read `codex/dev-forge-skill/AGENTS.md` and `codex/dev-forge-skill/execution-playbook.md`.

Using the product-design output from Task 1, execute project-forge full:

**Tech decisions:**
- Backend: Go (Gin) three-tier architecture, PostgreSQL
- Frontend: Flutter with clean architecture
- 2 sub-projects: go-api + flutter-app

**Execute:**
1. Phase 0: Detect prerequisites, route to full mode
2. Phase 2: Project setup — 2 sub-projects with tech stack assignment
3. Phase 3: Design to spec — generate requirements.md, design.md, tasks.md for go-api
4. Phase 4: Simulated build progress

**Expected output:**
```
.allforai/project-forge/forge-decisions.json
.allforai/project-forge/project-manifest.json
.allforai/project-forge/build-log.json
go-api/requirements.md
go-api/design.md
go-api/tasks.md
```

**Quality criteria:**
- requirements.md traces back to product-map tasks (T001-T024)
- design.md includes REST endpoints (40+) and DB schema (10+ tables)
- tasks.md has 30+ atomic implementation tasks

---

## Task 3: Demo Forge

Read `codex/demo-forge-skill/AGENTS.md` and `codex/demo-forge-skill/execution-playbook.md`.

Using all prior output, execute demo-forge:

**Execute:**
1. Phase 1: Demo plan — entities, data distribution, media requirements
2. Phase 2: Media asset manifest (simulated — metadata only)
3. Phase 3: Seed data generation — 300+ records across all entities
4. Phase 4: Verification report with multi-round iteration

**Expected output:**
```
.allforai/demo-forge/demo-plan.json
.allforai/demo-forge/assets-manifest.json
.allforai/demo-forge/forge-data.json
.allforai/demo-forge/verify-report.json
.allforai/demo-forge/round-history.json
```

**Quality criteria:**
- demo-plan covers all entities from the data model
- forge-data has 300+ records with realistic data
- verify-report shows iteration toward 95%+ pass rate

---

## Verification

After all 3 tasks, verify:

```bash
# File count
find test-fresheats/.allforai/ -type f | wc -l
# Expected: 26+ files

# JSON validation
find test-fresheats/.allforai/ -name "*.json" -exec python3 -m json.tool {} > /dev/null \;

# Key data checks
python3 -c "
import json
tasks = json.load(open('test-fresheats/.allforai/product-map/task-inventory.json'))
print(f'Tasks: {len(tasks) if isinstance(tasks, list) else \"check structure\"}')
"
```
