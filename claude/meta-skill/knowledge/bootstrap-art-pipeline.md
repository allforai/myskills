# Art pipeline Protocol

Load this file only when the planned graph includes art-direction, art-concept, concept-freeze, art-gen, or art-qa.

Bootstrap does not invent this chain from memory. Follow the injection and node-spec contracts below.

**Art Concept Node Injection (always applies when `art-direction` is in the selected workflow):**

After inserting the `art-direction` node, also insert an `art-concept` node immediately following it:
- `node_id: "art-concept"`, `capability: "art-concept-skill"`, `human_gate: false`
- `hard_blocked_by: ["art-direction"]`; update `art-spec-design` to `hard_blocked_by: ["art-concept"]` (remove `art-direction` from its hard_blocked_by list)
- `unlocks: ["art-spec-design"]`
- **No approval-records entry** (art-concept is a skill invocation, not a human-reviewed document)
- **Node-spec content** for art-concept (write verbatim to `.allforai/bootstrap/node-specs/art-concept.md`):

```markdown
---
node_id: art-concept
human_gate: false
hard_blocked_by: [art-direction]
unlocks: [art-spec-design]
exit_artifacts:
  - .allforai/game-design/art-pipeline-config.json
  - .allforai/game-design/art/2d-art-style-taxonomy.html
  - .allforai/game-design/art/2d-art-style-taxonomy.json
  - .allforai/game-design/art/human-visual-preferences.json
  - .allforai/game-design/art/art-concept-validation.html
  - .allforai/game-design/art/art-concept-validation.json
  - .allforai/game-design/art/art-direction-benchmark.json
  - .allforai/game-design/art/art-direction-benchmark.md
---

# Task: 美术技术规格确认（Art Concept Skill Invocation）

## 执行方法

读取并执行 `${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/art-concept/SKILL.md` skill，完成交互式 Q&A 并产出 `art-pipeline-config.json`。

art-concept skill 完成后，依次调用以下 game-art 子 skill 细化策略（读取对应 SKILL.md 并执行）：

1. **2D 美术风格分类与偏好契约：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/2d-art-style-taxonomy/SKILL.md`
   - 输入：产品/游戏概念、已有美术偏好、项目摘要
   - 输出：`.allforai/game-design/art/2d-art-style-taxonomy.html`（中文，人类阅读）、`.allforai/game-design/art/2d-art-style-taxonomy.json`、`.allforai/game-design/art/human-visual-preferences.json`
   - 要求：在项目启动前向用户交代可选 2D 美术风格族、适合类型、生产成本、LLM 生图难度、LoRA/参考图/编辑模式需求、程序加工适配度、运行时风险和禁止风格；不得把具体项目标准写死到全局 skill。

2. **动画生产计划：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/2d-animation-production-plan/SKILL.md`
   - 输入：参见 SKILL.md 的 Invocation Contract
   - 输出：动画方案选择（帧动画/视频抽帧/姿态切换/Tween/混合）及降级路径。不得选择骨骼动画。

3. **动效设计**（当游戏有动效需求时，即 art-pipeline-config.json 中存在动画资产时）：`${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/motion-design/SKILL.md`
   - 输入：`art-pipeline-config.json`、`art-style-guide.json.art_overview`
   - 输出：关键帧意图、Timing 规则、可读性规范

4. **美术概念验证 HTML Gate：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/art-concept-validation/SKILL.md`
   - 输入：产品/游戏概念、美术方向输入契约、art-pipeline-config、style tokens 或 art-style-guide、人类偏好
   - 输出：`.allforai/game-design/art/art-concept-validation.html`（中文，人类阅读）和 `.allforai/game-design/art/art-concept-validation.json`
   - 要求：验证美术方向与产品概念、玩法可读性、目标受众、UI/世界观一致性、VFX/动效、运行时约束和人类偏好是否闭合；未通过则不得进入 concept-freeze / art-gen。

5. **美术导演基准：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/art-direction-benchmark/SKILL.md`
   - 输入：产品/游戏概念、美术方向输入契约、art-pipeline-config、人类偏好、style tokens
   - 输出：`.allforai/game-design/art/art-direction-benchmark.json` 和 `.allforai/game-design/art/art-direction-benchmark.md`
   - 要求：定义项目级商业视觉承诺、参考/反参考、视觉质量评分轴、资产家族标准、运行时截图标准和禁止通过项。这个基准回答“好不好看、像不像本游戏、有没有商业卖相”，不是回答“文件有没有生成”。

## 完成条件

`.allforai/game-design/art-pipeline-config.json` 存在且 `status == "final"`，
`.allforai/game-design/art/2d-art-style-taxonomy.html` 存在且为中文，
`.allforai/game-design/art/2d-art-style-taxonomy.json` 存在且 `status in ["ready", "pending_user_choice"]`，
`.allforai/game-design/art/art-concept-validation.html` 存在，
`.allforai/game-design/art/art-concept-validation.json` 存在且 `state in ["passed", "passed_with_warnings"]`，
`.allforai/game-design/art/art-direction-benchmark.json` 存在且 `status == "ready"`，
`.allforai/game-design/art/art-direction-benchmark.md` 存在。
```

**Concept Freeze Node Injection (applies when art-spec-design is in the selected workflow):**

After inserting `art-spec-design`, also insert a `concept-freeze` node immediately following it:
- `node_id: "concept-freeze"`, `capability: "concept-contract"`, `human_gate: false`
- `hard_blocked_by: ["art-spec-design"]`; update all art-gen nodes (`ai-art-generation`, `tile-art-gen`, `character-art-gen`, `environment-art-gen`, `vfx-art-gen`, etc.) to `hard_blocked_by: ["concept-freeze"]` (remove `art-spec-design` from their hard_blocked_by)
- `unlocks`: all art-gen nodes
- **No approval-records entry** (concept-freeze has `human_gate: false` — no discipline_owner review needed)
- **Node-spec content** for concept-freeze (write verbatim to `.allforai/bootstrap/node-specs/concept-freeze.md`):

```markdown
---
node_id: concept-freeze
human_gate: false
hard_blocked_by: [art-spec-design]
unlocks: []  # populated by bootstrap from workflow's art-gen nodes
exit_artifacts:
  - .allforai/concept-contract.json
  - .allforai/game-design/asset-registry.json
---

# Task: 概念合约冻结（Concept Freeze）

## 执行方法

读取并执行 `${CLAUDE_PLUGIN_ROOT}/knowledge/capabilities/concept-contract.md` capability，完成 canonical_registry 构建并写入 `concept-contract.json`。

concept-contract capability 完成后，依次调用以下 game-art 子 skill（读取对应 SKILL.md 并执行）：

1. **工具能力检测：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/production-tool-capability-registry/SKILL.md`
   - （输入/输出：参见 SKILL.md 的 Invocation Contract）
   - 将检测结果写回 `art-pipeline-config.json.toolchain.detected_capabilities`

2. **资产注册表初始化：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/asset-registry/SKILL.md`
   - （输入/输出：参见 SKILL.md 的 Invocation Contract）
   - 输出：`.allforai/game-design/asset-registry.json`（以 canonical_registry 为权威，资产 ID → 文件前缀 → 生命周期状态的单一可信注册表）

3. **2D 动画工具链检测：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/00-env/2d-animation-toolchain-env/SKILL.md`
   - （输入/输出：参见 SKILL.md 的 Invocation Contract；依赖动画生产计划与 `asset-registry.json`）
   - 当动画生产计划包含 `frame_animation`、`motion_video_to_sprite`、`pose_swap`、`ui_tween` 或 `vfx_only` 时，验证帧动画/视频抽帧/图集/预览/运行时导入工具链；缺少必需工具时返回 `blocked_by_missing_toolchain`，不得让下游动画节点假装完成。
   - Canonical remap：`skeletal_animation` / `dragonbones` / `dragonbones_mesh` / `spine` / `skeletal_3d` / `3d_skeletal` / `part_tween` → `animation_system=frame`、`character.rig=frame_sequence`、`animation_method=frame_animation`。`dimension=3d` → `2d`。记录 remap，并在 Phase A 摘要里向用户明示一次（这是管线能力约束，不是可选路线：3D 资产无法生成，所以不摆成选项，但也不许只写在 registry 里让人事后才发现）；不得继续骨骼或 3D 网格动画生产。

4. **资产来源策略：** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/10-design/asset-source-strategy-spec/SKILL.md`
   - （输入/输出：参见 SKILL.md 的 Invocation Contract；依赖上一步生成的 `asset-registry.json`）
   - 输出：每类资产的 `source_strategy`（`existing_asset_pack` / `existing_3d_source_asset` / `user_provided_asset` / `adapt_existing_asset` / `hybrid` / `placeholder_only`）写入 `asset-registry.json`

## 完成条件

`.allforai/concept-contract.json` 存在且 `schema_version == "1.0"` 且 `.allforai/game-design/asset-registry.json` 存在。
如果 `.allforai/game-design/art/art-concept-validation.json` 不存在或状态不是 `passed` / `passed_with_warnings`，必须返回 `UPSTREAM_DEFECT`，不得冻结概念或推进 art-gen。

## 重要说明

所有后续 art-gen 节点必须从 `concept-contract.json` 读取 `canonical_registry`，使用其中的 `file_prefix` 作为生成文件的命名权威来源，不得自行命名。
```

**Art-Gen Node Injection (when `art-spec-design` and `concept-freeze` are in the selected workflow):**

After injecting `concept-freeze`, read `art-pipeline-config.json.active_nodes` and inject one node-spec per entry. Use the sub-skill mapping table below to determine which `game-art` sub-skills each node-spec should delegate to.

**Sub-Skill Mapping Table:**

| `node_id` | Pre-Spec Sub-Skills (read first) | Generate Sub-Skills (run after) | Condition |
|-----------|----------------------------------|--------------------------------|-----------|
| `tile-art-gen` | `skills/game-art/20-spec/tileset-spec/SKILL.md` | `skills/game-art/30-generate/tileset-generation/SKILL.md` | always |
| `tile-art-gen` | + `skills/game-art/20-spec/2-5d-production-mode-spec/SKILL.md` + `skills/game-art/20-spec/2-5d-lighting-shadow-spec/SKILL.md` | + `skills/game-art/30-generate/render-to-2d-asset-generation/SKILL.md` | when `dimension=2.5d` |
| `character-art-gen` | `skills/game-art/00-env/2d-animation-toolchain-env/SKILL.md` + `skills/game-art/20-spec/visual-style-tokens/SKILL.md` + `skills/game-art/20-spec/frame-animation-spec/SKILL.md` | `skills/game-art/30-generate/frame-animation-generation/SKILL.md` | always. Apply canonical remap first. Do not invoke `character-layer-sheet` by default. |
| `character-art-gen` | + `skills/game-art/20-spec/character-layer-sheet/SKILL.md` | — | only when `art-pipeline-config.json` `character.use_layer_sheet === true` from an explicit art-concept user choice. Invented outfit/skin fields are not enough. Not a rig. |
| `character-art-gen` | same default pre-spec | + `skills/game-art/30-generate/motion-video-to-sprite-animation/SKILL.md` | when the animation plan selects `motion_video_to_sprite` |
| `character-art-gen` | — | + `skills/game-art/30-generate/expression-set-generation/SKILL.md` | when `character.expressions=true` (append after primary generate) |
| `environment-art-gen` | `skills/game-art/20-spec/2d-view-mode-spec/SKILL.md` | `skills/game-art/30-generate/background-generation/SKILL.md` + `skills/game-art/30-generate/prop-generation/SKILL.md` | always |
| `environment-art-gen` | + `skills/game-art/20-spec/3d-source-asset-spec/SKILL.md` | + `skills/game-art/30-generate/render-to-2d-asset-generation/SKILL.md` | when `dimension=2.5d` only. Remap `dimension=3d` to `2d` and skip this row. |
| `ui-art-gen` | `skills/game-ui/00-env/ui-registry/SKILL.md` + `skills/game-ui/10-design/hud-information-design/SKILL.md` + `skills/game-ui/20-spec/component-state-spec/SKILL.md` + `skills/game-ui/20-spec/screen-layout-spec/SKILL.md` + `skills/game-art/20-spec/visual-style-tokens/SKILL.md` | `skills/game-ui/30-generate/ui-mockup-generation/SKILL.md` + `skills/game-art/30-generate/icon-generation/SKILL.md` | always |
| `ui-art-gen` | — | + `skills/game-art/30-generate/portrait-generation/SKILL.md` | when `concept_art.needed=true` |
| `vfx-art-gen` | `skills/game-art/20-spec/vfx-spec/SKILL.md` | `skills/game-art/30-generate/vfx-generation/SKILL.md` | always |
| `vfx-art-gen` | — | + `skills/game-art/30-generate/particle-system/SKILL.md` | when `vfx.approach` includes `particle` |
| `vfx-art-gen` | — | + `skills/game-art/30-generate/sprite-vfx-generation/SKILL.md` | when `vfx.approach` includes `sprite` or `spritesheet` |
| `vfx-art-gen` | — | + `skills/game-art/30-generate/shader-vfx-generation/SKILL.md` | when `vfx.approach` includes `shader` |
| `vfx-art-gen` | — | + `skills/game-art/30-generate/trail-generation/SKILL.md` | when `vfx.approach` includes `trail` |
| `vfx-art-gen` | — | + `skills/game-art/30-generate/screen-effect-generation/SKILL.md` | when `vfx.approach` includes `screen` or `postprocess` |
| `vfx-art-gen` | — | + `skills/game-art/30-generate/light-pulse-generation/SKILL.md` | when `vfx.approach` includes `light` |
| `vfx-art-gen` | — | + `skills/game-art/30-generate/decal-generation/SKILL.md` | when `vfx.approach` includes `decal` |
| `vfx-art-gen` | — | + `skills/game-art/30-generate/animation-event-fx/SKILL.md` | when VFX must bind to animation events |

**Node-spec template for each `active_node` entry:**

Write `.allforai/bootstrap/node-specs/<node_id>.md` using this template, substituting `<TYPE>`, `<REGISTRY_KEY>`, `<CONFIG_SECTION>`, and `<DISCIPLINE_OWNER>` from the table below:

| `node_id` | `<TYPE>` | `<REGISTRY_KEY>` | `<CONFIG_SECTION>` | `<DISCIPLINE_OWNER>` |
|-----------|----------|-----------------|-------------------|---------------------|
| `tile-art-gen` | tile | `tiles` | `tileset` | `concept-artist` |
| `character-art-gen` | character | `characters` | `character` | `character-modeler` |
| `environment-art-gen` | environment | `environments` | `environment` | `environment-artist` |
| `ui-art-gen` | UI | `ui` + `other` | _(all remaining)_ | `ui-artist` |
| `vfx-art-gen` | VFX | `vfx` | `vfx` | `vfx-artist` |

```markdown
---
node_id: <node_id>
human_gate: true
hard_blocked_by: [concept-freeze]
unlocks: [art-qa]
exit_artifacts:
  - path: .allforai/game-design/<node_id>-review.html
  - path: .allforai/game-design/systems/<node_id>-spec.json
---

# Goal

Generate <TYPE> art assets for all entries in `.allforai/concept-contract.json` `canonical_registry.<REGISTRY_KEY>[]`.

## Inputs

- `.allforai/concept-contract.json` — `canonical_registry.<REGISTRY_KEY>[]` (authoritative asset IDs and `file_prefix` values; do not invent your own names)
- `.allforai/game-design/art-pipeline-config.json` — `<CONFIG_SECTION>` configuration and `toolchain.detected_capabilities`
- `.allforai/game-design/art-asset-inventory.json` — current asset states (skip assets with `current_state == "locked"`)
- `.allforai/game-design/asset-registry.json` — canonical registry built by concept-freeze
- `.allforai/game-design/art/asset-acceptance-criteria.json` — project/runtime-specific standard for this node's assets
- `.allforai/game-design/art/2d-art-style-taxonomy.json` — selected style family, avoid styles, LLM fit, processing fit, and user-facing preference contract
- `.allforai/game-design/art/programmatic-art-processing-plan.json` — material-first processing rules for raw materials, assembly, previews, and runtime outputs

## Sub-Skill Invocation

Read and follow each sub-skill SKILL.md in order. Each sub-skill defines its own output contract — follow it exactly.

### Step -1 — Project Art Generation Specialization

Before resolving per-asset sources, evaluate
`${CLAUDE_PLUGIN_ROOT}/knowledge/domains/game-genre-specialization.md`
§Art Generation Specialization. If this project or node requires
family-level or play-surface-specific art generation rules, generate or read
the project-local specialized skill at
`.allforai/bootstrap/specialized-skills/<specialization_id>-art-generation/SKILL.md`.

Use it to define node-local prompt templates, model profile preferences,
preview validation contexts, and repair routing. This project-local skill must
still route concrete generation through the bundled source strategy,
image-model-capability-registry, image-generation-contract, accepted-image
manifest, style QA, and runtime import contracts.

### Step -0.5 — Asset Acceptance Criteria

Before any image generation, source adaptation, 3D render-to-2D output, atlas
packaging, or visual QA, invoke
`${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/asset-acceptance-criteria/SKILL.md`.
This writes `.allforai/game-design/art/asset-acceptance-criteria.json` and
`.allforai/game-design/art/asset-acceptance-criteria.md`.

The criteria must combine project-specific standards from the specialized
art-generation skill with technology-specific standards from the target runtime,
engine export profile, atlas/import rules, view mode, and platform. Do not use
generic visual standards when the project type or runtime imposes different
requirements.

### Step -0.4 — Programmatic Art Processing Plan

Before prompt compilation or direct image generation, invoke
`${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/programmatic-art-processing-plan/SKILL.md`.
This writes `.allforai/game-design/art/programmatic-art-processing-plan.json`
and `.allforai/game-design/art/programmatic-art-processing-plan.md`.

The default policy is `material_first`: ask LLM/image/search sources for raw
materials that deterministic tools can layer, assemble, recolor, atlas, animate,
decorate, mask, componentize, or preview into runtime assets. Direct final-image
generation is an exception and must be justified in the plan. If required
automatable processing tools are missing, block with the missing capability
instead of silently accepting lower-quality final images.

### Step 0 — Source Resolution (per asset, before Pre-Spec)

For each asset in `canonical_registry.<REGISTRY_KEY>[]`, check its `source_strategy` from `asset-registry.json`:

- **`existing_asset_pack`:**
  1. `${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/asset-pack-search-spec/SKILL.md` — search and select candidate pack
  2. `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-license-provenance-qa/SKILL.md` — verify license; if FAIL → fall back to `ai_generated` for this asset and proceed to Step 1
  3. `${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/existing-asset-adaptation-spec/SKILL.md` — adapt to spec
  4. Mark asset `current_state: adapted`; skip Step 1 and Step 2 for this asset.

- **`adapt_existing_asset`:**
  1. `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-license-provenance-qa/SKILL.md` — verify license; if FAIL → fall back to `ai_generated` and proceed to Step 1
  2. `${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/existing-asset-adaptation-spec/SKILL.md` — adapt to spec
  3. Mark asset `current_state: adapted`; skip Step 1 and Step 2 for this asset.

- **`existing_3d_source_asset` / `user_provided_asset`:**
  1. `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-license-provenance-qa/SKILL.md` — verify license; if FAIL → halt with UPSTREAM_DEFECT (user-provided assets cannot silently fall back)
  2. Proceed to Step 1 (pre-spec for rendering/conversion pipeline).

- **`ai_generated` / `hybrid` / `placeholder_only`:** skip Step 0, proceed directly to Step 1.

### Step 1 — Pre-Spec

<List the pre-spec sub-skill paths from the mapping table above for this node_id, with conditions. Skip for assets that completed Step 0 and are already marked `adapted`.>

### Step 1.5 — Prompt Compilation And Batch Plan

For every asset still using `ai_generated`, `image_edit`, or `hybrid`
production, invoke:

1. `${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/image-prompt-compiler/SKILL.md`
   - 输出：`.allforai/game-design/art/image-generation/compiled-prompt-manifest.json` 和 prompt 文件目录
   - 要求：按资产类型、风格基准、验收标准、模型路由、LoRA/参考图锁定和程序加工计划编译 prompt；不得使用临时自由 prompt。
2. `${CLAUDE_PLUGIN_ROOT}/skills/game-art/20-spec/image-batch-generation-plan/SKILL.md`
   - 输出：`.allforai/game-design/art/image-generation/image-batch-generation-plan.json` 和 `.md`
   - 要求：按资产家族、模型能力、prompt 模板、候选数量、重试预算和 material-first 策略分批；覆盖不足必须触发下一批或保持阻塞。

### Step 2 — Generate

<List the generate sub-skill paths from the mapping table above for this node_id, with conditions. Skip for assets already marked `adapted`.>

After batch generation, invoke
`${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/generated-candidate-selection/SKILL.md`
before any downstream consumer reads images. Raw MCP/image outputs are candidates
only. They may enter `.allforai/game-design/art/image-generation/accepted-image-manifest.json`
with `consumer_ready: true` only after selection verifies visual evidence,
processing readiness, coverage, and acceptance criteria.

## Completion Condition

`.allforai/game-design/systems/<node_id>-spec.json` exists AND `.allforai/game-design/<node_id>-review.html` exists AND `.allforai/game-design/art/programmatic-art-processing-plan.json` exists AND `.allforai/game-design/art/image-generation/compiled-prompt-manifest.json` exists when generation is required AND `.allforai/game-design/art/image-generation/image-batch-generation-plan.json` exists when batch generation is required AND `.allforai/game-design/art/image-generation/generated-candidate-selection-report.json` exists when new images were generated AND `.allforai/game-design/art/image-generation/accepted-image-manifest.json` contains entries for this node's produced/adapted bitmap assets with `consumer_ready: true` AND the referenced image files exist.

Spec-only, manifest-only, or path-existence-only output is not a completed art-gen node. If the node is expected to generate, adapt, search, register, or render images and no actual visual evidence exists, return `FAILED_VALIDATION` or `blocked_by_missing_visual_evidence`; do not advance to `art-qa`.

If any sub-skill returns `UPSTREAM_DEFECT` → halt and report the defect. Do not advance to `art-qa`.
```

**Key rules for art-gen injection:**
- `hard_blocked_by: ["concept-freeze"]` for ALL art-gen nodes (regardless of type)
- `unlocks: ["art-qa"]` for ALL art-gen nodes
- `human_gate: true` for ALL art-gen nodes (discipline-specific approval required)
- `approval_record_path: ".allforai/game-design/approval-records.json"` for ALL art-gen nodes
- `review_checklist`: use the checklist from `game-design.md` canonical registry table
- Do NOT inject a node-spec for entries in `skipped_nodes` — only `active_nodes` get node-specs

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
node_id: art-qa
human_gate: true
hard_blocked_by: []  # populated by bootstrap: all active art-gen node IDs
unlocks: [game-design-finalize]
exit_artifacts:
  - path: .allforai/game-design/art-qa-report.html
  - path: .allforai/game-design/art/qa/asset-family-consistency-report.json
  - path: .allforai/game-design/art/qa/asset-family-consistency-report.md
  - path: .allforai/game-design/art/qa/in-game-beauty-gate-report.json
  - path: .allforai/game-design/art/qa/in-game-beauty-gate-report.md
  - path: .allforai/game-design/art/export/engine-ready-art-output-contract.json
  - path: .allforai/game-runtime/art/engine-ready-art-manifest.json
---

# Goal

Run quality assurance across all generated art assets. Invoke the appropriate game-art QA sub-skills and aggregate results into `art-qa-report.html`.

## Inputs

- `.allforai/concept-contract.json` — `canonical_registry` (all types)
- `.allforai/game-design/art-pipeline-config.json` — `dimension`, `style`, `vfx.approach`
- `.allforai/game-design/systems/` — all `*-art-spec.json` outputs from art-gen nodes
- `.allforai/game-design/art-style-guide.json` — visual style reference
- `.allforai/game-design/art/art-direction-benchmark.json` — project-specific benchmark for commercial visual quality, family cohesion, anti-reference rejection, and runtime screenshot beauty

## Sub-Skill Invocation

Read and follow each applicable sub-skill SKILL.md in order:

1. **Preview evidence (always):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/art-preview-qa/SKILL.md`
2. **Visual acceptance batch documents + two independent review documents (Codex CLI and Claude Code) + reconciliation + closure audit (always for generated/adapted bitmap assets):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/visual-acceptance-review/SKILL.md`
3. **Asset family consistency (always):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-family-consistency-qa/SKILL.md`
4. **Style consistency (always):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/2d-style-consistency-qa/SKILL.md`
5. **UI readability** (when `ui-art-gen` ran): `${CLAUDE_PLUGIN_ROOT}/skills/game-ui/40-qa/ui-readability-qa/SKILL.md`
6. **Atlas packaging (always):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/atlas-packaging/SKILL.md`
7. **Runtime import (always):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/runtime-import-check/SKILL.md`
8. **In-game beauty gate (always when runtime screenshots can be captured):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/in-game-beauty-gate/SKILL.md`
9. **3D-assisted QA** (when `dimension=2.5d`): `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/3d-assisted-2d-qa/SKILL.md`
10. **Asset pack QA** (when any asset has `source_strategy=existing_asset_pack`): `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-pack-integration-qa/SKILL.md`
11. **License provenance sweep** (always, as final audit): `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/asset-license-provenance-qa/SKILL.md` — for external-source assets this is a confirmation sweep (primary check already ran in art-gen Step 0); for AI-generated assets this catches potential training-data IP issues
12. **Engine-ready art handoff (always):** `${CLAUDE_PLUGIN_ROOT}/skills/game-art/40-qa/engine-ready-art-output-contract/SKILL.md`

## Completion Condition

`art-qa-report.html` exists, `.allforai/game-runtime/art/engine-ready-art-manifest.json` exists, `.allforai/game-design/art/qa/visual-acceptance-task-list.json` exists, `.allforai/game-design/art/qa/visual-acceptance-batches/` contains Markdown batch documents, `.allforai/game-design/art/qa/codex-visual-review.json` exists, `.allforai/game-design/art/qa/codex-visual-review.md` exists, `.allforai/game-design/art/qa/claude-code-visual-review.json` exists, `.allforai/game-design/art/qa/claude-code-visual-review.md` exists, `.allforai/game-design/art/qa/visual-review-reconciliation.json` exists, `.allforai/game-design/art/qa/visual-review-closure-audit.json` exists, `.allforai/game-design/art/qa/visual-review-closure-audit.md` exists, `.allforai/game-design/art/qa/asset-family-consistency-report.json` exists with `status == "passed"`, `.allforai/game-design/art/qa/in-game-beauty-gate-report.json` exists with `status == "passed"` when runtime screenshots are available, and if either reviewer found a blocker/major visual issue then `.allforai/game-design/art/qa/visual-repair-loop-report.json` and `.allforai/game-design/art/qa/visual-repair-loop-report.md` exist showing regenerate/repair plus rerun of both independent visual reviews, reconciliation, and Claude Code closure audit for affected batches. No sub-skill may return `UPSTREAM_DEFECT`, `FAILED_VALIDATION`, `blocked_by_missing_visual_evidence`, `blocked_by_missing_codex_cli`, `blocked_by_missing_runtime_screenshots`, `quality_gaps`, `visual_quality_gaps`, `beauty_gaps`, or `runtime_visual_gaps`.

`COMPLETED_WITH_LIMITS` cannot pass art-qa when the limit is missing images, missing contact sheets, missing screenshots, missing Codex CLI visual review, missing Claude Code visual review, missing reconciliation, or missing Claude Code closure audit.

**Gate action on any art QA failure:**
For each failing asset, asset family, or runtime screenshot, first execute the
visual repair loop. The loop must write an owner-specific feedback report
(`image-feedback-report.json` for image-owned failures,
`.allforai/game-frontend/qa/runtime-visual-feedback-report.json` for
runtime/UI-owned failures, or an equivalent import/binding feedback report),
repair the narrowest upstream owner, rebuild affected previews/contact sheets or
runtime screenshots, rerun both independent visual reviews for the affected evidence,
and rerun the specific QA gate that failed. Append every iteration to
`.allforai/game-design/art/qa/visual-repair-loop-report.json` and
`.allforai/game-design/art/qa/visual-repair-loop-report.md`.

If the issue still fails after the repair budget, set
`gate_status: "revision-requested"` in
`.allforai/game-design/approval-records.json` for the relevant art-gen or
runtime/frontend node, and populate `revision_notes` with the QA sub-skill's
issue list. The orchestrator will re-run that node with `revision_notes` as
context. Do not let `art-qa` unlock `game-design-finalize` or engine-ready art
handoff while `quality_gaps`, `visual_quality_gaps`, `beauty_gaps`, or
`runtime_visual_gaps` remain.
```

