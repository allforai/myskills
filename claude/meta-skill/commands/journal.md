---
name: journal
description: 记录本轮对话中的产品决策、用户选择和设计变更到 decision-journal.json。每次调用生成一个新批次。
arguments:
  - name: topic
    description: 本批次主题（如 "iOS 改进"、"学习状态机"）
    required: false
---

# Product Decision Journal

You are collecting product decisions made during this conversation session.

## Protocol

### Step 1: Scan Conversation Context

Review the current conversation to identify product-level decisions. Look for:

- **User choices**: when user selected from options you presented (naming, tech stack, features to include/exclude)
- **Design changes**: when user corrected or redirected your approach (e.g., "not local storage, use server-side data")
- **Feature removals**: when user decided to remove or defer a feature
- **Architecture changes**: when user changed tech direction (e.g., "delete Flutter, use native")
- **Behavior specifications**: when user clarified how something should work (e.g., "Coco should not be deletable... actually allow delete for testing")

Do NOT record:
- Implementation details (which file, which function)
- Bug fixes
- Temporary debugging decisions
- Things already in the product-map or spec files

### Step 2: Summarize Decisions

For each decision found, record:
- `question`: what was being decided
- `chosen`: what the user chose
- `rationale`: why (if stated or implied)
- `supersedes` (optional): if this overrides a previous decision, reference it

### Step 3: Write to Journal

File: `.allforai/product-concept/decision-journal.json`

If file exists, read it and append a new batch. If not, create it.

```json
{
  "schema_version": "1.0",
  "batches": [
    {
      "batch_id": "<ISO timestamp>",
      "source": "user_session",
      "topic": "<topic from argument, or auto-detected>",
      "decisions": [
        {
          "question": "...",
          "chosen": "...",
          "rationale": "...",
          "supersedes": null
        }
      ]
    }
  ]
}
```

### Step 4: Confirm with User

Present the recorded decisions as a summary:

```
📋 已记录 N 条产品决策：

批次：{topic} ({timestamp})

  1. {question} → {chosen}
  2. {question} → {chosen}
  ...

已写入 .allforai/product-concept/decision-journal.json
```

### Step 5: Remind about Concept Sync

If decisions significantly change the product direction (tech stack change, core feature rename, feature removal), remind:

```
⚠️ 以下决策可能需要同步更新产品定义：
  - product-map/role-profiles.json (角色名称变更)
  - product-map/task-inventory.json (功能增删)
  - bootstrap-profile.json (技术栈变更)

建议在下次 /bootstrap 前更新这些文件，或让 /bootstrap 自动检测差异。
```
