---
name: e2e-verify
description: >
  Use when the user wants to "run cross-project E2E tests", "verify end-to-end flows",
  "test cross-service scenarios", "e2e verification", "跨端验证", "端到端测试",
  "跨子项目验证", "业务流程测试", "跨端 E2E",
  or needs to derive and execute cross-sub-project E2E test scenarios from business flows.
  Requires project-manifest.json and running sub-project applications.
version: "1.0.0"
---

# E2E Verify — 跨端验证

> 从业务流推导跨子项目场景，Playwright 跨端执行，验证业务完整性

## 目标

以 `business-flows.json` 和 `project-manifest.json` 为输入，验证跨子项目的业务完整性：

1. **场景推导** — 从 business-flows 提取跨角色/跨子项目流程
2. **端点映射** — 每个流程步骤映射到具体子项目的 URL + 操作
3. **Playwright 执行** — 跨子项目浏览器自动化测试
4. **失败分类** — 用户确认失败原因（代码缺陷 / 环境问题 / 暂缓）
5. **报告输出** — 按子项目汇总结果 + 需修复的问题

---

## 定位

```
product-verify（单端验收）   e2e-verify（跨端验证）
验证单个子项目的功能覆盖     验证跨子项目的业务流程完整性
静态扫描 + 动态测试         仅动态测试（Playwright）
不涉及跨项目               跨多个子项目 + 角色
```

**前提**：
- 必须有 `.allforai/project-forge/project-manifest.json`
- 必须有 `.allforai/product-map/business-flows.json`（或 `flow-index.json`）
- 各子项目应用必须正在运行

---

## 快速开始

```
/e2e-verify                 # 推导场景 + 执行全部
/e2e-verify full            # 同上
/e2e-verify plan            # 仅推导场景，不执行
/e2e-verify run             # 加载已有场景并执行
```

---

## 动态趋势补充（WebSearch）

除经典理论外，执行跨端验证时通过 WebSearch 补充最新测试实践：

**搜索关键词模板**：
- `"Playwright cross-project E2E testing {year}"`
- `"Patrol Flutter integration testing best practices"`
- `"contract testing microservices {year}"`
- `"E2E testing monorepo strategy {year}"`

**来源优先级**：P1 官方文档（Playwright/Patrol/Detox）> P2 知名作者（Dodds, Cohn）> P3 技术媒体 > P4 社区帖

**采纳决策**：记录到 `.allforai/project-forge/trend-sources.json`，标注 ADOPT / REJECT / DEFER + 理由。

---

## 跨端验证理论支持

> 详见 `docs/dev-forge-principles.md` — 尾段：验证与交付

| 理论/框架 | 对应步骤 | 落地方式 |
|-----------|---------|---------|
| **Test Pyramid** (Cohn, 2009) | 整体策略 | E2E 在金字塔顶层，仅覆盖跨端关键业务路径，不替代单元测试 |
| **Test Trophy** (Dodds, 2019) | Step 1 场景推导 | 场景来自 business-flows 实际业务流，集成测试优先 |
| **Contract Testing** (Pact) | Step 2 API 验证步骤 | 前端→后端 API 调用的数据结构一致性验证 |
| **BDD** (North, 2006) | Step 1 场景格式 | 场景描述遵循 Given/When/Then，步骤对应业务行为 |
| **Shift-Left Testing** (Forrester, 2016) | 整体时机 | mock-server 阶段即可运行前端部分 E2E，不等后端完成 |

---

## 工作流

```
前置: 加载
  project-manifest.json → 子项目列表 + 端口
  business-flows.json（或 flow-index.json）→ 业务流列表
  use-case-tree.json（可选）→ E2E 级别用例
  ↓
Step 0: 应用可达性检查
  逐子项目检查端口可访问:
    Bash curl -s -o /dev/null -w "%{http_code}" http://localhost:{port}/health
  全部可达 → 继续
  部分不可达 → 列出不可达项目，AskUserQuestion:
    a. 用户启动后重试
    b. 跳过不可达项目的场景
    c. 终止
  ↓
Step 1: 跨端场景推导
  从 business-flows 提取跨角色/跨子项目流程
  每个 flow 映射为 E2E 场景:
    场景名: flow.name
    步骤序列: [
      { sub_project, role, action, url, input, expected_result }
    ]
  示例:
    商户上架商品(merchant-admin)
    → 消费者浏览(customer-web)
    → 消费者下单(customer-web + api-backend)
    → 商户查看订单(merchant-admin)
  各端测试差异:
    admin → Playwright 桌面视口
    web-customer → Playwright 桌面 + 移动视口
    web-mobile → Playwright 移动视口模拟
    mobile-native → 标记为需要 Detox/Maestro（Playwright 无法测）
    backend → 作为 API 提供者，通过 API 调用验证
  → AskUserQuestion 确认场景列表
  → 写入 .allforai/project-forge/e2e-scenarios.json
  ↓
Step 2: 场景执行（Playwright）
  逐场景、逐步骤执行:
    browser_navigate → 子项目 A 的 URL
    browser_snapshot → 获取页面状态
    browser_fill / browser_click → 执行操作
    browser_snapshot → 验证结果
    browser_navigate → 切换到子项目 B
    ...重复直到场景完成
  后端 API 验证步骤:
    Bash curl 调用 API → 检查响应状态和数据
  记录每步:
    status: pass | fail
    error: 错误信息（失败时）
    screenshot: 截图路径（失败时）
    duration_ms: 耗时
  ↓
Step 3: 失败分类
  逐失败项 AskUserQuestion:
    FIX_REQUIRED — 代码缺陷，需要修复
    ENV_ISSUE — 环境/数据问题，不计入报告
    DEFERRED — 暂缓，记录但不阻塞
  ↓
Step 4: 报告生成
  写入:
    .allforai/project-forge/e2e-report.json — 机器版
    .allforai/project-forge/e2e-report.md — 人类版
  按子项目汇总需修复的问题
```

---

## e2e-scenarios.json

```json
{
  "generated_at": "ISO8601",
  "source": "business-flows.json",
  "scenarios": [
    {
      "id": "E2E-001",
      "name": "商户上架 → 消费者购买 → 商户查看订单",
      "flow_ref": "BF-003",
      "priority": "high",
      "steps": [
        {
          "seq": 1,
          "sub_project": "merchant-admin",
          "role": "merchant",
          "viewport": "desktop",
          "action": "登录并进入商品管理",
          "url": "http://localhost:3000/products",
          "operations": [
            { "type": "navigate", "url": "http://localhost:3000/login" },
            { "type": "fill", "selector": "[name=email]", "value": "merchant@test.com" },
            { "type": "fill", "selector": "[name=password]", "value": "SeedForge2024!" },
            { "type": "click", "selector": "button[type=submit]" },
            { "type": "navigate", "url": "http://localhost:3000/products/new" },
            { "type": "fill", "selector": "[name=name]", "value": "E2E 测试商品" },
            { "type": "click", "selector": "button[type=submit]" }
          ],
          "expected": "商品创建成功，跳转到商品列表"
        },
        {
          "seq": 2,
          "sub_project": "customer-web",
          "role": "consumer",
          "viewport": "desktop",
          "action": "浏览并购买商品",
          "url": "http://localhost:3002/products",
          "operations": [
            { "type": "navigate", "url": "http://localhost:3002/products" },
            { "type": "snapshot", "verify": "页面包含 E2E 测试商品" },
            { "type": "click", "selector": "text=E2E 测试商品" },
            { "type": "click", "selector": "text=购买" }
          ],
          "expected": "订单创建成功"
        },
        {
          "seq": 3,
          "sub_project": "api-backend",
          "role": "system",
          "action": "API 验证订单数据一致性",
          "operations": [
            { "type": "api_call", "method": "GET", "url": "http://localhost:3001/api/orders?latest=true" }
          ],
          "expected": "最新订单包含 E2E 测试商品"
        },
        {
          "seq": 4,
          "sub_project": "merchant-admin",
          "role": "merchant",
          "viewport": "desktop",
          "action": "查看新订单",
          "url": "http://localhost:3000/orders",
          "operations": [
            { "type": "navigate", "url": "http://localhost:3000/orders" },
            { "type": "snapshot", "verify": "订单列表包含 E2E 测试商品" }
          ],
          "expected": "商户可以看到消费者的订单"
        }
      ]
    }
  ]
}
```

---

## e2e-report.json

```json
{
  "generated_at": "ISO8601",
  "summary": {
    "total_scenarios": 5,
    "pass": 3,
    "fail": 1,
    "partial": 1,
    "skipped": 0
  },
  "results": [
    {
      "scenario_id": "E2E-001",
      "scenario_name": "商户上架 → 消费者购买",
      "status": "fail",
      "steps": [
        { "seq": 1, "status": "pass", "duration_ms": 3200 },
        { "seq": 2, "status": "fail", "error": "商品未出现在列表中", "screenshot": "e2e/screenshots/E2E-001-step2.png", "duration_ms": 5100 },
        { "seq": 3, "status": "skip", "reason": "前置步骤失败" },
        { "seq": 4, "status": "skip", "reason": "前置步骤失败" }
      ],
      "failure_classification": "FIX_REQUIRED",
      "affected_sub_projects": ["customer-web", "api-backend"],
      "total_duration_ms": 8300
    }
  ],
  "by_sub_project": {
    "merchant-admin": { "involved_in": 4, "failures": 0 },
    "customer-web": { "involved_in": 3, "failures": 1 },
    "api-backend": { "involved_in": 2, "failures": 0 }
  }
}
```

---

## 各端测试差异

| 子项目类型 | 测试工具 | 视口 | 跨端 E2E 角色 |
|-----------|---------|------|---------------|
| backend | curl / HTTP client | — | API 提供者，通过 API 验证数据 |
| admin | Playwright | 桌面 (1280x720) | 操作发起方（管理操作） |
| web-customer | Playwright | 桌面 + 移动 | 消费方（浏览/购买） |
| web-mobile | Playwright | 移动 (375x812) | 消费方（移动端交互） |
| mobile-native (RN) | Detox / Maestro | 原生 | 消费方（原生应用视角） |
| mobile-native (Flutter) | Patrol / integration_test | 原生 | 消费方（原生应用视角） |

**混合场景处理**：
- Web 端步骤 → Playwright 自动执行
- API 步骤 → Bash curl 执行
- Flutter 端步骤 → Patrol 脚本执行（Patrol 支持类 Playwright 的 native interaction API，可自动化原生 UI 测试），跨端数据一致性通过 API 层验证
- React Native 端步骤 → Detox/Maestro 执行，跨端数据通过 API 层验证
- 原生端工具不可用时 → 降级为手动验证点 + API 层验证

---

## Playwright 执行策略

### 浏览器管理

```
每个场景使用独立 browser context:
  - 隔离 cookie / localStorage（不同子项目的登录态互不干扰）
  - 场景结束后关闭 context

跨子项目步骤:
  - 同一 context 内 navigate 到不同子项目 URL
  - 或创建多个 context（模拟不同用户/角色同时操作）
```

### 等待策略

```
每步操作前:
  browser_snapshot → 确认页面状态
  等待网络空闲（API 调用完成）
  等待目标元素可见

超时:
  单步操作: 10 秒
  单个场景: 120 秒（跨端场景步骤多）
  全部场景: 无总超时（逐场景执行）
```

### 失败处理

```
步骤失败时:
  1. browser_take_screenshot → 保存到 e2e/screenshots/
  2. 记录错误信息 + 页面 URL + 页面标题
  3. 后续步骤标记为 skip（前置失败）
  4. 继续下一个场景
```

---

## 输出文件

```
.allforai/project-forge/
├── e2e-scenarios.json              # Step 1 推导的场景
├── e2e-report.json                 # Step 4 测试结果（机器版）
├── e2e-report.md                   # Step 4 测试结果（人类版）
└── forge-decisions.json            # 追加 E2E 相关决策

e2e/screenshots/                    # 失败截图
```

---

## 5 条铁律

### 1. 场景来自业务流，不来自想象

所有 E2E 场景必须可追溯到 business-flows.json 中的具体流程。不凭空编造测试场景。

### 2. 用户确认场景列表

Step 1 推导出的场景列表必须经用户确认后才执行。用户可以增删场景。

### 3. 失败分类需用户确认

测试失败可能是代码缺陷、环境问题或暂缓功能。必须逐条由用户确认分类，不允许自动归类。

### 4. 不修改代码

发现问题只记录到报告，不自动修复。按子项目汇总需修复的问题供后续处理。

### 5. 原生端降级处理

mobile-native 子项目的步骤在 Playwright 中无法执行。标记为手动验证点，通过 API 层验证数据一致性作为替代。
