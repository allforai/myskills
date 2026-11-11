---
name: game-art-30-generate-image-generation-contract
description: "Define the shared contract for generated and acquired game images (and generated motion video): images come from Codex image generation, video from the Grok CLI; every result is validated and recorded before consumption, with a downstream feedback loop; writes art/image-generation/accepted-image-manifest.json."
---

# Image Generation Contract Skill

> Internal sub-skill for game art pipelines.
> Status: bundled.
> This file is installed with meta-skill but is not automatically invoked by
> `/bootstrap` or `/run` until a node-spec explicitly reads this path.

## Overview

Every image a downstream skill consumes, whatever its source, is untrusted until
it is checked against its request and recorded in the accepted-image manifest.
Downstream skills that find a defect send it back to the original request
instead of working around it.

Asset-specific skills (`icon-generation`, `tileset-generation`,
`character-layer-sheet`, `sprite-vfx-generation`, `decal-generation`,
`particle-system`, `trail-generation`, `frame-animation-generation`,
`ui-mockup-generation`, and the rest) decide what each asset is for. This
contract decides where generated pixels come from and when a result counts as
accepted.

Generated results are candidates. They are not consumer-ready until
`game-art/40-qa/generated-candidate-selection/SKILL.md` and the checks below
pass.

## Generation Sources

The image and video models are the generators. The contract does not keep a
provider catalog, model routing table, prompt compiler, or batch planner: the
agent writes each request's prompt from the request itself, and the acceptance
checks below judge the result.

| Need | Source | How it is reached |
|---|---|---|
| New image, image edit, variation from reference images | Codex image generation | On Codex: its own image generation. On Claude Code or Pi: `codex exec` through `codex-cli-delegation/30-execute/codex-cli-task/SKILL.md`, asked to save each image at the request's `output_path`. |
| New motion video (image-to-video, reference-to-video) | Grok CLI (`grok`) | Headless `grok -p` limited to its `image_to_video` or `reference_to_video` tool, then the saved video is copied to the request's `output_path`. |

Rules for both:
- One source per medium. Do not fall back to another provider, an MCP image
  server, a browser session, or placeholder art when the source is unavailable.
  Return `blocked_by_missing_image_cli` (no usable `codex`) or
  `blocked_by_missing_video_cli` (no usable `grok`, no logged-in subscription
  that includes video, or video disabled by the account's data-retention
  setting) and name what is missing.
- Grant the generator only what the request needs: Codex gets workspace writes
  for the output root; Grok gets only its media tool. Never auto-approve all
  tools.
- A result exists only as a file at the request's `output_path`. A path printed
  by the tool, a file left in the tool's own session or cache directory, or a
  temporary URL is not a result until it is copied there. When the generated
  file exists elsewhere, copy it to `output_path` and validate it; that is not a
  repair attempt and needs no regeneration.

Tool facts the agent cannot infer: Codex keeps generated images under
`$CODEX_HOME/generated_images/` unless told to save them at a path. Grok saves
media under `~/.grok/sessions/<encoded cwd>/<session id>/images|videos/` (the
session id is in its `--output-format json` result), and restricts itself to one
tool with `--tools <tool> --allow <tool>`; `video_gen` is a feature flag, not a
tool name.
- Identity or style consistency across outputs comes from passing the approved
  reference images to the generator (edit / reference mode), and is judged by
  visual QA. A prompt-only result for an asset whose acceptance criteria demand
  identity lock cannot be `consumer_ready: true`.
- Prefer generating raw materials the programmatic processing plan asks for
  (`game-art/20-spec/programmatic-art-processing-plan/SKILL.md`,
  `material_first`) over a flattened final image when that plan exists.

Non-generated sources stay allowed and go through the same gate:
`web_or_marketplace_search`, `existing_asset_pack`, `user_provided_asset`,
`3d_assisted_render`, `local_asset_library`, `local_existing_asset`, `hybrid`.
Generated sources are `llm_image_generation` and `image_edit` (Codex) and
`ai_video` (Grok).

## Request

Every image-producing skill writes its requests to
`.allforai/game-design/art/image-generation/image-request-manifest.json`. Each
request states:

- `request_id`, `asset_id`, `file_prefix`, `purpose` (the asset family, e.g.
  `icon`, `tileset`, `ui_mockup`, `layer_sheet`, `sprite_vfx`, `portrait`,
  `frame_animation`, `motion_video`);
- `source_kind` from the lists above;
- `prompt`: subject, style source, view/camera, composition, background policy,
  and what must not appear;
- `reference_images` when the output must match existing art;
- `output_path` under the caller's approved root, filename starting with
  `file_prefix`; format, size/aspect, and alpha policy;
- `acceptance`: the checks this output must pass, drawn from
  `.allforai/game-design/art/asset-acceptance-criteria.json` for production
  assets, plus `max_repair_attempts`;
- `consumer_skill` and its input contract.

A request missing any of these returns `UPSTREAM_DEFECT`.

## Accepted Image Manifest Gate

`.allforai/game-design/art/image-generation/accepted-image-manifest.json` is the
only handoff from image upstreams to downstream asset, UI, VFX, atlas,
animation, and engine-export skills. Downstream skills must not consume raw PNG
paths directly.

Each entry records `request_id`, `asset_id`, `source_kind`,
`accepted_image_path`, `consumer_skill`, `consumer_input_contract`,
`consumer_ready`, `acceptance_state` (`accepted | needs_revision | rejected |
blocked_by_license | blocked_by_validation | blocked_by_downstream_validation |
blocked_by_missing_generator`),
the checks run and their results, provenance (generator and prompt for generated
files; source URL, license and adaptation reports for acquired files),
`repair_history`, and `downstream_revalidation`.

`consumer_ready` may be true only when all of the following hold:
- the file exists at `accepted_image_path` and matches the declared format,
  size, and alpha policy;
- the request's acceptance checks pass, judged by looking at the image itself,
  not at its manifest entry;
- the entry names its downstream consumer and input contract;
- license/provenance passes for searched, pack, user-provided, or local assets;
- adaptation or render reports pass for adapted or 3D-rendered assets;
- after any downstream feedback, the consumer validation that failed has been
  re-run and passed.

If any of these cannot be checked, `consumer_ready` stays false and the contract
returns `FAILED_VALIDATION`, `UPSTREAM_DEFECT`, or the specific blocked state.

## Modes

| Mode | Behavior |
|---|---|
| `generate_validate` | Generate the requested images/videos, validate, repair, record. |
| `validate_existing` | Validate existing outputs against their requests. |
| `register_searched_or_existing` | Register searched, marketplace, user-provided, adapted, local, or rendered images, then validate them into the accepted manifest. |
| `process_downstream_feedback` | Read downstream defects, classify root cause, reopen requests when needed. |
| `repair_coverage_shortage` | Generate the missing candidates or variants after a coverage shortage. |

## Validation

Deterministic: the file exists at the output path with the declared prefix,
format, size/aspect, and alpha; every accepted entry went through this manifest;
non-generated sources carry license/provenance and adaptation/render evidence.

Visual, on the actual pixels (and on sampled frames for video): subject matches
the purpose; required elements present and forbidden ones absent; style matches
the art style guide and references; nothing important cropped; background/alpha
policy met; readable at the target size when required; composition fits the
downstream use; for video, motion matches the request and the first frame stays
consistent with its source image.

## Downstream Feedback Loop

Downstream skills must not silently compensate for unusable upstream images. A
consumer that fails on an accepted image writes an item to
`.allforai/game-design/art/image-generation/image-feedback-report.json` naming
the `request_id`, the consumer, a defect code (`STYLE_DRIFT`, `CROPPED_SUBJECT`,
`MISSING_REQUIRED_PART`, `MERGED_PARTS`, `WRONG_VIEW`, `LOW_READABILITY`,
`BAD_ALPHA`, `SEAM_FAILURE`, `TEXT_ARTIFACT`, `WRONG_SCALE`,
`DOWNSTREAM_SPEC_ERROR`, `RUNTIME_IMPORT_ERROR`), evidence, and a root cause:

- `image_generation` or `prompt_contract`: reopen the request as
  `needs_revision`, tighten the prompt for the failed check, regenerate,
  revalidate, then re-run the downstream consumer validation that failed;
- `source_selection`, `license_provenance`, `asset_adaptation`: repair through
  the owning source/adaptation skill, re-register here, re-run the consumer
  validation; do not generate by default;
- `downstream_spec` or `runtime_tooling`: the image is fine; repair the spec or
  tooling instead;
- `unknown`: one repair pass, then a structured failure.

Coverage shortage (too few usable candidates, missing variants or tile states,
an incomplete expression set) means the earlier batch was not complete: reopen
only the affected requests and generate again, then revalidate.

The repair budget is shared by the image and its consumer (default 3 image
attempts plus 2 downstream revalidations). When it runs out, return
`FAILED_VALIDATION` with the last evidence and the repair target. Placeholder or
spec-only output is never accepted generation output.

Do not ask for human reference images or human approval.

## Completion Conditions

Return `COMPLETED` only when the request manifest, reports, and
`accepted-image-manifest.json` validate and every required image is
`consumer_ready: true` for its declared consumer.

Return `blocked_by_missing_image_cli` or `blocked_by_missing_video_cli` when the
required generator is unavailable, `FAILED_VALIDATION` when outputs fail
acceptance after the repair budget or acquired assets lack provenance, and
`UPSTREAM_DEFECT` when a request cannot be completed from its inputs.
