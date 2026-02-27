---
name: product-verify
description: >
  Use when the user wants to "verify product implementation", "acceptance test",
  "validate code against product map", "check if features are implemented",
  "static code coverage check", "dynamic browser testing", "find unimplemented tasks",
  "find extra code not in product map", "产品验收", "静态验收", "动态验收",
  "代码是否实现了产品地图", "验证功能实现", "找漏实现的功能", "代码覆盖检查",
  or wants to prove code implements the product map features and flows.
  Requires product-map to have been run first. Optionally uses screen-map and use-case.
version: "1.1.0"
---

# Product Verify — 产品验收

> 产品地图说应该有的，代码里真的实现了吗？行为符合预期吗？

## 目标

以 `product-map`（以及可选的 `screen-map`、`use-case`）为基准，回答两个问题：

1. **静态：代码有没有？** — 每个任务是否有对应的 API 路由？每个界面是否有对应的组件？每条约束是否有对应的校验逻辑？
2. **动态：行为对不对？** — 用 Playwright 运行实际应用，用例脚本跑得通吗？

发现差异，生成三类任务清单：
- **IMPLEMENT** — 产品地图有但代码没有（漏实现）
- **REMOVE_EXTRA** — 代码有但产品地图没有（多余代码，需用户确认去留）
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

## 增强协议（WebSearch + 4E+4V）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：
- `"automated acceptance testing {framework} {year}"`
- `"Playwright testing best practices {year}"`
- `"Lighthouse CI performance budget {year}"`

**4E+4V 重点**：
- **E3 Guardrails**: 扩展 S3 约束检查范围：覆盖 task.rules（业务规则验证逻辑）+ task.audit（审计中间件）+ task.exceptions（异常处理逻辑）
- **E2 Provenance**: 每条 verify-task 标注 `_Source: T001_`，可追溯到 product-map 任务

---

## 产品验收理论支持

> 详见 `docs/dev-forge-principles.md` — 尾段：验证与交付

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|---------|---------|
| **ATDD** (Beck, 2003) | Step 1 静态验收 | 验收条件来自 use-case，先有条件再验证实现 |
| **Heuristic Evaluation** (Nielsen, 1994) | Step 2 动态验收 | 10 条启发式原则辅助判断 UI 可用性问题 |
| **Shift-Left Quality** (Forrester, 2016) | 整体时机 | 静态扫描不需运行应用，尽早发现覆盖缺口 |
| **Hexagonal Architecture** (Cockburn, 2005) | Step 1 路由扫描 | 通过端口（路由/端点）验证核心逻辑是否暴露 |
| **Test Pyramid** (Cohn, 2009) | Step 2 动态策略 | 动态验收聚焦关键路径，不重复单元测试覆盖的逻辑 |

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
    检查 screen-index.json → 获取界面 id/name/task_refs/action_count（S2 用）
    任一索引不存在 → 对应数据回退到 Phase 2 全量加载（向后兼容）
  Phase 2 — 按需加载完整数据：
    加载 .allforai/product-map/product-map.json
    若 product-map.json 也不存在 → 提示用户先运行 /product-map，终止
  其他可选数据：
    screen-map.json 可选（存在则启用 S2）
    use-case-tree.json 可选（dynamic 优先使用，否则自动推导）
    verify-decisions.json 存在则加载历史决策，已决策项自动跳过
  ↓

[Static 阶段]（static / full 模式）
  S1: Task → API 覆盖检查
      遍历 task-inventory.json，扫描代码路由，比对覆盖状态
      ↓ 用户确认
  S2: Screen → 组件覆盖检查（screen-map.json 存在时）
      遍历 screen-map.json，扫描页面组件，比对覆盖状态
      ↓ 用户确认（或跳过）
  S3: 约束 → 代码覆盖检查
      遍历 product-map constraints，Grep 校验/中间件逻辑
      ↓ 用户确认
  S4: Extra 代码扫描
      反向：扫描代码路由，找出未在产品地图中出现的端点
      ↓ 用户确认（逐条确认 EXTRA 去留）

[Dynamic 阶段]（dynamic / full 模式）
  D0: 应用可达性预检
      询问用户应用 URL（或从代码配置自动检测）
      HTTP 请求验证可达性 → 不可达则提示用户启动应用，暂停 dynamic 阶段
      ↓ 可达后继续
  D1: 加载/推导测试序列
      use-case-tree.json 存在 → 提取正常流 + E2E 用例
      不存在 → 从 task-inventory.json 自动推导（高/中频任务）
      ↓ 展示测试计划，用户确认
  D2: 执行正常流用例（Playwright）
      ↓ 用户确认
  D3: 执行 E2E 流用例（Playwright）
      ↓ 用户确认
  D4: 汇总结果，用户确认失败原因分类
      FIX_FAILING（代码缺陷）vs ENV_ISSUE（测试环境问题，不计入任务）
      ↓ 用户确认

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

**前提**：`.allforai/screen-map/screen-map.json` 存在；否则跳过，提示「如需界面覆盖检查，请先运行 /screen-map」。

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

### S4：Extra 代码扫描

**策略**：反向扫描——提取代码中所有路由端点，与 task-inventory 中的任务做反向比对，找出**代码有但产品地图没有**的端点。

**排除项**（自动标注「基础设施/开发支持，不计入 EXTRA」）：
- 健康检查端点（/health, /ping, /ready, /metrics, /status）
- 认证/OAuth 回调端点（/auth/callback, /oauth/*, /login, /logout）
- API 文档端点（/api-docs, /swagger, /openapi, /redoc）
- 静态资源路由（/public/*, /static/*, /assets/*, /favicon.ico）
- 框架内置路由（Next.js `_next/*`, Rails `/rails/*`, Django `/admin/`, Vite `/@vite/*`）
- WebSocket 升级端点（/ws, /socket.io）

**输出**：每条 EXTRA 项，用户确认：
- `add_to_map` — 补录到产品地图（记录 INFO）
- `mark_remove` — 标记为 REMOVE_EXTRA 任务
- `ignore` — 合理遗留，忽略

---

### D0：应用可达性预检

**目的**：在启动 Playwright 测试前确认应用可访问，避免浪费时间。

**检测策略**：
1. 自动检测：Grep 代码中的 `PORT`、`listen`、`localhost`、`.env` 等配置，推测应用 URL
2. 若无法自动检测，询问用户提供应用 URL（如 `http://localhost:3000`）
3. 使用 Bash `curl -s -o /dev/null -w "%{http_code}" <URL>` 验证 HTTP 可达性
4. 返回非 2xx/3xx → 提示「应用未运行或不可达，请先启动应用后告知」，暂停 dynamic 阶段，等待用户确认后重试

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
- 向用户展示推导出的测试序列，确认后执行

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

**结果分类**（每个用例）：
- `pass` — 所有步骤成功
- `fail` — 某步骤失败（记录原因）
- `skip` — 前置条件不满足（如需要种子数据未准备）
- `error` — Playwright 自身错误（环境问题）

---

### D4：汇总 + 失败原因确认

对每个 `fail` 用例，向用户确认失败原因分类：
- `FIX_FAILING` — 代码缺陷，生成修复任务
- `ENV_ISSUE` — 测试环境问题（如数据库未初始化），不计入任务清单，记录 INFO
- `DEFERRED` — 用户标记暂缓，不生成任务

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
| Dynamic (D0-D4) | **跳过** | 动态测试留给 full 模式 |

**输出**：结果追加到 `static-report.json`（不覆盖之前的全量结果），同时返回给调用方（task-execute）用于写入 build-log.json 的 `verification` 字段。

---

## 输出文件结构

```
.allforai/product-verify/
├── static-report.json       # S1-S4: 静态覆盖状态
├── dynamic-report.json      # D2-D3: 动态测试结果
├── verify-tasks.json        # 待处理任务清单（IMPLEMENT / REMOVE_EXTRA / FIX_FAILING）
├── verify-report.md         # 可读版报告
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
  ]
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
4. **用户确认 EXTRA 归属** — EXTRA 代码是「合理遗留」「补录产品地图」还是「标记删除」，由用户逐条决定；skill 不自动判定
5. **动态失败需用户确认分类** — 测试失败可能是代码缺陷也可能是测试环境问题，必须逐条由用户确认后才写入 FIX_FAILING；不允许自动归类
