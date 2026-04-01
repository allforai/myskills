---
name: journal-merge
description: 将 decision-journal 中的决策合并到 product-concept.json，交互式解决冲突，生成 concept-drift.json 供 /bootstrap 增量重规划。
allowed-tools: ["Read", "Write", "Edit", "Bash", "AskUserQuestion"]
---

# Journal Merge

合并 decision-journal.json 的决策到 product-concept.json，解决冲突，生成变更清单。

## Step 1: Load Files

Read:
- `.allforai/product-concept/decision-journal.json`
- `.allforai/product-concept/product-concept.json`
- `.allforai/product-concept/concept-drift.json` (if exists, for last_merged_batch tracking)

If journal doesn't exist → report "没有 decision-journal.json，请先运行 /journal 记录决策。" and stop.
If concept doesn't exist → report "没有 product-concept.json，请先运行产品概念阶段。" and stop.

## Step 2: Identify Unmerged Decisions

Determine which journal batches are unmerged:
- If concept-drift.json exists and has `last_merged_batch` → batches after that timestamp are unmerged
- If no drift file → all batches are unmerged

For each unmerged decision, classify:
- **Conflict**: decision contradicts current concept content
- **Addition**: decision adds something not in concept (new feature, new constraint)
- **No-op**: decision aligns with concept (already consistent)

If no unmerged decisions → report "所有决策已合并，无需操作。" and stop.

## Step 3: Interactive Conflict Resolution

For each **conflict**, use AskUserQuestion:

```
冲突 {i}/{total}:

  journal ({batch_date}): {decision.question} → {decision.chosen}
  理由: {decision.rationale}

  concept 当前值: {current concept value and location}
```

Options:
- **接受 journal 决策** — 更新 concept 为 journal 的值
- **保留 concept 原值** — 忽略此条 journal 决策
- **自定义** — 提供 "其他" 输入框让用户输入折中方案

For **additions**: auto-accept, include in summary.
For **no-ops**: skip silently.

Record each resolution with before/after values.

## Step 4: Update product-concept.json

Apply all accepted changes to concept. Types of updates:

| Decision Type | Concept Update |
|---------------|----------------|
| Feature removed | Remove from `features[]`. If in `must_have[]`/`differentiators[]`, remove there too. Add to `errc_highlights.eliminate[]`. |
| Feature added | Add to `features[]`. Remove from `eliminate[]` if present. |
| Feature modified | Update the feature description in `features[]`. |
| Role removed | Remove from `roles[]`. |
| Role added | Add to `roles[]`. |
| Tech changed | Update `roles[].client_type` or relevant tech field. |

Write the updated `product-concept.json`.

## Step 5: Write Audit Trail

Write `.allforai/product-concept/merge-audit.json`:

If file exists, append to `merges[]` array. If not, create it.

```json
{
  "schema_version": "1.0",
  "merges": [
    {
      "merged_at": "<ISO timestamp>",
      "batches_merged": ["<batch_id_1>", "<batch_id_2>"],
      "resolutions": [
        {
          "decision_batch": "<batch_id>",
          "question": "<what was decided>",
          "resolution": "accept_journal | keep_concept | custom",
          "custom_value": "<only if resolution=custom>",
          "before": "<old concept value>",
          "after": "<new concept value>"
        }
      ]
    }
  ]
}
```

## Step 6: Generate concept-drift.json

Write `.allforai/product-concept/concept-drift.json`:

```json
{
  "schema_version": "1.0",
  "drifted_at": "<ISO timestamp>",
  "last_merged_batch": "<latest merged batch_id>",
  "source_batches": ["<batch IDs that caused changes>"],
  "changes": [
    {
      "type": "feature_removed | feature_added | feature_modified | role_removed | role_added | tech_changed | client_removed | client_added | module_merged | module_split",
      "target": "<what changed>",
      "before": "<old value>",
      "after": "<new value>",
      "impact": ["product-map", "experience-map", "workflow", "code"]
    }
  ],
  "resolved": false
}
```

Impact classification:
- `feature_removed` → `["product-map", "experience-map", "workflow", "code"]`
- `feature_added` → `["product-map", "experience-map", "workflow"]`
- `feature_modified` → depends on scope (name change: `["product-map"]`; behavior change: all)
- `role_removed` → `["product-map", "experience-map", "workflow", "code"]`
- `role_added` → `["product-map", "experience-map", "workflow"]`
- `tech_changed` → `["workflow", "code"]`
- `client_removed` → `["workflow", "code"]` (remove impl + compile + e2e nodes for that client)
- `client_added` → `["workflow"]` (add impl + compile + e2e nodes for new client)
- `module_merged` → `["workflow", "code"]` (remove merged service nodes, extend target service)
- `module_split` → `["workflow", "code"]` (create new service nodes, reduce source service scope)

If concept-drift.json already exists with `resolved: false` (previous unresolved drift),
merge new changes into the existing changes[] array (don't overwrite).

## Step 7: Display Impact Report

```
✅ 合并完成。已更新 product-concept.json。

变更摘要：
  {for each accepted change:}
  - {type_label}: {target}

影响分析：
  {for each unique impacted artifact:}
  ✗ {artifact} — {why it's affected}

  {for each unaffected major area:}
  ✓ {area} — 不受影响

已写入：
  - product-concept.json（已更新）
  - merge-audit.json（审计记录）
  - concept-drift.json（变更清单）

下一步：运行 /bootstrap 重新规划工作流（仅受影响部分）。
```
