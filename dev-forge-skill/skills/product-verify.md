---
name: product-verify
description: >
  Use when the user wants to "verify product implementation", "acceptance test",
  "validate code against product map", "check if features are implemented",
  "static code coverage check", "dynamic browser testing", "find unimplemented tasks",
  "find extra code not in product map", "产品验收", "静态验收", "动态验收",
  "代码是否实现了产品地图", "验证功能实现", "找漏实现的功能", "代码覆盖检查",
  or wants to prove code implements the product map features and flows.
  Requires product-map to have been run first. Optionally uses experience-map and use-case.
version: "1.3.0"
---

# Product Verify — 产品验收

> 产品地图说应该有的，代码里真的实现了吗？行为符合预期吗？

## 目标

以 `product-map`（以及可选的 `experience-map`、`use-case`）为基准，回答两个问题：

1. **静态：代码有没有？** — 每个任务是否有对应的 API 路由？每个界面是否有对应的组件？每条约束是否有对应的校验逻辑？
2. **动态：行为对不对？** — 用 Playwright 运行实际应用，用例脚本跑得通吗？

发现差异，生成三类任务清单：
- **IMPLEMENT** — 产品地图有但代码没有（漏实现）
- **REMOVE_EXTRA** — 代码有但产品地图没有（多余代码，自动建议 keep/remove）
- **FIX_FAILING** — 代码有但行为不符合预期（测试失败）

---

## 定位

```
product-map（现状+方向）   feature-gap（功能查漏）    product-verify（验收）
产品应该长什么样           地图说有的，现在有没有      代码实现了地图里的任务吗
基础层                    产品层比对                 代码层比对 + 运行时验证
不看代码                  不看代码                   扫描代码 + 跑浏览器
```

**与 feature-gap 的区别**：feature-gap 检查**产品地图自身**是否完整（CRUD 齐不齐、旅程通不通）；product-verify 检查**代码**是否实现了产品地图中的任务（路由有没有、组件在不在、行为对不对）。一个审产品设计，一个审代码实现。

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。

---

## 快速开始

```
/product-verify           # 静态验收（默认，无需应用运行）
/product-verify static    # 同上，显式指定
/product-verify dynamic   # 动态验收（需要应用正在运行）
/product-verify full      # 静态 + 动态完整验收
/product-verify refresh   # 清除决策缓存，重新完整验收
/product-verify scope --tasks T001,T002 --sub-projects api-backend
                          # 增量验收（仅检查指定任务/子项目范围）
```

---

## 增强协议（WebSearch + 4E+4V + OpenRouter）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：
- `"automated acceptance testing {framework} {year}"`
- `"Playwright testing best practices {year}"`
- `"Lighthouse CI performance budget {year}"`

**4E+4V 重点**：
- **E3 Guardrails**: 扩展 S3 约束检查范围：覆盖 task.rules（业务规则验证逻辑）+ task.audit（审计中间件）+ task.exceptions（异常处理逻辑）
- **E2 Provenance**: 每条 verify-task 标注 `_Source: T001_`，可追溯到 product-map 任务

**OpenRouter 覆盖交叉验证**：
- **`code_impl_review`** (DeepSeek) — S5 步骤，详见工作流中 S5 节
- 审查 S1/S3 的 covered 判定是否存在假阳性（路由在但 handler 为空桩）

---

## 产品验收原则

> 以下原则在各步骤中强制执行。

| 原则 | 对应步骤 | 具体规则 |
|------|---------|---------|
| 先有条件再验证 | Step 1 静态 | 验收条件必须来自 use-case-tree.json 的 Given/When/Then，不自行编造验收标准 |
| 可用性启发式检查 | Step 2 动态 | 每个页面检查：错误状态有提示、加载有反馈、操作可撤销、导航一致、权限拒绝有说明 |
| 静态先行 | 整体时机 | 静态扫描（代码+路由+文件匹配）不需要启动应用，优先执行，尽早发现覆盖缺口 |
| 从路由验证覆盖 | Step 1 路由扫描 | 扫描实际路由/端点文件，与 product-map 任务列表对照。路由存在 = 功能已暴露，路由缺失 = 功能未实现 |
| E2E 只覆盖关键路径 | Step 2 动态 | 动态验收聚焦 business-flows 中的主路径，不重复验证已有单元测试覆盖的底层逻辑 |
| 交叉验证降低盲区 | S5 交叉验证 | S1-S4 的 covered 判定基于模式匹配，可能存在假阳性（路由在但 handler 为空桩）。通过 OpenRouter 调用第二模型读实际代码片段独立判断，标记分歧项为 REVIEW_NEEDED |

---

## 模式说明

| 模式 | 说明 | 是否需要应用运行 |
|------|------|----------------|
| `static` | 代码扫描，检查 API/组件/约束覆盖 | 否 |
| `dynamic` | Playwright 浏览器测试 | 是 |
| `full` | 静态 + 动态 | dynamic 阶段需要 |
| `refresh` | 清除 verify-decisions.json 缓存，重新完整运行 | 视模式而定 |
| `scope` | 增量验收：仅 S1+S3 范围过滤，S2/S4/Dynamic 跳过 | 否 |

---

## 工作流

```
前置检查（两阶段加载）：
  Phase 1 — 加载索引（< 5KB）：
    检查 task-index.json → 获取任务 id/task_name/frequency/owner_role/risk_level + 模块分组
    检查 experience-map.json → 获取界面 id/name/task_refs/action_count（S2 用）
    任一索引不存在 → 对应数据回退到 Phase 2 全量加载（向后兼容）
  Phase 2 — 按需加载完整数据：
    加载 .allforai/product-map/product-map.json
    若 product-map.json 也不存在 → 提示用户先运行 /product-map，终止
  其他可选数据：
    experience-map.json 必须（不存在则自动运行 experience-map 生成，然后启用 S2）
    use-case-tree.json 可选（dynamic 优先使用，否则自动推导）
    verify-decisions.json 存在则加载历史决策，已决策项自动跳过
  ↓
前置: 创新保护感知
  加载 task-inventory.json 检查 innovation_tasks 字段：
    存在 → 提取所有 protection_level=core 的任务 ID 列表
      在 S1-S5 静态验证和 D2-D3 动态验证中，core 创新任务视为 frequency=high，确保不被优先级降级
      S5 成本控制中，core 创新任务始终包含在审查集中，不受 covered 数量阈值限制
    不存在 → 跳过，按标准优先级处理
  ↓
前置: 上游过期检测
  加载输入文件时，比较关键上游文件的修改时间与本技能上次输出的生成时间：
  - product-map.json 在 verify-report.md 生成后被更新
    → ⚠ 警告「product-map.json 在 verify-report.md 生成后被更新，数据可能过期，建议重新运行 product-map」
  - requirements.md 在 verify-report.md 生成后被更新
    → ⚠ 警告「requirements.md 在 verify-report.md 生成后被更新，数据可能过期，建议重新运行 design-to-spec」
  - 仅警告不阻断，用户可选择继续或先刷新上游
  ↓

[Static 阶段]（static / full 模式）
  S1: Task → API 覆盖检查
      遍历 task-inventory.json，扫描代码路由，比对覆盖状态
      → 输出进度: 「S1 Task→API ✓ covered:{N} missing:{M} partial:{K}」
  S2: Screen → 组件覆盖检查（experience-map.json 存在时）
      遍历 experience-map.json，扫描页面组件，比对覆盖状态
      → 输出进度: 「S2 Screen→组件 ✓ covered:{N} missing:{M}」（或 WARNING 跳过）
  S3: 约束 → 代码覆盖检查
      遍历 product-map constraints，Grep 校验/中间件逻辑
      → 输出进度: 「S3 约束→代码 ✓ covered:{N} missing:{M}」
  S4: Extra 代码扫描
      反向：扫描代码路由，找出未在产品地图中出现的端点
      → 输出进度: 「S4 Extra ✓ {N} 端点不在产品地图中」
  ↓
  S5: Cross-Model 交叉验证（OpenRouter 可用时）
      目的: 降低 S1/S3 模式匹配的假阳性（路由在但 handler 为空桩/TODO）
      输入: S1 中 status=covered 的任务 + S3 中 status=covered 的约束
      流程:
        1. 对每个 covered 项，Read 匹配文件的关键代码段（路由 handler ±15 行）
        2. 调用 OpenRouter DeepSeek（task: "technical_validation"）:
           prompt: 任务描述 + 代码片段 → 判断: genuine / stub / partial
        3. DeepSeek 判定与 Claude 分歧的项 → 标记 REVIEW_NEEDED
        4. 高频任务（frequency=高）优先审查，低频可跳过以控制成本
      成本控制:
        covered 项 ≤ 20 → 全量审查
        covered 项 > 20 → 仅审查 frequency=高 + risk_level=高 的项
      OpenRouter 不可用 → 跳过 S5，输出: 「S5 交叉验证 ⊘ OpenRouter 不可用，跳过」
      → 输出进度: 「S5 交叉验证 ✓ {N} 项审查, {M} 项分歧(REVIEW_NEEDED)」
  ↓
  静态汇总确认（单次交互）:
    展示覆盖率汇总表:
    | 检查项 | 已覆盖 | 缺失 | 部分 | 分歧 |
    |--------|--------|------|------|------|
    | S1 Task→API | {N} | {M} | {K} | {J} |
    | S2 Screen→组件 | {N} | {M} | — | — |
    | S3 约束→代码 | {N} | {M} | — | {J} |

    REVIEW_NEEDED 分歧项（S5 交叉验证发现）:
    | 任务/约束 | Claude 判定 | DeepSeek 判定 | 代码位置 | 理由 |
    |----------|------------|--------------|---------|------|
    | T005 创建退款 | covered | stub | routes/refund.ts:23 | handler 仅返回 TODO 注释 |

    IMPLEMENT 候选: {N} 项（按频次排序）
    EXTRA 端点（自动建议）:
    | 端点 | 建议 | 理由 |
    |------|------|------|
    | /api/legacy/export | ignore | 无匹配任务，可能历史遗留 |
    | /api/internal/sync | ignore | 内部同步，不面向用户 |

    → 自动采纳全部建议决策（不停）

[Dynamic 阶段]（dynamic / full 模式）
  D0: 应用可达性预检
      自动检测 URL（Grep 代码配置 PORT/listen/.env）
      HTTP 请求验证可达性
      可达 → 继续（不停）
      不可达 → 记录为 ENV_ISSUE，跳过 dynamic 阶段（不停）
  D1: 加载/推导测试序列
      use-case-tree.json 存在 → 提取正常流 + E2E 用例
      不存在 → 从 task-inventory.json 自动推导（高/中频任务）
      自动推导测试序列（不停，汇总到 D4 批量确认）
  D2: 执行正常流用例（Playwright）
      → 输出进度: 「D2 正常流 ✓ pass:{N} fail:{M} skip:{K}」
  D3: 执行 E2E 流用例（Playwright）
      → 输出进度: 「D3 E2E流 ✓ pass:{N} fail:{M} skip:{K}」
  D4: 自动分类 + 批量确认（单次交互）
      基于错误特征自动建议分类（FIX_FAILING / ENV_ISSUE）
      展示通过数 + 失败项汇总表（含自动建议分类及理由）
      → 自动采纳全部建议分类（不停）

生成输出文件：
  static-report.json / dynamic-report.json / verify-tasks.json / verify-report.md
```

---

### S1：Task → API 覆盖检查

**数据加载**：两阶段加载——先检查 `.allforai/product-map/task-index.json`（索引，< 5KB），存在则加载索引获取任务 id/task_name/frequency/owner_role，再按需从 `task-inventory.json` 加载完整任务数据。索引不存在时回退到全量加载 `task-inventory.json`。

**扫描策略**：
1. **框架检测**：Grep package.json / Gemfile / requirements.txt / composer.json 识别后端框架（Express / Rails / Django / Laravel / NestJS 等）
2. **路由扫描**：Glob 路由文件（routes/**, **/router.**, **/controllers/**），提取所有已定义端点
3. **映射比对**：对每个 task，检查是否存在路径或方法关键词匹配的路由

**覆盖状态**：
- `covered` — 找到匹配路由
- `missing_api` — 未找到任何匹配路由（→ IMPLEMENT 候选）
- `partial` — 找到路由但缺少角色鉴权中间件

**输出**：写入 `static-report.json` 的 `task_coverage` 字段。

---

### S2：Screen → 组件覆盖检查

**前提**：`.allforai/experience-map/experience-map.json` 存在；否则自动加载并执行 `${CLAUDE_PLUGIN_ROOT}/../product-design-skill/skills/experience-map.md` 的完整工作流生成体验地图，完成后继续 S2。

**扫描策略**：
1. Glob 前端页面/视图文件（pages/**, views/**, src/pages/**, app/**/page.**, 等）
2. 对每个 screen，匹配路由路径或组件名关键词

**覆盖状态**：
- `covered` — 找到对应页面组件
- `missing_screen` — 未找到（→ IMPLEMENT 候选）

**输出**：写入 `static-report.json` 的 `screen_coverage` 字段。

---

### S3：约束 → 代码覆盖检查

**数据来源**：
- `product-map.json` 中的 `constraints` — 全局业务约束
- `task-inventory.json` 中每个任务的 `rules` — 任务级业务规则（幂等、阈值、校验）
- `task-inventory.json` 中每个任务的 `exceptions` — 异常处理逻辑（超时、冲突、权限）
- `task-inventory.json` 中每个任务的 `audit` — 审计中间件（操作记录、字段变更）

**扫描策略**：对每条约束/规则/异常/审计要求，Grep 代码库中的：
- 校验器（validator, validate, schema）
- 中间件（middleware, guard, interceptor, policy）
- 审计逻辑（audit, log, track, record）
- 条件判断中的约束关键词

**覆盖状态**：
- `covered` — 找到对应校验逻辑
- `missing_constraint` — 未找到（→ IMPLEMENT 候选，高风险约束优先）

**输出**：写入 `static-report.json` 的 `constraint_coverage` 字段。

---

### S3.5：Implementation Contract 验证

**前提**：`.allforai/experience-map/experience-map.json` 中 screens 含 `implementation_contract` 字段。字段不存在 → 跳过 S3.5。

**扫描策略**：
1. 遍历 experience-map 中每个 screen 的 `implementation_contract`
2. 对每个 screen，Grep 前端代码找到对应组件
3. 检查组件是否匹配 `pattern`：
   - `bottom-sheet` → 查找 BottomSheet / Drawer / ActionSheet 组件
   - `modal-picker` → 查找 Modal / Dialog / Picker 组件
   - `multi-step-form` → 查找 Stepper / Steps / multi-step 模式
   - `full-page` → 查找独立页面路由
   - `standard-page` → 不检查（默认模式）
   - 其他值 → ⚠ WARNING「未知 pattern: {value}，跳过验证」（product-design 可能新增了 pattern 但 S3.5 未同步）
4. 检查 `forbidden` 列表中的模式是否出现
5. 检查 `required_behaviors` 是否有对应实现

**覆盖状态**：
- `compliant` — 组件匹配 pattern，无 forbidden 违规
- `violation` — 使用了 forbidden 模式，或缺少 required_behaviors（→ FIX_CONTRACT 任务）
- `unchecked` — 组件未找到（由 S2 处理）

**输出**：写入 `static-report.json` 的 `contract_compliance` 字段。violation 项生成 `FIX_CONTRACT` 类型任务到 `verify-tasks.json`。

---

### S4：Extra 代码扫描

**策略**：反向扫描——提取代码中所有路由端点，与 task-inventory 中的任务做反向比对，找出**代码有但产品地图没有**的端点。

**排除项**（自动标注「基础设施/开发支持，不计入 EXTRA」）：
- 健康检查端点（/health, /ping, /ready, /metrics, /status）
- 认证/OAuth 回调端点（/auth/callback, /oauth/*, /login, /logout）
- API 文档端点（/api-docs, /swagger, /openapi, /redoc）
- 静态资源路由（/public/*, /static/*, /assets/*, /favicon.ico）
- 框架内置路由（Next.js `_next/*`, Rails `/rails/*`, Django `/admin/`, Vite `/@vite/*`）
- WebSocket 升级端点（/ws, /socket.io）

**EXTRA 自动建议规则**：
基础设施端点已在排除列表中自动跳过。剩余 EXTRA 端点默认建议 `ignore`，用户在静态汇总确认时可改为 `add_to_map` 或 `mark_remove`。

**输出**：EXTRA 项在静态汇总中批量展示（含自动建议），用户一次确认或逐条调整：
- `add_to_map` — 补录到产品地图（记录 INFO）
- `mark_remove` — 标记为 REMOVE_EXTRA 任务
- `ignore` — 合理遗留，忽略

---

### S5：Cross-Model 交叉验证

**目的**：S1 和 S3 的 covered 判定基于 Glob+Grep 模式匹配，存在假阳性风险——路由文件存在但 handler 内容为 `TODO`、空函数、或仅返回 mock 数据。通过 OpenRouter 调用第二模型（DeepSeek）读取实际代码片段，独立判断是否真正实现。

**触发条件**：OpenRouter MCP 可用时自动执行。不可用时跳过并在汇总中标注。

**审查范围**（成本控制）：

| covered 总数 | 审查策略 |
|-------------|---------|
| ≤ 20 项 | 全量审查所有 covered 项 |
| 21-50 项 | 仅审查 frequency=高 + risk_level=高 的 covered 项 |
| > 50 项 | 仅审查 frequency=高 的 covered 项（上限 30 项） |

例外：`protection_level=core` 的创新任务始终纳入审查，不受数量阈值限制。

**执行流程**：

```
对每个待审查的 covered 项:
  1. Read 匹配文件（matched_routes / matched_code 中的文件路径）
     提取路由 handler / 校验逻辑的关键代码段（匹配行 ±15 行，上限 50 行）
  2. 构造审查 prompt:
     角色: 你是一位严格的代码审查员
     任务描述: "{task_name}: {task 简述}"
     代码片段: （上一步提取的代码）
     判断标准:
       genuine — handler 包含实际业务逻辑（数据库操作/服务调用/条件判断）
       stub — handler 为空函数、仅返回固定值、包含 TODO/FIXME、或仅 console.log
       partial — handler 有部分逻辑但明显不完整（如只处理了 happy path，缺少错误处理）
     输出: { "verdict": "genuine|stub|partial", "reason": "一句话理由" }
  3. 调用 OpenRouter:
     mcp__plugin_product-design_ai-gateway__ask_model(
       task: "technical_validation",
       model_family: "deepseek",
       prompt: 上述 prompt
     )
  4. 比对结果:
     Claude covered + DeepSeek genuine → 确认 covered（无分歧）
     Claude covered + DeepSeek stub → 标记 REVIEW_NEEDED（假阳性嫌疑）
     Claude covered + DeepSeek partial → 标记 REVIEW_NEEDED（实现不完整）
```

**分歧处理**：REVIEW_NEEDED 项在静态汇总中单独展示，用户可选：
- `downgrade` — 将 covered 降级为 missing（加入 IMPLEMENT 候选）
- `keep` — 维持 covered（代码足够）
- `partial` — 标记为 partial（生成补全任务）

**输出**：写入 `static-report.json` 的 `cross_model_review` 字段。

---

### D0：应用可达性预检

**目的**：在启动 Playwright 测试前确认应用可访问，避免浪费时间。

**检测策略**（优先自动检测，仅不可达时交互）：
1. 自动检测：Grep 代码中的 `PORT`、`listen`、`localhost`、`.env` 等配置，推测应用 URL
2. 使用 Bash `curl -s -o /dev/null -w "%{http_code}" <URL>` 验证 HTTP 可达性
3. 可达 → 继续（不停）
4. 不可达 → 记录为 ENV_ISSUE，跳过 dynamic 阶段（不停）

**输出**：确认的 `app_url` 写入 `dynamic-report.json` 的 `app_url` 字段。

---

### D1：加载/推导测试序列

**use-case-tree.json 存在时**：
- 提取所有 `type: "normal"` 的正常流用例
- 提取所有 `type: "e2e"` 的 E2E 用例
- 过滤掉 `priority: "低"` 的用例（可选，询问用户）

**use-case-tree.json 不存在时（自动推导）**：
- 从 task-inventory.json 提取 frequency=高 和 frequency=中 的任务
- 按角色分组，为每个角色生成最简测试序列（登录 → 执行核心任务 → 验证结果）
- 自动推导测试序列（不停，汇总到 D4 批量确认）

---

### D2/D3：Playwright 执行

**执行方式**：使用 MCP Playwright 工具交互式测试，主要工具：
- `browser_navigate` — 导航到目标页面
- `browser_snapshot` — 获取页面可访问性快照（用于定位元素）
- `browser_click` / `browser_type` / `browser_fill_form` — 模拟用户操作
- `browser_take_screenshot` — 失败时截图保存到 `.allforai/product-verify/screenshots/`
- `browser_wait_for` — 等待页面加载或元素出现

**执行原则**：
- 每个用例独立运行，不相互依赖
- 每步操作前先 `browser_snapshot` 获取当前页面状态，再根据快照中的元素 ref 执行操作
- 失败时记录：失败步骤、错误信息、截图路径
- 超时阈值：单步 10 秒，单用例 60 秒（可配置）

---

### D3.5：LLM Cognitive Walkthrough（可发现性测试）

**前提**：dynamic 或 full 模式 + Playwright 可用 + 应用已可达（D0 通过）。任一不满足 → 跳过。

**目的**：验证用户能否**发现**功能，而非功能是否存在。E2E 测试知道组件 ID 直接点击；认知走查模拟真实用户只看界面内容。

**执行流程**：

1. 从 role-profiles.json 提取角色列表
2. 从 experience-map.json 提取每个角色的核心操作线（取 frequency=高 的前 3 条）
3. 对每条操作线构造认知走查任务:
   - persona: "{角色名}，首次使用本系统"
   - goal: 操作线的 name（如 "完成首次下单"）
   - 期望步数: 操作线 continuity.total_steps
   - 禁止提供: 路由名、组件 ID、导航提示
4. 对每个任务:
   a. browser_navigate 到首页
   b. browser_snapshot 获取页面快照
   c. 基于快照内容（纯文本，不看 HTML 结构），决定下一步点击
   d. 记录每次点击的 ref 和原因
   e. 重复 b-d 直到目标完成或达到 max_clicks（期望步数 x 3）
   f. 记录: 完成/放弃、实际点击数、卡住点
5. 输出 cognitive-walkthrough.json

**卡住判定**：连续 2 次快照相同（点击无效果）或 3 次回退（找不到入口）。

**输出**：`.allforai/product-verify/cognitive-walkthrough.json`

`discoverability_score` = `expected_clicks / actual_clicks`（上限 1.0）。
`overall_discoverability` = 所有走查分数的算术平均。

**D4 汇总集成**：D3.5 结果在 D4 汇总中展示为独立段落，不影响 FIX_FAILING 分类。discoverability_score < 0.5 的走查标记为 WARNING。

**结果分类**（每个用例）：
- `pass` — 所有步骤成功
- `fail` — 某步骤失败（记录原因）
- `skip` — 前置条件不满足（如需要种子数据未准备）
- `error` — Playwright 自身错误（环境问题）

---

### D4：自动分类 + 批量确认

**自动分类规则**（基于错误特征建议分类，用户仍是最终决策者）：

| 错误特征 | 自动建议 | 理由 |
|---------|---------|------|
| HTTP 5xx 响应 | FIX_FAILING | 服务端错误 = 代码缺陷 |
| 404 on expected route | FIX_FAILING | 路由未实现 |
| 元素未找到 / 断言失败 | FIX_FAILING | 页面实现不完整 |
| Connection refused / timeout | ENV_ISSUE | 服务未启动或网络问题 |
| Database error in response | ENV_ISSUE | 数据库未初始化 |
| Auth redirect (unexpected) | FIX_FAILING | 权限配置错误 |
| CORS error | ENV_ISSUE | 开发环境跨域配置 |

**批量确认展示格式**：

```
## 动态验收结果

通过: {N}/{M} 用例

失败项（自动建议分类）:
| 用例 | 失败步骤 | 错误 | 建议分类 | 理由 |
|------|---------|------|---------|------|
| UC001 创建订单 | Step 3 | 500 Internal Error | FIX_FAILING | HTTP 5xx |
| UC005 导出报表 | Step 1 | Connection refused | ENV_ISSUE | 连接拒绝 |
| UC008 批量删除 | Step 2 | Element not found | FIX_FAILING | 元素缺失 |

→ 自动采纳全部建议分类（不停）
```

---

## Scope 模式（增量验收）

供 `task-execute` 每 Round 结束后调用，仅验证本 Round 涉及的任务和子项目。

**调用方式**：`/product-verify scope --tasks T001,T002,T003 --sub-projects api-backend`

**参数**：
- `--tasks` — 逗号分隔的 task_id 列表（来自 build-log.json 当前 Round 的任务）
- `--sub-projects` — 逗号分隔的子项目名（来自 build-log.json 当前 Round 涉及的子项目）

**执行范围**：

| 步骤 | Scope 模式行为 | 理由 |
|------|--------------|------|
| S1: Task → API 覆盖 | 仅检查 `--tasks` 中的任务 | 增量：只验证本 Round 新实现的 |
| S2: Screen → 组件覆盖 | **跳过** | 界面覆盖需全量比对才有意义 |
| S3: 约束 → 代码覆盖 | 仅检查 `--tasks` 关联的约束 | 增量：只验证本 Round 涉及的约束 |
| S4: Extra 代码扫描 | **跳过** | 反向扫描需全量，增量无意义 |
| S5: 交叉验证 | 仅审查 `--tasks` 中 covered 的项 | 增量：只交叉验证本 Round 的结果 |
| Dynamic (D0-D4) | **跳过** | 动态测试留给 full 模式 |

**输出**：结果追加到 `static-report.json`（不覆盖之前的全量结果），同时返回给调用方（task-execute）用于写入 build-log.json 的 `verification` 字段。

---

## 输出文件结构

```
.allforai/product-verify/
├── static-report.json       # S1-S4: 静态覆盖状态
├── dynamic-report.json      # D2-D3: 动态测试结果
├── verify-tasks.json        # 待处理任务清单（IMPLEMENT / REMOVE_EXTRA / FIX_FAILING）
├── verify-report.md         # 可读版报告（含 innovation_coverage）
└── verify-decisions.json    # 用户决策日志（S4 EXTRA 归属 + D4 失败分类）
```

### static-report.json

```json
{
  "generated_at": "2024-01-15T10:30:00Z",
  "task_coverage": [
    {
      "task_id": "T001",
      "task_name": "{任务名}",
      "frequency": "高 | 中 | 低",
      "owner_role": "{角色名}",
      "status": "covered | missing_api | partial",
      "matched_routes": ["/api/orders POST"],
      "notes": "缺少角色鉴权中间件"
    }
  ],
  "screen_coverage": [
    {
      "screen_id": "S001",
      "screen_name": "{界面名}",
      "status": "covered | missing_screen",
      "matched_components": ["src/pages/orders/index.tsx"],
      "notes": ""
    }
  ],
  "constraint_coverage": [
    {
      "task_id": "T001",
      "constraint": "{约束描述}",
      "status": "covered | missing_constraint",
      "matched_code": ["src/middleware/auth.ts:42"],
      "risk_level": "高 | 中 | 低"
    }
  ],
  "extra_endpoints": [
    {
      "route": "/api/legacy/export GET",
      "file": "src/routes/legacy.ts:15",
      "decision": "add_to_map | mark_remove | ignore | pending"
    }
  ],
  "cross_model_review": {
    "enabled": true,
    "model": "deepseek",
    "reviewed_count": 12,
    "results": [
      {
        "source_step": "S1",
        "item_id": "T005",
        "item_name": "创建退款",
        "claude_verdict": "covered",
        "deepseek_verdict": "stub",
        "deepseek_reason": "handler 仅包含 // TODO: implement refund logic",
        "matched_file": "src/routes/refund.ts:23",
        "resolution": "downgrade | keep | partial | pending"
      }
    ],
    "summary": {
      "agree": 10,
      "disagree": 2
    }
  },
  "innovation_coverage": {
    "core_tasks_total": 0,
    "core_tasks_verified": 0,
    "coverage_rate": "100%"
  }
}
```

### dynamic-report.json

```json
{
  "generated_at": "2024-01-15T11:00:00Z",
  "app_url": "http://localhost:3000",
  "test_sequences": [
    {
      "case_id": "UC001",
      "case_name": "{用例名}",
      "source": "use-case-tree | auto-derived",
      "role": "{角色名}",
      "task_id": "T001",
      "result": "pass | fail | skip | error",
      "steps": [
        {
          "step": 1,
          "action": "{操作描述}",
          "status": "pass | fail",
          "error": null,
          "screenshot": ".allforai/product-verify/screenshots/UC001-step1.png"
        }
      ],
      "duration_ms": 3200,
      "failure_classification": "FIX_FAILING | ENV_ISSUE | DEFERRED | null"
    }
  ],
  "summary": {
    "total": 20,
    "pass": 15,
    "fail": 3,
    "skip": 1,
    "error": 1
  }
}
```

### verify-tasks.json

> 以下示例以虚构业务为背景，仅用于说明输出格式。

```json
[
  {
    "id": "VT-001",
    "type": "IMPLEMENT | REMOVE_EXTRA | FIX_FAILING",
    "task_id": "T001",
    "task_name": "{任务名}",
    "frequency": "高 | 中 | 低",
    "priority": "P0 | P1 | P2",
    "source_step": "S1 | S2 | S3 | S4 | D4",
    "description": "「创建订单」任务无对应 API 路由",
    "affected_roles": ["客服专员"],
    "suggested_action": "实现 POST /api/orders 端点"
  }
]
```

### verify-decisions.json

```json
[
  {
    "step": "S4",
    "item_id": "/api/legacy/export",
    "item_name": "旧版导出端点",
    "decision": "add_to_map | mark_remove | ignore",
    "reason": "用户备注（可选）",
    "decided_at": "2024-01-15T10:30:00Z"
  },
  {
    "step": "D4",
    "item_id": "UC003",
    "item_name": "客服创建退款用例失败",
    "decision": "FIX_FAILING | ENV_ISSUE | DEFERRED",
    "reason": "数据库连接超时，非代码问题",
    "decided_at": "2024-01-15T11:15:00Z"
  }
]
```

**加载逻辑**：每个 Step 开始前检查 verify-decisions.json，已有决策的条目跳过确认直接沿用。`refresh` 模式下将文件重命名为 `.bak` 后重跑。

---

## 5 条铁律

1. **product-map 是验收基准** — 静态验收以 product-map.json 为唯一真值，不引入额外需求来源；有争议的功能先补充到产品地图，再重跑验收
2. **只报告不修改代码** — 发现缺口只标记到 verify-tasks.json，不自动生成、修改或删除任何实现代码
3. **频次决定优先级** — IMPLEMENT 任务按 frequency 排序，高频漏实现优先于低频；低频漏实现仅列出不主动建议
4. **EXTRA 自动建议归属** — EXTRA 代码由系统自动建议 keep/remove，写入决策日志
5. **动态失败自动分类** — 基于错误特征自动建议分类（FIX_FAILING / ENV_ISSUE），自动采纳写入决策日志
