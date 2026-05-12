---
name: game-design
description: >
  Game Design Document (GDD) orchestration capability for game projects. Defines
  bootstrap node routing, approval gates, final aggregation, and downstream
  handoff for game design workflows. Concrete design methodology, art generation,
  and validation are delegated to bundled game-* sub-skills.
---

# Game Design Capability

> Orchestration layer for game project design. Reads lightweight domain
> selection knowledge from `${CLAUDE_PLUGIN_ROOT}/knowledge/domains/gaming.md`
> and delegates concrete execution to bundled game-* sub-skills.

## Goal

Bridge `product-concept` (vision) and `generate-artifacts` (code) by injecting
game-design nodes, approval gates, and final handoff artifacts. This capability
does not own detailed game design or art production methods; those live in
`skills/game-design/*`, `skills/game-systems/*`, `skills/game-level/*`,
`skills/game-narrative/*`, `skills/game-balance/*`, `skills/game-combat/*`,
`skills/game-content/*`, `skills/game-onboarding/*`, `skills/game-liveops/*`,
`skills/game-genre-common/*`, `skills/game-art/*`, `skills/game-ui/*`, and
`skills/game-audio/*`. Client assembly and playable frontend validation live in
`skills/game-frontend/*`. Program/runtime-facing contracts live in
`skills/game-runtime/*`.

## Knowledge Layer Reference

This capability is the **orchestration layer** over `domains/gaming.md`:

| Layer | File | Responsibility |
|-------|------|----------------|
| Knowledge | `domains/gaming.md` | Lightweight genre/template selection and fallback LLM guidance |
| Orchestration | `capabilities/game-design.md` (this file) | Node registry, sub-skill mapping, approval gate protocol, final aggregation, downstream handoff |
| Execution | `skills/game-*/*/SKILL.md` | Concrete methodology, input/output contracts, generation, QA, repair routing |

Bootstrap reads `gaming.md` and this file when generating node-specs for game
projects:
- From `gaming.md`: scenario/template selection and fallback LLM context.
- From this file: canonical node IDs, output paths, approval gates, sub-skill
  mapping, and final handoff rules.
- From mapped sub-skills: concrete methodology, artifact contracts, validation,
  generation, and repair routing.

## Trigger Conditions

Bootstrap activates this capability when `bootstrap-profile.json.is_game_project = true`.

`is_game_project` is set to true only after explicit user confirmation — engine detection
(Unity, Unreal, Godot, LÖVE2D, Bevy, Flame, pygame) triggers a confirmation question in
Step 1.5; user must confirm the project is a game before `is_game_project` is set.
Direct selection of 业务领域 f) 游戏 in the no-code prompt also sets `is_game_project = true`.

Skip when:
- Project is a game SDK / engine (not a playable game itself)
- Project is a game editor plugin / game tool

## Pipeline Position

```
product-concept
  ↓
[game-design nodes — bootstrap selects from game-scenario-templates/]
  ├─ core-loop-design
  ├─ [scenario-specific system nodes]
  ├─ art-direction            (delegates to game-art art-direction input contract)
  │     ↓
  │   art-concept skill       (交互式美术技术规格，产出 art-pipeline-config.json)
  │     ↓
  ├─ art-spec-design          (delegates to game-art asset registry/spec skills)
  └─ [art-gen nodes]          (由 art-pipeline-config.active_nodes 决定)
  ↓
game-design-finalize  (aggregates all system JSONs → game-design-doc.json + handoff artifacts; human gate: lead-designer)
  ↓
product-analysis  (reads game-design-doc.json as concept baseline)
  ↓
generate-artifacts
```

## Art Concept Trigger

Bootstrap 在生成 `art-spec-design` node-spec 时，须在其 `Context Pull` 段注明：

```
执行前检查 art-pipeline-config.json 是否存在：
  存在且 status="final" → 直接读取，按 config 特化资产清单
  不存在 / status="draft" → 提示用户先运行 art-concept skill：
    "art-pipeline-config.json 不存在或未完成。请在继续前运行 /art-concept 确认美术技术规格。"
    暂停执行，等待 art-concept 完成后重新触发
```

`art-direction` 节点 approved → `/run` 自动调起 `art-concept` skill（读取
`art-style-guide.json.art_overview`）。art-concept 完成后，`/run` 继续推进 `art-spec-design`。

## Team Roles

Used in `discipline_owner` and `discipline_reviewers` node-spec fields.

**Design (策划)**
- `lead-designer` — 主策划
- `combat-designer` — 战斗策划
- `systems-designer` — 系统策划
- `narrative-designer` — 剧情策划
- `level-designer` — 关卡策划
- `numeric-designer` — 数值策划
- `monetization-designer` — 商业化策划
- `ux-designer` — UI/UX 策划

**Engineering (程序)**
- `gameplay-programmer` — 玩法程序
- `backend-programmer` — 服务端程序
- `ui-programmer` — UI 程序
- `ai-programmer` — AI 程序
- `graphics-programmer` — 渲染程序
- `tools-programmer` — 工具程序

**Art (美术)**
- `art-director` — 美术总监
- `concept-artist` — 原画
- `ui-artist` — UI 美术
- `character-modeler` — 角色建模
- `environment-artist` — 场景美术
- `animator` — 动画师
- `vfx-artist` — 特效师
- `technical-artist` — 技术美术

**Other**
- `audio-director` — 音频总监
- `producer` — 制作人

## Node Execution Protocol

### HTML Output And Review Dashboard

Every game-design node generates a static HTML file as its primary review
artifact. Node HTML files are read-only display documents. Approval state lives
only in `.allforai/game-design/approval-records.json`.

Bootstrap must also generate `.allforai/game-design/review-dashboard.html`
immediately after creating `approval-records.json`. This dashboard is the
approval control surface and must exist before any game-design node runs. It is
not produced by `game-design-finalize`.

`review-dashboard.html` must be a static file served by a local static server
when `/run` needs review interaction, for example:

```bash
python3 -m http.server 43871 --directory .allforai/game-design
```

When served over HTTP, the page fetches `approval-records.json` with a
cache-busting query and refreshes periodically. It must use Chinese interface
text for human reviewers, show every gate record, link to each node's HTML
output when present, provide checklist visibility, provide `reviewer_notes`
and `revision_notes` text inputs, and expose controls equivalent to Approve /
Request revision / Save notes.

Because browser static pages cannot safely write arbitrary local files, write
back is owned by `/run` through Playwright:

1. Playwright opens `review-dashboard.html`.
2. The user or automation fills notes and clicks an action button.
3. The page queues a JSON action in `window.__approvalDashboard.getPendingAction()`.
4. `/run` reads that action with Playwright and applies it to
   `approval-records.json` using
   `.allforai/bootstrap/scripts/apply_approval_action.py`.
5. `/run` clears the queued action with
   `window.__approvalDashboard.clearPendingAction()` and refreshes the page.

This preserves the source of truth in `approval-records.json` while still
making approval an interactive, Playwright-controlled part of the skill flow.

### Approval Records Schema

`/run` reads this file to determine gate status before advancing:

```json
{
  "records": [
    {
      "node_id": "<node_id from Canonical Node Registry>",
      "gate_status": "pending | in-review | approved | revision-requested",
      "review_checklist": [
        { "item": "<role-specific quality check>", "checked": false }
      ],
      "discipline_owner": "<role_id>",
      "discipline_reviewers": ["<role_id>"],
      "approved_by": [],
      "revision_notes": "",
      "reviewer_notes": "",
      "approved_at": null,
      "unlocks": ["<downstream_node_id>"]
    }
  ]
}
```

**Consistency invariant:** The `unlocks[]` field here MUST be identical to the corresponding `workflow.json nodes[].unlocks[]` field written by bootstrap. Bootstrap is the single writer of both fields and MUST derive them from the same source (node_order). `/run` uses `approval-records.json.unlocks[]` for gate-driven unblocking of game-design nodes; if these diverge from `workflow.json.nodes[].unlocks[]`, the orchestrator graph will be out of sync. Verify after bootstrap: `records[i].unlocks == workflow.json.nodes[matching_id].unlocks` for every game-design node.

Note on `revision_notes` vs `reviewer_notes`: `revision_notes` is written by the `discipline_owner` when requesting changes (triggers re-execution); `reviewer_notes` is written by `discipline_reviewers` for advisory observations that do not change `gate_status`.

Gate rules:
- `gate_status == "pending"` AND node's `exit_artifacts` all exist → `/run` automatically sets `gate_status` to `"in-review"` and notifies `discipline_owner` that the output is ready for review. (Bootstrap initializes all records as `pending`; node execution produces the artifacts; `/run` transitions to `in-review` — this is the only way to reach `in-review`.)
- `gate_status == "in-review"` → wait for `discipline_owner` to review the HTML output and either approve or request revision. `/run` does not advance to next game-design node while any predecessor is `in-review`.
- `gate_status == "approved"` → unlock all `unlocks[]` nodes
- `gate_status == "revision-requested"` → re-execute node with `revision_notes` as instruction; after re-execution completes, reset `gate_status` to `"in-review"` (awaiting fresh approval from `discipline_owner`)
- `discipline_owner` must approve (drives `gate_status`); `discipline_reviewers` approval is advisory — reviewers may add `reviewer_notes` but cannot change `gate_status` unilaterally; if reviewer flags an issue post-approval, they must coordinate with `discipline_owner` to reset `gate_status` to `"revision-requested"`

Bootstrap initialises this file with one `pending` record per game-design node
when writing node-specs to `.allforai/bootstrap/`, then immediately renders
`.allforai/game-design/review-dashboard.html` from it.

### Node-Spec Extension Fields

Every game-design node-spec adds these fields beyond standard node-spec schema:

```json
{
  "discipline_owner": "<role_id>",
  "discipline_reviewers": ["<role_id>"],
  "html_output": ".allforai/game-design/<filename>.html",
  "json_output": ".allforai/game-design/systems/<artifact>.json",
  "prose_output": null,
  "human_gate": true,
  "gate_approval_rule": "discipline_owner must approve; reviewers approval is advisory",
  "approval_record_path": ".allforai/game-design/approval-records.json",
  "gate_status": "pending",
  "review_checklist": [{ "item": "<check>", "checked": false }],
  "presentation": {
    "primary_audience": "<role_id>",
    "layout": "<layout_type>",
    "required_visuals": ["<visual_type>"],
    "progressive_disclosure": {
      "above_fold": "<content shown immediately>",
      "expanded": "<content shown on expand>",
      "collapsed": "<content shown on demand>"
    }
  }
}
```

**review_checklist population:** Bootstrap generates 3–5 role-specific checklist items per
node type based on `discipline_owner`. Items must be concrete and verifiable — not generic
("looks good") but specific ("all character sprites have consistent line weight").

Checklist items by node:

| Node | discipline_owner | Checklist items |
|------|-----------------|-----------------|
| `art-direction` | `art-director` | 1. 风格参考图与目标受众匹配; 2. 色调方案有明确主色/辅色/强调色; 3. 字体层级清晰（正文/标题/UI）; 4. 动画风格与引擎能力匹配 |
| `art-spec-design` | `concept-artist` | 1. 所有 must_have 资产已列入清单; 2. 每个资产有明确尺寸规格; 3. 资产 ID 唯一无重复; 4. ai_generatable 分类合理; 5. milestone_gate 与发布计划一致 |
| `character-design` | `character-artist` | 1. 主角有完整表情图; 2. 骨骼绑定点位标注清楚; 3. 角色比例在同一参考系下统一 |
| `environment-design` | `environment-artist` | 1. 地砖可无缝拼接（边缘像素匹配）; 2. 视差层数与 art-pipeline-config 一致; 3. 光源方向全场景统一 |
| `ui-art-gen` | `ui-artist` | 1. 所有交互元素有 hover/pressed 状态; 2. 字体渲染在目标分辨率下清晰; 3. 色盲友好（不依赖颜色单独传达信息） |

## Output Language Policy

All game-design nodes produce documents reviewed by Chinese development teams.
Bootstrap MUST inject this policy into every generated game-design node-spec.

| Content type | Required language |
|---|---|
| HTML navigation, section headings, labels, button text, captions | Chinese (zh-CN) |
| Document title, page header, badge text | Chinese (zh-CN) |
| Design descriptions, rationale, comments | Chinese (zh-CN) |
| JSON description/display string values | Chinese (zh-CN) |
| In-game proper nouns (character names, place names, item names) | Game world's native language (e.g., Japanese for Japan-themed games) — do NOT translate |
| JSON field **keys** | English snake_case (schema convention — do not translate) |
| JSON ID / enum values | English snake_case |

**Enforcement rule:** Any HTML output that uses English for navigation tabs, section titles, or
descriptive labels is a policy violation and must be requested for revision.

## Design Integrity Rules

Every game-design node execution MUST follow these rules to prevent stale or conflicting content
from appearing in output documents.

### Rule 1: Input-First, No Invention

All mechanics, currencies, item names, and system values in output documents MUST be sourced
from the authoritative input files (concept-baseline.json, core-mechanics.json, worldbuilding.json,
etc.). The LLM MUST NOT fill in values from general game design knowledge when the input files
provide the authoritative values.

**Before generating any content section, explicitly read the relevant input fields:**
- Currency system → read `concept-baseline.json.economy.currency_model`
- Special mechanics → read `core-mechanics.json` for the active mechanic list
- Character names → read `worldbuilding.json.characters[]`
- Chapter structure → read `worldbuilding.json.chapters[]`

### Rule 2: No Deprecated Content in Output Documents

Output HTML and JSON MUST NOT contain any reference to systems, mechanics, or values that are
not currently active in the project design. This includes:

- **Never** reference old mechanic names even as historical context (e.g., "旧版 X", "previously X", "replaced by Y")
- **Never** include currency types, item names, or SKUs that are not in the current concept-baseline
- **Never** include color swatches, UI components, or asset entries for removed systems
- If a sub-skill template contains placeholder examples with generic game design patterns (e.g.,
  "hard currency", "bomb tile"), those placeholders MUST be replaced with the actual values from
  the project's input files — never output the placeholder itself

**Enforcement:** Any reference to a system not present in concept-baseline.json or core-mechanics.json
is a violation. The node must re-read the input files and remove the reference before finalizing output.

### Rule 3: Sub-Skill Output Verification

After invoking each sub-skill, the orchestrating node MUST verify that the sub-skill's output:
1. Does not contain system/mechanic names absent from the project's authoritative input files
2. Does not include "旧版", "deprecated", "old version", "previously", "replaced" in visible UI text
3. Color palettes, icon lists, and asset tables only reference currently-active game systems

If a violation is found, the node corrects it before writing the final exit artifact — it does NOT
pass the violation through to the output document.

### Rule 4: Concept-Baseline is the Single Source of Truth

`concept-baseline.json` is the authoritative contract for:
- Economy model (single/dual currency, currency names, IAP SKUs)
- Core mechanic names and special tile/block identifiers
- Chapter count and structure
- Retention hook constraints (e.g., no time-pressure mechanics)

Any sub-skill output that contradicts concept-baseline.json MUST be overridden by the
orchestrating node before writing exit artifacts.

## Canonical Node Registry

Bootstrap MUST use these exact IDs when generating game-design node-specs.
No improvised names.

| node_id | discipline_owner | html_output | json_output | gaming.md phase |
|---------|-----------------|-------------|-------------|-----------------|
| `core-loop-design` | `lead-designer` | `game-design/core-loop.html` | `game-design/systems/core-mechanics.json` | core-mechanics-design |
| `ftue-design` | `ux-designer` | `game-design/ftue.html` | `game-design/systems/ftue.json` | level-design |
| `monetization-design` | `monetization-designer` | `game-design/monetization.html` | `game-design/systems/monetization-design.json` | monetization-design |
| `retention-hook-design` | `systems-designer` | `game-design/retention-hook.html` | `game-design/systems/retention-hook.json` | progression-system |
| `meta-game-design` | `systems-designer` | `game-design/meta-game.html` | `game-design/systems/meta-game.json` | progression-system |
| `combat-system-design` | `combat-designer` | `game-design/combat-system.html` | `game-design/systems/combat-system.json` | core-mechanics-design |
| `skill-tree-design` | `combat-designer` | `game-design/skill-tree.html` | `game-design/systems/skill-tree.json` | progression-system |
| `progression-curve-design` | `numeric-designer` | `game-design/progression-curve.html` | `game-design/systems/progression-curve.json` | progression-system |
| `economy-design` | `numeric-designer` | `game-design/economy-design.html` | `game-design/systems/economy-model.json` | economy-design |
| `narrative-design` | `narrative-designer` | `game-design/narrative.html` | `game-design/systems/narrative-design.json` | narrative-design |
| `level-design` | `level-designer` | `game-design/level-design.html` | `game-design/systems/level-design.json` | level-design |
| `worldbuilding` | `narrative-designer` | `game-design/worldbuilding.html` | `game-design/systems/worldbuilding.json` _(structured summary; aggregated by finalize)_; `prose_output`: `game-design/systems/worldbuilding-bible.md` _(full lore prose; linked via lore_file field, not parsed as JSON)_ | worldbuilding |
| `network-architecture-design` | `backend-programmer` | `game-runtime/network/network-architecture.html` | `game-runtime/network/network-architecture-spec.json` | (runtime architecture) |
| `matchmaking-design` | `backend-programmer` | `game-runtime/server/matchmaking-service.html` | `game-runtime/server/matchmaking-service-spec.json` | (runtime service) |
| `competitive-balance-design` | `numeric-designer` | `game-design/competitive-balance.html` | `game-design/systems/balance-report.json` | balance-testing |
| `run-structure-design` | `lead-designer` | `game-design/run-structure.html` | `game-design/systems/run-structure.json` | core-mechanics-design |
| `meta-progression-design` | `systems-designer` | `game-design/meta-progression.html` | `game-design/systems/meta-progression.json` | progression-system |
| `procedural-gen-spec` | `gameplay-programmer` | `game-runtime/simulation/procedural-generator.html` | `game-runtime/simulation/procedural-generator-spec.json` | (runtime simulation) |
| `ai-faction-design` | `ai-programmer` | `game-runtime/simulation/ai-faction-runtime.html` | `game-runtime/simulation/ai-faction-runtime-spec.json` | (runtime simulation) |
| `tech-tree-design` | `systems-designer` | `game-design/tech-tree.html` | `game-design/systems/tech-tree.json` | progression-system |
| `branching-structure-design` | `narrative-designer` | `game-design/branching-structure.html` | `game-design/systems/branching-structure.json` | narrative-design |
| `character-arc-design` | `narrative-designer` | `game-design/character-arc.html` | `game-design/systems/character-arc.json` | narrative-design |
| `art-direction` | `art-director` | `game-design/art-direction.html` | `game-design/art-style-guide.json` (含 art_overview 字段) | art-direction |
| `art-concept` | _(skill — /run 自动调起，无 discipline_owner)_ | — | `game-design/art-pipeline-config.json` | art-direction |
| `art-spec-design` | `concept-artist` | `game-design/art-spec-design.html` | `game-design/art-asset-inventory.json` | art-direction |
| `tile-art-gen` | `concept-artist` | `game-design/tile-art-review.html` | `game-design/systems/tile-art-spec.json` | art-gen |
| `character-art-gen` | `character-modeler` | `game-design/character-art-review.html` | `game-design/systems/character-art-spec.json` | art-gen |
| `environment-art-gen` | `environment-artist` | `game-design/environment-art-review.html` | `game-design/systems/environment-art-spec.json` | art-gen |
| `ui-art-gen` | `ui-artist` | `game-design/ui-art-review.html` | `game-design/systems/ui-art-spec.json` | art-gen |
| `vfx-art-gen` | `vfx-artist` | `game-design/vfx-art-review.html` | `game-design/systems/vfx-asset-spec.json` | art-gen |
| `art-qa` | `art-director` | `game-design/art-qa-report.html` | — | art-gen |
| `anti-cheat-design` | `backend-programmer` | `game-runtime/security/anti-cheat-architecture.html` | `game-runtime/security/anti-cheat-architecture-spec.json` | (runtime security) |
| `dialogue-system-spec` | `gameplay-programmer` | `game-design/dialogue-system.html` | `game-design/systems/dialogue-system.json` | narrative-design |
| `audio-design` | `audio-director` | `game-design/audio-design.html` | `game-design/systems/audio-design.json` | — |
| `game-design-finalize` | `lead-designer` | `game-design/game-design-dashboard.html` | `game-design/game-design-doc.json` | — |
| `puzzle-design` | `level-designer` | `game-design/puzzle-design.html` | `game-design/systems/puzzle-design.json` | level-design |
| `card-system-design` | `systems-designer` | `game-design/card-system.html` | `game-design/systems/card-system.json` | progression-system |
| `ai-art-generation` | _(automatic — no discipline_owner)_ | _(updates art-direction.html)_ | updates `art-asset-inventory.json` | — |

## Finalize Exit Artifacts

`game-design-finalize` has one primary `json_output` in the registry table, but
it must also produce handoff artifacts consumed by art and downstream program
development. Bootstrap MUST add all paths below to the `game-design-finalize`
node's `exit_artifacts`:

```text
.allforai/game-design/game-design-doc.json
.allforai/game-design/game-design-dashboard.html
.allforai/game-design/design/art-input-handoff.json
.allforai/game-design/design/art-input-handoff-report.json
.allforai/game-design/design/game-planning-handoff.md
.allforai/game-design/design/program-development-node-handoff.json
```

The handoff artifacts are formal cross-phase contracts, not optional helper
files. `product-analysis` and downstream implementation nodes may rely on them
after `game-design-finalize` is approved.

## Sub-Skill Mapping

Bootstrap reads this table when injecting game-design node-specs. Nodes with `sub_skill_paths` → generate thin delegating node-spec (read and follow each SKILL.md in sequence). Nodes with `—` → generate LLM-based node-spec using `domains/gaming.md` methodology.
After reading this table, bootstrap MUST apply §Conditional Sub-Skill Expansion
Rules and MUST validate every expanded path before writing node-specs.

Sub-skill paths expand to `${CLAUDE_PLUGIN_ROOT}/skills/<path>/SKILL.md`.

| node_id | sub_skill_paths |
|---------|----------------|
| `core-loop-design` | `game-systems/10-design/core-loop-design` |
| `ftue-design` | `game-onboarding/10-design/first-session-experience-spec`, `game-onboarding/20-spec/tutorial-step-spec`, `game-onboarding/20-spec/feature-unlock-teaching-spec`, `game-onboarding/40-qa/ftue-friction-qa`, `game-ui/10-design/ui-flow-design`, `game-ui/20-spec/screen-layout-spec` |
| `monetization-design` | `game-design/20-spec/economy-spec` |
| `retention-hook-design` | `game-design/10-concept/player-experience-contract` |
| `meta-game-design` | `game-design/20-spec/meta-game-spec` |
| `combat-system-design` | `game-design/20-spec/combat-spec`, `game-combat/20-spec/enemy-behavior-spec`, `game-combat/20-spec/skill-design-spec`, `game-combat/20-spec/status-effect-spec`, `game-combat/40-qa/combat-readability-qa` |
| `skill-tree-design` | `game-systems/20-spec/progression-spec` |
| `progression-curve-design` | `game-systems/20-spec/progression-spec` |
| `economy-design` | `game-systems/20-spec/economy-spec` |
| `narrative-design` | `game-narrative/10-design/narrative-tone-design`, `game-narrative/20-spec/quest-text-spec` |
| `level-design` | `game-design/20-spec/level-design-spec`, `game-level/00-env/level-registry`, `game-level/10-design/level-flow-design`, `game-level/20-spec/level-layout-spec`, `game-level/20-spec/player-skill-model-spec`, `game-level/20-spec/level-difficulty-budget-spec`, `game-level/20-spec/teaching-beat-spec`, `game-level/20-spec/encounter-placement-spec`, `game-level/20-spec/reward-placement-spec`, `game-level/40-qa/level-difficulty-validation-qa`, `game-level/40-qa/level-pacing-qa`, `game-level/40-qa/level-playability-qa` |
| `worldbuilding` | `game-narrative/10-design/narrative-tone-design` |
| `network-architecture-design` | `game-runtime/20-spec/network-architecture-spec` |
| `matchmaking-design` | `game-runtime/20-spec/matchmaking-service-spec` |
| `competitive-balance-design` | `game-balance/00-env/balance-registry`, `game-balance/10-design/balance-goal-spec`, `game-balance/30-generate/balance-table-generation`, `game-balance/40-qa/combat-balance-qa`, `game-systems/40-qa/balance-sanity-qa` |
| `run-structure-design` | `game-design/10-concept/core-game-loop-spec` |
| `meta-progression-design` | `game-systems/20-spec/progression-spec` |
| `procedural-gen-spec` | `game-runtime/20-spec/procedural-generator-spec` |
| `ai-faction-design` | `game-runtime/20-spec/ai-faction-runtime-spec` |
| `tech-tree-design` | `game-design/20-spec/mechanics-spec` |
| `branching-structure-design` | `game-narrative/20-spec/dialogue-spec` |
| `character-arc-design` | `game-narrative/10-design/narrative-tone-design` |
| `art-direction` | `game-art/10-design/art-direction-input-contract` |
| `art-concept` | _(skill — auto-triggered by /run, not a registry node)_ |
| `art-spec-design` | `game-art/00-env/asset-registry` |
| `tile-art-gen` | _(see bootstrap.md Art-Gen Node Injection)_ |
| `character-art-gen` | _(see bootstrap.md Art-Gen Node Injection)_ |
| `environment-art-gen` | _(see bootstrap.md Art-Gen Node Injection)_ |
| `ui-art-gen` | _(see bootstrap.md Art-Gen Node Injection)_ |
| `vfx-art-gen` | _(see bootstrap.md Art-Gen Node Injection)_ |
| `art-qa` | _(see bootstrap.md Art-Gen Node Injection)_ |
| `anti-cheat-design` | `game-runtime/20-spec/anti-cheat-architecture-spec` |
| `dialogue-system-spec` | `game-narrative/20-spec/dialogue-spec` |
| `audio-design` | `game-audio/10-design/audio-style-design`, `game-audio/20-spec/music-cue-spec`, `game-audio/20-spec/sfx-spec` |
| `game-design-finalize` | `game-design/30-generate/design-data-table-generation`, `game-design/30-generate/art-input-handoff-generation`, `game-design/40-qa/content-coverage-qa`, `game-design/40-qa/core-loop-closure-qa`, `game-design/40-qa/contract-wiring-qa`, `game-design/40-qa/game-design-final-closure-qa` |
| `puzzle-design` | `game-design/20-spec/level-design-spec`, `game-level/10-design/level-flow-design`, `game-level/20-spec/level-layout-spec`, `game-level/20-spec/teaching-beat-spec`, `game-level/40-qa/level-pacing-qa` |
| `card-system-design` | `game-design/20-spec/mechanics-spec` |
| `ai-art-generation` | _(legacy — superseded by art-gen nodes)_ |

## Conditional Sub-Skill Expansion Rules

Bootstrap must keep workflow nodes coarse-grained. These rules append leaf
sub-skills into the selected node-spec's `Sub-Skill Invocation`; they do not
create additional workflow nodes unless a scenario template explicitly selects
one.

**Path validation:** For every sub-skill path from §Sub-Skill Mapping or this
section, verify `${CLAUDE_PLUGIN_ROOT}/skills/<path>/SKILL.md` exists before
writing node-specs. The file must include `Input Contract`, `Output Contract`,
`Invocation Contract`, `Automatic Validation`, and `Completion Conditions`.
If any required file or section is missing, fail bootstrap with
`BOOTSTRAP_SUB_SKILL_MAPPING_INVALID` and list the missing path/section. Do not
fall back to generic LLM execution for a path that is explicitly mapped.

**Level design:** The `level-design` chain owns level flow, layout, player
skill model, difficulty budget, teaching, encounter/reward placement, and
pacing QA.
`level-blockout-generation` may be appended when a visual/blockout preview is
required by the scenario or when downstream frontend/runtime validation needs a
map artifact.
`level-difficulty-validation-qa` is the hard gate for level difficulty. It must
run after difficulty budget, teaching, encounter, reward, and layout specs, and
before pacing/playability closure. Pacing/playability QA may not pass a level
that has blocker difficulty-validation findings.

**Templates:** Append the following to `game-design-finalize` when the game has
items, enemies, skills, levels, quests, economy rows, drop tables, content packs,
or any implementation goal that needs reusable data containers:
`game-templates/00-env/template-registry`,
`game-templates/20-spec/template-schema-spec`,
`game-templates/20-spec/template-inheritance-spec`,
`game-templates/20-spec/template-reference-binding-spec`,
`game-templates/30-generate/template-instance-generation`,
`game-templates/40-qa/template-reference-closure-qa`.
Append `game-templates/40-qa/template-runtime-load-qa` only when a runnable
frontend/runtime load surface exists; if it cannot run, the skill must block
rather than accept static inspection.

**Frontend handoff:** Do not inject `game-frontend` as a game-design review
node. When the overall user goal includes implementation, `game-design-finalize`
must emit `program-development-node-handoff.json` entries telling downstream
program nodes to invoke the `game-frontend` pack after approved art, UI, audio,
level, template, and runtime contracts exist. Frontend validation must run
through the executable QA skills in `game-frontend/40-qa`; unavailable runtime
commands are blockers.

**Shared production map:** `game-production/SKILL.md` is a routing reference,
not an executable node. Bootstrap may cite it in generated node-specs when
resolving ownership conflicts, but must not add it to workflow execution.

## Presentation Contract

All HTML outputs are static review artifacts. Bootstrap embeds data at
generation time; HTML must not write approval state. Approval state lives only
in `.allforai/game-design/approval-records.json`.

Per-node layout details belong to mapped sub-skills. `review-dashboard.html` is
the live approval dashboard generated during bootstrap. `game-design-dashboard.html`
is the final overview generated by `game-design-finalize` and must at minimum
show node status, approval blockers, revision notes, and art/audio/system
readiness from `approval-records.json` and `game-design-doc.json`.

## Art Pipeline Delegation

`game-design.md` only declares art orchestration points. Concrete art methods
live in `skills/game-art/SKILL.md` and child skills.

| Stage | Orchestration rule |
|---|---|
| `art-direction` | Delegate to `game-art/10-design/art-direction-input-contract`. |
| `art-concept` | Auto-triggered by `/run`; writes `.allforai/game-design/art-pipeline-config.json` and delegates concept alignment review to `game-art/10-design/art-concept-validation`. |
| `art-spec-design` | Delegate to `game-art/00-env/asset-registry` and asset spec skills. |
| role art-gen nodes | Selected from `art-pipeline-config.json.active_nodes` by bootstrap. |
| `art-qa` | Delegate to `game-art/40-qa/art-preview-qa` plus specialized QA/import skills, ending with `game-art/40-qa/engine-ready-art-output-contract`. |

The orchestration invariant is simple: generated or sourced art cannot be
treated as accepted unless the relevant game-art QA/import skill returns a
validated status. Missing tools, missing images, placeholder-only output, or
unrunnable import checks must surface as blocking validation failures, not as
substitute evidence.

Before bulk asset generation, art concept validation must produce
`.allforai/game-design/art/art-concept-validation.html` and
`.allforai/game-design/art/art-concept-validation.json`. The HTML is the
human-readable Chinese review gate for product/game concept alignment, visual
pillars, UI/world consistency, risk flags, and human preference decisions.

Program implementation consumes art through
`.allforai/game-runtime/art/engine-ready-art-manifest.json`, produced by
`game-art/40-qa/engine-ready-art-output-contract`. Runtime nodes must use
manifest `runtime_id` and `asset_id` references rather than raw generated paths.
Playable client assembly, scene binding, HUD binding, input/camera binding, and
runtime screenshot validation belong to `game-frontend`.

## game-design-doc.json Schema

`game-design-finalize` produces `.allforai/game-design/game-design-doc.json`
by aggregating all approved system JSONs. It also produces the handoff artifacts
listed in §Finalize Exit Artifacts. Only include fields whose source JSON exists
(skip missing optional nodes).

```json
{
  "game_title": "<string>",
  "scenario": "<casual-mobile | action-rpg | multiplayer-online | roguelike | strategy-sim | narrative-adventure>",
  "design_version": "<semver string>",
  "generated_at": "<ISO 8601>",
  "player_roles": [
    { "role_id": "<string>", "archetype": "<string>", "motivation": "<string>", "pain_points": ["<string>"] }
  ],
  "core_loop": { "$ref": "systems/core-mechanics.json" },
  "systems": [
    {
      "system_id": "<node_id from canonical registry>",
      "system_name": "<display name>",
      "json_path": "<relative path under .allforai/game-design/systems/>",
      "gate_status": "approved"
    }
  ],
  "economy": {
    "currencies": ["<string>"],
    "balance_targets": { "<dimension>": "<target range>" },
    "sink_source_summary": "<string>"
  },
  "progression": {
    "max_level": "<number | null>",
    "curve_type": "<linear | exponential | sigmoid | custom>",
    "meta_unlocks": ["<string>"]
  },
  "narrative": {
    "story_acts": "<number | null>",
    "branching_depth": "<number | null>",
    "endings_count": "<number | null>"
  },
  "worldbuilding": {
    "setting": "<brief setting description | null>",
    "factions_count": "<number | null>",
    "key_locations_count": "<number | null>",
    "lore_file": "game-design/systems/worldbuilding-bible.md"
  },
  "art": {
    "style_id": "<string from art-style-guide.json>",
    "asset_count": "<number>",
    "placeholder_count": "<number>",
    "temp_count": "<number>",
    "alpha_count": "<number>",
    "final_count": "<number>"
  },
  "audio": {
    "music_tracks": "<number | null>",
    "sfx_events": "<number | null>"
  },
  "approval_summary": {
    "total_nodes": "<number>",
    "approved": "<number>",
    "pending": "<number>",
    "revision_requested": "<number>"
  }
}
```

`product-analysis` reads: `player_roles[]`, `systems[]`, `core_loop`,
`progression`, and `.allforai/game-design/design/program-development-node-handoff.json`.
`demo-forge` reads: `progression`, `economy.currencies`.
`quality-checks` reads: `economy.balance_targets`, `audio.sfx_events`, `art` counts.
`generate-artifacts` reads: `systems[]` for code generation targets.

## Downstream Consumers

| Capability | Reads | Uses |
|-----------|-------|------|
| `product-analysis` | `.allforai/game-design/game-design-doc.json`, `.allforai/game-design/design/program-development-node-handoff.json` | Concept baseline plus implementation-node seed; `player_roles` → `role-profiles.json`; `systems[]` and `implementation_nodes[]` → task-inventory |
| `ui-design` | `.allforai/game-design/art-style-guide.json`, `.allforai/game-design/game-design-doc.json` | Design tokens from art direction; game screens (HUD, menus, inventory, dialogue) |
| `demo-forge` | `.allforai/game-design/art-asset-inventory.json`, `.allforai/game-design/game-design-doc.json` `.progression` | Player save data at progression stages using available art state |
| `quality-checks` | `.allforai/game-design/game-design-doc.json` `.economy.balance_targets`, `.allforai/game-design/systems/audio-design.json.sfx_catalogue[].milestone_gate` | Numerical QA; art-agnostic check; milestone gate check; audio milestone check |
| `generate-artifacts` | `.allforai/game-design/game-design-doc.json` `.systems[]` | Code generation targets; must implement Asset Registry |
| `product-verify` | `.allforai/game-design/game-design-doc.json` | Verifies implementation against game design spec; checks all `systems[]` were implemented |
| `concept-acceptance` | `.allforai/game-design/game-design-doc.json` | Post-implementation concept fitness check; compares shipped game systems against original concept |
| `launch-prep` | `.allforai/game-design/game-design-doc.json` | Competitive research context (what systems does this game have?); monetization model for pricing research |

## Composition Hints

### Full Pipeline (new game from scratch)
All nodes for detected scenario. `art-direction` + `art-concept`(skill，自动调起) +
`art-spec-design` + `[art-gen nodes from active_nodes]` + `art-qa` +
`game-design-finalize` always appended.

**art-gen nodes** are determined by `art-pipeline-config.json.active_nodes` at art-concept
completion time. Bootstrap writes only the listed nodes into `workflow.json`.
Every art-gen node requires human approval gate (discipline-specific).

**Dependency rule for `game-design-finalize`:** Set `blocked_by` = ALL other game-design
nodes in the scenario (not just the preceding node). Finalize aggregates every system JSON;
it must not run until all upstream nodes are approved. Upstream nodes may run in parallel
after `core-loop-design` — finalize waits for all of them.

### Partial Pipeline (existing game, adding feature)
Read `approval-records.json`. For each node with `gate_status == "approved"`:
skip generating a new node-spec for it — the approved output still stands.
Only generate node-specs for nodes that are `pending`, `in-review`, `revision-requested`,
or **absent from the approval records** (newly added node for the feature).

Bootstrap identifies the minimum set of nodes that need re-running:
1. The node whose design is changing (the feature being added/modified)
2. Any node whose output references data from the changed node
3. `game-design-finalize` always re-runs (to produce an updated `game-design-doc.json` and handoff artifacts)

Example: Adding ranked PvP mode → only `competitive-balance-design` + `game-design-finalize` need re-running if all other nodes are approved.

### Skip Entirely
Game SDK / engine projects, CLI game tools, non-game projects.

---

## Concept Visualization Integration

> 引用协议：`knowledge/capabilities/concept-visualization.md`（phase-id = `game-design`）

**启动：** 游戏设计阶段第一个节点（通常是 `core-loop-design`）开始执行前，调用「工具层：启动序列」（phase-id = `game-design`）。

**跨 session 累积：** game-design 分多次 `/run` 执行（各节点之间有 human_gate 暂停）。
`conclusion-kanban.html` 和 `mindmap.html` 跨 session 累积：每次 `/run` 启动时检查文件是否存在，若存在则读取已有内容继续追加。
`wireframes.html` 每次 session 重置（总是重写初始模板后再按触发规则生成新线框）。

**各节点执行完成且 human_gate 通过后** 调用「工具层：结论更新序列」：

| 节点 | 目标看板列 slug | 线框触发 |
|---|---|---|
| `core-loop-design` | `wanfa` | **低保真**（此节点完成时触发，内容：HUD草图+关卡布局草图） |
| `economy-design` | `jingji` | — |
| `progression-design` | `chengzhang` | — |
| `narrative-design` | `xushi` | — |
| `art-direction` | `meishu` | **中保真**（此节点完成时触发，内容：完整游戏UI层级线框） |

game-design 思维导图使用**结论节点**（fill: `#744210`，橙色）表示关键设计决策，区分于普通结构节点。

**结束：** 所有游戏设计节点完成（`game-design-finalize` 通过 human_gate）后，调用「工具层：结束序列」。
