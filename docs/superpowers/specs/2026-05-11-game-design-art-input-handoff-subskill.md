# Game Design Art Input Handoff Subskill

## Goal

Create a game-design subskill that serializes game concept and game planning
outputs into validated handoff contracts for game-art and downstream program
development.

## Scope

- Add `game-design/30-generate/art-input-handoff-generation`.
- Register it in `game-design/SKILL.md`.
- Make `game-art/art-direction-input-contract` prefer the new handoff artifact.
- Emit a human-readable planning handoff document.
- Emit program development node handoff JSON for downstream implementation.
- Keep bootstrap integration unchanged.

## Tasks

- [x] Add art input handoff subskill.
- [x] Define total input contract and total output contract.
- [x] Define validation and repair routing back to planning subskills.
- [x] Add handoff document output.
- [x] Add program development node handoff output.
- [x] Register the subskill in `game-design/SKILL.md`.
- [x] Update game-art entry contract to consume the handoff.
