---
name: game-art-20-spec-image-prompt-compiler
description: Compile project art direction, asset specs, model routing, LoRA/reference locks, and acceptance criteria into standardized per-request prompt files before LLM image generation.
---

# Image Prompt Compiler Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive,
> image-generation upstream.

## Purpose

LLM image generation must not rely on ad-hoc prompts written independently by
each asset node. This skill compiles production prompts from approved project
contracts so every generated image request carries the same art direction,
style locks, runtime constraints, negative prompts, and repair metadata.

Prefer material-first generation. When a downstream deterministic process can
assemble, crop, layer, recolor, atlas, rig, animate, or compose the final
runtime asset, the prompt should ask the LLM for stable raw material rather
than a fully final in-game asset. Examples: character parts for skeletal
animation, clean pose references for motion extraction, scene layers for
parallax, tile source motifs for procedural variants, icon foreground symbols
for programmatic frame/background composition, VFX source sprites for generated
emitters, and background plates with separate foreground/midground/background
layers.

## Input Contract

Required:

```text
.allforai/game-design/art/art-direction-benchmark.json
.allforai/game-design/art/asset-acceptance-criteria.json
.allforai/game-design/art/image-generation/image-request-manifest.json
.allforai/game-design/art/image-generation/image-model-routing-report.json
.allforai/game-design/asset-registry.json
```

Optional:

```text
.allforai/game-design/art/visual-style-tokens.json
.allforai/game-design/art-style-guide.json
.allforai/game-design/art/lora/lora-adapter-registry.json
.allforai/game-design/art/image-generation/image-feedback-report.json
.allforai/bootstrap/specialized-skills/<specialization_id>-art-generation/SKILL.md
```

Return `UPSTREAM_DEFECT` when benchmark, acceptance criteria, request manifest,
or routing report is missing. Do not synthesize production prompts from a single
asset description.

## Output Contract

Writes:

```text
.allforai/game-design/art/image-generation/compiled-prompt-manifest.json
.allforai/game-design/art/image-generation/prompts/
```

Each compiled prompt entry must include:

```json
{
  "request_id": "",
  "asset_id": "",
  "task_type": "",
  "prompt_template_id": "",
  "positive_prompt_path": "",
  "negative_prompt_path": "",
  "style_lock_terms": [],
  "composition_terms": [],
  "runtime_size_terms": [],
  "do_not_include": [],
  "reference_set_id": null,
  "lora_adapter_id": null,
  "lora_trigger_tokens": [],
  "lora_weight": null,
  "material_first": {
    "enabled": true,
    "raw_material_kind": "layer | part | motif | plate | symbol | pose_reference | texture_source | vfx_source",
    "programmatic_consumer": "",
    "assembly_contract_ref": ""
  },
  "seed_strategy": "fixed_family_seed | varied_candidates | edit_preserve_seed",
  "variant_strategy": {},
  "repair_context": {},
  "acceptance_ref": ".allforai/game-design/art/asset-acceptance-criteria.json"
}
```

## Compilation Rules

For every image request:

1. Select the prompt template from `task_type`, never from free-form taste:
   `icon_prompt`, `tileset_prompt`, `ui_mockup_prompt`,
   `layer_sheet_prompt`, `pose_reference_prompt`, `sprite_vfx_prompt`,
   `decal_prompt`, `particle_texture_prompt`, `trail_texture_prompt`,
   `background_prompt`, `prop_prompt`, `portrait_prompt`,
   `item_art_prompt`, `frame_animation_prompt`, `expression_set_prompt`, or
   `preview_prompt`.
2. Decide whether material-first generation is possible. If a programmatic
   consumer can create the final runtime output more consistently, compile the
   prompt for raw material and record `material_first.enabled=true`.
3. Pull shared style terms from `art-direction-benchmark`,
   `visual-style-tokens`, and `asset-acceptance-criteria`.
4. Pull family-specific constraints from the asset registry and specialized
   art-generation skill when present.
5. Pull model-specific constraints from `image-model-routing-report`.
6. Inject LoRA/reference/edit terms only when the routing report and acceptance
   criteria allow them. If `requires_lora=true`, include adapter id, trigger
   tokens, and weight; otherwise return `blocked_by_missing_identity_lock`.
7. Write prompts to files. The batch executor receives paths, not large prompt
   text embedded in chat/tool calls.
8. When repairing, preserve the previous failure reason in `repair_context` and
   compile a narrower prompt or edit instruction instead of random regeneration.

## Automatic Validation

Reject with `FAILED_VALIDATION` when:

- any request lacks positive and negative prompt files;
- prompts omit benchmark anti-reference rules or acceptance criteria;
- prompt files contain contradictory style tokens;
- strict identity locks are routed to prompt-only generation;
- material-first opportunities are ignored without explanation for skeletal
  animation, scene layering, tile variants, icons, VFX, or other programmatic
  assembly-friendly outputs;
- raw material prompts omit isolation, layer separation, alpha/background,
  camera, crop, pivot, or downstream assembly constraints;
- edit-mode requests lack context image, base prompt, or mask requirements;
- prompts ignore runtime size/readability constraints;
- compiled prompts cannot be traced back to request id, asset id, template, and
  acceptance criteria.

## Completion Conditions

Return `COMPLETED` only when every active image request has a compiled prompt
entry, prompt files exist, identity/style locks are explicit, and repair
context is preserved for reruns. Every request must either use material-first
generation or explain why direct final-image generation is required. Prompt
compilation does not mark any image `consumer_ready`.
