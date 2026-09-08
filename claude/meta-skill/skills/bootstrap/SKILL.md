---
name: bootstrap
argument-hint: [path]
version: "0.14.2"
description: Analyze the target project and generate its .allforai/ workflow (product concept, experience map, art, game design, verify nodes) for /run. User-invoked only via /bootstrap; never invoke it yourself.
---

# Bootstrap Protocol v0.3.0

> Invoked only by the user as `/bootstrap [path]`. Claude must not start it on its own.
> Arguments: $ARGUMENTS (target project path; default is the current directory). Analyze the project and generate its workflow, node-specs, and run command by following this protocol.

## Overview

Bootstrap analyzes a target project and generates project-specific configurations:
- node-specs (one per workflow node)
- workflow.json (node graph + transition log)
- .claude/commands/run.md (orchestrator entry point)

Generated contracts can be reconciled through `/bootstrap`; preserve recorded user decisions and unrelated completed work.
See `docs/adr/0001-bootstrap-free-planning.md`.

## Disclosed Protocols

Read these when the matching branch fires. Do not load all of them up front.

| File | When |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}/knowledge/engine-detection.md` | Step 1 classification |
| `${CLAUDE_PLUGIN_ROOT}/knowledge/suppress-rules.md` | after classification, before planning |
| `${CLAUDE_PLUGIN_ROOT}/knowledge/bootstrap-planning.md` | before designing the node graph |
| `${CLAUDE_PLUGIN_ROOT}/knowledge/bootstrap-art-pipeline.md` | planned graph includes art-direction / art-concept / concept-freeze / art-gen / art-qa |
| `${CLAUDE_PLUGIN_ROOT}/knowledge/node-spec-template.md` | writing any node-spec |
| `${CLAUDE_PLUGIN_ROOT}/knowledge/bootstrap-audits.md` | after candidate workflow + node-specs exist |
| `${CLAUDE_PLUGIN_ROOT}/knowledge/verification-protocol.md` | any verify/smoke/acceptance node |
| `${CLAUDE_PLUGIN_ROOT}/knowledge/safety.md` | generating a demo-forge node-spec |
| `${CLAUDE_PLUGIN_ROOT}/knowledge/domains/game-genre-specialization.md` | generating project-local specialized skills |
| `${CLAUDE_PLUGIN_ROOT}/knowledge/brainstorming-lite.md` | Phase A (via audits Protocol) |

---

## Step 1: Lightweight Analysis

> Goal: Understand the project enough to generate good node-specs.

### 1.0 Capture the Task, Then Detect Existing State

Before code analysis, capture the user's concrete `task_goal` from the invoking
message. If it is unclear, ask only what outcome or boundary is missing. Select
`task_route` from that goal: `local-change`, `product-reconstruction`, or
`new-product`. Existing code and missing product documents cannot choose the
route. A maintenance, verification, migration or implementation request can be
local to its stated scope; do not reinterpret it as product redesign.

For product reconstruction and new products, read and execute
`${CLAUDE_PLUGIN_ROOT}/knowledge/product-intent-confirmation.md` before planning
dependent work. Copy its interactive CLI at discussion entry; use `resume` on
re-entry to restore history/reasons and explicitly excluded scope, asking only
the returned pending topics. For a local request against legacy documents,
use its `admit` operation for relevant projections, then local decide/freeze/plan;
never overwrite old concept/baseline documents or expand the interview globally.
An existing hand-projected `local-requirements.json` without `intent_session_path`
is resumed with `resume`, not re-admitted: it returns only the projections whose
journal choice evidences the goal alone (`legacy_reuse`) or no longer verifies,
and one `confirm` per item recovers the gates in place.
Bind generated plans to the frozen user-confirmed scope.

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/bootstrap-planning.md` § Goal and requirement scope before
collecting local requirements. Limit analysis and classification to the modules,
interfaces and product questions needed for this task. Record unrelated areas as
non-goals; preserve their existing decisions and workflow progress.

### Detect Existing State

Before analyzing code, check if this project already has artifacts:

```bash
ls .allforai/product-map/ .allforai/experience-map/ .allforai/use-case/ .allforai/bootstrap/ 2>/dev/null
```

Record what exists:
- `has_product_artifacts`: true if product-map/task-inventory.json exists
- `has_experience_map`: true if experience-map/experience-map.json exists
- `has_bootstrap`: true if bootstrap/workflow.json exists (previous /bootstrap run)
- `has_code`: true if source code files (*.ts, *.tsx, *.js, *.mjs, *.go, *.py, *.cs, *.rs, *.dart, *.swift, *.kt, *.java, *.cpp, *.c, *.rb, *.lua, *.luau, *.server.luau, *.client.luau, *.gd, *.hx, *.p8, *.p8.png, *.twee, *.tw, etc.) are detected in Step 1.1. Config-only files (package.json, Cargo.toml, go.mod, pubspec.yaml, pom.xml with no src/) do NOT set has_code = true. Notes: *.p8 PICO-8 cartridges embed Lua code; *.luau is Roblox's Luau dialect (Rojo projects use .luau not .lua); *.twee/*.tw are Twine story source files.
- `has_iteration_feedback`: true if product-concept/iteration-feedback.json exists (previous concept-acceptance feedback)
- `has_product_concept`: true if product-concept/product-concept.json exists
- `has_decision_journal`: true if product-concept/decision-journal.json exists (previous recorded product decisions)
- `has_concept_drift`: true if ANY of the following conditions hold:
  - `product-concept/concept-drift.json` exists AND its `resolved` field is false
  - `.allforai/game-design/approval-records.json` exists AND any record has `gate_status == "revision-requested"` (in-flight revision cycle on a design gate)
  - `.allforai/game-design/approval-records.json` exists AND any record has non-empty `revision_notes` AND `gate_status == "approved"` (a previous revision was re-approved — downstream consumers may need re-execution)
  - (when `is_game_project = false`) `.allforai/app-design/approval-records.json` exists AND any record has `gate_status == "revision-requested"` (in-flight revision cycle on an app design gate)
  - (when `is_game_project = false`) `.allforai/app-design/approval-records.json` exists AND any record has `gate_status == "approved"` AND `revision_notes` is non-empty (a previous app-design revision was re-approved — downstream consumers may need re-execution)
  
  When `has_concept_drift` is true due to approval-records (not concept-drift.json), set:
  - `concept_drift_source: "product-concept"` — when triggered by concept-drift.json (condition 1 above)
  - `concept_drift_source: "game-design-gate"` — when triggered by either game-design approval-records.json condition (conditions 2 or 3 above)
  - `concept_drift_source: "app-design-gate"` — when triggered by either app-design approval-records.json condition (conditions 4 or 5 above, when `is_game_project = false`)

This affects Step 1.5 options:
- has_product_artifacts + has_code → verification/demo/tune options are relevant
- has_bootstrap → offer to reuse or regenerate
- no code + no artifacts → ask for missing context only if the stated goal needs it; do not infer the route
- has_iteration_feedback → LLM reads feedback in Step 2, prioritizes fixing previous gaps in Step 3
- has_concept_drift → Step 3 uses incremental re-planning (Step 3.0) instead of full planning



### 1.1 Classify the project

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/engine-detection.md`.
Record language, framework, `architecture_pattern`, `is_game_project`,
`game_engines_detected`, modules, build/test commands, and runtime needs.

Then apply `${CLAUDE_PLUGIN_ROOT}/knowledge/suppress-rules.md`.

### 1.2 Fill the rest of the profile

Read whatever files the profile still needs. There is no required sample count.

### 1.5 Collect Target Information (Interactive)

Use the captured goal and route, asking only necessary scope questions:

- `local-change`: clarify the requested outcome, relevant business rules,
  acceptance conditions and impact boundary. Reuse applicable recorded user
  decisions. Missing documents require local investigation and focused questions,
  not whole-product reverse-concept. Persist confirmed requirements using the
  contract in `bootstrap-planning.md`; unanswered items remain pending.
- `product-reconstruction`: enter reverse-concept's evidence-backed draft and
  interactive product confirmation process. Inference is provisional, including
  high-confidence code facts; it cannot authorize downstream execution.
- `new-product`: establish intent directly from the user's vision and decisions,
  then use the applicable product-concept/downstream process without reverse-concept.

Record target stacks, fidelity constraints and domain choices only when they
matter to the requested work. The following engine/domain questions apply only
when their answer is needed for this scope and is not already known.

**If game engine detected in Step 1.1 AND the user has not explicitly identified it as a game:**

**If `game_engines_detected` has 2+ entries (multiple engines detected):** First disambiguate before game/non-game confirmation:

```
检测到多个游戏引擎标记：[engine1], [engine2]。请确认主引擎：
   a) 主引擎是 [engine1]（[engine2] 为工具/辅助依赖）
   b) 主引擎是 [engine2]（[engine1] 为工具/辅助依赖）
   c) 这不是游戏项目（引擎仅用于工具/可视化/仿真）
```

If user selects (c): `is_game_project = false`. Otherwise, keep only the selected primary engine in `game_engines_detected`.

**If `game_engines_detected` has exactly 1 entry:** Confirm the project type:

```
检测到 [引擎名] 项目，请确认项目类型：
   a) 游戏项目（继续选择游戏品类）
   b) 非游戏 VR/AR 体验（沉浸式可视化 / 训练仿真 / 工业 AR / 医疗 XR 等）
   c) 非游戏可视化/仿真工具（数据可视化、物理仿真、建筑可视化等）
   d) 其他非游戏用途（请说明）
```

If user selects (b): set `is_game_project = false`, `architecture_pattern: 'xr-experience'`. Treat
engine as tech stack context, load `knowledge/domains/xr.md` if available as supplementary reference.
If user selects (c): set `is_game_project = false`, `architecture_pattern: 'visualization-sim'`.
If user selects (d): set `is_game_project = false`, record user's description in `business_context`.
For all non-game selections: skip game scenario selection entirely and proceed with normal bootstrap flow.

**If business_domain = "gaming" confirmed (user selected (a) above, or explicitly chose
gaming in the task description):**

After confirming the main goal, ask ONE additional question.

If the detected engine has a **scenario hint** (marked in the game engines list above as "scenario hint: X"), pre-mark that option with `[推荐]` in the list. The user can override — they are not locked in.

```
游戏品类（选一）：
   a) 超休闲/中度手游 (casual-mobile)
   b) 动作/卡牌/RPG (action-rpg)         ← [推荐] if RPG Maker detected
   c) 在线多人 MMO/MOBA/FPS (multiplayer-online)
   d) 肉鸽/Roguelite (roguelike)
   e) 策略/模拟经营 (strategy-sim)
   f) 叙事/视觉小说/AVG (narrative-adventure)  ← [推荐] if Ren'Py / Twine detected
```

If the user's game doesn't fit any template exactly, suggest the closest match:
- 体育/运动游戏 (FIFA/NBA style) → e) 策略/模拟经营 (team management + balance focus)
- 格斗游戏 (Street Fighter style) → b) 动作/卡牌/RPG (combat system focus)
- 沙盒/开放世界 (Minecraft style) → b) or e) depending on combat vs. economy emphasis
- 音乐/节奏游戏 (Guitar Hero style) → a) 超休闲/中度手游 (session design + retention focus)
- 益智/解谜 (Wordle/casual puzzle) → a) 超休闲/中度手游
- 放置/挂机/增量游戏 (idle/incremental — e.g. Cookie Clicker, AdVenture Capitalist) → e) 策略/模拟经营 (economy-design + progression-curve-design focus; session loop is offline accumulation, NOT retention-hook); note: present disambiguation to user if unclear between idle and strategy: "该游戏是否有实时操作（战斗/建造），还是主要依赖离线积累？"
- 放置 RPG (AFK-style idle with hero collection) → d) 肉鸽/Roguelite OR b) 动作/卡牌/RPG depending on whether each run is discrete; note: distinguish from pure idle (no runs, continuous offline progression)
- 教育/严肃游戏 (EdTech/serious game) → a) 超休闲/中度手游 (FTUE + session design focus); note to user: "combat-system-design 对教育类游戏通常不适用，请在可选节点中跳过"
- PICO-8 / 幻想主机 / 复古风格游戏 → a) 超休闲/中度手游; note: despite the "mobile" label, treat as general casual — apply platform capability guard below
- 平台移植 (same-engine platform port, e.g., Unity PC → Unity mobile) → `rebuild` within the requested port boundary; add note: "platform port = rebuild with target platform constraints (touch input, resolution, performance budget)"

**Platform capability guard (applies during Step 3.1 node injection):**
Some game engines/platforms structurally cannot support IAP, push notifications, or retention systems.
For these platforms, suppress `monetization-design`, `retention-hook-design`, and `meta-game-design`
from BOTH (a) the `required_nodes` list AND (b) the canonical optional eligibility pool, regardless
of what the selected scenario template declares. If these nodes appear in a template's `required_nodes`,
remove them before building the workflow — the platform constraint overrides the template:
- PICO-8 (*.p8 detected) — no store integration, no push API
- LÖVE2D standalone (*.love or main.lua+conf.lua, no build.settings) — no native store
- GBStudio (*.gbsproj) — Game Boy cartridge, no runtime monetization
- Twine/Ren'Py web export — static web narrative, no IAP
- HaxeFlixel targeting HTML5/desktop only (haxelib.json + flixel, no mobile build config) — no native store
- Roblox (default.project.json or *.rbxl detected) — DOES have its own monetization (Robux, Developer Products, Game Passes, Limited Items via DevEx), but these use the **Roblox economy API**, NOT App Store IAP/StoreKit/Google Play Billing. Suppress generic `monetization-design` and `launch-prep` IAP compliance nodes. Instead inject `roblox-monetization-design` as optional node (covers Robux product setup, premium payouts, DevEx setup). Do NOT suppress retention-hook-design (Roblox supports daily login rewards via DataStore + RemoteEvent).
Note in the bootstrap output: "Platform [{engine}] does not support IAP/push — monetization/retention nodes removed from workflow (required and optional)."

The template is a STARTING POINT. The user can add or remove nodes via the optional node question that follows.

Map answer to `game_scenario` field in bootstrap-profile.json.
If no scenario hint and user is unsure, suggest `action-rpg` as default (broadest node set).

After the user selects a scenario, bootstrap reads the selected template's `bootstrap_note`
(if present). If the note lists ad-hoc optional nodes, present them as a follow-up question:

```
以下功能模块可选（非必需）：
   [list nodes from bootstrap_note, one per line with short description]
   需要加入哪些？（可多选，直接回车跳过）
```

**Canonical optional nodes** (those that appear in the template's `node_order`) form an *eligibility pool* — not an auto-include list. Bootstrap selects from the pool based on project signals. Examples of project signals:
- Include `narrative-design` / `branching-structure-design` / `character-arc-design` / `dialogue-system-spec` only if the game has explicit narrative or branching dialogue (not for hack-and-slash, idle, or sports games)
- Include `combat-system-design` and `competitive-balance-design` only if the game has combat or PvP mechanics
- Include `puzzle-design` only if the game has dedicated puzzle content
- Include `retention-hook-design` / `meta-game-design` for mobile games with session loops
- Include `monetization-design` as **strongly recommended** (annotate with `[推荐]` in opt-in question) for any `casual-mobile` scenario game targeting Android/iOS (detected from Unity mobile build targets, Android/iOS in *.uproject target platforms, `pubspec.yaml` Flutter targets, or similar). Exception: apply platform capability guard (PICO-8, LÖVE2D, etc.) first.
- Include `economy-design` / `tech-tree-design` for RTS games (in multiplayer-online scenario) or strategy games
- Include `level-design` for games with designed maps, levels, or zones

**Ad-hoc optional nodes** (those listed in `bootstrap_note` but NOT in `node_order`) MUST be explicitly presented to the user for opt-in. When parsing `bootstrap_note`, identify ad-hoc nodes as those with phrases like "not in canonical node registry" or those absent from `node_order`. Do NOT re-present canonical optional nodes (already in `node_order`) in the user opt-in question — they are handled automatically by bootstrap's context judgment.

**Map the requested work to capability goals after selecting the route.**

Use `implement` for adding or changing behavior while preserving existing code;
use `translate` or `rebuild` only for the requested migration/rebuild boundary.
Do not treat `implement` as `rebuild`: preserve existing code and plan only
missing or changed behavior in the requested boundary. The legacy selection
`l) 继续实施开发` maps to this same scoped implementation path.
Other requested outcomes can use `analyze`, `tune`, `demo`, `ui-forge`,
`product-verify`, `visual-verify`, `quality-checks` or `launch-prep`. These are
methodologies, not automatic node bundles.

For an implementation scope that actually needs all of these responsibilities,
the goal list can remain `["implement", "demo", "product-verify", "visual-verify", "quality-checks", "concept-acceptance"]`.
Select the relevant subset for local work and apply suppress rules; absence of
product documents does not expand that list or request full reconstruction.

Only `product-reconstruction` selects whole-product `reverse-concept`; it
produces provisional input for interactive confirmation, never an independent
approved baseline by itself. `new-product` starts with `create` and user intent.
Missing concept/baseline/design files never auto-prepend reconstruction to a
local request. For local `analyze` or `implement`, use the confirmed local
requirement record as the basis for planning and acceptance.

Plan dependencies from actual inputs: confirmed requirements precede the
selected translate / rebuild / create / implement work, applicable integration/effect verification follows implementation,
and launch acceptance follows its required verification. Apply suppress rules.
Preserve real runtime, UI and quality obligations within the selected scope;
do not add whole-product demo/discovery/acceptance solely because a local change
produces code. Before pricing/tier decisions in launch work, perform the relevant
competitive research. Any new product choice still needs recorded confirmation.

### 1.6 Output bootstrap-profile.json

Write to `.allforai/bootstrap/bootstrap-profile.json`:

```json
{
  "schema_version": "1.0",
  "project_name": "<from directory name or package.json name>",
  "task_goal": "<the user's concrete requested outcome>",
  "task_route": "local-change | product-reconstruction | new-product",
  "task_scope": {
    "areas": ["<relevant business/module boundary>"],
    "requirement_refs": [{"path": ".allforai/bootstrap/local-requirements.json", "id": "<stable requirement id>", "revision": 1}]
  },
  "business_domain": "<inferred: ecommerce/fintech/healthcare/saas/social/gaming/...>",
  "business_context": "<1-2 sentence description of what this project does>",
  "tech_stacks": [
    {
      "role": "frontend | backend | mobile | shared",
      "language": "<language>",
      "language_version": "<version if detectable>",
      "framework": "<framework name + version>",
      "state_management": "<if applicable>",
      "router": "<if applicable>",
      "orm": "<if applicable>",
      "db": "<if applicable>",
      "build_tool": "<vite/webpack/go build/cargo/...>"
    }
  ],
  "goals": ["reverse-concept | analyze | translate | rebuild | create | implement | tune | demo | ui-forge | product-verify | visual-verify | quality-checks | launch-prep | concept-acceptance | runtime-smoke-verify"],
  "product_vision": "<one sentence, only for goals includes create>",
  "target_stacks": [
    {
      "role": "frontend | backend | mobile",
      "language": "<target language>",
      "framework": "<target framework>"
    }
  ],
  "ui_fidelity": "faithful | native | null",
  "modules": [
    {
      "id": "M001",
      "path": "<relative path>",
      "role": "frontend | backend | shared | mobile | infra",
      "description": "<what this module contains>"
    }
  ],
  "build_commands": {
    "<role>": "<build command>"
  },
  "test_commands": {
    "<role>": "<test command>"
  },
  "detected_patterns": ["<REST API>", "<JWT auth>", "<Redis cache>", "..."],
  "architecture_pattern": "<MVC/Clean/Layered/Feature-sliced/...>",
  "complexity_estimate": "low | medium | high",
  "is_game_project": false,
  "game_engines_detected": ["<engine name(s) from Step 1.1 detection, empty if none>"],
  "game_scenario": "casual-mobile | action-rpg | multiplayer-online | roguelike | strategy-sim | narrative-adventure | null",
  "deployment_platform": "vercel | null",  // vercel when vercel.json / vercel devDep detected; null otherwise
  "offline_first": false,  // true when Flutter+Drift without backend module detected
  "requires_runtime_env": false,  // true only when goals include translate/rebuild/create/implement; false for analyze/tune/quality-checks
  "detected_state": {
    "has_code": false,
    "has_product_artifacts": false,
    "has_bootstrap": false,
    "has_product_concept": false,
    "has_experience_map": false,
    "has_iteration_feedback": false,
    "has_decision_journal": false,
    "has_concept_drift": false
  }
}
```

> **bootstrap-profile.json vs discovery source-summary.json — no conflict:**
> bootstrap-profile.json is produced during /bootstrap phase and lives in `.allforai/bootstrap/`.
> It is NOT consumed by /run-time subagents directly. If the workflow includes a discovery node,
> that node produces `source-summary.json` by reading source code directly — it does NOT read
> bootstrap-profile.json. The two artifacts have overlapping fields (tech_stacks, modules,
> architecture_pattern, detected_patterns) but are independent: bootstrap-profile captures
> the structural view needed for workflow planning; source-summary captures the deep semantic
> view needed for code generation. Downstream node-specs reference source-summary.json only.

---




## Step 2: Load Knowledge (on demand)

Capabilities are REFERENCE material, not a node menu.

Load only what this run needs:

1. Capability files whose names match selected `goals` (and their declared knowledge refs).
   Do not read every file in `knowledge/capabilities/`.
2. `${CLAUDE_PLUGIN_ROOT}/knowledge/domains/<domain>.md` when it matches `business_domain`.
   If `business_domain = gaming` but `is_game_project = false`, load `gaming.md` only as
   supplementary methodology — do not inject game-design nodes.
3. Cross-domain methodology only when the product actually uses that pattern
   (gamification, realtime chat, marketplace).
4. `${CLAUDE_PLUGIN_ROOT}/knowledge/cross-phase-protocols.md` and
   `${CLAUDE_PLUGIN_ROOT}/knowledge/defensive-patterns.md` when planning
   implementation, verify, or design nodes.
5. Tech-stack mappings under `knowledge/mappings/` only for translate/rebuild.
6. Blind-spots: if `.allforai/bootstrap/learned/blind-spots.md` or
   `${CLAUDE_PLUGIN_ROOT}/knowledge/learned/blind-spots.md` exists, read it
   and add any `open`/`scheduled` prevention capability in Step 3.
7. Iteration feedback / product-concept / decision-journal when the matching
   `has_*` flag from Step 1.0 is true. Respect journal decisions; do not re-ask.
8. Knowledge-gap research only when domain files do not cover a named subsystem or the
   target stack is unfamiliar. Per gap, record what was searched, the conclusion, and a
   confidence; stop a gap when the conclusion stops changing, not at a query count.

Proceed to planning with confirmed inputs. Missing product decisions return to the interactive Phase A queue before dependent work is offered; they never become run-time interviews.

## Step 3: Plan Workflow (LLM Free Planning)

> Goal: Design a project-specific workflow. NOT selecting from templates.
> LLM has absorbed all knowledge in Step 2. Now freely plan what nodes
> this specific project needs.

### 3.0 Incremental Re-Planning (when concept-drift exists)

At every bootstrap/resume boundary, follow `${CLAUDE_PLUGIN_ROOT}/knowledge/input-freshness.md`
even when concept-drift is absent. Declare each node's `source_inputs`, consumed
`input_dependencies` and `required_documents`; observe inputs before generating
documents, publish verified contract observations before readiness, and consume
freshness through reconciliation. Preserve unaffected evidence and journal authority.
Invalidated items name a `diff` and `repair_owner`: resolve `interactive-bootstrap`
items here (answer the pending decision, or refreeze and replan the recorded
change), and leave node-owned items for `/run` to repair and republish.

At the same boundary, send `{"operation":"external-changes"}` to detect code
changed outside the delivery flow. A change whose recorded acceptance still passes
is an implementation fact: resynchronize its documents and republish. A failing one,
or changed source no node declares, is a conflict reported to the user, never a new
requirement. Record the user's `accept` (with the explicit desired intent it
establishes), `reject` (baseline kept, scoped implementation repair) or `defer`
through `product_intent.py`'s `external-change` operation with an actual user
reference and reason. A deferred or interrupted decision keeps the conflict and
blocks only the work that depends on it; unrelated valid records are preserved.
A Run Policy `accept` is a run choice and never accepts a product behavior change.
The freshness, artifact, reconciliation and readiness gates run the same
comparison themselves, so an interrupted boundary still routes the conflict to
the interactive decision instead of reporting it as node-owned repair.

> This section only applies when `has_concept_drift` is true AND an existing
> `workflow.json` exists. Otherwise, skip to 3.1 for full planning.

**Re-bootstrap state index and reconciliation gate (hard rule):**
When an existing `.allforai/bootstrap/workflow.json` is present, bootstrap must
not silently overwrite the workflow or node-specs. Before any full or
incremental re-planning, run:

```bash
python3 .allforai/bootstrap/scripts/reconcile_bootstrap_workflow.py . --write
```

This writes:

- `.allforai/bootstrap/workflow-state-index.json`
- `.allforai/bootstrap/workflow-reconciliation-plan.json`
- `.allforai/bootstrap/workflow-reconciliation-plan.md`

If bootstrap creates a candidate workflow before committing the final one, run
the same script with `--candidate-workflow <candidate-path> --write` and use
the plan actions instead of direct replacement:

| Plan Action | Meaning |
|-------------|---------|
| `keep` | Preserve node, node_id, and completed evidence unless downstream invalidation says otherwise. |
| `update` | Keep node_id but regenerate node-spec and mark affected downstream nodes `needs-rerun`. |
| `add` | Add new node and node-spec. |
| `remove` | Remove unused/unexecuted node-spec or node. |
| `supersede` | Do not silently delete completed work; replace with a new node only with audit trail. |
| `invalidate` | Existing artifact is missing, blocked, stale, invalid, or quality/effect incomplete; rerun node and downstream QA/closure. |

The final written workflow must explain how each non-`keep` action was applied
in `workflow.json.reconciliation_applied[]`. Re-bootstrap must preserve
`transition_log[]` for audit, remove orphan node-specs, and keep stable
`node_id`s unless a node's meaning has changed enough to require `supersede`.
Canonical action set: `keep/update/add/remove/supersede/invalidate`.
Bootstrap must not silently overwrite an existing workflow.

**Goal Change Detection (runs BEFORE incremental re-planning):**
Before running §3.0, compare the user's current goal (from Step 1.5) against the `goals` field in the existing `workflow.json`:
- If goals are DIFFERENT (e.g., was `["analyze"]`, now `["create"]`): do NOT use blind incremental re-planning. Generate a candidate full workflow, run the reconciliation gate above, then apply explicit `keep/update/add/remove/supersede/invalidate` actions. Preserve `transition_log[]` for audit. Existing node-specs are stale until the reconciliation plan keeps or regenerates them.
- If goals are THE SAME but concept drifted: use §3.0 incremental re-planning (below).
- If `workflow.json` has no `goals` field (schema mismatch from older bootstrap): treat as "goals differ" → candidate full re-planning + reconciliation.

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
| client_removed | Remove the implementation + compile-verify + e2e triplet for that client. If the role becomes single-client, Level 3 parity check no longer applies. |
| client_added | Add implementation + compile-verify + e2e triplet for the new client. Trigger Level 3 parity check. |
| module_merged | Remove nodes for merged services. Extend the target service node's goal to absorb merged functionality. |
| module_split | Create new service nodes for the split-out module. Reduce the source service node's goal. |

4. **Preserve unaffected nodes**: nodes whose goal does not relate to any drift change
   remain in workflow.json with their transition_log entries intact. Completed work is not lost.
   **Cross-change dependencies**: a tech_changed may also affect infrastructure nodes
   (e.g., Flutter→SwiftUI means FCM push is no longer needed, only APNs). LLM must
   trace second-order effects of each change on ALL nodes, not just the obvious ones.

5. **Handle affected completed nodes**:
   - Node removed → transition_log entry stays for audit, but node removed from nodes[]
   - Node goal modified → clear its transition_log entry (needs re-execution)
   - New node added → no transition_log entry yet

6. Write updated workflow.json with modified nodes[] and preserved transition_log[].
7. Regenerate node-specs for all affected nodes at `.allforai/bootstrap/node-specs/`.
8. Proceed to Step 3.5 (Coverage Self-Check) — concept has changed, coverage must be re-verified.
9. Do NOT mark drift as resolved here. The orchestrator (/run) marks drift resolved AFTER all nodes complete successfully. This prevents the case where bootstrap marks drift resolved but /run fails partway — next /bootstrap would then wrongly see drift as already resolved and skip re-planning.

**When `concept_drift_source == "game-design-gate"`:**

1. Read `.allforai/game-design/approval-records.json` → collect all records with non-empty `revision_notes`
2. For each revised node, identify which downstream nodes consume its output (from `consumers[]` in workflow.json)
3. Mark those downstream nodes as `"status": "needs-rerun"` in workflow.json — they must re-execute with the updated design input
4. Nodes whose `hard_blocked_by` does not include any revised node → preserve as-is (no re-execution needed)
5. Write revision summary to `.allforai/product-concept/concept-drift.json` if it doesn't exist yet:
   ```json
   {
     "source": "game-design-gate",
     "changes": [
       { "node_id": "<revised node id>", "revision_notes": "<notes from approval-records>", "detected_at": "<ISO>" }
     ],
     "resolved": false
   }
   ```
6. Do NOT mark drift as resolved here. The orchestrator (/run) marks it resolved after all re-run nodes complete successfully.

**After incremental re-planning, skip 3.1-3.3** (they are for full planning) and go directly
to Step 3.4 (Confirm with User) → Step 3.5 (Coverage Self-Check) → Step 4.



### 3.1 Design the Node Graph

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/bootstrap-planning.md` and apply suppress-rules.

There is no fixed template and no required game node list. Design nodes for
this project's goals. If the planned graph includes art production, read
`${CLAUDE_PLUGIN_ROOT}/knowledge/bootstrap-art-pipeline.md` and follow it.

If `is_game_project` and goals include `create` / `translate` / `rebuild`
(or `analyze` with no approval-records), load `knowledge/capabilities/game-design.md`
as methodology and artifact contracts — not as a mandatory node menu.

For `implement`, consume existing approved design/art/UI/audio handoff artifacts.
If required handoff artifacts are missing, add a targeted regeneration node or
block unattended readiness. Do not silently convert `implement` into `rebuild`.

Declare `workflow.json.expanders` for any project-local expander that applies
(e.g. `expand_game_2d_production.py`) and run them after the first graph write.

**Project-local specialized skills:** follow
`${CLAUDE_PLUGIN_ROOT}/knowledge/domains/game-genre-specialization.md`.
Write them under `.allforai/bootstrap/specialized-skills/`.
Each generated specialized skill must include:
`Input Contract`, `Output Contract`, `Invocation Contract`, `Automatic Validation`,
`Repair Routing`, and `Completion Conditions`.

If total nodes > 30, offer phased `/bootstrap` → `/run` cycles in Step 3.4.

### 3.2 Write workflow.json

```json
{
  "schema_version": "2.0",
  "project": "<project name>",
  "goals": ["<user-selected goal codes, e.g. 'analyze', 'translate', 'quality-checks'>"],
  "planned_at": "<ISO timestamp>",
  "nodes": [
    {
      "node_id": "<project-specific name>",
      "capability": "<name of the capability this node is based on, e.g. discovery, product-analysis, translate>",
      "goal": "<one sentence: what this node achieves>",
      "exit_artifacts": [
        {
          "path": "<project-relative file path>",
          "validation_commands": []
        }
      ],
      "source_inputs": ["<project-relative product source files, directories or globs this node's documents and evidence trace to; explicit [] only when no product source is relevant>"],
      "knowledge_refs": ["<which knowledge files this node should reference>"],
      "consumers": ["<node IDs that read this node's exit_artifacts>"],
      "hard_blocked_by": ["<node IDs that must complete before this node can start — strict execution gate>"],
      "alignment_refs": ["<node IDs this node reads from but can run concurrently — reads artifacts after they exist>"],
      "unlocks": ["<node IDs unblocked when this node completes>"],
      "human_gate": false,
      "discipline_owner": null
    }
  ],
  "transition_log": [],
  "diagnosis_history": [],
  "corrections_applied": []
}
```

**Node fields:**
- `node_id`: Project-specific. NOT from a fixed vocabulary. `id` is forbidden in workflow nodes.
- `capability`: Which capability this node is based on. Matches a file in
  `knowledge/capabilities/<capability>.md`. Used at Context Pull generation time
  to look up which upstream artifacts this node may consume.
- `goal`: One sentence. Clear enough that a subagent knows what to do.
- `exit_artifacts`: Array of artifact objects. Artifact existence is necessary
  but not sufficient for runtime, UI, art, audio, VFX, network, storage, and
  game nodes. Such nodes are complete only when their effect verification also
  passes and the result is written into an exit artifact.
  Each entry has:
  - `path`: Project-relative file path. The file must exist and pass its completion checks.
  - `validation_commands` (optional): Shell commands that must exit 0 after the file exists.
    Use for format checks beyond mere existence (e.g., `python3 -c "import json,sys; json.load(open('file.json'))"` for JSON validity,
    `grep -q '"status": "final"' file.json` for specific field checks).
    Empty array skips external commands, not built-in JSON and status checks. Bootstrap should populate these for JSON output files.
  - `required_fields` and `accepted_statuses` (optional): For JSON completion reports, declare required top-level fields and accepted values of `status` (for example `["status", "evidence"]` and `["passed"]`). Use domain validation commands for data artifacts that have no status field. Malformed JSON is always invalid; an empty exit-artifact list cannot prove node completion. Validation commands must be repeatable, non-mutating, and finish within 300 seconds.
  
  **Shorthand:** Bootstrap may also use the string form `"<path>"` for artifacts with no
  validation_commands. check_artifacts.py accepts both forms.
- `knowledge_refs`: Which knowledge files to inject into the node-spec.
- `consumers`: Which downstream nodes read this node's output. Used to generate
  the Downstream Contract section in the node-spec — tells the subagent "who
  will consume your output and what they need from it".
  **How to populate**: For each node N, `consumers[]` = all node IDs M where N appears in M's `hard_blocked_by[]` AND N's exit_artifacts are listed in the Downstream Consumers table of M's capability file. Bootstrap derives this during Step 3.1 node graph design — after hard_blocked_by chains are established, traverse them in reverse to fill consumers.
- `hard_blocked_by`: Node IDs that must complete (exit_artifacts ready + human_gate approved if applicable) before this node can START. The orchestrator will not dispatch this node until all hard_blocked_by nodes are complete and artifact-status validation passes. Use for true data dependencies — this node's inputs are not usable until upstream finishes.
- `alignment_refs`: Node IDs this node reads artifacts FROM but does not strictly depend on for execution timing. The orchestrator may dispatch this node in parallel with alignment_refs nodes; the node-spec's Context Pull section must handle the case where alignment_refs artifacts may not yet exist (graceful degradation). Use for "I want to align with X's output but can work without it."

- `unlocks`: Node IDs unblocked when this node's gate is approved. Used by the orchestrator to advance the workflow after approval.
- `discipline_owner`: Role ID for a Phase A decision owner when `decision_mode` is `brainstorm`; `null` otherwise.

### CC-superset fields (emit on every node — Codex ignore them)

When writing each node into `workflow.json`, add:
- `node_spec_path`: relative path to this node's spec under `node-specs/`.
- `profile_slice`: the subset of `bootstrap-profile.json` this node needs (tech stack, scenario, target paths) — NOT the whole profile.
- `decision_mode`: `"brainstorm"` if this node's direction is a human decision gathered in Phase A; else `"none"`.
- `requirement_refs`: exact `{path, id, revision}` references from `task_scope` for this node; mirror them in its Node-spec.
- `responsibilities`: scoped obligations this node owns (`implementation`, `documentation`, `verification`); combine or split by actual work, not fixed node names.
- `decision_inputs`: paths to the `.allforai/<domain>/decision-<id>.json` artifacts this node consumes (the former `human_gate` is re-expressed here — see below).
- `source_inputs`: the product source (files, directories or globs, project-relative) that this node's documents, contract and evidence trace to. Required on every node that consumes `requirement_refs`; write explicit `[]` only when no product source is relevant. Omission or a malformed value is refused by all public gates (`missing_source_inputs` / `invalid_source_inputs`) — never a silent skip of freshness. Do not declare the whole repository to silence drift; extra files consumed during execution are registered through the freshness `read` operation. Retained completed legacy nodes keep their historical contract and no provenance is invented for them.
- `input_dependencies`: additional consumed files (generated artifacts, policies) beyond `source_inputs`; `required_documents`: generated fact documents that must accompany delivery; `document_verification`: for each required document, a project-specific argv that executes its stated facts against the current source (a doctest of its examples, an interface or schema comparison, a behavior probe), never mere existence or a status field. Every gate refuses a required document without it (`missing_document_verification`), and evidence publication runs it so a code-only acceptance cannot complete a delivery with outdated facts. Mirror all four in the Node-spec frontmatter.
- `closure_verify`: closure types to verify (e.g. `["audio"]`, `["save-load"]`, `["2d-placeholder"]`) when applicable; else omit or `[]`.
- `soft_retry_max`: integer (default 2) — leave unset to use the engine default.

At the top level of `workflow.json`, add:
- `expanders`: the list of project-local expander scripts that apply (e.g. `["expand_game_2d_production.py"]`), promoting today's hardcoded invocation to a declared list.

**`human_gate` is not a runtime concept.** Direction decisions are Phase A
`decision_inputs` artifacts. See `docs/adr/0001-bootstrap-free-planning.md`.
Do not emit `human_gate: true` or `approval_record_path` on new nodes.
Existing write-path initialization of `approval-records.json` stays in Step 6
until that chain is retired in a later change.

**No entry_requires.** Execution order is `hard_blocked_by` + artifact existence.

**exit_artifacts paths** must be exact project-relative paths from the repo root
(include the monorepo prefix). Prefer object form `{path, validation_commands}`.
String form is allowed when there are no validation commands.
JSON outputs should include at least
`python3 -c "import json; json.load(open('<path>'))"`.

### 3.3 Pre-Generate Node-Specs

For each node, write `.allforai/bootstrap/node-specs/<node_id>.md` from
`${CLAUDE_PLUGIN_ROOT}/knowledge/node-spec-template.md`.

**Context Pull:** for each upstream producer (this node appears in their
`consumers[]`), keep relevant Downstream Consumers rows; mark required vs
optional. First nodes omit Context Pull.

**Safety:** demo-forge node-specs start with the staging-vs-production check
from `knowledge/safety.md`.

### 3.4 Confirm with User

Present summary:

```
Bootstrap 完成。

项目：{project_name}
目标：{goal}
技术栈：{tech stacks}

规划了 {N} 个节点：
  {list each node id + goal}

确认正确吗？
```

User confirms → proceed to Step 4.

---



### 3.5–3.8 Audits

Read and execute `${CLAUDE_PLUGIN_ROOT}/knowledge/bootstrap-audits.md`
(Coverage Self-Check, G0, A0, Phase A, three-lens DAG, node-spec audit via
`bootstrap-node-expansion-qa`).
`/run` is offered only when decision-input and DAG-structure lenses return OK
and the node-spec audit passes.

## Step 4: Generate run.md

Read `${CLAUDE_PLUGIN_ROOT}/knowledge/orchestrator-template.md` for the template.
Write the result to `.claude/commands/run.md` in the target project.

No customization needed beyond what the template provides — the orchestrator
reads workflow.json at runtime, which already contains all project-specific information.

---

## Step 5: Validate

Ensure the candidate profile, requirement records, workflow and Node-specs are
on disk and copy the helper set in Step 6.2 before invoking the validators.
Preserve prior approved records and apply the reconciliation plan when publishing
updates; validation failure never authorizes replacing them with empty defaults.

Run:
```bash
python3 .allforai/bootstrap/scripts/validate_bootstrap.py .allforai/bootstrap/
```

If errors: fix and re-validate (max 3 attempts).

---

## Step 6: Write Files to Target Project

### 6.1 Create Directories (preserve learned/)

```bash
mkdir -p .claude/commands
mkdir -p .allforai/bootstrap/node-specs
mkdir -p .allforai/bootstrap/learned   # preserved across re-bootstrap
```

**Re-bootstrap behavior:**
If `.allforai/bootstrap/` already exists (previous run):
- **Preserve**: `.allforai/bootstrap/learned/` (project experience, never delete)
- **Preserve for audit**: `transition_log[]`, `run-log.jsonl`,
  `workflow-state-index.json`, `workflow-reconciliation-plan.json`, and
  `workflow-reconciliation-plan.md`
- **Reconcile before overwrite**: run `reconcile_bootstrap_workflow.py --write`
  before replacing `workflow.json` or `node-specs/`; if a candidate workflow is
  generated, run it again with `--candidate-workflow`.
- **Overwrite only by plan**: apply explicit `keep/update/add/remove/supersede/
  invalidate` actions. Do not reset workflow progress merely because
  re-bootstrap ran.
- This means re-bootstrap keeps learned experience and execution audit, while
  only regenerating nodes whose contracts, inputs, outputs, or evidence became
  stale.

### 6.2 Copy Orchestrator Scripts

Copy scripts and protocol files to the target project so `/run` works independently:

```bash
mkdir -p .allforai/bootstrap/scripts
mkdir -p .allforai/bootstrap/protocols
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/check_artifacts.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/product_intent.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/evidence_freshness.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/knowledge/input-freshness.md .allforai/bootstrap/protocols/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/check_decision_inputs.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/validate_bootstrap.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/expand_game_2d_production.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/reconcile_bootstrap_workflow.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/validate_unattended_readiness.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/render_approval_dashboard.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/serve_approval.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/apply_approval_action.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/record_meta_skill_feedback.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/record_run_event.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/scripts/orchestrator/summarize_run_log.py .allforai/bootstrap/scripts/
cp ${CLAUDE_PLUGIN_ROOT}/knowledge/diagnosis.md .allforai/bootstrap/protocols/
cp ${CLAUDE_PLUGIN_ROOT}/knowledge/learning-protocol.md .allforai/bootstrap/protocols/
cp ${CLAUDE_PLUGIN_ROOT}/knowledge/feedback-protocol.md .allforai/bootstrap/protocols/
```

> **Why copy?** The meta-skill plugin is installed in Claude's plugin cache.
> The target project needs its own copy so `/run` works even if the plugin
> is uninstalled or updated. All run.md references use project-local paths.

### 6.3 Write Files

Persist the validated files from Steps 3–5 and required runtime assets:

1. `.allforai/bootstrap/bootstrap-profile.json`
2. `.allforai/bootstrap/workflow.json`
3. `.allforai/bootstrap/coverage-matrix.json` (from Step 3.5, only if product-concept.json exists)
4. `.allforai/bootstrap/node-specs/*.md` — update only as authorized by the reconciliation plan
5. `.claude/commands/run.md`
6. `.allforai/bootstrap/scripts/check_artifacts.py`
7. `.allforai/bootstrap/scripts/validate_bootstrap.py`
8. `.allforai/bootstrap/scripts/expand_game_2d_production.py`
9. `.allforai/bootstrap/scripts/validate_unattended_readiness.py`
10. `.allforai/bootstrap/scripts/record_meta_skill_feedback.py`
11. `.allforai/bootstrap/scripts/record_run_event.py`
12. `.allforai/bootstrap/scripts/summarize_run_log.py`
13. `.allforai/bootstrap/unattended-run-readiness-spec.json`：声明本次 workflow 在 `/run` 前必须满足的无人值守能力、审批、工具、Key、运行时、长任务恢复、视觉验收和禁止降级完成规则。读取并遵循 `${CLAUDE_PLUGIN_ROOT}/skills/meta-orchestration/40-qa/unattended-run-readiness-qa/SKILL.md`。
14. `.allforai/bootstrap/unattended-run-readiness.json` 和 `.allforai/bootstrap/unattended-run-readiness.md`：bootstrap 结束前运行一次：
    ```bash
    python3 .allforai/bootstrap/scripts/validate_unattended_readiness.py . --write-report
    ```
    允许 `status: "not_ready"`，但必须把 blocker 前置暴露给用户。`/run` 会再次执行同一检查；未 ready 时不得启动长任务。
15. `.allforai/bootstrap/protocols/*.md`
16. `.allforai/game-design/approval-records.json`：为每个 `human_gate: true` 的游戏设计节点初始化一条 `pending` 记录。**重建时（goals 包含 `create` 或 `rebuild`）如果文件已存在，重置所有记录为 `gate_status: "pending"`，清空 `approved_by`、`approved_at`、`reviewer_notes`、`revision_notes`。保留节点列表结构，但重置审批状态。**首次 bootstrap 时创建新文件。`human_gate: false` 的节点（art-concept、concept-freeze、architecture-concept-validation）不写入审批记录。
17. `.allforai/game-design/review-dashboard.html`：在生成 `approval-records.json` 后立即渲染，并且必须早于任何 game-design 节点执行：
    ```bash
    python3 .allforai/bootstrap/scripts/render_approval_dashboard.py \
      --approval .allforai/game-design/approval-records.json \
      --approval .allforai/app-design/approval-records.json \
      --workflow .allforai/bootstrap/workflow.json \
      --output .allforai/game-design/review-dashboard.html
    ```
    审批看板是实时审批操作界面。不要等到 `game-design-finalize` 才创建它；`game-design-dashboard.html` 只作为最终汇总产物。

### 6.4 Confirm Completion

If any scope, decision, audit or readiness gate blocks, report that status and
its specific missing input instead of the success text below. Keep unanswered
requirements pending for interactive bootstrap reentry; do not offer `/run` as ready.


```
Bootstrap 完成。

已写入 {count} 个文件：
  .allforai/bootstrap/bootstrap-profile.json
  .allforai/bootstrap/workflow.json
  .allforai/bootstrap/coverage-matrix.json (覆盖率: {coverage_rate})
  .allforai/bootstrap/node-specs/ ({node_count} 个节点)
  .allforai/bootstrap/unattended-run-readiness.md
  .claude/commands/run.md

现在可以使用 /run [目标] 执行工作流。例如：
  /run 逆向分析
  /run 复刻到 SwiftUI
  /run 代码治理
```

---
