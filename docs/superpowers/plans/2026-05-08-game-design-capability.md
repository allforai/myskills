# Game Design Capability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `game-design` capability to meta-skill so that bootstrap generates game-type-specific design nodes with HTML output, human approval gates, art substitution pipeline, and AI image generation.

**Architecture:** Three new files + one bootstrap.md modification. `game-design.md` is the execution-layer capability (HTML specs, gate protocol, art pipeline); six `game-scenario-templates/*.json` files tell bootstrap which nodes to inject per game genre; `bootstrap.md` gains game engine detection + game-design node injection logic. All existing capabilities and `gaming.md` domain knowledge are untouched.

**Tech Stack:** Markdown (capability files), JSON (scenario templates), Bash (validation)

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `claude/meta-skill/knowledge/capabilities/game-design.md` | Execution layer: HTML specs, gate protocol, art substitution, AI gen, team roles, canonical node registry |
| Create | `claude/meta-skill/knowledge/game-scenario-templates/casual-mobile.json` | Node set for hyper-casual / mid-core mobile |
| Create | `claude/meta-skill/knowledge/game-scenario-templates/action-rpg.json` | Node set for action / card / RPG |
| Create | `claude/meta-skill/knowledge/game-scenario-templates/multiplayer-online.json` | Node set for MMO / MOBA / FPS |
| Create | `claude/meta-skill/knowledge/game-scenario-templates/roguelike.json` | Node set for roguelike / roguelite |
| Create | `claude/meta-skill/knowledge/game-scenario-templates/strategy-sim.json` | Node set for strategy / sim |
| Create | `claude/meta-skill/knowledge/game-scenario-templates/narrative-adventure.json` | Node set for narrative / AVG |
| Modify | `claude/meta-skill/skills/bootstrap.md` | Add: LÖVE2D/Bevy detection, game scenario Step 1.5 branch, bootstrap-profile fields, Step 3.1 game-design injection |

---

## Task 1: Create `game-design.md` Capability

**Files:**
- Create: `claude/meta-skill/knowledge/capabilities/game-design.md`

- [ ] **Step 1: Write the file**

```markdown
---
name: game-design
description: >
  Game Design Document (GDD) capability for game projects. Generates HTML-first,
  human-reviewed design nodes for core loop, combat systems, economy, narrative,
  art direction, and art asset specs. Activated by bootstrap when a game engine is
  detected. All nodes require discipline-specific human approval before proceeding.
---

# Game Design Capability

> Execution layer for game project design. Reads domain knowledge from
> `${CLAUDE_PLUGIN_ROOT}/knowledge/domains/gaming.md`. Adds HTML outputs,
> human gate protocol, art substitution pipeline, and AI image generation.

## Goal

Bridge `product-concept` (vision) and `generate-artifacts` (code) with
domain-specific game design documentation. Each node outputs a static HTML
for human review and a JSON artifact for downstream consumption.

## Knowledge Layer Reference

This capability is the **execution layer** over `domains/gaming.md`:

| Layer | File | Responsibility |
|-------|------|----------------|
| Knowledge | `domains/gaming.md` | Node definitions, theory anchors, artifact content, genre node selection |
| Execution | `capabilities/game-design.md` (this file) | HTML output specs, human gate protocol, art substitution, AI image generation, team role assignment |

Bootstrap reads both files when generating node-specs for game projects:
- From `gaming.md`: node content methodology and artifact schemas
- From this file: execution layer rules (HTML paths, gate protocol, art pipeline)

## Trigger Conditions

Bootstrap activates this capability when:
- Game engine detected: `project.godot`, `*.uproject` + `Source/`, `Assets/` +
  `ProjectSettings/ProjectVersion.txt`, `*.love`, `Cargo.toml` + bevy dependency
- OR `bootstrap-profile.json.business_domain = "gaming"`
- OR user selects game domain in Step 1.5

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
  ├─ art-direction
  ├─ art-spec-design
  └─ ai-art-generation  (automatic node, no human gate)
  ↓
product-analysis  (reads game-design-doc.json as concept baseline)
  ↓
generate-artifacts
```

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

### HTML Output (v1: Static)

Every game-design node generates a **static HTML file** as primary output.
HTML files are read-only display documents — no JavaScript writes back.
Approval state is tracked in `.allforai/game-design/approval-records.json`.

### Approval Records Schema

`/run` reads this file to determine gate status before advancing:

```json
{
  "records": [
    {
      "node_id": "<node_id from Canonical Node Registry>",
      "gate_status": "pending | in-review | approved | revision-requested",
      "discipline_owner": "<role_id>",
      "approved_by": [],
      "revision_notes": "",
      "approved_at": null,
      "unblocks": ["<downstream_node_id>"]
    }
  ]
}
```

Gate rules:
- `gate_status == "approved"` → unlock all `unblocks[]` nodes
- `gate_status == "revision-requested"` → re-execute node with `revision_notes` as instruction
- `discipline_owner` must approve; `discipline_reviewers` approval is advisory

Bootstrap initialises this file with one `pending` record per game-design node when
writing node-specs to `.allforai/bootstrap/`.

### Node-Spec Extension Fields

Every game-design node-spec adds these fields beyond standard node-spec schema:

```json
{
  "discipline_owner": "<role_id>",
  "discipline_reviewers": ["<role_id>"],
  "html_output": ".allforai/game-design/<filename>.html",
  "json_output": ".allforai/game-design/systems/<artifact>.json",
  "human_gate": true,
  "gate_approval_rule": "discipline_owner must approve; reviewers approval is advisory",
  "approval_record_path": ".allforai/game-design/approval-records.json",
  "gate_status": "pending",
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
| `economy-design` | `numeric-designer` | `game-design/economy.html` | `game-design/systems/economy-model.json` | economy-design |
| `narrative-design` | `narrative-designer` | `game-design/narrative.html` | `game-design/systems/narrative-design.json` | narrative-design |
| `level-design` | `level-designer` | `game-design/level-design.html` | `game-design/systems/level-design.json` | level-design |
| `worldbuilding` | `narrative-designer` | `game-design/worldbuilding.html` | `game-design/systems/worldbuilding-bible.md` | worldbuilding |
| `network-architecture-design` | `backend-programmer` | `game-design/network-arch.html` | `game-design/systems/network-architecture.json` | (Step 2.7 research) |
| `matchmaking-design` | `backend-programmer` | `game-design/matchmaking.html` | `game-design/systems/matchmaking.json` | (Step 2.7 research) |
| `competitive-balance-design` | `numeric-designer` | `game-design/competitive-balance.html` | `game-design/systems/balance-report.json` | balance-testing |
| `run-structure-design` | `lead-designer` | `game-design/run-structure.html` | `game-design/systems/run-structure.json` | core-mechanics-design |
| `meta-progression-design` | `systems-designer` | `game-design/meta-progression.html` | `game-design/systems/meta-progression.json` | progression-system |
| `procedural-gen-spec` | `gameplay-programmer` | `game-design/procedural-gen.html` | `game-design/systems/procedural-gen.json` | (engine specialisation) |
| `ai-faction-design` | `ai-programmer` | `game-design/ai-faction.html` | `game-design/systems/ai-faction.json` | core-mechanics-design |
| `tech-tree-design` | `systems-designer` | `game-design/tech-tree.html` | `game-design/systems/tech-tree.json` | progression-system |
| `branching-structure-design` | `narrative-designer` | `game-design/branching-structure.html` | `game-design/systems/branching-structure.json` | narrative-design |
| `character-arc-design` | `narrative-designer` | `game-design/character-arc.html` | `game-design/systems/character-arc.json` | narrative-design |
| `art-direction` | `art-director` | `game-design/art-direction.html` | `game-design/art-style-guide.json` | art-direction |
| `art-spec-design` | `concept-artist` | `game-design/art-spec.html` | `game-design/art-asset-inventory.json` | art-direction |
| `ai-art-generation` | _(automatic — no discipline_owner)_ | _(updates art-direction.html)_ | updates `art-asset-inventory.json` | — |

## HTML Presentation Specs

All HTML outputs are **static** (v1). Bootstrap embeds data at generation time.

### `game-design-dashboard.html`
- **Audience:** producer, lead-designer
- **Goal:** 5-second status overview — see what needs attention
- **Layout:** Tab navigation by discipline (Design / Art / Engineering / Audio)
- **Required content:** node status badges (pending/in-review/approved/revision-requested) + discipline + last-updated; art progress heatmap (placeholder/temp/alpha/final counts per type); milestone completion gauge (gate-ready assets / total)

### `core-loop.html`
- **Audience:** lead-designer
- **Above fold:** SVG loop diagram — Primary → Secondary → Tertiary with duration labels
- **Expanded:** Design intent (2-3 sentences, gameplay language, not spec language)
- **Decision callouts:** ⚠️ warning blocks for unresolved design choices with option comparison

### `combat-system.html`
- **Audience:** combat-designer (primary), gameplay-programmer (secondary)
- **Layout:** Two-column — left: gameplay language; right: technical spec
- **Above fold:** System overview + 3 key design decisions (one decision per callout)
- **Expanded:** Sortable skill table (columns: name / damage-multiplier / cooldown / cost / range / status-effect)
- **Expanded:** SVG state machine diagram (node = state, edge = transition + condition)
- **Collapsed:** Full formulas, edge cases, boundary conditions

### `economy-design.html`
- **Audience:** numeric-designer
- **Above fold:** Sankey chart — currency sources → pool → sinks (edge width = volume)
- **Expanded:** Growth curve line chart (X: level, Y: value; tab-switch dimensions: XP/ATK/DEF/economy)
- **Expanded:** Balance thresholds — ⚠️ highlight on values that need designer confirmation
- **Collapsed:** Full parameter tables (numeric, sortable)

### `art-direction.html`
- **Audience:** art-director
- **Rule:** Image-first. Maximum 3 consecutive lines of text anywhere on page.
- **Above fold:** Mood image (full-width)
- **Below:** Color palette swatches (hex + role label) + forbidden styles (tag chips)
- **Below:** Reference works (thumbnail row, labelled)
- **Below:** AI-generated drafts (2×2 grid, click to enlarge)

### `art-spec-design.html`
- **Audience:** each art discipline (filter to own assets)
- **Layout:** Filterable card grid — filter by discipline / type / state
- **Each card:** ID + name + dimensions + description + palette constraint chips + milestone gate + AI-gen preview if available + approval status

### `narrative-structure.html`
- **Audience:** narrative-designer
- **Above fold:** Interactive SVG story tree (nodes expandable on click, colour = act)
- **Expanded:** Emotional arc line chart (X: story progress %, Y: intensity; annotate peaks / valleys / reversals)
- **Expanded:** Character arc timeline (horizontal, one row per character)
- **Collapsed:** Dialogue node detail (click to expand per node)

## Art Substitution Pipeline

### Four States (formal milestones, not workarounds)

| State | Content | Code / Demo usable |
|-------|---------|-------------------|
| `placeholder` | Geometry / solid color / text label | ✅ always |
| `temp` | AI-generated image or free asset | ✅ demo / test |
| `alpha` | First human art pass | ✅ Alpha milestone |
| `final` | Ship quality | ✅ Release |

### Default Substitution Rules

- `character`: Capsule geometry, name label on head
- `environment`: Whitebox geometry, functional zones in distinct solid colors
- `animation`: Position tween, no skeletal animation
- `vfx`: Single-color particle burst (white circle)
- `ui-icon`: Rounded rectangle + icon name text
- `ui-bg`: Solid color + game title text
- `audio-sfx`: 440 Hz sine (hit) / 200 Hz (damage received) / 880 Hz (level-up)
- `audio-bgm`: Silent OR CC0 library track

### Milestone Gate Rules

- **Alpha:** all `milestone_gate = "alpha"` assets must reach `alpha` state
- **Beta:** all `milestone_gate = "beta"` assets must reach `alpha` state (beta allowed to lag)
- **Release:** all assets must reach `final` state
- `demo-forge` and `product-verify` execute at any art state — never blocked by missing final art

### Art-Agnostic Code Constraint

`generate-artifacts` node-spec MUST include:
> Code references assets via an Asset Registry (ID → path lookup). Hardcoded asset paths are prohibited. Path resolved from `art-asset-inventory.json.assets[].substitution[current_state]` at runtime.

`quality-checks` adds scan: detect hardcoded asset paths that bypass Asset Registry.

## AI Art Generation

### Trigger

Automatically triggered after `art-direction` node reaches `gate_status = "approved"`.
`ai-art-generation` has no `human_gate` — it runs and updates the dashboard on completion.

### Prompt Construction

```
final_prompt = art_style_guide.style_prompt_prefix
             + ", " + asset.art_spec.description
             + ", " + target_suffix[asset.ai_gen_target]

target_suffix:
  "concept-reference" → "character concept sheet, front side back views, white background"
  "actual-asset"      → "game UI icon, isolated, transparent background, no shadow"
  "mood-reference"    → "environment concept art, cinematic composition, dramatic lighting"
```

### Tool Priority (requires ai-gateway MCP configured)

1. `mcp__plugin_meta-skill_ai-gateway__flux_generate_image` (FLUX Pro)
2. `mcp__plugin_meta-skill_ai-gateway__generate_image` (Google Imagen 4)
3. `mcp__plugin_meta-skill_ai-gateway__openrouter_generate_image`

**Degradation:** If none available → keep `placeholder` state, embed spec text + size frame
in HTML. Set `ai_generatable = true` for future re-run. Never block pipeline.

### State Update After Generation

- `ai_gen_target = "actual-asset"` → `current_state: placeholder → temp`; write image path to `substitution.temp`
- `ai_gen_target = "concept-reference" | "mood-reference"` → `current_state` stays `placeholder`; record path in `ai_generated.path` (reference only, not ingested into game)

## Downstream Consumers

| Capability | Reads | Uses |
|-----------|-------|------|
| `product-analysis` | `game-design-doc.json` | Concept baseline; `player_roles` → `role-profiles.json`; `systems[]` → task-inventory in system-spec format |
| `ui-design` | `art-style-guide.json`, `game-design-doc.json` | Design tokens from art direction; game screens (HUD, menus, inventory, dialogue) |
| `demo-forge` | `art-asset-inventory.json`, `game-design-doc.json.progression` | Player save data at progression stages using available art state |
| `quality-checks` | `game-design-doc.json.economy.balance_targets` | Numerical QA; art-agnostic check; milestone gate check |
| `generate-artifacts` | `game-design-doc.json.systems[]` | Code generation targets; must implement Asset Registry |

## Composition Hints

### Full Pipeline (new game from scratch)
All nodes for detected scenario. `art-direction` + `art-spec-design` + `ai-art-generation`
always appended. Every node requires human approval gate.

### Partial Pipeline (existing game, adding feature)
Skip `core-loop-design` and `art-direction` if both have `approved` records.
Start from the system node being modified.

### Skip Entirely
Game SDK / engine projects, CLI game tools, non-game projects.
```

- [ ] **Step 2: Verify file is valid (check YAML frontmatter and required sections)**

```bash
# Verify frontmatter exists
head -10 claude/meta-skill/knowledge/capabilities/game-design.md

# Verify all 25 node_ids in canonical table are present
grep -c '`core-loop-design`\|`ftue-design`\|`monetization-design`\|`combat-system-design`\|`economy-design`\|`art-direction`\|`art-spec-design`\|`ai-art-generation`' \
  claude/meta-skill/knowledge/capabilities/game-design.md
```

Expected: frontmatter shows `name: game-design`; grep count ≥ 8 (spot-check key IDs).

- [ ] **Step 3: Commit**

```bash
git add claude/meta-skill/knowledge/capabilities/game-design.md
git commit -m "feat: add game-design capability (execution layer over gaming.md)"
```

---

## Task 2: Create 6 Game Scenario Template JSONs

**Files:**
- Create: `claude/meta-skill/knowledge/game-scenario-templates/casual-mobile.json`
- Create: `claude/meta-skill/knowledge/game-scenario-templates/action-rpg.json`
- Create: `claude/meta-skill/knowledge/game-scenario-templates/multiplayer-online.json`
- Create: `claude/meta-skill/knowledge/game-scenario-templates/roguelike.json`
- Create: `claude/meta-skill/knowledge/game-scenario-templates/strategy-sim.json`
- Create: `claude/meta-skill/knowledge/game-scenario-templates/narrative-adventure.json`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p claude/meta-skill/knowledge/game-scenario-templates
```

- [ ] **Step 2: Write `casual-mobile.json`**

```json
{
  "scenario_id": "casual-mobile",
  "display_name_zh": "超休闲/中度手游",
  "display_name_en": "Casual / Mid-core Mobile",
  "description": "Mobile-first games: hyper-casual, mid-core, card, idle, merge",
  "gaming_md_emphasis": ["core-mechanics-design", "monetization-design", "progression-system", "level-design"],
  "required_nodes": [
    "core-loop-design",
    "ftue-design",
    "monetization-design"
  ],
  "optional_nodes": [
    "retention-hook-design",
    "meta-game-design"
  ],
  "always_include": [
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ],
  "node_order": [
    "core-loop-design",
    "ftue-design",
    "monetization-design",
    "retention-hook-design",
    "meta-game-design",
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ]
}
```

- [ ] **Step 3: Write `action-rpg.json`**

```json
{
  "scenario_id": "action-rpg",
  "display_name_zh": "动作/卡牌/RPG",
  "display_name_en": "Action / Card / RPG",
  "description": "Action games, card games, role-playing games with progression and combat",
  "gaming_md_emphasis": ["core-mechanics-design", "economy-design", "progression-system", "narrative-design", "level-design", "balance-testing"],
  "required_nodes": [
    "core-loop-design",
    "combat-system-design",
    "skill-tree-design",
    "progression-curve-design",
    "economy-design"
  ],
  "optional_nodes": [
    "narrative-design",
    "level-design",
    "worldbuilding"
  ],
  "always_include": [
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ],
  "node_order": [
    "core-loop-design",
    "combat-system-design",
    "skill-tree-design",
    "progression-curve-design",
    "economy-design",
    "narrative-design",
    "level-design",
    "worldbuilding",
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ]
}
```

- [ ] **Step 4: Write `multiplayer-online.json`**

```json
{
  "scenario_id": "multiplayer-online",
  "display_name_zh": "在线多人游戏",
  "display_name_en": "Multiplayer Online (MMO / MOBA / FPS)",
  "description": "Online multiplayer games: MMO, MOBA, FPS, battle royale, co-op",
  "gaming_md_emphasis": ["core-mechanics-design", "balance-testing", "player-archetype-definition", "monetization-design"],
  "required_nodes": [
    "core-loop-design",
    "network-architecture-design",
    "matchmaking-design",
    "competitive-balance-design"
  ],
  "optional_nodes": [
    "social-system-design",
    "anti-cheat-design",
    "live-ops-design"
  ],
  "always_include": [
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ],
  "node_order": [
    "core-loop-design",
    "network-architecture-design",
    "matchmaking-design",
    "competitive-balance-design",
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ],
  "bootstrap_note": "social-system-design, anti-cheat-design, live-ops-design not in canonical node registry — bootstrap uses Step 2.7 research to generate ad-hoc node-specs for these when selected"
}
```

- [ ] **Step 5: Write `roguelike.json`**

```json
{
  "scenario_id": "roguelike",
  "display_name_zh": "肉鸽/Roguelite",
  "display_name_en": "Roguelike / Roguelite",
  "description": "Run-based games with procedural generation and meta-progression",
  "gaming_md_emphasis": ["core-mechanics-design", "progression-system", "economy-design", "balance-testing"],
  "required_nodes": [
    "core-loop-design",
    "run-structure-design",
    "meta-progression-design",
    "procedural-gen-spec"
  ],
  "optional_nodes": [
    "build-variety-design"
  ],
  "always_include": [
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ],
  "node_order": [
    "core-loop-design",
    "run-structure-design",
    "meta-progression-design",
    "procedural-gen-spec",
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ],
  "bootstrap_note": "build-variety-design not in canonical node registry — bootstrap generates ad-hoc node-spec when selected"
}
```

- [ ] **Step 6: Write `strategy-sim.json`**

```json
{
  "scenario_id": "strategy-sim",
  "display_name_zh": "策略/模拟经营",
  "display_name_en": "Strategy / Simulation",
  "description": "Strategy games, city builders, tycoon, 4X, tower defense",
  "gaming_md_emphasis": ["economy-design", "core-mechanics-design", "progression-system", "balance-testing"],
  "required_nodes": [
    "core-loop-design",
    "economy-design",
    "ai-faction-design",
    "tech-tree-design"
  ],
  "optional_nodes": [
    "map-generation-spec"
  ],
  "always_include": [
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ],
  "node_order": [
    "core-loop-design",
    "economy-design",
    "ai-faction-design",
    "tech-tree-design",
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ],
  "bootstrap_note": "map-generation-spec not in canonical node registry — bootstrap generates ad-hoc node-spec when selected"
}
```

- [ ] **Step 7: Write `narrative-adventure.json`**

```json
{
  "scenario_id": "narrative-adventure",
  "display_name_zh": "叙事/视觉小说/AVG",
  "display_name_en": "Narrative / Visual Novel / Adventure",
  "description": "Story-driven games: visual novels, point-and-click adventures, interactive fiction",
  "gaming_md_emphasis": ["narrative-design", "worldbuilding", "art-direction"],
  "required_nodes": [
    "core-loop-design",
    "narrative-design",
    "branching-structure-design",
    "character-arc-design"
  ],
  "optional_nodes": [
    "dialogue-system-spec"
  ],
  "always_include": [
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ],
  "node_order": [
    "core-loop-design",
    "narrative-design",
    "branching-structure-design",
    "character-arc-design",
    "art-direction",
    "art-spec-design",
    "ai-art-generation"
  ],
  "bootstrap_note": "dialogue-system-spec not in canonical node registry — bootstrap generates ad-hoc node-spec when selected"
}
```

- [ ] **Step 8: Validate all JSON files are syntactically valid**

```bash
for f in claude/meta-skill/knowledge/game-scenario-templates/*.json; do
  echo -n "Checking $f ... "
  python3 -m json.tool "$f" > /dev/null && echo "OK" || echo "INVALID"
done
```

Expected output: 6 lines, each ending in `OK`.

- [ ] **Step 9: Commit**

```bash
git add claude/meta-skill/knowledge/game-scenario-templates/
git commit -m "feat: add 6 game scenario templates (casual-mobile, action-rpg, multiplayer-online, roguelike, strategy-sim, narrative-adventure)"
```

---

## Task 3: Modify `bootstrap.md`

**Files:**
- Modify: `claude/meta-skill/skills/bootstrap.md`

Three targeted edits. Read the file before each edit to confirm line context.

- [ ] **Step 1: Add LÖVE2D and Bevy detection to Step 1.1**

Find the existing game engine block (around line 68):
```
**Game engines:**
- ProjectSettings/ProjectVersion.txt, Assets/ (Unity)
- *.uproject, Source/ (Unreal Engine)
- project.godot (Godot)
```

Replace with:
```
**Game engines:**
- ProjectSettings/ProjectVersion.txt, Assets/ (Unity)
- *.uproject, Source/ (Unreal Engine)
- project.godot (Godot)
- *.love (LÖVE2D)
- Cargo.toml with `bevy` in dependencies (Bevy/Rust)
```

- [ ] **Step 2: Add `is_game_project` + `game_scenario` to Step 1.5**

Find the `**If no code exists**` block in Step 1.5. After the `4. 业务领域：` line that lists `f) 游戏`, add a new conditional block immediately BEFORE the `**Goal mapping**` section:

```markdown
**If business_domain = "gaming" (detected or user-selected):**

After confirming the main goal, ask ONE additional question:

```
游戏品类（选一）：
   a) 超休闲/中度手游 (casual-mobile)
   b) 动作/卡牌/RPG (action-rpg)
   c) 在线多人 MMO/MOBA/FPS (multiplayer-online)
   d) 肉鸽/Roguelite (roguelike)
   e) 策略/模拟经营 (strategy-sim)
   f) 叙事/视觉小说/AVG (narrative-adventure)
```

Map answer to `game_scenario` field in bootstrap-profile.json.
If user is unsure, suggest `action-rpg` as default (broadest node set).
```

- [ ] **Step 3: Add `is_game_project` and `game_scenario` fields to Step 1.6 bootstrap-profile.json schema**

Find the `bootstrap-profile.json` code block in Step 1.6. After the `"complexity_estimate"` line, add:

```json
  "is_game_project": false,
  "game_scenario": "casual-mobile | action-rpg | multiplayer-online | roguelike | strategy-sim | narrative-adventure | null"
```

- [ ] **Step 4: Add game-design node injection to Step 3.1**

Find the paragraph in Step 3.1 that begins:
```
**There is no fixed template.** A game project might have nodes for
"design-economy-system" and "balance-test-combat".
```

Add this block immediately AFTER that paragraph:

```markdown
**Game project node injection (when `is_game_project = true`):**

1. Read `${CLAUDE_PLUGIN_ROOT}/knowledge/game-scenario-templates/${game_scenario}.json`
2. Read `${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/game-design.md` §Canonical Node Registry
3. Insert game-design nodes into the workflow AFTER `product-concept` node and BEFORE `product-analysis` node
4. For each node in `required_nodes` + `always_include` (and selected `optional_nodes`):
   - Look up `node_id` in game-design.md Canonical Node Registry
   - Generate node-spec with: `capability: game-design`, `discipline_owner`, `html_output`, `json_output`, `human_gate: true`, `approval_record_path: ".allforai/game-design/approval-records.json"`, `gate_status: "pending"`, `presentation` spec from game-design.md §HTML Presentation Specs
   - `blocked_by`: previous node in `node_order`
   - `unlocks`: next node in `node_order`
5. Initialise `.allforai/game-design/approval-records.json` with one `pending` record per game-design node
6. Ad-hoc nodes (listed in `bootstrap_note` of the scenario template): generate node-spec with `capability: game-design`, but use Step 2.7 research for content — they are not in the canonical registry
```

- [ ] **Step 5: Verify bootstrap.md changes read coherently**

```bash
# Confirm all four additions are present
grep -n "LÖVE2D\|is_game_project\|game_scenario\|game-design node injection" \
  claude/meta-skill/skills/bootstrap.md
```

Expected: 4+ matches across the 4 insertion points.

- [ ] **Step 6: Commit**

```bash
git add claude/meta-skill/skills/bootstrap.md
git commit -m "feat: bootstrap — add game engine detection, game scenario selection, game-design node injection"
```

---

## Task 4: Cross-Reference Validation

**Files:**
- Create (temp, not committed): `scripts/validate-game-nodes.py`

- [ ] **Step 1: Write validation script**

```python
#!/usr/bin/env python3
"""Validate game-design node cross-references across capability and scenario templates."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent / "claude/meta-skill/knowledge"
CAPABILITY = ROOT / "capabilities/game-design.md"
TEMPLATES_DIR = ROOT / "game-scenario-templates"

VALID_ROLES = {
    "lead-designer", "combat-designer", "systems-designer", "narrative-designer",
    "level-designer", "numeric-designer", "monetization-designer", "ux-designer",
    "gameplay-programmer", "backend-programmer", "ui-programmer", "ai-programmer",
    "graphics-programmer", "tools-programmer",
    "art-director", "concept-artist", "ui-artist", "character-modeler",
    "environment-artist", "animator", "vfx-artist", "technical-artist",
    "audio-director", "producer",
}

errors = []

# 1. Extract canonical node_ids from game-design.md
capability_text = CAPABILITY.read_text()
# Match rows like: | `core-loop-design` | ...
node_ids_in_capability = set(re.findall(r'`([a-z][a-z0-9-]+)`', capability_text))
# Filter to only IDs that appear in the canonical table rows
table_lines = [l for l in capability_text.splitlines() if l.startswith("| `")]
canonical_ids = set()
for line in table_lines:
    m = re.match(r'\| `([a-z][a-z0-9-]+)`', line)
    if m:
        canonical_ids.add(m.group(1))

print(f"Found {len(canonical_ids)} canonical node IDs in game-design.md")

# 2. Validate each scenario template
for tmpl_path in sorted(TEMPLATES_DIR.glob("*.json")):
    with open(tmpl_path) as f:
        tmpl = json.load(f)

    scenario_id = tmpl["scenario_id"]

    for field in ("required_nodes", "optional_nodes", "always_include", "node_order"):
        for node_id in tmpl.get(field, []):
            if node_id not in canonical_ids:
                # Check if it has a bootstrap_note (ad-hoc nodes are expected)
                if "bootstrap_note" not in tmpl:
                    errors.append(
                        f"[{scenario_id}] {field}: '{node_id}' not in canonical registry "
                        f"and no bootstrap_note present"
                    )

    print(f"  {scenario_id}: {len(tmpl['required_nodes'])} required + "
          f"{len(tmpl.get('optional_nodes', []))} optional + "
          f"{len(tmpl['always_include'])} always_include")

# 3. Check discipline_owner values in game-design.md canonical table
for line in table_lines:
    parts = [p.strip() for p in line.split("|") if p.strip()]
    if len(parts) >= 2:
        owner = parts[1].strip("`")
        if owner and owner != "automatic — no discipline_owner" and owner not in VALID_ROLES:
            errors.append(f"Canonical table: unknown role '{owner}' in line: {line[:60]}")

if errors:
    print(f"\n❌ {len(errors)} validation error(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\n✅ All cross-references valid")
```

- [ ] **Step 2: Run validation**

```bash
python3 scripts/validate-game-nodes.py
```

Expected output:
```
Found 25 canonical node IDs in game-design.md
  action-rpg: 5 required + 3 optional + 3 always_include
  casual-mobile: 3 required + 2 optional + 3 always_include
  multiplayer-online: 4 required + 3 optional + 3 always_include
  narrative-adventure: 4 required + 1 optional + 3 always_include
  roguelike: 4 required + 1 optional + 3 always_include
  strategy-sim: 4 required + 1 optional + 3 always_include

✅ All cross-references valid
```

If errors appear, fix the specific node_id or role name indicated.

- [ ] **Step 3: Final commit (validation script as dev tool)**

```bash
git add scripts/validate-game-nodes.py
git commit -m "chore: add game node cross-reference validator"
```

---

## Self-Review Checklist

**Spec coverage:**
- §2.3 (gaming.md inheritance) → Covered in Task 1 game-design.md §Knowledge Layer Reference
- §2.4 (Pipeline position) → Covered in Task 1 game-design.md §Pipeline Position
- §3 (Scenario templates) → Covered in Task 2 (6 JSON files)
- §3.1 (Canonical node registry) → Embedded in Task 1 game-design.md
- §4.1 (Node-spec extension fields) → Covered in Task 1 §Node Execution Protocol
- §4.2 (Team roles) → Covered in Task 1 §Team Roles
- §6.0 (v1 static HTML + approval-records.json) → Covered in Task 1 §Node Execution Protocol
- §6.1–6.7 (HTML presentation specs) → Covered in Task 1 §HTML Presentation Specs
- §7 (AI art generation) → Covered in Task 1 §AI Art Generation
- §8 (Art substitution) → Covered in Task 1 §Art Substitution Pipeline
- §9.1 (Bootstrap modifications) → Covered in Task 3 (4 specific edits)
- §10 (Implementation scope: 3 files + bootstrap) → Fully covered

**Placeholder scan:** No TBD / TODO / "implement later" / "similar to" present.

**Type consistency:** node_id values in Task 2 JSON files match the canonical table in Task 1 game-design.md (both drawn from spec §3.1). Role IDs in Task 1 §Team Roles match VALID_ROLES set in Task 4 validator.
