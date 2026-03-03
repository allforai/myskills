---
name: code-replicate
description: >
  Use when user wants to "replicate code", "clone a project", "copy functionality",
  "reverse engineer", "rewrite in another language/framework", "接口复刻", "代码复刻",
  "功能复刻", "百分百复刻", "跨技术栈复刻", "逆向工程", "迁移到新技术栈",
  "copy this codebase", "implement same as", "port to", "migrate from",
  "re-implement", "同款功能", "换技术栈实现", or mentions converting existing
  code to a different tech stack while preserving behavior.
version: "1.0.0"
---

# Code Replicate — 代码复刻

> 逆向工程桥梁：将已有代码转化为 `.allforai/` 产物，交还 dev-forge 流水线生成目标技术栈代码。

## 核心思路

```
已有代码（任意技术栈）
    ↓ 逆向分析（本技能）
.allforai/ 产物（product-design 兼容格式）
    ↓ dev-forge 流水线
目标技术栈代码（/design-to-spec → /task-execute）
```

**这不是又一个代码生成工具。** 本技能的唯一职责是将已有代码逆向为 allforai 产物，控制权交还给 dev-forge 的成熟基础设施。

---

## 信度等级（Fidelity Level）

| 等级 | 复刻什么 | 典型场景 |
|------|---------|---------|
| `interface` | API 合约（路由/参数/响应/状态码） | 后端重写，前端不动；接口兼容迁移 |
| `functional` | 业务行为（逻辑、数据流、错误处理） | 技术栈迁移，保留业务逻辑 |
| `architecture` | 模块结构、分层、依赖关系 | 大规模重构，保持架构决策 |
| `exact` | 百分百复刻，含 bug、边界用例 | 行为零容忍回归；监管合规 |

> 详见 `${CLAUDE_PLUGIN_ROOT}/docs/fidelity-guide.md`

---

## 增强协议（4D + 6V + XV）

> 通用框架见 `docs/information-fidelity.md`，以下仅列代码复刻方向的定制。

代码复刻中，**源码本身就是信息**。失真发生在三个环节：
1. **读取**：AI 对代码意图的推断可能偏离原作者意图（注释过时、命名误导）
2. **提取**：从代码到行为规格的转换中，约束和边界条件容易丢失
3. **映射**：跨栈转换时语义等价不代表行为等价（如 PHP Session → JWT 的状态语义差异）

### 4D 信息卡（提高维度）

每个提取的行为/端点/组件，除结论字段外，必须携带 4 层信息：

| 层 | 字段 | 代码复刻含义 |
|----|------|------------|
| **D1 结论层** | `description` | 这段代码做了什么 |
| **D2 证据层** | `source_refs` | 代码位置引用（`file:line`）+ 测试引用 + 文档引用 |
| **D3 约束层** | `constraints` | 代码内嵌的业务/技术约束（DB 唯一索引、校验规则、事务边界） |
| **D4 决策层** | `decision_rationale` | 为什么这样实现（已知时记录，未知时标注 `[INFERRED]`） |

**置信度标注**（写入 `confidence` 字段）：
- `confirmed` — D2 有代码 + 测试 + 文档三源支撑
- `partial` — D2 有代码 + 测试 或 代码 + 文档（二源）
- `code-only` — 仅有代码实现，附 `[UNTESTED]`
- `inferred` — 从上下文推断，无直接代码依据，附 `[INFERRED]`

**冲突标注**：代码与文档矛盾时，写入 `[CONFLICT:file:line vs file:line]` 并加入歧义 log，不停流程。

### 6V 视角矩阵（多视角）

高频/高风险行为（`frequency: high` 或 `risk_level: high`）需覆盖以下视角，防止单视角分析遗漏关键约束。**代码复刻语境下的 6V 定制**：

| 视角 | 在代码复刻中的含义 |
|------|-----------------|
| `user` | 这个行为对终端用户的可见效果（成功/失败/边界情况） |
| `business` | 实现了什么业务规则（隐含在代码里的业务逻辑） |
| `tech` | 技术实现细节 + 目标技术栈等价物（映射风险） |
| `ux` | 行为对 UI/交互的影响（前端/移动项目重点） |
| `data` | 数据模型影响（创建/修改/删除了什么数据，约束是什么） |
| `risk` | 若此行为在目标栈中实现有偏差，会发生什么（严重度） |

高风险对象（涉及支付/权限/数据完整性）必须覆盖 6/6 视角；普通对象 4/6 视角即可。

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

### XV 跨模型验证

> 通用机制见 `docs/information-fidelity.md` 第三节，以下为代码复刻定制。

**触发时机**：Step 2 完成后，自动执行（检测 `OPENROUTER_API_KEY` 环境变量）。

**代码复刻专用验证点**（2 次调用）：

| # | task_type | 发送内容 | 写入字段 |
|---|-----------|---------|---------|
| 1 | `behavior_completeness_review` | 源码技术栈 + 已提取的行为摘要清单 + 模块树 | `cross_model_review.missing_behaviors` |
| 2 | `cross_stack_risk_review` | 源栈 + 目标栈 + 已识别的映射关系 | `cross_model_review.mapping_risks` |

**Prompt 模板**：

调用 1（行为遗漏检测）：
```
源码技术栈: {source_stack}，模块: {module_list}
已提取行为数: {n}，行为清单摘要: {behavior_summary}

作为熟悉 {source_stack} 的工程师，请识别：
1. 常见于此技术栈但我可能遗漏的行为模式（如 middleware 副作用、ORM 事件钩子）
2. 任何"隐式行为"（框架自动处理但需在目标栈手动实现的部分）
限 300 字。
```

调用 2（跨栈语义漂移风险）：
```
迁移方向: {source_stack} → {target_stack}
已识别映射: {mapping_summary}

请指出此迁移中最容易发生语义漂移的 3-5 个点（不是一般建议，而是针对上述具体映射关系）。
限 300 字。
```

**自动采纳规则**（不问用户，直接修正数据）：
- `missing_behaviors` 中的遗漏项 → 直接追加到 `api-contracts.json` 或 `behavior-specs.json`，标注 `[XV:added]`，更新置信度为 `inferred`
- `mapping_risks` 中的高风险项（severity: high/critical）→ 直接修正对应端点的 `viewpoints.tech.mapping_risk` 字段为 `high`，并在 `constraints.risk` 中追加风险描述，标注 `[XV:risk_elevated]`
- `mapping_risks` 中的低风险项（severity: low/medium）→ 写入 `cross_model_review` 字段备查，不修改主数据
- `OPENROUTER_API_KEY` 不存在 → 静默跳过，流程不受影响
- API 调用失败 → 抛出异常，不静默吞错

**结果写入**：每个产出 JSON 文件顶层追加 `cross_model_review` 字段（结构见 `information-fidelity.md` 第三节）。

### 歧义收集规则

分析过程中遇到歧义 → 记入 `ambiguity_log`（含文件位置、失真类型、描述），**不停流程**。Step 3 汇总确认时一次性展示。

**唯一允许即时停止**：发现影响整体架构判断的致命歧义（如：无法确定项目是单体还是微服务），此时停下比产出错误产物代价更低。

---

## 工作流

```
Step 0: Preflight — 一次性收集所有参数 + 歧义处理策略 + 断点续作检测
    ↓ 用户确认后，以下步骤连续执行不停顿
Step 1: 源码解构（技术栈识别 + 模块树 + 代码规模）
    ↓ 不停
Step 2: 信度专项分析（按模式分支，歧义收集入 log）
    ↓ 不停
Step 2.5: [可选] 跨模型交叉校验（OpenRouter）
    ↓ 不停
Step 3: 汇总确认（展示所有歧义 + 映射决策，ONE-SHOT 用户输入）
    ↓ 收到用户输入后，连续执行不停顿
Step 4: 生成 allforai 产物
    ↓ 不停
Step 5: 交接 dev-forge（最终汇总报告）
```

**核心规则**：除 Step 0 Preflight 和 Step 3 汇总确认外，**所有步骤连续执行，不停顿，不询问。** 中间步骤的疑问收集到 Step 3 统一处理。

---

## Step 0：Preflight — 一次性收集所有参数

### 断点续作检测（优先）

检查 `.allforai/code-replicate/replicate-config.json` 是否存在：
- **存在** → 展示上次配置摘要（模式、路径、完成步骤），询问"从上次继续"还是"重新开始"
- **不存在** → 继续 Preflight

### 从命令行参数解析

若 `$ARGUMENTS` 非空，尝试解析 `mode` 和 `path`：
- 已知 mode（interface/functional/architecture/exact）→ 预填信度等级
- 已知 path → 预填源码路径

### 目标技术栈快速检测

检查 `.allforai/project-forge/project-manifest.json` 是否存在且有 `sub_projects`：
- **存在** → 读取目标技术栈，Preflight 时展示供确认
- **不存在** → 需用户输入

### Preflight 收集（AskUserQuestion，最多 4 题，一次性）

展示以下配置表，让用户确认或调整（参数从命令行/已有产物预填）：

```markdown
## Code Replicate — Preflight 配置

以下配置将在本次分析中全程使用，请确认后开始（可调整任意字段）：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 信度等级 | {预填或待选} | interface / functional / architecture / exact |
| 源码路径 | {预填或待填} | 要分析的代码目录 |
| 复刻范围 | full | full = 整个代码库；或填指定子目录列表 |
| 目标技术栈 | {预填或待填} | 从 project-manifest 读取或手动指定 |
| 歧义处理策略 | conservative | conservative = 遇歧义标注后继续；strict = 遇架构歧义即停 |
| exact 模式: bug 复刻默认 | replicate | replicate = 默认复刻所有 bug；fix = 默认修复；ask = 在 Step 3 逐一决策 |
```

用 `AskUserQuestion` 仅询问**缺失**的必填项（信度等级、源码路径、目标技术栈）。已知项不再询问。

### 写入配置

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

输出「✅ Preflight 完成，开始分析（Steps 1-2 连续执行，不停顿）」，自动继续。

---

## 项目类型感知分析

源码项目类型不同，逆向分析的重心截然不同。Step 1 完成技术栈识别后，**自动判定项目类型**，并在 Step 2 中调整分析重心。

### 项目类型检测特征

| 类型 | 检测特征 | 分析重心 |
|------|---------|---------|
| **后端 API** | `routes/`、`controllers/`、`middleware/`、`services/`、ORM 配置、`main.go/app.py/index.ts` 入口 | API 合约、业务逻辑、ORM 映射、中间件链 |
| **前端 Web** | `components/`、`pages/`、`store/`、`hooks/`、`src/app/`（Next.js）、路由配置文件 | 组件树、页面路由、状态管理、API 调用层 |
| **前端移动** | `screens/`、`widgets/`、`navigation/`、`pubspec.yaml`（Flutter）、`android/ios/` 目录 | 导航结构、状态管理、原生模块调用、平台差异 |
| **微服务** | `.proto` 文件、消息队列 consumer/producer、`saga/`、事件定义文件 | 服务契约（proto/schema）、消息格式、事件流、幂等性 |
| **混合单体** | 前后端混合（如 Django+React 同仓库、Rails+Vue）| 先拆分边界，再分别分析；在 Step 3 给出拆分建议 |

### 各类型 Step 2 分析调整

#### 后端 API 项目（标准模式）

执行默认 Step 2 分析（api-contracts → behavior-specs → arch-map）。

额外关注：
- 认证中间件链（JWT/Session/OAuth 如何注入）
- 数据库事务边界（哪些操作是原子的）
- 外部服务调用（第三方 API、消息队列 publish）

#### 前端 Web 项目

Step 2 调整为以下维度：

| 维度 | 分析内容 | 对应产物 |
|------|---------|---------|
| **组件树** | 页面 → 区域组件 → 原子组件层级，Props 接口 | `api-contracts.json`（以组件 Props 为"接口"） |
| **路由结构** | 所有路由路径、路由守卫、懒加载边界 | `arch-map.json` 路由层 |
| **状态管理** | Store 结构、action 类型、selector 模式 | `behavior-specs.json` 状态流 |
| **API 调用层** | 每个 API 调用点（service/hook 层） | `api-contracts.json` API 依赖清单 |
| **UI 状态** | Modal/Loading/Error 状态机 | `behavior-specs.json` UI 行为 |

> 特别注意：前端迁移时，"接口"有双重含义 — 组件 Props 接口（内部契约）和后端 API 调用（外部依赖）。两者都需要分析。

#### 前端移动项目（Flutter/React Native）

Step 2 额外关注：
- **导航结构**：页面栈、Tab 切换、深链接路由
- **平台差异**：platform-specific 代码块（`Platform.isIOS`、`dart:io`）→ 标注为跨栈映射决策点
- **原生模块调用**：相机、定位、推送、生物识别 → 加入 Step 3 映射决策
- **状态持久化**：SharedPreferences/Hive/AsyncStorage 等 → 目标平台等价物

#### 微服务项目

Step 2 替换为服务契约分析：

| 维度 | 分析内容 | 对应产物 |
|------|---------|---------|
| **服务契约** | gRPC proto 定义 / REST API / GraphQL schema | `api-contracts.json`（服务间接口） |
| **消息格式** | 消息队列 payload 结构、topic 命名、序列化格式 | `behavior-specs.json` 消息流 |
| **事件定义** | 领域事件 schema、事件版本、消费者清单 | `arch-map.json` 事件流 |
| **幂等性** | 哪些操作有幂等保障，幂等键策略 | `behavior-specs.json` |
| **服务依赖图** | 服务间调用关系、循环依赖检测 | `arch-map.json` |

#### 混合单体项目

Step 1 完成后**先给出拆分建议**（加入 Step 3 汇总确认）：

```markdown
### 检测到混合单体项目

检测到前后端代码混合在同一仓库：
- 后端部分：{path}（{backend_stack}）
- 前端部分：{path}（{frontend_stack}）

建议：分别对两部分进行独立分析。
是否在 Step 3 确认拆分策略？
```

---

## Step 1：源码解构（自动执行，不停顿）

### 1a. 技术栈识别

扫描以下文件识别技术栈（优先顺序：依赖文件 > 目录结构 > 文件扩展名）：

| 文件 | 技术栈 |
|------|--------|
| `package.json` | Node.js；框架从 dependencies 推断 |
| `requirements.txt` / `pyproject.toml` | Python；框架从依赖推断 |
| `go.mod` | Go；框架从 import 路径推断 |
| `pom.xml` / `build.gradle` | Java/Kotlin |
| `composer.json` | PHP Laravel/Symfony |
| `Gemfile` | Ruby on Rails |
| `pubspec.yaml` | Dart/Flutter |
| `Cargo.toml` | Rust |

记录到 `source_analysis.json` 的 `source_stack` 字段，附证据 `[CONFIRMED:file]`。

### 1b. 模块树提取

扫描目录结构，对每个模块生成：
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

### 1c. 代码规模评估

统计：总文件数、代码行数（估算）、路由数量（估算）、模块数量。

写入 `.allforai/code-replicate/source-analysis.json`，输出进度「Step 1 ✓ {N} 模块 | {N}± 路由 | {source_stack}」，自动继续 Step 2。

---

## Step 2：信度专项分析（自动执行，不停顿）

按信度等级叠加执行（每个模式包含上一级全部内容）。所有歧义收集到内部 `ambiguity_log`，不停下询问。

### 所有模式：API 合约分析 → `api-contracts.json`

对每个路由文件提取（含 4D 字段）：

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

### functional 模式加：行为规格分析 → `behavior-specs.json`

对每个 Service 函数提取业务逻辑路径（含 4D + 6V 字段）：

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

### architecture 模式加：架构地图 → `arch-map.json`

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

发现架构歧义（如：无法确定是否有多个入口点） → 若 `ambiguity_policy = strict` 且影响架构走向 → 即时停下询问；否则标注加入 log 继续。

---

### exact 模式加：Bug 注册表 → `bug-registry.json`

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

### Step 2 完成

写入所有 JSON 文件，更新 `replicate-config.json`，输出进度「Step 2 ✓ {N} 端点 | {N} 行为 | {N} 歧义待确认」，自动继续 Step 2.5（或 Step 3）。

---

## Step 2.5：XV 跨模型验证（自动执行）

检测 `OPENROUTER_API_KEY` 环境变量：
- **存在** → 执行 2 次跨模型调用（见「增强协议 → XV」段落），自动继续
- **不存在** → 静默跳过，流程不受影响

**行为遗漏检测**（调用 1）→ 将遗漏行为追加到 `api-contracts.json` / `behavior-specs.json`，标注 `[XV:added]`。

**跨栈语义漂移风险**（调用 2）→ 高风险项直接修正产物中对应端点的 `mapping_risk` 字段并追加 `constraints.risk`，标注 `[XV:risk_elevated]`；不加入 Step 3 决策列表，不问用户。

自动继续 Step 3。

---

## Step 3：汇总确认（ONE-SHOT 用户输入）

这是 Step 0 之后**唯一一次停下来询问用户**的环节。将所有待决策项一次性呈现。

### 3a. 歧义报告

展示 ambiguity_log 中的所有项目（若有）：

```markdown
## 分析发现 {N} 个歧义/风险点

| # | 位置 | 类型 | 描述 | 建议处理 |
|---|------|------|------|---------|
| 1 | user.service.ts:87 | [CONFLICT] | 状态码代码返回 500，文档写 400 | 以代码为准 |
| 2 | auth.service.ts:23 | [INFERRED] | JWT 过期时间从代码推断为 7d，无配置文件 | 确认后继续 |
| 3 | order.service.ts | [UNTESTED] | 订单超时取消逻辑无测试覆盖 | 标注并继续 |
```

若用户无异议，建议默认处理（以代码为准、标注继续）。

### 3b. 跨栈映射决策（多方案可选项）

> 详细映射规则见 `${CLAUDE_PLUGIN_ROOT}/docs/stack-mappings.md`

分析 Step 1-2 中发现的所有需要决策的构造，**一次性**展示全部：

```markdown
## 需要你决策的跨栈映射（{N} 项）

### 决策 1：异步任务队列

源码使用: Python Celery（src/tasks/email_tasks.py）

| 方案 | 描述 | 优势 | 劣势 | 复杂度 |
|------|------|------|------|--------|
| A: asynq（推荐） | Redis 后端，Go 原生 | 轻量，生产可用 | 仅 Go | 低 |
| B: goroutine + channel | 零依赖 | 极简 | 无持久化，重启丢任务 | 低 |
| C: machinery | 多后端 | 功能丰富 | 配置复杂 | 高 |

### 决策 2：会话管理
...（每个决策项同样格式）
```

### 3c. exact 模式：Bug 复刻决策（仅 `bug_replicate_default = ask`）

逐一展示需要用户决策的 bug，用 `AskUserQuestion` 一次性收集所有 bug 决策。

### 汇总 AskUserQuestion

将 3a/3b/3c 中需要用户输入的问题，合并成**最多 4 个** `AskUserQuestion` 调用（选项化，不开放填写），收集用户决策。

无需决策的项（歧义用默认处理、无复杂映射）→ 直接跳过，展示「无待确认项，直接继续」。

### 写入决策

将所有用户决策写入 `.allforai/code-replicate/stack-mapping-decisions.json`（持久化，下次重跑复用）：

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

输出「Step 3 ✓ {N} 个映射决策，{N} 个歧义已处理，继续生成产物（不停顿）」，自动继续 Step 4。

---

## Step 4：生成 allforai 产物（自动执行，不停顿）

将分析结果转写为 product-design 兼容格式。

### 4a. `product-map/task-inventory.json`（所有模式）

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

### 4b. `product-map/business-flows.json`（functional+ 模式）

从 `behavior-specs.json` 提取，转换为 product-map 兼容格式（与 `/product-map` 产出结构一致）。

### 4c. `use-case/use-case-tree.json`（functional+ 模式）

从业务行为生成用例树，格式兼容 product-design `use-case/` 目录。

### 4d. `product-map/constraints.json`（exact 模式）

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

### 4e. `code-replicate/stack-mapping.json`

完整映射记录（自动映射 + 用户决策 + 架构决策）：

```json
{
  "source_stack": "express-typescript",
  "target_stack": "go-gin",
  "auto_mapped": [
    { "source_construct": "Express router.get()", "target_construct": "Gin r.GET()", "rule": "express-to-gin-route" }
  ],
  "user_decisions": [...],
  "arch_decisions": [...],
  "unmapped": [],
  "created_at": "ISO8601"
}
```

### 4f. `code-replicate/replicate-report.md`

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

写入所有产物文件，更新 `replicate-config.json`，自动继续 Step 5。

---

## Step 5：交接 dev-forge（最终输出）

```markdown
## ✅ 复刻分析完成

| 产物 | 状态 | 数量 |
|------|------|------|
| `.allforai/product-map/task-inventory.json` | ✅ | {N} tasks |
| `.allforai/product-map/business-flows.json` | ✅ / - | functional+ |
| `.allforai/product-map/constraints.json` | ✅ / - | exact |
| `.allforai/use-case/use-case-tree.json` | ✅ / - | functional+ |
| `.allforai/code-replicate/source-analysis.json` | ✅ | |
| `.allforai/code-replicate/api-contracts.json` | ✅ | {N} endpoints |
| `.allforai/code-replicate/replicate-report.md` | ✅ | |

**信息失真风险点**：{N} 个（详见 replicate-report.md）

---

**下一步（dev-forge 流水线）**：

若尚未选择目标技术栈，先运行 `/project-setup`。

```
/design-to-spec   ← 读取上述产物，生成目标技术栈的实现规格（需指定目标技术栈）
/task-execute     ← 逐任务生成代码
```
```

---

## 输出文件完整清单

```
.allforai/
├── product-map/
│   ├── task-inventory.json          ← 所有模式
│   ├── business-flows.json          ← functional/architecture/exact
│   └── constraints.json             ← exact
├── use-case/
│   └── use-case-tree.json           ← functional/architecture/exact
└── code-replicate/
    ├── replicate-config.json        ← 配置 + 进度追踪
    ├── source-analysis.json         ← Step 1
    ├── api-contracts.json           ← Step 2（所有模式）
    ├── behavior-specs.json          ← Step 2（functional+）
    ├── arch-map.json                ← Step 2（architecture+）
    ├── bug-registry.json            ← Step 2（exact）
    ├── stack-mapping.json           ← Step 4
    ├── stack-mapping-decisions.json ← Step 3 决策（持久化）
    └── replicate-report.md          ← Step 4 人类可读摘要
```

---

## 五条铁律

### 1. Preflight 一次收齐，中途不再询问

所有参数在 Step 0 收齐。中间步骤的问题收集到 Step 3 一次性处理。消灭"分析到一半停下来问"的体验。

### 2. 证据优先，结论必须可追溯

每个分析结论附代码位置引用。无法追溯的结论标注 `[INFERRED]` 并降级置信度，不当作确定事实处理。

### 3. 歧义收集，汇总处理，不拦截流程

分析过程中发现歧义 → 记入 log 继续 → Step 3 一次性展示。唯一例外：影响整体架构走向的致命歧义（strict 模式下）。

### 4. 决策持久化，跨 session 复用

`stack-mapping-decisions.json` 持久存储。下次重跑时优先复用历史决策，相同构造不再重复询问。

### 5. 只产出 allforai 产物，不直接生成代码

本技能的边界是 `.allforai/` 目录。代码生成由 dev-forge 负责。用户要求直接生成代码时，引导完成本技能流程后使用 `/task-execute`。
