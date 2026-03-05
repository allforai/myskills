# Schema Reference — 代码复刻产物 JSON 格式

> 本文件供按需加载。skills/code-replicate-core.md、cr-backend.md、cr-frontend.md、cr-fullstack.md、cr-module.md 中以 `> 详见` 引用。

---

## 6V 视角 JSON 结构

```json
{
  "viewpoints": {
    "user": { "success": "...", "failure": "...", "edge": "..." },
    "business": { "rule": "...", "enforcement": "..." },
    "tech": { "current": "...", "target_equivalent": "...", "mapping_risk": "low|medium|high" },
    "ux": { "impact": "...", "skip_if": "纯 API 项目" },
    "data": { "creates": "...", "modifies": "...", "constraint": "..." },
    "risk": { "if_wrong": "...", "severity": "low|medium|high|critical" }
  }
}
```

---

## replicate-config.json

```json
// .allforai/code-replicate/replicate-config.json
{
  "version": "1.0.0",
  "created_at": "ISO8601",
  "project_type": "backend | frontend | fullstack",
  "fidelity": "interface | functional | architecture | exact",
  "source_path": "相对路径或绝对路径（本地）",
  "source_url": "远程 git URL（HTTPS/SSH，可追加 #branch/#tag/#sha；clone 后 source_path 指向临时目录）",
  "source_ref": "分支/tag/commit（从 source_url 的 # 后解析，无则为默认分支）",
  "clone_depth": "shallow | full（浅克隆或完整历史，按需升级）",
  "scope": "full | modules | feature",
  "scope_detail": "modules 时为目录列表 [\"src/user\", \"src/order\"]；feature 时为功能描述字符串",
  "scope_filter": {
    "included_modules": ["实际纳入分析的模块 ID 列表"],
    "excluded_modules": ["排除的模块 ID 列表"],
    "reason": "各模块纳入/排除原因"
  },
  "analysis_granularity": "fine | standard | coarse（由范围规模自动决定）",
  "business_direction": "replicate | slim | extend（1:1复刻 / 精简 / 扩展）",
  "target_stack": "go-gin | nestjs | ...",
  "ambiguity_policy": "conservative | strict",
  "bug_replicate_default": "replicate | fix | ask",
  "steps_completed": [],
  "last_updated": "ISO8601",

  // fullstack 模式额外字段
  "backend_path": "后端代码目录（相对于源码根目录，fullstack 模式）",
  "frontend_path": "前端代码目录（相对于源码根目录，fullstack 模式）",
  "backend_target_stack": "后端目标技术栈（fullstack 模式）",
  "frontend_target_stack": "前端目标技术栈（fullstack 模式）",

  // cr-module 模式额外字段
  "module_boundary_decisions": [
    {
      "module": "外部模块名",
      "decision": "include | external_interface | event_contract | prerequisite",
      "reason": "决策原因"
    }
  ]
}
```

---

## 模块树条目（source-analysis.json 内）

```json
{
  "id": "M001",
  "name": "user",
  "path": "src/modules/user",
  "inferred_responsibility": "用户账户管理（注册/登录/资料）",
  "confidence": "high | medium | low",
  "evidence": "[CONFIRMED:src/modules/user/user.controller.ts]",
  "key_files": ["user.controller.ts", "user.service.ts"]
}
```

模块职责无法确定时：标注 `"confidence": "low"` + `[INFERRED]`，加入歧义 log，**不停下询问**。

---

## api-contracts.json — 端点条目（含 4D + 6V）

```json
{
  "endpoint_id": "EP001",
  "method": "POST",
  "path": "/api/v1/users/register",
  "source_file": "src/modules/user/user.controller.ts",
  "source_line": 42,
  "auth_required": false,
  "request": {
    "body": {
      "email": { "type": "string", "required": true, "format": "email" },
      "password": { "type": "string", "required": true, "minLength": 8 }
    }
  },
  "responses": [
    { "status": 201, "description": "注册成功", "schema": { "token": "string" } },
    { "status": 400, "description": "参数错误" },
    { "status": 409, "description": "邮箱已存在" }
  ],
  "confidence": "confirmed | partial | code-only | inferred",
  "source_refs": [
    "[CONFIRMED:src/modules/user/user.controller.ts:42]",
    "[CONFIRMED:src/modules/user/user.spec.ts:15]"
  ],
  "constraints": {
    "business": ["邮箱全局唯一（DB unique index）"],
    "technical": ["密码 bcrypt hash rounds=10（硬编码）"],
    "risk": ["注册不限频次，无 rate limiting"]
  },
  "decision_rationale": "返回 409 而非 400 区分参数错误和冲突，符合 REST 语义 [INFERRED]",
  "viewpoints": {
    "user": { "success": "获得 JWT token，直接登录", "failure": "409 提示邮箱已存在" },
    "business": { "rule": "一邮箱一账号", "enforcement": "DB 唯一约束 + 代码层 ConflictException" },
    "tech": { "current": "NestJS + TypeORM", "target_equivalent": "待 Phase 3 确认", "mapping_risk": "low" },
    "data": { "creates": "users 表一行", "constraint": "email UNIQUE" },
    "risk": { "if_wrong": "允许重复邮箱注册，账号系统混乱", "severity": "high" }
  }
}
```

若响应状态码与实际异常处理不一致 → 标注 `[CONFLICT]`，加入 ambiguity_log，**不停下**。

---

## behavior-specs.json — 行为条目（含 4D + 6V）

> functional+ 模式使用。

```json
{
  "behavior_id": "BH001",
  "name": "用户注册",
  "source_file": "src/modules/user/user.service.ts",
  "source_line": 15,
  "flow": [
    { "step": 1, "action": "检查邮箱是否已存在", "condition": "if exists → throw ConflictException" },
    { "step": 2, "action": "密码 bcrypt hash（rounds=10）", "note": "hardcoded rounds [INFERRED:no config ref]" },
    { "step": 3, "action": "写入数据库", "transaction": false },
    { "step": 4, "action": "生成 JWT token", "detail": "expires 7d [CONFIRMED:auth.service.ts:23]" },
    { "step": 5, "action": "发送欢迎邮件（异步，不阻塞）", "side_effect": true }
  ],
  "error_handling": [
    { "error": "ConflictException", "trigger": "邮箱已存在", "http_status": 409 }
  ],
  "confidence": "confirmed",
  "source_refs": [
    "[CONFIRMED:src/modules/user/user.service.ts:15]",
    "[CONFIRMED:src/modules/user/user.service.spec.ts:23]"
  ],
  "constraints": {
    "business": ["邮箱不可重复注册"],
    "technical": ["欢迎邮件异步发送，注册响应不等邮件结果"],
    "risk": ["邮件失败不回滚注册（副作用与主流程解耦）"]
  },
  "decision_rationale": "邮件异步是有意设计，避免邮件服务不可用阻塞注册 [INFERRED:try-catch 包裹邮件调用]",
  "viewpoints": {
    "user": { "success": "收到欢迎邮件（最终一致）", "failure": "注册成功但邮件可能延迟/丢失" },
    "business": { "rule": "注册即激活，不需邮件确认", "enforcement": "无邮件验证步骤" },
    "tech": { "current": "nestjs-mailer 异步", "target_equivalent": "goroutine + 邮件 SDK [待 Phase 3]", "mapping_risk": "low" },
    "data": { "creates": "users 行 + email_log 行（异步）" },
    "risk": { "if_wrong": "若目标栈同步发邮件，注册 P99 延迟暴增", "severity": "medium" }
  }
}
```

无测试覆盖的行为 → 标注 `[UNTESTED]`，加入 ambiguity_log，继续。

---

## arch-map.json — 架构地图（architecture+ 模式）

```json
{
  "layers": [
    { "name": "Controller", "path_pattern": "src/modules/*/controller.ts", "responsibility": "HTTP 处理、DTO 验证" },
    { "name": "Service", "path_pattern": "src/modules/*/service.ts", "responsibility": "业务逻辑" },
    { "name": "Repository", "path_pattern": "src/modules/*/repository.ts", "responsibility": "数据访问" }
  ],
  "patterns_detected": [
    { "pattern": "Repository Pattern", "evidence": "[CONFIRMED:src/modules/*/repository.ts]" },
    { "pattern": "DTO Validation", "evidence": "[CONFIRMED:class-validator decorators]" }
  ],
  "dependencies": [
    { "from": "OrderService", "to": "UserService", "type": "constructor injection",
      "concern": "跨模块依赖，可能有循环风险 [INFERRED]" }
  ],
  "cross_cutting": {
    "logging": "winston，middleware 层统一注入 [CONFIRMED:src/middleware/logger.ts]",
    "auth": "JWT Guard 装饰器，Controller 层 [CONFIRMED]",
    "caching": "未检测到"
  }
}
```

发现架构歧义 → 若 `ambiguity_policy = strict` 且影响架构走向 → 即时停下询问；否则标注加入 log 继续。

---

## bug-registry.json — Bug 注册表（exact 模式）

```json
{
  "bugs": [
    {
      "bug_id": "BUG001",
      "type": "off-by-one",
      "location": "src/modules/product/product.service.ts:87",
      "description": "分页从 0 开始（page=0 返回第一页），API 文档说从 1 开始",
      "evidence": "[CONFLICT:src/product.service.ts:87 vs swagger/openapi.yaml:134]",
      "confidence": "confirmed",
      "evidence_sources": ["code", "doc"],
      "replicate_decision": "{从 replicate-config.bug_replicate_default 预填}"
    }
  ]
}
```

若 `bug_replicate_default = ask` → 将每个 bug 的决策加入 Phase 5 的"待确认列表"，不即时停下。

---

## Phase 6 产物格式

### task-inventory.json（所有模式）

每个 API 端点 → 一个任务：

```json
{
  "tasks": [
    {
      "task_id": "T001",
      "task_name": "用户注册",
      "module": "user",
      "source_endpoint": "POST /api/v1/users/register",
      "source_file": "src/modules/user/user.controller.ts:42",
      "task_type": "CRUD",
      "frequency": "high",
      "risk_level": "medium",
      "replicate_fidelity": "functional",
      "api_contract_ref": "EP001",
      "behavior_spec_ref": "BH001"
    }
  ]
}
```

### constraints.json（exact 模式）

将 `bug-registry.json` 中 `replicate_decision: "replicate"` 的 bug 转为约束：

```json
{
  "constraints": [
    {
      "constraint_id": "CN001",
      "source_bug": "BUG001",
      "description": "分页从 0 开始（客户端依赖此行为，不可修改）",
      "enforcement": "hard",
      "affects": ["T003", "T007"]
    }
  ]
}
```

### stack-mapping.json

完整映射记录（自动映射 + 用户决策 + 架构决策）：

```json
{
  "source_stack": "express-typescript",
  "target_stack": "go-gin",
  "auto_mapped": [
    { "source_construct": "Express router.get()", "target_construct": "Gin r.GET()", "rule": "express-to-gin-route" }
  ],
  "user_decisions": [],
  "arch_decisions": [],
  "unmapped": [],
  "created_at": "ISO8601"
}
```

### stack-mapping-decisions.json（Phase 5 决策持久化）

```json
{
  "decisions": [
    {
      "source_construct": "Python Celery task queue",
      "target_construct": "asynq",
      "rationale": "用户选择 A",
      "semantic_drift_risk": "low | medium | high",
      "drift_details": "可选，XV 审查后补充的漂移说明",
      "decided_at": "ISO8601",
      "reusable": true
    }
  ],
  "ambiguity_resolutions": [
    { "ambiguity_id": "AMB001", "resolution": "以代码为准", "decided_at": "ISO8601" }
  ],
  "cross_model_review": {
    "mapping_decision_issues": [
      {
        "task_type": "mapping_decision_review",
        "model": "deepseek",
        "issues": [
          {
            "type": "suboptimal_choice | risk_underestimate | missing_mapping",
            "target_decision": "对应的 source_construct（suboptimal/risk_underestimate 时）",
            "description": "问题描述",
            "action_taken": "[XV:risk_elevated] | [XV:added]"
          }
        ],
        "reviewed_at": "ISO8601"
      }
    ]
  }
}
```

---

## Fullstack 交叉验证产物（fullstack 模式）

### api-bindings.json — API 绑定分析

```json
{
  "bindings": [
    {
      "binding_id": "BIND001",
      "frontend_call": {
        "file": "src/services/userApi.ts",
        "line": 23,
        "method": "POST",
        "url": "/api/v1/users/register",
        "request_shape": { "email": "string", "password": "string" },
        "response_shape": { "token": "string" }
      },
      "backend_endpoint": {
        "endpoint_id": "EP001",
        "file": "src/modules/user/user.controller.ts",
        "line": 42,
        "method": "POST",
        "path": "/api/v1/users/register",
        "request_shape": { "email": "string", "password": "string", "name": "string" },
        "response_shape": { "token": "string", "user": "object" }
      },
      "status": "matched | unmatched_frontend | unmatched_backend",
      "shape_mismatches": [
        {
          "direction": "request | response",
          "field": "name",
          "issue": "后端要求 name 字段（required），前端未发送",
          "severity": "high | medium | low"
        }
      ]
    }
  ],
  "summary": {
    "total_frontend_calls": 0,
    "total_backend_endpoints": 0,
    "matched": 0,
    "unmatched_frontend": 0,
    "unmatched_backend": 0,
    "shape_mismatches": 0
  }
}
```

### schema-alignment.json — 数据 Schema 对齐

```json
{
  "alignments": [
    {
      "entity": "User",
      "backend_source": {
        "file": "src/entities/user.entity.ts",
        "fields": [
          { "name": "id", "type": "number", "nullable": false },
          { "name": "email", "type": "string", "nullable": false },
          { "name": "password_hash", "type": "string", "nullable": false },
          { "name": "created_at", "type": "timestamp", "nullable": false }
        ]
      },
      "frontend_source": {
        "file": "src/types/user.ts",
        "fields": [
          { "name": "id", "type": "number" },
          { "name": "email", "type": "string" },
          { "name": "createdAt", "type": "number" }
        ]
      },
      "field_alignment": [
        { "backend": "id", "frontend": "id", "status": "aligned" },
        { "backend": "email", "frontend": "email", "status": "aligned" },
        { "backend": "password_hash", "frontend": null, "status": "backend_only", "note": "内部字段，不应暴露给前端" },
        { "backend": "created_at", "frontend": "createdAt", "status": "type_mismatch", "issue": "后端 timestamp vs 前端 number；命名 snake_case vs camelCase" }
      ]
    }
  ],
  "summary": {
    "total_entities": 0,
    "total_fields": 0,
    "aligned": 0,
    "type_mismatch": 0,
    "backend_only": 0,
    "frontend_only": 0
  }
}
```

### constraint-reconciliation.json — 约束一致性

```json
{
  "constraints": [
    {
      "constraint_id": "CR001",
      "rule": "邮箱全局唯一",
      "enforcement": {
        "db": { "present": true, "detail": "users.email UNIQUE INDEX", "source": "migration/001_create_users.sql:5" },
        "backend": { "present": true, "detail": "ConflictException on duplicate", "source": "user.service.ts:23" },
        "frontend": { "present": true, "detail": "实时邮箱可用性检查", "source": "RegisterForm.tsx:45" }
      },
      "coverage": "full | partial | single_layer",
      "gap_risk": "none | acceptable | risky",
      "note": "全层覆盖，无缺口"
    }
  ],
  "summary": {
    "total_rules": 0,
    "full_coverage": 0,
    "partial_coverage": 0,
    "single_layer": 0,
    "risky_gaps": 0
  }
}
```

### auth-propagation.json — 认证流程追踪

```json
{
  "auth_flow": {
    "backend": {
      "token_issue": {
        "endpoint": "POST /api/auth/login",
        "source": "auth.service.ts:15",
        "token_type": "JWT",
        "expiry": "7d",
        "refresh_supported": true
      },
      "token_verify": {
        "mechanism": "JWT Guard middleware",
        "source": "auth.guard.ts:10",
        "protected_routes": "所有 /api/* 路由（除 /auth/login, /auth/register）"
      },
      "token_refresh": {
        "endpoint": "POST /api/auth/refresh",
        "source": "auth.controller.ts:45",
        "strategy": "refresh token rotation"
      },
      "token_revoke": {
        "endpoint": "POST /api/auth/logout",
        "source": "auth.controller.ts:60",
        "strategy": "token blacklist（Redis TTL）"
      }
    },
    "frontend": {
      "token_store": {
        "mechanism": "localStorage",
        "source": "utils/auth.ts:8",
        "security_note": "XSS 风险 — 建议改用 httpOnly cookie"
      },
      "token_inject": {
        "mechanism": "Axios interceptor（Authorization: Bearer）",
        "source": "services/api.ts:12"
      },
      "token_refresh": {
        "mechanism": "401 拦截 → 自动调用 refresh → 重试原请求",
        "source": "services/api.ts:25",
        "implemented": true
      },
      "token_clear": {
        "mechanism": "localStorage.removeItem on logout",
        "source": "store/auth.ts:34"
      }
    },
    "breakpoints": [
      {
        "location": "token 存储",
        "issue": "前端使用 localStorage，后端未设置 httpOnly cookie",
        "severity": "medium",
        "recommendation": "迁移时考虑使用 httpOnly cookie + CSRF token"
      }
    ]
  }
}
```

### error-mapping.json — 错误处理对齐

```json
{
  "mappings": [
    {
      "http_status": 409,
      "backend_source": {
        "exception": "ConflictException",
        "triggers": ["邮箱已存在", "用户名已占用"],
        "source_files": ["user.service.ts:23", "user.service.ts:45"]
      },
      "frontend_handling": {
        "handled": true,
        "handler": "catch block in RegisterForm",
        "source": "RegisterForm.tsx:67",
        "user_feedback": "显示'邮箱已被注册'提示"
      },
      "status": "handled | unhandled | no_backend_source"
    }
  ],
  "summary": {
    "total_error_codes": 0,
    "handled": 0,
    "unhandled": 0,
    "no_backend_source": 0,
    "has_generic_fallback": true
  }
}
```

### infrastructure.json — 基础设施行为

```json
{
  "services": [
    {
      "name": "backend-api",
      "source": "docker-compose.yml",
      "image": "node:18-alpine",
      "ports": ["3000:3000"],
      "env_vars": ["DATABASE_URL", "JWT_SECRET", "REDIS_URL"],
      "depends_on": ["postgres", "redis"],
      "volumes": ["./backend:/app"]
    }
  ],
  "reverse_proxy": {
    "type": "nginx",
    "source": "nginx.conf",
    "routes": [
      { "path": "/api/*", "upstream": "backend-api:3000" },
      { "path": "/*", "upstream": "frontend:8080" }
    ],
    "cors_config": {
      "origins": ["http://localhost:3000"],
      "methods": ["GET", "POST", "PUT", "DELETE"],
      "credentials": true
    }
  },
  "cron_jobs": [
    {
      "schedule": "0 2 * * *",
      "command": "node scripts/daily-report.js",
      "source": "crontab",
      "description": "每日凌晨2点生成报表"
    }
  ],
  "env_vars": [
    { "key": "DATABASE_URL", "usage": "PostgreSQL 连接字符串", "used_by": ["backend"] },
    { "key": "JWT_SECRET", "usage": "JWT 签名密钥", "used_by": ["backend"] },
    { "key": "NEXT_PUBLIC_API_URL", "usage": "前端 API 地址", "used_by": ["frontend"] }
  ]
}
```

---

## Module 边界产物（cr-module 模式）

### module-boundaries.json — 模块依赖边界

```json
{
  "target_modules": ["user"],
  "external_dependencies": [
    {
      "module": "auth",
      "decision": "include | external_interface | event_contract | prerequisite",
      "interfaces_used": [
        {
          "name": "AuthService.validateToken",
          "signature": "(token: string) => Promise<User>",
          "source_file": "src/modules/auth/auth.service.ts",
          "source_line": 42
        }
      ]
    }
  ],
  "event_contracts": [
    {
      "event": "UserCreated",
      "direction": "publish | subscribe",
      "source_file": "src/modules/user/user.service.ts",
      "source_line": 67,
      "payload_schema": {
        "userId": "string",
        "email": "string",
        "createdAt": "ISO8601"
      },
      "consumers": ["order", "analytics", "notification"]
    }
  ],
  "shared_dependencies": [
    {
      "name": "AuthGuard",
      "type": "middleware | shared_type | config | database_relation",
      "source_file": "src/common/guards/auth.guard.ts",
      "decision": "include | prerequisite"
    }
  ],
  "database_relations": [
    {
      "source_table": "users",
      "target_table": "orders",
      "relation_type": "one-to-many | many-to-many | one-to-one",
      "foreign_key": "orders.user_id → users.id",
      "decision": "document_relation"
    }
  ]
}
```

---

### replicate-report.md 模板

```markdown
# 代码复刻报告

## 基本信息

| 项目 | 值 |
|------|----|
| 源码路径 | {source_path} |
| 源技术栈 | {source_stack} |
| 目标技术栈 | {target_stack} |
| 信度等级 | {fidelity} |
| 分析时间 | {datetime} |

## 分析结果摘要

- API 端点: {N} 个（confirmed: {N}, partial: {N}, code-only: {N}）
- 业务行为: {N} 个（functional+ 模式）
- 架构模式: {list}（architecture+ 模式）
- 发现 bug: {N} 个，复刻: {N}，修复: {N}（exact 模式）

## 信息失真风险点

| 类型 | 位置 | 描述 | 处理方式 |
|------|------|------|---------|
| [CONFLICT] | ... | ... | 以代码为准 |
| [INFERRED] | ... | ... | 标注，低置信度 |
| [UNTESTED] | ... | ... | 标注，待补测试 |

## 跨栈映射决策

### 自动映射（{N} 项）
...

### 用户决策（{N} 项）
...

## 下一步

已生成 {N} 个任务到 `.allforai/product-map/task-inventory.json`。

使用 dev-forge 流水线继续：
- `/design-to-spec`   ← 生成目标技术栈实现规格
- `/task-execute`     ← 逐任务生成代码
```
