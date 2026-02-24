# Feature Audit — 执行流程与规范总览

> 本文档是 feature-audit 技能的中枢文档，定义执行流程、模式、交互规范和词汇纪律。

---

## 1. 执行流程总览

```
Step 0: 项目画像 + 需求源发现
  │  扫描项目结构、识别技术栈、定位需求源（PRD/README/OpenAPI/路由/菜单）
  │  输出: audit-sources.json
  │  ▸ 用户确认需求来源列表
  ▼
Step 1: 功能清单构建
  │  并行构建"计划功能"列表 + "已实现功能"列表，执行匹配对齐
  │  输出: feature-inventory.json
  │  ▸ 用户确认匹配结果
  ▼
Step 2: 差距分析
  │  对每个功能分类: COMPLETE / PARTIAL / MISSING / UNPLANNED / DEFERRED
  │  输出: gap-analysis.json
  │  ▸ 用户确认分类
  ▼
Step 3: 闭环验证 ★ 核心步骤
  │  对 COMPLETE/PARTIAL 功能做用户旅程四步验证（纯静态）
  │  入口存在 → 操作可执行 → 有反馈 → 结果可见
  │  输出: closed-loop.json
  │  ▸ 用户确认误报
  ▼
Step 4: 报告生成
  │  汇总所有结果，写入文件 + 对话中直接输出摘要
  │  输出: audit-report.md / audit-tasks.json / audit-decisions.json
  │  ▸ 用户确认最终报告
  ▼
  Done
```

---

## 2. 执行模式

| 模式 | 参数 | 执行步骤 | 适用场景 |
|------|------|----------|----------|
| **full** | 无参数 或 `full` | Step 0 → 1 → 2 → 3 → 4 | 首次审计、完整审计 |
| **quick** | `quick` | Step 0 → 1 → 2 → 4（跳过 Step 3） | 快速看差距，不需要闭环验证 |
| **incremental** | `incremental` | git diff → 筛选变动功能 → Step 2 → 3 → 4 | 代码有改动，只审计变更部分 |
| **verify** | `verify` | 加载已有清单 → Step 3 → Step 4 | 修复后重新验证闭环 |

### 模式前置条件

```
full / quick     → 无前置条件，从零开始
                   若已有 audit-decisions.json → 自动复用用户历史决策

incremental      → 必须已有 feature-inventory.json
                   否则提示: "请先运行 /feature-audit full 生成基线数据"

verify           → 必须已有 feature-inventory.json + gap-analysis.json
                   否则提示: "请先运行 /feature-audit full 生成基线数据"
```

---

## 3. 交互模式

### 核心原则：每个 Step 必须有用户确认环节

Claude 不得在用户确认前自动进入下一个 Step。每个 Step 的确认环节是**强制性的**，不可跳过。

### 确认检查点

| Step | 确认内容 | 询问方式 |
|------|----------|----------|
| Step 0 | 需求来源列表是否完整 | "我发现以下需求来源：{列表}。是否有遗漏？是否需要排除某些来源？" |
| Step 1 | 功能匹配结果是否准确 | "以下功能匹配结果中有 {N} 条低置信度匹配，请确认：{列表}" |
| Step 2 | 差距分类是否正确 | "以下功能初步分类为 MISSING/PARTIAL，请逐条确认是否正确，或标记为 DEFERRED" |
| Step 3 | 闭环断裂是否为误报 | "以下功能被检测到旅程断裂：{列表}。是否有误报？" |
| Step 4 | 最终报告是否准确 | 在对话中直接输出完整摘要，包含具体功能列表和闭环详情 |

### 交互流程示意

```
Claude: [执行 Step N]
Claude: "Step N 完成。结果如下：..."
Claude: "请确认以上结果，或指出需要调整的地方。"
        ← 等待用户回复 →
用户:   "XX 功能分类不对，应该是 DEFERRED"
Claude: "已更新。确认继续下一步？"
用户:   "继续"
Claude: [执行 Step N+1]
```

**禁止行为**：
- 不得将多个 Step 合并执行后一次性展示
- 不得在用户未回复时自动跳到下一个 Step
- 不得用 "如果没问题我继续了" 然后不等回复就继续

---

## 4. 词汇规范

### 允许使用的措辞

| 措辞 | 适用场景 |
|------|----------|
| "未找到对应实现" | 需求源中有描述，但代码中无对应实现（MISSING） |
| "未在需求源中提及" | 代码中存在功能，但需求文档未提及（UNPLANNED） |
| "代码中存在但需求源未覆盖" | 同上，用于报告中的正式表述 |
| "用户旅程在第 X 步中断" | 闭环验证发现断裂（Step 3） |
| "部分实现" | 有代码但不完整（PARTIAL） |

### 绝对禁止的措辞

| 禁止措辞 | 违规原因 |
|----------|----------|
| "应该添加" | 暗示用户必须添加功能 — 审计不做建议 |
| "建议实现" | 同上 |
| "最佳实践建议" | 超出审计范围，进入了 code-tuner 的领域 |
| "推荐增加" | 暗示功能缺失是问题 — 但只有用户才能决定 |
| "缺少必要的" | 预设了"必要"的判断 — 审计只陈述事实 |
| "需要补充" | 暗示当前状态不完整 — 可能是 DEFERRED |

### 原则

审计只回答 **"有没有"**，不回答 **"应不应该"**。

```
正确: "需求源 docs/prd.md:42 描述了'批量导出'功能，未找到对应实现。"
错误: "缺少批量导出功能，建议实现。"

正确: "代码中存在 /api/legacy-sync 端点，未在需求源中提及。"
错误: "存在未规划的 legacy-sync 功能，需要补充文档。"

正确: "'订单管理'用户旅程在第 3 步中断：创建订单后无 Toast/跳转反馈。"
错误: "'订单管理'缺少必要的成功提示，应该添加 Toast 提示。"
```

---

## 5. 输出文件

所有输出文件位于项目根目录下的 `.feature-audit/` 目录：

| 文件 | 产出 Step | 内容 | 格式 |
|------|-----------|------|------|
| `audit-sources.json` | Step 0 | 需求源列表（PRD/README/OpenAPI 等路径 + 类型） | JSON |
| `feature-inventory.json` | Step 1 | 计划功能列表 + 已实现功能列表 + 匹配关系 | JSON |
| `gap-analysis.json` | Step 2 | 每个功能的差距分类 + 证据 + 来源引用 | JSON |
| `closed-loop.json` | Step 3 | 每个功能的闭环评分（X/4）+ 断裂环节详情 | JSON |
| `audit-report.md` | Step 4 | 人类可读的审计报告 | Markdown |
| `audit-tasks.json` | Step 4 | 待办清单（可导入 issue tracker） | JSON |
| `audit-decisions.json` | Step 4 | 用户决策日志（增量运行复用） | JSON |

### 目录结构

```
your-project/
└── .feature-audit/
    ├── audit-sources.json       # Step 0 产出
    ├── feature-inventory.json   # Step 1 产出
    ├── gap-analysis.json        # Step 2 产出
    ├── closed-loop.json         # Step 3 产出
    ├── audit-report.md          # Step 4 产出：审计报告
    ├── audit-tasks.json         # Step 4 产出：待办清单
    └── audit-decisions.json     # Step 4 产出：用户决策日志（跨运行持久化）
```

---

## 6. 闭环验证是核心

> Step 3（闭环验证）是 feature-audit 技能的**核心价值所在**。差距分析只回答"有没有做"，闭环验证回答"做了能不能用"。

### 用户旅程四步验证

对每个 COMPLETE 或 PARTIAL 功能，检查用户旅程是否闭环：

```
Step A: 入口存在？        Step B: 操作可执行？      Step C: 有反馈？         Step D: 结果可见？
───────────────────      ──────────────────       ──────────────          ────────────────
菜单项 / 导航链接 /       表单组件 / 提交按钮 /     Toast / 消息提示 /       列表刷新 /
路由可达 / 按钮入口        API 调用 / 事件处理       页面跳转 / 状态变更      详情页展示 /
                                                                         数据更新可见
```

### 评分规则

| 评分 | 含义 | 说明 |
|------|------|------|
| **4/4** | 完整闭环 | 四步全部通过 |
| **3/4** | 基本闭环 | 缺少反馈或结果可见中的一步 |
| **2/4** | 部分闭环 | 有入口和操作，但后续断裂 |
| **1/4** | 严重断裂 | 仅有入口，操作不可执行 |
| **0/4** | 无闭环 | 无入口或完全不可达 |

### 检查方式（纯静态分析）

闭环验证通过**代码分析**完成，不需要运行应用：

```
入口存在    → 检查路由配置、菜单配置、导航组件中是否有对应路径
操作可执行  → 检查页面组件中是否有表单、提交事件、API 调用
有反馈      → 检查操作后是否有 message.success / Toast / notification / router.push
结果可见    → 检查操作后是否有列表刷新（refetch/invalidate）、跳转到详情页、状态更新
```

### 为什么闭环验证是核心

```
场景: "订单管理"功能

差距分析结果: COMPLETE（需求有，代码也有）
  → 但这不代表功能可用

闭环验证结果: 2/4
  ✅ 入口存在（菜单中有"订单管理"，路由 /orders 已注册）
  ✅ 操作可执行（OrderForm 组件有表单，提交调用 POST /api/orders）
  ❌ 无反馈（提交后无 Toast/跳转，onSuccess 回调为空）
  ❌ 结果不可见（OrderList 组件未在创建后调用 refetch）

  → 功能"做了"但用户旅程在第 3 步中断
```

**没有闭环验证，审计只是一份对照表；有了闭环验证，审计变成了真正的质量检查。**

---

## 7. 5 条铁律速查

| # | 铁律 | 一句话 | 违规示例 |
|---|------|--------|----------|
| 1 | **来源绑定** | 每条发现必须引用 `文件:行号` | ~~"缺少导出功能"~~（没有来源） |
| 2 | **词汇纪律** | 只说"有没有"，不说"应不应该" | ~~"建议实现批量删除"~~ |
| 3 | **用户权威** | 所有分类由用户最终确认 | ~~自动将功能标为 MISSING 不询问~~ |
| 4 | **保守分类** | 不确定就标 `needs_confirmation` | ~~猜测功能匹配关系~~ |
| 5 | **硬编码禁令** | 报告中禁止出现功能添加/最佳实践/技术选型建议 | ~~"推荐使用 Redux 管理状态"~~ |

### 速记口诀

```
来源绑定 — 无证据不发言
词汇纪律 — 陈述事实不建议
用户权威 — 用户说了算
保守分类 — 不确定就问
硬编码禁令 — 审计不是咨询
```

---

## 8. 增量运行机制

### audit-decisions.json 的作用

`audit-decisions.json` 保存用户在审计过程中做出的所有决策，使后续运行不需要重复询问。

### 持久化的决策类型

```json
{
  "_meta": {
    "version": "1.0",
    "created_at": "2026-02-24T10:00:00Z",
    "updated_at": "2026-02-24T14:30:00Z",
    "project_hash": "abc123"
  },
  "decisions": [
    {
      "feature_id": "F-012",
      "feature_name": "日报管理",
      "decision": "DEFERRED",
      "reason": "用户确认：该功能已砍掉，不再需要",
      "decided_at": "2026-02-24T10:15:00Z"
    },
    {
      "feature_id": "F-023",
      "feature_name": "legacy-sync",
      "decision": "UNPLANNED_ACCEPTED",
      "reason": "用户确认：历史遗留功能，保留但不纳入审计范围",
      "decided_at": "2026-02-24T10:20:00Z"
    }
  ],
  "source_overrides": [
    {
      "file": "docs/draft-v2.md",
      "action": "exclude",
      "reason": "用户确认：这是草稿，不作为需求源"
    }
  ],
  "match_overrides": [
    {
      "planned": "用户权限管理",
      "implemented": "/admin/permissions",
      "action": "confirm_match",
      "reason": "用户确认匹配"
    }
  ]
}
```

### 增量运行流程

```
/feature-audit incremental
        │
        ▼
  检测 git diff（与上次审计的 commit 对比）
        │
        ▼
  筛选变动涉及的功能
  （路由文件变了 → 对应功能；页面组件变了 → 对应功能）
        │
        ▼
  加载 audit-decisions.json
  （已确认为 DEFERRED 的功能 → 跳过；已确认的匹配 → 复用）
        │
        ▼
  仅对变动功能执行 Step 2 → Step 3 → Step 4
        │
        ▼
  更新 audit-decisions.json（合并新决策）
```

### 决策复用规则

| 决策类型 | 复用条件 | 失效条件 |
|----------|----------|----------|
| DEFERRED | 无条件复用 | 用户手动取消 |
| UNPLANNED_ACCEPTED | 无条件复用 | 对应代码被删除 |
| source_overrides | 无条件复用 | 用户手动取消 |
| match_overrides | 对应代码未变动时复用 | 对应代码有 git diff 变动 |
| 闭环验证确认 | 对应代码未变动时复用 | 对应代码有 git diff 变动 |

### 首次运行 vs 增量运行

```
首次运行 (full):
  ✅ 全量扫描所有功能
  ✅ 每条分类都需要用户确认
  ✅ 生成 audit-decisions.json 作为基线

增量运行 (incremental):
  ✅ 只处理 git diff 涉及的功能
  ✅ 自动复用已确认的决策（不重复询问）
  ✅ 仅对新发现或变动功能询问用户
  ✅ 合并更新 audit-decisions.json
```
