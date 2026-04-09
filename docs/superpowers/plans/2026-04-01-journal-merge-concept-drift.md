# Journal Merge + Concept Drift Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable explicit journal-to-concept merge with interactive conflict resolution, concept drift tracking, and bootstrap incremental re-planning.

**Architecture:** Three markdown file changes: rewrite journal Step 5 for conflict detection, create journal-merge command, add drift detection + incremental planning to bootstrap. All pure markdown — no scripts, no code.

**Tech Stack:** Markdown skill/command files

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `claude/meta-skill/commands/journal.md` | Modify | Rewrite Step 5: conflict detection + merge reminder |
| `claude/meta-skill/commands/journal-merge.md` | Create | Interactive merge command: resolve conflicts → update concept → generate drift |
| `claude/meta-skill/skills/bootstrap.md` | Modify | Step 1.0: detect drift. Step 3: incremental re-planning when drift exists. |

---

### Task 1: Rewrite journal.md Step 5 for conflict detection

**Files:**
- Modify: `claude/meta-skill/commands/journal.md:83-94`

- [ ] **Step 1: Replace Step 5 content**

Find the existing Step 5 section (lines 83-94) that starts with "### Step 5: Remind about Concept Sync" and replace the entire section with:

```markdown
### Step 5: Conflict Detection

After recording decisions, check for conflicts with the current product concept.

1. Read `.allforai/product-concept/product-concept.json` (if not found, skip to Step 5.3)
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
```

- [ ] **Step 2: Read back the modified file to verify**

Read `claude/meta-skill/commands/journal.md` lines 83 onward and confirm Step 5 is replaced correctly and the file ends properly.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/commands/journal.md
git commit -m "feat(meta-skill): journal Step 5 detects conflicts with product-concept"
```

---

### Task 2: Create journal-merge.md command

**Files:**
- Create: `claude/meta-skill/commands/journal-merge.md`

- [ ] **Step 1: Write the command file**

Create `claude/meta-skill/commands/journal-merge.md` with this exact content:

```markdown
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

选择：
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
      "type": "feature_removed | feature_added | feature_modified | role_removed | role_added | tech_changed",
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
```

- [ ] **Step 2: Read back the file to verify it's well-formed**

Read `claude/meta-skill/commands/journal-merge.md` and confirm all sections are present, AskUserQuestion pattern is correct, and JSON examples are valid.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/commands/journal-merge.md
git commit -m "feat(meta-skill): add /journal-merge command for interactive concept reconciliation"
```

---

### Task 3: Add concept-drift detection to bootstrap Step 1.0

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:43`

- [ ] **Step 1: Add has_concept_drift detection**

Find the line `- `has_decision_journal`: true if product-concept/decision-journal.json exists` (line 43). Add after it:

```markdown
- `has_concept_drift`: true if product-concept/concept-drift.json exists AND its `resolved` field is false
```

- [ ] **Step 2: Add drift routing to Step 1.5 context**

Find the bullet list under "This affects Step 1.5 options:" (around line 45-48). Add:

```markdown
- has_concept_drift → Step 3 uses incremental re-planning instead of full planning
```

- [ ] **Step 3: Verify the changes read correctly**

Read bootstrap.md lines 36-50 and confirm the new lines integrate naturally.

- [ ] **Step 4: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): detect concept-drift in bootstrap Step 1.0"
```

---

### Task 4: Add incremental re-planning to bootstrap Step 3

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md:369-375`

- [ ] **Step 1: Insert incremental planning section**

Find "## Step 3: Plan Workflow (LLM Free Planning)" (line 369). After the blockquote (lines 371-373) and before "### 3.1 Design the Node Graph" (line 375), insert:

```markdown
### 3.0 Incremental Re-Planning (when concept-drift exists)

> This section only applies when `has_concept_drift` is true AND an existing
> `workflow.json` exists. Otherwise, skip to 3.1 for full planning.

When concept has drifted since last bootstrap:

1. Read `.allforai/product-concept/concept-drift.json` → changes[]
2. Read existing `.allforai/bootstrap/workflow.json` → nodes[] + transition_log[]
3. For each change, determine affected nodes:

| Change Type | Node Action |
|-------------|-------------|
| feature_removed | Remove nodes whose goal is primarily about this feature. Add a `cleanup-{feature}` node if code already exists (detected from transition_log). |
| feature_added | Add new implementation + verification nodes for the feature. |
| feature_modified | Update affected nodes' goal and regenerate their node-specs. |
| role_removed | Remove role-specific nodes (e.g., e2e-test for that role's app). Update shared nodes to exclude this role. |
| tech_changed | Replace implementation + compile-verify + e2e nodes for the affected module with new tech stack equivalents. |

4. **Preserve unaffected nodes**: nodes whose goal does not relate to any drift change
   remain in workflow.json with their transition_log entries intact. Completed work is not lost.

5. **Handle affected completed nodes**:
   - Node removed → transition_log entry stays for audit, but node removed from nodes[]
   - Node goal modified → clear its transition_log entry (needs re-execution)
   - New node added → no transition_log entry yet

6. Write updated workflow.json with modified nodes[] and preserved transition_log[].
7. Regenerate node-specs for all affected nodes at `.allforai/bootstrap/node-specs/`.
8. Proceed to Step 3.5 (Coverage Self-Check) — concept has changed, coverage must be re-verified.
9. After Step 3.5 completes, mark drift as resolved:
   read concept-drift.json, set `"resolved": true`, write back.

**After incremental re-planning, skip 3.1-3.3** (they are for full planning) and go directly
to Step 3.4 (Confirm with User) → Step 3.5 (Coverage Self-Check) → Step 4.
```

- [ ] **Step 2: Verify insertion position**

Read bootstrap.md around lines 369-380 and confirm 3.0 is between the Step 3 header and 3.1.

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(meta-skill): add incremental re-planning to bootstrap Step 3 for concept drift"
```

---

### Task 5: Final verification

**Files:**
- Read: `claude/meta-skill/commands/journal.md` (Step 5)
- Read: `claude/meta-skill/commands/journal-merge.md` (full file)
- Read: `claude/meta-skill/skills/bootstrap.md` (Step 1.0, Step 3.0)

- [ ] **Step 1: Verify journal.md Step 5**

Read journal.md and confirm:
- Step 5 is now "Conflict Detection" ✓
- Checks features, tech, roles against concept ✓
- Displays conflicts with merge reminder ✓

- [ ] **Step 2: Verify journal-merge.md**

Read journal-merge.md and confirm:
- 7 steps: load → identify → resolve → update concept → audit → drift → report ✓
- AskUserQuestion with 3 options per conflict ✓
- concept-drift.json schema has `resolved`, `last_merged_batch`, `changes[]` ✓
- Impact classification table complete ✓

- [ ] **Step 3: Verify bootstrap.md Step 1.0 + Step 3.0**

Read bootstrap.md and confirm:
- `has_concept_drift` detected in Step 1.0 ✓
- Step 3.0 exists before Step 3.1 ✓
- Incremental re-planning handles all 5 change types ✓
- Preserves unaffected nodes + transition_log ✓
- Marks drift resolved after completion ✓
- Skips 3.1-3.3 after incremental planning ✓

- [ ] **Step 4: Cross-check with spec**

Read `docs/superpowers/specs/2026-04-01-journal-merge-concept-drift-design.md` and verify every spec requirement has a corresponding task.
