---
name: game-frontend-40-qa-runtime-gameplay-visual-acceptance
description: Internal bundled meta-skill module for game-frontend/40-qa/runtime-gameplay-visual-acceptance; use to validate playable game functionality through repeated runtime screenshots, Codex CLI visual review, and repair/revalidation loops.
---

# Runtime Gameplay Visual Acceptance Skill

> Internal sub-skill for game-frontend pipelines. Status: bundled, inactive, not wired.

## Overview

Validates that automated gameplay actions produce a playable and readable visual
experience, not only correct state transitions. This skill bridges functional
automation and visual acceptance: Playwright or engine automation drives the
game, captures screenshots at declared gameplay milestones, and delegates visual
judgment to Codex CLI through the shared batch visual acceptance workflow.

State assertions remain mandatory. Screenshot review is mandatory for visible
gameplay acceptance. A node must not pass from logs, DOM, canvas probes, or
state deltas alone when the player-facing result is visible.

## Input Contract

Required:
- `.allforai/game-frontend/qa/playable-smoke-test-report.json`
- `.allforai/game-frontend/qa/playability-probe-report.json`
- `.allforai/visual-qa/visual-acceptance-criteria.json`
- `.allforai/visual-qa/visual-acceptance-criteria.md`
- `.allforai/game-frontend/bindings/scene-composition-spec.json`
- `.allforai/game-frontend/bindings/gameplay-system-binding-spec.json`
- `.allforai/game-frontend/bindings/hud-ui-binding-spec.json`
- `.allforai/game-frontend/bindings/animation-vfx-binding-spec.json`
- runtime command, dev server URL, or engine launch command from frontend runtime detection

Optional:
- project-local specialized frontend runtime skill
- level difficulty budget and psychological curve probes
- viewport/device matrix
- previous visual baseline screenshots
- Playwright traces, console logs, network logs, engine logs, and state probe dumps
- `.allforai/visual-qa/visual-model-routing-report.json`

## Output Contract

Writes:

```text
.allforai/game-frontend/qa/runtime-gameplay-visual-acceptance-plan.json
.allforai/game-frontend/qa/runtime-gameplay-screenshot-manifest.json
.allforai/game-frontend/qa/runtime-gameplay-visual-batches/
.allforai/game-frontend/qa/codex-gameplay-visual-review.json
.allforai/game-frontend/qa/codex-gameplay-visual-review.md
.allforai/game-frontend/qa/runtime-gameplay-visual-repair-loop-report.json
.allforai/game-frontend/qa/runtime-gameplay-visual-repair-loop-report.md
.allforai/game-frontend/qa/runtime-gameplay-visual-acceptance-report.json
.allforai/game-frontend/qa/runtime-gameplay-visual-acceptance-report.md
```

The screenshot manifest must include `screenshot_id`, `probe_id`, `scene_id`,
`gameplay_milestone`, `viewport`, `actions_before_capture`, `expected_state`,
`actual_state`, `expected_visual`, `image_path`, `trace_path`, `log_refs`,
`state_probe_refs`, and `capture_status`.

The final report must include `functional_status`, `visual_status`,
`blocking_findings`, `repair_targets`, `rerun_batches`, `unresolved_findings`,
and `acceptance_state`.

Allowed states: `passed`, `passed_with_warnings`, `needs_revision`,
`failed_validation`, `blocked_by_unrunnable_client`,
`blocked_by_missing_screenshot`, `blocked_by_missing_codex_cli`,
`blocked_by_missing_visual_model_capability`.

## Invocation Contract

```json
{
  "skill": "game-frontend/runtime-gameplay-visual-acceptance",
  "mode": "validate",
  "input_paths": {
    "smoke_report": ".allforai/game-frontend/qa/playable-smoke-test-report.json",
    "playability_probe": ".allforai/game-frontend/qa/playability-probe-report.json",
    "scene_composition": ".allforai/game-frontend/bindings/scene-composition-spec.json",
    "gameplay_binding": ".allforai/game-frontend/bindings/gameplay-system-binding-spec.json",
    "hud_ui": ".allforai/game-frontend/bindings/hud-ui-binding-spec.json",
    "animation_vfx": ".allforai/game-frontend/bindings/animation-vfx-binding-spec.json"
  },
  "output_root": ".allforai/game-frontend/qa"
}
```

Supported modes: `plan`, `capture`, `validate`, `rerun_failed_batches`,
`repair_targets`.

## Gameplay Screenshot Plan

Create a task list before capture. Each gameplay probe must define screenshots
for visible milestones, such as:
- initial loaded scene;
- first player input;
- first valid game action;
- first invalid action or blocked input;
- scoring/resource/HUD change;
- animation, VFX, or feedback moment;
- win, lose, retry, pause, or transition state when applicable;
- responsive viewport variants when the target includes mobile or desktop.

For games where visual feedback is the main playability signal, such as puzzle,
board, match, rhythm, action, tower defense, or UI-heavy management games,
capture before/after pairs around the action. For example: before selection,
after selection highlight, after valid match/path/attack/cast, after resolution.

The plan must be project-specific. Use the specialized frontend runtime skill
when present to choose genre-specific milestones, but keep this skill's output
contract unchanged.

Every plan must include at least one `production_visual_binding` milestone for
the primary gameplay screen. This milestone checks that production assets,
HUD/UI, background/context, and feedback layers are visible at the same time as
the core loop. It is not enough for a canvas to contain playable placeholder
geometry.

## Automatic Validation

1. Start the real client or engine. If it cannot run, return
   `blocked_by_unrunnable_client`; do not substitute static review.
2. Execute the declared gameplay actions with Playwright, engine automation, or
   project-local test commands.
3. Capture screenshots at every planned milestone and record the action/state
   evidence next to each image.
4. Run functional assertions for state changes, counters, objectives, input
   response, and error-free runtime logs.
5. Build batch Markdown/JSON documents under
   `.allforai/game-frontend/qa/runtime-gameplay-visual-batches/`.
6. Ensure `.allforai/visual-qa/visual-acceptance-criteria.json` covers the
   current gameplay scene, state, asset bindings, forbidden placeholders, and
   repair routes. If it is missing or generic, return
   `blocked_by_missing_visual_criteria`.
7. Invoke:

```text
${CLAUDE_PLUGIN_ROOT}/skills/visual-qa/40-qa/batch-visual-acceptance/SKILL.md
${CLAUDE_PLUGIN_ROOT}/skills/codex-cli-delegation/30-execute/codex-cli-task/SKILL.md
```

Use Codex CLI in pull mode with short, path-based prompts. Codex CLI must inspect
the actual screenshots for visible playability: blank canvas, missing assets,
unclear selection/target feedback, weak or absent action feedback, HUD overlap,
wrong z-order, unreadable text, indistinguishable tiles/icons, broken animation
frames, VFX hiding gameplay, camera/framing errors, and viewport-specific
interaction risk.

Codex CLI must also run a prototype/placeholder rejection check. The review
must fail the batch when screenshots show pure-color blocks, black debug
backgrounds, generic geometric tiles, sample/prototype boards, missing HUD, or
visuals that do not match the declared art direction and engine-ready asset
manifest. If the game is playable but the screenshot is still a prototype scene,
return `failed_validation`; do not downgrade it to a warning.

When placeholder-like visuals are detected, the review prompt must tell Codex
CLI to read only the relevant paths: scene entrypoint/config, scene composition
spec, asset import binding spec, engine-ready art manifest, and screenshots. It
must identify whether the root cause is wrong entrypoint, missing scene binding,
missing asset loader mapping, placeholder fallback, or ungenerated/unimported
art.

Claude Code must not re-score visual quality. Claude Code only checks closure:
review files exist, screenshot evidence paths are present, findings have repair
targets, failed batches were rerun, and unresolved blockers remain blocking.

## Repair And Revalidation Loop

Every blocker or major finding must route to one of:
- gameplay-system binding or game data when state/action behavior is wrong;
- HUD/UI binding or game-ui when UI blocks gameplay;
- scene composition or input-camera binding when camera/framing/layers fail;
- animation/VFX binding when feedback timing or event binding fails;
- game-art QA or asset import binding when assets are missing, unreadable, or
  inconsistent;
- frontend code assembly when runtime implementation is wrong.

Prototype/placeholder findings route as follows:
- wrong production entrypoint or active sample scene -> scene-flow or playable
  client assembly;
- prototype component/debug renderer active -> frontend code assembly;
- engine-ready assets exist but are not visible -> asset import binding;
- HUD/background/context missing -> scene composition or HUD/UI binding;
- visual assets absent or unreadable -> game-art QA and engine-ready output.

After repair, rerun the same affected gameplay screenshot tasks. Do not close
from an edited report or partial evidence. The loop completes only when the
functional assertion and Codex CLI visual review both pass for affected
milestones.

## Completion Conditions

Return `COMPLETED` when all required gameplay screenshot tasks were captured,
functional assertions passed, Codex CLI visual review has no unresolved blocker
or major finding, and rerun evidence exists for repaired batches.

Return `FAILED_VALIDATION` when the game runs but gameplay visuals remain
unacceptable after the repair budget.

Return `blocked_by_missing_screenshot` when required screenshots are absent.
Return `blocked_by_missing_codex_cli` when Codex CLI cannot run. Return
`blocked_by_missing_visual_model_capability` when no usable visual model route
exists for review. Return `blocked_by_missing_visual_criteria` when no explicit
visual acceptance criteria cover the gameplay screenshot batch.
