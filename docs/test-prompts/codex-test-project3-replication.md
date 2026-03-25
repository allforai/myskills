# Codex Test — Project 3: Open Source Project Replication

## Context

You are testing the myskills plugin suite on the Codex platform. Plugins at `/path/to/myskills/codex/`.

Test project directory: `test-replication/`

## Task 1: Code Replicate (reverse-engineer existing Go API)

Read `codex/code-replicate-skill/AGENTS.md` and `codex/code-replicate-skill/execution-playbook.md`.

**Source project (simulated):**
A simple Go REST API for task management:
- 5 endpoints: GET /tasks, POST /tasks, GET /tasks/:id, PUT /tasks/:id, DELETE /tasks/:id
- User auth: POST /auth/register, POST /auth/login, GET /auth/profile
- JWT authentication middleware
- PostgreSQL with GORM
- ~500 lines of Go code
- Three-tier: handlers → services → repositories

**Execute code-replicate in functional mode:**
1. Phase 1: Discovery — scan source code, identify endpoints, entities, auth pattern
2. Phase 2: Structure analysis (stages A-D) — map layers, dependencies, resources
3. Phase 3: Artifact generation — produce .allforai/ artifacts compatible with dev-forge
4. Phase 4: Verification

**Expected output (reverse-engineered artifacts):**
```
.allforai/product-map/role-profiles.json      (at least 1 role: user)
.allforai/product-map/task-inventory.json     (at least 8 tasks from endpoints)
.allforai/product-map/task-index.json         (at least 2 modules: tasks, auth)
.allforai/product-map/business-flows.json     (at least 2 flows: task CRUD, auth)
.allforai/use-case/use-case-tree.json         (at least 10 use cases)
.allforai/use-case/use-case-report.md         (summary)
```

---

## Task 2: Dev Forge (generate Flutter frontend from replicated artifacts)

Read `codex/dev-forge-skill/AGENTS.md` and `codex/dev-forge-skill/execution-playbook.md`.

Using the reverse-engineered .allforai/ artifacts from Task 1, generate a Flutter frontend:

**Key decision:** Backend already exists — only generate frontend.

**Execute:**
1. forge-decisions: Flutter-only, backend exists at localhost:8080
2. project-manifest: 1 sub-project (flutter-app)
3. Spec generation: requirements, design (about 8 screens, navigation, API integration), tasks (at least 12 tasks)

**Expected output:**
```
.allforai/project-forge/forge-decisions.json
.allforai/project-forge/project-manifest.json
flutter-app/requirements.md
flutter-app/design.md
flutter-app/tasks.md
```

---

## Verification

```bash
find test-replication/.allforai/ -type f | wc -l
# Expected: 9+ files

find test-replication/.allforai/ -name "*.json" -exec python3 -m json.tool {} > /dev/null \;

# Check reverse-engineered task count
python3 -c "
import json
tasks = json.load(open('test-replication/.allforai/product-map/task-inventory.json'))
print(f'Reverse-engineered tasks: {len(tasks) if isinstance(tasks, list) else \"check structure\"}')
"
```
