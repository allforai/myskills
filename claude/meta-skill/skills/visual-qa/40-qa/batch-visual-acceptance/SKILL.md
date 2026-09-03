---
name: visual-qa-40-qa-batch-visual-acceptance
description: Reusable batch visual acceptance workflow with dual independent visual review (Codex CLI and Claude Code each inspect the evidence), auditable Markdown batches, JSON/Markdown reports, reconciliation, feedback routing, reruns, and closure audit.
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

Visual judgment is **dual-reviewer by design**. Codex CLI and Claude Code each
inspect the same visual evidence independently and each write their own review
report. Neither review substitutes for the other, and neither is skipped to save
tokens — visual defects are exactly the class of problem a single reviewer
misses.

Independence is the point: neither reviewer may read the other's findings before
writing its own report. A third step reconciles the two reports and audits
process closure: report completeness, evidence references, feedback routing,
repair execution, and rerun records.

All Codex CLI execution must follow
`${CLAUDE_PLUGIN_ROOT}/skills/codex-cli-delegation/30-execute/codex-cli-task/SKILL.md`
so ClaudeCode passes only a short, path-based prompt and Codex reads files from
the target workspace.

## Input Contract

Required:
- acceptance criteria document or JSON supplied by the caller;
  prefer `.allforai/visual-qa/visual-acceptance-criteria.json` and
  `.allforai/visual-qa/visual-acceptance-criteria.md` produced by
  `visual-qa/20-spec/visual-acceptance-criteria/SKILL.md`;
- `.allforai/visual-qa/visual-model-routing-report.json` or caller-local
  equivalent produced by
  `visual-qa/00-env/visual-model-capability-registry/SKILL.md`;
- visual evidence paths: images, screenshots, contact sheets, preview maps,
  animation previews, HTML screenshots, video frame captures, or rendered
  canvases;
- runtime probe files when the criteria require dynamic object evidence;
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

If criteria require runtime probe evidence and the probe output is missing,
stale, or not tied to the screenshot task id, return
`blocked_by_missing_runtime_probe`.

If acceptance criteria are missing, stale, generic, or do not cover the current
visual scope, return `blocked_by_missing_visual_criteria` or
`UPSTREAM_DEFECT`. Do not run Codex CLI with an implicit standard such as
"looks good" or "canvas exists".

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
<output_root>/claude-code-visual-review.json
<output_root>/claude-code-visual-review.md
<output_root>/visual-review-reconciliation.json
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
4. Verify the criteria came from
   `visual-qa/20-spec/visual-acceptance-criteria` or an equivalent
   project-local specialization and contains visual promise, forbidden visuals,
   failure codes, evidence requirements, and repair routes.

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

## Codex CLI Review (independent review 1 of 2)

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

## Claude Code Visual Review (independent review 2 of 2)

Claude Code opens the same visual evidence as images and writes its own review to
`<output_root>/claude-code-visual-review.json` and
`<output_root>/claude-code-visual-review.md`.

This is a real visual inspection, not a summary of the Codex report. Claude Code
must not read `codex-visual-review.json` or `codex-visual-review.md` before its
own report is written; ordering between the two reviews is free, but they must
not be allowed to contaminate each other.

Claude Code review must cover, per batch:
- every evidence path actually opened, listed in `inspected_evidence_paths`;
- blocker/major/minor findings against the same acceptance criteria and failure
  codes the batch document gives Codex;
- blank regions, clipped or overflowing text, unreadable contrast, placeholder or
  prototype visuals, wrong visual state, obstruction by modal/keyboard, broken or
  incoherent responsive layout;
- evidence references and recommended repair per finding;
- a pass/fail summary.

JSON state must be one of:

- `passed`
- `passed_with_warnings`
- `failed_visual_review`
- `blocked_by_missing_visual_evidence`
- `blocked_by_unreadable_evidence`

If Claude Code cannot open an evidence file as an image, it returns
`blocked_by_unreadable_evidence` for that batch rather than judging it from the
batch document text.

## Reconciliation And Closure Audit

After both reviews exist, write `<output_root>/visual-review-reconciliation.json`,
then `<output_root>/visual-review-closure-audit.json` and
`<output_root>/visual-review-closure-audit.md`.

Reconciliation rules:
- **Blockers are a union, not an intersection.** A blocker or major finding
  raised by either reviewer blocks the batch. Agreement between reviewers is not
  required to fail.
- Findings that both reviewers raise for the same artifact and failure code are
  merged into one repair item with `agreed: true`.
- Findings raised by only one reviewer are kept with
  `raised_by: codex | claude-code` and `agreed: false`. They are NOT downgraded
  for being unilateral.
- Direct contradictions (one reviewer passes what the other blocks) are recorded
  in `disagreements[]` with both claims and both evidence refs, and resolve in
  favour of the blocking claim.

The reconciliation JSON must include `batch_id`, `merged_findings[]`,
`disagreements[]`, `union_blocking_count`, and `reviewer_agreement_rate`.

Closure audit checks:
- both the Codex report and the Claude Code report exist and are parseable;
- every reviewed batch has inspected evidence paths in **both** reports;
- every blocker/major finding has artifact id, failure code, evidence refs, and
  repair suggestion;
- coverage shortage findings have required count, accepted count, missing
  variant/state ids when known, and repair suggestion;
- reconciliation exists and its union blocking set covers every blocker/major
  finding from either reviewer;
- feedback was emitted for every reconciled blocker/major finding;
- required repairs were executed or explicitly failed;
- failed batches were rerun by **both** reviewers after repair;
- final unresolved blockers/majors are represented as `FAILED_VALIDATION`.

## Repair And Rerun Loop

When either reviewer reports blocker/major issues (union set from
reconciliation):
1. Write caller-compatible feedback with `artifact_id`, `batch_id`,
   `failure_code`, `severity`, `evidence_refs`, `root_cause`, and
   `requested_action`.
   Use `root_cause=coverage_shortage` when the problem is too few accepted
   images, missing required variants, incomplete state coverage, or rejected
   candidate count rather than a single-image defect.
2. Route repair to the caller-provided owner skill/node.
3. Rebuild only affected evidence and batch documents.
4. Rerun **both** reviews for affected batches: Codex CLI and Claude Code
   independent visual review.
5. Reconcile and audit closure again.
6. Append the iteration to `visual-repair-loop-report.json` and
   `visual-repair-loop-report.md`.

Default budget: 3 repair attempts and 2 rerun attempts per affected batch.
Return `FAILED_VALIDATION` with the last evidence if the issue remains.
Never resolve a finding by dropping the reviewer that raised it.

## Automatic Validation

Before returning success:
1. Every batch document references existing visual evidence.
2. Visual model routing exists for every batch.
3. High-risk batches are not accepted with unknown visual model capability.
4. Codex CLI was invoked and produced JSON and Markdown reports.
5. Claude Code produced its own JSON and Markdown visual review reports.
6. Both reports list inspected evidence paths, and neither is a restatement of
   the other.
7. Reconciliation exists and its blocking set is the union of both reviewers'
   blocker/major findings.
8. Closure audit exists.
9. Blocker/major findings from either reviewer have feedback or remain
   `FAILED_VALIDATION`.
10. Any repair rerun has new or updated evidence plus a rerun report from both
    reviewers.
11. No artifact is accepted from metadata, manifest, or prose alone.
12. Acceptance criteria are explicit for the reviewed scope and include blocker
    rejection for blank/prototype/placeholder visuals when runtime or generated
    production assets are in scope.
13. When criteria require runtime probe evidence, the batch references the probe
    path alongside screenshots and validates that probe ids/counts/binding refs
    do not contradict the visible evidence.

## Completion Conditions

Return `COMPLETED` when batches, Codex reports, Claude Code reports,
reconciliation, closure audit, and any required repair loop reports exist, and
**neither** reviewer has unresolved blocker/major findings.

Return `FAILED_VALIDATION` when blocker/major findings from either reviewer
remain after the repair budget or when feedback/rerun closure is incomplete.

Return `blocked_by_missing_visual_evidence` when required evidence is missing or
unreadable. Return `blocked_by_missing_codex_cli` when Codex CLI cannot run.
Return `blocked_by_unreadable_evidence` when Claude Code cannot open required
evidence as images.
Return `blocked_by_missing_visual_model_capability` when required visual model
capability is unavailable or unknown. Return
`blocked_by_missing_visual_criteria` when no explicit criteria document covers
the batch. Return `blocked_by_missing_runtime_probe` when required runtime probe
evidence is missing.
