---
name: code-replicate-core
description: >
  Internal shared protocol for code replication. Do NOT invoke directly —
  loaded by cr-backend.md, cr-frontend.md, cr-fullstack.md, or cr-module.md.
  Contains 4D/6V/XV protocols, Preflight, Phase 1-7 workflow, iron rules,
  and output file spec.
version: "1.0.0"
---

# Code Replicate Core — 共享协议

> 内部技能，不直接触发。由 `cr-backend.md`、`cr-frontend.md`、`cr-fullstack.md` 或 `cr-module.md` 加载。

## 核心思路

```
已有代码（任意技术栈）
    ↓ 逆向分析（本技能）
.allforai/ 产物（product-design 兼容格式）
    ↓ dev-forge 流水线
目标技术栈代码（/design-to-spec → /task-execute）
```

**这不是又一个代码生成工具。** 本技能的唯一职责是将已有代码逆向为 allforai 产物，控制权交还给 dev-forge 的成熟基础设施。

**核心区分**：复刻的输入是源系统的**业务意图**（做什么），不是源系统的**实现决策**（怎么做）。实现方式由目标生态的架构惯例填充。源码中的同步/异步模型、错误处理约定、通信协议等属于实现决策，应在 Phase 3 目标生态对齐时替换为目标生态惯例。

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

> 以下为代码复刻方向的 4D/6V/XV 定制协议。

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

> 6V JSON 结构详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（6V 视角 JSON 结构）

### XV 跨模型验证

> 以下为代码复刻定制的 XV 验证点。

**触发时机**：Phase 4 完成后，自动执行（检测 `OPENROUTER_API_KEY` 环境变量）。

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

**结果写入**：每个产出 JSON 文件顶层追加 `cross_model_review` 字段，结构为 `{ "task_type": string, "model": string, "issues": [{ "type": string, "description": string, "action_taken": string }], "reviewed_at": "ISO8601" }`。映射决策的 `cross_model_review` 结构详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（stack-mapping-decisions.json）。

### 歧义收集规则

分析过程中遇到歧义 → 记入 `ambiguity_log`（含文件位置、失真类型、描述），**不停流程**。Phase 5 汇总确认时一次性展示。

**唯一允许即时停止**：发现影响整体架构判断的致命歧义（如：无法确定项目是单体还是微服务），此时停下比产出错误产物代价更低。

---

## 工作流总览（7 Phase 平铺）

```
Phase 1: Preflight        收集基本参数（源码地址、信度、范围）
    ↓ 用户确认
Phase 2: 源码解构          技术栈识别 + 模块树 + 数据结构 + 代码规模       ← cr-backend / cr-frontend / cr-fullstack / cr-module
    ↓
Phase 3: 目标确认          展示源码全貌，锁定：                             ← 停顿
    │                      ① 复刻哪些模块/功能（范围）
    │                      ② 用什么技术栈重写（目标）
    │                      ③ 业务方向：1:1 / 精简 / 扩展
    │                      ④ 输出产物清单（哪些 allforai 文件会生成）
    │                      ⑤ 目标生态对齐（自动：源意图 vs 目标惯例）
    │                      ⑥ 分析粒度（自动决定）
    ↓ 用户确认 → 目标锁定
Phase 4: 深度分析          信度专项分析 + [可选] XV 跨模型校验              ← cr-backend / cr-frontend / cr-fullstack / cr-module
    ↓ 连续执行
Phase 5: 汇总确认          展示歧义 + 映射决策，ONE-SHOT 用户输入           ← 停顿
    ↓ 用户确认 → 连续执行到完
Phase 6: 生成产物          分析结果 → allforai 产物                        ← 共享 + 各技能各自
    ↓ 不停
Phase 7: 交接              最终报告 + dev-forge 下一步指引
```

**与 dev-forge 的同构关系**：
```
code-replicate Phase 1-5（分析+确认）  ≈  dev-forge /design-to-spec（规格化）
code-replicate Phase 6-7（执行+交接）  ≈  dev-forge /task-execute（产出）
code-replicate 的产出                  =  dev-forge 的输入
```

**核心规则**：
- **三个停顿点**：Phase 1（Preflight）、Phase 3（目标确认）、Phase 5（汇总确认）需要用户输入。
- 其余阶段连续执行，不停顿，不询问。中间阶段的疑问收集到 Phase 5 统一处理。
- **指导思想：先确定好目标，一路干到完。** Phase 1 定"从哪来" → Phase 3 定"到哪去"（复刻什么 + 用什么重写 + 输出什么）→ Phase 5 处理路上的歧义 → Phase 6-7 一路执行交接。

---

## Phase 1：Preflight — 一次性收集所有参数

### 断点续作检测（优先）

检查 `.allforai/code-replicate/replicate-config.json` 是否存在：
- **存在** → 展示上次配置摘要（模式、路径、完成步骤），询问"从上次继续"还是"重新开始"
- **不存在** → 继续 Preflight

### 从命令行参数解析

若 `$ARGUMENTS` 非空，尝试解析 `mode`、`path`（或 git URL）、`--type` 和 `--scope`：
- 已知 mode（interface/functional/architecture/exact）→ 预填信度等级
- 已知 path 或 URL → 预填源码地址
- `--type backend|frontend` → 预填 project_type
- `--scope` → 预填复刻范围（见下方说明）

### 源码地址处理

- **本地路径** → 直接使用
- **远程 git URL** → 自动 clone 到临时目录，后续分析该目录

**Git URL 识别**（满足以下任一条件即视为 git 地址）：
- HTTPS: `https://github.com/org/repo`、`https://gitlab.com/org/repo.git`
- SSH: `git@github.com:org/repo.git`
- GitHub 短链: `org/repo`（含且仅含一个 `/`，无路径分隔符）
- 任意含 `.git` 后缀或 `github.com`/`gitlab.com`/`bitbucket.org` 域名的 URL

**分支/Tag/Commit 支持**：
- URL 后可追加 `#branch-name` 或 `#tag-name` 或 `#commit-sha`
- 示例：`https://github.com/org/repo#v2.0`、`git@github.com:org/repo.git#develop`
- 未指定 → 使用默认分支

**两阶段 Clone 策略**（先快后深，按需升级）：

**阶段 1：浅克隆（Preflight 时执行）** — 只拿当前代码，秒级完成：
```bash
# 无分支指定
git clone --depth 1 <url> /tmp/cr-clone-<hash>

# 有分支/tag 指定
git clone --depth 1 --branch <ref> <url> /tmp/cr-clone-<hash>

# 有 commit SHA 指定（需全量 clone）
git clone <url> /tmp/cr-clone-<hash> && cd /tmp/cr-clone-<hash> && git checkout <sha>
```

**阶段 2：按需取完整历史（Phase 4 中触发）** — 仅在以下场景自动执行：
```bash
# 在已有浅克隆目录中取回完整历史
cd /tmp/cr-clone-<hash> && git fetch --unshallow
```

触发条件（满足任一即自动 unshallow，不问用户）：
- `fidelity = exact` — 需要 git blame 辅助判断代码意图和 bug 来源
- 分析中发现 `[INFERRED]` 项需要 commit message / blame 佐证 — 先尝试取历史再标注
- 用户在 Preflight 显式指定 `--full-history`

不触发时（绝大多数场景）：浅克隆足够，Phase 2-7 只读当前代码快照。

Clone 成功后：
- `source_path` → 指向 clone 目录
- `source_url` → 记录原始 git URL（含 ref）
- `clone_depth` → `shallow` 或 `full`（记录当前状态）
- 后续所有分析使用 `source_path`

Clone 失败 → 输出错误信息（URL 无效 / 权限不足 / 网络问题），要求用户检查后重试

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
| 项目类型 | {预填或待选} | backend / frontend（自动检测或 --type 指定） |
| 信度等级 | {预填或待选} | interface / functional / architecture / exact |
| 源码地址 | {预填或待填} | 本地路径 或 远程 git URL（自动 clone 到临时目录） |
| 复刻范围 | {预填或待选} | full / modules / feature（见下方说明） |
| 目标技术栈 | {预填或待填} | 从 project-manifest 读取或手动指定 |
| 歧义处理策略 | conservative | conservative = 遇歧义标注后继续；strict = 遇架构歧义即停 |
| exact 模式: bug 复刻默认 | replicate | replicate = 默认复刻所有 bug；fix = 默认修复；ask = 在 Phase 5 逐一决策 |
```

用 `AskUserQuestion` 仅询问**缺失**的必填项。已知项不再询问。

**提问优先级**（严格按此顺序，因为后续项依赖前序项）：
1. **源码地址**（最优先 — 项目类型检测依赖于它；没有源码地址，后续一切无法开始）
2. **复刻范围**（决定分析边界 — 整个项目 vs 某个功能，直接影响后续所有步骤的工作量）
3. **信度等级**（决定分析深度）
4. **项目类型**（若用户未通过 `--type` 指定且源码地址已知，可在 Phase 2 自动检测，此时不问）
5. **目标技术栈**（可从 project-manifest 预填；若用户尚未确定，允许留空，延迟到 Phase 3 看完源码后再定）

### 复刻范围详解

| 范围 | 含义 | 命令行 | 典型场景 |
|------|------|--------|---------|
| `full` | 整个代码库 | `--scope full`（默认） | 完整项目迁移 |
| `modules` | 指定模块/目录列表 | `--scope "src/user,src/order"` | 只迁移用户和订单模块 |
| `feature` | 按功能描述，由 AI 定位相关代码 | `--scope "用户注册和登录功能"` | 只复刻某个业务功能，不确定涉及哪些文件 |

**`feature` 模式工作方式**：
1. 用户用自然语言描述要复刻的功能（如"支付流程"、"用户认证"）
2. Phase 2 正常扫描整个项目的技术栈和模块树
3. Phase 4 时仅分析与该功能相关的代码路径（从路由/入口点追踪到 Service/Store/组件）
4. 产物中标注 `scope_filter`，记录哪些模块被纳入、哪些被排除及原因

**范围对 Phase 2/4 的影响**：
- `full` → 扫描并分析所有代码
- `modules` → Phase 2 扫描全部（需要全局上下文），Phase 4 仅分析指定目录下的端点/行为/组件
- `feature` → Phase 2 扫描全部，Phase 4 从功能入口追踪调用链，仅分析链上代码

### 写入配置

写入 `.allforai/code-replicate/replicate-config.json`（含 project_type, fidelity, source_path, source_url, source_ref, scope, scope_detail, target_stack, business_direction, ambiguity_policy, bug_replicate_default, analysis_granularity, steps_completed 字段）。

> 完整格式详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（replicate-config.json）

输出「✅ Preflight 完成，开始分析」，自动继续 Phase 2。

---

## Phase 2：源码解构（由各专项技能定义）

> **本 Phase 由各专项技能实现，core 不定义具体步骤。**
>
> - 后端项目 → `cr-backend.md` Phase 2（技术栈识别 + 模块树 + 代码规模）
> - 前端项目 → `cr-frontend.md` Phase 2（技术栈识别 + 组件树 + 代码规模）
> - 全栈项目 → `cr-fullstack.md` Phase 2（双栈扫描 + 基础设施）
> - 模块复刻 → `cr-module.md` Phase 2（标准扫描 + 依赖边界）
>
> Phase 2 完成后自动继续 Phase 3。

---

## Phase 3：目标确认（源码扫描完成后，必须停顿）

> **所有 scope 都执行此步骤。** 这是"先确定好目标，一路干到完"的关键卡点 — Phase 2 提供了源码全貌，此时用户才能做出准确决策。

Phase 2 完成后，展示源码全貌，让用户一次性确认三件事：**复刻范围**、**目标技术栈/业务方向**、**分析粒度**。确认后 Phase 4→7 一路执行（仅 Phase 5 处理分析中的歧义后继续）。

### 3a. 展示源码全貌

```markdown
## 源码扫描完成 — 请确认复刻目标

### 源码概览

| 项目 | 值 |
|------|----|
| 源技术栈 | {source_stack}（{framework} {version}） |
| 项目类型 | {backend/frontend} |
| 模块数 | {N} |
| 估算代码量 | {lines}± 行 |
| 路由/端点数 | {N}±（后端）/ 页面数 {N}±（前端） |

### 模块清单

| # | 模块 | 路径 | 职责（推断） | 关键文件 | 估算规模 |
|---|------|------|------------|---------|---------|
| 1 | user | src/modules/user | 用户注册/登录/资料 | user.controller.ts, user.service.ts | ~15 路由 |
| 2 | auth | src/modules/auth | JWT 认证/授权 | auth.guard.ts, auth.service.ts | ~5 路由 |
| 3 | order | src/modules/order | 订单管理 | order.controller.ts | ~20 路由 |
| 4 | payment | src/modules/payment | 支付集成 | payment.service.ts | ~8 路由 |
| ... | | | | | |

### 主要数据结构

| 模型/表 | 关键字段 | 关联模块 |
|---------|---------|---------|
| users | id, email, password_hash, role | user, auth |
| orders | id, user_id, status, total | order, payment |
| ... | | |
```

### 3b. scope = feature 时：功能追踪结果

```markdown
### 功能追踪

你要求复刻的功能: 「{scope_detail}」

从入口点追踪到以下调用链:
- 入口: POST /api/auth/login → AuthController.login()
- 调用: AuthService.validateUser() → UserService.findByEmail()
- 依赖: JwtService.sign(), BcryptUtil.compare()
- 数据: users 表（email, password_hash 字段）

**建议纳入的模块**: user ✅, auth ✅
**建议排除的模块**: order ❌, payment ❌（与该功能无关）
```

### 3c. 用户确认（AskUserQuestion，一次性）

展示以下决策清单，让用户确认或调整：

```markdown
### 请确认以下复刻目标

| 决策项 | 当前值 | 说明 |
|--------|-------|------|
| **复刻范围** | {scope + 模块列表} | 上表中哪些模块纳入？可增减 |
| **目标技术栈** | {target_stack 或 待定} | 用什么技术栈重写？（已看到源码全貌，现在可以确定） |
| **业务方向** | 1:1 复刻 / 精简 / 扩展 | 功能范围与源码一致？还是有增减？ |
| **输出产物** | {根据信度等级自动列出} | 本次分析将生成哪些 allforai 文件 |

确认后将一路执行到完成，中途仅在发现歧义时暂停（Phase 5）。
```

**输出产物预览**（根据信度等级自动生成）：

```markdown
### 本次将产出以下文件

| 产物 | 路径 | 本次生成？ |
|------|------|-----------|
| 任务清单 | product-map/task-inventory.json | ✅ 所有模式 |
| 业务流程 | product-map/business-flows.json | ✅ / ❌ functional+ |
| 约束清单 | product-map/constraints.json | ✅ / ❌ exact |
| 用例树 | use-case/use-case-tree.json | ✅ / ❌ functional+ |
| API 合约 | code-replicate/api-contracts.json | ✅ 所有模式 |
| 行为规格 | code-replicate/behavior-specs.json | ✅ / ❌ functional+ |
| 架构地图 | code-replicate/arch-map.json | ✅ / ❌ architecture+ |
| Bug 注册表 | code-replicate/bug-registry.json | ✅ / ❌ exact |
| 栈映射 | code-replicate/stack-mapping.json | ✅ 所有模式 |
| 复刻报告 | code-replicate/replicate-report.md | ✅ 所有模式 |

这些产物将作为 dev-forge（/design-to-spec → /task-execute）的输入。
```

用 `AskUserQuestion` 收集：
1. **复刻范围确认** — 纳入/排除的模块列表（scope=full 时默认全选，用户可裁剪）
2. **目标技术栈确认** — Phase 1 若已填则展示供确认，若未填则此时必须确定
3. **业务方向** — 三选一：
   - `replicate`（1:1 复刻，功能不增不减）
   - `slim`（精简，去掉部分功能，用户指定排除项）
   - `extend`（扩展，在复刻基础上预留扩展点，用户指定新增方向）
4. **输出产物确认** — 展示产物清单，用户确认（通常无需调整，但可以明确预期）

### 3d. 目标生态对齐（自动执行，不停顿）

> **核心原则**：复刻的输入是源系统的**业务意图**，不是源系统的**实现决策**。实现方式由目标生态的架构惯例填充。

用户确认目标技术栈后，**自动执行**以下检查（不问用户），产出写入 `replicate-config.json` 的 `ecosystem_alignment` 字段：

**步骤 1：识别源系统的架构决策**

扫描 Phase 2 产出的 `source-analysis.json`，提取源系统在以下维度的实现方式：

| 维度 | 提取内容 | 示例 |
|------|---------|------|
| 通信模型 | 同步/异步/混合 | REST 同步调用、WebSocket 推送 |
| 并发模式 | 进程/线程/协程/事件循环 | PHP-FPM 多进程、Node.js 事件循环 |
| 错误处理 | 返回码/异常/Result 类型 | 全局异常过滤器、错误码枚举 |
| 状态管理 | Session/Token/混合 | 服务端 Session + Cookie |
| 数据访问 | ORM/查询构建器/原生 SQL | ActiveRecord 模式 |
| 任务调度 | 队列/定时器/无 | Celery + Redis |

**步骤 2：查询目标生态的惯用方式**

根据目标技术栈，确定目标生态在上述每个维度的**惯用方式**（来源：框架官方文档推荐 + 社区主流实践）。

**步骤 3：生成对齐约束**

对比源系统实现与目标生态惯例，生成 `ecosystem_constraints` 列表。每条约束标明：

```json
{
  "dimension": "通信模型",
  "source_approach": "PHP 同步阻塞",
  "target_convention": "Go goroutine + channel 异步",
  "alignment_action": "adopt_target",
  "rationale": "业务逻辑保留，通信层采用目标生态异步模型"
}
```

`alignment_action` 取值：
- `adopt_target` — 采用目标生态惯例（绝大多数情况）
- `preserve_source` — 保留源系统方式（仅当目标生态无对应惯例，或业务逻辑与实现方式强耦合时）
- `hybrid` — 部分采用，需在 Phase 5 展示供用户确认

**对 Phase 4 的影响**：Phase 4 深度分析时，`alignment_action: adopt_target` 的维度，仅从源码提取**业务逻辑**（做什么），不提取实现方式（怎么做）。`behavior-specs.json` 中对应行为的 `implementation_notes` 标注 `[TARGET_CONVENTION]`，表示实现方式将由目标生态决定。

**对 Phase 5 的影响**：`alignment_action: hybrid` 的条目加入 Phase 5 的决策清单，供用户确认。

**展示**（信息性，不停顿）：

```markdown
### 目标生态对齐

| 维度 | 源系统 | 目标生态 | 决策 |
|------|--------|---------|------|
| 通信模型 | 同步阻塞 | 异步 (goroutine) | ✅ 采用目标 |
| 错误处理 | 自定义错误码 | 标准 error 接口 | ✅ 采用目标 |
| 状态管理 | Session | JWT | ⚠️ 待确认 |
```

### 3e. 分析粒度自适应

根据确认后的范围规模，**自动决定 Phase 4 的分析粒度**：

| 规模 | 判定条件 | 粒度 | Phase 4 行为 |
|------|---------|------|------------|
| **小** | ≤5 模块 且 ≤50 路由/组件 | `fine` | 每个端点/组件逐一分析，6V 全覆盖，追踪每条代码路径 |
| **中** | 6-15 模块 或 51-150 路由/组件 | `standard` | 每个端点/组件分析，高风险项 6V，普通项 4V |
| **大** | >15 模块 或 >150 路由/组件 | `coarse` | 按模块聚合分析，仅高频+高风险端点做 6V，其余提取接口签名 + 关键约束 |

**粒度对产物的影响**：
- `fine` → 产物最详细，每个行为都有完整 4D 信息卡 + 6V 视角 + 代码级 source_refs
- `standard` → 默认水平，高风险项完整，普通项省略 ux/risk 视角
- `coarse` → 产物偏概要，模块级 behavior-specs（非函数级），api-contracts 仅含签名+关键约束，不含完整 flow 步骤

粒度写入 `replicate-config.json` 的 `analysis_granularity` 字段，Phase 4 据此执行。

### 3f. 写入确认结果

更新 `replicate-config.json`：scope_filter, target_stack, business_direction, ecosystem_alignment, analysis_granularity, expected_outputs。

输出「Phase 3 ✓ {N} 模块纳入 | 目标: {target_stack} | 方向: {replicate/slim/extend} | 生态对齐: {N} 项 adopt_target / {N} 项 hybrid | 粒度: {fine/standard/coarse} | 产物: {N} 个文件 | 开始深度分析（不再停顿）」，自动继续 Phase 4。

---

## Phase 4 附：XV 跨模型验证（自动执行）

检测 `OPENROUTER_API_KEY` 环境变量：
- **存在** → 执行 2 次跨模型调用（见「增强协议 → XV」段落），自动继续
- **不存在** → 静默跳过，流程不受影响

**行为遗漏检测**（调用 1）→ 将遗漏行为追加到 `api-contracts.json` / `behavior-specs.json`，标注 `[XV:added]`。

**跨栈语义漂移风险**（调用 2）→ 高风险项直接修正产物中对应端点的 `mapping_risk` 字段并追加 `constraints.risk`，标注 `[XV:risk_elevated]`；不加入 Phase 5 决策列表，不问用户。

自动继续 Phase 5。

---

## Phase 5：汇总确认（ONE-SHOT 用户输入）

Phase 3 锁定目标后的最后一个停顿点。将深度分析中发现的所有待决策项一次性呈现。

### 5a. 歧义报告

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

### 5a-0. 目标框架内置能力扫描（5b 前置步骤）

> 详细框架内置能力速查表见 `${CLAUDE_PLUGIN_ROOT}/docs/stack-mappings.md`（框架内置能力速查表）

在执行 5b 跨栈映射决策之前，先扫描源码中手写实现的功能是否可被目标框架内置能力替代，避免不必要的自定义代码复刻。

**步骤**：

1. **识别目标框架内置能力**：根据 `replicate-config.json` 的 `target_stack`，查询 `stack-mappings.md` 中的框架内置能力速查表，列出目标框架的内置能力清单
2. **交叉比对源码产物**：扫描 `api-contracts.json` + `behavior-specs.json`（若有）+ `arch-map.json`（若有），识别源码中手写实现了以下类别功能的部分：
   - 参数校验（手写验证逻辑 vs 框架校验装饰器/标签）
   - 认证授权（手写 RBAC/Guard vs 框架内置）
   - 分页（手写分页 vs 框架 Pagination helper）
   - 缓存（手写缓存逻辑 vs 框架 Cache 模块）
   - 日志（自定义日志中间件 vs 框架 Logger）
   - 错误处理（自定义异常过滤 vs 框架 Exception Filter）
   - 文件上传（手写 multipart 处理 vs 框架集成）
   - 定时任务（手写调度 vs 框架 Scheduler）
   - CORS（手写 CORS 头 vs 框架 CORS 中间件）
   - 序列化（手写转换 vs 框架 Serializer/DTO）
3. **生成替代建议**：每个匹配项标记 `framework_builtin: true` + 目标框架内置方案名称
4. **展示给用户确认**（若有匹配项）：

```markdown
## 目标框架内置能力替代（{N} 项）

以下源码手写实现可直接使用 {target_stack} 内置功能替代：

| # | 源码实现 | 源码位置 | 目标框架内置 | 建议 |
|---|---------|---------|------------|------|
| 1 | 手写分页逻辑 | utils/paginate.ts | NestJS Pagination | 使用内置（推荐） |
| 2 | 手写 RBAC | guards/role.guard.ts | NestJS Guards + CASL | 使用内置（推荐） |
| 3 | 自定义日志中间件 | middleware/logger.ts | NestJS Logger | 使用内置 |
```

用 `AskUserQuestion` 收集决策（与 5a/5b/5c 合并到汇总 AskUserQuestion 中）：
- **全部使用内置**（推荐）
- **逐项决策**（用户可对每项选择 `use_builtin` / `keep_custom` / `hybrid`）

5. **写入产物**：结果写入 `stack-mapping-decisions.json` 的 `framework_builtins` 数组

> 产物格式详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（stack-mapping-decisions.json — framework_builtins）

**无匹配项** → 展示「未发现可替代的框架内置能力，继续映射决策」，直接进入 5b。

**对 Phase 6 的影响**：`decision: use_builtin` 的条目 → Phase 6 生成 task-inventory 时对应任务标记 `task_type: "framework_integration"`（区别于常规 `task_type`），任务描述注明使用框架内置方案，降低实现复杂度。

### 5b. 跨栈映射决策（多方案可选项）

> 详细映射规则见 `${CLAUDE_PLUGIN_ROOT}/docs/stack-mappings.md`

分析 Phase 2-4 中发现的所有需要决策的构造，**一次性**展示全部：

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

### 5c. exact 模式：Bug 复刻决策（仅 `bug_replicate_default = ask`）

逐一展示需要用户决策的 bug，用 `AskUserQuestion` 一次性收集所有 bug 决策。

### 汇总 AskUserQuestion

将 5a/5a-0/5b/5c 中需要用户输入的问题，合并成**最多 4 个** `AskUserQuestion` 调用（选项化，不开放填写），收集用户决策。

无需决策的项（歧义用默认处理、无复杂映射）→ 直接跳过，展示「无待确认项，直接继续」。

### 写入决策

将所有用户决策写入 `.allforai/code-replicate/stack-mapping-decisions.json`（持久化，下次重跑复用；含 decisions 和 ambiguity_resolutions 数组）。

> 决策文件格式详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（stack-mapping-decisions.json）

输出「Phase 5 ✓ {N} 个映射决策，{N} 个歧义已处理，继续生成产物（不停顿）」，自动继续 Phase 5 附。

---

## Phase 5 附：映射决策 XV 验证（自动执行）

检测 `OPENROUTER_API_KEY` 环境变量：
- **存在** → 执行 1 次映射决策审查，自动继续
- **不存在** → 静默跳过

| # | task_type | 发送内容 | 写入字段 |
|---|-----------|---------|---------|
| 5 | `mapping_decision_review` | 源栈 + 目标栈 + 全部映射决策摘要 | `cross_model_review.mapping_decision_issues` |

Prompt 模板：

调用 5（映射决策审查）：
```
源栈: {source_stack}
目标栈: {target_stack}
映射决策数: {n}，决策摘要:
{decisions_summary — 每条: source → selected, rationale, semantic_drift_risk}

请审查：
1. 是否有决策选了次优方案（存在更合适的选项未被选中）
2. semantic_drift_risk 是否被低估（标为 low 但实际应为 high）
3. 是否遗漏了该迁移方向的关键映射点（源栈有但未覆盖的构造）
限 300 字。
```

**自动采纳规则**（不问用户）：
- 次优方案警告 → 对应决策的 `semantic_drift_risk` 提升一级，rationale 追加 `[XV:risk_elevated]` 说明
- 遗漏映射点 → 追加新决策到 decisions 数组，标注 `[XV:added]`，`selected` 留空待 Phase 6 使用默认推荐
- 风险低估项 → 修正 `semantic_drift_risk` 字段 + 补充 `drift_details`，标注 `[XV:risk_elevated]`
- 无问题 → `cross_model_review.mapping_decision_issues` 写入空数组
- 所有修改回写 `stack-mapping-decisions.json`

自动继续 Phase 6。

---

## Phase 6：生成 allforai 产物（共享部分）

> **⚠️ 产物路径铁律 — 三个目录，不可混淆**
>
> 产物分布在 `.allforai/` 下的**三个独立目录**，写入时必须使用完整路径：
>
> | 产物 | 完整写入路径 | 生成条件 |
> |------|------------|---------|
> | task-inventory.json | **`.allforai/product-map/`**`task-inventory.json` | 所有模式 |
> | business-flows.json | **`.allforai/product-map/`**`business-flows.json` | functional+ |
> | constraints.json | **`.allforai/product-map/`**`constraints.json` | exact |
> | use-case-tree.json | **`.allforai/use-case/`**`use-case-tree.json` | functional+ |
> | 其余所有产物 | **`.allforai/code-replicate/`**`{filename}` | 按模式 |
>
> **错误示例**：写到 `.allforai/code-replicate/task-inventory.json` ❌
> **正确示例**：写到 `.allforai/product-map/task-inventory.json` ✅

以下产物由 core 统一生成，不区分前后端：

### 6a. `.allforai/product-map/task-inventory.json`（所有模式）

每个 API 端点/组件 → 一个任务（含 task_id, task_name, module, source_endpoint, source_file, task_type, frequency, risk_level, replicate_fidelity, api_contract_ref, behavior_spec_ref）。

### 6e. `.allforai/code-replicate/stack-mapping.json`

完整映射记录（source_stack, target_stack, auto_mapped, user_decisions, arch_decisions, unmapped）。

### 6f. `.allforai/code-replicate/replicate-report.md`

Markdown 人类可读摘要（基本信息表、分析结果摘要、信息失真风险点表、跨栈映射决策、下一步指引）。

> Phase 6 所有产物的完整 JSON 格式和 report 模板详见 `${CLAUDE_PLUGIN_ROOT}/docs/schema-reference.md`（Phase 6 产物格式）

**6b/6c/6d 由 cr-backend、cr-frontend 或 cr-fullstack 各自生成**（见各自技能文件）。

写入所有产物文件，更新 `replicate-config.json`，自动继续 Phase 7。

---

## Phase 7：交接 dev-forge（最终输出）

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

**项目类型**：{project_type}
**信息失真风险点**：{N} 个（详见 replicate-report.md）

---

### 提交建议：手写文件与生成文件分开提交

dev-forge `/task-execute` 产出的文件分两类，**必须分开提交**：

| 类型 | 示例 | 提交策略 |
|------|------|---------|
| **手写文件** | Service 业务逻辑、Controller、自定义中间件、工具函数 | 先提交，便于 code review |
| **生成文件** | ORM migration、Swagger/OpenAPI 生成物、proto 编译产物、框架脚手架 | 后提交，review 时可跳过 |

建议提交顺序：
1. `git add` 手写业务代码 → `git commit -m "feat: {module} business logic"`
2. `git add` 生成/配置文件 → `git commit -m "chore: {module} generated files"`

---

**下一步（dev-forge 流水线）**：

若尚未选择目标技术栈，先运行 `/project-setup`。

```
/design-to-spec   ← 读取上述产物，生成目标技术栈的实现规格（需指定目标技术栈）
/task-execute     ← 逐任务生成代码
```
```

> **fullstack 模式**：`project_type = fullstack` 时使用 cr-fullstack.md 的交接模板（生成 `fullstack-report.md` 替代 `replicate-report.md`）。

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
    ├── source-analysis.json         ← Phase 2
    ├── api-contracts.json           ← Phase 4（所有模式）
    ├── behavior-specs.json          ← Phase 4（functional+）
    ├── arch-map.json                ← Phase 4（architecture+）
    ├── bug-registry.json            ← Phase 4（exact）
    ├── stack-mapping.json           ← Phase 6
    ├── stack-mapping-decisions.json ← Phase 5 决策（持久化）
    └── replicate-report.md          ← Phase 6 人类可读摘要
```

**fullstack 模式额外产物**（详见 cr-fullstack.md）：
```
.allforai/code-replicate/
├── backend/                        ← 后端命名空间
│   ├── source-analysis.json
│   ├── api-contracts.json
│   └── behavior-specs.json
├── frontend/                       ← 前端命名空间
│   ├── source-analysis.json
│   ├── api-contracts.json
│   └── behavior-specs.json
├── api-bindings.json               ← 交叉验证层
├── schema-alignment.json
├── constraint-reconciliation.json
├── auth-propagation.json
├── error-mapping.json
├── infrastructure.json
└── fullstack-report.md             ← 替代 replicate-report.md
```

---

## 五条铁律

### 1. Preflight 一次收齐，中途不再询问

所有参数在 Phase 1 收齐。中间步骤的问题收集到 Phase 5 一次性处理。消灭"分析到一半停下来问"的体验。

### 2. 证据优先，结论必须可追溯

每个分析结论附代码位置引用。无法追溯的结论标注 `[INFERRED]` 并降级置信度，不当作确定事实处理。

### 3. 歧义收集，汇总处理，不拦截流程

分析过程中发现歧义 → 记入 log 继续 → Phase 5 一次性展示。唯一例外：影响整体架构走向的致命歧义（strict 模式下）。

### 4. 决策持久化，跨 session 复用

`stack-mapping-decisions.json` 持久存储。下次重跑时优先复用历史决策，相同构造不再重复询问。

### 5. 只产出 allforai 产物，不直接生成代码

本技能的边界是 `.allforai/` 目录。代码生成由 dev-forge 负责。用户要求直接生成代码时，引导完成本技能流程后使用 `/task-execute`。
