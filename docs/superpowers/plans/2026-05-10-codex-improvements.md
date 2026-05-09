# Codex Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 7 architectural improvements to the meta-skill plugin, hardening the workflow contract, parallelization semantics, and asset lifecycle tracking.

**Architecture:** All changes are documentation/markdown edits to skill files and capability files — no compiled code. Each task is independent and can be reviewed in isolation. Verification is grep-based (checking that specific patterns exist in the modified files).

**Tech Stack:** Markdown, JSON schema documentation, meta-skill plugin structure at `/Users/aa/workspace/myskills/claude/meta-skill/`

---

## File Structure

| Action | Path | Responsible for |
|--------|------|----------------|
| Create | `knowledge/capabilities/concept-contract.md` | Concept freeze capability — canonical_registry, asset ID authority |
| Create | `knowledge/capabilities/app-design.md` | App-specific design phases (non-game) |
| Modify | `skills/bootstrap.md` | workflow.json schema: hard_blocked_by, alignment_refs, validation_commands, concept-freeze injection |
| Modify | `knowledge/orchestrator-template.md` | Orchestrator loop: honor hard_blocked_by vs alignment_refs |
| Modify | `knowledge/capabilities/game-design.md` | current_state: add `locked`; node frontmatter: add review_checklist |
| Modify | `knowledge/domains/art-methodology.md` | Asset lifecycle: document locked state semantics |

---

## Task 1: Concept Contract Capability (#1)

Creates the `concept-freeze` node capability and inserts its injection rule into bootstrap, solving the naming-mismatch problem by locking asset IDs and file prefixes before execution nodes run.

**Files:**
- Create: `knowledge/capabilities/concept-contract.md`
- Modify: `skills/bootstrap.md` (add injection rule after art-spec-design, ~line 920)

- [ ] **Step 1: Write the capability file**

Create `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/concept-contract.md` with this exact content:

```markdown
# Concept Contract Capability

> Node: `concept-freeze`. Runs after all concept-phase human gates are approved.
> Captures all approved creative decisions into a canonical source of truth with
> a `canonical_registry` that maps every asset ID to a definitive file prefix.
>
> **Why this exists:** Execution nodes (art-gen, tile-gen, etc.) independently
> invent asset file names, causing naming mismatches (npc_ahai vs npc_kenzo).
> The canonical_registry is the single authoritative ID→filename mapping that
> all downstream nodes must follow.

## Goal

Emit `.allforai/concept-contract.json` — a frozen, version-stamped snapshot of
all approved concept-phase decisions, with a `canonical_registry` derived from
`art-asset-inventory.json`.

## Inputs

| File | Required fields |
|------|----------------|
| `.allforai/product-concept/product-concept.json` | `genre`, `target_platform`, `core_loop` |
| `.allforai/game-design/art-style-guide.json` | `art_overview` |
| `.allforai/game-design/art-pipeline-config.json` | `dimension`, `style`, `active_nodes` |
| `.allforai/game-design/art-asset-inventory.json` | `assets[].asset_id`, `assets[].type`, `assets[].name` |
| `.allforai/game-design/approval-records.json` | all records with `gate_status` |

If `art-asset-inventory.json` is missing → report UPSTREAM_DEFECT and halt.
If any human_gate node has `gate_status != "approved"` → halt with error listing unapproved gates.

## Output

`.allforai/concept-contract.json`

## Protocol

### Step 1: Validate all gates approved

Read `.allforai/game-design/approval-records.json`. Every record must have
`gate_status == "approved"`. Collect any non-approved records and report them.
If any exist → halt. Do not produce the contract until all gates pass.

### Step 2: Build canonical_registry

Read `art-asset-inventory.json.assets[]`. For each asset:
- `asset_id` is the canonical slug (never invent a new one)
- Derive `file_prefix` by convention:
  - type=`character` → `npc_{asset_id}`
  - type=`tile` → `t_{asset_id}`
  - type=`environment` → `env_{asset_id}`
  - type=`ui` → `ui_{asset_id}`
  - type=`vfx` → `vfx_{asset_id}`
  - type=`icon` → `ico_{asset_id}`
  - type=`audio-cover` → `aud_{asset_id}`
  - other → `{asset_id}` (no prefix)
- Group into `characters[]`, `tiles[]`, `environments[]`, `ui[]`, `vfx[]`, `other[]`

### Step 3: Write concept-contract.json

Stamp with `frozen_at` (ISO timestamp) and `schema_version: "1.0"`.

## Output Schema

```json
{
  "schema_version": "1.0",
  "frozen_at": "<ISO timestamp>",
  "project": {
    "genre": "<from product-concept.json>",
    "target_platform": "<from product-concept.json>",
    "dimension": "<2d | 3d | 2.5d>",
    "style": "<cartoon | pixel | realistic | hand_drawn | vector>",
    "animation_system": "<frame | dragonbones | 3d_skeletal | mixed>"
  },
  "canonical_registry": {
    "characters": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "npc_<slug>" }
    ],
    "tiles": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "t_<slug>" }
    ],
    "environments": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "env_<slug>" }
    ],
    "ui": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "ui_<slug>" }
    ],
    "vfx": [
      { "asset_id": "<slug>", "name": "<display name>", "file_prefix": "vfx_<slug>" }
    ],
    "other": []
  },
  "active_art_nodes": ["<node ids from art-pipeline-config.active_nodes>"],
  "human_gates_approved": ["<list of approved node ids from approval-records.json>"]
}
```

## Downstream Consumers

| Consumer node | Fields read | Purpose |
|---------------|------------|---------|
| All `*-art-gen` nodes | `canonical_registry.*` | Authoritative file_prefix for every generated asset |
| `art-spec-design` | `canonical_registry.*` | Use as cross-reference when building asset list |
| `art-qa` | `canonical_registry.*`, `active_art_nodes` | Completeness check — every registry entry must have coverage |
| Code generation nodes | `canonical_registry.*` | Asset Registry (ID → path) must reference these prefixes |

## Completion Check

`.allforai/concept-contract.json` exists AND `schema_version == "1.0"`.
```

- [ ] **Step 2: Verify the file was written**

```bash
grep -c "canonical_registry" /Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/concept-contract.md
grep "schema_version" /Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/concept-contract.md
```

Expected: count ≥ 3 (canonical_registry appears in multiple places), schema_version appears in the schema.

- [ ] **Step 3: Add concept-freeze injection rule to bootstrap.md**

In `skills/bootstrap.md`, find the block that ends with the art-concept injection (around line 919–920):

```
- **No approval-records entry** (art-concept is a skill invocation, not a human-reviewed document)
```

After the art-concept injection block (after the closing ` ``` ` of the node-spec content and the `5. Initialise...` line), insert this new block:

```markdown
**Concept Freeze Node Injection (applies when art-spec-design is in the selected workflow):**

After inserting `art-spec-design`, also insert a `concept-freeze` node immediately following it:
- `node_id: "concept-freeze"`, `capability: "concept-contract"`, `human_gate: false`
- `hard_blocked_by: ["art-spec-design"]`; update all art-gen nodes (`ai-art-generation`, `tile-art-gen`, `character-art-gen`, `environment-art-gen`, `vfx-art-gen`, etc.) to `hard_blocked_by: ["concept-freeze"]` (remove `art-spec-design` from their hard_blocked_by)
- `unlocks`: all art-gen nodes
- **Node-spec content** (write verbatim to `.allforai/bootstrap/node-specs/concept-freeze.md`):

```markdown
---
node: concept-freeze
human_gate: false
hard_blocked_by: [art-spec-design]
exit_artifacts:
  - .allforai/concept-contract.json
---

# Task: 概念合约冻结（Concept Freeze）

## 执行方法

读取并执行 `${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/concept-contract.md` capability。

该节点完成以下工作：
1. 验证所有 human_gate 节点均已 approved（approval-records.json）
2. 从 art-asset-inventory.json 构建 canonical_registry（ID→文件前缀映射）
3. 写入 `.allforai/concept-contract.json`（schema_version=1.0）

## 完成条件

`.allforai/concept-contract.json` 存在且 `schema_version == "1.0"`。

## 重要说明

所有后续 art-gen 节点必须从 concept-contract.json 读取 canonical_registry，
使用其中的 file_prefix 作为生成文件的命名权威来源，不得自行命名。
\```
```

- [ ] **Step 4: Verify the injection rule was added**

```bash
grep -n "concept-freeze\|concept-contract\|canonical_registry" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -10
```

Expected: at least 3 matches including `concept-freeze`, `concept-contract`, and `canonical_registry`.

- [ ] **Step 5: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/knowledge/capabilities/concept-contract.md claude/meta-skill/skills/bootstrap.md
git commit -m "feat: add concept-contract capability and concept-freeze node injection

Adds canonical_registry to prevent asset naming mismatches between
concept and execution phases. concept-freeze node runs after art-spec-design
and before all art-gen nodes."
```

---

## Task 2: App Design Capability (#2)

Creates `knowledge/capabilities/app-design.md` — the non-game equivalent of `game-design.md`, covering app-specific design phases (information architecture, user flows, interaction design) for non-game products.

**Files:**
- Create: `knowledge/capabilities/app-design.md`

- [ ] **Step 1: Write the capability file**

Create `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/app-design.md` with this content:

```markdown
# App Design Capability

> Covers the design phase for non-game app products. Parallel to `game-design.md`
> but tailored for SaaS, consumer apps, tools, and e-commerce products.
> Each node in this capability has `human_gate: true` and requires `discipline_owner` approval.

## Canonical Node Registry

Bootstrap uses this registry when `business_domain != "gaming"` and the goal includes design phases.

| Node ID | Discipline Owner | HTML Output | JSON Output | Blocked By |
|---------|-----------------|-------------|-------------|------------|
| `ia-design` | `lead-ux` | `app-design/ia-design.html` | `app-design/ia-design.json` | _(none — first node)_ |
| `user-flow-design` | `lead-ux` | `app-design/user-flow-design.html` | `app-design/user-flow-design.json` | `ia-design` |
| `interaction-design` | `lead-ux` | `app-design/interaction-design.html` | `app-design/interaction-design.json` | `user-flow-design` |
| `content-design` | `lead-content` | `app-design/content-design.html` | `app-design/content-design.json` | `ia-design` |
| `data-model-design` | `lead-engineer` | `app-design/data-model-design.html` | `app-design/data-model-design.json` | `ia-design` |
| `app-design-finalize` | `lead-pm` | `app-design/app-design-doc.html` | `app-design/app-design-doc.json` | ALL above |

**Required nodes (always included):** `ia-design`, `user-flow-design`, `interaction-design`, `app-design-finalize`

**Optional nodes:** `content-design` (content-heavy apps), `data-model-design` (data-intensive apps)

## Node Descriptions

### ia-design — Information Architecture

Goal: Define the app's structure — screens, navigation model, content hierarchy.

Inputs: `product-concept.json.must_have`, `product-concept.json.differentiators`

Output JSON schema:
```json
{
  "nav_model": "<tab | drawer | stack | hybrid>",
  "screens": [
    {
      "screen_id": "<slug>",
      "name": "<display name>",
      "purpose": "<one sentence>",
      "entry_points": ["<screen_id>"]
    }
  ],
  "primary_flows": ["<flow name>"]
}
```

HTML presentation: Screen map diagram + navigation model rationale.

### user-flow-design — User Flows

Goal: Map the step-by-step paths users take to complete core tasks.

Inputs: `ia-design.json.screens[]`, `product-concept.json.core_loop`

Output JSON schema:
```json
{
  "flows": [
    {
      "flow_id": "<slug>",
      "name": "<display name>",
      "trigger": "<entry screen_id>",
      "steps": [
        { "step": 1, "screen": "<screen_id>", "action": "<user action>", "outcome": "<result>" }
      ],
      "happy_path_length": 0,
      "error_paths": ["<description>"]
    }
  ]
}
```

HTML presentation: Flow diagrams per primary flow.

### interaction-design — Interaction Patterns

Goal: Define micro-interactions, states, and feedback patterns for key UI components.

Output JSON schema:
```json
{
  "components": [
    {
      "component_id": "<slug>",
      "name": "<display name>",
      "states": ["default", "hover", "active", "disabled", "loading", "error"],
      "feedback": "<how the component responds to user action>",
      "animation": "<none | subtle | prominent>"
    }
  ],
  "gesture_model": "<tap-only | swipe-primary | mixed>",
  "loading_strategy": "<skeleton | spinner | progressive>"
}
```

### app-design-finalize — Aggregation

Goal: Merge all approved design JSONs into `app-design-doc.json`.

Blocked by ALL other app-design nodes (same pattern as `game-design-finalize`).

Output: `app-design/app-design-doc.json` — merged document with all schemas nested under their node IDs.

## Human Gate Protocol

Identical to `game-design.md` human gate protocol:
- Approval tracked in `.allforai/app-design/approval-records.json`
- Same gate_status lifecycle: `pending → in-review → approved | revision-requested`
- discipline_owner approves; discipline_reviewers are advisory

## Downstream Consumers

| Consumer | From | Fields |
|----------|------|--------|
| `ui-design` | `ia-design.json` | Screen list, nav model |
| `ui-design` | `user-flow-design.json` | Flow steps → wireframe sequence |
| `product-verify` | `app-design-doc.json` | Expected screens and flows for QA |
| `concept-acceptance` | `app-design-doc.json` | Baseline for concept vs. implementation comparison |
```

- [ ] **Step 2: Verify the file was written**

```bash
grep -c "ia-design\|user-flow-design\|interaction-design" /Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/app-design.md
```

Expected: count ≥ 6 (each appears multiple times).

- [ ] **Step 3: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/knowledge/capabilities/app-design.md
git commit -m "feat: add app-design capability for non-game product design phases"
```

---

## Task 3: validation_commands in exit_artifacts (partial #3)

Adds `validation_commands` as an optional field on each exit_artifact entry in workflow.json, enabling bootstrap to emit machine-verifiable checks alongside file-existence checks. The orchestrator can run these commands as a secondary confirmation that files are well-formed, not just present.

**Files:**
- Modify: `skills/bootstrap.md` (workflow.json schema section, ~lines 1184–1218)

- [ ] **Step 1: Find the exit_artifacts schema section**

```bash
grep -n "exit_artifacts\|validation_command\|Node fields" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -20
```

Identify the line number of: `"exit_artifacts": ["<file paths that prove this node is done>"]`

- [ ] **Step 2: Update workflow.json schema in bootstrap.md**

In `skills/bootstrap.md`, find this exact block (around line 1184–1193):

```json
    {
      "id": "<project-specific name>",
      "capability": "<name of the capability this node is based on, e.g. discovery, product-analysis, translate>",
      "goal": "<one sentence: what this node achieves>",
      "exit_artifacts": ["<file paths that prove this node is done>"],
      "knowledge_refs": ["<which knowledge files this node should reference>"],
      "consumers": ["<node IDs that read this node's exit_artifacts>"],
      "blocked_by": ["<node IDs that must complete before this node can run; empty if no dependencies>"],
      "unlocks": ["<node IDs unblocked when this node completes>"],
      "human_gate": false,
      "discipline_owner": null
    }
```

Replace `"exit_artifacts": ["<file paths that prove this node is done>"]` with:

```json
      "exit_artifacts": [
        {
          "path": "<project-relative file path>",
          "validation_commands": []
        }
      ],
```

Then update the field description below the schema block. Find:

```
- `exit_artifacts`: File paths. Node is complete when these files exist.
```

Replace with:

```
- `exit_artifacts`: Array of artifact objects. Node is complete when all `path` files exist.
  Each entry has:
  - `path`: Project-relative file path. Node is complete when this file exists.
  - `validation_commands` (optional): Shell commands that must exit 0 after the file exists.
    Use for format checks beyond mere existence (e.g., `python3 -c "import json,sys; json.load(open('file.json'))"` for JSON validity,
    `grep -q '"status": "final"' file.json` for specific field checks).
    Empty array = existence check only. Bootstrap should populate these for JSON output files.
  
  **Shorthand:** Bootstrap may also use the string form `"<path>"` for artifacts with no
  validation_commands. check_artifacts.py accepts both forms.
```

- [ ] **Step 3: Update the exit_artifacts path convention section**

Find the section (around line 1220): `**exit_artifacts 路径规范（重要）：**`

After the last bullet point in that section, add:

```
- `validation_commands` 建议：对所有 JSON 输出文件，至少加入 JSON 合法性检查：
  `python3 -c "import json,sys; json.load(open('<path>'))"` 
  对有 `status` 字段的 JSON，加入：`grep -q '"status": "final"' <path>`
```

- [ ] **Step 4: Verify the changes**

```bash
grep -n "validation_commands\|validation command" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -10
```

Expected: at least 3 matches including in the schema template and in the description.

- [ ] **Step 5: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(#3): add validation_commands to exit_artifacts schema

Optional per-artifact shell commands that must exit 0 after file
existence is confirmed. Enables format validation beyond mere
file presence check."
```

---

## Task 4: hard_blocked_by + alignment_refs (#4)

Splits `blocked_by` into two semantic fields:
- `hard_blocked_by`: strict dependency — node cannot start until these complete
- `alignment_refs`: informational dependency — can run concurrently but should read these artifacts before proceeding

This enables parallelization of nodes that only need to read (not wait for) upstream outputs.

**Files:**
- Modify: `skills/bootstrap.md` (workflow.json schema + all blocked_by references in the node injection rules)
- Modify: `knowledge/orchestrator-template.md` (Core Loop step 4)

- [ ] **Step 1: Update the workflow.json node schema in bootstrap.md**

In `skills/bootstrap.md`, find the workflow.json template (around line 1182–1194). Change:

```json
      "blocked_by": ["<node IDs that must complete before this node can run; empty if no dependencies>"],
```

To:

```json
      "hard_blocked_by": ["<node IDs that must complete before this node can start — strict execution gate>"],
      "alignment_refs": ["<node IDs this node reads from but can run concurrently — reads artifacts after they exist>"],
```

- [ ] **Step 2: Update the Node fields description in bootstrap.md**

Find:

```
- `blocked_by`: Node IDs that must be approved/completed before this node runs. Orchestrator checks this at runtime to decide which nodes are eligible. For game-design nodes, also checks `approval-records.json` gate_status.
```

Replace with:

```
- `hard_blocked_by`: Node IDs that must complete (exit_artifacts exist + human_gate approved if applicable) before this node can START. The orchestrator will not dispatch this node until all hard_blocked_by nodes are complete. Use for true data dependencies — this node's inputs don't exist until upstream finishes.
- `alignment_refs`: Node IDs this node reads artifacts FROM but does not strictly depend on for execution timing. The orchestrator may dispatch this node in parallel with alignment_refs nodes; the node-spec's Context Pull section must handle the case where alignment_refs artifacts may not yet exist (graceful degradation). Use for "I want to align with X's output but can work without it."

**Migration note:** The legacy `blocked_by` field is equivalent to `hard_blocked_by`. Both are accepted; `hard_blocked_by` is preferred for new bootstrap runs.
```

- [ ] **Step 3: Update node injection rules in bootstrap.md to use hard_blocked_by**

Search for all occurrences of `blocked_by:` in the bootstrap.md injection rule blocks (the node-spec YAML frontmatter examples). Change them to `hard_blocked_by:`.

Key occurrences to update (verify with grep before editing):
```bash
grep -n "^blocked_by:\|  blocked_by:" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -20
```

For each occurrence in the node-spec YAML templates (not in documentation prose), change `blocked_by:` → `hard_blocked_by:`.

- [ ] **Step 4: Update orchestrator-template.md**

In `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/orchestrator-template.md`, find the Core Loop step 4:

```
  4. Decide next node:
     - What's done? What's pending? What makes sense next?
     - Can run multiple nodes in parallel if their exit_artifacts don't overlap
```

After `- Can run multiple nodes in parallel if their exit_artifacts don't overlap`, add:

```
     - **hard_blocked_by**: node cannot start until ALL hard_blocked_by nodes are complete (exit_artifacts exist + gate approved)
     - **alignment_refs**: node CAN start even if alignment_refs are not complete; read their artifacts if available, degrade gracefully if not
     - Legacy `blocked_by` field = treat as `hard_blocked_by`
```

- [ ] **Step 5: Verify changes**

```bash
grep -n "hard_blocked_by\|alignment_refs" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -10
grep -n "hard_blocked_by\|alignment_refs" /Users/aa/workspace/myskills/claude/meta-skill/knowledge/orchestrator-template.md | head -5
```

Expected: hard_blocked_by appears in both files; alignment_refs appears in both files.

- [ ] **Step 6: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/skills/bootstrap.md claude/meta-skill/knowledge/orchestrator-template.md
git commit -m "feat(#4): split blocked_by into hard_blocked_by + alignment_refs

Enables parallelization: hard_blocked_by is a strict execution gate;
alignment_refs are informational reads that can run concurrently.
Legacy blocked_by treated as hard_blocked_by."
```

---

## Task 5: Human Gate review_checklist (partial #5)

Adds a `review_checklist` field to the game-design node frontmatter schema. Bootstrap populates 3–5 role-specific checklist items per node type, giving `discipline_owner` a concrete quality bar to check before approving.

**Files:**
- Modify: `knowledge/capabilities/game-design.md` (approval-records schema + node frontmatter)
- Modify: `skills/bootstrap.md` (node injection — add review_checklist to game-design node-specs)

- [ ] **Step 1: Add review_checklist to approval-records.json schema in game-design.md**

In `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/game-design.md`, find the approval-records.json schema section (around line 127–155). Find the record object:

```json
      "gate_status": "pending | in-review | approved | revision-requested",
```

After `gate_status`, add:

```json
      "review_checklist": [
        { "item": "<role-specific check>", "checked": false }
      ],
```

- [ ] **Step 2: Add review_checklist to the node frontmatter schema in game-design.md**

In game-design.md, find the node frontmatter example (around line 176–179):

```yaml
  "human_gate": true,
  ...
  "approval_record_path": ".allforai/game-design/approval-records.json",
  "gate_status": "pending",
```

After `gate_status`, add:

```yaml
  "review_checklist": [
    { "item": "<check>", "checked": false }
  ]
```

Then add this explanation paragraph after the frontmatter schema:

```markdown
**review_checklist population:** Bootstrap generates 3–5 role-specific checklist items per
node type based on `discipline_owner`. Items must be concrete and verifiable — not generic
("looks good") but specific ("all character sprites have consistent line weight of 2px").

Checklist items by node:

| Node | discipline_owner | Checklist items (3–5) |
|------|-----------------|----------------------|
| `art-direction` | `art-director` | 1. 风格参考图与目标受众匹配; 2. 色调方案有明确主色/辅色/强调色; 3. 字体层级清晰（正文/标题/UI）; 4. 动画风格与引擎能力匹配 |
| `art-spec-design` | `concept-artist` | 1. 所有 must_have 资产已列入清单; 2. 每个资产有明确尺寸规格; 3. 资产 ID 唯一无重复; 4. ai_generatable 分类合理; 5. milestone_gate 与发布计划一致 |
| `character-design` | `character-artist` | 1. 主角有完整表情图; 2. 骨骼绑定点位标注清楚; 3. 角色比例在同一参考系下统一 |
| `environment-design` | `environment-artist` | 1. 地砖可无缝拼接（边缘像素匹配）; 2. 视差层数与 art-pipeline-config 一致; 3. 光源方向全场景统一 |
| `ui-art-gen` | `ui-artist` | 1. 所有交互元素有 hover/pressed 状态; 2. 字体渲染在目标分辨率下清晰; 3. 色盲友好（不依赖颜色单独传达信息） |
```

- [ ] **Step 3: Add review_checklist generation to bootstrap.md node injection**

In `skills/bootstrap.md`, find the game-design node injection section that says:

```
All nodes get: `capability: game-design`, `human_gate: true`, `approval_record_path: ".allforai/game-design/approval-records.json"`, `gate_status: "pending"`
```

Replace with:

```
All nodes get: `capability: game-design`, `human_gate: true`, `approval_record_path: ".allforai/game-design/approval-records.json"`, `gate_status: "pending"`, `review_checklist: [<3–5 items from game-design.md checklist table for this node type; use generic items if node not in table>]`
```

- [ ] **Step 4: Verify changes**

```bash
grep -n "review_checklist" /Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/game-design.md | head -10
grep -n "review_checklist" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -5
```

Expected: review_checklist appears in both files.

- [ ] **Step 5: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/knowledge/capabilities/game-design.md claude/meta-skill/skills/bootstrap.md
git commit -m "feat(#5): add review_checklist to human gate nodes

Bootstrap populates 3-5 role-specific checklist items per node type.
discipline_owner must check all items before approving gate."
```

---

## Task 6: Concept Drift Coverage for All Human Gates (#6)

Extends `has_concept_drift` detection to cover revisions in any human gate, not just product-concept. If an art-direction or game-design node was revision-requested, the bootstrap should detect this as drift and trigger incremental re-planning.

**Files:**
- Modify: `skills/bootstrap.md` (Step 1.0 detection + Step 3.0 incremental re-planning)

- [ ] **Step 1: Extend has_concept_drift detection in bootstrap.md Step 1.0**

In `skills/bootstrap.md`, find the `has_concept_drift` detection (around line 44–51):

```
- `has_concept_drift`: true if product-concept/concept-drift.json exists AND its `resolved` field is false
```

Replace with:

```
- `has_concept_drift`: true if ANY of the following:
  - `product-concept/concept-drift.json` exists AND its `resolved` field is false
  - `.allforai/game-design/approval-records.json` exists AND any record has `gate_status == "revision-requested"` (indicates an in-flight revision cycle on a design gate)
  - `.allforai/game-design/approval-records.json` exists AND `revision_notes` is non-empty on any record whose `gate_status == "approved"` in the CURRENT run but `revision_notes` was written in a PREVIOUS run (indicates a re-approval after revision — downstream consumers may need re-execution)
  
  When `has_concept_drift` is true due to approval-records (not concept-drift.json), record the source:
  - `concept_drift_source: "product-concept"` — from concept-drift.json
  - `concept_drift_source: "game-design-gate"` — from approval-records.json revision
```

- [ ] **Step 2: Add game-design drift handling to Step 3.0**

In `skills/bootstrap.md`, find Step 3.0 Incremental Re-Planning section (around line 803). After the existing intro paragraph that begins "When concept has drifted since last bootstrap:", add:

```markdown
**When `concept_drift_source == "game-design-gate"`:**

1. Read `.allforai/game-design/approval-records.json` → collect all records with non-empty `revision_notes`
2. For each revised node, identify which downstream nodes consume its output (from `consumers[]` in workflow.json)
3. Mark those downstream nodes as `"status": "needs-rerun"` — they must re-execute with the updated design input
4. Nodes whose `hard_blocked_by` does not include any revised node → preserve as-is (no re-execution needed)
5. Write revision summary to `.allforai/product-concept/concept-drift.json` if it doesn't exist yet:
   ```json
   {
     "source": "game-design-gate",
     "changes": [
       { "node": "<revised node id>", "revision_notes": "<notes from approval-records>", "detected_at": "<ISO>" }
     ],
     "resolved": false
   }
   ```
6. Set `resolved: false` — orchestrator (/run) marks it resolved after all re-run nodes complete.
```

- [ ] **Step 3: Verify changes**

```bash
grep -n "concept_drift_source\|game-design-gate\|revision-requested" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -10
```

Expected: all three terms appear in the file.

- [ ] **Step 4: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat(#6): extend concept-drift detection to all human gate revisions

has_concept_drift now triggers on approval-records.json revision-requested
status, not just product-concept/concept-drift.json. Downstream consumers
of revised nodes are marked for re-execution."
```

---

## Task 7: Asset Lifecycle locked State (#7)

Adds `locked` as a 5th and final asset state. `locked` means the asset has passed QA and been accepted into the release build — it must not be regenerated or replaced. Formalizes the lifecycle progression rules.

**Files:**
- Modify: `knowledge/capabilities/game-design.md` (current_state schema, art-qa section)
- Modify: `knowledge/domains/art-methodology.md` (lifecycle documentation)

- [ ] **Step 1: Update current_state enum in game-design.md**

In `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/game-design.md`, find:

```json
      "current_state": "placeholder | temp | alpha | final",
```

Replace with:

```json
      "current_state": "placeholder | temp | alpha | final | locked",
```

- [ ] **Step 2: Update substitution schema to include locked**

In game-design.md, find the substitution object:

```json
      "substitution": {
        "placeholder": "<path to geometry / solid color asset>",
        "temp": "<path to AI-generated or free asset>",
        "alpha": null,
        "final": null
      }
```

Replace with:

```json
      "substitution": {
        "placeholder": "<path to geometry / solid color asset>",
        "temp": "<path to AI-generated or free asset>",
        "alpha": null,
        "final": null,
        "locked": null
      }
```

- [ ] **Step 3: Update summary.by_state to include locked**

Find:

```json
    "by_state": { "placeholder": 0, "temp": 0, "alpha": 0, "final": 0 },
```

Replace with:

```json
    "by_state": { "placeholder": 0, "temp": 0, "alpha": 0, "final": 0, "locked": 0 },
```

- [ ] **Step 4: Add lifecycle transition rules after the schema**

After the closing `}` of the art-asset-inventory.json schema block, add:

```markdown
### Asset Lifecycle Transition Rules

```
placeholder → temp:    AI generation succeeds (ai-art-generation node)
temp → alpha:          Art QA passes initial review (art-qa node scores ≥ 3/5)
alpha → final:         discipline_owner approves in art-qa gate
final → locked:        Release build confirmed — set by launch-prep or a dedicated asset-lock command
locked → *:            FORBIDDEN — locked assets cannot regress; create a new asset_id for replacements
```

**Orchestrator behavior:**
- ai-art-generation: transitions placeholder → temp
- art-qa: transitions temp → alpha (on QA pass), alpha → final (on discipline_owner approval)  
- launch-prep: transitions final → locked (when milestone_gate="final" and build is confirmed)
- Any node attempting to overwrite a `locked` asset must report UPSTREAM_DEFECT and halt
```

- [ ] **Step 5: Update art-methodology.md with lifecycle documentation**

In `/Users/aa/workspace/myskills/claude/meta-skill/knowledge/domains/art-methodology.md`, find the section that discusses asset states (search for `current_state` or `placeholder`). Add after the relevant section:

```markdown
## Asset Lifecycle States

| State | Meaning | Set by | Can overwrite? |
|-------|---------|--------|----------------|
| `placeholder` | Geometry shape / solid color stand-in | art-spec-design | Yes |
| `temp` | AI-generated or free asset, unreviewed | ai-art-generation | Yes |
| `alpha` | Passed initial QA (score ≥ 3/5) | art-qa | Yes |
| `final` | Approved by discipline_owner | art-qa gate | Yes (only by re-approval) |
| `locked` | Accepted into release build | launch-prep | **No** — create new asset_id |

**Regression rule:** States may only advance forward. A `final` asset cannot regress to `alpha`
unless a new revision cycle is opened (gate_status → revision-requested). A `locked` asset
is immutable — do not regenerate it; if replacement is needed, create a new asset_id.
```

- [ ] **Step 6: Verify changes**

```bash
grep -n "locked" /Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/game-design.md | head -10
grep -n "locked\|Lifecycle" /Users/aa/workspace/myskills/claude/meta-skill/knowledge/domains/art-methodology.md | head -10
```

Expected: `locked` appears in both files; art-methodology.md has the lifecycle table.

- [ ] **Step 7: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/knowledge/capabilities/game-design.md claude/meta-skill/knowledge/domains/art-methodology.md
git commit -m "feat(#7): add locked as 5th asset lifecycle state

locked = accepted into release build, immutable. Documents full
lifecycle: placeholder→temp→alpha→final→locked with regression rules."
```

---

## Self-Review

**Spec coverage check:**

| Improvement | Task | Covered? |
|-------------|------|---------|
| #1 Concept Contract + canonical_registry | Task 1 | ✅ |
| #2 App Design Capability | Task 2 | ✅ |
| #3 validation_commands (partial) | Task 3 | ✅ |
| #4 hard_blocked_by + alignment_refs | Task 4 | ✅ |
| #5 review_checklist (partial, 3–5 items) | Task 5 | ✅ |
| #6 Concept drift all human gates | Task 6 | ✅ |
| #7 locked state + lifecycle rules | Task 7 | ✅ |

**Placeholder scan:** No TBDs. All task steps contain exact content or exact grep commands to find insertion points.

**Dependencies:** Tasks are independent. Each can be executed and committed separately. Task 4 (hard_blocked_by) and Task 1 (concept-freeze) both touch bootstrap.md — execute Task 1 first, then Task 4 will see the concept-freeze injection already present and avoid conflicts. Task 3 also touches bootstrap.md — same ordering applies (1 → 3 → 4 → 5 → 6).

**Ordering recommendation:** 1 → 2 → 7 → 5 → 3 → 4 → 6 (bootstrap.md changes at end to minimize conflicts; independent file changes first).
