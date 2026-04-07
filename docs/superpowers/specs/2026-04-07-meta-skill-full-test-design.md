# Meta-Skill 全量思维测试设计

**日期**：2026-04-07  
**测试项目**：RetailSphere — 零售超级 App  
**测试范围**：全量（14 capabilities × 结构完整性 + 数据流连通性）

---

## 目标

验证 meta-skill 全量 pipeline 的两类断言：

- **断言 A（结构完整性）**：每个 capability 的输出文件 schema 满足自身声明的契约
- **断言 B（数据流连通性）**：capability N 的 input 字段能从 capability N-1 的 output 中找到对应项

---

## 测试项目：RetailSphere

### 目录结构

```
retail-sphere/
├── apps/
│   ├── consumer/          # Flutter — pubspec.yaml
│   ├── merchant-app/      # React Native — package.json + metro.config.js
│   ├── ios-vip/           # SwiftUI — *.xcodeproj
│   ├── android-pos/       # Kotlin — build.gradle.kts
│   ├── merchant-web/      # Next.js — next.config.ts
│   └── admin-web/         # React — vite.config.ts
├── services/
│   └── api/               # Go — go.mod
└── docker-compose.yml
```

### 模块清单（7 个）

| module_id | role | platform | detected_by |
|-----------|------|----------|-------------|
| consumer | mobile | Flutter | pubspec.yaml |
| merchant-app | mobile | React Native | metro.config.js |
| ios-vip | mobile | iOS/SwiftUI | *.xcodeproj |
| android-pos | mobile | Android/Kotlin | build.gradle.kts |
| merchant-web | frontend | Next.js | next.config.ts |
| admin-web | frontend | React/Vite | vite.config.ts |
| api | backend | Go | go.mod |

---

## 执行结构

### 特化阶段（串行，先于所有 Agent）

Bootstrap 读 RetailSphere，产出 `specialization-report`：

**工具分配表（核心约束验证）**

| module_id | compile_tool | test_tool | e2e_tool | Playwright? |
|-----------|-------------|-----------|----------|-------------|
| consumer | `flutter build` | `flutter test` | `flutter test integration_test/` | ❌ 禁止 |
| merchant-app | `npx react-native build` | `jest` | Detox/Maestro | ❌ 禁止 |
| ios-vip | `xcodebuild build` | `xcodebuild test` | XCUITest | ❌ 禁止 |
| android-pos | `./gradlew assembleDebug` | `./gradlew test` | `./gradlew connectedAndroidTest` | ❌ 禁止 |
| merchant-web | `npm run build` | `vitest` | Playwright | ✅ |
| admin-web | `vite build` | `vitest` | Playwright | ✅ |
| api | `go build ./...` | `go test ./...` | curl/HTTP | ❌ N/A |

**特化阶段失败条件**：
- 任意 mobile 模块 `e2e_tool` = Playwright → `CONSTRAINT_VIOLATION`
- 任意模块无对应 node-spec → `MISSING_NODE`

### 执行阶段（5 Agent 并行）

| Agent | 负责 capabilities | 断言 A | 断言 B（检查上游） |
|-------|-----------------|--------|-----------------|
| Agent-1 | product-concept, reverse-concept, product-analysis | 输出 schema 完整性 | concept-baseline → product-analysis 链路 |
| Agent-2 | feature-gap, feature-prune, ui-design | 输出 schema 完整性 | task-inventory → gap-tasks → prune-tasks 链路 |
| Agent-3 | translate, compile-verify | node-spec 工具分配（7 模块全覆盖） | prune-tasks → translate 范围传递 |
| Agent-4 | test-verify, product-verify | 验证工具分配（Playwright 约束） | compile-verify artifacts → test-verify 前置条件 |
| Agent-5 | demo-forge, quality-checks, code-tuner, launch-prep | 输出 schema 完整性 | verify-report → 各下游引用 |

---

## 数据流图

```
product-concept ──→ product-concept/product-concept.json
                         ↓
reverse-concept ──→ product-concept/concept-baseline.json
                         ↓
product-analysis ─→ product-map/task-inventory.json
                    product-map/role-profiles.json
                         ↓
feature-gap ──────→ feature-gap/gap-tasks.json
feature-prune ────→ feature-prune/prune-tasks.json
ui-design ────────→ ui-design/ui-design-spec.md
                         ↓
translate ────────→ [代码]
compile-verify ───→ [build artifacts]
test-verify ──────→ [test reports]
                         ↓
product-verify ───→ product-verify/verify-report.json
demo-forge ───────→ demo-forge/forge-data/
quality-checks ───→ deadhunt/validation-profile.json
code-tuner ───────→ code-tuner/tuner-report.json
launch-prep ──────→ [launch checklist]
```

**高风险断链点**：

| 风险 | 上游字段 | 下游需要 | 断言 |
|------|---------|---------|------|
| 高 | `task-inventory.json → tasks[].id` | `gap-tasks.json → task_ref` | 字段名匹配 |
| 高 | `concept-baseline.json → features[]` | product-analysis 输入 | baseline 存在 |
| 中 | `prune-tasks.json → included[]` | translate 实现范围 | prune 决策传递 |
| 中 | `ui-design-spec.md → screens[]` | product-verify 验证路径 | 屏幕覆盖完整 |
| 低 | `verify-report.json → score` | code-tuner 参考基线 | score 字段格式 |

---

## Agent 输出格式

每个 Agent 输出固定结构：

```yaml
agent: Agent-N
capabilities: [cap-1, cap-2]

results:
  - capability: cap-1
    assertion_A: PASS | FAIL
    assertion_B: PASS | FAIL | N/A
    notes: null | "失败原因"

critical_violations: []
```

## 汇总表格式

```
capability        | A:结构 | B:数据流 | 状态
──────────────────┼────────┼──────────┼──────
product-concept   |        |  N/A     |
reverse-concept   |        |          |
product-analysis  |        |          |
feature-gap       |        |          |
feature-prune     |        |          |
ui-design         |        |          |
translate         |        |          |
compile-verify    |        |          |
test-verify       |        |          |
product-verify    |        |          |
demo-forge        |        |          |
quality-checks    |        |          |
code-tuner        |        |          |
launch-prep       |        |          |
```

FAIL 行需钻入 Agent 输出查看详情。

---

## 通过标准

- 特化阶段：0 个 `CONSTRAINT_VIOLATION`，0 个 `MISSING_NODE`
- 执行阶段：断言 A 全部 PASS，断言 B 全部 PASS（或有记录的 N/A）
- 任意 FAIL 须附失败原因，不接受静默通过
