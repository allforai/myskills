# Bootstrap Thought Tests

5 个虚拟项目，覆盖所有入口路径 + 新特性（fan_out / soft goto / hooks）。
每个项目追踪：入口条件 → bootstrap 生成 → orchestrator 执行路径。

---

## Test 1: pnpm Monorepo 跨栈复刻（入口 B：has_code, no artifacts）

**项目**: `shopnow` — React + Express 电商平台，pnpm workspaces，4 个 package
```
shopnow/
├── pnpm-workspace.yaml
├── packages/
│   ├── web/          # React 18, Vite
│   ├── api/          # Express + Prisma + PostgreSQL
│   ├── shared/       # TypeScript 类型定义
│   └── admin/        # React 18, 后台管理
```

**用户选择**: `b) 跨栈复刻` → 目标: SwiftUI + Vapor (Swift)

### Bootstrap 应生成的节点

| 节点 ID | 能力模板 | fan_out? |
|---------|---------|----------|
| `discover-shopnow` | discovery | - |
| `analyze-shopnow` | product-analysis | - |
| `generate-artifacts` | generate-artifacts | - |
| `plan-translation-dag` | (内置逻辑) | - |
| `translate-packages` | translate | **fan_out** ✓ |
| `verify-swift-build` | compile-verify | - |
| `verify-tests` | test-verify | - |
| `verify-visual` | visual-verify | - |

### fan_out 测试点

`translate-packages` 节点的 frontmatter:
```yaml
fan_out:
  source: .allforai/bootstrap/bootstrap-profile.json
  path: $.modules[*]
  parallel: true
```

orchestrator 应该：
1. 读 bootstrap-profile.json → 找到 4 个 modules (web, api, shared, admin)
2. 起 4 个 subagent，每个收到 `{{FAN_OUT_ITEM}}` = `{"id":"M001","path":"packages/web","role":"frontend",...}`
3. 受 `max_concurrent_nodes: 3` 限制，先跑 3 个，完成一个再补第 4 个
4. 全部 success → 节点 success；任一 failure → 节点 failure

### soft goto 测试点

`verify-swift-build` 完成后返回：
```json
{
  "status": "success",
  "suggest_next": "verify-tests",
  "suggest_reason": "build succeeded, shared package has unit tests worth running first"
}
```

orchestrator 正常会按 DAG 走，但这个 hint 让它优先跑 test-verify 而非 visual-verify。

### hooks 测试点

默认 hooks 即可，无 custom hook。验证 pre_node `check_requires entry` 阻止 translate 在 plan-dag 完成前执行。

---

## Test 2: 空项目从零构建（入口 D：no code, no artifacts）

**项目**: `medtrack` — 空目录，只有 README.md 写了一句话"慢病管理 App"

**用户选择**: `d) 从零构建`，目标技术栈：Flutter + Go，业务领域：医疗

### Bootstrap 应生成的节点

| 节点 ID | 能力模板 | 说明 |
|---------|---------|------|
| `product-concept` | product-concept | **起点**（从零构建） |
| `product-map` | product-analysis | - |
| `generate-artifacts` | generate-artifacts | - |
| `design-ui` | ui-design | - |
| `feature-gap` | feature-gap | - |
| `implement-flutter` | translate | 前端实现 |
| `implement-go-api` | translate | 后端实现 |
| `verify-flutter-build` | compile-verify | - |
| `verify-go-build` | compile-verify | - |
| `verify-tests` | test-verify | - |

### 关键验证

- 入口问题应该是"从零构建"格式（包含产品愿景、技术栈、业务领域选择）
- `product-concept` 是 root 节点（entry_requires 为空）
- 无 fan_out（两个实现节点是独立节点，不是同一模板展开）
- verify-flutter-build 和 verify-go-build 可以并行（output_files 不交叉）

### hooks 测试点

医疗项目可能需要 custom hook：
```json
{
  "hooks": {
    "post_node": [
      "check_requires exit",
      "loop_detection",
      "progress_monotonicity",
      "node_timeout",
      {"command_succeeds": "grep -r 'TODO.*HIPAA' . | wc -l | xargs test 0 -eq", "on_fail": "warn"}
    ]
  }
}
```
每个节点执行完检查是否有未处理的 HIPAA 相关 TODO。这是一个 bootstrap 根据 `business_domain: "医疗"` 自动加的 custom hook。

---

## Test 3: 已有代码+产物，做验收（入口 A：has_code + has_product_artifacts）

**项目**: `taskflow` — Next.js + Supabase 任务管理 SaaS，已经跑过 product-design 全流程

```
taskflow/
├── .allforai/
│   ├── product-map/task-inventory.json    ✓
│   ├── experience-map/experience-map.json ✓
│   ├── use-case/use-case-tree.json        ✓
│   └── ui-design/ui-design-spec.md        ✓
├── src/                                   ✓ (Next.js app)
├── supabase/                              ✓
└── package.json
```

**用户选择**: `h + i + j`（功能验收 + 视觉验收 + 质量检查）

### Bootstrap 应生成的节点

| 节点 ID | 能力模板 | 说明 |
|---------|---------|------|
| `verify-static` | product-verify | 静态校验（use-case 覆盖率） |
| `verify-dynamic` | product-verify | Playwright 动态验证 |
| `verify-visual` | visual-verify | 截图对比 |
| `check-deadlinks` | quality-checks | 死链扫描 |
| `check-fields` | quality-checks | 字段一致性 |

### 关键验证

- 所有 root 节点的 entry_requires 指向已有的 `.allforai/` 文件（不需要先跑分析）
- verify-static 和 check-deadlinks 可以并行
- 无 fan_out（单体应用）

### soft goto 测试点

`verify-static` 发现 3 个 use-case 未实现：
```json
{
  "status": "success",
  "summary": "87% use-case coverage. 3 unimplemented: UC-015, UC-022, UC-031",
  "suggest_next": "verify-dynamic",
  "suggest_reason": "static found gaps, dynamic tests should focus on implemented features first"
}
```

orchestrator 收到建议后，可能先跑 verify-dynamic 而不是 visual-verify，因为知道部分功能缺失没必要先截图。

---

## Test 4: 微服务项目做代码治理（入口 A：has_code + has_artifacts）

**项目**: `fincore` — Go 微服务，6 个服务，已有 .allforai/ 产物

```
fincore/
├── services/
│   ├── gateway/       # Go, Chi router
│   ├── auth/          # Go, JWT + OAuth
│   ├── accounts/      # Go, GORM + PostgreSQL
│   ├── transactions/  # Go, event-driven
│   ├── notifications/ # Go, email + SMS
│   └── reports/       # Go, PDF generation
├── proto/             # gRPC proto definitions
├── .allforai/         # 已有产物
└── go.work
```

**用户选择**: `e) 代码治理`

### Bootstrap 应生成的节点

| 节点 ID | 能力模板 | fan_out? |
|---------|---------|----------|
| `discover-fincore` | discovery | - |
| `tune-services` | tune | **fan_out** ✓ |
| `tune-cross-service` | tune | - (全局重复检测) |
| `tune-report` | tune | - (汇总报告) |

### fan_out 测试点

`tune-services` 对每个微服务独立跑治理：
```yaml
fan_out:
  source: .allforai/bootstrap/bootstrap-profile.json
  path: $.modules
  filter: {field: "role", equals: "backend"}
  parallel: true
```

6 个服务 → 6 个 subagent（受 `max_concurrent_nodes: 3` 限制，分两批）。

每个 subagent 输出独立的治理报告到 `.allforai/code-tuner/<service-name>/`。

### fan_out + soft goto 组合测试

tune-services 的某个 subagent（比如 transactions 服务）返回：
```json
{
  "status": "success",
  "suggest_next": "tune-cross-service",
  "suggest_reason": "transactions service has 40% code overlap with accounts service — cross-service dedup will be high value"
}
```

但 fan_out 节点要等所有 6 个子任务完成才算 success。suggest_next 作为节点级建议只在**所有子任务完成后**才传递给 orchestrator。

**问题发现**：当前 fan_out 协议没有说明如何处理子任务的 suggest_next。需要定义汇总规则。

### hooks 测试点

金融项目 bootstrap 可能加：
```json
{"command_succeeds": "go vet ./services/... 2>&1 | wc -l | xargs test 0 -eq", "on_fail": "warn"}
```

---

## Test 5: 已有 bootstrap，重新 bootstrap（入口特殊：has_bootstrap）

**项目**: `shopnow`（同 Test 1），但之前已经跑过一次 bootstrap + 部分 /run

```
shopnow/
├── .allforai/
│   ├── bootstrap/
│   │   ├── state-machine.json       # progress: 3/8 nodes completed
│   │   ├── node-specs/              # 8 个节点文件
│   │   ├── learned/
│   │   │   └── react-swiftui.md     # 上次学到的经验
│   │   └── scripts/
│   ├── product-map/                 # 已生成
│   └── experience-map/              # 已生成
├── packages/                        # 原始 React 代码
└── ios/                             # 部分翻译的 Swift 代码
```

### 关键验证

- Bootstrap 检测到 `has_bootstrap: true`，应该问用户"复用还是重新生成"
- 如果重新生成：**保留** `learned/react-swiftui.md`，**覆盖**其他所有文件
- 新生成的 node-spec 应该读取 `learned/` 里的经验并嵌入 hints
- progress 重置为 0（但 session resume 会重新验证已有产出物，自动跳过已完成的节点）

### Session Resume 测试

重新 bootstrap 后用户跑 `/run 复刻到 SwiftUI`：
1. Orchestrator 读 state-machine.json → progress 全空
2. 但 pre_node hooks 发现 discover 和 analyze 的 exit_requires 已满足（产物还在）
3. 这些节点直接标记 completed，不用重跑
4. 从 translate-packages 开始（ios/ 已有部分代码，部分 package 可能也 pass）

---

## 发现的问题（全部已修复）

### ✅ 问题 1: fan_out 子任务的 suggest_next 汇总
→ 定义了共识规则：全部一致则采纳，不一致则丢弃。见 orchestrator-template.md "Fan-Out suggest_next Aggregation"。

### ✅ 问题 2: fan_out JSONPath 的 filter 语法
→ 加了 `fan_out.filter` 字段（`{field, equals}`），path 只用简单 JSONPath。见 bootstrap.md + validate_bootstrap.py。

### ✅ 问题 3: Session Resume 跳过已完成节点的效率
→ 加了 fast-forward：completed_nodes 为空时检查所有节点的 exit_requires，自动标记已满足的。见 orchestrator-template.md "Session Resume Protocol"。

---

## 覆盖矩阵

| 测试 | 入口 | fan_out | soft goto | hooks | 特殊场景 |
|------|------|---------|-----------|-------|---------|
| Test 1 shopnow | B (code, no artifacts) | ✓ translate 4 packages | ✓ build→test 优先级 | 默认 | 并行限制 |
| Test 2 medtrack | D (空项目) | - | - | ✓ custom HIPAA | 从零构建起点 |
| Test 3 taskflow | A (code + artifacts) | - | ✓ 跳过无意义截图 | 默认 | 多目标组合 |
| Test 4 fincore | A (code + artifacts) | ✓ tune 6 services | ✓ fan_out 内 | ✓ custom go vet | fan_out + goto 组合 |
| Test 5 shopnow redux | has_bootstrap | ✓ (同 Test 1) | - | 默认 | learned 保留 + fast-forward |

---

## Iteration 2: 边界条件测试

### Test 6: fan_out 空数组

**场景**: bootstrap-profile.json 的 modules 数组为空（比如用户选了"从零构建"但 bootstrap 还没填 modules）。

**预期**:
- fan_out 展开时发现空数组 → 节点 failure
- orchestrator 触发 diagnosis → root cause 是上游没生成 modules
- 不会死循环（loop_detection 会捕获重复 failure hash）

### Test 7: fan_out filter 匹配零项

**场景**: `$.modules` 有 4 项，但 `filter: {field: "role", equals: "mobile"}` 匹配 0 项（项目没有 mobile 模块）。

**预期**: 和空数组一样 → failure。但 suggest_reason 应该说"filter matched 0 items"而非"empty array"。

**问题发现**: 当前 orchestrator 文档只说"empty array → failure"，没有区分"数组本身为空"和"filter 后为空"。诊断时需要能区分这两种情况，否则 diagnosis 会误判 root cause。

**建议**: orchestrator 在 fan_out failure 时记录原因：
- `fan_out_error: "source array empty"` 或 `fan_out_error: "filter matched 0 of N items"`

### Test 8: soft goto 指向不存在的节点

**场景**: subagent 返回 `suggest_next: "verify-integration-tests"`，但 state-machine.json 里没有这个节点 ID。

**预期**: orchestrator 忽略这个建议，正常按 DAG 选下一个节点。不应报错或 crash。

**验证**: 当前文档说"advisory, NOT binding"，隐含了忽略无效值。但没有显式说"如果 suggest_next 不在节点列表中则忽略"。

### Test 9: pre_node hook 全部跳过

**场景**: 所有候选节点的 pre_node hook 都失败（比如 budget_check 达到上限）。

**预期**: orchestrator 应该终止并输出当前进度 + TODO list，而不是无限循环尝试找可执行的节点。

**问题发现**: Core Loop 步骤 3 说"If any hook fails → skip node, pick next candidate, back to 2"。如果所有候选都被跳过，会无限循环在 1→2→3→2→3。

**建议**: 加一个逃逸条件："If all candidate nodes skipped by pre_node hooks in a single iteration → terminate with current progress"。

### Test 10: fan_out 部分失败

**场景**: translate-packages 展开 4 个子任务，3 个 success，1 个 failure（比如 admin package 翻译失败）。

**预期**: 节点整体 failure。但 3 个成功的翻译结果应该保留（文件已写入磁盘）。

**验证**:
- orchestrator 触发 diagnosis
- diagnosis 应该能定位到是哪个子任务失败（需要子任务 ID/label）
- repair plan 只重跑失败的那个子任务？还是整个 fan_out 重跑？

**问题发现**: 当前协议没有"部分重跑"机制。fan_out 是 all-or-nothing。对于翻译场景，重跑全部 4 个很浪费。

**建议**: fan_out 节点失败时，在 node_summaries 里记录每个子任务的状态：
```json
{
  "fan_out_results": [
    {"item": "packages/web", "status": "success"},
    {"item": "packages/api", "status": "success"},
    {"item": "packages/shared", "status": "success"},
    {"item": "packages/admin", "status": "failure", "error": "..."}
  ]
}
```
重跑时 orchestrator 只展开 status != "success" 的子任务。

---

## Iteration 3: Bootstrap 生成逻辑测试

### Test 11: fan_out vs 多节点的选择

**场景**: `shopnow` 项目（React → SwiftUI），bootstrap 需要决定翻译策略。

**正确选择**:
- `translate-react-to-swiftui` (前端) 和 `translate-express-to-vapor` (后端) → **两个独立节点**（不同平台，node-spec 完全不同）
- `translate-react-to-swiftui` 内部处理 4 个 package → **fan_out**（同一模板重复 4 次）

**错误选择**:
- 把 4 个 package 做成 4 个独立节点 → 浪费（node-spec 一样，只是路径不同）
- 把前后端合成一个 fan_out 节点 → 错误（Swift 和 Vapor 的翻译指令完全不同）

**验证 bootstrap 的判断规则**:
- 如果 `modules` 中有多个 `role` 值 → 按 role 分节点
- 如果同一 role 下有多个 module → 该节点加 fan_out

### Test 12: hooks 生成 — bootstrap 何时加 custom hook

**场景对比**:

| 项目 | 领域 | 应加的 custom hook |
|------|------|-------------------|
| medtrack | 医疗 | HIPAA TODO 检查 |
| fincore | 金融 | go vet / lint |
| shopnow | 电商 | 无 |
| gamedev | 游戏 | 无 |

**验证**: bootstrap 是否只在有明确理由时才加 custom hook，而不是对所有领域都加。

**问题**: 当前 bootstrap.md 没有指导何时加 custom hook。这完全靠 LLM 判断。

**结论**: 不需要改 — 这正是"LLM 尽量发挥"的范畴。如果加了不必要的 hook，最坏情况是多跑一个 command_succeeds，成本极低。如果漏了必要的 hook，用户可以在 Step 5.5 确认时提出。

### Test 13: 多目标组合时的节点去重

**场景**: 用户选 `a + e`（逆向分析 + 代码治理）。两个 goal 都需要 discovery 节点。

**预期**: bootstrap 只生成一个 discovery 节点，不重复。tune 节点的 entry_requires 指向 discovery 的产出文件。

**验证**: 当前 bootstrap 文档没有显式说"去重"，但 Step 2.2 的能力选择是 set-based（"which capabilities needed"），不会重复选同一个 capability。节点 ID 是项目相关的（`discover-fincore`），不会冲突。

**结论**: 不需要改 — 隐式去重已经够了。

---

## 最终状态

### 新增特性清单

| 特性 | 定义位置 | 验证位置 |
|------|---------|---------|
| fan_out 声明 | bootstrap.md (node-spec format) | validate_bootstrap.py |
| fan_out filter | orchestrator-template.md | validate_bootstrap.py |
| fan_out partial retry | orchestrator-template.md | (协议级，无代码) |
| fan_out error reporting | orchestrator-template.md | (协议级) |
| fan_out suggest_next 汇总 | orchestrator-template.md | (协议级) |
| soft goto hint | orchestrator-template.md (response contract) | (协议级) |
| hooks 协议 | orchestrator-template.md | (协议级) |
| custom hooks | orchestrator-template.md | (协议级) |
| fast-forward resume | orchestrator-template.md (session resume) | (协议级) |
| all-skip 逃逸 | orchestrator-template.md (core loop) | (协议级) |
| fan_out vs 多节点指导 | bootstrap.md (composition) | (文档级) |

### 已修复的问题

1. ✅ fan_out 子任务 suggest_next 无汇总规则 → 定义了共识/丢弃规则
2. ✅ fan_out JSONPath 不支持 filter → 加了 filter 字段
3. ✅ re-bootstrap 后无 fast-forward → 加了空 completed_nodes 时的 fast-forward
4. ✅ pre_node hook 全跳过无限循环 → 加了逃逸条件
5. ✅ fan_out 部分失败全量重跑 → 加了 partial retry + fan_out_results
6. ✅ fan_out error 不区分空数组和 filter 空 → 加了错误分类
7. ✅ soft goto 指向不存在节点 → core loop 显式忽略
8. ✅ bootstrap 不知道何时用 fan_out → 加了选择指导
