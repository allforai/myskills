---
name: game-2d-code-repair-loop
description: Repair code gaps found by 2D runtime QA, rebuild, and rerun affected QA evidence before final production closure.
---

# Code Repair Loop

This is the 2D game specialization of the generic
`${CLAUDE_PLUGIN_ROOT}/skills/meta-orchestration/40-qa/execution-repair-loop/SKILL.md`
contract. Follow the generic repair-and-revalidation rules first, then apply
the 2D runtime screenshot and gameplay-specific evidence requirements below.

## Input Contract

Read:

- `.allforai/game-2d/qa/core-loop-playability-qa-report.json`
- `.allforai/game-2d/qa/asset-binding-visual-qa-report.json`
- `.allforai/game-2d/qa/session-completion-qa-report.json`
- `.allforai/game-2d/assembly/playable-slice-manifest.json`
- `.allforai/game-2d/env/2d-runtime-profile.json`
- project-local specialized QA reports when present.

Each QA report must classify findings into:

- `code_gaps`: implementation defects that can be repaired in project code.
- `asset_gaps`: art/UI/audio asset defects routed to upstream asset repair.
- `contract_gaps`: missing or contradictory design/spec contracts.
- `environment_blockers`: missing runtime, command, device, key, or external tool.

## Output Contract

Write:

- `.allforai/game-2d/repair/code-repair-loop-report.json`
- `.allforai/game-2d/repair/code-repair-loop-report.md`
- `.allforai/game-2d/qa/revalidation-report.json`

The report must include attempted fixes, changed files, commands run, QA reports
rerun, screenshots regenerated, remaining blockers, and `repair_status`.

## Invocation Contract

Run after core-loop, asset-binding visual, and session-completion QA reports
exist. This node is not optional for a 2D production workflow.

```json
{
  "skill": "game-2d-production/40-qa/code-repair-loop",
  "mode": "repair_and_revalidate",
  "input_paths": [
    ".allforai/game-2d/qa/core-loop-playability-qa-report.json",
    ".allforai/game-2d/qa/asset-binding-visual-qa-report.json",
    ".allforai/game-2d/qa/session-completion-qa-report.json"
  ],
  "output_root": ".allforai/game-2d/repair"
}
```

## Automatic Validation

1. Parse all QA reports and collect `code_gaps`.
2. If no `code_gaps` exist, write a no-op repair report with
   `repair_status: "no_code_gaps"` and preserve non-code blockers for closure.
3. If `code_gaps` exist, repair them in project code, then run build/start
   commands from the runtime profile.
4. Any project code, scene, prefab, asset-binding, UI, VFX, audio, or resource
   change made by this node invalidates prior runtime, screenshot, visual, and
   closure QA artifacts. Mark the stale reports in the repair report and rerun
   every affected QA path; do not reuse pre-repair visual evidence.
5. Rerun runtime screenshot capture, runtime probe capture, Codex CLI visual
   review, core-loop assertions, asset-binding visual QA, and session-completion
   QA when the repair touches visible gameplay, scene entrypoints, generated
   nodes, asset loading, HUD, VFX, audio triggers, or completion flow.
6. Repeat repair and revalidation up to 3 attempts.

Do not repair design intent, art direction, asset source quality, missing
external tools, or unavailable runtimes in this node. Route those findings to
their upstream owners and keep them blocking.

## Completion Conditions

Return `COMPLETED` only when all repairable `code_gaps` are fixed and affected
QA evidence is rerun after the last code/resource change, or when no code gaps
exist. `fix-without-verify` is not a valid completion state: if a report is
older than changed gameplay code, scene files, runtime resources, or generated
asset bindings, return `FAILED_VALIDATION` or a blocking stale-evidence status.
Return `FAILED_VALIDATION` when repairable code gaps remain after 3 attempts.
Return a blocking status for environment/tool/runtime blockers that prevent
revalidation.
