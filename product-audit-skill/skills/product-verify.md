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
version: "1.0.0"
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
```

**前提**：必须先运行 `product-map`，生成 `.allforai/product-map/product-map.json`。

---

## 快速开始

```
/product-verify           # 静态验收（默认，无需应用运行）
/product-verify static    # 同上，显式指定
/product-verify dynamic   # 动态验收（需要应用正在运行）
/product-verify full      # 静态 + 动态完整验收
/product-verify refresh   # 清除决策缓存，重新完整验收
```

---

## 模式说明

| 模式 | 说明 | 是否需要应用运行 |
|------|------|----------------|
| `static` | 代码扫描，检查 API/组件/约束覆盖 | 否 |
| `dynamic` | Playwright 浏览器测试 | 是 |
| `full` | 静态 + 动态 | dynamic 阶段需要 |
| `refresh` | 清除 verify-decisions.json 缓存，重新完整运行 | 视模式而定 |

---

## 工作流

```
前置检查：
  product-map.json 必须存在（否则终止）
  screen-map.json 可选（存在则启用 S2）
  use-case-tree.json 可选（dynamic 优先使用，否则自动推导）
  verify-decisions.json 存在则加载历史决策
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

**数据加载**：从 `.allforai/product-map/task-inventory.json` 读取所有任务（或通过 task-index.json 两阶段加载）。

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

**数据来源**：`product-map.json` 中每个任务的 `constraints` 字段。

**扫描策略**：对每条约束，Grep 代码库中的：
- 校验器（validator, validate, schema）
- 中间件（middleware, guard, interceptor, policy）
- 条件判断中的约束关键词

**覆盖状态**：
- `covered` — 找到对应校验逻辑
- `missing_constraint` — 未找到（→ IMPLEMENT 候选，高风险约束优先）

**输出**：写入 `static-report.json` 的 `constraint_coverage` 字段。

---

### S4：Extra 代码扫描

**策略**：反向扫描——提取代码中所有路由端点，与 task-inventory 中的任务做反向比对，找出**代码有但产品地图没有**的端点。

**排除项**：
- 健康检查端点（/health, /ping, /metrics）→ 自动标注「开发支持，不计入 EXTRA」
- 认证/OAuth 回调端点 → 自动标注「基础设施，不计入 EXTRA」

**输出**：每条 EXTRA 项，用户确认：
- `add_to_map` — 补录到产品地图（记录 INFO）
- `mark_remove` — 标记为 REMOVE_EXTRA 任务
- `ignore` — 合理遗留，忽略

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

**执行原则**：
- 每个用例独立运行，不相互依赖
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

## 输出文件

| 文件 | 内容 |
|------|------|
| `static-report.json` | 每个 task/screen/constraint 的覆盖状态 |
| `dynamic-report.json` | 每个用例的测试结果（pass/fail/skip/error） |
| `verify-tasks.json` | 待处理任务清单（IMPLEMENT / REMOVE_EXTRA / FIX_FAILING） |
| `verify-report.md` | 可读版报告 |
| `verify-decisions.json` | 用户决策日志（S4 EXTRA 归属确认 + D4 失败原因确认） |

---

## 5 条铁律

1. **product-map 是验收基准** — 静态验收以 product-map.json 为唯一真值，不引入额外需求来源；有争议的功能先补充到产品地图，再重跑验收
2. **只报告不修改代码** — 发现缺口只标记到 verify-tasks.json，不自动生成、修改或删除任何实现代码
3. **频次决定优先级** — IMPLEMENT 任务按 frequency 排序，高频漏实现优先于低频；低频漏实现仅列出不主动建议
4. **用户确认 EXTRA 归属** — EXTRA 代码是「合理遗留」「补录产品地图」还是「标记删除」，由用户逐条决定；skill 不自动判定
5. **动态失败需用户确认分类** — 测试失败可能是代码缺陷也可能是测试环境问题，必须逐条由用户确认后才写入 FIX_FAILING；不允许自动归类
