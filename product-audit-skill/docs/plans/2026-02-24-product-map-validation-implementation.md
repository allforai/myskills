# product-map 竞品参考 + 校验步骤 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 product-map 技能中新增竞品参考（Step 0 提问，Step 7 分析）和三合一校验步骤（完整性 + 冲突重扫 + 竞品差异），版本升至 v2.3.0。

**Architecture:** 纯 Markdown skill 文件改动，无运行时代码。改动集中在 `skills/product-map.md`（主逻辑）和 `commands/product-map.md`（命令入口），辅以 README.md、SKILL.md、plugin.json 同步更新。每个 Task 独立可验证：改完后用 Read 工具确认内容正确，再提交。

**Tech Stack:** Markdown（skill 文件）、JSON schema（示例）、git

**设计文档：** `docs/plans/2026-02-24-product-map-validation-design.md`

---

## Task 1：`skills/product-map.md` — Step 0 新增竞品提问

**Files:**
- Modify: `skills/product-map.md`（Step 0 章节，约第 94-116 行）

**Step 1：定位 Step 0 的用户确认位置**

读取 `skills/product-map.md` 第 94-120 行，找到：
```
**用户确认**：这个项目的功能全景对吗？有没有遗漏的模块？
```

**Step 2：在用户确认前插入竞品提问段落**

在上述「用户确认」行的**前面**插入：

```markdown
**竞品提问**（画像确认前，先问一句）：

> 这个产品主要对标哪些竞品？（例如：Shopify、有赞、微盟；或「暂时没有参照」也可以）

根据用户回答：
- **有竞品**：记录名字列表，生成 `competitor-profile.json` 草稿（只写名字，不做分析），Step 7 再做 Web 搜索
- **无竞品**：记录 `competitors: []`，Step 7 跳过竞品差异部分，只做完整性 + 冲突校验

生成 `competitor-profile.json` 草稿：

```json
{
  "competitors": ["Shopify", "有赞"],
  "analysis_status": "pending",
  "analyzed_at": null
}
```

> 草稿此时只写入名字，Step 7 执行完后补全竞品功能数据，`analysis_status` 改为 `"completed"`。

```

**Step 3：验证**

读取改动区域，确认：
- 竞品提问出现在「用户确认」之前
- JSON 草稿 schema 包含 `competitors`、`analysis_status`、`analyzed_at`
- 有/无竞品两种分支都有说明

**Step 4：提交**

```bash
cd /home/hello/Documents/myskills/product-audit-skill
git add skills/product-map.md
git commit -m "feat(product-map): Step 0 新增竞品提问"
```

---

## Task 2：`skills/product-map.md` — 新增 Step 7 校验章节

**Files:**
- Modify: `skills/product-map.md`（Step 6 章节末尾之后插入）

**Step 1：定位插入位置**

读取 `skills/product-map.md`，找到 Step 6 章节末尾：
```
输出：`.allforai/product-map/product-map.json`、`.allforai/product-map/product-map-report.md`
```
在此行后、`## 输出文件结构` 章节前插入 Step 7。

**Step 2：插入完整 Step 7 章节**

```markdown
---

### Step 7：校验

Step 6 完成后必须执行（所有模式均不可跳过）。分三部分顺序执行，完成后统一展示，一次用户确认。

#### Part 1：完整性扫描

遍历 `task-inventory.json` 所有任务，逐项检查字段完整性：

| 检查项 | Flag |
|--------|------|
| `exceptions` 为空或缺失 | `MISSING_EXCEPTIONS` |
| `acceptance_criteria` 少于 3 条 | `THIN_AC` |
| `rules` 为空 | `MISSING_RULES` |
| 高频任务缺少 CRUD 中某类操作 | `HIGH_FREQ_CRUD_GAP` |
| `value` 字段缺失 | `MISSING_VALUE` |

#### Part 2：冲突重扫

基于完整地图，比 Step 4 覆盖更广，检测三类跨任务冲突：

| 冲突类型 | Flag | 说明 |
|----------|------|------|
| 跨角色规则矛盾 | `CROSS_ROLE_CONFLICT` | A 角色的规则和 B 角色的规则互相冲突 |
| 状态流转死锁 | `STATE_DEADLOCK` | 任务 A 的输出状态被任务 B 的规则拒绝 |
| 幂等规则不一致 | `IDEMPOTENCY_CONFLICT` | 两个任务对同一对象的幂等规则不一致 |

#### Part 3：竞品差异（`competitors` 非空时执行）

Web 搜索加载各竞品功能概况，与完整任务清单做 diff，生成三列：

| 列 | 含义 | 用户决策 |
|----|------|----------|
| `we_have_they_dont` | 我们有竞品没有 | 确认是否作为差异化保留 |
| `they_have_we_dont` | 竞品有我们没有 | 评估是否补齐 |
| `both_have_different_approach` | 都有但做法不同 | 确认设计分歧方向 |

Web 搜索完成后，将竞品功能数据补全到 `competitor-profile.json`，`analysis_status` 改为 `"completed"`。

#### 用户确认

三部分结果合并展示，用户确认：
- 哪些完整性问题是真实问题（vs 误报）
- 哪些冲突需要处理
- 哪些竞品差距需要跟进

确认后将结果写入 `validation-report.json` 和 `validation-report.md`。

#### `validation-report.json` Schema

```json
{
  "generated_at": "2026-02-24T12:00:00Z",
  "summary": {
    "completeness_issues": 3,
    "conflict_issues": 2,
    "competitor_gaps": 4
  },
  "completeness": [
    {
      "task_id": "T001",
      "task_name": "创建并提交退款单",
      "flags": ["THIN_AC"],
      "detail": "acceptance_criteria 只有 2 条，建议补充到 5 条以上",
      "confirmed": false
    }
  ],
  "conflicts": [
    {
      "id": "V001",
      "type": "CROSS_ROLE_CONFLICT",
      "description": "T001 规定退款金额提交后不可修改，T007（财务审核）允许审核时调整金额",
      "affected_tasks": ["T001", "T007"],
      "severity": "高",
      "confirmed": false
    }
  ],
  "competitor_diff": {
    "competitors_analyzed": ["Shopify", "有赞"],
    "we_have_they_dont": [
      {
        "feature": "退款单幂等去重",
        "our_task": "T001",
        "note": "差异化优势，建议保留",
        "confirmed": false
      }
    ],
    "they_have_we_dont": [
      {
        "feature": "批量退款",
        "competitor": "有赞",
        "note": "高频场景，建议评估是否补齐",
        "confirmed": false
      }
    ],
    "both_have_different_approach": [
      {
        "feature": "审批流",
        "our_approach": "固定两级审批",
        "their_approach": "动态多级审批（有赞）",
        "note": "设计分歧，需确认方向",
        "confirmed": false
      }
    ]
  }
}
```

#### `validation-report.md` 结构（摘要级，人类可读）

```
# 产品地图校验报告

校验问题 X 个（完整性 X / 冲突 X）· 竞品差距：竞品有我没有 X 个 / 我有竞品没有 X 个 / 做法不同 X 个

## 完整性问题
- T001 THIN_AC：acceptance_criteria 只有 2 条
- T005 MISSING_EXCEPTIONS：exceptions 为空

## 冲突问题
- V001 CROSS_ROLE_CONFLICT（高）：T001 vs T007，退款金额修改规则矛盾

## 竞品差异
### 竞品有我们没有（潜在缺口）
- 批量退款（有赞）— 高频场景，建议评估

### 我们有竞品没有（差异化）
- 退款单幂等去重 — 差异化优势，建议保留

### 做法不同（设计分歧）
- 审批流：我们固定两级 vs 有赞动态多级 — 需确认方向

> 完整数据见 .allforai/product-map/validation-report.json
```

输出：`.allforai/product-map/validation-report.json`、`.allforai/product-map/validation-report.md`、`.allforai/product-map/competitor-profile.json`（补全）

```

**Step 3：验证**

读取改动区域，确认：
- Step 7 位于 Step 6 之后、`## 输出文件结构` 之前
- 三部分（完整性 / 冲突重扫 / 竞品差异）均有完整说明
- validation-report.json Schema 包含 `completeness`、`conflicts`、`competitor_diff` 三个顶层字段
- validation-report.md 模板存在且为摘要级

**Step 4：提交**

```bash
git add skills/product-map.md
git commit -m "feat(product-map): 新增 Step 7 校验（完整性+冲突重扫+竞品差异）"
```

---

## Task 3：`skills/product-map.md` — 更新输出文件结构 + summary schema + 工作流图

**Files:**
- Modify: `skills/product-map.md`（三处：工作流图、输出文件结构、Step 6 的 product-map.json schema）

**Step 1：更新工作流图**

找到：
```
Step 6: 输出产品地图报告
      汇总所有已确认数据，生成 product-map.json 和 product-map-report.md
```
在末尾追加：
```
      ↓
Step 7: 校验
      完整性扫描 + 冲突重扫 + 竞品差异（Web 搜索）
      → 用户确认，生成 validation-report.json + validation-report.md
```

**Step 2：更新输出文件结构**

找到：
```
.allforai/product-map/
├── role-profiles.json          # Step 1: 角色画像
├── task-inventory.json         # Step 2: 任务清单（完整功能点描述）
├── conflict-report.json        # Step 4: 任务级冲突检测结果
├── constraints.json            # Step 5: 业务约束清单
├── product-map.json            # Step 6: 汇总文件（供其他技能加载）
├── product-map-report.md       # Step 6: 可读报告
└── product-map-decisions.json  # 用户决策日志（增量复用）
```
替换为：
```
.allforai/product-map/
├── role-profiles.json          # Step 1: 角色画像
├── task-inventory.json         # Step 2: 任务清单（完整功能点描述）
├── conflict-report.json        # Step 4: 任务级冲突检测结果
├── constraints.json            # Step 5: 业务约束清单
├── product-map.json            # Step 6: 汇总文件（供其他技能加载）
├── product-map-report.md       # Step 6: 可读报告
├── competitor-profile.json     # Step 0 草稿 → Step 7 补全竞品功能数据
├── validation-report.json      # Step 7: 三合一校验结果（机器可读）
├── validation-report.md        # Step 7: 校验摘要（人类可读）
└── product-map-decisions.json  # 用户决策日志（增量复用）
```

**Step 3：更新 product-map.json 的 summary schema**

找到 Step 6 中 `summary` 字段示例：
```json
"summary": {
    "role_count": 3,
    "task_count": 24,
    "conflict_count": 1,
    "constraint_count": 5
  },
```
替换为：
```json
"summary": {
    "role_count": 3,
    "task_count": 24,
    "conflict_count": 1,
    "constraint_count": 5,
    "validation_issues": 5,
    "competitor_gaps": 3
  },
```

**Step 4：验证**

确认三处改动均正确：工作流图有 Step 7、输出文件列表有三个新文件、summary 有两个新字段。

**Step 5：提交**

```bash
git add skills/product-map.md
git commit -m "feat(product-map): 更新工作流图、输出结构和 summary schema"
```

---

## Task 4：`skills/product-map.md` — 铁律更新

**Files:**
- Modify: `skills/product-map.md`（`## 5 条铁律` 章节）

**Step 1：更新铁律 5，新增 Step 7 不可跳过的说明**

找到铁律 5：
```
### 5. 完整功能地图不依赖界面梳理
```
在铁律 5 之后，追加新铁律：

```markdown
### 6. Step 7 校验不可跳过

Step 7 是地图质量保障，在所有模式（包括 `quick`）下必须执行。校验发现的问题只报告，由用户决定处理优先级；竞品差异只供参考，用户有权忽略。`validation-report.json` 中每条问题的 `confirmed` 字段记录用户决策，下次运行自动跳过已确认项。
```

同时在「每步确认，增量复用」段落，更新提及 Step 的范围：将原来的说明补充"包括 Step 7 的校验决策"。

**Step 2：验证**

确认铁律 6 存在，内容包含「所有模式必须执行」和「confirmed 字段」。

**Step 3：提交**

```bash
git add skills/product-map.md
git commit -m "feat(product-map): 新增铁律 6（Step 7 校验不可跳过）"
```

---

## Task 5：`commands/product-map.md` — 模式路由 + 报告摘要更新

**Files:**
- Modify: `commands/product-map.md`

**Step 1：更新模式路由**

找到：
```
- **无参数 或 `full`** → 完整流程：Step 0 → Step 1 → Step 2 → Step 4 → Step 5 → Step 6
- **`quick`** → 快速模式：Step 0 → Step 1 → Step 2 → Step 6（跳过 Step 4 冲突检测和 Step 5 约束识别）
```
替换为：
```
- **无参数 或 `full`** → 完整流程：Step 0 → Step 1 → Step 2 → Step 4 → Step 5 → Step 6 → Step 7
- **`quick`** → 快速模式：Step 0 → Step 1 → Step 2 → Step 6 → Step 7（跳过 Step 4/5，Step 7 不可跳过）
```

**Step 2：更新报告摘要模板**

找到报告摘要中的总览表格：
```
| 用户角色 | X 个 |
| 核心任务 | X 个 |
| 高频任务（帕累托 Top 20%） | X 个 |
| 冲突/CRUD 缺口（仅 full 模式） | X 个 |
| 业务约束（仅 full 模式） | X 条 |
```
替换为：
```
| 用户角色 | X 个 |
| 核心任务 | X 个 |
| 高频任务（帕累托 Top 20%） | X 个 |
| 冲突/CRUD 缺口（仅 full 模式） | X 个 |
| 业务约束（仅 full 模式） | X 条 |
| 校验问题 | X 个（完整性 X / 冲突 X） |
| 竞品差距 | 竞品有我没有 X 个 / 我有竞品没有 X 个 / 做法不同 X 个 |
```

**Step 3：更新「结果写入」说明**

找到：
```
1. 将结果写入 `.product-map/` 目录下对应的 JSON 文件
```
在写入说明后补充：
```
（Step 7 将结果写入 `validation-report.json`、`validation-report.md`、`competitor-profile.json`）
```

**Step 4：更新报告底部的文件路径列表**

找到：
```
> 产品地图: `.allforai/product-map/product-map.json`
> 可读报告: `.allforai/product-map/product-map-report.md`
> 决策日志: `.allforai/product-map/product-map-decisions.json`
```
替换为：
```
> 产品地图: `.allforai/product-map/product-map.json`
> 可读报告: `.allforai/product-map/product-map-report.md`
> 校验报告: `.allforai/product-map/validation-report.md`
> 竞品分析: `.allforai/product-map/competitor-profile.json`
> 决策日志: `.allforai/product-map/product-map-decisions.json`
```

**Step 5：验证**

读取 `commands/product-map.md`，确认：
- 两个模式路由都以 Step 7 结尾
- 总览表格有「校验问题」和「竞品差距」两行
- 报告底部有 `validation-report.md` 和 `competitor-profile.json`

**Step 6：提交**

```bash
git add commands/product-map.md
git commit -m "feat(product-map): 命令层更新模式路由和报告摘要"
```

---

## Task 6：`README.md` + `SKILL.md` — 同步新增输出文件

**Files:**
- Modify: `README.md`（输出目录树）
- Modify: `SKILL.md`（文件结构树）

**Step 1：更新 README.md 输出树**

找到 `product-map/` 子树：
```
    ├── product-map/
    │   ├── role-profiles.json          # 角色画像（权限边界、KPI）
    ...
    │   └── product-map-decisions.json  # 用户决策日志
```
在 `product-map-decisions.json` 行之前插入三行：
```
    │   ├── competitor-profile.json     # 竞品功能概况（Step 0 草稿→Step 7 补全）
    │   ├── validation-report.json      # 三合一校验结果（机器可读）
    │   ├── validation-report.md        # 校验摘要（人类可读）
```

**Step 2：同样更新 SKILL.md 文件结构树**

找到 SKILL.md 中 `product-map/` 子树，同样插入三行（内容同上）。

**Step 3：验证**

确认 README.md 和 SKILL.md 的 product-map 子树都有三个新文件。

**Step 4：提交**

```bash
git add README.md SKILL.md
git commit -m "docs: README 和 SKILL.md 同步新增校验和竞品输出文件"
```

---

## Task 7：`plugin.json` — 版本升至 v2.3.0

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1：更新版本**

找到：
```json
"version": "2.2.0"
```
替换为：
```json
"version": "2.3.0"
```

**Step 2：验证**

读取文件确认版本正确。

**Step 3：提交并推送**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: v2.3.0 — product-map 新增竞品参考和校验步骤"
git push origin main
```

---

## 验证清单（全部完成后）

- [ ] `skills/product-map.md` Step 0 有竞品提问 + `competitor-profile.json` 草稿 schema
- [ ] `skills/product-map.md` Step 7 有三部分（完整性 / 冲突重扫 / 竞品差异）
- [ ] `skills/product-map.md` 工作流图以 Step 7 结尾
- [ ] `skills/product-map.md` 输出文件结构包含三个新文件
- [ ] `skills/product-map.md` summary schema 含 `validation_issues` 和 `competitor_gaps`
- [ ] `skills/product-map.md` 铁律 6 存在
- [ ] `commands/product-map.md` 模式路由以 Step 7 结尾
- [ ] `commands/product-map.md` 报告摘要有竞品差距和校验问题两行
- [ ] `README.md` + `SKILL.md` product-map 子树有三个新文件
- [ ] `plugin.json` 版本为 `2.3.0`
