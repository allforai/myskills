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

### Step 5: Conflict Detection

After recording decisions, check for conflicts with the current product concept.

1. Read `.allforai/product-concept/product-concept.json` (if not found, skip to step 4 below)
2. For each decision just recorded, check if it contradicts the concept:
   - Decision removes a feature → is it in concept's `features[]`, `must_have[]`, or `differentiators[]`?
   - Decision changes tech stack → does concept's `roles[].client_type` disagree?
   - Decision adds a feature → is it in concept's `errc_highlights.eliminate[]`?
   - Decision removes a role → is the role in concept's `roles[]`?

3. **If conflicts found**, display:

```
⚠️ 检测到 {N} 条决策与 product-concept.json 冲突：

  {for each conflict:}
  {i}. journal: {decision.chosen}
     concept: {current concept value and location}

运行 /journal merge 解决冲突并更新产品定义。
```

4. **If no conflicts**, display:

```
✅ 所有决策与 product-concept.json 一致，无需合并。
如有其他产品定义需要更新，运行 /journal merge。
```
