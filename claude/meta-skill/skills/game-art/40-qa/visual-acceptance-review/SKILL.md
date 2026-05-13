---
name: game-art-40-qa-visual-acceptance-review
description: Internal bundled meta-skill module for game-art/40-qa/visual-acceptance-review; use when generated or adapted game art must be visually inspected through task lists, Codex CLI review, and Claude Code closure audit before downstream acceptance.
---

# Visual Acceptance Review Skill

> Internal sub-skill for game art pipelines. Status: bundled, inactive, not wired.

## Overview

Game-art wrapper for reusable batch visual acceptance. It supplies art-specific
acceptance criteria, evidence manifests, output paths, and repair routing, then
delegates the actual batch review mechanics to
`${CLAUDE_PLUGIN_ROOT}/skills/visual-qa/40-qa/batch-visual-acceptance/SKILL.md`.

Codex CLI remains the required visual reviewer. Claude Code only audits closure
through the delegated visual-qa skill. Claude Code does not re-judge visual quality.

This skill must run for generated, searched, adapted, user-provided, local, or
3D-rendered bitmap assets before they can be treated as visually accepted.

## Input Contract

Required:
- `.allforai/game-design/art/image-generation/accepted-image-manifest.json`
- actual PNG/JPG/WebP files referenced by that manifest
- one of: contact sheets, preview maps, animation previews, UI mockup previews,
  runtime screenshots, or per-asset image paths suitable for visual inspection
- `.allforai/game-design/art-style-guide.json` or an equivalent style token
  artifact
- `.allforai/game-design/art/asset-acceptance-criteria.json`
- `.allforai/game-design/art/asset-acceptance-criteria.md`

Optional:
- `.allforai/game-design/asset-registry.json`
- `.allforai/game-design/art/qa/art-preview-qa-report.json`
- `.allforai/game-design/art/qa/2d-style-consistency-qa-report.json`
- `.allforai/game-design/art/image-generation/image-generation-report.json`
- project-local specialized art-generation skill
- `.allforai/bootstrap/specialized-skills/<specialization_id>-art-generation/SKILL.md`

If the manifest exists but image files are missing or unreadable, return
`blocked_by_missing_visual_evidence`. Do not accept manifest-only review.

## Output Contract

Write:

```text
.allforai/game-design/art/qa/visual-acceptance-task-list.json
.allforai/game-design/art/qa/visual-acceptance-batches/
.allforai/game-design/art/qa/codex-visual-review.json
.allforai/game-design/art/qa/codex-visual-review.md
.allforai/game-design/art/qa/visual-review-closure-audit.json
.allforai/game-design/art/qa/visual-review-closure-audit.md
.allforai/game-design/art/qa/visual-repair-loop-report.json
.allforai/game-design/art/qa/visual-repair-loop-report.md
```

The JSON task list is an index only. The review source of truth is a set of
batch Markdown documents under
`.allforai/game-design/art/qa/visual-acceptance-batches/`.

Each task index item must include:
- `task_id`
- `batch_doc_path`
- `asset_id`
- `asset_kind`
- `image_paths`
- `preview_paths`
- `contract_refs`
- `visual_questions`
- `acceptance_criteria`
- `blocking_failure_codes`

Each batch Markdown document must contain:
- batch id, asset kind, and reviewer goal;
- compact asset table with `asset_id`, image paths, preview/contact-sheet paths,
  contract refs, and expected use;
- visual questions grouped by theme;
- acceptance criteria and blocking failure codes;
- instructions that the reviewer must inspect images and must not pass assets
  from specs alone;
- enough references for audit, but no pasted large specs.

Codex review findings must include:
- `finding_id`
- `task_id`
- `asset_id`
- `severity`
- `claim`
- `evidence_paths`
- `failure_code`
- `recommended_fix`

Claude Code closure audit must include:
- `audit_id`
- `codex_review_ref`
- `audit_verdict`: `closed | incomplete | malformed_report | missing_evidence | missing_feedback | missing_rerun`
- `checked_items`
- `missing_items`
- `blocking_codex_findings`
- `feedback_report_refs`
- `repair_loop_refs`
- `notes`

The repair loop report must include:
- `loop_iteration`
- `failed_task_ids`
- `codex_failure_codes`
- `feedback_report_path`
- `regenerated_or_repaired_assets`
- `rerun_batch_doc_paths`
- `rerun_codex_review_path`
- `rerun_closure_audit_path`
- `final_verdict`

## Invocation Contract

```json
{
  "skill": "game-art/visual-acceptance-review",
  "mode": "batch_docs_codex_cli_audit",
  "input_paths": {
    "accepted_image_manifest": ".allforai/game-design/art/image-generation/accepted-image-manifest.json",
    "asset_acceptance_criteria": ".allforai/game-design/art/asset-acceptance-criteria.json",
    "asset_acceptance_criteria_doc": ".allforai/game-design/art/asset-acceptance-criteria.md",
    "asset_registry": ".allforai/game-design/asset-registry.json",
    "style_guide": ".allforai/game-design/art-style-guide.json",
    "art_preview_report": ".allforai/game-design/art/qa/art-preview-qa-report.json",
    "style_consistency_report": ".allforai/game-design/art/qa/2d-style-consistency-qa-report.json",
    "image_generation_report": ".allforai/game-design/art/image-generation/image-generation-report.json"
  },
  "output_root": ".allforai/game-design/art/qa"
}
```

Supported modes: `batch_docs_codex_cli_audit`, `audit_existing_codex_report`.

## Batch Review Documents

## Delegation

Read and follow:

```text
${CLAUDE_PLUGIN_ROOT}/skills/codex-cli-delegation/30-execute/codex-cli-task/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/visual-qa/00-env/visual-model-capability-registry/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/visual-qa/40-qa/batch-visual-acceptance/SKILL.md
```

Invoke it with:

```json
{
  "skill": "visual-qa/batch-visual-acceptance",
  "mode": "batch_docs_codex_cli_audit",
  "input_paths": {
    "acceptance_criteria": ".allforai/game-design/art/asset-acceptance-criteria.json",
    "acceptance_criteria_doc": ".allforai/game-design/art/asset-acceptance-criteria.md",
    "visual_model_routing": ".allforai/game-design/art/qa/visual-model-routing-report.json",
    "evidence_manifest": ".allforai/game-design/art/image-generation/accepted-image-manifest.json"
  },
  "output_root": ".allforai/game-design/art/qa"
}
```

The rest of this skill defines game-art-specific criteria mapping and feedback
routing for that delegated workflow.

For game-art, high-risk visual batches include character identity, expression
sets, icon readability, tile distinguishability, VFX readability, animation
continuity, UI layout screenshots, and subtle style drift. These batches must
have a routed model with known sufficient visual capability or return
`blocked_by_missing_visual_model_capability`.

## Project-Specific Acceptance

Visual acceptance principles must be specialized per project. The bundled skill
defines the review mechanism, evidence requirements, and failure routing; it
must not hardcode one universal beauty standard.

Before writing batch documents, read the project-local art generation
specialization when it exists:

```text
.allforai/bootstrap/specialized-skills/<specialization_id>-art-generation/SKILL.md
```

Fold its project-specific standards and
`.allforai/game-design/art/asset-acceptance-criteria.md` into every batch
document's `acceptance_criteria`, including:
- game genre and view mode, such as side-view, top-down, isometric, puzzle
  board, visual novel, platformer, or 2.5D baked output;
- gameplay scale and minimum readable size;
- first-screenshot promise and visual hook;
- asset family distinction rules, such as tile states, piece families,
  character identities, UI states, or VFX event meanings;
- target platform and expected display density;
- approved style tokens and human preference constraints;
- downstream engine/runtime constraints.

If no project specialization exists but the project clearly has type-specific
visual risks, return `UPSTREAM_DEFECT` and request the specialized art-generation
skill instead of applying generic standards.

Create batch documents by visually meaningful asset group, not one vague global
task and not one prompt per tiny asset:
- tile readability and distinguishability;
- character identity, expression consistency, crop, and dialogue-box fit;
- portrait and icon small-size readability;
- UI state clarity and layout fit;
- VFX frame or preview readability;
- background/gameplay foreground separation;
- animation frame or skeletal preview continuity.

Each batch must point to actual images or preview sheets. If individual assets
are too numerous, first create contact sheets, preview maps, or animation
previews and reference those files. A batch without image evidence is blocked.

Batching rules:
- keep one batch focused on one asset family and acceptance question set;
- prefer contact sheets or preview maps over listing dozens of isolated images
  in the prompt body;
- write image paths as relative paths so reviewers can open them directly;
- store every batch as a Markdown document so the review is auditable and can
  be reused without reloading all upstream specs into context.

## Codex CLI Review

Invoke Codex CLI as an independent reviewer after the batch documents are
written. The reviewer must receive the batch document paths and image evidence
paths, not only the source specs. Instruct it to inspect the images and return
structured JSON plus a Markdown review document.

Use a command shape equivalent to:

```bash
codex exec --json --output .allforai/game-design/art/qa/codex-visual-review.json \
  "Read every Markdown batch under .allforai/game-design/art/qa/visual-acceptance-batches/, inspect the referenced images, and write .allforai/game-design/art/qa/codex-visual-review.md with visual blockers, major issues, and repair suggestions. Do not pass assets you did not visually inspect."
```

If the local Codex CLI cannot be called, return `blocked_by_missing_codex_cli`.
Do not replace this step with the same agent's prose summary.

## Claude Code Closure Audit

After Codex CLI writes its report, Claude Code audits the process closure
without re-scoring visual quality. Codex CLI is the visual judge. Claude Code
checks whether the report is usable and whether the pipeline reacted correctly:
- every Codex finding cites existing image/contact-sheet/preview evidence;
- every blocker/major Codex finding has `asset_id`, `task_id`, `failure_code`,
  severity, and recommended fix;
- blocker/major findings were written to
  `.allforai/game-design/art/image-generation/image-feedback-report.json` or
  explicitly routed to a non-image owner;
- repair/re-generation happened for affected assets when required;
- affected batch documents were rebuilt when their evidence changed;
- Codex CLI was rerun for affected batches;
- final Codex output has no unresolved blocker/major findings, or the remaining
  issues are reported as `FAILED_VALIDATION`.

Claude Code must not override Codex's visual judgment with a second subjective
visual judgment. If the Codex report is malformed, lacks evidence references, or
does not support repair routing, the audit returns `malformed_report` or
`missing_evidence` and the Codex review must be rerun with a corrected batch
document.

## Repair And Revalidation Loop

Visual acceptance is iterative. A Codex blocker or major issue must not only
produce comments; it must drive repair and revalidation until the repair budget
is exhausted.

Loop:
1. Codex CLI reviews batch documents and image evidence.
2. Claude Code audits the Codex report for evidence references, structure, and
   repair routing; it does not re-score the images.
3. For every Codex blocker/major issue that passes closure-audit structure
   checks, write downstream feedback to
   `.allforai/game-design/art/image-generation/image-feedback-report.json`.
4. Route the defect by root cause:
   - `image_generation` or `prompt_contract`: invoke
     `game-art/30-generate/image-generation-contract/SKILL.md` in
     `process_downstream_feedback` or `repair_request` mode, then regenerate
     or re-register affected images.
   - `coverage_shortage`: invoke
     `game-art/30-generate/image-generation-contract/SKILL.md` in
     `repair_coverage_shortage` mode and generate additional candidates through
     `game-art/30-generate/batch-image-generation/SKILL.md` using
     `mcp-image-batch` file handoff.
   - `source_selection`: route to `asset-source-strategy-spec` or
     `asset-pack-search-spec`, then re-register through
     `image-generation-contract`.
   - `asset_adaptation`: route to `existing-asset-adaptation-spec`, then
     re-register through `image-generation-contract`.
   - `downstream_spec`: route to the producing asset spec/generation skill; do
     not regenerate images until the spec is corrected.
   - `runtime_tooling`: route to atlas, import, or engine output skills; do not
     regenerate images by default.
5. Rebuild only the affected contact sheets, preview maps, or batch documents.
6. Re-run Codex CLI review for the affected batches; this is the required
   rerun Codex CLI review step.
7. Re-run Claude Code closure audit for the affected Codex report.
8. Append the iteration to
   `.allforai/game-design/art/qa/visual-repair-loop-report.json` and
   `.allforai/game-design/art/qa/visual-repair-loop-report.md`.

Default budget: 3 image/source/adaptation repair attempts and 2 batch
revalidation attempts per affected asset group. If the issue remains after the
budget, return `FAILED_VALIDATION` with the last visual evidence and repair
target. Do not downgrade a Codex blocker to a warning just to pass.

## Automatic Validation

Before returning success:
1. Confirm every batch document references at least one existing visual evidence
   path.
2. Confirm Codex CLI produced both JSON and Markdown review outputs.
3. Confirm Claude Code closure audit produced both JSON and Markdown outputs.
4. Confirm every Codex blocker/major issue is covered by the Claude Code closure
   audit and either has feedback/repair routing or remains `FAILED_VALIDATION`.
5. Confirm no asset is marked visually accepted unless Codex CLI inspected the
   evidence and Claude Code closure audit passed with `audit_verdict: closed`.
6. Confirm manifest-only, spec-only, or path-existence-only review returns
   `blocked_by_missing_visual_evidence`.
7. Confirm all required visual evidence paths were inspected and recorded.
8. Confirm every Codex blocker/major issue is either fixed by a completed
   repair-and-revalidation iteration or remains as `FAILED_VALIDATION`.
9. Confirm the repair loop report exists whenever any Codex blocker/major issue
   was found.
10. Confirm coverage shortage, insufficient variants, missing required images,
    or too few visually accepted candidates triggered another `mcp-image-batch`
    repair batch or remains `FAILED_VALIDATION` after budget exhaustion.

## Completion Conditions

Return `COMPLETED` only when the batch documents, task index, Codex CLI review,
Claude Code closure audit, and any required repair loop reports exist, all visual
evidence paths were inspected by Codex CLI, the closure audit is `closed`, and no
Codex blocker or major visual issues remain after revalidation.

Return `FAILED_VALIDATION` when Codex blocker/major visual issues remain.
Return `blocked_by_missing_visual_evidence` when required images, previews, or
contact sheets are missing or unreadable.
Return `blocked_by_missing_codex_cli` when Codex CLI cannot be invoked.
