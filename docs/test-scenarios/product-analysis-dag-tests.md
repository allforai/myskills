# Product Analysis 3-Node DAG Thought Tests

覆盖 core → ux → verify 的所有状态迁移路径，包括正常流转、回退、跳过、合并。

---

## Test A: 正常流转（无回退）— 简单 SaaS

**项目**: `taskboard` — 任务管理 SaaS，React + Node.js，3 个角色（admin/member/viewer）

**入口**: 已有代码（goal=analyze）

### 预期流转

```
iter 1: core    waiting → success   "3 roles, 24 tasks, 5 flows"
iter 2: ux      waiting → success   "12 screens, all states defined, gate pass"
iter 3: verify  waiting → success   "use-case tree complete, 0 gaps, audit clean"
```

**验证**: 3 次迭代，无回退。transition_log 只有 3 条记录，全部向下。
DAG 图上只有实线箭头，没有虚线。

---

## Test B: verify → core 回退 — 缺少 CRUD 任务

**项目**: `bookshelf` — 图书管理系统，Vue + Django

**场景**: core 阶段识别了"图书"实体但只提取了 create + read，漏了 update 和 delete。
ux 阶段正常通过（因为 UI 上确实只有添加和查看页面）。
verify 的 CRUD 覆盖检查发现缺口。

### 预期流转

```
iter 1: core    waiting → success   "2 roles, 18 tasks, 4 flows"
iter 2: ux      waiting → success   "8 screens, gate pass"
iter 3: verify  waiting → failure   "CRUD gap: Book entity missing update/delete"
         ↓ diagnosis: root cause = core 漏了 update/delete tasks
iter 4: core    completed → success "2 roles, 22 tasks (+4 CRUD补全), 4 flows"
iter 5: verify  failed → success    "CRUD complete, 0 gaps, audit clean"
```

**关键**: iter 4 回退到 core 而不是 ux，因为问题在任务层不在 UI 层。
ux 不需要重跑（experience-map 的页面定义没变，只是 core 补了任务）。

**验证**: DAG 图上有一条红色虚线 `verify ⤴ core`。

**数据闭环检查**:
- core 重跑后 task-inventory.json 多了 4 个任务
- verify 重跑时拉 task-inventory.json → 读到新任务 → CRUD 覆盖通过
- ux 的 experience-map.json 没变（不需要重跑）

---

## Test C: verify → ux 回退 — 缺少屏幕状态

**项目**: `healthcheck` — 健康监测 App，Flutter + Go

**场景**: ux 阶段给"血压记录页"只定义了 success 状态，漏了 empty（第一次没数据）和 error（传感器断连）。verify 的屏幕完整性检查发现缺口。

### 预期流转

```
iter 1: core    waiting → success   "4 roles (patient/doctor/nurse/admin), 35 tasks"
iter 2: ux      waiting → success   "18 screens, gate pass"
iter 3: verify  waiting → failure   "Screen gaps: blood-pressure-record missing empty/error states"
         ↓ diagnosis: root cause = ux 的 experience-map 不完整
iter 4: ux      completed → success "18 screens, all states complete, gate re-pass"
iter 5: verify  failed → success    "All screens complete, audit clean"
```

**关键**: 回退到 ux 而不是 core，因为角色和任务没问题，只是 UI 状态定义不完整。

**数据闭环检查**:
- ux 重跑时拉 product-map/*.json（没变）
- ux 重跑后 experience-map.json 更新了血压记录页的状态定义
- verify 重跑时拉 experience-map.json → 读到完整状态 → 通过

---

## Test D: ux → core 回退 — 引用不存在的角色

**项目**: `classroom` — 在线教育平台，React + Spring Boot

**场景**: core 识别了 teacher + student 两个角色。ux 在做 experience-map 时发现代码里有"家长查看孩子成绩"的页面，但 core 没有识别 parent 角色。

### 预期流转

```
iter 1: core    waiting → success   "2 roles (teacher/student), 28 tasks, 6 flows"
iter 2: ux      waiting → failure   "Screen 'parent-grade-view' references role 'parent' not in role-profiles"
         ↓ ux 自己无法解决（角色定义在 core 的管辖范围）
iter 3: core    completed → success "3 roles (+parent), 34 tasks (+6 parent tasks), 7 flows"
iter 4: ux      failed → success    "22 screens (+ parent screens), gate pass"
iter 5: verify  waiting → success   "use-case tree complete, 2 minor gaps, audit clean"
```

**关键**: ux 发现问题后直接回退 core，不是自己瞎编一个 parent 角色。
core 重跑后 ux 重跑（因为新角色带来了新页面）。

**数据闭环检查**:
- core 重跑后 role-profiles.json 多了 parent，task-inventory.json 多了 6 个任务
- ux 重跑时拉新的 role-profiles → 为 parent 生成页面 → experience-map 更新
- verify 拉 core + ux 的完整输出 → 通过

---

## Test E: 双重回退 — verify → ux → core

**项目**: `logistics` — 物流管理系统，React + Go 微服务

**场景**: 一个复杂的连锁回退。

1. core 漏了"签收确认"这个任务（只有发货、运输、到达）
2. ux 因此也没有"签收确认页"的 experience-map
3. verify 的 journey walkthrough 发现"发货→运输→到达→???"流程断了

### 预期流转

```
iter 1: core    waiting → success   "5 roles, 42 tasks, 8 flows"
iter 2: ux      waiting → success   "24 screens, gate pass"
iter 3: verify  waiting → failure   "Flow 'delivery' has no end state after 'arrived'"
         ↓ diagnosis: flow incomplete → 需要补签收任务 → root cause = core
iter 4: core    completed → success "5 roles, 44 tasks (+签收确认+签收异常), 8 flows (delivery flow 补完)"
iter 5: ux      completed → success "26 screens (+签收确认页+签收异常页), gate re-pass"
iter 6: verify  failed → success    "All flows complete, audit clean"
```

**关键**: verify 诊断后直接回退到 core（root cause），core 修完后 ux 也要重跑
（因为新任务意味着新页面）。这是一个 **连锁回退**：verify → core → ux → verify。

**transition_log 应该显示**:
```
iter 3: verify  → failure
iter 4: core    → success  (backtrack edge: verify ⤴ core)
iter 5: ux      → success  (forward edge: core → ux, 因为 core 的输出变了)
iter 6: verify  → success  (forward edge: ux → verify)
```

**DAG 图**: 有一条红色虚线 verify ⤴ core，但 core → ux → verify 是正常实线
（不是回退，是 core 更新后的正常重新流转）。

---

## Test F: ux 被跳过 — CLI 项目

**项目**: `dbmigrate` — 数据库迁移工具，Go CLI

**场景**: CLI 项目没有前端，ux 整个跳过。

### 预期流转

```
iter 1: core    waiting → success   "1 role (operator), 12 commands, 4 command-flows"
iter 2: verify  waiting → success   "command scenarios complete, coverage OK"
```

**关键**: ux 节点不存在（bootstrap 不生成它）。core 直接连 verify。
verify 的 entry_requires 只检查 product-map/*.json，不要求 experience-map/。

**验证**: DAG 图上只有 2 个节点。

**数据闭环检查**:
- core 用 CLI archetype 输出 command-tree.json 代替 task-inventory.json
- verify 用 CLI archetype 做 command coverage 代替 screen completeness

---

## Test G: 3 节点合并成 1 — 超小项目

**项目**: `qrgen` — 二维码生成器，纯 Python 脚本，1 个功能

**场景**: 项目太小（1 个角色、3 个任务、2 个页面），bootstrap 把 core + ux + verify 合并成单个 `product-analysis` 节点。

### 预期流转

```
iter 1: product-analysis  waiting → success  "1 role, 3 tasks, 2 screens, 0 gaps"
```

**关键**: 1 次迭代完成。内部仍然按 core → ux → verify 的逻辑跑，
但全在一个 subagent 里，没有 orchestrator 级别的状态迁移。

**验证**: DAG 图上只有 1 个产品分析节点。

---

## Test H: verify 多次回退不同方向

**项目**: `marketplace` — 二手交易平台，React Native + Node.js

**场景**: verify 第一次回退到 ux（缺状态），修完后第二次回退到 core（缺角色）。

### 预期流转

```
iter 1: core    waiting → success   "3 roles (buyer/seller/admin), 38 tasks"
iter 2: ux      waiting → success   "20 screens, gate pass"
iter 3: verify  waiting → failure   "Screen 'dispute-resolution' missing error state"
         ↓ diagnosis → ux
iter 4: ux      completed → success "20 screens, dispute states complete, gate re-pass"
iter 5: verify  failed → failure    "Role 'moderator' referenced in dispute flow but not in roles"
         ↓ diagnosis → core (不同的 root cause)
iter 6: core    completed → success "4 roles (+moderator), 42 tasks, 9 flows"
iter 7: ux      completed → success "22 screens (+moderator screens), gate re-pass"
iter 8: verify  failed → success    "All complete, audit clean"
```

**关键**: verify 两次失败，两次回退到**不同方向**。
- 第一次 → ux（屏幕状态问题）
- 第二次 → core（角色缺失问题）

第二次回退到 core 后，ux 也要重跑（和 Test E 一样的连锁）。

**transition_log 应该有**:
- 2 条回退边：verify ⤴ ux (iter 4), verify ⤴ core (iter 6)
- 1 条连锁重跑：core → ux (iter 7)
- verify 自身出现 3 次 (iter 3, 5, 8)

---

## 覆盖矩阵

| Test | 入口 | core→ux | ux→verify | verify→ux | verify→core | ux→core | 跳过/合并 |
|------|------|---------|-----------|-----------|-------------|---------|----------|
| A taskboard | 有代码 | ✓ | ✓ | - | - | - | - |
| B bookshelf | 有代码 | ✓ | ✓ | - | ✓ backtrack | - | - |
| C healthcheck | 有代码 | ✓ | ✓ | ✓ backtrack | - | - | - |
| D classroom | 有代码 | ✓ backtrack→retry | ✓ | - | - | ✓ backtrack | - |
| E logistics | 有代码 | ✓ | ✓ | - | ✓ chain | - | 连锁回退 |
| F dbmigrate | 有代码 | - (跳过ux) | - | - | - | - | ux 跳过 |
| G qrgen | 有代码 | - | - | - | - | - | 全合并 |
| H marketplace | 有代码 | ✓ | ✓ | ✓ | ✓ | - | 多方向回退 |

### 状态覆盖

| 状态迁移 | 覆盖 Test |
|----------|----------|
| waiting → success | A (全部) |
| waiting → failure | B, C, D, E, H (verify/ux 首次失败) |
| completed → success (重跑) | B, D, E, H (回退后重跑) |
| failed → success (重试) | B, C, E, H (回退修复后重试) |
| failed → failure (连续失败) | H (verify 两次失败不同原因) |
| 节点跳过 | F (ux 不生成) |
| 节点合并 | G (3合1) |
| 连锁回退 (verify→core→ux→verify) | E, H |
| 双方向回退 (verify→ux + verify→core) | H |

---

## Iteration 2: 从零构建入口 + implement/tune-frontend 组合

### Test I: 从零构建 — concept → core → ux → verify → implement

**项目**: `petclinic` — 宠物诊所管理系统，从零构建，Flutter + Go

**入口**: 空目录 + README（goal=create）

**预期流转**:

```
iter 1:  product-concept  waiting → success  "宠物诊所：挂号、诊疗、处方、支付"
iter 2:  pa-core          waiting → success  "4 roles (owner/vet/nurse/admin), 32 tasks, 6 flows"
iter 3:  pa-ux            waiting → success  "16 screens, gate pass"
iter 4:  pa-verify        waiting → success  "use-cases complete, 1 minor gap, audit clean"
iter 5:  ui-design        waiting → success  "design spec + 4-role preview"
iter 6:  implement-flutter waiting → success  "Flutter client, 16 screens"
iter 7:  implement-go     waiting → success  "Go API, 32 endpoints"
iter 8:  compile-verify   waiting → success  "both build clean"
iter 9:  test-verify      waiting → success  "92% pass"
```

**关键验证**:
- pa-core 的入口是 product-concept.json（不是 source-summary.json）
- implement 节点（不是 translate）因为没有源码
- implement 拉 design-audit/audit-report.json + experience-map + ui-design-spec 来写代码

**数据闭环**:
```
concept → core 拉 concept.json → 写 product-map/
core → ux 拉 product-map/ → 写 experience-map/
ux → verify 拉 product-map/ + experience-map/ → 写 use-case/ + feature-gap/ + design-audit/
verify → ui-design 拉 experience-map/ → 写 ui-design/
verify → implement 拉 design-audit/ + experience-map/ + ui-design/ + task-inventory/ → 写代码
```

每一步都有明确的输入文件来源，无断裂。

---

### Test J: 从零构建 + 回退到 concept

**项目**: `mealplan` — 膳食规划 App，从零构建，React Native + Supabase

**场景**: concept 阶段定义了"膳食规划 + 营养追踪"，但 pa-core 做任务展开时发现 concept 中关于"过敏源管理"的需求含糊（只写了"支持过敏管理"但没说清是用户自己标记还是系统推荐）。

```
iter 1:  product-concept  waiting → success   "膳食规划 + 营养追踪 + 过敏管理"
iter 2:  pa-core          waiting → failure   "过敏源管理需求含糊，无法展开任务"
          ↓ diagnosis → concept 需要补充
iter 3:  product-concept  completed → success "补充：用户自标记过敏源 + 食谱自动过滤"
iter 4:  pa-core          failed → success    "5 roles, 38 tasks (+过敏标记+食谱过滤), 7 flows"
iter 5:  pa-ux            waiting → success   "20 screens, gate pass"
iter 6:  pa-verify        waiting → success   "complete"
```

**关键**: pa-core 回退到 product-concept（concept 本身也是一个节点，可以被回退到）。这验证了 concept 不只是"跑一次就完"的起始节点，它也参与图状流转。

**问题发现**: 当前 product-concept.md 的 Composition Hints 没有提到"可以被下游回退到"这个情况。concept 重跑时，它需要知道是补充细化而不是从头重新构思。

**建议**: 在 product-concept.md 加一条 backtrack 说明。

---

### Test K: implement + tune-frontend 组合

**项目**: `devboard` — 开发者仪表盘，React + Fastify，从零构建

**场景**: 从零构建完成后，跑 tune-frontend 检查前端架构。

```
iter 1-6:  (concept → core → ux → verify → ui-design → implement) 全部顺利
iter 7:    implement-react   waiting → success  "React client, 14 screens, Zustand state"
iter 8:    implement-api     waiting → success  "Fastify API, 28 endpoints"
iter 9:    compile-verify    waiting → success  "build clean"
iter 10:   tune-frontend     waiting → success  "Score 82/100: 2 duplicate components, consistent state mgmt, 3 magic numbers"
iter 11:   tune              waiting → success  "Score 88/100: clean architecture, 1 minor duplication"
```

**关键**: tune 和 tune-frontend **并行执行**（output_files 不交叉：tune 写 `.allforai/code-tuner/`，tune-frontend 写 `.allforai/tune-frontend/`）。

**验证**:
- tune-frontend 拉代码文件（不拉 .allforai/），和 tune 的输入来源一样但检查维度不同
- 两者的报告独立，不互相依赖
- 从零构建的代码因为是 LLM 生成的，tune-frontend 可能会发现更多组件重复（LLM 倾向于复制粘贴式编码）

---

### Test L: 大项目 pa-core 按领域拆分 + fan_out

**项目**: `supermarket` — 超市管理系统（POS + 库存 + 会员 + 供应链），从零构建

**场景**: 项目太大，bootstrap 把 pa-core 按业务领域拆成 fan_out。

```
bootstrap 生成：
  pa-core  fan_out: {source: bootstrap-profile.json, path: $.domains, parallel: true}
    → 4 个子任务：POS、库存、会员、供应链

iter 1:  product-concept   waiting → success
iter 2:  pa-core           waiting → success  "fan_out 4/4: POS 12 tasks, 库存 15 tasks, 会员 10 tasks, 供应链 18 tasks"
iter 3:  pa-ux             waiting → success  "38 screens total across 4 domains"
iter 4:  pa-verify         waiting → failure  "Cross-domain gap: POS 结账流程引用了会员积分但会员域没有积分查询任务"
          ↓ diagnosis → pa-core (fan_out partial retry: 只重跑会员子任务)
iter 5:  pa-core           completed → success "fan_out partial: 会员 12 tasks (+积分查询+积分抵扣)"
iter 6:  pa-ux             completed → success "40 screens (+积分相关页面)"
iter 7:  pa-verify         failed → success   "cross-domain complete"
```

**关键**: pa-core 回退时用 **fan_out partial retry** — 只重跑会员域，POS/库存/供应链不重跑。

**数据闭环**:
- 会员域的子任务重跑后，task-inventory.json 被 merge（其他域的任务保留）
- pa-ux 重跑时拉到更新后的 task-inventory → 为新任务生成页面
- pa-verify 拉到完整的 task-inventory + experience-map → 跨域覆盖通过

---

## 更新后的覆盖矩阵

| Test | 入口 | 特殊场景 |
|------|------|---------|
| A taskboard | 有代码 | 正常流转，无回退 |
| B bookshelf | 有代码 | verify→core 回退 |
| C healthcheck | 有代码 | verify→ux 回退 |
| D classroom | 有代码 | ux→core 回退 |
| E logistics | 有代码 | 连锁回退 verify→core→ux→verify |
| F dbmigrate | 有代码 | ux 跳过 (CLI) |
| G qrgen | 有代码 | 3 节点合并 |
| H marketplace | 有代码 | 多方向回退 |
| **I petclinic** | **从零** | **concept→core→ux→verify→implement 全链路** |
| **J mealplan** | **从零** | **pa-core→concept 回退** |
| **K devboard** | **从零** | **implement + tune + tune-frontend 并行** |
| **L supermarket** | **从零** | **pa-core fan_out + partial retry** |

### 发现的问题

**✅ 问题 1: product-concept 缺少 backtrack 说明**
→ 已修复，加了 Backtrack Triggers 段落。

---

## Iteration 3: 交互关系审计 — generate-artifacts 与 pa-core 产出冲突

### 发现的问题

**问题 2: generate-artifacts 和 pa-core 产出相同文件**

两者都写 `.allforai/product-map/` 下的 `task-inventory.json`, `role-profiles.json`, `business-flows.json`。

| | generate-artifacts | pa-core |
|--|-------------------|---------|
| 方法 | 从代码机械提取（fragments → merge scripts） | LLM 业务分析 |
| 入口 | source-summary + code-index | source-summary OR concept |
| 产出位置 | .allforai/product-map/ | .allforai/product-map/ |
| 脚本 | cr_merge_*.py | 无（LLM 直接生成） |

**这不是 bug，是职责定义不清。** 两者的关系应该是：

```
从代码流: discovery → generate-artifacts (机械提取) → pa-core (业务细化) → pa-ux → pa-verify
从零流:   concept → pa-core (直接生成) → pa-ux → pa-verify
```

即：generate-artifacts 是 pa-core 的**可选前置步骤**。当有代码时，先机械提取一遍，pa-core 在这个基础上做业务层面的细化和补全。当没有代码时，跳过 generate-artifacts，pa-core 直接从 concept 生成。

### 解决方案

1. generate-artifacts 产出写到 `.allforai/code-replicate/extracted/`（提取结果，中间产物）
2. pa-core 检测到 `.allforai/code-replicate/extracted/` 存在时，读它作为初始输入进行业务细化
3. pa-core 写最终版到 `.allforai/product-map/`（业务分析结果，最终产物）
4. 无代码时 pa-core 不读 extracted/，直接从 concept 生成

这样 generate-artifacts 和 pa-core 职责清晰：
- generate-artifacts = **提取**（从代码到结构化数据）
- pa-core = **分析**（从结构化数据到业务理解）

### Test M: generate-artifacts + pa-core 协作

**项目**: `shopnow` — React + Express 电商（有代码，goal=analyze+translate）

```
iter 1:  discovery           waiting → success  "4 packages, React 18 + Express"
iter 2:  generate-artifacts  waiting → success  "extracted: 3 roles, 28 tasks, 5 flows (机械提取)"
iter 3:  pa-core             waiting → success  "refined: 4 roles (+guest), 35 tasks (+7 补全), 6 flows (业务细化)"
iter 4:  pa-ux               waiting → success  "20 screens"
iter 5:  pa-verify           waiting → success  "complete"
```

**关键**:
- generate-artifacts 提取了 28 个 tasks，pa-core 在此基础上补全了 7 个（CRUD 闭合 + 业务推理）
- generate-artifacts 漏了 guest 角色（代码里没有显式的 guest auth），pa-core 从业务角度补上
- pa-core 的 entry_requires 包含 generate-artifacts 的产出文件

### Test N: 无 generate-artifacts — 从零构建

**项目**: `petclinic`（同 Test I）

```
iter 1:  product-concept  waiting → success
iter 2:  pa-core          waiting → success  "直接从 concept 生成，不读 extracted/"
...
```

**关键**: bootstrap 不生成 generate-artifacts 节点。pa-core 的 entry_requires 只有 concept.json。
- 回退时上游重跑 → 产出文件更新 → 下游重跑时拉到新数据
- 连锁回退时 orchestrator 的 diagnosis 正确定位 root cause
- 跳过/合并时 bootstrap 按项目规模决定，不影响数据契约
