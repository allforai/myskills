---
name: game-art-20-spec-lora-identity-style-lock-spec
description: Internal bundled meta-skill module for game-art/20-spec/lora-identity-style-lock-spec; use when a project must decide whether LoRA is required and whether to train locally, rent remote GPU, or use provider/API LoRA training.
---

# LoRA Identity Style Lock Spec Skill

## Overview

Decide whether a game art project needs LoRA or can use lower-cost identity lock
methods such as reference edit mode. This skill owns the local-vs-remote-vs-API
decision, not image generation itself.

LoRA is required only when the project needs repeatable identity/style across
many future assets and acceptance criteria forbid prompt-only drift.

## Input Contract

Required:
- `.allforai/game-design/art/asset-acceptance-criteria.json`
- `.allforai/game-design/art/visual-style-tokens.json` or equivalent style guide
- asset registry or requested asset families
- available provider/model capability registry

Optional:
- local GPU inventory and VRAM
- existing LoRA adapters or marketplace LoRA candidates
- dataset/reference image folder
- budget, privacy, license, and latency policy

## Output Contract

Writes:

```text
.allforai/game-design/art/lora/lora-identity-style-lock-spec.json
.allforai/game-design/art/lora/lora-training-decision-report.md
```

The JSON must include:
- `lock_scope`
- `requires_lora`
- `allowed_fallback_methods`
- `training_location`: `local_gpu | remote_gpu_rental | provider_api_training | existing_lora | not_required`
- `decision_reason`
- `minimum_dataset`
- `base_model`
- `provider_candidates`
- `privacy_license_constraints`
- `blocked_state`

Allowed blocked states: `blocked_by_missing_identity_lock`,
`blocked_by_missing_dataset`, `blocked_by_missing_training_runtime`,
`blocked_by_license`, `blocked_by_budget`.

## Decision Rule

Use this order:

1. If the asset is low-risk or one-off, use `prompt_only` or
   `reference_image_only`.
2. If the asset needs local variation while preserving a single base image, use
   `reference_edit_mode`.
3. If the asset family must remain stable across many batches, use LoRA.
4. If an existing licensed LoRA satisfies the style/identity contract, prefer
   `existing_lora`.
5. If local GPU has enough VRAM and installable training stack is verified, use
   `local_gpu`.
6. If local GPU is insufficient or absent, choose `provider_api_training` for
   simple managed LoRA jobs, or `remote_gpu_rental` for custom training stacks.

Practical defaults:
- `provider_api_training`: best for managed pipelines such as fal.ai-style LoRA
  training when API access, model schema, and output adapter ref are available.
- `remote_gpu_rental`: best for custom ComfyUI/kohya/AI-Toolkit training or
  privacy-controlled runs on RunPod/Vast/Lambda-style GPU rentals.
- `local_gpu`: best only when the local machine has a verified GPU, enough VRAM,
  pinned dependencies, and no urgent throughput requirement.

Do not choose local training just because the machine exists. Local is valid
only after a runnable training command is verified.

## Automatic Validation

Before completion:
1. Every `requires_lora=true` asset family has lock scope and failure codes.
2. A training location is chosen or a blocked state is explicit.
3. Remote/provider choices include cost, API/tool availability, and license
   handling.
4. Local choices include executable training command evidence, not only GPU
   presence.
5. Fallback methods are explicitly allowed by acceptance criteria.

## Completion Conditions

Return `COMPLETED` when every lock-required family has a selected LoRA path,
existing LoRA, allowed fallback, or blocked state.

Return `blocked_by_missing_identity_lock` when strict identity/style lock is
required but no LoRA or allowed fallback exists.
