# Meta-Skill 全量思维测试设计

**日期**：2026-04-07  
**测试项目**：RetailSphere — 零售超级 App  
**测试范围**：全量（14 capabilities × 结构完整性 + 数据流连通性）

---

## 目标

验证 meta-skill 全量 pipeline 的三类断言：

- **断言 A（结构完整性）**：每个 capability 的输出文件 schema 满足自身声明的契约
- **断言 B1（机械链路）**：字段名、路径、ID 引用、枚举值可由规则判定
- **断言 B2（语义链路）**：屏幕覆盖、实现范围传递、基线引用需 LLM 判断

B1 失败 = 接线断了（修 5 秒）。B2 失败 = 业务理解偏差（需人介入）。两类失败路由不同，不能混用。

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

## Capability Contract 表（全 14 条）

每条契约格式：`artifact_path | required_fields | optional_fields | producer | consumers | validation_mode`

### 1. product-concept

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/product-concept/product-concept.json` |
| required_fields | `name`, `vision`, `target_users[]`, `core_features[]` |
| optional_fields | `business_model`, `constraints[]`, `assumption_register` |
| producer | product-concept |
| consumers | reverse-concept, product-analysis, launch-prep |
| validation_mode | B2 (semantic) — 内容是否覆盖产品愿景 |

### 2. reverse-concept

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/product-concept/concept-baseline.json` |
| required_fields | `features[]`, `business_flows[]`, `constraints[]`, `evidence_sources[]` |
| optional_fields | `iteration_feedback`, `assumption_gaps[]` |
| producer | reverse-concept |
| consumers | product-analysis, concept-acceptance, launch-prep |
| validation_mode | B1 (mechanical) — `features[].id` 存在；B2 — 反推内容是否有证据支撑 |

### 3. product-analysis

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/product-map/task-inventory.json`, `role-profiles.json` |
| required_fields | `tasks[].id`, `tasks[].name`, `tasks[].role_ref`, `roles[].name`, `roles[].id` |
| optional_fields | `tasks[].priority`, `business-flows.json`, `task-index.json` |
| producer | product-analysis |
| consumers | feature-gap, ui-design, translate, product-verify |
| validation_mode | B1 — `tasks[].id` 格式一致；B2 — 任务覆盖是否完整 |

### 4. feature-gap

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/feature-gap/gap-tasks.json` |
| required_fields | `gaps[].task_ref`, `gaps[].type` (task/screen/journey), `gaps[].priority` |
| optional_fields | `gaps[].description`, `gap-report.md` |
| producer | feature-gap |
| consumers | feature-prune |
| validation_mode | B1 — `gaps[].task_ref` 能在 `task-inventory.json` 中找到对应 `tasks[].id` |

### 5. feature-prune

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/feature-prune/prune-tasks.json` |
| required_fields | `decisions[].task_id`, `decisions[].included` (bool), `decisions[].reason` |
| optional_fields | `frequency-tier.json`, `prune-report.md` |
| producer | feature-prune |
| consumers | translate, ui-design |
| validation_mode | B1 — `decisions[].task_id` 能在 `gap-tasks.json` 或 `task-inventory.json` 中找到 |

### 6. ui-design

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/ui-design/ui-design-spec.md` |
| required_fields | `screens[]`（含 `screen_name`, `role`）, `navigation_flows[]` |
| optional_fields | `design_tokens`, `preview/*.html` |
| producer | ui-design |
| consumers | product-verify, visual-verify |
| validation_mode | B2 — screens 是否覆盖所有 prune 决策 `included=true` 的任务 |

### 7. translate

| 字段 | 值 |
|------|----|
| artifact_path | 源代码文件（非 `.allforai/`） |
| required_fields | 每个 `prune-tasks.included=true` 的任务对应至少一个实现文件 |
| optional_fields | 注释、测试桩 |
| producer | translate |
| consumers | compile-verify |
| validation_mode | B2 — prune 范围是否完整实现（语义判断） |

### 8. compile-verify

| 字段 | 值 |
|------|----|
| artifact_path | build artifacts（`dist/`, `build/`, `.apk`, `.app`, binary） |
| required_fields | `exit_code=0`, `artifact_paths[]`（每模块一条） |
| optional_fields | `warnings[]` |
| producer | compile-verify |
| consumers | test-verify |
| validation_mode | B1 — exit_code 存在且为 0；artifact_paths 每模块都有条目 |

### 9. test-verify

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/test-verify/test-verify-report.json` |
| required_fields | `results[].module_id`, `results[].layer` (R2/R3/R4), `results[].pass_rate`, `composite_score` |
| optional_fields | `verification_reasoning[]`, `failures[]` |
| producer | test-verify |
| consumers | product-verify, code-tuner |
| validation_mode | B1 — 每个 module_id 在 bootstrap-profile 中存在；B2 — pass_rate 阈值是否合理 |

### 10. product-verify

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/product-verify/verify-report.json` |
| required_fields | `static_score`, `dynamic_score`, `composite_score`, `issues[]` |
| optional_fields | `screenshots[]`, `static-report.json`, `dynamic-report.json` |
| producer | product-verify |
| consumers | code-tuner, launch-prep |
| validation_mode | B1 — score 字段为数值；B2 — dynamic 验证是否覆盖所有 ui-design screens |

### 11. demo-forge

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/demo-forge/forge-data/` |
| required_fields | `seed_data[]`（含 role_ref）, `demo_scenarios[]` |
| optional_fields | `assets/`, `round-history.json` |
| producer | demo-forge |
| consumers | product-verify（动态测试数据） |
| validation_mode | B1 — `seed_data[].role_ref` 在 `role-profiles.json` 中存在 |

### 12. quality-checks

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/quality-checks/deadhunt-report.json`, `fieldcheck-report.json` |
| required_fields | `dead_routes[]`（含 file:line）, `field_mismatches[]`, `fix_tasks[]` |
| optional_fields | `severity_levels` |
| producer | quality-checks |
| consumers | translate（fix loop） |
| validation_mode | B1 — fix_tasks 格式正确；B2 — 检测覆盖范围是否完整 |

### 13. code-tuner

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/code-tuner/tuner-report.json`, `tuner-tasks.json` |
| required_fields | `compliance_score`, `duplication_score`, `abstraction_score`, `tuner_tasks[].id` |
| optional_fields | `tuner-profile.json`, `phase1-4 JSONs` |
| producer | code-tuner |
| consumers | launch-prep |
| validation_mode | B1 — score 字段为 0-100 数值；B2 — tuner_tasks 是否对应真实代码问题 |

### 14. launch-prep

| 字段 | 值 |
|------|----|
| artifact_path | `.allforai/launch-prep/launch-checklist.json`, `compliance-checklist.json` |
| required_fields | `competitive_research`（完成标志）, `checklist[]`（含 `item`, `status`） |
| optional_fields | `implementation-gaps.json`, `pricing_tiers` |
| producer | launch-prep |
| consumers | （终点，无下游） |
| validation_mode | B2 — checklist 是否覆盖目标平台合规要求 |

---

## 执行结构

### 运行模式说明

本设计支持两种模式，影响责任域能否并行：

| 模式 | 说明 | 并行性 |
|------|------|--------|
| **静态分析**（当前）| 读各 capability `.md` 文件，验证 contract 声明自洽 | 各组**可并行** |
| **运行时检查**（扩展）| 跑真实 pipeline，验证实际 artifact 字段 | 需 **readiness gate**，上游完成后下游才能执行 |

### 特化阶段（串行，先于所有责任域）

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

### 执行阶段：责任域分组

静态模式下五组可并行；运行时模式需按依赖顺序执行（见 `depends_on`）。

| 责任域 | 负责 capabilities | 断言 A | 断言 B1 | 断言 B2 | depends_on（运行时） |
|--------|-----------------|--------|---------|---------|---------------------|
| 域-1 | product-concept, reverse-concept, product-analysis | schema 完整 | concept-baseline.features[].id 存在 | 反推内容有证据 | — |
| 域-2 | feature-gap, feature-prune, ui-design | schema 完整 | task_ref / task_id 能回溯到 task-inventory | screens 覆盖 prune included 任务 | 域-1 |
| 域-3 | translate, compile-verify | node-spec 工具分配（7 模块） | artifact_paths 每模块存在 | prune 范围完整实现 | 域-2 |
| 域-4 | test-verify, product-verify | schema 完整 | module_id 存在于 bootstrap-profile | dynamic 验证覆盖 ui-design screens | 域-3 |
| 域-5 | demo-forge, quality-checks, code-tuner, launch-prep | schema 完整 | role_ref / score 字段格式正确 | checklist 覆盖目标平台合规 | 域-4 |

---

## 数据流图

```
product-concept ──→ .allforai/product-concept/product-concept.json
                         ↓
reverse-concept ──→ .allforai/product-concept/concept-baseline.json
                         ↓
product-analysis ─→ .allforai/product-map/task-inventory.json
                    .allforai/product-map/role-profiles.json
                         ↓
feature-gap ──────→ .allforai/feature-gap/gap-tasks.json
feature-prune ────→ .allforai/feature-prune/prune-tasks.json
ui-design ────────→ .allforai/ui-design/ui-design-spec.md
                         ↓
translate ────────→ [源代码]
compile-verify ───→ [build artifacts: dist/, .apk, .app, binary]
test-verify ──────→ .allforai/test-verify/test-verify-report.json
                         ↓
product-verify ───→ .allforai/product-verify/verify-report.json
demo-forge ───────→ .allforai/demo-forge/forge-data/
quality-checks ───→ .allforai/quality-checks/deadhunt-report.json
code-tuner ───────→ .allforai/code-tuner/tuner-report.json
launch-prep ──────→ .allforai/launch-prep/launch-checklist.json
```

**高风险断链点**：

| 风险 | 类型 | 上游字段 | 下游需要 | 断言 |
|------|------|---------|---------|------|
| 高 | B1 | `task-inventory.tasks[].id` | `gap-tasks.gaps[].task_ref` | 字段名匹配 |
| 高 | B1 | `concept-baseline.features[]` | product-analysis 输入 | baseline 存在且非空 |
| 高 | B1 | `prune-tasks.decisions[].task_id` | `gap-tasks.gaps[].task_ref` | ID 格式一致 |
| 中 | B2 | `prune-tasks.included=true` 的任务 | translate 实现范围 | 实现文件覆盖 |
| 中 | B2 | `ui-design-spec.screens[].screen_name` | product-verify 验证路径 | 屏幕一一对应 |
| 低 | B1 | `verify-report.composite_score` | code-tuner 参考基线 | score 为数值 |

---

## 责任域输出格式

每个责任域输出固定结构：

```yaml
domain: 域-N
capabilities: [cap-1, cap-2]

results:
  - capability: cap-1
    assertion_A: PASS | FAIL
    assertion_B1: PASS | FAIL | N/A
    assertion_B2: PASS | FAIL | N/A
    b1_failures: []        # 机械失败：字段名、路径、格式
    b2_findings: []        # 语义发现：需人工判断的项

critical_violations: []
```

## 汇总表格式

```
capability        | A:结构 | B1:机械 | B2:语义 | 状态
──────────────────┼────────┼─────────┼─────────┼──────
product-concept   |        |   N/A   |         |
reverse-concept   |        |         |         |
product-analysis  |        |         |         |
feature-gap       |        |         |   N/A   |
feature-prune     |        |         |   N/A   |
ui-design         |        |   N/A   |         |
translate         |        |   N/A   |         |
compile-verify    |        |         |   N/A   |
test-verify       |        |         |         |
product-verify    |        |         |         |
demo-forge        |        |         |   N/A   |
quality-checks    |        |         |         |
code-tuner        |        |         |         |
launch-prep       |        |   N/A   |         |
```

B1 FAIL → 自动修复候选。B2 FAIL → 人工审查队列。

---

## 通过标准

- 特化阶段：0 个 `CONSTRAINT_VIOLATION`，0 个 `MISSING_NODE`
- 执行阶段断言 A：全部 PASS
- 执行阶段断言 B1：全部 PASS（机械检查，无例外）
- 执行阶段断言 B2：全部 PASS 或附记录的 FINDING（语义检查允许人工复核，但不允许静默跳过）
