---
name: game-art-20-spec-image-batch-generation-plan
description: Plan LLM image generation batches by asset family, model profile, prompt template, reference/LoRA lock, variant count, retry budget, and acceptance target before long-task execution.
---

# Image Batch Generation Plan Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive,
> image-generation upstream.

## Purpose

Bulk image generation should be planned as coverage, not improvised as a list
of prompts. This skill decides how many candidates are needed per asset family,
which model/profile handles each batch, how variants and seeds are assigned,
and how retries/edits are routed.

The default production strategy is raw-material-first. LLM batches should
prefer generating reusable source parts, layers, motifs, plates, references, or
texture sources that deterministic tools can compose into consistent runtime
assets. Direct final-image batches are allowed only when programmatic assembly
would not improve consistency or is out of scope for that asset family.

## Input Contract

Required:

```text
.allforai/game-design/art/image-generation/image-request-manifest.json
.allforai/game-design/art/image-generation/compiled-prompt-manifest.json
.allforai/game-design/art/image-generation/image-model-routing-report.json
.allforai/game-design/art/asset-acceptance-criteria.json
.allforai/game-design/asset-registry.json
```

Optional:

```text
.allforai/game-design/art/image-generation/image-feedback-report.json
.allforai/game-design/art/image-generation/generated-image-files-manifest.json
.allforai/game-design/art/image-generation/accepted-image-manifest.json
.allforai/game-design/art/lora/lora-adapter-registry.json
```

## Output Contract

Writes:

```text
.allforai/game-design/art/image-generation/image-batch-generation-plan.json
.allforai/game-design/art/image-generation/image-batch-generation-plan.md
```

The JSON must include:

```json
{
  "status": "ready | blocked",
  "batch_groups": [
    {
      "batch_id": "",
      "asset_family": "",
      "task_type": "",
      "operation": "generate | edit",
      "request_ids": [],
      "model_profile": {},
      "prompt_template_id": "",
      "reference_set_id": null,
      "lora_adapter_id": null,
      "required_candidate_count": 0,
      "variants_per_asset": 0,
      "seed_policy": "",
      "acceptance_target": {},
      "material_first_policy": {
        "enabled": true,
        "raw_material_kind": "",
        "assembly_consumer": "",
        "postprocess_required": true
      },
      "retry_budget": 3,
      "mcp_image_batch_required": true
    }
  ],
  "coverage_targets": {},
  "blocked_batches": []
}
```

## Planning Rules

1. Group requests by compatible task type, selected model/profile, operation,
   prompt template, identity lock method, output format, and acceptance target.
2. Split raw-material generation batches from final-runtime-output batches.
   Raw material often needs different background, crop, alpha, and candidate
   count policies.
3. Do not mix strict identity locked requests with prompt-only requests in the
   same batch.
4. Do not mix edit-mode requests with text-to-image requests in the same batch.
5. Set `required_candidate_count` high enough to survive rejection. Art-heavy
   production should generate multiple candidates per asset or family unless
   the asset is an edit from a locked approved image.
6. Set seed policy by goal:
   family coherence uses fixed or bounded family seeds; broad ideation uses
   varied candidates; edit repair uses preservation seed policy.
7. Set retry budgets and repair modes from downstream feedback. A failed
   family should not rerun the whole project batch.
8. Prefer `mcp-image-batch` for multi-request generation or edit runs. If the
   MCP is unavailable and no verified provider path exists, set `status=blocked`
   with `blocked_by_missing_mcp_image_batch` or provider-specific blocker.

## Automatic Validation

Reject with `FAILED_VALIDATION` when:

- any request lacks a batch group;
- a batch mixes incompatible operation/model/identity-lock modes;
- required candidate counts are below acceptance coverage targets;
- prompt-only is selected for strict identity/style locks;
- raw-material-first policy is missing for programmatic assembly-friendly
  families, or direct final-image generation is used without a reason;
- postprocess/assembly consumer is missing for raw-material batches;
- retry budget is missing;
- plan does not explain how coverage shortage will trigger another batch.

## Completion Conditions

Return `COMPLETED` only when every request is assigned to a valid batch group,
coverage targets are explicit, model/profile choices match the routing report,
and blocked batches name exact missing capabilities. This skill does not call
the image provider.
