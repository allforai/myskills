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

## infrastructure-profile.json

LLM-generated infrastructure inventory. Stored at `.allforai/code-replicate/infrastructure-profile.json`. Generated in Phase 2b-infra by LLM reading source code (not dependency manifests).

```json
{
  "generated_at": "ISO8601",
  "components": [
    {
      "name": "LLM 自命名（描述该组件的作用）",
      "category": "LLM 自分类（不限定枚举）",
      "files": ["该组件的实现文件路径"],
      "what_it_does": "LLM 描述该组件做了什么",
      "how_it_works": "LLM 描述实现机制",
      "is_standard": true | false,
      "standard_equivalent": "最接近的标准技术 | null",
      "cannot_substitute": true | false,
      "migration_risk": "critical | high | medium | low",
      "migration_risk_reason": "LLM 解释为什么是这个风险等级",
      "protocol_spec": { "...（自定义协议/加密/序列化组件必填）" }
    }
  ]
}
```

**Field notes:**
- `components[]` — LLM-discovered infrastructure components. LLM decides what qualifies as "infrastructure" based on reading the actual code, not matching package names
- `category` — LLM-assigned, free-form. Not limited to a fixed enum. Examples: communication, encryption, communication_encryption (cross-cutting), storage, cache, protocol, native_sdk, code_generation, state_management, search, queue, scheduling, distributed_lock, etc.
- `is_standard` — false for custom/proprietary implementations that have no standard library equivalent
- `cannot_substitute` — true when the component MUST be precisely replicated, not approximated. Critical for: encryption algorithms (wire format compatibility), custom protocols (client compatibility), native SDKs (vendor-specific)
- `migration_risk_reason` — LLM explains WHY this risk level, not just what level
- `protocol_spec` — **required for custom protocol/encryption/serialization components**. Structured specification: frame_format (field offsets, lengths, encodings), state_machine (transitions), test_vectors (verifiable input/output pairs). Enables target code verification without access to source runtime
- Cross-cutting components (e.g., communication + encryption in one layer) should be listed as a **single component** to preserve the coupling semantics

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
- `module` field: module ID (e.g., "M001") or `null` for root-level files (e.g., nginx.conf, routes.yaml, OpenAPI specs). Root-level config files often contain routing, permission, or infrastructure definitions that are critical for task/role/flow extraction
- `cross_cutting` — each entry may include `phase` field to describe execution ordering (e.g., OpenResty's access/content/log phases, Express middleware ordering). This helps stack-mapping translate phase-based middleware to chain-based middleware
- `dependency_map[]` — **LLM-generated** module dependency graph. Replaces cr_discover.py's mechanical import parsing, which only supports Go/JS/Python. LLM reads key_files and understands any language's import syntax (Lua require, Rust use, C# using, nginx include, etc.). Each entry:
  - `from` — source module ID
  - `to` — target module ID (or `null` for external/shared-state dependencies)
  - `via` — the actual import/require statement or reference mechanism
  - `type` — `direct_call` / `middleware` / `event` / `shared_state` / `config_ref`
  Phase 4 outer loop OL-D3 reads this field for cross-cutting coverage verification
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
    "containerization": "docker-compose",
    "upstream_services": [
      {"name": "user-service", "endpoints": ["10.0.1.1:8080"], "protocol": "http", "health_check": true}
    ],
    "shared_memory": [
      {"name": "rate_limit_counter", "mechanism": "ngx.shared.DICT", "size": "10m", "migration_note": "需要 Redis 替代"}
    ]
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
  "platform_adaptation": {
    "source_platform": "mobile",
    "target_platform": "desktop",
    "experience_priority_override": {
      "primary_experience": "desktop-web",
      "reasoning": ["Target is hospital WPF workstation, primary users are doctors/nurses"]
    },
    "ux_transformations": [
      {
        "source_pattern": "single_task_focus screens",
        "target_pattern": "multi_panel master-detail layout",
        "affected_screens": "all list+detail screen pairs"
      },
      {
        "source_pattern": "touch gestures (swipe, pull-to-refresh)",
        "target_pattern": "keyboard shortcuts + context menu + toolbar",
        "affected_screens": "all"
      },
      {
        "source_pattern": "full-screen page navigation",
        "target_pattern": "region-based navigation (e.g., Prism RegionManager)",
        "affected_screens": "all flow transitions"
      }
    ],
    "attention_threshold_override": {
      "max_steps_per_screen": 15,
      "context_switch_limit": 6,
      "reasoning": "Desktop users have higher sustained attention than mobile users"
    },
    "skip_source_features": [
      {"feature": "offline_cache", "reason": "Desktop has stable network"},
      {"feature": "gps_location", "reason": "Desktop has no GPS"}
    ]
  },
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
- `auto_mapped` — direct equivalences that need no user input. Each entry has `compatibility`: `flexible` (design choice, freely replaceable) or `exact` (protocol-level, must preserve wire behavior). Components communicating with existing servers default to `exact`
- `user_decisions` — multi-option scenarios where the user chose a target construct. Also has `compatibility` field
- `framework_builtins` — source hand-written code replaceable by target framework built-ins
- `unmapped` — constructs that could not be mapped (require manual resolution)
- `infrastructure_mapping[]` — **LLM-generated** mapping of each infrastructure-profile component to target stack equivalent. Fields:
  - `source` — component from infrastructure-profile (name + category)
  - `target` — target stack equivalent (or "需要重新实现" for custom components)
  - `cannot_substitute` — if true, must preserve exact behavior (e.g., custom encryption cannot be swapped for a "similar" algorithm)
  - `is_standard` — if false, no off-the-shelf library exists in target stack
  - `risk` — critical/high/medium/low
  - `migration_plan` — LLM's recommended approach (port source code / find equivalent library / rewrite to spec)
- `platform_adaptation` — **LLM-generated** when source and target platforms have different interaction models (mobile→desktop, desktop→mobile, web→native). Fields:
  - `source_platform` / `target_platform` — platform category (mobile / desktop / web / native)
  - `experience_priority_override` — overrides the source-inferred experience_priority for the target platform. dev-forge and cr-fidelity read this to adjust consumer maturity rules
  - `ux_transformations[]` — maps source UX patterns to target equivalents. dev-forge design-to-spec reads this to transform screen specs. Each entry has `source_pattern`, `target_pattern`, `affected_screens`
  - `attention_threshold_override` — adjusts attention management thresholds for target platform (desktop allows more steps/switches than mobile)
  - `skip_source_features[]` — source features that don't apply to target platform (e.g., GPS on desktop, offline cache on stable-network desktop). cr-fidelity excludes these from scoring
- `abstraction_mapping` — maps source code's reuse patterns to target stack equivalents. LLM generates this based on source-summary.abstractions + understanding of the target stack. Fields:
  - `source_abstraction` — name from source-summary.abstractions
  - `what_it_provides` — the behavior contract (stack-agnostic)
  - `source_mechanism` / `target_mechanism` — how reuse is implemented in each stack
  - `target_equivalent` — what the LLM recommends in the target stack
  - `migration_notes` — key differences that may cause semantic drift
  - `semantic_drift_risk` — LLM's assessment of how much behavior may change

---

## test-vectors.json

Verifiable input/output pairs extracted from source code for critical infrastructure components. Stored at `.allforai/code-replicate/test-vectors.json`. Generated in Phase 3 Step 3.5.5.

```json
{
  "generated_at": "ISO8601",
  "vectors": [
    {
      "component": "LLM 自命名",
      "source_file": "组件实现文件路径",
      "cases": [
        {
          "input": "测试输入数据",
          "expected_output": "期望的输出数据",
          "description": "LLM 从源码测试/常量中提取的用例描述"
        }
      ]
    }
  ]
}
```

**Field notes:**
- Only generated for components with `cannot_substitute: true` or `compatibility: exact`
- Test cases extracted from: source unit tests (priority 1), source constants/fixtures (priority 2), LLM-constructed from algorithm understanding (priority 3)
- cr-fidelity R3 uses these vectors to verify target implementation produces identical outputs
- dev-forge testforge can consume these to generate unit tests with known-good assertions (solves the "designing tests from answers" problem — these answers come from SOURCE code, not target)

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
- `dimensions` — each F1-F8 dimension has independent score, counts, and gap details
- `runtime` — R1-R4 runtime verification results: `R1_build`, `R2_smoke`, `R3_test_vectors`, `R4_protocol`. Each has `score`, `passed`, `detail`
- `F7_constraint` — null for non-exact fidelity levels
- `F8_infrastructure` — null when no infrastructure-profile exists
- `gaps[]` — each gap has `type` (CODE_FIX / ARTIFACT_GAP / DESIGN_DECISION), `description`, `affected_artifact`, `fix_status`
- `history` — score progression across rounds (for convergence tracking)
- `passed` — true when `overall_score >= threshold`
- Convergence control (CG-F): max 3 rounds, monotonic score increase required
