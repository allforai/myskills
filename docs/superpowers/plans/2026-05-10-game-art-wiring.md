# Game-Art Sub-Skill Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the 51 game-art sub-skills into the meta-skill orchestration so that art-gen nodes delegate to `skills/game-art/` instead of embedding generation instructions.

**Architecture:** All changes are in `bootstrap.md` (adds art-gen + art-qa node injection rules with thin node-spec templates) and `game-design.md` (removes legacy embedded `ai-art-generation` prompt construction, replaces with sub-skill delegation note). The sub-skill SKILL.md files are already present and correct — nothing in them changes. Node-specs generated at runtime call sub-skills via `${CLAUDE_PLUGIN_ROOT}/skills/game-art/<layer>/<skill>/SKILL.md`.

**Tech Stack:** Markdown (LLM instruction files), grep for verification. No Python changes.

---

## File Structure

| Action | Path | Change |
|--------|------|--------|
| Modify | `claude/meta-skill/skills/bootstrap.md` (lines ~927-954) | Update art-concept node-spec to reference game-art/10-design sub-skills |
| Modify | `claude/meta-skill/skills/bootstrap.md` (lines ~965-994) | Update concept-freeze node-spec to reference game-art/00-env sub-skills |
| Modify | `claude/meta-skill/skills/bootstrap.md` (after line 994) | Add art-gen node injection block with sub-skill mapping table + per-node-spec templates |
| Modify | `claude/meta-skill/skills/bootstrap.md` (same section) | Add art-qa node injection block |
| Modify | `claude/meta-skill/knowledge/capabilities/game-design.md` (lines ~535-570) | Remove embedded ai-art-generation prompt/tool logic; replace with sub-skill delegation note |

All paths are under `/Users/aa/workspace/myskills/claude/meta-skill/`.

---

## Task 1: Update art-concept node-spec to reference game-art/10-design sub-skills

**Files:**
- Modify: `skills/bootstrap.md` lines ~927-954 (the verbatim art-concept node-spec block)

- [ ] **Step 1: Read the current art-concept node-spec block**

```bash
sed -n '927,955p' /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md
```

Confirm the block starts with ` ```markdown` and contains `读取并执行 \`${CLAUDE_PLUGIN_ROOT}/skills/art-concept.md\`` .

- [ ] **Step 2: Replace the art-concept node-spec content**

In `skills/bootstrap.md`, find this exact block (the verbatim art-concept node-spec between the triple-backtick fences):

```
```markdown
---
node: art-concept
human_gate: false
hard_blocked_by: [art-direction]
unlocks: [art-spec-design]
exit_artifacts:
  - .allforai/game-design/art-pipeline-config.json
---

# Task: 美术技术规格确认（Art Concept Skill Invocation）

## 执行方法

读取并执行 `${CLAUDE_PLUGIN_ROOT}/skills/art-concept.md` skill。

该 skill 完成以下工作：
1. 验收 art-direction 输出（读取 art-style-guide.json.art_overview，3个字段）
2. 执行竞品美术研究（搜索驱动，内部使用）
3. 按维度分支（2D通用/2D像素/3D）进行 Q&A，逐问确认技术规格
4. 产出 `.allforai/game-design/art-pipeline-config.json`（status=final）

## 完成条件

`.allforai/game-design/art-pipeline-config.json` 存在且 `status == "final"`。
```
```

Replace with:

```
```markdown
---
node: art-concept
human_gate: false
hard_blocked_by: [art-direction]
unlocks: [art-spec-design]
exit_artifacts:
  - .allforai/game-design/art-pipeline-config.json
---

# Task: 美术技术规格确认（Art Concept Skill Invocation）

## 执行方法

读取并执行 `${CLAUDE_PLUGIN_ROOT}/skills/art-concept.md` skill，完成交互式 Q&A 并产出 `art-pipeline-config.json`。

art-concept skill 完成后，依次调用以下 game-art 子 skill 细化策略（读取对应 SKILL.md 并执行）：

1. **资产来源策略：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/asset-source-strategy-spec/SKILL.md`
   - 输入：`art-pipeline-config.json`、`art-asset-inventory.json`（若已存在）
   - 输出：每类资产的来源策略（生成/外包/改造/混合）

2. **动画生产计划：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/2d-animation-production-plan/SKILL.md`
   - 输入：`art-pipeline-config.json.animation_system`、`art-pipeline-config.json.character`
   - 输出：动画方案选择（帧动画/DragonBones/Tween/混合）及降级路径

3. **动效设计**（当 `animation_system != "none"` 时）：`${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/motion-design/SKILL.md`
   - 输入：`art-pipeline-config.json`、`art-style-guide.json.art_overview`
   - 输出：关键帧意图、Timing 规则、可读性规范

## 完成条件

`.allforai/game-design/art-pipeline-config.json` 存在且 `status == "final"`。
```
```

- [ ] **Step 3: Verify**

```bash
grep -n "asset-source-strategy-spec\|2d-animation-production-plan\|motion-design\|game-art/10-design" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -10
```

Expected: all three game-art/10-design sub-skill paths appear.

- [ ] **Step 4: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/skills/bootstrap.md
git commit -m "$(cat <<'EOF'
feat: art-concept node delegates to game-art/10-design sub-skills

art-concept node-spec now references asset-source-strategy-spec,
2d-animation-production-plan, and motion-design sub-skills after
the interactive Q&A phase.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Update concept-freeze node-spec to reference game-art/00-env sub-skills

**Files:**
- Modify: `skills/bootstrap.md` lines ~965-994 (the verbatim concept-freeze node-spec block)

- [ ] **Step 1: Read the current concept-freeze node-spec block**

```bash
sed -n '956,995p' /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md
```

Confirm the block contains `读取并执行 \`${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/concept-contract.md\``.

- [ ] **Step 2: Replace the concept-freeze node-spec content**

In `skills/bootstrap.md`, find this exact block (inside the triple-backtick concept-freeze node-spec):

```
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
```

Replace with:

```
# Task: 概念合约冻结（Concept Freeze）

## 执行方法

读取并执行 `${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/concept-contract.md` capability，完成 canonical_registry 构建并写入 `concept-contract.json`。

concept-contract capability 完成后，依次调用以下 game-art 子 skill（读取对应 SKILL.md 并执行）：

1. **工具能力检测：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/production-tool-capability-registry/SKILL.md`
   - 输入：`art-pipeline-config.json.toolchain`
   - 输出：可用工具清单（Blender CLI、图像生成、Atlas 打包工具的实际可用性）
   - 将检测结果写回 `art-pipeline-config.json.toolchain.detected_capabilities`

2. **资产注册表初始化：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/asset-registry/SKILL.md`
   - 输入：`concept-contract.json`（canonical_registry）、`art-asset-inventory.json`
   - 输出：`.allforai/game-design/asset-registry.json`（以 canonical_registry 为权威，资产 ID → 文件前缀 → 生命周期状态的单一可信注册表）

## 完成条件

`.allforai/concept-contract.json` 存在且 `schema_version == "1.0"` 且 `.allforai/game-design/asset-registry.json` 存在。

## 重要说明

所有后续 art-gen 节点必须从 `concept-contract.json` 读取 `canonical_registry`，使用其中的 `file_prefix` 作为生成文件的命名权威来源，不得自行命名。
```

- [ ] **Step 3: Verify**

```bash
grep -n "production-tool-capability-registry\|asset-registry\|game-art/00-env\|detected_capabilities" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -10
```

Expected: both game-art/00-env sub-skill paths appear.

- [ ] **Step 4: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/skills/bootstrap.md
git commit -m "$(cat <<'EOF'
feat: concept-freeze node delegates to game-art/00-env sub-skills

concept-freeze node-spec now calls production-tool-capability-registry
(detects Blender/image tools) and asset-registry (initializes the
canonical asset registry) after building concept-contract.json.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Add art-gen node injection block with sub-skill mapping

**Files:**
- Modify: `skills/bootstrap.md` — insert after the concept-freeze injection block (line ~994), before the `**App Design Node Injection**` section

- [ ] **Step 1: Find the insertion point**

```bash
grep -n "App Design Node Injection\|Concept Freeze for app" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -5
```

Note the line number of `**App Design Node Injection**`. The new block goes immediately before it.

- [ ] **Step 2: Insert the art-gen node injection block**

In `skills/bootstrap.md`, find this exact text (the start of the App Design injection):

```
**App Design Node Injection (when `is_game_project = false` AND goal includes design phase):**
```

BEFORE that line, insert a blank line then this entire block:

````markdown
**Art-Gen Node Injection (when `art-spec-design` and `concept-freeze` are in the selected workflow):**

After injecting `concept-freeze`, read `art-pipeline-config.json.active_nodes` and inject one node-spec per entry. Use the sub-skill mapping table below to determine which `game-art` sub-skills each node-spec should delegate to.

**Sub-Skill Mapping Table:**

| `node_id` | Pre-Spec Sub-Skills (read first) | Generate Sub-Skills (run after) | Condition |
|-----------|----------------------------------|--------------------------------|-----------|
| `tile-art-gen` | `skills/game-art/20-spec/tileset-spec/SKILL.md` | `skills/game-art/30-generate/tileset-generation/SKILL.md` | always |
| `tile-art-gen` | + `skills/game-art/20-spec/2-5d-production-mode-spec/SKILL.md` + `skills/game-art/20-spec/2-5d-lighting-shadow-spec/SKILL.md` | + `skills/game-art/30-generate/render-to-2d-asset-generation/SKILL.md` | when `dimension=2.5d` |
| `character-art-gen` | `skills/game-art/20-spec/character-layer-sheet/SKILL.md` + `skills/game-art/20-spec/visual-style-tokens/SKILL.md` | `skills/game-art/30-generate/skeletal-animation/SKILL.md` | when `character.rig` = `dragonbones`, `dragonbones_mesh`, or `skeletal_3d` |
| `character-art-gen` | same pre-spec | `skills/game-art/30-generate/frame-animation-generation/SKILL.md` | when `character.rig=frame_sequence` |
| `character-art-gen` | — | + `skills/game-art/30-generate/expression-set-generation/SKILL.md` | when `character.expressions=true` (append after primary generate) |
| `environment-art-gen` | `skills/game-art/20-spec/2d-view-mode-spec/SKILL.md` | `skills/game-art/30-generate/background-generation/SKILL.md` + `skills/game-art/30-generate/prop-generation/SKILL.md` | always |
| `environment-art-gen` | + `skills/game-art/20-spec/3d-source-asset-spec/SKILL.md` | + `skills/game-art/30-generate/render-to-2d-asset-generation/SKILL.md` | when `dimension=3d` or `2.5d` |
| `ui-art-gen` | `skills/game-art/20-spec/visual-style-tokens/SKILL.md` | `skills/game-art/30-generate/icon-generation/SKILL.md` | always |
| `ui-art-gen` | — | + `skills/game-art/30-generate/portrait-generation/SKILL.md` | when `concept_art.needed=true` |
| `vfx-art-gen` | `skills/game-art/20-spec/vfx-spec/SKILL.md` | `skills/game-art/30-generate/vfx-generation/SKILL.md` | always |

**Node-spec template for each `active_node` entry:**

Write `.allforai/bootstrap/node-specs/<node-id>.md` using this template, substituting `<TYPE>`, `<REGISTRY_KEY>`, `<CONFIG_SECTION>`, and `<DISCIPLINE_OWNER>` from the canonical node registry in `game-design.md`:

| `node_id` | `<TYPE>` | `<REGISTRY_KEY>` | `<CONFIG_SECTION>` | `<DISCIPLINE_OWNER>` |
|-----------|----------|-----------------|-------------------|---------------------|
| `tile-art-gen` | tile | `tiles` | `tileset` | `concept-artist` |
| `character-art-gen` | character | `characters` | `character` | `character-modeler` |
| `environment-art-gen` | environment | `environments` | `environment` | `environment-artist` |
| `ui-art-gen` | UI | `ui` + `other` | _(all remaining)_ | `ui-artist` |
| `vfx-art-gen` | VFX | `vfx` | `vfx` | `vfx-artist` |

```markdown
---
node: <node-id>
human_gate: true
hard_blocked_by: [concept-freeze]
unlocks: [art-qa]
exit_artifacts:
  - path: .allforai/game-design/<node-id>-review.html
  - path: .allforai/game-design/systems/<node-id>-spec.json
---

# Goal

Generate <TYPE> art assets for all entries in `.allforai/concept-contract.json` `canonical_registry.<REGISTRY_KEY>[]`.

## Inputs

- `.allforai/concept-contract.json` — `canonical_registry.<REGISTRY_KEY>[]` (authoritative asset IDs and `file_prefix` values; do not invent your own names)
- `.allforai/game-design/art-pipeline-config.json` — `<CONFIG_SECTION>` configuration and `toolchain.detected_capabilities`
- `.allforai/game-design/art-asset-inventory.json` — current asset states (skip assets with `current_state == "locked"`)
- `.allforai/game-design/asset-registry.json` — canonical registry built by concept-freeze

## Sub-Skill Invocation

Read and follow each sub-skill SKILL.md in order. Pass the inputs above to each sub-skill. Each sub-skill defines its own output contract — follow it exactly.

### Step 1 — Pre-Spec

<List the pre-spec sub-skill paths from the mapping table above for this node_id, with conditions>

### Step 2 — Generate

<List the generate sub-skill paths from the mapping table above for this node_id, with conditions>

## Completion Condition

`.allforai/game-design/systems/<node-id>-spec.json` exists AND `.allforai/game-design/<node-id>-review.html` exists AND all `canonical_registry.<REGISTRY_KEY>[]` entries have `current_state != "placeholder"`.

If any sub-skill returns `UPSTREAM_DEFECT` → halt and report the defect. Do not advance to `art-qa`.
```

**Key rules for art-gen injection:**
- `hard_blocked_by: ["concept-freeze"]` for ALL art-gen nodes (regardless of type)
- `unlocks: ["art-qa"]` for ALL art-gen nodes
- `human_gate: true` for ALL art-gen nodes (discipline-specific approval required)
- `approval_record_path: ".allforai/game-design/approval-records.json"` for ALL art-gen nodes
- `review_checklist`: use the checklist from `game-design.md` canonical registry table (rows 205-209)
- Do NOT inject a node-spec for entries in `skipped_nodes` — only `active_nodes` get node-specs

````

- [ ] **Step 3: Verify the insertion**

```bash
grep -n "Art-Gen Node Injection\|Sub-Skill Mapping Table\|tile-art-gen.*tileset-spec\|character-art-gen.*skeletal\|vfx-art-gen.*vfx-spec\|UPSTREAM_DEFECT" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -20
```

Expected: "Art-Gen Node Injection" appears; all 5 node_id rows from the mapping table appear; `UPSTREAM_DEFECT` appears in the node-spec template.

- [ ] **Step 4: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/skills/bootstrap.md
git commit -m "$(cat <<'EOF'
feat: add art-gen node injection with game-art sub-skill mapping

bootstrap.md now injects thin node-specs for tile/character/environment/
ui/vfx-art-gen nodes. Each node-spec delegates to the appropriate
game-art/20-spec and game-art/30-generate sub-skills via SKILL.md
references. Includes sub-skill mapping table for all 5 node types
with conditional sub-skill selection by dimension and rig type.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Add art-qa node injection block

**Files:**
- Modify: `skills/bootstrap.md` — add art-qa injection immediately after the art-gen injection block (before `**App Design Node Injection**`)

- [ ] **Step 1: Find the insertion point**

```bash
grep -n "Art-Gen Node Injection\|App Design Node Injection" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -5
```

The art-qa injection goes between the end of the art-gen injection block and `**App Design Node Injection**`.

- [ ] **Step 2: Insert the art-qa injection block**

In `skills/bootstrap.md`, find the line immediately after the art-gen injection ends (the line "- Do NOT inject a node-spec for entries in `skipped_nodes`..."). After that paragraph, before `**App Design Node Injection**`, insert:

````markdown
**Art-QA Node Injection (when `art-qa` is in the canonical node registry for the selected scenario):**

After injecting all art-gen nodes, inject the `art-qa` node:
- `node_id: "art-qa"`, `capability: "game-design"`, `human_gate: true`
- `hard_blocked_by:` ALL active art-gen nodes (i.e., every entry in `active_nodes` that was actually injected — tile-art-gen, character-art-gen, environment-art-gen, ui-art-gen, vfx-art-gen, whichever are in `active_nodes`)
- `unlocks: ["game-design-finalize"]`
- `discipline_owner: "art-director"`
- `approval_record_path: ".allforai/game-design/approval-records.json"`
- `review_checklist:` ["全资产风格一致性（调色板/线条/光影）", "所有资产均有 alpha/final 状态", "Atlas 打包无越界/重叠", "运行时导入通过（无丢失引用）", "3D 衍生资产透视/枢轴正确（若 dimension=2.5d）"]

**Node-spec for art-qa** (write verbatim to `.allforai/bootstrap/node-specs/art-qa.md`):

```markdown
---
node: art-qa
human_gate: true
hard_blocked_by: []  # populated by bootstrap: all active art-gen node IDs
unlocks: [game-design-finalize]
exit_artifacts:
  - path: .allforai/game-design/art-qa-report.html
---

# Goal

Run quality assurance across all generated art assets. Invoke the appropriate game-art QA sub-skills and aggregate results into `art-qa-report.html`.

## Inputs

- `.allforai/concept-contract.json` — `canonical_registry` (all types)
- `.allforai/game-design/art-pipeline-config.json` — `dimension`, `style`, `vfx.approach`
- `.allforai/game-design/systems/` — all `*-art-spec.json` outputs from art-gen nodes
- `.allforai/game-design/art-style-guide.json` — visual style reference

## Sub-Skill Invocation

Read and follow each applicable sub-skill SKILL.md in order:

1. **Style consistency (always):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/2d-style-consistency-qa/SKILL.md`
2. **Atlas packaging (always):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/atlas-packaging/SKILL.md`
3. **Runtime import (always):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/runtime-import-check/SKILL.md`
4. **3D-assisted QA** (when `dimension=2.5d`): `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/3d-assisted-2d-qa/SKILL.md`
5. **Asset pack QA** (when any asset has `source_strategy=pack`): `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-pack-integration-qa/SKILL.md`
6. **License provenance** (when any asset has `source_strategy=pack` or `external`): `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-license-provenance-qa/SKILL.md`

## Completion Condition

`art-qa-report.html` exists AND no sub-skill returned `UPSTREAM_DEFECT`.

**Gate action on sub-skill score < 3/5:**
For each failing asset, set `gate_status: "revision-requested"` in `.allforai/game-design/approval-records.json` for the relevant art-gen node, and populate `revision_notes` with the QA sub-skill's issue list. The orchestrator will re-run that art-gen node with `revision_notes` as context.
```

````

- [ ] **Step 3: Verify**

```bash
grep -n "Art-QA Node Injection\|2d-style-consistency-qa\|atlas-packaging\|runtime-import-check\|art-license-provenance\|revision-requested" /Users/aa/workspace/myskills/claude/meta-skill/skills/bootstrap.md | head -15
```

Expected: "Art-QA Node Injection" appears; all 6 QA sub-skill paths appear; "revision-requested" appears in gate action.

- [ ] **Step 4: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/skills/bootstrap.md
git commit -m "$(cat <<'EOF'
feat: add art-qa node injection delegating to game-art/40-qa sub-skills

art-qa node-spec references 2d-style-consistency-qa, atlas-packaging,
runtime-import-check plus conditional 3d-assisted-2d-qa, asset-pack
and license-provenance QA sub-skills. Gate action on score < 3/5
sets revision-requested on the failing art-gen node.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Simplify game-design.md — remove embedded ai-art-generation instructions

**Files:**
- Modify: `knowledge/capabilities/game-design.md` (ai-art-generation Prompt Construction + Tool Priority + State Update sections, ~lines 535-570)

- [ ] **Step 1: Read the current ai-art-generation section**

```bash
sed -n '520,580p' /Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/game-design.md
```

Confirm you can see the "Prompt Construction", "Tool Priority", "State Update After Generation", and "Completion Signal" sub-sections.

- [ ] **Step 2: Replace embedded generation instructions with delegation note**

In `knowledge/capabilities/game-design.md`, find the section beginning with:

```
### Prompt Construction

```
final_prompt = art_style_guide.style_prompt_prefix
```
```

And ending just before `### Completion Signal` (or whatever section follows). Replace the entire "Prompt Construction", "Tool Priority (requires ai-gateway MCP configured)", and "State Update After Generation" sub-sections with:

```markdown
### Generation Delegation

**New projects:** Art generation is handled entirely by the role-based art-gen node-specs injected by `bootstrap.md`. Each art-gen node-spec delegates to the appropriate `game-art` sub-skills:

- `tile-art-gen` → `game-art/20-spec/tileset-spec` + `game-art/30-generate/tileset-generation`
- `character-art-gen` → `game-art/20-spec/character-layer-sheet` + `game-art/30-generate/skeletal-animation` (or `frame-animation-generation`)
- `environment-art-gen` → `game-art/20-spec/2d-view-mode-spec` + `game-art/30-generate/background-generation`
- `ui-art-gen` → `game-art/20-spec/visual-style-tokens` + `game-art/30-generate/icon-generation`
- `vfx-art-gen` → `game-art/20-spec/vfx-spec` + `game-art/30-generate/vfx-generation`

See `bootstrap.md` Art-Gen Node Injection for the full sub-skill mapping table and node-spec templates.

**Legacy `ai-art-generation` node** (retained for backward compatibility only): uses the old embedded prompt construction and image generation API. Do not use for new projects. The `ai-art-generation` node-spec, if present, still updates `current_state`, `ai_generated.*`, and `substitution.*` fields as before.
```

- [ ] **Step 3: Verify**

```bash
grep -n "Generation Delegation\|game-art/20-spec\|game-art/30-generate\|backward compatibility only\|Prompt Construction" /Users/aa/workspace/myskills/claude/meta-skill/knowledge/capabilities/game-design.md | head -15
```

Expected: "Generation Delegation" appears; sub-skill paths appear; "Prompt Construction" does NOT appear (removed).

- [ ] **Step 4: Run all unit tests to confirm no Python regressions**

```bash
cd /Users/aa/workspace/myskills
python3 -m pytest claude/meta-skill/tests/unit/ -v 2>&1 | tail -5
```

Expected: `10 passed`.

- [ ] **Step 5: Commit**

```bash
cd /Users/aa/workspace/myskills
git add claude/meta-skill/knowledge/capabilities/game-design.md
git commit -m "$(cat <<'EOF'
refactor: replace embedded art generation logic with sub-skill delegation note

Removes Prompt Construction, Tool Priority, and State Update sections
from the ai-art-generation description in game-design.md. New projects
use role-based art-gen node-specs that delegate to game-art/ sub-skills.
Legacy ai-art-generation node retained for backward compatibility.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**Spec coverage:**

| Requirement | Task | Covered? |
|-------------|------|---------|
| art-concept → game-art/10-design sub-skills | Task 1 | ✅ |
| concept-freeze → game-art/00-env sub-skills | Task 2 | ✅ |
| art-gen node injection with sub-skill mapping | Task 3 | ✅ |
| tile-art-gen → tileset-spec + tileset-generation | Task 3 | ✅ |
| character-art-gen → character-layer-sheet + skeletal/frame-animation | Task 3 | ✅ |
| environment-art-gen → 2d-view-mode-spec + background + prop | Task 3 | ✅ |
| ui-art-gen → visual-style-tokens + icon + portrait | Task 3 | ✅ |
| vfx-art-gen → vfx-spec + vfx-generation | Task 3 | ✅ |
| art-qa node injection | Task 4 | ✅ |
| art-qa → 2d-style-consistency-qa + atlas-packaging + runtime-import-check | Task 4 | ✅ |
| art-qa gate action → revision-requested on failing art-gen node | Task 4 | ✅ |
| Remove embedded generation instructions from game-design.md | Task 5 | ✅ |

**Placeholder scan:** None — all sub-skill paths are fully specified. All conditions (dragonbones vs frame, dimension=2.5d, expressions=true) are explicit. The node-spec template is complete with all required YAML fields.

**Consistency check:**
- `hard_blocked_by: ["concept-freeze"]` used consistently for all art-gen nodes in Task 3 ✅
- `unlocks: ["art-qa"]` used consistently for all art-gen nodes in Task 3 ✅
- `game-art/` path prefix used consistently throughout ✅
- `${CLAUDE_PLUGIN_ROOT}` variable used consistently in all sub-skill references ✅
- `approval_record_path: ".allforai/game-design/approval-records.json"` consistent with bootstrap.md convention ✅
