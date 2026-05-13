---
name: visual-qa-40-qa-batch-visual-acceptance
description: Reusable batch visual acceptance workflow using mandatory Codex CLI image/screenshot inspection, auditable Markdown batches, JSON/Markdown reports, feedback routing, reruns, and closure audit.
---

# Batch Visual Acceptance Skill

## Overview

Run reusable batch visual acceptance for screenshots, generated images, contact
sheets, preview maps, UI states, HTML gates, runtime captures, and visual
regression sets.

This skill is intentionally domain-neutral. The caller supplies the standard;
this skill enforces the review mechanics.

Any workflow that produces user-facing screenshots or visual runtime captures
should prefer this skill for visual judgment, including UI automation tests,
browser/Electron/Tauri screenshots, Android/iOS/Flutter/React Native screenshots,
game client smoke-test captures, HTML approval gates, and generated art review.

Codex CLI is mandatory for visual inspection. Claude Code should not spend
tokens re-judging the same images. Claude Code only audits closure: report
completeness, evidence references, feedback routing, repair execution, and rerun
records.

All Codex CLI execution must follow
`${CLAUDE_PLUGIN_ROOT}/skills/codex-cli-delegation/30-execute/codex-cli-task/SKILL.md`
so ClaudeCode passes only a short, path-based prompt and Codex reads files from
the target workspace.

## Input Contract

Required:
- acceptance criteria document or JSON supplied by the caller;
- `.allforai/visual-qa/visual-model-routing-report.json` or caller-local
  equivalent produced by
  `visual-qa/00-env/visual-model-capability-registry/SKILL.md`;
- visual evidence paths: images, screenshots, contact sheets, preview maps,
  animation previews, HTML screenshots, video frame captures, or rendered
  canvases;
- for test screenshots, a test report or flow/state manifest that maps each
  screenshot to the exercised route, viewport/device, state, expected UI, and
  pass/fail assertions;
- batch grouping policy;
- blocking failure codes;
- repair routes or owner nodes for failures.

Optional:
- previous visual review report;
- previous feedback report;
- runtime/import/test reports;
- baseline screenshots or golden references;
- project-local specialization document.

If evidence files are missing, unreadable, stale, or not directly inspectable,
return `blocked_by_missing_visual_evidence`.

If Codex CLI cannot be invoked, return `blocked_by_missing_codex_cli`. Do not
replace Codex CLI with a same-agent prose summary.

If a high-risk batch lacks a capable routed visual model, return
`blocked_by_missing_visual_model_capability`.

## Output Contract

Default output root is caller-provided. If none is provided, write under:

```text
.allforai/visual-qa/
```

Required outputs:

```text
<output_root>/visual-acceptance-task-list.json
<output_root>/visual-acceptance-batches/
<output_root>/visual-model-routing-report.json
<output_root>/codex-visual-review.json
<output_root>/codex-visual-review.md
<output_root>/visual-review-closure-audit.json
<output_root>/visual-review-closure-audit.md
<output_root>/visual-repair-loop-report.json
<output_root>/visual-repair-loop-report.md
```

`visual-repair-loop-report.*` is required only when Codex reports blocker/major
issues or when a previous run had unresolved issues.

## Invocation Contract

```json
{
  "skill": "visual-qa/batch-visual-acceptance",
  "mode": "batch_docs_codex_cli_audit",
  "input_paths": {
    "acceptance_criteria": ".allforai/.../acceptance-criteria.json",
    "acceptance_criteria_doc": ".allforai/.../acceptance-criteria.md",
    "visual_model_routing": ".allforai/visual-qa/visual-model-routing-report.json",
    "evidence_manifest": ".allforai/.../visual-evidence-manifest.json",
    "previous_review": ".allforai/.../codex-visual-review.json",
    "previous_feedback": ".allforai/.../visual-feedback-report.json"
  },
  "output_root": ".allforai/visual-qa"
}
```

Supported modes: `batch_docs_codex_cli_audit`, `audit_existing_codex_report`,
`rerun_failed_batches`.

## Batch Documents

Before creating or running batches:
1. Invoke or read
   `${CLAUDE_PLUGIN_ROOT}/skills/visual-qa/00-env/visual-model-capability-registry/SKILL.md`.
2. Ensure each batch has `task_risk`, `minimum_capabilities`,
   `selected_visual_model`, and `model_reason`.
3. Block high-risk batches with `blocked_by_missing_visual_model_capability`
   when no capable visual model is available.

Create Markdown batch documents under `<output_root>/visual-acceptance-batches/`.
The task-list JSON is only an index; the batch Markdown documents are the audit
source of truth.

Each batch document must include:
- selected visual model and model reason from the visual model routing report;
- batch id and review goal;
- compact evidence table with IDs, paths, expected use, and criteria refs;
- acceptance criteria copied or linked from the caller's standard;
- visual questions grouped by theme;
- blocking failure codes;
- instruction that Codex must inspect visual evidence and must not pass from
  specs or metadata alone.

Batching rules:
- group by visual standard and failure mode, not by arbitrary file count;
- prefer contact sheets, preview maps, or representative screenshots over
  dumping long image lists into the prompt;
- for UI/test screenshots, group by user flow and viewport/device first, then by
  failure mode;
- keep paths relative and auditable;
- keep domain-specific details in the caller's criteria document.

## Codex CLI Review

Invoke Codex CLI after batch documents exist. The command must point Codex at
the batch documents and visual evidence paths.

Read and follow
`${CLAUDE_PLUGIN_ROOT}/skills/codex-cli-delegation/30-execute/codex-cli-task/SKILL.md`
before invoking Codex CLI. Do not paste batch contents, acceptance criteria, or
image metadata into the ClaudeCode prompt; pass paths and output contracts.

If Codex CLI supports model selection, pass the routed `selected_visual_model`
for each batch or batch group. If only the CLI default is available, the routing
report must state that the default satisfies the batch's minimum capability.

Use a command shape equivalent to:

```bash
codex exec --json --output <output_root>/codex-visual-review.json \
  "Read every Markdown batch under <output_root>/visual-acceptance-batches/, inspect the referenced visual evidence, and write <output_root>/codex-visual-review.md with blockers, major issues, minor issues, evidence refs, failure codes, and repair suggestions. Do not pass artifacts you did not visually inspect."
```

Do not enable `--return-all-messages`; ClaudeCode should read the final report files and closure-relevant fields only.

Codex output must include:
- reviewed batch ids;
- inspected evidence paths;
- blocker/major/minor findings;
- failure codes;
- evidence references;
- recommended repair;
- pass/fail summary.

## Closure Audit

Claude Code writes `<output_root>/visual-review-closure-audit.json` and
`<output_root>/visual-review-closure-audit.md` without re-judging visual
quality.

Audit checks:
- Codex report exists and is parseable;
- every reviewed batch has inspected evidence paths;
- every blocker/major finding has artifact id, failure code, evidence refs, and
  repair suggestion;
- coverage shortage findings have required count, accepted count, missing
  variant/state ids when known, and repair suggestion;
- feedback was emitted for blocker/major findings;
- required repairs were executed or explicitly failed;
- failed batches were rerun by Codex CLI after repair;
- final unresolved blockers/majors are represented as `FAILED_VALIDATION`.

## Repair And Rerun Loop

When Codex reports blocker/major issues:
1. Write caller-compatible feedback with `artifact_id`, `batch_id`,
   `failure_code`, `severity`, `evidence_refs`, `root_cause`, and
   `requested_action`.
   Use `root_cause=coverage_shortage` when the problem is too few accepted
   images, missing required variants, incomplete state coverage, or rejected
   candidate count rather than a single-image defect.
2. Route repair to the caller-provided owner skill/node.
3. Rebuild only affected evidence and batch documents.
4. Rerun Codex CLI for affected batches.
5. Audit closure again.
6. Append the iteration to `visual-repair-loop-report.json` and
   `visual-repair-loop-report.md`.

Default budget: 3 repair attempts and 2 rerun attempts per affected batch.
Return `FAILED_VALIDATION` with the last evidence if the issue remains.

## Automatic Validation

Before returning success:
1. Every batch document references existing visual evidence.
2. Visual model routing exists for every batch.
3. High-risk batches are not accepted with unknown visual model capability.
4. Codex CLI was invoked and produced JSON and Markdown reports.
5. Codex report lists inspected evidence paths.
6. Closure audit exists and does not re-score visual quality.
7. Blocker/major findings have feedback or remain `FAILED_VALIDATION`.
8. Any repair rerun has new or updated evidence and a rerun Codex report.
9. No artifact is accepted from metadata, manifest, or prose alone.

## Completion Conditions

Return `COMPLETED` when batches, Codex reports, closure audit, and any required
repair loop reports exist, and Codex has no unresolved blocker/major findings.

Return `FAILED_VALIDATION` when Codex blocker/major findings remain after the
repair budget or when feedback/rerun closure is incomplete.

Return `blocked_by_missing_visual_evidence` when required evidence is missing or
unreadable. Return `blocked_by_missing_codex_cli` when Codex CLI cannot run.
Return `blocked_by_missing_visual_model_capability` when required visual model
capability is unavailable or unknown.
