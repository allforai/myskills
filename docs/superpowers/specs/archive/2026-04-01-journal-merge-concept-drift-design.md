# Journal Merge + Concept Drift Design

> When product decisions recorded in decision-journal.json conflict with product-concept.json, provide an explicit merge command with interactive conflict resolution, generate a concept drift manifest, and enable bootstrap incremental re-planning.

## Problem

During development, users make product decisions via `/journal` that may contradict the original product concept. Currently:

- `decision-journal.json` records decisions (append-only log)
- `product-concept.json` holds the official product definition
- Bootstrap Step 2.6 reads journal and says "journal wins on conflict"
- But Step 3.5 coverage check reads concept → may auto-add nodes for features the user already decided to remove
- concept-acceptance reads concept → verifies against stale baseline

The two files can drift apart with no explicit reconciliation mechanism.

## Solution

Three coordinated changes:

1. **`/journal` Step 5** — detect conflicts after recording, remind user to merge
2. **`/journal merge`** — new command: interactive conflict resolution → write concept → generate drift
3. **Bootstrap incremental re-planning** — read drift manifest, update only affected nodes

```
/journal → record decisions → detect conflicts → remind merge
    ↓
/journal merge → resolve conflicts → update concept → generate drift
    ↓ user decides when
/bootstrap → read drift → incremental re-plan → /run continues
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Conflict resolution timing | At `/journal merge`, not at `/journal` | Journal is a log; merge is the explicit action |
| Conflict resolution mode | Interactive (user decides per conflict) | User said: journal is manual trigger, interaction is expected |
| Concept modification | Only via `/journal merge`, not auto | Explicit is better; journal stays append-only for audit |
| Drift manifest | Separate file, not inline in concept | Enables bootstrap to detect "what changed" without diffing |
| Re-planning scope | Incremental (keep unaffected nodes) | Full re-bootstrap wastes completed work |

---

## Part 1: `/journal` Step 5 — Conflict Detection

### Current Step 5 (Remind about Concept Sync)

Currently shows a generic reminder about files that might need updating. Replace with specific conflict detection.

### New Step 5: Conflict Detection

After writing decisions to journal (Step 3) and confirming with user (Step 4):

1. Read `product-concept.json` (if exists; if not, skip)
2. For each decision just recorded, check if it contradicts the concept:
   - Decision says "remove feature X" → is X in concept's features/must_have/differentiators?
   - Decision says "change tech to Y" → does concept's roles[].client_type disagree?
   - Decision says "add feature Z" → is Z in concept's eliminate list?
3. If conflicts found, display:

```
⚠️ 检测到 {N} 条决策与 product-concept.json 冲突：

  1. journal: 删除「医生在线咨询」
     concept: 在 differentiators 中

  2. journal: 技术栈改为 SwiftUI
     concept: roles[R1].client_type = flutter-mobile

运行 /journal merge 解决冲突并更新产品定义。
```

4. If no conflicts: show existing Step 5 behavior (generic reminder for non-conflicting changes that may need attention).

---

## Part 2: `/journal merge` Command

### Command Definition

New file: `claude/meta-skill/commands/journal-merge.md`

Arguments: none (reads journal + concept automatically)

### Step 1: Load Files

Read:
- `.allforai/product-concept/decision-journal.json`
- `.allforai/product-concept/product-concept.json`

If either file doesn't exist, report and exit.

### Step 2: Identify Unmerged Decisions

Find journal batches that haven't been merged yet. Track merge state via a `last_merged_batch` field in concept-drift.json (or absence of drift file = nothing merged).

For each unmerged decision, classify:
- **Conflict**: decision contradicts current concept content
- **Addition**: decision adds something not in concept (no conflict)
- **No-op**: decision aligns with concept (already consistent)

### Step 3: Interactive Conflict Resolution

For each conflict, present options using AskUserQuestion:

```
冲突 {i}/{total}:

  journal ({batch_date}): {decision.question} → {decision.chosen}
  concept: {current concept value}

选择：
  a) 接受 journal 决策 → 更新 concept
  b) 保留 concept 原值 → 忽略此条决策
  c) 自定义 → 输入新值（折中方案）
```

Record each resolution.

For additions (no conflict): auto-accept, show in summary.
For no-ops: skip silently.

### Step 4: Write Back to product-concept.json

Apply all accepted changes to concept. Each modified field gets a `_journal_override` marker in a sidecar tracking file (not in concept itself, to keep concept clean):

Write `.allforai/product-concept/merge-audit.json`:

```json
{
  "merged_at": "<ISO timestamp>",
  "resolutions": [
    {
      "decision_batch": "<batch_id>",
      "question": "<what was decided>",
      "resolution": "accept_journal | keep_concept | custom",
      "before": "<old concept value>",
      "after": "<new concept value>"
    }
  ]
}
```

### Step 5: Generate concept-drift.json

Write `.allforai/product-concept/concept-drift.json`:

```json
{
  "drifted_at": "<ISO timestamp>",
  "source_batches": ["<journal batch IDs that caused changes>"],
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

Impact classification rules:
- `feature_removed` → impacts: product-map, experience-map, workflow, code
- `feature_added` → impacts: product-map, experience-map, workflow
- `feature_modified` → impacts: depends on what changed (name only → product-map; behavior → all)
- `role_removed` → impacts: product-map, experience-map, workflow, code
- `tech_changed` → impacts: workflow, code (product-map unaffected)

### Step 6: Display Impact Report

```
✅ 合并完成。已更新 product-concept.json。

变更摘要：
  - 移除功能: 医生在线咨询
  - 移除角色: R2 宠物医生
  - 保留功能: 社区帖子（用户选择保留）

影响分析：
  ✗ product-map/role-profiles.json — R2 角色需删除
  ✗ product-map/task-inventory.json — 咨询相关任务需删除
  ✗ experience-map/experience-map.json — 咨询相关屏幕需删除
  ✗ workflow.json — 相关节点需重新规划
  ✗ 已实现代码 — WebSocket 咨询代码需清理

  ✓ 商品/购物车/订单 — 不受影响
  ✓ 健康档案 — 不受影响

已写入 concept-drift.json。
下一步：运行 /bootstrap 重新规划工作流（仅受影响部分）。
```

---

## Part 3: Bootstrap Incremental Re-Planning

### Step 1.0: Detect concept-drift

Add to existing state detection:

```
- `has_concept_drift`: true if product-concept/concept-drift.json exists AND resolved == false
```

### Step 3: Incremental Planning (when drift exists)

When `has_concept_drift` is true AND an existing `workflow.json` exists:

1. Read concept-drift.json changes[]
2. Read existing workflow.json nodes[] + transition_log[]
3. For each change, determine affected nodes:

| Change Type | Node Action |
|-------------|-------------|
| feature_removed | Remove nodes whose goal is primarily about this feature. Add a "cleanup-{feature}" node if code already exists. |
| feature_added | Add new implementation + verification nodes for the feature. |
| feature_modified | Update affected nodes' goal + regenerate their node-specs. |
| role_removed | Remove role-specific nodes (e.g., e2e-test for that role's app). Update shared nodes to exclude this role. |
| tech_changed | Replace implementation + compile-verify + e2e nodes for the affected module. |

4. Preserve unaffected nodes and their transition_log entries (completed work is not lost).
5. Write updated workflow.json + regenerate affected node-specs.
6. Run Step 3.5 coverage self-check on the updated workflow (concept has changed, coverage must be re-verified).
7. Mark drift as `resolved: true`.

### Transition Log Preservation

When re-planning, transition_log entries for unaffected nodes are preserved. For affected nodes:
- Node removed → transition_log entry stays (audit trail) but node no longer in nodes[]
- Node modified → transition_log entry cleared (needs re-execution)
- Node added → no transition_log entry yet

---

## Change Scope

| File | Change |
|------|--------|
| `claude/meta-skill/commands/journal.md` | Rewrite Step 5: conflict detection + merge reminder |
| `claude/meta-skill/commands/journal-merge.md` | **New file**: interactive merge command |
| `claude/meta-skill/skills/bootstrap.md` | Step 1.0: add `has_concept_drift`. Step 3: add incremental re-planning when drift exists. |

Three files: one modified, one new, one modified.
