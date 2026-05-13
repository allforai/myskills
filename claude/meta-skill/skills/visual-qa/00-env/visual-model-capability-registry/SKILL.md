---
name: visual-qa-00-env-visual-model-capability-registry
description: Detect and route Codex CLI visual model capabilities for batch visual acceptance, including task-risk model selection and blocked states when required visual capability is unavailable.
---

# Visual Model Capability Registry

## Overview

Detects whether Codex CLI can perform visual inspection and records which visual
model profile should be used for each batch visual QA task.

This skill does not judge images. It prepares model routing for
`visual-qa/40-qa/batch-visual-acceptance/SKILL.md`.

## Input Contract

Required:
- Codex CLI availability;
- batch task list or planned batch categories;
- caller-provided risk classification or enough batch metadata to infer risk.

Optional:
- project-local model preference;
- cost/latency limits;
- previous visual model routing report.

## Output Contract

Write:

```text
.allforai/visual-qa/visual-model-capability-registry.json
.allforai/visual-qa/visual-model-routing-report.json
```

The routing report must include:

```json
{
  "schema_version": "1.0",
  "codex_cli_available": true,
  "available_visual_models": [],
  "batch_routes": [
    {
      "batch_id": "string",
      "task_risk": "low|medium|high",
      "minimum_capabilities": [],
      "selected_visual_model": "codex-default|<model>",
      "fallback_visual_model": "string|null",
      "model_reason": "string",
      "blocked_state": null
    }
  ]
}
```

## Invocation Contract

```json
{
  "skill": "visual-qa/visual-model-capability-registry",
  "mode": "detect_route_visual_models",
  "input_paths": {
    "task_list": ".allforai/visual-qa/visual-acceptance-task-list.json",
    "batch_docs": ".allforai/visual-qa/visual-acceptance-batches/"
  },
  "output_root": ".allforai/visual-qa"
}
```

Supported modes: `detect_only`, `route_batches`, `detect_route_visual_models`.

## Risk Routing

Use stronger visual model capability for high-risk batches:
- character identity and expression consistency;
- small-size icon readability;
- tile or puzzle-piece distinguishability;
- UI layout, overlap, text-fit, and responsive screenshots;
- animation frame continuity;
- VFX occlusion, brightness, and gameplay readability;
- subtle style drift across a family.

Medium-risk batches may use the Codex CLI default visual model when it supports
multi-image inspection and evidence-grounded reporting.

Low-risk batches may use the fastest available visual model when checking:
- non-empty images;
- obvious crop/alpha/background failures;
- contact-sheet existence;
- broad visual mismatch.

## Codex CLI Model Selection

If Codex CLI exposes a model parameter, record and use the selected model in the
Codex invocation. If the installed CLI only supports its default model, record
`selected_visual_model: "codex-default"` and whether that default satisfies the
batch's `minimum_capabilities`.

Do not pass high-risk visual acceptance when the required model capability is
unknown. Return `blocked_by_missing_visual_model_capability` for affected
batches.

## Automatic Validation

Before completion:
1. Confirm Codex CLI is callable or return `blocked_by_missing_codex_cli`.
2. Confirm every batch has `task_risk`, `minimum_capabilities`,
   `selected_visual_model`, and `model_reason`.
3. Confirm high-risk batches are not routed to unknown-capability models.
4. Confirm blocked batches include `blocked_by_missing_visual_model_capability`.
5. Confirm the batch visual acceptance skill can read the routing report.

## Completion Conditions

Return `COMPLETED` when model capability and routing reports exist and every
batch has a valid route.

Return `blocked_by_missing_codex_cli` when Codex CLI cannot be invoked.
Return `blocked_by_missing_visual_model_capability` when a high-risk task cannot
be routed to a capable visual model.
