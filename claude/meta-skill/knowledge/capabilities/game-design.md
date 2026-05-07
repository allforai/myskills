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
game-design-finalize  (aggregates all system JSONs → game-design-doc.json; human gate: lead-designer)
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
| `game-design-finalize` | `lead-designer` | `game-design/game-design-dashboard.html` | `game-design/game-design-doc.json` | — |
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

### `narrative.html`
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
+ `game-design-finalize` always appended. Every node requires human approval gate
(except `ai-art-generation` which is automatic).

### Partial Pipeline (existing game, adding feature)
Skip `core-loop-design` and `art-direction` if both have `approved` records.
Start from the system node being modified.

### Skip Entirely
Game SDK / engine projects, CLI game tools, non-game projects.
