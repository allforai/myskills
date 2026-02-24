# product-map 竞品参考 + 校验步骤 设计文档

**日期**：2026-02-24
**版本影响**：v2.2.0 → v2.3.0

---

## 背景

功能地图是整个产品审计套件的基础，生成质量直接影响下游所有技能。当前流程缺少两个维度：

1. **竞品参照**：地图完全基于代码和 PM 视角，没有外部参照系，容易遗漏行业标准功能
2. **生成后校验**：地图生成后没有系统性验证，字段完整性、规则冲突、竞品差异都靠人工发现

---

## 设计目标

- Step 0 新增竞品提问，记录名字备用，不打断主流程
- Step 6 完成后新增 Step 7（校验），三合一：完整性 + 冲突重扫 + 竞品差异
- 竞品 Web 搜索集中在 Step 7 执行，避免主流程分心
- Step 7 同样有用户确认，输出双格式报告（JSON + Markdown）
- Step 7 不可跳过（包括 quick 模式）

---

## 流程变更

### 旧流程
```
Step 0 → Step 1 → Step 2 → Step 4 → Step 5 → Step 6
```

### 新流程
```
Step 0（新增竞品提问）→ Step 1 → Step 2 → Step 4 → Step 5 → Step 6 → Step 7（新增）
quick 模式：Step 0 → Step 1 → Step 2 → Step 6 → Step 7
```

---

## 详细设计

### Step 0 改动：新增竞品提问

在原有画像确认前，插入一个问题：

```
在我们开始之前：这个产品主要对标哪些竞品？
（例如：Shopify、有赞、微盟；或「暂时没有参照」也可以）
```

- **有竞品**：记录名字列表，生成 `competitor-profile.json` 草稿，Step 7 再做 Web 搜索分析
- **无竞品**：Step 7 跳过竞品差异部分，只做完整性 + 冲突校验

`competitor-profile.json` 草稿（Step 0 写入）：
```json
{
  "competitors": ["Shopify", "有赞"],
  "analysis_status": "pending",
  "analyzed_at": null
}
```

Step 7 执行后补全竞品功能数据，`analysis_status` 改为 `"completed"`。

---

### Step 7：校验（新增）

Step 6 完成后执行，分三部分，一次用户确认。

#### Part 1：完整性扫描

遍历 `task-inventory.json` 所有任务，检查字段完整性：

| 检查项 | Flag |
|--------|------|
| `exceptions` 为空或缺失 | `MISSING_EXCEPTIONS` |
| `acceptance_criteria` 少于 3 条 | `THIN_AC` |
| `rules` 为空 | `MISSING_RULES` |
| 高频任务缺少 CRUD 中某类操作 | `HIGH_FREQ_CRUD_GAP` |
| `value` 字段缺失 | `MISSING_VALUE` |

#### Part 2：冲突重扫

基于完整地图，比 Step 4 覆盖更广：

| 冲突类型 | Flag |
|----------|------|
| 跨角色的规则互相矛盾 | `CROSS_ROLE_CONFLICT` |
| 状态流转死锁（A 输出状态被 B 的规则拒绝） | `STATE_DEADLOCK` |
| 两个任务对同一对象的幂等规则不一致 | `IDEMPOTENCY_CONFLICT` |

#### Part 3：竞品差异（有竞品时执行）

Web 搜索加载各竞品功能概况，与完整任务清单做 diff，生成三列：

- `we_have_they_dont`：我们有竞品没有（差异化，确认是否保留）
- `they_have_we_dont`：竞品有我们没有（潜在缺口，确认是否补齐）
- `both_have_different_approach`：都有但做法不同（设计分歧，需确认方向）

#### 用户确认

三部分结果合并展示，用户确认：
- 哪些完整性问题是真实问题（vs 误报）
- 哪些冲突需要处理
- 哪些竞品差距需要跟进

确认后写入文件。

---

## 输出文件变更

### 新增文件
```
.allforai/product-map/
├── competitor-profile.json    # Step 0 写草稿，Step 7 补全竞品功能数据
├── validation-report.json     # Step 7: 三合一校验结果（机器可读）
└── validation-report.md       # Step 7: 校验摘要（人类可读，问题优先展示）
```

### `validation-report.json` Schema

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
        "note": "差异化优势，建议保留"
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

### `validation-report.md` 结构（摘要级）

```
# 产品地图校验报告

校验问题 5 个（完整性 3 / 冲突 2） · 竞品差距：竞品有我没有 3 个 / 我有竞品没有 1 个 / 做法不同 2 个

## 完整性问题
- T001 THIN_AC：acceptance_criteria 只有 2 条
- T005 MISSING_EXCEPTIONS：exceptions 为空

## 冲突问题
- V001 CROSS_ROLE_CONFLICT（高）：T001 vs T007，退款金额修改规则矛盾

## 竞品差异
### 竞品有我们没有（潜在缺口）
- 批量退款（有赞）— 高频场景，建议评估

### 我们有竞品没有（差异化）
- 退款单幂等去重 — 差异化优势

### 做法不同（设计分歧）
- 审批流：我们固定两级 vs 有赞动态多级

> 完整数据见 .allforai/product-map/validation-report.json
```

### `product-map.json` summary 字段新增

```json
"summary": {
  "role_count": 3,
  "task_count": 24,
  "conflict_count": 1,
  "constraint_count": 5,
  "validation_issues": 5,
  "competitor_gaps": 3
}
```

---

## commands/product-map.md 改动

### 模式路由更新
- `full`：`Step 0 → 1 → 2 → 4 → 5 → 6 → 7`
- `quick`：`Step 0 → 1 → 2 → 6 → 7`
- Step 7 在所有模式下必须执行

### 报告摘要模板新增两行
```
| 校验问题 | X 个（完整性 X / 冲突 X） |
| 竞品差距 | 竞品有我没有 X 个 / 我有竞品没有 X 个 / 做法不同 X 个 |
```

---

## 版本说明

- 版本：v2.2.0 → v2.3.0
- Breaking change：`product-map.json` summary 新增两个字段（向后兼容，下游技能只读已有字段）
- 新增输出文件：`competitor-profile.json`、`validation-report.json`、`validation-report.md`
