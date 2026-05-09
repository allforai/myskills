# Light 2D Art Subskill Gap Closure

## Goal

Close the remaining game-art gaps for light-animation 2D indie games. The
existing art pack can generate assets, animations, UI images, icons, VFX, and
QA reports, but it needs six contracts that make the pipeline easier to call
from game production workflows.

## Target Scope

Add bundled internal sub-skills for:

- 2D view mode specification.
- 2D layering specification.
- 2D animation production planning.
- Animation state machine specification.
- Engine/export profile specification.
- 2D style consistency QA.

## Round 1: Planning And Contracts

- [x] Define a high-level 2D animation production plan skill.
- [x] Define a 2D view mode skill for side-view, top-down, isometric, fixed-room,
  board/grid, visual-novel, shooter, and hybrid presentation.
- [x] Define a 2D layering skill for scenes, character dress-up, animation
  overlays, VFX, UI, helper layers, atlas groups, and runtime sorting.
- [x] Define input/output contracts for animation technique selection.
- [x] Define a runtime animation state machine skill.
- [x] Define engine/export format decisions before runtime import.

## Round 2: QA And Closure

- [x] Define a 2D style consistency QA skill.
- [x] Add root-cause categories and repair routing.
- [x] Ensure outputs reference existing art, UI, level, and runtime consumers.
- [x] Ensure QA can route defects back to image generation, spec, or export.

## Round 3: Pack Integration

- [x] Add all new child skills to `game-art/SKILL.md`.
- [x] Add canonical invocation paths.
- [x] Add example role chains for light 2D indie games.
- [x] Verify standard contract sections and invocation path coverage.

## Round 4: Depth Pass

- [x] Add method/view/layer/runtime decision rules.
- [x] Add normalized output examples for call-site authors.
- [x] Add state progression gates for planning, specs, export, and QA.
- [x] Add evidence and acceptance thresholds for automatic validation.

## Completion Definition

This task is complete when the six missing sub-skills exist, the game-art pack
lists them, and checks confirm each new sub-skill has standard contract
sections, state/schema detail, repair routing, and canonical invocation paths.
