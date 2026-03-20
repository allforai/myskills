# Schema Reference

> JSON schemas for code-replicate artifacts. Standard allforai artifacts (task-inventory, business-flows, role-profiles, use-case-tree, experience-map) follow product-design definitions — see `product-design-skill/docs/schemas/`.

---

## discovery-profile.json

LLM-generated project-specific discovery rules. Stored at `.allforai/code-replicate/discovery-profile.json`. Generated in Phase 2a-pre, consumed by `cr_discover.py --profile`.

```json
{
  "source_roots": ["packages", "src"],
  "skip_dirs": ["node_modules", ".git", "dist", "build"],
  "code_extensions": [".ts", ".tsx", ".cs"],
  "entry_patterns": ["main", "index", "app", "program"],
  "module_boundaries": ["package.json", ".csproj"],
  "module_paths": [
    {"path": "src/ERP.Modules.Sales", "atomic": true},
    {"path": "packages/api/src/modules/user", "atomic": true}
  ],
  "mega_threshold": 50
}
```

**Field notes:**
- `module_paths` — **highest priority**: explicit module list from LLM. If provided, `cr_discover.py` uses these directly instead of scanning.
  - `path` — relative path from project root to the module directory
  - `atomic` — if true, this module should never be split further (its sub-dirs are layers, not sub-modules)
- `module_boundaries` — file names that mark a directory as an atomic project unit (e.g., `.csproj`, `package.json`). Size-based splitting is blocked for directories containing these files.
- `source_roots` / `skip_dirs` / `code_extensions` / `entry_patterns` — override built-in defaults for the scan fallback path
- `mega_threshold` — maximum code files before a directory is auto-split (default: 50)
- All fields are optional. Missing fields keep built-in defaults.

---

## extraction-plan.json

LLM-generated project-specific extraction rules for Phase 3 fragment generation. Stored at `.allforai/code-replicate/extraction-plan.json`. Generated in Phase 3-pre, consumed by LLM during Phase 3 Steps 3.1–3.5.

```json
{
  "role_sources": [
    {"module": "M003", "file": "internal/middleware/auth.go", "how": "RoleType enum defines 4 roles"}
  ],
  "task_sources": [
    {"module": "M001", "file": "cmd/api/handlers/*.go", "how": "each exported handler = one task"}
  ],
  "flow_sources": [
    {"module": "M002", "file": "internal/service/order_service.go", "how": "CreateOrder call chain = one flow"}
  ],
  "screen_sources": [
    {"module": "M010", "file": "src/app/*/page.tsx", "how": "each page.tsx = one screen"}
  ],
  "usecase_sources": [
    {"module": "M001", "file": "cmd/api/handlers/*.go", "how": "if/switch branches = boundary/exception UC"}
  ],
  "constraint_sources": [
    {"module": "M004", "file": "internal/model/*.go", "how": "validate struct tags = input constraints"}
  ],
  "cross_cutting": [
    {"concern": "auth", "files": ["internal/middleware/auth.go"], "applies_to": ["M001", "M002"]}
  ]
}
```

**Field notes:**
- Each `*_sources` entry tells the LLM exactly which file(s) to read and how to extract artifacts from them
- `how` field describes the extraction logic **specific to this project** — not a framework template
- `cross_cutting` lists concerns that span multiple modules (auth, logging, error handling, etc.)
- `abstraction_sources` — points to the implementation files of reuse patterns discovered in source-summary.abstractions. During Phase 3 fragment generation, LLM reads these files to understand the reuse contract, ensuring generated task/flow artifacts reference shared abstractions instead of inlining repeated logic
- Fullstack mode adds: `api_contract_files`, `cross_layer_mapping`
- Module mode adds: `boundary_interfaces`, `external_deps_mapping`

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
  },
  "abstractions": [
    {
      "name": "BaseBloc",
      "source_file": "lib/core/base_bloc.dart",
      "consumers": ["M003", "M004", "M005", "M006"],
      "consumer_count": 15,
      "what_it_provides": "统一的 loading/error state 处理 + 自动 analytics 埋点",
      "reuse_mechanism": "LLM 自由描述：继承、mixin、组合、装饰器、代码生成..."
    },
    {
      "name": "ApiService",
      "source_file": "lib/core/network/api_service.dart",
      "consumers": ["M003", "M004", "M005"],
      "consumer_count": 15,
      "what_it_provides": "统一 HTTP 封装：token 注入、错误拦截、自动重试",
      "reuse_mechanism": "依赖注入 — 所有 feature service 通过构造函数接收 ApiService 实例"
    }
  ]
}
```

**Field notes:**
- `modules[].confidence` — `high` means clear boundary and cohesive naming; `low` means inferred from file structure alone
- `cross_cutting` — behaviors applied across modules (middleware, decorators, base classes)
- `api_call_map.internal` — inter-module dependencies; `external` — third-party API calls
- `abstractions` — **LLM-discovered** reuse patterns in source code. LLM decides what qualifies as a "reuse pattern" based on reading the actual code. Fields:
  - `name` — LLM-assigned name for this abstraction
  - `source_file` — where the abstraction is defined
  - `consumers` — which modules use it (module IDs)
  - `consumer_count` — how many modules depend on it (signals importance)
  - `what_it_provides` — what behavior/contract this abstraction encapsulates
  - `reuse_mechanism` — how consumers use it (inheritance, composition, DI, mixin, etc.) — LLM describes freely, no enum

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
  "abstraction_mapping": [
    {
      "source_abstraction": "BaseBloc",
      "source_file": "lib/core/base_bloc.dart",
      "what_it_provides": "统一的 loading/error state 处理 + 自动 analytics 埋点",
      "source_mechanism": "Dart class inheritance (extends Bloc<E,S>)",
      "target_equivalent": "BaseViewModel : ObservableObject",
      "target_mechanism": "C# class inheritance + CommunityToolkit.Mvvm source generators",
      "migration_notes": "Bloc 的 event→state 模型变为 Command→Property 模型；loading/error 状态从 sealed class 变为 ObservableProperty<bool>",
      "semantic_drift_risk": "medium"
    },
    {
      "source_abstraction": "ApiService",
      "source_file": "lib/core/network/api_service.dart",
      "what_it_provides": "统一 HTTP 封装：token 注入、错误拦截、自动重试",
      "source_mechanism": "Dio interceptors + DI",
      "target_equivalent": "HttpClient + DelegatingHandler pipeline",
      "target_mechanism": "ASP.NET HttpClientFactory + Polly retry policies",
      "migration_notes": "Dio interceptor chain → DelegatingHandler chain；概念对等但 API 完全不同",
      "semantic_drift_risk": "low"
    }
  ],
  "created_at": "ISO8601"
}
```

**Field notes:**
- `auto_mapped` — direct equivalences that need no user input
- `user_decisions` — multi-option scenarios where the user chose a target construct
- `framework_builtins` — source hand-written code replaceable by target framework built-ins
- `unmapped` — constructs that could not be mapped (require manual resolution)
- `abstraction_mapping` — maps source code's reuse patterns to target stack equivalents. LLM generates this based on source-summary.abstractions + understanding of the target stack. Fields:
  - `source_abstraction` — name from source-summary.abstractions
  - `what_it_provides` — the behavior contract (stack-agnostic)
  - `source_mechanism` / `target_mechanism` — how reuse is implemented in each stack
  - `target_equivalent` — what the LLM recommends in the target stack
  - `migration_notes` — key differences that may cause semantic drift
  - `semantic_drift_risk` — LLM's assessment of how much behavior may change

---

## fidelity-report.json

Fidelity verification results from `/cr-fidelity`. Stored at `.allforai/code-replicate/fidelity-report.json`. Generated by cr-fidelity skill, updated each verification round.

```json
{
  "generated_at": "ISO8601",
  "round": 2,
  "threshold": 90,
  "overall_score": 92,
  "passed": true,
  "dimensions": {
    "F1_api_surface": {"score": 95, "total": 50, "matched": 47, "gaps": [...]},
    "F2_data_model": {"score": 90, "total": 30, "matched": 27, "gaps": [...]},
    "F3_business_flow": {"score": 88, "total": 20, "matched": 17, "gaps": [...]},
    "F4_role_permission": {"score": 100, "total": 5, "matched": 5, "gaps": []},
    "F5_exception_handling": {"score": 85, "total": 40, "matched": 34, "gaps": [...]},
    "F6_abstraction_reuse": {"score": 100, "total": 5, "matched": 5, "gaps": []},
    "F7_constraint": null
  },
  "attention_warnings": [],
  "fix_tasks": [],
  "history": [
    {"round": 1, "score": 78, "fixed_count": 15},
    {"round": 2, "score": 92, "fixed_count": 5}
  ]
}
```

**Field notes:**
- `dimensions` — each F1-F7 dimension has independent score, counts, and gap details
- `F7_constraint` — null for non-exact fidelity levels (only applicable when constraints.json exists)
- `gaps[]` — each gap has `type` (CODE_FIX / ARTIFACT_GAP / DESIGN_DECISION), `description`, `affected_artifact`, `fix_status`
- `history` — score progression across rounds (for convergence tracking)
- `passed` — true when `overall_score >= threshold`
- Convergence control (CG-F): max 3 rounds, monotonic score increase required
