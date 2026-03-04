# Schema Reference — 代码复刻产物 JSON 格式

> 本文件供按需加载。skills/code-replicate.md 中以 `> 详见` 引用。

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
  "fidelity": "interface | functional | architecture | exact",
  "source_path": "相对路径或绝对路径",
  "scope": "full",
  "target_stack": "go-gin | nestjs | ...",
  "ambiguity_policy": "conservative | strict",
  "bug_replicate_default": "replicate | fix | ask",
  "steps_completed": [],
  "last_updated": "ISO8601"
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
    "tech": { "current": "NestJS + TypeORM", "target_equivalent": "待 Step 3 决策", "mapping_risk": "low" },
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
    "tech": { "current": "nestjs-mailer 异步", "target_equivalent": "goroutine + 邮件 SDK [待 Step 3]", "mapping_risk": "low" },
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

若 `bug_replicate_default = ask` → 将每个 bug 的决策加入 Step 3 的"待确认列表"，不即时停下。

---

## Step 4 产物格式

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

### stack-mapping-decisions.json（Step 3 决策持久化）

```json
{
  "decisions": [
    {
      "source_construct": "Python Celery task queue",
      "target_construct": "asynq",
      "rationale": "用户选择 A",
      "decided_at": "ISO8601",
      "reusable": true
    }
  ],
  "ambiguity_resolutions": [
    { "ambiguity_id": "AMB001", "resolution": "以代码为准", "decided_at": "ISO8601" }
  ]
}
```

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
