# Skeletal Animation Skill

> Internal sub-skill for game art pipelines.
> Status: bundled, inactive, not wired.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

This sub-skill defines the production protocol for skeletal animation assets in
game projects. It covers 2D DragonBones-style animation and 3D skeletal
animation, with v1 optimized for 2D DragonBones because its JSON and atlas
outputs are more AI-addressable than full 3D character animation.

The skill turns approved art direction and character asset requirements into:
- a skeletal animation production plan,
- layered character reference specifications,
- skeleton overlay specifications,
- pose keyframe image specifications,
- DragonBones transform animation specifications,
- automated fallback specifications for complex rigging or mesh deformation.

The most important responsibility of this skill is to lock the creative workflow:
how a static character design becomes a rigged, animated game asset without
skipping the design decisions that make animation readable.

## Scope

Use this skill when a game art pipeline needs skeletal animation for characters,
simple animated props, or transform-based VFX.

In scope:
- 2D DragonBones character rig planning.
- 2D layered character reference image prompts and specs.
- Skeleton overlay and pivot-point diagrams.
- Pose keyframe sheet specifications.
- AI-generatable DragonBones transform animation JSON specs.
- Automated downgrade rules for complex IK, mesh deformation, or hand-authored
  animation requests.
- 3D skeletal animation planning at the specification level.

Out of scope for v1:
- Directly producing final DragonBones project files.
- Directly producing polished final animation atlases.
- High-quality 3D character modeling, skinning, or mocap cleanup.
- Pixel-art skeletal animation; pixel projects should use frame animation.
- Any requirement that depends on a human artist, animator, reviewer, or
  external manual approval.

## Input Contract

The node invoking this skill must provide enough information to decide what to
animate, how it should move, and how outputs should be named. Inputs are split
into required, optional, and inferred values.

### Required inputs

| Input | Required fields | Missing behavior |
|---|---|---|
| `.allforai/game-design/art-style-guide.json` | `art_overview.dimension`, `art_overview.style`, `art_overview.animation_system` | Return `UPSTREAM_DEFECT`; cannot choose animation branch. |
| `.allforai/game-design/art-pipeline-config.json` | `character.rig` for 2D, or `model_3d.anim_source` for 3D | Return `UPSTREAM_DEFECT`; cannot choose rig strategy. |
| `.allforai/game-design/art-asset-inventory.json` | `assets[].asset_id`, `assets[].type`, `assets[].name` | Return `UPSTREAM_DEFECT`; cannot select animated assets. |

### Required per-asset fields

Each selected animated asset must resolve these fields from inventory,
concept-contract, or node-spec context:

| Field | Purpose | Default / fallback |
|---|---|---|
| `asset_id` | Stable canonical id. | No fallback; missing means `UPSTREAM_DEFECT`. |
| `name` | Human-readable display name used in reports. | Use `asset_id` title-cased. |
| `file_prefix` | Deterministic output naming. | Use concept-contract prefix; fallback to `asset_id`. |
| `asset_type` | Character, prop, VFX, or 3D actor. | Use inventory `type`; unsupported types are ignored. |
| `gameplay_role` | Player, enemy, NPC, prop, boss, mascot, etc. | Infer from asset tags/name; if unsafe, use `generic_character`. |
| `target_view` | front, side, 3/4, top-down, isometric. | Infer from art direction; fallback `front`. |
| `scale_class` | small sprite, normal character, boss, UI mascot. | Fallback `normal_character`. |

### Optional inputs

| Input | Fields used | Fallback |
|---|---|---|
| `.allforai/concept-contract.json` | `canonical_registry.*[].asset_id`, `file_prefix` | Use `asset_id` as file prefix and set `source.used_concept_contract=false`. |
| Existing character reference image | silhouette, costume, proportions | Generate prompt/spec only; do not require image. |
| Existing layer sheet | part boundaries | Reuse if filenames match `file_prefix`; otherwise generate new spec. |
| Existing runtime/engine info | DragonBones runtime, Cocos, Phaser, Unity, Godot | Use neutral transform schema and browser/scripted preview. |
| Requested animation list | animation ids, durations, gameplay events | Infer from `gameplay_role`. |

### Inferred animation defaults

If no animation list is provided, infer this baseline:

| Gameplay role | Default animations |
|---|---|
| `player` | `idle`, `walk`, `run`, `attack`, `hit`, `death`, `interact` |
| `enemy` | `idle`, `walk`, `attack`, `hit`, `death` |
| `boss` | `idle`, `walk`, `attack`, `skill`, `hit`, `death` |
| `npc` | `idle`, `talk`, `gesture` |
| `prop` | `idle`, `activate`, `break` |
| `ui_mascot` | `idle`, `bounce`, `celebrate` |

If `concept-contract.json` is present, all filenames MUST use its
`file_prefix`. If missing, use `asset_id` as the fallback prefix and record the
fallback in the output plan.

### Input normalization

Before running the creative workflow, build an internal normalized input object:

```json
{
  "schema_version": "1.0",
  "project_art": {
    "dimension": "2d | 3d | 2.5d",
    "style": "cartoon | realistic | hand_drawn | vector | pixel",
    "animation_system": "dragonbones | 3d_skeletal | mixed"
  },
  "rig_strategy": "dragonbones | dragonbones_mesh | 3d_skeletal | not_applicable",
  "assets": [
    {
      "asset_id": "<required>",
      "name": "<resolved>",
      "file_prefix": "<resolved>",
      "asset_type": "character | prop | vfx | actor_3d",
      "gameplay_role": "<resolved>",
      "target_view": "<resolved>",
      "scale_class": "<resolved>",
      "requested_animations": []
    }
  ],
  "tooling": {
    "render_runtime": "browser_canvas | dragonbones_runtime | scripted_2d_transform | none",
    "vision_validator_available": true
  }
}
```

If normalization fails, write no partial creative outputs; return `UPSTREAM_DEFECT`
with the missing field list.

## Decision Rules

1. If `art_overview.style == "pixel"`, stop with `NOT_APPLICABLE` and recommend
   frame-sequence animation.
2. If `art_overview.dimension == "2d"` and `character.rig` is `dragonbones` or
   `dragonbones_mesh`, use the 2D DragonBones pipeline.
3. If `art_overview.dimension == "3d"` or `animation_system == "3d_skeletal"`,
   use the 3D skeletal planning pipeline.
4. If `character.rig == "frame_sequence"`, stop with `NOT_APPLICABLE` and
   recommend frame animation.
5. Treat transform-only animations as AI-generatable.
6. Treat IK, mesh deformation, cloth, hair simulation, facial blend shapes,
   complex weapon trails, and particle path choreography as automation-limited.
   Replace them with simplified transform animation, key pose references, or
   placeholder motion. Do not route to human review.

## No-Human Rule

This sub-skill must be fully self-contained and automatic. It must not require
human references, human approval, animator judgment, artist cleanup, or manual
tool operation to complete its own outputs.

Allowed:
- Infer missing creative details from upstream artifacts when safe.
- Render generated animation previews with available local tools or browser
  runtimes, then use visual validation to repair the spec.
- Produce simplified automated animation instead of complex final animation.
- Produce placeholder animation specs when final-quality automation is not
  feasible.
- Mark an item `automation_limited` with an explicit automatic fallback.
- Return `UPSTREAM_DEFECT` only when required source artifacts are missing and no
  reasonable fallback exists.

Forbidden:
- Asking the user or a human artist to decide animation content.
- Emitting human work orders.
- Marking anything as waiting for animator, artist, manual rigging, or manual
  approval.
- Depending on external human reference images not already present in the
  project artifacts.
- Claiming final-quality output for effects that the automated pipeline cannot
  produce.

## Image Generation Upstream Contract

When this skill requests layer sheets, skeleton overlays, pose keyframe sheets,
or visual reference images, each bitmap request must follow
`game-art/30-generate/image-generation-contract/SKILL.md`.

Use normalized image requests with `purpose=layer_sheet`, `pose_reference`, or
`preview`. The request must include asset id, file prefix, target view,
animation id when relevant, style source, output path, positive prompt, negative
prompt, pose/readability checks, crop checks, and
`downstream_feedback.enabled=true`.

If rig planning, preview rendering, pose validation, or runtime import reports
`MISSING_REQUIRED_PART`, `MERGED_PARTS`, `WRONG_VIEW`, `CROPPED_SUBJECT`,
`LOW_READABILITY`, `STYLE_DRIFT`, or `WRONG_SCALE`, route the defect through
`image-generation-contract`. Regenerate only the failed image request when root
cause is `image_generation` or `prompt_contract`; otherwise repair the
downstream animation spec.

## Creative Workflow

The skeletal animation workflow has eight fixed stages. Do not skip stages even
when final assets are not being generated yet. If a stage cannot be completed,
write the unresolved decision into the output plan and mark downstream work as
blocked, automation-limited, or not applicable.

| Stage | Purpose | Main output |
|---|---|---|
| 1. Animation intent | Decide what the animation must communicate in gameplay. | `animation_intent[]` |
| 2. Motion vocabulary | Choose animation ids, loops, durations, and priority. | `animation_set[]` |
| 3. Character decomposition | Split the static design into animatable visual parts. | `parts[]`, `layer_sheet_prompt` |
| 4. Rig design | Define bones, hierarchy, pivots, constraints, and z-order. | `bones[]`, `constraints[]` |
| 5. Key pose design | Define readable silhouette poses for each animation. | `pose_keyframes` specs |
| 6. Timing and curves | Define frame timing, easing, holds, anticipation, and follow-through. | `timelines[]` |
| 7. Render and preview | Render tool-generated frames/GIF/HTML preview when possible. | rendered preview files + `animation-preview-spec.json` |
| 8. Visual QA and repair | Use deterministic checks plus visual validation; repair until passing or capped. | QA report, repair log, fallback decisions |

The workflow is closed-loop: every stage has machine-checkable acceptance rules,
and every failed rule has a deterministic next action. A node running this skill
must not mark itself complete merely because output files exist.

## Closed Loop and Automatic Acceptance

### State model

Track each asset and each animation with one of these states:

| State | Meaning | Next action |
|---|---|---|
| `planned` | Required by inventory but not specified yet. | Run the next missing workflow stage. |
| `spec_ready` | Text spec exists and passes automatic checks. | Generate or request reference outputs. |
| `reference_ready` | Image/reference specs exist or generated files are present. | Build timeline and render preview. |
| `preview_ready` | Rendered preview exists or preview spec explains why rendering is unavailable. | Run deterministic and visual QA. |
| `approved` | Automatic checks pass and no automation blocker remains. | Downstream art-gen can consume it. |
| `needs_revision` | Automatic check failed but can be fixed by spec revision. | Re-run the failed stage only. |
| `automation_limited` | Requested motion exceeds automated capability. | Emit simplified fallback and mark limits. |
| `not_applicable` | Skeletal animation is inappropriate. | Route to frame animation or static asset flow. |

### Stage acceptance rules

| Stage | Automatic acceptance | Failure action |
|---|---|---|
| Animation intent | Every selected asset has `intent`, `readability_priority`, `exaggeration`, and `interrupt_policy`. | Mark asset `needs_revision`; return `UPSTREAM_DEFECT` if gameplay role is missing and cannot be inferred. |
| Motion vocabulary | Every animation has id, gameplay state, loop flag, duration, priority, interrupt policy, and production mode. | Infer baseline set from role once; if still incomplete, mark `needs_revision`. |
| Character decomposition | Every required animation references at least one moving part; every moving part has `part_id`, `z_order`, `pivot_hint`. | Add missing parts or mark animation `automation_limited` with simplified fallback. |
| Rig design | Bone graph has one root, no cycles, every non-root bone has an existing parent, every moving part binds to a bone. | Rebuild hierarchy; if impossible from current art, reduce to transform-only placeholder. |
| Key pose design | Every animation has minimum required poses and a stated silhouette/readability target. | Add missing poses; if acting complexity is high, switch production mode to `keyframe_reference` or `automation_limited`. |
| Timing and curves | Duration is in allowed range, keyframes are sorted, loop animations end on start pose, event frames fall within duration. | Normalize timing; if gameplay event timing is unknown, mark `needs_revision`. |
| Render and preview | Every animation has a rendered preview when tooling is available; otherwise it has a deterministic preview spec and fallback. | Generate preview, or record tool absence and use static keyframe validation. |
| Visual QA and repair | Deterministic checks pass; visual validation passes or repair attempts are exhausted with fallback ready. | Apply repair loop; then mark `approved`, `needs_revision`, or `automation_limited`. |

### Automatic validation checks

A runner or future script can validate the generated JSON with these deterministic
checks:

1. **ID consistency**: every `asset_id` exists in inventory or concept contract.
2. **Filename consistency**: every output path starts with the selected
   `file_prefix`.
3. **Part uniqueness**: no duplicate `part_id` per asset.
4. **Bone validity**: exactly one root; no cycles; all parents exist.
5. **Part binding**: every animated part is bound to at least one bone.
6. **Animation completeness**: every animation has production mode, duration,
   loop flag, key poses, timeline, preview, and fallback.
7. **Timing validity**: keyframe times are sorted, non-negative, and within
   `duration_ms`.
8. **Loop validity**: looped animations state how the final pose returns to the
   first pose.
9. **Automation honesty**: any animation using IK, mesh deformation, facial
   acting, cloth/hair simulation, or complex trails is not marked
   `ai_transform_json` unless represented as a simplified transform fallback.
10. **Pixel guard**: pixel-art projects are marked `not_applicable`.

### Tool render and visual validation loop

When a render path is available, complex actions should be attempted through a
render-and-validate loop before being marked `automation_limited`.

Render targets, in order of preference:

| Target | Use when | Preview output |
|---|---|---|
| Browser canvas / game runtime | Runtime can load generated JSON or a neutral transform schema. | HTML preview + PNG screenshots. |
| DragonBones-compatible runtime | DragonBones JSON and atlas are available. | frame sequence or GIF. |
| Scripted 2D transform renderer | Only part images and transform timelines exist. | transparent PNG frames + GIF. |
| Static keyframe board | No animation renderer exists. | keyframe sheet only; mark render unavailable. |

Loop:

1. Generate or update animation spec.
2. Render 3-8 representative frames plus one loop GIF when tooling exists.
3. Run deterministic checks.
4. Run visual validation on rendered frames/GIF:
   - body parts remain connected,
   - pivot points look plausible,
   - silhouette is readable,
   - attack/contact frame is visually distinct,
   - loop returns to the start pose without visible snap,
   - no unintended overlap hides important parts,
   - motion intensity matches `exaggeration`.
5. If validation fails, write a repair note and modify only the failing stage
   (`parts`, `bones`, `key_poses`, or `timeline`).
6. Re-render and re-validate.
7. Stop after 3 repair attempts per animation. If still failing, create a
   simplified fallback and mark the animation `automation_limited`.

Visual validation may be done by an LLM with image understanding. The validator
must judge rendered outputs, not only the JSON spec.

### Closure report

Always write a closure summary into `skeletal-animation-plan.json.acceptance`.
The node is complete only when the summary verdict is one of:
- `approved`: all required assets and animations are fully specified and pass
  automatic checks.
- `approved_with_automation_limits`: automatic parts pass, automation limits are
  documented, and fallback placeholders exist.
- `not_applicable`: skeletal animation was correctly rejected and a substitute
  animation path is named.

The node is not complete when verdict is:
- `needs_revision`,
- `blocked_by_missing_input`,
- `validation_failed`.

Example:

```json
{
  "acceptance": {
    "verdict": "approved_with_automation_limits",
    "checked_at": "<ISO timestamp>",
    "passed_checks": ["id_consistency", "bone_validity", "timing_validity"],
    "failed_checks": [],
    "automation_limited_items": ["forest_guardian.skill"],
    "rendered_previews": [".allforai/game-design/previews/forest_guardian_idle.gif"],
    "visual_validation_passed": true,
    "repair_attempts": 1,
    "fallbacks_ready": true,
    "next_action": "Downstream can use idle/walk/attack specs; skill animation uses simplified placeholder."
  }
}
```

### Stage 1: Animation intent

For each animated asset, write a short intent before naming animations. The
intent must answer:
- what the player should understand from the motion,
- what gameplay state the animation represents,
- how exaggerated the motion should be,
- whether the animation must loop seamlessly,
- whether it can interrupt or be interrupted.

Example:

```json
{
  "asset_id": "forest_guardian",
  "intent": "Slow heavy defender; idle should feel calm but massive, attack should read before hit frame.",
  "readability_priority": "windup_before_damage",
  "exaggeration": "medium",
  "interrupt_policy": "attack can be interrupted before contact only"
}
```

### Stage 2: Motion vocabulary

Build a minimum animation set. Do not copy a generic list blindly; choose motions
from gameplay needs.

Baseline game character set:

| Animation | Loop | Typical duration | Notes |
|---|---:|---:|---|
| `idle` | yes | 1000-1800 ms | Breath, weight shift, small secondary motion. |
| `walk` | yes | 600-1000 ms | Must match in-game movement speed. |
| `run` | yes | 450-750 ms | Optional unless gameplay has clear run state. |
| `attack` | no | 500-1000 ms | Must include anticipation, contact, follow-through. |
| `hit` | no | 250-500 ms | Fast readability, no excessive displacement. |
| `death` | no | 900-1800 ms | Use keyframe reference or simplified fallback if complex. |
| `skill` | no | 800-1800 ms | Use simplified transform fallback if acting or VFX trails are too complex. |
| `interact` | no | 500-1200 ms | Optional for dialogue, pickup, or environment use. |

Each animation must define:
- `animation_id`,
- `gameplay_state`,
- `loop`,
- `duration_ms`,
- `priority`,
- `interrupt_policy`,
- `production_mode`.

### Stage 3: Character decomposition

Convert the approved character design into layers only after motion vocabulary is
known. Decomposition must serve movement, not merely mirror anatomy.

Rules:
- Split at every joint that needs independent rotation.
- Keep costume pieces attached to the body part that should carry them.
- Separate hair, cape, tail, weapon, shield, and large accessories if they need
  delayed or secondary motion.
- Do not split tiny decorative details unless they need animation.
- Preserve a clean neutral pose with visible joint locations.

The output is both a part list and a `character_layer_sheet` image spec. The
layer sheet is a production reference, not final game art.

### Stage 4: Rig design

Define the rig after decomposition. Every bone must map to one or more visual
parts, and every part must either bind to a bone or be explicitly static.

Each bone must define:
- `bone_id`,
- `parent`,
- `bind_part_ids[]`,
- `pivot`,
- `default_rotation`,
- `rotation_limit`,
- `z_order_effect`,
- `notes`.

Pivot rules:
- shoulders, hips, knees, elbows, wrists, ankles, and neck pivots must sit at
  believable anatomical hinges,
- weapon pivots should sit at the grip point,
- hair/cape pivots should sit at the attachment point, not at visual center,
- pivot decisions must be visible in `skeleton_overlay`.

### Stage 5: Key pose design

Before writing transform timelines, define the key poses that make each motion
readable. Key poses are visual decisions and should be represented as
`pose_keyframes` image specs.

Minimum pose requirements:
- `idle`: neutral, inhale/up, exhale/down.
- `walk`: contact, down, passing, up, opposite contact.
- `attack`: anticipation, windup, contact, follow-through, recover.
- `hit`: neutral, impact, recoil, recover.
- `death`: hit/fail, fall, settle.

Silhouette rule: each key pose should remain understandable as a black
silhouette at small in-game size.

### Stage 6: Timing and curves

Convert key poses into timing. Use conservative timing for gameplay clarity.

Timing rules:
- anticipation should be long enough for the player to read incoming action,
- contact frames should be short and decisive,
- recovery may be longer if it creates tactical commitment,
- looped animations must return exactly to their starting pose,
- idle motion should be subtle enough not to distract from gameplay.

Curve rules:
- organic idle and walk: `sine_in_out`,
- attack windup: slow-in, then fast contact,
- hit reaction: fast out, slower settle,
- mechanical motion: stepped or linear when appropriate.

### Stage 7: Render and preview

Every animation must define how it will be reviewed before final integration:
- keyframe sheet,
- transform timeline table,
- rendered frame sequence when tooling exists,
- loop GIF or HTML/canvas preview when tooling exists,
- temporary placeholder animation,
- HTML report entry for review.

If a requested motion exceeds automated capability, define an automated
simplification and a fallback placeholder that can ship in prototype builds
without pretending to be final.

### Stage 8: Visual QA and repair

QA verifies both artistic readability and technical handoff. Use rendered
previews when they exist; otherwise use keyframe sheets and mark visual
validation as partial.

Visual checks:
- the intended gameplay state is readable without labels,
- the motion style matches art direction,
- pivots are correctly placed,
- no part tears away from the body during expected rotations,
- loops are seamless where required,
- key contact frames are visually distinct,
- simplified fallback still communicates the gameplay state,
- filenames match `file_prefix`,
- AI-generatable and automation-limited boundaries are honest,
- engine import requirements are stated.

## 2D DragonBones Pipeline

The 2D DragonBones pipeline implements the creative workflow above using
DragonBones-compatible planning artifacts.

### Step 1: Select animated assets

Filter `art-asset-inventory.json.assets[]` to include:
- `type == "character"`,
- animated props explicitly marked by the node-spec,
- VFX assets using `dragonbones_fx`.

For each selected asset, create an entry in
`skeletal-animation-plan.json.assets[]`.

### Step 2: Write animation intent and motion vocabulary

For each selected asset, produce `animation_intent` and `animation_set` before
writing part lists. If the animation list is missing, infer a conservative set
from gameplay role:
- player character: `idle`, `walk`, `run`, `attack`, `hit`, `death`, `interact`;
- enemy: `idle`, `walk`, `attack`, `hit`, `death`;
- NPC: `idle`, `talk`, `gesture`;
- prop: `idle` plus state-specific animations such as `open`, `activate`,
  `break`.

### Step 3: Define layer decomposition

For each character, define a stable part list. Use this baseline unless the
character design makes a part irrelevant:

```json
[
  "head",
  "neck",
  "torso",
  "pelvis",
  "upper_arm_l",
  "forearm_l",
  "hand_l",
  "upper_arm_r",
  "forearm_r",
  "hand_r",
  "upper_leg_l",
  "lower_leg_l",
  "foot_l",
  "upper_leg_r",
  "lower_leg_r",
  "foot_r",
  "hair_front",
  "hair_back",
  "weapon",
  "accessory"
]
```

Each part must define:
- `part_id`,
- `display_name`,
- `z_order`,
- `pivot_hint`,
- `mirrored_from` when applicable,
- `required_for_animations[]`.

### Step 4: Define skeleton hierarchy

Use a simple humanoid hierarchy by default:

```text
root
  pelvis
    torso
      neck
        head
      upper_arm_l -> forearm_l -> hand_l
      upper_arm_r -> forearm_r -> hand_r
    upper_leg_l -> lower_leg_l -> foot_l
    upper_leg_r -> lower_leg_r -> foot_r
```

For non-humanoid characters, preserve the same output schema but rename bones to
domain-accurate body parts.

### Step 5: Classify animations

Classify each requested animation into one of three production modes:

| Mode | Use when | Output |
|---|---|---|
| `ai_transform_json` | Position, rotation, scale, opacity, squash/stretch only | DragonBones transform JSON spec. |
| `keyframe_reference` | Needs expressive poses that can be described as key poses | Keyframe image spec and timing notes. |
| `automation_limited` | Needs IK, mesh deformation, cloth/hair physics, facial acting, or complex trails | Simplified transform fallback and explicit automation limit. |

### Step 6: Produce pose and timeline specs

For every animation:
- write the key pose sequence,
- write `duration_ms`,
- write keyframe timestamps,
- write easing choices,
- mark loop seams,
- state expected gameplay event timing, such as `damage_frame_ms` or
  `footstep_event_ms`.

### Step 7: Produce preview and QA specs

Create entries in `animation-preview-spec.json` and add checklist items for the
reviewer. Preview specs are required even when only placeholder animation exists.

### Step 8: Render, validate, repair, then close

Apply the render-and-validate loop from "Closed Loop and Automatic Acceptance".
Update each asset and animation state. Then write the final
`acceptance.verdict`. If any asset is `needs_revision`, only re-run the failed
stage for that asset; do not regenerate already accepted stages. If the repair
cap is reached, write a simplified fallback and mark only that animation
`automation_limited`.

## 3D Skeletal Pipeline

For 3D projects, do not promise final rigged output unless an actual 3D toolchain
node is present. Produce a specification package instead:
- skeleton bone hierarchy,
- animation clip list,
- expected clip durations,
- root motion policy,
- loop policy,
- export target (`GLB`, `FBX`, or engine-native),
- automation-limit notes for skinning, retargeting, and mocap cleanup.

If Blender headless generation is available, it may create low-fidelity rig
placeholders, but polished deformation remains automation-limited unless an
automated render-and-validate loop is available.

## Image Output Specifications

This skill defines image outputs as generation-ready specs. It does not require
image generation during this phase.

### `character_layer_sheet`

Purpose: one transparent-background image showing all separated character
parts, not overlapping, with consistent scale.

Filename:

```text
{file_prefix}_layer_sheet.png
```

Prompt requirements:
- transparent or flat neutral background,
- orthographic front or three-quarter view matching art direction,
- each body part separated with whitespace,
- no baked shadows crossing part boundaries,
- no text inside the image,
- all visible costume details included on the correct part,
- hands and feet separated enough for clean pivot placement.

Recommended size:
- 2048x2048 for normal 2D projects,
- 4096x4096 for high-detail characters,
- never pixel-art downsampled output.

### `skeleton_overlay`

Purpose: one annotated reference showing bones, joints, and pivot points.

Filename:

```text
{file_prefix}_skeleton_overlay.png
```

Content requirements:
- use the approved full character reference as the base,
- draw bone lines over limbs and torso,
- mark pivot points at shoulders, elbows, wrists, hips, knees, ankles, neck,
  and head,
- label only with short `part_id` values,
- keep labels outside the silhouette where possible.

### `pose_keyframes`

Purpose: pose reference sheet for one animation.

Filename:

```text
{file_prefix}_{animation_id}_keyframes.png
```

Content requirements:
- 3-5 poses for simple actions,
- 5-8 poses for attack or skill actions,
- poses arranged left to right in timeline order,
- consistent character scale and facing direction,
- include anticipation, contact, follow-through, and settle poses when relevant.

## Output Contract

The skill produces planning, reference, preview, and validation artifacts. All
outputs are project-relative and deterministic. JSON outputs must be valid JSON
and include `schema_version: "1.0"`.

| Output | Required | Purpose | Consumed by |
|---|---:|---|---|
| `.allforai/game-design/systems/skeletal-animation-plan.json` | yes | Canonical plan, states, validation, acceptance verdict. | Character art gen, runtime animation import, QA. |
| `.allforai/game-design/systems/layered-character-reference.json` | yes for 2D | Layer prompts/specs for split character assets. | Image generation, layer sheet renderer. |
| `.allforai/game-design/systems/animation-preview-spec.json` | yes | Preview strategy and rendered output references. | Visual validation, HTML reports. |
| `.allforai/game-design/previews/*` | required when render tooling exists | Rendered frames/GIF/HTML used for visual QA. | LLM vision validator, QA report. |

### Output completion rules

- The plan is the source of truth; other outputs must agree with it.
- Every output path must start with the resolved `file_prefix` where asset-specific.
- `acceptance.verdict` determines node completion.
- Rendered previews are required if a render path is available.
- If rendering is unavailable, `render_previews.render_path` must be
  `static_keyframe_board` and `visual_validation.validator` must be
  `partial_static_keyframes`.

## Invocation Contract

Other meta-skill flows call this sub-skill by reading this file and passing a
node-spec context. The caller must not rely on conversation state.

### Caller responsibilities

Before invoking, the caller must:
- ensure required input artifacts exist,
- pass the target asset filter if only some assets need skeletal animation,
- declare the desired output root if different from `.allforai/game-design/`,
- declare available render tools if known,
- declare whether visual validation with image understanding is available.

Minimal invocation context:

```json
{
  "skill": "game-art/skeletal-animation",
  "mode": "plan_and_validate",
  "input_paths": {
    "art_style_guide": ".allforai/game-design/art-style-guide.json",
    "art_pipeline_config": ".allforai/game-design/art-pipeline-config.json",
    "art_asset_inventory": ".allforai/game-design/art-asset-inventory.json",
    "concept_contract": ".allforai/concept-contract.json"
  },
  "asset_filter": {
    "asset_ids": [],
    "asset_types": ["character"]
  },
  "render_tools": {
    "browser_canvas": "unknown | available | unavailable",
    "dragonbones_runtime": "unknown | available | unavailable",
    "scripted_2d_transform": "unknown | available | unavailable",
    "ffmpeg": "unknown | available | unavailable"
  },
  "visual_validation": {
    "llm_vision_available": true,
    "max_repair_attempts": 3
  },
  "output_root": ".allforai/game-design"
}
```

### Supported modes

| Mode | Behavior |
|---|---|
| `plan_only` | Produce JSON specs; do not render previews. Use only when render tools are unavailable. |
| `plan_and_render` | Produce specs and rendered previews; deterministic checks only. |
| `plan_and_validate` | Produce specs, render previews, run visual validation, repair, and write acceptance. Preferred mode. |
| `validate_existing` | Read existing plan/previews and run deterministic + visual validation only. |

### Return protocol

The sub-skill must return one of these statuses to the caller:

| Status | Meaning | Caller action |
|---|---|---|
| `COMPLETED` | `acceptance.verdict` is acceptable. | Continue downstream. |
| `COMPLETED_WITH_LIMITS` | Fallbacks exist and limitations are explicit. | Continue downstream using fallback notes. |
| `NOT_APPLICABLE` | Skeletal animation is not suitable. | Route to frame animation/static asset flow. |
| `UPSTREAM_DEFECT` | Required input is missing or contradictory. | Pause caller node; fix upstream artifact. |
| `FAILED_VALIDATION` | Repair loop exhausted without valid fallback. | Do not continue downstream. |

Status mapping:
- `approved` -> `COMPLETED`
- `approved_with_automation_limits` -> `COMPLETED_WITH_LIMITS`
- `not_applicable` -> `NOT_APPLICABLE`
- `blocked_by_missing_input` -> `UPSTREAM_DEFECT`
- `needs_revision` or `validation_failed` -> `FAILED_VALIDATION`

### Downstream consumption contract

Callers must consume outputs this way:
- Art/image generation reads `layered-character-reference.json` for layer sheet
  prompts and naming.
- Animation generation reads `skeletal-animation-plan.json.assets[].animations`
  for pose/timeline specs.
- Preview/report nodes read `animation-preview-spec.json` and
  `render_previews.items[]`.
- Runtime import nodes use `file_prefix`, `bones[]`, and transform timelines.
- QA nodes read `acceptance`, `visual_validation`, and
  `automation_limited_animations`.

Callers must not invent alternate asset ids, animation ids, or filenames after
this skill writes its outputs.

## JSON Outputs

### `skeletal-animation-plan.json`

Write to:

```text
.allforai/game-design/systems/skeletal-animation-plan.json
```

Schema:

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO timestamp>",
  "source": {
    "used_concept_contract": true,
    "art_pipeline_config": ".allforai/game-design/art-pipeline-config.json",
    "art_asset_inventory": ".allforai/game-design/art-asset-inventory.json"
  },
  "rig_type": "dragonbones | dragonbones_mesh | 3d_skeletal",
  "stage_status": {
    "animation_intent": "pending | passed | failed | not_applicable",
    "motion_vocabulary": "pending | passed | failed | not_applicable",
    "character_decomposition": "pending | passed | failed | not_applicable",
    "rig_design": "pending | passed | failed | not_applicable",
    "key_pose_design": "pending | passed | failed | not_applicable",
    "timing_and_curves": "pending | passed | failed | not_applicable",
    "preview_and_fallback": "pending | passed | failed | not_applicable",
    "qa_and_handoff": "pending | passed | failed | not_applicable"
  },
  "assets": [
    {
      "asset_id": "<canonical asset id>",
      "name": "<display name>",
      "file_prefix": "<from concept-contract or fallback asset_id>",
      "state": "planned | spec_ready | reference_ready | preview_ready | approved | needs_revision | automation_limited | not_applicable",
      "production_branch": "2d_dragonbones | 3d_skeletal",
      "animation_intent": {
        "intent": "<what motion communicates>",
        "readability_priority": "<primary readability concern>",
        "exaggeration": "low | medium | high",
        "interrupt_policy": "<gameplay interruption rule>"
      },
      "layer_sheet": {
        "path": ".allforai/game-design/art/<file_prefix>_layer_sheet.png",
        "status": "spec_only | generated | approved"
      },
      "skeleton_overlay": {
        "path": ".allforai/game-design/art/<file_prefix>_skeleton_overlay.png",
        "status": "spec_only | generated | approved"
      },
      "parts": [],
      "bones": [],
      "animations": []
    }
  ],
  "ai_generatable_animations": [],
  "automation_limited_animations": [],
  "render_previews": {
    "render_path": "browser_canvas | dragonbones_runtime | scripted_2d_transform | static_keyframe_board",
    "output_dir": ".allforai/game-design/previews",
    "items": [
      {
        "asset_id": "<asset id>",
        "animation_id": "<animation id>",
        "frames": [".allforai/game-design/previews/<file_prefix>_<animation_id>_0001.png"],
        "gif": ".allforai/game-design/previews/<file_prefix>_<animation_id>.gif",
        "html": ".allforai/game-design/previews/<file_prefix>_<animation_id>.html"
      }
    ]
  },
  "visual_validation": {
    "validator": "llm_vision | deterministic_only | partial_static_keyframes",
    "items": [
      {
        "asset_id": "<asset id>",
        "animation_id": "<animation id>",
        "verdict": "pass | fail | partial",
        "issues": [],
        "repair_attempts": 0,
        "final_action": "approved | repaired | simplified_fallback | not_applicable"
      }
    ]
  },
  "qa_required": true,
  "acceptance": {
    "verdict": "approved | approved_with_automation_limits | not_applicable | needs_revision | blocked_by_missing_input | validation_failed",
    "checked_at": "<ISO timestamp>",
    "passed_checks": [],
    "failed_checks": [],
    "automation_limited_items": [],
    "rendered_previews": [],
    "visual_validation_passed": false,
    "repair_attempts": 0,
    "fallbacks_ready": false,
    "next_action": "<what happens next>"
  }
}
```

### `layered-character-reference.json`

Write to:

```text
.allforai/game-design/systems/layered-character-reference.json
```

Schema:

```json
{
  "schema_version": "1.0",
  "characters": [
    {
      "asset_id": "<asset id>",
      "file_prefix": "<file prefix>",
      "layer_sheet_prompt": "<image prompt>",
      "skeleton_overlay_prompt": "<image prompt>",
      "parts": [
        {
          "part_id": "upper_arm_l",
          "z_order": 20,
          "pivot_hint": "shoulder joint center",
          "required": true
        }
      ]
    }
  ]
}
```

### `animation-preview-spec.json`

Write to:

```text
.allforai/game-design/systems/animation-preview-spec.json
```

Schema:

```json
{
  "schema_version": "1.0",
  "preview_items": [
    {
      "asset_id": "<asset id>",
      "animation_id": "idle",
      "preview_type": "rendered_frames | gif | html_canvas | keyframe_sheet | transform_timeline | automation_limit_note",
      "image_path": ".allforai/game-design/art/<file_prefix>_idle_keyframes.png",
      "rendered_preview_path": ".allforai/game-design/previews/<file_prefix>_idle.gif",
      "duration_ms": 1200,
      "loop": true
    }
  ]
}
```

## DragonBones Transform Animation Spec

For `ai_transform_json` animations, describe keyframes in a neutral schema that
can later be converted to DragonBones JSON:

```json
{
  "animation_id": "idle",
  "duration_ms": 1200,
  "loop": true,
  "tracks": [
    {
      "bone": "torso",
      "keyframes": [
        { "time_ms": 0, "x": 0, "y": 0, "rotation": 0, "scale_x": 1, "scale_y": 1 },
        { "time_ms": 600, "x": 0, "y": 2, "rotation": 0, "scale_x": 1.01, "scale_y": 0.99 },
        { "time_ms": 1200, "x": 0, "y": 0, "rotation": 0, "scale_x": 1, "scale_y": 1 }
      ],
      "easing": "sine_in_out"
    }
  ]
}
```

Keep transform values conservative for gameplay readability. Exaggeration belongs
in key poses and VFX, not in uncontrolled rig distortion.

## Automation Capability Boundary

AI-generatable:
- idle breathing,
- simple walk bob,
- UI mascot bounce,
- weapon glow pulse,
- simple squash/stretch hit reaction,
- opacity/scale/rotation VFX.

Automation-limited:
- expressive acting,
- believable four-legged locomotion,
- complex attack choreography,
- cloth, hair, tail, or rope secondary motion,
- face rigs and phoneme animation,
- mesh deformation,
- IK constraints,
- final polish for production release.

For each automation-limited item, write:
- why full automation is unreliable,
- the simplified automated replacement,
- fallback placeholder behavior,
- automatic acceptance checklist,
- downstream note explaining the quality limit.

Complex actions are allowed when they can be represented as:
- a key pose sheet,
- a conservative transform timeline,
- a simplified anticipation/contact/recovery sequence,
- a non-final placeholder preview.

Complex actions are not allowed to silently become final-quality claims.

## QA Checklist

Before marking the skeletal animation spec complete:
- Every selected animated asset has a `file_prefix`.
- Every character has a layer sheet spec.
- Every character has a skeleton overlay spec.
- Every animation is classified as `ai_transform_json`, `keyframe_reference`, or
  `automation_limited`.
- No pixel-art asset is routed to skeletal animation.
- No final-quality claim is made for complex IK or mesh animation.
- Output filenames are deterministic and derived from `file_prefix`.
- Runtime notes specify whether the target engine can consume DragonBones JSON
  directly or needs conversion.

## Completion Conditions

This skill is complete only when all of these are true:
- `skeletal-animation-plan.json` exists and is valid JSON.
- `stage_status.*` values are all `passed`, except stages that are explicitly
  `not_applicable`.
- `acceptance.verdict` is `approved`, `approved_with_automation_limits`, or
  `not_applicable`.
- If verdict is `approved_with_automation_limits`, every automation-limited
  animation has:
  - a simplified automated replacement,
  - a fallback placeholder,
  - a named acceptance checklist,
  - a downstream note explaining the quality limit.
- Every failure has an explicit `next_action`.

Do not mark the skill complete if the only evidence is file existence.

## Future Integration Notes

This sub-skill is intentionally not wired into meta-skill orchestration yet.
Future integration can add a dedicated node such as `skeletal-animation-spec`
after `art-spec-design` and before character art generation.

Suggested future node:

```yaml
node: skeletal-animation-spec
capability: game-art-skeletal-animation
hard_blocked_by: [art-spec-design]
exit_artifacts:
  - path: .allforai/game-design/systems/skeletal-animation-plan.json
    validation_commands:
      - python3 -c "import json; json.load(open('.allforai/game-design/systems/skeletal-animation-plan.json'))"
```

Suggested invocation:

```markdown
Read and execute `${CLAUDE_PLUGIN_ROOT}/skills/game-art/30-generate/skeletal-animation/SKILL.md`.
```
