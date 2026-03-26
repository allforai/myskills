---
description: "测试驱动的质量锻造：审计测试缺口 → 补测试 → 修 bug → 直到全绿。覆盖测试金字塔全层级（unit / component / integration / platform-ui / e2e-chain）。模式: full / analyze / fix"
argument-hint: "[mode: full|analyze|fix] [--sub-project <name>] [--module <name>]"
allowed-tools: ["Read", "Write", "Edit", "Grep", "Glob", "Bash", "Task", "AskUserQuestion", "Agent"]
---

# TestForge — 测试驱动的质量锻造

用户请求: $ARGUMENTS

## 插件根目录

所有文档路径基于插件安装目录: `${CLAUDE_PLUGIN_ROOT}`

## 定位

```
product-verify  "代码实现了功能吗？"       → 只报告不改代码
testforge       "测试代码够好吗？够全吗？" → 审计 + 生成测试 + E2E 链 + 修 bug + 全绿
```

testforge 审查的是**项目自身的测试代码**，用 FVL 三维验证发现缺口。覆盖**测试金字塔全层级**：

若 `product-map.json` 含 `experience_priority.mode = consumer | mixed`，testforge 还必须额外审计一件事：测试是否真正守护了"成熟用户产品体验"，而不是只守护功能存在性。

```
     ╱ E2E Chains ╲        ← 跨子项目业务链（Path B）
    ╱  Platform UI  ╲       ← 同一场景 × N 个平台的 UI 自动化（Path C）
   ╱   Integration   ╲      ← 多模块协作测试（Path D）
  ╱     Component     ╲     ← UI 组件渲染 + 交互 + Flutter widget test（Path A）
 ╱        Unit         ╲    ← 函数、store、service、validation（Path A）
```

不只补测试，还主动推导"没人想到但该有"的场景，发现业务 bug 直接修复，循环至全绿。

## 模式路由

- **无参数 或 `full`** → 完整锻造：Phase 0 → 1 → 2 → 3 → 4 → 5 → 6
- **`analyze`** → 仅审计：Phase 0 → 1 → 2 → 3 → Step 4.0(静态接缝预检) → Step 4.0.5(Chain 0 冒烟) → 6（不补测试不修代码，但接缝预检+冒烟纳入审计）
- **`fix`** → 仅锻造：Phase 0 → 4 → 6（用已有 `testforge-analysis.json`，若分析文件时间早于最新 git commit 则警告并建议重新 analyze；若文件不存在则报错：「未找到 testforge-analysis.json，请先运行 `/testforge analyze`」）

`--sub-project <name>` 限制只处理指定子项目。
`--module <name>` 限制只处理指定模块。

---

## 上游消费链（Front-load Decisions）

Phase 0 的决策项可从上游产物自动获取，**已从上游获取的决策直接采用（展示一行摘要），仅缺失或冲突项才询问用户**：

```
优先级 1: .allforai/testforge/testforge-decisions.json（自身 resume 缓存）
    ↓ 不存在或过期
优先级 2: .allforai/project-forge/project-manifest.json（project-setup 产出）
    ↓ 不存在
优先级 3: 自动检测（扫描 package.json / go.mod / pubspec.yaml + 测试配置文件）
    ↓ 无法推断
优先级 4: AskUserQuestion 询问用户
```

---

## Phase 0：项目画像 + 测试基础设施探测

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/testforge/phase0-profile.md

---

## Phase 1：纵向审计 — tests ↔ 上游基准

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/testforge/phase1-vertical-audit.md

---

## Phase 2：横向审计 — 兄弟测试交叉验证

> "各子项目的测试之间一致吗？"

### 五类横向闭环

**H1: Mock 数据一致性**

后端测试 mock 的响应结构 ↔ 前端测试 mock 的请求/响应结构。
两边 mock 同一个 API，字段名和数据类型要一致。
不一致 = `MOCK_DRIFT`（测试绿了但上线会炸）。

扫描方式：
- Grep 前端测试文件中的 mock 返回值（`vi.fn()`, `mockResolvedValue`, `msw handlers` 等）
- Grep 后端测试文件中 mock 的响应结构
- 比对同一 API 端点的 mock 数据结构

**H2: 实体 CRUD 覆盖对称性**

跨角色看同一实体：后端对某实体有哪些 CRUD 测试？各前端有哪些？
哪些操作没有任何端测到？= `CROSS_PROJECT_GAP`

**H3: 业务规则测试归属**

一条约束可能涉及后端 + 前端（如"订单超时自动取消"）。
后端有定时任务/事件测试吗？前端有状态变更展示测试吗？
只测了一端 = `RULE_PARTIAL`

**H4: 错误处理对称性**

后端返回 4xx/5xx 错误 → 前端有没有测到这些错误码的 UI 处理？
后端测了错误返回但前端没测错误处理 = `ERROR_ASYMMETRY`

**H5: 跨站业务链完整性**（有 business-flows 或 ≥2 个前端子项目时执行）

从 API 路由表和页面路由表出发，按业务域分组，检查实体从"创建"到"终态"的全链路是否有跨站 E2E 测试覆盖。

### 输出

追加到 `testforge-analysis.json` 的 `horizontal_gaps` 字段。

→ 输出进度：「Phase 2 横向审计 ✓ MOCK_DRIFT:{a} CROSS_GAP:{b} RULE_PARTIAL:{c} ERROR_ASYM:{d} CHAIN:{e}」

---

## Phase 3：负空间推导

> "没人想到但该有的测试场景"

### 四层推导

**Layer A: 代码级负空间**（始终执行）— 并发竞态、数据边界、状态不一致、权限越界、外部依赖失败

**Layer B: 业务级负空间**（有 business-flows 时执行）— 流程中断、逆向操作、时序依赖、资源耗尽

若 `experience_priority.mode = consumer | mixed`，额外推导：下一步缺失、结果回流失败、持续关系断裂

**Layer C: 跨端负空间**（有 role-profiles 时执行）— 跨角色并发操作、权限变更时的会话处理

**Layer D: E2E 链负空间**（有 business-flows 且 ≥2 子项目时执行）— 链路断裂、角色越权、数据穿透延迟

### 标记与收敛

- 所有推导场景标记 `[DERIVED]`
- 总负空间场景 ≤ Phase 1 缺口数的 50%（CG-2 防膨胀）

→ 输出进度：「Phase 3 负空间 ✓ Layer A:{a} Layer B:{b} Layer C:{c} Layer D:{d}」

---

## Phase 4：锻造循环（Forge-Fix Loop）

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/testforge/phase4-forge-loop.md

---

## Phase 5：外循环校验

> "走了这么多步，还在正确的路上吗？"

锻造循环完成后，回到起点验证意图保真。

**OL-D1 意图保真**：读 `concept-baseline.json` → 核心角色的核心任务有测试守护吗？

**OL-D2 约束执行**：读 `constraints.json` → 硬约束有测试穿透验证吗？

**OL-D3 角色完整性**：读 `role-profiles.json` → 每个角色的 CRUD + 核心业务流有测试覆盖吗？

**收敛控制（CG-3）**：追加缺口 ≤ 总缺口数 20%，最多 1 轮。

**追加项锻造**：汇总 OL-D1/D2/D3 的追加缺口，遵循 A → D → C → B 顺序再跑一轮 Phase 4。

**无上游文档时**：Phase 5 整体跳过。

→ 输出进度：「Phase 5 外循环 ✓ 追加缺口:{N} 修复:{M}」

---

## Phase 6：报告输出

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/testforge/phase6-report.md

---

## 测试代码规范（跨技术栈通用原则）

1. **行为驱动命名** — describe/group 按功能分组，不按方法名
2. **Given-When-Then 结构** — 准备数据 → 执行操作 → 验证结果
3. **表驱动优先** — 同一逻辑的多个输入用 table-driven / parameterized
4. **Mock 最小化** — 只 mock 外部依赖，不 mock 被测模块内部方法
5. **一个测试一个断言意图** — 可以有多个 expect，但验证同一个行为
6. **错误路径必测** — 每个 catch/error return/throw 至少一个测试
7. **E2E 链数据自给自足** — 每条链在测试内创建所需数据
8. **导航路径封装** — 反复出现的导航操作抽取为 helper/Page Object
9. **认证状态复用** — 多测试共享同一登录态

---

## 铁律

> 详见 ${CLAUDE_PLUGIN_ROOT}/docs/testforge/iron-rules.md

核心铁律速查（完整版在上述文档中）：

| # | 规则 |
|---|------|
| 1 | 测试质量优于数量 |
| 5 | CG-1 收敛：max 3 轮、单调递减 |
| 10 | 不破坏已有测试 |
| 14 | E2E 选择器先看后写 |
| 16 | E2E = 模拟用户，严禁捷径 |
| 17 | Chain 0 是一切的前提（Step 4.0.5 前置执行，不等到 Path B） |
| 21 | E2E 断言必须穿透数据流 |
| 22 | 接缝层是 bug 密度最高的地方 |
| 24 | 断言源分离：期望值来自上游文档，不来自实现代码 |
| **25** | **控件数据完整性必须有测试守护：不仅测"能渲染"还要测"有数据"，禁止硬编码假数据** |
