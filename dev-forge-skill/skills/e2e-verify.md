---
name: e2e-verify
description: >
  Use when the user wants to "run cross-project E2E tests", "verify end-to-end flows",
  "test cross-service scenarios", "e2e verification", "跨端验证", "端到端测试",
  "跨子项目验证", "业务流程测试", "跨端 E2E",
  or needs to derive and execute cross-sub-project E2E test scenarios from business flows.
  Requires project-manifest.json and running sub-project applications.
version: "1.2.0"
---

# E2E Verify — 跨端验证

> 从业务流推导跨子项目场景，Playwright 跨端执行，验证业务完整性

## 目标

以 `business-flows.json` 和 `project-manifest.json` 为输入，验证跨子项目的业务完整性：

1. **场景推导** — 从 business-flows 提取跨角色/跨子项目流程
2. **端点映射** — 每个流程步骤映射到具体子项目的 URL + 操作
3. **Playwright 执行** — 跨子项目浏览器自动化测试
4. **失败分类** — 自动分类失败原因（代码缺陷 / 环境问题 / 暂缓）
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

## 增强协议（WebSearch + 4E+4V + OpenRouter）

> 通用框架见 `docs/skill-commons.md`，以下仅列本技能定制。

**WebSearch 关键词**：
- `"Playwright cross-project E2E testing {year}"`
- `"Patrol Flutter integration testing best practices"`
- `"contract testing microservices {year}"`

**4E+4V 重点**：
- **E3 Guardrails**: 从 task.exceptions 推导负向测试场景（异常路径 E2E）
- **behavior 视角**: 从 task.outputs.states 验证状态流转的跨端一致性

**OpenRouter 场景补全**：
- **`test_scenario_gap`** (Gemini) — Step 1 场景推导后，将场景列表 + 业务流摘要发给 Gemini：
  - 审查: 是否有明显遗漏的边界场景（并发操作、竞态条件、数据不一致）
  - Gemini 发散思维擅长想到"不显而易见"的边界情况
  - 输出: `{ "missing_scenarios": [{ "name", "type", "reason" }] }`
  - 补充的场景标记 `source: "cross_model_suggestion"`，用户在 Step 3 批量确认时可选择纳入或忽略
- OpenRouter 不可用 → 跳过，仅使用 Claude 推导的场景

---

## 跨端验证原则

> 以下原则在各步骤中强制执行。

| 原则 | 对应步骤 | 具体规则 |
|------|---------|---------|
| E2E 只覆盖关键业务路径 | 整体策略 | 仅验证 business-flows.json 中定义的跨端流程，不替代单元测试。每条 flow = 1 个 E2E 场景 |
| 场景来自业务流+用例 | Step 1 | 正向场景从 business-flows.json 推导（flow 主路径），负向场景从 use-case-tree.json 的 exception/boundary 用例推导。禁止自行编造场景 |
| API 契约一致性 | Step 2 | 前端调用的 API 路径/参数/响应格式必须与后端实际端点一致。不一致 = FIX_REQUIRED |
| Given/When/Then 格式 | Step 1 | 场景步骤必须遵循 Given（前置状态）/When（用户操作）/Then（预期结果），每步对应一个可断言的行为 |
| mock 阶段可先跑 | 整体时机 | mock-server 启动后即可运行前端 E2E（连 mock），不需要等后端完成。后端完成后切真实 API 重跑 |

---

## 工作流

```
前置: 加载
  project-manifest.json → 子项目列表 + 端口
  business-flows.json（或 flow-index.json）→ 业务流列表
  use-case-tree.json（可选）→ E2E 级别用例
  ↓
前置: 上游过期检测
  加载输入文件时，比较关键上游文件的修改时间与本技能上次输出的生成时间：
  - business-flows.json 在 e2e-report.json 生成后被更新
    → ⚠ 警告「business-flows.json 在 e2e-report.json 生成后被更新，数据可能过期，建议重新运行 product-map」
  - use-case-tree.json 在 e2e-report.json 生成后被更新
    → ⚠ 警告「use-case-tree.json 在 e2e-report.json 生成后被更新，数据可能过期，建议重新运行 use-case」
  - 仅警告不阻断，用户可选择继续或先刷新上游
  ↓
Step 0: 应用可达性检查
  逐子项目检查端口可访问:
    Bash curl -s -o /dev/null -w "%{http_code}" http://localhost:{port}/health
  全部可达 → 继续
  部分不可达：
    → 记录不可达项目为 ENV_ISSUE，跳过其场景（不停）
  ↓
Step 1: 跨端场景推导
  1-A 正向场景（从 business-flows）:
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
  1-B 负向场景（从 use-case-tree.json）:
    加载 use-case-tree.json（可选）
    提取 type = "exception" 和 "boundary" 的用例
    筛选涉及跨子项目的用例（通过 task_refs 关联到不同 sub_project）
    每个用例映射为负向 E2E 场景:
      场景名: "[负向] " + use_case.name
      priority: use_case.priority（exception 默认 high）
      步骤序列: 正常流前置步骤 + 触发异常的操作 + 验证错误处理
    示例:
      消费者下单(customer-web) → 库存不足(api-backend 返回 409)
      → 消费者看到错误提示(customer-web)
      商户修改价格(merchant-admin) → 消费者刷新看到新价格(customer-web)
    use-case-tree.json 不存在 → 跳过负向场景，仅用正向场景
  1-C 创新概念专属场景:
    加载 task-inventory.json 检查 innovation_tasks 字段：
    对每个 protection_level=core 的创新概念，若涉及跨子项目交互（如后端 API + 移动端 UI），自动生成专属 E2E 场景：
      source: "innovation_concept"
      priority: "critical"
      concept_ref: "IC001"
    创新专属场景在 Step 2 执行时优先运行
    不存在 innovation_tasks → 跳过
  各端测试差异:
    admin → Playwright 桌面视口
    web-customer → Playwright 桌面 + 移动视口
    web-mobile → Playwright 移动视口模拟
    mobile-native → 标记为需要 Detox/Maestro（Playwright 无法测）
    backend → 作为 API 提供者，通过 API 调用验证
  → 输出进度: 「E2E 场景 ✓ 正向 {N} + 负向 {M}」（不停，场景列表在 Step 3 批量确认中展示）
  → 写入 .allforai/project-forge/e2e-scenarios.json
  ↓
Step 1.5: 场景补全审查（OpenRouter 可用时）
  将 Step 1 场景列表摘要 + 业务流关键信息发给 Gemini
  调用: mcp__plugin_product-design_openrouter__ask_model(task: "research_synthesis", model_family: "gemini", temperature: 0.5)
  Gemini 审查是否遗漏:
    - 并发/竞态场景（两用户同时操作同一资源）
    - 跨时区/跨地区数据一致性
    - 网络中断后的恢复场景
    - 权限边界交叉（A 角色操作 B 角色的数据）
  补充场景标记 source: "cross_model_suggestion"
  → 追加到 e2e-scenarios.json，自动纳入（不停）
  → 输出进度: 「Step 1.5 场景补全 ✓ +{N} 建议场景」
  OpenRouter 不可用 → 跳过
  ↓
Step 2: 场景执行（Playwright）
  逐场景、逐步骤执行（不停，输出进度）:
    → 输出进度: 「E2E-001 ✓ / E2E-002 ✗ Step 2 / ...」
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
Step 3: 自动分类 + 批量确认
  自动分类规则（同 product-verify D4）:
    | 错误特征 | 自动建议 | 理由 |
    |---------|---------|------|
    | HTTP 5xx 响应 | FIX_REQUIRED | 服务端错误 = 代码缺陷 |
    | 404 on expected route | FIX_REQUIRED | 路由未实现 |
    | 元素未找到 / 断言失败 | FIX_REQUIRED | 页面实现不完整 |
    | Connection refused / timeout | ENV_ISSUE | 服务未启动或网络问题 |
    | Database error in response | ENV_ISSUE | 数据库未初始化 |
    | Auth redirect (unexpected) | FIX_REQUIRED | 权限配置错误 |
    | CORS error | ENV_ISSUE | 开发环境跨域配置 |

  批量确认展示:
    ## E2E 验证结果

    场景列表（Step 1 推导）:
    | 场景 | 类型 | 来源 | 步骤数 |
    |------|------|------|--------|
    | {name} | 正向/负向 | BF-{id} / UC-{id} | {N} |

    通过: {N}/{M} 场景

    失败项（自动建议分类）:
    | 场景 | 失败步骤 | 错误 | 建议分类 | 理由 |
    |------|---------|------|---------|------|
    | E2E-001 | Step 2 | Element not found | FIX_REQUIRED | 元素缺失 |

    → 自动采纳全部建议分类（不停）

  ### 规模自适应

  根据场景总数调整 Step 3 展示策略：
  - **小规模**（≤15 个场景）：逐条展示完整场景表
  - **中规模**（16-40 个场景）：按流程类型分组，展示计数 + 失败项详情
  - **大规模**（>40 个场景）：统计概览 + 仅展示失败和 critical 场景

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
      "type": "positive",
      "flow_ref": "BF-003",
      "use_case_ref": null,
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
    },
    {
      "id": "E2E-N01",
      "name": "[负向] 消费者购买库存不足商品 → 错误提示",
      "type": "negative",
      "flow_ref": null,
      "use_case_ref": "UC-EXC-003",
      "priority": "high",
      "steps": [
        {
          "seq": 1,
          "sub_project": "customer-web",
          "role": "consumer",
          "viewport": "desktop",
          "action": "尝试购买库存为 0 的商品",
          "url": "http://localhost:3002/products/out-of-stock",
          "operations": [
            { "type": "navigate", "url": "http://localhost:3002/products/out-of-stock" },
            { "type": "click", "selector": "text=购买" }
          ],
          "expected": "显示库存不足错误提示，不创建订单"
        },
        {
          "seq": 2,
          "sub_project": "api-backend",
          "role": "system",
          "action": "API 验证未创建订单",
          "operations": [
            { "type": "api_call", "method": "GET", "url": "http://localhost:3001/api/orders?latest=true" }
          ],
          "expected": "最新订单不包含库存不足商品"
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
  },
  "innovation_scenarios": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "concept_refs": []
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

### 1. 场景来自业务流和用例，不来自想象

正向 E2E 场景必须可追溯到 business-flows.json 中的具体流程。负向 E2E 场景必须可追溯到 use-case-tree.json 中的 exception/boundary 用例。不凭空编造测试场景。

### 2. 场景列表可追溯

场景从 business-flows 推导，执行后与结果一并展示。自动确认场景列表（不停）。

### 3. 失败自动分类

基于错误特征自动分类（FIX_REQUIRED / ENV_ISSUE / DEFERRED），写入决策日志。

### 4. 不修改代码

发现问题只记录到报告，不自动修复。按子项目汇总需修复的问题供后续处理。

### 5. 原生端降级处理

mobile-native 子项目的步骤在 Playwright 中无法执行。标记为手动验证点，通过 API 层验证数据一致性作为替代。
