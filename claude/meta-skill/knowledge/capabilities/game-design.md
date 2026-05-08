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
| `worldbuilding` | `narrative-designer` | `game-design/worldbuilding.html` | `game-design/systems/worldbuilding-bible.md` _(Markdown — lore prose)_ | worldbuilding |
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
| `anti-cheat-design` | `backend-programmer` | `game-design/anti-cheat.html` | `game-design/systems/anti-cheat-design.json` | — |
| `dialogue-system-spec` | `gameplay-programmer` | `game-design/dialogue-system.html` | `game-design/systems/dialogue-system.json` | narrative-design |
| `audio-design` | `audio-director` | `game-design/audio-design.html` | `game-design/systems/audio-design.json` | — |
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

### `anti-cheat.html`
- **Audience:** backend-programmer (primary), lead-designer (secondary)
- **Above fold:** Threat model overview — table of cheat types (speed hack / memory edit / packet manipulation / account sharing) × severity (critical/high/medium) × detection difficulty
- **Expanded:** Detection methods per cheat type with false-positive rate estimate
- **Expanded:** Third-party middleware comparison (EAC / BattlEye / custom) with cost/coverage matrix
- **Collapsed:** Technical implementation spec, ban escalation ladder

### `dialogue-system.html`
- **Audience:** gameplay-programmer (primary), narrative-designer (secondary)
- **Layout:** Two-column — left: design spec (narrative-designer readable); right: technical schema (programmer readable)
- **Above fold:** Node type catalogue (dialogue / choice / condition / jump / event-trigger) with visual icons
- **Expanded:** Variable system — global/local/character-scoped flags, data types, default values
- **Expanded:** Branching rules — max depth, merge points, dead-end detection
- **Collapsed:** Script format reference (YAML/JSON/ink/.twee spec), localization key pattern

### `audio-design.html`
- **Audience:** audio-director
- **Rule:** Embed audio previews where possible (base64 short clips or waveform SVG placeholders)
- **Above fold:** Audio identity statement (2-3 sentences: genre, mood, key instruments, forbidden sounds)
- **Below:** Adaptive music system diagram — layers, triggers, crossfade rules
- **Below:** SFX catalogue table (event → file → loop? → 3D spatial? → priority) — sortable
- **Below:** Voice acting spec — languages, tone notes, character voice reference
- **Collapsed:** Full audio asset list with milestone gates

### `ftue.html`
- **Audience:** ux-designer (primary), lead-designer (secondary)
- **Above fold:** FTUE flow diagram — step-by-step first session (step name / goal / UI screen / skip-able?)
- **Expanded:** Drop-off risk table — each step with expected completion %, red-flag threshold
- **Expanded:** Tutorial gating rules — what feature unlocks at which step
- **Collapsed:** Copy spec (tutorial messages verbatim, with tone notes)

### `monetization.html`
- **Audience:** monetization-designer (primary), lead-designer (secondary)
- **Above fold:** Revenue model summary — IAP tiers / ad types / subscription — with price anchoring chart
- **Expanded:** Purchase funnel: impression → consideration → conversion → repeat; target rates per step
- **Expanded:** Whale / dolphin / minnow player archetype spend profiles
- **Collapsed:** Full IAP SKU table (id / label / price / value / unlock), A/B test candidates
- **Gacha/抽卡 supplement (include when revenue model = Gacha):** Pull rate table (rarity tier × base rate × soft-pity rate × hard-pity threshold); banner structure (featured/limited/standard pool, rate-up mechanic); expected pulls to threshold chart (X: pulls, Y: cumulative probability of getting featured item)

### `retention-hook.html`
- **Audience:** systems-designer
- **Above fold:** Hook loop diagram — trigger → action → reward → investment cycle (SVG)
- **Expanded:** Daily/weekly/monthly hook schedule grid (day × hook type × reward)
- **Expanded:** Push notification strategy — event types, copy examples, opt-out risk
- **Collapsed:** Competitor hook analysis table

### `meta-game.html`
- **Audience:** systems-designer
- **Above fold:** Meta-game layer map — what exists outside the core loop (collection / progression / social / seasonal)
- **Expanded:** Collection system — item catalogue structure, display screen layout
- **Expanded:** Progression systems above core loop — battle pass / season / mastery
- **Collapsed:** Long-term engagement curve (X: days played, Y: engagement score)

### `skill-tree.html`
- **Audience:** combat-designer
- **Above fold:** Visual skill tree graph (SVG) — nodes = skills, edges = unlock requirements, color = tier
- **Expanded:** Per-skill detail cards (name / cost / effect / scaling formula / cooldown / max-rank)
- **Expanded:** Build archetype summary — top 3-5 paths with playstyle label
- **Collapsed:** Full skill table sortable by tier / cost / effect type

### `progression-curve.html`
- **Audience:** numeric-designer
- **Above fold:** Multi-line chart — XP required per level, power growth, economy growth (X: level, Y: value; toggle dimensions)
- **Expanded:** Pacing table — expected hours per level band (1-10 / 11-30 / 31-max); ⚠️ alert if band > 8 hours
- **Expanded:** Soft-cap / hard-cap annotations on curve
- **Collapsed:** Full level table (level / XP threshold / reward / unlocks)

### `level-design.html`
- **Audience:** level-designer (primary), combat-designer (secondary)
- **Above fold:** World map or level selection overview (placeholder image with zone labels)
- **Expanded:** Per-level spec cards — objective / enemy composition / hazards / estimated duration / difficulty rating
- **Expanded:** Difficulty curve chart (X: level index, Y: difficulty score)
- **Collapsed:** Encounter tables, spawn rules, pacing notes

### `worldbuilding.html`
- **Audience:** narrative-designer
- **Above fold:** World overview card — setting, era, tone, 3-5 defining facts
- **Below:** Faction relationship diagram (SVG — nodes = factions, edges = relationship type + tension)
- **Below:** Geography map (placeholder image with region labels and lore notes)
- **Below:** Terminology glossary (term / meaning / usage context), collapsible
- **Collapsed:** Full lore documents (history, religion, magic/tech system rules)

### `network-arch.html`
- **Audience:** backend-programmer
- **Above fold:** Architecture diagram (SVG) — client / relay / game server / database topology with latency budgets
- **Expanded:** Message flow — client → server → client for key actions (move / attack / ability)
- **Expanded:** Tick rate spec, bandwidth estimate (bytes/s per player at peak), concurrent player target
- **Collapsed:** Failure modes and fallback behavior (disconnect / desync / server crash)

### `matchmaking.html`
- **Audience:** backend-programmer (primary), systems-designer (secondary)
- **Above fold:** Matchmaking algorithm flowchart (SVG) — skill bucket → lobby fill → timeout expansion
- **Expanded:** Rating system spec (ELO / MMR / TrueSkill) with formula and decay rules
- **Expanded:** Queue time target vs. match quality trade-off chart
- **Collapsed:** Edge cases (solo vs. group, cross-region, skill floor/ceiling)

### `competitive-balance.html`
- **Audience:** numeric-designer (primary), combat-designer (secondary)
- **Above fold:** Balance radar chart — key game metrics vs. target ranges (DPS / TTK / win-rate spread)
- **Expanded:** Per-entity stat table (hero/class/weapon; sortable by metric)
- **Expanded:** Win-rate heat map (entity A vs. entity B; ⚠️ flag > 55% win rate)
- **Collapsed:** Balance changelog template, patch cycle cadence

### `run-structure.html`
- **Audience:** lead-designer
- **Above fold:** Run flow diagram (SVG) — start → floors/encounters → boss → end (with branch types: elite / shop / rest / treasure)
- **Expanded:** Encounter type table (type / weight / difficulty band / rewards)
- **Expanded:** Run length spec — target time per floor, total run target, variance range
- **Collapsed:** Seed / procedural rules that determine branch probabilities

### `meta-progression.html`
- **Audience:** systems-designer
- **Above fold:** Meta unlock tree (SVG) — permanent upgrades, grouped by type (character / passive / starting bonus)
- **Expanded:** Unlock economy table — meta currency sources (run completion / challenges) × sinks (unlock costs)
- **Expanded:** First-session vs. 10-session vs. 50-session progression state comparison
- **Collapsed:** Challenge / achievement definitions that feed meta currency

### `procedural-gen.html`
- **Audience:** gameplay-programmer (primary), lead-designer (secondary)
- **Layout:** Two-column — left: designer constraints; right: algorithm spec
- **Above fold:** Generator pipeline diagram — seed → room graph → content fill → validation
- **Expanded:** Constraint table — guaranteed rooms per run, min/max branching factor, forbidden adjacencies
- **Expanded:** Content distribution rules — enemy density curve, item rarity weights, loot tables
- **Collapsed:** Rejection sampling rules, seed format, replay-from-seed spec

### `ai-faction.html`
- **Audience:** ai-programmer (primary), systems-designer (secondary)
- **Above fold:** Faction behaviour state machine (SVG) — states = strategy, edges = transition condition
- **Expanded:** Per-faction profile — aggression / expansion / diplomacy weights + trigger thresholds
- **Expanded:** Difficulty scaling table — how AI weights shift per difficulty level
- **Collapsed:** Pathfinding spec, fog-of-war rules, economy weights

### `tech-tree.html`
- **Audience:** systems-designer (primary), numeric-designer (secondary)
- **Above fold:** Visual tech tree (SVG) — nodes = tech, edges = prerequisites, color = era/tier
- **Expanded:** Per-node spec cards (name / cost / prerequisites / unlocks / era)
- **Expanded:** Research pacing table — expected turns to key milestones at normal speed
- **Collapsed:** Full tech table sortable by era / cost / unlocked buildings or units

### `branching-structure.html`
- **Audience:** narrative-designer
- **Above fold:** Full story branch graph (SVG — interactive, nodes expandable on click, color = chapter)
- **Expanded:** Decision point table — choice text / consequence / affected flags / estimated word count
- **Expanded:** Convergence analysis — how many unique paths exist, where they merge
- **Collapsed:** Flag/variable catalogue (name / type / scope / default / read-by)

### `character-arc.html`
- **Audience:** narrative-designer
- **Above fold:** Per-character arc timeline (horizontal, one row per character; X: story %, annotate turning points)
- **Expanded:** Character sheet per character — motivation / wound / lie / truth / arc type (flat/positive/negative)
- **Expanded:** Relationship web (SVG — nodes = characters, edges = relationship + tension at start/end)
- **Collapsed:** Scene-by-scene character presence matrix

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

### Completion Signal

`ai-art-generation` has no `human_gate`, so `/run` uses a different completion check:

**Complete when:** all assets in `art-asset-inventory.json.assets[]` have either:
- `current_state != "placeholder"` (generation succeeded), OR
- `ai_generatable = true` AND `ai_generated.attempted = true` (generation was attempted but failed — graceful degradation)

After completion, write `"ai_art_generation_done": true` to `approval-records.json` for the `ai-art-generation` record (use `gate_status: "approved"` since no human review needed). This signals to `/run` that `game-design-finalize` is now unblocked.

## game-design-doc.json Schema

`game-design-finalize` produces `.allforai/game-design/game-design-doc.json` by aggregating all
approved system JSONs. Only include fields whose source JSON exists (skip missing optional nodes).

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
      "gate_status": "approved | revision-requested"
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

`product-analysis` reads: `player_roles[]`, `systems[]`, `core_loop`, `progression`.
`demo-forge` reads: `progression`, `economy.currencies`.
`quality-checks` reads: `economy.balance_targets`, `audio.sfx_events`, `art` counts.
`generate-artifacts` reads: `systems[]` for code generation targets.

## Downstream Consumers

| Capability | Reads | Uses |
|-----------|-------|------|
| `product-analysis` | `game-design-doc.json` | Concept baseline; `player_roles` → `role-profiles.json`; `systems[]` → task-inventory in system-spec format |
| `ui-design` | `art-style-guide.json`, `game-design-doc.json` | Design tokens from art direction; game screens (HUD, menus, inventory, dialogue) |
| `demo-forge` | `art-asset-inventory.json`, `game-design-doc.json.progression` | Player save data at progression stages using available art state |
| `quality-checks` | `game-design-doc.json.economy.balance_targets`, `audio-design.json.sfx_catalogue[].milestone_gate` | Numerical QA; art-agnostic check; milestone gate check; audio milestone check |
| `generate-artifacts` | `game-design-doc.json.systems[]` | Code generation targets; must implement Asset Registry |

## Engine-Specific Content

When `bootstrap-profile.json.game_engines_detected` is non-empty, game-design
node-specs should include engine-specific guidance in the HTML output and JSON artifact.

Key nodes that benefit from engine context:
- `procedural-gen-spec`: reference engine's procedural APIs (e.g., Godot: `TileMap` + `AStar3D`; Unity: `ProBuilder`; Bevy: ECS proc-gen patterns)
- `network-architecture-design`: reference engine's networking layer (Godot: `MultiplayerAPI`; Unity: `Netcode for GameObjects`; Unreal: `GameNetworkManager`)
- `dialogue-system-spec`: reference engine's dialogue tooling (Godot: `DialogueManager` plugin; Unity: `Yarn Spinner`; Ren'Py: native Ren'Py script format)
- `art-direction`: reference engine's renderer capabilities (Godot: CanvasItem shaders / Forward+ / Mobile; Unity: URP / HDRP; Unreal: Nanite / Lumen)

If `game_engines_detected` is empty (user confirmed game via 业务领域 f), omit engine-specific content — engine is unknown.

## Composition Hints

### Full Pipeline (new game from scratch)
All nodes for detected scenario. `art-direction` + `art-spec-design` + `ai-art-generation`
+ `game-design-finalize` always appended. Every node requires human approval gate
(except `ai-art-generation` which is automatic).

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
3. `game-design-finalize` always re-runs (to produce an updated `game-design-doc.json`)

Example: Adding ranked PvP mode → only `competitive-balance-design` + `game-design-finalize` need re-running if all other nodes are approved.

### Skip Entirely
Game SDK / engine projects, CLI game tools, non-game projects.
