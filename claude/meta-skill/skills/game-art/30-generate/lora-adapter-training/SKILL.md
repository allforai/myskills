---
name: game-art-30-generate-lora-adapter-training
description: Internal bundled meta-skill module for game-art/30-generate/lora-adapter-training; use to train, purchase/register, validate, and hand off LoRA adapters for strict game art identity/style locking.
---

# LoRA Adapter Training Skill

## Overview

Train, purchase/register, or validate LoRA adapters for strict game art
identity/style locking. This skill produces adapter profiles consumed by
`image-model-capability-registry`, `image-generation-contract`, and
`batch-image-generation`.

This skill must not silently fall back to prompt-only generation. If LoRA is
required but cannot be produced or registered, return a blocked state.

## Input Contract

Required:
- `.allforai/game-design/art/lora/lora-identity-style-lock-spec.json`
- dataset/reference image manifest
- base model/provider target
- license/privacy policy
- output root

Optional:
- existing adapter path or marketplace adapter metadata
- local GPU training command
- remote GPU rental config
- provider API training config
- validation prompt set

## Output Contract

Writes:

```text
.allforai/game-design/art/lora/lora-dataset-manifest.json
.allforai/game-design/art/lora/lora-training-job.json
.allforai/game-design/art/lora/lora-adapter-registry.json
.allforai/game-design/art/lora/lora-validation-report.json
.allforai/game-design/art/lora/lora-validation-contact-sheet.png
.allforai/game-design/art/lora/lora-training-report.md
```

`lora-adapter-registry.json` entries must include:
- `lora_adapter_id`
- `lora_adapter_kind`
- `base_model`
- `training_location`
- `adapter_path_or_provider_ref`
- `lora_trigger_tokens`
- `lora_weight_range`
- `dataset_ref`
- `license_ref`
- `validation_evidence`
- `state`

Allowed states: `ready`, `ready_with_warning`, `failed_validation`,
`blocked_by_missing_dataset`, `blocked_by_missing_training_runtime`,
`blocked_by_license`, `blocked_by_budget`.

Allowed `training_location` values: `local_gpu`, `remote_gpu_rental`,
`provider_api_training`, `existing_lora`.

## Training Location Execution

### Local GPU

Use local only when all are true:
- GPU and VRAM are detected;
- training command is executable;
- dependencies are pinned or project-local;
- output adapter file can be produced and loaded by a generation provider.

If any condition is false, do not pretend local is available.

### Remote GPU Rental

Use remote GPU rental when custom training is needed or local hardware is
insufficient. Required evidence:
- provider name and GPU class;
- training repo/template;
- dataset upload path;
- checkpoint/export path;
- cost cap;
- teardown policy;
- adapter download path.

### Provider API Training

Use provider API training when a managed LoRA endpoint is available. Required
evidence:
- API provider and endpoint;
- base model;
- dataset upload method;
- returned adapter id/ref;
- supported inference model;
- cost or unknown-cost status.

### Existing LoRA

Existing adapters may be registered only with license/provenance evidence and a
validation report against project prompts.

## Validation

Generate a validation set before accepting the adapter:
- 4 to 8 identity/style test prompts;
- at least one negative drift probe;
- one downstream-like use case, such as portrait, expression, tile family, icon
  family, or UI state;
- contact sheet for Codex visual review.

The adapter is `ready` only if visual QA confirms identity/style lock. If LoRA
validation fails, repair dataset/captions/training config and retry within
budget.

## Handoff

After validation, update:

```text
.allforai/game-design/art/image-generation/image-model-capability-registry.json
.allforai/game-design/art/image-generation/image-model-routing-report.json
```

with `lora_adapter`, `lora_adapter_id`, `lora_trigger_tokens`,
`lora_weight_range`, and `validation_evidence`.

## Completion Conditions

Return `COMPLETED` when a ready adapter is registered and validated.

Return `FAILED_VALIDATION` when an adapter was produced but fails validation
after the retry budget.

Return `blocked_by_missing_training_runtime`, `blocked_by_missing_dataset`,
`blocked_by_license`, or `blocked_by_budget` when the adapter cannot be created
or registered.
