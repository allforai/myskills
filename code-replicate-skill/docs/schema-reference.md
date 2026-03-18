# Schema Reference

> JSON schemas for code-replicate artifacts. Standard allforai artifacts (task-inventory, business-flows, role-profiles, use-case-tree, experience-map) follow product-design definitions — see `product-design-skill/docs/schemas/`.

---

## replicate-config.json

Configuration and progress tracking for a replication session. Stored at `.allforai/code-replicate/replicate-config.json`.

```json
{
  "version": "2.0.0",
  "source_path": "/path/to/source/project",
  "fidelity": "interface | functional | architecture | exact",
  "project_type": "backend | frontend | fullstack",
  "scope": "full | modules | feature",
  "target_stack": "go-gin | nestjs | nextjs | ...",
  "business_direction": "replicate | slim | extend",
  "granularity": "fine | standard | coarse",
  "progress": {
    "current_phase": 0,
    "current_step": "",
    "completed_steps": [],
    "fragments": {}
  },
  "created_at": "ISO8601",
  "last_updated": "ISO8601"
}
```

**Field notes:**
- `fidelity` — controls field depth in standard artifacts (see fidelity-guide.md)
- `scope` — `full` analyzes everything; `modules` limits to specified directories; `feature` limits to a described feature area
- `business_direction` — `replicate` preserves all behavior; `slim` drops low-value features; `extend` adds planned features
- `granularity` — auto-determined by scope size; affects analysis detail level
- `progress` — tracks resumable state; `fragments` holds partial results keyed by step ID

---

## source-summary.json

Global context carrier produced by Phase 2b analysis. Stored at `.allforai/code-replicate/source-summary.json`.

```json
{
  "project": {
    "name": "my-project",
    "detected_stacks": ["express", "typescript", "postgresql", "redis"],
    "total_files": 342,
    "total_lines": 28500
  },
  "modules": [
    {
      "id": "M001",
      "path": "src/modules/user",
      "responsibility": "User account management (registration, login, profile)",
      "exposed_interfaces": ["UserService.register", "UserService.login"],
      "dependencies": ["M003"],
      "key_files": ["user.controller.ts", "user.service.ts", "user.entity.ts"],
      "file_count": 8,
      "line_count": 1200,
      "confidence": "high | medium | low"
    }
  ],
  "cross_cutting": [
    {
      "concern": "authentication",
      "mechanism": "JWT Guard middleware",
      "applied_to": ["M001", "M002", "M004"],
      "source_files": ["src/common/guards/auth.guard.ts"]
    }
  ],
  "data_entities": [
    {
      "name": "User",
      "source_file": "src/entities/user.entity.ts",
      "fields": ["id", "email", "password_hash", "created_at"],
      "relations": [{ "target": "Order", "type": "one-to-many" }]
    }
  ],
  "infrastructure": {
    "database": "postgresql",
    "cache": "redis",
    "queue": "bull",
    "storage": "local",
    "containerization": "docker-compose"
  },
  "api_call_map": {
    "internal": [
      { "from": "M001", "to": "M003", "method": "direct import" }
    ],
    "external": [
      { "target": "https://api.stripe.com", "used_by": "M002", "purpose": "payment processing" }
    ]
  }
}
```

**Field notes:**
- `modules[].confidence` — `high` means clear boundary and cohesive naming; `low` means inferred from file structure alone
- `cross_cutting` — behaviors applied across modules (middleware, decorators, base classes)
- `api_call_map.internal` — inter-module dependencies; `external` — third-party API calls

---

## stack-mapping.json

Cross-stack mapping decisions produced by Phase 2d. Stored at `.allforai/code-replicate/stack-mapping.json`.

```json
{
  "source_stack": "express-typescript",
  "target_stack": "go-gin",
  "auto_mapped": [
    {
      "source_construct": "Express router.get()",
      "target_construct": "Gin r.GET()",
      "rule": "express-to-gin-route"
    }
  ],
  "user_decisions": [
    {
      "source_construct": "Python Celery task queue",
      "target_construct": "asynq",
      "rationale": "User chose Redis-backed queue for production reliability",
      "semantic_drift_risk": "low | medium | high",
      "decided_at": "ISO8601"
    }
  ],
  "framework_builtins": [
    {
      "source_impl": "Hand-written pagination logic",
      "source_refs": ["src/utils/paginate.ts:15"],
      "target_builtin": "Spring Data Pageable",
      "category": "pagination",
      "decision": "use_builtin | keep_custom | hybrid"
    }
  ],
  "unmapped": [],
  "created_at": "ISO8601"
}
```

**Field notes:**
- `auto_mapped` — direct equivalences that need no user input
- `user_decisions` — multi-option scenarios where the user chose a target construct
- `framework_builtins` — source hand-written code replaceable by target framework built-ins
- `unmapped` — constructs that could not be mapped (require manual resolution)
