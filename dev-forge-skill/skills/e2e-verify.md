---
name: e2e-verify
description: >
  Use when the user wants to "run cross-project E2E tests", "verify end-to-end flows",
  "test cross-service scenarios", "e2e verification", "跨端验证", "端到端测试",
  "跨子项目验证", "业务流程测试", "跨端 E2E",
  or needs to derive and execute cross-sub-project E2E test scenarios from business flows.
  Requires project-manifest.json and running sub-project applications.
version: "1.4.0"
---

# E2E Verify — 跨端验证

> 从业务流推导跨子项目场景，Playwright / Maestro 跨端执行，验证业务完整性

## 目标

以 `business-flows.json` 和 `project-manifest.json` 为输入，验证跨子项目的业务完整性：

1. **场景推导** — 从 business-flows 提取跨角色/跨子项目流程
2. **端点映射** — 每个流程步骤映射到具体子项目的 URL + 操作
3. **Playwright（Web 端）/ Maestro（移动原生端）执行** — 跨子项目浏览器自动化测试
4. **失败分类** — 自动分类失败原因（代码缺陷 / 环境问题 / 暂缓）
5. **报告输出** — 按子项目汇总结果 + 需修复的问题

---

## 定位

```
product-verify（单端验收）   e2e-verify（跨端验证）
验证单个子项目的功能覆盖     验证跨子项目的业务流程完整性
静态扫描 + 动态测试         仅动态测试（Playwright + Maestro）
不涉及跨项目               跨多个子项目 + 角色
```

**前提**：
- 必须有 `.allforai/project-forge/project-manifest.json`
- 必须有 `.allforai/product-map/business-flows.json`（或 `flow-index.json`）
- 各子项目应用必须正在运行

### 测试工具路由

根据子项目类型自动选择测试工具：

| 子项目类型 | 测试工具 | 执行方式 |
|-----------|---------|---------|
| `admin` / `web-customer` / `web-mobile` | **Playwright** | MCP browser_* 工具 |
| `mobile-native` (Flutter / Expo / RN) | **Maestro** | CLI `maestro test` |
| `backend` | **curl / HTTP** | Bash API 调用 |

**工具探测**：
- Playwright: 检测 `mcp__playwright__browser_navigate` 或 `mcp__plugin_playwright_playwright__browser_navigate` 工具可用性
- Maestro: 检测 `which maestro` CLI 可用性（Bash）
- 移动端无 Maestro → 降级策略：仅测后端 API 层 + 记录 `DEFERRED_NATIVE`

**Maestro 执行协议**：

1. **YAML 生成**：为每个移动端场景生成 Maestro flow YAML：
   ```yaml
   appId: {bundle_id from project-manifest}
   ---
   - launchApp
   - tapOn: "{element_text}"
   - assertVisible: "{expected_text}"
   - takeScreenshot: "{scenario_id}_{step}"
   ```

2. **执行**：`maestro test .allforai/project-forge/e2e-flows/{scenario_id}.yaml --format junit`

3. **结果收集**：解析 JUnit XML → 统一结果格式（与 Playwright 结果合并）

4. **截图**：Maestro 截图存储到 `.allforai/project-forge/e2e-screenshots/`

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
| 6V 诊断取代规则分类 | Step 3 | 失败不再按错误特征硬编码分类，LLM 从 6 个工程视角深度诊断根因，输出分类 + 修复线索 |
| 4D 跨端覆盖度闭环 | Step 3.5 | 按 Data/Interface/Logic/UX 四维度聚合跨端覆盖率，任一维度 < 85% 自动生成针对性修复任务 |
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
    mobile-native → 使用 Maestro 执行（见「测试工具路由」）
    backend → 作为 API 提供者，通过 API 调用验证
  → 输出进度: 「E2E 场景 ✓ 正向 {N} + 负向 {M}」（不停，场景列表在 Step 3 批量确认中展示）
  → 写入 .allforai/project-forge/e2e-scenarios.json
  ↓
Step 1.5: 场景补全审查（OpenRouter 可用时）
  将 Step 1 场景列表摘要 + 业务流关键信息发给 Gemini
  调用: mcp__plugin_product-design_ai-gateway__ask_model(task: "research_synthesis", model_family: "gemini", temperature: 0.5)
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
Step 1.7: 视觉回归基准准备（stitch-index.json 存在时）
  跳过条件：`<BASE>/ui-design/stitch-index.json` 不存在
  1. 读取 stitch-index.json，获取 status=success 的屏幕 + route_path
  2. 将 stitch/*.png 复制到 `.allforai/product-verify/visual-regression/baseline/`
  3. 在 Step 2（Playwright 场景执行）中，对每个有基准的路由：
     a. 导航到 route_path
     b. 截取实际渲染截图 → `visual-regression/actual/`
     c. 像素级对比（pixelmatch，阈值参考）：
        根据组件重要性和视觉精度要求动态判定阈值
  4. 输出 `visual-regression/visual-regression-report.json`
  5. 无基准截图 → 跳过，不影响其他 E2E 场景
  ↓
Step 2: 场景执行（Playwright，并行调度）
  **并行策略**：按数据隔离性分组，使用 Agent tool 并行执行：
    - 数据无交叉的场景 → 分组到不同 Agent，每个 Agent 使用独立 browser context
    - 共享数据的场景 → 分到同一 Agent 内串行
    - 负向场景单独分组（避免污染正向场景数据）
  调度方式：单条消息发出 N 个 Agent 调用（N = min(场景分组数, 4)）
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
Step 3: 6V 审计与自动分类
  Agent 对执行失败的步骤进行 6V 深度诊断（以 design.json + experience-map.json 为审计基准）：

  **6V 诊断维度**：
  1. **Contract (V1)**: 失败是否源于前后端字段名/类型/路径不一致（契约漂移）？
     - 基准: design.json 中的 API 端点定义 + api-contracts.json
     - 诊断: Read 前端调用代码 + 后端 handler 代码，比对字段名和请求格式
     → 分类: `CONTRACT_SYNC`（需同步 design.json 并级联更新下游）
  2. **Conformance (V2)**: 是否是环境不可达、超时或数据库连接问题？
     - 诊断: 分析错误日志中的网络/连接/超时特征
     → 分类: `ENV_ISSUE`
  3. **Correctness (V3)**: 代码逻辑是否未按 design.json 规格实现？
     - 基准: design.json 中对应功能的 business rules + 状态机设计
     - 诊断: Read handler 代码，对比 task.rules 和 task.exceptions 是否落地
     → 分类: `FIX_REQUIRED`
  4. **Consistency (V4)**: 跨子项目的数据状态是否一致？
     - 诊断: 前端展示的数据是否与后端 API 返回一致、子项目 A 写入的数据是否在子项目 B 正确展示
     → 分类: `FIX_REQUIRED`（标注数据流断裂点）
  5. **Capability (V5)**: 是否是性能/SLA 不达标导致的超时或渲染失败？
     - 基准: task.sla 定义的响应时间
     - 诊断: 分析 duration_ms 与 SLA 基准的偏差
     → 分类: `FIX_REQUIRED`（标注 SLA 基准值）
  6. **Context (V6)**: 失败点是否位于用户旅程的关键情感触点？
     - 基准: journey-emotion.json 中的情感标注
     - 诊断: 失败步骤是否对应焦虑/沮丧触点
     → 影响: 根据上下文判定是否提升优先级（不一律 critical）

  **Agent 诊断流程**（并行调度）：
  失败步骤 ≥ 3 个时，使用 Agent tool 并行诊断（每个 Agent 处理 1-2 个失败项）：
  对每个失败步骤:
    1. Read 失败截图 + browser 错误日志
    2. Read 对应子项目的代码文件（前端组件 / 后端 handler）
    3. 加载 design.json 对应节点的规格定义
    4. 诊断根因（6V 维度作为参考框架，不局限于预设分类），输出:
       { "step_ref": "E2E-001.step2",
         "primary_cause": "V1|V2|V3|V4|V5|V6",
         "classification": "FIX_REQUIRED|ENV_ISSUE|CONTRACT_SYNC",
         "diagnosis": "一句话诊断结论",
         "evidence": "代码位置 + 规格引用",
         "fix_hint": "修复方向建议",
         "emotion_escalation": true|false }

  **批量确认展示**:
    ## E2E 验证结果 (6V 诊断)

    场景列表（Step 1 推导）:
    | 场景 | 类型 | 来源 | 步骤数 | 结果 |
    |------|------|------|--------|------|
    | {name} | 正向/负向 | BF-{id} / UC-{id} | {N} | ✓/✗ |

    通过: {N}/{M} 场景

    失败项（6V 诊断详情）:
    | 场景 | 失败步骤 | 主因维度 | 诊断结论 | 分类 | 修复线索 |
    |------|---------|---------|---------|------|---------|
    | E2E-001 | Step 2 | V1 Contract | 前端 userName ≠ 后端 user_name | CONTRACT_SYNC | customer-web/api.ts:15 |
    | E2E-003 | Step 3 | V3 Correctness | 库存扣减未实现 | FIX_REQUIRED | api-backend/orders.ts:42 |
    | E2E-N01 | Step 1 | V2 Conformance | 端口 3002 不可达 | ENV_ISSUE | 检查 customer-web 启动状态 |

    → 自动采纳全部建议分类（不停）

  ### 规模自适应

  根据场景总数调整 Step 3 展示策略：
  - **小规模**（≤15 个场景）：逐条展示完整场景表 + 6V 诊断详情
  - **中规模**（16-40 个场景）：按流程类型分组，展示计数 + 仅失败项 6V 详情
  - **大规模**（>40 个场景）：统计概览 + 仅展示 FIX_REQUIRED 和 CONTRACT_SYNC 项

  ↓
Step 3.5: 跨端数据流闭环追踪 (Cross-Project Data Flow Tracing)
  **目的**：跟踪业务实体在跨子项目流转中的数据完整性，验证每个环节的输入 = 上游输出。
  **基准**：business-flows.json 中涉及跨子项目的 flow
  **验证流程**：
  对每条跨端 flow，在 Step 2 场景执行时同步追踪数据：
  1. **写入端验证**：子项目 A 创建/修改实体 → API 调用获取返回数据快照
  2. **传输验证**：等待数据同步（事件/API/轮询） → 验证中间状态
  3. **消费端验证**：子项目 B 读取/展示该实体 → Playwright 截图 + API 验证
  4. **一致性比对**：
     - 字段名一致：A 端 `user_name` vs B 端 `userName` → CONTRACT_DRIFT
     - 值精度一致：A 端金额 `100.50` vs B 端显示 `100.5` → PRECISION_LOSS
     - 时间一致：A 端 `2024-01-15T10:30:00Z` vs B 端 `1 小时前` → DISPLAY_OK
     - 关联数据完整：A 端创建的子实体在 B 端是否全部展示？
  **断裂检测**：
  - 某实体在 B 端查不到 → DATA_FLOW_BREAK（严重）
  - 字段值不一致 → DATA_INCONSISTENCY（需排查同步机制）
  - 关联数据缺失 → RELATION_BREAK（外键或嵌套数据丢失）
  → 输出进度: 「Step 3.5a 跨端数据流 ✓ flows:{N} breaks:{M}」
  ↓
Step 3.6: 跨端状态机完备性验证 (Cross-Project State Machine Verification)
  **目的**：验证跨子项目的状态流转链是否完整可达。
  **基准**：business-flows.json 状态流转序列 + task.outputs.states
  **验证逻辑**：
  1. 提取所有跨端状态转换（如 A 端 PENDING → B 端 APPROVED → A 端 CONFIRMED）
  2. 对每个转换链，验证：
     - 触发条件在 A 端执行后，B 端是否收到状态变更？
     - B 端操作后，A 端的状态是否同步更新？
     - 终态记录在各端的展示是否一致？
  3. 跨端死胡同检测：
     - A 端发起审批 → B 端无审批入口 → CROSS_PROJECT_DEAD_END
     - B 端审批通过 → A 端仍显示待审批 → STATE_SYNC_FAILURE
  → 输出进度: 「Step 3.6 跨端状态 ✓ transitions:{N} failures:{M}」
  ↓
Step 3.7: 4D 跨端覆盖度闭环审计
  **目的**：Step 2 执行完毕后，从 4D 维度审计跨端业务的完整度，发现场景级别无法暴露的系统性缺口。

  **4D 跨端审计基准**：
  - **Data (D1)**: 子项目 A 写入的数据是否在子项目 B 正确读取？实体关系是否跨端一致？
    基准: entity-model.json 中的实体定义 + 关联关系
  - **Interface (D2)**: 跨子项目 API 调用的请求/响应格式是否与 api-contracts.json 一致？
    基准: design.json 中每个子项目的 API 端点列表
  - **Logic (D3)**: 跨端业务流中的状态流转是否完整？（如：A 端创建 → B 端审批 → A 端确认）
    基准: business-flows.json 中定义的状态流转序列
  - **UX (D4)**: 跨端切换时用户体验是否连贯？（同一数据在不同端的展示是否一致）
    基准: experience-map.json 中的跨端 screen 关联

  **闭环逻辑**：
  Agent 汇总 Step 2 所有场景的通过/失败结果，按 4D 维度聚合：
  | 维度 | 覆盖率 | 薄弱环节 |
  |------|--------|---------|
  | Data | {N}% | {列出数据不一致的实体对} |
  | Interface | {N}% | {列出契约不匹配的 API} |
  | Logic | {N}% | {列出状态流转断裂的业务流} |
  | UX | {N}% | {列出跨端展示不一致的界面} |

  **闭环判定**：
  - 4D 每维度 ≥ 85% → E2E_PASS
  - 任一维度 < 85% → 生成针对性 FIX 任务（标注维度 + 涉及子项目 + 修复方向）
  - CONTRACT_SYNC 类任务自动触发 design.json 同步建议

  → 输出进度: 「Step 3.5 4D 闭环 ✓ D:{d}% I:{i}% L:{l}% U:{u}%」
  ↓
Step 4: 报告生成
  写入:
    .allforai/project-forge/e2e-report.json — 机器版（含 6V 诊断 + 4D 覆盖度矩阵）
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
      "six_v_diagnosis": {
        "primary_cause": "V3",
        "diagnosis": "商品列表查询未包含新上架商品（缺少 status=active 过滤）",
        "evidence": "customer-web/src/api/products.ts:28 → 缺少 status 参数",
        "fix_hint": "添加 ?status=active 查询参数或修改后端默认过滤逻辑",
        "emotion_escalation": false
      },
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
  },
  "four_d_coverage": {
    "data": { "rate": 0.92, "weak_points": [] },
    "interface": { "rate": 0.85, "weak_points": ["GET /api/products 缺少 status 过滤"] },
    "logic": { "rate": 0.88, "weak_points": [] },
    "ux": { "rate": 0.90, "weak_points": [] },
    "verdict": "E2E_PASS"
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
| mobile-native (RN) | **Maestro** | 原生 | 消费方（原生应用视角） |
| mobile-native (Flutter) | **Maestro** | 原生 | 消费方（原生应用视角） |

**混合场景处理**：
- Web 端步骤 → Playwright 自动执行
- API 步骤 → Bash curl 执行
- Flutter / RN 端步骤 → Maestro 执行（见「测试工具路由」），跨端数据一致性通过 API 层验证
- Maestro 不可用时 → 降级为仅测后端 API 层 + 记录 `DEFERRED_NATIVE`

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

### 3. 诊断驱动分类

失败诊断以 6V 维度为参考框架，但不局限于预设分类。可识别跨维度问题和新类型根因。输出分类 + 修复线索，写入决策日志。

### 4. 不修改代码

发现问题只记录到报告，不自动修复。按子项目汇总需修复的问题供后续处理。

### 5. 原生端降级处理

mobile-native 子项目优先使用 Maestro 执行自动化测试。Maestro 不可用时，降级为仅测后端 API 层 + 记录 `DEFERRED_NATIVE`，通过 API 层验证数据一致性作为替代。
