# Step 3: 竞品参考（可选）

> 看看同行在同阶段做了什么、没做什么，给剪枝决策提供外部参照。

---

## 1. 触发条件

| 模式 | 行为 |
|------|------|
| `quick` | 跳过此步骤 |
| `full` | 询问用户产品类型关键词后执行 |
| `scope` | 询问用户产品类型关键词后执行 |

用户可随时说"跳过竞品分析"，立即跳过此步骤进入下一阶段。

---

## 2. 搜索策略

用户提供产品类型关键词（例如："项目管理工具"、"跨境电商 SaaS"、"在线教育平台"）。

执行 3 次 WebSearch 搜索：

| 搜索序号 | 查询模板 | 目的 |
|---------|---------|------|
| 1 | `"{keyword} features"` 或 `"{keyword} 功能列表"` | 查找功能页面 |
| 2 | `"{keyword} pricing plans"` | 定价页面通常按层级列出功能 |
| 3 | `"{keyword} alternatives comparison"` | 对比类文章 |

目标：识别 3–5 个竞品。

关注点：从定价页/功能页提取功能列表，**不需要**深入了解实现细节。

---

## 3. 提取规则

对每个竞品，通过 WebFetch 提取：

- **name** — 竞品名称
- **url** — 功能页或定价页 URL
- **feature list** — 以 bullet points 形式列出功能
- **pricing tier info** — 哪些功能属于哪个定价层级

提取后执行：

1. 将竞品功能与本地功能列表按关键词匹配（keyword matching）
2. 生成 `coverage_matrix`（覆盖矩阵）

---

## 4. 对照分析

| 对照结果 | 信号 | 行动 |
|---------|------|------|
| 本项目有 + 竞品 0/N 有 | 强化 CUT/DEFER | 更新 assessment 中的分类 |
| 本项目有 + 竞品 ≥50% 有 | 弱化 CUT | 如果之前是 CUT，考虑改为 DEFER |
| 本项目没有 + 竞品有 | 仅标注 | **绝不建议添加**（只剪不加铁律）|

核心原则：竞品参考只用于调整剪枝强度，**永远不会导致新功能建议。**

---

## 5. 用户确认点

对照分析完成后：

1. 向用户呈现竞品对照矩阵表
2. 询问：**"以上竞品参考是否采纳？是否需要调整之前的分类？"**

用户可以：
- 采纳全部竞品信号
- 部分采纳（逐条确认）
- 完全拒绝竞品信号（`confirmed_by_user: false`）

---

## 6. 输出格式

输出文件：`benchmark.json`

```json
{
  "product_type": "项目管理工具",
  "competitors": [
    {
      "name": "Competitor A",
      "url": "https://example.com/features",
      "features": ["任务管理", "看板视图", "甘特图", "团队协作"]
    }
  ],
  "coverage_matrix": [
    {
      "feature_id": "F-015",
      "feature_name": "数据可视化大屏",
      "competitor_coverage": 0,
      "competitors_total": 4,
      "signal": "strengthen_cut",
      "note": "竞品在同阶段普遍不包含此功能"
    }
  ],
  "only_in_competitors": [
    {
      "feature_name": "甘特图",
      "coverage": 3,
      "note": "仅标注，不建议添加"
    }
  ],
  "confirmed_by_user": false
}
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| `product_type` | string | 用户提供的产品类型关键词 |
| `competitors` | array | 识别到的竞品列表，含名称、URL、功能列表 |
| `coverage_matrix` | array | 本项目功能在竞品中的覆盖情况 |
| `coverage_matrix[].signal` | enum | `strengthen_cut` / `weaken_cut` |
| `only_in_competitors` | array | 仅竞品有而本项目没有的功能（仅标注） |
| `confirmed_by_user` | boolean | 用户是否采纳了竞品参考结果 |

---

## 7. 铁律提醒 — 只剪不加

竞品中有而本项目没有的功能（`only_in_competitors`）：

- **仅标注**，记录到输出中供参考
- **绝不建议添加**为本项目功能
- 这是一条硬规则（hard rule），不受任何条件影响

竞品参考的唯一作用是：为已有功能的剪枝决策提供外部校准。

---

> **铁律速查** — 本步骤强相关：**只剪不加**（竞品有的功能绝不建议添加）、**用户权威**（竞品信号由用户决定是否采纳）。
