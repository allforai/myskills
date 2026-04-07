# Meta-Skill 全量思维测试 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 RetailSphere 测试夹具 + 5 个责任域检测 prompt，对 meta-skill 全量 14 个 capability 执行断言 A / B1 / B2，产出汇总表。

**Architecture:** 先写预期输出（expected YAML），再写执行 prompt，最后派 agent 执行并比对。B1 断言可机械比对，B2 断言由 LLM 审查后标 PASS/FINDING/FAIL。特化阶段串行，5 个责任域静态模式下并行。

**Tech Stack:** Markdown prompt 文件，YAML 预期输出，Claude agent dispatch，bash diff 比对 B1 结果。

---

## 文件结构

```
claude/meta-skill/tests/
├── fixtures/retail-sphere/          # Task 1: 7 个模块的最小触发文件
│   ├── apps/consumer/pubspec.yaml
│   ├── apps/merchant-app/package.json
│   ├── apps/merchant-app/metro.config.js
│   ├── apps/ios-vip/RetailSphere.xcodeproj/project.pbxproj
│   ├── apps/android-pos/build.gradle.kts
│   ├── apps/merchant-web/next.config.ts
│   ├── apps/admin-web/vite.config.ts
│   └── services/api/go.mod
├── expected/                        # Task 2: 预期输出（TDD 基准）
│   ├── specialization-expected.json
│   ├── domain-1-expected.yaml
│   ├── domain-2-expected.yaml
│   ├── domain-3-expected.yaml
│   ├── domain-4-expected.yaml
│   └── domain-5-expected.yaml
└── prompts/                         # Tasks 3-7: 执行 prompt
    ├── specialization.md
    ├── domain-1.md
    ├── domain-2.md
    ├── domain-3.md
    ├── domain-4.md
    └── domain-5.md

docs/superpowers/results/            # Task 8: 执行结果
    └── 2026-04-07-retail-sphere-test-results.md
```

---

## Task 1: 创建 RetailSphere 测试夹具

**Files:**
- Create: `claude/meta-skill/tests/fixtures/retail-sphere/apps/consumer/pubspec.yaml`
- Create: `claude/meta-skill/tests/fixtures/retail-sphere/apps/merchant-app/package.json`
- Create: `claude/meta-skill/tests/fixtures/retail-sphere/apps/merchant-app/metro.config.js`
- Create: `claude/meta-skill/tests/fixtures/retail-sphere/apps/ios-vip/RetailSphere.xcodeproj/project.pbxproj`
- Create: `claude/meta-skill/tests/fixtures/retail-sphere/apps/android-pos/build.gradle.kts`
- Create: `claude/meta-skill/tests/fixtures/retail-sphere/apps/merchant-web/next.config.ts`
- Create: `claude/meta-skill/tests/fixtures/retail-sphere/apps/admin-web/vite.config.ts`
- Create: `claude/meta-skill/tests/fixtures/retail-sphere/services/api/go.mod`

- [ ] **Step 1: 创建 Flutter consumer 触发文件**

```yaml
# apps/consumer/pubspec.yaml
name: retail_sphere_consumer
description: RetailSphere consumer Flutter app
version: 1.0.0+1
environment:
  sdk: '>=3.0.0 <4.0.0'
  flutter: '>=3.10.0'
dependencies:
  flutter:
    sdk: flutter
```

- [ ] **Step 2: 创建 React Native merchant-app 触发文件**

```json
// apps/merchant-app/package.json
{
  "name": "retail-sphere-merchant",
  "version": "1.0.0",
  "dependencies": {
    "react": "18.2.0",
    "react-native": "0.73.0"
  },
  "scripts": {
    "start": "react-native start",
    "test": "jest"
  }
}
```

```js
// apps/merchant-app/metro.config.js
const {getDefaultConfig, mergeConfig} = require('@react-native/metro-config');
module.exports = mergeConfig(getDefaultConfig(__dirname), {});
```

- [ ] **Step 3: 创建 iOS SwiftUI 触发文件**

```
// apps/ios-vip/RetailSphere.xcodeproj/project.pbxproj
// Minimal Xcode project file — bootstrap detects *.xcodeproj presence
// archiveVersion = 1;
// objectVersion = 56;
```

- [ ] **Step 4: 创建 Android Kotlin 触发文件**

```kotlin
// apps/android-pos/build.gradle.kts
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    compileSdk = 34
    defaultConfig {
        applicationId = "com.retailsphere.androidpos"
        minSdk = 24
    }
}
```

- [ ] **Step 5: 创建 Next.js merchant-web 触发文件**

```ts
// apps/merchant-web/next.config.ts
import type { NextConfig } from 'next'
const nextConfig: NextConfig = {}
export default nextConfig
```

- [ ] **Step 6: 创建 React/Vite admin-web 触发文件**

```ts
// apps/admin-web/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({ plugins: [react()] })
```

- [ ] **Step 7: 创建 Go API 触发文件**

```
// services/api/go.mod
module github.com/retailsphere/api
go 1.22
```

- [ ] **Step 8: 验证文件结构**

```bash
find claude/meta-skill/tests/fixtures/retail-sphere -type f | sort
```

预期输出（7 个模块，9 个文件）：
```
claude/meta-skill/tests/fixtures/retail-sphere/apps/admin-web/vite.config.ts
claude/meta-skill/tests/fixtures/retail-sphere/apps/android-pos/build.gradle.kts
claude/meta-skill/tests/fixtures/retail-sphere/apps/consumer/pubspec.yaml
claude/meta-skill/tests/fixtures/retail-sphere/apps/ios-vip/RetailSphere.xcodeproj/project.pbxproj
claude/meta-skill/tests/fixtures/retail-sphere/apps/merchant-app/metro.config.js
claude/meta-skill/tests/fixtures/retail-sphere/apps/merchant-app/package.json
claude/meta-skill/tests/fixtures/retail-sphere/apps/merchant-web/next.config.ts
claude/meta-skill/tests/fixtures/retail-sphere/services/api/go.mod
```

- [ ] **Step 9: Commit**

```bash
git add claude/meta-skill/tests/fixtures/
git commit -m "test(meta-skill): add RetailSphere test fixture (7 modules)"
```

---

## Task 2: 写预期输出（TDD 基准）

**Files:**
- Create: `claude/meta-skill/tests/expected/specialization-expected.json`
- Create: `claude/meta-skill/tests/expected/domain-1-expected.yaml`
- Create: `claude/meta-skill/tests/expected/domain-2-expected.yaml`
- Create: `claude/meta-skill/tests/expected/domain-3-expected.yaml`
- Create: `claude/meta-skill/tests/expected/domain-4-expected.yaml`
- Create: `claude/meta-skill/tests/expected/domain-5-expected.yaml`

- [ ] **Step 1: 写特化阶段预期输出**

```json
// expected/specialization-expected.json
{
  "modules_detected": 7,
  "constraint_violations": 0,
  "missing_nodes": 0,
  "tool_assignments": [
    {"module_id": "consumer",      "e2e_tool": "flutter test integration_test/", "playwright": false},
    {"module_id": "merchant-app",  "e2e_tool": "detox|maestro",                  "playwright": false},
    {"module_id": "ios-vip",       "e2e_tool": "xcodebuild test",                "playwright": false},
    {"module_id": "android-pos",   "e2e_tool": "gradlew connectedAndroidTest",   "playwright": false},
    {"module_id": "merchant-web",  "e2e_tool": "playwright",                     "playwright": true},
    {"module_id": "admin-web",     "e2e_tool": "playwright",                     "playwright": true},
    {"module_id": "api",           "e2e_tool": "curl",                           "playwright": false}
  ]
}
```

- [ ] **Step 2: 写域-1 预期输出（product-concept / reverse-concept / product-analysis）**

```yaml
# expected/domain-1-expected.yaml
domain: 域-1
capabilities: [product-concept, reverse-concept, product-analysis]

results:
  - capability: product-concept
    assertion_A: PASS
    assertion_B1: N/A
    assertion_B2: PASS
    b1_failures: []
    b2_findings: []

  - capability: reverse-concept
    assertion_A: PASS
    assertion_B1: PASS   # concept-baseline.features[].id 字段存在
    assertion_B2: PASS
    b1_failures: []
    b2_findings: []

  - capability: product-analysis
    assertion_A: PASS
    assertion_B1: PASS   # tasks[].id 格式一致
    assertion_B2: PASS
    b1_failures: []
    b2_findings: []

critical_violations: []
```

- [ ] **Step 3: 写域-2 预期输出（feature-gap / feature-prune / ui-design）**

```yaml
# expected/domain-2-expected.yaml
domain: 域-2
capabilities: [feature-gap, feature-prune, ui-design]

results:
  - capability: feature-gap
    assertion_A: PASS
    assertion_B1: PASS   # gaps[].task_ref 回溯到 task-inventory.tasks[].id
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: feature-prune
    assertion_A: PASS
    assertion_B1: PASS   # decisions[].task_id 存在于 gap-tasks 或 task-inventory
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: ui-design
    assertion_A: PASS
    assertion_B1: N/A
    assertion_B2: PASS   # screens 覆盖 prune included 任务
    b1_failures: []
    b2_findings: []

critical_violations: []
```

- [ ] **Step 4: 写域-3 预期输出（translate / compile-verify）**

```yaml
# expected/domain-3-expected.yaml
domain: 域-3
capabilities: [translate, compile-verify]

results:
  - capability: translate
    assertion_A: PASS
    assertion_B1: N/A
    assertion_B2: PASS   # prune included 任务有对应实现文件
    b1_failures: []
    b2_findings: []

  - capability: compile-verify
    assertion_A: PASS
    assertion_B1: PASS   # artifact_paths 每模块有条目，exit_code=0
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

critical_violations: []
```

- [ ] **Step 5: 写域-4 预期输出（test-verify / product-verify）**

```yaml
# expected/domain-4-expected.yaml
domain: 域-4
capabilities: [test-verify, product-verify]

results:
  - capability: test-verify
    assertion_A: PASS
    assertion_B1: PASS   # results[].module_id 全在 bootstrap-profile 中
    assertion_B2: PASS
    b1_failures: []
    b2_findings: []

  - capability: product-verify
    assertion_A: PASS
    assertion_B1: PASS   # composite_score 为数值
    assertion_B2: PASS   # dynamic 验证覆盖 ui-design screens
    b1_failures: []
    b2_findings: []

critical_violations: []
```

- [ ] **Step 6: 写域-5 预期输出（demo-forge / quality-checks / code-tuner / launch-prep）**

```yaml
# expected/domain-5-expected.yaml
domain: 域-5
capabilities: [demo-forge, quality-checks, code-tuner, launch-prep]

results:
  - capability: demo-forge
    assertion_A: PASS
    assertion_B1: PASS   # seed_data[].role_ref 在 role-profiles 中存在
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: quality-checks
    assertion_A: PASS
    assertion_B1: PASS   # fix_tasks 格式正确（含 file:line）
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: code-tuner
    assertion_A: PASS
    assertion_B1: PASS   # compliance_score / duplication_score / abstraction_score 为 0-100 数值
    assertion_B2: N/A
    b1_failures: []
    b2_findings: []

  - capability: launch-prep
    assertion_A: PASS
    assertion_B1: N/A
    assertion_B2: PASS   # checklist 覆盖目标平台合规
    b1_failures: []
    b2_findings: []

critical_violations: []
```

- [ ] **Step 7: Commit**

```bash
git add claude/meta-skill/tests/expected/
git commit -m "test(meta-skill): add expected outputs for all 5 domains (TDD baseline)"
```

---

## Task 3: 写特化阶段 prompt

**Files:**
- Create: `claude/meta-skill/tests/prompts/specialization.md`

- [ ] **Step 1: 写 prompt**

```markdown
<!-- prompts/specialization.md -->
# Bootstrap 特化阶段：RetailSphere

你是 bootstrap skill。分析以下项目结构，产出 specialization-report。

## 项目结构

```
claude/meta-skill/tests/fixtures/retail-sphere/
├── apps/consumer/pubspec.yaml
├── apps/merchant-app/package.json + metro.config.js
├── apps/ios-vip/RetailSphere.xcodeproj/project.pbxproj
├── apps/android-pos/build.gradle.kts
├── apps/merchant-web/next.config.ts
├── apps/admin-web/vite.config.ts
└── services/api/go.mod
```

## 执行 Step 1.1-1.2（模块检测）

读取上述文件，识别所有模块的 role 和 platform。

## 执行 Step 3.1（工具分配）

参考 `claude/meta-skill/knowledge/capabilities/compile-verify.md`、
`claude/meta-skill/knowledge/capabilities/test-verify.md`、
`claude/meta-skill/knowledge/capabilities/product-verify.md` 中的工具分配表。

为每个模块分配：compile_tool、test_tool、e2e_tool。
**约束：Playwright CANNOT test native mobile apps。**

## 输出格式

输出 JSON，严格匹配 `claude/meta-skill/tests/expected/specialization-expected.json` 的 schema：

```json
{
  "modules_detected": <number>,
  "constraint_violations": <number>,
  "missing_nodes": <number>,
  "tool_assignments": [
    {"module_id": "...", "e2e_tool": "...", "playwright": <bool>}
  ]
}
```
```

- [ ] **Step 2: Commit**

```bash
git add claude/meta-skill/tests/prompts/specialization.md
git commit -m "test(meta-skill): add specialization phase prompt"
```

---

## Task 4: 写责任域 prompt（域-1 至 域-5）

**Files:**
- Create: `claude/meta-skill/tests/prompts/domain-1.md`
- Create: `claude/meta-skill/tests/prompts/domain-2.md`
- Create: `claude/meta-skill/tests/prompts/domain-3.md`
- Create: `claude/meta-skill/tests/prompts/domain-4.md`
- Create: `claude/meta-skill/tests/prompts/domain-5.md`

- [ ] **Step 1: 写域-1 prompt（product-concept / reverse-concept / product-analysis）**

```markdown
<!-- prompts/domain-1.md -->
# 责任域-1 断言检查

读取以下文件：
- `claude/meta-skill/knowledge/capabilities/product-concept.md`
- `claude/meta-skill/knowledge/capabilities/reverse-concept.md`
- `claude/meta-skill/knowledge/capabilities/product-analysis.md`

对每个 capability，根据 contract 表执行：

**断言 A**：required_fields 是否在 capability 的 Output 声明中全部存在？
**断言 B1（机械）**：
- reverse-concept: `concept-baseline.features[].id` 字段是否被声明为必填且有格式约束？
- product-analysis: `tasks[].id` 和 `roles[].id` 是否被声明为必填，且被下游（feature-gap）引用的字段名一致？

**断言 B2（语义）**：
- product-concept: capability 的输出是否能覆盖完整的产品愿景（name/vision/target_users/core_features）？
- reverse-concept: 反推流程是否要求每个输出字段有代码证据支撑？
- product-analysis: 任务覆盖要求（>= 10 tasks）是否合理？

Contract 参考（来自设计 spec）：
- product-concept required_fields: name, vision, target_users[], core_features[]
- reverse-concept required_fields: features[], business_flows[], constraints[], evidence_sources[]
- product-analysis required_fields: tasks[].id, tasks[].name, tasks[].role_ref, roles[].name, roles[].id

输出严格匹配 `claude/meta-skill/tests/expected/domain-1-expected.yaml` 的 schema。
```

- [ ] **Step 2: 写域-2 prompt（feature-gap / feature-prune / ui-design）**

```markdown
<!-- prompts/domain-2.md -->
# 责任域-2 断言检查

读取以下文件：
- `claude/meta-skill/knowledge/capabilities/feature-gap.md`（如存在）
- `claude/meta-skill/knowledge/capabilities/feature-prune.md`（如存在）
- `claude/meta-skill/knowledge/capabilities/ui-design.md`

对每个 capability，根据 contract 表执行：

**断言 A**：required_fields 是否在 capability 的 Output 声明中全部存在？

**断言 B1（机械）**：
- feature-gap: `gaps[].task_ref` 是否被声明为引用 `task-inventory.tasks[].id`？字段名是否一致（task_ref vs id）？
- feature-prune: `decisions[].task_id` 是否能回溯到 gap-tasks 或 task-inventory 的主键？

**断言 B2（语义）**：
- ui-design: capability 是否要求 screens 覆盖所有 prune `included=true` 的任务？

Contract 参考：
- feature-gap required_fields: gaps[].task_ref, gaps[].type, gaps[].priority
- feature-prune required_fields: decisions[].task_id, decisions[].included, decisions[].reason
- ui-design required_fields: screens[]（含 screen_name, role）, navigation_flows[]

输出严格匹配 `claude/meta-skill/tests/expected/domain-2-expected.yaml` 的 schema。
```

- [ ] **Step 3: 写域-3 prompt（translate / compile-verify）**

```markdown
<!-- prompts/domain-3.md -->
# 责任域-3 断言检查

读取以下文件：
- `claude/meta-skill/knowledge/capabilities/compile-verify.md`
- `claude/meta-skill/knowledge/capabilities/test-verify.md`（仅参考 R1 prerequisite 部分）

对每个 capability，根据 contract 表执行：

**断言 A**：
- translate: 是否声明"每个 prune included=true 任务对应至少一个实现文件"？
- compile-verify: 是否声明 exit_code=0 和 artifact_paths[] 为必填输出？

**断言 B1（机械）**：
- compile-verify: artifact_paths 是否要求每模块一条（7 条）？Platform-Specific Build Commands 表是否覆盖所有 7 种 module 类型？

**断言 B2（语义）**：
- translate: prune 范围传递到 translate 实现范围的机制是否在 capability 中有描述？

Contract 参考：
- compile-verify required_fields: exit_code=0, artifact_paths[]（每模块一条）
- translate: 无 .allforai/ 输出，输出为源代码

输出严格匹配 `claude/meta-skill/tests/expected/domain-3-expected.yaml` 的 schema。
```

- [ ] **Step 4: 写域-4 prompt（test-verify / product-verify）**

```markdown
<!-- prompts/domain-4.md -->
# 责任域-4 断言检查

读取以下文件：
- `claude/meta-skill/knowledge/capabilities/test-verify.md`
- `claude/meta-skill/knowledge/capabilities/product-verify.md`

对每个 capability，根据 contract 表执行：

**断言 A**：
- test-verify: results[].module_id / results[].layer / results[].pass_rate / composite_score 是否为声明必填输出？
- product-verify: static_score / dynamic_score / composite_score / issues[] 是否为声明必填输出？

**断言 B1（机械）**：
- test-verify: Platform-Specific Test Commands 表是否覆盖 7 种 module 类型？是否包含 Flutter、iOS、Android 的正确命令？
- product-verify: composite_score 是否声明为数值类型？

**断言 B2（语义）**：
- test-verify: split-by-platform 约束（Do NOT put Flutter tests and Playwright tests in same node）是否有明确声明？
- product-verify: dynamic 验证是否要求覆盖 ui-design 的所有 screens？

**关键约束检查**：
- test-verify: 是否有"Playwright CANNOT test native mobile apps"或等价的硬约束声明？
- product-verify: 是否有"Playwright CANNOT test native mobile apps"的硬约束声明？

输出严格匹配 `claude/meta-skill/tests/expected/domain-4-expected.yaml` 的 schema。
```

- [ ] **Step 5: 写域-5 prompt（demo-forge / quality-checks / code-tuner / launch-prep）**

```markdown
<!-- prompts/domain-5.md -->
# 责任域-5 断言检查

读取以下文件：
- `claude/meta-skill/knowledge/capabilities/demo-forge.md`
- `claude/meta-skill/knowledge/capabilities/quality-checks.md`
- `claude/meta-skill/knowledge/capabilities/tune.md`
- `claude/meta-skill/knowledge/capabilities/launch-prep.md`

对每个 capability，根据 contract 表执行：

**断言 A**：required_fields 是否在 capability 的 Output 声明中全部存在？

**断言 B1（机械）**：
- demo-forge: seed_data[].role_ref 是否被声明为引用 role-profiles？
- quality-checks: fix_tasks 是否被声明为包含 file:line 引用？
- code-tuner: compliance_score / duplication_score / abstraction_score 是否被声明为数值型输出？

**断言 B2（语义）**：
- launch-prep: checklist 是否要求覆盖目标平台合规项（App Store / Google Play / Web）？

Contract 参考：
- demo-forge required_fields: seed_data[](含 role_ref), demo_scenarios[]
- quality-checks required_fields: dead_routes[](含 file:line), field_mismatches[], fix_tasks[]
- code-tuner required_fields: compliance_score, duplication_score, abstraction_score, tuner_tasks[].id
- launch-prep required_fields: competitive_research(完成标志), checklist[](含 item, status)

输出严格匹配 `claude/meta-skill/tests/expected/domain-5-expected.yaml` 的 schema。
```

- [ ] **Step 6: Commit**

```bash
git add claude/meta-skill/tests/prompts/
git commit -m "test(meta-skill): add domain prompts for 5 responsibility domains"
```

---

## Task 5: 执行特化阶段

**Files:**
- Create: `docs/superpowers/results/2026-04-07-retail-sphere-test-results.md`

- [ ] **Step 1: 以 specialization.md 为 prompt 派发 agent**

Dispatch agent，上下文包含：
- `claude/meta-skill/tests/prompts/specialization.md`
- `claude/meta-skill/tests/fixtures/retail-sphere/`（所有文件）
- `claude/meta-skill/knowledge/capabilities/compile-verify.md`
- `claude/meta-skill/knowledge/capabilities/test-verify.md`
- `claude/meta-skill/knowledge/capabilities/product-verify.md`

- [ ] **Step 2: 比对 B1 断言（机械）**

```bash
# 检查 agent 输出的 tool_assignments 中 playwright=false 的 mobile 模块数
# 预期：consumer / merchant-app / ios-vip / android-pos 的 playwright 全为 false
echo "Expected constraint_violations: 0"
echo "Expected missing_nodes: 0"
```

- [ ] **Step 3: 记录结果到 results 文件**

在 `docs/superpowers/results/2026-04-07-retail-sphere-test-results.md` 创建：

```markdown
# RetailSphere 全量测试结果

## 特化阶段
| 检查项 | 预期 | 实际 | 状态 |
|--------|------|------|------|
| modules_detected | 7 | ? | |
| constraint_violations | 0 | ? | |
| missing_nodes | 0 | ? | |
| consumer e2e_tool | flutter test integration_test/ | ? | |
| merchant-app e2e_tool | detox\|maestro | ? | |
| ios-vip e2e_tool | xcodebuild test | ? | |
| android-pos e2e_tool | gradlew connectedAndroidTest | ? | |
| merchant-web e2e_tool | playwright | ? | |
| admin-web e2e_tool | playwright | ? | |
| api e2e_tool | curl | ? | |
```

---

## Task 6: 执行 5 个责任域（静态模式，可并行）

- [ ] **Step 1: 并行派发 5 个域 agent**

每个 agent 读对应的 prompt + capability `.md` 文件，输出 YAML。

域-1 上下文：`domain-1.md` + `product-concept.md` + `reverse-concept.md` + `product-analysis.md`
域-2 上下文：`domain-2.md` + `feature-gap.md`(如存在) + `feature-prune.md`(如存在) + `ui-design.md`
域-3 上下文：`domain-3.md` + `compile-verify.md` + `test-verify.md`
域-4 上下文：`domain-4.md` + `test-verify.md` + `product-verify.md`
域-5 上下文：`domain-5.md` + `demo-forge.md` + `quality-checks.md` + `tune.md` + `launch-prep.md`

- [ ] **Step 2: 收集 5 个 agent 输出，填入 results 文件**

追加到 `docs/superpowers/results/2026-04-07-retail-sphere-test-results.md`：

```markdown
## 执行阶段汇总

| capability | A:结构 | B1:机械 | B2:语义 | 状态 | 备注 |
|------------|--------|---------|---------|------|------|
| product-concept | | N/A | | | |
| reverse-concept | | | | | |
| product-analysis | | | | | |
| feature-gap | | | N/A | | |
| feature-prune | | | N/A | | |
| ui-design | | N/A | | | |
| translate | | N/A | | | |
| compile-verify | | | N/A | | |
| test-verify | | | | | |
| product-verify | | | | | |
| demo-forge | | | N/A | | |
| quality-checks | | | | | |
| code-tuner | | | N/A | | |
| launch-prep | | N/A | | | |
```

- [ ] **Step 3: B1 差异比对**

对每个 B1=FAIL 的行，提取 `b1_failures` 内容，分类：
- 字段名不一致 → 记录 `[FIELD_NAME_MISMATCH] capability.field → downstream.field`
- 路径不存在 → 记录 `[MISSING_ARTIFACT] .allforai/path/to/file.json`
- 格式错误 → 记录 `[FORMAT_ERROR] field_name expected type`

- [ ] **Step 4: B2 语义审查**

对每个 B2 有 FINDING 的行，由人工判断是否为真实问题，标记：
- `ACCEPTED` — 确认为问题，创建 fix task
- `DISMISSED` — 误判，记录原因

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/results/
git commit -m "test(meta-skill): execute full test run on RetailSphere, record results"
```

---

## Task 7: 处理 FAIL 项

- [ ] **Step 1: 对每个 B1 FAIL 创建 fix task**

在 `docs/superpowers/results/2026-04-07-retail-sphere-test-results.md` 追加：

```markdown
## Fix Tasks

| id | capability | 类型 | 问题描述 | 修改文件 | 状态 |
|----|------------|------|---------|---------|------|
| F1 | | B1 | | | TODO |
```

- [ ] **Step 2: 对每个 B2 ACCEPTED FINDING 创建 fix task**

同上，类型标为 B2，并附 LLM 判断依据。

- [ ] **Step 3: 对每个 fix task 执行修改并验证**

对每个 F-N，修改对应 capability `.md`，重新跑对应域的 prompt，验证断言转为 PASS。

- [ ] **Step 4: 最终 Commit**

```bash
git add .
git commit -m "fix(meta-skill): resolve断言 failures found in full test run"
```
