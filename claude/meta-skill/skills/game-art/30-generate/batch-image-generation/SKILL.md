---
name: game-art-30-generate-batch-image-generation
description: Internal bundled meta-skill module for game-art/30-generate/batch-image-generation; use when multiple image requests should be generated through the mcp-image-batch long-task MCP using file-based input/output contracts.
---

# Batch Image Generation Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Execute bulk image generation through the `mcp-image-batch` MCP. This is a
long-task image generation path and must use file handoff. Do not paste large
prompt batches, reference manifests, generated image bytes, or per-image result
payloads into the conversation.

This skill does not replace `game-art/30-generate/image-generation-contract`.
It is the batch execution adapter used by that contract when many
`llm_image_generation` or `image_edit` requests should be produced together.

## Input Contract

Required:
- normalized image request manifest from
  `.allforai/game-design/art/image-generation/image-request-manifest.json`;
- image model routing report from
  `.allforai/game-design/art/image-generation/image-model-routing-report.json`;
- asset acceptance criteria from
  `.allforai/game-design/art/asset-acceptance-criteria.json`;
- output root and caller-approved image output directories;
- batch size policy and long-task timeout policy.

Optional:
- reference image paths;
- previous `mcp-image-batch` run report;
- downstream feedback report;
- visual acceptance coverage gap report;
- repair attempt index;
- provider/model overrides already validated by
  `image-model-capability-registry`.

Return `UPSTREAM_DEFECT` when required request, routing, or acceptance files are
missing. Return `blocked_by_missing_mcp_image_batch` when the MCP tool is not
available or cannot be called.

## Output Contract

Writes:

```text
.allforai/game-design/art/image-generation/mcp-image-batch-input.json
.allforai/game-design/art/image-generation/mcp-image-batch-task.json
.allforai/game-design/art/image-generation/mcp-image-batch-output.json
.allforai/game-design/art/image-generation/mcp-image-batch-report.md
.allforai/game-design/art/image-generation/generated-image-files-manifest.json
```

The normal image contract still owns:

```text
.allforai/game-design/art/image-generation/image-generation-report.json
.allforai/game-design/art/image-generation/accepted-image-manifest.json
```

`generated-image-files-manifest.json` is not a downstream handoff. Downstream
skills may consume only `accepted-image-manifest.json` after validation.

## Invocation Contract

```json
{
  "skill": "game-art/batch-image-generation",
  "mode": "mcp_image_batch_file_handoff",
  "input_paths": {
    "image_requests": ".allforai/game-design/art/image-generation/image-request-manifest.json",
    "image_model_routing": ".allforai/game-design/art/image-generation/image-model-routing-report.json",
    "asset_acceptance_criteria": ".allforai/game-design/art/asset-acceptance-criteria.json",
    "downstream_feedback": ".allforai/game-design/art/image-generation/image-feedback-report.json"
  },
  "output_root": ".allforai/game-design/art/image-generation",
  "image_output_roots": [".allforai/game-design/art/generated/"],
  "long_task": {
    "tool": "mcp-image-batch",
    "poll_interval_seconds": 10,
    "timeout_seconds": 3600
  }
}
```

Supported modes: `mcp_image_batch_file_handoff`, `poll_existing_task`,
`repair_failed_batch`, `register_existing_batch_output`.

## File Handoff Protocol

Build `.allforai/game-design/art/image-generation/mcp-image-batch-input.json`
before invoking the MCP. The file must contain only structured request data and
project-relative paths:

```json
{
  "schema_version": "1.0",
  "batch_id": "art_batch_001",
  "source_manifest": ".allforai/game-design/art/image-generation/image-request-manifest.json",
  "routing_report": ".allforai/game-design/art/image-generation/image-model-routing-report.json",
  "output_root": ".allforai/game-design/art/generated/",
  "requests": [
    {
      "request_id": "tile_grass_001",
      "asset_id": "tile_grass",
      "task_type": "tileset",
      "selected_provider": "project_local_mcp",
      "selected_model": "mcp-image-batch:<model-or-profile>",
      "prompt_path": ".allforai/game-design/art/image-generation/prompts/tile_grass_001.md",
      "negative_prompt_path": ".allforai/game-design/art/image-generation/prompts/tile_grass_001.negative.md",
      "reference_image_paths": [],
      "output_path": ".allforai/game-design/art/generated/tile_grass_001.png",
      "acceptance_ref": ".allforai/game-design/art/asset-acceptance-criteria.json"
    }
  ]
}
```

Prompt text may be written to per-request prompt files. Keep the MCP call small:
pass the input file path, output file path, and task policy. The MCP tool must
read from files and write files. Do not pass the full request array through the
chat/tool prompt when a file path is available.

## Long Task Protocol

`mcp-image-batch` is a long task:
1. Submit the batch using the input file path.
2. Write `.allforai/game-design/art/image-generation/mcp-image-batch-task.json`
   with `task_id`, `batch_id`, `submitted_at`, `input_path`, `expected_outputs`,
   `poll_interval_seconds`, and `timeout_seconds`.
3. Poll until the MCP reports completed, failed, cancelled, or timed out.
4. Write the raw structured MCP result to
   `.allforai/game-design/art/image-generation/mcp-image-batch-output.json`.
5. Write a concise Markdown report with generated paths, missing paths, failed
   requests, model/provider metadata, and retry recommendations.

Allowed task states: `submitted`, `running`, `completed`, `failed`,
`cancelled`, `timeout`, `blocked_by_missing_mcp_image_batch`.

Do not fabricate output images when the task fails or times out. Return the
blocking state with the task id and last MCP status.

## Registration And Validation

After the MCP completes:
1. Confirm every declared output path exists and is readable.
2. Write `generated-image-files-manifest.json` with one entry per request:
   `request_id`, `asset_id`, `output_path`, `provider`, `model`,
   `mcp_task_id`, `mcp_status`, `file_exists`, `bytes`, `format`, and
   `validation_state`.
3. Return control to `image-generation-contract` for deterministic validation,
   visual validation, repair routing, and accepted manifest updates.
4. Do not set `consumer_ready: true` in this skill. Only
   `image-generation-contract` may write accepted entries.

## Repair Loop

When downstream feedback or visual QA reports image defects, missing required
assets, insufficient variants, incomplete expression/state coverage, or not
enough visually accepted images:
1. Rebuild only affected request prompt files and batch input entries.
2. If the problem is coverage shortage, add the missing request ids or variant
   requests to the same repair batch instead of creating isolated one-off image
   calls.
3. Submit a repair batch to `mcp-image-batch`.
3. Preserve prior output paths in repair history and write new output paths or
   versioned filenames.
4. Re-run `image-generation-contract` validation and downstream consumer
   validation.

Default budget: 3 batch generation attempts per affected request.

Use `mcp-image-batch` again whenever the accepted output count is below the
caller-required count. Examples: fewer than required tile variants, missing
special tiles, insufficient icon alternatives, incomplete character expression
sets, failed contact-sheet coverage, or QA rejecting too many candidates. Do not
fill shortage with placeholder images or prose.

## Automatic Validation

Before returning success:
1. The MCP call used `mcp-image-batch`.
2. The MCP call used file handoff: input file path and output file path.
3. `mcp-image-batch-task.json` records a long-task id and final status.
4. Every completed request has an existing image file.
5. Failed or missing images are listed explicitly and are not accepted.
6. The output manifest references the original request ids.
7. No raw generated image path is handed to downstream skills outside
   `accepted-image-manifest.json`.
8. Coverage shortage or insufficient accepted images triggers another
   `mcp-image-batch` repair batch or returns `FAILED_VALIDATION` after budget
   exhaustion.

## Completion Conditions

Return `COMPLETED` when the MCP batch completed, output files exist, and
`generated-image-files-manifest.json` is complete.

Return `FAILED_VALIDATION` when the MCP completed but required output files are
missing, malformed, or unmatched to request ids.

Return `blocked_by_missing_mcp_image_batch` when the MCP tool is unavailable.
Return `FAILED_ENV` when the MCP tool exists but cannot execute due to local
environment failure.
