# Game Art Boundary Contracts

## Goal

Seal the game-art pipeline with an explicit input contract and output contract.
The input contract normalizes product concept and human preference before art
production. The output contract guarantees generated art can be consumed by
program implementation or a game engine/runtime.

## Scope

- Add `art-direction-input-contract`.
- Add `engine-ready-art-output-contract`.
- Keep engine-specific import differences inside `engine-export-profile` unless
  a real engine requires native project-file mutation or editor/CLI execution.

## Tasks

- [x] Define product/human-preference art input contract.
- [x] Define engine-ready art output contract.
- [x] Add multi-engine profile rules to `engine-export-profile`.
- [x] Require executable post-import validation evidence; static checks are
  diagnostics only and cannot pass validation.
- [x] Document when an engine-specific adapter sub-skill is warranted.
- [x] Wire the boundary contracts into `game-art/SKILL.md`.
- [x] Verify standard sections, routing, and canonical paths.
